"""/start handler — entry point, deep link referral, first contact."""

import logging
from typing import Optional

from aiogram import Router, F
from aiogram.filters import CommandStart, CommandObject
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.config import settings
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
        "bitta stol atrofida uchrashtiruvchi professional networking xizmati.\n\n"
        "Qanday ishlaydi:\n"
        "1. Ikki bosqichli anketani to'ldirasiz (o'zingiz va qidirilayotgan sheriklaringiz haqida)\n"
        "2. Ro'yxatdan o'tish 25-sentyabr soat 23:59 da to'xtatiladi\n"
        "3. Sun'iy intellekt sizga eng mos 3 nafar suhbatdoshni tanlaydi va Mini App akkauntingiz ochiladi\n"
        "4. Belgilangan chorshanba kuni Toshkent markazidagi qulay qahvaxonada jonli uchrashuv bo'ladi.\n\n"
        "Maqsad: Keraksiz reklamalarsiz, faqat o'zaro manfaatli professional aloqalar va hamkorlik muhiti.",
        reply_markup=start_keyboard(),
        parse_mode=None,
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
        try:
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
        except Exception:
            await session.rollback()
            result = await session.execute(
                select(User).where(User.telegram_id == message.from_user.id)
            )
            user = result.scalar_one()
    else:
        user.username = message.from_user.username
        user.first_name = message.from_user.first_name or user.first_name
        logger.info(f"Returning user: {user}")

    return user


async def _send_welcome(message: Message, first_name: str, has_profile: bool):
    """Send clean, elegant welcome message based on user state and deadline."""
    is_admin = message.from_user.id in settings.admin_ids_list

    if has_profile:
        bot_info = await message.bot.get_me()
        ref_link = f"https://t.me/{bot_info.username or 'teahouse_bot'}?start=ref_{message.from_user.id}"
        import urllib.parse
        share_text = "Toshkentdagi tadbirkorlar va mutaxassislar bilan networking! Teahouse saralash anketasidan o'ting:"
        share_url = f"https://t.me/share/url?url={urllib.parse.quote(ref_link)}&text={urllib.parse.quote(share_text)}"

        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Do'stlarga ulashish (Telegram)", url=share_url)],
            [InlineKeyboardButton(text="Mening anketam", callback_data="view_my_profile")],
        ])

        text = (
            f"Assalomu alaykum, {first_name}.\n\n"
            "Sizning anketangiz muvaffaqiyatli qabul qilingan va sun'iy intellekt tahlil tizimida faol holatda.\n\n"
            "Eslatma:\n"
            "- Qabul 25-sentyabr soat 23:59 gacha davom etadi;\n"
            "- 25-sentyabr kuni sun'iy intellekt barcha anketalarni tahlil qilib, sizga mos 3 nafar sherikni tanlaydi;\n"
            "- Shu kuni sizga shaxsiy Telegram Mini App akkauntingiz va uchrashuv stoli e'lon qilinadi.\n\n"
            "DO'STLARNI TAKLIF QILISH:\n"
            "O'zingizga munosib tadbirkor va mutaxassis do'stlaringizni taklif qiling:\n"
            f"{ref_link}"
        )
        await message.answer(
            text,
            reply_markup=kb,
            parse_mode=None,
        )
    elif not settings.is_registration_open():
        text = (
            f"Assalomu alaykum, {first_name}.\n\n"
            "Kechirasiz, Teahouse 1-mavsumi uchun saralash va ro'yxatdan o'tish 25-sentyabr kuni yakunlangan.\n\n"
            "Hozirda sun'iy intellekt ro'yxatdan o'tgan qatnashchilarni o'zaro mos stollarga taqsimlamoqda.\n"
            "Keyingi mavsum ochilganda birinchilardan bo'lib xabar topishingiz uchun botimizda qoling."
        )
        await message.answer(
            text,
            reply_markup=main_menu_keyboard(is_admin=is_admin),
            parse_mode=None,
        )
    else:
        text = (
            f"Assalomu alaykum, {first_name}.\n\n"
            "Teahouse professional networking platformasiga xush kelibsiz.\n\n"
            "Biznesingiz yoki loyihangiz uchun mos hamkorlar, investorlar va tajribali mutaxassislar davrasiga qo'shilish uchun ro'yxatdan o'ting.\n\n"
            "Anketani to'ldirish uchun pastdagi tugmani bosing:"
        )
        await message.answer(
            text,
            reply_markup=start_keyboard(),
            parse_mode=None,
        )
