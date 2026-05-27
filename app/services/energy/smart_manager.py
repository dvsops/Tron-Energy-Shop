import asyncio
import logging
from datetime import datetime, timedelta
import aiohttp
from app.models.database import db
from app.services.energy.marketplace import marketplace
from app.services.api.tron import tron_manager
from app.models.config import BOT_TOKEN
from app.services.energy.quote_engine import build_user_quote

logger = logging.getLogger(__name__)


class SmartEnergyManager:
    def __init__(self):
        self.is_running = False
        self._period_title = {
            "15min": "15 минут",
            "1hour": "1 час",
            "24hours": "24 часа",
        }

    async def _notify_user(self, user_id: int, text: str):
        if not BOT_TOKEN:
            return
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {"chat_id": user_id, "text": text}
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                await session.post(url, json=payload)
        except Exception:
            pass

    def _is_recent_notice(self, value: str, minutes: int = 120) -> bool:
        if not value:
            return False
        try:
            at = datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
            return datetime.utcnow() - at < timedelta(minutes=minutes)
        except Exception:
            return False

    async def process_once(self):
        users = await db.get_smart_enabled_users()
        for user in users:
            if not user.get("trx_wallet"):
                continue
            target_energy = max(int(user.get("target_energy_amount", 30000) or 30000), 30000)
            period_id = user.get("period_id", "24hours")
            min_trigger = max(int(user.get("min_energy_trigger", 10000) or 10000), 1)

            current_energy = await tron_manager.get_energy_available(user["trx_wallet"])
            if current_energy >= min_trigger:
                continue

            try:
                pricing = await build_user_quote(user["user_id"], target_energy, period_id)
            except Exception:
                continue

            final_price = float(pricing["final_price_trx"])
            if final_price > float(user.get("price_threshold_trx", 0)):
                continue

            # Перед каждой автопокупкой — живая проверка баланса.
            balance_now = await db.get_balance(user["user_id"])
            if balance_now < final_price:
                if not self._is_recent_notice(user.get("last_low_balance_notice_at")):
                    await self._notify_user(
                        user["user_id"],
                        (
                            "⚠️ Автопокупка энергии не выполнена: недостаточно средств.\n"
                            f"Нужно: {final_price:.4f} TRX\n"
                            f"Доступно: {balance_now:.4f} TRX\n"
                            f"Кошелек: {user['trx_wallet']}\n"
                            f"Текущая энергия: {current_energy:,}\n"
                            f"Порог запуска: < {min_trigger:,}"
                        ),
                    )
                    await db.mark_smart_low_balance_notice(user["user_id"])
                continue

            result = await marketplace.purchase_with_quote(
                pricing["quote"],
                user["trx_wallet"],
                user["user_id"],
            )
            if result.get("success"):
                await db.update_balance(user["user_id"], -final_price)
                await db.add_purchase(
                    user["user_id"],
                    target_energy,
                    f"{self._period_title.get(period_id, period_id)} (авто)",
                    final_price,
                    user["trx_wallet"],
                    result.get("order_id"),
                    provider=result.get("provider", "unknown"),
                    status="success",
                )
                await db.log_provider_order(
                    user["user_id"],
                    result.get("provider", "unknown"),
                    result.get("order_id"),
                    target_energy,
                    period_id,
                    final_price,
                    "success",
                )
                await db.mark_smart_auto_purchase(user["user_id"])
                await self._notify_user(
                    user["user_id"],
                    (
                        "✅ Автопокупка энергии выполнена.\n"
                        f"Объем: {target_energy:,}\n"
                        f"Период: {self._period_title.get(period_id, period_id)}\n"
                        f"Цена: {final_price:.4f} TRX\n"
                        f"Остаток баланса: {(balance_now - final_price):.4f} TRX"
                    ),
                )
                logger.info("Smart order success user_id=%s", user["user_id"])

    async def run(self):
        self.is_running = True
        while self.is_running:
            try:
                await self.process_once()
                await asyncio.sleep(120)
            except Exception as e:
                logger.exception("Smart manager error: %s", e)
                await asyncio.sleep(30)

    def stop(self):
        self.is_running = False


smart_manager = SmartEnergyManager()
