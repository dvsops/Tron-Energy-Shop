from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from app.models.database import db
from app.locales import locale_manager
from app.keyboards.user import get_purchase_keyboard, get_purchase_amount_keyboard, get_confirm_purchase_keyboard, get_back_keyboard
from app.services.energy.marketplace import marketplace
from app.services.energy.quote_engine import build_user_quote
from app.services.api.tron import tron_manager
from app.utils.helpers import check_subscription, get_or_create_first_message, validate_trx_address, safe_edit_or_send_message


async def safe_callback_answer(callback: types.CallbackQuery, text: str = None, show_alert: bool = False):
    try:
        await callback.answer(text, show_alert=show_alert)
    except Exception as e:
        print(f"Ошибка при ответе на callback: {e}")


async def get_user_locale(user_id: int) -> str:
    return await db.get_user_language(user_id)


async def callback_purchase(callback: types.CallbackQuery):
    if not await check_subscription(callback.bot, callback.from_user.id):
        locale = await get_user_locale(callback.from_user.id)
        await safe_callback_answer(callback, locale_manager.get_text('not_subscribed', locale), show_alert=True)
        return
    
    locale = await get_user_locale(callback.from_user.id)
    
    await safe_edit_or_send_message(
        callback.bot,
        callback.message.chat.id,
        callback.message.message_id,
        locale_manager.get_text('purchase', locale),
        get_purchase_keyboard(locale)
    )
    
    await safe_callback_answer(callback)


async def callback_purchase_energy(callback: types.CallbackQuery):
    if not await check_subscription(callback.bot, callback.from_user.id):
        locale = await get_user_locale(callback.from_user.id)
        await safe_callback_answer(callback, locale_manager.get_text('not_subscribed', locale), show_alert=True)
        return
    
    locale = await get_user_locale(callback.from_user.id)
    period = callback.data.split('_')[-1]
    
    text = locale_manager.get_text('purchase_energy_selection', locale, period=period)
    
    await safe_edit_or_send_message(
        callback.bot,
        callback.message.chat.id,
        callback.message.message_id,
        text,
        get_purchase_amount_keyboard(period, locale)
    )
    await safe_callback_answer(callback)


async def callback_purchase_energy_amount(callback: types.CallbackQuery):
    if not await check_subscription(callback.bot, callback.from_user.id):
        locale = await get_user_locale(callback.from_user.id)
        await safe_callback_answer(callback, locale_manager.get_text('not_subscribed', locale), show_alert=True)
        return
    
    locale = await get_user_locale(callback.from_user.id)
    parts = callback.data.split('_')
    period = parts[2]
    amount = int(parts[3])
    
    try:
        pricing = await build_user_quote(callback.from_user.id, amount, period)
        price = pricing['final_price_trx']
        period_name = locale_manager.get_text(f'energy_{period}', locale)

        text = f"""
🛒 Покупка энергии

⚡️ Энергия: {amount:,}
📅 Период: {period_name}
💳 Скидка подписки: -{pricing['subscription_discount_amount_trx']:.4f} TRX
💰 Итого к оплате: {price:.4f} TRX

Выберите кошелек для оплаты:
"""
    except Exception as e:
        print(f"❌ Ошибка при получении данных от API: {e}")
        period_name = locale_manager.get_text(f'energy_{period}', locale)
        text = f"❌ Ошибка получения данных от API Trenergy\n\n⚡️ Энергия: {amount:,}\n📅 Период: {period_name}\n\nПопробуйте позже или обратитесь в поддержку."
    
    await safe_edit_or_send_message(
        callback.bot,
        callback.message.chat.id,
        callback.message.message_id,
        text,
        get_confirm_purchase_keyboard(period, amount, locale)
    )
    await safe_callback_answer(callback)


async def callback_custom_purchase(callback: types.CallbackQuery, state: FSMContext):
    if not await check_subscription(callback.bot, callback.from_user.id):
        locale = await get_user_locale(callback.from_user.id)
        await safe_callback_answer(callback, locale_manager.get_text('not_subscribed', locale), show_alert=True)
        return
    
    locale = await get_user_locale(callback.from_user.id)
    period = callback.data.split('_')[-1]
    
    min_energy = 60000 if period == '15min' else 30000
    period_name = locale_manager.get_text(f'energy_{period}', locale)
    
    text = locale_manager.get_text('purchase_custom_energy', locale, 
        period=period_name,
        min_energy=min_energy
    )
    
    await safe_edit_or_send_message(
        callback.bot,
        callback.message.chat.id,
        callback.message.message_id,
        text,
        get_back_keyboard('purchase', locale)
    )
    
    await state.update_data(period=period)
    await state.set_state('waiting_for_purchase_custom_energy')
    await safe_callback_answer(callback)


