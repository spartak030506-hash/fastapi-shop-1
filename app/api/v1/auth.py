from fastapi import APIRouter, Depends, status, Request

from app.services.auth_service import AuthService
from app.schemas.auth import (
    RegisterRequest,
    LoginRequest,
    TokenResponse,
    RefreshTokenRequest,
    MessageResponse,
    AuthResponse,
)
from app.api.dependencies import get_current_active_user
from app.api.dependencies.services import get_auth_service
from app.models.user import User


router = APIRouter(prefix="/auth", tags=["Authentication"])


def get_device_info(request: Request) -> str:
    """Извлечь User-Agent из запроса"""
    return request.headers.get("user-agent", "Unknown")


@router.post(
    "/register",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Регистрация нового пользователя"
)
async def register(
    data: RegisterRequest,
    request: Request,
    service: AuthService = Depends(get_auth_service)
) -> AuthResponse:
    """
    Регистрация нового пользователя.

    Возвращает пользователя и пару токенов (access + refresh).
    """
    device_info = get_device_info(request)

    user, tokens = await service.register(data, device_info)

    return AuthResponse(user=user, tokens=tokens)


@router.post(
    "/login",
    response_model=AuthResponse,
    status_code=status.HTTP_200_OK,
    summary="Вход в систему"
)
async def login(
    data: LoginRequest,
    request: Request,
    service: AuthService = Depends(get_auth_service)
) -> AuthResponse:
    """
    Аутентификация пользователя по email и паролю.

    Возвращает пользователя и пару токенов (access + refresh).
    """
    device_info = get_device_info(request)

    user, tokens = await service.login(data, device_info)

    return AuthResponse(user=user, tokens=tokens)


@router.post(
    "/refresh",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Обновление токенов"
)
async def refresh_tokens(
    data: RefreshTokenRequest,
    request: Request,
    service: AuthService = Depends(get_auth_service)
) -> TokenResponse:
    """
    Обновление пары токенов по refresh токену.

    Старый refresh токен отзывается, выдаётся новая пара.
    """
    device_info = get_device_info(request)

    tokens = await service.refresh_tokens(data.refresh_token, device_info)

    return tokens


@router.post(
    "/logout",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Выход из системы"
)
async def logout(
    data: RefreshTokenRequest,
    service: AuthService = Depends(get_auth_service)
) -> MessageResponse:
    """
    Отзыв refresh токена (выход на текущем устройстве).

    Access токен продолжит работать до истечения срока действия.
    """
    await service.logout(data.refresh_token)

    return MessageResponse(message="Successfully logged out")


@router.post(
    "/logout-all",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Выход на всех устройствах"
)
async def logout_all_devices(
    current_user: User = Depends(get_current_active_user),
    service: AuthService = Depends(get_auth_service)
) -> MessageResponse:
    """
    Отзыв всех refresh токенов пользователя.

    Требуется аутентификация (Bearer token).
    """
    count = await service.logout_all_devices(current_user.id)

    return MessageResponse(message=f"Logged out from {count} device(s)")
