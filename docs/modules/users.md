# Users Module

Модуль аутентификации и управления пользователями.

---

## Назначение

Модуль Users отвечает за:
- регистрацию и аутентификацию пользователей
- управление профилем
- роли и доступ
- refresh tokens
- безопасность пользовательских сессий

---

## Модели

### User

**Файл:**
```
app/models/user.py
```

**Поля:**
| Field | Type | Notes |
|-----|-----|------|
| id | UUID | Primary key |
| email | EmailStr | Unique |
| password_hash | str | bcrypt |
| first_name | str | optional |
| last_name | str | optional |
| phone | str | optional |
| role | enum | CUSTOMER / ADMIN |
| is_active | bool | default True |
| is_verified | bool | default False |
| is_deleted | bool | soft delete |
| created_at | datetime | auto |
| updated_at | datetime | auto |

**Особенности:**
- lazy загрузка: `selectin`
- soft delete
- индексы на email

---

### RefreshToken

**Файл:**
```
app/models/refresh_token.py
```

**Поля:**
| Field | Type | Notes |
|-----|-----|------|
| id | UUID | Primary key |
| user_id | UUID | FK → users |
| token_hash | str | SHA-256 |
| device_info | str | optional |
| expires_at | datetime | indexed |
| created_at | datetime | auto |

**Особенности:**
- refresh токены хранятся только в виде hash
- индекс на `expires_at`

---

## Schemas

**Файлы:**
```
app/schemas/user.py
app/schemas/auth.py
```

### Auth schemas
- RegisterRequest
- LoginRequest
- TokenResponse
- RefreshRequest
- ChangePasswordRequest

### User schemas
- UserResponse (`frozen=True`)
- UserUpdate (`extra="forbid"`)

---

## Repositories

### UserRepository

**Файл:**
```
app/repositories/user.py
```

**Методы:**
- `get_by_id`
- `get_by_email`
- `email_exists`
- `list(filters, pagination)`

---

### RefreshTokenRepository

**Файл:**
```
app/repositories/refresh_token.py
```

**Методы:**
- `create`
- `revoke`
- `revoke_all_for_user`
- `get_valid_token`

---

## Services

### AuthService

**Файл:**
```
app/services/auth_service.py
```

**Ответственность:**
- регистрация
- логин
- refresh токены
- logout
- смена пароля
- удаление пользователя

#### Реализованные методы

- **register**
  - создаёт пользователя
  - защищён от race condition (IntegrityError)
  - возвращает TokenResponse

- **login**
  - проверяет пароль
  - проверяет `is_active`
  - выдаёт токены

- **refresh_tokens**
  - строгая валидация JWT payload
  - проверка пользователя
  - token rotation

- **logout**
  - отзыв одного refresh токена

- **logout_all_devices**
  - отзыв всех refresh токенов

- **change_password**
  - проверка старого пароля
  - отзыв всех refresh токенов

- **delete_user**
  - soft delete
  - отзыв всех refresh токенов

---

### UserService

**Файл:**
```
app/services/user_service.py
```

**Ответственность:**
- управление профилем
- чтение данных пользователя

#### Реализованные методы

- **get_user**
  - получение по ID
  - доменная ошибка если не найден

- **update_user**
  - строгий контракт
  - запрещено обновлять email, role, password
  - принимает только UserUpdate schema

- **list_users**
  - фильтрация: is_active, role, search
  - пагинация

---

## API Endpoints

**Файлы:**
```
app/api/v1/auth.py
app/api/v1/users.py
```

### Auth
- POST `/auth/register`
- POST `/auth/login`
- POST `/auth/refresh`
- POST `/auth/logout`
- POST `/auth/logout-all`

### Users
- GET `/users/me`
- PATCH `/users/me`
- POST `/users/me/change-password`
- DELETE `/users/me`

**Admin only:**
- GET `/users`
- GET `/users/{user_id}`
- DELETE `/users/{user_id}`

---

## Security

Особенности безопасности:
- JWT access + refresh
- двойные секреты
- SHA-256 для refresh токенов
- bcrypt для паролей
- token rotation
- device isolation
- отзыв токенов при смене пароля и удалении

---

## Тесты

**Директория:**
```
tests/users/
```

**Содержит:**
- fixtures (auth_fixtures.py)
- repositories tests
- security tests
- services tests

### AuthService tests
- 36 тестов
- покрывают весь auth flow
- проверяют edge cases JWT payload
- подтверждают безопасность refresh tokens

### UserService tests
- 19 тестов
- проверка валидации
- фильтрация и пагинация
- защита от запрещённых полей

---

## Итог

Модуль Users:
- полностью production-ready
- безопасен
- покрыт тестами
- может служить шаблоном для других доменов