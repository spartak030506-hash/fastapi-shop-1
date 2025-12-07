import uuid
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
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
from app.models.user import User
from app.models.refresh_token import RefreshToken
from app.repositories.user import UserRepository
from app.repositories.refresh_token import RefreshTokenRepository
from app.schemas.auth import RegisterRequest, LoginRequest, TokenResponse
from app.schemas.user import UserResponse


class AuthService:
    """
    Сервис аутентификации и авторизации.

    Содержит бизнес-логику для:
    - Регистрации пользователей
    - Входа в систему (login)
    - Обновления токенов (refresh)
    - Выхода из системы (logout)
    - Смены пароля
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
            HTTPException 400: Email уже существует
        """
        if await self.user_repo.email_exists(data.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

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
            HTTPException 401: Неверные учетные данные
            HTTPException 403: Пользователь неактивен
        """
        user = await self.user_repo.get_by_email(data.email)
        if not user or not verify_password(data.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password"
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is inactive"
            )

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
            HTTPException 401: Невалидный или истекший токен
        """
        try:
            payload = decode_refresh_token(refresh_token)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )

        user_id = uuid.UUID(payload.get("sub"))
        token_hash = hash_refresh_token(refresh_token)

        db_token = await self.token_repo.get_by_token_hash(token_hash)
        if not db_token or db_token.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )

        if not await self.token_repo.is_token_valid(token_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token expired or revoked"
            )

        await self.token_repo.revoke_token(token_hash)

        tokens = await self._create_tokens_for_user(user_id, device_info)

        return tokens

    async def logout(self, refresh_token: str) -> None:
        """
        Выход из системы (отзыв refresh токена).

        Args:
            refresh_token: Refresh токен для отзыва

        Raises:
            HTTPException 401: Невалидный токен
        """
        token_hash = hash_refresh_token(refresh_token)

        revoked = await self.token_repo.revoke_token(token_hash)
        if not revoked:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )

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
            HTTPException 401: Неверный старый пароль
            HTTPException 404: Пользователь не найден
        """
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        if not verify_password(old_password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect old password"
            )

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
            HTTPException 404: Пользователь не найден
        """
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Сначала отзываем все токены
        await self.token_repo.revoke_all_user_tokens(user_id)

        # Потом soft delete пользователя
        deleted = await self.user_repo.soft_delete(user_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete user"
            )

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
