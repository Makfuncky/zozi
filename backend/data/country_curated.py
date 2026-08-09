"""
Curated country profiles — used as fallback when external APIs are unavailable.

Each entry in ``CURATED_COUNTRIES`` is the full country payload that
``auto_populate_async`` would return from RestCountries + World Bank.

Add new countries here as the platform expands into new markets.
"""
from __future__ import annotations

from typing import Any, Optional

# ── GCC / MENA curated profiles ────────────────────────────────────────────────
CURATED_COUNTRIES: dict[str, dict[str, Any]] = {
    "OM": {
        "code": "OM",
        "name": "Oman",
        "official_name": "Sultanate of Oman",
        "alpha3": "OMN",
        "phone_code": "+968",
        "flag_url": "https://flagcdn.com/om.svg",
        "capital": "Muscat",
        "currency": "OMR",
        "currency_symbol": "ر.ع.",
        "currency_name": "Omani Rial",
        "language": "ar",
        "timezone": "Asia/Muscat",
        "region": "Asia",
        "subregion": "Western Asia",
        "population": 5106626,
        "gdp_per_capita_usd": 17922,
        "internet_penetration_pct": 93.2,
        "economic_tier": "emerging",
    },
    "AE": {
        "code": "AE",
        "name": "United Arab Emirates",
        "official_name": "United Arab Emirates",
        "alpha3": "ARE",
        "phone_code": "+971",
        "flag_url": "https://flagcdn.com/ae.svg",
        "capital": "Abu Dhabi",
        "currency": "AED",
        "currency_symbol": "د.إ",
        "currency_name": "UAE Dirham",
        "language": "ar",
        "timezone": "Asia/Dubai",
        "region": "Asia",
        "subregion": "Western Asia",
        "population": 9770529,
        "gdp_per_capita_usd": 43487,
        "internet_penetration_pct": 100.0,
        "economic_tier": "developed",
    },
    "SA": {
        "code": "SA",
        "name": "Saudi Arabia",
        "official_name": "Kingdom of Saudi Arabia",
        "alpha3": "SAU",
        "phone_code": "+966",
        "flag_url": "https://flagcdn.com/sa.svg",
        "capital": "Riyadh",
        "currency": "SAR",
        "currency_symbol": "﷼",
        "currency_name": "Saudi Riyal",
        "language": "ar",
        "timezone": "Asia/Riyadh",
        "region": "Asia",
        "subregion": "Western Asia",
        "population": 34813871,
        "gdp_per_capita_usd": 23792,
        "internet_penetration_pct": 98.6,
        "economic_tier": "developed",
    },
    "BH": {
        "code": "BH",
        "name": "Bahrain",
        "official_name": "Kingdom of Bahrain",
        "alpha3": "BHR",
        "phone_code": "+973",
        "flag_url": "https://flagcdn.com/bh.svg",
        "capital": "Manama",
        "currency": "BHD",
        "currency_symbol": ".د.ب",
        "currency_name": "Bahraini Dinar",
        "language": "ar",
        "timezone": "Asia/Bahrain",
        "region": "Asia",
        "subregion": "Western Asia",
        "population": 1701583,
        "gdp_per_capita_usd": 22737,
        "internet_penetration_pct": 98.0,
        "economic_tier": "developed",
    },
    "KW": {
        "code": "KW",
        "name": "Kuwait",
        "official_name": "State of Kuwait",
        "alpha3": "KWT",
        "phone_code": "+965",
        "flag_url": "https://flagcdn.com/kw.svg",
        "capital": "Kuwait City",
        "currency": "KWD",
        "currency_symbol": "د.ك",
        "currency_name": "Kuwaiti Dinar",
        "language": "ar",
        "timezone": "Asia/Kuwait",
        "region": "Asia",
        "subregion": "Western Asia",
        "population": 4270563,
        "gdp_per_capita_usd": 32020,
        "internet_penetration_pct": 99.7,
        "economic_tier": "developed",
    },
    "QA": {
        "code": "QA",
        "name": "Qatar",
        "official_name": "State of Qatar",
        "alpha3": "QAT",
        "phone_code": "+974",
        "flag_url": "https://flagcdn.com/qa.svg",
        "capital": "Doha",
        "currency": "QAR",
        "currency_symbol": "ر.ق",
        "currency_name": "Qatari Riyal",
        "language": "ar",
        "timezone": "Asia/Qatar",
        "region": "Asia",
        "subregion": "Western Asia",
        "population": 2881053,
        "gdp_per_capita_usd": 61695,
        "internet_penetration_pct": 100.0,
        "economic_tier": "developed",
    },
}


def get_curated_country(code: str) -> dict[str, Any] | None:
    """Return the curated country profile for *code* (ISO 3166-1 alpha-2), or
    ``None`` if no profile exists for that code."""
    return CURATED_COUNTRIES.get(code.upper())


def get_curated_macro(code: str) -> dict[str, Any] | None:
    """Return macro-economic indicators for *code*, or ``None``."""
    country = get_curated_country(code)
    if country is None:
        return None
    return {
        "population": country.get("population"),
        "gdp_per_capita_usd": country.get("gdp_per_capita_usd"),
        "internet_penetration_pct": country.get("internet_penetration_pct"),
        "economic_tier": country.get("economic_tier"),
    }
