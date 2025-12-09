# Development Guide

Гайд для разработчиков по расширению и развитию проекта.

---

## Общие принципы разработки

Проект спроектирован для:
- модульного расширения
- предсказуемого поведения
- минимизации связности между слоями

Каждый новый функциональный блок должен следовать существующей архитектуре.

---

## Добавление нового модуля

Новый модуль (домен) добавляется **вертикально**:  
модель → схема → репозиторий → сервис → API → тесты.

---

## 1. Модель (models)

Добавь новую модель в `app/models/`.

**Правила:**
- наследуется от `BaseModel`
- содержит UUID primary key
- использует soft delete (если применимо)
- описываются ограничения БД (indexes, constraints)

```python
class Example(BaseModel):
    __tablename__ = "examples"

    name: Mapped[str]
```

После добавления:

- создай alembic миграцию
- примени миграцию

## 2. Schema (schemas)

Добавь Pydantic схемы в `app/schemas/`.

**Разделение:**

- Create
- Update
- Response

**Правила:**

- input schemas → `extra="forbid"`
- response schemas → `frozen=True`

```python
class ExampleCreate(BaseModel):
    name: str

    model_config = ConfigDict(extra="forbid")
```

## 3. Repository (repositories)

Создай репозиторий в `app/repositories/`.

Наследуйся от `BaseRepository[T]`.

```python
class ExampleRepository(BaseRepository[Example]):
    async def get_by_name(self, name: str) -> Example | None:
        ...
```

**Ограничения:**

- только SQLAlchemy
- никаких бизнес-правил
- никаких исключений уровня HTTP

## 4. Service (services)

Добавь сервис в `app/services/`.

```python
class ExampleService:
    def __init__(self, repo: ExampleRepository):
        self.repo = repo
```

**Правила:**

- **АНТИПАТТЕРН**: commit / rollback
- выбрасывай доменные исключения
- возвращай доменные объекты или response schemas

## 5. API (api/v1)

Создай endpoint-файл в `app/api/v1/`.

```python
router = APIRouter(prefix="/examples", tags=["Examples"])
```

**Правила:**

- валидация только через Pydantic
- авторизация через dependencies
- никаких try/except (кроме мапинга ошибок)

## 6. Dependencies

Добавь dependency-функции, если требуется:

- get_example_service
- require_admin
- get_current_user

**Файл:**

```bash
app/api/dependencies/services.py
```

## 7. Тесты

Создай доменную директорию:

```bash
tests/examples/
```

**Структура:**

```
fixtures/
repositories/
services/
api/
```

**Правила:**

- пиши тесты по сценариям
- сначала failing test, потом код
- сервисы тестируются интеграционно

## Работа с БД

Транзакции управляются в `get_db()`.

✅ сервисы не коммитят  
✅ репозитории не коммитят

## Работа с ошибками

### Доменные исключения

Добавляй в `app/core/exceptions.py`.

```python
class ExampleNotFoundError(DomainException):
    status_code = 404
    detail = "Example not found"
```

### Валидация

- вся валидация — в schemas
- бизнес-проверки — в сервисах
- БД гарантирует целостность данных

## Когда добавлять новый пакет

Добавляй новый пакет, если:

- модуль стал слишком большим
- логика переиспользуется
- появляется отдельный bounded context