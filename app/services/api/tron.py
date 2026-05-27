from tronpy import Tron
from tronpy.keys import PrivateKey
from app.models.config import TRON_NETWORK, TRONGRID_API_KEY
import aiohttp
import asyncio


class TronManager:
    def __init__(self):
        if TRON_NETWORK == 'mainnet':
            self.tron = Tron(network='mainnet')
        else:
            self.tron = Tron(network='nile')
    
    def generate_wallet(self):
        private_key = PrivateKey.random()
        address = private_key.public_key.to_base58check_address()
        return {
            'address': address,
            'private_key': private_key.hex()
        }
    
    async def get_balance(self, address: str) -> float:
        max_retries = 3
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                url = f"https://api.trongrid.io/v1/accounts/{address}"
                
                headers = {}
                if TRONGRID_API_KEY:
                    headers['TRON-PRO-API-KEY'] = TRONGRID_API_KEY
                
                connector = aiohttp.TCPConnector(
                    limit=10,
                    limit_per_host=5,
                    keepalive_timeout=30,
                    enable_cleanup_closed=True
                )
                async with aiohttp.ClientSession(connector=connector) as session:
                    async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=30, connect=10)) as response:
                        if response.status == 200:
                            data = await response.json()
                            if 'data' in data and len(data['data']) > 0:
                                balance_sun = data['data'][0].get('balance', 0)
                                return balance_sun / 1_000_000
                            return 0.0
                        elif response.status == 429:
                            if attempt < max_retries - 1:
                                await asyncio.sleep(retry_delay * (attempt + 1))
                                continue
                            else:
                                return 0.0
                        else:
                            return 0.0
                            
            except asyncio.TimeoutError:
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay)
                    continue
                else:
                    return 0.0
            except aiohttp.ClientConnectorError as e:
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay * (attempt + 1))
                    continue
                else:
                    return 0.0
            except aiohttp.ServerDisconnectedError as e:
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay * (attempt + 1))
                    continue
                else:
                    return 0.0
            except Exception as e:
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay)
                    continue
                else:
                    return 0.0
        
        return 0.0
    
    async def transfer_trx(self, from_private_key: str, to_address: str, amount: float) -> bool:
        max_retries = 3
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                amount_sun = int(amount * 1_000_000)
                
                priv_key = PrivateKey(bytes.fromhex(from_private_key))
                
                from_address = priv_key.public_key.to_base58check_address()
                
                current_balance = await self.get_balance(from_address)
                if current_balance < amount + 1.0:
                    return False
                
                txn = (
                    self.tron.trx.transfer(from_address, to_address, amount_sun)
                    .build()
                    .sign(priv_key)
                )
                
                result = txn.broadcast()
                
                if result and 'result' in result:
                    return result['result']
                
                return False
                
            except aiohttp.ClientConnectorError as e:
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay * (attempt + 1))
                    continue
                else:
                    return False
            except aiohttp.ServerDisconnectedError as e:
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay * (attempt + 1))
                    continue
                else:
                    return False
            except Exception as e:
                error_msg = str(e)
                
                if "429" in error_msg or "Too Many Requests" in error_msg or "rate limit" in error_msg.lower():
                    if attempt < max_retries - 1:
                        await asyncio.sleep(retry_delay * (attempt + 1))
                        continue
                    else:
                        return False
                elif "insufficient" in error_msg.lower() or "balance" in error_msg.lower():
                    return False
                elif attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay)
                    continue
                else:
                    return False
        
        return False
    
    def is_valid_address(self, address: str) -> bool:
        try:
            return self.tron.is_address(address)
        except:
            return False

    async def get_transactions(self, address: str, limit: int = 20) -> tuple:
        max_retries = 3
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                url = f"https://api.trongrid.io/v1/accounts/{address}/transactions"
                
                headers = {}
                if TRONGRID_API_KEY:
                    headers['TRON-PRO-API-KEY'] = TRONGRID_API_KEY
                
                params = {
                    'limit': limit,
                    'only_to': 'true',
                    'order_by': 'block_timestamp,desc'
                }
                
                if attempt == 0:
                    print(f"🌐 Запрос транзакций: {url}?only_to=true&limit={limit}")
                
                connector = aiohttp.TCPConnector(
                    limit=10,
                    limit_per_host=5,
                    keepalive_timeout=30,
                    enable_cleanup_closed=True
                )
                
                timeout = aiohttp.ClientTimeout(total=30)
                
                async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
                    async with session.get(url, headers=headers, params=params) as response:
                        if response.status == 200:
                            data = await response.json()
                            transactions = data.get('data', [])
                            print(f"📊 API вернул {len(transactions)} транзакций для адреса {address}")
                            if not transactions:
                                print(f"📝 Нет транзакций для адреса {address}")
                            return transactions, True
                        elif response.status == 429:
                            if attempt < max_retries - 1:
                                await asyncio.sleep(retry_delay * (attempt + 1))
                                continue
                        else:
                            if attempt < max_retries - 1:
                                await asyncio.sleep(retry_delay)
                                continue
                            
            except Exception as e:
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay)
                    continue
                    
        return [], False

    async def get_energy_available(self, address: str) -> int:
        """
        Возвращает доступную энергию кошелька.
        Использует account_resource + fallback на total_energy_limit/weight.
        """
        max_retries = 3
        retry_delay = 2
        for attempt in range(max_retries):
            try:
                url = f"https://api.trongrid.io/v1/accounts/{address}"
                headers = {}
                if TRONGRID_API_KEY:
                    headers['TRON-PRO-API-KEY'] = TRONGRID_API_KEY
                timeout = aiohttp.ClientTimeout(total=20, connect=8)
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    async with session.get(url, headers=headers) as response:
                        if response.status != 200:
                            if attempt < max_retries - 1:
                                await asyncio.sleep(retry_delay * (attempt + 1))
                                continue
                            return 0
                        payload = await response.json()
                        rows = payload.get("data") or []
                        if not rows:
                            return 0
                        row = rows[0]
                        res = row.get("account_resource") or {}
                        limit = int(res.get("EnergyLimit", 0) or 0)
                        used = int(res.get("EnergyUsed", 0) or 0)
                        if limit > 0:
                            return max(limit - used, 0)
                        # fallback для некоторых аккаунтов
                        total_limit = int(row.get("total_energy_limit", 0) or 0)
                        total_weight = int(row.get("total_energy_weight", 0) or 0)
                        if total_limit > 0 and total_weight > 0:
                            return max(total_limit - total_weight, 0)
                        return 0
            except Exception:
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay * (attempt + 1))
                    continue
                return 0
        return 0


tron_manager = TronManager()

