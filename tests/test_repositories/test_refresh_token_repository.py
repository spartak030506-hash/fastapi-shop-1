import hashlib
import uuid
from datetime import datetime, timezone, timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.repositories.refresh_token import RefreshTokenRepository


@pytest.mark.integration
class TestRefreshTokenRepositoryBase:
    """Тесты базовых CRUD операций RefreshTokenRepository (наследуются от BaseRepository)"""

    async def test_get_by_id_existing_token(
        self,
        db_session: AsyncSession,
        test_user: User
    ):
        """Получение существующего токена по ID возвращает токен"""
        repo = RefreshTokenRepository(db_session)

        # Создаём токен
        token = RefreshToken(
            id=uuid.uuid4(),
            token_hash=hashlib.sha256(b"test_token_1").hexdigest(),
            user_id=test_user.id,
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
            device_info="Test Device",
        )
        await repo.create(token)
        await db_session.commit()

        result = await repo.get_by_id(token.id)

        assert result is not None
        assert result.id == token.id
        assert result.token_hash == token.token_hash

    async def test_get_by_id_non_existing_token(self, db_session: AsyncSession):
        """Получение несуществующего токена по ID возвращает None"""
        repo = RefreshTokenRepository(db_session)
        non_existing_id = uuid.uuid4()

        result = await repo.get_by_id(non_existing_id)

        assert result is None

    async def test_get_by_id_soft_deleted_token_excluded_by_default(
        self,
        db_session: AsyncSession,
        test_user: User
    ):
        """Soft-deleted токен исключается по умолчанию при поиске по ID"""
        repo = RefreshTokenRepository(db_session)

        token = RefreshToken(
            id=uuid.uuid4(),
            token_hash=hashlib.sha256(b"test_token_2").hexdigest(),
            user_id=test_user.id,
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        )
        await repo.create(token)
        await db_session.commit()
        await repo.soft_delete(token.id)

        result = await repo.get_by_id(token.id)

        assert result is None

    async def test_get_by_id_soft_deleted_token_included_when_requested(
        self,
        db_session: AsyncSession,
        test_user: User
    ):
        """Soft-deleted токен включается при include_deleted=True"""
        repo = RefreshTokenRepository(db_session)

        token = RefreshToken(
            id=uuid.uuid4(),
            token_hash=hashlib.sha256(b"test_token_3").hexdigest(),
            user_id=test_user.id,
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        )
        await repo.create(token)
        await db_session.commit()
        await repo.soft_delete(token.id)

        result = await repo.get_by_id(token.id, include_deleted=True)

        assert result is not None
        assert result.is_deleted is True

    async def test_get_all_returns_all_tokens(
        self,
        db_session: AsyncSession,
        test_user: User
    ):
        """get_all возвращает все токены"""
        repo = RefreshTokenRepository(db_session)

        # Создаём несколько токенов
        for i in range(3):
            token = RefreshToken(
                id=uuid.uuid4(),
                token_hash=hashlib.sha256(f"test_token_{i}".encode()).hexdigest(),
                user_id=test_user.id,
                expires_at=datetime.now(timezone.utc) + timedelta(days=7),
            )
            await repo.create(token)
        await db_session.commit()

        result = await repo.get_all()

        assert len(result) == 3
        assert all(isinstance(t, RefreshToken) for t in result)

    async def test_get_all_with_pagination(
        self,
        db_session: AsyncSession,
        test_user: User
    ):
        """get_all поддерживает пагинацию через skip и limit"""
        repo = RefreshTokenRepository(db_session)

        # Создаём 5 токенов
        for i in range(5):
            token = RefreshToken(
                id=uuid.uuid4(),
                token_hash=hashlib.sha256(f"test_token_{i}".encode()).hexdigest(),
                user_id=test_user.id,
                expires_at=datetime.now(timezone.utc) + timedelta(days=7),
            )
            await repo.create(token)
        await db_session.commit()

        result_page1 = await repo.get_all(skip=0, limit=2)
        result_page2 = await repo.get_all(skip=2, limit=2)

        assert len(result_page1) == 2
        assert len(result_page2) == 2
        assert result_page1[0].id != result_page2[0].id

    async def test_get_all_excludes_soft_deleted_by_default(
        self,
        db_session: AsyncSession,
        test_user: User
    ):
        """get_all исключает soft-deleted токены по умолчанию"""
        repo = RefreshTokenRepository(db_session)

        tokens = []
        for i in range(3):
            token = RefreshToken(
                id=uuid.uuid4(),
                token_hash=hashlib.sha256(f"test_token_{i}".encode()).hexdigest(),
                user_id=test_user.id,
                expires_at=datetime.now(timezone.utc) + timedelta(days=7),
            )
            await repo.create(token)
            tokens.append(token)
        await db_session.commit()

        # Удаляем первый токен
        await repo.soft_delete(tokens[0].id)

        result = await repo.get_all()

        assert len(result) == 2
        assert all(t.id != tokens[0].id for t in result)

    async def test_count_returns_correct_count(
        self,
        db_session: AsyncSession,
        test_user: User
    ):
        """count возвращает правильное количество токенов"""
        repo = RefreshTokenRepository(db_session)

        for i in range(3):
            token = RefreshToken(
                id=uuid.uuid4(),
                token_hash=hashlib.sha256(f"test_token_{i}".encode()).hexdigest(),
                user_id=test_user.id,
                expires_at=datetime.now(timezone.utc) + timedelta(days=7),
            )
            await repo.create(token)
        await db_session.commit()

        count = await repo.count()

        assert count == 3

    async def test_count_excludes_soft_deleted(
        self,
        db_session: AsyncSession,
        test_user: User
    ):
        """count исключает soft-deleted токены"""
        repo = RefreshTokenRepository(db_session)

        tokens = []
        for i in range(3):
            token = RefreshToken(
                id=uuid.uuid4(),
                token_hash=hashlib.sha256(f"test_token_{i}".encode()).hexdigest(),
                user_id=test_user.id,
                expires_at=datetime.now(timezone.utc) + timedelta(days=7),
            )
            await repo.create(token)
            tokens.append(token)
        await db_session.commit()

        await repo.soft_delete(tokens[0].id)

        count = await repo.count()

        assert count == 2

    async def test_count_includes_soft_deleted_when_requested(
        self,
        db_session: AsyncSession,
        test_user: User
    ):
        """count включает soft-deleted при include_deleted=True"""
        repo = RefreshTokenRepository(db_session)

        tokens = []
        for i in range(3):
            token = RefreshToken(
                id=uuid.uuid4(),
                token_hash=hashlib.sha256(f"test_token_{i}".encode()).hexdigest(),
                user_id=test_user.id,
                expires_at=datetime.now(timezone.utc) + timedelta(days=7),
            )
            await repo.create(token)
            tokens.append(token)
        await db_session.commit()

        await repo.soft_delete(tokens[0].id)

        count = await repo.count(include_deleted=True)

        assert count == 3

    async def test_create_token_success(
        self,
        db_session: AsyncSession,
        test_user: User
    ):
        """create успешно создаёт токен в БД"""
        repo = RefreshTokenRepository(db_session)

        new_token = RefreshToken(
            id=uuid.uuid4(),
            token_hash=hashlib.sha256(b"new_token").hexdigest(),
            user_id=test_user.id,
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
            device_info="iPhone 13",
        )

        result = await repo.create(new_token)
        await db_session.commit()

        assert result.id is not None
        assert result.token_hash == new_token.token_hash
        assert result.device_info == "iPhone 13"

        # Проверка что токен действительно в БД
        found_token = await repo.get_by_id(result.id)
        assert found_token is not None
        assert found_token.token_hash == new_token.token_hash

    async def test_update_token_success(
        self,
        db_session: AsyncSession,
        test_user: User
    ):
        """update успешно обновляет токен"""
        repo = RefreshTokenRepository(db_session)

        token = RefreshToken(
            id=uuid.uuid4(),
            token_hash=hashlib.sha256(b"test_token").hexdigest(),
            user_id=test_user.id,
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
            device_info="Old Device",
        )
        await repo.create(token)
        await db_session.commit()

        updated_token = await repo.update(
            token.id,
            device_info="New Device"
        )

        assert updated_token is not None
        assert updated_token.device_info == "New Device"
        assert updated_token.token_hash == token.token_hash  # не изменилось

    async def test_update_non_existing_token_returns_none(
        self,
        db_session: AsyncSession
    ):
        """update несуществующего токена возвращает None"""
        repo = RefreshTokenRepository(db_session)
        non_existing_id = uuid.uuid4()

        result = await repo.update(non_existing_id, device_info="Test")

        assert result is None

    async def test_update_soft_deleted_token_returns_none(
        self,
        db_session: AsyncSession,
        test_user: User
    ):
        """update soft-deleted токена возвращает None"""
        repo = RefreshTokenRepository(db_session)

        token = RefreshToken(
            id=uuid.uuid4(),
            token_hash=hashlib.sha256(b"test_token").hexdigest(),
            user_id=test_user.id,
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        )
        await repo.create(token)
        await db_session.commit()
        await repo.soft_delete(token.id)

        result = await repo.update(token.id, device_info="Updated")

        assert result is None

    async def test_soft_delete_token_success(
        self,
        db_session: AsyncSession,
        test_user: User
    ):
        """soft_delete успешно помечает токен как удалённый"""
        repo = RefreshTokenRepository(db_session)

        token = RefreshToken(
            id=uuid.uuid4(),
            token_hash=hashlib.sha256(b"test_token").hexdigest(),
            user_id=test_user.id,
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        )
        await repo.create(token)
        await db_session.commit()

        success = await repo.soft_delete(token.id)

        assert success is True

        # Проверка что токен помечен как удалённый
        deleted_token = await repo.get_by_id(token.id, include_deleted=True)
        assert deleted_token is not None
        assert deleted_token.is_deleted is True

    async def test_soft_delete_non_existing_token_returns_false(
        self,
        db_session: AsyncSession
    ):
        """soft_delete несуществующего токена возвращает False"""
        repo = RefreshTokenRepository(db_session)
        non_existing_id = uuid.uuid4()

        success = await repo.soft_delete(non_existing_id)

        assert success is False

    async def test_soft_delete_already_deleted_token_returns_false(
        self,
        db_session: AsyncSession,
        test_user: User
    ):
        """soft_delete уже удалённого токена возвращает False"""
        repo = RefreshTokenRepository(db_session)

        token = RefreshToken(
            id=uuid.uuid4(),
            token_hash=hashlib.sha256(b"test_token").hexdigest(),
            user_id=test_user.id,
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        )
        await repo.create(token)
        await db_session.commit()
        await repo.soft_delete(token.id)

        success = await repo.soft_delete(token.id)

        assert success is False

    async def test_hard_delete_token_success(
        self,
        db_session: AsyncSession,
        test_user: User
    ):
        """hard_delete физически удаляет токен из БД"""
        repo = RefreshTokenRepository(db_session)

        token = RefreshToken(
            id=uuid.uuid4(),
            token_hash=hashlib.sha256(b"test_token").hexdigest(),
            user_id=test_user.id,
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        )
        await repo.create(token)
        await db_session.commit()
        token_id = token.id

        success = await repo.hard_delete(token_id)

        assert success is True

        # Проверка что токен полностью удалён из БД
        result = await repo.get_by_id(token_id, include_deleted=True)
        assert result is None

    async def test_hard_delete_non_existing_token_returns_false(
        self,
        db_session: AsyncSession
    ):
        """hard_delete несуществующего токена возвращает False"""
        repo = RefreshTokenRepository(db_session)
        non_existing_id = uuid.uuid4()

        success = await repo.hard_delete(non_existing_id)

        assert success is False


