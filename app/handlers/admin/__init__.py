from aiogram import Dispatcher
from .admin import register_admin_handlers


def register_admin_handlers(dp: Dispatcher):
    from .admin import register_admin_handlers as register_admin
    register_admin(dp)
