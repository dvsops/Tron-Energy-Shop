import aiohttp
import ssl
from app.models.config import COINGECKO_API_URL, REQUIRED_CHANNEL_ID
from app.services.api.tron import tron_manager
from app.models.database import db
from typing import Optional


async def check_subscription(bot, user_id: int) -> bool:
    try:
        if not REQUIRED_CHANNEL_ID:
            return True
        
        member = await bot.get_chat_member(REQUIRED_CHANNEL_ID, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except Exception as e:
        return False


async def get_trx_price() -> float:
    try:
        try:
            db_price = await db.get_trx_price()
            if db_price > 0:
                print(f"📊 TRX курс из БД: ${db_price:.4f}")
                return db_price
        except Exception as e:
            print(f"❌ Ошибка получения курса из БД: {e}")
        
        price = await _get_price_from_coingecko()
        if price > 0:
            return price
        
        price = await _get_price_from_binance()
        if price > 0:
            return price
        
        print("⚠️ Все API недоступны, используем примерный курс")
        return 0.34
        
    except Exception as e:
        print(f"Ошибка при получении курса TRX: {e}")
        return 0.34


async def _get_price_from_coingecko() -> float:
    try:
        url = COINGECKO_API_URL
        
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        ssl_context.set_ciphers('HIGH:!DH:!aNULL')
        
        connector = aiohttp.TCPConnector(
            ssl=ssl_context,
            limit=10,
            limit_per_host=5,
            keepalive_timeout=30,
            enable_cleanup_closed=True
        )
        async with aiohttp.ClientSession(connector=connector) as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=15, connect=5)) as response:
                if response.status == 200:
                    data = await response.json()
                    price = data.get('tron', {}).get('usd', 0.0)
                    print(f"✅ CoinGecko TRX: ${price}")
                    return price
        return 0.0
    except Exception as e:
        print(f"❌ CoinGecko error: {e}")
        return 0.0


async def _get_price_from_binance() -> float:
    try:
        url = "https://api.binance.com/api/v3/ticker/price?symbol=TRXUSDT"
        
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        ssl_context.set_ciphers('HIGH:!DH:!aNULL')
        
        connector = aiohttp.TCPConnector(
            ssl=ssl_context,
            limit=10,
            limit_per_host=5,
            keepalive_timeout=30,
            enable_cleanup_closed=True
        )
        async with aiohttp.ClientSession(connector=connector) as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=15, connect=5)) as response:
                if response.status == 200:
                    data = await response.json()
                    price = float(data.get('price', 0))
                    print(f"✅ Binance TRX: ${price}")
                    return price
        return 0.0
    except Exception as e:
        print(f"❌ Binance error: {e}")
        return 0.0


def get_referral_link(bot_username: str, user_id: int) -> str:
    return f"https://t.me/{bot_username}?start=ref_{user_id}"


def validate_trx_address(address: str) -> bool:
    return tron_manager.is_valid_address(address)


def format_purchase_history(purchases) -> str:
    if not purchases:
        return "У вас пока нет покупок."
    
    history_text = ""
    for purchase in purchases:
        history_text += f"⚡️ {purchase['energy_amount']:,} энергии\n"
        history_text += f"📅 {purchase['period_days']} дней\n"
        history_text += f"📅 {purchase['created_at'][:10]}\n\n"
        history_text += f"📅 {purchase['wallet_address']}\n\n"

    return history_text.strip()


def get_main_menu_image(locale: str) -> str:
    if locale == 'en':
        return 'images/gl_menu_eng.jpg'
    else:
        return 'images/gl_menu_ru.jpg'


async def safe_edit_message(bot, chat_id: int, message_id: int, text: str, reply_markup=None, parse_mode=None):
    try:
        try:
            await bot.edit_message_caption(
                chat_id=chat_id,
                message_id=message_id,
                caption=text,
                reply_markup=reply_markup,
                parse_mode=parse_mode
            )
            return True
        except Exception as e1:
            if "message is not modified" in str(e1).lower():
                return True
            try:
                await bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=message_id,
                    text=text,
                    reply_markup=reply_markup,
                    parse_mode=parse_mode
                )
                return True
            except Exception as e2:
                if "message is not modified" in str(e2).lower():
                    return True
                print(f"❌ Ошибка редактирования текста: {e2}")
                return False
                
    except Exception as e:
        print(f"❌ Критическая ошибка редактирования: {e}")
        return False


async def safe_edit_or_send_message(bot, chat_id: int, message_id: int, text: str, reply_markup=None, parse_mode=None):
    try:
        if await safe_edit_message(bot, chat_id, message_id, text, reply_markup, parse_mode):
            return True
        
        await bot.delete_message(chat_id=chat_id, message_id=message_id)
        await bot.send_message(
            chat_id=chat_id,
            text=text,
            reply_markup=reply_markup,
            parse_mode=parse_mode
        )
        return True
    except Exception as e:
        print(f"❌ Ошибка в safe_edit_or_send_message: {e}")
        await bot.send_message(
            chat_id=chat_id,
            text=text,
            reply_markup=reply_markup,
            parse_mode=parse_mode
        )
        return True


