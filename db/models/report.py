from sqlalchemy import BigInteger, String, Integer, Boolean, Text, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from typing import Optional

from db.base import Base, TimestampMixin, BigIntPK


class Report(Base, TimestampMixin):
    """User report about another user."""

    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    reporter_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False)
    reported_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False)
    table_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("tables.id"), nullable=True
    )
    reason: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[str] = mapped_column(
        String(20), default="pending"
    )  # pending, reviewed, resolved
    admin_notes: Mapped[Optional[str]] = mapped_column(Text)

    def __repr__(self) -> str:
        return f"<Report id={self.id} reporter={self.reporter_id} reported={self.reported_id}>"


class Block(Base, TimestampMixin):
    """User block — blocked user is never matched with blocker."""

    __tablename__ = "blocks"

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    blocker_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False)
    blocked_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False)

    __table_args__ = (
        UniqueConstraint("blocker_id", "blocked_id", name="uq_block"),
    )

    def __repr__(self) -> str:
        return f"<Block blocker={self.blocker_id} blocked={self.blocked_id}>"


class NoShow(Base, TimestampMixin):
    """No-show record confirmed by peer reports (2 of 3 agreement)."""

    __tablename__ = "no_shows"

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False)
    table_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("tables.id"), nullable=False)
    reported_by_count: Mapped[int] = mapped_column(Integer, default=0)
    confirmed: Mapped[bool] = mapped_column(Boolean, default=False)

    def __repr__(self) -> str:
        return f"<NoShow user={self.user_id} table={self.table_id} confirmed={self.confirmed}>"
