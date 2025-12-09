# Testing Guide

Документация по организации, подходам и правилам тестирования проекта.

---

## Цели тестирования

Тесты в проекте предназначены для:
- проверки бизнес-логики
- гарантии безопасности
- защиты от регрессий
- уверенного рефакторинга кода

**Фокус — на поведении системы, а не на деталях реализации.**

---

## Инструменты

Используемый стек:

```
pytest
pytest-asyncio
pytest-cov
httpx
```

Тесты асинхронные и выполняются в изолированной среде.

---

## Типы тестов

### 1. Unit tests
- не используют БД
- тестируют чистые функции
- быстрые и изолированные

**Примеры:**
- password hashing
- JWT encode/decode
- validators

**Маркер:**
```python
@pytest.mark.unit
```

### 2. Integration tests
- используют реальную БД
- проверяют работу SQLAlchemy
- тестируют сервисы и репозитории

**Маркер:**

```python
@pytest.mark.integration
```

## Структура тестов

Тесты организованы по доменам, а не по слоям.

```bash
tests/
├── shared/
│   └── fixtures/
│       ├── db_fixtures.py
│       └── client_fixtures.py
└── users/
    ├── fixtures/
    ├── repositories/
    ├── security/
    └── services/
```

✅ Такая структура отражает реальное устройство бизнеса  
✅ Упрощает навигацию  
✅ Не ломается при рефакторинге слоёв

## Shared fixtures

### База данных

**setup_database:**

- создаёт таблицы перед тестом
- удаляет после завершения
- autouse fixture

```python
@pytest.fixture(autouse=True)
async def setup_database():
    ...
```

### AsyncSession

**db_session:**

- создаёт новую сессию на каждый тест
- исключает утечки состояния

### HTTP клиент

**client fixture:**

- использует FastAPI TestClient / AsyncClient
- подменяет get_db
- работает с тестовой БД

## Users domain tests

### Fixtures

Расположены в:

```bash
tests/users/fixtures/auth_fixtures.py
```

Содержат:

- test_user
- test_admin
- test_inactive_user
- test_unverified_user
- auth_headers
- test_users

Fixtures максимально переиспользуемы и декларативны.

### Repository tests

Пример:

```bash
tests/users/repositories/
└── test_user_repository.py
```

Проверяют:

- базовый CRUD
- уникальные ограничения
- фильтры и поиск

✅ Используется реальная БД  
✅ Проверяется SQL-логика  
✅ Нет мока ORM

### Service tests (ключевой уровень)

#### AuthService

Файл:

```bash
tests/users/services/test_auth_service.py
```

Содержит:

- 36 тестов
- 7 классов
- полностью покрывает auth flow

**Покрываемые сценарии:**
- регистрация
- логин
- refresh токены
- logout / logout_all
- смена пароля
- soft delete пользователя
- edge cases JWT payload

✅ Проверяется безопасность  
✅ Проверяется логика домена  
✅ Минимум моков

#### UserService

Файл:

```bash
tests/users/services/test_user_service.py
```

**Проверяем:**
- получение пользователя
- обновление профиля
- строгую валидацию (extra="forbid")
- фильтрацию и пагинацию

## Проверка ошибок

### ValidationError

Проверяется структура ошибки, а не текст:

```python
with pytest.raises(ValidationError) as exc:
    ...

assert exc.value.errors()[0]["loc"] == ("role",)
```

✅ Тесты устойчивы к обновлениям библиотек  
✅ Не зависят от текста сообщения

## Изоляция тестов

- каждая функция теста работает со свежей схемой БД
- нет шаринга данных
- нет зависимости от порядка выполнения

Это гарантируется:

- autouse setup_database
- отдельными AsyncSession

## Рекомендации

- добавляй тест вместе с функциональностью
- сначала воспроизводи баг тестом
- группируй тесты по сценариям
- избегай shared state