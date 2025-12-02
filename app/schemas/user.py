import re
import uuid
from datetime import datetime
from pydantic import BaseModel, EmailStr, ConfigDict, Field, field_validator

from app.models.user import UserRole


# Base schema с общими полями
class UserBase(BaseModel):
    """Базовая схема пользователя"""
    email: EmailStr
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    phone: str | None = Field(None, max_length=20, pattern=r"^\+?[0-9\-() ]{7,20}$")


# Схема для создания пользователя
class UserCreate(UserBase):
    """Схема для создания пользователя"""
    password: str = Field(..., min_length=8)

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Проверка сложности пароля"""
        if not re.search(r"[A-Z]", v):
            raise ValueError("Пароль должен содержать хотя бы одну заглавную букву")
        if not re.search(r"[a-z]", v):
            raise ValueError("Пароль должен содержать хотя бы одну строчную букву")
        if not re.search(r"[0-9]", v):
            raise ValueError("Пароль должен содержать хотя бы одну цифру")
        return v


# Схема для логина
class UserLogin(BaseModel):
    """Схема для логина пользователя"""
    email: EmailStr
    password: str


# Схема для обновления пользователя
class UserUpdate(BaseModel):
    """Схема для обновления пользователя"""
    first_name: str | None = Field(None, min_length=1, max_length=100)
    last_name: str | None = Field(None, min_length=1, max_length=100)
    phone: str | None = Field(None, max_length=20, pattern=r"^\+?[0-9\-() ]{7,20}$")

    model_config = ConfigDict(validate_assignment=True)


# Схема для изменения пароля
class UserPasswordChange(BaseModel):
    """Схема для изменения пароля"""
    old_password: str
    new_password: str = Field(..., min_length=8)

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        """Проверка сложности нового пароля"""
        if not re.search(r"[A-Z]", v):
            raise ValueError("Пароль должен содержать хотя бы одну заглавную букву")
        if not re.search(r"[a-z]", v):
            raise ValueError("Пароль должен содержать хотя бы одну строчную букву")
        if not re.search(r"[0-9]", v):
            raise ValueError("Пароль должен содержать хотя бы одну цифру")
        return v


# Схема для ответа (возвращаемая пользователю)
class UserResponse(UserBase):
    """Схема ответа с данными пользователя"""
    id: uuid.UUID
    role: UserRole
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Схема для краткого ответа (например, в списке)
class UserShort(BaseModel):
    """Краткая схема пользователя"""
    id: uuid.UUID
    email: EmailStr
    first_name: str
    last_name: str
    role: UserRole

    model_config = ConfigDict(from_attributes=True)
