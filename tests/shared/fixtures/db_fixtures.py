import asyncio
from typing import AsyncGenerator

import pytest
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
)
from sqlalchemy.pool import NullPool

from app.models.base import BaseModel


# Тестовая база данных
TEST_DATABASE_URL = "postgresql+asyncpg://FastAPIshop-tests:FastAPIshop-tests@localhost:5432/FastAPIshop-tests"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    poolclass=NullPool,
)

TestAsyncSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


@pytest.fixture(scope="session")
def event_loop():
    """
    Создаёт event loop для всей сессии тестирования.

    Необходимо для pytest-asyncio, чтобы избежать проблем с закрытием loop.
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function", autouse=True)
async def setup_database(request):
    """
    Создаёт таблицы перед каждым тестом и удаляет после.

    autouse=True применяет фикстуру автоматически ко всем тестам.
    Unit-тесты (@pytest.mark.unit) пропускают создание БД.
    Обеспечивает полную изоляцию тестов.
    """
    # Пропускаем setup для unit-тестов (они не требуют БД)
    if "unit" in request.keywords:
        yield
        return

    async with test_engine.begin() as conn:
        # Чистим схему на случай, если остались данные от прошлых запусков
        await conn.run_sync(BaseModel.metadata.drop_all)
        await conn.run_sync(BaseModel.metadata.create_all)

    yield

    async with test_engine.begin() as conn:
        await conn.run_sync(BaseModel.metadata.drop_all)


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Создаёт тестовую сессию БД для каждого теста.

    Yields:
        AsyncSession для работы с БД
    """
    async with TestAsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
