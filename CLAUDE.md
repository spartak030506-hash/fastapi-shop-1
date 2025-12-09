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

---

## Текущий стек

- **Python** 3.11+
- **FastAPI** 0.104.1
- **SQLAlchemy** 2.0.23 (async, Mapped, mapped_column)
- **Pydantic** 2.5.0 (ConfigDict, frozen, from_attributes)
- **PostgreSQL** 15+
- **JWT** (PyJWT 2.8.0+, bcrypt 4.0.0+)
- **pytest** 7.4.3 (pytest-asyncio, pytest-cov)

---

## Краткая архитектура

**3 слоя:**
1. **API Layer** - HTTP endpoints, валидация, DI
2. **Service Layer** - бизнес-логика, **БЕЗ commit/rollback**
3. **Repository Layer** - CRUD, работа с БД

**Транзакции:** 1 HTTP-запрос = 1 транзакция (управляется в `get_db()`)

**Исключения:** Доменные исключения вместо HTTPException

**Типизация:** Generic репозитории, Pydantic schemas для API

---

## Документация

Детальная документация вынесена в отдельные файлы:

### 📐 Архитектура
**[docs/architecture.md](docs/architecture.md)**
- Детальное описание 3-слойной архитектуры
- Управление транзакциями
- Dependency Injection
- Exception handling
- Структура проекта
- Реализованные модули

### ✨ Best Practices
**[docs/best-practices.md](docs/best-practices.md)**
- Один HTTP-запрос = одна транзакция
- Сервисы НЕ знают о транзакциях
- ORM модели НЕ возвращаются из API
- Доменные исключения вместо HTTPException
- Безопасный refresh tokens flow
- И другие практики

### 🧪 Тестирование
**[docs/testing.md](docs/testing.md)**
- Организация по доменам
- Shared fixtures
- Unit vs Integration тесты
- Проверка ошибок
- Изоляция тестов

### 🔐 Безопасность
**[docs/security.md](docs/security.md)**
- JWT архитектура (access + refresh tokens)
- Двойной секрет для JWT
- Хранение refresh токенов (SHA-256 hash)
- Token rotation
- Хеширование паролей (bcrypt)
- Проверка состояния пользователя

### 📚 API Reference
**[docs/api-reference.md](docs/api-reference.md)**
- Все endpoints (Auth, Users, Categories, Products)
- Query параметры
- Auth защита

### 🛠️ Development Guide
**[docs/development-guide.md](docs/development-guide.md)**
- Как добавить новый модуль
- Команды (миграции, запуск, тесты)

### 📦 Модули

**[docs/modules/users.md](docs/modules/users.md)**
- User & RefreshToken models
- AuthService, UserService
- Auth & Users endpoints

**[docs/modules/categories.md](docs/modules/categories.md)**
- Category model (иерархия)
- CategoryService (circular dependency detection)
- Category endpoints

**[docs/modules/products.md](docs/modules/products.md)**
- Product model
- ProductService (stock management)
- Product endpoints

---

## Golden Rules

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

### Тесты
✅ **По доменам:** tests/{domain}/{layer}/
✅ **Изоляция:** create/drop tables на каждый тест
✅ **Маркеры:** @pytest.mark.unit, @pytest.mark.integration
✅ **Не запускать без разрешения пользователя**

### Минимализм
✅ **Не over-engineer:** только то, что попросили
✅ **Полнота блока:** функционал делаем до конца
✅ **Production-ready:** никаких TODO, заглушек, устаревших решений
