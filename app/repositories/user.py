import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, UserRole
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    """
    Репозиторий для работы с пользователями.

    Наследует базовые CRUD операции и добавляет специфичные методы:
    - Поиск по email
    - Проверка существования email
    - Поиск по роли
    - Фильтрация по статусам (активные, верифицированные)
    """

    def __init__(self, db: AsyncSession):
        super().__init__(User, db)

    async def get_by_email(
        self,
        email: str,
        include_deleted: bool = False
    ) -> User | None:
        """
        Получить пользователя по email.

        Args:
            email: Email пользователя
            include_deleted: Включать ли удаленные записи

        Returns:
            Пользователь или None
        """
        query = select(User).where(User.email == email)

        if not include_deleted:
            query = query.where(User.is_deleted == False)

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def email_exists(
        self,
        email: str,
        exclude_user_id: uuid.UUID | None = None
    ) -> bool:
        """
        Проверить существование email в системе.

        Args:
            email: Email для проверки
            exclude_user_id: ID пользователя для исключения из проверки (для обновления профиля)

        Returns:
            True если email существует, False если свободен
        """
        query = select(User).where(
            User.email == email,
            User.is_deleted == False
        )

        if exclude_user_id:
            query = query.where(User.id != exclude_user_id)

        result = await self.db.execute(query)
        return result.scalar_one_or_none() is not None

    async def get_by_role(
        self,
        role: UserRole,
        skip: int = 0,
        limit: int = 100,
        include_deleted: bool = False
    ) -> list[User]:
        """
        Получить пользователей по роли.

        Args:
            role: Роль пользователя (CUSTOMER/ADMIN)
            skip: Количество записей для пропуска
            limit: Максимальное количество записей
            include_deleted: Включать ли удаленные записи

        Returns:
            Список пользователей с указанной ролью
        """
        query = select(User).where(User.role == role)

        if not include_deleted:
            query = query.where(User.is_deleted == False)

        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_active_users(
        self,
        skip: int = 0,
        limit: int = 100
    ) -> list[User]:
        """
        Получить активных пользователей.

        Args:
            skip: Количество записей для пропуска
            limit: Максимальное количество записей

        Returns:
            Список активных пользователей
        """
        query = select(User).where(
            User.is_active == True,
            User.is_deleted == False
        )

        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_verified_users(
        self,
        skip: int = 0,
        limit: int = 100
    ) -> list[User]:
        """
        Получить верифицированных пользователей.

        Args:
            skip: Количество записей для пропуска
            limit: Максимальное количество записей

        Returns:
            Список верифицированных пользователей
        """
        query = select(User).where(
            User.is_verified == True,
            User.is_deleted == False
        )

        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())
