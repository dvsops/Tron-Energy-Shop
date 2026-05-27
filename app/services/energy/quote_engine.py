from typing import Dict, Any
from app.models.database import db
from app.services.energy.marketplace import marketplace, ProviderQuote


async def build_user_quote(user_id: int, energy_amount: int, period_id: str) -> Dict[str, Any]:
    best_quote: ProviderQuote = await marketplace.get_best_quote(energy_amount, period_id, user_id)
    base_price = float(best_quote.base_price_trx)

    custom_margin = await db.get_user_margin(user_id)
    if custom_margin is None:
        margin_percent = await db.get_global_energy_margin()
        margin_type = "global"
    else:
        margin_percent = custom_margin
        margin_type = "individual"

    margin_amount = base_price * (margin_percent / 100)
    price_with_margin = base_price + margin_amount

    subscription = await db.get_active_subscription(user_id)
    subscription_discount_percent = float(subscription["discount_percent"]) if subscription else 0.0
    subscription_discount_amount = price_with_margin * (subscription_discount_percent / 100)
    final_price = max(0.0, price_with_margin - subscription_discount_amount)

    return {
        "quote": best_quote,
        "provider": best_quote.provider,
        "base_price_trx": base_price,
        "margin_percent": float(margin_percent),
        "margin_type": margin_type,
        "margin_amount_trx": float(margin_amount),
        "price_with_margin_trx": float(price_with_margin),
        "subscription_discount_percent": subscription_discount_percent,
        "subscription_discount_amount_trx": float(subscription_discount_amount),
        "final_price_trx": float(final_price),
    }
