"""Pure currency primitives — no external rate-feed dependencies.

Kernel must not import from rate or geography modules. Rate-dependent
functions live in infrastructure.utils.currency_service. This module
provides the pure currency metadata, normalisation, and conversion
arithmetic for use across domains without coupling to external feeds.
"""
from __future__ import annotations

import re
from decimal import Decimal, ROUND_HALF_UP
from typing import Any

from kernel.money import to_decimal


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


def normalize_currency_code(code: str | None, default: str = "OMR") -> str:
    if not code:
        return default
    normalized = re.sub(r"[^A-Z]", "", code.upper())
    if len(normalized) == 3:
        return normalized
    return default


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


def _quant_for_currency(currency_code: str) -> Decimal:
    decimals = get_currency_metadata(currency_code)["decimals"]
    return Decimal("1").scaleb(-decimals)


def convert_from_aed(amount: Any, rate: Decimal, currency_code: str) -> Decimal:
    normalized = normalize_currency_code(currency_code)
    converted = to_decimal(amount) * rate
    return converted.quantize(_quant_for_currency(normalized), rounding=ROUND_HALF_UP)


def convert_between_currencies(
    amount: Any,
    base_rate: Decimal,
    target_rate: Decimal,
    base_currency: str,
    target_currency: str,
) -> tuple[Decimal, Decimal, str]:
    base = normalize_currency_code(base_currency)
    target = normalize_currency_code(target_currency)
    if base == target:
        amount_decimal = to_decimal(amount).quantize(
            _quant_for_currency(target), rounding=ROUND_HALF_UP
        )
        return amount_decimal, Decimal("1"), "direct"

    amount_aed = to_decimal(amount) if base == "AED" else (to_decimal(amount) / base_rate)
    converted = (amount_aed * target_rate).quantize(
        _quant_for_currency(target), rounding=ROUND_HALF_UP
    )
    effective_rate = (
        target_rate if base == "AED" else (target_rate / base_rate)
    ).quantize(Decimal("0.000001"))
    return converted, effective_rate, "direct"


def get_rate_from_aed(rates: dict[str, Decimal], currency_code: str) -> tuple[Decimal, str]:
    normalized = normalize_currency_code(currency_code)
    rate = rates.get(normalized)
    if rate is not None:
        return rate, "direct"
    fallback = KNOWN_CURRENCY_META.get(normalized, {}).get("fallback_rate", Decimal("1"))
    return to_decimal(fallback), "fallback"


def money_to_minor_units_for_currency(amount: Any, rate: Decimal, currency_code: str) -> int:
    normalized = normalize_currency_code(currency_code)
    decimals = get_currency_metadata(normalized)["decimals"]
    factor = 10 ** decimals
    converted = convert_from_aed(amount, rate, normalized)
    return int((converted * Decimal(str(factor))).to_integral_value(rounding=ROUND_HALF_UP))


__all__ = [
    "KNOWN_CURRENCY_META",
    "COUNTRY_TO_CURRENCY",
    "normalize_currency_code",
    "get_currency_metadata",
    "convert_from_aed",
    "convert_between_currencies",
    "get_rate_from_aed",
    "money_to_minor_units_for_currency",
]
