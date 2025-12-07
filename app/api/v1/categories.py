import uuid

from fastapi import APIRouter, Depends, Query, status

from app.api.dependencies.auth import require_admin
from app.api.dependencies.services import get_category_service
from app.models.user import User
from app.schemas.category import (
    CategoryCreate,
    CategoryUpdate,
    CategoryResponse,
    CategoryWithChildren,
)
from app.schemas.common import MessageResponse
from app.services.category_service import CategoryService

router = APIRouter(prefix="/categories", tags=["categories"])


@router.post(
    "/",
    response_model=CategoryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Создать категорию",
    description="Создание новой категории. Требуются права администратора.",
)
async def create_category(
    data: CategoryCreate,
    service: CategoryService = Depends(get_category_service),
    _: User = Depends(require_admin),
) -> CategoryResponse:
    """
    Создание новой категории.

    Args:
        data: Данные для создания категории
        service: CategoryService (инжектируется)
        _: Текущий пользователь-администратор (проверка прав)

    Returns:
        CategoryResponse: Созданная категория

    Raises:
        409: Slug уже существует
        409: Имя уже существует в рамках parent
        404: Родительская категория не найдена
        403: Недостаточно прав (не admin)
    """
    return await service.create_category(data)


@router.get(
    "/",
    response_model=list[CategoryResponse],
    summary="Получить корневые категории",
    description="Получение списка корневых категорий (без parent).",
)
async def get_root_categories(
    skip: int = Query(0, ge=0, description="Количество записей для пропуска"),
    limit: int = Query(100, ge=1, le=100, description="Максимальное количество записей"),
    service: CategoryService = Depends(get_category_service),
) -> list[CategoryResponse]:
    """
    Получение корневых категорий.

    Args:
        skip: Смещение для пагинации
        limit: Лимит записей (максимум 100)
        service: CategoryService (инжектируется)

    Returns:
        list[CategoryResponse]: Список корневых категорий
    """
    return await service.get_root_categories(skip=skip, limit=limit)


@router.get(
    "/{category_id}",
    response_model=CategoryResponse,
    summary="Получить категорию по ID",
    description="Получение категории по её идентификатору.",
)
async def get_category(
    category_id: uuid.UUID,
    service: CategoryService = Depends(get_category_service),
) -> CategoryResponse:
    """
    Получение категории по ID.

    Args:
        category_id: UUID категории
        service: CategoryService (инжектируется)

    Returns:
        CategoryResponse: Категория

    Raises:
        404: Категория не найдена
    """
    return await service.get_category(category_id)


@router.get(
    "/slug/{slug}",
    response_model=CategoryResponse,
    summary="Получить категорию по slug",
    description="Получение категории по URL-friendly идентификатору.",
)
async def get_category_by_slug(
    slug: str,
    service: CategoryService = Depends(get_category_service),
) -> CategoryResponse:
    """
    Получение категории по slug.

    Args:
        slug: URL-friendly идентификатор категории
        service: CategoryService (инжектируется)

    Returns:
        CategoryResponse: Категория

    Raises:
        404: Категория не найдена
    """
    return await service.get_category_by_slug(slug)


@router.get(
    "/{category_id}/subcategories",
    response_model=list[CategoryResponse],
    summary="Получить подкатегории",
    description="Получение всех подкатегорий указанной категории.",
)
async def get_subcategories(
    category_id: uuid.UUID,
    skip: int = Query(0, ge=0, description="Количество записей для пропуска"),
    limit: int = Query(100, ge=1, le=100, description="Максимальное количество записей"),
    service: CategoryService = Depends(get_category_service),
) -> list[CategoryResponse]:
    """
    Получение подкатегорий.

    Args:
        category_id: UUID родительской категории
        skip: Смещение для пагинации
        limit: Лимит записей (максимум 100)
        service: CategoryService (инжектируется)

    Returns:
        list[CategoryResponse]: Список подкатегорий

    Raises:
        404: Родительская категория не найдена
    """
    return await service.get_subcategories(category_id, skip=skip, limit=limit)


@router.patch(
    "/{category_id}",
    response_model=CategoryResponse,
    summary="Обновить категорию",
    description="Обновление существующей категории. Требуются права администратора.",
)
async def update_category(
    category_id: uuid.UUID,
    data: CategoryUpdate,
    service: CategoryService = Depends(get_category_service),
    _: User = Depends(require_admin),
) -> CategoryResponse:
    """
    Обновление категории.

    Args:
        category_id: UUID категории
        data: Данные для обновления
        service: CategoryService (инжектируется)
        _: Текущий пользователь-администратор (проверка прав)

    Returns:
        CategoryResponse: Обновленная категория

    Raises:
        404: Категория не найдена
        409: Slug уже существует
        409: Имя уже существует в рамках parent
        400: Попытка установить саму себя как parent
        400: Попытка создать циклическую зависимость
        403: Недостаточно прав (не admin)
    """
    return await service.update_category(category_id, data)


@router.delete(
    "/{category_id}",
    response_model=MessageResponse,
    summary="Удалить категорию",
    description="Мягкое удаление категории вместе со всеми подкатегориями. Требуются права администратора.",
)
async def delete_category(
    category_id: uuid.UUID,
    service: CategoryService = Depends(get_category_service),
    _: User = Depends(require_admin),
) -> MessageResponse:
    """
    Удаление категории (soft delete).

    ВНИМАНИЕ: Удаляет категорию вместе со всеми подкатегориями (cascade).

    Args:
        category_id: UUID категории для удаления
        service: CategoryService (инжектируется)
        _: Текущий пользователь-администратор (проверка прав)

    Returns:
        MessageResponse: Сообщение об успешном удалении

    Raises:
        404: Категория не найдена
        403: Недостаточно прав (не admin)
    """
    await service.delete_category(category_id)
    return MessageResponse(message=f"Category {category_id} successfully deleted")
