"""LLM service — Google Gemini API with automatic key rotation.

10 ta API key bilan ishlaydi. Bitta key limiti tugasa, avtomatik keyingisiga o'tadi.
"""

import asyncio
import json
import logging
import threading
import google.generativeai as genai

from bot.config import settings

logger = logging.getLogger(__name__)


class KeyRotator:
    """Manages multiple Gemini API keys with automatic rotation.

    When a key hits rate limit or quota, switches to the next one.
    """

    def __init__(self, keys: list[str]):
        self.keys = keys
        self.current_index = 0
        self._lock = threading.Lock()
        logger.info(f"🔑 KeyRotator: {len(keys)} ta API key yuklandi")

    @property
    def current_key(self) -> str:
        return self.keys[self.current_index]

    def rotate(self) -> str:
        """Switch to the next key and return it."""
        with self._lock:
            old_index = self.current_index
            self.current_index = (self.current_index + 1) % len(self.keys)
            logger.warning(
                f"🔄 Key rotatsiya: #{old_index + 1} → #{self.current_index + 1} "
                f"(jami {len(self.keys)} ta)"
            )
            return self.current_key

    def configure_current(self):
        """Configure genai with the current key."""
        genai.configure(api_key=self.current_key)


# Initialize key rotator
_rotator = KeyRotator(settings.gemini_keys_list)
_rotator.configure_current()


SYSTEM_PROMPT = """Sen Teahouse botining suhbatdoshi — Toshkentdagi professionallarni qahvaxonada uchrashtiruvchi xizmatning intervyuchisisan.

Sening vazifang: foydalanuvchi haqida qisqa, samimiy suhbat orqali muhim ma'lumotlarni yig'ish.

MUHIM QOIDALAR:
1. O'zbek tilida gaplash. Foydalanuvchi qanday yozsa, shu uslubda javob ber (qisqa yozsa — qisqa, batafsil yozsa — batafsilroq).
2. Suhbat do'stona, qiziquvchan bo'lsin — anketa emas, suhbat.
3. Agar javob noaniq yoki juda qisqa bo'lsa — qo'shimcha savol ber, lekin haddan oshirma.
4. Butun suhbat 5 daqiqadan oshmasin. Ortiqcha savol berma.
5. Hech qachon ingliz yoki rus tilida javob berma (foydalanuvchi o'zi yozsa ham).

Sen yig'ishish kerak bo'lgan ma'lumotlar:
- Kasbi, lavozimi, kompaniyasi yoki loyihasi
- Soha (IT, moliya, ta'lim, tibbiyot va h.k.)
- Hozirgi maqsadi — aniq nima kerak (mijoz, sherik, maslahat, ish va h.k.)
- Boshqalarga nima taklif qila oladi (tajriba, aloqalar, ko'nikma)
- Tajriba darajasi (junior/mid/senior/founder)
- Yoshi
- Ish tashqarisidagi qiziqishlari

USLUB: Matchmaker — fikri bor, samimiy, biroz hazilkash. Forma emas — suhbat."""

PROFILE_EXTRACTION_PROMPT = """Quyidagi suhbat asosida foydalanuvchi profilini JSON formatda chiqar.
Faqat JSON qaytar, boshqa hech narsa yozma.

Kerakli maydonlar:
{
    "role": "lavozimi",
    "company": "kompaniya/loyiha nomi",
    "industry": "soha",
    "stage": "startup/corporate/freelance/student",
    "current_goal": "hozirgi maqsadi",
    "can_offer": "boshqalarga nima taklif qila oladi",
    "seniority": "junior/mid/senior/founder",
    "experience_years": 0,
    "age": 0,
    "interests": "qiziqishlari",
    "bio_summary": "2-3 gapda qisqa tavsif"
}"""

QUESTION_GENERATION_PROMPT = """Sen Teahouse suhbat savollarini yaratuvchisan.

Ikki kishi haqida ma'lumot beriladi. Ularning profillariga asoslanib, bir-birlari uchun 2-3 ta shaxsiy savol yarat.

Savollar:
- Professional va foydali bo'lsin
- Shaxsiy emas, intrusiv emas
- Bir kishining tajribasi ikkinchisiga qanday yordam berishi mumkinligini ochsin
- O'zbek tilida

Faqat JSON array qaytar: ["savol1", "savol2", "savol3"]"""


