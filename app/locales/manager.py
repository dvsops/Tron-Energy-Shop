import json
import os
from typing import Dict, Any

class LocaleManager:
    def __init__(self):
        self.locales = {}
        self.default_locale = 'ru'
        self.load_locales()
    
    def load_locales(self):
        ru_texts = {
            'start_not_subscribed': '''
👋 Добро пожаловать в ShopEnergy!

Для использования бота необходимо подписаться на наш канал:
''',
            'start_subscribed': '''
✅ Добро пожаловать в ShopEnergy!

💹 Курс TRX: ${trx_price} USD

💰 Ваш баланс: {user_balance:.2f} TRX

Выберите нужный раздел:
''',
            'not_subscribed': '''
❌ Для использования бота необходимо подписаться на наш канал!
''',
            'profile': '''
👤 Ваш профиль

🆔 ID: `{user_id}`
💰 Баланс: {balance} TRX
🔗 TRX кошелек: `{wallet}`
📊 Всего покупок: {purchases_count}
''',
            'calculator': '''
🧮 Калькулятор энергии

Выберите параметры для расчета:
''',
            'purchase': '''
🛒 Покупка энергии

Выберите период аренды:
''',
            'purchase_energy_selection': '''
⚡ Выберите количество энергии

Период: {period}
''',
            'purchase_custom_energy': '''
✏️ Введите количество энергии

Период: {period}
Минимум: {min_energy:,} энергии

Введите число:
''',
            'purchase_wallet_selection': '''
💳 Выберите кошелек для оплаты

Энергия: {energy:,}
Период: {period}
Стоимость: {price} TRX
Транзакций: {transactions}
''',
            'purchase_enter_wallet': '''
✏️ Введите адрес TRX кошелька

Энергия: {energy:,}
Период: {period}
Стоимость: {price} TRX
Транзакций: {transactions}

Отправьте адрес кошелька:
''',
            'purchase_confirmation': '''
✅ Подтверждение покупки

⚡ Энергия: {energy:,}
📅 Период: {period}
💰 Стоимость: {price} TRX
🔄 Транзакций: {transactions}
💳 Кошелек: {wallet}

Баланс кошелька: {balance} TRX

Подтвердите покупку:
''',
            'purchase_processing': '''
⏳ Обработка покупки...

Пожалуйста, подождите...
''',
            'history': '''
📊 История покупок

{history_text}
''',
            'about': '''
ℹ️ О ShopEnergy

ShopEnergy - это сервис для аренды энергии в сети TRON.

🔹 Мы предоставляем энергию для транзакций TRON
🔹 Быстрая активация после оплаты
🔹 Конкурентные цены
🔹 Надежный сервис

💡 Энергия используется для оплаты комиссий за транзакции в сети TRON, что позволяет экономить на комиссиях.

📞 Поддержка: @support
''',
            'referral': '''
🤝 Реферальная программа

💰 Ваш реферальный процент: {ref_percent}%
👥 Приглашено пользователей: {referrals_count}
💵 Заработано с рефералов: {referral_earnings:.2f} TRX

🔗 Ваша реферальная ссылка:
`{referral_link}`

💡 Приглашайте друзей и получайте {ref_percent}% от их пополнений!
''',
            'deposit_notification': '''
💰 Пополнение баланса!

💳 Сумма: {amount:.2f} TRX
💰 Текущий баланс: {balance:.2f} TRX

Спасибо за использование нашего сервиса!
''',
            'referral_bonus': '''
🎉 Реферальный бонус!

💰 Сумма: {amount:.2f} TRX
👤 От пользователя: {user_id}
💳 Сумма пополнения: {deposit_amount:.2f} TRX

Продолжайте приглашать друзей!
''',
            'subscribe_to_channel': 'Подписаться на канал',
            'check_subscription': 'Проверить подписку',
            'profile_menu': 'Профиль',
            'calculator_menu': 'Калькулятор',
            'purchase_menu': 'Покупка',
            'about_menu': 'О боте',
            'referral_menu': 'Рефералы',
            'wholesale_menu': 'Опт',
            'support_menu': 'Поддержка',
            'balance': 'Баланс',
            'wallet': 'Кошелек',
            'purchase_history': 'История',
            'change_language': 'Язык',
            'back': 'Назад',
            'energy_15min': '15 минут',
            'energy_1hour': '1 час',
            'energy_24hours': '24 часа',
            'custom_amount': 'Свое количество',
            'confirm_purchase': 'Подтвердить',
            'cancel': 'Отмена',
            'share_referral': 'Поделиться ссылкой',
            'referral_message': 'Присоединяйся к ShopEnergy!'
        }
        
        en_texts = {
            'start_not_subscribed': '''
👋 Welcome to ShopEnergy!

To use the bot, you need to subscribe to our channel:
''',
            'start_subscribed': '''
✅ Welcome to ShopEnergy!

💹 TRX Rate: ${trx_price} USD

💰 Your balance: {user_balance:.2f} TRX

Choose the section you need:
''',
            'not_subscribed': '''
❌ To use the bot, you need to subscribe to our channel!
''',
            'profile': '''
👤 Your profile

🆔 ID: `{user_id}`
💰 Balance: {balance} TRX
🔗 TRX wallet: `{wallet}`
📊 Total purchases: {purchases_count}
''',
            'calculator': '''
🧮 Energy calculator

Choose parameters for calculation:
''',
            'purchase': '''
🛒 Energy purchase

Choose rental period:
''',
            'purchase_energy_selection': '''
⚡ Choose energy amount

Period: {period}
''',
            'purchase_custom_energy': '''
✏️ Enter energy amount

Period: {period}
Minimum: {min_energy:,} energy

Enter number:
''',
            'purchase_wallet_selection': '''
💳 Choose payment wallet

Energy: {energy:,}
Period: {period}
Cost: {price} TRX
Transactions: {transactions}
''',
            'purchase_enter_wallet': '''
✏️ Enter TRX wallet address

Energy: {energy:,}
Period: {period}
Cost: {price} TRX
Transactions: {transactions}

Send wallet address:
''',
            'purchase_confirmation': '''
✅ Purchase confirmation

⚡ Energy: {energy:,}
📅 Period: {period}
💰 Cost: {price} TRX
🔄 Transactions: {transactions}
💳 Wallet: {wallet}

Wallet balance: {balance} TRX

Confirm purchase:
''',
            'purchase_processing': '''
⏳ Processing purchase...

Please wait...
''',
            'history': '''
📊 Purchase history

{history_text}
''',
            'about': '''
ℹ️ About ShopEnergy

ShopEnergy is a service for renting energy in the TRON network.

🔹 We provide energy for TRON transactions
🔹 Fast activation after payment
🔹 Competitive prices
🔹 Reliable service

💡 Energy is used to pay transaction fees in the TRON network, allowing you to save on fees.

📞 Support: @support
''',
            'referral': '''
🤝 Referral program

💰 Your referral percentage: {ref_percent}%
👥 Invited users: {referrals_count}
💵 Earned from referrals: {referral_earnings:.2f} TRX

🔗 Your referral link:
`{referral_link}`

💡 Invite friends and get {ref_percent}% from their deposits!
''',
            'deposit_notification': '''
💰 Balance top-up!

💳 Amount: {amount:.2f} TRX
💰 Current balance: {balance:.2f} TRX

Thank you for using our service!
''',
            'referral_bonus': '''
🎉 Referral bonus!

💰 Amount: {amount:.2f} TRX
👤 From user: {user_id}
💳 Deposit amount: {deposit_amount:.2f} TRX

Keep inviting friends!
''',
            'subscribe_to_channel': 'Subscribe to channel',
            'check_subscription': 'Check subscription',
            'profile_menu': 'Profile',
            'calculator_menu': 'Calculator',
            'purchase_menu': 'Purchase',
            'about_menu': 'About',
            'referral_menu': 'Referrals',
            'wholesale_menu': 'Wholesale',
            'support_menu': 'Support',
            'balance': 'Balance',
            'wallet': 'Wallet',
            'purchase_history': 'History',
            'change_language': 'Language',
            'back': 'Back',
            'energy_15min': '15 minutes',
            'energy_1hour': '1 hour',
            'energy_24hours': '24 hours',
            'custom_amount': 'Custom amount',
            'confirm_purchase': 'Confirm',
            'cancel': 'Cancel',
            'share_referral': 'Share link',
            'referral_message': 'Join ShopEnergy!'
        }
        
        self.locales = {
            'ru': ru_texts,
            'en': en_texts
        }
    
    def get_text(self, key: str, locale: str = None, **kwargs) -> str:
        if locale is None:
            locale = self.default_locale
        
        if locale not in self.locales:
            locale = self.default_locale
        
        text = self.locales[locale].get(key, self.locales[self.default_locale].get(key, key))
        
        try:
            return text.format(**kwargs)
        except (KeyError, ValueError):
            return text


locale_manager = LocaleManager()
