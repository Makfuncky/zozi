from __future__ import annotations

import asyncio
import json
import logging
import os
from datetime import datetime, date
from decimal import Decimal
from typing import Any, Optional, Callable, Awaitable

import httpx
from fastapi import APIRouter

from utils.config import settings
from utils.circuit_breaker import CircuitBreakerWithRetry, retry
from services.legal_contract_service import generate_all_legal_documents
from data.country_curated import get_curated_country, get_curated_macro
from data.curated_cities import get_cities as get_curated_cities
from data.vat_rates import get_vat_rate, get_legal_defaults
from data.category_tax_profiles import get_category_tax_profile

logger = logging.getLogger(__name__)

REDIS_TTL_SECONDS = 172800
CACHE_TTL_SECONDS = 172800
router = APIRouter()

api_breaker = CircuitBreakerWithRetry(
    failure_threshold=3,
    recovery_timeout=30.0,
    retry_count=2,
    retry_delay=0.5,
    retry_backoff=2.0,
)


def _get_redis():
    try:
        import redis
        return redis.Redis.from_url(settings.redis_url, decode_responses=True, socket_connect_timeout=2, socket_timeout=5)
    except Exception as e:
        logger.debug("Redis unavailable: %s", e)
        return None


def _cache_key(country_code: str) -> str:
    return f"country:auto_populate:{country_code}"


async def _execute_with_timeout(coro, timeout: float, name: str) -> dict:
    try:
        result = await asyncio.wait_for(coro, timeout=timeout)
        return {"success": True, "data": result, "error": None}
    except asyncio.TimeoutError:
        logger.warning("API timeout: %s", name)
        return {"success": False, "data": None, "error": f"{name} timed out after {timeout}s"}
    except Exception as e:
        logger.warning("API error: %s - %s", name, str(e))
        return {"success": False, "data": None, "error": str(e)}


REST_COUNTRIES_URL = "https://restcountries.com/v3.1"
WORLD_BANK_URL = "https://api.worldbank.org/v2/country"
GEO_NAMES_URL = "https://api.geonames.org/searchJSON"
NAGER_DATE_URL = "https://date.nager.at/api/v3"
VAT_RATES_URL = "https://api.vat-rates.com/api"

DEFAULT_TIMEOUT = 10.0
EXTENDED_TIMEOUT = 15.0

GATEWAY_REGISTRY = {
    "stripe": {"regions": ["GLOBAL"], "currencies": ["*"], "setup_days": 1, "avg_fee": 2.9, "name": "Stripe", "type": "card"},
    "tap": {"regions": ["ME", "KW", "BH", "AE", "OM", "SA"], "currencies": ["KWD", "BHD", "AED", "OMR", "SAR", "SAU"], "setup_days": 14, "avg_fee": 2.75, "name": "TAP", "type": "card"},
    "thawani": {"regions": ["OM"], "currencies": ["OMR"], "setup_days": 7, "avg_fee": 2.5, "name": "Thawani", "type": "wallet"},
    "mada": {"regions": ["SA"], "currencies": ["SAR"], "setup_days": 30, "avg_fee": 1.5, "name": "Mada", "type": "card"},
    "hyperpay": {"regions": ["ME", "SA", "AE"], "currencies": ["*"], "setup_days": 10, "avg_fee": 2.75, "name": "Hyperpay", "type": "card"},
    "paytabs": {"regions": ["ME", "SA", "AE", "OM"], "currencies": ["*"], "setup_days": 5, "avg_fee": 2.5, "name": "PayTabs", "type": "card"},
    "tabby": {"regions": ["ME", "SA", "AE", "KW"], "currencies": ["*"], "setup_days": 3, "avg_fee": 4.0, "name": "Tabby", "type": "bnpl"},
    "klarna": {"regions": ["EU", "NA"], "currencies": ["EUR", "USD", "GBP"], "setup_days": 5, "avg_fee": 2.99, "name": "Klarna", "type": "bnpl"},
    "omannet": {"regions": ["OM"], "currencies": ["OMR"], "setup_days": 21, "avg_fee": 1.8, "name": "OmanNet", "type": "card"},
    "stc_pay": {"regions": ["SA"], "currencies": ["SAR"], "setup_days": 14, "avg_fee": 2.0, "name": "STC Pay", "type": "wallet"},
}

