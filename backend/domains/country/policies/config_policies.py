"""Country domain policies — pure, side-effect-free business rules.

No DB, no request, no FastAPI. Each function takes plain values and returns a
verdict (bool / raised ValueError / normalized value). Services call these; they
are the single home for country configuration rules (Law: domains enforce
*policies*, not permissions).
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Optional

MAX_TAX_RATE = Decimal("1.0000")
MIN_TAX_RATE = Decimal("0.0000")
MAX_COMMISSION_RATE = Decimal("100.00")
MIN_COMMISSION_RATE = Decimal("0.00")
COD_MAX_AMOUNT_CEIL = Decimal("1000000.00")


def validate_tax_rate(rate) -> Decimal:
    """Tax rate must be a non-negative decimal <= 100%."""
    try:
        value = Decimal(str(rate))
    except (ValueError, TypeError, InvalidOperation):
        raise ValueError("tax_rate must be a decimal number")
    if value < MIN_TAX_RATE or value > MAX_TAX_RATE:
        raise ValueError("tax_rate must be between 0 and 1.0 (100%)")
    return value


def validate_commission_rate(rate_percent) -> Decimal:
    try:
        value = Decimal(str(rate_percent))
    except (ValueError, TypeError, InvalidOperation):
        raise ValueError("commission rate_percent must be a decimal number")
    if value < MIN_COMMISSION_RATE or value > MAX_COMMISSION_RATE:
        raise ValueError("commission rate_percent must be between 0 and 100")
    return value


def validate_cod_settings(
    cod_enabled: Optional[bool],
    cod_max_amount: Optional[Decimal],
    cod_verification_required: Optional[bool],
    settlement_hold_days: Optional[int],
) -> dict:
    """Validate and normalize COD / settlement configuration."""
    if cod_enabled is True:
        if cod_max_amount is None or Decimal(str(cod_max_amount)) <= 0:
            raise ValueError("cod_max_amount must be positive when COD is enabled")
        if Decimal(str(cod_max_amount)) > COD_MAX_AMOUNT_CEIL:
            raise ValueError("cod_max_amount exceeds allowed ceiling")
    if settlement_hold_days is not None and settlement_hold_days < 0:
        raise ValueError("settlement_hold_days cannot be negative")
    return {
        "cod_enabled": bool(cod_enabled) if cod_enabled is not None else False,
        "cod_max_amount": Decimal(str(cod_max_amount)) if cod_max_amount is not None else None,
        "cod_verification_required": bool(cod_verification_required)
        if cod_verification_required is not None
        else False,
        "settlement_hold_days": settlement_hold_days if settlement_hold_days is not None else 3,
    }


def is_config_approval_required(draft_type: str) -> bool:
    """Maker-checker gating: which draft types require approval before publish."""
    return draft_type in {
        "tax",
        "logistics",
        "commission",
        "payment_and_flags",
        "legal_rules",
        "supplier_requirements",
        "payout_settings",
    }
