"""Comprehensive two-stage onboarding handler (10-12 deep questions).

Ushbu handler orqali:
1-Bosqich: O'zining professional darajasi, faoliyati va erishgan asosiy natijalari
  1. To'liq ism-familiya
  2. Telefon raqam
  3. Kasbi va asosiy lavozimi
  4. Kompaniya, startap yoki loyihasi
  5. Faoliyat sohasi (tugmalar)
  6. Tajriba darajasi va yillari (tugmalar)
  7. Eng katta yutug'i va ko'rsatkichi (yozma/ovozli, AI chuqur tahlil qiladi)
  8. Yoshi (tugmalar)

2-Bosqich: Qidirilayotgan sheriklar va uchrashuv mezonlari
  9. Uchrashuvdan maqsad (Hamkor, Investor, Mijoz, Jamoa, Mentor, Networking)
  10. Izlanayotgan sheriklarning sohasi (tugmalar)
  11. Izlanayotgan sheriklarning tajriba darajasi (tugmalar)
  12. Boshqalarga nima foyda, tajriba yoki resurs bera oladi (yozma/ovozli, AI tahlil qiladi)
  13. Uchrashuvda aynan qaysi amaliy masala/mavzuni muhokama qilmoqchi

Barcha matnlar rasmiy, hurmat bilan va EMOJILARSIZ. Har bir javobdan so'ng OpenAI (GPT-4o-mini)
munosabat bildirib, keyingi savolni beradi.
"""

import logging
import re
from typing import Optional
import urllib.parse