BASE_COMMISSIONS = {
    "electronics": {"min": 0.04, "max": 0.08, "suggested": 0.06},
    "fashion": {"min": 0.12, "max": 0.22, "suggested": 0.17},
    "groceries": {"min": 0.02, "max": 0.05, "suggested": 0.035},
    "health_beauty": {"min": 0.05, "max": 0.10, "suggested": 0.075},
    "home_furniture": {"min": 0.03, "max": 0.08, "suggested": 0.055},
    "automotive": {"min": 0.02, "max": 0.06, "suggested": 0.04},
    "sports": {"min": 0.05, "max": 0.12, "suggested": 0.085},
    "books_media": {"min": 0.01, "max": 0.05, "suggested": 0.03},
    "toys_games": {"min": 0.05, "max": 0.15, "suggested": 0.10},
    "digital_goods": {"min": 0.05, "max": 0.15, "suggested": 0.10},
    "jewelry": {"min": 0.10, "max": 0.20, "suggested": 0.15},
    "pet_supplies": {"min": 0.03, "max": 0.10, "suggested": 0.065},
}

KYC_REQUIREMENTS = {
    "basic": {
        "documents": ["national_id"],
        "verification_days": 1,
        "requires_commercial": False,
    },
    "standard": {
        "documents": ["national_id", "commercial_register", "bank_statement"],
        "verification_days": 3,
        "requires_commercial": True,
    },
    "strict": {
        "documents": ["national_id", "commercial_register", "vat_certificate", "bank_statement", "trade_license"],
        "verification_days": 7,
        "requires_commercial": True,
    },
}

LEGAL_RULES = {
    "GCC": {
        "minimum_order_age": 18,
        "max_returns_allowed": 3,
        "return_window_days": 14,
        "refund_processing_days": 7,
        "requires_commercial_license": True,
        "requires_vat_registration": True,
        "product_restrictions": ["alcohol", "pork", "gambling"],
    },
    "ME": {
        "minimum_order_age": 18,
        "max_returns_allowed": 3,
        "return_window_days": 14,
        "refund_processing_days": 7,
        "requires_commercial_license": True,
        "requires_vat_registration": True,
        "product_restrictions": ["alcohol", "pork"],
    },
    "default": {
        "minimum_order_age": 18,
        "max_returns_allowed": 3,
        "return_window_days": 14,
        "refund_processing_days": 7,
        "requires_commercial_license": False,
        "requires_vat_registration": False,
        "product_restrictions": [],
    },
}

INTERNET_PENETRATION_BY_REGION = {
    "GCC": 97.9,
    "ME": 75.0,
    "EU": 90.0,
    "NA": 92.0,
    "APAC": 70.0,
    "default": 50.0,
}


def _first_currency(data: dict) -> tuple[list[str], str | None, str | None]:
    currencies = data.get("currencies") or {}
    codes = list(currencies.keys())
    if not codes:
        return [], None, None
    first = currencies.get(codes[0]) or {}
    return codes, first.get("symbol"), first.get("name")


def _phone_code(data: dict) -> str:
    idd = data.get("idd") or {}
    root = str(idd.get("root") or "").strip()
    suffixes = idd.get("suffixes") or []
    suffix = str(suffixes[0]).strip() if suffixes else ""
    if root or suffix:
        return f"{root}{suffix}"
    return ""


