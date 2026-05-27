from aiogram import Dispatcher
from .start import register_start_handlers
from .profile import register_profile_handlers
from .calculator import register_calculator_handlers
from .purchase import register_purchase_handlers
from .referral import register_referral_handlers
from .language import register_language_handlers
from .account import register_account_handlers


def register_user_handlers(dp: Dispatcher):
    register_start_handlers(dp)
    register_profile_handlers(dp)
    register_calculator_handlers(dp)
    register_purchase_handlers(dp)
    register_referral_handlers(dp)
    register_language_handlers(dp)
    register_account_handlers(dp)

