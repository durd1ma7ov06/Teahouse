"""Admin handler — dashboard, statistics, member list, Excel/CSV export, and broadcast.

Only accessible by authorized Telegram IDs configured in Settings (ADMIN_TELEGRAM_IDS).
"""

import os
import csv
import logging
from datetime import datetime
from zoneinfo import ZoneInfo

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from bot.config import settings
from db.session import async_session
from db.models import User, Profile

logger = logging.getLogger(__name__)
router = Router(name="admin")


class AdminStates(StatesGroup):
    waiting_for_broadcast_text = State()


def is_admin(telegram_id: int) -> bool:
    """Check if the given Telegram ID is an authorized admin."""
    return telegram_id in settings.admin_ids_list


def admin_main_keyboard() -> InlineKeyboardMarkup:
    """Admin boshqaruv tugmalari."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Statistika", callback_data="admin_stat"),
            InlineKeyboardButton(text="Excel yuklab olish", callback_data="admin_export"),
        ],
        [
            InlineKeyboardButton(text="A'zolar ro'yxati", callback_data="admin_users"),
            InlineKeyboardButton(text="Xabar yuborish", callback_data="admin_broadcast"),
        ],
    ])


@router.message(Command("admin"))
async def admin_dashboard(message: Message):
    """Admin boshqaruv markazi."""
    if not is_admin(message.from_user.id):
        return

    async with async_session() as session:
        total_users = await session.scalar(select(func.count(User.id)))
        completed_profiles = await session.scalar(
            select(func.count(Profile.id)).where(Profile.bio_summary.isnot(None))
        )

    deadline_status = "Ochiq (25-sentyabrgacha)" if settings.is_registration_open() else "Yopilgan"

    text = (
        "TEAHOUSE ADMIN BOSHQARUV PANELI\n\n"
        f"Jami kirgan foydalanuvchilar: {total_users or 0} nafar\n"
        f"Anketani to'liq topshirganlar: {completed_profiles or 0} nafar\n"
        f"Qabul holati: {deadline_status}\n"
        f"Deadlayn: {settings.registration_deadline}\n\n"
        "Mavjud buyruqlar:\n"
        "/stat — batafsil statistika\n"
        "/export — barcha ma'lumotlarni Excel (.csv) formatida yuklab olish\n"
        "/users — oxirgi ro'yxatdan o'tganlar ro'yxati\n"
        "/broadcast — barcha a'zolarga xabar tarqatish\n\n"
        "Quyidagi tugmalardan birini tanlang:"
    )
    await message.answer(text, reply_markup=admin_main_keyboard(), parse_mode=None)


@router.message(Command("stat"))
@router.callback_query(F.data == "admin_stat")
async def admin_stat_handler(event: Message | CallbackQuery):
    """Batafsil statistika."""
    user_id = event.from_user.id
    if not is_admin(user_id):
        return

    if isinstance(event, CallbackQuery):
        await event.answer()
        reply_target = event.message
    else:
        reply_target = event

    async with async_session() as session:
        total_users = await session.scalar(select(func.count(User.id)))
        users_with_phone = await session.scalar(select(func.count(User.id)).where(User.phone.isnot(None)))
        completed_profiles = await session.scalar(
            select(func.count(Profile.id)).where(Profile.bio_summary.isnot(None))
        )

        # Sohalar bo'yicha hisoblash
        industry_query = (
            select(Profile.industry, func.count(Profile.id))
            .where(Profile.industry.isnot(None))
            .group_by(Profile.industry)
        )
        industry_rows = (await session.execute(industry_query)).all()

    industry_text = "\n".join([f"- {row[0] or 'Boshqa'}: {row[1]} kishi" for row in industry_rows]) or "Hozircha anketalar to'ldirilmagan."

    stat_text = (
        "TEAHOUSE JORIY STATISTIKASI\n\n"
        f"Jami botga kirganlar: {total_users or 0} nafar\n"
        f"Telefon raqami kiritilganlar: {users_with_phone or 0} nafar\n"
        f"Anketani to'liq topshirganlar: {completed_profiles or 0} nafar\n\n"
        f"Sohalar bo'yicha taqsimot:\n{industry_text}\n\n"
        f"Baza fayli: teahouse.db (Lokal SQLite)\n"
        f"Ro'yxatdan o'tish yopilish vaqti: {settings.registration_deadline}"
    )

    await reply_target.answer(stat_text, reply_markup=admin_main_keyboard(), parse_mode=None)


@router.message(Command("users"))
@router.callback_query(F.data == "admin_users")
async def admin_users_list(event: Message | CallbackQuery):
    """Oxirgi a'zolar ro'yxati."""
    user_id = event.from_user.id
    if not is_admin(user_id):
        return

    if isinstance(event, CallbackQuery):
        await event.answer()
        reply_target = event.message
    else:
        reply_target = event

    async with async_session() as session:
        query = (
            select(User, Profile)
            .outerjoin(Profile, User.id == Profile.user_id)
            .order_by(User.id.desc())
            .limit(15)
        )
        rows = (await session.execute(query)).all()

    if not rows:
        await reply_target.answer("Hozircha ro'yxatdan o'tgan a'zolar mavjud emas.")
        return

    lines = ["OXIRGI RO'YXATDAN O'TGANLAR (Oxirgi 15 kishi):\n"]
    for idx, (u, p) in enumerate(rows, start=1):
        uname = f"@{u.username}" if u.username else "username yo'q"
        phone = u.phone or "tel yo'q"
        role = p.role if p and p.role else "anketa to'ldirilmagan"
        company = f"({p.company})" if p and p.company else ""
        target = f"Sherik: {p.target_partner}" if p and p.target_partner else ""
        lines.append(f"{idx}. {u.first_name} | {uname} | {phone}\n   Faoliyat: {role} {company}\n   {target}\n")

    text = "\n".join(lines)
    await reply_target.answer(text, reply_markup=admin_main_keyboard(), parse_mode=None)


@router.message(Command("export"))
@router.callback_query(F.data == "admin_export")
async def admin_export_csv(event: Message | CallbackQuery):
    """Barcha a'zolar ma'lumotlarini Excel (CSV utf-8-sig) formatida tayyorlab, Telegramga yuborish."""
    user_id = event.from_user.id
    if not is_admin(user_id):
        return

    if isinstance(event, CallbackQuery):
        await event.answer("Fayl shakllantirilmoqda...")
        reply_target = event.message
    else:
        reply_target = event

    async with async_session() as session:
        query = (
            select(User, Profile)
            .outerjoin(Profile, User.id == Profile.user_id)
            .order_by(User.id.asc())
        )
        rows = (await session.execute(query)).all()

    now_str = datetime.now().strftime("%Y_%m_%d_%H%M")
    filename = f"teahouse_members_{now_str}.csv"
    filepath = os.path.join(os.getcwd(), filename)

    fieldnames = [
        "ID",
        "Telegram ID",
        "Ism-Familiya",
        "Telegram Username",
        "Telefon raqam",
        "Yoshi",
        "Kasbi / Lavozimi",
        "Kompaniya / Loyiha",
        "Faoliyat sohasi",
        "Ish tajribasi (yil)",
        "Eng katta yutug'i va natijasi",
        "Qidirayotgan sherigi",
        "Qaysi sohadan sherik izlamoqda",
        "Qidirilayotgan daraja",
        "O'zi nima taklif qila oladi",
        "Muhokama mavzulari",
        "Qisqa xulosa (Bio Summary)",
        "Ro'yxatdan o'tgan sana",
    ]

    # delimiter=';' orqali WPS Office va Excel har bir ustunni chiroyli qilib ajratadi
    with open(filepath, mode="w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow(fieldnames)

        for u, p in rows:
            created_at_str = u.created_at.strftime("%Y-%m-%d %H:%M") if hasattr(u, "created_at") and u.created_at else ""
            writer.writerow([
                u.id,
                u.telegram_id,
                u.first_name,
                f"@{u.username}" if u.username else "",
                u.phone or "",
                p.age if p and p.age else "",
                p.role if p and p.role else "",
                p.company if p and p.company else "",
                p.industry if p and p.industry else "",
                p.experience_years if p and p.experience_years else "",
                p.achievements if p and hasattr(p, "achievements") and p.achievements else "",
                p.target_partner if p and p.target_partner else (p.current_goal if p else ""),
                p.target_industry if p and p.target_industry else "",
                p.target_seniority if p and hasattr(p, "target_seniority") and p.target_seniority else "",
                p.can_offer if p and p.can_offer else "",
                p.interests if p and p.interests else "",
                p.bio_summary if p and p.bio_summary else "",
                created_at_str,
            ])

    try:
        doc = FSInputFile(filepath, filename=filename)
        caption = (
            f"Teahouse a'zolari to'liq ro'yxati (Excel CSV)\n\n"
            f"Jami a'zolar: {len(rows)} nafar\n"
            f"Vaqt: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            "Ushbu faylni to'g'ridan-to'g'ri Microsoft Excel yoki Google Sheets dasturida ochishingiz mumkin."
        )
        await reply_target.answer_document(document=doc, caption=caption, parse_mode=None)
    finally:
        # Faylni jo'natgach o'chirish
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
            except Exception:
                pass


@router.message(Command("broadcast"))
@router.callback_query(F.data == "admin_broadcast")
async def start_broadcast(event: Message | CallbackQuery, state: FSMContext):
    """Barcha a'zolarga xabar yuborishni boshlash."""
    user_id = event.from_user.id
    if not is_admin(user_id):
        return

    if isinstance(event, CallbackQuery):
        await event.answer()
        reply_target = event.message
    else:
        reply_target = event

    await state.set_state(AdminStates.waiting_for_broadcast_text)
    await reply_target.answer(
        "Barcha ro'yxatdan o'tgan foydalanuvchilarga yuboriladigan xabar matnini kiriting:\n\n"
        "(Bekor qilish uchun /cancel deb yozing)"
    )


@router.message(AdminStates.waiting_for_broadcast_text, F.text)
async def process_broadcast_text(message: Message, state: FSMContext):
    """Xabarni barcha foydalanuvchilarga tarqatish."""
    if not is_admin(message.from_user.id):
        return

    if message.text.strip().lower() == "/cancel":
        await state.clear()
        await message.answer("Xabar yuborish bekor qilindi.", reply_markup=admin_main_keyboard())
        return

    broadcast_text = message.text.strip()
    await state.clear()

    async with async_session() as session:
        users = (await session.execute(select(User.telegram_id))).scalars().all()

    success = 0
    failed = 0
    for tg_id in users:
        try:
            await message.bot.send_message(chat_id=tg_id, text=broadcast_text, parse_mode=None)
            success += 1
        except Exception:
            failed += 1

    await message.answer(
        f"Xabarnoma tarqatildi:\n\n"
        f"Muvaffaqiyatli yetkazildi: {success} ta\n"
        f"Yetkazilmadi (bloklangan/o'chirilgan): {failed} ta",
        reply_markup=admin_main_keyboard(),
        parse_mode=None,
    )
