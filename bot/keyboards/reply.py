from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    """Doimiy pastki asosiy menyu tugmalari (Mini-app qulayligida)."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="☕ Suhbat / Intervyu"),
                KeyboardButton(text="👤 Mening profilim"),
            ],
            [
                KeyboardButton(text="📅 Haftalik uchrashuv"),
                KeyboardButton(text="👥 Taklif qilish"),
            ],
            [
                KeyboardButton(text="ℹ️ Teahouse haqida"),
                KeyboardButton(text="❓ Yordam"),
            ],
        ],
        resize_keyboard=True,
        is_persistent=True,
    )
