from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from app.models.database import db
from app.keyboards.user import get_smart_menu_keyboard, get_back_keyboard
from app.services.api.tron import tron_manager
from app.utils.helpers import safe_edit_or_send_message


PERIOD_TITLE = {
    "15min": "15 минут",
    "1hour": "1 час",
    "24hours": "24 часа",
}


async def _render_smart_menu(callback: types.CallbackQuery):
    settings = await db.get_smart_settings(callback.from_user.id)
    if not settings:
        settings = {
            "enabled": False,
            "price_threshold_trx": 1.0,
            "predicted_daily_energy": 30000,
            "target_energy_amount": 30000,
            "period_id": "24hours",
            "min_energy_trigger": 10000,
        }
        await db.upsert_smart_settings(
            callback.from_user.id,
            settings["enabled"],
            settings["price_threshold_trx"],
            False,
            settings["predicted_daily_energy"],
            settings["target_energy_amount"],
            settings["period_id"],
            settings["min_energy_trigger"],
        )

    user = await db.get_user(callback.from_user.id)
    wallet = (user or {}).get("trx_wallet")
    energy_now = None
    if wallet:
        try:
            energy_now = int(await tron_manager.get_energy_available(wallet))
        except Exception:
            energy_now = None

    text = (
        "🤖 Автопокупка энергии\n\n"
        f"Статус: {'ON ✅' if settings['enabled'] else 'OFF ❌'}\n"
        f"Кошелек: {wallet or 'не задан'}\n"
        f"Энергия сейчас: {(f'{energy_now:,}' if energy_now is not None else 'нет данных')}\n"
        f"Запуск, если энергия < {int(settings.get('min_energy_trigger', 10000)):,}\n"
        f"Объем одной автопокупки: {int(settings.get('target_energy_amount', 30000)):,}\n"
        f"Период: {PERIOD_TITLE.get(settings.get('period_id', '24hours'), settings.get('period_id', '24hours'))}\n"
        f"Макс цена: {settings['price_threshold_trx']:.4f} TRX\n\n"
        "Перед каждой автопокупкой бот проверяет ваш баланс.\n"
        "Если средств не хватает — отправляет уведомление."
    )
    await safe_edit_or_send_message(
        callback.bot,
        callback.message.chat.id,
        callback.message.message_id,
        text,
        get_smart_menu_keyboard(settings),
    )


async def _save_with_current(callback: types.CallbackQuery, **override):
    settings = await db.get_smart_settings(callback.from_user.id) or {}
    await db.upsert_smart_settings(
        callback.from_user.id,
        bool(override.get("enabled", settings.get("enabled", False))),
        float(override.get("price_threshold_trx", settings.get("price_threshold_trx", 1.0))),
        False,
        int(override.get("predicted_daily_energy", settings.get("predicted_daily_energy", 30000))),
        int(override.get("target_energy_amount", settings.get("target_energy_amount", 30000))),
        str(override.get("period_id", settings.get("period_id", "24hours"))),
        int(override.get("min_energy_trigger", settings.get("min_energy_trigger", 10000))),
    )


async def callback_smart_menu(callback: types.CallbackQuery):
    await _render_smart_menu(callback)
    await callback.answer()


async def callback_smart_toggle(callback: types.CallbackQuery):
    settings = await db.get_smart_settings(callback.from_user.id) or {}
    await _save_with_current(callback, enabled=not bool(settings.get("enabled", False)))
    await _render_smart_menu(callback)
    await callback.answer("Настройки обновлены")


async def callback_smart_threshold(callback: types.CallbackQuery):
    value = float(callback.data.split("_")[-1])
    await _save_with_current(callback, price_threshold_trx=value)
    await _render_smart_menu(callback)
    await callback.answer(f"Макс цена: {value} TRX")


async def callback_smart_threshold_custom(callback: types.CallbackQuery, state: FSMContext):
    text = (
        "✏️ Введите ваш лимит цены для автопокупки в TRX.\n\n"
        "Пример: 8.9556\n"
        "Допускаются точка или запятая."
    )
    await safe_edit_or_send_message(
        callback.bot,
        callback.message.chat.id,
        callback.message.message_id,
        text,
        get_back_keyboard("smart_menu"),
    )
    await state.set_state("waiting_for_smart_custom_threshold")
    await callback.answer()


async def process_smart_custom_threshold_input(message: types.Message, state: FSMContext):
    try:
        raw = message.text.strip().replace(",", ".")
        value = float(raw)
    except Exception:
        await message.answer("❌ Неверный формат. Введите число, например 8.9556")
        return

    if value <= 0:
        await message.answer("❌ Лимит должен быть больше 0")
        return
    if value > 1000:
        await message.answer("❌ Слишком большой лимит. Введите значение до 1000 TRX")
        return

    await _save_with_current(message, price_threshold_trx=value)
    await state.finish()
    await message.answer(
        f"✅ Новый лимит: {value:.4f} TRX",
        reply_markup=get_back_keyboard("smart_menu"),
    )


async def callback_smart_target(callback: types.CallbackQuery):
    target = int(callback.data.split("_")[-1])
    await _save_with_current(callback, target_energy_amount=target)
    await _render_smart_menu(callback)
    await callback.answer(f"Объем: {target:,}")


async def callback_smart_period(callback: types.CallbackQuery):
    period_id = callback.data.split("_")[-1]
    await _save_with_current(callback, period_id=period_id)
    await _render_smart_menu(callback)
    await callback.answer(f"Период: {PERIOD_TITLE.get(period_id, period_id)}")


async def callback_smart_trigger(callback: types.CallbackQuery):
    trigger = int(callback.data.split("_")[-1])
    await _save_with_current(callback, min_energy_trigger=trigger)
    await _render_smart_menu(callback)
    await callback.answer(f"Порог запуска: {trigger:,}")


def register_account_handlers(dp: Dispatcher):
    dp.register_callback_query_handler(callback_smart_menu, text="smart_menu", state="*")
    dp.register_callback_query_handler(callback_smart_toggle, text="smart_toggle", state="*")
    dp.register_callback_query_handler(callback_smart_threshold_custom, text="smart_threshold_custom", state="*")
    dp.register_callback_query_handler(callback_smart_threshold, text_startswith="smart_threshold_", state="*")
    dp.register_callback_query_handler(callback_smart_target, text_startswith="smart_target_", state="*")
    dp.register_callback_query_handler(callback_smart_period, text_startswith="smart_period_", state="*")
    dp.register_callback_query_handler(callback_smart_trigger, text_startswith="smart_trigger_", state="*")
    dp.register_message_handler(process_smart_custom_threshold_input, state="waiting_for_smart_custom_threshold")
