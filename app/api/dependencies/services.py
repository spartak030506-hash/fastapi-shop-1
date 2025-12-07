from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.category_service import CategoryService
from app.services.product_service import ProductService


def get_category_service(db: AsyncSession = Depends(get_db)) -> CategoryService:
    """
    Dependency для получения CategoryService.

    Args:
        db: Сессия БД (инжектируется через get_db)

    Returns:
        CategoryService: Экземпляр сервиса категорий
    """
    return CategoryService(db)


def get_product_service(db: AsyncSession = Depends(get_db)) -> ProductService:
    """
    Dependency для получения ProductService.

    Args:
        db: Сессия БД (инжектируется через get_db)

    Returns:
        ProductService: Экземпляр сервиса продуктов
    """
    return ProductService(db)
