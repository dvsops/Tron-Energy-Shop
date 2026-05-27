import asyncio
import aiohttp
from app.models.config import COINGECKO_API_URL
from app.models.database import db


class PriceUpdater:
    def __init__(self):
        self.is_running = False
    
    async def update_trx_price(self):
        try:
            url = COINGECKO_API_URL
            connector = aiohttp.TCPConnector(limit=10, limit_per_host=5, keepalive_timeout=30)
            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=15, connect=5)) as response:
                    if response.status == 200:
                        data = await response.json()
                        price = data.get('tron', {}).get('usd', 0.0)
                        
                        await db.set_trx_price(price)
                        print(f"TRX курс обновлен: ${price:.4f}")
                        
                        return price
            
            return 0.0
        except Exception as e:
            print(f"Ошибка при обновлении курса TRX: {e}")
            return 0.0
    
    async def run(self):
        self.is_running = True
        print("🔄 Запущено обновление курса TRX")
        
        while self.is_running:
            try:
                await self.update_trx_price()
                await asyncio.sleep(300)
            except Exception as e:
                print(f"❌ Ошибка в цикле обновления курса: {e}")
                await asyncio.sleep(60)
    
    def stop(self):
        self.is_running = False
        print("🛑 Остановлено обновление курса TRX")


price_updater = PriceUpdater()

