from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def start_keyboard() -> InlineKeyboardMarkup:
    """Main start keyboard after /start."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="☕ Boshlash", callback_data="start_interview")],
        [InlineKeyboardButton(text="ℹ️ Teahouse haqida", callback_data="about_teahouse")],
    ])


def confirm_keyboard() -> InlineKeyboardMarkup:
    """Confirm or redo the interview profile."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Tasdiqlash", callback_data="confirm_profile")],
        [InlineKeyboardButton(text="🔄 Qaytadan boshlash", callback_data="redo_interview")],
    ])


def voice_or_text_keyboard() -> InlineKeyboardMarkup:
    """Hint that user can reply with voice or text."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎤 Ovozli xabar", callback_data="hint_voice")],
        [InlineKeyboardButton(text="⌨️ Yozaman", callback_data="hint_text")],
    ])


def seniority_keyboard() -> InlineKeyboardMarkup:
    """Select seniority level."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🌱 Junior (0-2 yil)", callback_data="seniority_junior")],
        [InlineKeyboardButton(text="💼 Mid (3-5 yil)", callback_data="seniority_mid")],
        [InlineKeyboardButton(text="🏆 Senior (6-10 yil)", callback_data="seniority_senior")],
        [InlineKeyboardButton(text="🚀 Founder / Lead (10+ yil)", callback_data="seniority_founder")],
    ])


def age_range_keyboard() -> InlineKeyboardMarkup:
    """Select age range."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="18-24", callback_data="age_18_24"),
            InlineKeyboardButton(text="25-30", callback_data="age_25_30"),
        ],
        [
            InlineKeyboardButton(text="31-35", callback_data="age_31_35"),
            InlineKeyboardButton(text="36-40", callback_data="age_36_40"),
        ],
        [
            InlineKeyboardButton(text="41-50", callback_data="age_41_50"),
            InlineKeyboardButton(text="50+", callback_data="age_50_plus"),
        ],
    ])


def offer_keyboard() -> InlineKeyboardMarkup:
    """Accept or skip a match offer."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Joy band qilish (99,000 UZS)", callback_data="accept_offer")],
        [InlineKeyboardButton(text="⏭ Bu hafta o'tkazaman", callback_data="skip_offer")],
    ])


def payment_keyboard(stars_amount: int) -> InlineKeyboardMarkup:
    """Payment button with Telegram Stars."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"⭐ {stars_amount} Stars bilan to'lash", pay=True)],
    ])


def meet_again_keyboard(members: list[dict], selected_ids: set[int]) -> InlineKeyboardMarkup:
    """Toggle-style keyboard for selecting who to meet again.

    Args:
        members: list of dicts with 'user_id' and 'first_name'
        selected_ids: currently selected user IDs
    """
    buttons = []
    for member in members:
        uid = member["user_id"]
        name = member["first_name"]
        check = "✅ " if uid in selected_ids else ""
        buttons.append([
            InlineKeyboardButton(
                text=f"{check}{name}",
                callback_data=f"toggle_meet_{uid}",
            )
        ])
    buttons.append([
        InlineKeyboardButton(text="📨 Yuborish", callback_data="submit_feedback"),
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def no_show_keyboard(members: list[dict], selected_ids: set[int]) -> InlineKeyboardMarkup:
    """Toggle-style keyboard for reporting no-shows.

    Args:
        members: list of dicts with 'user_id' and 'first_name'
        selected_ids: currently selected as absent
    """
    buttons = []
    for member in members:
        uid = member["user_id"]
        name = member["first_name"]
        check = "❌ " if uid in selected_ids else ""
        buttons.append([
            InlineKeyboardButton(
                text=f"{check}{name}",
                callback_data=f"toggle_noshow_{uid}",
            )
        ])
    buttons.append([
        InlineKeyboardButton(text="👥 Hammasi keldi", callback_data="all_attended"),
    ])
    buttons.append([
        InlineKeyboardButton(text="📨 Yuborish", callback_data="submit_noshow"),
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def report_keyboard() -> InlineKeyboardMarkup:
    """Quick report access."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚨 Shikoyat bildirish", callback_data="start_report")],
    ])
