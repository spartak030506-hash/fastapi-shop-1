"""
Интеграционные тесты для AuthService.

Покрывает все методы сервиса:
- register: регистрация пользователей
- login: вход в систему
- refresh_tokens: обновление токенов
- logout: выход с одного устройства
- logout_all_devices: выход со всех устройств
- change_password: смена пароля
- delete_user: удаление пользователя
"""

import uuid

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    EmailAlreadyExistsError,
    InvalidCredentialsError,
    UserInactiveError,
    UserNotFoundError,
    InvalidTokenError,
    RefreshTokenNotFoundError,
)
from app.core.security import hash_refresh_token
from app.models.user import User as UserModel
from app.repositories.refresh_token import RefreshTokenRepository
from app.repositories.user import UserRepository
from app.schemas.auth import RegisterRequest, LoginRequest
from app.services.auth_service import AuthService


@pytest.mark.integration
class TestAuthServiceRegister:
    """Тесты для метода register"""

    async def test_register_success(self, db_session: AsyncSession):
        """Успешная регистрация нового пользователя"""
        service = AuthService(db_session)

        data = RegisterRequest(
            email="newuser@example.com",
            password="NewPassword123",
            first_name="New",
            last_name="User",
            phone="+1234567890",
        )

        user_response, tokens = await service.register(data, device_info="Test Device")

        # Проверяем UserResponse
        assert user_response.email == data.email
        assert user_response.first_name == data.first_name
        assert user_response.last_name == data.last_name
        assert user_response.phone == data.phone
        assert user_response.is_active is True
        assert user_response.is_verified is False

        # Проверяем TokenResponse
        assert tokens.access_token is not None
        assert tokens.refresh_token is not None
        assert tokens.token_type == "bearer"

        # Проверяем, что пользователь создан в БД
        user_repo = UserRepository(db_session)
        db_user = await user_repo.get_by_email(data.email)
        assert db_user is not None
        assert db_user.email == data.email

        # Проверяем, что refresh токен создан в БД
        token_repo = RefreshTokenRepository(db_session)
        token_hash = hash_refresh_token(tokens.refresh_token)
        db_token = await token_repo.get_by_token_hash(token_hash)
        assert db_token is not None
        assert db_token.user_id == db_user.id
        assert db_token.device_info == "Test Device"

    async def test_register_duplicate_email(
        self, db_session: AsyncSession, test_user: UserModel
    ):
        """Регистрация с уже существующим email - выбрасывает EmailAlreadyExistsError"""
        service = AuthService(db_session)

        data = RegisterRequest(
            email=test_user.email,  # Дубликат
            password="NewPassword123",
            first_name="Another",
            last_name="User",
        )

        with pytest.raises(EmailAlreadyExistsError) as exc_info:
            await service.register(data)

        assert exc_info.value.details["email"] == test_user.email

    async def test_register_without_device_info(self, db_session: AsyncSession):
        """Регистрация без указания device_info - должно работать"""
        service = AuthService(db_session)

        data = RegisterRequest(
            email="nodevice@example.com",
            password="Password123",
            first_name="No",
            last_name="Device",
        )

        user_response, tokens = await service.register(data, device_info=None)

        assert user_response.email == data.email
        assert tokens.refresh_token is not None

        # Проверяем, что device_info = None в БД
        token_repo = RefreshTokenRepository(db_session)
        token_hash = hash_refresh_token(tokens.refresh_token)
        db_token = await token_repo.get_by_token_hash(token_hash)
        assert db_token.device_info is None

    async def test_register_without_optional_fields(self, db_session: AsyncSession):
        """Регистрация без опциональных полей (phone)"""
        service = AuthService(db_session)

        data = RegisterRequest(
            email="minimal@example.com",
            password="Password123",
            first_name="Minimal",
            last_name="User",
            # phone отсутствует
        )

        user_response, tokens = await service.register(data)

        assert user_response.email == data.email
        assert user_response.phone is None
        assert tokens.access_token is not None


