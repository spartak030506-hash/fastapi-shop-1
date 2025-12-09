"""
Integration тесты для Auth API endpoints.

Покрывает все сценарии:
- Регистрация (успех, дубликат, невалидные данные)
- Логин (успех, ошибки авторизации)
- Refresh tokens (успех, невалидный токен)
- Logout (один девайс, все девайсы)
"""
import pytest
from httpx import AsyncClient

from app.models.user import User


pytestmark = pytest.mark.integration


class TestRegister:
    """Тесты регистрации новых пользователей"""

    async def test_register_success(self, client: AsyncClient):
        """Успешная регистрация нового пользователя"""
        # Arrange
        payload = {
            "email": "newuser@example.com",
            "password": "SecurePass123!",
            "first_name": "New",
            "last_name": "User",
            "phone": "+1234567890",
        }

        # Act
        response = await client.post("/api/v1/auth/register", json=payload)

        # Assert
        assert response.status_code == 201
        data = response.json()

        # Проверяем структуру ответа
        assert "user" in data
        assert "tokens" in data

        # Проверяем данные пользователя
        user = data["user"]
        assert user["email"] == payload["email"]
        assert user["first_name"] == payload["first_name"]
        assert user["last_name"] == payload["last_name"]
        assert user["phone"] == payload["phone"]
        assert user["role"] == "customer"  # UserRole.CUSTOMER.value
        assert user["is_active"] is True
        assert user["is_verified"] is False
        assert "id" in user
        assert "created_at" in user

        # Проверяем токены
        tokens = data["tokens"]
        assert "access_token" in tokens
        assert "refresh_token" in tokens
        assert tokens["token_type"] == "bearer"

        # Пароль не должен возвращаться
        assert "password" not in user
        assert "hashed_password" not in user

    async def test_register_duplicate_email(
        self,
        client: AsyncClient,
        test_user: User,
    ):
        """Регистрация с уже существующим email возвращает 409 Conflict"""
        # Arrange
        payload = {
            "email": test_user.email,  # уже существует
            "password": "SecurePass123!",
            "first_name": "Another",
            "last_name": "User",
        }

        # Act
        response = await client.post("/api/v1/auth/register", json=payload)

        # Assert
        assert response.status_code == 409
        data = response.json()
        assert "detail" in data

    async def test_register_invalid_email(self, client: AsyncClient):
        """Регистрация с невалидным email возвращает 422"""
        # Arrange
        payload = {
            "email": "not-an-email",
            "password": "SecurePass123!",
            "first_name": "Test",
            "last_name": "User",
        }

        # Act
        response = await client.post("/api/v1/auth/register", json=payload)

        # Assert
        assert response.status_code == 422

    async def test_register_weak_password(self, client: AsyncClient):
        """Регистрация со слабым паролем возвращает 422"""
        # Arrange
        payload = {
            "email": "test@example.com",
            "password": "123",  # слишком короткий
            "first_name": "Test",
            "last_name": "User",
        }

        # Act
        response = await client.post("/api/v1/auth/register", json=payload)

        # Assert
        assert response.status_code == 422

    async def test_register_missing_required_fields(self, client: AsyncClient):
        """Регистрация без обязательных полей возвращает 422"""
        # Arrange
        payload = {
            "email": "test@example.com",
            # отсутствуют password, first_name, last_name
        }

        # Act
        response = await client.post("/api/v1/auth/register", json=payload)

        # Assert
        assert response.status_code == 422

    async def test_register_extra_fields_forbidden(self, client: AsyncClient):
        """Регистрация с лишними полями возвращает 422 (extra='forbid')"""
        # Arrange
        payload = {
            "email": "test@example.com",
            "password": "SecurePass123!",
            "first_name": "Test",
            "last_name": "User",
            "extra_field": "should not be here",  # лишнее поле
        }

        # Act
        response = await client.post("/api/v1/auth/register", json=payload)

        # Assert
        assert response.status_code == 422

    async def test_register_without_optional_phone(self, client: AsyncClient):
        """Регистрация без опционального поля phone работает"""
        # Arrange
        payload = {
            "email": "nophone@example.com",
            "password": "SecurePass123!",
            "first_name": "No",
            "last_name": "Phone",
            # phone не указан
        }

        # Act
        response = await client.post("/api/v1/auth/register", json=payload)

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["user"]["phone"] is None


