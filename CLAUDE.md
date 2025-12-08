# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## E-commerce API - Best Practices Only

**Принцип разработки**: Пишем сразу production-ready код с best practices. Никаких устаревших решений, никаких TODO, никаких заглушек.

## Императивы

- **БЕЗОПАСНОСТЬ** - без компромиссов
- **BEST PRACTICES** - только современные подходы
- **ПОЛНОТА БЛОКА** - делаем функционал полностью и качественно
- **ЧИСТАЯ АРХИТЕКТУРА** - разделение ответственности, никаких коммитов в сервисах

---

## Правила работы с Claude Code

### Запуск тестов

**ВАЖНО:** Claude НЕ запускает тесты самостоятельно, если пользователь явно не попросил об этом.

**Причина:** Запуск тестов через pytest потребляет много токенов и времени.

**Правило:**
- ❌ НЕ запускай `pytest` без явного разрешения пользователя
- ✅ Напиши тесты и попроси пользователя запустить их
- ✅ После написания тестов скажи: "Тесты готовы. Можешь запустить: `pytest tests/...`"

**Пример:**
```
Я написал тесты для AuthService в tests/users/services/test_auth_service.py.
Можешь запустить их командой:
pytest tests/users/services/test_auth_service.py -v
```

---

## Текущий стек технологий

### Core
```
Python 3.11+
FastAPI 0.104.1
uvicorn[standard] 0.24.0
python-multipart 0.0.6
python-dotenv 1.0.0
```

### Database
```
SQLAlchemy 2.0.23 (async, Mapped, mapped_column)
asyncpg 0.29.0
alembic 1.12.1
PostgreSQL 15+
```

### Validation & Schemas
```
Pydantic 2.5.0 (ConfigDict, frozen, from_attributes)
pydantic-settings 2.1.0
email-validator 2.3.0
```

### Security
```
PyJWT 2.8.0+
bcrypt 4.0.0+
```

### Testing
```
pytest 7.4.3
pytest-asyncio 0.21.1
pytest-cov 4.1.0
httpx 0.25.2
```

### Code Quality (optional)
```
black 23.11.0
isort 5.12.0
flake8 6.1.0
mypy 1.7.0
```

### Future (установлено, не используется)
```
redis 5.0.1 - для кеширования при необходимости
```

---

## Архитектура

### 3-слойная архитектура

1. **API Layer** (`app/api/v1/`)
   - HTTP endpoints
   - Валидация запросов (Pydantic schemas)
   - Вызов сервисов
   - Возврат ответов

2. **Service Layer** (`app/services/`)
   - Бизнес-логика
   - Оркестрация репозиториев
   - **БЕЗ commit/rollback** (управляется в get_db)

3. **Repository Layer** (`app/repositories/`)
   - CRUD операции с БД
   - Только работа с данными
   - Generic типизация

### Управление транзакциями

**КРИТИЧНО:** Транзакции управляются в `get_db()` dependency.

Паттерн: **1 HTTP-запрос = 1 транзакция**

```python
# app/core/database.py
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()  # Автоматический commit при успехе
        except Exception:
            await session.rollback()  # Автоматический rollback при ошибке
            raise
        finally:
            await session.close()
```

**Сервисы НЕ делают commit/rollback!** Смотри: `app/services/auth_service.py`

---

## Структура проекта

```
app/
├── api/
│   ├── dependencies/
│   │   ├── auth.py              # get_current_user, require_role, require_admin
│   │   └── services.py          # get_auth_service, get_user_service, get_category_service, get_product_service
│   └── v1/
│       ├── router.py            # Главный роутер API v1
│       ├── auth.py              # Auth endpoints
│       ├── users.py             # Users endpoints
│       ├── categories.py        # Category endpoints
│       └── products.py          # Product endpoints
├── core/
│   ├── config.py                # Pydantic v2 settings
│   ├── database.py              # AsyncSession, get_db()
│   ├── security.py              # JWT, bcrypt, hash/verify
│   └── exceptions.py            # Custom HTTP exceptions
├── models/
│   ├── base.py                  # BaseModel (UUID, timestamps, soft delete)
│   ├── user.py                  # User model
│   ├── refresh_token.py         # RefreshToken model
│   ├── category.py              # Category model (иерархия)
│   └── product.py               # Product model
├── repositories/
│   ├── base.py                  # BaseRepository[T] (Generic CRUD)
│   ├── user.py                  # UserRepository
│   ├── refresh_token.py         # RefreshTokenRepository
│   ├── category.py              # CategoryRepository
│   └── product.py               # ProductRepository
├── schemas/
│   ├── __init__.py              # Exports всех схем
│   ├── user.py                  # User Pydantic schemas
│   ├── auth.py                  # Auth Pydantic schemas (AuthResponse!)
│   ├── category.py              # Category Pydantic schemas
│   ├── product.py               # Product Pydantic schemas
│   └── common.py                # MessageResponse (общие схемы)
├── services/
│   ├── auth_service.py          # AuthService (БЕЗ commit!)
│   ├── user_service.py          # UserService (БЕЗ commit!)
│   ├── category_service.py      # CategoryService (БЕЗ commit!)
│   └── product_service.py       # ProductService (БЕЗ commit!)
├── utils/
│   └── validators.py            # Validators (password, slug, URL, decimal, int)
└── main.py                      # FastAPI app

tests/
├── conftest.py                  # Корневой conftest - импортирует все fixtures
├── shared/                      # Общие компоненты для всех доменов
│   └── fixtures/
│       ├── db_fixtures.py       # БД fixtures (setup_database, db_session, event_loop)
│       └── client_fixtures.py   # HTTP client fixture
└── users/                       # Домен Users (аутентификация и пользователи)
    ├── fixtures/
    │   └── auth_fixtures.py     # Auth fixtures (test_user, test_admin, auth_headers)
    ├── api/                     # API endpoint tests (будущие)
    ├── repositories/            # Repository layer tests
    │   ├── test_user_repository.py
    │   └── test_refresh_token_repository.py
    ├── security/                # Security tests
    │   └── test_security_functions.py
    └── services/                # Service layer tests
        └── test_auth_service.py

alembic/
└── versions/
    ├── 450aefd42d81_initial_migration_users_and_refresh_.py
    ├── 4e6debc855da_улучшение_моделей_server_default_.py
    ├── 8f186bfe332d_add_category_and_product_models_with_.py
    └── 57a33d905860_add_image_url_to_product_model.py
```

---

## Реализованные модули (Production-Ready)

### ✅ Core & Infrastructure
- Database (SQLAlchemy 2.0 async)
- Security (JWT двойной секрет, bcrypt, SHA-256 для refresh токенов)
- Config (Pydantic v2 settings с .env)
- **Exceptions** (Доменные исключения + Exception handlers в main.py)
  - DomainException базовый класс (с status_code и details)
  - User domain: UserNotFoundError, EmailAlreadyExistsError, InvalidCredentialsError, etc.
  - Category domain: CategoryNotFoundError, CategorySlugAlreadyExistsError, CircularCategoryDependencyError, etc.
  - Product domain: ProductNotFoundError, InsufficientStockError, InvalidStockQuantityError, etc.
  - IntegrityError handler (автоматическая обработка нарушений БД → 409 Conflict)
- Migrations (Alembic, 4 миграции применены)

### ✅ Models (SQLAlchemy 2.0)
- **BaseModel** (UUID, created_at, updated_at, is_deleted, onupdate)
- **User** (роли: CUSTOMER/ADMIN, статусы: is_active/is_verified, lazy="selectin")
- **RefreshToken** (token_hash SHA-256, device_info, expires_at, индекс на expires_at)
- **Category** (иерархия parent/children, partial unique indexes с soft delete, is_active)
- **Product** (price Decimal(10,2), stock_quantity, SKU, image_url, CheckConstraints на уровне БД)

### ✅ Schemas (Pydantic v2)
- **User schemas** (frozen=True для responses, str_strip_whitespace для inputs)
- **Auth schemas** (AuthResponse вместо dict, Literal["bearer"], extra="forbid")
- **Category schemas** (Base, Create, Update, Response, Short, WithChildren)
- **Product schemas** (Base, Create, Update, Response, WithCategory, Short)
- **Validators**:
  - password strength (8+ chars, uppercase, lowercase, digits)
  - slug (URL-friendly format, lowercase + дефисы)
  - URL (http/https схемы)
  - positive_decimal (Decimal > 0)
  - non_negative_int (int >= 0)

### ✅ Repositories (Generic типизация)
- **BaseRepository[T]** (Generic CRUD, soft delete, type-safe)
- **UserRepository**:
  - email_exists, get_by_email, get_by_role
  - get_active_users, get_verified_users
  - **get_filtered_users** (is_active, role, search по email/name)
- **RefreshTokenRepository** (is_token_valid, revoke_token, revoke_all_user_tokens)
- **CategoryRepository**:
  - get_by_slug, slug_exists
  - get_by_parent (подкатегории)
  - get_root_categories (корневые категории)
  - name_exists_in_parent (уникальность в рамках parent)
  - get_active_categories
- **ProductRepository**:
  - get_by_slug, get_by_sku
  - slug_exists, sku_exists
  - get_by_category
  - get_active_products, get_low_stock_products, get_out_of_stock_products
  - search_by_name (регистронезависимый поиск)
  - search (комплексный поиск с фильтрами: название, категория, цена, наличие)

### ✅ Services

**Разделение ответственности:**

- **AuthService** - аутентификация и безопасность:
  - register, login, refresh_tokens
  - logout, logout_all_devices
  - change_password (меняет пароль + отзывает все токены)
  - **delete_user** (отзывает все токены + soft delete) - остается здесь, т.к. связанная операция

- **UserService** - CRUD операции с пользователями:
  - get_user (получение по ID с валидацией)
  - update_user (обновление профиля)
  - list_users (список с фильтрами: is_active, role, search)
  - Возвращает `UserResponse`, а не ORM объекты

- **CategoryService**:
  - create, update, delete
  - get_by_id, get_by_slug, get_root, get_subcategories
  - circular dependency detection (защита от циклов в иерархии)

- **ProductService**:
  - create, update, delete
  - get_by_id/slug/sku, search
  - stock management: increase/decrease/update

**ВАЖНО:** Все сервисы БЕЗ commit/rollback - транзакции управляются в get_db()

### ✅ API Endpoints
- **Dependencies**:
  - Auth: get_current_user, get_current_active_user, require_role, require_admin
  - Services: get_auth_service, get_user_service, get_category_service, get_product_service (Depends injection)
- **Auth endpoints** (/api/v1/auth):
  - POST /register, /login, /refresh, /logout, /logout-all
- **Users endpoints** (/api/v1/users):
  - GET /me, PATCH /me, POST /me/change-password, DELETE /me
  - GET /{user_id}, GET / (admin, с фильтрами: is_active, role, search)
  - DELETE /{user_id} (admin)
- **Category endpoints** (/api/v1/categories):
  - POST / (admin), GET /, GET /{id}, GET /slug/{slug}
  - GET /{id}/subcategories, PATCH /{id} (admin), DELETE /{id} (admin)
- **Product endpoints** (/api/v1/products):
  - POST / (admin), GET /search, GET /low-stock (admin)
  - GET /{id}, GET /slug/{slug}, GET /sku/{sku}
  - PATCH /{id} (admin), DELETE /{id} (admin)
  - POST /{id}/stock/increase (admin), POST /{id}/stock/decrease (admin)

### ✅ Tests (организация по доменам)
- **Структура по доменам**: tests организованы по доменным границам (users, будущие: categories, products)
- **Shared fixtures** (tests/shared/fixtures/):
  - db_fixtures.py: setup_database (autouse), db_session, event_loop
  - client_fixtures.py: HTTP client с переопределением БД
- **Users domain** (tests/users/):
  - fixtures/auth_fixtures.py: test_user, test_admin, test_inactive_user, auth_headers
  - repositories/: тесты UserRepository, RefreshTokenRepository (базовый CRUD + специфичные методы)
  - security/: unit-тесты security функций (hash_password, JWT, SHA-256)
  - services/: интеграционные тесты AuthService (@pytest.mark.integration)