async def safe_edit_or_send_photo(bot, chat_id: int, message_id: int, text: str, photo_path: str, reply_markup=None, parse_mode=None):
    try:
        if await safe_edit_message(bot, chat_id, message_id, text, reply_markup, parse_mode):
            return True
        
        await bot.delete_message(chat_id=chat_id, message_id=message_id)
        with open(photo_path, 'rb') as photo:
            await bot.send_photo(
                chat_id=chat_id,
                photo=photo,
                caption=text,
                reply_markup=reply_markup,
                parse_mode=parse_mode
            )
        return True
    except Exception as e:
        print(f"❌ Ошибка в safe_edit_or_send_photo: {e}")
        with open(photo_path, 'rb') as photo:
            await bot.send_photo(
                chat_id=chat_id,
                photo=photo,
                caption=text,
                reply_markup=reply_markup,
                parse_mode=parse_mode
            )
        return True


async def safe_edit_message_with_media(bot, chat_id: int, message_id: int, text: str, reply_markup=None, video_file=None):
    try:
        if await safe_edit_message(bot, chat_id, message_id, text, reply_markup):
            return True
        
        if video_file:
            try:
                await bot.delete_message(chat_id=chat_id, message_id=message_id)
                
                with open(video_file, 'rb') as video:
                    await bot.send_video(
                        chat_id=chat_id,
                        video=video,
                        caption=text,
                        reply_markup=reply_markup
                    )
                return True
            except Exception as e:
                print(f"❌ Ошибка при замене сообщения с медиа: {e}")
                await bot.send_message(
                    chat_id=chat_id,
                    text=text,
                    reply_markup=reply_markup
                )
                return True
        
        await bot.send_message(
            chat_id=chat_id,
            text=text,
            reply_markup=reply_markup
        )
        return True
        
    except Exception as e:
        print(f"❌ Критическая ошибка в safe_edit_message_with_media: {e}")
        return False


async def get_or_create_first_message(bot, user_id: int, chat_id: int, text: str, reply_markup=None, media_file=None, parse_mode=None):
    try:
        message_id, saved_chat_id = await db.get_first_message(user_id)
        
        if message_id and saved_chat_id:
            if await safe_edit_message(bot, saved_chat_id, message_id, text, reply_markup, parse_mode):
                return message_id, saved_chat_id
            
            if media_file:
                try:
                    await bot.delete_message(chat_id=saved_chat_id, message_id=message_id)
                    
                    if media_file.endswith('.mp4'):
                        with open(media_file, 'rb') as video:
                            sent_message = await bot.send_video(
                                chat_id=chat_id,
                                video=video,
                                caption=text,
                                reply_markup=reply_markup,
                                parse_mode=parse_mode
                            )
                    else:
                        with open(media_file, 'rb') as photo:
                            sent_message = await bot.send_photo(
                                chat_id=chat_id,
                                photo=photo,
                                caption=text,
                                reply_markup=reply_markup,
                                parse_mode=parse_mode
                            )
                    
                    await db.set_first_message(user_id, sent_message.message_id, chat_id)
                    return sent_message.message_id, chat_id
                except Exception as e:
                    print(f"❌ Ошибка при замене сообщения с медиа: {e}")
                    sent_message = await bot.send_message(
                        chat_id=chat_id,
                        text=text,
                        reply_markup=reply_markup,
                        parse_mode=parse_mode
                    )
                    await db.set_first_message(user_id, sent_message.message_id, chat_id)
                    return sent_message.message_id, chat_id
            
            sent_message = await bot.send_message(
                chat_id=chat_id,
                text=text,
                reply_markup=reply_markup,
                parse_mode=parse_mode
            )
            await db.set_first_message(user_id, sent_message.message_id, chat_id)
            return sent_message.message_id, chat_id
        
        if media_file:
            if media_file.endswith('.mp4'):
                with open(media_file, 'rb') as video:
                    sent_message = await bot.send_video(
                        chat_id=chat_id,
                        video=video,
                        caption=text,
                        reply_markup=reply_markup,
                        parse_mode=parse_mode
                    )
            else:
                with open(media_file, 'rb') as photo:
                    sent_message = await bot.send_photo(
                        chat_id=chat_id,
                        photo=photo,
                        caption=text,
                        reply_markup=reply_markup,
                        parse_mode=parse_mode
                    )
        else:
            sent_message = await bot.send_message(
                chat_id=chat_id,
                text=text,
                reply_markup=reply_markup,
                parse_mode=parse_mode
            )
        
        await db.set_first_message(user_id, sent_message.message_id, chat_id)
        
        return sent_message.message_id, chat_id
        
    except Exception as e:
        print(f"❌ Ошибка в get_or_create_first_message: {e}")
        if media_file:
            if media_file.endswith('.mp4'):
                with open(media_file, 'rb') as video:
                    sent_message = await bot.send_video(
                        chat_id=chat_id,
                        video=video,
                        caption=text,
                        reply_markup=reply_markup,
                        parse_mode=parse_mode
                    )
            else:
                with open(media_file, 'rb') as photo:
                    sent_message = await bot.send_photo(
                        chat_id=chat_id,
                        photo=photo,
                        caption=text,
                        reply_markup=reply_markup,
                        parse_mode=parse_mode
                    )
        else:
            sent_message = await bot.send_message(
                chat_id=chat_id,
                text=text,
                reply_markup=reply_markup,
                parse_mode=parse_mode
            )
        await db.set_first_message(user_id, sent_message.message_id, chat_id)
        return sent_message.message_id, chat_id
