"""
Integration тесты для Users API endpoints.

Покрывает все сценарии:
- /users/me endpoints (профиль, обновление, смена пароля, удаление)
- Admin endpoints (получение пользователей, удаление)
- Проверка авторизации и прав доступа
"""
import pytest
from httpx import AsyncClient

from app.models.user import User


pytestmark = pytest.mark.integration


class TestGetMyProfile:
    """Тесты получения своего профиля"""

    async def test_get_my_profile_success(
        self,
        client: AsyncClient,
        test_user: User,
        auth_headers,
    ):
        """Получение своего профиля с валидным токеном"""
        # Arrange
        headers = auth_headers(test_user)

        # Act
        response = await client.get("/api/v1/users/me", headers=headers)

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["id"] == str(test_user.id)
        assert data["email"] == test_user.email
        assert data["first_name"] == test_user.first_name
        assert data["last_name"] == test_user.last_name
        assert data["phone"] == test_user.phone
        assert data["role"] == test_user.role.value
        assert data["is_active"] is True

        # Пароль не должен возвращаться
        assert "password" not in data
        assert "hashed_password" not in data

    async def test_get_my_profile_requires_auth(self, client: AsyncClient):
        """Получение профиля без авторизации возвращает 403"""
        # Act - запрос без токена
        response = await client.get("/api/v1/users/me")

        # Assert
        # HTTPBearer возвращает 403 когда токена нет вообще
        assert response.status_code == 403

    async def test_get_my_profile_invalid_token(self, client: AsyncClient):
        """Получение профиля с невалидным токеном возвращает 401"""
        # Arrange
        headers = {"Authorization": "Bearer invalid.token.here"}

        # Act
        response = await client.get("/api/v1/users/me", headers=headers)

        # Assert
        assert response.status_code == 401

    async def test_get_my_profile_inactive_user(
        self,
        client: AsyncClient,
        test_inactive_user: User,
        auth_headers,
    ):
        """Получение профиля неактивного пользователя возвращает 403"""
        # Arrange
        headers = auth_headers(test_inactive_user)

        # Act
        response = await client.get("/api/v1/users/me", headers=headers)

        # Assert
        assert response.status_code == 403


