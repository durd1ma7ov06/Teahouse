from sqlalchemy import BigInteger, String, Integer, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from typing import Optional, List

from db.base import Base, TimestampMixin, BigIntPK


class Slot(Base, TimestampMixin):
    """A weekly meeting slot (one per week)."""

    __tablename__ = "slots"

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    week_number: Mapped[int] = mapped_column(Integer, nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    meeting_at: Mapped[datetime] = mapped_column(nullable=False)        # Wed 20:00
    offer_wave1_at: Mapped[datetime] = mapped_column(nullable=False)    # Mon 20:00
    offer_wave2_at: Mapped[datetime] = mapped_column(nullable=False)    # Tue 10:00
    reveal_at: Mapped[datetime] = mapped_column(nullable=False)         # Tue 20:00
    roster_locked: Mapped[bool] = mapped_column(Boolean, default=False)
    status: Mapped[str] = mapped_column(
        String(20), default="upcoming"
    )  # upcoming, active, completed

    # Relationships
    tables: Mapped[List["Table"]] = relationship("Table", back_populates="slot", lazy="selectin")

    def __repr__(self) -> str:
        return f"<Slot id={self.id} week={self.week_number}/{self.year} status={self.status}>"
