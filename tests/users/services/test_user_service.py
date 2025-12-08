"""
Интеграционные тесты для UserService.

Покрывает все методы сервиса:
- get_user: получение пользователя по ID
- update_user: обновление профиля пользователя
- list_users: список пользователей с фильтрами и пагинацией
"""

import uuid

import pytest
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import UserNotFoundError
from app.models.user import User as UserModel, UserRole
from app.repositories.user import UserRepository
from app.schemas.user import UserUpdate
from app.services.user_service import UserService


@pytest.mark.integration
class TestUserServiceGetUser:
    """Тесты для метода get_user"""

    async def test_get_user_success(
        self, db_session: AsyncSession, test_user: UserModel
    ):
        """Успешное получение пользователя по ID"""
        service = UserService(db_session)

        user_response = await service.get_user(test_user.id)

        # Проверяем, что вернулся UserResponse
        assert user_response.id == test_user.id
        assert user_response.email == test_user.email
        assert user_response.first_name == test_user.first_name
        assert user_response.last_name == test_user.last_name
        assert user_response.phone == test_user.phone
        assert user_response.role == test_user.role
        assert user_response.is_active == test_user.is_active
        assert user_response.is_verified == test_user.is_verified

    async def test_get_user_not_found(self, db_session: AsyncSession):
        """Получение несуществующего пользователя - выбрасывает UserNotFoundError"""
        service = UserService(db_session)

        fake_user_id = uuid.uuid4()

        with pytest.raises(UserNotFoundError) as exc_info:
            await service.get_user(fake_user_id)

        assert exc_info.value.details["user_id"] == str(fake_user_id)

    async def test_get_user_returns_admin(
        self, db_session: AsyncSession, test_admin: UserModel
    ):
        """Получение пользователя с ролью ADMIN работает корректно"""
        service = UserService(db_session)

        user_response = await service.get_user(test_admin.id)

        assert user_response.id == test_admin.id
        assert user_response.role == UserRole.ADMIN