@pytest.mark.integration
class TestRefreshTokenRepositorySpecific:
    """Тесты специфичных методов RefreshTokenRepository"""

    async def test_get_by_token_hash_existing_token(
        self,
        db_session: AsyncSession,
        test_user: User
    ):
        """Получение существующего токена по хешу возвращает токен"""
        repo = RefreshTokenRepository(db_session)

        token_hash = hashlib.sha256(b"test_token").hexdigest()
        token = RefreshToken(
            id=uuid.uuid4(),
            token_hash=token_hash,
            user_id=test_user.id,
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        )
        await repo.create(token)
        await db_session.commit()

        result = await repo.get_by_token_hash(token_hash)

        assert result is not None
        assert result.id == token.id
        assert result.token_hash == token_hash

    async def test_get_by_token_hash_non_existing_token(
        self,
        db_session: AsyncSession
    ):
        """Получение несуществующего токена по хешу возвращает None"""
        repo = RefreshTokenRepository(db_session)

        result = await repo.get_by_token_hash("nonexistent_hash")

        assert result is None

    async def test_get_by_token_hash_excludes_revoked_by_default(
        self,
        db_session: AsyncSession,
        test_user: User
    ):
        """Отозванный токен исключается по умолчанию при поиске по хешу"""
        repo = RefreshTokenRepository(db_session)

        token_hash = hashlib.sha256(b"test_token").hexdigest()
        token = RefreshToken(
            id=uuid.uuid4(),
            token_hash=token_hash,
            user_id=test_user.id,
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        )
        token.is_revoked = True
        await repo.create(token)
        await db_session.commit()

        result = await repo.get_by_token_hash(token_hash)

        assert result is None

    async def test_get_by_token_hash_includes_revoked_when_requested(
        self,
        db_session: AsyncSession,
        test_user: User
    ):
        """Отозванный токен включается при include_revoked=True"""
        repo = RefreshTokenRepository(db_session)

        token_hash = hashlib.sha256(b"test_token").hexdigest()
        token = RefreshToken(
            id=uuid.uuid4(),
            token_hash=token_hash,
            user_id=test_user.id,
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        )
        token.is_revoked = True
        await repo.create(token)
        await db_session.commit()

        result = await repo.get_by_token_hash(token_hash, include_revoked=True)

        assert result is not None
        assert result.is_revoked is True

    async def test_get_by_token_hash_excludes_soft_deleted_by_default(
        self,
        db_session: AsyncSession,
        test_user: User
    ):
        """Soft-deleted токен исключается по умолчанию при поиске по хешу"""
        repo = RefreshTokenRepository(db_session)

        token_hash = hashlib.sha256(b"test_token").hexdigest()
        token = RefreshToken(
            id=uuid.uuid4(),
            token_hash=token_hash,
            user_id=test_user.id,
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        )
        await repo.create(token)
        await db_session.commit()
        await repo.soft_delete(token.id)

        result = await repo.get_by_token_hash(token_hash)

        assert result is None

    async def test_get_by_token_hash_includes_soft_deleted_when_requested(
        self,
        db_session: AsyncSession,
        test_user: User
    ):
        """Soft-deleted токен включается при include_deleted=True"""
        repo = RefreshTokenRepository(db_session)

        token_hash = hashlib.sha256(b"test_token").hexdigest()
        token = RefreshToken(
            id=uuid.uuid4(),
            token_hash=token_hash,
            user_id=test_user.id,
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        )
        await repo.create(token)
        await db_session.commit()
        await repo.soft_delete(token.id)

        result = await repo.get_by_token_hash(token_hash, include_deleted=True)

        assert result is not None
        assert result.is_deleted is True

    async def test_get_user_tokens_returns_all_user_tokens(
        self,
        db_session: AsyncSession,
        test_user: User,
        test_admin: User
    ):
        """get_user_tokens возвращает все токены конкретного пользователя"""
        repo = RefreshTokenRepository(db_session)

        # Создаём токены для test_user
        for i in range(3):
            token = RefreshToken(
                id=uuid.uuid4(),
                token_hash=hashlib.sha256(f"user_token_{i}".encode()).hexdigest(),
                user_id=test_user.id,
                expires_at=datetime.now(timezone.utc) + timedelta(days=7),
            )
            await repo.create(token)

        # Создаём токен для test_admin
        admin_token = RefreshToken(
            id=uuid.uuid4(),
            token_hash=hashlib.sha256(b"admin_token").hexdigest(),
            user_id=test_admin.id,
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        )
        await repo.create(admin_token)
        await db_session.commit()

        result = await repo.get_user_tokens(test_user.id)

        assert len(result) == 3
        assert all(t.user_id == test_user.id for t in result)
        assert not any(t.user_id == test_admin.id for t in result)

    async def test_get_user_tokens_excludes_revoked_by_default(
        self,
        db_session: AsyncSession,
        test_user: User
    ):
        """get_user_tokens исключает отозванные токены по умолчанию"""
        repo = RefreshTokenRepository(db_session)

        # Создаём активный токен
        active_token = RefreshToken(
            id=uuid.uuid4(),
            token_hash=hashlib.sha256(b"active_token").hexdigest(),
            user_id=test_user.id,
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        )
        await repo.create(active_token)

        # Создаём отозванный токен
        revoked_token = RefreshToken(
            id=uuid.uuid4(),
            token_hash=hashlib.sha256(b"revoked_token").hexdigest(),
            user_id=test_user.id,
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        )
        revoked_token.is_revoked = True
        await repo.create(revoked_token)
        await db_session.commit()

        result = await repo.get_user_tokens(test_user.id)

        assert len(result) == 1
        assert result[0].id == active_token.id
        assert not any(t.id == revoked_token.id for t in result)

    async def test_get_user_tokens_includes_revoked_when_requested(
        self,
        db_session: AsyncSession,
        test_user: User
    ):
        """get_user_tokens включает отозванные токены при include_revoked=True"""
        repo = RefreshTokenRepository(db_session)

        # Создаём активный токен
        active_token = RefreshToken(
            id=uuid.uuid4(),
            token_hash=hashlib.sha256(b"active_token").hexdigest(),
            user_id=test_user.id,
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        )
        await repo.create(active_token)

        # Создаём отозванный токен
        revoked_token = RefreshToken(
            id=uuid.uuid4(),
            token_hash=hashlib.sha256(b"revoked_token").hexdigest(),
            user_id=test_user.id,
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        )
        revoked_token.is_revoked = True
        await repo.create(revoked_token)
        await db_session.commit()

        result = await repo.get_user_tokens(test_user.id, include_revoked=True)

        assert len(result) == 2
        assert any(t.id == active_token.id for t in result)
        assert any(t.id == revoked_token.id for t in result)

    async def test_get_user_tokens_excludes_soft_deleted_by_default(
        self,
        db_session: AsyncSession,
        test_user: User
    ):
        """get_user_tokens исключает soft-deleted токены по умолчанию"""
        repo = RefreshTokenRepository(db_session)

        tokens = []
        for i in range(2):
            token = RefreshToken(
                id=uuid.uuid4(),
                token_hash=hashlib.sha256(f"token_{i}".encode()).hexdigest(),
                user_id=test_user.id,
                expires_at=datetime.now(timezone.utc) + timedelta(days=7),
            )
            await repo.create(token)
            tokens.append(token)
        await db_session.commit()

        # Удаляем первый токен
        await repo.soft_delete(tokens[0].id)

        result = await repo.get_user_tokens(test_user.id)

        assert len(result) == 1
        assert result[0].id == tokens[1].id

    async def test_is_token_valid_returns_true_for_valid_token(
        self,
        db_session: AsyncSession,
        test_user: User
    ):
        """is_token_valid возвращает True для валидного токена"""
        repo = RefreshTokenRepository(db_session)

        token_hash = hashlib.sha256(b"valid_token").hexdigest()
        token = RefreshToken(
            id=uuid.uuid4(),
            token_hash=token_hash,
            user_id=test_user.id,
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        )
        await repo.create(token)
        await db_session.commit()

        is_valid = await repo.is_token_valid(token_hash)

        assert is_valid is True

    async def test_is_token_valid_returns_false_for_non_existing_token(
        self,
        db_session: AsyncSession
    ):
        """is_token_valid возвращает False для несуществующего токена"""
        repo = RefreshTokenRepository(db_session)

        is_valid = await repo.is_token_valid("nonexistent_hash")

        assert is_valid is False

    async def test_is_token_valid_returns_false_for_expired_token(
        self,
        db_session: AsyncSession,
        test_user: User
    ):
        """is_token_valid возвращает False для истекшего токена"""
        repo = RefreshTokenRepository(db_session)

        token_hash = hashlib.sha256(b"expired_token").hexdigest()
        token = RefreshToken(
            id=uuid.uuid4(),
            token_hash=token_hash,
            user_id=test_user.id,
            expires_at=datetime.now(timezone.utc) - timedelta(days=1),  # истёк вчера
        )
        await repo.create(token)
        await db_session.commit()

        is_valid = await repo.is_token_valid(token_hash)

        assert is_valid is False

    async def test_is_token_valid_returns_false_for_revoked_token(
        self,
        db_session: AsyncSession,
        test_user: User
    ):
        """is_token_valid возвращает False для отозванного токена"""
        repo = RefreshTokenRepository(db_session)

        token_hash = hashlib.sha256(b"revoked_token").hexdigest()
        token = RefreshToken(
            id=uuid.uuid4(),
            token_hash=token_hash,
            user_id=test_user.id,
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        )
        token.is_revoked = True
        await repo.create(token)
        await db_session.commit()

        is_valid = await repo.is_token_valid(token_hash)

        assert is_valid is False

    async def test_is_token_valid_returns_false_for_soft_deleted_token(
        self,
        db_session: AsyncSession,
        test_user: User
    ):
        """is_token_valid возвращает False для soft-deleted токена"""
        repo = RefreshTokenRepository(db_session)

        token_hash = hashlib.sha256(b"deleted_token").hexdigest()
        token = RefreshToken(
            id=uuid.uuid4(),
            token_hash=token_hash,
            user_id=test_user.id,
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        )
        await repo.create(token)
        await db_session.commit()
        await repo.soft_delete(token.id)

        is_valid = await repo.is_token_valid(token_hash)

        assert is_valid is False

    async def test_revoke_token_success(
        self,
        db_session: AsyncSession,
        test_user: User
    ):
        """revoke_token успешно отзывает токен"""
        repo = RefreshTokenRepository(db_session)

        token_hash = hashlib.sha256(b"test_token").hexdigest()
        token = RefreshToken(
            id=uuid.uuid4(),
            token_hash=token_hash,
            user_id=test_user.id,
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        )
        await repo.create(token)
        await db_session.commit()

        success = await repo.revoke_token(token_hash)

        assert success is True

        # Проверка что токен отозван
        revoked_token = await repo.get_by_token_hash(token_hash, include_revoked=True)
        assert revoked_token is not None
        assert revoked_token.is_revoked is True

    async def test_revoke_token_returns_false_for_non_existing_token(
        self,
        db_session: AsyncSession
    ):
        """revoke_token возвращает False для несуществующего токена"""
        repo = RefreshTokenRepository(db_session)

        success = await repo.revoke_token("nonexistent_hash")

        assert success is False

    async def test_revoke_token_returns_false_for_already_revoked_token(
        self,
        db_session: AsyncSession,
        test_user: User
    ):
        """revoke_token возвращает False для уже отозванного токена"""
        repo = RefreshTokenRepository(db_session)

        token_hash = hashlib.sha256(b"test_token").hexdigest()
        token = RefreshToken(
            id=uuid.uuid4(),
            token_hash=token_hash,
            user_id=test_user.id,
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        )
        token.is_revoked = True
        await repo.create(token)
        await db_session.commit()

        success = await repo.revoke_token(token_hash)

        assert success is False

    async def test_revoke_token_returns_false_for_soft_deleted_token(
        self,
        db_session: AsyncSession,
        test_user: User
    ):
        """revoke_token возвращает False для soft-deleted токена"""
        repo = RefreshTokenRepository(db_session)

        token_hash = hashlib.sha256(b"test_token").hexdigest()
        token = RefreshToken(
            id=uuid.uuid4(),
            token_hash=token_hash,
            user_id=test_user.id,
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        )
        await repo.create(token)
        await db_session.commit()
        await repo.soft_delete(token.id)

        success = await repo.revoke_token(token_hash)

        assert success is False

    async def test_revoke_all_user_tokens_success(
        self,
        db_session: AsyncSession,
        test_user: User
    ):
        """revoke_all_user_tokens успешно отзывает все токены пользователя"""
        repo = RefreshTokenRepository(db_session)

        # Создаём 3 токена
        tokens = []
        for i in range(3):
            token = RefreshToken(
                id=uuid.uuid4(),
                token_hash=hashlib.sha256(f"token_{i}".encode()).hexdigest(),
                user_id=test_user.id,
                expires_at=datetime.now(timezone.utc) + timedelta(days=7),
            )
            await repo.create(token)
            tokens.append(token)
        await db_session.commit()

        count = await repo.revoke_all_user_tokens(test_user.id)

        assert count == 3

        # Проверка что все токены отозваны
        user_tokens = await repo.get_user_tokens(test_user.id, include_revoked=True)
        assert all(t.is_revoked is True for t in user_tokens)

    async def test_revoke_all_user_tokens_excludes_already_revoked(
        self,
        db_session: AsyncSession,
        test_user: User
    ):
        """revoke_all_user_tokens не считает уже отозванные токены"""
        repo = RefreshTokenRepository(db_session)

        # Создаём активный токен
        active_token = RefreshToken(
            id=uuid.uuid4(),
            token_hash=hashlib.sha256(b"active_token").hexdigest(),
            user_id=test_user.id,
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        )
        await repo.create(active_token)

        # Создаём уже отозванный токен
        revoked_token = RefreshToken(
            id=uuid.uuid4(),
            token_hash=hashlib.sha256(b"revoked_token").hexdigest(),
            user_id=test_user.id,
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        )
        revoked_token.is_revoked = True
        await repo.create(revoked_token)
        await db_session.commit()

        count = await repo.revoke_all_user_tokens(test_user.id)

        assert count == 1  # только active_token был отозван

    async def test_revoke_all_user_tokens_excludes_soft_deleted(
        self,
        db_session: AsyncSession,
        test_user: User
    ):
        """revoke_all_user_tokens не учитывает soft-deleted токены"""
        repo = RefreshTokenRepository(db_session)

        # Создаём активный токен
        active_token = RefreshToken(
            id=uuid.uuid4(),
            token_hash=hashlib.sha256(b"active_token").hexdigest(),
            user_id=test_user.id,
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        )
        await repo.create(active_token)

        # Создаём удалённый токен
        deleted_token = RefreshToken(
            id=uuid.uuid4(),
            token_hash=hashlib.sha256(b"deleted_token").hexdigest(),
            user_id=test_user.id,
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        )
        await repo.create(deleted_token)
        await db_session.commit()
        await repo.soft_delete(deleted_token.id)

        count = await repo.revoke_all_user_tokens(test_user.id)

        assert count == 1  # только active_token был отозван

    async def test_revoke_all_user_tokens_returns_zero_for_user_without_tokens(
        self,
        db_session: AsyncSession,
        test_user: User
    ):
        """revoke_all_user_tokens возвращает 0 для пользователя без токенов"""
        repo = RefreshTokenRepository(db_session)

        count = await repo.revoke_all_user_tokens(test_user.id)

        assert count == 0

    async def test_delete_expired_tokens_removes_expired(
        self,
        db_session: AsyncSession,
        test_user: User
    ):
        """delete_expired_tokens удаляет только истекшие токены"""
        repo = RefreshTokenRepository(db_session)

        # Создаём истекший токен
        expired_token = RefreshToken(
            id=uuid.uuid4(),
            token_hash=hashlib.sha256(b"expired_token").hexdigest(),
            user_id=test_user.id,
            expires_at=datetime.now(timezone.utc) - timedelta(days=1),
        )
        await repo.create(expired_token)

        # Создаём валидный токен
        valid_token = RefreshToken(
            id=uuid.uuid4(),
            token_hash=hashlib.sha256(b"valid_token").hexdigest(),
            user_id=test_user.id,
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        )
        await repo.create(valid_token)
        await db_session.commit()

        count = await repo.delete_expired_tokens()

        assert count == 1

        # Проверка что истекший токен удалён
        all_tokens = await repo.get_all(include_deleted=True)
        assert len(all_tokens) == 1
        assert all_tokens[0].id == valid_token.id

    async def test_delete_expired_tokens_returns_zero_when_no_expired(
        self,
        db_session: AsyncSession,
        test_user: User
    ):
        """delete_expired_tokens возвращает 0 когда нет истекших токенов"""
        repo = RefreshTokenRepository(db_session)

        # Создаём только валидный токен
        valid_token = RefreshToken(
            id=uuid.uuid4(),
            token_hash=hashlib.sha256(b"valid_token").hexdigest(),
            user_id=test_user.id,
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        )
        await repo.create(valid_token)
        await db_session.commit()

        count = await repo.delete_expired_tokens()

        assert count == 0

    async def test_delete_expired_tokens_physical_deletion(
        self,
        db_session: AsyncSession,
        test_user: User
    ):
        """delete_expired_tokens выполняет физическое удаление, а не soft delete"""
        repo = RefreshTokenRepository(db_session)

        expired_token = RefreshToken(
            id=uuid.uuid4(),
            token_hash=hashlib.sha256(b"expired_token").hexdigest(),
            user_id=test_user.id,
            expires_at=datetime.now(timezone.utc) - timedelta(days=1),
        )
        await repo.create(expired_token)
        await db_session.commit()
        expired_id = expired_token.id

        await repo.delete_expired_tokens()

        # Проверка что токен полностью удалён (даже с include_deleted=True)
        result = await repo.get_by_id(expired_id, include_deleted=True)
        assert result is None

    async def test_delete_user_expired_tokens_removes_only_user_expired(
        self,
        db_session: AsyncSession,
        test_user: User,
        test_admin: User
    ):
        """delete_user_expired_tokens удаляет только истекшие токены конкретного пользователя"""
        repo = RefreshTokenRepository(db_session)

        # Создаём истекший токен для test_user
        user_expired_token = RefreshToken(
            id=uuid.uuid4(),
            token_hash=hashlib.sha256(b"user_expired").hexdigest(),
            user_id=test_user.id,
            expires_at=datetime.now(timezone.utc) - timedelta(days=1),
        )
        await repo.create(user_expired_token)

        # Создаём валидный токен для test_user
        user_valid_token = RefreshToken(
            id=uuid.uuid4(),
            token_hash=hashlib.sha256(b"user_valid").hexdigest(),
            user_id=test_user.id,
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        )
        await repo.create(user_valid_token)

        # Создаём истекший токен для test_admin
        admin_expired_token = RefreshToken(
            id=uuid.uuid4(),
            token_hash=hashlib.sha256(b"admin_expired").hexdigest(),
            user_id=test_admin.id,
            expires_at=datetime.now(timezone.utc) - timedelta(days=1),
        )
        await repo.create(admin_expired_token)
        await db_session.commit()

        count = await repo.delete_user_expired_tokens(test_user.id)

        assert count == 1

        # Проверка что удалён только токен test_user
        all_tokens = await repo.get_all(include_deleted=True)
        assert len(all_tokens) == 2
        assert any(t.id == user_valid_token.id for t in all_tokens)
        assert any(t.id == admin_expired_token.id for t in all_tokens)
        assert not any(t.id == user_expired_token.id for t in all_tokens)

    async def test_delete_user_expired_tokens_returns_zero_when_no_expired(
        self,
        db_session: AsyncSession,
        test_user: User
    ):
        """delete_user_expired_tokens возвращает 0 когда нет истекших токенов"""
        repo = RefreshTokenRepository(db_session)

        # Создаём только валидный токен
        valid_token = RefreshToken(
            id=uuid.uuid4(),
            token_hash=hashlib.sha256(b"valid_token").hexdigest(),
            user_id=test_user.id,
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        )
        await repo.create(valid_token)
        await db_session.commit()

        count = await repo.delete_user_expired_tokens(test_user.id)

        assert count == 0

    async def test_count_user_active_tokens_counts_only_active(
        self,
        db_session: AsyncSession,
        test_user: User
    ):
        """count_user_active_tokens считает только активные токены"""
        repo = RefreshTokenRepository(db_session)

        # Создаём активный токен
        active_token = RefreshToken(
            id=uuid.uuid4(),
            token_hash=hashlib.sha256(b"active").hexdigest(),
            user_id=test_user.id,
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        )
        await repo.create(active_token)

        # Создаём истекший токен
        expired_token = RefreshToken(
            id=uuid.uuid4(),
            token_hash=hashlib.sha256(b"expired").hexdigest(),
            user_id=test_user.id,
            expires_at=datetime.now(timezone.utc) - timedelta(days=1),
        )
        await repo.create(expired_token)

        # Создаём отозванный токен
        revoked_token = RefreshToken(
            id=uuid.uuid4(),
            token_hash=hashlib.sha256(b"revoked").hexdigest(),
            user_id=test_user.id,
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        )
        revoked_token.is_revoked = True
        await repo.create(revoked_token)

        # Создаём удалённый токен
        deleted_token = RefreshToken(
            id=uuid.uuid4(),
            token_hash=hashlib.sha256(b"deleted").hexdigest(),
            user_id=test_user.id,
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        )
        await repo.create(deleted_token)
        await db_session.commit()
        await repo.soft_delete(deleted_token.id)

        count = await repo.count_user_active_tokens(test_user.id)

        assert count == 1  # только active_token

    async def test_count_user_active_tokens_returns_zero_for_user_without_tokens(
        self,
        db_session: AsyncSession,
        test_user: User
    ):
        """count_user_active_tokens возвращает 0 для пользователя без активных токенов"""
        repo = RefreshTokenRepository(db_session)

        count = await repo.count_user_active_tokens(test_user.id)

        assert count == 0

    async def test_count_user_active_tokens_multiple_active(
        self,
        db_session: AsyncSession,
        test_user: User
    ):
        """count_user_active_tokens правильно считает несколько активных токенов"""
        repo = RefreshTokenRepository(db_session)

        # Создаём 3 активных токена
        for i in range(3):
            token = RefreshToken(
                id=uuid.uuid4(),
                token_hash=hashlib.sha256(f"active_{i}".encode()).hexdigest(),
                user_id=test_user.id,
                expires_at=datetime.now(timezone.utc) + timedelta(days=7),
            )
            await repo.create(token)
        await db_session.commit()

        count = await repo.count_user_active_tokens(test_user.id)

        assert count == 3

    async def test_count_user_active_tokens_excludes_other_users(
        self,
        db_session: AsyncSession,
        test_user: User,
        test_admin: User
    ):
        """count_user_active_tokens не учитывает токены других пользователей"""
        repo = RefreshTokenRepository(db_session)

        # Создаём токены для test_user
        for i in range(2):
            token = RefreshToken(
                id=uuid.uuid4(),
                token_hash=hashlib.sha256(f"user_token_{i}".encode()).hexdigest(),
                user_id=test_user.id,
                expires_at=datetime.now(timezone.utc) + timedelta(days=7),
            )
            await repo.create(token)

        # Создаём токены для test_admin
        for i in range(3):
            token = RefreshToken(
                id=uuid.uuid4(),
                token_hash=hashlib.sha256(f"admin_token_{i}".encode()).hexdigest(),
                user_id=test_admin.id,
                expires_at=datetime.now(timezone.utc) + timedelta(days=7),
            )
            await repo.create(token)
        await db_session.commit()

        count = await repo.count_user_active_tokens(test_user.id)

        assert count == 2  # только токены test_user
