from sqlalchemy import BigInteger, String, Integer, Boolean, Numeric, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from typing import Optional

from db.base import Base, TimestampMixin, BigIntPK


class Venue(Base, TimestampMixin):
    """Partner café where meetings take place."""

    __tablename__ = "venues"

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    address: Mapped[str] = mapped_column(String(500), nullable=False)
    latitude: Mapped[float] = mapped_column(Numeric(10, 7), nullable=False)
    longitude: Mapped[float] = mapped_column(Numeric(10, 7), nullable=False)
    max_capacity: Mapped[int] = mapped_column(Integer, default=4)
    takes_reservations: Mapped[bool] = mapped_column(Boolean, default=True)
    contact_phone: Mapped[Optional[str]] = mapped_column(String(20))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Relationships
    tables: Mapped[list["Table"]] = relationship("Table", back_populates="venue", lazy="selectin")

    def __repr__(self) -> str:
        return f"<Venue id={self.id} title={self.title}>"
