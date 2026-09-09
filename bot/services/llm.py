"""LLM service — OpenAI GPT-4o-mini (Primary) with Google Gemini Fallback.

Ushbu servis orqali foydalanuvchining har bir javobi tahlil qilinadi:
1. Suhbatdoshning darajasi, yutuqlari va tajribasiga insoniy munosabat bildirish.
2. Keyingi savolni juda tabiiy va professional tarzda shakllantirish.
3. Foydalanuvchi bergan barcha javoblar asosida 2 gaplik ixcham professional BIO chiqarish.
"""

import asyncio
import json
import logging
import re
from openai import AsyncOpenAI
import google.generativeai as genai

from bot.config import settings

logger = logging.getLogger(__name__)

# OpenAI Async Client
_openai_client = AsyncOpenAI(api_key=settings.openai_api_key)


SYSTEM_PROMPT = """Sen Teahouse xizmatining professional va mehmondo'st suhbatdoshisan — Toshkentdagi tadbirkorlar va mutaxassislarni qahvaxonada uchrashuvga moslashtiruvchi bosh kuratormisan.

Sening vazifang: foydalanuvchi bilan jonli, madaniyatli va mazmunli suhbat orqali uning professional darajasi, erishgan yutuqlari hamda unga qanday sheriklar kerakligini aniqlash.

MUHIM QOIDALAR:
1. O'zbek tilida gaplash.
2. EMOJILARDAN MUTLAQO FOYDALANMA. Matnda hech qanday smaylik yoki emoji belgisi bo'lmasin.
3. Suhbat rasmiy, ishbilarmon, samimiy va hurmat ohangida bo'lsin.
4. Javoblaring qisqa va lo'nda bo'lsin (1-2 gap munosabat + 1 ta savol).
5. Suhbatdosh aytgan ma'lumotlar (kompaniyasi, loyihasi, erishgan yutuqlari)ni e'tiborga olib, savolni uning darajasiga moslab ber."""


BIO_EXTRACTION_PROMPT = """Quyidagi suhbat va ma'lumotlar asosida foydalanuvchining qisqa, salmoqli va professional BIO xulosasini tuz (aniq 2 gapda).
Ushbu BIO uchrashuvdagi sheriklarga ko'rsatiladi.

Qoidalar:
- O'zbek tilida yoz.
- EMOJI MUTLAQO ISHLATMA.
- Foydalanuvchining kasbi, sohasi, erishgan asosiy natijasi va kimlar bilan uchrashmoqchi ekanini aniq ochib ber.
- Faqat matn qaytar, ortiqcha izohlarsiz."""


async def generate_conversational_reaction(
    user_name: str,
    answered_topic: str,
    user_answer: str,
    next_question: str,
    fallback_text: str,
) -> str:
    """Foydalanuvchining javobini tahlil qilib, jonli insondek munosabat va keyingi savolni shakllantirish."""
    prompt = (
        f"Foydalanuvchi ismi: {user_name}\n"
        f"Mavzu: {answered_topic}\n"
        f"Foydalanuvchi javobi: \"{user_answer}\"\n"
        f"Keyingi so'ralishi kerak bo'lgan ma'lumot: {next_question}\n\n"
        f"Ko'rsatma: Foydalanuvchining javobiga (yutug'i yoki darajasiga) qisqa, salmoqli va samimiy munosabat bildir (1 ta gap). "
        f"So'ng keyingi savolni uning darajasiga moslab, chiroyli va qiziqarli qilib ber. "
        f"Jami 2 ta gapdan oshmasin. Emojilardan mutlaqo foydalanma!"
    )

    try:
        response = await asyncio.wait_for(
            _openai_client.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=200,
            ),
            timeout=8.0
        )
        text = response.choices[0].message.content.strip()
        # Emojilarni tozalash (agar AI tasodifan qo'shsa)
        text = re.sub(r'[\U00010000-\U0010ffff]', '', text).strip()
        if text:
            return text
        return fallback_text
    except Exception as e:
        logger.warning(f"OpenAI reaction xatosi: {e}, fallback ishlatiladi.")
        return fallback_text


