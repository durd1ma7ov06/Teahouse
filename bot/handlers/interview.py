"""Two-stage onboarding and interview handler.

Stage 1: Ro'yxatdan o'tish va shaxsiy/professional ma'lumotlar (ism, telefon, kasb, kompaniya, soha, tajriba, yosh)
Stage 2: Qidirilayotgan sheriklar va uchrashuv mezonlari (maqsad, qaysi soha vakillari kerak, o'zining taklifi)

Barcha matnlar va tugmalar rasmiy, professional hamda EMOJILARSIZ.
"""

import logging
import re
from typing import Optional

from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import async_session
from db.models import User, Profile, InterviewSession, InterviewAnswer
from bot.states.interview import InterviewStates
from bot.keyboards.inline import (
    industry_keyboard,
    seniority_keyboard,
    age_range_keyboard,
    partner_goal_keyboard,
    target_industry_keyboard,
    confirm_keyboard,
)
from bot.keyboards.reply import phone_request_keyboard, main_menu_keyboard
from bot.services.llm import extract_profile
from bot.services.stt import transcribe_voice
from bot.services.notifications import send_typing

logger = logging.getLogger(__name__)
router = Router(name="interview")


# ─── Boshlash ───

@router.callback_query(F.data == "start_interview")
async def start_interview_callback(callback: CallbackQuery, state: FSMContext):
    """Intervyuni inline tugma orqali boshlash."""
    await callback.answer()
    await _begin_stage1(callback.message, state, callback.from_user.first_name)


@router.message(F.text.in_(["Anketa / Ro'yxatdan o'tish", "☕ Suhbat / Intervyu", "Ro'yxatdan o'tish"]))
async def start_interview_message(message: Message, state: FSMContext):
    """Intervyuni menyu orqali boshlash."""
    await _begin_stage1(message, state, message.from_user.first_name)


async def _begin_stage1(message: Message, state: FSMContext, default_name: str = ""):
    """1-bosqichni boshlash."""
    await state.clear()
    await state.set_state(InterviewStates.stage1_full_name)

    intro_text = (
        "Teahouse professional uchrashuvlar tizimi.\n\n"
        "Ro'yxatdan o'tish 2 bosqichdan iborat:\n"
        "1-bosqich: O'zingiz haqingizda to'liq professional ma'lumotlar\n"
        "2-bosqich: Sizga qanday sheriklar yoki suhbatdoshlar kerakligi\n\n"
        "1-BOSQICH: SHAXSIY VA KASBIY MA'LUMOTLAR\n\n"
        "To'liq ism va familiyangizni kiriting (masalan: Alisher Qodirov):"
    )

    if hasattr(message, "edit_text"):
        try:
            await message.edit_text(intro_text)
            return
        except Exception:
            pass
    await message.answer(intro_text)


# ─── 1-BOSQICH: SHAXSIY VA KASBIY MA'LUMOTLAR ───

@router.message(InterviewStates.stage1_full_name, F.text | F.voice)
async def handle_full_name(message: Message, state: FSMContext):
    """Ism va familiyani qabul qilish."""
    full_name = await _extract_answer(message)
    if not full_name or len(full_name.strip()) < 2:
        await message.answer("Iltimos, ism va familiyangizni to'liq kiriting:")
        return

    full_name = full_name.strip()
    await state.update_data(full_name=full_name)
    await state.set_state(InterviewStates.stage1_phone)

    await message.answer(
        f"Rahmat, {full_name}.\n\n"
        "Endi telefon raqamingizni tasdiqlang.\n"
        "Pastdagi tugmani bosing yoki raqamingizni xalqaro formatda yozing (+998901234567):",
        reply_markup=phone_request_keyboard(),
    )


@router.message(InterviewStates.stage1_phone, F.contact | F.text)
async def handle_phone(message: Message, state: FSMContext):
    """Telefon raqamini qabul qilish (kontakt yoki matn)."""
    phone = ""
    if message.contact:
        phone = message.contact.phone_number
    elif message.text:
        raw = message.text.strip()
        if raw == "Bekor qilish":
            await state.clear()
            await message.answer("Ro'yxatdan o'tish bekor qilindi.", reply_markup=main_menu_keyboard())
            return
        # Raqamni tekshirish
        digits = re.sub(r"[^\d+]", "", raw)
        if len(digits) >= 9:
            phone = digits
        else:
            await message.answer(
                "Telefon raqam noto'g'ri kiritildi. Iltimos, pastdagi tugmani bosing yoki raqamni to'liq yozing:",
                reply_markup=phone_request_keyboard(),
            )
            return

    if not phone.startswith("+"):
        phone = "+" + phone

    await state.update_data(phone=phone)
    await state.set_state(InterviewStates.stage1_role)

    await message.answer(
        f"Telefon raqamingiz qabul qilindi: {phone}\n\n"
        "Asosiy kasbingiz va lavozimingiz nima?\n"
        "(Masalan: Senior Backend dasturchi, Savdo bo'limi rahbari, Biznes asoschisi, Moliya direktori):",
        reply_markup=ReplyKeyboardRemove(),
    )


