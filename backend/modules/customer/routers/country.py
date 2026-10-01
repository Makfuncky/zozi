"""Customer country router — public, customer-facing country/currency endpoints.

Per ARCHITECTURE_DIAGRAM.md §3, this is a thin per-actor router:
auth context (optional) + require_feature(...) + one service call.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from domains.country.services.core.country_service import list_public_countries
from infrastructure.database.database import get_db
from infrastructure.utils.currency_service import get_currency_context
from rbac.dependencies import require_feature

router = APIRouter(prefix="/api/v1/customer/country", tags=["customer", "country"])


@router.get("/countries", status_code=200)
def list_countries(
    _: None = Depends(require_feature("catalog.list")),
    db: Session = Depends(get_db),
):
    return {"items": list_public_countries(db)}


@router.get("/currency/context", status_code=200)
def currency_context(
    country: str | None = Query(None, description="ISO country code"),
    currency: str | None = Query(None, description="ISO currency code"),
    _: None = Depends(require_feature("catalog.list")),
):
    return get_currency_context(country=country, currency=currency)
