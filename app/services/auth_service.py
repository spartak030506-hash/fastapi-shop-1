import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    hash_refresh_token,
)
from app.core.config import settings
from app.core.exceptions import (
    EmailAlreadyExistsError,
    InvalidCredentialsError,
    UserInactiveError,
    UserNotFoundError,
    InvalidTokenError,
    RefreshTokenNotFoundError,
)
from app.models.user import User
from app.models.refresh_token import RefreshToken
from app.repositories.user import UserRepository
from app.repositories.refresh_token import RefreshTokenRepository
from app.schemas.auth import RegisterRequest, LoginRequest, TokenResponse
from app.schemas.user import UserResponse


class AuthService:
    """
    Сервис аутентификации и авторизации.

    Отвечает за:
    - Регистрацию пользователей (создание user + токены)
    - Вход в систему (проверка пароля + создание токенов)
    - Обновление токенов (refresh)
    - Выход из системы (отзыв токенов)
    - Смену пароля (обновление + отзыв всех токенов)
    - Удаление пользователя (отзыв всех токенов + soft delete)

    НЕ отвечает за:
    - CRUD операции с пользователями (см. UserService)
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_repo = UserRepository(db)
        self.token_repo = RefreshTokenRepository(db)

    async def register(
        self,
        data: RegisterRequest,
        device_info: str | None = None
    ) -> tuple[UserResponse, TokenResponse]:
        """
        Регистрация нового пользователя.

        Args:
            data: Данные для регистрации
            device_info: Информация об устройстве (User-Agent)

        Returns:
            Кортеж (UserResponse, TokenResponse)

        Raises:
            EmailAlreadyExistsError: Email уже существует
        """
        if await self.user_repo.email_exists(data.email):
            raise EmailAlreadyExistsError(data.email)

        user = User(
            id=uuid.uuid4(),
            email=data.email,
            hashed_password=hash_password(data.password),
            first_name=data.first_name,
            last_name=data.last_name,
            phone=data.phone,
        )

        user = await self.user_repo.create(user)

        tokens = await self._create_tokens_for_user(user.id, device_info)

        return UserResponse.model_validate(user), tokens

    async def login(
        self,
        data: LoginRequest,
        device_info: str | None = None
    ) -> tuple[UserResponse, TokenResponse]:
        """
        Вход в систему.

        Args:
            data: Данные для входа (email, password)
            device_info: Информация об устройстве

        Returns:
            Кортеж (UserResponse, TokenResponse)

        Raises:
            InvalidCredentialsError: Неверные учетные данные
            UserInactiveError: Пользователь неактивен
        """
        user = await self.user_repo.get_by_email(data.email)
        if not user or not verify_password(data.password, user.hashed_password):
            raise InvalidCredentialsError()

        if not user.is_active:
            raise UserInactiveError(str(user.id))

        tokens = await self._create_tokens_for_user(user.id, device_info)

        return UserResponse.model_validate(user), tokens

    async def refresh_tokens(
        self,
        refresh_token: str,
        device_info: str | None = None
    ) -> TokenResponse:
        """
        Обновление пары токенов по refresh токену.

        Args:
            refresh_token: Refresh токен
            device_info: Информация об устройстве

        Returns:
            TokenResponse с новой парой токенов

        Raises:
            InvalidTokenError: Невалидный токен
            RefreshTokenNotFoundError: Токен не найден или истек
        """
        try:
            payload = decode_refresh_token(refresh_token)
        except Exception:
            raise InvalidTokenError("Invalid or malformed refresh token")

        user_id = uuid.UUID(payload.get("sub"))
        token_hash = hash_refresh_token(refresh_token)

        db_token = await self.token_repo.get_by_token_hash(token_hash)
        if not db_token or db_token.user_id != user_id:
            raise RefreshTokenNotFoundError()

        if not await self.token_repo.is_token_valid(token_hash):
            raise RefreshTokenNotFoundError()

        await self.token_repo.revoke_token(token_hash)

        tokens = await self._create_tokens_for_user(user_id, device_info)

        return tokens

    async def logout(self, refresh_token: str) -> None:
        """
        Выход из системы (отзыв refresh токена).

        Args:
            refresh_token: Refresh токен для отзыва

        Raises:
            RefreshTokenNotFoundError: Невалидный токен
        """
        token_hash = hash_refresh_token(refresh_token)

        revoked = await self.token_repo.revoke_token(token_hash)
        if not revoked:
            raise RefreshTokenNotFoundError()

    async def logout_all_devices(self, user_id: uuid.UUID) -> int:
        """
        Выход из системы на всех устройствах (отзыв всех токенов пользователя).

        Args:
            user_id: UUID пользователя

        Returns:
            Количество отозванных токенов
        """
        count = await self.token_repo.revoke_all_user_tokens(user_id)
        return count

    async def change_password(
        self,
        user_id: uuid.UUID,
        old_password: str,
        new_password: str
    ) -> None:
        """
        Смена пароля пользователя.

        Args:
            user_id: UUID пользователя
            old_password: Старый пароль
            new_password: Новый пароль

        Raises:
            InvalidCredentialsError: Неверный старый пароль
            UserNotFoundError: Пользователь не найден
        """
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise UserNotFoundError(str(user_id))

        if not verify_password(old_password, user.hashed_password):
            raise InvalidCredentialsError()

        await self.user_repo.update(
            user_id,
            hashed_password=hash_password(new_password)
        )

        await self.token_repo.revoke_all_user_tokens(user_id)

    async def delete_user(self, user_id: uuid.UUID) -> None:
        """
        Удаление пользователя (soft delete).

        При удалении:
        - Отзываются все refresh токены (выход со всех устройств)
        - Пользователь помечается как удаленный (is_deleted=True)

        Args:
            user_id: UUID пользователя

        Raises:
            UserNotFoundError: Пользователь не найден
        """
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise UserNotFoundError(str(user_id))

        # Сначала отзываем все токены
        await self.token_repo.revoke_all_user_tokens(user_id)

        # Потом soft delete пользователя
        await self.user_repo.soft_delete(user_id)

    async def _create_tokens_for_user(
        self,
        user_id: uuid.UUID,
        device_info: str | None = None
    ) -> TokenResponse:
        """
        Внутренний метод создания пары токенов для пользователя.

        Args:
            user_id: UUID пользователя
            device_info: Информация об устройстве

        Returns:
            TokenResponse с access и refresh токенами
        """
        access_token = create_access_token(data={"sub": str(user_id)})

        refresh_token = create_refresh_token(data={"sub": str(user_id)})
        token_hash = hash_refresh_token(refresh_token)

        expires_at = datetime.now(timezone.utc) + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )

        db_token = RefreshToken(
            id=uuid.uuid4(),
            token_hash=token_hash,
            user_id=user_id,
            expires_at=expires_at,
            device_info=device_info,
        )

        await self.token_repo.create(db_token)

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer"
        )
