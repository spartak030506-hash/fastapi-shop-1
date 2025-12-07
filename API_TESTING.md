# API Testing Guide

Руководство по тестированию API через Postman или Swagger UI (FastAPI Docs).

## Quick Start

1. Запустите сервер: `uvicorn app.main:app --reload`
2. Откройте Swagger UI: http://localhost:8000/docs
3. Или импортируйте Postman Collection (см. ниже)

---

## Base URL

```
http://localhost:8000
```

---

## 1. Authentication & Users

### 1.1 Регистрация нового пользователя

**Endpoint:** `POST /api/v1/auth/register`

**Request Body:**
```json
{
  "email": "test@example.com",
  "password": "TestPass123",
  "first_name": "Иван",
  "last_name": "Иванов",
  "phone": "89991234567"
}
```

**Response (201):**
```json
{
  "user": {
    "id": "uuid",
    "email": "test@example.com",
    "first_name": "Иван",
    "last_name": "Иванов",
    "phone": "89991234567",
    "role": "CUSTOMER",
    "is_active": true,
    "is_verified": false,
    "created_at": "2025-12-07T12:00:00Z"
  },
  "tokens": {
    "access_token": "eyJhbGc...",
    "refresh_token": "eyJhbGc...",
    "token_type": "bearer"
  }
}
```

---

### 1.2 Вход (Login)

**Endpoint:** `POST /api/v1/auth/login`

**Request Body:**
```json
{
  "email": "test@example.com",
  "password": "TestPass123"
}
```

**Response (200):**
```json
{
  "user": {
    "id": "uuid",
    "email": "test@example.com",
    ...
  },
  "tokens": {
    "access_token": "eyJhbGc...",
    "refresh_token": "eyJhbGc...",
    "token_type": "bearer"
  }
}
```

---

### 1.3 Обновление токенов

**Endpoint:** `POST /api/v1/auth/refresh`

**Request Body:**
```json
{
  "refresh_token": "eyJhbGc..."
}
```

**Response (200):**
```json
{
  "access_token": "eyJhbGc...",
  "refresh_token": "eyJhbGc...",
  "token_type": "bearer"
}
```

---

### 1.4 Выход (Logout)

**Endpoint:** `POST /api/v1/auth/logout`

**Headers:**
```
Authorization: Bearer {access_token}
```

**Request Body:**
```json
{
  "refresh_token": "eyJhbGc..."
}
```

**Response (200):**
```json
{
  "message": "Successfully logged out"
}
```

---

### 1.5 Получить свой профиль

**Endpoint:** `GET /api/v1/users/me`

**Headers:**
```
Authorization: Bearer {access_token}
```

**Response (200):**
```json
{
  "id": "uuid",
  "email": "test@example.com",
  "first_name": "Иван",
  "last_name": "Иванов",
  "phone": "89991234567",
  "role": "CUSTOMER",
  "is_active": true,
  "is_verified": false,
  "created_at": "2025-12-07T12:00:00Z"
}
```

---

### 1.6 Изменить пароль

**Endpoint:** `POST /api/v1/users/me/change-password`

**Headers:**
```
Authorization: Bearer {access_token}
```

**Request Body:**
```json
{
  "old_password": "TestPass123",
  "new_password": "NewPass456"
}
```

**Response (200):**
```json
{
  "message": "Password changed successfully"
}
```

---

## 2. Categories (Категории)

### 2.1 Создать категорию (Admin only)

**Endpoint:** `POST /api/v1/categories`

**Headers:**
```
Authorization: Bearer {admin_access_token}
```

**Request Body:**
```json
{
  "name": "Электроника",
  "slug": "electronics",
  "description": "Электронные устройства и гаджеты"
}
```

**Response (201):**
```json
{
  "id": "uuid",
  "name": "Электроника",
  "slug": "electronics",
  "description": "Электронные устройства и гаджеты",
  "parent_id": null,
  "is_active": true,
  "created_at": "2025-12-07T12:00:00Z"
}
```

---

### 2.2 Создать подкатегорию (Admin only)

**Endpoint:** `POST /api/v1/categories`

**Headers:**
```
Authorization: Bearer {admin_access_token}
```

**Request Body:**
```json
{
  "name": "Смартфоны",
  "slug": "smartphones",
  "description": "Мобильные телефоны",
  "parent_id": "{electronics_category_id}"
}
```

---

### 2.3 Получить все корневые категории

**Endpoint:** `GET /api/v1/categories?skip=0&limit=20`

**Response (200):**
```json
[
  {
    "id": "uuid",
    "name": "Электроника",
    "slug": "electronics",
    "description": "Электронные устройства и гаджеты",
    "parent_id": null,
    "is_active": true,
    "created_at": "2025-12-07T12:00:00Z"
  }
]
```

---

### 2.4 Получить категорию по ID

**Endpoint:** `GET /api/v1/categories/{category_id}`

