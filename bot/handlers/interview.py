"""Interview handler — adaptive conversational interview flow.

The interview is conversational and adaptive: a vague or thin answer gets
a follow-up rather than being accepted. It must read like a curious friend
who is good at asking questions, not a form.

Hard constraint: the whole interview finishes in about five minutes.
Cap total turns.
"""

import json
import logging
from typing import Optional

from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import async_session
from db.models import User, Profile, InterviewSession, InterviewAnswer
from bot.states.interview import InterviewStates
from bot.keyboards.inline import (
    seniority_keyboard,
    age_range_keyboard,
    confirm_keyboard,
)
from bot.services.llm import chat_interview, extract_profile
from bot.services.stt import transcribe_voice
from bot.services.notifications import send_typing

logger = logging.getLogger(__name__)
router = Router(name="interview")

MAX_TURNS = 12  # Hard cap on total conversation turns


@router.message(InterviewStates.asking_role, F.text | F.voice)
async def handle_role_answer(message: Message, state: FSMContext):
    """Handle the role/work question answer (text or voice)."""
    answer = await _extract_answer(message)
    if not answer:
        return

    data = await state.get_data()
    conversation = data.get("conversation", [])
    turn = data.get("turn", 0)

    conversation.append({"role": "user", "content": answer})

    # Save to DB
    await _save_answer(message.from_user.id, "role", answer, message, turn)

    # Ask LLM for next response
    await send_typing(message.chat.id)
    llm_response = await chat_interview(conversation)
    conversation.append({"role": "assistant", "content": llm_response})

    turn += 1
    await state.update_data(conversation=conversation, turn=turn)

    if turn >= 2:
        # Move to asking about goals
        await state.set_state(InterviewStates.asking_goal)

    await message.answer(llm_response)


@router.message(InterviewStates.asking_goal, F.text | F.voice)
async def handle_goal_answer(message: Message, state: FSMContext):
    """Handle the 'what are you trying to achieve' answer."""
    answer = await _extract_answer(message)
    if not answer:
        return

    data = await state.get_data()
    conversation = data.get("conversation", [])
    turn = data.get("turn", 0)

    conversation.append({"role": "user", "content": answer})
    await _save_answer(message.from_user.id, "goal", answer, message, turn)

    await send_typing(message.chat.id)
    llm_response = await chat_interview(conversation)
    conversation.append({"role": "assistant", "content": llm_response})

    turn += 1
    await state.update_data(conversation=conversation, turn=turn)

    if turn >= 4:
        await state.set_state(InterviewStates.asking_offer)

    await message.answer(llm_response)


@router.message(InterviewStates.asking_offer, F.text | F.voice)
async def handle_offer_answer(message: Message, state: FSMContext):
    """Handle the 'what can you offer others' answer."""
    answer = await _extract_answer(message)
    if not answer:
        return

    data = await state.get_data()
    conversation = data.get("conversation", [])
    turn = data.get("turn", 0)

    conversation.append({"role": "user", "content": answer})
    await _save_answer(message.from_user.id, "offer", answer, message, turn)

    await send_typing(message.chat.id)
    llm_response = await chat_interview(conversation)
    conversation.append({"role": "assistant", "content": llm_response})

    turn += 1
    await state.update_data(conversation=conversation, turn=turn)

    if turn >= 6:
        # Switch to button-based seniority question
        await state.set_state(InterviewStates.asking_seniority)
        await message.answer(
            f"{llm_response}\n\n"
            "Endi tajriba darajangizni tanlang 👇",
            reply_markup=seniority_keyboard(),
        )
        return

    await message.answer(llm_response)


@router.callback_query(InterviewStates.asking_seniority, F.data.startswith("seniority_"))
async def handle_seniority(callback: CallbackQuery, state: FSMContext):
    """Handle seniority button selection."""
    await callback.answer()

    seniority_map = {
        "seniority_junior": ("junior", 1),
        "seniority_mid": ("mid", 4),
        "seniority_senior": ("senior", 8),
        "seniority_founder": ("founder", 12),
    }

    seniority, default_years = seniority_map.get(callback.data, ("mid", 4))

    data = await state.get_data()
    conversation = data.get("conversation", [])
    turn = data.get("turn", 0)

    conversation.append({"role": "user", "content": f"Tajriba: {seniority}, taxminan {default_years} yil"})

    await state.update_data(
        conversation=conversation,
        turn=turn + 1,
        seniority=seniority,
        experience_years=default_years,
    )

    await state.set_state(InterviewStates.asking_age)
    await callback.message.edit_text(
        "👍 Yaxshi! Yoshingizni tanlang:",
        reply_markup=age_range_keyboard(),
    )