@router.message(InterviewStates.stage1_role, F.text | F.voice)
async def handle_role(message: Message, state: FSMContext):
    """Kasb va lavozimni qabul qilish."""
    role = await _extract_answer(message)
    if not role or len(role.strip()) < 2:
        await message.answer("Iltimos, kasbingiz yoki lavozimingizni kiriting:")
        return

    await state.update_data(role=role.strip())
    await state.set_state(InterviewStates.stage1_company)

    await message.answer(
        "Qaysi kompaniya, korxona yoki loyihada faoliyat yuritasiz?\n"
        "(Agar shaxsiy biznesingiz yoki startapingiz bo'lsa, uning nomini yozing):"
    )


@router.message(InterviewStates.stage1_company, F.text | F.voice)
async def handle_company(message: Message, state: FSMContext):
    """Kompaniya yoki loyiha nomini qabul qilish."""
    company = await _extract_answer(message)
    if not company:
        await message.answer("Iltimos, kompaniya yoki loyihangiz nomini kiriting:")
        return

    await state.update_data(company=company.strip())
    await state.set_state(InterviewStates.stage1_industry)

    await message.answer(
        "Faoliyat sohangizni tanlang:",
        reply_markup=industry_keyboard(),
    )


@router.callback_query(InterviewStates.stage1_industry, F.data.startswith("ind_"))
async def handle_industry_callback(callback: CallbackQuery, state: FSMContext):
    """Sohani inline tugma orqali tanlash."""
    await callback.answer()

    industry_map = {
        "ind_it": "Axborot texnologiyalari (IT)",
        "ind_finance": "Moliya, bank va investitsiya",
        "ind_retail": "Savdo, riteyl va xizmatlar",
        "ind_marketing": "Marketing, PR va reklama",
        "ind_production": "Ishlab chiqarish va sanoat",
        "ind_construction": "Qurilish va ko'chmas mulk",
        "ind_education": "Ta'lim va konsalting",
        "ind_medicine": "Tibbiyot va farmatsevtika",
    }

    if callback.data == "ind_other":
        await callback.message.edit_text("Faoliyat sohangizni yozib yuboring:")
        return

    industry = industry_map.get(callback.data, "Boshqa soha")
    await state.update_data(industry=industry)
    await state.set_state(InterviewStates.stage1_seniority)

    await callback.message.edit_text(
        f"Soha: {industry}\n\n"
        "Ushbu sohada qancha tajribaga egasiz? Darajangizni tanlang:",
        reply_markup=seniority_keyboard(),
    )


@router.message(InterviewStates.stage1_industry, F.text)
async def handle_industry_text(message: Message, state: FSMContext):
    """Sohani qo'lda yozganda qabul qilish."""
    industry = message.text.strip()
    await state.update_data(industry=industry)
    await state.set_state(InterviewStates.stage1_seniority)

    await message.answer(
        f"Soha: {industry}\n\n"
        "Ushbu sohada qancha tajribaga egasiz? Darajangizni tanlang:",
        reply_markup=seniority_keyboard(),
    )


@router.callback_query(InterviewStates.stage1_seniority, F.data.startswith("seniority_"))
async def handle_seniority_callback(callback: CallbackQuery, state: FSMContext):
    """Tajriba darajasini tanlash."""
    await callback.answer()

    seniority_map = {
        "seniority_junior": ("Boshlang'ich", 1),
        "seniority_mid": ("O'rta mutaxassis", 4),
        "seniority_senior": ("Katta mutaxassis", 8),
        "seniority_founder": ("Rahbar / Biznes asoschisi", 12),
    }

    seniority_title, default_years = seniority_map.get(callback.data, ("O'rta mutaxassis", 4))
    await state.update_data(seniority=seniority_title, experience_years=default_years)
    await state.set_state(InterviewStates.stage1_age)

    await callback.message.edit_text(
        f"Tajriba: {seniority_title}\n\n"
        "Yoshingizni tanlang:",
        reply_markup=age_range_keyboard(),
    )


