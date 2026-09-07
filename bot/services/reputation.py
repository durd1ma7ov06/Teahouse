"""Reputation scoring system.

Being selected by tablemates raises a user's internal reputation score.
High-reputation users get priority in matching and get placed with
other high-reputation users. This is the quality flywheel.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import ReputationScore, User


async def get_or_create_reputation(session: AsyncSession, user_id: int) -> ReputationScore:
    """Get or create a reputation score for a user."""
    result = await session.execute(
        select(ReputationScore).where(ReputationScore.user_id == user_id)
    )
    rep = result.scalar_one_or_none()

    if rep is None:
        rep = ReputationScore(user_id=user_id, score=50.0)
        session.add(rep)
        await session.flush()

    return rep


async def update_reputation_after_feedback(
    session: AsyncSession,
    user_id: int,
    was_selected: bool,
    was_no_show: bool,
) -> ReputationScore:
    """Update reputation after a meeting feedback round.

    Args:
        session: DB session
        user_id: User whose reputation to update
        was_selected: Whether someone picked "meet again" for this user
        was_no_show: Whether this user was marked as a no-show
    """
    rep = await get_or_create_reputation(session, user_id)

    rep.total_meetings += 1

    if was_selected:
        rep.times_selected += 1
        # Each selection boosts score
        rep.score = min(100.0, float(rep.score) + 3.0)

    if was_no_show:
        rep.no_show_count += 1
        # No-show heavily penalizes
        rep.score = max(0.0, float(rep.score) - 15.0)

    # Decay towards 50 over time (regression to mean)
    current = float(rep.score)
    rep.score = current + (50.0 - current) * 0.05

    await session.flush()
    return rep
