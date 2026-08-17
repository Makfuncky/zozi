"""Foreign-exchange + currency lookup provider.

External HTTP calls (open.er-api.com live rates, Wikidata currency resolution)
live here so ``infrastructure.utils.currency`` keeps only pure conversion arithmetic and string
normalisation. The caches are module-local and TTL-bounded; ``httpx`` (the vendor
transport) is imported only in this provider, not in the service/util layer.
"""
from __future__ import annotations

import logging
import re
import time
from decimal import Decimal
from typing import Any

import httpx

from infrastructure.utils.money import to_decimal

logger = logging.getLogger(__name__)

RATE_CACHE_TTL_SECONDS = 60 * 60
ER_API_BASE_URL = "https://open.er-api.com/v6/latest/AED"
WIKIDATA_API_URL = "https://www.wikidata.org/w/api.php"

_RATES_CACHE: dict[str, Any] = {"expires_at": 0.0, "rates": {}, "source": "fallback"}
_COUNTRY_CURRENCY_CACHE: dict[str, str] = {}


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


def fetch_rates() -> tuple[dict[str, Decimal], str]:
    """Return (rates_by_code, source) using a TTL cache; source is 'live' or 'fallback'."""
    now = time.time()
    if _RATES_CACHE["expires_at"] > now and _RATES_CACHE["rates"]:
        return _RATES_CACHE["rates"], _RATES_CACHE["source"]

    source = "fallback"
    rates: dict[str, Decimal] = {}

    try:
        with httpx.Client(timeout=4.0) as client:
            response = client.get(ER_API_BASE_URL)
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


def lookup_currency_from_wikidata(country: str) -> str | None:
    """Look up currency code from Wikidata (synchronous, free, no key).

    Uses Wikidata wbgetentities for ISO code of the country's currency.
    """
    normalized = _normalize_country_key(country)
    if not normalized:
        return None
    if normalized in _COUNTRY_CURRENCY_CACHE:
        return _COUNTRY_CURRENCY_CACHE[normalized]

    try:
        base = WIKIDATA_API_URL
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

            currency_claims = claims.get("P38", [])
            if not currency_claims:
                return None
            mainsnak = currency_claims[0].get("mainsnak", {})
            if mainsnak.get("snaktype") != "value":
                return None
            currency_id = mainsnak.get("datavalue", {}).get("value", {}).get("id")
            if not currency_id:
                return None

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
                labels = curr_entity.get("labels", {})
                label = labels.get("en", {}).get("value", "")
                currency_code = normalize_currency_code(label, default="")

            if currency_code:
                _COUNTRY_CURRENCY_CACHE[normalized] = currency_code
                return currency_code
    except Exception as exc:
        logger.debug("Wikidata currency lookup failed for %s: %s", country, exc)
    return None


def reset_rate_cache() -> None:
    """Force the next :func:`fetch_rates` call to hit the upstream provider."""
    _RATES_CACHE.update({"expires_at": 0.0, "rates": {}, "source": "fallback"})


def rate_cache_expiry() -> float:
    return float(_RATES_CACHE["expires_at"])


__all__ = [
    "RATE_CACHE_TTL_SECONDS",
    "normalize_currency_code",
    "fetch_rates",
    "lookup_currency_from_wikidata",
    "reset_rate_cache",
    "rate_cache_expiry",
]

