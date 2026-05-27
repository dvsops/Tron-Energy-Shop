import logging
import asyncio
from aiogram import Bot, Dispatcher, executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from app.models.config import BOT_TOKEN, RUN_BALANCE_CHECKER, RUN_PRICE_UPDATER, RUN_SMART_MANAGER, RUN_TRUST_MONITOR
from app.models.database import db
from app.handlers.user import register_user_handlers
from app.handlers.admin import register_admin_handlers
from app.services.balance.checker import BalanceChecker
from app.services.price.updater import price_updater
from app.services.energy.smart_manager import smart_manager
from app.services.trust.monitor import trust_monitor

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
balance_checker = None
tasks = []


async def on_startup(dp: Dispatcher):
    global balance_checker, tasks
    logger.info("Подключение к базе данных...")
    await db.connect()
    logger.info("База данных подключена")

    if RUN_BALANCE_CHECKER:
        balance_checker = BalanceChecker(dp.bot)
        tasks.append(asyncio.create_task(balance_checker.run()))

    if RUN_PRICE_UPDATER:
        tasks.append(asyncio.create_task(price_updater.run()))
    if RUN_SMART_MANAGER:
        tasks.append(asyncio.create_task(smart_manager.run()))
    if RUN_TRUST_MONITOR:
        tasks.append(asyncio.create_task(trust_monitor.run()))
    
    logger.info("Бот запущен и готов к работе!")


async def on_shutdown(dp: Dispatcher):
    logger.info("Остановка фоновых задач...")
    if balance_checker:
        balance_checker.stop()
    if RUN_PRICE_UPDATER:
        price_updater.stop()
    if RUN_SMART_MANAGER:
        smart_manager.stop()
    if RUN_TRUST_MONITOR:
        trust_monitor.stop()
    for task in tasks:
        task.cancel()
    
    logger.info("Закрытие соединения с базой данных...")
    await db.close()
    logger.info("Бот остановлен")


def main():
    if not BOT_TOKEN:
        logger.error("Не указан BOT_TOKEN в файле .env")
        return
    
    bot = Bot(token=BOT_TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(bot, storage=storage)
    
    register_user_handlers(dp)
    register_admin_handlers(dp)
    
    executor.start_polling(
        dp,
        on_startup=on_startup,
        on_shutdown=on_shutdown,
        skip_updates=True
    )


if __name__ == '__main__':
    main()

