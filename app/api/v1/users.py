import uuid as uuid_module
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.auth_service import AuthService
from app.repositories.user import UserRepository
from app.schemas.user import UserResponse, UserUpdate, UserPasswordChange
from app.schemas.common import MessageResponse
from app.api.dependencies import get_current_active_user, require_admin
from app.models.user import User


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
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """
    Обновить данные своего профиля (имя, фамилия, телефон).

    Требуется аутентификация (Bearer token).
    """
    user_repo = UserRepository(db)

    # Обновляем только переданные поля
    update_data = data.model_dump(exclude_unset=True)
    if update_data:
        updated_user = await user_repo.update(current_user.id, **update_data)
        return UserResponse.model_validate(updated_user)

    return UserResponse.model_validate(current_user)


@router.post(
    "/me/change-password",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Сменить пароль"
)
async def change_password(
    data: UserPasswordChange,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    """
    Сменить пароль.

    Требуется старый пароль для подтверждения.
    После смены пароля все refresh токены отзываются (выход на всех устройствах).

    Требуется аутентификация (Bearer token).
    """
    service = AuthService(db)
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
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    """
    Удалить свой аккаунт (soft delete).

    После удаления все refresh токены будут отозваны.
    Требуется аутентификация (Bearer token).
    """
    service = AuthService(db)
    await service.delete_user(current_user.id)

    return MessageResponse(message="Account deleted successfully")


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Получить пользователя по ID (только для админов)"
)
async def get_user_by_id(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
) -> UserResponse:
    """
    Получить данные пользователя по ID.

    Требуется роль ADMIN.
    """
    try:
        user_uuid = uuid_module.UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format"
        )

    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(user_uuid)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return UserResponse.model_validate(user)


@router.get(
    "/",
    response_model=list[UserResponse],
    status_code=status.HTTP_200_OK,
    summary="Получить список пользователей (только для админов)"
)
async def get_users_list(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
) -> list[UserResponse]:
    """
    Получить список всех пользователей с пагинацией.

    Требуется роль ADMIN.
    """
    user_repo = UserRepository(db)
    users = await user_repo.get_all(skip=skip, limit=limit)

    return [UserResponse.model_validate(user) for user in users]


@router.delete(
    "/{user_id}",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Удалить пользователя (только для админов)"
)
async def delete_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(require_admin),
) -> MessageResponse:
    """
    Удалить пользователя по ID (soft delete).

    Требуется роль ADMIN.
    Админ не может удалить сам себя через этот endpoint.
    """
    try:
        user_uuid = uuid_module.UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format"
        )

    # Проверка: админ не может удалить самого себя
    if user_uuid == current_admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot delete yourself. Use DELETE /users/me instead"
        )

    service = AuthService(db)
    await service.delete_user(user_uuid)

    return MessageResponse(message="User deleted successfully")
