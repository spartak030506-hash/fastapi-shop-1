import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    CategoryNotFoundError,
    CategorySlugAlreadyExistsError,
    CategoryNameAlreadyExistsError,
    CircularCategoryDependencyError,
    CategorySelfParentError,
)
from app.models.category import Category
from app.repositories.category import CategoryRepository
from app.schemas.category import CategoryCreate, CategoryUpdate, CategoryResponse


class CategoryService:
    """
    Сервис для работы с категориями товаров.

    Содержит бизнес-логику для:
    - Создания категорий
    - Обновления категорий
    - Удаления категорий (soft delete)
    - Получения категорий и иерархии
    - Валидации бизнес-правил
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.category_repo = CategoryRepository(db)

    async def create_category(self, data: CategoryCreate) -> CategoryResponse:
        """
        Создание новой категории.

        Уникальность slug и (name + parent_id) гарантируется UNIQUE индексами БД.
        При дублировании SQLAlchemy выбросит IntegrityError, который обрабатывается
        глобально в main.py (возвращает 409 Conflict с деталями).

        Args:
            data: Данные для создания категории

        Returns:
            CategoryResponse: Созданная категория

        Raises:
            CategoryNotFoundError: Родительская категория не найдена
            IntegrityError: Нарушение уникальности (автоматически → 409 Conflict)
        """
        # Проверка существования parent категории
        if data.parent_id:
            parent = await self.category_repo.get_by_id(data.parent_id)
            if not parent:
                raise CategoryNotFoundError(category_id=str(data.parent_id))

        # Создание категории
        # Уникальность slug и name+parent_id проверяется на уровне БД (UNIQUE индексы)
        category = Category(
            id=uuid.uuid4(),
            **data.model_dump()
        )

        category = await self.category_repo.create(category)
        return CategoryResponse.model_validate(category)

    async def update_category(
        self,
        category_id: uuid.UUID,
        data: CategoryUpdate
    ) -> CategoryResponse:
        """
        Обновление существующей категории.

        Уникальность slug и (name + parent_id) гарантируется UNIQUE индексами БД.
        При дублировании SQLAlchemy выбросит IntegrityError, который обрабатывается
        глобально в main.py (возвращает 409 Conflict с деталями).

        Args:
            category_id: ID категории
            data: Данные для обновления

        Returns:
            CategoryResponse: Обновленная категория

        Raises:
            CategoryNotFoundError: Категория не найдена
            CategorySelfParentError: Попытка установить саму себя как parent
            CircularCategoryDependencyError: Попытка создать циклическую зависимость
            IntegrityError: Нарушение уникальности (автоматически → 409 Conflict)
        """
        # Получение существующей категории
        category = await self.category_repo.get_by_id(category_id)
        if not category:
            raise CategoryNotFoundError(category_id=str(category_id))

        # Подготовка данных для обновления
        update_data = data.model_dump(exclude_unset=True)

        # Проверка parent_id (если меняется)
        if "parent_id" in update_data:
            new_parent_id = update_data["parent_id"]

            # Нельзя установить саму себя как parent
            if new_parent_id == category_id:
                raise CategorySelfParentError(str(category_id))

            # Проверка существования parent
            if new_parent_id:
                parent = await self.category_repo.get_by_id(new_parent_id)
                if not parent:
                    raise CategoryNotFoundError(category_id=str(new_parent_id))

                # Проверка на циклическую зависимость
                if await self._creates_circular_dependency(category_id, new_parent_id):
                    raise CircularCategoryDependencyError(
                        str(category_id),
                        str(new_parent_id)
                    )

        # Обновление категории
        # Уникальность slug и name+parent_id проверяется на уровне БД (UNIQUE индексы)
        updated_category = await self.category_repo.update(category_id, **update_data)
        return CategoryResponse.model_validate(updated_category)

    async def delete_category(self, category_id: uuid.UUID) -> None:
        """
        Мягкое удаление категории.

        ВАЖНО: Помечает is_deleted=True ТОЛЬКО для указанной категории.
        Подкатегории НЕ удаляются автоматически (soft delete не каскадируется).

        Args:
            category_id: ID категории для удаления

        Raises:
            CategoryNotFoundError: Категория не найдена
        """
        category = await self.category_repo.get_by_id(category_id)
        if not category:
            raise CategoryNotFoundError(category_id=str(category_id))

        # Soft delete (помечает только эту категорию, подкатегории остаются)
        await self.category_repo.soft_delete(category_id)

    async def get_category(self, category_id: uuid.UUID) -> CategoryResponse:
        """
        Получение категории по ID.

        Args:
            category_id: ID категории

        Returns:
            CategoryResponse: Категория

        Raises:
            CategoryNotFoundError: Категория не найдена
        """
        category = await self.category_repo.get_by_id(category_id)
        if not category:
            raise CategoryNotFoundError(category_id=str(category_id))

        return CategoryResponse.model_validate(category)

    async def get_category_by_slug(self, slug: str) -> CategoryResponse:
        """
        Получение категории по slug.

        Args:
            slug: URL-friendly идентификатор категории

        Returns:
            CategoryResponse: Категория

        Raises:
            CategoryNotFoundError: Категория не найдена
        """
        category = await self.category_repo.get_by_slug(slug)
        if not category:
            raise CategoryNotFoundError(slug=slug)

        return CategoryResponse.model_validate(category)

    async def get_root_categories(
        self,
        skip: int = 0,
        limit: int = 100
    ) -> list[CategoryResponse]:
        """
        Получение корневых категорий (без parent).

        Args:
            skip: Количество записей для пропуска
            limit: Максимальное количество записей

        Returns:
            list[CategoryResponse]: Список корневых категорий
        """
        categories = await self.category_repo.get_root_categories(skip=skip, limit=limit)
        return [CategoryResponse.model_validate(cat) for cat in categories]

    async def get_subcategories(
        self,
        parent_id: uuid.UUID,
        skip: int = 0,
        limit: int = 100
    ) -> list[CategoryResponse]:
        """
        Получение подкатегорий указанной категории.

        Args:
            parent_id: ID родительской категории
            skip: Количество записей для пропуска
            limit: Максимальное количество записей

        Returns:
            list[CategoryResponse]: Список подкатегорий

        Raises:
            CategoryNotFoundError: Родительская категория не найдена
        """
        parent = await self.category_repo.get_by_id(parent_id)
        if not parent:
            raise CategoryNotFoundError(category_id=str(parent_id))

        categories = await self.category_repo.get_by_parent(parent_id, skip=skip, limit=limit)
        return [CategoryResponse.model_validate(cat) for cat in categories]

    async def _creates_circular_dependency(
        self,
        category_id: uuid.UUID,
        new_parent_id: uuid.UUID
    ) -> bool:
        """
        Проверка создания циклической зависимости при изменении parent.

        Проходит вверх по иерархии от new_parent_id и проверяет,
        не встретится ли category_id на пути.

        Args:
            category_id: ID категории, которую хотим переместить
            new_parent_id: ID нового родителя

        Returns:
            True если создается циклическая зависимость, False иначе
        """
        current_id = new_parent_id

        # Проходим вверх по иерархии
        while current_id:
            if current_id == category_id:
                # Нашли циклическую зависимость
                return True

            current_category = await self.category_repo.get_by_id(current_id)
            if not current_category:
                break

            current_id = current_category.parent_id

        return False