- **Изоляция**: create/drop tables на каждый тест (autouse fixture setup_database)
- **Маркеры**: @pytest.mark.unit (пропускают БД), @pytest.mark.integration (требуют БД)

### ✅ Documentation
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

## Best Practices (НЕ НАРУШАТЬ)

### 1. SQLAlchemy 2.0 - современный синтаксис

**Используй:**
```python
from sqlalchemy.orm import Mapped, mapped_column

class User(BaseModel):
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)

    # Relationships с lazy="selectin" (избегаем N+1 проблемы)
    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(
        "RefreshToken",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
```

**НЕ используй:** `Column()`, `relationship()` без lazy, старый синтаксис

**Reference:** `app/models/user.py`, `app/models/base.py`

---

### 2. Pydantic v2 - правильная конфигурация

**Используй:**
```python
from pydantic import BaseModel, ConfigDict

# Для responses - frozen + from_attributes
class UserResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,  # для ORM объектов
        frozen=True,           # иммутабельный
    )

# Для requests - extra="forbid" + str_strip_whitespace
class LoginRequest(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

# Явные response schemas (НЕ dict!)
class AuthResponse(BaseModel):
    user: UserResponse
    tokens: TokenResponse

    model_config = ConfigDict(frozen=True)
```

**НЕ используй:** `class Config: orm_mode = True` (Pydantic v1), `response_model=dict`

**Reference:** `app/schemas/user.py`, `app/schemas/auth.py`

---

### 3. Datetime - ТОЛЬКО timezone-aware

**Используй:**
```python
from datetime import datetime, timezone

now = datetime.now(timezone.utc)  # ✅ ПРАВИЛЬНО
expire = now + timedelta(minutes=15)
```

**НЕ используй:**
```python
datetime.utcnow()  # ❌ УСТАРЕВШИЙ, без timezone
```

**Reference:** `app/core/security.py:107`, `app/services/auth_service.py:254`

---

### 4. Generic Repositories - type-safe

**Используй:**
```python
from typing import Generic, TypeVar
from app.models.base import BaseModel

ModelType = TypeVar("ModelType", bound=BaseModel)

class BaseRepository(Generic[ModelType]):
    def __init__(self, model: type[ModelType], db: AsyncSession):
        self.model = model
        self.db = db

    async def get_by_id(self, id: uuid.UUID) -> ModelType | None:
        # Автоматическая типизация
        ...

class UserRepository(BaseRepository[User]):
    def __init__(self, db: AsyncSession):
        super().__init__(User, db)
```

**Reference:** `app/repositories/base.py`

---

### 5. JWT Security - разные секреты

**Используй:**
```python
# Access token - короткий (15 мин), SECRET_KEY
access_token = create_access_token(data={"sub": str(user_id)})

# Refresh token - длинный (7 дней), REFRESH_TOKEN_SECRET (другой секрет!)
refresh_token = create_refresh_token(data={"sub": str(user_id)})

# Refresh токен хешируется в БД (SHA-256)
token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
```

**Payload токена:**
- `sub` - user_id
- `exp` - expiration
- `iat` - issued at
- `jti` - JWT ID (уникальный)
- `iss` - issuer ("fastapi-shop")
- `type` - "access" или "refresh"

**Reference:** `app/core/security.py`

---

### 6. Type Hints - современный синтаксис

**Используй:**
```python
def get_user(user_id: uuid.UUID) -> User | None:  # ✅ PEP 604
    ...

def get_list() -> list[User]:  # ✅ PEP 585
    ...
```

**НЕ используй:**
```python
from typing import Optional, Union, List  # ❌ Устаревший импорт
def get_user(user_id: uuid.UUID) -> Optional[User]:  # ❌
```

---

### 7. Endpoints = "Склейка" (Glue Code)

**КРИТИЧНО:** Endpoints содержат ТОЛЬКО склейку, вся логика в сервисах.

**Правильный паттерн:**
```python
@router.get("/{user_id}")
async def get_user_by_id(
    user_id: UUID,  # ✅ FastAPI автоматически валидирует UUID
    service: UserService = Depends(get_user_service),  # ✅ DI
    _: User = Depends(require_admin),  # ✅ Авторизация
) -> UserResponse:
    """
    Получить пользователя по ID.

    Требуется роль ADMIN.
    """
    return await service.get_user(user_id)  # ✅ Вся логика в сервисе
```

**Что остается в endpoints:**
- ✅ Получение параметров (path, query, body)
- ✅ Dependency Injection (сервисы, auth)
- ✅ Вызов метода сервиса
- ✅ Возврат response model

**Что УБРАТЬ из endpoints:**
- ❌ `db: AsyncSession = Depends(get_db)` - используй сервис
- ❌ `repo = UserRepository(db)` - репозитории только в сервисах
- ❌ `try: uuid.UUID(...) except ValueError` - валидация в сервисе или FastAPI
- ❌ `if not user: raise HTTPException` - бизнес-логика в сервисе
- ❌ Любые проверки, валидации, создание объектов

**Плохой пример (ДО):**
```python
@router.get("/{user_id}")
async def get_user_by_id(
    user_id: str,  # ❌ str вместо UUID
    db: AsyncSession = Depends(get_db),  # ❌ Прямой доступ к БД
    _: User = Depends(require_admin),
) -> UserResponse:
    # ❌ Валидация UUID в endpoint
    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID")

    # ❌ Создание репозитория в endpoint
    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(user_uuid)

    # ❌ Проверка существования в endpoint
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return UserResponse.model_validate(user)
```

**Хороший пример (ПОСЛЕ):**
```python
@router.get("/{user_id}")
async def get_user_by_id(
    user_id: UUID,  # ✅ FastAPI валидирует автоматически
    service: UserService = Depends(get_user_service),  # ✅ DI
    _: User = Depends(require_admin),
) -> UserResponse:
    return await service.get_user(user_id)  # ✅ Вся логика в сервисе
```

**Reference:** `app/api/v1/users.py` - эталонные endpoints

