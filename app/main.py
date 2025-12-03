from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import api_router
from app.core.config import settings


def create_app() -> FastAPI:
    """
    Фабрика для создания FastAPI приложения.

    Returns:
        Настроенное FastAPI приложение
    """
    app = FastAPI(
        title="FastAPI Shop",
        description="E-commerce API с best practices",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # В production указать конкретные домены
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Подключение роутеров
    app.include_router(api_router, prefix="/api")

    @app.get("/", tags=["Root"])
    async def root():
        """Корневой endpoint для проверки работы API"""
        return {
            "message": "FastAPI Shop API",
            "version": "1.0.0",
            "docs": "/docs",
            "redoc": "/redoc"
        }

    @app.get("/health", tags=["Health"])
    async def health_check():
        """Health check endpoint"""
        return {"status": "ok"}

    return app


# Создание приложения
app = create_app()
