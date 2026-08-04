import logging
import re
import time
from decimal import Decimal, ROUND_HALF_UP
from typing import Any

import httpx

from utils.money import to_decimal

logger = logging.getLogger(__name__)

RATE_CACHE_TTL_SECONDS = 60 * 60

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

_RATES_CACHE: dict[str, Any] = {
    "expires_at": 0.0,
    "rates": {},
    "source": "fallback",
}
_COUNTRY_CURRENCY_CACHE: dict[str, str] = {}


def refresh_rate_cache() -> dict[str, Any]:
    _RATES_CACHE.update({"expires_at": 0.0, "rates": {}, "source": "fallback"})
    rates, source = _fetch_rates_from_provider()
    return {
        "source": source,
        "currency_count": len(rates),
        "expires_at": _RATES_CACHE["expires_at"],
    }


def normalize_currency_code(code: str | None, default: str = "OMR") -> str:
    if not code:
        return default
    normalized = re.sub(r"[^A-Z]", "", code.upper())
    if len(normalized) == 3:
        return normalized
    return default


def _normalize_country_key(country: str | None) -> str:
    if not country:
        return ""
    return re.sub(r"[^A-Z]", "", country.upper())


def _fetch_rates_from_provider() -> tuple[dict[str, Decimal], str]:
    now = time.time()
    if _RATES_CACHE["expires_at"] > now and _RATES_CACHE["rates"]:
        return _RATES_CACHE["rates"], _RATES_CACHE["source"]

    source = "fallback"
    rates: dict[str, Decimal] = {
        code: meta["fallback_rate"]
        for code, meta in KNOWN_CURRENCY_META.items()
    }

    try:
        with httpx.Client(timeout=4.0) as client:
            response = client.get("https://open.er-api.com/v6/latest/AED")
        data = response.json() if response.is_success else {}
        remote_rates = data.get("rates") if isinstance(data, dict) else None
        if isinstance(remote_rates, dict):
            parsed_rates = {
                code.upper(): to_decimal(value)
                for code, value in remote_rates.items()
            }
            parsed_rates["AED"] = Decimal("1")
            rates = parsed_rates
            source = "live"
    except Exception as exc:  # pragma: no cover - network fallback
        logger.warning("Currency rate fetch failed; using fallback rates: %s", exc)

    _RATES_CACHE.update(
        {
            "expires_at": now + RATE_CACHE_TTL_SECONDS,
            "rates": rates,
            "source": source,
        }
    )
    return rates, source


def _lookup_currency_from_wikidata(country: str) -> str | None:
    """Look up currency code from Wikidata (synchronous, free, no key).

    Uses Wikidata wbgetentities for ISO code of the country's currency.
    """
    normalized = _normalize_country_key(country)
    if not normalized:
        return None
    if normalized in _COUNTRY_CURRENCY_CACHE:
        return _COUNTRY_CURRENCY_CACHE[normalized]

    try:
        base = "https://www.wikidata.org/w/api.php"
        # First get the Wikidata entity ID for this country code
        params = {
            "action": "wbsearchentities",
            "search": normalized if len(normalized) == 2 else country,
            "language": "en",
            "format": "json",
            "limit": 1,
        }
        with httpx.Client(timeout=4.0) as client:
            search_resp = client.get(base, params=params)
            if not search_resp.is_success:
                return None
            search_data = search_resp.json()
            results = search_data.get("search", [])
            if not results:
                return None
            qid = results[0].get("id", "")
            if not qid:
                return None

            # Fetch the country entity's currency (P38) and its ISO code (P498)
            entity_params = {
                "action": "wbgetentities",
                "ids": qid,
                "props": "claims",
                "format": "json",
            }
            entity_resp = client.get(base, params=entity_params)
            if not entity_resp.is_success:
                return None
            entity_data = entity_resp.json()
            entity = entity_data.get("entities", {}).get(qid, {})
            claims = entity.get("claims", {})

            # Extract currency entity ID (P38)
            currency_claims = claims.get("P38", [])
            if not currency_claims:
                return None
            mainsnak = currency_claims[0].get("mainsnak", {})
            if mainsnak.get("snaktype") != "value":
                return None
            currency_id = mainsnak.get("datavalue", {}).get("value", {}).get("id")
            if not currency_id:
                return None

            # Fetch currency entity for its ISO 4217 code (P498)
            curr_params = {
                "action": "wbgetentities",
                "ids": currency_id,
                "props": "claims|labels",
                "format": "json",
            }
            curr_resp = client.get(base, params=curr_params)
            if not curr_resp.is_success:
                return None
            curr_data = curr_resp.json()
            curr_entity = curr_data.get("entities", {}).get(currency_id, {})
            curr_claims = curr_entity.get("claims", {})
            iso_claims = curr_claims.get("P498", [])

            currency_code = ""
            if iso_claims:
                iso_snak = iso_claims[0].get("mainsnak", {})
                if iso_snak.get("snaktype") == "value":
                    currency_code = iso_snak.get("datavalue", {}).get("value", {}).get("text", "")

            if not currency_code:
                # Fall back to English label
                labels = curr_entity.get("labels", {})
                label = labels.get("en", {}).get("value", "")
                currency_code = normalize_currency_code(label, default="")

            if currency_code:
                _COUNTRY_CURRENCY_CACHE[normalized] = currency_code
                return currency_code
    except Exception as exc:
        logger.debug("Wikidata currency lookup failed for %s: %s", country, exc)
    return None


def currency_for_country(country: str | None, default_currency: str = "OMR") -> str:
    normalized = _normalize_country_key(country)
    if not normalized:
        return default_currency
    if normalized in COUNTRY_TO_CURRENCY:
        return COUNTRY_TO_CURRENCY[normalized]
    looked_up = _lookup_currency_from_wikidata(country or "")
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
    rates, source = _fetch_rates_from_provider()
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

