"""Common handlers — /help, /status, /report and persistent menu buttons."""

import logging
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import async_session
from db.models import User, Profile, Referral
from bot.keyboards.inline import report_keyboard, start_keyboard
from bot.keyboards.reply import main_menu_keyboard
from bot.states.interview import InterviewStates
from bot.services.notifications import send_typing

logger = logging.getLogger(__name__)
router = Router(name="common")


@router.message(F.text == "☕ Suhbat / Intervyu")
async def menu_interview(message: Message, state: FSMContext):
    """Start or restart interview from main menu."""
    await state.clear()
    await state.set_state(InterviewStates.asking_role)
    await send_typing(message.chat.id)
    await message.answer(
        "Ajoyib! Keling, tanishib olaylik 😊\n\n"
        "Avval — siz nima ish qilasiz? Kasbingiz, kompaniyangiz yoki loyihangiz haqida gapirib bering.\n\n"
        "💡 Yozib yoki 🎤 ovozli xabar yuborishingiz mumkin.",
    )


@router.message(F.text == "👤 Mening profilim")
@router.message(Command("status"))
async def status_command(message: Message):
    """Show user's current status and profile."""
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == message.from_user.id)
        )
        user = result.scalar_one_or_none()

        if not user:
            await message.answer(
                "Siz hali ro'yxatdan o'tmagansiz. Pastdagi tugma orqali suhbatni boshlang!",
                reply_markup=main_menu_keyboard(),
            )
            return

        result = await session.execute(
            select(Profile).where(Profile.user_id == user.id)
        )
        profile = result.scalar_one_or_none()

        if not profile or not profile.bio_summary:
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="☕ Profilni to'ldirish", callback_data="start_interview")]
            ])
            await message.answer(
                f"👤 *{user.first_name}*\n\n"
                "📋 Profil: ❌ *Tugallanmagan*\n\n"
                "Uchrashuvlarga taklif olish uchun 3 daqiqalik suhbatdan o'ting.",
                parse_mode="Markdown",
                reply_markup=kb,
            )
            return

        credit_text = f"\n⭐ *Kredit balansingiz:* {user.credit_balance} Stars" if user.credit_balance > 0 else ""

        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Profilni qayta yangilash", callback_data="redo_interview")]
        ])

        await message.answer(
            f"👤 *{user.first_name}* (@{user.username or 'mavjud emas'})\n\n"
            f"💼 *Kasb:* {profile.role or '—'}\n"
            f"🏢 *Kompaniya:* {profile.company or '—'}\n"
            f"🏭 *Soha:* {profile.industry or '—'}\n"
            f"📊 *Daraja:* {profile.seniority or '—'} ({profile.experience_years or 0} yil tajriba)\n"
            f"🎯 *Maqsad:* {profile.current_goal or '—'}\n"
            f"🤝 *Ulashishi mumkin:* {profile.can_offer or '—'}\n"
            f"{credit_text}\n\n"
            f"📝 *AI Xulosasi:*\n_{profile.bio_summary}_\n\n"
            f"🟢 *Holat:* Faol (Matching havzasida navbatda)",
            parse_mode="Markdown",
            reply_markup=kb,
        )


@router.message(F.text == "📅 Haftalik uchrashuv")
async def meeting_info(message: Message):
    """Show weekly meeting details and schedule."""
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="☕ Ishtirok etish uchun suhbat", callback_data="start_interview")],
    ])
    await message.answer(
        "📅 *Teahouse — Haftalik Uchrashuvlar*\n\n"
        "🕒 *Vaqt:* Har hafta **Chorshanba, soat 20:00 da**\n"
        "📍 *Manzil:* Toshkent shahar markazidagi eng shinam, sifatli qahvaxonalar\n"
        "👥 *Format:* 1 stol atrofida 4 nafar saralangan mutaxassis (Siz + 3 ta mos sherik)\n"
        "💵 *Xizmat haqi:* 99,000 UZS (matching va stol tashkillashtirish uchun)\n\n"
        "📌 *Jadval qanday ishlaydi:*\n"
        "• *Dushanba 20:00* — Mos ishtirokchilarga taklif yuboriladi\n"
        "• *Seshanba 20:00* — Stol tasdiqlanadi va qahvaxona manzili ochiladi\n"
        "• *Chorshanba 20:00* — Jonli va unutilmas uchrashuv! ☕",
        parse_mode="Markdown",
        reply_markup=kb,
    )


