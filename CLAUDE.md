# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Техническое задание E-commerce API

Этот проект находится в стадии разработки. Следуйте плану разработки пошагово.

## Императивы (НЕ НАРУШАТЬ)

- **БЕЗОПАСНОСТЬ** - никаких компромиссов, каждая уязвимость = провал
- **Best practices** - SQLAlchemy 2.0+ (mapped_column, Mapped), async/await везде
- **Продакшен сразу** - без TODO, заглушек, "потом доделаем"
- **Тесты после блока** - написал auth → тесты auth, написал products → тесты products
- **Type hints** - на всё (функции, переменные, возвраты)
- **Пошаговая разработка** - строго по плану

## Стек
```
Python 3.11+
FastAPI 0.104+
SQLAlchemy 2.0+ (async, mapped_column)
PostgreSQL 15+
Redis
Alembic
Pydantic v2
asyncpg
redis-py (async)
python-jose[cryptography]
passlib[bcrypt]
pytest + pytest-asyncio
httpx
uvicorn
```

## Структура проекта
```
ecommerce-api/
├── app/
│   ├── main.py
│   ├── api/v1/endpoints/     # Endpoints (auth, users, products, cart, orders, admin)
│   ├── services/             # Бизнес-логика
│   ├── repositories/         # Работа с БД (base + конкретные)
│   ├── models/               # SQLAlchemy модели
│   ├── schemas/              # Pydantic схемы
│   ├── core/                 # config, security, database, cache, exceptions, middleware
│   └── utils/
├── tests/
├── alembic/
├── docker/
├── .env.example
├── requirements.txt
└── README.md
```

## Архитектурные принципы

### Слои (строгое разделение)
- **API Layer** - валидация входа, вызов сервисов, возврат ответов
- **Service Layer** - вся бизнес-логика, транзакции, проверки
- **Repository Layer** - CRUD операции с БД, никакой логики

### Dependency Injection
- Все зависимости через `Depends()`
- get_db, get_redis, get_current_user, require_admin

### SQLAlchemy 2.0 Best Practices
- `mapped_column()` вместо Column
- `Mapped[тип]` для type hints
- `relationship()` с правильным typed
- Async session везде

### Безопасность в коде
- Bcrypt для паролей (passlib)
- JWT: access 15 мин, refresh 7 дней
- Refresh токены хешируются в БД (SHA-256)
- Rate limiting через Redis
- Soft delete (is_deleted флаг)
- CORS настроен явно
- Валидация UUID на всех endpoints

## План разработки (пошагово)

### ШАГ 1: Инфраструктура
1. Создать структуру папок
2. requirements.txt с версиями
3. .env.example (все переменные с комментариями)
4. .gitignore
5. docker-compose.yml (postgres, redis, app)
6. Dockerfile (multi-stage: builder + production)

### ШАГ 2: Core модули
1. **config.py** - Pydantic Settings (все настройки из .env)
2. **database.py** - async engine, AsyncSessionLocal, get_db dependency
3. **cache.py** - async Redis client, init/close, get_redis dependency
4. **exceptions.py** - кастомные (NotFoundError, UnauthorizedError, ForbiddenError, ValidationError, ConflictError)
5. **security.py** - hash/verify пароли, create/decode JWT, verify_token_type
6. **middleware.py** - CORS, rate limiting, request logging, exception handlers
7. **models/base.py** - BaseModel (id UUID, created_at, updated_at, is_deleted) с mapped_column

### ШАГ 3: Auth модуль
1. **models/user.py**:
   - User: email (unique, index), hashed_password, first/last name, phone, role (enum: customer/admin), is_active, is_verified
   - Relationships: refresh_tokens, carts, orders
2. **models/refresh_token.py**:
   - token_hash (unique, index), user_id (FK), expires_at, is_revoked, device_info
3. **schemas/user.py**:
   - UserCreate (валидация пароля: мин 8, заглавные/строчные/цифры)
   - UserUpdate (опциональные поля)
   - UserResponse
4. **schemas/auth.py**: LoginRequest, TokenResponse, RefreshRequest
5. **repositories/base.py** - BaseRepository[ModelType] с get_by_id, get_all, create, update, delete (soft)
6. **repositories/user_repository.py** - get_by_email, email_exists
7. **repositories/refresh_token_repository.py** - get_by_token_hash, revoke_token, revoke_all_user_tokens
8. **services/auth_service.py**:
   - register (проверка email, хеширование пароля)
   - login (проверка credentials, создание токенов, сохранение refresh в БД)
   - refresh_access_token (проверка refresh в БД)
   - logout (отзыв refresh токена)
