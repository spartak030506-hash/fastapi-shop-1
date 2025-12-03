# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## E-commerce API - Best Practices Only

**Принцип разработки**: Пишем сразу production-ready код с best practices. Никаких устаревших решений, никаких TODO, никаких заглушек.

## Императивы

- **БЕЗОПАСНОСТЬ** - без компромиссов
- **BEST PRACTICES** - только современные подходы (SQLAlchemy 2.0, Pydantic v2, async/await)
- **ПОЛНОТА БЛОКА** - если делаем auth, делаем его полностью и качественно, не жертвуем функционалом, делаем все сразу
- **ЧИСТАЯ АРХИТЕКТУРА** - разделение ответственности, никаких коммитов в сервисах

## Текущий статус проекта

### ✅ Реализовано (Production-Ready)

**Core & Infrastructure:**
- ✅ Database (SQLAlchemy 2.0 async, get_db с автокоммитом)
- ✅ Security (JWT с разными секретами, bcrypt, SHA-256 для refresh токенов)
- ✅ Config (Pydantic v2 settings)
- ✅ Migrations (Alembic, 2 миграции применены)

**Models:**
- ✅ BaseModel (UUID, timestamps, soft delete, onupdate)
- ✅ User (роли, статусы, lazy="selectin")
- ✅ RefreshToken (хеширование, device_info, индекс на expires_at)

**Schemas:**
- ✅ User schemas (frozen responses, str_strip_whitespace)
- ✅ Auth schemas (AuthResponse вместо dict, Literal["bearer"])
- ✅ Validators (password strength)

**Repositories (Generic типизация):**
- ✅ BaseRepository[T] (CRUD, soft delete, type-safe)
- ✅ UserRepository (email_exists, get_by_role)
- ✅ RefreshTokenRepository (is_token_valid, revoke)

**Services:**
- ✅ AuthService (register, login, refresh, logout, change_password)
- ✅ НЕТ commit/rollback внутри сервисов (правильно!)

**API:**
- ✅ Dependencies (get_current_user, require_role, require_admin)
- ✅ Auth endpoints (register, login, refresh, logout)
- ✅ Users endpoints (profile, change_password, admin list)
- ✅ Main app (CORS, health check)

**OpenAPI Documentation:**
- ✅ Swagger UI: http://localhost:8000/docs
- ✅ ReDoc: http://localhost:8000/redoc

### 🔄 Следующие шаги (при необходимости)

- Tests (pytest + pytest-asyncio)
- Products/Categories modules
- Orders module
- Redis cache (при необходимости)
- Rate limiting (при необходимости)

## Стек

```
Python 3.11+
FastAPI 0.104+
SQLAlchemy 2.0+ (async, mapped_column, Mapped)
Pydantic v2 (ConfigDict, model_config, frozen, str_strip_whitespace)
PostgreSQL 15+
Alembic
asyncpg
python-jose[cryptography]
passlib[bcrypt]
email-validator
pytest + pytest-asyncio
```

## Архитектура

3-слойная архитектура:
- **API Layer** (`app/api/v1/`) - endpoints, валидация, вызов сервисов
- **Service Layer** (`app/services/`) - бизнес-логика, БЕЗ commit/rollback
- **Repository Layer** (`app/repositories/`) - только CRUD операции

**Транзакции**: Управляются в `get_db()` dependency (паттерн "1 HTTP-запрос = 1 транзакция")

## Структура проекта

```
app/
├── api/
│   ├── dependencies/
│   │   └── auth.py           # get_current_user, require_role
│   └── v1/
│       ├── router.py         # Главный роутер v1
│       ├── auth.py           # Auth endpoints
│       └── users.py          # Users endpoints
├── core/
│   ├── config.py            # Pydantic v2 settings
│   ├── database.py          # AsyncSession, get_db()
│   └── security.py          # JWT, hash/verify
├── models/
│   ├── base.py              # BaseModel
│   ├── user.py              # User model
│   └── refresh_token.py     # RefreshToken model
├── repositories/
│   ├── base.py              # BaseRepository[T]
│   ├── user.py              # UserRepository
│   └── refresh_token.py     # RefreshTokenRepository
├── schemas/
│   ├── user.py              # User schemas
│   └── auth.py              # Auth schemas (AuthResponse!)
├── services/
│   └── auth_service.py      # AuthService (БЕЗ commit!)
├── utils/
│   └── validators.py        # Password validator
└── main.py                  # FastAPI app
```

## Best Practices (НЕ НАРУШАТЬ)

### Транзакции (КРИТИЧНО!)

```python
# ✅ ПРАВИЛЬНО - get_db() управляет транзакциями
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()  # Автоматический commit
        except Exception:
            await session.rollback()  # Автоматический rollback
            raise
        finally:
            await session.close()

# ✅ ПРАВИЛЬНО - сервис НЕ делает commit
class AuthService:
    async def register(self, data):
        user = await self.user_repo.create(user)
        tokens = await self._create_tokens_for_user(user.id)
        return user, tokens  # Commit сделает get_db()

# ❌ НЕПРАВИЛЬНО - НЕ делать commit в сервисе!
class AuthService:
    async def register(self, data):
        user = await self.user_repo.create(user)
        await self.db.commit()  # ❌ ПЛОХО!
```

### SQLAlchemy 2.0

```python
# ✅ ПРАВИЛЬНО
from sqlalchemy.orm import Mapped, mapped_column

class User(Base):
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)

    # Relationships с lazy="selectin" (избегаем N+1)
    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(
        "RefreshToken",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",  # ✅ Важно!
    )

# ❌ НЕПРАВИЛЬНО (устаревший синтаксис)
id = Column(UUID, primary_key=True)
```