@router.callback_query(InterviewStates.stage1_age, F.data.startswith("age_"))
async def handle_age_callback(callback: CallbackQuery, state: FSMContext):
    """Yoshni tanlash va 2-bosqichga o'tish."""
    await callback.answer()

    age_map = {
        "age_18_24": 21,
        "age_25_30": 27,
        "age_31_35": 33,
        "age_36_40": 38,
        "age_41_50": 45,
        "age_50_plus": 55,
    }

    age = age_map.get(callback.data, 28)
    await state.update_data(age=age)

    # 1-bosqich yakunlandi, 2-bosqich boshlanadi
    await state.set_state(InterviewStates.stage2_partner_goal)

    await callback.message.edit_text(
        "1-bosqich yakunlandi. Shaxsiy va kasbiy ma'lumotlaringiz qabul qilindi.\n\n"
        "2-BOSQICH: SIZGA QANDAY SHERIKLAR KERAKLIGI\n\n"
        "Teahouse uchrashuvlarida qanday maqsadda sherik yoki suhbatdosh qidiryapsiz?\n"
        "Asosiy maqsadingizni tanlang:",
        reply_markup=partner_goal_keyboard(),
    )


# ─── 2-BOSQICH: QIDIRILAYOTGAN SHERIKLAR VA TALABLAR ───

@router.callback_query(InterviewStates.stage2_partner_goal, F.data.startswith("goal_"))
async def handle_goal_callback(callback: CallbackQuery, state: FSMContext):
    """Sheriklik maqsadini tanlash."""
    await callback.answer()

    goal_map = {
        "goal_cofounder": "Biznes hamkor / Hammuassis",
        "goal_investor": "Investor / Moliyalashtirish",
        "goal_clients": "Mijozlar va buyurtmachilar topish",
        "goal_team": "Malakali mutaxassis / Jamoa yig'ish",
        "goal_mentor": "Mentor / Maslahatchi",
        "goal_networking": "Tajriba almashish va professional networking",
    }

    goal = goal_map.get(callback.data, "Tajriba almashish")
    await state.update_data(target_partner=goal, current_goal=goal)
    await state.set_state(InterviewStates.stage2_target_industry)

    await callback.message.edit_text(
        f"Maqsad: {goal}\n\n"
        "Aynan qaysi soha vakillari yoki mutaxassislari bilan uchrashish siz uchun eng foydali va qiziq?",
        reply_markup=target_industry_keyboard(),
    )


@router.message(InterviewStates.stage2_partner_goal, F.text | F.voice)
async def handle_goal_text(message: Message, state: FSMContext):
    """Sheriklik maqsadini yozma qabul qilish."""
    goal = await _extract_answer(message)
    if not goal:
        await message.answer("Iltimos, maqsadingizni tanlang yoki yozing:")
        return

    await state.update_data(target_partner=goal.strip(), current_goal=goal.strip())
    await state.set_state(InterviewStates.stage2_target_industry)

    await message.answer(
        f"Maqsad: {goal.strip()}\n\n"
        "Aynan qaysi soha vakillari yoki mutaxassislari bilan uchrashish siz uchun eng foydali va qiziq?",
        reply_markup=target_industry_keyboard(),
    )


@router.callback_query(InterviewStates.stage2_target_industry, F.data.startswith("tgt_"))
async def handle_target_industry_callback(callback: CallbackQuery, state: FSMContext):
    """Izlanayotgan sohani tanlash."""
    await callback.answer()

    tgt_map = {
        "tgt_all": "Barcha soha vakillari bilan",
        "tgt_it": "Axborot texnologiyalari (IT)",
        "tgt_business": "Biznes, savdo va investitsiya",
        "tgt_marketing": "Marketing va savdo mutaxassislari",
        "tgt_industry": "Ishlab chiqarish va xizmat ko'rsatish",
    }

    if callback.data == "tgt_other":
        await callback.message.edit_text("Qaysi soha vakillari bilan uchrashmoqchi ekanligingizni yozib yuboring:")
        return

    target_ind = tgt_map.get(callback.data, "Barcha sohalar")
    await state.update_data(target_industry=target_ind)
    await state.set_state(InterviewStates.stage2_offer)

    await callback.message.edit_text(
        f"Izlanayotgan soha: {target_ind}\n\n"
        "O'zingiz bo'lajak suhbatdoshlarga qanday yordam, tajriba yoki xizmat taklif eta olasiz?\n"
        "(Sizning eng kuchli tomoningiz yoki berishingiz mumkin bo'lgan foyda nima?):"
    )


