from sqlalchemy import BigInteger, String, Integer, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from typing import Optional

from db.base import Base, TimestampMixin, BigIntPK


class Profile(Base, TimestampMixin):
    """User professional profile built from the interview."""

    __tablename__ = "profiles"

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id"), unique=True, nullable=False
    )
    role: Mapped[Optional[str]] = mapped_column(String(255))
    company: Mapped[Optional[str]] = mapped_column(String(255))
    industry: Mapped[Optional[str]] = mapped_column(String(255))
    stage: Mapped[Optional[str]] = mapped_column(String(100))
    current_goal: Mapped[Optional[str]] = mapped_column(Text)
    can_offer: Mapped[Optional[str]] = mapped_column(Text)
    seniority: Mapped[Optional[str]] = mapped_column(String(50))
    experience_years: Mapped[Optional[int]] = mapped_column(Integer)
    age: Mapped[Optional[int]] = mapped_column(Integer)
    achievements: Mapped[Optional[str]] = mapped_column(Text)  # Eng katta yutuqlari va tajribasi
    target_partner: Mapped[Optional[str]] = mapped_column(Text)  # Qidirayotgan sherigi
    target_industry: Mapped[Optional[str]] = mapped_column(String(255))
    target_seniority: Mapped[Optional[str]] = mapped_column(String(100))  # Qidirayotgan sherigining darajasi
    interests: Mapped[Optional[str]] = mapped_column(Text)  # Muhokama mavzulari
    bio_summary: Mapped[Optional[str]] = mapped_column(Text)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="profile")

    def __repr__(self) -> str:
        return f"<Profile user_id={self.user_id} role={self.role}>"
