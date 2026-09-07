"""Teahouse Bot — main entry point.

Run with: python -m bot.main
"""

import asyncio
import logging
import sys

# Windows cp1251 konsolida emojilarni to'g'ri chiqarish uchun UTF-8 ga sozlash
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from bot.config import settings
from bot.handlers import start_router, interview_router, common_router
from bot.services.notifications import set_bot
from bot.services.scheduler import create_scheduler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


async def main():
    """Initialize and start the bot."""
    logger.info("🍵 Teahouse bot ishga tushmoqda...")

    # Initialize bot with Markdown as default parse mode
    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN),
    )

    # FSM storage: Redis mavjud bo'lsa Redis, bo'lmasa ichki xotira (MemoryStorage)
    storage = None
    try:
        from aiogram.fsm.storage.redis import RedisStorage
        import redis.asyncio as aioredis
        r = aioredis.from_url(settings.redis_url)
        await asyncio.wait_for(r.ping(), timeout=1.5)
        storage = RedisStorage.from_url(settings.redis_url)
        logger.info("✅ Redis FSM storage ulandi")
    except Exception:
        from aiogram.fsm.storage.memory import MemoryStorage
        storage = MemoryStorage()
        logger.info("ℹ️ Redis ulanmadi — ichki xotira (MemoryStorage) ishlatilmoqda")

    # Dispatcher
    dp = Dispatcher(storage=storage)

    # Register routers
    dp.include_router(start_router)
    dp.include_router(interview_router)
    dp.include_router(common_router)

    # Register bot for notification service
    set_bot(bot)

    # Create database tables (for development — use Alembic in production)
    from db.base import Base
    from db.session import engine
    import db.models  # noqa: F401 — ensure all models are imported

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("✅ Database tables yaratildi")

    # Start the weekly scheduler
    scheduler = create_scheduler()
    scheduler.start()
    logger.info("✅ Scheduler ishga tushdi")

    # Start polling
    logger.info("✅ Bot tayyor — polling boshlandi")
    try:
        await dp.start_polling(bot)
    finally:
        scheduler.shutdown()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
