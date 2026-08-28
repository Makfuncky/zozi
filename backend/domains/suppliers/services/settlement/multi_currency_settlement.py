"""Multi-currency settlement service for supplier payouts."""
from __future__ import annotations

import logging
import time
from decimal import Decimal, ROUND_HALF_UP
from typing import Any

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from domains.suppliers.models.suppliers import SupplierProfile
from domains.finance.ports import SupplierSettlement

logger = logging.getLogger(__name__)

# Static fallback exchange rates (relative to USD). Production must use
# a live FX provider via providers/exchange/.
_FX_RATES: dict[str, Decimal] = {
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

_FX_PRECISION = Decimal("0.0001")

# Rate freshness: static rates older than this (seconds) trigger a warning.
# Production should set _FX_LAST_UPDATED via a live FX provider refresh.
_FX_MAX_AGE_SECONDS = 86400  # 24 hours
_FX_LAST_UPDATED: float = time.monotonic()


def _check_fx_freshness() -> None:
    """Warn if static FX rates have not been refreshed within the max age."""
    age = time.monotonic() - _FX_LAST_UPDATED
    if age > _FX_MAX_AGE_SECONDS:
        logger.warning(
            "Static FX rates are stale (age %.0f hours > %d hours). "
            "Production must wire a live FX provider via providers/exchange/.",
            age / 3600,
            _FX_MAX_AGE_SECONDS // 3600,
        )


def convert_currency(
    amount: Decimal | float | str,
    from_currency: str,
    to_currency: str,
) -> Decimal:
    """Convert an amount from one currency to another using static FX rates.

    Falls back to identity conversion if either currency is unknown.
    Production deployments should wire a live FX provider.
    """
    if from_currency == to_currency:
        return Decimal(str(amount)).quantize(_FX_PRECISION, rounding=ROUND_HALF_UP)

    _check_fx_freshness()

    from_rate = _FX_RATES.get(from_currency.upper())
    to_rate = _FX_RATES.get(to_currency.upper())

    if from_rate is None or to_rate is None:
        logger.warning(
            "Unknown FX pair %s→%s; returning unconverted amount",
            from_currency, to_currency,
        )
        return Decimal(str(amount)).quantize(_FX_PRECISION, rounding=ROUND_HALF_UP)

    usd_amount = Decimal(str(amount)) / from_rate
    converted = (usd_amount * to_rate).quantize(_FX_PRECISION, rounding=ROUND_HALF_UP)
    return converted


def get_settlement_amount(
    supplier_id: int,
    currency: str,
    db: Session,
) -> dict[str, Any]:
    """Return the total settlement amount for a supplier in the requested currency.

    Aggregates pending and completed settlements, converting to the target
    currency when necessary.
    """
    supplier = db.query(SupplierProfile).filter(SupplierProfile.id == supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier profile not found")

    settlements = db.query(SupplierSettlement).filter(
        SupplierSettlement.supplier_id == supplier_id,
        SupplierSettlement.is_deleted == False,
    ).all()

    total_pending = Decimal("0")
    total_settled = Decimal("0")
    settlement_count = 0

    for s in settlements:
        net = Decimal(str(s.net_amount or 0))
        settlement_currency = (s.currency or "USD").upper()

        if settlement_currency != currency.upper():
            net = convert_currency(net, settlement_currency, currency)

        if s.status == "settled":
            total_settled += net
        else:
            total_pending += net

        settlement_count += 1

    return {
        "supplier_id": supplier_id,
        "currency": currency.upper(),
        "total_pending": float(total_pending.quantize(_FX_PRECISION, rounding=ROUND_HALF_UP)),
        "total_settled": float(total_settled.quantize(_FX_PRECISION, rounding=ROUND_HALF_UP)),
        "total": float((total_pending + total_settled).quantize(_FX_PRECISION, rounding=ROUND_HALF_UP)),
        "settlement_count": settlement_count,
    }
