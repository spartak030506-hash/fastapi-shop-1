# Categories Module

Модуль управления категориями и их иерархией.

---

## Назначение

Модуль Categories отвечает за:
- управление иерархией категорий
- публичное получение категорий
- админские операции (create/update/delete)
- защиту от циклических зависимостей

Категории используются как классификация продуктов.

---

## Модель

### Category

**Файл:**
```
app/models/category.py
```

**Поля:**
| Field | Type | Notes |
|-----|-----|------|
| id | UUID | Primary key |
| name | str | |
| slug | str | unique (partial index) |
| parent_id | UUID \| null | self-reference |
| is_active | bool | default True |
| is_deleted | bool | soft delete |
| created_at | datetime | auto |
| updated_at | datetime | auto |

---

## Иерархия

Модель поддерживает дерево категорий:

- категория может иметь `parent`
- категория может иметь несколько `children`
- допускается любая глубина

**SQLAlchemy конфигурация:**
- `parent` / `children`
- `remote_side`
- `lazy="selectin"`

---

## Ограничения БД

Реализованы:
- partial unique index на `slug` с учётом `is_deleted`
- foreign key на `parent_id`
- защита на уровне сервиса от циклов

✅ Можно повторно использовать slug после soft delete  
✅ Гарантируется целостность иерархии  

---

## Schemas

**Файл:**
```
app/schemas/category.py
```

**Схемы:**
- CategoryCreate
- CategoryUpdate
- CategoryResponse

**Правила:**
- input schemas → `extra="forbid"`
- response → `frozen=True`

---

## Repository

### CategoryRepository

**Файл:**
```
app/repositories/category.py
```

**Методы:**
- `get_by_id`
- `get_by_slug`
- `get_root`
- `get_subcategories`
- `exists_by_slug`

Репозиторий:
- не знает ничего о бизнес-правилах
- работает только с БД

---

## Service

### CategoryService

**Файл:**
```
app/services/category_service.py
```

**Ответственность:**
- бизнес-логика категорий
- контроль иерархии
- проверки уникальности slug

#### Реализованные методы

- **create**
  - создание категории
  - проверка уникальности slug
  - установка parent (опционально)

- **update**
  - обновление name / slug / parent
  - защита от циклической зависимости

- **delete**
  - soft delete

- **get_by_id**
- **get_by_slug**
- **get_root**
- **get_subcategories**

---

## Защита от циклов

При update категории выполняется:
- обход родителей вверх по дереву
- проверка, что новая категория не становится своим потомком

При нарушении:
- выбрасывается `CircularCategoryDependencyError`

---

## API Endpoints

**Файл:**
```
app/api/v1/categories.py
```

### Public
- GET `/categories`
- GET `/categories/{id}`
- GET `/categories/slug/{slug}`
- GET `/categories/{id}/subcategories`

### Admin only
- POST `/categories`
- PATCH `/categories/{id}`
- DELETE `/categories/{id}`

---

## Ошибки домена

Реализованы ошибки:
- `CategoryNotFoundError`
- `CategorySlugAlreadyExistsError`
- `CircularCategoryDependencyError`

Все ошибки:
- являются доменными
- мапятся в HTTP уровне

---

## Тесты

На текущий момент:
- структура для тестов заложена
- домен готов к добавлению тестов по аналогии с Users

**Рекомендуемая структура:**
```
tests/categories/
├── fixtures/
├── repositories/
├── services/
└── api/
```

---

## Итог

Модуль Categories:
- поддерживает сложную иерархию
- защищён от некорректных состояний
- безопасен для публичного доступа
- полностью готов для расширения