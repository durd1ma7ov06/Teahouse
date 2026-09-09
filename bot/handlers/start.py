"""/start handler — entry point, deep link referral, first contact."""

import logging
from typing import Optional

from aiogram import Router, F
from aiogram.filters import CommandStart, CommandObject
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import async_session
from db.models import User, Referral, ReputationScore, Profile
from bot.keyboards.inline import start_keyboard
from bot.keyboards.reply import main_menu_keyboard
from bot.services.notifications import send_typing

logger = logging.getLogger(__name__)
router = Router(name="start")


@router.message(CommandStart(deep_link=True))
async def start_with_referral(message: Message, command: CommandObject, state: FSMContext):
    """Handle /start with a deep link referral code (t.me/bot?start=ref_xxx)."""
    referral_code = command.args
    has_profile = False
    first_name = message.from_user.first_name or "Foydalanuvchi"

    async with async_session() as session:
        user = await _get_or_create_user(session, message, referral_code)
        prof_res = await session.execute(select(Profile).where(Profile.user_id == user.id))
        profile = prof_res.scalar_one_or_none()
        has_profile = bool(profile and profile.bio_summary)
        first_name = user.first_name
        await session.commit()

    await send_typing(message.chat.id)
    await _send_welcome(message, first_name, has_profile)


@router.message(CommandStart())
async def start_fresh(message: Message, state: FSMContext):
    """Handle plain /start — new user or returning user."""
    has_profile = False
    first_name = message.from_user.first_name or "Foydalanuvchi"

    async with async_session() as session:
        user = await _get_or_create_user(session, message)
        prof_res = await session.execute(select(Profile).where(Profile.user_id == user.id))
        profile = prof_res.scalar_one_or_none()
        has_profile = bool(profile and profile.bio_summary)
        first_name = user.first_name
        await session.commit()

    await send_typing(message.chat.id)
    await _send_welcome(message, first_name, has_profile)


@router.callback_query(F.data == "about_teahouse")
async def about_teahouse(callback: CallbackQuery):
    """User tapped 'Teahouse haqida'."""
    await callback.answer()

    await callback.message.edit_text(
        "Teahouse — Toshkentdagi tadbirkorlar va mutaxassislarni qahvaxonada "
        "bitta stol atrofida uchrashtiruvchi xizmat.\n\n"
        "Qanday ishlaydi:\n"
        "1. Ikki bosqichli anketani to'ldirasiz (o'zingiz va sizga kerakli sheriklar haqida)\n"
        "2. Sun'iy intellekt sizga mos 3 nafar suhbatdoshni tanlaydi\n"
        "3. Uchrashuv joyi band qilinadi (99,000 UZS)\n"
        "4. Chorshanba kuni soat 20:00 da shinam qahvaxonada uchrashuv bo'lib o'tadi.\n\n"
        "Maqsad: o'zaro manfaatli va professional networking muhitini yaratish.\n\n"
        "Har hafta, har chorshanba, soat 20:00 da.",
        reply_markup=start_keyboard(),
    )


async def _get_or_create_user(
    session: AsyncSession,
    message: Message,
    referral_code: Optional[str] = None,
) -> User:
    """Find or create a user from a Telegram message."""
    result = await session.execute(
        select(User).where(User.telegram_id == message.from_user.id)
    )
    user = result.scalar_one_or_none()

    if user is None:
        user = User(
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name or "Foydalanuvchi",
        )
        session.add(user)
        await session.flush()

        # Create default reputation
        rep = ReputationScore(user_id=user.id, score=50.0)
        session.add(rep)

        # Handle referral
        if referral_code and referral_code.startswith("ref_"):
            code = referral_code
            ref_result = await session.execute(
                select(Referral).where(Referral.deep_link_code == code)
            )
            referral = ref_result.scalar_one_or_none()
            if referral and referral.referred_id is None:
                referral.referred_id = user.id
                referral.status = "registered"
                user.referred_by = referral.referrer_id

        logger.info(f"New user created: {user}")
    else:
        user.username = message.from_user.username
        user.first_name = message.from_user.first_name or user.first_name
        logger.info(f"Returning user: {user}")

    return user


async def _send_welcome(message: Message, first_name: str, has_profile: bool):
    """Send welcome message based on user state."""
    await message.answer(
        "Xush kelibsiz. Asosiy menyudan foydalanishingiz mumkin:",
        reply_markup=main_menu_keyboard(),
    )

    if has_profile:
        await message.answer(
            f"Assalomu alaykum, {first_name}.\n\n"
            "Sizning profilingiz faol holatda. "
            "Navbatdagi uchrashuv uchun taklif kutishingiz mumkin.",
            reply_markup=start_keyboard(),
        )
    else:
        await message.answer(
            f"Assalomu alaykum, {first_name}.\n\n"
            "Teahouse — Toshkentdagi professional networking xizmati.\n\n"
            "Sizga mos 3 nafar qiziqarli va foydali mutaxassis bilan tanishish uchun "
            "ikki bosqichli qisqa anketani to'ldiring.\n\n"
            "Savollarga matn yoki ovozli xabar ko'rinishida javob berishingiz mumkin.\n\n"
            "Boshlash uchun pastdagi tugmani bosing:",
            reply_markup=start_keyboard(),
        )
