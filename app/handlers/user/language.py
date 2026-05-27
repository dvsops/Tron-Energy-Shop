from aiogram import types, Dispatcher
from app.models.database import db
from app.locales import locale_manager
from app.keyboards.user import get_subscription_keyboard, get_main_menu_keyboard
from app.utils.helpers import check_subscription, get_trx_price, get_main_menu_image, get_or_create_first_message, safe_edit_or_send_message, safe_edit_or_send_photo


async def safe_callback_answer(callback: types.CallbackQuery, text: str = None, show_alert: bool = False):
    try:
        await callback.answer(text, show_alert=show_alert)
    except Exception as e:
        print(f"Ошибка при ответе на callback: {e}")


async def callback_set_language(callback: types.CallbackQuery):
    language = callback.data.split('_')[-1]
    user_id = callback.from_user.id
    
    await db.set_user_language(user_id, language)
    
    if language == 'ru':
        await safe_callback_answer(callback, "✅ Язык изменен на русский", show_alert=True)
    else:
        await safe_callback_answer(callback, "✅ Language changed to English", show_alert=True)
    
    is_subscribed = await check_subscription(callback.bot, user_id)
    
    if not is_subscribed:
        await safe_edit_or_send_message(
            callback.bot,
            callback.message.chat.id,
            callback.message.message_id,
            locale_manager.get_text('start_not_subscribed', language),
            get_subscription_keyboard(language)
        )
    else:
        trx_price = await get_trx_price()
        price_text = f"{trx_price:.4f}" if trx_price > 0 else "0.0000"
        
        user = await db.get_user(user_id)
        user_balance = user['balance'] if user else 0.0
        
        text = locale_manager.get_text('start_subscribed', language, 
            trx_price=price_text,
            user_balance=user_balance
        )
        
        image_path = get_main_menu_image(language)
        await safe_edit_or_send_photo(
            callback.bot,
            callback.message.chat.id,
            callback.message.message_id,
            text,
            image_path,
            get_main_menu_keyboard(language, callback.from_user.id)
        )


def register_language_handlers(dp: Dispatcher):
    dp.register_callback_query_handler(callback_set_language, text_startswith='set_language_', state='*')