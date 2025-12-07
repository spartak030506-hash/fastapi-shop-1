import re
from decimal import Decimal
from urllib.parse import urlparse


def validate_slug(slug: str) -> str:
    """
    Валидация slug (URL-friendly строки).

    Требования:
    - Только lowercase буквы, цифры и дефисы
    - Не может начинаться или заканчиваться дефисом
    - Минимум 1 символ

    Args:
        slug: Slug для проверки

    Returns:
        str: Валидный slug

    Raises:
        ValueError: Если slug не соответствует требованиям
    """
    if not slug:
        raise ValueError("Slug не может быть пустым")

    if not re.match(r"^[a-z0-9]+(?:-[a-z0-9]+)*$", slug):
        raise ValueError(
            "Slug должен содержать только строчные буквы, цифры и дефисы. "
            "Не может начинаться или заканчиваться дефисом"
        )

    return slug


def validate_url(url: str) -> str:
    """
    Валидация URL.

    Args:
        url: URL для проверки

    Returns:
        str: Валидный URL

    Raises:
        ValueError: Если URL невалидный
    """
    try:
        result = urlparse(url)
        if not all([result.scheme, result.netloc]):
            raise ValueError("URL должен содержать scheme (http/https) и domain")
        if result.scheme not in ["http", "https"]:
            raise ValueError("URL должен использовать http или https схему")
        return url
    except Exception as e:
        raise ValueError(f"Невалидный URL: {str(e)}")


def validate_positive_decimal(value: Decimal) -> Decimal:
    """
    Валидация что Decimal > 0.

    Args:
        value: Значение для проверки

    Returns:
        Decimal: Валидное значение

    Raises:
        ValueError: Если значение <= 0
    """
    if value <= 0:
        raise ValueError("Значение должно быть больше нуля")
    return value


def validate_non_negative_int(value: int) -> int:
    """
    Валидация что int >= 0.

    Args:
        value: Значение для проверки

    Returns:
        int: Валидное значение

    Raises:
        ValueError: Если значение < 0
    """
    if value < 0:
        raise ValueError("Значение не может быть отрицательным")
    return value


def validate_password_strength(password: str) -> str:
    """
    Проверка сложности пароля.

    Требования:
    - Минимум одна заглавная буква
    - Минимум одна строчная буква
    - Минимум одна цифра

    Args:
        password: Пароль для проверки

    Returns:
        str: Валидный пароль

    Raises:
        ValueError: Если пароль не соответствует требованиям
    """
    if not re.search(r"[A-Z]", password):
        raise ValueError("Пароль должен содержать хотя бы одну заглавную букву")
    if not re.search(r"[a-z]", password):
        raise ValueError("Пароль должен содержать хотя бы одну строчную букву")
    if not re.search(r"[0-9]", password):
        raise ValueError("Пароль должен содержать хотя бы одну цифру")
    return password
