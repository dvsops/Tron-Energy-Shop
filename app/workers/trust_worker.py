import asyncio
import logging
from app.models.database import db
from app.services.trust.monitor import trust_monitor

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


async def main():
    await db.connect()
    logger.info("Trust worker started")
    try:
        await trust_monitor.run()
    finally:
        trust_monitor.stop()
        await db.close()


if __name__ == "__main__":
    asyncio.run(main())
