from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    """Asosiy menyu tugmalari (emojilarsiz, rasmiy uslubda)."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="Anketa / Ro'yxatdan o'tish"),
                KeyboardButton(text="Mening profilim"),
            ],
            [
                KeyboardButton(text="Haftalik uchrashuv"),
                KeyboardButton(text="Do'stlarni taklif qilish"),
            ],
            [
                KeyboardButton(text="Teahouse haqida"),
                KeyboardButton(text="Yordam"),
            ],
        ],
        resize_keyboard=True,
        is_persistent=True,
    )


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
