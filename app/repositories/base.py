import uuid
from typing import Generic, TypeVar

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import BaseModel

ModelType = TypeVar("ModelType", bound=BaseModel)


class BaseRepository(Generic[ModelType]):
    """
    Базовый репозиторий с CRUD операциями.

    Использует Generic для типобезопасности.
    Автоматически фильтрует is_deleted=False во всех запросах.
    """

    def __init__(self, model: type[ModelType], db: AsyncSession):
        self.model = model
        self.db = db

    async def get_by_id(
        self,
        id: uuid.UUID,
        include_deleted: bool = False
    ) -> ModelType | None:
        """
        Получить запись по ID.

        Args:
            id: UUID записи
            include_deleted: Включать ли удаленные записи

        Returns:
            Запись или None
        """
        query = select(self.model).where(self.model.id == id)

        if not include_deleted:
            query = query.where(self.model.is_deleted.is_(False))

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        include_deleted: bool = False
    ) -> list[ModelType]:
        """
        Получить все записи с пагинацией.

        Args:
            skip: Количество записей для пропуска
            limit: Максимальное количество записей
            include_deleted: Включать ли удаленные записи

        Returns:
            Список записей
        """
        query = select(self.model)

        if not include_deleted:
            query = query.where(self.model.is_deleted.is_(False))

        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def count(self, include_deleted: bool = False) -> int:
        """
        Получить общее количество записей.

        Args:
            include_deleted: Включать ли удаленные записи

        Returns:
            Количество записей
        """
        query = select(func.count(self.model.id))

        if not include_deleted:
            query = query.where(self.model.is_deleted.is_(False))

        result = await self.db.execute(query)
        return result.scalar_one()

    async def create(self, obj: ModelType) -> ModelType:
        """
        Создать новую запись.

        Args:
            obj: Объект для создания

        Returns:
            Созданный объект
        """
        self.db.add(obj)
        await self.db.flush()
        await self.db.refresh(obj)
        return obj

    async def update(self, id: uuid.UUID, **kwargs) -> ModelType | None:
        """
        Обновить запись по ID.

        Использует ORM-стиль вместо bulk update для поддержания синхронизации сессии.

        Args:
            id: UUID записи
            **kwargs: Поля для обновления

        Returns:
            Обновленная запись или None
        """
        # Загружаем объект через ORM
        obj = await self.get_by_id(id, include_deleted=False)
        if obj is None:
            return None

        # Обновляем атрибуты объекта
        for key, value in kwargs.items():
            setattr(obj, key, value)

        # Flush изменений в БД и обновляем объект
        await self.db.flush()
        await self.db.refresh(obj)
        return obj

    async def soft_delete(self, id: uuid.UUID) -> bool:
        """
        Мягкое удаление записи (is_deleted = True).

        Использует ORM-стиль вместо bulk update для поддержания синхронизации сессии.

        Args:
            id: UUID записи

        Returns:
            True если запись удалена, False если не найдена
        """
        # Загружаем объект через ORM
        obj = await self.get_by_id(id, include_deleted=False)
        if obj is None:
            return False

        # Помечаем как удаленный
        obj.is_deleted = True

        # Flush изменений в БД
        await self.db.flush()
        return True

    async def hard_delete(self, id: uuid.UUID) -> bool:
        """
        Физическое удаление записи из БД.

        ВНИМАНИЕ: Используйте только когда необходимо!
        В большинстве случаев используйте soft_delete.

        Args:
            id: UUID записи

        Returns:
            True если запись удалена, False если не найдена
        """
        obj = await self.get_by_id(id, include_deleted=True)
        if obj:
            await self.db.delete(obj)
            await self.db.flush()
            return True
        return False
