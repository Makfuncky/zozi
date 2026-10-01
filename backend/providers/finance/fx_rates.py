"""FX rate provider with live fetch and static fallback.

Used by settlement and travel services. Tries live rates from the geography
provider first; falls back to hardcoded rates if the upstream is unavailable.
"""
from __future__ import annotations

import logging
import time
from decimal import Decimal

logger = logging.getLogger(__name__)

_RATE_CACHE_TTL = 3600  # 1 hour
_cached_rates: dict[str, Decimal] = {}
_cached_source: str = "fallback"
_cached_at: float = 0.0

_STATIC_FALLBACK: dict[str, Decimal] = {
    "USD": Decimal("1.0"),
    "SAR": Decimal("3.75"),
    "AED": Decimal("3.6725"),
    "EGP": Decimal("48.5"),
    "KWD": Decimal("0.308"),
    "QAR": Decimal("3.64"),
    "BHD": Decimal("0.376"),
    "OMR": Decimal("0.385"),
    "JOD": Decimal("0.709"),
    "EUR": Decimal("0.92"),
    "GBP": Decimal("0.79"),
    "TRY": Decimal("32.5"),
    "PKR": Decimal("278.5"),
    "INR": Decimal("83.5"),
    "PHP": Decimal("56.5"),
    "MYR": Decimal("4.75"),
    "IDR": Decimal("15500"),
    "THB": Decimal("35.5"),
}


def _fetch_live_rates() -> dict[str, Decimal] | None:
    """Attempt to fetch live rates from the geography provider. Returns None on failure."""
    try:
        from providers.geography.rates import fetch_rates
        aed_based, source = fetch_rates()
    except Exception as exc:
        logger.debug("Geography rate provider unavailable: %s", exc)
        return None

    if not aed_based or source != "live":
        return None

    usd_rate = aed_based.get("USD")
    if usd_rate is None or usd_rate == 0:
        return None

    usd_based: dict[str, Decimal] = {}
    for code, rate in aed_based.items():
        if rate > 0:
            usd_based[code] = rate / usd_rate
    return usd_based


def get_fx_rates(force_refresh: bool = False) -> tuple[dict[str, Decimal], str]:
    """Return (rates_relative_to_usd, source).

    Source is 'live' when fresh upstream data is available, 'fallback' otherwise.
    Rates are cached for ``_RATE_CACHE_TTL`` seconds.
    """
    global _cached_rates, _cached_source, _cached_at

    now = time.monotonic()
    if not force_refresh and _cached_rates and (now - _cached_at) < _RATE_CACHE_TTL:
        return _cached_rates, _cached_source

    live = _fetch_live_rates()
    if live:
        _cached_rates = live
        _cached_source = "live"
    else:
        _cached_rates = dict(_STATIC_FALLBACK)
        _cached_source = "fallback"
    _cached_at = now
    return _cached_rates, _cached_source


def get_rate(currency: str) -> Decimal | None:
    """Return the USD-based rate for a single currency, or None if unknown."""
    rates, _ = get_fx_rates()
    return rates.get(currency.upper())


def reset_cache() -> None:
    """Clear the rate cache so the next call re-fetches."""
    global _cached_rates, _cached_at, _cached_source
    _cached_rates = {}
    _cached_at = 0.0
    _cached_source = "fallback"


__all__ = [
    "get_fx_rates",
    "get_rate",
    "reset_cache",
    "_STATIC_FALLBACK",
]
