import hashlib 
import uuid
import bcrypt
import jwt
from datetime import datetime, timedelta, timezone

from app.core.config import settings


# Максимальная длина пароля для bcrypt (в байтах)
BCRYPT_MAX_BYTES = 72


def _ensure_password_length(password: str) -> None:
    """
    Проверка длины пароля в байтах для bcrypt.
    
    Бросает ValueError только если пароль реально больше 72 байт.
    
    Args:
        password: Пароль для проверки
        
    Raises:
        TypeError: Если password не строка
        ValueError: Если пароль больше 72 байт в UTF-8
    """
    if not isinstance(password, str):
        raise TypeError("password must be a string")
    
    if len(password.encode("utf-8")) > BCRYPT_MAX_BYTES:
        raise ValueError(
            "password cannot be longer than 72 bytes, truncate manually if necessary"
        )


def hash_password(password: str) -> str:
    """
    Хеширует пароль с использованием bcrypt.
    
    Args:
        password: Пароль для хеширования
        
    Returns:
        Хеш пароля в виде строки
        
    Raises:
        ValueError: Если пароль больше 72 байт
    """
    _ensure_password_length(password)
    
    # Генерируем salt и хешируем
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    
    # Возвращаем как строку
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Проверяет соответствие пароля и хеша.
    
    Args:
        plain_password: Открытый пароль
        hashed_password: Хеш пароля
        
    Returns:
        True если пароль совпадает, False в противном случае
        
    Note:
        - Пустой пароль → False
        - Пароль >72 байт → False (не бросаем исключение)
        - Любые ошибки bcrypt → False
    """
    # Пустой пароль считаем просто неверным
    if not plain_password:
        return False
    
    try:
        _ensure_password_length(plain_password)
    except ValueError:
        # Слишком длинный пароль — считаем неверным
        return False
    
    try:
        password_bytes = plain_password.encode('utf-8')
        hashed_bytes = hashed_password.encode('utf-8')
        return bcrypt.checkpw(password_bytes, hashed_bytes)
    except (ValueError, Exception):
        # Если bcrypt бросит любую ошибку — возвращаем False
        return False


# Создание access токена
def create_access_token(data: dict) -> str:
    """
    Создаёт access токен JWT.
    
    Args:
        data: Данные для включения в payload
        
    Returns:
        Закодированный JWT токен
    """
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
    """
    Создаёт refresh токен JWT.
    
    Args:
        data: Данные для включения в payload
        
    Returns:
        Закодированный JWT токен
    """
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


# Декодирование access токена (бросает исключение при ошибке)
def decode_access_token(token: str) -> dict:
    """
    Декодирует access токен JWT.
    
    Args:
        token: JWT токен для декодирования
        
    Returns:
        Payload токена в виде словаря
        
    Raises:
        jwt.InvalidTokenError: Если токен невалиден или истёк
    """
    return jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=[settings.ALGORITHM],
        options={
            "verify_signature": True,
            "verify_exp": True,
            "verify_iat": True,
        }
    )


# Декодирование refresh токена (бросает исключение при ошибке)
def decode_refresh_token(token: str) -> dict:
    """
    Декодирует refresh токен JWT.
    
    Args:
        token: JWT токен для декодирования
        
    Returns:
        Payload токена в виде словаря
        
    Raises:
        jwt.InvalidTokenError: Если токен невалиден или истёк
    """
    return jwt.decode(
        token,
        settings.REFRESH_TOKEN_SECRET,
        algorithms=[settings.ALGORITHM],
        options={
            "verify_signature": True,
            "verify_exp": True,
            "verify_iat": True,
        }
    )


# Хеширование refresh токена для хранения в БД (SHA-256)
def hash_refresh_token(token: str) -> str:
    """
    Создаёт SHA-256 хеш токена для безопасного хранения в БД.
    
    Args:
        token: Токен для хеширования
        
    Returns:
        SHA-256 хеш в hex формате (64 символа)
    """
    return hashlib.sha256(token.encode()).hexdigest()