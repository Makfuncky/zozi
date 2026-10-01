"""Multi-currency settlement service for supplier payouts."""
from __future__ import annotations

import logging
from decimal import Decimal, ROUND_HALF_UP
from typing import Any

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from domains.suppliers.models.suppliers import SupplierProfile
from domains.finance.ports import SupplierSettlement
from providers.finance.fx_rates import get_rate

logger = logging.getLogger(__name__)

_FX_PRECISION = Decimal("0.0001")


def convert_currency(
    amount: Decimal | float | str,
    from_currency: str,
    to_currency: str,
) -> Decimal:
    """Convert an amount from one currency to another using FX rates.

    Tries live rates from providers/finance/fx_rates.py first; falls back to
    hardcoded values if no external source is available. Falls back to identity
    conversion if either currency is unknown.
    """
    if from_currency == to_currency:
        return Decimal(str(amount)).quantize(_FX_PRECISION, rounding=ROUND_HALF_UP)

    from_rate = get_rate(from_currency)
    to_rate = get_rate(to_currency)

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
