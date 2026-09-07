from sqlalchemy import BigInteger, String, Integer, Boolean, Text, ForeignKey, UniqueConstraint, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from typing import Optional

from db.base import Base, TimestampMixin, BigIntPK


class ReputationScore(Base, TimestampMixin):
    """Internal reputation score for matching quality improvement."""

    __tablename__ = "reputation_scores"

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id"), unique=True, nullable=False
    )
    score: Mapped[float] = mapped_column(Numeric(5, 2), default=50.0)
    total_meetings: Mapped[int] = mapped_column(Integer, default=0)
    times_selected: Mapped[int] = mapped_column(Integer, default=0)
    no_show_count: Mapped[int] = mapped_column(Integer, default=0)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="reputation")

    def __repr__(self) -> str:
        return f"<Reputation user={self.user_id} score={self.score}>"
