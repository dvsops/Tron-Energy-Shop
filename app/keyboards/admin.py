from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_admin_menu_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats"),
        InlineKeyboardButton(text="📨 Рассылка", callback_data="admin_broadcast"),
    )
    keyboard.add(
        InlineKeyboardButton(text="🔍 Поиск пользователя", callback_data="admin_find_user"),
        InlineKeyboardButton(text="💰 Реф. процент", callback_data="admin_ref_percent"),
    )
    keyboard.add(
        InlineKeyboardButton(text="📈 Маржа", callback_data="admin_margin"),
        InlineKeyboardButton(text="🔐 Настройки кошелька", callback_data="admin_wallet_settings"),
    )
    keyboard.add(
        InlineKeyboardButton(text="💸 Массовый перевод", callback_data="admin_mass_transfer"),
        InlineKeyboardButton(text="🔄 Сброс отслеживания", callback_data="admin_reset_tracking"),
    )
    keyboard.add(
        InlineKeyboardButton(text="⚡ Настройки скорости", callback_data="admin_speed_settings"),
    )
    keyboard.add(
        InlineKeyboardButton(text="◀️ Закрыть", callback_data="admin_close")
    )
    return keyboard


def get_speed_settings_keyboard():
    keyboard = InlineKeyboardMarkup()
    keyboard.add(
        InlineKeyboardButton(text="🎯 Автонастройка", callback_data="admin_speed_auto"),
    )
    keyboard.add(
        InlineKeyboardButton(text="◀️ Назад", callback_data="admin_menu")
    )
    return keyboard


def get_admin_back_keyboard():
    keyboard = InlineKeyboardMarkup()
    keyboard.add(
        InlineKeyboardButton(text="◀️ Назад в админку", callback_data="admin_panel")
    )
    return keyboard


def get_broadcast_confirm_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton(text="✅ Отправить", callback_data="broadcast_confirm"),
        InlineKeyboardButton(text="❌ Отмена", callback_data="admin_panel"),
    )
    return keyboard


def get_margin_settings_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton(text="🌍 Глобальная маржа", callback_data="admin_global_margin"),
        InlineKeyboardButton(text="👤 Индивидуальная маржа", callback_data="admin_user_margin"),
    )
    keyboard.add(
        InlineKeyboardButton(text="◀️ Назад", callback_data="admin_panel")
    )
    return keyboard


def get_ref_percent_settings_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton(text="🌍 Глобальный процент", callback_data="admin_global_ref_percent"),
        InlineKeyboardButton(text="👤 Индивидуальный процент", callback_data="admin_user_ref_percent"),
    )
    keyboard.add(
        InlineKeyboardButton(text="◀️ Назад", callback_data="admin_panel")
    )
    return keyboard


def get_user_actions_keyboard(user_id):
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton(text="💰 Пополнить баланс", callback_data=f"admin_add_balance_{user_id}"),
        InlineKeyboardButton(text="💸 Снять с баланса", callback_data=f"admin_subtract_balance_{user_id}"),
    )
    keyboard.add(
        InlineKeyboardButton(text="📊 Статистика пользователя", callback_data=f"admin_user_stats_{user_id}"),
        InlineKeyboardButton(text="◀️ Назад", callback_data="admin_panel"),
    )
    return keyboard


def get_mass_transfer_keyboard():
    keyboard = InlineKeyboardMarkup()
    keyboard.add(
        InlineKeyboardButton(text="◀️ Назад", callback_data="admin_panel")
    )
    return keyboard


def get_reset_tracking_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton(text="✅ Сбросить", callback_data="admin_reset_confirm"),
        InlineKeyboardButton(text="❌ Отмена", callback_data="admin_panel"),
    )
    return keyboard

