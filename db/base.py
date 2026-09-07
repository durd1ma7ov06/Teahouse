from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import func, BigInteger, Integer
from datetime import datetime

# SQLite'da autoincrement ROWID bo'lishi uchun INTEGER, PostgreSQL'da esa BIGSERIAL
BigIntPK = BigInteger().with_variant(Integer, "sqlite")


class Base(DeclarativeBase):
    """Base class for all database models."""
    pass


class TimestampMixin:
    """Mixin that adds created_at and updated_at columns."""

    created_at: Mapped[datetime] = mapped_column(
        default=func.now(),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        default=func.now(),
        server_default=func.now(),
        onupdate=func.now(),
    )