from aiogram import Router, F, Bot
from aiogram.types import (
    Message,
    CallbackQuery,
    ReplyKeyboardRemove,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from aiogram.fsm.context import FSMContext

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.config import settings
from db.session import async_session
from db.models import User, Profile, InterviewSession
from bot.states.interview import InterviewStates
from bot.keyboards.inline import (
    industry_keyboard,
    seniority_keyboard,
    age_range_keyboard,
    partner_goal_keyboard,
    target_industry_keyboard,
    target_seniority_keyboard,
    confirm_keyboard,
)
from bot.keyboards.reply import phone_request_keyboard, main_menu_keyboard
from bot.services.llm import generate_conversational_reaction, extract_bio_summary
from bot.services.notifications import send_typing

logger = logging.getLogger(__name__)
router = Router(name="interview")


# ─── Yordamchi matn olish funksiyasi ───

async def _extract_answer(message: Message) -> str:
    """Xabardan matnni ajratib olish."""
    if message.text:
        return message.text.strip()
    return ""


# ─── Boshlash ───

@router.callback_query(F.data == "start_interview")
async def start_interview_callback(callback: CallbackQuery, state: FSMContext):
    """Intervyuni inline tugma orqali boshlash."""
    await callback.answer()
    await _begin_stage1(callback.message, state)


@router.message(F.text.in_(["Anketa / Ro'yxatdan o'tish", "☕ Suhbat / Intervyu", "Ro'yxatdan o'tish", "🚀 Ro'yxatdan o'tish"]))
async def start_interview_message(message: Message, state: FSMContext):
    """Intervyuni menyu orqali boshlash."""
    await _begin_stage1(message, state)


async def _begin_stage1(message: Message, state: FSMContext):
    """1-bosqichni boshlash."""
    await state.clear()
    await state.set_state(InterviewStates.stage1_full_name)

    intro_text = (
        "📋 **Teahouse professional uchrashuvlar saralash anketasi**\n\n"
        "✨ Tizimimiz bir-biriga eng mos, o'zaro manfaatli va kuchli mutaxassislarni 3-4 kishilik davralarga birlashtiradi.\n\n"
        "Anketa 2 ta asosiy qismdan iborat:\n"
        "🔹 **1-qism:** Sizning kasbiy tajribangiz, faoliyatingiz va erishgan natijalaringiz;\n"
        "🔹 **2-qism:** Siz qidirayotgan sheriklar, uchrashuv mezonlari va muhokama mavzulari.\n\n"
        "━━━━━━━━━━━━━━━━━━━\n"
        "👤 **1-QISM: SHAXSIY VA KASBIY MA'LUMOTLAR**\n\n"
        "1️⃣-savol: To'liq ism va familiyangizni kiriting:\n"
        "(Masalan: Rustam Olimov)"
    )

    if hasattr(message, "edit_text"):
        try:
            await message.edit_text(intro_text)
            return
        except Exception:
            pass
    await message.answer(intro_text)


# ─── 1-BOSQICH: SHAXSIY VA KASBIY TAJRIBA HAMDA NATIJALAR ───

@router.message(InterviewStates.stage1_full_name, F.text)
async def handle_full_name(message: Message, state: FSMContext):
    """1. Ism-familiya."""
    full_name = message.text.strip()
    if len(full_name) < 3 or " " not in full_name:
        await message.answer("⚠️ Iltimos, ism va familiyangizni to'liq kiriting (masalan: Rustam Olimov):")
        return

    await state.update_data(full_name=full_name)
    await state.set_state(InterviewStates.stage1_phone)

    try:
        async with async_session() as session:
            res_u = await session.execute(select(User).where(User.telegram_id == message.from_user.id))
            u = res_u.scalar_one_or_none()
            if u:
                u.first_name = full_name
                await session.commit()
    except Exception as e:
        logger.error(f"Ism saqlashda baza xatosi: {e}")

    await message.answer(
        f"✅ Rahmat, {full_name}!\n\n"
        "📱 **2️⃣-savol: Telefon raqamingizni tasdiqlang.**\n"
        "Pastdagi tugmani bosing yoki raqamingizni xalqaro formatda yozing (+998901234567):",
        reply_markup=phone_request_keyboard(),
    )


@router.message(InterviewStates.stage1_phone, F.contact | F.text)
async def handle_phone(message: Message, state: FSMContext):
    """2. Telefon raqam."""
    phone = ""
    if message.contact:
        phone = message.contact.phone_number
    elif message.text:
        raw = message.text.strip()
        if raw in ["Bekor qilish", "❌ Bekor qilish"]:
            await state.clear()
            await message.answer("❌ Ro'yxatdan o'tish bekor qilindi.", reply_markup=main_menu_keyboard())
            return
        digits = re.sub(r"[^\d+]", "", raw)
        if len(digits) >= 9:
            phone = digits
        else:
            await message.answer(
                "⚠️ Telefon raqam noto'g'ri kiritildi. Iltimos, raqamni to'liq yozing yoki tugmani bosing:",
                reply_markup=phone_request_keyboard(),
            )
            return

    if not phone.startswith("+"):
        phone = "+" + phone

    await state.update_data(phone=phone)
    await state.set_state(InterviewStates.stage1_role)

    try:
        async with async_session() as session:
            res_u = await session.execute(select(User).where(User.telegram_id == message.from_user.id))
            u = res_u.scalar_one_or_none()
            if u:
                u.phone = phone
                await session.commit()
    except Exception as e:
        logger.error(f"Telefon saqlashda baza xatosi: {e}")

    await message.answer(
        f"📞 Telefon raqamingiz qabul qilindi: {phone}\n\n"
        "💼 **3️⃣-savol: Asosiy kasbingiz va lavozimingiz nima?**\n"
        "(Masalan: Senior Backend muhandisi, Savdo bo'limi boshlig'i, Bosh direktor / Asoschi, Moliya maslahatchisi):",
        reply_markup=ReplyKeyboardRemove(),
    )


@router.message(InterviewStates.stage1_role, F.text)
async def handle_role(message: Message, state: FSMContext):
    """3. Kasb va lavozim."""
    role = message.text.strip()
    if len(role) < 2:
        await message.answer("⚠️ Iltimos, kasbingiz yoki lavozimingizni to'liqroq yozing:")
        return

    await state.update_data(role=role)
    await state.set_state(InterviewStates.stage1_company)

    data = await state.get_data()
    fallback = (
        "Juda yaxshi! 🏢 **4️⃣-savol: Hozirda qaysi kompaniya, tashkilot yoki startap loyihasi ustida ishlayapsiz?**\n"
        "(Agar shaxsiy biznesingiz yoki frilans bo'lsa, loyihangiz nomini yoki sohasini yozing):"
    )
    await send_typing(message.chat.id)
    ai_reply = await generate_conversational_reaction(
        user_name=data.get("full_name", ""),
        answered_topic="Kasbi va lavozimi",
        user_answer=role,
        next_question="4-savol: Qaysi kompaniya, startap yoki loyiha ustida faoliyat yuritishi",
        fallback_text=fallback,
    )
    await message.answer(ai_reply)


@router.message(InterviewStates.stage1_company, F.text)
async def handle_company(message: Message, state: FSMContext):
    """4. Kompaniya yoki loyiha."""
    company = message.text.strip()
    await state.update_data(company=company)
    await state.set_state(InterviewStates.stage1_industry)

    await message.answer(
        f"🏢 Kompaniya / Loyiha: {company}\n\n"
        "🌐 **5️⃣-savol: Asosiy faoliyat sohangizni tanlang:**",
        reply_markup=industry_keyboard(),
    )


@router.callback_query(InterviewStates.stage1_industry, F.data.startswith("ind_"))
async def handle_industry_callback(callback: CallbackQuery, state: FSMContext):
    """5. Sohani tanlash."""
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
        await callback.message.edit_text("✍️ Faoliyat sohangizni yozib yuboring:")
        return

    industry = industry_map.get(callback.data, "Boshqa soha")
    await state.update_data(industry=industry)
    await state.set_state(InterviewStates.stage1_seniority)

    await callback.message.edit_text(
        f"🌐 Soha: {industry}\n\n"
        "⏳ **6️⃣-savol: Ushbu sohada tajriba darajangiz qanday? O'zingizga mosini tanlang:**",
        reply_markup=seniority_keyboard(),
    )


@router.message(InterviewStates.stage1_industry, F.text)
async def handle_industry_text(message: Message, state: FSMContext):
    """5. Sohani qo'lda kiritish."""
    industry = message.text.strip()
    await state.update_data(industry=industry)
    await state.set_state(InterviewStates.stage1_seniority)

    await message.answer(
        f"🌐 Soha: {industry}\n\n"
        "⏳ **6️⃣-savol: Ushbu sohada tajriba darajangiz qanday? O'zingizga mosini tanlang:**",
        reply_markup=seniority_keyboard(),
    )


@router.callback_query(InterviewStates.stage1_seniority, F.data.startswith("seniority_"))
async def handle_seniority_callback(callback: CallbackQuery, state: FSMContext):
    """6. Tajriba darajasini tanlash -> 7. Yutuqlar va natijalar so'raladi."""
    await callback.answer()
    seniority_map = {
        "seniority_junior": ("Boshlang'ich", 1),
        "seniority_mid": ("O'rta mutaxassis", 4),
        "seniority_senior": ("Katta mutaxassis", 8),
        "seniority_founder": ("Rahbar / Biznes asoschisi", 12),
    }
    seniority_title, default_years = seniority_map.get(callback.data, ("O'rta mutaxassis", 4))
    await state.update_data(seniority=seniority_title, experience_years=default_years)
    await state.set_state(InterviewStates.stage1_achievements)

    msg_text = (
        f"⏳ Tajriba darajasi: {seniority_title}\n\n"
        "🏆 **7️⃣-savol (Muhim): Faoliyatingiz davomidagi eng katta yutug'ingiz, muvaffaqiyatli loyihangiz "
        "yoki erishgan asosiy biznes ko'rsatkichlaringiz nimalardan iborat?**\n"
        "(Masalan: Yillik aylanma, jamoa soni, foydalanuvchilar soni, eksport yoki qilingan yirik loyiha haqida batafsilroq yozing):"
    )
    await callback.message.edit_text(msg_text)


@router.message(InterviewStates.stage1_achievements, F.text)
async def handle_achievements(message: Message, state: FSMContext):
    """7. Yutuqlarni qabul qilish va AI orqali tahlil qilib, 8-savolga o'tish."""
    achievements = message.text.strip()
    if len(achievements) < 10:
        await message.answer("⚠️ Iltimos, erishgan natijangiz yoki loyihangiz haqida batafsilroq yozing (kamida 1-2 gap):")
        return

    await state.update_data(achievements=achievements)
    await state.set_state(InterviewStates.stage1_age)

    data = await state.get_data()
    fallback = "Salmoqli natijalar! 🎂 **8️⃣-savol: Yoshingizni tanlang:**"
    await send_typing(message.chat.id)
    ai_reply = await generate_conversational_reaction(
        user_name=data.get("full_name", ""),
        answered_topic="Erishgan yutuqlari va biznes natijalari",
        user_answer=achievements,
        next_question="8-savol: Yoshingizni tanlash",
        fallback_text=fallback,
    )
    await message.answer(ai_reply, reply_markup=age_range_keyboard())


@router.callback_query(InterviewStates.stage1_age, F.data.startswith("age_"))
async def handle_age_callback(callback: CallbackQuery, state: FSMContext):
    """8. Yoshni tanlash -> 1-bosqich tugaydi, 2-bosqich boshlanadi."""
    await callback.answer()
    age_map = {
        "age_18_24": 22,
        "age_25_30": 27,
        "age_31_35": 33,
        "age_36_40": 38,
        "age_41_50": 45,
        "age_50_plus": 55,
    }
    age = age_map.get(callback.data, 28)
    await state.update_data(age=age)

    # 2-Bosqich boshlanishi
    await state.set_state(InterviewStates.stage2_partner_goal)

    text = (
        "🎉 1-qism yakunlandi! Sizning kasbiy tajribangiz va natijalaringiz qabul qilindi.\n\n"
        "━━━━━━━━━━━━━━━━━━━\n"
        "🤝 **2-QISM: QIDIRILAYOTGAN SHERIKLAR VA UCHRASHUV TALABLARI**\n\n"
        "🎯 **9️⃣-savol: Teahouse uchrashuvlarida qatnashishdan asosiy maqsadingiz nima?**\n"
        "Sizga aynan qanday suhbatdoshlar kerakligini tanlang:"
    )
    await callback.message.edit_text(text, reply_markup=partner_goal_keyboard())


# ─── 2-BOSQICH: QIDIRILAYOTGAN SHERIKLAR VA MEZONLAR ───

@router.callback_query(InterviewStates.stage2_partner_goal, F.data.startswith("goal_"))
async def handle_goal_callback(callback: CallbackQuery, state: FSMContext):
    """9. Maqsadni tanlash -> 10-savol: Soha."""
    await callback.answer()
    goal_map = {
        "goal_cofounder": "Biznes hamkor / Hammuassis topish",
        "goal_investor": "Investor / Moliyalashtirish jalb qilish",
        "goal_clients": "Mijozlar va buyurtmachilar topish",
        "goal_team": "Malakali mutaxassis / Jamoa yig'ish",
        "goal_mentor": "Mentor / Maslahatchi topish",
        "goal_networking": "Tajriba almashish va professional aloqalar",
    }
    goal = goal_map.get(callback.data, "Tajriba almashish")
    await state.update_data(target_partner=goal, current_goal=goal)
    await state.set_state(InterviewStates.stage2_target_industry)

    await callback.message.edit_text(
        f"🎯 Maqsad: {goal}\n\n"
        "🔍 **🔟-savol: Bo'lajak uchrashuvda asosan qaysi soha vakillari bilan muloqot qilish siz uchun eng manfaatli?**",
        reply_markup=target_industry_keyboard(),
    )


@router.callback_query(InterviewStates.stage2_target_industry, F.data.startswith("tgt_"))
async def handle_target_industry_callback(callback: CallbackQuery, state: FSMContext):
    """10. Izlanayotgan soha -> 11-savol: Sherikning tajriba darajasi."""
    await callback.answer()
    tgt_map = {
        "tgt_all": "Barcha soha vakillari bilan",
        "tgt_it": "Axborot texnologiyalari (IT)",
        "tgt_business": "Biznes, savdo va investitsiya",
        "tgt_marketing": "Marketing va savdo mutaxassislari",
        "tgt_industry": "Ishlab chiqarish va xizmat ko'rsatish",
    }
    if callback.data == "tgt_other":
        await callback.message.edit_text("✍️ Qaysi soha vakillari bilan uchrashmoqchisiz? Yozib yuboring:")
        return

    target_ind = tgt_map.get(callback.data, "Barcha sohalar")
    await state.update_data(target_industry=target_ind)
    await state.set_state(InterviewStates.stage2_target_seniority)

    await callback.message.edit_text(
        f"🔍 Izlanayotgan soha: {target_ind}\n\n"
        "📊 **1️⃣1️⃣-savol: Siz qidirayotgan suhbatdoshlar qanday darajadagi tajribaga ega bo'lishi muhim?**",
        reply_markup=target_seniority_keyboard(),
    )


@router.message(InterviewStates.stage2_target_industry, F.text)
async def handle_target_industry_text(message: Message, state: FSMContext):
    """10. Izlanayotgan sohani qo'lda kiritish."""
    target_ind = message.text.strip()
    await state.update_data(target_industry=target_ind)
    await state.set_state(InterviewStates.stage2_target_seniority)

    await message.answer(
        f"🔍 Izlanayotgan soha: {target_ind}\n\n"
        "📊 **1️⃣1️⃣-savol: Siz qidirayotgan suhbatdoshlar qanday darajadagi tajribaga ega bo'lishi muhim?**",
        reply_markup=target_seniority_keyboard(),
    )


@router.callback_query(InterviewStates.stage2_target_seniority, F.data.startswith("tsen_"))
async def handle_target_seniority_callback(callback: CallbackQuery, state: FSMContext):
    """11. Sherikning darajasi -> 12-savol: O'zining taklifi va bera oladigan foydasi."""
    await callback.answer()
    sen_map = {
        "tsen_founder": "Biznes egalari / Top-menejerlar",
        "tsen_senior": "Katta mutaxassislar (Senior / 5+ yil)",
        "tsen_mid": "O'rta darajadagi mutaxassislar (Mid)",
        "tsen_any": "Darajaning farqi yo'q (G'oyasi borlar)",
    }
    target_seniority = sen_map.get(callback.data, "Biznes egalari va katta mutaxassislar")
    await state.update_data(target_seniority=target_seniority)
    await state.set_state(InterviewStates.stage2_offer)

    text = (
        f"📊 Talab qilinadigan daraja: {target_seniority}\n\n"
        "🎁 **1️⃣2️⃣-savol (Muhim): O'zingiz bo'lajak suhbatdoshlarga qanday aniq foyda, resurs yoki tajriba taklif qila olasiz?**\n"
        "(Masalan: B2B savdo tajribasi, investitsiya jalb qilish, jamoani boshqarish, texnik arxitektura yoki mijozlar bazasi):"
    )
    await callback.message.edit_text(text)


@router.message(InterviewStates.stage2_offer, F.text)
async def handle_offer(message: Message, state: FSMContext):
    """12. O'zining taklifini qabul qilish va AI munosabatidan so'ng 13-savol (mavzular)."""
    offer = message.text.strip()
    if len(offer) < 10:
        await message.answer("⚠️ Iltimos, taklifingiz va bera oladigan foydangiz haqida batafsilroq yozing (kamida 1-2 gap):")
        return

    await state.update_data(can_offer=offer)
    await state.set_state(InterviewStates.stage2_expectations)

    data = await state.get_data()
    fallback = (
        "Juda qimmatli taklif! Har qanday doimiy hamkorlik o'zaro manfaat ustiga quriladi.\n\n"
        "💡 **1️⃣3️⃣-savol (Yakuniy): 25-sentyabrdan keyingi jonli uchrashuv stolida aynan qaysi amaliy "
        "muammo yoki professional mavzuni boshqalar bilan muhokama qilishni xohlaysiz?**"
    )
    await send_typing(message.chat.id)
    ai_reply = await generate_conversational_reaction(
        user_name=data.get("full_name", ""),
        answered_topic="Boshqalarga bera oladigan aniq taklifi va yordami",
        user_answer=offer,
        next_question="13-savol: Uchrashuvda muhokama qilmoqchi bo'lgan amaliy muammo va mavzular",
        fallback_text=fallback,
    )
    await message.answer(ai_reply)


@router.message(InterviewStates.stage2_expectations, F.text)
async def handle_expectations(message: Message, state: FSMContext):
    """13. Muhokama mavzulari -> AI orqali bio_summary tuziladi va tasdiqlash ko'rsatiladi."""
    expectations = message.text.strip()
    await state.update_data(interests=expectations)
    await send_typing(message.chat.id)

    data = await state.get_data()

    # OpenAI orqali ixcham va professional bio_summary tuzish
    bio_summary = await extract_bio_summary(data)
    await state.update_data(bio_summary=bio_summary)
    await state.set_state(InterviewStates.confirming_profile)

    summary_text = (
        "📋 **ANKETA TO'LIQ TO'LDIRILDI!**\n"
        "Kiritilgan barcha ma'lumotlarni tekshiring:\n\n"
        "👤 **1-QISM: SHAXSIY VA KASBIY MA'LUMOTLAR**\n"
        f"• Ism-familiya: {data.get('full_name')}\n"
        f"• Telefon: {data.get('phone')}\n"
        f"• Kasb va lavozim: {data.get('role')}\n"
        f"• Kompaniya / Loyiha: {data.get('company')}\n"
        f"• Faoliyat sohasi: {data.get('industry')}\n"
        f"• Tajriba: {data.get('seniority')} ({data.get('experience_years')} yil)\n"
        f"• Asosiy yutuqlari: {data.get('achievements')}\n"
        f"• Yoshi: {data.get('age')}\n\n"
        "🤝 **2-QISM: QIDIRILAYOTGAN SHERIKLAR VA MEZONLAR**\n"
        f"• Uchrashuvdan maqsad: {data.get('target_partner')}\n"
        f"• Qidirilayotgan soha: {data.get('target_industry')}\n"
        f"• Qidirilayotgan daraja: {data.get('target_seniority')}\n"
        f"• Boshqalarga taklifi: {data.get('can_offer')}\n"
        f"• Muhokama mavzulari: {expectations}\n\n"
        "🤖 **SUN'IY INTELLEKT XULOSASI (BIO):**\n"
        f"\"{bio_summary}\"\n\n"
        "Ma'lumotlar to'g'rimi? Tasdiqlaysizmi?"
    )

    await message.answer(summary_text, reply_markup=confirm_keyboard())


# ─── TASDIQLASH VA BAZAGA SAQLASH ───

@router.callback_query(InterviewStates.confirming_profile, F.data == "confirm_profile")
async def handle_confirm(callback: CallbackQuery, state: FSMContext):
    """Anketani tasdiqlash va bazaga saqlash."""
    await callback.answer("✅ Ma'lumotlar saqlanmoqda...")
    data = await state.get_data()

    try:
        async with async_session() as session:
            res_user = await session.execute(
                select(User).where(User.telegram_id == callback.from_user.id)
            )
            user = res_user.scalar_one_or_none()

            if not user:
                user = User(
                    telegram_id=callback.from_user.id,
                    username=callback.from_user.username,
                    first_name=data.get("full_name", callback.from_user.first_name),
                    phone=data.get("phone"),
                )
                session.add(user)
                await session.flush()
            else:
                user.first_name = data.get("full_name", user.first_name)
                if data.get("phone"):
                    user.phone = data.get("phone")

            res_prof = await session.execute(
                select(Profile).where(Profile.user_id == user.id)
            )
            profile = res_prof.scalar_one_or_none()

            if not profile:
                profile = Profile(user_id=user.id)
                session.add(profile)

            # Ma'lumotlarni to'liq saqlash
            profile.role = data.get("role")
            profile.company = data.get("company")
            profile.industry = data.get("industry")
            profile.seniority = data.get("seniority")
            profile.experience_years = data.get("experience_years")
            profile.age = data.get("age")
            profile.achievements = data.get("achievements")
            profile.current_goal = data.get("target_partner")
            profile.target_partner = data.get("target_partner")
            profile.target_industry = data.get("target_industry")
            profile.target_seniority = data.get("target_seniority")
            profile.can_offer = data.get("can_offer")
            profile.interests = data.get("interests")
            profile.bio_summary = data.get("bio_summary") or f"{profile.company}da {profile.role}"

            session_record = InterviewSession(
                user_id=user.id,
                status="completed",
                total_turns=13,
            )
            session.add(session_record)
            await session.commit()
    except Exception as e:
        logger.error(f"Tasdiqlashda baza xatosi: {e}")

    await state.clear()

    bot_info = await callback.bot.get_me()
    bot_username = bot_info.username or "teahouse_bot"
    ref_link = f"https://t.me/{bot_username}?start=ref_{callback.from_user.id}"
    share_text = "Toshkentdagi tadbirkorlar va kuchli mutaxassislar bilan networking! Teahouse saralash anketasidan o'ting:"
    share_url = f"https://t.me/share/url?url={urllib.parse.quote(ref_link)}&text={urllib.parse.quote(share_text)}"

    ref_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👥 Do'stlarni taklif qilish (Telegram)", url=share_url)],
        [
            InlineKeyboardButton(text="ℹ️ Teahouse haqida", callback_data="about_teahouse_info"),
            InlineKeyboardButton(text="❓ Yordam / FAQ", callback_data="help_info"),
        ],
        [InlineKeyboardButton(text="👤 Mening anketam", callback_data="view_my_profile")],
    ])

    final_text = (
        "🎉 **Anketangiz muvaffaqiyatli qabul qilindi va tasdiqlandi!**\n\n"
        "☕ **Bizni kuting!** Sun'iy intellekt tizimimiz siz kiritgan ma'lumotlar, sohangiz va erishgan natijalaringizni "
        "chuqur tahlil qilib, aynan sizga mos va manfaatli bo'lgan jamoaviy davra (3 nafar suhbatdosh)ni tanlaydi.\n\n"
        "📅 **25-sentyabr kuni soat 23:59 da** saralash yakunlanadi va biz sizga shaxsiy stolingiz, "
        "sheriklaringiz kimligi hamda Toshkent markazidagi shinam qahvaxonadagi uchrashuv tafsilotlari bilan qaytamiz!\n\n"
        "🚀 **DO'STLARNI TAKLIF QILISH:**\n"
        "O'zingiz kabi intiluvchan tadbirkor va kuchli mutaxassis do'stlaringizni taklif qiling. "
        "Davramiz qanchalik keng bo'lsa, siz uchun hamkorlik imkoniyatlari shunchalik yuqori bo'ladi.\n\n"
        "🔗 **Sizning shaxsiy taklif havolangiz:**\n"
        f"{ref_link}"
    )

    await callback.message.edit_text(final_text, reply_markup=ref_keyboard)
    is_admin = callback.from_user.id in settings.admin_ids_list
    await callback.message.answer(
        "⚡ Boshqaruv menyusi faollashdi:",
        reply_markup=main_menu_keyboard(is_admin=is_admin)
    )