@pytest.mark.integration
class TestUserServiceUpdateUser:
    """Тесты для метода update_user"""

    async def test_update_user_all_fields(
        self, db_session: AsyncSession, test_user: UserModel
    ):
        """Успешное обновление всех полей профиля"""
        service = UserService(db_session)

        update_data = UserUpdate(
            first_name="UpdatedFirst",
            last_name="UpdatedLast",
            phone="+9999999999",
        )

        updated_response = await service.update_user(test_user.id, update_data)

        # Проверяем, что вернулся обновлённый UserResponse
        assert updated_response.id == test_user.id
        assert updated_response.first_name == "UpdatedFirst"
        assert updated_response.last_name == "UpdatedLast"
        assert updated_response.phone == "+9999999999"
        assert updated_response.email == test_user.email  # email не меняется

        # Проверяем, что изменения сохранились в БД
        user_repo = UserRepository(db_session)
        db_user = await user_repo.get_by_id(test_user.id)
        assert db_user.first_name == "UpdatedFirst"
        assert db_user.last_name == "UpdatedLast"
        assert db_user.phone == "+9999999999"

    async def test_update_user_partial_fields(
        self, db_session: AsyncSession, test_user: UserModel
    ):
        """Обновление части полей (остальные не меняются)"""
        service = UserService(db_session)

        original_phone = test_user.phone

        update_data = UserUpdate(
            first_name="NewFirstName",
            # last_name и phone не указываем (будут None)
        )

        updated_response = await service.update_user(test_user.id, update_data)

        assert updated_response.first_name == "NewFirstName"
        assert updated_response.last_name == test_user.last_name  # не изменилось
        assert updated_response.phone == original_phone  # не изменилось

    async def test_update_user_no_fields(
        self, db_session: AsyncSession, test_user: UserModel
    ):
        """Обновление без указания полей - возвращает текущее состояние"""
        service = UserService(db_session)

        # Создаём пустой UserUpdate (все поля None)
        update_data = UserUpdate()

        updated_response = await service.update_user(test_user.id, update_data)

        # Ничего не изменилось
        assert updated_response.id == test_user.id
        assert updated_response.first_name == test_user.first_name
        assert updated_response.last_name == test_user.last_name
        assert updated_response.phone == test_user.phone

    async def test_update_user_not_found(self, db_session: AsyncSession):
        """Обновление несуществующего пользователя - выбрасывает UserNotFoundError"""
        service = UserService(db_session)

        fake_user_id = uuid.uuid4()
        update_data = UserUpdate(first_name="New Name")

        with pytest.raises(UserNotFoundError) as exc_info:
            await service.update_user(fake_user_id, update_data)

        assert exc_info.value.details["user_id"] == str(fake_user_id)

    async def test_update_user_phone_to_none(
        self, db_session: AsyncSession, test_user: UserModel
    ):
        """Обновление phone на None (удаление номера)"""
        service = UserService(db_session)

        assert test_user.phone is not None  # Изначально phone есть

        update_data = UserUpdate(phone=None)
        updated_response = await service.update_user(test_user.id, update_data)

        assert updated_response.phone is None

        # Проверяем в БД
        user_repo = UserRepository(db_session)
        db_user = await user_repo.get_by_id(test_user.id)
        assert db_user.phone is None

    async def test_update_user_forbidden_fields_rejected(
        self, db_session: AsyncSession, test_user: UserModel
    ):
        """Попытка обновить запрещенные поля (role, email, password) - выбрасывает ValidationError"""
        service = UserService(db_session)

        original_role = test_user.role
        original_email = test_user.email

        # Пытаемся передать запрещенное поле role
        with pytest.raises(ValidationError) as exc_info:
            UserUpdate(
                first_name="New Name",
                role=UserRole.ADMIN,  # ❌ Запрещено
            )

        # Проверяем, что Pydantic v2 блокирует лишнее поле
        error_message = str(exc_info.value).lower()
        assert "extra inputs are not permitted" in error_message or "extra fields not permitted" in error_message

        # Пытаемся передать email (запрещено)
        with pytest.raises(ValidationError):
            UserUpdate(
                first_name="New Name",
                email="newemail@example.com",  # ❌ Запрещено
            )

        # Пытаемся передать password (запрещено)
        with pytest.raises(ValidationError):
            UserUpdate(
                first_name="New Name",
                password="NewPassword123",  # ❌ Запрещено
            )

        # Проверяем, что ничего не изменилось в БД
        user_repo = UserRepository(db_session)
        db_user = await user_repo.get_by_id(test_user.id)
        assert db_user.role == original_role
        assert db_user.email == original_email