def _normalize_rest_country(data: dict) -> dict:
    currencies, currency_symbol, currency_name = _first_currency(data)
    languages = data.get("languages") or {}
    timezones = data.get("timezones") or []
    return {
        "code": data.get("cca2", ""),
        "name": data.get("name", {}).get("common", ""),
        "official_name": data.get("name", {}).get("official", ""),
        "alpha3": data.get("cca3", ""),
        "phone_code": _phone_code(data),
        "flag_url": data.get("flags", {}).get("svg") or data.get("flags", {}).get("png", ""),
        "latitude": data.get("latlng", [None, None])[0],
        "longitude": data.get("latlng", [None, None])[1],
        "capital": data.get("capital", [""])[0] if data.get("capital") else "",
        "languages": list(languages.keys()) or list(languages.values()),
        "currencies": currencies,
        "currency_symbol": currency_symbol,
        "currency_name": currency_name,
        "timezone": timezones[0] if timezones else "UTC",
        "region": data.get("region", ""),
        "subregion": data.get("subregion", ""),
        "population": data.get("population"),
    }


async def fetch_rest_countries(search: str) -> Optional[dict]:
    async def _fetch():
        term = str(search or "").strip()
        if not term:
            return None
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
            if term.isalpha() and len(term) in (2, 3):
                resp = await client.get(f"{REST_COUNTRIES_URL}/alpha/{term.upper()}")
            else:
                resp = await client.get(f"{REST_COUNTRIES_URL}/name/{term}", params={"fullText": "true"})
                if resp.status_code == 404:
                    resp = await client.get(f"{REST_COUNTRIES_URL}/name/{term}")
            if resp.status_code != 200:
                return None
            data = resp.json()
            if isinstance(data, list):
                data = data[0]
            return _normalize_rest_country(data)
    try:
        return await retry(_fetch, retries=2, delay=0.5, backoff=2.0, exceptions=(httpx.HTTPStatusError, httpx.RequestError, asyncio.TimeoutError))
    except Exception as e:
        logger.debug("fetch_rest_countries failed: %s", e)
        return None


async def fetch_world_bank_data(code: str) -> Optional[dict]:
    async def _fetch():
        indicators = {
            "gdp_per_capita_usd": "NY.GDP.PCAP.CD",
            "population": "SP.POP.TOTL",
            "internet_penetration_pct": "IT.NET.USER.ZS",
        }

        async def _indicator(client: httpx.AsyncClient, field: str, indicator: str) -> tuple[str, float | None]:
            resp = await client.get(f"{WORLD_BANK_URL}/{code}/indicator/{indicator}", params={"format": "json", "per_page": 5})
            if resp.status_code != 200:
                return field, None
            data = resp.json()
            if not isinstance(data, list) or len(data) < 2:
                return field, None
            for row in data[1] or []:
                value = row.get("value")
                if value is not None:
                    return field, float(value)
            return field, None

        async with httpx.AsyncClient(timeout=EXTENDED_TIMEOUT) as client:
            values = await asyncio.gather(*[
                _indicator(client, field, indicator)
                for field, indicator in indicators.items()
            ])
            result = {field: value for field, value in values if value is not None}
            return result or None
    try:
        return await retry(_fetch, retries=2, delay=0.5, backoff=2.0, exceptions=(httpx.HTTPStatusError, httpx.RequestError, asyncio.TimeoutError))
    except Exception as e:
        logger.debug("fetch_world_bank_data failed: %s", e)
        return None


async def fetch_geodb_cities(code: str, limit: int = 20) -> list[dict]:
    async def _fetch():
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
            resp = await client.get(f"https://geodb-studios.github.io/rest-countries/api/{code}.json")
            if resp.status_code != 200:
                return []
            data = resp.json()
            cities = data.get("data", [])[:limit]
            return [
                {
                    "name": c.get("name"),
                    "name_local": c.get("nameLocal"),
                    "latitude": c.get("latitude"),
                    "longitude": c.get("longitude"),
                    "population": c.get("population"),
                    "is_capital": c.get("isCapital", False),
                    "region": c.get("region", ""),
                }
                for c in cities
            ]
    try:
        return await retry(_fetch, retries=2, delay=0.5, backoff=2.0, exceptions=(httpx.HTTPStatusError, httpx.RequestError, asyncio.TimeoutError))
    except Exception as e:
        logger.debug("fetch_geodb_cities failed: %s", e)
        return []


