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


@router.message(F.text.in_(["Anketa / Ro'yxatdan o'tish", "☕ Suhbat / Intervyu", "Ro'yxatdan o'tish", "Suhbat / Intervyu"]))
async def menu_interview(message: Message, state: FSMContext):
    """Anketa to'ldirishni asosiy menyudan boshlash."""
    await _begin_stage1(message, state, message.from_user.first_name)


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
                "Siz hali ro'yxatdan o'tmagansiz. Pastdagi tugma orqali anketani to'ldiring.",
                reply_markup=main_menu_keyboard(),
            )
            return

        result = await session.execute(
            select(Profile).where(Profile.user_id == user.id)
        )
        profile = result.scalar_one_or_none()

        if not profile or not profile.bio_summary:
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Anketani to'ldirish", callback_data="start_interview")]
            ])
            await message.answer(
                f"Foydalanuvchi: {user.first_name}\n\n"
                "Holat: Anketa to'ldirilmagan\n\n"
                "Uchrashuvlarga taklif olish uchun ikki bosqichli anketadan o'ting.",
                reply_markup=kb,
            )
            return

        credit_text = f"\nKredit balansingiz: {user.credit_balance} Stars" if user.credit_balance > 0 else ""

        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Profilni qayta yangilash", callback_data="redo_interview")]
        ])

        profile_text = (
            f"FOYDALANUVCHI PROFILI\n"
            f"Ism: {user.first_name} (@{user.username or 'mavjud emas'})\n"
            f"Telefon: {user.phone or 'kiritilmagan'}\n\n"
            f"1-BOSQICH: SHAXSIY VA KASBIY MA'LUMOTLAR\n"
            f"- Kasb va lavozim: {profile.role or '—'}\n"
            f"- Kompaniya / Loyiha: {profile.company or '—'}\n"
            f"- Faoliyat sohasi: {profile.industry or '—'}\n"
            f"- Tajriba: {profile.seniority or '—'} ({profile.experience_years or 0} yil)\n"
            f"- Yosh: {profile.age or '—'}\n\n"
            f"2-BOSQICH: QIDIRILAYOTGAN SHERIKLAR VA MEZONLAR\n"
            f"- Sheriklik maqsadi: {profile.target_partner or profile.current_goal or '—'}\n"
            f"- Izlanayotgan soha: {profile.target_industry or 'Barcha sohalar'}\n"
            f"- Beradigan taklifi: {profile.can_offer or '—'}\n"
            f"- Muhokama mavzulari: {profile.interests or '—'}\n"
            f"{credit_text}\n"
            f"Xulosa:\n{profile.bio_summary}\n\n"
            f"Holat: Faol (navbatdagi uchrashuv havzasida)"
        )

        await message.answer(profile_text, reply_markup=kb, parse_mode=None)


@router.message(F.text.in_(["Haftalik uchrashuv", "📅 Haftalik uchrashuv"]))
async def meeting_info(message: Message):
    """Haftalik uchrashuvlar tartibi va vaqti."""
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Ishtirok etish uchun anketa", callback_data="start_interview")],
    ])
    meeting_text = (
        "Teahouse: Haftalik professional uchrashuvlar\n\n"
        "Vaqt: Har hafta Chorshanba kuni, soat 20:00 da\n"
        "Manzil: Toshkent shahar markazidagi qulay va shinam qahvaxonalar\n"
        "Format: 1 stol atrofida 4 nafar saralangan mutaxassis (Siz va 3 nafar mos sherik)\n"
        "Xizmat haqi: 99,000 UZS (matching va stolni tashkillashtirish uchun)\n\n"
        "Jadval qanday ishlaydi:\n"
        "- Dushanba 20:00: Mos ishtirokchilarga taklifnoma yuboriladi\n"
        "- Seshanba 20:00: Joy band qilinadi va qahvaxona manzili ko'rsatiladi\n"
        "- Chorshanba 20:00: Qahva ustida jonli suhbat va tanishuv"
    )
    await message.answer(meeting_text, reply_markup=kb)


@router.message(F.text.in_(["Do'stlarni taklif qilish", "Taklif qilish", "👥 Taklif qilish"]))
async def referral_info(message: Message):
    """Shaxsiy taklif havolasi."""
    ref_link = f"https://t.me/teahouse_tashkent_bot?start=ref_{message.from_user.id}"
    share_text = "Toshkentdagi professionallar bilan qahva ustida tanishing! Teahouse botiga qo'shiling:"
    share_url = f"https://t.me/share/url?url={ref_link}&text={share_text}"

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Do'stlarga ulashish", url=share_url)],
    ])

    await message.answer(
        "Do'stlarni taklif qiling.\n\n"
        "Teahouse professional tarmog'i qanchalik kengaysa, uchrashuvlar sifati shunchalik yuqori bo'ladi.\n\n"
        "Sizning shaxsiy taklif havolangiz:\n"
        f"{ref_link}\n\n"
        "Do'stingiz ro'yxatdan o'tib, uchrashuvga qatnashganda sizga bonus kreditlar taqdim etiladi.",
        reply_markup=kb,
    )


@router.message(F.text.in_(["Teahouse haqida", "ℹ️ Teahouse haqida", "Loyiha haqida"]))
async def about_command(message: Message):
    """Loyiha konsepsiyasi haqida ma'lumot."""
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Anketani to'ldirish", callback_data="start_interview")],
    ])
    await message.answer(
        "Teahouse — Toshkentdagi professionallarni qahva stoli atrofida birlashtiruvchi xizmat.\n\n"
        "Algoritm qanday ishlaydi:\n"
        "Sun'iy intellekt har bir ishtirokchining kasbi, maqsadlari va izlayotgan sheriklarini tahlil qilib, "
        "bir-biriga eng ko'p foydasi tegadigan 4 kishini bitta stolga jamlaydi.\n\n"
        "Afzalliklari:\n"
        "- Har bir ishtirokchi moderatsiyadan o'tadi\n"
        "- Keraksiz suhbatlar va reklamalar yo'q\n"
        "- O'zaro manfaatli muloqot va biznes aloqalar.",
        reply_markup=kb,
    )


@router.message(F.text.in_(["Yordam", "❓ Yordam"]))
@router.message(Command("help"))
async def help_command(message: Message):
    """Yordam va ko'p beriladigan savollar."""
    help_text = (
        "Savol-javoblar va yordam:\n\n"
        "Uchrashuv qachon bo'ladi?\n"
        "Har chorshanba kuni soat 20:00 da.\n\n"
        "Qahvaxonani kim tanlaydi?\n"
        "Biz Toshkent markazidagi sifatli qahvaxonalardan birini tanlab, stol band qilamiz.\n\n"
        "To'lov nimani o'z ichiga oladi?\n"
        "99,000 UZS to'lov sizga mos stol a'zolarini saralash va tashkiliy xizmatlar uchun olinadi. "
        "Qahvaxonadagi ichimlik va taomlar uchun har kim o'zi buyurtma beradi.\n\n"
        "Shikoyat bildirish uchun /report buyrug'ini yuborishingiz mumkin."
    )
    await message.answer(help_text, reply_markup=report_keyboard())


@router.message(Command("report"))
async def report_command(message: Message):
    """Shikoyat bildirish."""
    await message.answer(
        "Shikoyat bildirish.\n\n"
        "Agar biror kishi sizni bezovta qilgan yoki noqulay vaziyat yuz bergan bo'lsa, "
        "pastdagi tugmani bosing.\n\n"
        "Har bir murojaat ma'muriyat tomonidan ko'rib chiqiladi.",
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
        await _begin_stage1(message, state, message.from_user.first_name)
