import uuid

from sqlalchemy import select, or_, exists
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
            query = query.where(User.is_deleted.is_(False))

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
        # Создаем подзапрос для exists
        subquery = select(User.id).where(
            User.email == email,
            User.is_deleted.is_(False)
        )

        if exclude_user_id:
            subquery = subquery.where(User.id != exclude_user_id)

        # Используем exists() для проверки
        query = select(exists(subquery))
        result = await self.db.execute(query)
        return result.scalar()

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
            query = query.where(User.is_deleted.is_(False))

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
            User.is_active.is_(True),
            User.is_deleted.is_(False)
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
            User.is_verified.is_(True),
            User.is_deleted.is_(False)
        )

        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_filtered_users(
        self,
        skip: int = 0,
        limit: int = 100,
        is_active: bool | None = None,
        role: UserRole | None = None,
        search: str | None = None,
    ) -> list[User]:
        """
        Получить пользователей с фильтрацией.

        Args:
            skip: Количество записей для пропуска
            limit: Максимальное количество записей
            is_active: Фильтр по статусу активности (опционально)
            role: Фильтр по роли (опционально)
            search: Поиск по email, first_name, last_name (опционально, регистронезависимый)

        Returns:
            Список пользователей, соответствующих фильтрам
        """
        query = select(User).where(User.is_deleted.is_(False))

        # Фильтр по is_active
        if is_active is not None:
            query = query.where(User.is_active.is_(is_active))

        # Фильтр по role
        if role is not None:
            query = query.where(User.role == role)

        # Поиск по email, first_name, last_name
        if search:
            search_term = f"%{search}%"
            query = query.where(
                or_(
                    User.email.ilike(search_term),
                    User.first_name.ilike(search_term),
                    User.last_name.ilike(search_term),
                )
            )

        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())