@router.message(F.text == "👥 Taklif qilish")
async def referral_info(message: Message):
    """Show personal referral link and benefits."""
    ref_link = f"https://t.me/teahouse_tashkent_bot?start=ref_{message.from_user.id}"
    share_text = "Toshkentdagi professionallar bilan qahva ustida tanishing! Teahouse botiga qo'shiling:"
    share_url = f"https://t.me/share/url?url={ref_link}&text={share_text}"

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📤 Do'stlarga ulashish", url=share_url)],
    ])

    await message.answer(
        "👥 *Do'stlarni taklif qiling!*\n\n"
        "Teahouse tarmog'i qanchalik kengaysa, uchrashuvlar shunchalik qiziqarli bo'ladi.\n\n"
        "Sizning shaxsiy taklif havolangiz:\n"
        f"`{ref_link}`\n\n"
        "💡 *Bonus:* Do'stingiz ro'yxatdan o'tib, ilk uchrashuvga borganda, sizga bonus kreditlar taqdim etiladi!",
        parse_mode="Markdown",
        reply_markup=kb,
    )


@router.message(F.text == "ℹ️ Teahouse haqida")
async def about_command(message: Message):
    """Show information about Teahouse concept."""
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="☕ Boshlash", callback_data="start_interview")],
    ])
    await message.answer(
        "🍵 *Teahouse nima?*\n\n"
        "Biz professionallarni quruq tarmoqlarda emas, samimiy qahva stoli atrofida birlashtiramiz.\n\n"
        "🎯 *Bizning algoritmimiz:*\n"
        "Sun'iy intellekt har bir ishtirokchining kasbi, maqsadlari va qiziqishlarini tahlil qilib, bir-biriga eng ko'p foyda keltira oladigan 4 kishini bitta stolga jamlaydi.\n\n"
        "🛡 *Xavfsizlik va Madaniyat:*\n"
        "• Har bir a'zo moderatsiyadan o'tadi\n"
        "• Hech qanday keraksiz reklama yoki noqulay suhbatlar bo'lmaydi\n"
        "• Faqat samimiy fikr almashuv va professional o'sish.",
        parse_mode="Markdown",
        reply_markup=kb,
    )


@router.message(F.text == "❓ Yordam")
@router.message(Command("help"))
async def help_command(message: Message):
    """Show help information."""
    await message.answer(
        "❓ *Yordam va Tez-tez beriladigan savollar*\n\n"
        "🔹 *Uchrashuv qachon bo'ladi?*\n"
        "Har chorshanba kuni soat 20:00 da.\n\n"
        "🔹 *Qahvaxonani kim tanlaydi?*\n"
        "Biz Toshkent markazidagi eng yaxshi qahvaxonalardan birini tanlab, joy band qilamiz.\n\n"
        "🔹 *Qanday savollar beriladi?*\n"
        "Suhbat qulay o'tishi uchun sun'iy intellekt stol a'zolariga mos mavzular va savollar tavsiya etadi.\n\n"
        "🚨 Agar muammo bo'lsa yoki shikoyat bildirmoqchi bo'lsangiz /report buyrug'ini yuboring.",
        parse_mode="Markdown",
        reply_markup=report_keyboard(),
    )


@router.message(Command("report"))
async def report_command(message: Message):
    """Start report flow."""
    await message.answer(
        "🚨 *Shikoyat bildirish*\n\n"
        "Agar biror kishi sizni bezovta qilgan yoki noqulay vaziyat yuz bergan bo'lsa, "
        "pastdagi tugmani bosing.\n\n"
        "Har bir shikoyat admin tomonidan ko'rib chiqiladi.",
        parse_mode="Markdown",
        reply_markup=report_keyboard(),
    )


@router.message(F.text | F.voice)
async def default_message_handler(message: Message, state: FSMContext):
    """Foydalanuvchi ixtiyoriy matn yoki ovoz yuborganda AI bilan qabul qilish."""
    current_state = await state.get_state()
    if current_state is None:
        await state.set_state(InterviewStates.asking_role)
        from bot.handlers.interview import handle_role_answer
        await handle_role_answer(message, state)