@pytest.mark.integration
class TestAuthServiceLogin:
    """Тесты для метода login"""

    async def test_login_success(
        self, db_session: AsyncSession, test_user: UserModel, test_password: str
    ):
        """Успешный вход в систему"""
        service = AuthService(db_session)

        data = LoginRequest(email=test_user.email, password=test_password)

        user_response, tokens = await service.login(data, device_info="Browser")

        # Проверяем UserResponse
        assert user_response.id == test_user.id
        assert user_response.email == test_user.email

        # Проверяем TokenResponse
        assert tokens.access_token is not None
        assert tokens.refresh_token is not None
        assert tokens.token_type == "bearer"

        # Проверяем, что refresh токен создан в БД
        token_repo = RefreshTokenRepository(db_session)
        token_hash = hash_refresh_token(tokens.refresh_token)
        db_token = await token_repo.get_by_token_hash(token_hash)
        assert db_token is not None
        assert db_token.user_id == test_user.id
        assert db_token.device_info == "Browser"

    async def test_login_invalid_email(self, db_session: AsyncSession):
        """Вход с несуществующим email - выбрасывает InvalidCredentialsError"""
        service = AuthService(db_session)

        data = LoginRequest(email="nonexistent@example.com", password="Password123")

        with pytest.raises(InvalidCredentialsError):
            await service.login(data)

    async def test_login_invalid_password(
        self, db_session: AsyncSession, test_user: UserModel
    ):
        """Вход с неверным паролем - выбрасывает InvalidCredentialsError"""
        service = AuthService(db_session)

        data = LoginRequest(email=test_user.email, password="WrongPassword123")

        with pytest.raises(InvalidCredentialsError):
            await service.login(data)

    async def test_login_inactive_user(
        self, db_session: AsyncSession, test_inactive_user: UserModel, test_password: str
    ):
        """Вход неактивного пользователя - выбрасывает UserInactiveError"""
        service = AuthService(db_session)

        data = LoginRequest(email=test_inactive_user.email, password=test_password)

        with pytest.raises(UserInactiveError) as exc_info:
            await service.login(data)

        assert exc_info.value.details["user_id"] == str(test_inactive_user.id)

    async def test_login_creates_new_token_on_each_login(
        self, db_session: AsyncSession, test_user: UserModel, test_password: str
    ):
        """Каждый login создаёт новый токен (можно войти с нескольких устройств)"""
        service = AuthService(db_session)

        data = LoginRequest(email=test_user.email, password=test_password)

        # Первый вход
        _, tokens1 = await service.login(data, device_info="Device1")

        # Второй вход
        _, tokens2 = await service.login(data, device_info="Device2")

        # Токены разные
        assert tokens1.refresh_token != tokens2.refresh_token
        assert tokens1.access_token != tokens2.access_token

        # Оба токена валидны в БД
        token_repo = RefreshTokenRepository(db_session)
        hash1 = hash_refresh_token(tokens1.refresh_token)
        hash2 = hash_refresh_token(tokens2.refresh_token)

        assert await token_repo.is_token_valid(hash1) is True
        assert await token_repo.is_token_valid(hash2) is True