async def process_purchase_custom_energy_input(message: types.Message, state: FSMContext):
    locale = await get_user_locale(message.from_user.id)
    
    try:
        energy_text = message.text.strip().replace(',', '').replace(' ', '')
        energy = int(energy_text)
        
        data = await state.get_data()
        period = data.get('period')
        
        if not period:
            await message.answer("❌ Ошибка: период не найден. Попробуйте снова.")
            await state.finish()
            return
        
        min_energy = 60000 if period == '15min' else 30000
        
        if energy < min_energy:
            period_name = locale_manager.get_text(f'energy_{period}', locale)
            await message.answer(f"❌ Минимальное количество энергии для {period_name}: {min_energy:,}")
            return
        
        try:
            pricing = await build_user_quote(message.from_user.id, energy, period)
            price = pricing['final_price_trx']
            period_name = locale_manager.get_text(f'energy_{period}', locale)

            text = f"""
🛒 Покупка энергии

⚡️ Энергия: {energy:,}
📅 Период: {period_name}
💳 Скидка подписки: -{pricing['subscription_discount_amount_trx']:.4f} TRX
💰 Итого к оплате: {price:.4f} TRX

Выберите кошелек для оплаты:
"""
        except Exception as e:
            print(f"❌ Ошибка при получении данных от API: {e}")
            period_name = locale_manager.get_text(f'energy_{period}', locale)
            text = f"❌ Ошибка получения данных от API Trenergy\n\n⚡️ Энергия: {energy:,}\n📅 Период: {period_name}\n\nПопробуйте позже или обратитесь в поддержку."
        
        try:
            await message.delete()
        except:
            pass
        
        await get_or_create_first_message(
            message.bot,
            message.from_user.id,
            message.chat.id,
            text,
            get_back_keyboard('purchase', locale)
        )
        
    except ValueError:
        await message.answer("❌ Неверный формат числа. Введите целое число (например: 100000)")
        return
    except Exception as e:
        print(f"Ошибка при обработке ввода энергии: {e}")
        await message.answer("❌ Произошла ошибка. Попробуйте снова.")
    
    await state.finish()


async def callback_confirm_purchase(callback: types.CallbackQuery, state: FSMContext):
    if not await check_subscription(callback.bot, callback.from_user.id):
        locale = await get_user_locale(callback.from_user.id)
        await safe_callback_answer(callback, locale_manager.get_text('not_subscribed', locale), show_alert=True)
        return
    
    locale = await get_user_locale(callback.from_user.id)
    parts = callback.data.split('_')
    period = parts[2]
    amount = int(parts[3])
    
    try:
        pricing = await build_user_quote(callback.from_user.id, amount, period)
        quote = pricing['quote']
        price = pricing['final_price_trx']
        period_name = locale_manager.get_text(f'energy_{period}', locale)

        user = await db.get_user(callback.from_user.id)
        balance = user['balance'] if user else 0.0

        if not user or not user.get('trx_wallet'):
            text = "❌ Сначала укажите TRX-кошелек в профиле."
            await safe_callback_answer(callback, text, show_alert=True)
            return

        if balance < price:
            text = f"""
❌ Недостаточно средств

⚡️ Энергия: {amount:,}
📅 Период: {period_name}
💰 Стоимость: {price:.2f} TRX
💳 Ваш баланс: {balance:.2f} TRX

Пополните баланс для совершения покупки.
"""
            await get_or_create_first_message(
                callback.bot,
                callback.from_user.id,
                callback.message.chat.id,
                text,
                get_back_keyboard('purchase', locale)
            )
            await safe_callback_answer(callback)
            return

        purchase_result = await marketplace.purchase_with_quote(
            quote, user['trx_wallet'], callback.from_user.id
        )

        if purchase_result['success']:
            await db.update_balance(callback.from_user.id, -price)
            await db.add_purchase(
                callback.from_user.id,
                amount,
                period_name,
                price,
                user['trx_wallet'],
                purchase_result['order_id'],
                provider=purchase_result.get('provider', 'unknown'),
                status='success'
            )
            await db.log_provider_order(
                callback.from_user.id,
                purchase_result.get('provider', 'unknown'),
                purchase_result.get('order_id'),
                amount,
                period,
                price,
                'success'
            )
            text = f"""
✅ Покупка успешно завершена!

⚡️ Энергия: {amount:,}
📅 Период: {period_name}
💳 Скидка подписки: -{pricing['subscription_discount_amount_trx']:.4f} TRX
💰 Итого: {price:.4f} TRX
🆔 ID заказа: {purchase_result['order_id']}

Энергия будет активирована в течение 5 минут.
"""
        else:
            await db.log_provider_order(
                callback.from_user.id,
                purchase_result.get('provider', 'unknown'),
                purchase_result.get('order_id'),
                amount,
                period,
                price,
                'failed'
            )
            text = f"""
❌ Ошибка при покупке

⚡️ Энергия: {amount:,}
📅 Период: {period_name}
💰 Стоимость: {price:.2f} TRX

Ошибка: {purchase_result.get('error', 'Неизвестная ошибка')}

Попробуйте позже или обратитесь в поддержку.
"""
    except Exception as e:
        print(f"❌ Ошибка при покупке энергии: {e}")
        text = "❌ Произошла ошибка при покупке. Попробуйте позже или обратитесь в поддержку."
    
    await get_or_create_first_message(
        callback.bot,
        callback.from_user.id,
        callback.message.chat.id,
        text,
        get_back_keyboard('main_menu', locale)
    )
    await safe_callback_answer(callback)


def register_purchase_handlers(dp: Dispatcher):
    dp.register_callback_query_handler(callback_purchase, text='purchase', state='*')
    dp.register_callback_query_handler(callback_purchase_energy_amount, text_startswith='purchase_energy_15min_', state='*')
    dp.register_callback_query_handler(callback_purchase_energy_amount, text_startswith='purchase_energy_1hour_', state='*')
    dp.register_callback_query_handler(callback_purchase_energy_amount, text_startswith='purchase_energy_24hours_', state='*')
    dp.register_callback_query_handler(callback_purchase_energy, text='purchase_energy_15min', state='*')
    dp.register_callback_query_handler(callback_purchase_energy, text='purchase_energy_1hour', state='*')
    dp.register_callback_query_handler(callback_purchase_energy, text='purchase_energy_24hours', state='*')
    dp.register_callback_query_handler(callback_custom_purchase, text_startswith='custom_purchase_', state='*')
    dp.register_callback_query_handler(callback_confirm_purchase, text_startswith='confirm_purchase_', state='*')
    dp.register_message_handler(process_purchase_custom_energy_input, state='waiting_for_purchase_custom_energy')