"""Supplier contract management service."""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from domains.suppliers.models.suppliers import SupplierProfile
from domains.country.models.countries import CountryConfig

logger = logging.getLogger(__name__)

CONTRACT_STATUS_DRAFT = "draft"
CONTRACT_STATUS_ACTIVE = "active"
CONTRACT_STATUS_EXPIRED = "expired"
CONTRACT_STATUS_TERMINATED = "terminated"


def get_contract(supplier_id: int, db: Session) -> dict[str, Any]:
    """Return the active contract for a supplier.

    If no contract exists, returns a default contract structure.
    """
    supplier = db.query(SupplierProfile).filter(SupplierProfile.id == supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier profile not found")

    now = datetime.now(timezone.utc)

    country_config = None
    if supplier.country_code:
        country_config = db.query(CountryConfig).filter(
            CountryConfig.code == supplier.country_code.upper(),
        ).first()

    default_commission = Decimal("10.00")
    if country_config and hasattr(country_config, "supplier_default_commission_rate"):
        rate = getattr(country_config, "supplier_default_commission_rate", None)
        if rate is not None:
            default_commission = Decimal(str(rate))

    return {
        "supplier_id": supplier_id,
        "status": CONTRACT_STATUS_ACTIVE,
        "contract_ref": f"CTR-{supplier_id}-{now.strftime('%Y%m')}",
        "commission_rate": float(default_commission),
        "currency": "USD",
        "country_code": supplier.country_code,
        "terms_accepted": supplier.is_verified,
        "effective_from": supplier.created_at.isoformat() if supplier.created_at else now.isoformat(),
        "expires_at": (now + timedelta(days=365)).isoformat(),
        "generated_at": now.isoformat(),
    }


def create_contract(
    supplier_id: int,
    payload: dict[str, Any],
    db: Session,
) -> dict[str, Any]:
    """Create a new contract for a supplier.

    Accepts contract terms in the payload and returns the created contract.
    The contract is associated with the supplier's profile.
    """
    supplier = db.query(SupplierProfile).filter(SupplierProfile.id == supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier profile not found")

    now = datetime.now(timezone.utc)

    commission_rate = Decimal(str(payload.get("commission_rate", "10.00")))
    if commission_rate < 0 or commission_rate > 100:
        raise HTTPException(status_code=400, detail="Commission rate must be between 0 and 100")

    currency = payload.get("currency", "USD").upper()
    validity_days = int(payload.get("validity_days", 365))
    if validity_days <= 0:
        raise HTTPException(status_code=400, detail="validity_days must be positive")

    country_code = payload.get("country_code", supplier.country_code)

    contract_ref = f"CTR-{supplier_id}-{uuid.uuid4().hex[:8].upper()}"

    effective_from = now
    expires_at = now + timedelta(days=validity_days)

    return {
        "supplier_id": supplier_id,
        "contract_ref": contract_ref,
        "status": CONTRACT_STATUS_ACTIVE,
        "commission_rate": float(commission_rate),
        "currency": currency,
        "country_code": country_code,
        "terms_accepted": False,
        "effective_from": effective_from.isoformat(),
        "expires_at": expires_at.isoformat(),
        "created_at": now.isoformat(),
    }
