from sqlalchemy import BigInteger, String, Integer, Boolean, Text, ForeignKey, UniqueConstraint, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from typing import Optional, List

from db.base import Base, TimestampMixin, BigIntPK


class QuestionSet(Base, TimestampMixin):
    """Personalized conversation questions for each pair at a table."""

    __tablename__ = "question_sets"

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    table_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("tables.id"), nullable=False)
    for_user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False)
    about_user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False)
    questions: Mapped[dict] = mapped_column(JSON, nullable=False)

    # Relationships
    table: Mapped["Table"] = relationship("Table", back_populates="question_sets")

    def __repr__(self) -> str:
        return f"<QuestionSet table={self.table_id} for={self.for_user_id} about={self.about_user_id}>"


class Feedback(Base, TimestampMixin):
    """Post-meeting feedback: who would you meet again + no-show reports."""

    __tablename__ = "feedback"

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    table_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("tables.id"), nullable=False)
    from_user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False)
    selected_user_ids: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    no_show_user_ids: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    submitted_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)

    # Relationships
    table: Mapped["Table"] = relationship("Table", back_populates="feedbacks")

    def __repr__(self) -> str:
        return f"<Feedback table={self.table_id} from={self.from_user_id}>"


class Connection(Base, TimestampMixin):
    """Mutual match connection between two users."""

    __tablename__ = "connections"

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    table_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("tables.id"), nullable=False)
    user_a_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False)
    user_b_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False)
    notified: Mapped[bool] = mapped_column(Boolean, default=False)

    __table_args__ = (
        UniqueConstraint("table_id", "user_a_id", "user_b_id", name="uq_connection"),
    )

    def __repr__(self) -> str:
        return f"<Connection table={self.table_id} a={self.user_a_id} b={self.user_b_id}>"
