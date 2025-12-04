import pytest
import time
import jwt
from datetime import datetime, timedelta, timezone

from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_access_token,
    decode_refresh_token,
    hash_refresh_token,
)
from app.core.config import settings


# ============================================================================
# Тесты для hash_password() и verify_password()
# ============================================================================

@pytest.mark.unit
def test_hash_password_returns_different_hash_each_time():
    """Bcrypt должен генерировать разные хеши для одного пароля (из-за salt)"""
    password = "MySecretPassword123"
    hash1 = hash_password(password)
    hash2 = hash_password(password)

    assert hash1 != hash2
    assert len(hash1) > 0
    assert len(hash2) > 0


@pytest.mark.unit
def test_verify_password_with_correct_password():
    """Верификация пароля должна работать с корректным паролем"""
    password = "CorrectPassword123"
    hashed = hash_password(password)

    assert verify_password(password, hashed) is True


@pytest.mark.unit
def test_verify_password_with_incorrect_password():
    """Верификация пароля должна возвращать False для неверного пароля"""
    correct_password = "CorrectPassword123"
    wrong_password = "WrongPassword456"
    hashed = hash_password(correct_password)

    assert verify_password(wrong_password, hashed) is False


@pytest.mark.unit
def test_verify_password_with_empty_password():
    """Верификация пустого пароля должна возвращать False"""
    password = "SomePassword123"
    hashed = hash_password(password)

    assert verify_password("", hashed) is False


@pytest.mark.unit
def test_hash_password_with_special_characters():
    """Хеширование должно работать со спецсимволами"""
    password = "P@ssw0rd!#$%^&*()"
    hashed = hash_password(password)

    assert verify_password(password, hashed) is True


# ============================================================================
# Тесты для create_access_token() и decode_access_token()
# ============================================================================

@pytest.mark.unit
def test_create_access_token_valid_payload():
    """Access токен должен содержать корректные поля"""
    user_id = "123e4567-e89b-12d3-a456-426614174000"
    token = create_access_token(data={"sub": user_id})

    payload = decode_access_token(token)

    assert payload["sub"] == user_id
    assert payload["type"] == "access"
    assert payload["iss"] == settings.TOKEN_ISSUER
    assert "exp" in payload
    assert "iat" in payload
    assert "jti" in payload


@pytest.mark.unit
def test_decode_access_token_valid():
    """Декодирование валидного access токена должно работать"""
    user_id = "test-user-id"
    token = create_access_token(data={"sub": user_id})

    payload = decode_access_token(token)

    assert payload["sub"] == user_id
    assert payload["type"] == "access"


@pytest.mark.unit
def test_decode_access_token_expired():
    """Декодирование просроченного access токена должно вызывать jwt.ExpiredSignatureError"""
    user_id = "test-user-id"
    now = datetime.now(timezone.utc)
    past_time = now - timedelta(minutes=30)  # Истёк 30 минут назад

    payload = {
        "sub": user_id,
        "exp": past_time,
        "iat": past_time - timedelta(minutes=15),
        "iss": settings.TOKEN_ISSUER,
        "jti": "test-jti",
        "type": "access",
    }

    expired_token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    with pytest.raises(jwt.ExpiredSignatureError):
        decode_access_token(expired_token)


@pytest.mark.unit
def test_decode_access_token_invalid_signature():
    """Декодирование токена с неверной подписью должно вызывать jwt.InvalidSignatureError"""
    user_id = "test-user-id"
    token = create_access_token(data={"sub": user_id})

    # Подменяем подпись
    tampered_token = token[:-10] + "X" * 10

    with pytest.raises(jwt.InvalidSignatureError):
        decode_access_token(tampered_token)


