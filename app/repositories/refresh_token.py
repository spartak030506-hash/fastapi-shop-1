import uuid
from datetime import datetime, timezone

from sqlalchemy import select, update, delete, and_, exists
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.refresh_token import RefreshToken
from app.repositories.base import BaseRepository


class RefreshTokenRepository(BaseRepository[RefreshToken]):
    """
    Репозиторий для работы с refresh токенами.

    Наследует базовые CRUD операции и добавляет специфичные методы:
    - Поиск по хешу токена
    - Получение токенов пользователя
    - Отзыв токенов (revoke)
    - Очистка истекших токенов
    - Проверка валидности токена
    """

    def __init__(self, db: AsyncSession):
        super().__init__(RefreshToken, db)

    async def get_by_token_hash(
        self,
        token_hash: str,
        include_revoked: bool = False,
        include_deleted: bool = False
    ) -> RefreshToken | None:
        """
        Получить refresh токен по хешу.

        Args:
            token_hash: SHA-256 хеш токена
            include_revoked: Включать ли отозванные токены
            include_deleted: Включать ли удаленные записи

        Returns:
            Токен или None
        """
        query = select(RefreshToken).where(RefreshToken.token_hash == token_hash)

        if not include_revoked:
            query = query.where(RefreshToken.is_revoked.is_(False))

        if not include_deleted:
            query = query.where(RefreshToken.is_deleted.is_(False))

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_user_tokens(
        self,
        user_id: uuid.UUID,
        include_revoked: bool = False,
        include_deleted: bool = False
    ) -> list[RefreshToken]:
        """
        Получить все токены пользователя.

        Args:
            user_id: UUID пользователя
            include_revoked: Включать ли отозванные токены
            include_deleted: Включать ли удаленные записи

        Returns:
            Список токенов пользователя
        """
        query = select(RefreshToken).where(RefreshToken.user_id == user_id)

        if not include_revoked:
            query = query.where(RefreshToken.is_revoked.is_(False))

        if not include_deleted:
            query = query.where(RefreshToken.is_deleted.is_(False))

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def is_token_valid(
        self,
        token_hash: str
    ) -> bool:
        """
        Проверить валидность токена (не истек, не отозван, не удален).

        Args:
            token_hash: SHA-256 хеш токена

        Returns:
            True если токен валиден, False если нет
        """
        now = datetime.now(timezone.utc)
        # Создаем подзапрос для exists
        subquery = select(RefreshToken.id).where(
            and_(
                RefreshToken.token_hash == token_hash,
                RefreshToken.is_revoked.is_(False),
                RefreshToken.is_deleted.is_(False),
                RefreshToken.expires_at > now
            )
        )
        # Используем exists() для проверки
        query = select(exists(subquery))
        result = await self.db.execute(query)
        return result.scalar()

    async def revoke_token(
        self,
        token_hash: str
    ) -> bool:
        """
        Отозвать токен по хешу.

        ПРИМЕЧАНИЕ: Использует bulk update для производительности (не требует загрузки объекта).

        Args:
            token_hash: SHA-256 хеш токена

        Returns:
            True если токен отозван, False если не найден
        """
        query = (
            update(RefreshToken)
            .where(RefreshToken.token_hash == token_hash)
            .where(RefreshToken.is_deleted.is_(False))
            .where(RefreshToken.is_revoked.is_(False))
            .values(is_revoked=True)
        )
        result = await self.db.execute(query)
        await self.db.flush()
        return result.rowcount > 0

    async def revoke_all_user_tokens(
        self,
        user_id: uuid.UUID
    ) -> int:
        """
        Отозвать все токены пользователя.

        ПРИМЕЧАНИЕ: Использует bulk update для производительности (массовая операция).

        Args:
            user_id: UUID пользователя

        Returns:
            Количество отозванных токенов
        """
        query = (
            update(RefreshToken)
            .where(RefreshToken.user_id == user_id)
            .where(RefreshToken.is_deleted.is_(False))
            .where(RefreshToken.is_revoked.is_(False))
            .values(is_revoked=True)
        )
        result = await self.db.execute(query)
        await self.db.flush()
        return result.rowcount

    async def delete_expired_tokens(self) -> int:
        """
        Удалить все истекшие токены (физическое удаление).

        Рекомендуется запускать периодически через cron/scheduler.

        Returns:
            Количество удаленных токенов
        """
        now = datetime.now(timezone.utc)
        query = delete(RefreshToken).where(RefreshToken.expires_at < now)
        result = await self.db.execute(query)
        await self.db.flush()
        return result.rowcount

    async def delete_user_expired_tokens(
        self,
        user_id: uuid.UUID
    ) -> int:
        """
        Удалить истекшие токены конкретного пользователя.

        Args:
            user_id: UUID пользователя

        Returns:
            Количество удаленных токенов
        """
        now = datetime.now(timezone.utc)
        query = (
            delete(RefreshToken)
            .where(RefreshToken.user_id == user_id)
            .where(RefreshToken.expires_at < now)
        )
        result = await self.db.execute(query)
        await self.db.flush()
        return result.rowcount

    async def count_user_active_tokens(
        self,
        user_id: uuid.UUID
    ) -> int:
        """
        Подсчитать количество активных токенов пользователя.

        Args:
            user_id: UUID пользователя

        Returns:
            Количество активных токенов
        """
        now = datetime.now(timezone.utc)
        query = select(RefreshToken).where(
            and_(
                RefreshToken.user_id == user_id,
                RefreshToken.is_revoked.is_(False),
                RefreshToken.is_deleted.is_(False),
                RefreshToken.expires_at > now
            )
        )
        result = await self.db.execute(query)
        return len(list(result.scalars().all()))
