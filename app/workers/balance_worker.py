import asyncio
import logging
from aiogram import Bot
from app.models.config import BOT_TOKEN
from app.models.database import db
from app.services.balance.checker import BalanceChecker

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


async def main():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN is required")

    bot = Bot(token=BOT_TOKEN)
    checker = BalanceChecker(bot)

    await db.connect()
    logger.info("Balance worker started")
    try:
        await checker.run()
    finally:
        checker.stop()
        await db.close()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