### Pydantic v2

```python
# ✅ ПРАВИЛЬНО
from pydantic import BaseModel, ConfigDict

class UserResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,  # для ORM объектов
        frozen=True,           # иммутабельный ответ
    )

class LoginRequest(BaseModel):
    model_config = ConfigDict(
        extra="forbid",              # запретить лишние поля
        str_strip_whitespace=True,   # обрезать пробелы
    )

# ✅ ПРАВИЛЬНО - явные схемы вместо dict
class AuthResponse(BaseModel):
    user: UserResponse
    tokens: TokenResponse

@router.post("/register", response_model=AuthResponse)
async def register(...) -> AuthResponse:
    return AuthResponse(user=user, tokens=tokens)

# ❌ НЕПРАВИЛЬНО
class Config:
    orm_mode = True  # Pydantic v1

@router.post("/register", response_model=dict)  # ❌ Плохо для OpenAPI
```

### Generic Repositories

```python
# ✅ ПРАВИЛЬНО
from typing import Generic, TypeVar

ModelType = TypeVar("ModelType", bound=BaseModel)

class BaseRepository(Generic[ModelType]):
    def __init__(self, model: type[ModelType], db: AsyncSession):
        self.model = model
        self.db = db

    async def get_by_id(self, id: uuid.UUID) -> ModelType | None:
        ...

class UserRepository(BaseRepository[User]):
    def __init__(self, db: AsyncSession):
        super().__init__(User, db)
```

### JWT Security

```python
# ✅ ПРАВИЛЬНО
from datetime import datetime, timezone

now = datetime.now(timezone.utc)  # timezone-aware
expire = now + timedelta(minutes=15)

payload = {
    "sub": str(user_id),
    "exp": expire,
    "iat": now,
    "jti": str(uuid.uuid4()),
    "iss": "fastapi-shop",
    "type": "access"  # ✅ Разные типы токенов
}

# Разные секреты для access и refresh
jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
jwt.encode(refresh_payload, settings.REFRESH_TOKEN_SECRET, algorithm="HS256")

# Refresh токены хешируются в БД
token_hash = hashlib.sha256(token.encode()).hexdigest()

# ❌ НЕПРАВИЛЬНО
datetime.utcnow()  # устаревший, без timezone
```

### Type Hints

```python
# ✅ Хорошо
async def get_user(user_id: uuid.UUID) -> User | None:
    ...

def create_token(data: dict) -> str:
    ...

# ✅ Generic
class BaseRepository(Generic[ModelType]):
    async def get_all(self) -> list[ModelType]:
        ...

# ❌ Избыточно
from typing import Optional, Union, List, Dict, Any, Tuple
```

### Async everywhere

```python
# ✅ ПРАВИЛЬНО
async def get_user(db: AsyncSession, user_id: uuid.UUID):
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()

# ❌ НЕПРАВИЛЬНО
def get_user(db: Session, user_id: uuid.UUID):  # sync
```

## Примеры кода (Reference Implementation)

### Полный пример нового модуля

**Смотри реализацию Auth модуля:**
- Models: `app/models/user.py`, `app/models/refresh_token.py`
- Schemas: `app/schemas/user.py`, `app/schemas/auth.py`
- Repositories: `app/repositories/user.py`, `app/repositories/refresh_token.py`
- Services: `app/services/auth_service.py`
- Dependencies: `app/api/dependencies/auth.py`
- Endpoints: `app/api/v1/auth.py`, `app/api/v1/users.py`

**При добавлении нового модуля (например, Products):**
1. Скопируй структуру из Users
2. Адаптируй под свою доменную модель
3. Подключи роутер в `app/api/v1/router.py`

## Безопасность

**JWT:**
- Access token: 15 минут, подписан SECRET_KEY
- Refresh token: 7 дней, подписан REFRESH_TOKEN_SECRET (отдельный секрет!)
- Refresh token хешируется в БД (SHA-256)
- Все токены содержат: exp, iat, jti, iss, type

**Пароли:**
- Bcrypt через passlib
- Валидация: минимум 8 символов, заглавные, строчные, цифры

**Прочее:**
- Soft delete везде (is_deleted флаг)
- UUID для всех ID
- Проверка владельца ресурса перед операцией
- CORS настроен (в production указать конкретные домены!)

## Команды

```bash
# Миграции
alembic revision --autogenerate -m "description"
alembic upgrade head

# Запуск
uvicorn app.main:app --reload

# Проверка
curl http://localhost:8000/health

# Документация
open http://localhost:8000/docs

# Тесты (когда будут)
pytest -v
pytest --cov=app
```

## API Endpoints

**Auth (`/api/v1/auth`):**
- `POST /register` - Регистрация (возвращает AuthResponse)
- `POST /login` - Вход (возвращает AuthResponse)
- `POST /refresh` - Обновление токенов (TokenResponse)
- `POST /logout` - Выход (один токен)
- `POST /logout-all` - Выход на всех устройствах

**Users (`/api/v1/users`):**
- `GET /me` - Свой профиль
- `PATCH /me` - Обновить профиль
- `POST /me/change-password` - Сменить пароль
- `GET /{user_id}` - Получить пользователя (admin)
- `GET /` - Список пользователей (admin, с пагинацией)

## Помни

- Production-ready код с best practices
- Никаких устаревших решений
- Никаких TODO
- Никаких commit в сервисах
- Явные response schemas вместо dict
- Generic типизация где возможно
- Минимализм + полнота