@pytest.mark.integration
class TestUserServiceListUsers:
    """Тесты для метода list_users с фильтрацией и пагинацией"""

    async def test_list_users_default(
        self, db_session: AsyncSession, test_users: list[UserModel]
    ):
        """Получение списка всех пользователей (по умолчанию)"""
        service = UserService(db_session)

        users = await service.list_users()

        # test_users содержит 5 пользователей
        assert len(users) == 5
        assert all(user.email.startswith("user") for user in users)

    async def test_list_users_with_pagination(
        self, db_session: AsyncSession, test_users: list[UserModel]
    ):
        """Пагинация работает корректно (skip и limit)"""
        service = UserService(db_session)

        # Первая страница (2 элемента)
        page1 = await service.list_users(skip=0, limit=2)
        assert len(page1) == 2

        # Вторая страница (2 элемента)
        page2 = await service.list_users(skip=2, limit=2)
        assert len(page2) == 2

        # Третья страница (1 элемент)
        page3 = await service.list_users(skip=4, limit=2)
        assert len(page3) == 1

        # Проверяем, что не пересекаются
        page1_ids = {user.id for user in page1}
        page2_ids = {user.id for user in page2}
        assert page1_ids.isdisjoint(page2_ids)

    async def test_list_users_limit_max_100(
        self, db_session: AsyncSession, test_users: list[UserModel]
    ):
        """Limit ограничен максимум 100 элементами"""
        service = UserService(db_session)

        # Запрашиваем больше 100
        users = await service.list_users(limit=500)

        # Должно вернуться максимум 100 (или меньше, если всего меньше)
        assert len(users) <= 100

    async def test_list_users_filter_by_is_active(
        self, db_session: AsyncSession, test_user: UserModel, test_inactive_user: UserModel
    ):
        """Фильтр по is_active работает"""
        service = UserService(db_session)

        # Только активные
        active_users = await service.list_users(is_active=True)
        active_ids = {user.id for user in active_users}

        assert test_user.id in active_ids
        assert test_inactive_user.id not in active_ids

        # Только неактивные
        inactive_users = await service.list_users(is_active=False)
        inactive_ids = {user.id for user in inactive_users}

        assert test_inactive_user.id in inactive_ids
        assert test_user.id not in inactive_ids

    async def test_list_users_filter_by_role(
        self, db_session: AsyncSession, test_user: UserModel, test_admin: UserModel
    ):
        """Фильтр по role работает"""
        service = UserService(db_session)

        # Только CUSTOMER
        customers = await service.list_users(role=UserRole.CUSTOMER)
        customer_ids = {user.id for user in customers}

        assert test_user.id in customer_ids
        assert test_admin.id not in customer_ids

        # Только ADMIN
        admins = await service.list_users(role=UserRole.ADMIN)
        admin_ids = {user.id for user in admins}

        assert test_admin.id in admin_ids
        assert test_user.id not in admin_ids

    async def test_list_users_filter_by_search(
        self, db_session: AsyncSession, test_user: UserModel, test_admin: UserModel
    ):
        """Поиск по email, first_name, last_name работает"""
        service = UserService(db_session)

        # Поиск по email
        users = await service.list_users(search=test_user.email)
        assert len(users) >= 1
        assert any(user.id == test_user.id for user in users)

        # Поиск по части имени (регистронезависимый)
        users = await service.list_users(search="test")  # test_user: first_name="Test"
        assert len(users) >= 1
        assert any(user.id == test_user.id for user in users)

        # Поиск по фамилии
        users = await service.list_users(search="User")  # last_name="User"
        assert len(users) >= 1

    async def test_list_users_combined_filters(
        self, db_session: AsyncSession, test_user: UserModel, test_admin: UserModel, test_inactive_user: UserModel
    ):
        """Комбинация нескольких фильтров работает"""
        service = UserService(db_session)

        # Активные CUSTOMER
        users = await service.list_users(is_active=True, role=UserRole.CUSTOMER)
        user_ids = {user.id for user in users}

        assert test_user.id in user_ids  # Активный CUSTOMER
        assert test_admin.id not in user_ids  # ADMIN
        assert test_inactive_user.id not in user_ids  # Неактивный

    async def test_list_users_empty_result(self, db_session: AsyncSession):
        """Список пуст, если пользователей нет или фильтры не подходят"""
        service = UserService(db_session)

        # Ищем несуществующий email
        users = await service.list_users(search="nonexistent@nowhere.com")
        assert len(users) == 0

    async def test_list_users_skip_beyond_total(
        self, db_session: AsyncSession, test_users: list[UserModel]
    ):
        """skip больше общего количества - возвращает пустой список"""
        service = UserService(db_session)

        users = await service.list_users(skip=1000)
        assert len(users) == 0

    @pytest.mark.parametrize("limit", [1, 5, 10, 50, 100])
    async def test_list_users_various_limits(
        self, db_session: AsyncSession, test_users: list[UserModel], limit: int
    ):
        """Различные значения limit работают корректно"""
        service = UserService(db_session)

        users = await service.list_users(limit=limit)

        # Вернётся меньше или равно limit (зависит от общего количества)
        assert len(users) <= limit
        assert len(users) <= len(test_users)
