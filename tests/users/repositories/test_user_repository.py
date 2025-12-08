import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models.user import User, UserRole
from app.repositories.user import UserRepository


@pytest.mark.integration
class TestUserRepositoryBase:
    """Тесты базовых CRUD операций UserRepository (наследуются от BaseRepository)"""

    async def test_get_by_id_existing_user(self, db_session: AsyncSession, test_user: User):
        """Получение существующего пользователя по ID возвращает пользователя"""
        repo = UserRepository(db_session)

        result = await repo.get_by_id(test_user.id)

        assert result is not None
        assert result.id == test_user.id
        assert result.email == test_user.email

    async def test_get_by_id_non_existing_user(self, db_session: AsyncSession):
        """Получение несуществующего пользователя по ID возвращает None"""
        repo = UserRepository(db_session)
        non_existing_id = uuid.uuid4()

        result = await repo.get_by_id(non_existing_id)

        assert result is None

    async def test_get_by_id_soft_deleted_user_excluded_by_default(
        self,
        db_session: AsyncSession,
        test_user: User
    ):
        """Soft-deleted пользователь исключается по умолчанию при поиске по ID"""
        repo = UserRepository(db_session)
        await repo.soft_delete(test_user.id)

        result = await repo.get_by_id(test_user.id)

        assert result is None

    async def test_get_by_id_soft_deleted_user_included_when_requested(
        self,
        db_session: AsyncSession,
        test_user: User
    ):
        """Soft-deleted пользователь включается при include_deleted=True"""
        repo = UserRepository(db_session)
        await repo.soft_delete(test_user.id)

        result = await repo.get_by_id(test_user.id, include_deleted=True)

        assert result is not None
        assert result.is_deleted is True

    async def test_get_all_returns_all_users(
        self,
        db_session: AsyncSession,
        test_users: list[User]
    ):
        """get_all возвращает всех пользователей"""
        repo = UserRepository(db_session)

        result = await repo.get_all()

        assert len(result) == 5
        assert all(isinstance(u, User) for u in result)

    async def test_get_all_with_pagination(
        self,
        db_session: AsyncSession,
        test_users: list[User]
    ):
        """get_all поддерживает пагинацию через skip и limit"""
        repo = UserRepository(db_session)

        result_page1 = await repo.get_all(skip=0, limit=2)
        result_page2 = await repo.get_all(skip=2, limit=2)

        assert len(result_page1) == 2
        assert len(result_page2) == 2
        assert result_page1[0].id != result_page2[0].id

    async def test_get_all_excludes_soft_deleted_by_default(
        self,
        db_session: AsyncSession,
        test_users: list[User]
    ):
        """get_all исключает soft-deleted пользователей по умолчанию"""
        repo = UserRepository(db_session)
        await repo.soft_delete(test_users[0].id)

        result = await repo.get_all()

        assert len(result) == 4
        assert all(u.id != test_users[0].id for u in result)

    async def test_count_returns_correct_count(
        self,
        db_session: AsyncSession,
        test_users: list[User]
    ):
        """count возвращает правильное количество пользователей"""
        repo = UserRepository(db_session)

        count = await repo.count()

        assert count == 5

    async def test_count_excludes_soft_deleted(
        self,
        db_session: AsyncSession,
        test_users: list[User]
    ):
        """count исключает soft-deleted пользователей"""
        repo = UserRepository(db_session)
        await repo.soft_delete(test_users[0].id)

        count = await repo.count()

        assert count == 4

    async def test_count_includes_soft_deleted_when_requested(
        self,
        db_session: AsyncSession,
        test_users: list[User]
    ):
        """count включает soft-deleted при include_deleted=True"""
        repo = UserRepository(db_session)
        await repo.soft_delete(test_users[0].id)

        count = await repo.count(include_deleted=True)

        assert count == 5

    async def test_create_user_success(self, db_session: AsyncSession, test_password: str):
        """create успешно создаёт пользователя в БД"""
        repo = UserRepository(db_session)

        new_user = User(
            id=uuid.uuid4(),
            email="new@example.com",
            hashed_password=hash_password(test_password),
            first_name="New",
            last_name="User",
            role=UserRole.CUSTOMER,
        )

        result = await repo.create(new_user)
        await db_session.commit()

        assert result.id is not None
        assert result.email == "new@example.com"

        # Проверка что пользователь действительно в БД
        found_user = await repo.get_by_id(result.id)
        assert found_user is not None
        assert found_user.email == "new@example.com"

    async def test_update_user_success(self, db_session: AsyncSession, test_user: User):
        """update успешно обновляет пользователя"""
        repo = UserRepository(db_session)

        updated_user = await repo.update(
            test_user.id,
            first_name="Updated",
            last_name="Name"
        )

        assert updated_user is not None
        assert updated_user.first_name == "Updated"
        assert updated_user.last_name == "Name"
        assert updated_user.email == test_user.email  # не изменилось

    async def test_update_non_existing_user_returns_none(self, db_session: AsyncSession):
        """update несуществующего пользователя возвращает None"""
        repo = UserRepository(db_session)
        non_existing_id = uuid.uuid4()

        result = await repo.update(non_existing_id, first_name="Test")

        assert result is None

    async def test_update_soft_deleted_user_returns_none(
        self,
        db_session: AsyncSession,
        test_user: User
    ):
        """update soft-deleted пользователя возвращает None"""
        repo = UserRepository(db_session)
        await repo.soft_delete(test_user.id)

        result = await repo.update(test_user.id, first_name="Updated")

        assert result is None

    async def test_soft_delete_user_success(self, db_session: AsyncSession, test_user: User):
        """soft_delete успешно помечает пользователя как удалённого"""
        repo = UserRepository(db_session)

        success = await repo.soft_delete(test_user.id)

        assert success is True

        # Проверка что пользователь помечен как удалённый
        deleted_user = await repo.get_by_id(test_user.id, include_deleted=True)
        assert deleted_user is not None
        assert deleted_user.is_deleted is True

    async def test_soft_delete_non_existing_user_returns_false(
        self,
        db_session: AsyncSession
    ):
        """soft_delete несуществующего пользователя возвращает False"""
        repo = UserRepository(db_session)
        non_existing_id = uuid.uuid4()

        success = await repo.soft_delete(non_existing_id)

        assert success is False

    async def test_soft_delete_already_deleted_user_returns_false(
        self,
        db_session: AsyncSession,
        test_user: User
    ):
        """soft_delete уже удалённого пользователя возвращает False"""
        repo = UserRepository(db_session)
        await repo.soft_delete(test_user.id)

        success = await repo.soft_delete(test_user.id)

        assert success is False

    async def test_hard_delete_user_success(self, db_session: AsyncSession, test_user: User):
        """hard_delete физически удаляет пользователя из БД"""
        repo = UserRepository(db_session)
        user_id = test_user.id

        success = await repo.hard_delete(user_id)

        assert success is True

        # Проверка что пользователь полностью удалён из БД
        result = await repo.get_by_id(user_id, include_deleted=True)
        assert result is None

    async def test_hard_delete_non_existing_user_returns_false(
        self,
        db_session: AsyncSession
    ):
        """hard_delete несуществующего пользователя возвращает False"""
        repo = UserRepository(db_session)
        non_existing_id = uuid.uuid4()

        success = await repo.hard_delete(non_existing_id)

        assert success is False


@pytest.mark.integration
class TestUserRepositorySpecific:
    """Тесты специфичных методов UserRepository"""

    async def test_get_by_email_existing_user(
        self,
        db_session: AsyncSession,
        test_user: User
    ):
        """Получение существующего пользователя по email возвращает пользователя"""
        repo = UserRepository(db_session)

        result = await repo.get_by_email(test_user.email)

        assert result is not None
        assert result.id == test_user.id
        assert result.email == test_user.email

    async def test_get_by_email_non_existing_user(self, db_session: AsyncSession):
        """Получение несуществующего пользователя по email возвращает None"""
        repo = UserRepository(db_session)

        result = await repo.get_by_email("nonexisting@example.com")

        assert result is None

    async def test_get_by_email_case_sensitive(
        self,
        db_session: AsyncSession,
        test_user: User
    ):
        """Поиск по email чувствителен к регистру"""
        repo = UserRepository(db_session)

        result = await repo.get_by_email(test_user.email.upper())

        assert result is None

    async def test_get_by_email_soft_deleted_user_excluded_by_default(
        self,
        db_session: AsyncSession,
        test_user: User
    ):
        """Soft-deleted пользователь исключается по умолчанию при поиске по email"""
        repo = UserRepository(db_session)
        await repo.soft_delete(test_user.id)

        result = await repo.get_by_email(test_user.email)

        assert result is None

    async def test_get_by_email_soft_deleted_user_included_when_requested(
        self,
        db_session: AsyncSession,
        test_user: User
    ):
        """Soft-deleted пользователь включается при include_deleted=True"""
        repo = UserRepository(db_session)
        await repo.soft_delete(test_user.id)

        result = await repo.get_by_email(test_user.email, include_deleted=True)

        assert result is not None
        assert result.is_deleted is True

    async def test_email_exists_returns_true_for_existing_email(
        self,
        db_session: AsyncSession,
        test_user: User
    ):
        """email_exists возвращает True для существующего email"""
        repo = UserRepository(db_session)

        exists = await repo.email_exists(test_user.email)

        assert exists is True

    async def test_email_exists_returns_false_for_non_existing_email(
        self,
        db_session: AsyncSession
    ):
        """email_exists возвращает False для несуществующего email"""
        repo = UserRepository(db_session)

        exists = await repo.email_exists("nonexisting@example.com")

        assert exists is False

    async def test_email_exists_excludes_soft_deleted_users(
        self,
        db_session: AsyncSession,
        test_user: User
    ):
        """email_exists исключает soft-deleted пользователей"""
        repo = UserRepository(db_session)
        await repo.soft_delete(test_user.id)

        exists = await repo.email_exists(test_user.email)

        assert exists is False

    async def test_email_exists_excludes_specific_user_id(
        self,
        db_session: AsyncSession,
        test_user: User
    ):
        """email_exists исключает конкретного пользователя из проверки"""
        repo = UserRepository(db_session)

        exists = await repo.email_exists(test_user.email, exclude_user_id=test_user.id)

        assert exists is False

    async def test_email_exists_with_exclude_finds_other_users(
        self,
        db_session: AsyncSession,
        test_user: User,
        test_admin: User
    ):
        """email_exists с exclude находит других пользователей с таким email"""
        repo = UserRepository(db_session)

        # Создаём ещё одного пользователя с другим email
        another_user = User(
            id=uuid.uuid4(),
            email="another@example.com",
            hashed_password=test_user.hashed_password,
            first_name="Another",
            last_name="User",
            role=UserRole.CUSTOMER,
        )
        await repo.create(another_user)
        await db_session.commit()

        # Проверяем что email другого пользователя существует даже при исключении test_user
        exists = await repo.email_exists(another_user.email, exclude_user_id=test_user.id)

        assert exists is True

    async def test_get_by_role_customer(
        self,
        db_session: AsyncSession,
        test_user: User,
        test_admin: User
    ):
        """get_by_role возвращает только пользователей с ролью CUSTOMER"""
        repo = UserRepository(db_session)

        result = await repo.get_by_role(UserRole.CUSTOMER)

        assert len(result) >= 1
        assert all(u.role == UserRole.CUSTOMER for u in result)
        assert any(u.id == test_user.id for u in result)
        assert not any(u.id == test_admin.id for u in result)

    async def test_get_by_role_admin(
        self,
        db_session: AsyncSession,
        test_user: User,
        test_admin: User
    ):
        """get_by_role возвращает только пользователей с ролью ADMIN"""
        repo = UserRepository(db_session)

        result = await repo.get_by_role(UserRole.ADMIN)

        assert len(result) >= 1
        assert all(u.role == UserRole.ADMIN for u in result)
        assert any(u.id == test_admin.id for u in result)
        assert not any(u.id == test_user.id for u in result)

    async def test_get_by_role_with_pagination(
        self,
        db_session: AsyncSession,
        test_users: list[User]
    ):
        """get_by_role поддерживает пагинацию"""
        repo = UserRepository(db_session)

        result_page1 = await repo.get_by_role(UserRole.CUSTOMER, skip=0, limit=2)
        result_page2 = await repo.get_by_role(UserRole.CUSTOMER, skip=2, limit=2)

        assert len(result_page1) == 2
        assert len(result_page2) >= 2
        assert result_page1[0].id != result_page2[0].id

    async def test_get_by_role_excludes_soft_deleted_by_default(
        self,
        db_session: AsyncSession,
        test_users: list[User]
    ):
        """get_by_role исключает soft-deleted пользователей по умолчанию"""
        repo = UserRepository(db_session)
        await repo.soft_delete(test_users[0].id)

        result = await repo.get_by_role(UserRole.CUSTOMER)

        assert all(u.id != test_users[0].id for u in result)

    async def test_get_by_role_includes_soft_deleted_when_requested(
        self,
        db_session: AsyncSession,
        test_users: list[User]
    ):
        """get_by_role включает soft-deleted при include_deleted=True"""
        repo = UserRepository(db_session)
        await repo.soft_delete(test_users[0].id)

        result = await repo.get_by_role(UserRole.CUSTOMER, include_deleted=True)

        deleted_user = next((u for u in result if u.id == test_users[0].id), None)
        assert deleted_user is not None
        assert deleted_user.is_deleted is True

    async def test_get_active_users_returns_only_active(
        self,
        db_session: AsyncSession,
        test_user: User,
        test_inactive_user: User
    ):
        """get_active_users возвращает только активных пользователей"""
        repo = UserRepository(db_session)

        result = await repo.get_active_users()

        assert len(result) >= 1
        assert all(u.is_active is True for u in result)
        assert any(u.id == test_user.id for u in result)
        assert not any(u.id == test_inactive_user.id for u in result)

    async def test_get_active_users_with_pagination(
        self,
        db_session: AsyncSession,
        test_users: list[User]
    ):
        """get_active_users поддерживает пагинацию"""
        repo = UserRepository(db_session)

        result_page1 = await repo.get_active_users(skip=0, limit=2)
        result_page2 = await repo.get_active_users(skip=2, limit=2)

        assert len(result_page1) == 2
        assert len(result_page2) >= 2
        assert result_page1[0].id != result_page2[0].id

    async def test_get_active_users_excludes_soft_deleted(
        self,
        db_session: AsyncSession,
        test_user: User
    ):
        """get_active_users исключает soft-deleted пользователей"""
        repo = UserRepository(db_session)
        await repo.soft_delete(test_user.id)

        result = await repo.get_active_users()

        assert not any(u.id == test_user.id for u in result)

    async def test_get_verified_users_returns_only_verified(
        self,
        db_session: AsyncSession,
        test_user: User,
        test_unverified_user: User
    ):
        """get_verified_users возвращает только верифицированных пользователей"""
        repo = UserRepository(db_session)

        # Делаем test_user верифицированным
        test_user.is_verified = True
        await db_session.commit()
        await db_session.refresh(test_user)

        result = await repo.get_verified_users()

        assert len(result) >= 1
        assert all(u.is_verified is True for u in result)
        assert any(u.id == test_user.id for u in result)
        assert not any(u.id == test_unverified_user.id for u in result)

    async def test_get_verified_users_with_pagination(
        self,
        db_session: AsyncSession,
        test_users: list[User]
    ):
        """get_verified_users поддерживает пагинацию"""
        repo = UserRepository(db_session)

        # Делаем всех пользователей верифицированными
        for user in test_users:
            user.is_verified = True
        await db_session.commit()

        result_page1 = await repo.get_verified_users(skip=0, limit=2)
        result_page2 = await repo.get_verified_users(skip=2, limit=2)

        assert len(result_page1) == 2
        assert len(result_page2) >= 2
        assert result_page1[0].id != result_page2[0].id

    async def test_get_verified_users_excludes_soft_deleted(
        self,
        db_session: AsyncSession,
        test_user: User
    ):
        """get_verified_users исключает soft-deleted пользователей"""
        repo = UserRepository(db_session)
        await repo.soft_delete(test_user.id)

        result = await repo.get_verified_users()

        assert not any(u.id == test_user.id for u in result)