@router.callback_query(InterviewStates.confirming_profile, F.data == "redo_interview")
async def handle_redo(callback: CallbackQuery, state: FSMContext):
    """Qaytadan boshlash."""
    await callback.answer()
    await _begin_stage1(callback.message, state)


@router.callback_query(F.data == "view_my_profile")
async def view_my_profile_callback(callback: CallbackQuery):
    """Foydalanuvchining o'z anketasini ko'rsatish."""
    await callback.answer()
    async with async_session() as session:
        res_u = await session.execute(select(User).where(User.telegram_id == callback.from_user.id))
        user = res_u.scalar_one_or_none()
        if not user:
            await callback.message.answer("⚠️ Ma'lumot topilmadi.")
            return

        res_p = await session.execute(select(Profile).where(Profile.user_id == user.id))
        profile = res_p.scalar_one_or_none()

    if not profile or not profile.bio_summary:
        await callback.message.answer("⚠️ Siz hali anketani to'ldirmagansiz.")
        return

    bot_info = await callback.bot.get_me()
    ref_link = f"https://t.me/{bot_info.username or 'teahouse_bot'}?start=ref_{callback.from_user.id}"
    share_text = "Toshkentdagi tadbirkorlar va mutaxassislar bilan networking! Teahouse saralashidan o'ting:"
    share_url = f"https://t.me/share/url?url={urllib.parse.quote(ref_link)}&text={urllib.parse.quote(share_text)}"

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👥 Do'stlarga ulashish (Telegram)", url=share_url)],
        [InlineKeyboardButton(text="🔄 Qaytadan to'ldirish", callback_data="redo_interview")],
    ])

    text = (
        "📋 **SIZNING ANKETANGIZ VA PROFILINGIZ**\n\n"
        f"👤 Ism: {user.first_name}\n"
        f"📱 Telefon: {user.phone or '—'}\n"
        f"💼 Kasb va lavozim: {profile.role or '—'}\n"
        f"🏢 Kompaniya: {profile.company or '—'}\n"
        f"🌐 Soha: {profile.industry or '—'}\n"
        f"⏳ Tajriba: {profile.seniority or '—'} ({profile.experience_years or 0} yil)\n"
        f"🏆 Eng katta yutug'i: {profile.achievements or '—'}\n"
        f"🎯 Qidirayotgan sherigi: {profile.target_partner or '—'}\n"
        f"📊 Kerakli daraja: {profile.target_seniority or '—'}\n"
        f"🎁 Boshqalarga taklifi: {profile.can_offer or '—'}\n\n"
        f"🤖 **AI Xulosasi (BIO):**\n\"{profile.bio_summary}\"\n\n"
        f"🔗 **Sizning taklif havolangiz:**\n{ref_link}"
    )
    await callback.message.answer(text, reply_markup=kb)


