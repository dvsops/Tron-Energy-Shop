import aiohttp
import logging
from typing import Dict, Any, List
from app.models.config import TRENERGY_API_KEY, TRENERGY_BASE_URL
from app.models.database import db

logger = logging.getLogger(__name__)

class TrenergyAPI:
    
    def __init__(self):
        self.api_key = TRENERGY_API_KEY
        self.base_url = TRENERGY_BASE_URL
        self.session = None
    
    async def __aenter__(self):
        timeout = aiohttp.ClientTimeout(total=30)
        self.session = aiohttp.ClientSession(timeout=timeout)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def _get_headers(self) -> Dict[str, str]:
        return {
            'Authorization': f'Bearer {self.api_key}',
            'Accept': 'application/json'
        }
    
    async def _make_request(self, method: str, endpoint: str, data: Dict = None) -> Dict[str, Any]:
        if not self.session:
            raise RuntimeError("API client not initialized. Use async context manager.")
        
        url = f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
        headers = self._get_headers()
        
        try:
            async with self.session.request(
                method=method,
                url=url,
                headers=headers,
                json=data,
            ) as response:
                response_data = await response.json()
                logger.info(f"API Response [{method} {url}]: Status {response.status}")
                if response.status >= 400:
                    logger.error(f"API Error {response.status}")
                    raise Exception(f"API Error {response.status}: {response_data.get('error', 'Unknown error')}")
                return response_data
                    
        except aiohttp.ClientError as e:
            logger.error(f"Network error: {e}")
            raise Exception(f"Network error: {e}")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise
    
    async def get_available_periods(self) -> List[Dict[str, Any]]:
        return [
            {
                'id': '15min',
                'name': '15 минут',
                'duration_minutes': 15,
                'min_energy': 60000,
                'description': 'Краткосрочная аренда энергии'
            },
            {
                'id': '1hour',
                'name': '1 час',
                'duration_minutes': 60,
                'min_energy': 30000,
                'description': 'Среднесрочная аренда энергии'
            },
            {
                'id': '24hours',
                'name': '24 часа',
                'duration_minutes': 1440,
                'min_energy': 30000,
                'description': 'Долгосрочная аренда энергии'
            }
        ]
    
    async def calculate_energy_price(self, energy_amount: int, period_id: str, user_id: int = None) -> Dict[str, Any]:
        periods = await self.get_available_periods()
        period = next((p for p in periods if p['id'] == period_id), None)
        
        if not period:
            raise ValueError(f"Invalid period: {period_id}")
        
        if energy_amount < period['min_energy']:
            raise ValueError(f"Minimum energy amount for {period['name']} is {period['min_energy']}")
        
        try:
            consumer_data = {
                'name': f'Price check {energy_amount} energy {period_id}',
                'address': 'TY3dRk4eQ75dCrW7tUcCzggU9rnz4V1111',
                'resource': 'ENERGY',
                'resource_amount': energy_amount,
                'desired_resource_amount': energy_amount,
                'creation_type': 2,
                'consumption_type': 1,
                'payment_period': period['duration_minutes']
            }
            
            response = await self._make_request('POST', '/consumers', consumer_data)
            
            if response.get('status') and response.get('data'):
                consumer_id = response['data']['id']
                
                consumer_info = await self._make_request('GET', f'/consumers/{consumer_id}')
                
                if consumer_info.get('status') and consumer_info.get('data'):
                    estimated_cost = consumer_info['data'].get('estimated_cost_trx', 0)
                    
                    price_data = {
                        'energy_amount': energy_amount,
                        'period_id': period_id,
                        'period_name': period['name'],
                        'duration_minutes': period['duration_minutes'],
                        'estimated_cost_trx': estimated_cost,
                        'consumer_id': consumer_id
                    }
                    
                    price_data = await self._apply_margin_to_price(price_data, user_id)
                    
                    return price_data
                else:
                    raise Exception("Failed to get consumer info")
            else:
                raise Exception("Failed to create consumer")
                    
        except Exception as e:
            logger.error(f"Error calculating energy price: {e}")
            return await self._get_fixed_data(energy_amount, period_id, user_id)
    
    async def _apply_margin_to_price(self, price_data: Dict[str, Any], user_id: int = None) -> Dict[str, Any]:
        try:
            custom_margin = None
            if user_id:
                custom_margin = await db.get_user_margin(user_id)
            
            if custom_margin is not None:
                margin_percent = custom_margin
                margin_type = 'individual'
            else:
                margin_percent = await db.get_global_energy_margin()
                margin_type = 'global'
            
            original_price = price_data['estimated_cost_trx']
            margin_amount = original_price * (margin_percent / 100)
            final_price = original_price + margin_amount
            
            price_data['original_price_trx'] = original_price
            price_data['margin_percent'] = margin_percent
            price_data['margin_amount_trx'] = margin_amount
            price_data['final_price_trx'] = final_price
            price_data['margin_type'] = margin_type
            
            logger.info(f"Применена {margin_type} наценка {margin_percent}% для пользователя {user_id}: {original_price} -> {final_price} TRX")
            
            return price_data
            
        except Exception as e:
            logger.error(f"Error applying margin: {e}")
            return price_data
    
    async def _get_fixed_data(self, energy_amount: int, period_id: str, user_id: int = None) -> Dict[str, Any]:
        fixed_prices = {
            '15min': {
                60000: 0.5,
                100000: 0.8,
                150000: 1.2
            },
            '1hour': {
                30000: 0.3,
                50000: 0.5,
                100000: 1.0
            },
            '24hours': {
                30000: 0.2,
                50000: 0.3,
                100000: 0.6,
                131000: 8.78
            }
        }
        
        period_prices = fixed_prices.get(period_id, {})
        base_price = period_prices.get(energy_amount, 1.0)
        
        price_data = {
            'energy_amount': energy_amount,
            'period_id': period_id,
            'period_name': period_id,
            'duration_minutes': 15 if period_id == '15min' else (60 if period_id == '1hour' else 1440),
            'estimated_cost_trx': base_price,
            'consumer_id': None
        }
        
        return await self._apply_margin_to_price(price_data, user_id)
    
    async def validate_api_price(self, api_price: float, fixed_price: float) -> bool:
        if fixed_price == 0:
            return True
        
        diff_percent = abs(api_price - fixed_price) / fixed_price * 100
        is_critical_diff = diff_percent > 90
        
        if is_critical_diff:
            logger.warning(f"Критическая разница в цене: {diff_percent:.1f}%")
        
        return not is_critical_diff
    
    async def purchase_energy(self, energy_amount: int, period_id: str, user_wallet: str, user_id: int = None) -> Dict[str, Any]:
        try:
            price_data = await self.calculate_energy_price(energy_amount, period_id, user_id)
            
            consumer_data = {
                'name': f'Energy purchase {energy_amount} for {period_id}',
                'address': user_wallet,
                'resource': 'ENERGY',
                'resource_amount': energy_amount,
                'desired_resource_amount': energy_amount,
                'creation_type': 1,
                'consumption_type': 1,
                'payment_period': price_data['duration_minutes']
            }
            
            response = await self._make_request('POST', '/consumers', consumer_data)
            
            if response.get('status') and response.get('data'):
                consumer_id = response['data']['id']
                
                return {
                    'success': True,
                    'consumer_id': consumer_id,
                    'price_data': price_data,
                    'message': 'Energy purchase created successfully'
                }
            else:
                return {
                    'success': False,
                    'error': 'Failed to create energy purchase',
                    'price_data': price_data
                }
                    
        except Exception as e:
            logger.error(f"Error purchasing energy: {e}")
            return {
                'success': False,
                'error': str(e)
            }

