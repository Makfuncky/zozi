from __future__ import annotations

import logging
from decimal import Decimal, ROUND_HALF_UP
from typing import Any

from providers.geography.rates import (
    RATE_CACHE_TTL_SECONDS,
    fetch_rates,
    lookup_currency_from_wikidata,
    normalize_currency_code,
    reset_rate_cache,
    rate_cache_expiry,
    _normalize_country_key,
)
from infrastructure.utils.money import to_decimal

logger = logging.getLogger(__name__)

KNOWN_CURRENCY_META: dict[str, dict[str, Any]] = {
    "AED": {
        "name": "UAE Dirham",
        "symbol": "AED",
        "locale": "en-AE",
        "decimals": 2,
        "fallback_rate": Decimal("1"),
    },
    "OMR": {
        "name": "Omani Rial",
        "symbol": "OMR",
        "locale": "en-OM",
        "decimals": 3,
        "fallback_rate": Decimal("0.10489"),
    },
    "SAR": {
        "name": "Saudi Riyal",
        "symbol": "SAR",
        "locale": "ar-SA",
        "decimals": 2,
        "fallback_rate": Decimal("1.0208"),
    },
    "QAR": {
        "name": "Qatari Riyal",
        "symbol": "QAR",
        "locale": "ar-QA",
        "decimals": 2,
        "fallback_rate": Decimal("0.99231"),
    },
    "KWD": {
        "name": "Kuwaiti Dinar",
        "symbol": "KWD",
        "locale": "ar-KW",
        "decimals": 3,
        "fallback_rate": Decimal("0.08391"),
    },
    "BHD": {
        "name": "Bahraini Dinar",
        "symbol": "BHD",
        "locale": "ar-BH",
        "decimals": 3,
        "fallback_rate": Decimal("0.10278"),
    },
    "USD": {
        "name": "US Dollar",
        "symbol": "USD",
        "locale": "en-US",
        "decimals": 2,
        "fallback_rate": Decimal("0.27225"),
    },
    "GBP": {
        "name": "British Pound",
        "symbol": "GBP",
        "locale": "en-GB",
        "decimals": 2,
        "fallback_rate": Decimal("0.21420"),
    },
    "EUR": {
        "name": "Euro",
        "symbol": "EUR",
        "locale": "en-IE",
        "decimals": 2,
        "fallback_rate": Decimal("0.25000"),
    },
    "INR": {
        "name": "Indian Rupee",
        "symbol": "INR",
        "locale": "en-IN",
        "decimals": 2,
        "fallback_rate": Decimal("22.65000"),
    },
    "PKR": {
        "name": "Pakistani Rupee",
        "symbol": "PKR",
        "locale": "en-PK",
        "decimals": 2,
        "fallback_rate": Decimal("75.80000"),
    },
}

COUNTRY_TO_CURRENCY: dict[str, str] = {
    "AE": "AED",
    "UAE": "AED",
    "UNITEDARABEMIRATES": "AED",
    "OM": "OMR",
    "OMAN": "OMR",
    "SA": "SAR",
    "SAUDIARABIA": "SAR",
    "QA": "QAR",
    "QATAR": "QAR",
    "KW": "KWD",
    "KUWAIT": "KWD",
    "BH": "BHD",
    "BAHRAIN": "BHD",
    "US": "USD",
    "USA": "USD",
    "UNITEDSTATES": "USD",
    "UNITEDSTATESOFAMERICA": "USD",
    "GB": "GBP",
    "UK": "GBP",
    "UNITEDKINGDOM": "GBP",
    "GREATBRITAIN": "GBP",
    "IE": "EUR",
    "IRELAND": "EUR",
    "DE": "EUR",
    "GERMANY": "EUR",
    "FR": "EUR",
    "FRANCE": "EUR",
    "IT": "EUR",
    "ITALY": "EUR",
    "ES": "EUR",
    "SPAIN": "EUR",
    "NL": "EUR",
    "NETHERLANDS": "EUR",
    "IN": "INR",
    "INDIA": "INR",
    "PK": "PKR",
    "PAKISTAN": "PKR",
}

