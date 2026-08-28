"""Customer logistics router — public logistics partners and shipping quotes.

Per ARCHITECTURE_DIAGRAM.md §3, this is a thin per-actor router:
auth context (optional) + require_feature(...) + one service call.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from typing import Optional

from infrastructure.database.database import get_db
from rbac.dependencies import require_feature

router = APIRouter(prefix="/api/v1/customer/logistics", tags=["customer", "logistics"])


# === Pydantic Schemas ===

class ShippingQuoteRequest(BaseModel):
    origin_country_code: str = Field(..., pattern=r"^[A-Z]{2}$")
    destination_country_code: str = Field(..., pattern=r"^[A-Z]{2}$")
    weight_kg: float
    dimensions_cm: Optional[dict] = None


# === Public Logistics Partners ===

@router.get("/partners")
def list_public_partners(
    request: Request,
    q: Optional[str] = Query(None),
    country: Optional[str] = Query(None, min_length=2, max_length=10),
    limit: int = Query(12, ge=1, le=50),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("logistics.shipping.tracking")),
):
    from domains.logistics.services.partners.service import list_public_logistics_partners
    resolved_country = (
        country
        or request.headers.get("X-Country-Code")
        or getattr(request.state, "country_code", None)
    )
    return list_public_logistics_partners(request, q=q, country=resolved_country, limit=limit, db=db)


@router.get("/partners/{partner_id}")
def get_public_partner(
    partner_id: int,
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("logistics.shipping.tracking")),
):
    from domains.logistics.services.partners.service import get_public_logistics_partner
    return get_public_logistics_partner(partner_id, db)


# === Shipping Quotes ===

@router.post("/shipping-quote")
def get_shipping_quote(
    data: ShippingQuoteRequest,
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("logistics.shipping.tracking")),
):
    from domains.logistics.services.partners.service import shipping_quote_for_customer
    return shipping_quote_for_customer(data, db)
