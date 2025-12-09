import uuid

from sqlalchemy import select, or_, exists, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product import Product
from app.repositories.base import BaseRepository


class ProductRepository(BaseRepository[Product]):
    """
    Репозиторий для работы с продуктами.

    Наследует базовые CRUD операции и добавляет специфичные методы:
    - Поиск по slug и SKU
    - Проверка существования slug и SKU
    - Получение по категории
    - Фильтрация по активности и остаткам
    - Поиск по названию
    """

    def __init__(self, db: AsyncSession):
        super().__init__(Product, db)

    async def get_by_slug(
        self,
        slug: str,
        include_deleted: bool = False
    ) -> Product | None:
        """
        Получить продукт по slug.

        Args:
            slug: URL-friendly идентификатор продукта
            include_deleted: Включать ли удаленные записи

        Returns:
            Продукт или None
        """
        query = select(Product).where(Product.slug == slug)

        if not include_deleted:
            query = query.where(Product.is_deleted.is_(False))

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_sku(
        self,
        sku: str,
        include_deleted: bool = False
    ) -> Product | None:
        """
        Получить продукт по SKU (артикулу).

        Args:
            sku: Артикул продукта
            include_deleted: Включать ли удаленные записи

        Returns:
            Продукт или None
        """
        query = select(Product).where(Product.sku == sku)

        if not include_deleted:
            query = query.where(Product.is_deleted.is_(False))

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def slug_exists(
        self,
        slug: str,
        exclude_product_id: uuid.UUID | None = None
    ) -> bool:
        """
        Проверить существование slug в системе.

        Args:
            slug: Slug для проверки
            exclude_product_id: ID продукта для исключения (для обновления)

        Returns:
            True если slug существует, False если свободен
        """
        # Создаем подзапрос для exists
        subquery = select(Product.id).where(
            Product.slug == slug,
            Product.is_deleted.is_(False)
        )

        if exclude_product_id:
            subquery = subquery.where(Product.id != exclude_product_id)

        # Используем exists() для проверки
        query = select(exists(subquery))
        result = await self.db.execute(query)
        return result.scalar()

    async def sku_exists(
        self,
        sku: str,
        exclude_product_id: uuid.UUID | None = None
    ) -> bool:
        """
        Проверить существование SKU в системе.

        Args:
            sku: SKU для проверки
            exclude_product_id: ID продукта для исключения (для обновления)

        Returns:
            True если SKU существует, False если свободен
        """
        # Создаем подзапрос для exists
        subquery = select(Product.id).where(
            Product.sku == sku,
            Product.is_deleted.is_(False)
        )

        if exclude_product_id:
            subquery = subquery.where(Product.id != exclude_product_id)

        # Используем exists() для проверки
        query = select(exists(subquery))
        result = await self.db.execute(query)
        return result.scalar()

    async def get_by_category(
        self,
        category_id: uuid.UUID,
        skip: int = 0,
        limit: int = 100,
        include_deleted: bool = False
    ) -> list[Product]:
        """
        Получить продукты по категории.

        Args:
            category_id: ID категории
            skip: Количество записей для пропуска
            limit: Максимальное количество записей
            include_deleted: Включать ли удаленные записи

        Returns:
            Список продуктов в категории
        """
        query = select(Product).where(Product.category_id == category_id)

        if not include_deleted:
            query = query.where(Product.is_deleted.is_(False))

        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_active_products(
        self,
        skip: int = 0,
        limit: int = 100
    ) -> list[Product]:
        """
        Получить активные продукты.

        Args:
            skip: Количество записей для пропуска
            limit: Максимальное количество записей

        Returns:
            Список активных продуктов
        """
        query = select(Product).where(
            Product.is_active.is_(True),
            Product.is_deleted.is_(False)
        )

        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def search_by_name(
        self,
        search_term: str,
        skip: int = 0,
        limit: int = 100,
        include_deleted: bool = False
    ) -> list[Product]:
        """
        Поиск продуктов по названию (регистронезависимый).

        Args:
            search_term: Поисковый запрос
            skip: Количество записей для пропуска
            limit: Максимальное количество записей
            include_deleted: Включать ли удаленные записи

        Returns:
            Список найденных продуктов
        """
        query = select(Product).where(
            Product.name.ilike(f"%{search_term}%")
        )

        if not include_deleted:
            query = query.where(Product.is_deleted.is_(False))

        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_low_stock_products(
        self,
        threshold: int = 10,
        skip: int = 0,
        limit: int = 100
    ) -> list[Product]:
        """
        Получить продукты с низким остатком.

        Args:
            threshold: Порог остатка (по умолчанию 10)
            skip: Количество записей для пропуска
            limit: Максимальное количество записей

        Returns:
            Список продуктов с остатком <= threshold
        """
        query = select(Product).where(
            Product.stock_quantity <= threshold,
            Product.is_deleted.is_(False)
        )

        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_out_of_stock_products(
        self,
        skip: int = 0,
        limit: int = 100
    ) -> list[Product]:
        """
        Получить продукты с нулевым остатком.

        Args:
            skip: Количество записей для пропуска
            limit: Максимальное количество записей

        Returns:
            Список продуктов с stock_quantity = 0
        """
        query = select(Product).where(
            Product.stock_quantity == 0,
            Product.is_deleted.is_(False)
        )

        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def search(
        self,
        search_term: str,
        category_id: uuid.UUID | None = None,
        min_price: float | None = None,
        max_price: float | None = None,
        in_stock_only: bool = False,
        active_only: bool = True,
        skip: int = 0,
        limit: int = 100
    ) -> list[Product]:
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
            Список найденных продуктов
        """
        query = select(Product).where(Product.is_deleted.is_(False))

        # Поиск по названию или описанию
        if search_term:
            query = query.where(
                or_(
                    Product.name.ilike(f"%{search_term}%"),
                    Product.description.ilike(f"%{search_term}%")
                )
            )

        # Фильтр по категории
        if category_id:
            query = query.where(Product.category_id == category_id)

        # Фильтр по цене
        if min_price is not None:
            query = query.where(Product.price >= min_price)
        if max_price is not None:
            query = query.where(Product.price <= max_price)

        # Только товары в наличии
        if in_stock_only:
            query = query.where(Product.stock_quantity > 0)

        # Только активные товары
        if active_only:
            query = query.where(Product.is_active.is_(True))

        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def atomic_update_stock(
        self,
        product_id: uuid.UUID,
        quantity_delta: int
    ) -> Product | None:
        """
        Атомарное обновление остатка товара (thread-safe, race condition safe).

        Использует UPDATE с выражением: stock_quantity = stock_quantity + delta
        с проверкой что результат >= 0. Это гарантирует что при конкурентной
        нагрузке не произойдет oversell (продажа больше чем есть).

        Args:
            product_id: ID продукта
            quantity_delta: Изменение количества (может быть отрицательным)

        Returns:
            Product | None: Обновленный продукт или None если:
                - продукт не найден
                - недостаточно товара (stock_quantity + delta < 0)
        """
        # UPDATE products
        # SET stock_quantity = stock_quantity + quantity_delta
        # WHERE id = product_id
        #   AND is_deleted = False
        #   AND stock_quantity + quantity_delta >= 0
        stmt = (
            update(Product)
            .where(
                Product.id == product_id,
                Product.is_deleted.is_(False),
                # Проверка что новый остаток не будет отрицательным
                Product.stock_quantity + quantity_delta >= 0
            )
            .values(stock_quantity=Product.stock_quantity + quantity_delta)
            .returning(Product)
        )

        result = await self.db.execute(stmt)
        await self.db.flush()

        # Возвращаем обновленный продукт или None если update не выполнился
        return result.scalar_one_or_none()
