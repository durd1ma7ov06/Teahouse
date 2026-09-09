from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def start_keyboard() -> InlineKeyboardMarkup:
    """Boshlash va ma'lumot klaviaturasi (emojilarsiz)."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Boshlash", callback_data="start_interview")],
        [InlineKeyboardButton(text="Teahouse haqida", callback_data="about_teahouse")],
    ])


def confirm_keyboard() -> InlineKeyboardMarkup:
    """Anketani tasdiqlash yoki qaytadan boshlash."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Tasdiqlash va saqlash", callback_data="confirm_profile")],
        [InlineKeyboardButton(text="Qaytadan to'ldirish", callback_data="redo_interview")],
    ])


def industry_keyboard() -> InlineKeyboardMarkup:
    """Faoliyat sohalari tanlovi."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Axborot texnologiyalari (IT)", callback_data="ind_it")],
        [InlineKeyboardButton(text="Moliya, bank va investitsiya", callback_data="ind_finance")],
        [InlineKeyboardButton(text="Savdo, riteyl va xizmatlar", callback_data="ind_retail")],
        [InlineKeyboardButton(text="Marketing, PR va reklama", callback_data="ind_marketing")],
        [InlineKeyboardButton(text="Ishlab chiqarish va sanoat", callback_data="ind_production")],
        [InlineKeyboardButton(text="Qurilish va ko'chmas mulk", callback_data="ind_construction")],
        [InlineKeyboardButton(text="Ta'lim va konsalting", callback_data="ind_education")],
        [InlineKeyboardButton(text="Tibbiyot va farmatsevtika", callback_data="ind_medicine")],
        [InlineKeyboardButton(text="Boshqa soha (qo'lda kiritaman)", callback_data="ind_other")],
    ])


def seniority_keyboard() -> InlineKeyboardMarkup:
    """Tajriba darajasini tanlash."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Boshlang'ich (0-2 yil)", callback_data="seniority_junior")],
        [InlineKeyboardButton(text="O'rta mutaxassis (3-5 yil)", callback_data="seniority_mid")],
        [InlineKeyboardButton(text="Katta mutaxassis (6-10 yil)", callback_data="seniority_senior")],
        [InlineKeyboardButton(text="Rahbar / Biznes asoschisi (10+ yil)", callback_data="seniority_founder")],
    ])


def age_range_keyboard() -> InlineKeyboardMarkup:
    """Yosh oralig'ini tanlash."""
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


def partner_goal_keyboard() -> InlineKeyboardMarkup:
    """2-Bosqich: Sherikdan ko'zlangan asosiy maqsad."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Biznes hamkor / Hammuassis", callback_data="goal_cofounder")],
        [InlineKeyboardButton(text="Investor / Moliyalashtirish", callback_data="goal_investor")],
        [InlineKeyboardButton(text="Mijozlar / Buyurtmachilar topish", callback_data="goal_clients")],
        [InlineKeyboardButton(text="Malakali mutaxassis / Jamoa yig'ish", callback_data="goal_team")],
        [InlineKeyboardButton(text="Mentor / Tajribali maslahatchi", callback_data="goal_mentor")],
        [InlineKeyboardButton(text="Tajriba almashish va networking", callback_data="goal_networking")],
    ])


def target_industry_keyboard() -> InlineKeyboardMarkup:
    """2-Bosqich: Qaysi soha vakillari bilan uchrashish qiziq."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Barcha soha vakillari bilan", callback_data="tgt_all")],
        [InlineKeyboardButton(text="Axborot texnologiyalari (IT)", callback_data="tgt_it")],
        [InlineKeyboardButton(text="Biznes, savdo va investitsiya", callback_data="tgt_business")],
        [InlineKeyboardButton(text="Marketing va savdo mutaxassislari", callback_data="tgt_marketing")],
        [InlineKeyboardButton(text="Ishlab chiqarish va xizmat ko'rsatish", callback_data="tgt_industry")],
        [InlineKeyboardButton(text="Boshqa aniq soha (qo'lda yozaman)", callback_data="tgt_other")],
    ])


def offer_keyboard() -> InlineKeyboardMarkup:
    """Taklifni qabul qilish yoki o'tkazib yuborish."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Joy band qilish (99,000 UZS)", callback_data="accept_offer")],
        [InlineKeyboardButton(text="Bu hafta o'tkazib yuboraman", callback_data="skip_offer")],
    ])


def payment_keyboard(stars_amount: int) -> InlineKeyboardMarkup:
    """Telegram Stars orqali to'lov tugmasi."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"{stars_amount} Stars bilan to'lash", pay=True)],
    ])


def meet_again_keyboard(members: list[dict], selected_ids: set[int]) -> InlineKeyboardMarkup:
    """Uchrashuvdan so'ng kimlar bilan yana ko'rishish so'rovi."""
    buttons = []
    for member in members:
        uid = member["user_id"]
        name = member["first_name"]
        check = "[+] " if uid in selected_ids else ""
        buttons.append([
            InlineKeyboardButton(
                text=f"{check}{name}",
                callback_data=f"toggle_meet_{uid}",
            )
        ])
    buttons.append([
        InlineKeyboardButton(text="Yuborish", callback_data="submit_feedback"),
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def no_show_keyboard(members: list[dict], selected_ids: set[int]) -> InlineKeyboardMarkup:
    """Kelmaganlarni belgilash klaviaturasi."""
    buttons = []
    for member in members:
        uid = member["user_id"]
        name = member["first_name"]
        check = "[-] " if uid in selected_ids else ""
        buttons.append([
            InlineKeyboardButton(
                text=f"{check}{name}",
                callback_data=f"toggle_noshow_{uid}",
            )
        ])
    buttons.append([
        InlineKeyboardButton(text="Hammasi keldi", callback_data="all_attended"),
    ])
    buttons.append([
        InlineKeyboardButton(text="Yuborish", callback_data="submit_noshow"),
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def report_keyboard() -> InlineKeyboardMarkup:
    """Shikoyat bildirish tugmasi."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Shikoyat bildirish", callback_data="start_report")],
    ])
