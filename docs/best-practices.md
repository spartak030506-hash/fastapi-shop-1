# Best Practices (Production-Ready)

Набор практик, которые используются в проекте для поддержания
предсказуемости, безопасности и масштабируемости кода.

---

## 1. Один HTTP-запрос = одна транзакция

**Правило:**  
Транзакции управляются **только** на уровне dependency `get_db()`.

✅ commit — если запрос завершился успешно  
✅ rollback — при любой ошибке  
❌ Никаких commit / rollback в сервисах и репозиториях

```python
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
```

**Почему это важно:**

- Нет частичных сохранений
- Легко рассуждать о данных
- Поведение одинаково для всех endpoint'ов

## 2. Сервисы НЕ знают о транзакциях

Service layer:

- содержит бизнес-логику
- вызывает репозитории
- не управляет состоянием БД

```python
class UserService:
    async def update_user(self, user: User, data: UserUpdate):
        user.first_name = data.first_name
        user.last_name = data.last_name
        return user
```

✅ Повышает тестируемость  
✅ Упрощает повторное использование сервисов  
✅ Убирает скрытые side-effects

## 3. Репозитории = только работа с БД

Repository layer:

- CRUD операции
- SQLAlchemy queries
- никакой бизнес-логики

```python
class UserRepository(BaseRepository[User]):
    async def get_by_email(self, email: str) -> User | None:
        stmt = select(User).where(User.email == email)
        return await self.session.scalar(stmt)
```

❌ Никаких проверок ролей  
❌ Никаких HTTP ошибок  
❌ Никаких commit / rollback

## 4. ORM модели НЕ возвращаются из API

Из API всегда возвращаются Pydantic Schemas, а не SQLAlchemy модели.

```python
return UserResponse.model_validate(user)
```

**Почему:**

- Нет утечки внутренних полей
- Контроль формата ответа
- Защита от lazy-loading ловушек

## 5. Строгие схемы запросов (extra="forbid")

Для входящих данных используется строгая валидация:

```python
class UserUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None

    model_config = ConfigDict(extra="forbid")
```

✅ Клиент не может передать лишние поля  
✅ Защита от массового присвоения  
✅ Ошибка возникает автоматически, без ручных проверок

## 6. Frozen response schemas

Response-схемы помечены как immutable:

```python
class UserResponse(BaseModel):
    id: UUID
    email: EmailStr

    model_config = ConfigDict(frozen=True)
```

✅ Нельзя случайно изменить объект  
✅ Чёткий контракт API  
✅ Меньше багов в сервисах

## 7. Доменные исключения вместо HTTPException

Логика домена не зависит от HTTP.

```python
class UserNotFoundError(DomainException):
    status_code = 404
    detail = "User not found"
```

HTTP-слой просто мапит ошибки.

✅ Домены переиспользуемы  
✅ Лёгкое тестирование  
✅ Централизованная обработка ошибок

## 8. IntegrityError → понятная доменная ошибка

Race conditions обрабатываются корректно:

```python
try:
    user = await repo.create(user)
except IntegrityError:
    raise EmailAlreadyExistsError()
```

✅ Нет двойных записей  
✅ Корректная работа при конкурентных запросах  
✅ Предсказуемое поведение

## 9. Безопасный refresh tokens flow

Применяются практики:

- хранение hash(refresh_token), а не токена
- token rotation
- отзыв старых токенов
- проверка user state (is_active, is_deleted)

```python
if not payload.sub or not isinstance(payload.sub, UUID):
    raise InvalidTokenError()
```

✅ Защита от replay-атак  
✅ Можно безопасно отзывать доступ  
✅ Поддержка multiple devices

## 10. Тесты отражают бизнес-сценарии

Тесты пишутся по доменам, а не по слоям.

**Пример:**

- users/services/test_auth_service.py
- users/repositories/test_user_repository.py

✅ Тестируется поведение, а не реализация
✅ Легче читать и поддерживать
✅ Рефакторинг без переписывания тестов

## 11. SQLAlchemy Best Practices

### ORM-стиль вместо bulk update
```python
# ❌ Плохо - рассинхронизация сессии
update(User).where(...).values(name="New")

# ✅ Хорошо - объект синхронизирован
user = await repo.get_by_id(id)
user.name = "New"
await db.flush()
```

### exists() для проверок существования
```python
# ❌ Плохо - может упасть на дубликатах
result.scalar_one_or_none() is not None

# ✅ Хорошо - корректная семантика
query = select(exists(select(User.id).where(...)))
result.scalar()
```

### .is_() для boolean сравнений
```python
# ❌ Плохо
User.is_active == True
User.is_deleted == False

# ✅ Хорошо - SQLAlchemy best practice
User.is_active.is_(True)
User.is_deleted.is_(False)
```

**Исключение:** Bulk update допустим для массовых операций (revoke_all_tokens), где не нужен объект после обновления.