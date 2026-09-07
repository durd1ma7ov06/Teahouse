from sqlalchemy import BigInteger, String, Integer, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from typing import Optional, List

from db.base import Base, TimestampMixin, BigIntPK


class Table(Base, TimestampMixin):
    """A table of 3-4 matched people at a venue."""

    __tablename__ = "tables"

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    slot_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("slots.id"), nullable=False)
    venue_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("venues.id"), nullable=True
    )
    status: Mapped[str] = mapped_column(
        String(20), default="forming"
    )  # forming, confirmed, cancelled, completed
    actual_attendees: Mapped[int] = mapped_column(Integer, default=0)

    # Relationships
    slot: Mapped["Slot"] = relationship("Slot", back_populates="tables")
    venue: Mapped[Optional["Venue"]] = relationship("Venue", back_populates="tables")
    members: Mapped[List["TableMember"]] = relationship(
        "TableMember", back_populates="table", lazy="selectin"
    )
    question_sets: Mapped[List["QuestionSet"]] = relationship(
        "QuestionSet", back_populates="table", lazy="selectin"
    )
    feedbacks: Mapped[List["Feedback"]] = relationship(
        "Feedback", back_populates="table", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<Table id={self.id} slot={self.slot_id} status={self.status}>"


class TableMember(Base, TimestampMixin):
    """A user's seat at a specific table."""

    __tablename__ = "table_members"

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    table_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("tables.id"), nullable=False)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), default="offered"
    )  # offered, paid, confirmed, attended, no_show
    offered_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    paid_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    payment_deadline: Mapped[Optional[datetime]] = mapped_column(nullable=True)

    __table_args__ = (UniqueConstraint("table_id", "user_id", name="uq_table_user"),)

    # Relationships
    table: Mapped["Table"] = relationship("Table", back_populates="members")
    user: Mapped["User"] = relationship("User", back_populates="table_memberships")
    payment: Mapped[Optional["Payment"]] = relationship(
        "Payment", back_populates="table_member", uselist=False, lazy="selectin"
    )
    reveal: Mapped[Optional["Reveal"]] = relationship(
        "Reveal", back_populates="table_member", uselist=False, lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<TableMember table={self.table_id} user={self.user_id} status={self.status}>"