@router.callback_query(InterviewStates.asking_age, F.data.startswith("age_"))
async def handle_age(callback: CallbackQuery, state: FSMContext):
    """Handle age range button selection."""
    await callback.answer()

    age_map = {
        "age_18_24": 21,
        "age_25_30": 27,
        "age_31_35": 33,
        "age_36_40": 38,
        "age_41_50": 45,
        "age_50_plus": 55,
    }

    age = age_map.get(callback.data, 30)

    data = await state.get_data()
    conversation = data.get("conversation", [])

    conversation.append({"role": "user", "content": f"Yoshim: {age}"})
    await state.update_data(conversation=conversation, age=age)

    await state.set_state(InterviewStates.asking_interests)
    await callback.message.edit_text(
        "Zo'r! Oxirgi savol — ishdan tashqari nimalar qiziqtiradi?\n\n"
        "Sport, kitob, sayohat, musiqa — har narsa bo'lishi mumkin 😊"
    )


@router.message(InterviewStates.asking_interests, F.text | F.voice)
async def handle_interests(message: Message, state: FSMContext):
    """Handle interests answer — last question before profile generation."""
    answer = await _extract_answer(message)
    if not answer:
        return

    data = await state.get_data()
    conversation = data.get("conversation", [])

    conversation.append({"role": "user", "content": f"Qiziqishlarim: {answer}"})
    await state.update_data(conversation=conversation, interests=answer)

    await send_typing(message.chat.id)

    # Generate profile from conversation
    full_conversation = "\n".join(
        f"{'Foydalanuvchi' if m['role'] == 'user' else 'Bot'}: {m['content']}"
        for m in conversation
    )

    try:
        profile_data = await extract_profile(full_conversation)
    except Exception as e:
        logger.error(f"Profile extraction failed: {e}")
        profile_data = {}

    # Override with button-selected values
    profile_data["seniority"] = data.get("seniority", profile_data.get("seniority", "mid"))
    profile_data["experience_years"] = data.get("experience_years", profile_data.get("experience_years", 0))
    profile_data["age"] = data.get("age", profile_data.get("age", 0))
    profile_data["interests"] = answer

    await state.update_data(profile_data=profile_data)
    await state.set_state(InterviewStates.confirming_profile)

    # Show profile summary for confirmation
    summary = (
        f"📋 *Sizning profilingiz:*\n\n"
        f"💼 *Kasb:* {profile_data.get('role', '—')}\n"
        f"🏢 *Kompaniya:* {profile_data.get('company', '—')}\n"
        f"🏭 *Soha:* {profile_data.get('industry', '—')}\n"
        f"🎯 *Maqsad:* {profile_data.get('current_goal', '—')}\n"
        f"🤝 *Taklif:* {profile_data.get('can_offer', '—')}\n"
        f"📊 *Tajriba:* {profile_data.get('seniority', '—')} ({profile_data.get('experience_years', 0)} yil)\n"
        f"🎂 *Yosh:* {profile_data.get('age', '—')}\n"
        f"🎮 *Qiziqish:* {profile_data.get('interests', '—')}\n\n"
        f"📝 _{profile_data.get('bio_summary', '')}_"
    )

    await message.answer(summary, parse_mode="Markdown", reply_markup=confirm_keyboard())