async def extract_bio_summary(user_data: dict) -> str:
    """Barcha ma'lumotlar asosida OpenAI orqali chiroyli va professional bio_summary yaratish."""
    context = (
        f"Ism: {user_data.get('full_name')}\n"
        f"Kasb/Lavozim: {user_data.get('role')}\n"
        f"Kompaniya/Loyiha: {user_data.get('company')}\n"
        f"Soha: {user_data.get('industry')}\n"
        f"Tajriba: {user_data.get('seniority')} ({user_data.get('experience_years')} yil)\n"
        f"Yutuqlari / Ko'rsatkichlari: {user_data.get('achievements')}\n"
        f"Sheriklik maqsadi: {user_data.get('target_partner')}\n"
        f"Qidirilayotgan soha: {user_data.get('target_industry')}\n"
        f"Qidirilayotgan daraja: {user_data.get('target_seniority')}\n"
        f"Taklifi (nima bera oladi): {user_data.get('can_offer')}\n"
        f"Muhokama mavzusi: {user_data.get('interests')}\n"
    )

    try:
        response = await asyncio.wait_for(
            _openai_client.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {"role": "system", "content": BIO_EXTRACTION_PROMPT},
                    {"role": "user", "content": context}
                ],
                temperature=0.3,
                max_tokens=250,
            ),
            timeout=10.0
        )
        bio = response.choices[0].message.content.strip()
        bio = re.sub(r'[\U00010000-\U0010ffff]', '', bio).strip()
        if bio:
            return bio
    except Exception as e:
        logger.warning(f"OpenAI bio extraction xatosi: {e}")

    # Fallback
    return (
        f"{user_data.get('company', 'Mustaqil loyiha')}da {user_data.get('role', 'mutaxassis')}. "
        f"{user_data.get('target_partner', 'Tajriba almashish')} maqsadida uchrashuvda qatnashadi."
    )


async def extract_profile(conversation: str) -> dict:
    """Moslik va zaxira uchun profil ekstraksiyasi."""
    prompt = f"Ushbu ma'lumotlardan profil ma'lumotlarini ajratib, JSON ko'rinishida ber:\n\n{conversation}"
    try:
        response = await _openai_client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": "Faqat JSON qaytar. Hech qanday emoji ishlatma."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.2,
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        logger.error(f"Extract profile error: {e}")
        return {}


async def chat_interview(messages: list[dict]) -> str:
    """Send interview conversation to OpenAI and get next response."""
    try:
        openai_msgs = [{"role": "system", "content": SYSTEM_PROMPT}]
        for m in messages:
            role = "user" if m.get("role") == "user" else "assistant"
            openai_msgs.append({"role": role, "content": m.get("content", "")})

        res = await _openai_client.chat.completions.create(
            model=settings.openai_model,
            messages=openai_msgs,
            temperature=0.7,
            max_tokens=200,
        )
        return res.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"chat_interview error: {e}")
        return "Tushundim. Faoliyatingiz haqida yana nimalarni qo'shimcha qila olasiz?"


async def generate_questions(profile_a: dict, profile_b: dict) -> list[str]:
    """Ikki kishi bir-biri bilan tanishganda berishi mumkin bo'lgan aqlli savollar."""
    prompt = (
        f"A kishi: {profile_a}\n"
        f"B kishi: {profile_b}\n"
        f"Ular Toshkentdagi uchrashuvda bitta stolda o'tirishadi. Bir-birlari bilan samarali "
        f"muloqot qilishlari uchun 3 ta professional savol tayyorlab ber. "
        f"Faqat JSON array qaytar: [\"savol 1\", \"savol 2\", \"savol 3\"]"
    )
    try:
        res = await _openai_client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": "Sen uchrashuv moderatorisan. Faqat JSON array qaytar."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.7,
        )
        data = json.loads(res.choices[0].message.content)
        if isinstance(data, dict):
            for v in data.values():
                if isinstance(v, list):
                    return v
        return ["Loyihangizdagi asosiy maqsad nima?", "Qanday hamkorlik qila olamiz?"]
    except Exception as e:
        logger.error(f"generate_questions error: {e}")
        return ["Loyihangizdagi asosiy maqsad nima?", "Qanday hamkorlik qila olamiz?"]


async def transcribe_voice(audio_bytes: bytes) -> str:
    """Transcribe voice message using OpenAI Whisper API."""
    try:
        import io
        file_obj = io.BytesIO(audio_bytes)
        file_obj.name = "voice.ogg"
        res = await _openai_client.audio.transcriptions.create(
            model="whisper-1",
            file=file_obj,
            language="uz"
        )
        return res.text.strip()
    except Exception as e:
        logger.error(f"transcribe_voice error: {e}")
        return ""