@pytest.mark.integration
class TestAuthServiceRefreshTokens:
    """Тесты для метода refresh_tokens"""

    async def test_refresh_tokens_success(
        self, db_session: AsyncSession, test_user: UserModel, test_password: str
    ):
        """Успешное обновление токенов"""
        service = AuthService(db_session)

        # Сначала логинимся, чтобы получить refresh токен
        login_data = LoginRequest(email=test_user.email, password=test_password)
        _, old_tokens = await service.login(login_data, device_info="Device1")

        # Обновляем токены
        new_tokens = await service.refresh_tokens(
            old_tokens.refresh_token, device_info="Device1"
        )

        # Проверяем, что получили новые токены
        assert new_tokens.access_token is not None
        assert new_tokens.refresh_token is not None
        assert new_tokens.access_token != old_tokens.access_token
        assert new_tokens.refresh_token != old_tokens.refresh_token

        # Проверяем, что старый токен отозван
        token_repo = RefreshTokenRepository(db_session)
        old_token_hash = hash_refresh_token(old_tokens.refresh_token)
        is_valid = await token_repo.is_token_valid(old_token_hash)
        assert is_valid is False

        # Проверяем, что новый токен валиден
        new_token_hash = hash_refresh_token(new_tokens.refresh_token)
        is_valid = await token_repo.is_token_valid(new_token_hash)
        assert is_valid is True

    async def test_refresh_tokens_invalid_token(self, db_session: AsyncSession):
        """Обновление с невалидным токеном - выбрасывает InvalidTokenError"""
        service = AuthService(db_session)

        with pytest.raises(InvalidTokenError):
            await service.refresh_tokens("invalid-token-string")

    async def test_refresh_tokens_missing_sub(
        self, db_session: AsyncSession, test_user: UserModel, test_password: str
    ):
        """Токен без поля 'sub' - выбрасывает InvalidTokenError"""
        service = AuthService(db_session)

        # Создаём токен без поля sub
        from app.core.security import create_refresh_token

        # Передаём пустой payload (без sub)
        token_without_sub = create_refresh_token(data={"some_field": "value"})

        with pytest.raises(InvalidTokenError) as exc_info:
            await service.refresh_tokens(token_without_sub)

        assert "missing or invalid 'sub' field" in str(exc_info.value.message).lower()

    async def test_refresh_tokens_null_sub(
        self, db_session: AsyncSession
    ):
        """Токен с sub=None - выбрасывает InvalidTokenError"""
        service = AuthService(db_session)

        # Создаём токен с sub=None
        from app.core.security import create_refresh_token

        token_with_null_sub = create_refresh_token(data={"sub": None})

        with pytest.raises(InvalidTokenError) as exc_info:
            await service.refresh_tokens(token_with_null_sub)

        # JWT библиотека сама валидирует sub и выбрасывает ошибку
        assert "subject must be a string" in str(exc_info.value.message).lower()

    async def test_refresh_tokens_invalid_uuid_format(
        self, db_session: AsyncSession
    ):
        """Токен с sub не в формате UUID - выбрасывает InvalidTokenError"""
        service = AuthService(db_session)

        # Создаём токен с невалидным UUID в sub
        from app.core.security import create_refresh_token

        token_with_invalid_uuid = create_refresh_token(data={"sub": "not-a-valid-uuid"})

        with pytest.raises(InvalidTokenError) as exc_info:
            await service.refresh_tokens(token_with_invalid_uuid)

        assert "invalid user id format" in str(exc_info.value.message).lower()

    async def test_refresh_tokens_integer_sub(
        self, db_session: AsyncSession
    ):
        """Токен с sub=integer (не строка) - выбрасывает InvalidTokenError"""
        service = AuthService(db_session)

        # Создаём токен с sub=123 (число вместо строки)
        from app.core.security import create_refresh_token

        token_with_int_sub = create_refresh_token(data={"sub": 12345})

        with pytest.raises(InvalidTokenError) as exc_info:
            await service.refresh_tokens(token_with_int_sub)

        # JWT библиотека сама валидирует sub и выбрасывает ошибку
        assert "subject must be a string" in str(exc_info.value.message).lower()

    async def test_refresh_tokens_inactive_user(
        self, db_session: AsyncSession, test_inactive_user: UserModel, test_password: str
    ):
        """Неактивный пользователь не может обновить токены - выбрасывает UserInactiveError"""
        service = AuthService(db_session)

        # Активируем пользователя временно, чтобы залогиниться
        user_repo = UserRepository(db_session)
        await user_repo.update(test_inactive_user.id, is_active=True)

        # Логинимся
        login_data = LoginRequest(email=test_inactive_user.email, password=test_password)
        _, tokens = await service.login(login_data)

        # Деактивируем пользователя
        await user_repo.update(test_inactive_user.id, is_active=False)

        # Пытаемся обновить токены - должна быть ошибка
        with pytest.raises(UserInactiveError) as exc_info:
            await service.refresh_tokens(tokens.refresh_token)

        assert exc_info.value.details["user_id"] == str(test_inactive_user.id)

    async def test_refresh_tokens_deleted_user(
        self, db_session: AsyncSession, test_user: UserModel, test_password: str
    ):
        """Удалённый пользователь не может обновить токены - выбрасывает UserNotFoundError"""
        service = AuthService(db_session)

        # Логинимся
        login_data = LoginRequest(email=test_user.email, password=test_password)
        _, tokens = await service.login(login_data)

        # Удаляем пользователя (soft delete)
        user_repo = UserRepository(db_session)
        await user_repo.soft_delete(test_user.id)

        # Пытаемся обновить токены - должна быть ошибка
        with pytest.raises(UserNotFoundError) as exc_info:
            await service.refresh_tokens(tokens.refresh_token)

        assert exc_info.value.details["user_id"] == str(test_user.id)

    async def test_refresh_tokens_not_found_in_db(
        self, db_session: AsyncSession, test_user: UserModel
    ):
        """Обновление с токеном, которого нет в БД - выбрасывает RefreshTokenNotFoundError"""
        service = AuthService(db_session)

        # Создаём валидный refresh токен, но не сохраняем в БД
        from app.core.security import create_refresh_token

        fake_token = create_refresh_token(data={"sub": str(test_user.id)})

        with pytest.raises(RefreshTokenNotFoundError):
            await service.refresh_tokens(fake_token)

    async def test_refresh_tokens_user_mismatch(
        self, db_session: AsyncSession, test_user: UserModel, test_admin: UserModel, test_password: str
    ):
        """Обновление с токеном другого пользователя - выбрасывает RefreshTokenNotFoundError"""
        service = AuthService(db_session)

        # Логинимся как test_user
        login_data = LoginRequest(email=test_user.email, password=test_password)
        _, tokens = await service.login(login_data)

        # Создаём токен с admin ID, но используем хеш от токена test_user
        from app.core.security import create_refresh_token

        fake_token = create_refresh_token(data={"sub": str(test_admin.id)})

        # Токен валидный по структуре, но user_id не совпадает с записью в БД
        with pytest.raises(RefreshTokenNotFoundError):
            await service.refresh_tokens(fake_token)

    async def test_refresh_tokens_already_used(
        self, db_session: AsyncSession, test_user: UserModel, test_password: str
    ):
        """Попытка использовать уже использованный refresh токен - ошибка"""
        service = AuthService(db_session)

        # Логинимся
        login_data = LoginRequest(email=test_user.email, password=test_password)
        _, old_tokens = await service.login(login_data)

        # Первое обновление - успех
        await service.refresh_tokens(old_tokens.refresh_token)

        # Второе обновление с тем же токеном - ошибка (токен уже отозван)
        with pytest.raises(RefreshTokenNotFoundError):
            await service.refresh_tokens(old_tokens.refresh_token)


