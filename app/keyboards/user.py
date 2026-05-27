from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from app.locales import locale_manager
from app.models.config import CHANNEL_LINK, WHOLESALE_LINK, SUPPORT_LINK, ADMIN_IDS


def get_subscription_keyboard(locale='ru'):
    keyboard = InlineKeyboardMarkup()
    keyboard.add(
        InlineKeyboardButton(text=f"📢 {locale_manager.get_text('subscribe_to_channel', locale)}", url=CHANNEL_LINK or "https://t.me/shopenergy")
    )
    keyboard.add(
        InlineKeyboardButton(text=f"✅ {locale_manager.get_text('check_subscription', locale)}", callback_data="check_subscription")
    )
    return keyboard


def get_main_menu_keyboard(locale='ru', user_id=None):
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton(text=f"👤 {locale_manager.get_text('profile_menu', locale)}", callback_data="profile"),
        InlineKeyboardButton(text=f"🧮 {locale_manager.get_text('calculator_menu', locale)}", callback_data="calculator"),
    )
    keyboard.add(
        InlineKeyboardButton(text=f"🛒 {locale_manager.get_text('purchase_menu', locale)}", callback_data="purchase"),
        InlineKeyboardButton(text=f"ℹ️ {locale_manager.get_text('about_menu', locale)}", callback_data="about"),
    )
    keyboard.add(
        InlineKeyboardButton(text=f"🤝 {locale_manager.get_text('referral_menu', locale)}", callback_data="referral"),
    )
    keyboard.add(
        InlineKeyboardButton(text=f"📦 {locale_manager.get_text('wholesale_menu', locale)}", url=WHOLESALE_LINK),
        InlineKeyboardButton(text=f"🆘 {locale_manager.get_text('support_menu', locale)}", url=SUPPORT_LINK),
    )
    
    if user_id and user_id in ADMIN_IDS:
        keyboard.add(
            InlineKeyboardButton(text="🔐 Админ-панель", callback_data="admin_panel"),
        )
    
    return keyboard


def get_profile_keyboard(locale='ru'):
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton(text=f"💰 {locale_manager.get_text('balance', locale)}", callback_data="top_up"),
        InlineKeyboardButton(text=f"🔗 {locale_manager.get_text('wallet', locale)}", callback_data="set_wallet"),
    )
    keyboard.add(
        InlineKeyboardButton(text="🤖 Автопокупка энергии", callback_data="smart_menu"),
    )
    keyboard.add(
        InlineKeyboardButton(text=f"📊 {locale_manager.get_text('purchase_history', locale)}", callback_data="purchase_history"),
        InlineKeyboardButton(text=f"🔙 {locale_manager.get_text('back', locale)}", callback_data="main_menu"),
    )
    return keyboard


def get_calculator_keyboard(locale='ru'):
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton(text=f"⚡ {locale_manager.get_text('energy_15min', locale)}", callback_data="calc_energy_15min"),
        InlineKeyboardButton(text=f"⚡ {locale_manager.get_text('energy_1hour', locale)}", callback_data="calc_energy_1hour"),
    )
    keyboard.add(
        InlineKeyboardButton(text=f"⚡ {locale_manager.get_text('energy_24hours', locale)}", callback_data="calc_energy_24hours"),
        InlineKeyboardButton(text=f"🔙 {locale_manager.get_text('back', locale)}", callback_data="main_menu"),
    )
    return keyboard


def get_purchase_keyboard(locale='ru'):
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton(text=f"⚡ {locale_manager.get_text('energy_15min', locale)}", callback_data="purchase_energy_15min"),
        InlineKeyboardButton(text=f"⚡ {locale_manager.get_text('energy_1hour', locale)}", callback_data="purchase_energy_1hour"),
    )
    keyboard.add(
        InlineKeyboardButton(text=f"⚡ {locale_manager.get_text('energy_24hours', locale)}", callback_data="purchase_energy_24hours"),
        InlineKeyboardButton(text=f"🔙 {locale_manager.get_text('back', locale)}", callback_data="main_menu"),
    )
    return keyboard


def get_energy_amount_keyboard(period_id, locale='ru'):
    keyboard = InlineKeyboardMarkup(row_width=2)
    
    if period_id == '15min':
        amounts = [60000, 100000, 150000]
    elif period_id == '1hour':
        amounts = [30000, 50000, 100000]
    else:
        amounts = [30000, 50000, 100000, 131000]
    
    for amount in amounts:
        keyboard.add(
            InlineKeyboardButton(
                text=f"⚡ {amount:,} энергии",
                callback_data=f"calc_energy_{period_id}_{amount}"
            )
        )
    
    keyboard.add(
        InlineKeyboardButton(text=f"✏️ {locale_manager.get_text('custom_amount', locale)}", callback_data=f"custom_energy_{period_id}"),
        InlineKeyboardButton(text=f"🔙 {locale_manager.get_text('back', locale)}", callback_data="calculator"),
    )
    
    return keyboard


def get_purchase_amount_keyboard(period_id, locale='ru'):
    keyboard = InlineKeyboardMarkup(row_width=2)
    
    if period_id == '15min':
        amounts = [60000, 100000, 150000]
    elif period_id == '1hour':
        amounts = [30000, 50000, 100000]
    else:
        amounts = [30000, 50000, 100000, 131000]
    
    for amount in amounts:
        keyboard.add(
            InlineKeyboardButton(
                text=f"⚡ {amount:,} энергии",
                callback_data=f"purchase_energy_{period_id}_{amount}"
            )
        )
    
    keyboard.add(
        InlineKeyboardButton(text=f"✏️ {locale_manager.get_text('custom_amount', locale)}", callback_data=f"custom_purchase_{period_id}"),
        InlineKeyboardButton(text=f"🔙 {locale_manager.get_text('back', locale)}", callback_data="purchase"),
    )
    
    return keyboard


