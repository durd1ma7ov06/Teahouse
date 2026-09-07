"""Payment service — Telegram Stars (Phase 1), Payme/Click (Phase 2)."""

import logging
from typing import Optional

from aiogram import Bot
from aiogram.types import LabeledPrice

from bot.config import settings

logger = logging.getLogger(__name__)


async def create_stars_invoice(
    bot: Bot,
    chat_id: int,
    title: str = "Teahouse — Joy band qilish",
    description: str = "Chorshanba 20:00 da qahvaxonada uchrashuv uchun joy",
    stars_amount: int = 1,
    payload: str = "",
) -> None:
    """Send a Telegram Stars payment invoice.

    Args:
        bot: Bot instance
        chat_id: User's chat ID
        title: Invoice title
        description: Invoice description
        stars_amount: Number of Stars to charge
        payload: Custom payload for tracking (e.g., table_member_id)
    """
    prices = [LabeledPrice(label="Teahouse uchrashuv", amount=stars_amount)]

    await bot.send_invoice(
        chat_id=chat_id,
        title=title,
        description=description,
        payload=payload,
        provider_token="",  # Empty for Telegram Stars
        currency="XTR",     # Telegram Stars currency code
        prices=prices,
    )
    logger.info(f"Stars invoice sent to {chat_id}: {stars_amount} stars, payload={payload}")


async def refund_stars(bot: Bot, user_id: int, charge_id: str) -> bool:
    """Refund a Telegram Stars payment (full refund only — API limitation).

    Args:
        bot: Bot instance
        user_id: User's Telegram ID
        charge_id: The charge ID from the successful payment

    Returns:
        True if refund succeeded
    """
    try:
        await bot.refund_star_payment(
            user_id=user_id,
            telegram_payment_charge_id=charge_id,
        )
        logger.info(f"Stars refund issued: user={user_id}, charge={charge_id}")
        return True
    except Exception as e:
        logger.error(f"Stars refund failed: user={user_id}, charge={charge_id}, error={e}")
        return False


def calculate_stars_amount(price_uzs: int, credits_available: int = 0) -> int:
    """Calculate Stars amount from UZS price, applying credits.

    Note: Stars price must be divisible by 4 for quarter-credit math.
    Current rate is approximate — will need real exchange tracking.

    Args:
        price_uzs: Price in UZS (99000)
        credits_available: Star credits available to user

    Returns:
        Stars amount to charge (after credits)
    """
    # Approximate: 1 Star ≈ 12,000-15,000 UZS (varies)
    # Use a fixed Stars price that's divisible by 4
    base_stars = 8  # 8 Stars ≈ 99,000 UZS, divisible by 4

    net_stars = max(0, base_stars - credits_available)

    if net_stars == 0:
        # Credit covers full price — no Stars invoice needed
        return 0

    return net_stars


def calculate_credit_per_empty_seat(stars_price: int) -> int:
    """Calculate credit amount per empty seat.

    With 4-person tables and Stars price divisible by 4:
    credit = stars_price / 4

    Args:
        stars_price: Full Stars price for the meeting

    Returns:
        Credit amount in Stars
    """
    return stars_price // 4