@pytest.mark.unit
def test_decode_access_token_missing_fields():
    """Токен без обязательных полей всё равно декодируется (проверка на уровне приложения)"""
    # JWT сам по себе не требует обязательных полей, проверка должна быть в коде
    minimal_payload = {
        "sub": "user-id",
        "exp": datetime.now(timezone.utc) + timedelta(minutes=15),
    }

    token = jwt.encode(minimal_payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    payload = decode_access_token(token)

    assert payload["sub"] == "user-id"


@pytest.mark.unit
def test_access_token_with_custom_data():
    """Access токен должен поддерживать произвольные данные в payload"""
    custom_data = {
        "sub": "user-123",
        "role": "admin",
        "permissions": ["read", "write"],
    }

    token = create_access_token(data=custom_data)
    payload = decode_access_token(token)

    assert payload["sub"] == "user-123"
    assert payload["role"] == "admin"
    assert payload["permissions"] == ["read", "write"]


# ============================================================================
# Тесты для create_refresh_token() и decode_refresh_token()
# ============================================================================

@pytest.mark.unit
def test_create_refresh_token_valid_payload():
    """Refresh токен должен содержать type='refresh' и больший exp"""
    user_id = "test-user-id"
    access_token = create_access_token(data={"sub": user_id})
    refresh_token = create_refresh_token(data={"sub": user_id})

    access_payload = decode_access_token(access_token)
    refresh_payload = decode_refresh_token(refresh_token)

    assert refresh_payload["type"] == "refresh"
    assert refresh_payload["sub"] == user_id
    assert refresh_payload["exp"] > access_payload["exp"]  # Refresh живёт дольше


@pytest.mark.unit
def test_decode_refresh_token_valid():
    """Декодирование валидного refresh токена должно работать"""
    user_id = "test-user-id"
    token = create_refresh_token(data={"sub": user_id})

    payload = decode_refresh_token(token)

    assert payload["sub"] == user_id
    assert payload["type"] == "refresh"


@pytest.mark.unit
def test_decode_refresh_token_expired():
    """Декодирование просроченного refresh токена должно вызывать jwt.ExpiredSignatureError"""
    user_id = "test-user-id"
    now = datetime.now(timezone.utc)
    past_time = now - timedelta(days=10)  # Истёк 10 дней назад

    payload = {
        "sub": user_id,
        "exp": past_time,
        "iat": past_time - timedelta(days=7),
        "iss": settings.TOKEN_ISSUER,
        "jti": "test-jti",
        "type": "refresh",
    }

    expired_token = jwt.encode(payload, settings.REFRESH_TOKEN_SECRET, algorithm=settings.ALGORITHM)

    with pytest.raises(jwt.ExpiredSignatureError):
        decode_refresh_token(expired_token)


@pytest.mark.unit
def test_decode_refresh_token_with_wrong_secret():
    """Декодирование refresh токена с SECRET_KEY вместо REFRESH_TOKEN_SECRET должно вызывать jwt.InvalidSignatureError"""
    user_id = "test-user-id"
    # Создаём токен с правильным секретом
    token = create_refresh_token(data={"sub": user_id})

    # Пытаемся декодировать с неправильным секретом (SECRET_KEY)
    with pytest.raises(jwt.InvalidSignatureError):
        jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])


@pytest.mark.unit
def test_refresh_token_uses_different_secret_than_access():
    """Refresh токен должен использовать отдельный секрет"""
    user_id = "test-user-id"
    access_token = create_access_token(data={"sub": user_id})
    refresh_token = create_refresh_token(data={"sub": user_id})

    # Access токен не должен декодироваться REFRESH_TOKEN_SECRET
    with pytest.raises(jwt.InvalidSignatureError):
        jwt.decode(access_token, settings.REFRESH_TOKEN_SECRET, algorithms=[settings.ALGORITHM])

    # Refresh токен не должен декодироваться SECRET_KEY
    with pytest.raises(jwt.InvalidSignatureError):
        jwt.decode(refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])


# ============================================================================
# Тесты для hash_refresh_token()
# ============================================================================

@pytest.mark.unit
def test_hash_refresh_token_returns_sha256():
    """hash_refresh_token должен возвращать SHA-256 хеш (64 символа hex)"""
    token = "some-refresh-token-12345"
    token_hash = hash_refresh_token(token)

    assert len(token_hash) == 64  # SHA-256 в hex = 64 символа
    assert all(c in "0123456789abcdef" for c in token_hash)  # Только hex символы


@pytest.mark.unit
def test_hash_refresh_token_deterministic():
    """Одинаковый токен должен всегда давать одинаковый хеш"""
    token = "test-token-123"
    hash1 = hash_refresh_token(token)
    hash2 = hash_refresh_token(token)

    assert hash1 == hash2


@pytest.mark.unit
def test_hash_refresh_token_different_tokens():
    """Разные токены должны давать разные хеши"""
    token1 = "token-1"
    token2 = "token-2"

    hash1 = hash_refresh_token(token1)
    hash2 = hash_refresh_token(token2)

    assert hash1 != hash2