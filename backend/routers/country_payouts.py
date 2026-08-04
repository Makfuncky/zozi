"""Country-level payout rules — category and product overrides."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from data.controllers_admin_controller import require_country_access
from data.db import get_db
from data.dependencies_auth import get_current_user
from services.country.country_router_service import (
    get_payout_rule_categories,
    create_payout_rule_category,
    delete_payout_rule_category,
    get_payout_rule_products,
    create_payout_rule_product,
    delete_payout_rule_product,
)

router = APIRouter(tags=["country_payouts"])


# ── Schemas ─────────────────────────────────────────────────────────────────────

class PayoutRuleCategoryBody(BaseModel):
    category_slug: str = Field(..., min_length=1, max_length=120)
    payout_rate: float = Field(..., ge=0, le=1)
    min_amount: float | None = Field(None, ge=0)
    max_amount: float | None = Field(None, ge=0)
    is_active: bool = True


class PayoutRuleProductBody(BaseModel):
    product_id: int = Field(..., ge=1)
    payout_rate: float = Field(..., ge=0, le=1)
    min_amount: float | None = Field(None, ge=0)
    max_amount: float | None = Field(None, ge=0)
    is_active: bool = True


# ── Category-level payout rules ────────────────────────────────────────────────

@router.get("/admin/countries/{code}/payout-rules/categories")
def list_payout_rule_categories_endpoint(
    code: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_country_access(code, current_user)
    return get_payout_rule_categories(db, code, skip=skip, limit=limit)


@router.post("/admin/countries/{code}/payout-rules/categories")
def create_payout_rule_category_endpoint(
    code: str,
    body: PayoutRuleCategoryBody,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_country_access(code, current_user)
    return create_payout_rule_category(db, code, body.model_dump())


@router.delete("/admin/countries/{code}/payout-rules/categories/{rule_id}")
def delete_payout_rule_category_endpoint(
    code: str,
    rule_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_country_access(code, current_user)
    return delete_payout_rule_category(db, code, rule_id)


# ── Product-level payout rules ────────────────────────────────────────────────────

@router.get("/admin/countries/{code}/payout-rules/products")
def list_payout_rule_products_endpoint(
    code: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_country_access(code, current_user)
    return get_payout_rule_products(db, code, skip=skip, limit=limit)


@router.post("/admin/countries/{code}/payout-rules/products")
def create_payout_rule_product_endpoint(
    code: str,
    body: PayoutRuleProductBody,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_country_access(code, current_user)
    return create_payout_rule_product(db, code, body.model_dump())


@router.delete("/admin/countries/{code}/payout-rules/products/{rule_id}")
def delete_payout_rule_product_endpoint(
    code: str,
    rule_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_country_access(code, current_user)
    return delete_payout_rule_product(db, code, rule_id)