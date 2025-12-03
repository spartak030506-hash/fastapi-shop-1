import uuid
from typing import Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.user import User, UserRole
from app.repositories.user import UserRepository


# HTTP Bearer token схема для Swagger UI
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Dependency для получения текущего пользователя из access token.

    Args:
        credentials: Bearer token из Authorization заголовка
        db: Сессия базы данных

    Returns:
        User объект текущего пользователя

    Raises:
        HTTPException 401: Невалидный токен или пользователь не найден
    """
    token = credentials.credentials

    # Декодирование токена
    try:
        payload = decode_access_token(token)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Проверка типа токена
    token_type = payload.get("type")
    if token_type != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Получение user_id из токена
    user_id_str = payload.get("sub")
    if not user_id_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        user_id = uuid.UUID(user_id_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user ID in token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Получение пользователя из БД
    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Dependency для получения текущего АКТИВНОГО пользователя.

    Args:
        current_user: Пользователь из get_current_user

    Returns:
        User объект активного пользователя

    Raises:
        HTTPException 403: Пользователь неактивен
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )

    return current_user


async def get_current_verified_user(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """
    Dependency для получения текущего ВЕРИФИЦИРОВАННОГО пользователя.

    Args:
        current_user: Активный пользователь из get_current_active_user

    Returns:
        User объект верифицированного пользователя

    Raises:
        HTTPException 403: Пользователь не верифицирован
    """
    if not current_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User not verified"
        )

    return current_user


def require_role(*allowed_roles: UserRole) -> Callable:
    """
    Фабрика dependency для проверки роли пользователя.

    Args:
        *allowed_roles: Разрешённые роли (UserRole.ADMIN, UserRole.CUSTOMER)

    Returns:
        Dependency функция для использования в роутах

    Example:
        @router.get("/admin-only", dependencies=[Depends(require_role(UserRole.ADMIN))])
        async def admin_endpoint():
            return {"message": "Admin only"}
    """
    async def check_role(
        current_user: User = Depends(get_current_active_user),
    ) -> User:
        """
        Проверяет роль пользователя.

        Args:
            current_user: Активный пользователь

        Returns:
            User объект если роль разрешена

        Raises:
            HTTPException 403: Недостаточно прав
        """
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
        return current_user

    return check_role


# Готовые dependency для частых случаев
require_admin = require_role(UserRole.ADMIN)
require_customer = require_role(UserRole.CUSTOMER)
