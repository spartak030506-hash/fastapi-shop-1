import uuid
from typing import Callable

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password, create_access_token
from app.models.user import User, UserRole


@pytest.fixture
def test_password() -> str:
    """Возвращает тестовый пароль для обычных пользователей"""
    return "TestPassword123"


@pytest.fixture
def admin_password() -> str:
    """Возвращает тестовый пароль для администратора"""
    return "AdminPassword123"


@pytest.fixture
async def test_user(db_session: AsyncSession, test_password: str) -> User:
    """
    Создаёт тестового пользователя (CUSTOMER) в БД.

    Args:
        db_session: Тестовая сессия БД
        test_password: Пароль для пользователя

    Returns:
        Созданный пользователь
    """
    user = User(
        id=uuid.uuid4(),
        email="test@example.com",
        hashed_password=hash_password(test_password),
        first_name="Test",
        last_name="User",
        phone="+1234567890",
        role=UserRole.CUSTOMER,
    )

    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    return user


@pytest.fixture
async def test_admin(db_session: AsyncSession, admin_password: str) -> User:
    """
    Создаёт тестового администратора в БД.

    Args:
        db_session: Тестовая сессия БД
        admin_password: Пароль для администратора

    Returns:
        Созданный администратор
    """
    admin = User(
        id=uuid.uuid4(),
        email="admin@example.com",
        hashed_password=hash_password(admin_password),
        first_name="Admin",
        last_name="User",
        phone="+9876543210",
        role=UserRole.ADMIN,
    )

    db_session.add(admin)
    await db_session.commit()
    await db_session.refresh(admin)

    return admin


@pytest.fixture
async def test_inactive_user(db_session: AsyncSession, test_password: str) -> User:
    """
    Создаёт неактивного пользователя (is_active=False) в БД.

    Args:
        db_session: Тестовая сессия БД
        test_password: Пароль для пользователя

    Returns:
        Созданный неактивный пользователь
    """
    user = User(
        id=uuid.uuid4(),
        email="inactive@example.com",
        hashed_password=hash_password(test_password),
        first_name="Inactive",
        last_name="User",
        phone="+1111111111",
        role=UserRole.CUSTOMER,
    )
    user.is_active = False

    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    return user


@pytest.fixture
async def test_unverified_user(db_session: AsyncSession, test_password: str) -> User:
    """
    Создаёт неверифицированного пользователя (is_verified=False) в БД.

    Args:
        db_session: Тестовая сессия БД
        test_password: Пароль для пользователя

    Returns:
        Созданный неверифицированный пользователь
    """
    user = User(
        id=uuid.uuid4(),
        email="unverified@example.com",
        hashed_password=hash_password(test_password),
        first_name="Unverified",
        last_name="User",
        phone="+2222222222",
        role=UserRole.CUSTOMER,
    )
    user.is_verified = False

    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    return user


@pytest.fixture
def auth_headers() -> Callable[[User], dict[str, str]]:
    """
    Возвращает функцию для создания Bearer token headers для любого пользователя.

    Returns:
        Функция, принимающая User и возвращающая headers с Authorization

    Usage:
        headers = auth_headers(test_user)
        response = await client.get("/users/me", headers=headers)
    """
    def _create_headers(user: User) -> dict[str, str]:
        access_token = create_access_token(data={"sub": str(user.id)})
        return {"Authorization": f"Bearer {access_token}"}

    return _create_headers


@pytest.fixture
async def test_users(db_session: AsyncSession, test_password: str) -> list[User]:
    """
    Создаёт несколько тестовых пользователей для тестирования пагинации.

    Args:
        db_session: Тестовая сессия БД
        test_password: Пароль для пользователей

    Returns:
        Список из 5 созданных пользователей
    """
    users = []

    for i in range(5):
        user = User(
            id=uuid.uuid4(),
            email=f"user{i}@example.com",
            hashed_password=hash_password(test_password),
            first_name=f"User{i}",
            last_name=f"Test{i}",
            phone=f"+100000000{i}",
            role=UserRole.CUSTOMER,
        )
        db_session.add(user)
        users.append(user)

    await db_session.commit()

    for user in users:
        await db_session.refresh(user)

    return users