@router.callback_query(InterviewStates.confirming_profile, F.data == "confirm_profile")
async def confirm_profile(callback: CallbackQuery, state: FSMContext):
    """User confirmed their profile — save to database."""
    await callback.answer("✅ Profil saqlandi!")

    data = await state.get_data()
    profile_data = data.get("profile_data", {})

    async with async_session() as session:
        # Get user
        result = await session.execute(
            select(User).where(User.telegram_id == callback.from_user.id)
        )
        user = result.scalar_one_or_none()
        if not user:
            await callback.message.edit_text("❌ Xatolik yuz berdi. /start buyrug'ini qayta yuboring.")
            return

        # Create or update profile
        result = await session.execute(
            select(Profile).where(Profile.user_id == user.id)
        )
        profile = result.scalar_one_or_none()

        if profile is None:
            profile = Profile(user_id=user.id)
            session.add(profile)

        profile.role = profile_data.get("role")
        profile.company = profile_data.get("company")
        profile.industry = profile_data.get("industry")
        profile.stage = profile_data.get("stage")
        profile.current_goal = profile_data.get("current_goal")
        profile.can_offer = profile_data.get("can_offer")
        profile.seniority = profile_data.get("seniority")
        profile.experience_years = profile_data.get("experience_years")
        profile.age = profile_data.get("age")
        profile.interests = profile_data.get("interests")
        profile.bio_summary = profile_data.get("bio_summary")

        # Complete interview session
        interview = InterviewSession(
            user_id=user.id,
            status="completed",
            total_turns=data.get("turn", 0),
        )
        session.add(interview)

        await session.commit()

    await state.clear()
    await callback.message.edit_text(
        "🎉 Ajoyib! Profilingiz saqlandi.\n\n"
        "Endi siz matching pool'ga qo'shildingiz. Yetarli odamlar yig'ilganda, "
        "sizga uchrashuv taklifi yuboriladi.\n\n"
        "Kutib turing — tez orada xabar beramiz! ☕"
    )


@router.callback_query(InterviewStates.confirming_profile, F.data == "redo_interview")
async def redo_interview(callback: CallbackQuery, state: FSMContext):
    """User wants to redo the interview."""
    await callback.answer()
    await state.clear()
    await state.set_state(InterviewStates.asking_role)

    await callback.message.edit_text(
        "Xo'p, qaytadan boshlaylik! 😊\n\n"
        "Siz nima ish qilasiz? Kasbingiz, kompaniyangiz yoki loyihangiz haqida gapirib bering.\n\n"
        "💡 Yozib yoki 🎤 ovozli xabar yuborishingiz mumkin.",
    )


# ─── Helpers ───


async def _extract_answer(message: Message) -> Optional[str]:
    """Extract text from a message (text or voice)."""
    if message.voice:
        try:
            # Download voice file
            bot: Bot = message.bot
            file = await bot.get_file(message.voice.file_id)
            voice_bytes = await bot.download_file(file.file_path)
            voice_data = voice_bytes.read()

            # Transcribe
            text = await transcribe_voice(voice_data)
            if text:
                # Send transcription back so user sees what was understood
                await message.reply(f"🎤 _{text}_", parse_mode="Markdown")
                return text
            else:
                await message.reply("Kechirasiz, ovozingizni tushunolmadim. Qayta urinib ko'ring yoki yozib yuboring.")
                return None
        except Exception as e:
            logger.error(f"Voice transcription failed: {e}")
            await message.reply("Ovozli xabarni qayta ishlashda xatolik. Yozib yuborishingiz mumkin.")
            return None
    elif message.text:
        return message.text
    return None


async def _save_answer(
    telegram_id: int,
    question_key: str,
    answer: str,
    message: Message,
    turn: int,
):
    """Save an interview answer to the database."""
    try:
        async with async_session() as session:
            result = await session.execute(
                select(User).where(User.telegram_id == telegram_id)
            )
            user = result.scalar_one_or_none()
            if not user:
                return

            # Find or create active session
            from sqlalchemy import and_
            result = await session.execute(
                select(InterviewSession).where(
                    and_(
                        InterviewSession.user_id == user.id,
                        InterviewSession.status == "in_progress",
                    )
                )
            )
            interview = result.scalar_one_or_none()
            if not interview:
                interview = InterviewSession(user_id=user.id)
                session.add(interview)
                await session.flush()

            answer_record = InterviewAnswer(
                session_id=interview.id,
                question_key=question_key,
                answer_text=answer,
                answer_type="voice" if message.voice else "text",
                turn_number=turn,
            )
            session.add(answer_record)
            interview.total_turns = turn + 1
            await session.commit()
    except Exception as e:
        logger.error(f"Failed to save interview answer: {e}")
