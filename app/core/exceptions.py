from fastapi import HTTPException, status


class NotFoundError(HTTPException):
    """Ресурс не найден"""

    def __init__(self, detail: str = "Ресурс не найден"):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class UnauthorizedError(HTTPException):
    """Неавторизованный доступ"""

    def __init__(self, detail: str = "Требуется авторизация"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )
