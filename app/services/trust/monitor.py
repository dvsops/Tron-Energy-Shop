import asyncio
import logging
from app.models.database import db
from app.services.api.tron import tron_manager
from app.models.config import MAIN_WALLET_ADDRESS

logger = logging.getLogger(__name__)


class TrustMonitor:
    def __init__(self):
        self.is_running = False

    async def process_once(self):
        total_user = await db.get_total_user_balance()
        hot_balance = 0.0
        if MAIN_WALLET_ADDRESS:
            hot_balance = await tron_manager.get_balance(MAIN_WALLET_ADDRESS)
        await db.add_reserve_snapshot(total_user, hot_balance)

    async def run(self):
        self.is_running = True
        while self.is_running:
            try:
                await self.process_once()
                await asyncio.sleep(600)
            except Exception as e:
                logger.exception("Trust monitor error: %s", e)
                await asyncio.sleep(60)

    def stop(self):
        self.is_running = False


trust_monitor = TrustMonitor()
