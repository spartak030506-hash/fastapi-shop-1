from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.category_service import CategoryService
from app.services.product_service import ProductService
from app.services.auth_service import AuthService
from app.services.user_service import UserService


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


def get_auth_service(db: AsyncSession = Depends(get_db)) -> AuthService:
    """
    Dependency для получения AuthService.

    Args:
        db: Сессия БД (инжектируется через get_db)

    Returns:
        AuthService: Экземпляр сервиса аунтификации
    """
    return AuthService(db)


def get_user_service(db: AsyncSession = Depends(get_db)) -> UserService:
    """
    Dependency для получения UserService.

    Args:
        db: Сессия БД (инжектируется через get_db)

    Returns:
        UserService: Экземпляр сервиса управления пользователями
    """
    return UserService(db)