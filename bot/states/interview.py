from aiogram.fsm.state import State, StatesGroup


class InterviewStates(StatesGroup):
    """FSM states for the comprehensive 10-12 question onboarding flow."""

    # 1-BOSQICH: SHAXSIY VA KASBIY MA'LUMOTLAR HAMDA ERISHILGAN NATIJALAR
    stage1_full_name = State()       # 1. Ism va familiya
    stage1_phone = State()           # 2. Telefon raqam
    stage1_role = State()            # 3. Kasb va asosiy lavozim
    stage1_company = State()         # 4. Kompaniya / startap / loyiha
    stage1_industry = State()        # 5. Faoliyat sohasi
    stage1_seniority = State()       # 6. Tajriba darajasi va yillari
    stage1_achievements = State()    # 7. Eng katta yutug'i, loyihasi yoki biznes ko'rsatkichi (daromad, jamoa, eksport)
    stage1_age = State()             # 8. Yoshi

    # 2-BOSQICH: QIDIRILAYOTGAN SHERIKLAR VA UCHRASHUV TALABLARI
    stage2_partner_goal = State()    # 9. Uchrashuvdan asosiy maqsad (Hammuassis, Investor, Mijozlar, Jamoa, Mentor)
    stage2_target_industry = State() # 10. Qaysi soha vakillari bilan uchrashish kerak
    stage2_target_seniority = State()# 11. Qidirilayotgan sherikning tajriba darajasi (founder, senior, investor)
    stage2_offer = State()           # 12. O'zi boshqalarga qanday aniq foyda, tajriba yoki resurs bera oladi
    stage2_expectations = State()    # 13. Stolda aynan qaysi amaliy muammo yoki mavzuni muhokama qilmoqchi

    # Yakuniy tasdiqlash
    confirming_profile = State()
    completed = State()


class OfferStates(StatesGroup):
    """FSM states for match offer and payment flow."""
    offer_shown = State()
    awaiting_payment = State()
    payment_confirmed = State()


class FeedbackStates(StatesGroup):
    """FSM states for post-meeting feedback."""
    selecting_meet_again = State()
    selecting_no_shows = State()
    feedback_submitted = State()


class ReportStates(StatesGroup):
    """FSM states for reporting a user."""
    selecting_user = State()
    entering_reason = State()
    report_submitted = State()
