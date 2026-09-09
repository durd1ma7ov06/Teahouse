from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
from bot.config import settings


def pre_launch_keyboard(is_admin: bool = False) -> ReplyKeyboardMarkup:
    """25-sentyabrgacha bo'lgan toza va oddiy menyu (chalg'ituvchi tugmalarsiz)."""
    buttons = [
        [
            KeyboardButton(text="👤 Mening anketam"),
            KeyboardButton(text="👥 Do'stlarni taklif qilish"),
        ],
        [
            KeyboardButton(text="ℹ️ Teahouse haqida"),
            KeyboardButton(text="❓ Yordam"),
        ],
    ]
    if is_admin:
        buttons.append([KeyboardButton(text="⚙️ Admin boshqaruvi")])

    return ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True,
        is_persistent=True,
    )


def post_launch_keyboard(is_admin: bool = False) -> ReplyKeyboardMarkup:
    """25-sentyabrdan keyingi to'liq menyu (Mini App va stol tafsilotlari bilan)."""
    if settings.webapp_url and settings.webapp_url.startswith("https://"):
        top_row = [KeyboardButton(text="🍵 Teahouse Mini App", web_app=WebAppInfo(url=settings.webapp_url))]
    else:
        top_row = [KeyboardButton(text="🍵 Teahouse Mini App")]

    buttons = [
        top_row,
        [
            KeyboardButton(text="👥 Mening sheriklarim"),
            KeyboardButton(text="👤 Mening profilim"),
        ],
        [
            KeyboardButton(text="📅 Uchrashuv tafsilotlari"),
            KeyboardButton(text="👥 Do'stlarni taklif qilish"),
        ],
        [
            KeyboardButton(text="ℹ️ Teahouse haqida"),
            KeyboardButton(text="❓ Yordam"),
        ],
    ]
    if is_admin:
        buttons.append([KeyboardButton(text="⚙️ Admin boshqaruvi")])

    return ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True,
        is_persistent=True,
    )


def main_menu_keyboard(is_admin: bool = False) -> ReplyKeyboardMarkup:
    """Joriy sana (25-sentyabrgacha yoki keyin) ga qarab to'g'ri menyuni qaytaradi."""
    if settings.is_registration_open():
        return pre_launch_keyboard(is_admin)
    return post_launch_keyboard(is_admin)


def phone_request_keyboard() -> ReplyKeyboardMarkup:
    """Telefon raqamni yuborish tugmasi."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Telefon raqamimni yuborish", request_contact=True)],
            [KeyboardButton(text="Bekor qilish")],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )
