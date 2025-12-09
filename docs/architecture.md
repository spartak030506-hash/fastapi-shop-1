## Текущий стек технологий

### Core
Python 3.11+
FastAPI 0.104.1
uvicorn[standard] 0.24.0
python-multipart 0.0.6
python-dotenv 1.0.0

### Database
SQLAlchemy 2.0.23 (async, Mapped, mapped_column)
asyncpg 0.29.0
alembic 1.12.1
PostgreSQL 15+

### Validation & Schemas
Pydantic 2.5.0 (ConfigDict, frozen, from_attributes)
pydantic-settings 2.1.0
email-validator 2.3.0

### Security
PyJWT 2.8.0+
bcrypt 4.0.0+

### Testing
pytest 7.4.3
pytest-asyncio 0.21.1
pytest-cov 4.1.0
httpx 0.25.2

### Code Quality (optional)
black 23.11.0
isort 5.12.0
flake8 6.1.0
mypy 1.7.0

### Future (установлено, не используется)
redis 5.0.1 - для кеширования при необходимости

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

Сервисы НЕ делают commit/rollback! Смотри: app/services/auth_service.py

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
│   ├── auth.py                  # Auth schemas (register/login/refresh)
│   ├── user.py                  # User schemas
│   ├── category.py              # Category schemas
│   └── product.py               # Product schemas
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

## Реализованные модули (Production-Ready)

### ✅ Core & Infrastructure
- **Database** (SQLAlchemy 2.0 async)
- **Security** (JWT двойной секрет, bcrypt, SHA-256 для refresh токенов)
- **Config** (Pydantic v2 settings с .env)
- **Exceptions** (Доменные исключения + Exception handlers в main.py)
  - DomainException базовый класс (с status_code и details)
  - User domain: UserNotFoundError, EmailAlreadyExistsError, InvalidCredentialsError, etc.
  - Category domain: CategoryNotFoundError, CategorySlugAlreadyExistsError, CircularCategoryDependencyError, etc.
  - Product domain: ProductNotFoundError, InsufficientStockError, InvalidStockQuantityError, etc.
  - IntegrityError handler (автоматическая обработка нарушений БД → 409 Conflict)
- **Migrations** (Alembic, 4 миграции применены)

### ✅ Models (SQLAlchemy 2.0)
- **BaseModel** (UUID, created_at, updated_at, is_deleted, onupdate)
- **User** (роли: CUSTOMER/ADMIN, статусы: is_active/is_verified, lazy="selectin")
- **RefreshToken** (token_hash SHA-256, device_info, expires_at, индекс на expires_at)
- **Category** (иерархия parent/children, partial unique indexes с soft delete, is_active)
- **Product** (price Decimal(10,2), stock_quantity, SKU, image_url, CheckConstraints на уровне БД)

### ✅ Schemas (Pydantic v2)
- User schemas (frozen=True для responses, extra="forbid" для requests)
- Auth schemas (RegisterRequest, LoginRequest, TokenResponse)
- Category schemas (create/update/response)
- Product schemas (create/update/response)

### ✅ Repositories
- **BaseRepository[T]** - generic CRUD
- **UserRepository** - get_by_email, email_exists, filters
- **RefreshTokenRepository** - create, revoke, revoke_all_for_user
- **CategoryRepository** - get_by_slug, get_root, get_subcategories
- **ProductRepository** - get_by_slug, get_by_sku, search, low_stock

### ✅ Services

Разделение ответственности:

**AuthService** - аутентификация и безопасность:
- **register**: создание пользователя + токены
  - ✅ Race condition защита (IntegrityError → EmailAlreadyExistsError)
- **login**: вход в систему + токены
  - ✅ Проверка is_active перед выдачей токенов
- **refresh_tokens**: обновление пары токенов
  - ✅ Безопасный парсинг JWT payload (проверка sub: None, missing, неверный тип, невалидный UUID)
  - ✅ Проверка статуса пользователя (is_active, is_deleted) перед обновлением
  - ✅ Token rotation (отзыв старого токена)
- **logout**: отзыв одного refresh токена
- **logout_all_devices**: отзыв всех refresh токенов пользователя
- **change_password**: смена пароля + отзыв всех токенов
- **delete_user**: soft delete + отзыв всех токенов

