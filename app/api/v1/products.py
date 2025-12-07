import uuid

from fastapi import APIRouter, Depends, Query, status

from app.api.dependencies.auth import require_admin
from app.api.dependencies.services import get_product_service
from app.models.user import User
from app.schemas.common import MessageResponse
from app.schemas.product import (
    ProductCreate,
    ProductUpdate,
    ProductResponse,
    ProductWithCategory,
)
from app.services.product_service import ProductService

router = APIRouter(prefix="/products", tags=["products"])


@router.post(
    "/",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Создать продукт",
    description="Создание нового продукта. Требуются права администратора.",
)
async def create_product(
    data: ProductCreate,
    service: ProductService = Depends(get_product_service),
    _: User = Depends(require_admin),
) -> ProductResponse:
    """
    Создание нового продукта.

    Args:
        data: Данные для создания продукта
        service: ProductService (инжектируется)
        _: Текущий пользователь-администратор (проверка прав)

    Returns:
        ProductResponse: Созданный продукт

    Raises:
        404: Категория не найдена
        409: Slug уже существует
        409: SKU уже существует
        403: Недостаточно прав (не admin)
    """
    return await service.create_product(data)


@router.get(
    "/search",
    response_model=list[ProductResponse],
    summary="Поиск продуктов",
    description="Комплексный поиск продуктов с фильтрами по названию, категории, цене и остаткам.",
)
async def search_products(
    search_term: str | None = Query(None, description="Поиск по названию или описанию"),
    category_id: uuid.UUID | None = Query(None, description="Фильтр по категории"),
    min_price: float | None = Query(None, ge=0, description="Минимальная цена"),
    max_price: float | None = Query(None, ge=0, description="Максимальная цена"),
    in_stock_only: bool = Query(False, description="Только товары в наличии"),
    active_only: bool = Query(True, description="Только активные товары"),
    skip: int = Query(0, ge=0, description="Количество записей для пропуска"),
    limit: int = Query(100, ge=1, le=100, description="Максимальное количество записей"),
    service: ProductService = Depends(get_product_service),
) -> list[ProductResponse]:
    """
    Поиск продуктов с фильтрами.

    Args:
        search_term: Поиск по названию или описанию (регистронезависимый)
        category_id: Фильтр по категории
        min_price: Минимальная цена
        max_price: Максимальная цена
        in_stock_only: Только товары с остатком > 0
        active_only: Только активные товары
        skip: Смещение для пагинации
        limit: Лимит записей (максимум 100)
        service: ProductService (инжектируется)

    Returns:
        list[ProductResponse]: Список найденных продуктов
    """
    return await service.search_products(
        search_term=search_term,
        category_id=category_id,
        min_price=min_price,
        max_price=max_price,
        in_stock_only=in_stock_only,
        active_only=active_only,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/low-stock",
    response_model=list[ProductResponse],
    summary="Получить продукты с низким остатком",
    description="Получение продуктов с остатком ниже порогового значения. Требуются права администратора.",
)
async def get_low_stock_products(
    threshold: int = Query(10, ge=0, description="Порог остатка"),
    skip: int = Query(0, ge=0, description="Количество записей для пропуска"),
    limit: int = Query(100, ge=1, le=100, description="Максимальное количество записей"),
    service: ProductService = Depends(get_product_service),
    _: User = Depends(require_admin),
) -> list[ProductResponse]:
    """
    Получение продуктов с низким остатком.

    Args:
        threshold: Порог остатка (по умолчанию 10)
        skip: Смещение для пагинации
        limit: Лимит записей (максимум 100)
        service: ProductService (инжектируется)
        _: Текущий пользователь-администратор (проверка прав)

    Returns:
        list[ProductResponse]: Список продуктов с остатком <= threshold

    Raises:
        403: Недостаточно прав (не admin)
    """
    return await service.get_low_stock_products(
        threshold=threshold,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/{product_id}",
    response_model=ProductResponse,
    summary="Получить продукт по ID",
    description="Получение продукта по его идентификатору.",
)
async def get_product(
    product_id: uuid.UUID,
    service: ProductService = Depends(get_product_service),
) -> ProductResponse:
    """
    Получение продукта по ID.

    Args:
        product_id: UUID продукта
        service: ProductService (инжектируется)

    Returns:
        ProductResponse: Продукт

    Raises:
        404: Продукт не найден
    """
    return await service.get_product(product_id)


