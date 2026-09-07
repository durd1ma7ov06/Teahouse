from sqlalchemy import BigInteger, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from typing import Optional

from db.base import Base, TimestampMixin, BigIntPK


class Reveal(Base, TimestampMixin):
    """Tracks what was revealed to each table member 24h before meeting."""

    __tablename__ = "reveals"

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    table_member_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("table_members.id"), nullable=False, unique=True
    )
    venue_sent: Mapped[bool] = mapped_column(Boolean, default=False)
    profiles_sent: Mapped[bool] = mapped_column(Boolean, default=False)
    questions_sent: Mapped[bool] = mapped_column(Boolean, default=False)
    sent_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)

    # Relationships
    table_member: Mapped["TableMember"] = relationship("TableMember", back_populates="reveal")

    def __repr__(self) -> str:
        return f"<Reveal member={self.table_member_id} sent={self.sent_at}>"
