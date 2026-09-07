"""Speech-to-text service — uses Gemini's built-in audio understanding.

Gemini can process audio directly, so no separate Whisper service needed.
Voice transcription is handled by llm.transcribe_voice().
"""

from bot.services.llm import transcribe_voice

__all__ = ["transcribe_voice"]