**UserService** - CRUD операции с пользователями:
- **get_user**: получение по ID с валидацией
- **update_user**: обновление профиля (строгий контракт)
  - ✅ Принимает UserUpdate schema (только first_name, last_name, phone)
  - ✅ Pydantic блокирует запрещенные поля (role, email, password) через extra="forbid"
- **list_users**: список с фильтрами (is_active, role, search) и пагинацией
  - Возвращает UserResponse, а не ORM объекты

**CategoryService**:
- create, update, delete
- get_by_id, get_by_slug, get_root, get_subcategories
- circular dependency detection (защита от циклов в иерархии)

**ProductService**:
- create, update, delete
- get_by_id/slug/sku, search
- stock management: increase/decrease/update

**ВАЖНО:** Все сервисы БЕЗ commit/rollback - транзакции управляются в get_db()

### ✅ API Endpoints

**Dependencies:**
- Auth: get_current_user, get_current_active_user, require_role, require_admin
- Services: get_auth_service, get_user_service, get_category_service, get_product_service (Depends injection)

**Auth endpoints** (/api/v1/auth):
- POST /register, /login, /refresh, /logout, /logout-all

**Users endpoints** (/api/v1/users):
- GET /me, PATCH /me, POST /me/change-password, DELETE /me
- GET /{user_id}, GET / (admin, с фильтрами: is_active, role, search)
- DELETE /{user_id} (admin)

**Category endpoints** (/api/v1/categories):
- POST / (admin), GET /, GET /{id}, GET /slug/{slug}
- GET /{id}/subcategories, PATCH /{id} (admin), DELETE /{id} (admin)

**Product endpoints** (/api/v1/products):
- POST / (admin), GET /search, GET /low-stock (admin)
- GET /{id}, GET /slug/{slug}, GET /sku/{sku}
- PATCH /{id} (admin), DELETE /{id} (admin)
- POST /{id}/stock/increase (admin), POST /{id}/stock/decrease (admin)

### ✅ Tests (организация по доменам)

**Структура по доменам:** tests организованы по доменным границам (users, будущие: categories, products)

**Shared fixtures** (tests/shared/fixtures/):
- db_fixtures.py: setup_database (autouse), db_session, event_loop
- client_fixtures.py: HTTP client с переопределением БД

**Users domain** (tests/users/):
- fixtures/auth_fixtures.py: test_user, test_admin, test_inactive_user, test_unverified_user, test_users, auth_headers
- repositories/: тесты UserRepository, RefreshTokenRepository (базовый CRUD + специфичные методы)
- security/: unit-тесты security функций (hash_password, JWT, SHA-256)
- **services/** ✅ ГОТОВО (56 интеграционных тестов):
  
  **test_auth_service.py** (36 тестов, 7 классов):
  - TestAuthServiceRegister (4 теста): успешная регистрация, дубликат email, без optional полей
  - TestAuthServiceLogin (5 тестов): успешный вход, неверные credentials, неактивный user, множественные логины
  - TestAuthServiceRefreshTokens (12 тестов): успешный refresh, невалидные токены (missing sub, null sub, invalid UUID, integer sub), неактивный/удалённый user, token rotation, повторное использование
  - TestAuthServiceLogout (4 тесты): logout, logout_all_devices, изоляция устройств
  - TestAuthServiceChangePassword (4 теста): успешная смена, неверный старый пароль, отзыв всех токенов
  - TestAuthServiceDeleteUser (4 теста): soft delete, отзыв токенов, невозможность логина после удаления
  - Покрытие безопасности: JWT payload валидация, статус пользователя, race condition защита
  
  **test_user_service.py** (19 тестов, 3 класса):
  - TestUserServiceGetUser (3 теста): получение по ID, user not found, получение admin
  - TestUserServiceUpdateUser (6 тестов): обновление полей, частичное обновление, пустое обновление, защита от изменения role/email/password (ValidationError с проверкой структуры)
  - TestUserServiceListUsers (10 тестов): пагинация, фильтры (is_active, role, search), комбинированные фильтры, параметризация

**Best practices:** устойчивые assertions (не зависят от текстов PyJWT/Pydantic), проверка структуры ValidationError через errors(), организация по классам

**Изоляция:** create/drop tables на каждый тест (autouse fixture setup_database)

**Маркеры:** @pytest.mark.unit (пропускают БД), @pytest.mark.integration (требуют БД)