---

### 8. Async everywhere

**Используй:**
```python
async def get_user(db: AsyncSession, user_id: uuid.UUID):
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()
```

**НЕ используй:** sync функции для работы с БД

---

### 9. Сервисы возвращают Pydantic Schemas

**ВАЖНО:** Сервисы возвращают Pydantic schemas (`UserResponse`), а НЕ ORM объекты (`User`).

**Правильно:**
```python
# app/services/user_service.py
class UserService:
    async def get_user(self, user_id: UUID) -> UserResponse:  # ✅ Pydantic
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return UserResponse.model_validate(user)  # ✅ Конвертация в schema

    async def list_users(self, ...) -> list[UserResponse]:  # ✅ Pydantic list
        users = await self.user_repo.get_filtered_users(...)
        return [UserResponse.model_validate(u) for u in users]  # ✅
```

**Неправильно:**
```python
# ❌ ПЛОХО - возвращает ORM
class UserService:
    async def get_user(self, user_id: UUID) -> User:  # ❌ ORM объект
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(...)
        return user  # ❌ Возвращаем ORM напрямую
```

**Почему важно:**
1. **Консистентность** - endpoints получают готовые schemas
2. **Отделение слоёв** - ORM остаётся в repository layer
3. **Безопасность** - schemas контролируют, что отдаётся в API
4. **Иммутабельность** - response schemas frozen, нельзя случайно изменить

**Reference:**
- `app/services/user_service.py` - эталонная реализация
- `app/services/product_service.py` - тоже правильно
- `app/services/auth_service.py` - возвращает `UserResponse` + `TokenResponse`

---

### 10. Доменные исключения вместо HTTPException

**КРИТИЧНО:** Сервисы НЕ выбрасывают `HTTPException`, только доменные исключения из `app/core/exceptions.py`.

**Правильно:**
```python
from app.core.exceptions import (
    UserNotFoundError,
    EmailAlreadyExistsError,
    InvalidCredentialsError,
)

class AuthService:
    async def register(self, data: RegisterRequest):
        # ✅ Доменное исключение
        if await self.user_repo.email_exists(data.email):
            raise EmailAlreadyExistsError(data.email)

        user = User(...)
        return await self.user_repo.create(user)

    async def login(self, data: LoginRequest):
        user = await self.user_repo.get_by_email(data.email)

        # ✅ Доменное исключение
        if not user or not verify_password(data.password, user.hashed_password):
            raise InvalidCredentialsError()

        # ✅ Доменное исключение
        if not user.is_active:
            raise UserInactiveError(str(user.id))

        return tokens
```

**Неправильно:**
```python
from fastapi import HTTPException, status

class AuthService:
    async def register(self, data: RegisterRequest):
        # ❌ HTTPException в сервисе - ПЛОХО!
        if await self.user_repo.email_exists(data.email):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already exists"
            )
```

**Архитектура обработки исключений:**

```
Сервис (Service Layer)
    ↓ raise EmailAlreadyExistsError(email)

FastAPI Exception Handlers (app/main.py)
    ↓ @app.exception_handler(DomainException)

HTTP Response
    ↓ 409 Conflict + JSON {"detail": "...", "email": "...", "field": "email"}
```

**Exception Handlers в app/main.py:**

1. **domain_exception_handler** - обрабатывает все доменные исключения:
```python
@app.exception_handler(DomainException)
async def domain_exception_handler(request: Request, exc: DomainException):
    return JSONResponse(
        status_code=exc.status_code,  # 404, 409, 400, 401, 403...
        content={
            "detail": exc.message,
            **exc.details,  # Распаковка: email, field, user_id и др.
        },
    )
```

2. **integrity_error_handler** - ловит IntegrityError от SQLAlchemy:
```python
@app.exception_handler(IntegrityError)
async def integrity_error_handler(request: Request, exc: IntegrityError):
    # Парсит тип нарушения: unique_violation, foreign_key_violation, etc.
    return JSONResponse(
        status_code=409,
        content={
            "detail": "Database integrity constraint violation",
            "constraint_type": constraint_type,
            "error": error_detail,
        },
    )
```

**Доступные доменные исключения:**

**User Domain:**
- `UserNotFoundError(user_id)` → 404
- `EmailAlreadyExistsError(email)` → 409
- `UserInactiveError(user_id)` → 403
- `InvalidCredentialsError()` → 401
- `InvalidTokenError(reason)` → 401
- `TokenExpiredError()` → 401
- `RefreshTokenNotFoundError()` → 401

**Category Domain:**
- `CategoryNotFoundError(category_id, slug)` → 404
- `CategorySlugAlreadyExistsError(slug)` → 409
- `CategoryNameAlreadyExistsError(name, parent_id)` → 409
- `CircularCategoryDependencyError(category_id, parent_id)` → 400
- `CategorySelfParentError(category_id)` → 400

**Product Domain:**
- `ProductNotFoundError(product_id, slug, sku)` → 404
- `ProductSlugAlreadyExistsError(slug)` → 409
- `ProductSKUAlreadyExistsError(sku)` → 409
- `InsufficientStockError(product_id, requested, available)` → 400
- `InvalidStockQuantityError(quantity, reason)` → 400

**Преимущества:**
1. ✅ **Разделение ответственности** - сервисы не знают о HTTP
2. ✅ **Типизация** - IDE подсказывает, какие исключения может выбросить метод
3. ✅ **Централизация** - все HTTP-маппинги в одном месте (main.py)
4. ✅ **Безопасность** - IntegrityError автоматически обрабатывается
5. ✅ **Детализация** - в ответе есть structured данные (email, field, user_id, etc.)

**Reference:**
- `app/core/exceptions.py` - все доменные исключения
- `app/main.py` - exception handlers
- `app/services/auth_service.py` - пример использования

---

## Безопасность

### JWT токены
- **Access token**: 15 минут, подписан `SECRET_KEY`
- **Refresh token**: 7 дней, подписан `REFRESH_TOKEN_SECRET` (отдельный!)
- Refresh token хешируется в БД через SHA-256
- Все токены содержат: sub, exp, iat, jti, iss, type

