# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## E-commerce API - Best Practices Only

**Принцип разработки**: Пишем сразу production-ready код с best practices. Никаких устаревших решений, никаких TODO, никаких заглушек.

## Императивы

- **БЕЗОПАСНОСТЬ** - без компромиссов
- **BEST PRACTICES** - только современные подходы (SQLAlchemy 2.0, Pydantic v2, async/await)
- **ПОЛНОТА БЛОКА** - если делаем auth, делаем его полностью и качественно, не жертвуем фунционалом, делаем все сразу

## Стек

```
Python 3.11+
FastAPI 0.104+
SQLAlchemy 2.0+ (async, mapped_column, Mapped)
Pydantic v2 (ConfigDict, model_config)
PostgreSQL 15+
Alembic
asyncpg
python-jose[cryptography]
passlib[bcrypt]
pytest + pytest-asyncio
```

## Архитектура

3-слойная архитектура:
- **API Layer** - endpoints, валидация, вызов сервисов
- **Service Layer** - бизнес-логика, транзакции
- **Repository Layer** - только CRUD операции

## Best Practices (НЕ НАРУШАТЬ)

### SQLAlchemy 2.0
```python
# ✅ ПРАВИЛЬНО
from sqlalchemy.orm import Mapped, mapped_column

class User(Base):
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)

# ❌ НЕПРАВИЛЬНО (устаревший синтаксис)
id = Column(UUID, primary_key=True)
```

### Pydantic v2
```python
# ✅ ПРАВИЛЬНО
from pydantic import BaseModel, ConfigDict

class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

# ❌ НЕПРАВИЛЬНО (Pydantic v1)
class Config:
    orm_mode = True
```

### JWT Security
```python
# ✅ ПРАВИЛЬНО
from datetime import datetime, timezone

now = datetime.now(timezone.utc)  # timezone-aware
expire = now + timedelta(minutes=15)

payload = {
    "sub": user_id,
    "exp": expire,
    "iat": now,
    "jti": str(uuid.uuid4()),
    "iss": "fastapi-shop",
    "type": "access"
}

# Разные секреты для access и refresh
jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
jwt.encode(refresh_payload, settings.REFRESH_TOKEN_SECRET, algorithm="HS256")

# ❌ НЕПРАВИЛЬНО
datetime.utcnow()  # устаревший, без timezone
return {}  # при ошибке декодирования - должна быть exception
```

### Type Hints
Разумно, без фанатизма:
```python
# ✅ Хорошо
async def get_user(user_id: uuid.UUID) -> User | None:
    ...

# ✅ Нормально
def create_token(data: dict) -> str:
    ...

# ❌ Избыточно (не импортить кучу типов ради аннотаций)
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

### Безопасность

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

## Последовательность разработки Auth модуля

1. **Models** (user.py, refresh_token.py)
2. **Alembic миграции** - сначала миграции!
3. **Security** (hash/verify, JWT)
4. **Schemas** (user.py, auth.py) - после миграций
5. **Repositories** (base, user, refresh_token)
6. **Services** (auth_service.py)
7. **Dependencies** (get_current_user)
8. **Endpoints** (auth.py, users.py)
9. **Tests**

## Что добавлять по мере необходимости

Не создавать сразу:
- Redis/cache - когда понадобится
- Middleware (CORS, rate limiting) - когда понадобится
- Exception types - только нужные
- Конфиги - только используемые

## Команды

```bash
# Миграции
alembic revision --autogenerate -m "description"
alembic upgrade head

# Тесты
pytest -v
pytest --cov=app

# Запуск
uvicorn app.main:app --reload
```

## Помни

Пишем production-ready код с best practices. Никаких устаревших решений. Никаких TODO. Минимализм + полнота.
