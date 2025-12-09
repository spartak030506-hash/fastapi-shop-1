import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    ProductNotFoundError,
    ProductSlugAlreadyExistsError,
    ProductSKUAlreadyExistsError,
    CategoryNotFoundError,
    InsufficientStockError,
    InvalidStockQuantityError,
)
from app.models.product import Product
from app.repositories.product import ProductRepository
from app.repositories.category import CategoryRepository
from app.schemas.product import ProductCreate, ProductUpdate, ProductResponse


class ProductService:
    """
    Сервис для работы с продуктами.

    Содержит бизнес-логику для:
    - Создания и обновления продуктов
    - Управления остатками (stock)
    - Удаления продуктов (soft delete)
    - Поиска и фильтрации продуктов
    - Валидации бизнес-правил
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.product_repo = ProductRepository(db)
        self.category_repo = CategoryRepository(db)

    async def create_product(self, data: ProductCreate) -> ProductResponse:
        """
        Создание нового продукта.

        Уникальность slug и sku гарантируется UNIQUE индексами БД.
        При дублировании SQLAlchemy выбросит IntegrityError, который обрабатывается
        глобально в main.py (возвращает 409 Conflict с деталями).

        Args:
            data: Данные для создания продукта

        Returns:
            ProductResponse: Созданный продукт

        Raises:
            CategoryNotFoundError: Категория не найдена
            IntegrityError: Нарушение уникальности (автоматически → 409 Conflict)
        """
        # Проверка существования категории
        category = await self.category_repo.get_by_id(data.category_id)
        if not category:
            raise CategoryNotFoundError(category_id=str(data.category_id))

        # Создание продукта
        # Уникальность slug и sku проверяется на уровне БД (UNIQUE индексы)
        product = Product(
            id=uuid.uuid4(),
            **data.model_dump()
        )

        product = await self.product_repo.create(product)
        return ProductResponse.model_validate(product)

    async def update_product(
        self,
        product_id: uuid.UUID,
        data: ProductUpdate
    ) -> ProductResponse:
        """
        Обновление существующего продукта.

        Уникальность slug и sku гарантируется UNIQUE индексами БД.
        При дублировании SQLAlchemy выбросит IntegrityError, который обрабатывается
        глобально в main.py (возвращает 409 Conflict с деталями).

        Args:
            product_id: ID продукта
            data: Данные для обновления

        Returns:
            ProductResponse: Обновленный продукт

        Raises:
            ProductNotFoundError: Продукт не найден
            CategoryNotFoundError: Категория не найдена
            IntegrityError: Нарушение уникальности (автоматически → 409 Conflict)
        """
        # Получение существующего продукта
        product = await self.product_repo.get_by_id(product_id)
        if not product:
            raise ProductNotFoundError(product_id=str(product_id))

        # Подготовка данных для обновления
        update_data = data.model_dump(exclude_unset=True)

        # Проверка существования категории (если меняется)
        if "category_id" in update_data:
            category = await self.category_repo.get_by_id(update_data["category_id"])
            if not category:
                raise CategoryNotFoundError(category_id=str(update_data["category_id"]))

        # Обновление продукта
        # Уникальность slug и sku проверяется на уровне БД (UNIQUE индексы)
        updated_product = await self.product_repo.update(product_id, **update_data)
        return ProductResponse.model_validate(updated_product)

    async def delete_product(self, product_id: uuid.UUID) -> None:
        """
        Мягкое удаление продукта.

        Args:
            product_id: ID продукта для удаления

        Raises:
            ProductNotFoundError: Продукт не найден
        """
        product = await self.product_repo.get_by_id(product_id)
        if not product:
            raise ProductNotFoundError(product_id=str(product_id))

        await self.product_repo.soft_delete(product_id)

    async def get_product(self, product_id: uuid.UUID) -> ProductResponse:
        """
        Получение продукта по ID.

        Args:
            product_id: ID продукта

        Returns:
            ProductResponse: Продукт

        Raises:
            ProductNotFoundError: Продукт не найден
        """
        product = await self.product_repo.get_by_id(product_id)
        if not product:
            raise ProductNotFoundError(product_id=str(product_id))

        return ProductResponse.model_validate(product)

    async def get_product_by_slug(self, slug: str) -> ProductResponse:
        """
        Получение продукта по slug.

        Args:
            slug: URL-friendly идентификатор продукта

        Returns:
            ProductResponse: Продукт

        Raises:
            ProductNotFoundError: Продукт не найден
        """
        product = await self.product_repo.get_by_slug(slug)
        if not product:
            raise ProductNotFoundError(slug=slug)

        return ProductResponse.model_validate(product)

    async def get_product_by_sku(self, sku: str) -> ProductResponse:
        """
        Получение продукта по SKU (артикулу).

        Args:
            sku: Артикул продукта

        Returns:
            ProductResponse: Продукт

        Raises:
            ProductNotFoundError: Продукт не найден
        """
        product = await self.product_repo.get_by_sku(sku)
        if not product:
            raise ProductNotFoundError(sku=sku)

        return ProductResponse.model_validate(product)

    async def update_stock(
        self,
        product_id: uuid.UUID,
        quantity_delta: int
    ) -> ProductResponse:
        """
        Обновление остатка продукта (увеличение или уменьшение).

        ВАЖНО: Использует атомарный UPDATE для защиты от race conditions.
        При конкурентной нагрузке гарантирует что не произойдет oversell.

        Args:
            product_id: ID продукта
            quantity_delta: Изменение количества (может быть отрицательным)

        Returns:
            ProductResponse: Обновленный продукт

        Raises:
            ProductNotFoundError: Продукт не найден или недостаточно товара
            InsufficientStockError: Недостаточно товара на складе
        """
        # Атомарное обновление: UPDATE stock_quantity = stock_quantity + delta
        # WHERE stock_quantity + delta >= 0
        updated_product = await self.product_repo.atomic_update_stock(
            product_id,
            quantity_delta
        )

        # Если update не выполнился - либо продукт не найден, либо недостаточно товара
        if not updated_product:
            # Проверяем существование продукта для точного сообщения об ошибке
            product = await self.product_repo.get_by_id(product_id)
            if not product:
                raise ProductNotFoundError(product_id=str(product_id))

            # Продукт существует, значит недостаточно товара
            raise InsufficientStockError(
                str(product_id),
                abs(quantity_delta),
                product.stock_quantity
            )

        return ProductResponse.model_validate(updated_product)

    async def increase_stock(
        self,
        product_id: uuid.UUID,
        quantity: int
    ) -> ProductResponse:
        """
        Увеличение остатка продукта (поступление товара).

        Args:
            product_id: ID продукта
            quantity: Количество для добавления (должно быть > 0)

        Returns:
            ProductResponse: Обновленный продукт

        Raises:
            InvalidStockQuantityError: Количество должно быть положительным
            ProductNotFoundError: Продукт не найден
        """
        if quantity <= 0:
            raise InvalidStockQuantityError(quantity, "Quantity must be positive")

        return await self.update_stock(product_id, quantity)

    async def decrease_stock(
        self,
        product_id: uuid.UUID,
        quantity: int
    ) -> ProductResponse:
        """
        Уменьшение остатка продукта (продажа, резервирование).

        Args:
            product_id: ID продукта
            quantity: Количество для уменьшения (должно быть > 0)

        Returns:
            ProductResponse: Обновленный продукт

        Raises:
            InsufficientStockError: Недостаточно товара на складе
            InvalidStockQuantityError: Количество должно быть положительным
            ProductNotFoundError: Продукт не найден
        """
        if quantity <= 0:
            raise InvalidStockQuantityError(quantity, "Quantity must be positive")

        return await self.update_stock(product_id, -quantity)

    async def search_products(
        self,
        search_term: str | None = None,
        category_id: uuid.UUID | None = None,
        min_price: float | None = None,
        max_price: float | None = None,
        in_stock_only: bool = False,
        active_only: bool = True,
        skip: int = 0,
        limit: int = 100
    ) -> list[ProductResponse]:
        """
        Комплексный поиск продуктов с фильтрами.

        Args:
            search_term: Поиск по названию или описанию
            category_id: Фильтр по категории
            min_price: Минимальная цена
            max_price: Максимальная цена
            in_stock_only: Только товары в наличии
            active_only: Только активные товары
            skip: Количество записей для пропуска
            limit: Максимальное количество записей

        Returns:
            list[ProductResponse]: Список найденных продуктов
        """
        products = await self.product_repo.search(
            search_term=search_term or "",
            category_id=category_id,
            min_price=min_price,
            max_price=max_price,
            in_stock_only=in_stock_only,
            active_only=active_only,
            skip=skip,
            limit=limit
        )

        return [ProductResponse.model_validate(prod) for prod in products]

    async def get_low_stock_products(
        self,
        threshold: int = 10,
        skip: int = 0,
        limit: int = 100
    ) -> list[ProductResponse]:
        """
        Получение продуктов с низким остатком.

        Args:
            threshold: Порог остатка (по умолчанию 10)
            skip: Количество записей для пропуска
            limit: Максимальное количество записей

        Returns:
            list[ProductResponse]: Список продуктов с низким остатком
        """
        products = await self.product_repo.get_low_stock_products(
            threshold=threshold,
            skip=skip,
            limit=limit
        )

        return [ProductResponse.model_validate(prod) for prod in products]
