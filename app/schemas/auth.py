from typing import Literal

from pydantic import BaseModel, EmailStr, ConfigDict, Field, field_validator

from app.utils.validators import validate_password_strength


# Схема для регистрации
class RegisterRequest(BaseModel):
    """Схема запроса регистрации"""
    email: EmailStr
    password: str = Field(..., min_length=8)
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    phone: str | None = Field(
        None,
        max_length=20,
        pattern=r"^\+?[0-9\-() ]{7,20}$",
    )

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,  # обрежет пробелы вокруг строк
    )

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        return validate_password_strength(v)


# Схема для входа
class LoginRequest(BaseModel):
    """Схема запроса входа"""
    email: EmailStr
    password: str

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )


# Схема ответа с токенами
class TokenResponse(BaseModel):
    """Схема ответа с токенами"""
    access_token: str
    refresh_token: str
    token_type: Literal["bearer"] = "bearer"

    model_config = ConfigDict(
        frozen=True,  # ответ иммутабелен
    )


# Схема для refresh токена
class RefreshTokenRequest(BaseModel):
    """Схема запроса обновления токена"""
    refresh_token: str

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )


# Схема ответа при успешной операции
class MessageResponse(BaseModel):
    """Схема ответа с сообщением"""
    message: str

    model_config = ConfigDict(
        frozen=True,
    )
