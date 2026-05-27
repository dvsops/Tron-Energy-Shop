import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
REQUIRED_CHANNEL_ID = os.getenv('REQUIRED_CHANNEL_ID')
CHANNEL_LINK = os.getenv('CHANNEL_LINK')
ADMIN_IDS = [int(admin_id) for admin_id in os.getenv('ADMIN_IDS', '').split(',') if admin_id]

SUPPORT_LINK = os.getenv('SUPPORT_LINK', 'https://t.me/support')
WHOLESALE_LINK = os.getenv('WHOLESALE_LINK', 'https://t.me/wholesale_manager')
RULES_LINK = os.getenv('RULES_LINK', 'https://t.me/rules')

REFERRAL_BONUS_PERCENT = float(os.getenv('REFERRAL_BONUS_PERCENT', '2'))

COINGECKO_API_URL = 'https://api.coingecko.com/api/v3/simple/price?ids=tron&vs_currencies=usd'

TRON_NETWORK = os.getenv('TRON_NETWORK', 'mainnet')
TRONGRID_API_KEY = os.getenv('TRONGRID_API_KEY', '')
MAIN_WALLET_ADDRESS = os.getenv('MAIN_WALLET_ADDRESS', '')
MAIN_WALLET_PRIVATE_KEY = os.getenv('MAIN_WALLET_PRIVATE_KEY', '')
MIN_DEPOSIT_AMOUNT = float(os.getenv('MIN_DEPOSIT_AMOUNT', '10'))

ENERGY_MARGIN = float(os.getenv('ENERGY_MARGIN', '10'))

DATABASE_PATH = 'database.db'
MAIN_MENU_IMAGE = 'images/main_menu.jpg'

TRENERGY_API_KEY = os.getenv('TRENERGY_API_KEY', '')
TRENERGY_BASE_URL = os.getenv('TRENERGY_BASE_URL', 'https://nile-core.tr.energy/api')

TRENERGY_ALTERNATIVE_URLS = [
    'https://nile-core.tr.energy/api',
    'https://nile-core.tr.energy',
    'https://api.nile.tr.energy',
    'https://nile.tr.energy/api',
    'https://api.tr.energy',
    'https://core.tr.energy/api'
]

ENCRYPTION_SECRET_KEY = os.getenv("ENCRYPTION_SECRET_KEY", "")

RUN_BALANCE_CHECKER = os.getenv("RUN_BALANCE_CHECKER", "true").lower() == "true"
RUN_PRICE_UPDATER = os.getenv("RUN_PRICE_UPDATER", "true").lower() == "true"

ENERGY_PROVIDER_TIMEOUT_SECONDS = float(os.getenv("ENERGY_PROVIDER_TIMEOUT_SECONDS", "20"))
ENERGY_PROVIDER_RETRIES = int(os.getenv("ENERGY_PROVIDER_RETRIES", "2"))

TRONEX_API_URL = os.getenv("TRONEX_API_URL", "")
TRONEX_API_KEY = os.getenv("TRONEX_API_KEY", "")
TRONPULSE_API_URL = os.getenv("TRONPULSE_API_URL", "")
TRONPULSE_API_KEY = os.getenv("TRONPULSE_API_KEY", "")
ENERGYFI_API_URL = os.getenv("ENERGYFI_API_URL", "")
ENERGYFI_API_KEY = os.getenv("ENERGYFI_API_KEY", "")

RUN_SMART_MANAGER = os.getenv("RUN_SMART_MANAGER", "false").lower() == "true"
RUN_TRUST_MONITOR = os.getenv("RUN_TRUST_MONITOR", "false").lower() == "true"
