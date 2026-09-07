"""Weekly scheduler — all timed events for the Teahouse bot.

Schedule (Asia/Tashkent, UTC+5, no DST):
  Mon 20:00 — Offer wave 1
  Mon 21:00 — Wave 1 closes, unpaid released, pool re-formed
  Tue 10:00 — Offer wave 2
  Tue 11:00 — Wave 2 closes
  Tue 20:00 — Roster lock + 24h reveal (venue, profiles, questions)
  Wed morning — Day-of nudge
  Wed 18:00 — 2-hours-out nudge
  Wed 20:00 — Meeting time
  Thu morning — Feedback poll
"""

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from bot.config import settings

TZ = ZoneInfo(settings.timezone)


def create_scheduler() -> AsyncIOScheduler:
    """Create and configure the APScheduler instance with all weekly jobs."""
    scheduler = AsyncIOScheduler(timezone=TZ)

    # Monday 20:00 — Offer wave 1
    scheduler.add_job(
        trigger_offer_wave1,
        CronTrigger(day_of_week="mon", hour=20, minute=0, timezone=TZ),
        id="offer_wave1",
        name="Offer Wave 1",
        replace_existing=True,
    )

    # Monday 21:00 — Wave 1 deadline
    scheduler.add_job(
        trigger_wave1_close,
        CronTrigger(day_of_week="mon", hour=21, minute=0, timezone=TZ),
        id="wave1_close",
        name="Wave 1 Close",
        replace_existing=True,
    )

    # Tuesday 10:00 — Offer wave 2
    scheduler.add_job(
        trigger_offer_wave2,
        CronTrigger(day_of_week="tue", hour=10, minute=0, timezone=TZ),
        id="offer_wave2",
        name="Offer Wave 2",
        replace_existing=True,
    )

    # Tuesday 11:00 — Wave 2 deadline
    scheduler.add_job(
        trigger_wave2_close,
        CronTrigger(day_of_week="tue", hour=11, minute=0, timezone=TZ),
        id="wave2_close",
        name="Wave 2 Close",
        replace_existing=True,
    )

    # Tuesday 20:00 — Roster lock + 24h reveal
    scheduler.add_job(
        trigger_reveal,
        CronTrigger(day_of_week="tue", hour=20, minute=0, timezone=TZ),
        id="reveal",
        name="24h Reveal",
        replace_existing=True,
    )

    # Wednesday 09:00 — Morning nudge
    scheduler.add_job(
        trigger_morning_nudge,
        CronTrigger(day_of_week="wed", hour=9, minute=0, timezone=TZ),
        id="morning_nudge",
        name="Morning Nudge",
        replace_existing=True,
    )

    # Wednesday 18:00 — 2 hours out
    scheduler.add_job(
        trigger_two_hour_nudge,
        CronTrigger(day_of_week="wed", hour=18, minute=0, timezone=TZ),
        id="two_hour_nudge",
        name="2-Hour Nudge",
        replace_existing=True,
    )

    # Thursday 09:00 — Feedback poll
    scheduler.add_job(
        trigger_feedback_poll,
        CronTrigger(day_of_week="thu", hour=9, minute=0, timezone=TZ),
        id="feedback_poll",
        name="Feedback Poll",
        replace_existing=True,
    )

    return scheduler


# ─── Job handlers (stubs, will be implemented with full logic) ───


async def trigger_offer_wave1():
    """Send match offers to all eligible users (wave 1)."""
    from bot.services.notifications import send_offer_wave
    await send_offer_wave(wave=1)


async def trigger_wave1_close():
    """Close wave 1: release unpaid seats, reform pool."""
    from bot.services.notifications import close_offer_wave
    await close_offer_wave(wave=1)


async def trigger_offer_wave2():
    """Send match offers for remaining seats (wave 2)."""
    from bot.services.notifications import send_offer_wave
    await send_offer_wave(wave=2)


async def trigger_wave2_close():
    """Close wave 2: finalize paid pool."""
    from bot.services.notifications import close_offer_wave
    await close_offer_wave(wave=2)


async def trigger_reveal():
    """Lock rosters and send 24h reveals: venue, profiles, questions."""
    from bot.services.notifications import send_reveals
    await send_reveals()


async def trigger_morning_nudge():
    """Send morning reminder on meeting day."""
    from bot.services.notifications import send_nudge
    await send_nudge(nudge_type="morning")


async def trigger_two_hour_nudge():
    """Send 2-hours-out reminder."""
    from bot.services.notifications import send_nudge
    await send_nudge(nudge_type="two_hours")


async def trigger_feedback_poll():
    """Send post-meeting feedback poll on Thursday morning."""
    from bot.services.notifications import send_feedback_polls
    await send_feedback_polls()