class TestLogin:
    """Тесты входа в систему"""

    async def test_login_success(
        self,
        client: AsyncClient,
        test_user: User,
        test_password: str,
    ):
        """Успешный вход с правильными учётными данными"""
        # Arrange
        payload = {
            "email": test_user.email,
            "password": test_password,
        }

        # Act
        response = await client.post("/api/v1/auth/login", json=payload)

        # Assert
        assert response.status_code == 200
        data = response.json()

        # Проверяем структуру ответа
        assert "user" in data
        assert "tokens" in data

        # Проверяем данные пользователя
        user = data["user"]
        assert user["email"] == test_user.email
        assert user["id"] == str(test_user.id)

        # Проверяем токены
        tokens = data["tokens"]
        assert "access_token" in tokens
        assert "refresh_token" in tokens
        assert tokens["token_type"] == "bearer"

    async def test_login_wrong_password(
        self,
        client: AsyncClient,
        test_user: User,
    ):
        """Вход с неправильным паролем возвращает 401"""
        # Arrange
        payload = {
            "email": test_user.email,
            "password": "WrongPassword123!",
        }

        # Act
        response = await client.post("/api/v1/auth/login", json=payload)

        # Assert
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data

    async def test_login_nonexistent_user(self, client: AsyncClient):
        """Вход с несуществующим email возвращает 401"""
        # Arrange
        payload = {
            "email": "nonexistent@example.com",
            "password": "SomePassword123!",
        }

        # Act
        response = await client.post("/api/v1/auth/login", json=payload)

        # Assert
        assert response.status_code == 401

    async def test_login_inactive_user(
        self,
        client: AsyncClient,
        test_inactive_user: User,
        test_password: str,
    ):
        """Вход неактивного пользователя возвращает 403"""
        # Arrange
        payload = {
            "email": test_inactive_user.email,
            "password": test_password,
        }

        # Act
        response = await client.post("/api/v1/auth/login", json=payload)

        # Assert
        assert response.status_code == 403
        data = response.json()
        assert "detail" in data

    async def test_login_deleted_user(
        self,
        client: AsyncClient,
        test_user: User,
        test_password: str,
        db_session,
    ):
        """Вход удалённого пользователя (soft delete) возвращает 401"""
        # Arrange
        test_user.is_deleted = True
        await db_session.commit()

        payload = {
            "email": test_user.email,
            "password": test_password,
        }

        # Act
        response = await client.post("/api/v1/auth/login", json=payload)

        # Assert
        # Репозиторий фильтрует is_deleted=False, поэтому возвращает None
        # Это обрабатывается как InvalidCredentials (401), а не User not found (404)
        assert response.status_code == 401

    async def test_login_invalid_email_format(self, client: AsyncClient):
        """Вход с невалидным форматом email возвращает 422"""
        # Arrange
        payload = {
            "email": "not-an-email",
            "password": "SomePassword123!",
        }

        # Act
        response = await client.post("/api/v1/auth/login", json=payload)

        # Assert
        assert response.status_code == 422


class TestRefreshTokens:
    """Тесты обновления токенов"""

    async def test_refresh_tokens_success(
        self,
        client: AsyncClient,
        test_user: User,
        test_password: str,
    ):
        """Успешное обновление токенов с валидным refresh token"""
        # Arrange - сначала логинимся для получения refresh token
        login_response = await client.post(
            "/api/v1/auth/login",
            json={"email": test_user.email, "password": test_password},
        )
        old_refresh_token = login_response.json()["tokens"]["refresh_token"]

        # Act - обновляем токены
        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": old_refresh_token},
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

        # Новый refresh token должен отличаться от старого (token rotation)
        assert data["refresh_token"] != old_refresh_token

    async def test_refresh_tokens_invalid_token(self, client: AsyncClient):
        """Обновление с невалидным refresh token возвращает 401"""
        # Arrange
        payload = {"refresh_token": "invalid.refresh.token"}

        # Act
        response = await client.post("/api/v1/auth/refresh", json=payload)

        # Assert
        assert response.status_code == 401

    async def test_refresh_tokens_reuse_old_token(
        self,
        client: AsyncClient,
        test_user: User,
        test_password: str,
    ):
        """Попытка повторного использования старого refresh token возвращает 401"""
        # Arrange - логинимся и обновляем токены
        login_response = await client.post(
            "/api/v1/auth/login",
            json={"email": test_user.email, "password": test_password},
        )
        old_refresh_token = login_response.json()["tokens"]["refresh_token"]

        # Обновляем токены первый раз
        await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": old_refresh_token},
        )

        # Act - пытаемся использовать старый токен повторно
        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": old_refresh_token},
        )

        # Assert - старый токен должен быть отозван
        assert response.status_code == 401


