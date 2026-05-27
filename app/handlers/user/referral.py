from aiogram import types, Dispatcher
from app.models.database import db
from app.locales import locale_manager
from app.keyboards.user import get_referral_keyboard, get_about_keyboard
from app.utils.helpers import check_subscription, get_or_create_first_message, get_referral_link, safe_edit_or_send_message


async def safe_callback_answer(callback: types.CallbackQuery, text: str = None, show_alert: bool = False):
    try:
        await callback.answer(text, show_alert=show_alert)
    except Exception as e:
        print(f"Ошибка при ответе на callback: {e}")


async def get_user_locale(user_id: int) -> str:
    return await db.get_user_language(user_id)


async def callback_referral(callback: types.CallbackQuery):
    if not await check_subscription(callback.bot, callback.from_user.id):
        locale = await get_user_locale(callback.from_user.id)
        await safe_callback_answer(callback, locale_manager.get_text('not_subscribed', locale), show_alert=True)
        return
    
    locale = await get_user_locale(callback.from_user.id)
    user_id = callback.from_user.id
    bot_info = await callback.bot.get_me()
    ref_link = get_referral_link(bot_info.username, user_id)
    
    ref_count = await db.get_referrals_count(user_id)
    ref_earnings = await db.get_referral_earnings(user_id)
    level_stats = await db.get_referral_levels_stats(user_id)
    
    custom_ref_percent = await db.get_user_ref_percent(user_id)
    if custom_ref_percent is not None:
        ref_percent = custom_ref_percent
    else:
        ref_percent = await db.get_global_referral_percent()
    
    text = locale_manager.get_text('referral', locale,
        ref_percent=ref_percent,
        referrals_count=ref_count,
        referral_earnings=ref_earnings,
        referral_link=ref_link
    )
    text += (
        "\n\n📊 Уровни рефералки:\n"
        f"• L1: {ref_percent:.2f}% (факт: {level_stats['level1']:.2f} TRX)\n"
        f"• L2: 1.00% (факт: {level_stats['level2']:.2f} TRX)\n"
        f"• L3: 0.50% (факт: {level_stats['level3']:.2f} TRX)\n"
        f"• Итого по уровням: {level_stats['total']:.2f} TRX"
    )
    
    await safe_edit_or_send_message(
        callback.bot,
        callback.message.chat.id,
        callback.message.message_id,
        text,
        get_referral_keyboard(bot_info.username, user_id, locale)
    )
    
    await safe_callback_answer(callback)


async def callback_about(callback: types.CallbackQuery):
    if not await check_subscription(callback.bot, callback.from_user.id):
        locale = await get_user_locale(callback.from_user.id)
        await safe_callback_answer(callback, locale_manager.get_text('not_subscribed', locale), show_alert=True)
        return
    
    locale = await get_user_locale(callback.from_user.id)
    
    await safe_edit_or_send_message(
        callback.bot,
        callback.message.chat.id,
        callback.message.message_id,
        locale_manager.get_text('about', locale),
        get_about_keyboard(locale)
    )
    
    await safe_callback_answer(callback)


def register_referral_handlers(dp: Dispatcher):
    dp.register_callback_query_handler(callback_referral, text='referral', state='*')
    dp.register_callback_query_handler(callback_about, text='about', state='*')