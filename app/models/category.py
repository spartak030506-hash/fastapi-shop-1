from __future__ import annotations

from typing import TYPE_CHECKING
import uuid

from sqlalchemy import String, Boolean, ForeignKey, Index, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.product import Product


class Category(BaseModel):
    """Модель категории товаров с поддержкой иерархии"""

    __tablename__ = "categories"

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    slug: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        String(1000),
        nullable=True,
    )

    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("categories.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
    )

    # Relationships
    parent: Mapped["Category | None"] = relationship(
        "Category",
        remote_side="Category.id",
        back_populates="children",
        lazy="selectin",
    )

    children: Mapped[list["Category"]] = relationship(
        "Category",
        back_populates="parent",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    products: Mapped[list["Product"]] = relationship(
        "Product",
        back_populates="category",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    # Индексы с учетом soft delete
    __table_args__ = (
        # Уникальность name в рамках одного parent (только для активных)
        Index(
            "ix_category_parent_name",
            "parent_id",
            "name",
            unique=True,
            postgresql_where=text("is_deleted = false"),
        ),
        # Уникальность slug (только для активных)
        Index(
            "ix_category_slug",
            "slug",
            unique=True,
            postgresql_where=text("is_deleted = false"),
        ),
    )
