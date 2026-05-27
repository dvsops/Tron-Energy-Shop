import asyncio
import aiohttp
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from app.models.config import (
    TRENERGY_API_KEY,
    TRENERGY_BASE_URL,
    TRONEX_API_URL,
    TRONEX_API_KEY,
    TRONPULSE_API_URL,
    TRONPULSE_API_KEY,
    ENERGYFI_API_URL,
    ENERGYFI_API_KEY,
    ENERGY_PROVIDER_TIMEOUT_SECONDS,
    ENERGY_PROVIDER_RETRIES,
)
from app.services.api.trenergy import TrenergyAPI


@dataclass
class ProviderQuote:
    provider: str
    base_price_trx: float
    payload: Dict[str, Any]


class BaseProvider:
    name = "base"

    async def quote(self, energy_amount: int, period_id: str, user_id: Optional[int]) -> Optional[ProviderQuote]:
        raise NotImplementedError

    async def purchase(self, quote: ProviderQuote, user_wallet: str, user_id: Optional[int]) -> Dict[str, Any]:
        raise NotImplementedError


class TrenergyProvider(BaseProvider):
    name = "trenergy"

    async def quote(self, energy_amount: int, period_id: str, user_id: Optional[int]) -> Optional[ProviderQuote]:
        async with TrenergyAPI() as api:
            price_info = await api.calculate_energy_price(energy_amount, period_id, user_id)
            base_price = float(
                price_info.get("original_price_trx")
                or price_info.get("estimated_cost_trx")
                or price_info.get("final_price_trx")
                or 0.0
            )
            return ProviderQuote(
                provider=self.name,
                base_price_trx=base_price,
                payload=price_info,
            )

    async def purchase(self, quote: ProviderQuote, user_wallet: str, user_id: Optional[int]) -> Dict[str, Any]:
        async with TrenergyAPI() as api:
            result = await api.purchase_energy(
                quote.payload["energy_amount"],
                quote.payload["period_id"],
                user_wallet,
                user_id,
            )
            if not result.get("success"):
                raise RuntimeError(result.get("error", "purchase failed"))
            return {
                "success": True,
                "provider": self.name,
                "order_id": result.get("consumer_id"),
            }


class GenericEnergyProvider(BaseProvider):
    def __init__(self, name: str, base_url: str, api_key: str):
        self.name = name
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key

    async def quote(self, energy_amount: int, period_id: str, user_id: Optional[int]) -> Optional[ProviderQuote]:
        if not self.base_url:
            return None
        payload = {"energy_amount": energy_amount, "period_id": period_id, "user_id": user_id}
        data = await self._request("POST", "/quote", payload)
        base_price = float(data.get("base_price_trx", data["final_price_trx"]))
        return ProviderQuote(
            provider=self.name,
            base_price_trx=base_price,
            payload=data,
        )

    async def purchase(self, quote: ProviderQuote, user_wallet: str, user_id: Optional[int]) -> Dict[str, Any]:
        payload = {
            "quote_id": quote.payload.get("quote_id"),
            "energy_amount": quote.payload.get("energy_amount"),
            "period_id": quote.payload.get("period_id"),
            "wallet": user_wallet,
            "user_id": user_id,
        }
        data = await self._request("POST", "/purchase", payload)
        return {
            "success": bool(data.get("success", True)),
            "provider": self.name,
            "order_id": data.get("order_id"),
        }

    async def _request(self, method: str, endpoint: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        headers = {"Accept": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        url = f"{self.base_url}{endpoint}"

        for attempt in range(ENERGY_PROVIDER_RETRIES + 1):
            try:
                timeout = aiohttp.ClientTimeout(total=ENERGY_PROVIDER_TIMEOUT_SECONDS)
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    async with session.request(method, url, headers=headers, json=payload) as response:
                        response.raise_for_status()
                        return await response.json()
            except Exception:
                if attempt >= ENERGY_PROVIDER_RETRIES:
                    raise
                await asyncio.sleep(0.7 * (attempt + 1))


class EnergyMarketplace:
    def __init__(self):
        self.providers: List[BaseProvider] = [
            TrenergyProvider(),
            GenericEnergyProvider("tronex", TRONEX_API_URL, TRONEX_API_KEY),
            GenericEnergyProvider("tronpulse", TRONPULSE_API_URL, TRONPULSE_API_KEY),
            GenericEnergyProvider("energyfi", ENERGYFI_API_URL, ENERGYFI_API_KEY),
        ]

    async def get_best_quote(self, energy_amount: int, period_id: str, user_id: Optional[int]) -> ProviderQuote:
        quotes: List[ProviderQuote] = []
        for provider in self.providers:
            try:
                quote = await provider.quote(energy_amount, period_id, user_id)
                if quote:
                    quotes.append(quote)
            except Exception:
                continue

        if not quotes:
            raise RuntimeError("Нет доступных провайдеров энергии")
        return min(quotes, key=lambda q: q.base_price_trx)

    async def purchase_with_quote(self, quote: ProviderQuote, user_wallet: str, user_id: Optional[int]) -> Dict[str, Any]:
        provider = next(p for p in self.providers if p.name == quote.provider)
        purchase_result = await provider.purchase(quote, user_wallet, user_id)
        return {
            "success": purchase_result.get("success", False),
            "order_id": purchase_result.get("order_id"),
            "provider": quote.provider,
            "price_info": quote.payload,
            "base_price_trx": quote.base_price_trx,
        }

    async def purchase_with_best_price(
        self, energy_amount: int, period_id: str, user_wallet: str, user_id: Optional[int]
    ) -> Dict[str, Any]:
        best_quote = await self.get_best_quote(energy_amount, period_id, user_id)
        return await self.purchase_with_quote(best_quote, user_wallet, user_id)


marketplace = EnergyMarketplace()
