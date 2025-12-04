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
│   │   └── auth.py              # get_current_user, require_role, require_admin
│   └── v1/
│       ├── router.py            # Главный роутер API v1
│       ├── auth.py              # Auth endpoints
│       └── users.py             # Users endpoints
├── core/
│   ├── config.py                # Pydantic v2 settings
│   ├── database.py              # AsyncSession, get_db()
│   ├── security.py              # JWT, bcrypt, hash/verify
│   └── exceptions.py            # Custom HTTP exceptions
├── models/
│   ├── base.py                  # BaseModel (UUID, timestamps, soft delete)
│   ├── user.py                  # User model
│   └── refresh_token.py         # RefreshToken model
├── repositories/
│   ├── base.py                  # BaseRepository[T] (Generic CRUD)
│   ├── user.py                  # UserRepository
│   └── refresh_token.py         # RefreshTokenRepository
├── schemas/
│   ├── user.py                  # User Pydantic schemas
│   └── auth.py                  # Auth Pydantic schemas (AuthResponse!)
├── services/
│   └── auth_service.py          # AuthService (БЕЗ commit!)
├── utils/
│   └── validators.py            # Password strength validator
└── main.py                      # FastAPI app

tests/
├── conftest.py                  # Pytest fixtures (db_session, client, test_user, etc.)
├── test_api/
├── test_repositories/
├── test_security/
│   └── test_security_functions.py
└── test_services/

alembic/
└── versions/
    ├── 450aefd42d81_initial_migration_users_and_refresh_.py
    └── 4e6debc855da_улучшение_моделей_server_default_.py
```

---

## Реализованные модули (Production-Ready)

### ✅ Core & Infrastructure
- Database (SQLAlchemy 2.0 async)
- Security (JWT двойной секрет, bcrypt, SHA-256 для refresh токенов)
- Config (Pydantic v2 settings с .env)
- Exceptions (Custom HTTPException классы)
- Migrations (Alembic, 2 миграции применены)

### ✅ Models (SQLAlchemy 2.0)
- BaseModel (UUID, created_at, updated_at, is_deleted, onupdate)
- User (роли: CUSTOMER/ADMIN, статусы: is_active/is_verified, lazy="selectin")
- RefreshToken (token_hash SHA-256, device_info, expires_at, индекс на expires_at)

### ✅ Schemas (Pydantic v2)
- User schemas (frozen=True для responses, str_strip_whitespace для inputs)
- Auth schemas (AuthResponse вместо dict, Literal["bearer"], extra="forbid")
- Validators (password strength: 8+ chars, uppercase, lowercase, digits)

### ✅ Repositories (Generic типизация)
- BaseRepository[T] (Generic CRUD, soft delete, type-safe)
- UserRepository (email_exists, get_by_email, get_by_role)
- RefreshTokenRepository (is_token_valid, revoke_token, revoke_all_user_tokens)

### ✅ Services
- AuthService (register, login, refresh_tokens, logout, logout_all_devices, change_password)
- **БЕЗ commit/rollback** - транзакции управляются в get_db()

### ✅ API Endpoints
- Dependencies (get_current_user, get_current_active_user, require_role)
- Auth endpoints (register, login, refresh, logout, logout-all)
- Users endpoints (GET /me, PATCH /me, POST /me/change-password, admin endpoints)

### ✅ Tests
- conftest.py с fixtures (db_session, client, test_user, test_admin, auth_headers)
- test_security_functions.py (unit тесты для hash_password, JWT, SHA-256)
- Изоляция тестов (create/drop tables на каждый тест)

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

### 7. Async everywhere

**Используй:**
```python
async def get_user(db: AsyncSession, user_id: uuid.UUID):
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()
```

**НЕ используй:** sync функции для работы с БД

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

## API Endpoints

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

# Конкретный файл
pytest tests/test_security/test_security_functions.py -v

# С маркерами
pytest -m unit -v
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

8. **Напиши тесты** (`tests/test_api/test_products.py`)

**Reference implementation:** Auth module (user.py, auth_service.py, auth.py)

---

## Следующие шаги (roadmap)

- [ ] Products module (модель, CRUD, endpoints)
- [ ] Categories module (иерархия категорий)
- [ ] Orders module (корзина, заказы, статусы)
- [ ] Redis cache (для частых запросов)
- [ ] Rate limiting (защита от abuse)
- [ ] Email notifications (регистрация, заказы)
- [ ] File uploads (изображения продуктов)
- [ ] Full-text search (PostgreSQL tsvector или Elasticsearch)

---

## Помни

✅ Production-ready код с best practices
✅ Современный стек (SQLAlchemy 2.0, Pydantic v2, async)
✅ Никаких commit в сервисах
✅ Явные response schemas (НЕ dict)
✅ Generic типизация где возможно
✅ datetime.now(timezone.utc) (НЕ datetime.utcnow!)
✅ Тесты для всего нового функционала
✅ Минимализм + полнота
