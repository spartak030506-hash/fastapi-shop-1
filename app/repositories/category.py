import uuid

from sqlalchemy import select, exists
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.category import Category
from app.repositories.base import BaseRepository


class CategoryRepository(BaseRepository[Category]):
    """
    Репозиторий для работы с категориями.

    Наследует базовые CRUD операции и добавляет специфичные методы:
    - Поиск по slug
    - Проверка существования slug
    - Получение подкатегорий (children)
    - Получение корневых категорий (без parent)
    - Фильтрация по активности
    """

    def __init__(self, db: AsyncSession):
        super().__init__(Category, db)

    async def get_by_slug(
        self,
        slug: str,
        include_deleted: bool = False
    ) -> Category | None:
        """
        Получить категорию по slug.

        Args:
            slug: URL-friendly идентификатор категории
            include_deleted: Включать ли удаленные записи

        Returns:
            Категория или None
        """
        query = select(Category).where(Category.slug == slug)

        if not include_deleted:
            query = query.where(Category.is_deleted.is_(False))

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def slug_exists(
        self,
        slug: str,
        exclude_category_id: uuid.UUID | None = None
    ) -> bool:
        """
        Проверить существование slug в системе.

        Args:
            slug: Slug для проверки
            exclude_category_id: ID категории для исключения (для обновления)

        Returns:
            True если slug существует, False если свободен
        """
        # Создаем подзапрос для exists
        subquery = select(Category.id).where(
            Category.slug == slug,
            Category.is_deleted.is_(False)
        )

        if exclude_category_id:
            subquery = subquery.where(Category.id != exclude_category_id)

        # Используем exists() для проверки
        query = select(exists(subquery))
        result = await self.db.execute(query)
        return result.scalar()

    async def get_by_parent(
        self,
        parent_id: uuid.UUID,
        skip: int = 0,
        limit: int = 100,
        include_deleted: bool = False
    ) -> list[Category]:
        """
        Получить подкатегории (children) указанной категории.

        Args:
            parent_id: ID родительской категории
            skip: Количество записей для пропуска
            limit: Максимальное количество записей
            include_deleted: Включать ли удаленные записи

        Returns:
            Список подкатегорий
        """
        query = select(Category).where(Category.parent_id == parent_id)

        if not include_deleted:
            query = query.where(Category.is_deleted.is_(False))

        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_root_categories(
        self,
        skip: int = 0,
        limit: int = 100,
        include_deleted: bool = False
    ) -> list[Category]:
        """
        Получить корневые категории (без parent_id).

        Args:
            skip: Количество записей для пропуска
            limit: Максимальное количество записей
            include_deleted: Включать ли удаленные записи

        Returns:
            Список корневых категорий
        """
        query = select(Category).where(Category.parent_id.is_(None))

        if not include_deleted:
            query = query.where(Category.is_deleted.is_(False))

        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_active_categories(
        self,
        skip: int = 0,
        limit: int = 100
    ) -> list[Category]:
        """
        Получить активные категории.

        Args:
            skip: Количество записей для пропуска
            limit: Максимальное количество записей

        Returns:
            Список активных категорий
        """
        query = select(Category).where(
            Category.is_active.is_(True),
            Category.is_deleted.is_(False)
        )

        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def name_exists_in_parent(
        self,
        name: str,
        parent_id: uuid.UUID | None,
        exclude_category_id: uuid.UUID | None = None
    ) -> bool:
        """
        Проверить существование имени категории в рамках одного parent.
        (для соблюдения уникальности на уровне приложения)

        Args:
            name: Имя категории
            parent_id: ID родительской категории (None для корневых)
            exclude_category_id: ID категории для исключения (для обновления)

        Returns:
            True если имя существует в данном parent, False если свободно
        """
        # Создаем подзапрос для exists
        subquery = select(Category.id).where(
            Category.name == name,
            Category.is_deleted.is_(False)
        )

        # Обработка parent_id (может быть None)
        if parent_id is None:
            subquery = subquery.where(Category.parent_id.is_(None))
        else:
            subquery = subquery.where(Category.parent_id == parent_id)

        if exclude_category_id:
            subquery = subquery.where(Category.id != exclude_category_id)

        # Используем exists() для проверки
        query = select(exists(subquery))
        result = await self.db.execute(query)
        return result.scalar()