### Пароли
- Bcrypt хеширование (bcrypt.hashpw + salt)
- Проверка длины (max 72 байта для bcrypt)
- Валидация силы: минимум 8 символов, uppercase, lowercase, цифры

### Прочее
- Soft delete везде (`is_deleted` флаг)
- UUID для всех ID
- CORS настроен (в production указать конкретные домены в `app/main.py`)
- Custom exceptions для стандартизации ошибок

**Reference:** `app/core/security.py`, `app/utils/validators.py`, `app/core/exceptions.py`

---

## API Endpoints (краткий список)

### Auth (`/api/v1/auth`)
- `POST /register` → AuthResponse (user + tokens)
- `POST /login` → AuthResponse (user + tokens)
- `POST /refresh` → TokenResponse (новые токены)
- `POST /logout` → MessageResponse (отзыв 1 токена)
- `POST /logout-all` → MessageResponse (отзыв всех токенов, требует auth)

### Users (`/api/v1/users`)
- `GET /me` → UserResponse (свой профиль)
- `PATCH /me` → UserResponse (обновить профиль)
- `POST /me/change-password` → MessageResponse
- `GET /{user_id}` → UserResponse (только admin)
- `GET /` → list[UserResponse] (список, только admin, пагинация)

### Categories (`/api/v1/categories`)
- `POST /` → CategoryResponse (создать, admin)
- `GET /` → list[CategoryResponse] (корневые, pagination)
- `GET /{id}` → CategoryResponse
- `GET /slug/{slug}` → CategoryResponse
- `GET /{id}/subcategories` → list[CategoryResponse]
- `PATCH /{id}` → CategoryResponse (обновить, admin)
- `DELETE /{id}` → MessageResponse (удалить, admin)

### Products (`/api/v1/products`)
- `POST /` → ProductResponse (создать, admin)
- `GET /search` → list[ProductResponse] (поиск с фильтрами)
- `GET /low-stock` → list[ProductResponse] (низкие остатки, admin)
- `GET /{id}` → ProductResponse
- `GET /slug/{slug}` → ProductResponse
- `GET /sku/{sku}` → ProductResponse
- `PATCH /{id}` → ProductResponse (обновить, admin)
- `DELETE /{id}` → MessageResponse (удалить, admin)
- `POST /{id}/stock/increase` → ProductResponse (admin)
- `POST /{id}/stock/decrease` → ProductResponse (admin)

**Полная документация endpoints с таблицами и примерами:** см. раздел "API Endpoints с Dependency Injection"

---

## Команды

### Миграции
```bash
# Создать миграцию
alembic revision --autogenerate -m "описание изменений"

# Применить миграции
alembic upgrade head

# Откатить на 1 миграцию назад
alembic downgrade -1
```

### Запуск приложения
```bash
# Development
uvicorn app.main:app --reload

# Production
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Тесты
```bash
# Запустить все тесты
pytest -v

# С покрытием
pytest --cov=app --cov-report=html

# Конкретный домен
pytest tests/users/ -v

# Конкретный слой в домене
pytest tests/users/repositories/ -v
pytest tests/users/services/ -v
pytest tests/users/security/ -v

# Конкретный файл
pytest tests/users/security/test_security_functions.py -v

# По маркерам
pytest -m unit -v           # Только unit-тесты (без БД)
pytest -m integration -v    # Только интеграционные тесты (с БД)

# Комбинации
pytest tests/users/ -m integration -v
```

### Проверка
```bash
# Health check
curl http://localhost:8000/health

# Документация
curl http://localhost:8000/docs
curl http://localhost:8000/redoc
```

### Code Quality
```bash
# Форматирование
black app tests
isort app tests

# Линтинг
flake8 app tests
mypy app
```

---

## Добавление нового модуля

**Пример: Products**

1. **Создай модель** (`app/models/product.py`)
   - Наследуй от `BaseModel`
   - Используй `Mapped`, `mapped_column`
   - lazy="selectin" для relationships

2. **Создай схемы** (`app/schemas/product.py`)
   - Request schemas (extra="forbid", str_strip_whitespace=True)
   - Response schemas (frozen=True, from_attributes=True)

3. **Создай репозиторий** (`app/repositories/product.py`)
   - Наследуй от `BaseRepository[Product]`
   - Добавь специфичные методы (search, filter, etc.)

4. **Создай сервис** (`app/services/product_service.py`)
   - Инжекти репозитории через __init__
   - Бизнес-логика БЕЗ commit/rollback

5. **Создай endpoints** (`app/api/v1/products.py`)
   - Используй dependencies (get_db, get_current_user, require_admin)
   - Явные response_model

6. **Подключи роутер** (`app/api/v1/router.py`)
   ```python
   from app.api.v1 import products
   api_router.include_router(products.router)
   ```

7. **Создай миграцию**
   ```bash
   alembic revision --autogenerate -m "Add products table"
   alembic upgrade head
   ```

8. **Напиши тесты** (организация по доменам, см. ниже)

**Reference implementation:** Auth module (user.py, auth_service.py, auth.py)

---

## Организация тестов по доменам

**Принцип**: Тесты организованы по доменным границам (users, categories, products, orders).

### Структура домена

Для нового домена (например, `products`) создай:

```
tests/
├── shared/                      # Уже существует
│   └── fixtures/
│       ├── db_fixtures.py
│       └── client_fixtures.py
└── products/                    # Новый домен
    ├── __init__.py
    ├── fixtures/
    │   ├── __init__.py
    │   └── product_fixtures.py  # Domain-specific fixtures
    ├── api/
    │   ├── __init__.py
    │   └── test_products_api.py
    ├── repositories/
    │   ├── __init__.py
    │   └── test_product_repository.py
    └── services/
        ├── __init__.py
        └── test_product_service.py
