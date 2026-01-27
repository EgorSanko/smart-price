"""SQLAlchemy Base class and common mixins."""

from datetime import datetime

from sqlalchemy import DateTime, Integer, func
from sqlalchemy.orm import DeclarativeBase, Mapped, declared_attr, mapped_column


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models.

    Provides:
        - Automatic __tablename__ generation from class name
        - Common id primary key
        - repr() for debugging
    """

    # Generate __tablename__ automatically from class name
    @declared_attr.directive
    @classmethod
    def __tablename__(cls) -> str:
        """Convert CamelCase to snake_case for table name."""
        name = cls.__name__
        # CamelCase -> snake_case: ProductMatch -> product_matches
        import re

        s1 = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", name)
        table_name = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s1).lower()
        # Pluralize: product_match -> product_matches
        if table_name.endswith("y"):
            return table_name[:-1] + "ies"
        elif table_name.endswith(("s", "x", "ch", "sh")):
            return table_name + "es"
        return table_name + "s"

    # Common primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    def __repr__(self) -> str:
        """Generate repr string with all column values."""
        cols = [f"{c.name}={getattr(self, c.name)!r}" for c in self.__table__.columns]
        return f"{self.__class__.__name__}({', '.join(cols[:3])}{'...' if len(cols) > 3 else ''})"


class TimestampMixin:
    """Mixin that adds created_at and updated_at timestamps.

    Usage:
        class Product(Base, TimestampMixin):
            ...
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class SoftDeleteMixin:
    """Mixin for soft delete functionality.

    Instead of deleting records, marks them as deleted.

    Usage:
        class Product(Base, SoftDeleteMixin):
            ...
    """

    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
    )

    @property
    def is_deleted(self) -> bool:
        """Check if record is soft-deleted."""
        return self.deleted_at is not None