class TestUpdateMyProfile:
    """Тесты обновления своего профиля"""

    async def test_update_profile_success(
        self,
        client: AsyncClient,
        test_user: User,
        auth_headers,
    ):
        """Успешное обновление профиля"""
        # Arrange
        headers = auth_headers(test_user)
        payload = {
            "first_name": "Updated",
            "last_name": "Name",
            "phone": "+9999999999",
        }

        # Act
        response = await client.patch(
            "/api/v1/users/me",
            headers=headers,
            json=payload,
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["first_name"] == payload["first_name"]
        assert data["last_name"] == payload["last_name"]
        assert data["phone"] == payload["phone"]
        assert data["id"] == str(test_user.id)
        assert data["email"] == test_user.email  # email не изменился

    async def test_update_profile_partial(
        self,
        client: AsyncClient,
        test_user: User,
        auth_headers,
    ):
        """Частичное обновление профиля (только одно поле)"""
        # Arrange
        headers = auth_headers(test_user)
        payload = {"first_name": "NewFirstName"}

        # Act
        response = await client.patch(
            "/api/v1/users/me",
            headers=headers,
            json=payload,
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["first_name"] == payload["first_name"]
        # Остальные поля не изменились
        assert data["last_name"] == test_user.last_name
        assert data["phone"] == test_user.phone

    async def test_update_profile_requires_auth(self, client: AsyncClient):
        """Обновление профиля без авторизации возвращает 403"""
        # Arrange
        payload = {"first_name": "New"}

        # Act
        response = await client.patch("/api/v1/users/me", json=payload)

        # Assert
        # HTTPBearer возвращает 403 когда токена нет вообще
        assert response.status_code == 403

    async def test_update_profile_extra_fields_forbidden(
        self,
        client: AsyncClient,
        test_user: User,
        auth_headers,
    ):
        """Обновление с лишними полями возвращает 422"""
        # Arrange
        headers = auth_headers(test_user)
        payload = {
            "first_name": "New",
            "extra_field": "should not be here",
        }

        # Act
        response = await client.patch(
            "/api/v1/users/me",
            headers=headers,
            json=payload,
        )

        # Assert
        assert response.status_code == 422

    async def test_update_profile_cannot_change_email(
        self,
        client: AsyncClient,
        test_user: User,
        auth_headers,
    ):
        """Попытка изменить email через обновление профиля игнорируется"""
        # Arrange
        headers = auth_headers(test_user)
        payload = {
            "email": "newemail@example.com",  # не должно измениться
            "first_name": "New",
        }

        # Act
        response = await client.patch(
            "/api/v1/users/me",
            headers=headers,
            json=payload,
        )

        # Assert
        # Может вернуть либо 422 (extra field), либо 200 с неизменённым email
        if response.status_code == 200:
            data = response.json()
            assert data["email"] == test_user.email  # email не изменился


class TestChangePassword:
    """Тесты смены пароля"""

    async def test_change_password_success(
        self,
        client: AsyncClient,
        test_user: User,
        test_password: str,
        auth_headers,
    ):
        """Успешная смена пароля"""
        # Arrange
        headers = auth_headers(test_user)
        payload = {
            "old_password": test_password,
            "new_password": "NewSecurePass123!",
        }

        # Act
        response = await client.post(
            "/api/v1/users/me/change-password",
            headers=headers,
            json=payload,
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "message" in data

        # Verify: можем войти с новым паролем
        login_response = await client.post(
            "/api/v1/auth/login",
            json={"email": test_user.email, "password": payload["new_password"]},
        )
        assert login_response.status_code == 200

    async def test_change_password_wrong_old_password(
        self,
        client: AsyncClient,
        test_user: User,
        auth_headers,
    ):
        """Смена пароля с неправильным старым паролем возвращает 401"""
        # Arrange
        headers = auth_headers(test_user)
        payload = {
            "old_password": "WrongOldPassword123!",
            "new_password": "NewSecurePass123!",
        }

        # Act
        response = await client.post(
            "/api/v1/users/me/change-password",
            headers=headers,
            json=payload,
        )

        # Assert
        assert response.status_code == 401

    async def test_change_password_requires_auth(self, client: AsyncClient):
        """Смена пароля без авторизации возвращает 403"""
        # Arrange
        payload = {
            "old_password": "OldPass123!",
            "new_password": "NewPass123!",
        }

        # Act
        response = await client.post(
            "/api/v1/users/me/change-password",
            json=payload,
        )

        # Assert
        # HTTPBearer возвращает 403 когда токена нет вообще
        assert response.status_code == 403

    async def test_change_password_weak_new_password(
        self,
        client: AsyncClient,
        test_user: User,
        test_password: str,
        auth_headers,
    ):
        """Смена на слабый пароль возвращает 422"""
        # Arrange
        headers = auth_headers(test_user)
        payload = {
            "old_password": test_password,
            "new_password": "123",  # слишком слабый
        }

        # Act
        response = await client.post(
            "/api/v1/users/me/change-password",
            headers=headers,
            json=payload,
        )

        # Assert
        assert response.status_code == 422


class TestDeleteMyAccount:
    """Тесты удаления своего аккаунта"""

    async def test_delete_my_account_success(
        self,
        client: AsyncClient,
        test_user: User,
        test_password: str,
        auth_headers,
    ):
        """Успешное удаление своего аккаунта"""
        # Arrange
        headers = auth_headers(test_user)

        # Act
        response = await client.delete("/api/v1/users/me", headers=headers)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "message" in data

        # Verify: не можем войти после удаления
        login_response = await client.post(
            "/api/v1/auth/login",
            json={"email": test_user.email, "password": test_password},
        )
        # Репозиторий фильтрует is_deleted=False, возвращая InvalidCredentials (401)
        assert login_response.status_code == 401

    async def test_delete_my_account_requires_auth(self, client: AsyncClient):
        """Удаление аккаунта без авторизации возвращает 403"""
        # Act
        response = await client.delete("/api/v1/users/me")

        # Assert
        # HTTPBearer возвращает 403 когда токена нет вообще
        assert response.status_code == 403


class TestGetUserById:
    """Тесты получения пользователя по ID (admin only)"""

    async def test_get_user_by_id_success_as_admin(
        self,
        client: AsyncClient,
        test_admin: User,
        test_user: User,
        auth_headers,
    ):
        """Админ может получить пользователя по ID"""
        # Arrange
        headers = auth_headers(test_admin)

        # Act
        response = await client.get(
            f"/api/v1/users/{test_user.id}",
            headers=headers,
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["id"] == str(test_user.id)
        assert data["email"] == test_user.email

    async def test_get_user_by_id_forbidden_for_customer(
        self,
        client: AsyncClient,
        test_user: User,
        auth_headers,
    ):
        """Обычный пользователь не может получить других пользователей"""
        # Arrange
        headers = auth_headers(test_user)
        some_user_id = "550e8400-e29b-41d4-a716-446655440000"

        # Act
        response = await client.get(
            f"/api/v1/users/{some_user_id}",
            headers=headers,
        )

        # Assert
        assert response.status_code == 403

    async def test_get_user_by_id_nonexistent(
        self,
        client: AsyncClient,
        test_admin: User,
        auth_headers,
    ):
        """Получение несуществующего пользователя возвращает 404"""
        # Arrange
        headers = auth_headers(test_admin)
        nonexistent_id = "550e8400-e29b-41d4-a716-446655440000"

        # Act
        response = await client.get(
            f"/api/v1/users/{nonexistent_id}",
            headers=headers,
        )

        # Assert
        assert response.status_code == 404


class TestGetUsersList:
    """Тесты получения списка пользователей (admin only)"""

    async def test_get_users_list_success(
        self,
        client: AsyncClient,
        test_admin: User,
        test_users: list[User],
        auth_headers,
    ):
        """Админ может получить список пользователей"""
        # Arrange
        headers = auth_headers(test_admin)

        # Act
        response = await client.get("/api/v1/users/", headers=headers)

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)
        assert len(data) >= len(test_users)  # минимум test_users + test_admin

    async def test_get_users_list_with_pagination(
        self,
        client: AsyncClient,
        test_admin: User,
        test_users: list[User],
        auth_headers,
    ):
        """Пагинация работает корректно"""
        # Arrange
        headers = auth_headers(test_admin)

        # Act
        response = await client.get(
            "/api/v1/users/?skip=0&limit=2",
            headers=headers,
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)
        assert len(data) <= 2

    async def test_get_users_list_filter_by_role(
        self,
        client: AsyncClient,
        test_admin: User,
        test_users: list[User],
        auth_headers,
    ):
        """Фильтрация по роли работает"""
        # Arrange
        headers = auth_headers(test_admin)

        # Act - передаём значение enum (lowercase)
        response = await client.get(
            "/api/v1/users/?role=admin",
            headers=headers,
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        # Все пользователи в ответе должны быть админами
        for user in data:
            assert user["role"] == "admin"

    async def test_get_users_list_filter_by_is_active(
        self,
        client: AsyncClient,
        test_admin: User,
        test_inactive_user: User,
        auth_headers,
    ):
        """Фильтрация по is_active работает"""
        # Arrange
        headers = auth_headers(test_admin)

        # Act - получаем только активных
        response = await client.get(
            "/api/v1/users/?is_active=true",
            headers=headers,
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        # Все пользователи должны быть активными
        for user in data:
            assert user["is_active"] is True

        # test_inactive_user не должен быть в списке
        inactive_ids = [user["id"] for user in data]
        assert str(test_inactive_user.id) not in inactive_ids

    async def test_get_users_list_search(
        self,
        client: AsyncClient,
        test_admin: User,
        test_user: User,
        auth_headers,
    ):
        """Поиск по email, имени или фамилии работает"""
        # Arrange
        headers = auth_headers(test_admin)

        # Act - ищем по email
        response = await client.get(
            f"/api/v1/users/?search={test_user.email}",
            headers=headers,
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        # test_user должен быть в результатах
        found_emails = [user["email"] for user in data]
        assert test_user.email in found_emails

    async def test_get_users_list_forbidden_for_customer(
        self,
        client: AsyncClient,
        test_user: User,
        auth_headers,
    ):
        """Обычный пользователь не может получить список пользователей"""
        # Arrange
        headers = auth_headers(test_user)

        # Act
        response = await client.get("/api/v1/users/", headers=headers)

        # Assert
        assert response.status_code == 403


class TestDeleteUser:
    """Тесты удаления пользователя админом"""

    async def test_delete_user_success_as_admin(
        self,
        client: AsyncClient,
        test_admin: User,
        test_user: User,
        test_password: str,
        auth_headers,
    ):
        """Админ может удалить пользователя"""
        # Arrange
        headers = auth_headers(test_admin)

        # Act
        response = await client.delete(
            f"/api/v1/users/{test_user.id}",
            headers=headers,
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "message" in data

        # Verify: пользователь не может войти после удаления
        login_response = await client.post(
            "/api/v1/auth/login",
            json={"email": test_user.email, "password": test_password},
        )
        # Репозиторий фильтрует is_deleted=False, возвращая InvalidCredentials (401)
        assert login_response.status_code == 401

    async def test_delete_user_forbidden_for_customer(
        self,
        client: AsyncClient,
        test_user: User,
        auth_headers,
    ):
        """Обычный пользователь не может удалить других пользователей"""
        # Arrange
        headers = auth_headers(test_user)
        some_user_id = "550e8400-e29b-41d4-a716-446655440000"

        # Act
        response = await client.delete(
            f"/api/v1/users/{some_user_id}",
            headers=headers,
        )

        # Assert
        assert response.status_code == 403

    async def test_admin_cannot_delete_self_via_endpoint(
        self,
        client: AsyncClient,
        test_admin: User,
        auth_headers,
    ):
        """Админ не может удалить самого себя через этот endpoint"""
        # Arrange
        headers = auth_headers(test_admin)

        # Act
        response = await client.delete(
            f"/api/v1/users/{test_admin.id}",
            headers=headers,
        )

        # Assert
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "DELETE /users/me" in data["detail"]

    async def test_delete_user_nonexistent(
        self,
        client: AsyncClient,
        test_admin: User,
        auth_headers,
    ):
        """Удаление несуществующего пользователя возвращает 404"""
        # Arrange
        headers = auth_headers(test_admin)
        nonexistent_id = "550e8400-e29b-41d4-a716-446655440000"

        # Act
        response = await client.delete(
            f"/api/v1/users/{nonexistent_id}",
            headers=headers,
        )

        # Assert
        assert response.status_code == 404