```

### Шаги создания тестов для нового домена

1. **Создай структуру папок**:
   ```bash
   mkdir tests/products
   mkdir tests/products/fixtures
   mkdir tests/products/api
   mkdir tests/products/repositories
   mkdir tests/products/services
   ```

2. **Создай fixtures** (`tests/products/fixtures/product_fixtures.py`):
   ```python
   import pytest
   from app.models.product import Product
   from decimal import Decimal

   @pytest.fixture
   async def test_product(db_session, test_category):
       """Создаёт тестовый продукт в БД"""
       product = Product(
           name="Test Product",
           slug="test-product",
           price=Decimal("100.00"),
           category_id=test_category.id,
           stock_quantity=10,
       )
       db_session.add(product)
       await db_session.commit()
       await db_session.refresh(product)
       return product
   ```

3. **Импортируй fixtures** в `tests/conftest.py`:
   ```python
   from tests.products.fixtures.product_fixtures import *  # noqa
   ```

4. **Напиши тесты репозитория**:
   ```python
   # tests/products/repositories/test_product_repository.py
   import pytest
   from app.repositories.product import ProductRepository

   @pytest.mark.integration
   class TestProductRepository:
       async def test_get_by_slug(self, db_session, test_product):
           repo = ProductRepository(db_session)
           result = await repo.get_by_slug(test_product.slug)
           assert result is not None
           assert result.id == test_product.id
   ```

5. **Напиши тесты сервиса**:
   ```python
   # tests/products/services/test_product_service.py
   import pytest
   from app.services.product_service import ProductService

   @pytest.mark.integration
   class TestProductService:
       async def test_increase_stock(self, db_session, test_product):
           service = ProductService(db_session)
           updated = await service.increase_stock(test_product.id, 5)
           assert updated.stock_quantity == 15
   ```

6. **Напиши тесты API** (когда endpoints готовы):
   ```python
   # tests/products/api/test_products_api.py
   import pytest
   from httpx import AsyncClient

   @pytest.mark.integration
   class TestProductsAPI:
       async def test_get_product_by_slug(self, client: AsyncClient, test_product):
           response = await client.get(f"/api/v1/products/slug/{test_product.slug}")
           assert response.status_code == 200
           assert response.json()["slug"] == test_product.slug
   ```

### Правила организации

1. **Маркеры**:
   - `@pytest.mark.unit` - для unit-тестов (не требуют БД, быстрые)
   - `@pytest.mark.integration` - для интеграционных тестов (требуют БД)

2. **Fixtures**:
   - **Shared fixtures** (db_session, client) → `tests/shared/fixtures/`
   - **Domain-specific fixtures** (test_product, test_category) → `tests/{domain}/fixtures/`

3. **Именование**:
   - Файлы тестов: `test_*.py`
   - Классы тестов: `Test{ComponentName}` (например, `TestProductRepository`)
   - Методы тестов: `test_{what_it_tests}` (например, `test_get_by_slug_returns_product`)

4. **Изоляция**:
   - Каждый тест получает чистую БД (setup_database fixture autouse)
   - Не полагайся на порядок выполнения тестов
   - Создавай все необходимые данные через fixtures

5. **Reference implementation**: `tests/users/` - эталонная структура доменных тестов

---

## Category & Product модули (Production-Ready)

### Category Model (app/models/category.py)

**Поля:**
- `name` - название категории (String 255)
- `slug` - URL-friendly идентификатор (String 255)
- `description` - описание (String 1000, nullable)
- `parent_id` - ID родительской категории (UUID, nullable, FK с CASCADE)
- `is_active` - активность категории (Boolean, default True)

**Relationships:**
- `parent` - родительская категория (self-referential, lazy="selectin")
- `children` - подкатегории (list, cascade="all, delete-orphan")
- `products` - товары в категории (list, cascade="all, delete-orphan")

**Индексы и ограничения:**
```python
# Partial unique index для slug (только для is_deleted=false)
Index("ix_category_slug", "slug", unique=True,
      postgresql_where=text("is_deleted = false"))

# Partial unique index для name в рамках parent_id
Index("ix_category_parent_name", "parent_id", "name", unique=True,
      postgresql_where=text("is_deleted = false"))
```

**Особенности:**
- Поддержка иерархии (неограниченная вложенность)
- Partial indexes для корректной работы с soft delete
- Автоматическая загрузка связей через lazy="selectin"

---

### Product Model (app/models/product.py)

**Поля:**
- `name` - название продукта (String 255)
- `slug` - URL-friendly идентификатор (String 255)
- `description` - описание (String 2000, nullable)
- `price` - цена (Numeric 10,2) **с CheckConstraint > 0**
- `category_id` - ID категории (UUID, FK с RESTRICT)
- `stock_quantity` - остаток (Integer, default 0) **с CheckConstraint >= 0**
- `sku` - артикул (String 100, nullable, unique)
- `image_url` - URL изображения (String 500, nullable)
- `is_active` - активность (Boolean, default True)

**Relationships:**
- `category` - категория товара (Many-to-One, lazy="selectin")

**Constraints и индексы:**
```python
# Валидация на уровне БД
CheckConstraint("price > 0", name="check_price_positive")
CheckConstraint("stock_quantity >= 0", name="check_stock_non_negative")

# Partial unique indexes
Index("ix_product_slug", "slug", unique=True,
      postgresql_where=text("is_deleted = false"))
Index("ix_product_sku", "sku", unique=True,
      postgresql_where=text("sku IS NOT NULL AND is_deleted = false"))
```

**Особенности:**
- CheckConstraints защищают от некорректных данных на уровне БД
- Decimal для цены (избегаем проблем с float)
- ondelete="RESTRICT" - нельзя удалить категорию с товарами
- Partial indexes для SKU учитывают NULL значения

---

### Pydantic Schemas

**Category Schemas (app/schemas/category.py):**
- `CategoryBase` - базовые поля (name, slug, description)
- `CategoryCreate` - создание + валидация slug
- `CategoryUpdate` - обновление (все поля optional)
- `CategoryResponse` - ответ API (frozen, from_attributes)
- `CategoryShort` - краткая версия для списков
- `CategoryWithChildren` - с вложенными подкатегориями

**Product Schemas (app/schemas/product.py):**
- `ProductBase` - базовые поля
- `ProductCreate` - создание + валидация (slug, price, stock, image_url)
- `ProductUpdate` - обновление (все поля optional)
- `ProductResponse` - ответ API
- `ProductWithCategory` - с вложенной категорией
- `ProductShort` - краткая версия

**Валидаторы (app/utils/validators.py):**
```python
validate_slug(slug: str) -> str
  # Только lowercase, цифры, дефисы
  # Регулярка: ^[a-z0-9]+(?:-[a-z0-9]+)*$

