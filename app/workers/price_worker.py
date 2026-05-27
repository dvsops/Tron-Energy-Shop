import asyncio
import logging
from app.models.database import db
from app.services.price.updater import price_updater

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


async def main():
    await db.connect()
    logger.info("Price worker started")
    try:
        await price_updater.run()
    finally:
        price_updater.stop()
        await db.close()


if __name__ == "__main__":
    asyncio.run(main())
