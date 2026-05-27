from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from app.models.config import ADMIN_IDS
from app.models.database import db
from app.keyboards.admin import get_admin_menu_keyboard
from app.utils.helpers import safe_edit_or_send_message


class AdminStates(StatesGroup):
    waiting_for_broadcast = State()
    waiting_for_user_id = State()
    waiting_for_balance_change = State()
    waiting_for_ref_percent = State()
    waiting_for_margin = State()
    waiting_for_main_wallet = State()
    waiting_for_private_key = State()
    waiting_for_user_margin = State()
    waiting_for_user_ref_percent = State()
    waiting_for_mass_transfer_confirm = State()


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


async def cmd_admin(message: types.Message):
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет доступа к админ-панели")
        return
    
    await show_admin_panel(message)


async def show_admin_panel(message: types.Message):
    text = """
🔐 Админ-панель

Выберите действие:
"""
    await message.answer(text, reply_markup=get_admin_menu_keyboard())


async def callback_admin_panel(callback: types.CallbackQuery, state: FSMContext = None):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещен", show_alert=True)
        return
    
    if state:
        await state.finish()
    
    text = """
🔐 Админ-панель

Выберите действие:
"""
    await safe_edit_or_send_message(
        callback.bot,
        callback.message.chat.id,
        callback.message.message_id,
        text,
        get_admin_menu_keyboard()
    )
    await callback.answer()


async def callback_admin_close(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещен", show_alert=True)
        return
    
    await callback.message.delete()
    await callback.answer("✅ Админ-панель закрыта")


def register_admin_handlers(dp: Dispatcher):
    dp.register_message_handler(cmd_admin, commands=['admin'], state='*')
    dp.register_callback_query_handler(callback_admin_panel, text='admin_panel', state='*')
    dp.register_callback_query_handler(callback_admin_close, text='admin_close', state='*')