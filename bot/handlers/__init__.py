from bot.handlers.start import router as start_router
from bot.handlers.interview import router as interview_router
from bot.handlers.common import router as common_router

__all__ = ["start_router", "interview_router", "common_router"]
