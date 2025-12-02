import re


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
