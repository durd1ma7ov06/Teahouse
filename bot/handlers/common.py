"""Common handlers — /help, /status, /report and main menu buttons without emojis."""

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
from bot.handlers.interview import _begin_stage1

logger = logging.getLogger(__name__)
router = Router(name="common")


@router.message(F.text.in_(["Teahouse Mini App", "Mini App"]))
@router.message(Command("app"))
async def open_mini_app(message: Message):
    """Teahouse Mini Appga kirish."""
    from bot.config import settings
    from aiogram.types import WebAppInfo

    if settings.webapp_url and settings.webapp_url.startswith("https://"):
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Teahouse Mini Appni ochish", web_app=WebAppInfo(url=settings.webapp_url))]
        ])
    else:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Teahouse Mini Appni ochish", url=settings.webapp_url or "http://localhost:8000")]
        ])

    await message.answer(
        "Teahouse Telegram Mini App:\n\n"
        "- 4 kishilik interaktiv stol simulyatori\n"
        "- Ikki bosqichli vizual anketa\n"
        "- Shaxsiy VIP Networking Pass\n"
        "- Toshkent qahvaxonalari va Chorshanba taymeri\n\n"
        "Mini Appni ochish uchun pastdagi tugmani bosing:",
        reply_markup=kb,
    )


@router.message(F.text.in_(["Anketa / Ro'yxatdan o'tish", "☕ Suhbat / Intervyu", "Ro'yxatdan o'tish", "Suhbat / Intervyu", "🚀 Ro'yxatdan o'tish"]))
async def menu_interview(message: Message, state: FSMContext):
    """Anketa to'ldirishni asosiy menyudan boshlash."""
    await _begin_stage1(message, state)


@router.message(F.text.in_(["Mening profilim", "👤 Mening profilim", "👤 Mening anketam", "Mening anketam", "Anketam"]))
@router.message(Command("status"))
async def status_command(message: Message):
    """Foydalanuvchining to'liq profili (1 va 2-bosqich ma'lumotlari)."""
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == message.from_user.id)
        )
        user = result.scalar_one_or_none()

        if not user:
            await message.answer(
                "⚠️ Siz hali ro'yxatdan o'tmagansiz. Pastdagi tugma orqali anketani to'ldiring.",
                reply_markup=main_menu_keyboard(),
            )
            return

        result = await session.execute(
            select(Profile).where(Profile.user_id == user.id)
        )
        profile = result.scalar_one_or_none()

        if not profile or not profile.bio_summary:
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🚀 Anketani to'ldirish", callback_data="start_interview")]
            ])
            await message.answer(
                f"👤 Foydalanuvchi: {user.first_name}\n\n"
                "Holat: Anketa hali to'ldirilmagan.\n\n"
                "Uchrashuvlarga saralanish uchun anketadan o'ting:",
                reply_markup=kb,
            )
            return

        bot_info = await message.bot.get_me()
        ref_link = f"https://t.me/{bot_info.username or 'teahouse_bot'}?start=ref_{message.from_user.id}"
        import urllib.parse
        share_text = "Toshkentdagi tadbirkorlar va mutaxassislar bilan networking! Teahouse saralash anketasidan o'ting:"
        share_url = f"https://t.me/share/url?url={urllib.parse.quote(ref_link)}&text={urllib.parse.quote(share_text)}"

        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="👥 Do'stlarga ulashish (Telegram)", url=share_url)],
            [InlineKeyboardButton(text="🔄 Profilni qayta to'ldirish", callback_data="redo_interview")],
        ])

        profile_text = (
            "📋 **SIZNING ANKETANGIZ VA PROFILINGIZ**\n\n"
            f"👤 Ism: {user.first_name} (@{user.username or 'yo\'q'})\n"
            f"📱 Telefon: {user.phone or 'kiritilmagan'}\n\n"
            "👤 **1-QISM: SHAXSIY VA KASBIY MA'LUMOTLAR**\n"
            f"• Kasb va lavozim: {profile.role or '—'}\n"
            f"• Kompaniya / Loyiha: {profile.company or '—'}\n"
            f"• Faoliyat sohasi: {profile.industry or '—'}\n"
            f"• Tajriba: {profile.seniority or '—'} ({profile.experience_years or 0} yil)\n"
            f"• Asosiy yutuqlari: {profile.achievements or '—'}\n"
            f"• Yosh: {profile.age or '—'}\n\n"
            "🤝 **2-QISM: QIDIRILAYOTGAN SHERIKLAR VA MEZONLAR**\n"
            f"• Sheriklik maqsadi: {profile.target_partner or profile.current_goal or '—'}\n"
            f"• Izlanayotgan soha: {profile.target_industry or 'Barcha sohalar'}\n"
            f"• Qidirilayotgan daraja: {profile.target_seniority or '—'}\n"
            f"• Boshqalarga taklifi: {profile.can_offer or '—'}\n"
            f"• Muhokama mavzulari: {profile.interests or '—'}\n\n"
            f"🤖 **AI Xulosasi (BIO):**\n\"{profile.bio_summary}\"\n\n"
            "⏳ **Holat:** Qabul qilingan. Sun'iy intellekt 25-sentyabr kuni soat 23:59 da sizga mos suhbatdoshlar davrasini taqsimlaydi."
        )

        await message.answer(profile_text, reply_markup=kb, parse_mode=None)


