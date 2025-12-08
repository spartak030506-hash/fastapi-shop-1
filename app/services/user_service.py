import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import UserNotFoundError
from app.models.user import User, UserRole
from app.repositories.user import UserRepository
from app.schemas.user import UserResponse


class UserService:
    """
    Сервис для управления пользователями (CRUD операции).

    Отвечает за:
    - Получение пользователя по ID
    - Обновление профиля пользователя
    - Список пользователей с фильтрацией и пагинацией

    НЕ отвечает за:
    - Аутентификацию (см. AuthService)
    - Регистрацию (см. AuthService)
    - Удаление пользователя (см. AuthService - требует отзыв токенов)
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_repo = UserRepository(db)

    async def get_user(self, user_id: uuid.UUID) -> UserResponse:
        """
        Получить пользователя по ID.

        Args:
            user_id: UUID пользователя

        Returns:
            UserResponse с данными пользователя

        Raises:
            UserNotFoundError: Пользователь не найден
        """
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise UserNotFoundError(str(user_id))

        return UserResponse.model_validate(user)

    async def update_user(
        self,
        user_id: uuid.UUID,
        **update_data
    ) -> UserResponse:
        """
        Обновить профиль пользователя.

        Args:
            user_id: UUID пользователя
            **update_data: Поля для обновления (first_name, last_name, phone)

        Returns:
            UserResponse с обновленными данными

        Raises:
            UserNotFoundError: Пользователь не найден
        """
        # Проверка существования
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise UserNotFoundError(str(user_id))

        # Обновление
        if update_data:
            updated_user = await self.user_repo.update(user_id, **update_data)
            return UserResponse.model_validate(updated_user)

        return UserResponse.model_validate(user)

    async def list_users(
        self,
        skip: int = 0,
        limit: int = 100,
        is_active: bool | None = None,
        role: UserRole | None = None,
        search: str | None = None,
    ) -> list[UserResponse]:
        """
        Получить список пользователей с фильтрацией и пагинацией.

        Args:
            skip: Количество записей для пропуска
            limit: Максимальное количество записей (макс 100)
            is_active: Фильтр по статусу активности (опционально)
            role: Фильтр по роли (опционально)
            search: Поиск по email, имени или фамилии (опционально)

        Returns:
            Список UserResponse
        """
        # Валидация limit
        if limit > 100:
            limit = 100

        # Получение пользователей с фильтрами
        users = await self.user_repo.get_filtered_users(
            skip=skip,
            limit=limit,
            is_active=is_active,
            role=role,
            search=search,
        )

        return [UserResponse.model_validate(user) for user in users]