@router.callback_query(F.data == "about_teahouse_info")
async def about_teahouse_info_callback(callback: CallbackQuery):
    """Teahouse haqida ma'lumot."""
    await callback.answer()
    text = (
        "☕ **TEAHOUSE HAQIDA:**\n\n"
        "Teahouse — Toshkentdagi tadbirkorlar, startapchilar va yuqori malakali mutaxassislarni "
        "qahva stoli atrofida birlashtiruvchi saralangan networking klubi.\n\n"
        "Har bir ishtirokchi sun'iy intellekt tomonidan tahlil qilinib, "
        "bitta stol atrofida bir-biriga eng ko'p manfaati tegadigan 4 kishi jamlanadi.\n\n"
        "📅 **25-sentyabr kuni soat 23:59 da** ro'yxatdan o'tish to'xtatiladi va stollar e'lon qilinadi."
    )
    await callback.message.answer(text)


@router.callback_query(F.data == "help_info")
async def help_info_callback(callback: CallbackQuery):
    """Yordam va ko'p beriladigan savollar."""
    await callback.answer()
    text = (
        "❓ **YORDAM VA SAVOL-JAVOBLAR:**\n\n"
        "1️⃣ **Uchrashuv qachon bo'ladi?**\n"
        "25-sentyabr saralashidan so'ng, Chorshanba kuni soat 20:00 da.\n\n"
        "2️⃣ **Uchrashuv qayerda o'tkaziladi?**\n"
        "Toshkent markazidagi eng shinam va nufuzli qahvaxonalaridan birida.\n\n"
        "3️⃣ **Bir stolda necha kishi o'tiradi?**\n"
        "Har bir stolda aniq 4 nafar saralangan qatnashchi bo'ladi.\n\n"
        "Savollaringiz yoki takliflaringiz bo'lsa, @durd1matov administratoriga yozishingiz mumkin."
    )
    await callback.message.answer(text)