async def _call_with_rotation(func, *args, max_retries=None, **kwargs):
    """Call a Gemini function with automatic key rotation on failure.

    If a key hits rate limit or quota, rotates to the next key and retries.
    """
    if max_retries is None:
        max_retries = len(_rotator.keys)

    last_error = None
    for attempt in range(max_retries):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            details = getattr(e, "details", "")
            if callable(details):
                try:
                    details = details()
                except Exception:
                    details = ""
            error_str = f"{e} {repr(e)} {details}".lower()
            last_error = e

            # Check if it's a rate limit or quota error or temporary server issue
            if any(keyword in error_str for keyword in [
                "resource_exhausted", "rate limit", "quota",
                "429", "too many requests", "exhausted", "unavailable",
                "deadline_exceeded", "timed out"
            ]):
                logger.warning(f"⚠️ Key #{_rotator.current_index + 1} limit yoki xatolik: {repr(e)[:120]}")
                _rotator.rotate()
                _rotator.configure_current()
                continue
            else:
                raise

    # All keys exhausted
    logger.error(f"❌ Barcha {len(_rotator.keys)} ta key limit tugadi!")
    raise last_error


def _get_model(system_instruction: str = SYSTEM_PROMPT, **kwargs):
    """Get Gemini model instance with current key."""
    return genai.GenerativeModel(
        model_name=settings.gemini_model,
        system_instruction=system_instruction,
        **kwargs,
    )


async def chat_interview(messages: list[dict]) -> str:
    """Send interview conversation to Gemini and get next response.

    Args:
        messages: conversation history [{"role": "user/assistant", "content": "..."}]

    Returns:
        Bot's next message in the interview
    """
    async def _do_chat():
        model = _get_model()

        # Convert to Gemini format
        gemini_messages = []
        for msg in messages:
            role = "user" if msg["role"] == "user" else "model"
            gemini_messages.append({"role": role, "parts": [msg["content"]]})

        # Generate content with timeout
        response = await asyncio.wait_for(
            model.generate_content_async(gemini_messages),
            timeout=12.0
        )
        if response and response.text:
            return response.text.strip()
        return "Tushundim! Juda qiziqarli. Hozirda qanday maqsad yoki loyihalar ustida ishlayapsiz?"

    try:
        return await _call_with_rotation(_do_chat)
    except Exception as e:
        logger.error(f"AI chat xatosi: {e}")
        return "Ajoyib! Ayting-chi, boshqa mutaxassislardan qanday tajriba yoki yordam olishni xohlardingiz?"


async def extract_profile(conversation: str) -> dict:
    """Extract structured profile data from interview conversation."""

    async def _do_extract():
        model = _get_model(
            system_instruction=PROFILE_EXTRACTION_PROMPT,
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json",
                temperature=0.2,
            ),
        )
        response = await asyncio.wait_for(
            model.generate_content_async(f"Ushbu suhbatdan profil ma'lumotlarini ajratib ol:\n\n{conversation}"),
            timeout=15.0
        )
        text = response.text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1]
            if text.endswith("```"):
                text = text.rsplit("```", 1)[0]
        return json.loads(text)

    try:
        return await _call_with_rotation(_do_extract)
    except Exception as e:
        logger.error(f"Profile extraction fallback: {e}")
        return {
            "role": "Mutaxassis",
            "company": "Toshkent",
            "industry": "Boshqa",
            "seniority": "mid",
            "bio_summary": "Toshkentlik professional mutaxassis, o'z sohasida rivojlanish va yangi tanishuvlarga qiziqadi."
        }


async def generate_questions(profile_a: dict, profile_b: dict) -> list[str]:
    """Generate personalized conversation questions for two people."""

    context = (
        f"Birinchi kishi:\n"
        f"- Kasb: {profile_a.get('role', '?')}, {profile_a.get('company', '?')}\n"
        f"- Soha: {profile_a.get('industry', '?')}\n"
        f"- Maqsad: {profile_a.get('current_goal', '?')}\n"
        f"- Taklif: {profile_a.get('can_offer', '?')}\n\n"
        f"Ikkinchi kishi:\n"
        f"- Kasb: {profile_b.get('role', '?')}, {profile_b.get('company', '?')}\n"
        f"- Soha: {profile_b.get('industry', '?')}\n"
        f"- Maqsad: {profile_b.get('current_goal', '?')}\n"
        f"- Taklif: {profile_b.get('can_offer', '?')}\n"
    )

    async def _do_generate():
        model = _get_model(
            system_instruction=QUESTION_GENERATION_PROMPT,
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json",
                temperature=0.7,
            ),
        )
        response = await model.generate_content_async(context)
        return json.loads(response.text)

    return await _call_with_rotation(_do_generate)


async def transcribe_voice(audio_bytes: bytes) -> str:
    """Transcribe voice message using Gemini's audio understanding.

    Gemini can process audio directly — no need for a separate STT service!

    Args:
        audio_bytes: raw audio bytes (OGG from Telegram)

    Returns:
        Transcribed text
    """
    async def _do_transcribe():
        model = _get_model(
            system_instruction="Berilgan audio faylni matniga o'gir. Faqat matni yoz, boshqa hech narsa qo'shma.",
        )
        response = await model.generate_content_async([
            "Quyidagi ovozli xabarni matnga o'gir:",
            {"mime_type": "audio/ogg", "data": audio_bytes},
        ])
        return response.text.strip()

    return await _call_with_rotation(_do_transcribe)
