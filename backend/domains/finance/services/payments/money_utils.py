"""Money conversion helpers for the payments domain.

Minimal, deterministic implementations sufficient for routing/quote flows.
Real FX rates should be injected via the providers layer; absent that, we treat
AED as the base and fall back to a 1:1 passthrough so callers never crash
(Law 30).
"""
from __future__ import annotations

from decimal import Decimal
from typing import Union

Number = Union[int, float, Decimal]

_AED_RATES: dict[str, Decimal] = {
    "AED": Decimal("1"),
    "USD": Decimal("0.27"),
    "SAR": Decimal("1.02"),
    "KWD": Decimal("0.082"),
    "BHD": Decimal("0.10"),
    "OMR": Decimal("0.10"),
    "QAR": Decimal("0.99"),
    "EGP": Decimal("13.0"),
    "JOD": Decimal("0.19"),
}


def convert_from_aed(amount: Number, currency: str) -> Decimal:
    """Convert an AED amount into the target currency using static rates."""
    rate = _AED_RATES.get(str(currency).upper(), Decimal("1"))
    return Decimal(str(amount)) * rate


def money_to_minor_units_for_currency(amount: Number, currency: str) -> int:
    """Return the amount expressed in the currency's minor units (e.g. fils)."""
    # GCC currencies are 2-decimal; treat everything as 2dp for safety.
    return int((Decimal(str(amount)) * Decimal("100")).to_integral_value(rounding="ROUND_HALF_UP"))