async def fetch_public_holidays(code: str, year: int = None) -> list[dict]:
    year = year or datetime.utcnow().year
    async def _fetch():
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
            iso_code = {"GB": "GB", "AE": "AE", "SA": "SA", "OM": "OM", "KW": "KW", "BH": "BH"}
            nager_code = iso_code.get(code.upper(), code.upper())
            resp = await client.get(f"{NAGER_DATE_URL}/publicholidays/{year}/{nager_code}")
            if resp.status_code != 200:
                return []
            holidays = resp.json()
            return [
                {
                    "name": h.get("name"),
                    "date": h.get("date"),
                    "local_name": h.get("localName"),
                }
                for h in holidays
            ]
    try:
        return await retry(_fetch, retries=2, delay=0.5, backoff=2.0, exceptions=(httpx.HTTPStatusError, httpx.RequestError, asyncio.TimeoutError))
    except Exception as e:
        logger.debug("fetch_public_holidays failed: %s", e)
        return []


async def fetch_vat_rate(country_code: str) -> Optional[float]:
    async def _fetch():
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
            resp = await client.get(f"{VAT_RATES_URL}/rates/{country_code}")
            if resp.status_code != 200:
                gcc_rates = {"SA": 15, "AE": 5, "OM": 5, "BH": 5, "KW": 5}
                return gcc_rates.get(country_code.upper(), 0.05) * 0.01
            data = resp.json()
            return float(data.get("standard_rate", 0))
    try:
        return await retry(_fetch, retries=2, delay=0.5, backoff=2.0, exceptions=(httpx.HTTPStatusError, httpx.RequestError, asyncio.TimeoutError))
    except Exception as e:
        logger.debug("fetch_vat_rate failed: %s", e)
        gcc_rates = {"SA": 15, "AE": 5, "OM": 5, "BH": 5, "KW": 5}
        return gcc_rates.get(country_code.upper(), 5) * 0.01


def calculate_confidence_score(rest_data: Optional[dict], wb_data: Optional[dict], cities: list) -> float:
    """Calculate confidence score based on data completeness."""
    if not rest_data:
        return 0.0
    
    score = 0.0
    total_checks = 10
    
    if rest_data.get("name"):
        score += 1
    if rest_data.get("currencies"):
        score += 1
    if rest_data.get("capital"):
        score += 1
    if rest_data.get("latitude") and rest_data.get("longitude"):
        score += 1
    if rest_data.get("languages"):
        score += 1
    if wb_data and wb_data.get("gdp_per_capita_usd"):
        score += 1
    if cities and len(cities) > 0:
        score += 1
    if rest_data.get("region"):
        score += 1
    if rest_data.get("flag_url"):
        score += 1
    if rest_data.get("phone_code"):
        score += 1
    
    return round(score / total_checks, 4)


def calculate_gateway_rankings(country_code: str, currencies: list[str], region: str = None, internet_pen: float = 50) -> list[dict]:
    scores = []
    for gw_id, gw in GATEWAY_REGISTRY.items():
        score = 0
        if country_code.upper() in gw["regions"] or "GLOBAL" in gw["regions"]:
            score += 40
        for curr in currencies:
            if curr in gw["currencies"] or "*" in gw["currencies"]:
                score += 25
                break
        if internet_pen > 80:
            score += 15
        elif internet_pen > 50:
            score += 10
        else:
            score += 5
        score += max(0, 10 - (gw["avg_fee"] - 1.5))
        score += max(0, 10 - (gw["setup_days"] / 3))
        if score > 50:
            scores.append({
                "gateway_id": gw_id,
                "score": score,
                "name": gw["name"],
                "type": gw["type"],
                "avg_fee": gw["avg_fee"],
                "setup_days": gw["setup_days"],
            })
    return sorted(scores, key=lambda x: x["score"], reverse=True)