@pytest.mark.integration
class TestAuthServiceLogout:
    """Тесты для методов logout и logout_all_devices"""

    async def test_logout_success(
        self, db_session: AsyncSession, test_user: UserModel, test_password: str
    ):
        """Успешный выход из системы"""
        service = AuthService(db_session)

        # Логинимся
        login_data = LoginRequest(email=test_user.email, password=test_password)
        _, tokens = await service.login(login_data)

        # Проверяем, что токен валиден
        token_repo = RefreshTokenRepository(db_session)
        token_hash = hash_refresh_token(tokens.refresh_token)
        is_valid = await token_repo.is_token_valid(token_hash)
        assert is_valid is True

        # Выходим
        await service.logout(tokens.refresh_token)

        # Проверяем, что токен отозван
        is_valid = await token_repo.is_token_valid(token_hash)
        assert is_valid is False

    async def test_logout_invalid_token(self, db_session: AsyncSession):
        """Выход с невалидным токеном - выбрасывает RefreshTokenNotFoundError"""
        service = AuthService(db_session)

        with pytest.raises(RefreshTokenNotFoundError):
            await service.logout("non-existent-token")

    async def test_logout_does_not_affect_other_devices(
        self, db_session: AsyncSession, test_user: UserModel, test_password: str
    ):
        """Logout отзывает только один токен, не затрагивая другие устройства"""
        service = AuthService(db_session)

        # Логинимся с двух устройств
        login_data = LoginRequest(email=test_user.email, password=test_password)

        _, tokens1 = await service.login(login_data, device_info="Device1")
        _, tokens2 = await service.login(login_data, device_info="Device2")

        # Выходим с Device1
        await service.logout(tokens1.refresh_token)

        # Device1 токен отозван
        token_repo = RefreshTokenRepository(db_session)
        hash1 = hash_refresh_token(tokens1.refresh_token)
        assert await token_repo.is_token_valid(hash1) is False

        # Device2 токен всё ещё валиден
        hash2 = hash_refresh_token(tokens2.refresh_token)
        assert await token_repo.is_token_valid(hash2) is True

    async def test_logout_all_devices(
        self, db_session: AsyncSession, test_user: UserModel, test_password: str
    ):
        """Выход со всех устройств отзывает все токены пользователя"""
        service = AuthService(db_session)

        # Логинимся с нескольких устройств
        login_data = LoginRequest(email=test_user.email, password=test_password)

        _, tokens1 = await service.login(login_data, device_info="Device1")
        _, tokens2 = await service.login(login_data, device_info="Device2")
        _, tokens3 = await service.login(login_data, device_info="Device3")

        # Проверяем, что все токены валидны
        token_repo = RefreshTokenRepository(db_session)
        for token in [tokens1.refresh_token, tokens2.refresh_token, tokens3.refresh_token]:
            token_hash = hash_refresh_token(token)
            is_valid = await token_repo.is_token_valid(token_hash)
            assert is_valid is True

        # Выходим со всех устройств
        count = await service.logout_all_devices(test_user.id)
        assert count == 3

        # Проверяем, что все токены отозваны
        for token in [tokens1.refresh_token, tokens2.refresh_token, tokens3.refresh_token]:
            token_hash = hash_refresh_token(token)
            is_valid = await token_repo.is_token_valid(token_hash)
            assert is_valid is False

    async def test_logout_all_devices_returns_zero_if_no_tokens(
        self, db_session: AsyncSession, test_user: UserModel
    ):
        """logout_all_devices возвращает 0, если нет активных токенов"""
        service = AuthService(db_session)

        count = await service.logout_all_devices(test_user.id)
        assert count == 0