---

### 2.5 Получить категорию по slug

**Endpoint:** `GET /api/v1/categories/slug/electronics`

---

### 2.6 Получить подкатегории

**Endpoint:** `GET /api/v1/categories/{category_id}/subcategories?skip=0&limit=20`

---

### 2.7 Обновить категорию (Admin only)

**Endpoint:** `PATCH /api/v1/categories/{category_id}`

**Headers:**
```
Authorization: Bearer {admin_access_token}
```

**Request Body:**
```json
{
  "name": "Электроника и техника",
  "is_active": true
}
```

---

### 2.8 Удалить категорию (Admin only)

**Endpoint:** `DELETE /api/v1/categories/{category_id}`

**Headers:**
```
Authorization: Bearer {admin_access_token}
```

**Response (200):**
```json
{
  "message": "Category deleted successfully"
}
```

---

## 3. Products (Товары)

### 3.1 Создать продукт (Admin only)

**Endpoint:** `POST /api/v1/products`

**Headers:**
```
Authorization: Bearer {admin_access_token}
```

**Request Body:**
```json
{
  "name": "iPhone 15 Pro",
  "slug": "iphone-15-pro",
  "description": "Флагманский смартфон Apple 2023 года",
  "price": 99999.00,
  "category_id": "{smartphones_category_id}",
  "stock_quantity": 50,
  "sku": "APL-IPH15P-256GB",
  "image_url": "https://example.com/images/iphone15pro.jpg"
}
```

**Response (201):**
```json
{
  "id": "uuid",
  "name": "iPhone 15 Pro",
  "slug": "iphone-15-pro",
  "description": "Флагманский смартфон Apple 2023 года",
  "price": "99999.00",
  "category_id": "uuid",
  "stock_quantity": 50,
  "sku": "APL-IPH15P-256GB",
  "image_url": "https://example.com/images/iphone15pro.jpg",
  "is_active": true,
  "created_at": "2025-12-07T12:00:00Z"
}
```

---

### 3.2 Поиск продуктов (с фильтрами)

**Endpoint:** `GET /api/v1/products/search`

**Query Parameters:**
- `search_term` (optional) - поиск по названию/описанию
- `category_id` (optional) - фильтр по категории
- `min_price` (optional) - минимальная цена
- `max_price` (optional) - максимальная цена
- `in_stock_only` (optional, default: false) - только в наличии
- `active_only` (optional, default: true) - только активные
- `skip` (optional, default: 0) - пагинация
- `limit` (optional, default: 20, max: 100) - лимит

**Пример:**
```
GET /api/v1/products/search?search_term=iPhone&min_price=50000&max_price=150000&in_stock_only=true&skip=0&limit=20
```

**Response (200):**
```json
[
  {
    "id": "uuid",
    "name": "iPhone 15 Pro",
    "slug": "iphone-15-pro",
    "price": "99999.00",
    "stock_quantity": 50,
    "is_active": true,
    ...
  }
]
```

---

### 3.3 Получить продукт по ID

**Endpoint:** `GET /api/v1/products/{product_id}`

---

### 3.4 Получить продукт по slug

**Endpoint:** `GET /api/v1/products/slug/iphone-15-pro`

---

### 3.5 Получить продукт по SKU

**Endpoint:** `GET /api/v1/products/sku/APL-IPH15P-256GB`

---

### 3.6 Получить товары с низким остатком (Admin only)

**Endpoint:** `GET /api/v1/products/low-stock?threshold=10`

**Headers:**
```
Authorization: Bearer {admin_access_token}
```

**Response (200):**
```json
[
  {
    "id": "uuid",
    "name": "iPhone 14",
    "stock_quantity": 5,
    ...
  }
]
```

---

### 3.7 Обновить продукт (Admin only)

**Endpoint:** `PATCH /api/v1/products/{product_id}`

**Headers:**
```
Authorization: Bearer {admin_access_token}
```

**Request Body:**
```json
{
  "price": 89999.00,
  "stock_quantity": 30,
  "is_active": true
}
```

---

### 3.8 Увеличить остаток товара (Admin only)

**Endpoint:** `POST /api/v1/products/{product_id}/stock/increase`

**Headers:**
```
Authorization: Bearer {admin_access_token}
```

**Request Body:**
```json
{
  "quantity": 100
}
```

**Response (200):**
```json
{
  "id": "uuid",
  "name": "iPhone 15 Pro",
  "stock_quantity": 150,
  ...
}
```

---

### 3.9 Уменьшить остаток товара (Admin only)

**Endpoint:** `POST /api/v1/products/{product_id}/stock/decrease`

**Headers:**
```
Authorization: Bearer {admin_access_token}
```

**Request Body:**
```json
{
  "quantity": 5
}
```

**Response (200):**
```json
{
  "id": "uuid",
  "name": "iPhone 15 Pro",
  "stock_quantity": 145,
  ...
}
```

