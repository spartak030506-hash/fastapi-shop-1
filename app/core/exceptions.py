"""
Доменные исключения приложения.

Все бизнес-логические ошибки должны наследоваться от DomainException.
В API-слое они маппятся на HTTP-коды через exception handlers.
"""

from typing import Any


# BASE EXCEPTIONS


class DomainException(Exception):
    """
    Базовое исключение для всех доменных ошибок.

    Attributes:
        message: Сообщение об ошибке
        status_code: HTTP статус код (по умолчанию 400)
        details: Дополнительные данные об ошибке
    """

    def __init__(
        self,
        message: str,
        status_code: int = 400,
        details: dict[str, Any] | None = None,
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class NotFoundError(DomainException):
    """Ресурс не найден (404)"""

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(message, status_code=404, details=details)


class ConflictError(DomainException):
    """Конфликт при создании/обновлении ресурса (409)"""

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(message, status_code=409, details=details)


class ValidationError(DomainException):
    """Ошибка валидации бизнес-правил (400)"""

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(message, status_code=400, details=details)


class UnauthorizedError(DomainException):
    """Не авторизован (401)"""

    def __init__(self, message: str = "Not authenticated", details: dict[str, Any] | None = None):
        super().__init__(message, status_code=401, details=details)


class ForbiddenError(DomainException):
    """Доступ запрещен (403)"""

    def __init__(self, message: str = "Not enough permissions", details: dict[str, Any] | None = None):
        super().__init__(message, status_code=403, details=details)


# USER DOMAIN EXCEPTIONS


class UserNotFoundError(NotFoundError):
    """Пользователь не найден"""

    def __init__(self, user_id: str | None = None):
        message = f"User with ID {user_id} not found" if user_id else "User not found"
        super().__init__(message, details={"user_id": user_id} if user_id else {})


class EmailAlreadyExistsError(ConflictError):
    """Email уже занят"""

    def __init__(self, email: str):
        super().__init__(
            f"User with email '{email}' already exists",
            details={"email": email, "field": "email"},
        )


class UserInactiveError(ForbiddenError):
    """Пользователь неактивен"""

    def __init__(self, user_id: str | None = None):
        message = "User account is inactive"
        super().__init__(message, details={"user_id": user_id} if user_id else {})


class InvalidCredentialsError(UnauthorizedError):
    """Неверные учетные данные"""

    def __init__(self):
        super().__init__("Incorrect email or password")


class InvalidTokenError(UnauthorizedError):
    """Невалидный токен"""

    def __init__(self, reason: str = "Invalid token"):
        super().__init__(reason)


class TokenExpiredError(UnauthorizedError):
    """Токен истек"""

    def __init__(self):
        super().__init__("Token has expired")


class RefreshTokenNotFoundError(UnauthorizedError):
    """Refresh token не найден"""

    def __init__(self):
        super().__init__("Refresh token not found or has been revoked")


# ============================================================================
# CATEGORY DOMAIN EXCEPTIONS
# ============================================================================


class CategoryNotFoundError(NotFoundError):
    """Категория не найдена"""

    def __init__(self, category_id: str | None = None, slug: str | None = None):
        if slug:
            message = f"Category with slug '{slug}' not found"
            details = {"slug": slug}
        elif category_id:
            message = f"Category with ID {category_id} not found"
            details = {"category_id": category_id}
        else:
            message = "Category not found"
            details = {}
        super().__init__(message, details=details)


class CategorySlugAlreadyExistsError(ConflictError):
    """Slug категории уже существует"""

    def __init__(self, slug: str):
        super().__init__(
            f"Category with slug '{slug}' already exists",
            details={"slug": slug, "field": "slug"},
        )


class CategoryNameAlreadyExistsError(ConflictError):
    """Имя категории уже существует в рамках parent"""

    def __init__(self, name: str, parent_id: str | None = None):
        message = f"Category with name '{name}' already exists in this parent category"
        details = {"name": name, "field": "name"}
        if parent_id:
            details["parent_id"] = parent_id
        super().__init__(message, details=details)


class CircularCategoryDependencyError(ValidationError):
    """Циклическая зависимость в иерархии категорий"""

    def __init__(self, category_id: str, parent_id: str):
        super().__init__(
            "Cannot set parent category: this would create a circular dependency",
            details={"category_id": category_id, "parent_id": parent_id},
        )


class CategorySelfParentError(ValidationError):
    """Попытка установить категорию родителем самой себе"""

    def __init__(self, category_id: str):
        super().__init__(
            "Category cannot be its own parent",
            details={"category_id": category_id},
        )


# ============================================================================
# PRODUCT DOMAIN EXCEPTIONS
# ============================================================================


class ProductNotFoundError(NotFoundError):
    """Продукт не найден"""

    def __init__(
        self,
        product_id: str | None = None,
        slug: str | None = None,
        sku: str | None = None
    ):
        if sku:
            message = f"Product with SKU '{sku}' not found"
            details = {"sku": sku}
        elif slug:
            message = f"Product with slug '{slug}' not found"
            details = {"slug": slug}
        elif product_id:
            message = f"Product with ID {product_id} not found"
            details = {"product_id": product_id}
        else:
            message = "Product not found"
            details = {}
        super().__init__(message, details=details)


class ProductSlugAlreadyExistsError(ConflictError):
    """Slug продукта уже существует"""

    def __init__(self, slug: str):
        super().__init__(
            f"Product with slug '{slug}' already exists",
            details={"slug": slug, "field": "slug"},
        )


class ProductSKUAlreadyExistsError(ConflictError):
    """SKU продукта уже существует"""

    def __init__(self, sku: str):
        super().__init__(
            f"Product with SKU '{sku}' already exists",
            details={"sku": sku, "field": "sku"},
        )


class InsufficientStockError(ValidationError):
    """Недостаточно товара на складе"""

    def __init__(self, product_id: str, requested: int, available: int):
        super().__init__(
            f"Insufficient stock: requested {requested}, but only {available} available",
            details={
                "product_id": product_id,
                "requested": requested,
                "available": available,
            },
        )


class InvalidStockQuantityError(ValidationError):
    """Некорректное количество товара"""

    def __init__(self, quantity: int, reason: str = "Quantity must be positive"):
        super().__init__(
            reason,
            details={"quantity": quantity},
        )
