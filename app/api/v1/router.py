from fastapi import APIRouter

from app.api.v1 import auth, users


# Основной роутер для API v1
api_router = APIRouter(prefix="/v1")

# Подключение всех роутеров
api_router.include_router(auth.router)
api_router.include_router(users.router)

# В будущем добавляются так:
# api_router.include_router(products.router)
# api_router.include_router(orders.router)
