from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from app.models.database import db
from app.services.api.tron import tron_manager
from app.locales import locale_manager
from app.keyboards.user import get_language_keyboard, get_subscription_keyboard, get_main_menu_keyboard
from app.utils.helpers import check_subscription, get_trx_price, get_main_menu_image, get_or_create_first_message, safe_edit_or_send_message, safe_edit_or_send_photo


class UserStates(StatesGroup):
    waiting_for_wallet = State()
    waiting_for_custom_energy = State()
    waiting_for_purchase_custom_energy = State()
    waiting_for_purchase_wallet = State()
    waiting_for_purchase_confirmation = State()


async def get_user_locale(user_id: int) -> str:
    return await db.get_user_language(user_id)


async def safe_callback_answer(callback: types.CallbackQuery, text: str = None, show_alert: bool = False):
    try:
        await callback.answer(text, show_alert=show_alert)
    except Exception as e:
        print(f"Ошибка при ответе на callback: {e}")


async def check_sub_decorator(func):
    async def wrapper(callback: types.CallbackQuery, *args, **kwargs):
        try:
            if not await check_subscription(callback.bot, callback.from_user.id):
                locale = await get_user_locale(callback.from_user.id)
                await safe_callback_answer(callback, locale_manager.get_text('not_subscribed', locale), show_alert=True)
                return
            return await func(callback, *args, **kwargs)
        except Exception as e:
            print(f"Ошибка в декораторе check_sub_decorator: {e}")
            await safe_callback_answer(callback, "❌ Произошла ошибка", show_alert=True)
    return wrapper


async def cmd_start(message: types.Message, state: FSMContext):
    await state.finish()
    
    user_id = message.from_user.id
    
    referrer_id = None
    if message.get_args().startswith('ref_'):
        try:
            referrer_id = int(message.get_args().split('_')[1])
            if referrer_id == user_id:
                referrer_id = None
        except:
            pass
    
    is_new_user = not await db.user_exists(user_id)
    
    if is_new_user:
        await db.add_user(
            user_id=user_id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
            referrer_id=referrer_id
        )
        
        try:
            wallet = tron_manager.generate_wallet()
            await db.set_deposit_wallet(
                user_id,
                wallet['address'],
                wallet['private_key']
            )
            print(f"Создан депозитный кошелек для пользователя {user_id}")
        except Exception as e:
            print(f"Ошибка при создании депозитного кошелька: {e}")
        
        await message.answer(
            "🌍 Выберите язык / Choose language:",
            reply_markup=get_language_keyboard()
        )
        return
        
    
    locale = await get_user_locale(user_id)
    
    is_subscribed = await check_subscription(message.bot, user_id)
    
    if not is_subscribed:
        await message.answer(
            locale_manager.get_text('start_not_subscribed', locale),
            reply_markup=get_subscription_keyboard(locale)
        )
    else:
        trx_price = await get_trx_price()
        price_text = f"{trx_price:.4f}" if trx_price > 0 else "0.0000"
        
        user = await db.get_user(user_id)
        user_balance = user['balance'] if user else 0.0
        
        text = locale_manager.get_text('start_subscribed', locale, 
            trx_price=price_text,
            user_balance=user_balance
        )
        
        image_path = get_main_menu_image(locale)
        with open(image_path, 'rb') as photo:
            sent_message = await message.answer_photo(
                photo=photo,
                caption=text,
                reply_markup=get_main_menu_keyboard(locale, user_id)
            )
            await db.set_first_message(user_id, sent_message.message_id, sent_message.chat.id)


async def show_main_menu(callback: types.CallbackQuery, locale: str = 'ru'):
    trx_price = await get_trx_price()
    price_text = f"{trx_price:.4f}" if trx_price > 0 else "0.0000"
    
    user = await db.get_user(callback.from_user.id)
    user_balance = user['balance'] if user else 0.0
    
    text = locale_manager.get_text('start_subscribed', locale, 
        trx_price=price_text,
        user_balance=user_balance
    )
    
    image_path = get_main_menu_image(locale)
    await safe_edit_or_send_photo(
        callback.bot,
        callback.message.chat.id,
        callback.message.message_id,
        text,
        image_path,
        get_main_menu_keyboard(locale, callback.from_user.id)
    )


async def callback_check_subscription(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    locale = await get_user_locale(user_id)
    
    is_subscribed = await check_subscription(callback.bot, user_id)
    
    if is_subscribed:
        await show_main_menu(callback, locale)
        await safe_callback_answer(callback, "✅ Подписка подтверждена!")
    else:
        await safe_callback_answer(callback, locale_manager.get_text('not_subscribed', locale), show_alert=True)


async def callback_main_menu(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    locale = await get_user_locale(user_id)
    
    trx_price = await get_trx_price()
    price_text = f"{trx_price:.4f}" if trx_price > 0 else "0.0000"
    
    user = await db.get_user(user_id)
    user_balance = user['balance'] if user else 0.0
    
    text = locale_manager.get_text('start_subscribed', locale, 
        trx_price=price_text,
        user_balance=user_balance
    )
    
    image_path = get_main_menu_image(locale)
    await safe_edit_or_send_photo(
        callback.bot,
        callback.message.chat.id,
        callback.message.message_id,
        text,
        image_path,
        get_main_menu_keyboard(locale, user_id)
    )
    await safe_callback_answer(callback)


def register_start_handlers(dp: Dispatcher):
    dp.register_message_handler(cmd_start, commands=['start'], state='*')
    dp.register_callback_query_handler(callback_check_subscription, text='check_subscription', state='*')
    dp.register_callback_query_handler(callback_main_menu, text='main_menu', state='*')