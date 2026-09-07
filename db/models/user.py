from sqlalchemy import BigInteger, String, Boolean, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from typing import Optional, List

from db.base import Base, TimestampMixin, BigIntPK


class User(Base, TimestampMixin):
    """Telegram user who interacts with the Teahouse bot."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False, index=True)
    username: Mapped[Optional[str]] = mapped_column(String(255))
    first_name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[Optional[str]] = mapped_column(String(20))
    language: Mapped[str] = mapped_column(String(5), default="uz")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_banned: Mapped[bool] = mapped_column(Boolean, default=False)
    credit_balance: Mapped[int] = mapped_column(Integer, default=0)
    referred_by: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("users.id"), nullable=True
    )

    # Relationships
    profile: Mapped[Optional["Profile"]] = relationship(
        "Profile", back_populates="user", uselist=False, lazy="selectin"
    )
    interview_sessions: Mapped[List["InterviewSession"]] = relationship(
        "InterviewSession", back_populates="user", lazy="selectin"
    )
    table_memberships: Mapped[List["TableMember"]] = relationship(
        "TableMember", back_populates="user", lazy="selectin"
    )
    reputation: Mapped[Optional["ReputationScore"]] = relationship(
        "ReputationScore", back_populates="user", uselist=False, lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} tg={self.telegram_id} name={self.first_name}>"
