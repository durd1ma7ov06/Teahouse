"""Notification service — sends offers, reveals, nudges, feedback polls.

All messages are in Uzbek with warm, matchmaker-like personality.
"""

import logging
from typing import Optional

from aiogram import Bot
from aiogram.enums import ChatAction

from db.session import async_session

logger = logging.getLogger(__name__)

# Global bot instance (set in main.py)
_bot: Optional[Bot] = None


def set_bot(bot: Bot):
    """Register the bot instance for notifications."""
    global _bot
    _bot = bot


def get_bot() -> Bot:
    """Get the registered bot instance."""
    if _bot is None:
        raise RuntimeError("Bot not registered. Call set_bot() first.")
    return _bot


async def send_typing(chat_id: int):
    """Send typing indicator so pauses feel like thinking, not lag."""
    bot = get_bot()
    await bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)


async def send_offer_wave(wave: int):
    """Send match offers to eligible users.

    Wave 1: Monday 20:00
    Wave 2: Tuesday 10:00 (remaining seats)
    """
    bot = get_bot()
    logger.info(f"Sending offer wave {wave}")

    async with async_session() as session:
        # TODO: Query eligible users, build offers, send messages
        # For now, log the event
        logger.info(f"Offer wave {wave} — implementation pending")


async def close_offer_wave(wave: int):
    """Close an offer wave: release unpaid seats, reform pool.

    Wave 1 close: Monday 21:00
    Wave 2 close: Tuesday 11:00
    """
    bot = get_bot()
    logger.info(f"Closing offer wave {wave}")

    async with async_session() as session:
        # TODO: Find unpaid table_members, release seats, re-form pool
        logger.info(f"Wave {wave} close — implementation pending")


async def send_reveals():
    """Lock rosters and send 24h reveal to each confirmed member.

    Sends: venue card (sendVenue), partial profiles, personalized question sets.
    Fires: Tuesday 20:00
    """
    bot = get_bot()
    logger.info("Sending 24h reveals")

    async with async_session() as session:
        # TODO: Lock rosters, assign venues, generate questions, send reveals
        logger.info("Reveals — implementation pending")


async def send_nudge(nudge_type: str):
    """Send meeting reminder nudge.

    nudge_type: 'morning' (Wed 09:00) or 'two_hours' (Wed 18:00)
    """
    bot = get_bot()

    nudge_messages = {
        "morning": "☀️ Bugun katta kun! Chorshanba uchrashuvingiz soat 20:00 da. Tayyormisiz? 😊",
        "two_hours": "⏰ 2 soat qoldi! Yo'lda bo'lishni unutmang. Sizni kutishyapti! 🚶",
    }

    message = nudge_messages.get(nudge_type, "")
    if not message:
        return

    async with async_session() as session:
        # TODO: Query confirmed members for this week, send nudge
        logger.info(f"Nudge '{nudge_type}' — implementation pending")


async def send_feedback_polls():
    """Send post-meeting feedback poll on Thursday morning.

    Two polls:
    1. Who would you want to meet again? (multi-select toggle)
    2. Was anyone not there? (no-show detection)
    """
    bot = get_bot()
    logger.info("Sending feedback polls")

    async with async_session() as session:
        # TODO: Query completed tables, send polls to each member
        logger.info("Feedback polls — implementation pending")