@router.message(InterviewStates.stage2_target_industry, F.text)
async def handle_target_industry_text(message: Message, state: FSMContext):
    """Izlanayotgan sohani yozma qabul qilish."""
    target_ind = message.text.strip()
    await state.update_data(target_industry=target_ind)
    await state.set_state(InterviewStates.stage2_offer)

    await message.answer(
        f"Izlanayotgan soha: {target_ind}\n\n"
        "O'zingiz bo'lajak suhbatdoshlarga qanday yordam, tajriba yoki xizmat taklif eta olasiz?\n"
        "(Sizning eng kuchli tomoningiz yoki berishingiz mumkin bo'lgan foyda nima?):"
    )


@router.message(InterviewStates.stage2_offer, F.text | F.voice)
async def handle_offer(message: Message, state: FSMContext):
    """Foydalanuvchining o'z taklifini qabul qilish."""
    offer = await _extract_answer(message)
    if not offer:
        await message.answer("Iltimos, boshqalarga nima bera olishingizni yozib yuboring:")
        return

    await state.update_data(can_offer=offer.strip())
    await state.set_state(InterviewStates.stage2_expectations)

    await message.answer(
        "Oxirgi savol: Uchrashuvda qanday mavzular yoki masalalarni muhokama qilishni xohlardingiz?\n"
        "(Qisqa tarzda yozing yoki ovozli xabar yuboring):"
    )


@router.message(InterviewStates.stage2_expectations, F.text | F.voice)
async def handle_expectations(message: Message, state: FSMContext):
    """Kutilayotgan mavzularni qabul qilish va yakuniy xulosani ko'rsatish."""
    expectations = await _extract_answer(message)
    if not expectations:
        expectations = "Professional tajriba almashish va yangi tanishuvlar"

    await state.update_data(interests=expectations.strip())
    await send_typing(message.chat.id)

    data = await state.get_data()

    # AI orqali qisqa professional xulosa yaratish
    prompt = (
        f"Foydalanuvchi ma'lumotlari:\n"
        f"Ism: {data.get('full_name')}\n"
        f"Kasb: {data.get('role')}\n"
        f"Kompaniya: {data.get('company')}\n"
        f"Soha: {data.get('industry')}\n"
        f"Tajriba: {data.get('seniority')} ({data.get('experience_years')} yil)\n"
        f"Sheriklik maqsadi: {data.get('target_partner')}\n"
        f"Izlanayotgan soha: {data.get('target_industry')}\n"
        f"Taklifi: {data.get('can_offer')}\n"
        f"Mavzular: {expectations}\n"
    )

    bio_summary = ""
    try:
        extracted = await extract_profile(prompt)
        bio_summary = extracted.get("bio_summary", "")
    except Exception as e:
        logger.error(f"Bio extraction error: {e}")

    if not bio_summary:
        bio_summary = (
            f"{data.get('company')} kompaniyasida {data.get('role')} bo'lib faoliyat yuritadi. "
            f"{data.get('target_partner')} maqsadida uchrashuvlarga qatnashadi."
        )

    await state.update_data(bio_summary=bio_summary)
    await state.set_state(InterviewStates.confirming_profile)

    # Yakuniy rasmiy ko'rik (emojilarsiz)
    summary_text = (
        "ANKETA TO'LDIRILDI\n"
        "Kiritilgan ma'lumotlarni tekshiring:\n\n"
        "1-BOSQICH: SHAXSIY VA KASBIY MA'LUMOTLAR\n"
        f"- To'liq ism: {data.get('full_name')}\n"
        f"- Telefon: {data.get('phone')}\n"
        f"- Kasb va lavozim: {data.get('role')}\n"
        f"- Kompaniya / Loyiha: {data.get('company')}\n"
        f"- Faoliyat sohasi: {data.get('industry')}\n"
        f"- Tajriba: {data.get('seniority')} ({data.get('experience_years')} yil)\n"
        f"- Yosh: {data.get('age')}\n\n"
        "2-BOSQICH: QIDIRILAYOTGAN SHERIKLAR VA MEZONLAR\n"
        f"- Sheriklik maqsadi: {data.get('target_partner')}\n"
        f"- Qidirilayotgan soha: {data.get('target_industry')}\n"
        f"- Sizning taklifingiz: {data.get('can_offer')}\n"
        f"- Muhokama mavzulari: {data.get('interests')}\n\n"
        f"Xulosa:\n{bio_summary}\n\n"
        "Barcha ma'lumotlar to'g'ri bo'lsa, tasdiqlang:"
    )

    await message.answer(summary_text, reply_markup=confirm_keyboard())


