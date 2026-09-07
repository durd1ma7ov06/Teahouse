"""Matching algorithm: complementarity-based, not similarity-based.

The strongest table has enough shared context that conversation flows
and enough difference that each person can actually help another.
Match what A needs against what B offers, across all four seats.
"""

import random
from itertools import combinations
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import User, Profile, Block, TableMember, ReputationScore

# Weights for matching score
WEIGHTS = {
    "need_offer_match": 40,    # A needs what B offers (most important)
    "industry_diversity": 15,  # Different industries = richer table
    "seniority_spread": 15,    # Mix of experience levels
    "reputation": 15,          # Higher reputation = better placement
    "age_spread": 10,          # Reasonable age range
    "no_repeat": 5,            # Penalize repeat pairings
}

SENIORITY_ORDER = {"junior": 0, "mid": 1, "senior": 2, "founder": 3}


def _need_offer_score(profiles: list[dict]) -> float:
    """Score how well the group members' needs match others' offers.

    Higher = more complementary. Checks keywords overlap between
    what each person needs and what others can offer.
    """
    total = 0
    count = 0
    for i, p1 in enumerate(profiles):
        goal_words = set((p1.get("current_goal", "") or "").lower().split())
        for j, p2 in enumerate(profiles):
            if i == j:
                continue
            offer_words = set((p2.get("can_offer", "") or "").lower().split())
            overlap = len(goal_words & offer_words)
            total += min(overlap, 5)  # Cap at 5 keyword matches
            count += 1
    return (total / max(count, 1)) * 10  # Normalize to 0-50 range


def _industry_diversity_score(profiles: list[dict]) -> float:
    """More unique industries = higher score."""
    industries = set(p.get("industry", "").lower() for p in profiles if p.get("industry"))
    if not industries:
        return 0
    return (len(industries) / len(profiles)) * 10


def _seniority_spread_score(profiles: list[dict]) -> float:
    """Penalize tables where everyone is same seniority level."""
    levels = [
        SENIORITY_ORDER.get(p.get("seniority", "mid"), 1)
        for p in profiles
    ]
    unique = len(set(levels))
    spread = max(levels) - min(levels) if levels else 0
    return (unique / len(profiles)) * 5 + min(spread, 3) * 2


def _age_spread_score(profiles: list[dict]) -> float:
    """Reasonable age spread — not all 22 or all 45."""
    ages = [p.get("age", 30) or 30 for p in profiles]
    spread = max(ages) - min(ages)
    if spread < 3:
        return 2  # Too homogeneous
    if spread > 20:
        return 3  # Too spread out
    return 8  # Sweet spot


def _reputation_score(profiles: list[dict]) -> float:
    """Average reputation of the table."""
    scores = [p.get("reputation_score", 50) for p in profiles]
    return (sum(scores) / len(scores)) / 10  # Normalize 0-10


def score_table(profiles: list[dict], past_pairs: set[tuple]) -> float:
    """Calculate total matching score for a proposed table.

    Args:
        profiles: list of profile dicts for the proposed table
        past_pairs: set of (user_id_a, user_id_b) tuples that already met

    Returns:
        Score (higher = better match)
    """
    score = 0.0

    score += _need_offer_score(profiles) * (WEIGHTS["need_offer_match"] / 100)
    score += _industry_diversity_score(profiles) * (WEIGHTS["industry_diversity"] / 100)
    score += _seniority_spread_score(profiles) * (WEIGHTS["seniority_spread"] / 100)
    score += _age_spread_score(profiles) * (WEIGHTS["age_spread"] / 100)
    score += _reputation_score(profiles) * (WEIGHTS["reputation"] / 100)

    # Penalize repeat pairings
    user_ids = [p["user_id"] for p in profiles]
    repeat_count = 0
    for a, b in combinations(user_ids, 2):
        pair = tuple(sorted([a, b]))
        if pair in past_pairs:
            repeat_count += 1
    score -= repeat_count * 5

    return score


async def get_blocked_pairs(session: AsyncSession) -> set[tuple]:
    """Get all block relationships as sorted pairs."""
    result = await session.execute(select(Block.blocker_id, Block.blocked_id))
    pairs = set()
    for row in result.all():
        pairs.add(tuple(sorted([row[0], row[1]])))
    return pairs


async def get_past_pairs(session: AsyncSession) -> set[tuple]:
    """Get all pairs of users who have been at the same table before."""
    # Get all completed table members
    result = await session.execute(
        select(TableMember.table_id, TableMember.user_id).where(
            TableMember.status.in_(["attended", "paid", "confirmed"])
        )
    )
    rows = result.all()

    # Group by table
    tables: dict[int, list[int]] = {}
    for table_id, user_id in rows:
        tables.setdefault(table_id, []).append(user_id)

    # Build pairs
    pairs = set()
    for table_id, users in tables.items():
        for a, b in combinations(users, 2):
            pairs.add(tuple(sorted([a, b])))

    return pairs


def build_tables(
    pool: list[dict],
    past_pairs: set[tuple],
    blocked_pairs: set[tuple],
    table_size: int = 4,
    min_size: int = 3,
) -> list[list[dict]]:
    """Assemble optimal tables from the paid user pool.

    This is re-runnable — tables can be reshuffled until roster lock.

    Args:
        pool: list of user profile dicts (each has 'user_id')
        past_pairs: pairs who already met
        blocked_pairs: pairs who blocked each other
        table_size: target table size (4)
        min_size: minimum table size (3)

    Returns:
        list of tables, each being a list of profile dicts
    """
    if len(pool) < min_size:
        return []

    # Filter out blocked combinations
    valid_pool = list(pool)
    random.shuffle(valid_pool)

    # Try many random combinations and pick the best-scoring arrangement
    best_arrangement = None
    best_score = -float("inf")

    for _ in range(200):  # 200 random attempts
        random.shuffle(valid_pool)
        tables = []
        remaining = list(valid_pool)

        while len(remaining) >= min_size:
            # Take the next table_size people
            size = min(table_size, len(remaining))
            if len(remaining) - size < min_size and len(remaining) - size > 0:
                # Don't leave a remainder smaller than min_size
                size = len(remaining) - min_size
                if size < min_size:
                    size = len(remaining)  # Take all

            table = remaining[:size]
            remaining = remaining[size:]

            # Check for blocked pairs
            user_ids = [p["user_id"] for p in table]
            has_block = False
            for a, b in combinations(user_ids, 2):
                if tuple(sorted([a, b])) in blocked_pairs:
                    has_block = True
                    break

            if has_block:
                continue  # Skip this arrangement

            tables.append(table)

        if not tables:
            continue

        # Score the whole arrangement
        total_score = sum(score_table(t, past_pairs) for t in tables)
        avg_score = total_score / len(tables)

        if avg_score > best_score:
            best_score = avg_score
            best_arrangement = tables

    return best_arrangement or []
