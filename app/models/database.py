import aiosqlite
import asyncio
import hashlib
import secrets
from app.models.config import DATABASE_PATH
from typing import Optional, List, Dict, Any
from app.services.security.crypto import secret_cipher


class Database:
    def __init__(self, db_path: str = None):
        self.db_path = db_path or DATABASE_PATH
        self.conn = None
    
    async def connect(self):
        self.conn = await aiosqlite.connect(self.db_path)
        await self.create_tables()
    
    async def close(self):
        if self.conn:
            await self.conn.close()
    
    async def create_tables(self):
        await self.conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                balance REAL DEFAULT 0.0,
                trx_wallet TEXT,
                deposit_wallet_address TEXT,
                deposit_wallet_private_key TEXT,
                last_checked_balance REAL DEFAULT 0.0,
                referrer_id INTEGER,
                language TEXT DEFAULT 'ru',
                first_message_id INTEGER,
                first_message_chat_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (referrer_id) REFERENCES users (user_id)
            )
        ''')
        
        try:
            await self.conn.execute('ALTER TABLE users ADD COLUMN language TEXT DEFAULT "ru"')
            await self.conn.execute('UPDATE users SET language = "ru" WHERE language IS NULL')
            await self.conn.commit()
        except Exception as e:
            pass
        
        try:
            await self.conn.execute('ALTER TABLE users ADD COLUMN first_message_id INTEGER')
        except Exception as e:
            pass
            
        try:
            await self.conn.execute('ALTER TABLE users ADD COLUMN first_message_chat_id INTEGER')
        except Exception as e:
            pass
        
        try:
            await self.conn.execute('ALTER TABLE users ADD COLUMN custom_margin_percent REAL')
        except Exception as e:
            pass
            
        try:
            await self.conn.execute('ALTER TABLE users ADD COLUMN custom_ref_percent REAL')
        except Exception as e:
            pass

        try:
            await self.conn.execute('ALTER TABLE users ADD COLUMN last_checked_tx_timestamp INTEGER DEFAULT 0')
        except Exception as e:
            pass
        try:
            await self.conn.execute('ALTER TABLE users ADD COLUMN api_balance REAL DEFAULT 0.0')
        except Exception as e:
            pass
        
        try:
            await self.conn.execute('ALTER TABLE purchases ADD COLUMN period TEXT')
        except Exception as e:
            pass
        
        try:
            await self.conn.execute('ALTER TABLE purchases ADD COLUMN price_trx REAL')
        except Exception as e:
            pass
        
        try:
            await self.conn.execute('ALTER TABLE purchases ADD COLUMN wallet_address TEXT')
        except Exception as e:
            pass
        
        try:
            await self.conn.execute('ALTER TABLE purchases ADD COLUMN order_id INTEGER')
        except Exception as e:
            pass
        try:
            await self.conn.execute('ALTER TABLE purchases ADD COLUMN provider TEXT')
        except Exception as e:
            pass
        try:
            await self.conn.execute('ALTER TABLE purchases ADD COLUMN status TEXT DEFAULT "created"')
        except Exception as e:
            pass
        
        await self.conn.execute('''
            CREATE TABLE IF NOT EXISTS purchases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                energy_amount INTEGER,
                period TEXT,
                price_trx REAL,
                wallet_address TEXT,
                order_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        await self.conn.execute('''
            CREATE TABLE IF NOT EXISTS transaction_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                amount REAL,
                type TEXT,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        try:
            await self.conn.execute('''
                INSERT INTO transaction_history (id, user_id, amount, type, description, created_at)
                SELECT id, user_id, amount, type, description, created_at 
                FROM transactions 
                WHERE transaction_hash IS NULL
            ''')
        except Exception as e:
            pass
        
        await self.conn.execute('''
            CREATE TABLE IF NOT EXISTS trx_prices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                price REAL NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        await self.conn.execute('''
            CREATE TABLE IF NOT EXISTS system_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                setting_key TEXT UNIQUE NOT NULL,
                setting_value TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        default_settings = [
            ('global_energy_margin', '10'),
            ('global_referral_percent', '2'),
            ('check_interval_seconds', '60'),
            ('api_requests_per_minute', '69'),
            ('api_requests_per_day', '100000'),
            ('max_wallet_check_delay_minutes', '5'),
            ('requests_today', '0'),
            ('last_reset_date', '')
        ]
        
        for key, value in default_settings:
            try:
                await self.conn.execute('''
                    INSERT OR IGNORE INTO system_settings (setting_key, setting_value)
                    VALUES (?, ?)
                ''', (key, value))
            except:
                pass
        
        try:
            cursor = await self.conn.execute("PRAGMA table_info(transactions)")
            columns = await cursor.fetchall()
            has_transaction_hash = any(col[1] == 'transaction_hash' for col in columns)
            
            if not has_transaction_hash and columns:
                await self.conn.execute('DROP TABLE IF EXISTS transactions')
        except Exception as e:
            pass
        
        await self.conn.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                wallet_address TEXT NOT NULL,
                transaction_hash TEXT UNIQUE,
                amount REAL NOT NULL,
                transaction_time TIMESTAMP,
                processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')

        await self.conn.execute('''
            CREATE TABLE IF NOT EXISTS user_wallets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                label TEXT,
                address TEXT NOT NULL,
                private_key_enc TEXT,
                is_active INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')

        await self.conn.execute('''
            CREATE TABLE IF NOT EXISTS smart_settings (
                user_id INTEGER PRIMARY KEY,
                enabled INTEGER DEFAULT 0,
                price_threshold_trx REAL DEFAULT 0.0,
                auto_renew INTEGER DEFAULT 0,
                predicted_daily_energy INTEGER DEFAULT 0,
                target_energy_amount INTEGER DEFAULT 30000,
                period_id TEXT DEFAULT '24hours',
                min_energy_trigger INTEGER DEFAULT 10000,
                last_low_balance_notice_at TEXT,
                last_auto_purchase_at TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        try:
            await self.conn.execute("ALTER TABLE smart_settings ADD COLUMN target_energy_amount INTEGER DEFAULT 30000")
        except Exception:
            pass
        try:
            await self.conn.execute("ALTER TABLE smart_settings ADD COLUMN period_id TEXT DEFAULT '24hours'")
        except Exception:
            pass
        try:
            await self.conn.execute("ALTER TABLE smart_settings ADD COLUMN min_energy_trigger INTEGER DEFAULT 10000")
        except Exception:
            pass
        try:
            await self.conn.execute("ALTER TABLE smart_settings ADD COLUMN last_low_balance_notice_at TEXT")
        except Exception:
            pass
        try:
            await self.conn.execute("ALTER TABLE smart_settings ADD COLUMN last_auto_purchase_at TEXT")
        except Exception:
            pass

        await self.conn.execute('''
            CREATE TABLE IF NOT EXISTS subscriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                plan_code TEXT NOT NULL,
                status TEXT DEFAULT 'active',
                daily_energy_limit INTEGER DEFAULT 0,
                fee_trx REAL DEFAULT 0.0,
                discount_percent REAL DEFAULT 0.0,
                next_billing_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')

        await self.conn.execute('''
            CREATE TABLE IF NOT EXISTS provider_order_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                provider TEXT,
                order_id TEXT,
                energy_amount INTEGER,
                period TEXT,
                price_trx REAL,
                status TEXT,
                request_hash TEXT,
                tx_reference TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        await self.conn.execute('''
            CREATE TABLE IF NOT EXISTS reserve_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                total_user_balance REAL NOT NULL,
                total_hot_wallet_balance REAL NOT NULL,
                coverage_ratio REAL NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        await self.conn.execute('''
            CREATE TABLE IF NOT EXISTS referral_payouts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                from_user_id INTEGER NOT NULL,
                to_user_id INTEGER NOT NULL,
                level INTEGER NOT NULL,
                amount REAL NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        await self.conn.execute('''
            CREATE TABLE IF NOT EXISTS api_apps (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL UNIQUE,
                app_name TEXT NOT NULL,
                token_hash TEXT NOT NULL,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')

        await self.conn.execute('''
            CREATE TABLE IF NOT EXISTS api_usage_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                app_id INTEGER NOT NULL,
                endpoint TEXT NOT NULL,
                status_code INTEGER NOT NULL,
                cost_trx REAL DEFAULT 0.0,
                revenue_trx REAL DEFAULT 0.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (app_id) REFERENCES api_apps (id)
            )
        ''')
        try:
            await self.conn.execute('ALTER TABLE api_usage_logs ADD COLUMN revenue_trx REAL DEFAULT 0.0')
        except Exception:
            pass
        
        await self.conn.commit()
    
    async def user_exists(self, user_id: int) -> bool:
        cursor = await self.conn.execute('SELECT 1 FROM users WHERE user_id = ?', (user_id,))
        return await cursor.fetchone() is not None
    
    async def add_user(self, user_id: int, username: str = None, first_name: str = None, referrer_id: int = None):
        await self.conn.execute('''
            INSERT OR IGNORE INTO users (user_id, username, first_name, referrer_id)
            VALUES (?, ?, ?, ?)
        ''', (user_id, username, first_name, referrer_id))
        await self.conn.commit()
    
    async def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        cursor = await self.conn.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        row = await cursor.fetchone()
        if row:
            columns = [description[0] for description in cursor.description]
            return dict(zip(columns, row))
        return None
    
    async def update_balance(self, user_id: int, amount: float):
        await self.conn.execute('''
            UPDATE users SET balance = balance + ? WHERE user_id = ?
        ''', (amount, user_id))
        await self.conn.commit()
    
    async def get_balance(self, user_id: int) -> float:
        cursor = await self.conn.execute('SELECT balance FROM users WHERE user_id = ?', (user_id,))
        row = await cursor.fetchone()
        return row[0] if row else 0.0
    
    async def set_deposit_wallet(self, user_id: int, address: str, private_key: str):
        encrypted_private_key = secret_cipher.encrypt(private_key)
        await self.conn.execute('''
            UPDATE users SET deposit_wallet_address = ?, deposit_wallet_private_key = ?
            WHERE user_id = ?
        ''', (address, encrypted_private_key, user_id))
        await self.conn.commit()
    
    async def get_deposit_wallet(self, user_id: int) -> Optional[Dict[str, str]]:
        cursor = await self.conn.execute('''
            SELECT deposit_wallet_address, deposit_wallet_private_key FROM users WHERE user_id = ?
        ''', (user_id,))
        row = await cursor.fetchone()
        if row and row[0]:
            return {
                'address': row[0],
                'private_key': secret_cipher.decrypt(row[1])
            }
        return None
    
    async def get_all_deposit_wallets(self) -> List[Dict[str, Any]]:
        cursor = await self.conn.execute('''
            SELECT user_id, deposit_wallet_address FROM users 
            WHERE deposit_wallet_address IS NOT NULL AND deposit_wallet_address != ''
        ''')
        rows = await cursor.fetchall()
        return [{'user_id': row[0], 'address': row[1]} for row in rows]
    
    async def update_last_checked_balance(self, user_id: int, balance: float):
        await self.conn.execute('''
            UPDATE users SET last_checked_balance = ? WHERE user_id = ?
        ''', (balance, user_id))
        await self.conn.commit()
    
    async def get_purchases_count(self, user_id: int) -> int:
        cursor = await self.conn.execute('SELECT COUNT(*) as count FROM purchases WHERE user_id = ?', (user_id,))
        row = await cursor.fetchone()
        return row[0] if row else 0
    
    async def add_transaction_history(self, user_id: int, amount: float, transaction_type: str, description: str = None):
        await self.conn.execute('''
            INSERT INTO transaction_history (user_id, amount, type, description)
            VALUES (?, ?, ?, ?)
        ''', (user_id, amount, transaction_type, description))
        await self.conn.commit()
    
    async def get_referrals_count(self, user_id: int) -> int:
        cursor = await self.conn.execute('SELECT COUNT(*) as count FROM users WHERE referrer_id = ?', (user_id,))
        row = await cursor.fetchone()
        return row[0] if row else 0

    async def get_referrer_id(self, user_id: int) -> Optional[int]:
        cursor = await self.conn.execute('SELECT referrer_id FROM users WHERE user_id = ?', (user_id,))
        row = await cursor.fetchone()
        return int(row[0]) if row and row[0] is not None else None
    
    async def get_referral_earnings(self, user_id: int) -> float:
        cursor = await self.conn.execute('''
            SELECT SUM(amount) as total FROM transaction_history WHERE user_id = ? AND type = 'referral_bonus'
        ''', (user_id,))
        row = await cursor.fetchone()
        return row[0] if row and row[0] else 0.0

    async def get_referral_levels_stats(self, user_id: int) -> Dict[str, float]:
        cursor = await self.conn.execute('''
            SELECT level, COALESCE(SUM(amount), 0)
            FROM referral_payouts
            WHERE to_user_id = ?
            GROUP BY level
        ''', (user_id,))
        rows = await cursor.fetchall()
        result = {1: 0.0, 2: 0.0, 3: 0.0}
        for level, amount in rows:
            if level in result:
                result[level] = float(amount or 0.0)
        return {
            'level1': result[1],
            'level2': result[2],
            'level3': result[3],
            'total': result[1] + result[2] + result[3],
        }
    
    async def set_user_language(self, user_id: int, language: str):
        try:
            await self.conn.execute('UPDATE users SET language = ? WHERE user_id = ?', (language, user_id))
            await self.conn.commit()
        except Exception as e:
            pass
    
    async def get_user_language(self, user_id: int) -> str:
        try:
            cursor = await self.conn.execute('SELECT language FROM users WHERE user_id = ?', (user_id,))
            row = await cursor.fetchone()
            return row[0] if row and row[0] else 'ru'
        except Exception as e:
            return 'ru'
    
    async def set_user_margin(self, user_id: int, margin_percent: float):
        await self.conn.execute('''
            UPDATE users SET custom_margin_percent = ? WHERE user_id = ?
        ''', (margin_percent, user_id))
        await self.conn.commit()
    
    async def get_user_margin(self, user_id: int) -> Optional[float]:
        cursor = await self.conn.execute('SELECT custom_margin_percent FROM users WHERE user_id = ?', (user_id,))
        row = await cursor.fetchone()
        return row[0] if row and row[0] is not None else None
    
    async def reset_user_margin(self, user_id: int):
        await self.conn.execute('''
            UPDATE users SET custom_margin_percent = NULL WHERE user_id = ?
        ''', (user_id,))
        await self.conn.commit()
    
    async def set_user_ref_percent(self, user_id: int, ref_percent: float):
        await self.conn.execute('''
            UPDATE users SET custom_ref_percent = ? WHERE user_id = ?
        ''', (ref_percent, user_id))
        await self.conn.commit()
    
    async def get_user_ref_percent(self, user_id: int) -> Optional[float]:
        cursor = await self.conn.execute('SELECT custom_ref_percent FROM users WHERE user_id = ?', (user_id,))
        row = await cursor.fetchone()
        return row[0] if row and row[0] is not None else None
    
    async def reset_user_ref_percent(self, user_id: int):
        await self.conn.execute('''
            UPDATE users SET custom_ref_percent = NULL WHERE user_id = ?
        ''', (user_id,))
        await self.conn.commit()
    
    async def get_global_energy_margin(self) -> float:
        cursor = await self.conn.execute('SELECT setting_value FROM system_settings WHERE setting_key = ?', ('global_energy_margin',))
        row = await cursor.fetchone()
        return float(row[0]) if row else 10.0
    
    async def set_global_energy_margin(self, margin: float):
        await self.conn.execute('''
            INSERT OR REPLACE INTO system_settings (setting_key, setting_value, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
        ''', ('global_energy_margin', str(margin)))
        await self.conn.commit()
    
    async def get_global_referral_percent(self) -> float:
        cursor = await self.conn.execute('SELECT setting_value FROM system_settings WHERE setting_key = ?', ('global_referral_percent',))
        row = await cursor.fetchone()
        return float(row[0]) if row else 2.0
    
    async def set_global_referral_percent(self, percent: float):
        await self.conn.execute('''
            INSERT OR REPLACE INTO system_settings (setting_key, setting_value, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
        ''', ('global_referral_percent', str(percent)))
        await self.conn.commit()
    
    async def get_api_limits(self) -> Dict[str, Any]:
        cursor = await self.conn.execute('''
            SELECT setting_key, setting_value FROM system_settings 
            WHERE setting_key IN ('api_requests_per_minute', 'api_requests_per_day', 'requests_today', 'last_reset_date')
        ''')
        rows = await cursor.fetchall()
        limits = {}
        for row in rows:
            limits[row[0]] = row[1]
        
        return {
            'per_minute': int(float(limits.get('api_requests_per_minute', '69'))),
            'per_day': int(float(limits.get('api_requests_per_day', '100000'))),
            'requests_today': int(float(limits.get('requests_today', '0'))),
            'last_reset_date': limits.get('last_reset_date', '')
        }
    
    async def increment_requests_today(self):
        try:
            cursor = await self.conn.execute('SELECT setting_value FROM system_settings WHERE setting_key = ?', ('requests_today',))
            row = await cursor.fetchone()
            current = int(float(row[0])) if row else 0
            new_value = current + 1
            
            await self.conn.execute('''
                INSERT OR REPLACE INTO system_settings (setting_key, setting_value, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            ''', ('requests_today', str(new_value)))
            await self.conn.commit()
        except Exception as e:
            pass
    
    async def reset_requests_today(self):
        await self.conn.execute('''
            INSERT OR REPLACE INTO system_settings (setting_key, setting_value, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
        ''', ('requests_today', '0'))
        await self.conn.commit()
    
    async def set_last_reset_date(self, date: str):
        await self.conn.execute('''
            INSERT OR REPLACE INTO system_settings (setting_key, setting_value, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
        ''', ('last_reset_date', date))
        await self.conn.commit()
    
    async def calculate_optimal_interval(self, wallet_count: int) -> int:
        limits = await self.get_api_limits()
        per_minute = limits['per_minute']
        per_day = limits['per_day']
        requests_today = limits['requests_today']
        
        max_delay_minutes = 5
        min_interval_for_5min = (max_delay_minutes * 60) / wallet_count
        
        if wallet_count <= per_minute * max_delay_minutes:
            optimal_interval = max(min_interval_for_5min, 3)
        else:
            optimal_interval = max(3, min_interval_for_5min)
        
        min_interval_for_daily_limit = (3600 * wallet_count * 24) // (per_day * 0.95)
        optimal_interval = max(optimal_interval, min_interval_for_daily_limit)
        
        return int(optimal_interval)
    
    async def set_check_interval(self, interval: int):
        await self.conn.execute('''
            INSERT OR REPLACE INTO system_settings (setting_key, setting_value, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
        ''', ('check_interval_seconds', str(interval)))
        await self.conn.commit()
    
    async def get_check_interval(self) -> int:
        try:
            cursor = await self.conn.execute('SELECT setting_value FROM system_settings WHERE setting_key = ?', ('check_interval_seconds',))
            row = await cursor.fetchone()
            return int(float(row[0])) if row else 60
        except Exception as e:
            return 60
    
    async def add_transaction(self, user_id: int, wallet_address: str, transaction_hash: str, amount: float, transaction_time: str = None):
        try:
            await self.conn.execute('''
                INSERT INTO transactions (user_id, wallet_address, transaction_hash, amount, transaction_time)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, wallet_address, transaction_hash, amount, transaction_time))
            await self.conn.commit()
            return True
        except Exception as e:
            return False

    async def transaction_exists(self, transaction_hash: str) -> bool:
        try:
            cursor = await self.conn.execute('SELECT 1 FROM transactions WHERE transaction_hash = ?', (transaction_hash,))
            return await cursor.fetchone() is not None
        except Exception as e:
            return False

    async def get_all_users_with_deposit_wallets(self):
        cursor = await self.conn.execute('''
            SELECT user_id, deposit_wallet_address, deposit_wallet_private_key, 
                   last_checked_balance, referrer_id, last_checked_tx_timestamp FROM users 
            WHERE deposit_wallet_address IS NOT NULL AND deposit_wallet_address != ''
        ''')
        rows = await cursor.fetchall()
        return [{
            'user_id': row[0],
            'deposit_wallet_address': row[1],
            'deposit_wallet_private_key': secret_cipher.decrypt(row[2]),
            'last_checked_balance': row[3],
            'referrer_id': row[4],
            'last_checked_tx_timestamp': int(row[5] or 0),
        } for row in rows]

    async def update_last_checked_tx_timestamp(self, user_id: int, timestamp_ms: int):
        await self.conn.execute('''
            UPDATE users SET last_checked_tx_timestamp = ? WHERE user_id = ?
        ''', (int(timestamp_ms), user_id))
        await self.conn.commit()

    async def initialize_last_checked_balance(self, user_id: int, balance: float):
        await self.conn.execute('''
            UPDATE users SET last_checked_balance = ? WHERE user_id = ?
        ''', (balance, user_id))
        await self.conn.commit()

    async def set_trx_wallet(self, user_id: int, wallet: str):
        await self.conn.execute('''
            UPDATE users SET trx_wallet = ? WHERE user_id = ?
        ''', (wallet, user_id))
        await self.conn.commit()

    async def get_first_message(self, user_id: int):
        cursor = await self.conn.execute('''
            SELECT first_message_id, first_message_chat_id FROM users WHERE user_id = ?
        ''', (user_id,))
        row = await cursor.fetchone()
        return (row[0], row[1]) if row and row[0] else (None, None)

    async def set_first_message(self, user_id: int, message_id: int, chat_id: int):
        await self.conn.execute('''
            UPDATE users SET first_message_id = ?, first_message_chat_id = ? WHERE user_id = ?
        ''', (message_id, chat_id, user_id))
        await self.conn.commit()

    async def get_trx_price(self) -> float:
        cursor = await self.conn.execute('''
            SELECT price FROM trx_prices ORDER BY updated_at DESC LIMIT 1
        ''')
        row = await cursor.fetchone()
        return row[0] if row else 0.0

    async def set_trx_price(self, price: float):
        await self.conn.execute('''
            INSERT INTO trx_prices (price) VALUES (?)
        ''', (price,))
        await self.conn.commit()

    async def get_user_purchases(self, user_id: int, limit: int = 10):
        cursor = await self.conn.execute('''
            SELECT energy_amount, period, price_trx, created_at, wallet_address 
            FROM purchases WHERE user_id = ? ORDER BY created_at DESC LIMIT ?
        ''', (user_id, limit))
        rows = await cursor.fetchall()
        return [{
            'energy_amount': row[0],
            'period': row[1],
            'price_trx': row[2],
            'created_at': row[3],
            'wallet_address': row[4]
        } for row in rows]

    async def add_purchase(self, user_id: int, energy_amount: int, period: str, price_trx: float, wallet_address: str, order_id: int, provider: str = "unknown", status: str = "created"):
        await self.conn.execute('''
            INSERT INTO purchases (user_id, energy_amount, period, price_trx, wallet_address, order_id, provider, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, energy_amount, period, price_trx, wallet_address, order_id, provider, status))
        await self.conn.commit()

    async def log_provider_order(self, user_id: int, provider: str, order_id: str, energy_amount: int, period: str, price_trx: float, status: str, request_hash: str = None, tx_reference: str = None):
        await self.conn.execute('''
            INSERT INTO provider_order_log (user_id, provider, order_id, energy_amount, period, price_trx, status, request_hash, tx_reference)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, provider, str(order_id) if order_id is not None else None, energy_amount, period, price_trx, status, request_hash, tx_reference))
        await self.conn.commit()

    async def upsert_smart_settings(
        self,
        user_id: int,
        enabled: bool,
        price_threshold_trx: float,
        auto_renew: bool,
        predicted_daily_energy: int,
        target_energy_amount: int = 30000,
        period_id: str = "24hours",
        min_energy_trigger: int = 10000,
    ):
        await self.conn.execute('''
            INSERT INTO smart_settings (
                user_id, enabled, price_threshold_trx, auto_renew, predicted_daily_energy,
                target_energy_amount, period_id, min_energy_trigger, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(user_id) DO UPDATE SET
                enabled = excluded.enabled,
                price_threshold_trx = excluded.price_threshold_trx,
                auto_renew = excluded.auto_renew,
                predicted_daily_energy = excluded.predicted_daily_energy,
                target_energy_amount = excluded.target_energy_amount,
                period_id = excluded.period_id,
                min_energy_trigger = excluded.min_energy_trigger,
                updated_at = CURRENT_TIMESTAMP
        ''', (
            user_id,
            1 if enabled else 0,
            price_threshold_trx,
            1 if auto_renew else 0,
            predicted_daily_energy,
            target_energy_amount,
            period_id,
            min_energy_trigger,
        ))
        await self.conn.commit()

    async def get_smart_settings(self, user_id: int) -> Optional[Dict[str, Any]]:
        cursor = await self.conn.execute('''
            SELECT user_id, enabled, price_threshold_trx, auto_renew, predicted_daily_energy,
                   target_energy_amount, period_id, min_energy_trigger, last_low_balance_notice_at, last_auto_purchase_at
            FROM smart_settings WHERE user_id = ?
        ''', (user_id,))
        row = await cursor.fetchone()
        if not row:
            return None
        return {
            'user_id': row[0],
            'enabled': bool(row[1]),
            'price_threshold_trx': float(row[2] or 0),
            'auto_renew': bool(row[3]),
            'predicted_daily_energy': int(row[4] or 0),
            'target_energy_amount': int(row[5] or 30000),
            'period_id': row[6] or '24hours',
            'min_energy_trigger': int(row[7] or 10000),
            'last_low_balance_notice_at': row[8],
            'last_auto_purchase_at': row[9],
        }

    async def get_smart_enabled_users(self) -> List[Dict[str, Any]]:
        cursor = await self.conn.execute('''
            SELECT s.user_id, s.price_threshold_trx, s.auto_renew, s.predicted_daily_energy,
                   s.target_energy_amount, s.period_id, s.min_energy_trigger, s.last_low_balance_notice_at,
                   u.trx_wallet, u.balance
            FROM smart_settings s
            JOIN users u ON u.user_id = s.user_id
            WHERE s.enabled = 1
        ''')
        rows = await cursor.fetchall()
        return [{
            'user_id': row[0],
            'price_threshold_trx': float(row[1] or 0),
            'auto_renew': bool(row[2]),
            'predicted_daily_energy': int(row[3] or 0),
            'target_energy_amount': int(row[4] or 30000),
            'period_id': row[5] or '24hours',
            'min_energy_trigger': int(row[6] or 10000),
            'last_low_balance_notice_at': row[7],
            'trx_wallet': row[8],
            'balance': float(row[9] or 0),
        } for row in rows]

    async def mark_smart_low_balance_notice(self, user_id: int):
        await self.conn.execute('''
            UPDATE smart_settings
            SET last_low_balance_notice_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
            WHERE user_id = ?
        ''', (user_id,))
        await self.conn.commit()

    async def mark_smart_auto_purchase(self, user_id: int):
        await self.conn.execute('''
            UPDATE smart_settings
            SET last_auto_purchase_at = CURRENT_TIMESTAMP, last_low_balance_notice_at = NULL, updated_at = CURRENT_TIMESTAMP
            WHERE user_id = ?
        ''', (user_id,))
        await self.conn.commit()

    async def upsert_subscription(self, user_id: int, plan_code: str, fee_trx: float, discount_percent: float, daily_energy_limit: int):
        await self.conn.execute('''
            UPDATE subscriptions
            SET status = 'inactive', updated_at = CURRENT_TIMESTAMP
            WHERE user_id = ? AND status = 'active'
        ''', (user_id,))
        await self.conn.execute('''
            INSERT INTO subscriptions (user_id, plan_code, status, daily_energy_limit, fee_trx, discount_percent, next_billing_at)
            VALUES (?, ?, 'active', ?, ?, ?, datetime('now', '+30 day'))
        ''', (user_id, plan_code, daily_energy_limit, fee_trx, discount_percent))
        await self.conn.commit()

    async def get_active_subscription(self, user_id: int) -> Optional[Dict[str, Any]]:
        cursor = await self.conn.execute('''
            SELECT plan_code, daily_energy_limit, fee_trx, discount_percent, next_billing_at
            FROM subscriptions
            WHERE user_id = ? AND status = 'active'
            ORDER BY id DESC LIMIT 1
        ''', (user_id,))
        row = await cursor.fetchone()
        if not row:
            return None
        return {
            'plan_code': row[0],
            'daily_energy_limit': int(row[1] or 0),
            'fee_trx': float(row[2] or 0),
            'discount_percent': float(row[3] or 0),
            'next_billing_at': row[4],
        }

    async def add_user_wallet(self, user_id: int, label: str, address: str, private_key: str = ""):
        encrypted_key = secret_cipher.encrypt(private_key) if private_key else ""
        await self.conn.execute('''
            INSERT INTO user_wallets (user_id, label, address, private_key_enc, is_active)
            VALUES (?, ?, ?, ?, 0)
        ''', (user_id, label, address, encrypted_key))
        await self.conn.commit()

    async def get_user_wallets(self, user_id: int) -> List[Dict[str, Any]]:
        cursor = await self.conn.execute('''
            SELECT id, label, address, is_active, created_at
            FROM user_wallets
            WHERE user_id = ?
            ORDER BY id DESC
        ''', (user_id,))
        rows = await cursor.fetchall()
        return [{
            'id': row[0],
            'label': row[1],
            'address': row[2],
            'is_active': bool(row[3]),
            'created_at': row[4],
        } for row in rows]

    async def add_reserve_snapshot(self, total_user_balance: float, total_hot_wallet_balance: float):
        coverage_ratio = (total_hot_wallet_balance / total_user_balance) if total_user_balance > 0 else 1.0
        await self.conn.execute('''
            INSERT INTO reserve_snapshots (total_user_balance, total_hot_wallet_balance, coverage_ratio)
            VALUES (?, ?, ?)
        ''', (total_user_balance, total_hot_wallet_balance, coverage_ratio))
        await self.conn.commit()

    async def get_total_user_balance(self) -> float:
        cursor = await self.conn.execute('SELECT COALESCE(SUM(balance), 0) FROM users')
        row = await cursor.fetchone()
        return float(row[0] or 0.0)

    async def get_public_stats(self) -> Dict[str, Any]:
        cursor = await self.conn.execute('SELECT COUNT(*) FROM provider_order_log WHERE status = "success"')
        success = (await cursor.fetchone())[0]
        cursor = await self.conn.execute('SELECT COUNT(*) FROM provider_order_log')
        total = (await cursor.fetchone())[0]
        cursor = await self.conn.execute('SELECT AVG(price_trx) FROM provider_order_log WHERE status = "success"')
        avg_price = (await cursor.fetchone())[0] or 0
        cursor = await self.conn.execute('SELECT total_user_balance, total_hot_wallet_balance, coverage_ratio, created_at FROM reserve_snapshots ORDER BY id DESC LIMIT 1')
        reserve = await cursor.fetchone()
        return {
            'orders_total': int(total),
            'orders_success': int(success),
            'success_rate': float(success / total * 100) if total else 0.0,
            'avg_price_trx': float(avg_price),
            'reserve_snapshot': {
                'total_user_balance': float(reserve[0]),
                'total_hot_wallet_balance': float(reserve[1]),
                'coverage_ratio': float(reserve[2]),
                'created_at': reserve[3],
            } if reserve else None
        }

    async def create_or_rotate_api_app(self, user_id: int, app_name: str = "My App") -> str:
        token = "sea_" + secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
        await self.conn.execute('''
            INSERT INTO api_apps (user_id, app_name, token_hash, is_active, updated_at)
            VALUES (?, ?, ?, 1, CURRENT_TIMESTAMP)
            ON CONFLICT(user_id) DO UPDATE SET
                app_name = excluded.app_name,
                token_hash = excluded.token_hash,
                is_active = 1,
                updated_at = CURRENT_TIMESTAMP
        ''', (user_id, app_name, token_hash))
        await self.conn.commit()
        return token

    async def get_api_app_by_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        cursor = await self.conn.execute('''
            SELECT id, user_id, app_name, is_active, created_at, updated_at
            FROM api_apps WHERE user_id = ?
        ''', (user_id,))
        row = await cursor.fetchone()
        if not row:
            return None
        return {
            'id': row[0],
            'user_id': row[1],
            'app_name': row[2],
            'is_active': bool(row[3]),
            'created_at': row[4],
            'updated_at': row[5],
        }

    async def get_api_app_by_token(self, token: str) -> Optional[Dict[str, Any]]:
        token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
        cursor = await self.conn.execute('''
            SELECT id, user_id, app_name, is_active
            FROM api_apps
            WHERE token_hash = ?
        ''', (token_hash,))
        row = await cursor.fetchone()
        if not row:
            return None
        return {
            'id': row[0],
            'user_id': row[1],
            'app_name': row[2],
            'is_active': bool(row[3]),
        }

    async def transfer_user_to_api_balance(self, user_id: int, amount: float) -> bool:
        if amount <= 0:
            return False
        balance = await self.get_balance(user_id)
        if balance < amount:
            return False
        await self.conn.execute('UPDATE users SET balance = balance - ?, api_balance = api_balance + ? WHERE user_id = ?', (amount, amount, user_id))
        await self.conn.commit()
        return True

    async def transfer_api_to_user_balance(self, user_id: int, amount: float) -> bool:
        if amount <= 0:
            return False
        cursor = await self.conn.execute('SELECT api_balance FROM users WHERE user_id = ?', (user_id,))
        row = await cursor.fetchone()
        api_balance = float(row[0] or 0) if row else 0.0
        if api_balance < amount:
            return False
        await self.conn.execute('UPDATE users SET api_balance = api_balance - ?, balance = balance + ? WHERE user_id = ?', (amount, amount, user_id))
        await self.conn.commit()
        return True

    async def get_api_balance(self, user_id: int) -> float:
        cursor = await self.conn.execute('SELECT api_balance FROM users WHERE user_id = ?', (user_id,))
        row = await cursor.fetchone()
        return float(row[0] or 0.0) if row else 0.0

    async def debit_api_balance(self, user_id: int, amount: float) -> bool:
        if amount <= 0:
            return False
        api_balance = await self.get_api_balance(user_id)
        if api_balance < amount:
            return False
        await self.conn.execute('UPDATE users SET api_balance = api_balance - ? WHERE user_id = ?', (amount, user_id))
        await self.conn.commit()
        return True

    async def log_api_usage(self, app_id: int, endpoint: str, status_code: int, cost_trx: float = 0.0, revenue_trx: float = 0.0):
        await self.conn.execute('''
            INSERT INTO api_usage_logs (app_id, endpoint, status_code, cost_trx, revenue_trx)
            VALUES (?, ?, ?, ?, ?)
        ''', (app_id, endpoint, status_code, cost_trx, revenue_trx))
        await self.conn.commit()

    async def get_api_app_stats(self, app_id: int) -> Dict[str, Any]:
        cursor = await self.conn.execute('SELECT COUNT(*) FROM api_usage_logs WHERE app_id = ?', (app_id,))
        total = (await cursor.fetchone())[0]
        cursor = await self.conn.execute('SELECT COUNT(*) FROM api_usage_logs WHERE app_id = ? AND status_code < 400', (app_id,))
        success = (await cursor.fetchone())[0]
        cursor = await self.conn.execute('SELECT COALESCE(SUM(cost_trx), 0) FROM api_usage_logs WHERE app_id = ?', (app_id,))
        cost = (await cursor.fetchone())[0] or 0.0
        cursor = await self.conn.execute('SELECT COALESCE(SUM(revenue_trx), 0) FROM api_usage_logs WHERE app_id = ?', (app_id,))
        revenue = (await cursor.fetchone())[0] or 0.0
        return {
            'requests_total': int(total),
            'requests_success': int(success),
            'success_rate': float(success / total * 100) if total else 0.0,
            'total_cost_trx': float(cost),
            'total_revenue_trx': float(revenue),
        }


db = Database()
