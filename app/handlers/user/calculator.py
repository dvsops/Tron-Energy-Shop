from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from app.models.database import db
from app.locales import locale_manager
from app.keyboards.user import get_calculator_keyboard, get_energy_amount_keyboard, get_back_keyboard
from app.services.energy.quote_engine import build_user_quote
from app.utils.helpers import check_subscription, safe_edit_or_send_message


async def safe_callback_answer(callback: types.CallbackQuery, text: str = None, show_alert: bool = False):
    try:
        await callback.answer(text, show_alert=show_alert)
    except Exception as e:
        print(f"Ошибка при ответе на callback: {e}")


async def get_user_locale(user_id: int) -> str:
    return await db.get_user_language(user_id)


async def callback_calculator(callback: types.CallbackQuery):
    if not await check_subscription(callback.bot, callback.from_user.id):
        locale = await get_user_locale(callback.from_user.id)
        await safe_callback_answer(callback, locale_manager.get_text('not_subscribed', locale), show_alert=True)
        return
    
    locale = await get_user_locale(callback.from_user.id)
    
    text = locale_manager.get_text('calculator', locale)
    
    await safe_edit_or_send_message(
        callback.bot,
        callback.message.chat.id,
        callback.message.message_id,
        text,
        get_calculator_keyboard(locale)
    )
    await safe_callback_answer(callback)


async def callback_calc_energy(callback: types.CallbackQuery):
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
        get_energy_amount_keyboard(period, locale)
    )
    await safe_callback_answer(callback)


async def callback_calc_energy_amount(callback: types.CallbackQuery):
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
        period_name = locale_manager.get_text(f'energy_{period}', locale)

        text = f"""
🧮 Результат расчета

⚡️ Энергия: {amount:,}
📅 Период: {period_name}
💳 Скидка подписки: -{pricing['subscription_discount_amount_trx']:.4f} TRX
💰 Итого к оплате: {pricing['final_price_trx']:.4f} TRX
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
        get_back_keyboard('calculator', locale)
    )
    await safe_callback_answer(callback)


async def callback_custom_energy(callback: types.CallbackQuery, state: FSMContext):
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
        get_back_keyboard('calculator', locale)
    )
    
    await state.update_data(period=period)
    await state.set_state('waiting_for_custom_energy')
    await safe_callback_answer(callback)


async def process_custom_energy_input(message: types.Message, state: FSMContext):
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
            period_name = locale_manager.get_text(f'energy_{period}', locale)

            text = f"""
🧮 Результат расчета

⚡️ Энергия: {energy:,}
📅 Период: {period_name}
💳 Скидка подписки: -{pricing['subscription_discount_amount_trx']:.4f} TRX
💰 Итого к оплате: {pricing['final_price_trx']:.4f} TRX
"""
        except Exception as e:
            print(f"❌ Ошибка при получении данных от API: {e}")
            period_name = locale_manager.get_text(f'energy_{period}', locale)
            text = f"❌ Ошибка получения данных от API Trenergy\n\n⚡️ Энергия: {energy:,}\n📅 Период: {period_name}\n\nПопробуйте позже или обратитесь в поддержку."
        
        try:
            await message.delete()
        except:
            pass
        
        await message.answer(
            text,
            reply_markup=get_back_keyboard('calculator', locale)
        )
        
    except ValueError:
        await message.answer("❌ Неверный формат числа. Введите целое число (например: 100000)")
        return
    except Exception as e:
        print(f"Ошибка при обработке ввода энергии: {e}")
        await message.answer("❌ Произошла ошибка. Попробуйте снова.")
    
    await state.finish()


def register_calculator_handlers(dp: Dispatcher):
    dp.register_callback_query_handler(callback_calculator, text='calculator', state='*')
    dp.register_callback_query_handler(callback_calc_energy, text='calc_energy_15min', state='*')
    dp.register_callback_query_handler(callback_calc_energy, text='calc_energy_1hour', state='*')
    dp.register_callback_query_handler(callback_calc_energy, text='calc_energy_24hours', state='*')
    dp.register_callback_query_handler(callback_calc_energy_amount, text_startswith='calc_energy_15min_', state='*')
    dp.register_callback_query_handler(callback_calc_energy_amount, text_startswith='calc_energy_1hour_', state='*')
    dp.register_callback_query_handler(callback_calc_energy_amount, text_startswith='calc_energy_24hours_', state='*')
    dp.register_callback_query_handler(callback_custom_energy, text_startswith='custom_energy_', state='*')
    dp.register_message_handler(process_custom_energy_input, state='waiting_for_custom_energy')