def calculate_commission_tiers(economic_tier: str, gdp: int = 0) -> dict:
    multiplier = {"emerging": 0.85, "developing": 1.0, "developed": 1.10}.get(economic_tier, 1.0)
    result = {}
    for cat, bounds in BASE_COMMISSIONS.items():
        result[cat] = {
            "min_rate": bounds["min"],
            "max_rate": bounds["max"],
            "suggested_rate": min(bounds["max"], max(bounds["min"], round(bounds["suggested"] * multiplier, 4))),
        }
    return result


def determine_kyc_tier(gdp_per_capita: int) -> str:
    if gdp_per_capita > 40000:
        return "strict"
    elif gdp_per_capita > 10000:
        return "standard"
    else:
        return "basic"


def determine_logistics_model(internet_penetration: float, population: int) -> str:
    if internet_penetration > 80 and population > 5000000:
        return "hub_and_spoke"
    elif internet_penetration > 50:
        return "point_to_point"
    else:
        return "basic_delivery"


def determine_region(internet_pen: float, gdp: int) -> str:
    if gdp > 25000:
        return "developed"
    elif gdp > 6000:
        return "developing"
    return "emerging"


def get_product_restrictions_for_region(region: str) -> list[str]:
    region_lower = region.lower()
    if region_lower in ["gcc", "middle east"]:
        return ["alcohol", "pork", "gambling"]
    return []


def get_legal_rules_for_region(region: str) -> dict:
    region_lower = region.lower()
    if region_lower in ["gcc", "middle east"]:
        return LEGAL_RULES["GCC"]
    elif region_lower in ["europe", "north america"]:
        return LEGAL_RULES["default"]
    return LEGAL_RULES["default"]