validate_url(url: str) -> str
  # Проверка схемы (http/https) и домена

validate_positive_decimal(value: Decimal) -> Decimal
  # value > 0

validate_non_negative_int(value: int) -> int
  # value >= 0
```

---

### Repositories

**CategoryRepository (app/repositories/category.py):**

Базовые CRUD + специфичные методы:
- `get_by_slug(slug)` - поиск по slug
- `slug_exists(slug, exclude_id)` - проверка уникальности
- `get_by_parent(parent_id)` - получить подкатегории
- `get_root_categories()` - корневые категории (parent_id IS NULL)
- `get_active_categories()` - только активные
- `name_exists_in_parent(name, parent_id)` - уникальность в рамках parent

**ProductRepository (app/repositories/product.py):**

Базовые CRUD + E-commerce методы:
- `get_by_slug(slug)`, `get_by_sku(sku)` - поиск
- `slug_exists()`, `sku_exists()` - проверка уникальности
- `get_by_category(category_id)` - товары категории
- `get_active_products()` - только активные
- `search_by_name(term)` - поиск по названию (ILIKE)
- `get_low_stock_products(threshold)` - низкие остатки
- `get_out_of_stock_products()` - stock_quantity = 0
- **`search(...)`** - комплексный поиск с фильтрами:
  ```python
  search(
      search_term="телефон",        # название или описание
      category_id=uuid,             # фильтр по категории
      min_price=1000, max_price=5000,  # диапазон цен
      in_stock_only=True,           # только в наличии
      active_only=True,             # только активные
      skip=0, limit=20              # пагинация
  )
  ```

---

### Примеры использования

**Работа с категориями:**
```python
from app.repositories import CategoryRepository
from app.models.category import Category

# Создание корневой категории
electronics = Category(
    name="Электроника",
    slug="electronics",
    description="Электронные устройства",
    is_active=True
)
category = await category_repo.create(electronics)

# Создание подкатегории
phones = Category(
    name="Телефоны",
    slug="phones",
    parent_id=electronics.id,
    is_active=True
)
await category_repo.create(phones)

# Получение подкатегорий
children = await category_repo.get_by_parent(electronics.id)

# Проверка slug
exists = await category_repo.slug_exists("phones")
```

**Работа с продуктами:**
```python
from app.repositories import ProductRepository
from app.models.product import Product
from decimal import Decimal

# Создание продукта
iphone = Product(
    name="iPhone 15 Pro",
    slug="iphone-15-pro",
    description="Флагманский смартфон Apple",
    price=Decimal("99999.00"),
    category_id=phones_id,
    stock_quantity=50,
    sku="APL-IPH15P-256",
    image_url="https://cdn.example.com/iphone15.jpg",
    is_active=True
)
product = await product_repo.create(iphone)

# Комплексный поиск
results = await product_repo.search(
    search_term="iPhone",
    category_id=phones_id,
    min_price=50000,
    max_price=150000,
    in_stock_only=True,
    active_only=True,
    skip=0,
    limit=20
)

# Товары с низким остатком
low_stock = await product_repo.get_low_stock_products(threshold=10)
```

---

### Services (Бизнес-логика)

**CategoryService (app/services/category_service.py):**

Методы:
- `create_category(data)` - создание с валидацией:
  - Проверка уникальности slug
  - Проверка уникальности name в рамках parent
  - Проверка существования parent категории
- `update_category(id, data)` - обновление с валидацией:
  - Проверка уникальности при изменении slug/name
  - Защита от установки самой себя как parent
  - **Проверка циклических зависимостей** (алгоритм обхода вверх по иерархии)
- `delete_category(id)` - soft delete с cascade (удаление всех подкатегорий)
- `get_category(id)` - получение по ID
- `get_category_by_slug(slug)` - получение по slug
- `get_root_categories(skip, limit)` - корневые категории с пагинацией
- `get_subcategories(parent_id, skip, limit)` - подкатегории с пагинацией

**Особенности:**
```python
async def _creates_circular_dependency(
    self, category_id: uuid.UUID, new_parent_id: uuid.UUID
) -> bool:
    """
    Проходит вверх по иерархии от new_parent_id
    и проверяет, не встретится ли category_id на пути.
    Защита от создания циклов: A → B → C → A
    """
    current_id = new_parent_id
    while current_id:
        if current_id == category_id:
            return True
        current_category = await self.category_repo.get_by_id(current_id)
        if not current_category:
            break
        current_id = current_category.parent_id
    return False
```

**ProductService (app/services/product_service.py):**

Методы:
- `create_product(data)` - создание с валидацией:
  - Проверка существования категории
  - Проверка уникальности slug
  - Проверка уникальности SKU (если указан)
- `update_product(id, data)` - обновление с валидацией
- `delete_product(id)` - soft delete
- `get_product(id)`, `get_product_by_slug(slug)`, `get_product_by_sku(sku)`
- **Stock Management** (управление остатками):
  - `update_stock(id, quantity_delta)` - базовый метод (может быть ±)
  - `increase_stock(id, quantity)` - поступление товара (валидация > 0)
  - `decrease_stock(id, quantity)` - продажа/резервирование (валидация остатков)
- `search_products(...)` - комплексный поиск с фильтрами
- `get_low_stock_products(threshold)` - мониторинг остатков

**Stock Management пример:**
```python
from app.core.exceptions import InsufficientStockError

# Увеличение остатка
await product_service.increase_stock(product_id, quantity=100)

# Уменьшение с проверкой
try:
    await product_service.decrease_stock(product_id, quantity=5)
except InsufficientStockError as e:
    # Доменное исключение с детальной информацией
    print(f"Недостаточно товара: запрошено {e.details['requested']}, доступно {e.details['available']}")
