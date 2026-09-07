from aiogram.fsm.state import State, StatesGroup


class InterviewStates(StatesGroup):
    """FSM states for the onboarding interview flow."""

    # Waiting for bot to introduce itself
    greeting = State()

    # Core interview questions
    asking_role = State()          # What do you do? Role, company, industry
    followup_role = State()        # Follow-up if answer was vague
    asking_goal = State()          # What are you trying to achieve right now?
    followup_goal = State()        # Follow-up if answer was thin
    asking_offer = State()         # What can you offer others?
    followup_offer = State()       # Follow-up if answer was thin
    asking_seniority = State()     # Experience level
    asking_age = State()           # Age
    asking_interests = State()     # Interests outside work

    # Confirmation
    confirming_profile = State()   # Review and confirm
    completed = State()            # Interview done


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