class TestLogout:
    """Тесты выхода из системы"""

    async def test_logout_success(
        self,
        client: AsyncClient,
        test_user: User,
        test_password: str,
        auth_headers,
    ):
        """Успешный выход с валидным refresh token"""
        # Arrange - логинимся для получения refresh token
        login_response = await client.post(
            "/api/v1/auth/login",
            json={"email": test_user.email, "password": test_password},
        )
        refresh_token = login_response.json()["tokens"]["refresh_token"]
        headers = auth_headers(test_user)

        # Act
        response = await client.post(
            "/api/v1/auth/logout",
            headers=headers,
            json={"refresh_token": refresh_token},
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "message" in data

    async def test_logout_with_revoked_token(
        self,
        client: AsyncClient,
        test_user: User,
        test_password: str,
        auth_headers,
    ):
        """Выход с уже отозванным токеном возвращает 401"""
        # Arrange
        login_response = await client.post(
            "/api/v1/auth/login",
            json={"email": test_user.email, "password": test_password},
        )
        refresh_token = login_response.json()["tokens"]["refresh_token"]
        headers = auth_headers(test_user)

        # Выходим первый раз
        await client.post(
            "/api/v1/auth/logout",
            headers=headers,
            json={"refresh_token": refresh_token},
        )

        # Act - пытаемся выйти повторно с тем же токеном
        response = await client.post(
            "/api/v1/auth/logout",
            headers=headers,
            json={"refresh_token": refresh_token},
        )

        # Assert
        assert response.status_code == 401

    async def test_logout_invalid_token(
        self,
        client: AsyncClient,
        test_user: User,
        auth_headers,
    ):
        """Выход с невалидным refresh токеном возвращает 401"""
        # Arrange
        headers = auth_headers(test_user)
        payload = {"refresh_token": "invalid.token.here"}

        # Act
        response = await client.post(
            "/api/v1/auth/logout",
            headers=headers,
            json=payload,
        )

        # Assert
        assert response.status_code == 401

    async def test_logout_requires_auth(self, client: AsyncClient):
        """Выход без авторизации возвращает 403"""
        # Arrange
        payload = {"refresh_token": "some.token.here"}

        # Act - запрос без Bearer token
        response = await client.post("/api/v1/auth/logout", json=payload)

        # Assert
        # HTTPBearer возвращает 403 когда токена нет вообще
        assert response.status_code == 403


class TestLogoutAllDevices:
    """Тесты выхода на всех устройствах"""

    async def test_logout_all_devices_success(
        self,
        client: AsyncClient,
        test_user: User,
        test_password: str,
        auth_headers,
    ):
        """Успешный выход на всех устройствах"""
        # Arrange - создаём несколько refresh токенов (эмулируем несколько устройств)
        device_tokens = []
        for _ in range(3):
            login_response = await client.post(
                "/api/v1/auth/login",
                json={"email": test_user.email, "password": test_password},
            )
            device_tokens.append(
                login_response.json()["tokens"]["refresh_token"]
            )

        headers = auth_headers(test_user)

        # Act
        response = await client.post(
            "/api/v1/auth/logout-all",
            headers=headers,
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "3" in data["message"] or data["message"].endswith("device(s)")

        # Verify: все токены должны быть отозваны
        for token in device_tokens:
            refresh_response = await client.post(
                "/api/v1/auth/refresh",
                json={"refresh_token": token},
            )
            assert refresh_response.status_code == 401

    async def test_logout_all_devices_requires_auth(self, client: AsyncClient):
        """Выход на всех устройствах требует авторизации"""
        # Act - запрос без токена
        response = await client.post("/api/v1/auth/logout-all")

        # Assert
        # HTTPBearer возвращает 403 когда токена нет вообще
        assert response.status_code == 403

    async def test_logout_all_devices_inactive_user(
        self,
        client: AsyncClient,
        test_inactive_user: User,
        auth_headers,
    ):
        """Выход на всех устройствах неактивного пользователя возвращает 403"""
        # Arrange
        headers = auth_headers(test_inactive_user)

        # Act
        response = await client.post(
            "/api/v1/auth/logout-all",
            headers=headers,
        )

        # Assert
        assert response.status_code == 403