```

**ВАЖНО:**
- Сервисы НЕ делают commit/rollback - транзакции управляются в `get_db()`!
- Сервисы НЕ выбрасывают HTTPException - только доменные исключения!

---

### API Endpoints с Dependency Injection

**Dependency Pattern (BEST PRACTICE):**

```python
# app/api/dependencies/services.py
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.services.category_service import CategoryService

def get_category_service(db: AsyncSession = Depends(get_db)) -> CategoryService:
    """Dependency для инжекции CategoryService"""
    return CategoryService(db)

# Использование в endpoints:
@router.post("/categories")
async def create_category(
    data: CategoryCreate,
    service: CategoryService = Depends(get_category_service),  # ✅ ПРАВИЛЬНО
    _: User = Depends(require_admin),
) -> CategoryResponse:
    return await service.create_category(data)
```

**НЕ делай так:**
```python
# ❌ НЕПРАВИЛЬНО - создание вручную в endpoint
@router.post("/categories")
async def create_category(
    data: CategoryCreate,
    db: AsyncSession = Depends(get_db),
) -> CategoryResponse:
    service = CategoryService(db)  # ❌ Плохая практика
    return await service.create_category(data)
```

**Category Endpoints (/api/v1/categories):**

| Method | Path | Description | Auth | Response |
|--------|------|-------------|------|----------|
| POST | / | Создать категорию | Admin | CategoryResponse |
| GET | / | Корневые категории (pagination) | Public | list[CategoryResponse] |
| GET | /{id} | Получить по ID | Public | CategoryResponse |
| GET | /slug/{slug} | Получить по slug | Public | CategoryResponse |
| GET | /{id}/subcategories | Подкатегории (pagination) | Public | list[CategoryResponse] |
| PATCH | /{id} | Обновить категорию | Admin | CategoryResponse |
| DELETE | /{id} | Удалить (soft delete + cascade) | Admin | MessageResponse |

**Product Endpoints (/api/v1/products):**

| Method | Path | Description | Auth | Response |
|--------|------|-------------|------|----------|
| POST | / | Создать продукт | Admin | ProductResponse |
| GET | /search | Комплексный поиск с фильтрами | Public | list[ProductResponse] |
| GET | /low-stock | Продукты с низким остатком | Admin | list[ProductResponse] |
| GET | /{id} | Получить по ID | Public | ProductResponse |
| GET | /slug/{slug} | Получить по slug | Public | ProductResponse |
| GET | /sku/{sku} | Получить по SKU | Public | ProductResponse |
| PATCH | /{id} | Обновить продукт | Admin | ProductResponse |
| DELETE | /{id} | Удалить (soft delete) | Admin | MessageResponse |
| POST | /{id}/stock/increase | Увеличить остаток | Admin | ProductResponse |
| POST | /{id}/stock/decrease | Уменьшить остаток | Admin | ProductResponse |

**Пример GET /products/search:**
```http
GET /api/v1/products/search?search_term=iPhone&category_id=uuid&min_price=50000&max_price=150000&in_stock_only=true&skip=0&limit=20
```

Query параметры:
- `search_term` (optional) - поиск по названию/описанию (ILIKE)
- `category_id` (optional) - фильтр по категории
- `min_price`, `max_price` (optional) - диапазон цен
- `in_stock_only` (boolean, default: false) - только в наличии
- `active_only` (boolean, default: true) - только активные
- `skip`, `limit` - пагинация (limit max 100)

**Auth защита:**
- Public endpoints - доступны всем
- Admin endpoints - требуют `require_admin` dependency (проверка role == ADMIN)

---

## Следующие шаги (roadmap)

- [x] **Categories module** - модель, schemas, repositories, services, API endpoints ✅
- [x] **Products module** - модель, schemas, repositories, services, API endpoints ✅
- [x] **Domain Exceptions** - доменные исключения + exception handlers + IntegrityError обработка ✅
- [ ] Orders module (корзина, заказы, статусы)
- [ ] Redis cache (для частых запросов)
- [ ] Rate limiting (защита от abuse)
- [ ] Email notifications (регистрация, заказы)
- [ ] File uploads (изображения продуктов)
- [ ] Full-text search (PostgreSQL tsvector или Elasticsearch)

---

## Помни - Golden Rules

### Архитектура
✅ **3 слоя:** API (склейка) → Service (логика) → Repository (данные)
✅ **Endpoints = склейка:** только DI + вызов сервиса + return
✅ **Сервисы БЕЗ commit/rollback** - управляется в get_db()
✅ **Сервисы возвращают Pydantic schemas**, не ORM
✅ **Сервисы выбрасывают доменные исключения**, не HTTPException
✅ **Exception handlers в main.py** - маппят исключения на HTTP-коды
✅ **Dependency Injection:** get_auth_service, get_user_service, etc.

### Код
✅ **SQLAlchemy 2.0:** Mapped, mapped_column, lazy="selectin"
✅ **Pydantic v2:** ConfigDict, frozen=True, from_attributes=True
✅ **Type hints:** User | None, list[User] (PEP 604, 585)
✅ **Datetime:** datetime.now(timezone.utc) - НЕ utcnow()!
✅ **Generic:** BaseRepository[T], type-safe

### Безопасность
✅ **JWT:** разные секреты (SECRET_KEY, REFRESH_TOKEN_SECRET)
✅ **Refresh tokens:** SHA-256 в БД, 7 дней
✅ **Soft delete:** is_deleted везде
✅ **UUID:** для всех ID
✅ **IntegrityError:** автоматически обрабатывается → 409 Conflict
✅ **Доменные исключения:** structured errors с детальной информацией

### Тесты
✅ **По доменам:** tests/{domain}/{layer}/
✅ **Изоляция:** create/drop tables на каждый тест
✅ **Маркеры:** @pytest.mark.unit, @pytest.mark.integration
✅ **Не запускать без разрешения пользователя**

### Минимализм
✅ **Не over-engineer:** только то, что попросили
✅ **Полнота блока:** функционал делаем до конца
✅ **Production-ready:** никаких TODO, заглушек, устаревших решений