---

### 3.10 Удалить продукт (Admin only)

**Endpoint:** `DELETE /api/v1/products/{product_id}`

**Headers:**
```
Authorization: Bearer {admin_access_token}
```

**Response (200):**
```json
{
  "message": "Product deleted successfully"
}
```

---

## 4. Тестовый сценарий (Full Flow)

### Шаг 1: Регистрация пользователя
```bash
POST /api/v1/auth/register
{
  "email": "customer@test.com",
  "password": "TestPass123",
  "first_name": "Покупатель",
  "last_name": "Тестовый",
  "phone": "89991234567"
}
```
➡️ Сохраните `access_token` и `refresh_token`

---

### Шаг 2: Регистрация админа (для тестов)
```bash
POST /api/v1/auth/register
{
  "email": "admin@test.com",
  "password": "AdminPass123",
  "first_name": "Админ",
  "last_name": "Тестовый",
  "phone": "89997654321"
}
```
➡️ **Вручную измените роль в БД на ADMIN** или используйте существующего админа

---

### Шаг 3: Создать категорию (как админ)
```bash
POST /api/v1/categories
Headers: Authorization: Bearer {admin_access_token}
{
  "name": "Электроника",
  "slug": "electronics",
  "description": "Электронные устройства"
}
```
➡️ Сохраните `category_id`

---

### Шаг 4: Создать подкатегорию
```bash
POST /api/v1/categories
Headers: Authorization: Bearer {admin_access_token}
{
  "name": "Смартфоны",
  "slug": "smartphones",
  "parent_id": "{electronics_category_id}"
}
```
➡️ Сохраните `smartphones_category_id`

---

### Шаг 5: Создать продукт
```bash
POST /api/v1/products
Headers: Authorization: Bearer {admin_access_token}
{
  "name": "iPhone 15 Pro",
  "slug": "iphone-15-pro",
  "description": "Флагманский смартфон",
  "price": 99999.00,
  "category_id": "{smartphones_category_id}",
  "stock_quantity": 50,
  "sku": "APL-IPH15P-256GB"
}
```

---

### Шаг 6: Поиск продуктов (как обычный пользователь)
```bash
GET /api/v1/products/search?search_term=iPhone&in_stock_only=true
```

---

### Шаг 7: Получить свой профиль
```bash
GET /api/v1/users/me
Headers: Authorization: Bearer {customer_access_token}
```

---

### Шаг 8: Управление остатками (как админ)
```bash
POST /api/v1/products/{product_id}/stock/decrease
Headers: Authorization: Bearer {admin_access_token}
{
  "quantity": 5
}
```

---

## 5. Postman Collection

### Импорт в Postman:

1. Откройте Postman
2. File → Import → Raw text
3. Вставьте URL: `http://localhost:8000/openapi.json`
4. Нажмите Import

Или:

1. Создайте новую коллекцию "FastAPI Shop"
2. Добавьте переменные:
   - `base_url`: `http://localhost:8000`
   - `access_token`: (заполните после login)
   - `refresh_token`: (заполните после login)

---

## 6. Примеры ошибок

### 400 Bad Request - Email уже существует
```json
{
  "detail": "Email already registered"
}
```

### 401 Unauthorized - Неверные credentials
```json
{
  "detail": "Incorrect email or password"
}
```

### 403 Forbidden - Нет прав доступа
```json
{
  "detail": "Not enough permissions"
}
```

### 404 Not Found - Ресурс не найден
```json
{
  "detail": "Category not found"
}
```

### 422 Validation Error
```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "value is not a valid email address",
      "type": "value_error.email"
    }
  ]
}
```

---

## 7. Swagger UI (FastAPI Docs)

Самый простой способ тестирования:

1. Откройте: http://localhost:8000/docs
2. Нажмите на endpoint
3. Нажмите "Try it out"
4. Заполните параметры
5. Нажмите "Execute"

**Для авторизованных запросов:**
1. В правом верхнем углу нажмите "Authorize"
2. Введите: `Bearer {your_access_token}`
3. Нажмите "Authorize"

---

## 8. Валидация паролей

Пароль должен содержать:
- Минимум 8 символов
- Хотя бы одну заглавную букву (A-Z)
- Хотя бы одну строчную букву (a-z)
- Хотя бы одну цифру (0-9)

**Примеры валидных паролей:**
- `TestPass123`
- `MySecret456`
- `AdminPass789`

**Примеры НЕвалидных паролей:**
- `test123` (нет заглавной буквы)
- `TESTPASS123` (нет строчной буквы)
- `TestPass` (нет цифры)
- `Test12` (меньше 8 символов)

---

## 9. Health Check

**Endpoint:** `GET /health`

**Response (200):**
```json
{
  "status": "ok"
}
```

---

## Полезные ссылки

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- OpenAPI JSON: http://localhost:8000/openapi.json
- Health Check: http://localhost:8000/health
