import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.utils.validators import (
    validate_slug,
    validate_url,
    validate_positive_decimal,
    validate_non_negative_int,
)
from app.schemas.category import CategoryShort


# Базовая схема с общими полями
class ProductBase(BaseModel):
    """Базовая схема продукта"""

    name: str = Field(..., min_length=1, max_length=255)
    slug: str = Field(..., min_length=1, max_length=255)
    description: str | None = Field(None, max_length=2000)
    price: Decimal = Field(..., gt=0)
    category_id: uuid.UUID
    stock_quantity: int = Field(default=0, ge=0)
    sku: str | None = Field(None, max_length=100)
    image_url: str | None = Field(None, max_length=500)
    is_active: bool = True


# Схема для создания продукта
class ProductCreate(ProductBase):
    """Схема для создания продукта"""

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    @field_validator("slug")
    @classmethod
    def validate_slug_format(cls, v: str) -> str:
        return validate_slug(v)

    @field_validator("price")
    @classmethod
    def validate_price_positive(cls, v: Decimal) -> Decimal:
        return validate_positive_decimal(v)

    @field_validator("stock_quantity")
    @classmethod
    def validate_stock_non_negative(cls, v: int) -> int:
        return validate_non_negative_int(v)

    @field_validator("image_url")
    @classmethod
    def validate_image_url_format(cls, v: str | None) -> str | None:
        if v is not None and v.strip():
            return validate_url(v)
        return v


# Схема для обновления продукта
class ProductUpdate(BaseModel):
    """Схема для обновления продукта"""

    name: str | None = Field(None, min_length=1, max_length=255)
    slug: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = Field(None, max_length=2000)
    price: Decimal | None = Field(None, gt=0)
    category_id: uuid.UUID | None = None
    stock_quantity: int | None = Field(None, ge=0)
    sku: str | None = Field(None, max_length=100)
    image_url: str | None = Field(None, max_length=500)
    is_active: bool | None = None

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    @field_validator("slug")
    @classmethod
    def validate_slug_format(cls, v: str | None) -> str | None:
        if v is not None:
            return validate_slug(v)
        return v

    @field_validator("price")
    @classmethod
    def validate_price_positive(cls, v: Decimal | None) -> Decimal | None:
        if v is not None:
            return validate_positive_decimal(v)
        return v

    @field_validator("stock_quantity")
    @classmethod
    def validate_stock_non_negative(cls, v: int | None) -> int | None:
        if v is not None:
            return validate_non_negative_int(v)
        return v

    @field_validator("image_url")
    @classmethod
    def validate_image_url_format(cls, v: str | None) -> str | None:
        if v is not None and v.strip():
            return validate_url(v)
        return v


# Схема для ответа
class ProductResponse(ProductBase):
    """Схема ответа с данными продукта"""

    id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
        frozen=True,
    )


# Схема для ответа с вложенной категорией
class ProductWithCategory(ProductResponse):
    """Схема продукта с данными категории"""

    category: CategoryShort

    model_config = ConfigDict(
        from_attributes=True,
        frozen=True,
    )


# Краткая схема (для списков)
class ProductShort(BaseModel):
    """Краткая схема продукта"""

    id: uuid.UUID
    name: str
    slug: str
    price: Decimal
    image_url: str | None
    is_active: bool

    model_config = ConfigDict(
        from_attributes=True,
        frozen=True,
    )
