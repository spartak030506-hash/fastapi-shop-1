"""Add server_default to all boolean and int columns

Revision ID: 3cd76b50f997
Revises: 57a33d905860
Create Date: 2025-12-07 19:49:59.565374

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3cd76b50f997'
down_revision: Union[str, None] = '57a33d905860'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Добавляем server_default для users таблицы
    op.alter_column('users', 'is_active',
                    existing_type=sa.Boolean(),
                    server_default='true',
                    existing_nullable=False)

    op.alter_column('users', 'is_verified',
                    existing_type=sa.Boolean(),
                    server_default='false',
                    existing_nullable=False)

    op.alter_column('users', 'is_deleted',
                    existing_type=sa.Boolean(),
                    server_default='false',
                    existing_nullable=False)

    op.alter_column('users', 'role',
                    existing_type=sa.Enum('CUSTOMER', 'ADMIN', name='user_role', native_enum=False),
                    server_default='CUSTOMER',
                    existing_nullable=False)

    # Добавляем server_default для refresh_tokens таблицы
    op.alter_column('refresh_tokens', 'is_revoked',
                    existing_type=sa.Boolean(),
                    server_default='false',
                    existing_nullable=False)

    op.alter_column('refresh_tokens', 'is_deleted',
                    existing_type=sa.Boolean(),
                    server_default='false',
                    existing_nullable=False)

    # Добавляем server_default для categories таблицы
    op.alter_column('categories', 'is_active',
                    existing_type=sa.Boolean(),
                    server_default='true',
                    existing_nullable=False)

    op.alter_column('categories', 'is_deleted',
                    existing_type=sa.Boolean(),
                    server_default='false',
                    existing_nullable=False)

    # Добавляем server_default для products таблицы
    op.alter_column('products', 'is_active',
                    existing_type=sa.Boolean(),
                    server_default='true',
                    existing_nullable=False)

    op.alter_column('products', 'is_deleted',
                    existing_type=sa.Boolean(),
                    server_default='false',
                    existing_nullable=False)

    op.alter_column('products', 'stock_quantity',
                    existing_type=sa.Integer(),
                    server_default='0',
                    existing_nullable=False)


def downgrade() -> None:
    # Убираем server_default (откат)
    op.alter_column('products', 'stock_quantity',
                    existing_type=sa.Integer(),
                    server_default=None,
                    existing_nullable=False)

    op.alter_column('products', 'is_deleted',
                    existing_type=sa.Boolean(),
                    server_default=None,
                    existing_nullable=False)

    op.alter_column('products', 'is_active',
                    existing_type=sa.Boolean(),
                    server_default=None,
                    existing_nullable=False)

    op.alter_column('categories', 'is_deleted',
                    existing_type=sa.Boolean(),
                    server_default=None,
                    existing_nullable=False)

    op.alter_column('categories', 'is_active',
                    existing_type=sa.Boolean(),
                    server_default=None,
                    existing_nullable=False)

    op.alter_column('refresh_tokens', 'is_deleted',
                    existing_type=sa.Boolean(),
                    server_default=None,
                    existing_nullable=False)

    op.alter_column('refresh_tokens', 'is_revoked',
                    existing_type=sa.Boolean(),
                    server_default=None,
                    existing_nullable=False)

    op.alter_column('users', 'role',
                    existing_type=sa.Enum('CUSTOMER', 'ADMIN', name='user_role', native_enum=False),
                    server_default=None,
                    existing_nullable=False)

    op.alter_column('users', 'is_deleted',
                    existing_type=sa.Boolean(),
                    server_default=None,
                    existing_nullable=False)

    op.alter_column('users', 'is_verified',
                    existing_type=sa.Boolean(),
                    server_default=None,
                    existing_nullable=False)

    op.alter_column('users', 'is_active',
                    existing_type=sa.Boolean(),
                    server_default=None,
                    existing_nullable=False)