9. **api/dependencies.py** - get_current_user, require_admin
10. **api/v1/endpoints/auth.py** - POST register, login, refresh, logout, GET me
11. **api/v1/endpoints/users.py** - PUT /users/me (обновление профиля)
12. **api/v1/router.py** - подключение всех роутеров
13. main.py - подключение router, middleware, lifespan (init/close redis)
14. Alembic: настроить env.py, создать миграцию
15. **tests/conftest.py** - фикстуры (db_session, client)
16. **tests/test_auth.py** - все сценарии (register success/duplicate, login success/fail, refresh, logout, get me)
17. **tests/test_users.py** - update user (success, partial, unauthorized)

**СТОП: Проверить что всё работает, тесты проходят**

### ШАГ 4: Категории
1. **models/category.py**: name, slug (unique, index), description, parent_id (self-reference), is_active
2. **schemas/category.py**: CategoryCreate, CategoryUpdate, CategoryResponse, CategoryTree (с children)
3. **repositories/category_repository.py**: get_by_slug, get_with_children
4. **services/category_service.py**: create, update, delete (проверка is_active), get_tree
5. **api/v1/endpoints/categories.py**:
   - GET /categories (дерево категорий)
   - GET /categories/{id}
   - POST/PUT/DELETE - require_admin
6. Миграция
7. **tests/test_categories.py** (все CRUD, дерево, проверка прав)

**СТОП: Тесты**

### ШАГ 5: Товары
1. **models/product.py**:
   - name, slug (unique, index), description
   - price (DECIMAL), discount_price (nullable)
   - stock_quantity (int)
   - category_id (FK), sku (unique)
   - images (JSON/Array)
   - is_active
   - Индексы: category_id, is_active, price
2. **schemas/product.py**:
   - ProductCreate, ProductUpdate, ProductResponse
   - ProductFilter (category_id, price_min/max, search, is_active)
   - ProductList (с пагинацией meta)
3. **repositories/product_repository.py**:
   - get_with_filters (category, price range, search по name/description)
   - get_by_slug
   - update_stock (с проверкой остатка)
4. **services/product_service.py**:
   - create (проверка slug уникальность)
   - update (проверка существования)
   - delete (soft, проверка можно ли удалить)
   - get_list (фильтры, пагинация, сортировка)
   - search (full-text через PostgreSQL)
5. **api/v1/endpoints/products.py**:
   - GET /products (список с фильтрами, пагинация)
   - GET /products/{id}
   - GET /products/search?q=
   - POST/PUT/DELETE - require_admin
6. Миграция (с индексами)
7. **tests/test_products.py** (CRUD, фильтры, поиск, пагинация, проверка прав)

**СТОП: Тесты**

### ШАГ 6: Корзина
1. **models/cart.py**:
   - user_id (FK, index), product_id (FK)
   - quantity (int, > 0)
   - price_at_addition (DECIMAL, фиксация цены)
   - Unique constraint: (user_id, product_id)
2. **schemas/cart.py**:
   - CartItemCreate (product_id, quantity)
   - CartItemUpdate (quantity)
   - CartItemResponse (с product details)
   - CartResponse (items + total)
3. **repositories/cart_repository.py**:
   - get_user_cart (с join product)
   - get_cart_item (user_id, product_id)
   - update_quantity
   - clear_cart
4. **services/cart_service.py**:
   - add_item (проверка stock, проверка существования товара, обновление если уже в корзине)
   - update_quantity (проверка stock)
   - remove_item (проверка владельца)
   - get_cart (с пересчетом total)
   - clear_cart
5. **api/v1/endpoints/cart.py**:
   - GET /cart/items
   - POST /cart/items
   - PUT /cart/items/{id}
   - DELETE /cart/items/{id}
   - DELETE /cart/clear
6. Миграция
7. **tests/test_cart.py** (добавление, обновление, удаление, проверка stock, проверка владельца)

**СТОП: Тесты**

### ШАГ 7: Заказы
1. **models/order.py**:
   - user_id (FK, index), order_number (unique, auto-generated)
   - status (enum: pending, paid, processing, shipped, delivered, cancelled)
   - total_amount (DECIMAL)
   - shipping_address (JSON: {name, address, city, zip, country, phone})
   - payment_method, payment_status
   - Индексы: user_id, status, created_at
2. **models/order_item.py**:
   - order_id (FK), product_id (FK)
   - quantity, price (фиксированная)
   - product_snapshot (JSON: {name, sku} на случай удаления товара)