async def auto_populate_country(country_code: str) -> dict:
    code = country_code.upper()
    warnings: list[str] = []
    degraded = False
    
    if not code:
        return {"error": "Empty search term", "degraded": True, "warnings": ["Empty search term"]}
    
    redis = _get_redis()
    cache_key = _cache_key(code)
    
    if redis:
        try:
            cached = redis.get(cache_key)
            if cached:
                result = json.loads(cached)
                result["cached"] = True
                return result
        except Exception as e:
            logger.debug("Redis get failed: %s", e)
    
    async def safe_fetch_with_breaker(fetch_func, name: str):
        try:
            return await api_breaker.call(fetch_func)
        except Exception as e:
            logger.warning("API %s failed after retries/circuit breaker: %s", name, e)
            return {"success": False, "data": None, "error": str(e)}
    
    results = await asyncio.gather(
        safe_fetch_with_breaker(lambda: fetch_rest_countries(code), "rest_countries"),
        safe_fetch_with_breaker(lambda: fetch_world_bank_data(code), "world_bank"),
        safe_fetch_with_breaker(lambda: fetch_geodb_cities(code), "geodb_cities"),
        safe_fetch_with_breaker(lambda: fetch_public_holidays(code), "public_holidays"),
        safe_fetch_with_breaker(lambda: fetch_vat_rate(code), "vat_rate"),
    )
    
    rest_result, wb_result, cities_result, holidays_result, vat_result = results
    
    rest_data = rest_result["data"]
    wb_data = wb_result["data"] or {}
    cities = cities_result["data"] or []
    holidays = holidays_result["data"] or []
    vat_rate = vat_result["data"] or 0.05
    
    if rest_result["error"]:
        warnings.append(rest_result["error"])
        degraded = True
    if wb_result["error"]:
        warnings.append(wb_result["error"])
        degraded = True
    if cities_result["error"]:
        warnings.append(cities_result["error"])
        degraded = True
    if holidays_result["error"]:
        warnings.append(holidays_result["error"])
        degraded = True
    if vat_result["error"]:
        warnings.append(vat_result["error"])
        degraded = True
    
    if not rest_data:
        return {"error": f"Country {code} not found", "degraded": True, "warnings": ["Wikipedia/Wikidata unavailable or country not found"]}
    
    wb_data = wb_data or {}
    gdp = wb_data.get("gdp_per_capita_usd", 0) or 0
    internet = wb_data.get("internet_penetration_pct", INTERNET_PENETRATION_BY_REGION.get("default", 50))
    population = wb_data.get("population", 0) or 0
    
    currencies = rest_data.get("currencies", ["USD"])
    region = rest_data.get("region", "")
    economic_tier = determine_region(internet, gdp)
    
    if economic_tier == "developed":
        internet_pen = 90.0
    elif economic_tier == "developing":
        internet_pen = 70.0
    else:
        internet_pen = 50.0
    
    gateway_rankings = calculate_gateway_rankings(code, currencies, region, internet)
    payment_gateways = [
        {
            "gateway_id": gw["gateway_id"],
            "name": gw["name"],
            "type": gw["type"],
            "enabled": True,
            "credential_ref": None,
            "supports_cod": gw["gateway_id"] in ["tap", "thawani", "omannet"],
            "supports_installments": gw["gateway_id"] in ["stripe", "tap", "hyperpay"],
            "fee_percentage": gw["avg_fee"],
            "fee_fixed": 0.30,
            "integration_feasibility_score": gw["score"],
            "recommendation": "highly_recommended" if gw["score"] >= 75 else "recommended" if gw["score"] >= 50 else "consider",
            "adapter_exists": gw["gateway_id"] in ["stripe", "tap", "thawani", "mada", "hyperpay", "paytabs", "tabby", "klarna"],
        }
        for gw in gateway_rankings
    ]
    
    kyc_tier = determine_kyc_tier(gdp)
    kyc_reqs = KYC_REQUIREMENTS.get(kyc_tier, KYC_REQUIREMENTS["standard"])
    
    cities_formatted = [
        {
            "name": c.get("name"),
            "region": c.get("region") or "",
            "lat": c.get("latitude"),
            "lng": c.get("longitude"),
            "population": c.get("population"),
            "is_capital": c.get("is_capital", False),
        }
        for c in cities
    ]
    
    currency_code = currencies[0] if currencies else "USD"
    currency_info = rest_data.get("currencies", {}).get(currency_code, {})
    currency_symbol = currency_info.get("symbol") or "$"
    currency_name = currency_info.get("name") or "US Dollar"
    
    result = {
        "code": code,
        "name": rest_data.get("name", ""),
        "official_name": rest_data.get("official_name", ""),
        "alpha3": rest_data.get("alpha3", ""),
        "phone_code": rest_data.get("phone_code", ""),
        "flag_url": rest_data.get("flag_url", ""),
        "latitude": rest_data.get("latitude"),
        "longitude": rest_data.get("longitude"),
        "capital": rest_data.get("capital", ""),
        "language": rest_data.get("languages", ["en"])[0] if rest_data.get("languages") else "en",
        "languages": rest_data.get("languages", []),
        "currency": currency_code,
        "currencies": currencies,
        "currency_symbol": currency_symbol,
        "currency_name": currency_name,
        "gdp_per_capita_usd": gdp,
        "population": population,
        "internet_penetration_pct": internet,
        "economic_tier": economic_tier,
        "region": region,
        "tax_type": "VAT" if code.upper() in ["SA", "AE", "OM", "BH", "KW"] else "SalesTax",
        "tax_rate": vat_rate or 0.05,
        "tax_name": "VAT" if code.upper() in ["SA", "AE", "OM", "BH", "KW"] else "Sales Tax",
        "tax_inclusive_pricing": False,
        "legal_entity_required": True,
        "consumer_protection_days": 14 if economic_tier == "developed" else 7,
        "data_privacy_framework": "GDPR" if economic_tier == "developed" else "PDPL" if code.upper() in ["SA", "AE", "OM"] else "Standard",
        "data_residency_tier": "strict" if code.upper() in ["SA", "AE", "OM"] else "standard",
        "timezone": "UTC",
        "measurement_system": "metric",
        "address_format": "{street}, {city}, {postal_code}",
        "working_days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
        "public_holidays": holidays,
        "cities": cities_formatted,
        "category_tax_rates": [],
        "legal_rules": get_legal_rules_for_region(region),
        "logistics_model": determine_logistics_model(internet, population),
        "default_vehicle_type": None,
        "base_rate": None,
        "per_km_rate": None,
        "minimum_charge": None,
        "weight_surcharge_rate": None,
        "weight_surcharge_threshold_kg": None,
        "payment_methods": [],
        "payment_gateways": payment_gateways,
        "logistics_providers": [],
        "supplier_requirements": {
            "kyc_level": kyc_tier,
            "required_documents": kyc_reqs["documents"],
            "approval_required": kyc_reqs["requires_commercial"],
        },
        "payout_settings": {
            "minimum_payout_amount": 100.0,
            "payout_schedule": "weekly",
            "payout_day": "sunday",
            "batch_size": 50,
        },
        "commission_tiers": [
            {
                "min_order_value": 0,
                "max_order_value": 50,
                "commission_percentage": 0.08,
                "fixed_fee": 0,
            },
            {
                "min_order_value": 50,
                "max_order_value": 200,
                "commission_percentage": 0.10,
                "fixed_fee": 0,
            },
            {
                "min_order_value": 200,
                "max_order_value": None,
                "commission_percentage": 0.12,
                "fixed_fee": 0,
            },
        ],
        "tax_exempt_categories": [],
        "tax_reduced_rates": {},
        "regions": [],
        "economic_tier": economic_tier,
        "fraud_risk_tier": "low" if gdp > 20000 else "medium" if gdp > 5000 else "high",
        "suggested_logistics_model": determine_logistics_model(internet, population),
        "confidence_score": calculate_confidence_score(rest_data, wb_data, cities),
        "cod_enabled": True,
        "cod_max_amount": None,
        "cod_verification_required": False,
        "cod_remittance_days": 7,
        "settlement_hold_days": 3,
        "minimum_payout_amount": 100.0,
        "payout_currency": currencies[0] if currencies else "USD",
        "supplier_kyc_tier": kyc_tier,
        "supplier_onboarding_fee": None,
        "supplier_monthly_fee": None,
        "supplier_rating_threshold": None,
        "legal_entity_required": True,
        "consumer_protection_days": 14 if economic_tier == "developed" else 7,
        "data_privacy_framework": "GDPR" if economic_tier == "developed" else "PDPL" if code.upper() in ["SA", "AE", "OM"] else "Standard",
        "max_package_weight_kg": None,
        "max_package_dimensions_cm": None,
        "signature_required_threshold": None,
        "measurement_system": "metric",
        "working_days_json": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
        "public_holidays_json": holidays,
        "macro_indicators_json": {"gdp_per_capita": gdp, "population": population, "internet_penetration": internet},
        "payment_gateways_json": payment_gateways,
        "logistics_providers_json": [],
        "suggested_gateway_rankings": payment_gateways,
        "suggested_commission_ranges": calculate_commission_tiers(economic_tier, gdp),
        "consumer_behavior_profile_json": {
            "return_window_days": 14 if economic_tier == "developed" else 7,
            "min_order_age": 18,
            "max_returns_allowed": 3,
            "refund_processing_days": 7,
            "prefers_cod": internet < 70,
            "average_order_value_estimate_usd": 50 + (gdp / 1000),
            "mobile_commerce_likely": internet > 50,
            "digital_wallet_penetration": min(internet * 0.8, 90),
        },
        "legal_contracts": generate_all_legal_documents(code, "en"),
        "source": "auto-populate",
        "cached": False,
        "degraded": degraded,
        "warnings": warnings,
        "fetched_at": datetime.utcnow().isoformat(),
        "is_active": False,
    }
    
    if redis:
        try:
            redis.setex(cache_key, CACHE_TTL_SECONDS, json.dumps(result, default=str))
        except Exception as e:
            logger.debug("Redis set failed: %s", e)
    
    return result

