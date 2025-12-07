import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.utils.validators import validate_slug


# Базовая схема с общими полями
class CategoryBase(BaseModel):
    """Базовая схема категории"""

    name: str = Field(..., min_length=1, max_length=255)
    slug: str = Field(..., min_length=1, max_length=255)
    description: str | None = Field(None, max_length=1000)


# Схема для создания категории
class CategoryCreate(CategoryBase):
    """Схема для создания категории"""

    parent_id: uuid.UUID | None = None
    is_active: bool = True

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    @field_validator("slug")
    @classmethod
    def validate_slug_format(cls, v: str) -> str:
        return validate_slug(v)


# Схема для обновления категории
class CategoryUpdate(BaseModel):
    """Схема для обновления категории"""

    name: str | None = Field(None, min_length=1, max_length=255)
    slug: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = Field(None, max_length=1000)
    parent_id: uuid.UUID | None = None
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


# Схема для ответа
class CategoryResponse(CategoryBase):
    """Схема ответа с данными категории"""

    id: uuid.UUID
    parent_id: uuid.UUID | None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
        frozen=True,
    )


# Краткая схема (для списков, вложенных объектов)
class CategoryShort(BaseModel):
    """Краткая схема категории"""

    id: uuid.UUID
    name: str
    slug: str
    parent_id: uuid.UUID | None

    model_config = ConfigDict(
        from_attributes=True,
        frozen=True,
    )


# Схема с вложенными подкатегориями (для иерархии)
class CategoryWithChildren(CategoryResponse):
    """Схема категории с подкатегориями"""

    children: list["CategoryShort"] = []

    model_config = ConfigDict(
        from_attributes=True,
        frozen=True,
    )