def get_language_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton(text="🇷🇺 Русский", callback_data="set_language_ru"),
        InlineKeyboardButton(text="🇺🇸 English", callback_data="set_language_en"),
    )
    return keyboard


def get_back_keyboard(callback_data="main_menu", locale='ru'):
    keyboard = InlineKeyboardMarkup()
    keyboard.add(
        InlineKeyboardButton(text=f"🔙 {locale_manager.get_text('back', locale)}", callback_data=callback_data)
    )
    return keyboard


def get_confirm_purchase_keyboard(period_id, amount, locale='ru'):
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton(text=f"✅ {locale_manager.get_text('confirm_purchase', locale)}", callback_data=f"confirm_purchase_{period_id}_{amount}"),
        InlineKeyboardButton(text=f"❌ {locale_manager.get_text('cancel', locale)}", callback_data="purchase"),
    )
    return keyboard


def get_referral_keyboard(bot_username, user_id, locale='ru'):
    keyboard = InlineKeyboardMarkup()
    keyboard.add(
        InlineKeyboardButton(
            text=f"📤 {locale_manager.get_text('share_referral', locale)}",
            url=f"https://t.me/share/url?url=https://t.me/{bot_username}?start=ref_{user_id}&text={locale_manager.get_text('referral_message', locale)}"
        )
    )
    keyboard.add(
        InlineKeyboardButton(text=f"🔙 {locale_manager.get_text('back', locale)}", callback_data="main_menu")
    )
    return keyboard


def get_about_keyboard(locale='ru'):
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(InlineKeyboardButton(text=f"🔙 {locale_manager.get_text('back', locale)}", callback_data="main_menu"))
    return keyboard


def get_smart_menu_keyboard(settings: dict):
    keyboard = InlineKeyboardMarkup(row_width=2)
    enabled = bool(settings.get("enabled", False))
    current_target = int(settings.get("target_energy_amount", 30000) or 30000)
    current_period = str(settings.get("period_id", "24hours"))
    current_trigger = int(settings.get("min_energy_trigger", 10000) or 10000)
    current_threshold = float(settings.get("price_threshold_trx", 1.0) or 1.0)

    def mark(is_selected: bool, text: str) -> str:
        return f"✅ {text}" if is_selected else text

    keyboard.add(
        InlineKeyboardButton(
            text=f"Автопокупка: {'ON ✅' if enabled else 'OFF ❌'}",
            callback_data="smart_toggle"
        ),
    )
    keyboard.add(
        InlineKeyboardButton(text=mark(current_target == 30000, "Объем 30k"), callback_data="smart_target_30000"),
        InlineKeyboardButton(text=mark(current_target == 100000, "Объем 100k"), callback_data="smart_target_100000"),
    )
    keyboard.add(
        InlineKeyboardButton(text=mark(current_target == 300000, "Объем 300k"), callback_data="smart_target_300000"),
        InlineKeyboardButton(text=mark(current_target == 500000, "Объем 500k"), callback_data="smart_target_500000"),
    )
    keyboard.add(
        InlineKeyboardButton(text=mark(current_period == "1hour", "Период 1ч"), callback_data="smart_period_1hour"),
        InlineKeyboardButton(text=mark(current_period == "24hours", "Период 24ч"), callback_data="smart_period_24hours"),
    )
    keyboard.add(
        InlineKeyboardButton(text=mark(current_trigger == 10000, "Запуск 10k"), callback_data="smart_trigger_10000"),
        InlineKeyboardButton(text=mark(current_trigger == 30000, "Запуск 30k"), callback_data="smart_trigger_30000"),
    )
    keyboard.add(
        InlineKeyboardButton(text=mark(current_trigger == 50000, "Запуск 50k"), callback_data="smart_trigger_50000"),
    )
    keyboard.add(
        InlineKeyboardButton(text=mark(abs(current_threshold - 0.5) < 1e-9, "Макс 0.5 TRX"), callback_data="smart_threshold_0.5"),
        InlineKeyboardButton(text=mark(abs(current_threshold - 1.0) < 1e-9, "Макс 1.0 TRX"), callback_data="smart_threshold_1.0"),
    )
    keyboard.add(
        InlineKeyboardButton(text=mark(abs(current_threshold - 2.0) < 1e-9, "Макс 2.0 TRX"), callback_data="smart_threshold_2.0"),
    )
    is_custom_threshold = not (
        abs(current_threshold - 0.5) < 1e-9
        or abs(current_threshold - 1.0) < 1e-9
        or abs(current_threshold - 2.0) < 1e-9
    )
    custom_label = (
        f"Свой лимит: {current_threshold:.4f} TRX"
        if is_custom_threshold
        else "Свой лимит цены"
    )
    keyboard.add(
        InlineKeyboardButton(text=mark(is_custom_threshold, custom_label), callback_data="smart_threshold_custom"),
    )
    keyboard.add(
        InlineKeyboardButton(text="🔙 Назад", callback_data="profile")
    )
    return keyboard

