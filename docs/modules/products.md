# Products Module

Модуль управления продуктами и складскими остатками.

---

## Назначение

Модуль Products отвечает за:
- управление товарами
- привязку к категориям
- публичное получение продуктов
- поиск и фильтрацию
- учёт складских остатков

---

## Модель

### Product

**Файл:**
```
app/models/product.py
```

**Поля:**
| Field | Type | Notes |
|-----|-----|------|
| id | UUID | Primary key |
| name | str | |
| slug | str | unique (partial index) |
| sku | str | unique |
| price | Decimal(10,2) | |
| stock_quantity | int | >= 0 |
| image_url | str | optional |
| category_id | UUID | FK → categories |
| is_deleted | bool | soft delete |
| created_at | datetime | auto |
| updated_at | datetime | auto |

---

## Ограничения БД

Реализованы:
- unique index на `sku`
- partial unique index на `slug` с учётом `is_deleted`
- CheckConstraint на `stock_quantity >= 0`
- ForeignKey constraint на `category_id`

✅ Целостность данных гарантируется БД  
✅ Бизнес-правила дублируются на уровне сервиса  

---

## Schemas

**Файл:**
```
app/schemas/product.py
```

**Схемы:**
- ProductCreate
- ProductUpdate
- ProductResponse

**Правила:**
- input schemas → `extra="forbid"`
- response → `frozen=True`

---

## Repository

### ProductRepository

**Файл:**
```
app/repositories/product.py
```

**Методы:**
- `get_by_id`
- `get_by_slug`
- `get_by_sku`
- `search`
- `low_stock`

Отвечает только за:
- SQL-запросы
- фильтрацию и сортировку
- пагинацию

---

## Service

### ProductService

**Файл:**
```
app/services/product_service.py
```

**Ответственность:**
- бизнес-логика продуктов
- управление остатками
- защита от некорректных данных

#### Реализованные методы

- **create**
  - создание продукта
  - проверка уникальности slug и sku

- **update**
  - обновление данных продукта

- **delete**
  - soft delete

- **get_by_id**
- **get_by_slug**
- **get_by_sku**
- **search**

---

## Управление остатками

**Методы:**
- **increase_stock**
- **decrease_stock**
- **update_stock**

**Правила:**
- нельзя уменьшить остаток ниже 0
- отрицательные значения запрещены

При нарушении:
- `InsufficientStockError`
- `InvalidStockQuantityError`

---

## API Endpoints

**Файл:**
```
app/api/v1/products.py
```

### Public
- GET `/products/{id}`
- GET `/products/slug/{slug}`
- GET `/products/sku/{sku}`
- GET `/products/search`

### Admin only
- POST `/products`
- PATCH `/products/{id}`
- DELETE `/products/{id}`
- GET `/products/low-stock`
- POST `/products/{id}/stock/increase`
- POST `/products/{id}/stock/decrease`

---

## Ошибки домена

Реализованы:
- `ProductNotFoundError`
- `InvalidStockQuantityError`
- `InsufficientStockError`

Ошибки:
- выбрасываются в сервисе
- мапятся в HTTP уровне

---

## Тесты

**Текущий статус:**
- архитектура полностью готова
- логика идентична Users domain
- тесты могут быть добавлены без изменения кода

**Рекомендуемая структура:**
```
tests/products/
├── fixtures/
├── repositories/
├── services/
└── api/
```

---

## Итог

Модуль Products:
- полностью production-ready
- защищён на уровне БД и сервиса
- масштабируем
- легко покрывается тестами