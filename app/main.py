from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError

from app.api.v1 import api_router
from app.core.config import settings
from app.core.exceptions import DomainException


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

    @app.exception_handler(DomainException)
    async def domain_exception_handler(request: Request, exc: DomainException):
        """
        Глобальный обработчик доменных исключений.

        Маппит все DomainException на соответствующие HTTP-коды с JSON-ответом.
        """
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "detail": exc.message,
                **exc.details,
            },
        )

    @app.exception_handler(IntegrityError)
    async def integrity_error_handler(request: Request, exc: IntegrityError):
        """
        Обработчик IntegrityError от SQLAlchemy.

        Отлавливает нарушения целостности БД (unique constraints, foreign keys, etc.)
        и возвращает 409 Conflict с детальной информацией.
        """
        # Извлекаем детали ошибки из оригинального исключения
        error_detail = str(exc.orig) if hasattr(exc, "orig") else str(exc)

        # Пытаемся определить тип нарушения constraint
        constraint_type = "unknown"
        if "unique constraint" in error_detail.lower():
            constraint_type = "unique_violation"
        elif "foreign key constraint" in error_detail.lower():
            constraint_type = "foreign_key_violation"
        elif "check constraint" in error_detail.lower():
            constraint_type = "check_violation"
        elif "not null constraint" in error_detail.lower():
            constraint_type = "not_null_violation"

        return JSONResponse(
            status_code=409,
            content={
                "detail": "Database integrity constraint violation",
                "constraint_type": constraint_type,
                "error": error_detail,
            },
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
