from sqlalchemy import BigInteger, String, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from typing import Optional

from db.base import Base, TimestampMixin, BigIntPK


class Payment(Base, TimestampMixin):
    """Payment record for a seat booking."""

    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False)
    table_member_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("table_members.id"), nullable=False
    )
    amount_uzs: Mapped[int] = mapped_column(Integer, nullable=False, default=99000)
    amount_stars: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    credits_used: Mapped[int] = mapped_column(Integer, default=0)
    method: Mapped[str] = mapped_column(String(20), default="stars")  # stars, payme, click
    charge_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), default="pending"
    )  # pending, completed, refunded

    # Relationships
    user: Mapped["User"] = relationship("User")
    table_member: Mapped["TableMember"] = relationship("TableMember", back_populates="payment")

    def __repr__(self) -> str:
        return f"<Payment id={self.id} user={self.user_id} status={self.status}>"
