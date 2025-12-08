import uuid as uuid_module
from fastapi import APIRouter, Depends, status, HTTPException

from app.services.auth_service import AuthService
from app.services.user_service import UserService
from app.schemas.user import UserResponse, UserUpdate, UserPasswordChange
from app.schemas.common import MessageResponse
from app.api.dependencies import get_current_active_user, require_admin
from app.api.dependencies.services import get_auth_service, get_user_service
from app.models.user import User, UserRole


router = APIRouter(prefix="/users", tags=["Users"])


@router.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Получить свой профиль"
)
async def get_my_profile(
    current_user: User = Depends(get_current_active_user),
) -> UserResponse:
    """
    Получить данные своего профиля.

    Требуется аутентификация (Bearer token).
    """
    return UserResponse.model_validate(current_user)


@router.patch(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Обновить свой профиль"
)
async def update_my_profile(
    data: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    service: UserService = Depends(get_user_service),
) -> UserResponse:
    """
    Обновить данные своего профиля (имя, фамилия, телефон).

    Требуется аутентификация (Bearer token).
    """
    update_data = data.model_dump(exclude_unset=True)
    return await service.update_user(current_user.id, **update_data)


@router.post(
    "/me/change-password",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Сменить пароль"
)
async def change_password(
    data: UserPasswordChange,
    current_user: User = Depends(get_current_active_user),
    service: AuthService = Depends(get_auth_service)
) -> MessageResponse:
    """
    Сменить пароль.

    Требуется старый пароль для подтверждения.
    После смены пароля все refresh токены отзываются (выход на всех устройствах).

    Требуется аутентификация (Bearer token).
    """
    await service.change_password(
        current_user.id,
        data.old_password,
        data.new_password
    )

    return MessageResponse(message="Password changed successfully")


@router.delete(
    "/me",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Удалить свой аккаунт"
)
async def delete_my_account(
    current_user: User = Depends(get_current_active_user),
    service: AuthService = Depends(get_auth_service)
) -> MessageResponse:
    """
    Удалить свой аккаунт (soft delete).

    После удаления все refresh токены будут отозваны.
    Требуется аутентификация (Bearer token).
    """
    await service.delete_user(current_user.id)

    return MessageResponse(message="Account deleted successfully")


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Получить пользователя по ID (только для админов)"
)
async def get_user_by_id(
    user_id: uuid_module.UUID,
    service: UserService = Depends(get_user_service),
    _: User = Depends(require_admin),
) -> UserResponse:
    """
    Получить данные пользователя по ID.

    Требуется роль ADMIN.
    """
    return await service.get_user(user_id)


@router.get(
    "/",
    response_model=list[UserResponse],
    status_code=status.HTTP_200_OK,
    summary="Получить список пользователей (только для админов)"
)
async def get_users_list(
    skip: int = 0,
    limit: int = 100,
    is_active: bool | None = None,
    role: UserRole | None = None,
    search: str | None = None,
    service: UserService = Depends(get_user_service),
    _: User = Depends(require_admin),
) -> list[UserResponse]:
    """
    Получить список всех пользователей с пагинацией и фильтрацией.

    Query параметры:
    - skip: Количество записей для пропуска (пагинация)
    - limit: Максимум записей (max 100)
    - is_active: Фильтр по статусу активности (опционально)
    - role: Фильтр по роли (CUSTOMER/ADMIN, опционально)
    - search: Поиск по email, имени или фамилии (опционально)

    Требуется роль ADMIN.
    """
    return await service.list_users(
        skip=skip,
        limit=limit,
        is_active=is_active,
        role=role,
        search=search,
    )


@router.delete(
    "/{user_id}",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Удалить пользователя (только для админов)"
)
async def delete_user(
    user_id: uuid_module.UUID,
    service: AuthService = Depends(get_auth_service),
    current_admin: User = Depends(require_admin),
) -> MessageResponse:
    """
    Удалить пользователя по ID (soft delete).

    Требуется роль ADMIN.
    Админ не может удалить сам себя через этот endpoint.
    """
    # Проверка: админ не может удалить самого себя
    if user_id == current_admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot delete yourself. Use DELETE /users/me instead"
        )

    await service.delete_user(user_id)

    return MessageResponse(message="User deleted successfully")