def refresh_rate_cache() -> dict[str, Any]:
    reset_rate_cache()
    rates, source = fetch_rates()
    return {
        "source": source,
        "currency_count": len(rates),
        "expires_at": rate_cache_expiry(),
    }


def currency_for_country(country: str | None, default_currency: str = "OMR") -> str:
    normalized = _normalize_country_key(country)
    if not normalized:
        return default_currency
    if normalized in COUNTRY_TO_CURRENCY:
        return COUNTRY_TO_CURRENCY[normalized]
    looked_up = lookup_currency_from_wikidata(country or "")
    if looked_up:
        return looked_up
    return default_currency


def get_currency_metadata(currency_code: str) -> dict[str, Any]:
    normalized = normalize_currency_code(currency_code)
    meta = KNOWN_CURRENCY_META.get(normalized, {})
    decimals = 3 if normalized in {"OMR", "KWD", "BHD"} else 2
    return {
        "code": normalized,
        "name": meta.get("name", normalized),
        "symbol": meta.get("symbol", normalized),
        "locale": meta.get("locale", "en"),
        "decimals": int(meta.get("decimals", decimals)),
    }


def get_rate_from_aed(currency_code: str) -> tuple[Decimal, str]:
    normalized = normalize_currency_code(currency_code)
    rates, source = fetch_rates()
    rate = rates.get(normalized)
    if rate is not None:
        return rate, source
    fallback = KNOWN_CURRENCY_META.get(normalized, {}).get("fallback_rate", Decimal("1"))
    return to_decimal(fallback), "fallback"


def _quant_for_currency(currency_code: str) -> Decimal:
    decimals = get_currency_metadata(currency_code)["decimals"]
    return Decimal("1").scaleb(-decimals)


def convert_from_aed(amount: Any, currency_code: str) -> Decimal:
    normalized = normalize_currency_code(currency_code)
    rate, _ = get_rate_from_aed(normalized)
    converted = to_decimal(amount) * rate
    return converted.quantize(_quant_for_currency(normalized), rounding=ROUND_HALF_UP)


def convert_between_currencies(amount: Any, base_currency: str, target_currency: str) -> tuple[Decimal, Decimal, str]:
    base = normalize_currency_code(base_currency)
    target = normalize_currency_code(target_currency)
    if base == target:
        amount_decimal = to_decimal(amount).quantize(_quant_for_currency(target), rounding=ROUND_HALF_UP)
        return amount_decimal, Decimal("1"), "direct"

    base_rate, base_source = get_rate_from_aed(base)
    target_rate, target_source = get_rate_from_aed(target)
    amount_aed = to_decimal(amount) if base == "AED" else (to_decimal(amount) / base_rate)
    converted = (amount_aed * target_rate).quantize(_quant_for_currency(target), rounding=ROUND_HALF_UP)
    effective_rate = (target_rate if base == "AED" else (target_rate / base_rate)).quantize(Decimal("0.000001"))
    source = target_source if target_source == base_source else f"{base_source}->{target_source}"
    return converted, effective_rate, source


def money_to_minor_units_for_currency(amount: Any, currency_code: str) -> int:
    normalized = normalize_currency_code(currency_code)
    decimals = get_currency_metadata(normalized)["decimals"]
    factor = 10 ** decimals
    converted = convert_from_aed(amount, normalized)
    return int((converted * Decimal(str(factor))).to_integral_value(rounding=ROUND_HALF_UP))


def get_currency_context(
    *,
    country: str | None = None,
    currency: str | None = None,
    default_currency: str = "OMR",
) -> dict[str, Any]:
    resolved_currency = (
        normalize_currency_code(currency, default="")
        if currency
        else currency_for_country(country, default_currency=default_currency)
    ) or default_currency
    metadata = get_currency_metadata(resolved_currency)
    rate_from_aed, source = get_rate_from_aed(resolved_currency)
    return {
        "currency": metadata["code"],
        "currency_code": metadata["code"],
        "symbol": metadata["symbol"],
        "name": metadata["name"],
        "locale": metadata["locale"],
        "decimals": metadata["decimals"],
        "country": country,
        "rate_from_aed": float(rate_from_aed),
        "source": source,
    }



