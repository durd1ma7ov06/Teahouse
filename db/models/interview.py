from sqlalchemy import BigInteger, String, Integer, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from typing import Optional, List

from db.base import Base, TimestampMixin, BigIntPK


class InterviewSession(Base, TimestampMixin):
    """A single interview session with a user."""

    __tablename__ = "interview_sessions"

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), default="in_progress"
    )  # in_progress, completed, abandoned
    total_turns: Mapped[int] = mapped_column(Integer, default=0)
    completed_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="interview_sessions")
    answers: Mapped[List["InterviewAnswer"]] = relationship(
        "InterviewAnswer", back_populates="session", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<InterviewSession id={self.id} user={self.user_id} status={self.status}>"


class InterviewAnswer(Base, TimestampMixin):
    """Individual answer within an interview session."""

    __tablename__ = "interview_answers"

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("interview_sessions.id"), nullable=False
    )
    question_key: Mapped[str] = mapped_column(
        String(100), nullable=False
    )  # role, goal, offer, seniority, age, interests
    question_text: Mapped[Optional[str]] = mapped_column(Text)
    answer_text: Mapped[Optional[str]] = mapped_column(Text)
    answer_type: Mapped[str] = mapped_column(String(20), default="text")  # text, voice
    turn_number: Mapped[int] = mapped_column(Integer, default=0)

    # Relationships
    session: Mapped["InterviewSession"] = relationship(
        "InterviewSession", back_populates="answers"
    )

    def __repr__(self) -> str:
        return f"<InterviewAnswer key={self.question_key} turn={self.turn_number}>"
