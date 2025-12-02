import re
from pydantic import BaseModel, EmailStr, Field, field_validator


# Схема для регистрации
class RegisterRequest(BaseModel):
    """Схема запроса регистрации"""
    email: EmailStr
    password: str = Field(..., min_length=8)
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    phone: str | None = Field(None, max_length=20, pattern=r"^\+?[0-9\-() ]{7,20}$")

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


# Схема для входа
class LoginRequest(BaseModel):
    """Схема запроса входа"""
    email: EmailStr
    password: str


# Схема ответа с токенами
class TokenResponse(BaseModel):
    """Схема ответа с токенами"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


# Схема для refresh токена
class RefreshTokenRequest(BaseModel):
    """Схема запроса обновления токена"""
    refresh_token: str


# Схема ответа при успешной операции
class MessageResponse(BaseModel):
    """Схема ответа с сообщением"""
    message: str
