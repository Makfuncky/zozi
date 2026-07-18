"""Money utilities."""
from __future__ import annotations

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any


MONEY_QUANT = Decimal("0.01")


def to_decimal(value: Any, default: Decimal = Decimal("0.00")) -> Decimal:
    if value is None:
        return default
    if isinstance(value, Decimal):
        return value
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return default


def round_money(value: Any, places: str = "0.01") -> Decimal:
    return to_decimal(value).quantize(Decimal(places), rounding=ROUND_HALF_UP)


def to_cents(amount: Any) -> int:
    return int(round_money(amount) * 100)


def money_to_minor_units(amount: Any) -> int:
    """Compatibility alias for code paths that refer to minor currency units."""
    return to_cents(amount)


def from_cents(cents: int) -> Decimal:
    return Decimal(cents) / 100


def format_currency(amount: Any, currency: str = "USD") -> str:
    return f"{currency} {round_money(amount):.2f}"


__all__ = [
    "MONEY_QUANT",
    "format_currency",
    "from_cents",
    "money_to_minor_units",
    "round_money",
    "to_cents",
    "to_decimal",
]

