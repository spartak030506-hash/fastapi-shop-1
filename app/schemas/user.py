import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, ConfigDict, Field, field_validator

from app.models.user import UserRole
from app.utils.validators import validate_password_strength


# Base schema с общими полями
class UserBase(BaseModel):
    """Базовая схема пользователя"""
    email: EmailStr
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    phone: str | None = Field(
        None,
        max_length=20,
        pattern=r"^\+?[0-9\-() ]{7,20}$",
    )


# Схема для создания пользователя
class UserCreate(UserBase):
    """Схема для создания пользователя"""
    password: str = Field(..., min_length=8, max_length=72)

    model_config = ConfigDict(extra="forbid")

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        return validate_password_strength(v)


# Схема для логина
class UserLogin(BaseModel):
    """Схема для логина пользователя"""
    email: EmailStr
    password: str

    model_config = ConfigDict(extra="forbid")


# Схема для обновления пользователя
class UserUpdate(BaseModel):
    """Схема для обновления пользователя"""
    first_name: str | None = Field(None, min_length=1, max_length=100)
    last_name: str | None = Field(None, min_length=1, max_length=100)
    phone: str | None = Field(
        None,
        max_length=20,
        pattern=r"^\+?[0-9\-() ]{7,20}$",
    )

    # validate_assignment убрал — обычно схемы не мутируют после создания
    model_config = ConfigDict(extra="forbid")


# Схема для изменения пароля
class UserPasswordChange(BaseModel):
    """Схема для изменения пароля"""
    old_password: str
    new_password: str = Field(..., min_length=8)

    model_config = ConfigDict(extra="forbid")

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        return validate_password_strength(v)


# Схема для ответа (возвращаемая пользователю)
class UserResponse(UserBase):
    """Схема ответа с данными пользователя"""
    id: uuid.UUID
    role: UserRole
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,  # можно создавать из ORM-объекта
        frozen=True,           # иммутабельный объект ответа
    )


# Схема для краткого ответа (например, в списке)
class UserShort(UserBase):
    """Краткая схема пользователя"""
    id: uuid.UUID
    role: UserRole

    model_config = ConfigDict(
        from_attributes=True,
        frozen=True,
    )