# ─── TASDIQLASH VA SAQLASH ───

@router.callback_query(InterviewStates.confirming_profile, F.data == "confirm_profile")
async def confirm_profile(callback: CallbackQuery, state: FSMContext):
    """Anketani tasdiqlash va bazaga saqlash."""
    await callback.answer("Ma'lumotlar saqlandi.")

    data = await state.get_data()

    async with async_session() as session:
        # Foydalanuvchini olish yoki yangilash
        result = await session.execute(
            select(User).where(User.telegram_id == callback.from_user.id)
        )
        user = result.scalar_one_or_none()

        if not user:
            user = User(
                telegram_id=callback.from_user.id,
                first_name=data.get("full_name", callback.from_user.first_name),
                username=callback.from_user.username,
                phone=data.get("phone"),
            )
            session.add(user)
            await session.flush()
        else:
            if data.get("full_name"):
                user.first_name = data.get("full_name")
            if data.get("phone"):
                user.phone = data.get("phone")

        # Profilni olish yoki yaratish
        res_prof = await session.execute(
            select(Profile).where(Profile.user_id == user.id)
        )
        profile = res_prof.scalar_one_or_none()

        if profile is None:
            profile = Profile(user_id=user.id)
            session.add(profile)

        profile.role = data.get("role")
        profile.company = data.get("company")
        profile.industry = data.get("industry")
        profile.current_goal = data.get("current_goal")
        profile.target_partner = data.get("target_partner")
        profile.target_industry = data.get("target_industry")
        profile.can_offer = data.get("can_offer")
        profile.seniority = data.get("seniority")
        profile.experience_years = data.get("experience_years")
        profile.age = data.get("age")
        profile.interests = data.get("interests")
        profile.bio_summary = data.get("bio_summary")

        # Intervyu sessiyasini belgilash
        session_record = InterviewSession(
            user_id=user.id,
            status="completed",
            total_turns=10,
        )
        session.add(session_record)

        await session.commit()

    await state.clear()

    success_text = (
        "Anketa muvaffaqiyatli saqlandi.\n\n"
        "Siz Teahouse professional uchrashuvlar tizimida ro'yxatdan o'tdingiz.\n"
        "Sizning sohangiz va mezonlaringizga mos sheriklar shakllanganda, "
        "navbatdagi chorshanba uchrashuvi uchun taklifnoma yuboriladi.\n\n"
        "Profilingizni ko'rish yoki yangilash uchun quyidagi menyudan foydalanishingiz mumkin."
    )

    try:
        await callback.message.edit_text(success_text)
    except Exception:
        await callback.message.answer(success_text)

    await callback.message.answer("Asosiy menyu:", reply_markup=main_menu_keyboard())


@router.callback_query(InterviewStates.confirming_profile, F.data == "redo_interview")
async def redo_interview(callback: CallbackQuery, state: FSMContext):
    """Anketani qaytadan boshlash."""
    await callback.answer()
    await _begin_stage1(callback.message, state, callback.from_user.first_name)


# ─── Yordamchi funksiyalar ───

async def _extract_answer(message: Message) -> Optional[str]:
    """Xabardan matnni ajratib olish (yozma yoki ovozli)."""
    if message.voice:
        try:
            bot: Bot = message.bot
            file = await bot.get_file(message.voice.file_id)
            voice_bytes = await bot.download_file(file.file_path)
            voice_data = voice_bytes.read()

            text = await transcribe_voice(voice_data)
            if text:
                await message.reply(f"Ovozli xabar matni: {text}")
                return text
            else:
                await message.reply("Ovozli xabar aniqlanmadi. Iltimos, qayta yuboring yoki yozma kiriting.")
                return None
        except Exception as e:
            logger.error(f"Voice transcription error: {e}")
            await message.reply("Ovozli xabarni qayta ishlash imkoni bo'lmadi. Iltimos, yozma kiriting.")
            return None
    elif message.text:
        return message.text
    return None
