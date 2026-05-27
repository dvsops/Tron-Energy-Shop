from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from app.models.database import db
from app.locales import locale_manager
from app.keyboards.user import get_profile_keyboard, get_language_keyboard, get_back_keyboard
from app.utils.helpers import check_subscription, get_or_create_first_message, safe_edit_or_send_message


async def safe_callback_answer(callback: types.CallbackQuery, text: str = None, show_alert: bool = False):
    try:
        await callback.answer(text, show_alert=show_alert)
    except Exception as e:
        print(f"Ошибка при ответе на callback: {e}")


async def get_user_locale(user_id: int) -> str:
    return await db.get_user_language(user_id)


async def callback_profile(callback: types.CallbackQuery):
    if not await check_subscription(callback.bot, callback.from_user.id):
        locale = await get_user_locale(callback.from_user.id)
        await safe_callback_answer(callback, locale_manager.get_text('not_subscribed', locale), show_alert=True)
        return
    
    locale = await get_user_locale(callback.from_user.id)
    user = await db.get_user(callback.from_user.id)
    purchases_count = await db.get_purchases_count(callback.from_user.id)
    
    wallet = user['trx_wallet'] if user['trx_wallet'] else 'Не привязан'
    
    text = locale_manager.get_text('profile', locale,
        user_id=callback.from_user.id,
        balance=user['balance'],
        wallet=wallet,
        purchases_count=purchases_count
    )
    
    await safe_edit_or_send_message(
        callback.bot,
        callback.message.chat.id,
        callback.message.message_id,
        text,
        get_profile_keyboard(locale),
        'Markdown'
    )
    
    await safe_callback_answer(callback)


async def callback_change_language(callback: types.CallbackQuery):
    if not await check_subscription(callback.bot, callback.from_user.id):
        locale = await get_user_locale(callback.from_user.id)
        await safe_callback_answer(callback, locale_manager.get_text('not_subscribed', locale), show_alert=True)
        return
    
    await safe_edit_or_send_message(
        callback.bot,
        callback.message.chat.id,
        callback.message.message_id,
        "🌍 Выберите язык / Choose language:",
        get_language_keyboard()
    )
    await safe_callback_answer(callback)


async def callback_top_up(callback: types.CallbackQuery):
    if not await check_subscription(callback.bot, callback.from_user.id):
        locale = await get_user_locale(callback.from_user.id)
        await safe_callback_answer(callback, locale_manager.get_text('not_subscribed', locale), show_alert=True)
        return
    
    locale = await get_user_locale(callback.from_user.id)
    user = await db.get_user(callback.from_user.id)
    
    if not user or not user['deposit_wallet_address']:
        await safe_callback_answer(callback, "❌ Депозитный кошелек не найден", show_alert=True)
        return
    
    wallet_address = user['deposit_wallet_address']
    balance = user['balance']
    
    text = f"""
💰 Пополнение баланса

💳 Ваш депозитный адрес:
`{wallet_address}`

💰 Текущий баланс: {balance:.2f} TRX

📝 Отправьте TRX на указанный адрес для пополнения баланса.
Минимальная сумма пополнения: 10 TRX

⏰ Пополнения обрабатываются автоматически в течение 5 минут.
"""
    
    await safe_edit_or_send_message(
        callback.bot,
        callback.message.chat.id,
        callback.message.message_id,
        text,
        get_back_keyboard('profile', locale),
        'Markdown'
    )
    await safe_callback_answer(callback)


async def callback_set_wallet(callback: types.CallbackQuery, state: FSMContext):
    if not await check_subscription(callback.bot, callback.from_user.id):
        locale = await get_user_locale(callback.from_user.id)
        await safe_callback_answer(callback, locale_manager.get_text('not_subscribed', locale), show_alert=True)
        return
    
    locale = await get_user_locale(callback.from_user.id)
    
    text = """
🔗 Привязка TRX кошелька

📝 Отправьте адрес вашего TRX кошелька для привязки.

⚠️ Внимание: Убедитесь, что адрес корректный, так как на него будут отправляться покупки энергии.
"""
    
    await safe_edit_or_send_message(
        callback.bot,
        callback.message.chat.id,
        callback.message.message_id,
        text,
        get_back_keyboard('profile', locale)
    )
    
    await state.set_state('waiting_for_wallet')
    await safe_callback_answer(callback)


async def process_wallet_input(message: types.Message, state: FSMContext):
    locale = await get_user_locale(message.from_user.id)
    wallet_address = message.text.strip()
    
    from app.services.api.tron import tron_manager
    
    if not tron_manager.is_valid_address(wallet_address):
        await message.answer(
            "❌ Неверный формат адреса TRX кошелька.\n\nПопробуйте еще раз:",
            reply_markup=get_back_keyboard('profile', locale)
        )
        return
    
    await db.set_trx_wallet(message.from_user.id, wallet_address)
    
    await message.answer(
        f"✅ TRX кошелек успешно привязан!\n\n💳 Адрес: `{wallet_address}`",
        reply_markup=get_back_keyboard('profile', locale),
        parse_mode='Markdown'
    )
    
    await state.finish()


async def callback_purchase_history(callback: types.CallbackQuery):
    if not await check_subscription(callback.bot, callback.from_user.id):
        locale = await get_user_locale(callback.from_user.id)
        await safe_callback_answer(callback, locale_manager.get_text('not_subscribed', locale), show_alert=True)
        return
    
    locale = await get_user_locale(callback.from_user.id)
    
    purchases = await db.get_user_purchases(callback.from_user.id, limit=10)
    
    if not purchases:
        text = locale_manager.get_text('history', locale, history_text="У вас пока нет покупок.")
    else:
        history_text = ""
        for purchase in purchases:
            history_text += f"⚡️ {purchase['energy_amount']:,} энергии\n"
            history_text += f"📅 {purchase['period']}\n"
            history_text += f"💰 {purchase['price_trx']:.2f} TRX\n"
            history_text += f"📅 {purchase['created_at'][:10]}\n\n"
        
        text = locale_manager.get_text('history', locale, history_text=history_text.strip())
    
    await safe_edit_or_send_message(
        callback.bot,
        callback.message.chat.id,
        callback.message.message_id,
        text,
        get_back_keyboard('profile', locale)
    )
    await safe_callback_answer(callback)


def register_profile_handlers(dp: Dispatcher):
    dp.register_callback_query_handler(callback_profile, text='profile', state='*')
    dp.register_callback_query_handler(callback_change_language, text='change_language', state='*')
    dp.register_callback_query_handler(callback_top_up, text='top_up', state='*')
    dp.register_callback_query_handler(callback_set_wallet, text='set_wallet', state='*')
    dp.register_callback_query_handler(callback_purchase_history, text='purchase_history', state='*')
    dp.register_message_handler(process_wallet_input, state='waiting_for_wallet')