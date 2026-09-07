from sqlalchemy import BigInteger, String, Integer, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from typing import Optional

from db.base import Base, TimestampMixin, BigIntPK


class Referral(Base, TimestampMixin):
    """Referral tracking via deep links."""

    __tablename__ = "referrals"

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    referrer_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False)
    referred_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("users.id"), nullable=True
    )
    deep_link_code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), default="clicked"
    )  # clicked, registered, first_meeting

    def __repr__(self) -> str:
        return f"<Referral code={self.deep_link_code} status={self.status}>"


class Credit(Base, TimestampMixin):
    """Star credits issued as compensation (not advertised)."""

    __tablename__ = "credits"

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False)
    amount_stars: Mapped[int] = mapped_column(Integer, nullable=False)
    reason: Mapped[Optional[str]] = mapped_column(String(50))  # empty_seat, table_cancelled
    table_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("tables.id"), nullable=True
    )
    used: Mapped[bool] = mapped_column(Boolean, default=False)

    def __repr__(self) -> str:
        return f"<Credit user={self.user_id} stars={self.amount_stars} used={self.used}>"