@pytest.mark.integration
class TestAuthServiceChangePassword:
    """Тесты для метода change_password"""

    async def test_change_password_success(
        self, db_session: AsyncSession, test_user: UserModel, test_password: str
    ):
        """Успешная смена пароля"""
        service = AuthService(db_session)

        # Логинимся и получаем токены
        login_data = LoginRequest(email=test_user.email, password=test_password)
        _, tokens = await service.login(login_data, device_info="Device1")

        # Меняем пароль
        new_password = "NewSecurePassword123"
        await service.change_password(test_user.id, test_password, new_password)

        # Проверяем, что старые токены отозваны
        token_repo = RefreshTokenRepository(db_session)
        token_hash = hash_refresh_token(tokens.refresh_token)
        is_valid = await token_repo.is_token_valid(token_hash)
        assert is_valid is False

        # Проверяем, что можем войти с новым паролем
        new_login_data = LoginRequest(email=test_user.email, password=new_password)
        user_response, new_tokens = await service.login(new_login_data)
        assert user_response.id == test_user.id
        assert new_tokens.access_token is not None

        # Проверяем, что со старым паролем войти нельзя
        with pytest.raises(InvalidCredentialsError):
            await service.login(login_data)

    async def test_change_password_wrong_old_password(
        self, db_session: AsyncSession, test_user: UserModel
    ):
        """Смена пароля с неверным старым паролем - выбрасывает InvalidCredentialsError"""
        service = AuthService(db_session)

        with pytest.raises(InvalidCredentialsError):
            await service.change_password(
                test_user.id, "WrongOldPassword123", "NewPassword123"
            )

    async def test_change_password_user_not_found(self, db_session: AsyncSession):
        """Смена пароля несуществующего пользователя - выбрасывает UserNotFoundError"""
        service = AuthService(db_session)

        fake_user_id = uuid.uuid4()

        with pytest.raises(UserNotFoundError) as exc_info:
            await service.change_password(
                fake_user_id, "OldPassword123", "NewPassword123"
            )

        assert exc_info.value.details["user_id"] == str(fake_user_id)

    async def test_change_password_revokes_all_tokens(
        self, db_session: AsyncSession, test_user: UserModel, test_password: str
    ):
        """Смена пароля отзывает все токены со всех устройств"""
        service = AuthService(db_session)

        # Логинимся с нескольких устройств
        login_data = LoginRequest(email=test_user.email, password=test_password)
        _, tokens1 = await service.login(login_data, device_info="Device1")
        _, tokens2 = await service.login(login_data, device_info="Device2")

        # Меняем пароль
        await service.change_password(test_user.id, test_password, "NewPassword123")

        # Проверяем, что все токены отозваны
        token_repo = RefreshTokenRepository(db_session)
        for token in [tokens1.refresh_token, tokens2.refresh_token]:
            token_hash = hash_refresh_token(token)
            is_valid = await token_repo.is_token_valid(token_hash)
            assert is_valid is False


