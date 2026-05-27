import asyncio
from datetime import datetime
from app.models.database import db
from app.services.api.tron import tron_manager
from app.locales import locale_manager
from app.models.config import MIN_DEPOSIT_AMOUNT, ADMIN_IDS
from tronpy.keys import to_base58check_address


def hex_to_base58(hex_address: str) -> str:
    if hex_address.startswith('41'):
        return to_base58check_address(hex_address)
    return hex_address


class BalanceChecker:
    def __init__(self, bot):
        self.bot = bot
        self.is_running = False
        self.current_user_index = 0
        self.api_error_count = 0
        self.last_problem_notification = 0
    
    async def check_all_wallets(self):
        try:
            users = await db.get_all_users_with_deposit_wallets()
            
            if not users:
                return
            
            user = users[self.current_user_index % len(users)]
            self.current_user_index += 1
            
            user_id = user['user_id']
            address = user['deposit_wallet_address']
            private_key = user['deposit_wallet_private_key']
            last_balance = user['last_checked_balance']
            referrer_id = user['referrer_id']
            last_checked_tx_timestamp = user.get('last_checked_tx_timestamp', 0)
            
            print(f"🔍 Проверяю пополнения кошелька {self.current_user_index}/{len(users)}: {address}")
            
            transactions, api_success = await tron_manager.get_transactions(address, limit=10)
            
            await db.increment_requests_today()
            
            if not api_success:
                print(f"⚠️ Ошибка API при получении транзакций для {address} - используем fallback через баланс")
                
                self.api_error_count += 1
                
                import time
                current_time = time.time()
                if (self.api_error_count >= 5 and 
                    current_time - self.last_problem_notification > 3600):
                    
                    await self._notify_admin_about_problem(
                        "Множественные ошибки API",
                        f"Ошибок API: {self.api_error_count}. Система переключилась на fallback-режим."
                    )
                    self.last_problem_notification = current_time
                
                current_balance = await tron_manager.get_balance(address)
                
                if last_balance == 0.0 and current_balance > 0:
                    await db.initialize_last_checked_balance(user_id, current_balance)
                    print(f"🔄 Инициализирован баланс для кошелька {address}: {current_balance} TRX")
                    return
                
                if current_balance > last_balance and current_balance >= MIN_DEPOSIT_AMOUNT:
                    deposit_amount = current_balance - last_balance
                    print(f"💰 Обнаружено пополнение (fallback): User {user_id}, Amount: {deposit_amount} TRX")
                    
                    await self._notify_admins(user_id, deposit_amount)
                    await db.update_balance(user_id, deposit_amount)
                    
                    await db.update_last_checked_balance(user_id, current_balance)
                    
                    if referrer_id:
                        await self._apply_multi_level_referral_bonus(user_id, deposit_amount)
                    
                    try:
                        current_user_balance = await self._get_user_balance(user_id)
                        user_locale = await db.get_user_language(user_id)
                        await self.bot.send_message(
                            user_id,
                            locale_manager.get_text('deposit_notification', user_locale,
                                amount=deposit_amount,
                                balance=current_user_balance
                            )
                        )
                    except Exception as e:
                        print(f"❌ Не удалось отправить уведомление пользователю {user_id}: {e}")
                
                return
            
            if not transactions:
                print(f"📝 Нет транзакций для адреса {address}")
                print(f"✅ Кошелек {address} проверен - транзакций нет")
                return

            # First successful sync: set watermark to latest seen tx
            # and skip historical credits.
            if last_checked_tx_timestamp == 0:
                newest_ts = max((int(tx.get('block_timestamp', 0) or 0) for tx in transactions), default=0)
                if newest_ts > 0:
                    await db.update_last_checked_tx_timestamp(user_id, newest_ts)
                    print(f"🔒 Инициализирован watermark транзакций для {address}: {newest_ts}")
                return
            
            print(f"🔍 Найдено {len(transactions)} транзакций для кошелька {address}")
            max_seen_ts = last_checked_tx_timestamp
            
            for i, tx in enumerate(transactions):
                tx_hash = tx.get('txID')
                print(f"🔍 Транзакция {i+1}: {tx_hash}")
                
                if await db.transaction_exists(tx_hash):
                    print(f"  ⏭️ Транзакция уже обработана, пропускаем")
                    continue
                
                raw_data = tx.get('raw_data', {})
                contract = raw_data.get('contract', [])
                print(f"📋 Контрактов в транзакции: {len(contract)}")
                
                if contract and len(contract) > 0:
                    contract_data = contract[0]
                    contract_type = contract_data.get('type', '')
                    parameter = contract_data.get('parameter', {})
                    value = parameter.get('value', {})
                    
                    if contract_type == 'TransferAssetContract':
                        print(f"  ⏭️ Пропускаем TransferAssetContract (токен TRC10)")
                        continue
                    
                    amount = float(value.get('amount', 0)) / 1000000
                    to_address_hex = value.get('to_address')
                    tx_time = int(tx.get('block_timestamp', 0) or 0)
                    if tx_time > max_seen_ts:
                        max_seen_ts = tx_time
                    if tx_time <= last_checked_tx_timestamp:
                        print(f"  ⏭️ Старая транзакция ({tx_time}), уже в проверенном диапазоне")
                        continue
                    
                    to_address_base58 = hex_to_base58(to_address_hex) if to_address_hex else None
                    
                    print(f"  💵 Сумма: {amount} TRX, На адрес: {to_address_base58}")
                    
                    if (to_address_base58 == address and 
                        amount >= MIN_DEPOSIT_AMOUNT):
                        
                        print(f"  ✅ Транзакция подходит для обработки!")
                        
                        await db.add_transaction(
                            user_id=user_id,
                            wallet_address=address,
                            transaction_hash=tx_hash,
                            amount=amount,
                            transaction_time=tx_time
                        )
                        print(f"  💾 Транзакция сохранена в БД: {tx_hash}")
                        
                        await self._notify_admins(user_id, amount)
                        
                        await db.update_balance(user_id, amount)
                        print(f"  💰 Баланс пользователя обновлен: +{amount} TRX")
                        
                        if referrer_id:
                            await self._apply_multi_level_referral_bonus(user_id, amount)
                        
                        try:
                            current_balance = await self._get_user_balance(user_id)
                            user_locale = await db.get_user_language(user_id)
                            await self.bot.send_message(
                                user_id,
                                locale_manager.get_text('deposit_notification', user_locale,
                                    amount=amount,
                                    balance=current_balance
                                )
                            )
                            print(f"  ✅ Уведомление о пополнении отправлено пользователю {user_id}: {amount:.2f} TRX")
                        except Exception as e:
                            print(f"  ❌ Не удалось отправить уведомление пользователю {user_id}: {e}")
            
            if self.api_error_count > 0:
                self.api_error_count = 0
            if max_seen_ts > last_checked_tx_timestamp:
                await db.update_last_checked_tx_timestamp(user_id, max_seen_ts)
                
        except Exception as e:
            print(f"Ошибка при проверке пополнений кошельков: {e}")
    
    async def _notify_admins(self, user_id: int, amount: float):
        for admin_id in ADMIN_IDS:
            try:
                await self.bot.send_message(
                    admin_id,
                    f"💰 Новое пополнение!\n"
                    f"👤 Пользователь: {user_id}\n"
                    f"💳 Сумма: {amount:.2f} TRX\n"
                    f"⏰ Время: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}"
                )
            except Exception as e:
                print(f"❌ Не удалось уведомить админа {admin_id}: {e}")
    
    async def _notify_admin_about_problem(self, title: str, message: str):
        for admin_id in ADMIN_IDS:
            try:
                await self.bot.send_message(
                    admin_id,
                    f"⚠️ {title}\n\n{message}\n\n⏰ {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}"
                )
            except Exception as e:
                print(f"❌ Не удалось уведомить админа о проблеме {admin_id}: {e}")
    
    async def _get_user_balance(self, user_id: int) -> float:
        return await db.get_balance(user_id)

    async def _apply_multi_level_referral_bonus(self, source_user_id: int, deposit_amount: float):
        level1 = await db.get_referrer_id(source_user_id)
        if not level1:
            return
        levels = [(level1, None), (await db.get_referrer_id(level1), 1.0), (await db.get_referrer_id(await db.get_referrer_id(level1) or 0), 0.5)]
        for idx, (ref_user_id, fixed_percent) in enumerate(levels, start=1):
            if not ref_user_id:
                continue
            if idx == 1:
                custom_ref_percent = await db.get_user_ref_percent(ref_user_id)
                ref_percent = custom_ref_percent if custom_ref_percent is not None else await db.get_global_referral_percent()
            else:
                ref_percent = fixed_percent or 0.0
            referral_bonus = deposit_amount * (ref_percent / 100)
            if referral_bonus <= 0:
                continue
            await db.update_balance(ref_user_id, referral_bonus)
            await db.add_transaction_history(
                ref_user_id,
                referral_bonus,
                'referral_bonus',
                f'Level {idx} referral bonus from user {source_user_id}'
            )
            await db.conn.execute(
                'INSERT INTO referral_payouts (from_user_id, to_user_id, level, amount) VALUES (?, ?, ?, ?)',
                (source_user_id, ref_user_id, idx, referral_bonus)
            )
            await db.conn.commit()
            try:
                referrer_locale = await db.get_user_language(ref_user_id)
                await self.bot.send_message(
                    ref_user_id,
                    locale_manager.get_text(
                        'referral_bonus',
                        referrer_locale,
                        amount=referral_bonus,
                        user_id=source_user_id,
                        deposit_amount=deposit_amount
                    )
                )
            except Exception as e:
                print(f"  ❌ Не удалось отправить реферальный бонус пользователю {ref_user_id}: {e}")
    
    async def run(self):
        self.is_running = True
        print("🔄 Запуск проверки балансов...")
        
        while self.is_running:
            try:
                await self.check_all_wallets()
                
                interval = await db.get_check_interval()
                await asyncio.sleep(interval)
                
            except Exception as e:
                print(f"❌ Ошибка в цикле проверки балансов: {e}")
                await asyncio.sleep(60)
    
    def stop(self):
        self.is_running = False
        print("⏹️ Остановка проверки балансов...")