@router.message(F.text.in_(["Haftalik uchrashuv", "📅 Haftalik uchrashuv"]))
async def meeting_info(message: Message):
    """Haftalik uchrashuvlar tartibi va vaqti."""
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚀 Ishtirok etish uchun anketa", callback_data="start_interview")],
    ])
    meeting_text = (
        "☕ **Teahouse: Haftalik professional uchrashuvlar**\n\n"
        "📅 **Saralash:** 25-sentyabr soat 23:59 gacha davom etadi.\n"
        "⏰ **Vaqt:** 25-sentyabrdan so'ng, Chorshanba kuni soat 20:00 da.\n"
        "📍 **Manzil:** Toshkent markazidagi eng shinam va nufuzli qahvaxonalar.\n"
        "👥 **Format:** Har bir stolda aniq 4 nafar sun'iy intellekt tanlagan mos mutaxassislar."
    )
    await message.answer(meeting_text, reply_markup=kb)


@router.message(F.text.in_(["Do'stlarni taklif qilish", "Taklif qilish", "👥 Taklif qilish", "👥 Do'stlarni taklif qilish"]))
async def referral_info(message: Message):
    """Shaxsiy taklif havolasi."""
    bot_info = await message.bot.get_me()
    bot_username = bot_info.username or "teahouse_bot"
    ref_link = f"https://t.me/{bot_username}?start=ref_{message.from_user.id}"
    share_text = "Toshkentdagi tadbirkorlar va mutaxassislar bilan networking! Teahouse saralash anketasidan o'ting:"
    import urllib.parse
    share_url = f"https://t.me/share/url?url={urllib.parse.quote(ref_link)}&text={urllib.parse.quote(share_text)}"

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👥 Do'stlarga ulashish (Telegram)", url=share_url)],
    ])

    await message.answer(
        "👥 **DO'STLARNI TAKLIF QILISH**\n\n"
        "O'zingiz kabi intiluvchan tadbirkor va kuchli mutaxassis do'stlaringizni taklif qiling.\n\n"
        "Teahouse saralangan a'zolar tarmog'i qanchalik keng bo'lsa, siz uchun hamkorlik imkoniyatlari shunchalik yuqori bo'ladi.\n\n"
        f"🔗 **Sizning shaxsiy taklif havolangiz:**\n{ref_link}",
        reply_markup=kb,
    )


