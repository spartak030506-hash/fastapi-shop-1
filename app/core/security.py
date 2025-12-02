import hashlib 
import uuid
from datetime import datetime, timedelta, timezone
from jose import jwt
from passlib.context import CryptContext

from app.core.config import settings


# Контекст для хеширования паролей
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# Хеширование пароля с использованием bcrypt
def hash_password(password: str) -> str:
    return pwd_context.hash(password)


# Проверка пароля
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


# Создание access токена
def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({
        "exp": expire,
        "iat": now,
        "iss": settings.TOKEN_ISSUER,
        "jti": str(uuid.uuid4()),
        "type": "access",
    })

    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


# Создание refresh токена
def create_refresh_token(data: dict) -> str:
    """Создание refresh токена"""
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    expire = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({
        "exp": expire,
        "iat": now,
        "iss": settings.TOKEN_ISSUER,
        "jti": str(uuid.uuid4()),
        "type": "refresh",
    })
    return jwt.encode(to_encode, settings.REFRESH_TOKEN_SECRET, algorithm=settings.ALGORITHM)


# Декодирование access токена (бросает исключение при ошибке
def decode_access_token(token: str) -> dict:
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])


# Декодирование refresh токена (бросает исключение при ошибке
def decode_refresh_token(token: str) -> dict:
    return jwt.decode(token, settings.REFRESH_TOKEN_SECRET, algorithms=[settings.ALGORITHM])


# Хеширование refresh токена для хранения в БД (SHA-256
def hash_refresh_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()