@pytest.mark.integration
class TestAuthServiceDeleteUser:
    """Тесты для метода delete_user"""

    async def test_delete_user_success(
        self, db_session: AsyncSession, test_user: UserModel, test_password: str
    ):
        """Успешное удаление пользователя (soft delete)"""
        service = AuthService(db_session)

        # Логинимся, чтобы создать токены
        login_data = LoginRequest(email=test_user.email, password=test_password)
        _, tokens = await service.login(login_data, device_info="Device1")

        # Удаляем пользователя
        await service.delete_user(test_user.id)

        # Проверяем, что пользователь помечен как удаленный (не возвращается через repo)
        user_repo = UserRepository(db_session)
        deleted_user = await user_repo.get_by_id(test_user.id)
        assert deleted_user is None  # Soft delete - не возвращается через get_by_id

        # Проверяем напрямую в БД (обходим soft delete фильтр)
        result = await db_session.execute(
            select(UserModel).where(UserModel.id == test_user.id)
        )
        db_user = result.scalar_one_or_none()
        assert db_user is not None
        assert db_user.is_deleted is True

        # Проверяем, что токены отозваны
        token_repo = RefreshTokenRepository(db_session)
        token_hash = hash_refresh_token(tokens.refresh_token)
        is_valid = await token_repo.is_token_valid(token_hash)
        assert is_valid is False

    async def test_delete_user_not_found(self, db_session: AsyncSession):
        """Удаление несуществующего пользователя - выбрасывает UserNotFoundError"""
        service = AuthService(db_session)

        fake_user_id = uuid.uuid4()

        with pytest.raises(UserNotFoundError) as exc_info:
            await service.delete_user(fake_user_id)

        assert exc_info.value.details["user_id"] == str(fake_user_id)

    async def test_delete_user_revokes_multiple_tokens(
        self, db_session: AsyncSession, test_user: UserModel, test_password: str
    ):
        """Удаление пользователя отзывает все токены со всех устройств"""
        service = AuthService(db_session)

        # Логинимся с нескольких устройств
        login_data = LoginRequest(email=test_user.email, password=test_password)
        _, tokens1 = await service.login(login_data, device_info="Device1")
        _, tokens2 = await service.login(login_data, device_info="Device2")
        _, tokens3 = await service.login(login_data, device_info="Device3")

        # Удаляем пользователя
        await service.delete_user(test_user.id)

        # Проверяем, что все токены отозваны
        token_repo = RefreshTokenRepository(db_session)
        for token in [tokens1.refresh_token, tokens2.refresh_token, tokens3.refresh_token]:
            token_hash = hash_refresh_token(token)
            is_valid = await token_repo.is_token_valid(token_hash)
            assert is_valid is False

    async def test_delete_user_cannot_login_after_deletion(
        self, db_session: AsyncSession, test_user: UserModel, test_password: str
    ):
        """После удаления пользователь не может войти в систему"""
        service = AuthService(db_session)

        # Удаляем пользователя
        await service.delete_user(test_user.id)

        # Пытаемся войти
        login_data = LoginRequest(email=test_user.email, password=test_password)

        with pytest.raises(InvalidCredentialsError):
            await service.login(login_data)