@router.message(F.text.in_(["Teahouse haqida", "ℹ️ Teahouse haqida", "Loyiha haqida"]))
async def about_command(message: Message):
    """Loyiha konsepsiyasi haqida ma'lumot."""
    await message.answer(
        "☕ **TEAHOUSE HAQIDA:**\n\n"
        "Teahouse — Toshkentdagi tadbirkorlar, startapchilar va yuqori malakali mutaxassislarni "
        "qahva stoli atrofida birlashtiruvchi saralangan networking klubi.\n\n"
        "Sun'iy intellekt har bir ishtirokchining kasbi, sohasi, darajasi va maqsadlarini chuqur tahlil qilib, "
        "bir-biriga eng ko'p manfaati tegadigan 4 kishini bitta stolga jamlaydi.\n\n"
        "📅 **25-sentyabr kuni soat 23:59 da** anketalar qabuli to'xtatiladi va uchrashuv stollari e'lon qilinadi.",
        parse_mode=None,
    )


@router.message(F.text.in_(["Yordam", "❓ Yordam"]))
@router.message(Command("help"))
async def help_command(message: Message):
    """Yordam va ko'p beriladigan savollar."""
    help_text = (
        "❓ **YORDAM VA SAVOL-JAVOBLAR:**\n\n"
        "1️⃣ **Sheriklarim va uchrashuv qachon e'lon qilinadi?**\n"
        "25-sentyabr kuni soat 23:59 da anketalar qabuli yopiladi va sun'iy intellekt stollarni taqsimlaydi.\n\n"
        "2️⃣ **Uchrashuv qayerda o'tkaziladi?**\n"
        "Toshkent markazidagi eng shinam va nufuzli qahvaxonalaridan birida.\n\n"
        "3️⃣ **Bir stolda necha kishi o'tiradi?**\n"
        "Har bir stolda aniq 4 nafar saralangan qatnashchi bo'ladi.\n\n"
        "Savollaringiz yoki takliflaringiz bo'lsa, @durd1matov administratoriga yozishingiz mumkin."
    )
    await message.answer(help_text, reply_markup=report_keyboard())


@router.message(Command("report"))
async def report_command(message: Message):
    """Shikoyat bildirish."""
    await message.answer(
        "📝 **Shikoyat yoki taklif bildirish:**\n\n"
        "Agar biror noqulay vaziyat yuz bergan bo'lsa yoki taklifingiz bo'lsa, "
        "pastdagi tugmani bosing yoki @durd1matov ga yozing.",
        reply_markup=report_keyboard(),
    )


@router.message(F.text.in_(["⚙️ Admin boshqaruvi", "Admin boshqaruvi", "Admin"]))
async def forward_admin(message: Message):
    """Admin menyusiga o'tish."""
    from bot.handlers.admin import admin_dashboard
    await admin_dashboard(message)


@router.message(F.text | F.voice)
async def default_message_handler(message: Message, state: FSMContext):
    """FSM holatidan tashqarida yozilgan xabarlarni qayta ishlash."""
    current_state = await state.get_state()
    if current_state is None:
        async with async_session() as session:
            res_u = await session.execute(select(User).where(User.telegram_id == message.from_user.id))
            user = res_u.scalar_one_or_none()
            has_profile = False
            if user:
                res_p = await session.execute(select(Profile).where(Profile.user_id == user.id))
                prof = res_p.scalar_one_or_none()
                has_profile = bool(prof and prof.bio_summary)

        if has_profile:
            await message.answer(
                "✅ Sizning anketangiz muvaffaqiyatli qabul qilingan!\n\n"
                "☕ Sun'iy intellekt 25-sentyabr kuni soat 23:59 da barcha ishtirokchilarni tahlil qilib, "
                "sizga eng mos 3 nafar suhbatdoshni tanlaydi va uchrashuv stoli tafsilotlari e'lon qilinadi.\n\n"
                "Quyidagi menyudan kerakli bo'limni tanlashingiz mumkin:",
                reply_markup=main_menu_keyboard(),
            )
        else:
            await _begin_stage1(message, state)
