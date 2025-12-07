from __future__ import annotations

from typing import TYPE_CHECKING
import uuid
from decimal import Decimal

from sqlalchemy import String, Boolean, ForeignKey, Integer, Numeric, CheckConstraint, Index, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.category import Category


class Product(BaseModel):
    """Модель товара"""

    __tablename__ = "products"

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )

    slug: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        String(2000),
        nullable=True,
    )

    price: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),  # 10 цифр всего, 2 после запятой (макс. 99999999.99)
        nullable=False,
    )

    category_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("categories.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    stock_quantity: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )

    sku: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    image_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
    )

    # Relationships
    category: Mapped["Category"] = relationship(
        "Category",
        back_populates="products",
        lazy="selectin",
    )

    # Constraints и индексы с учетом soft delete
    __table_args__ = (
        # Валидация данных на уровне БД
        CheckConstraint("price > 0", name="check_price_positive"),
        CheckConstraint("stock_quantity >= 0", name="check_stock_non_negative"),
        # Уникальность slug (только для активных)
        Index(
            "ix_product_slug",
            "slug",
            unique=True,
            postgresql_where=text("is_deleted = false"),
        ),
        # Уникальность sku (только для активных и не-null)
        Index(
            "ix_product_sku",
            "sku",
            unique=True,
            postgresql_where=text("sku IS NOT NULL AND is_deleted = false"),
        ),
    )