3. **schemas/order.py**:
   - OrderCreate (shipping_address), OrderResponse, OrderList
   - OrderItemResponse, OrderUpdate (status)
4. **repositories/order_repository.py**:
   - get_user_orders (с пагинацией)
   - get_with_items (join order_items)
   - update_status
5. **services/order_service.py**:
   - create_order (ТРАНЗАКЦИЯ: проверка корзины, проверка stock, списание stock, создание order/items, очистка корзины, генерация order_number)
   - cancel_order (проверка статуса pending, возврат stock)
   - update_status (только админ)
   - get_user_orders
6. **api/v1/endpoints/orders.py**:
   - POST /orders (создание из корзины)
   - GET /orders (мои заказы)
   - GET /orders/{id}
   - PUT /orders/{id}/cancel
7. Миграция
8. **tests/test_orders.py** (создание, отмена, проверка транзакции, проверка stock, проверка владельца)

**СТОП: Тесты**

### ШАГ 8: Admin панель
1. **api/v1/endpoints/admin.py**:
   - GET /admin/users (список пользователей, фильтры, пагинация)
   - PUT /admin/users/{id} (изменение роли, is_active)
   - GET /admin/orders (все заказы, фильтры)
   - PUT /admin/orders/{id}/status
   - GET /admin/statistics (общая статистика: кол-во заказов, выручка, товары)
2. Все endpoints с require_admin
3. **tests/test_admin.py** (CRUD users/orders, проверка прав)

**СТОП: Тесты**

## Требования к коду

### SQLAlchemy 2.0
```python
# ПРАВИЛЬНО (mapped_column)
from sqlalchemy.orm import Mapped, mapped_column

class User(Base):
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    is_active: Mapped[bool] = mapped_column(default=True)
    
# НЕПРАВИЛЬНО (Column)
id = Column(UUID, primary_key=True)  # НЕ ТАК!
```

### Type hints везде
```python
async def get_user(user_id: UUID) -> Optional[User]:
    ...

async def create_order(data: OrderCreate, user: User) -> Order:
    ...
```

### Безопасность (обязательно)
- Пароли: bcrypt, никогда plain text
- Refresh токены: SHA-256 в БД
- UUID валидация в endpoints
- Проверка владельца ресурса (user.id == resource.user_id)
- Rate limiting на auth endpoints (3/min)
- SQL injection: только ORM, параметризация
- Soft delete везде

### Транзакции
```python
# Критичные операции в транзакции
async with db.begin():
    # проверки
    # списание stock
    # создание order
    # очистка корзины
```

### Пагинация
```python
# Общий dependency
async def pagination_params(skip: int = 0, limit: int = 100):
    return {"skip": skip, "limit": min(limit, 100)}

# Response с meta
{
  "items": [...],
  "total": 150,
  "page": 1,
  "pages": 2
}
```

### Кеширование
- Категории (TTL 1 час)
- Детали товара (TTL 5 мин)
- Корзина пользователя (TTL 10 мин)

## Docker

### docker-compose.yml
- postgres (healthcheck)
- redis (healthcheck)
- app (depends_on с condition: service_healthy, migrations перед запуском)

### Dockerfile
- Multi-stage (builder + production)
- Не root user
- Health check endpoint

## Тестирование

### Покрытие
- Минимум 70%
- Каждый endpoint
- Позитивные и негативные сценарии
- Проверка прав доступа

### Фикстуры
- db_session (создание/удаление схемы)
- client (AsyncClient с override get_db)
- auth_headers (для авторизованных запросов)

## Запуск

### Локально
```bash
docker-compose up -d postgres redis
cp .env.example .env
alembic upgrade head
uvicorn app.main:app --reload
pytest -v --cov=app
```

### Production
```bash
docker-compose up --build
```

## Чек-лист перед деплоем

- [ ] Все тесты проходят (>70% покрытие)
- [ ] mapped_column везде (не Column)
- [ ] Type hints на всё
- [ ] Пароли хешированы
- [ ] Refresh токены хешированы
- [ ] Rate limiting работает
- [ ] Транзакции на критичных операциях
- [ ] Индексы на FK и часто используемых полях
- [ ] Soft delete проверяется везде
- [ ] CORS настроен
- [ ] SECRET_KEY изменен
- [ ] DEBUG=False
- [ ] Health check работает

## Помни

**Код сразу в production. Без TODO. Без компромиссов по безопасности. Тесты после каждого блока.**