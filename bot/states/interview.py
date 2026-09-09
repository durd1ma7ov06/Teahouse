from aiogram.fsm.state import State, StatesGroup


class InterviewStates(StatesGroup):
    """FSM states for the two-stage onboarding flow."""

    # 1-Bosqich: Ro'yxatdan o'tish va o'zi haqida ma'lumot
    stage1_full_name = State()       # Ism va familiya
    stage1_phone = State()           # Telefon raqam
    stage1_role = State()            # Kasb va lavozim
    stage1_company = State()         # Kompaniya / Loyiha
    stage1_industry = State()        # Faoliyat sohasi
    stage1_seniority = State()       # Tajriba darajasi
    stage1_age = State()             # Yoshi

    # 2-Bosqich: Qidirilayotgan sheriklar va uchrashuv talablari
    stage2_partner_goal = State()    # Sherikdan ko'zlangan maqsad
    stage2_target_industry = State() # Qaysi soha vakillari kerak
    stage2_offer = State()           # Bo'lajak sheriklarga o'zining taklifi
    stage2_expectations = State()    # Uchrashuvdan kutilma

    # Yakuniy ko'rib chiqish va tasdiqlash
    confirming_profile = State()
    completed = State()

    # Moslik uchun eski nomlar
    asking_role = stage1_role
    asking_goal = stage2_partner_goal
    asking_offer = stage2_offer
    asking_seniority = stage1_seniority
    asking_age = stage1_age
    asking_interests = stage2_expectations


class OfferStates(StatesGroup):
    """FSM states for match offer and payment flow."""

    offer_shown = State()          # User sees the offer (date/time only)
    awaiting_payment = State()     # Waiting for payment
    payment_confirmed = State()    # Payment received


class FeedbackStates(StatesGroup):
    """FSM states for post-meeting feedback."""

    selecting_meet_again = State()   # Toggle who to meet again
    selecting_no_shows = State()     # Who was not there?
    feedback_submitted = State()     # Done


class ReportStates(StatesGroup):
    """FSM states for reporting a user."""

    selecting_user = State()       # Who to report
    entering_reason = State()      # Why
    report_submitted = State()     # Done
