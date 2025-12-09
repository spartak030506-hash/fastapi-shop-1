# API Reference

Полная документация по HTTP API проекта.  
Все endpoints описаны с указанием доступа, параметров и ответов.

**Базовый префикс:**
```
/api/v1
```

**Авторизация:**
```
Authorization: Bearer <access_token>
```

---

## Authentication (`/auth`)

### POST /auth/register
Регистрация нового пользователя.

**Request body:**
| Field | Type | Required |
|-----|-----|---------|
| email | EmailStr | ✅ |
| password | string | ✅ |
| first_name | string | ❌ |
| last_name | string | ❌ |
| phone | string | ❌ |

**Responses:**
- `201 Created` — успешная регистрация
- `409 Conflict` — email уже существует
- `422 Validation Error`

---

### POST /auth/login
Аутентификация пользователя.

**Request body:**
| Field | Type | Required |
|-----|-----|---------|
| email | EmailStr | ✅ |
| password | string | ✅ |

**Responses:**
- `200 OK` — access + refresh tokens
- `401 Unauthorized` — неверные credentials
- `403 Forbidden` — пользователь неактивен
- `422 Validation Error`

---

### POST /auth/refresh
Обновление пары токенов.

**Request body:**
| Field | Type | Required |
|-----|-----|---------|
| refresh_token | string | ✅ |

**Responses:**
- `200 OK` — новая пара токенов
- `401 Unauthorized` — невалидный токен
- `403 Forbidden` — пользователь неактивен / удалён

---

### POST /auth/logout
Выход с текущего устройства.

**Auth:** required

**Responses:**
- `204 No Content`
- `401 Unauthorized`

---

### POST /auth/logout-all
Выход со всех устройств.

**Auth:** required

**Responses:**
- `204 No Content`
- `401 Unauthorized`

---

## Users (`/users`)

### GET /users/me
Текущий пользователь.

**Auth:** required

**Responses:**
- `200 OK` — профиль пользователя
- `401 Unauthorized`

---

### PATCH /users/me
Обновление профиля.

**Auth:** required

**Request body:**
| Field | Type |
|-----|-----|
| first_name | string |
| last_name | string |
| phone | string |

**Rules:**
- запрещено изменять email, role, password
- строгая валидация (`extra="forbid"`)

**Responses:**
- `200 OK`
- `422 Validation Error`

---

### POST /users/me/change-password
Смена пароля.

**Auth:** required

**Request body:**
| Field | Type | Required |
|-----|-----|---------|
| old_password | string | ✅ |
| new_password | string | ✅ |

**Effects:**
- отзыв всех refresh токенов

---

### DELETE /users/me
Удаление пользователя (soft delete).

**Auth:** required

**Responses:**
- `204 No Content`
- `401 Unauthorized`

---

### GET /users
Список пользователей.

**Auth:** admin only

**Query params:**
| Param | Type |
|-----|-----|
| is_active | bool |
| role | enum |
| search | string |
| page | int |
| size | int |

**Responses:**
- `200 OK`

---

### GET /users/{user_id}
Получение пользователя по ID.

**Auth:** admin only

**Responses:**
- `200 OK`
- `404 Not Found`

---

### DELETE /users/{user_id}
Удаление пользователя администратором.

**Auth:** admin only

---

## Categories (`/categories`)

### POST /categories
Создание категории.

**Auth:** admin only

**Request body:**
| Field | Type |
|-----|-----|
| name | string |
| slug | string |
| parent_id | UUID \| null |

**Responses:**
- `201 Created`
- `409 Conflict` — slug уже существует
- `400 Bad Request` — circular dependency

---

### GET /categories
Получение корневых категорий.

**Public**

---

### GET /categories/{id}
Категория по ID.

**Public**

---

### GET /categories/slug/{slug}
Категория по slug.

**Public**

---

### GET /categories/{id}/subcategories
Подкатегории.

**Public**

---

### PATCH /categories/{id}
Обновление категории.

**Auth:** admin only

---

### DELETE /categories/{id}
Удаление категории (soft delete).

**Auth:** admin only

---

## Products (`/products`)

### POST /products
Создание продукта.

**Auth:** admin only

**Request body:**
| Field | Type |
|-----|-----|
| name | string |
| slug | string |
| sku | string |
| price | decimal |
| stock_quantity | int |
| category_id | UUID |
| image_url | string |

---

### GET /products/search
Поиск продуктов.

**Query params:**
| Param | Type |
|-----|-----|
| search | string |
| category_id | UUID |
| min_price | decimal |
| max_price | decimal |
| page | int |
| size | int |

---

### GET /products/low-stock
Товары с низким остатком.

**Auth:** admin only

---

### GET /products/{id}
Продукт по ID.

---

### GET /products/slug/{slug}
Продукт по slug.

---

### GET /products/sku/{sku}
Продукт по SKU.

---

### PATCH /products/{id}
Обновление продукта.

**Auth:** admin only

---

### DELETE /products/{id}
Удаление продукта (soft delete).

**Auth:** admin only

---

### POST /products/{id}/stock/increase
Увеличение остатка.

**Auth:** admin only

**Request body:**
| Field | Type |
|-----|-----|
| amount | int |

---

### POST /products/{id}/stock/decrease
Уменьшение остатка.

**Auth:** admin only

**Rules:**
- нельзя уйти в отрицательный stock

---

## Общие HTTP коды

| Code | Description |
|----|------------|
| 200 | OK |
| 201 | Created |
| 204 | No Content |
| 400 | Bad Request |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Not Found |
| 409 | Conflict |
| 422 | Validation Error |

---

## Документация

- Swagger UI: `/docs`
- ReDoc: `/redoc`