@router.get(
    "/slug/{slug}",
    response_model=ProductResponse,
    summary="Получить продукт по slug",
    description="Получение продукта по URL-friendly идентификатору.",
)
async def get_product_by_slug(
    slug: str,
    service: ProductService = Depends(get_product_service),
) -> ProductResponse:
    """
    Получение продукта по slug.

    Args:
        slug: URL-friendly идентификатор продукта
        service: ProductService (инжектируется)

    Returns:
        ProductResponse: Продукт

    Raises:
        404: Продукт не найден
    """
    return await service.get_product_by_slug(slug)


@router.get(
    "/sku/{sku}",
    response_model=ProductResponse,
    summary="Получить продукт по SKU",
    description="Получение продукта по артикулу (SKU).",
)
async def get_product_by_sku(
    sku: str,
    service: ProductService = Depends(get_product_service),
) -> ProductResponse:
    """
    Получение продукта по SKU.

    Args:
        sku: Артикул продукта
        service: ProductService (инжектируется)

    Returns:
        ProductResponse: Продукт

    Raises:
        404: Продукт не найден
    """
    return await service.get_product_by_sku(sku)


@router.patch(
    "/{product_id}",
    response_model=ProductResponse,
    summary="Обновить продукт",
    description="Обновление существующего продукта. Требуются права администратора.",
)
async def update_product(
    product_id: uuid.UUID,
    data: ProductUpdate,
    service: ProductService = Depends(get_product_service),
    _: User = Depends(require_admin),
) -> ProductResponse:
    """
    Обновление продукта.

    Args:
        product_id: UUID продукта
        data: Данные для обновления
        service: ProductService (инжектируется)
        _: Текущий пользователь-администратор (проверка прав)

    Returns:
        ProductResponse: Обновленный продукт

    Raises:
        404: Продукт не найден
        404: Категория не найдена
        409: Slug уже существует
        409: SKU уже существует
        403: Недостаточно прав (не admin)
    """
    return await service.update_product(product_id, data)


@router.delete(
    "/{product_id}",
    response_model=MessageResponse,
    summary="Удалить продукт",
    description="Мягкое удаление продукта. Требуются права администратора.",
)
async def delete_product(
    product_id: uuid.UUID,
    service: ProductService = Depends(get_product_service),
    _: User = Depends(require_admin),
) -> MessageResponse:
    """
    Удаление продукта (soft delete).

    Args:
        product_id: UUID продукта для удаления
        service: ProductService (инжектируется)
        _: Текущий пользователь-администратор (проверка прав)

    Returns:
        MessageResponse: Сообщение об успешном удалении

    Raises:
        404: Продукт не найден
        403: Недостаточно прав (не admin)
    """
    await service.delete_product(product_id)
    return MessageResponse(message=f"Product {product_id} successfully deleted")


@router.post(
    "/{product_id}/stock/increase",
    response_model=ProductResponse,
    summary="Увеличить остаток продукта",
    description="Увеличение остатка продукта (поступление товара). Требуются права администратора.",
)
async def increase_stock(
    product_id: uuid.UUID,
    quantity: int = Query(..., gt=0, description="Количество для добавления"),
    service: ProductService = Depends(get_product_service),
    _: User = Depends(require_admin),
) -> ProductResponse:
    """
    Увеличение остатка продукта.

    Args:
        product_id: UUID продукта
        quantity: Количество для добавления (должно быть > 0)
        service: ProductService (инжектируется)
        _: Текущий пользователь-администратор (проверка прав)

    Returns:
        ProductResponse: Обновленный продукт

    Raises:
        400: Количество должно быть положительным
        404: Продукт не найден
        403: Недостаточно прав (не admin)
    """
    return await service.increase_stock(product_id, quantity)


@router.post(
    "/{product_id}/stock/decrease",
    response_model=ProductResponse,
    summary="Уменьшить остаток продукта",
    description="Уменьшение остатка продукта (продажа, резервирование). Требуются права администратора.",
)
async def decrease_stock(
    product_id: uuid.UUID,
    quantity: int = Query(..., gt=0, description="Количество для уменьшения"),
    service: ProductService = Depends(get_product_service),
    _: User = Depends(require_admin),
) -> ProductResponse:
    """
    Уменьшение остатка продукта.

    Args:
        product_id: UUID продукта
        quantity: Количество для уменьшения (должно быть > 0)
        service: ProductService (инжектируется)
        _: Текущий пользователь-администратор (проверка прав)

    Returns:
        ProductResponse: Обновленный продукт

    Raises:
        400: Количество должно быть положительным
        400: Недостаточно товара на складе
        404: Продукт не найден
        403: Недостаточно прав (не admin)
    """
    return await service.decrease_stock(product_id, quantity)
