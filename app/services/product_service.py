import uuid

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

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

        Args:
            data: Данные для создания продукта

        Returns:
            ProductResponse: Созданный продукт

        Raises:
            HTTPException 404: Категория не найдена
            HTTPException 409: Slug уже существует
            HTTPException 409: SKU уже существует
        """
        # Проверка существования категории
        category = await self.category_repo.get_by_id(data.category_id)
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Category with id {data.category_id} not found"
            )

        # Проверка уникальности slug
        if await self.product_repo.slug_exists(data.slug):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Product with slug '{data.slug}' already exists"
            )

        # Проверка уникальности SKU (если указан)
        if data.sku and await self.product_repo.sku_exists(data.sku):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Product with SKU '{data.sku}' already exists"
            )

        # Создание продукта
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

        Args:
            product_id: ID продукта
            data: Данные для обновления

        Returns:
            ProductResponse: Обновленный продукт

        Raises:
            HTTPException 404: Продукт не найден
            HTTPException 404: Категория не найдена
            HTTPException 409: Slug уже существует
            HTTPException 409: SKU уже существует
        """
        # Получение существующего продукта
        product = await self.product_repo.get_by_id(product_id)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with id {product_id} not found"
            )

        # Подготовка данных для обновления
        update_data = data.model_dump(exclude_unset=True)

        # Проверка существования категории (если меняется)
        if "category_id" in update_data:
            category = await self.category_repo.get_by_id(update_data["category_id"])
            if not category:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Category with id {update_data['category_id']} not found"
                )

        # Проверка уникальности slug (если меняется)
        if "slug" in update_data and update_data["slug"] != product.slug:
            if await self.product_repo.slug_exists(update_data["slug"], exclude_product_id=product_id):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Product with slug '{update_data['slug']}' already exists"
                )

        # Проверка уникальности SKU (если меняется)
        if "sku" in update_data and update_data["sku"] != product.sku:
            if update_data["sku"] and await self.product_repo.sku_exists(
                update_data["sku"],
                exclude_product_id=product_id
            ):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Product with SKU '{update_data['sku']}' already exists"
                )

        # Обновление продукта
        updated_product = await self.product_repo.update(product_id, **update_data)
        return ProductResponse.model_validate(updated_product)

    async def delete_product(self, product_id: uuid.UUID) -> None:
        """
        Мягкое удаление продукта.

        Args:
            product_id: ID продукта для удаления

        Raises:
            HTTPException 404: Продукт не найден
        """
        product = await self.product_repo.get_by_id(product_id)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with id {product_id} not found"
            )

        success = await self.product_repo.soft_delete(product_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with id {product_id} not found"
            )

    async def get_product(self, product_id: uuid.UUID) -> ProductResponse:
        """
        Получение продукта по ID.

        Args:
            product_id: ID продукта

        Returns:
            ProductResponse: Продукт

        Raises:
            HTTPException 404: Продукт не найден
        """
        product = await self.product_repo.get_by_id(product_id)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with id {product_id} not found"
            )

        return ProductResponse.model_validate(product)

    async def get_product_by_slug(self, slug: str) -> ProductResponse:
        """
        Получение продукта по slug.

        Args:
            slug: URL-friendly идентификатор продукта

        Returns:
            ProductResponse: Продукт

        Raises:
            HTTPException 404: Продукт не найден
        """
        product = await self.product_repo.get_by_slug(slug)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with slug '{slug}' not found"
            )

        return ProductResponse.model_validate(product)

    async def get_product_by_sku(self, sku: str) -> ProductResponse:
        """
        Получение продукта по SKU (артикулу).

        Args:
            sku: Артикул продукта

        Returns:
            ProductResponse: Продукт

        Raises:
            HTTPException 404: Продукт не найден
        """
        product = await self.product_repo.get_by_sku(sku)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with SKU '{sku}' not found"
            )

        return ProductResponse.model_validate(product)

    async def update_stock(
        self,
        product_id: uuid.UUID,
        quantity_delta: int
    ) -> ProductResponse:
        """
        Обновление остатка продукта (увеличение или уменьшение).

        Args:
            product_id: ID продукта
            quantity_delta: Изменение количества (может быть отрицательным)

        Returns:
            ProductResponse: Обновленный продукт

        Raises:
            HTTPException 404: Продукт не найден
            HTTPException 400: Недостаточно товара на складе
        """
        product = await self.product_repo.get_by_id(product_id)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with id {product_id} not found"
            )

        new_quantity = product.stock_quantity + quantity_delta

        # Проверка на отрицательный остаток
        if new_quantity < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient stock. Available: {product.stock_quantity}, requested: {abs(quantity_delta)}"
            )

        # Обновление остатка
        updated_product = await self.product_repo.update(
            product_id,
            stock_quantity=new_quantity
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
            HTTPException 400: Количество должно быть положительным
            HTTPException 404: Продукт не найден
        """
        if quantity <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Quantity must be positive"
            )

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
            HTTPException 400: Количество должно быть положительным
            HTTPException 400: Недостаточно товара на складе
            HTTPException 404: Продукт не найден
        """
        if quantity <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Quantity must be positive"
            )

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
