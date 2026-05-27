import asyncio
import logging
from app.models.database import db
from app.services.energy.smart_manager import smart_manager

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


async def main():
    await db.connect()
    logger.info("Smart worker started")
    try:
        await smart_manager.run()
    finally:
        smart_manager.stop()
        await db.close()


if __name__ == "__main__":
    asyncio.run(main())
