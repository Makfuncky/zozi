"""Country-level payout rules — category and product overrides."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from data.controllers_admin_controller import require_country_access
from data.db import get_db
from data.models import PayoutRuleCategory, PayoutRuleProduct, User
from routers.auth import get_current_user
from utils.dependencies import require_admin

from services.write_helpers import add_and_flush, commit_and_refresh, commit_only, delete_only
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


# ── Category-level payout rules ─────────────────────────────────────────────────

@router.get("/admin/countries/{code}/payout-rules/categories")
def list_payout_rule_categories(
    code: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_country_access(code, current_user)
    rows = db.query(PayoutRuleCategory).filter(
        PayoutRuleCategory.country_code == code.upper(),
        PayoutRuleCategory.is_active == True,
    ).offset(skip).limit(limit).all()
    return [
        {
            "id": r.id,
            "country_code": r.country_code,
            "category_slug": r.category_slug,
            "payout_rate": float(r.payout_rate),
            "min_amount": float(r.min_amount) if r.min_amount else None,
            "max_amount": float(r.max_amount) if r.max_amount else None,
            "is_active": r.is_active,
        }
        for r in rows
    ]


@router.post("/admin/countries/{code}/payout-rules/categories")
def create_payout_rule_category(
    code: str,
    body: PayoutRuleCategoryBody,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_country_access(code, current_user)
    code_upper = code.upper()
    existing = db.query(PayoutRuleCategory).filter(
        PayoutRuleCategory.country_code == code_upper,
        PayoutRuleCategory.category_slug == body.category_slug,
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="Rule already exists for this category")
    row = PayoutRuleCategory(
        country_code=code_upper,
        category_slug=body.category_slug,
        payout_rate=body.payout_rate,
        min_amount=body.min_amount,
        max_amount=body.max_amount,
        is_active=body.is_active,
    )
    add_and_flush(db, row)
    commit_and_refresh(db, row)
    return {"message": "Category payout rule created", "id": row.id}


@router.delete("/admin/countries/{code}/payout-rules/categories/{rule_id}")
def delete_payout_rule_category(
    code: str,
    rule_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_country_access(code, current_user)
    row = db.query(PayoutRuleCategory).filter(
        PayoutRuleCategory.id == rule_id,
        PayoutRuleCategory.country_code == code.upper(),
    ).first()
    if not row:
        raise HTTPException(status_code=404)
    delete_only(db, row)
    commit_only(db)
    return {"message": "Category payout rule deleted"}


# ── Product-level payout rules ──────────────────────────────────────────────────

@router.get("/admin/countries/{code}/payout-rules/products")
def list_payout_rule_products(
    code: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_country_access(code, current_user)
    rows = db.query(PayoutRuleProduct).filter(
        PayoutRuleProduct.country_code == code.upper(),
        PayoutRuleProduct.is_active == True,
    ).offset(skip).limit(limit).all()
    return [
        {
            "id": r.id,
            "country_code": r.country_code,
            "product_id": r.product_id,
            "payout_rate": float(r.payout_rate),
            "min_amount": float(r.min_amount) if r.min_amount else None,
            "max_amount": float(r.max_amount) if r.max_amount else None,
            "is_active": r.is_active,
        }
        for r in rows
    ]


@router.post("/admin/countries/{code}/payout-rules/products")
def create_payout_rule_product(
    code: str,
    body: PayoutRuleProductBody,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_country_access(code, current_user)
    code_upper = code.upper()
    existing = db.query(PayoutRuleProduct).filter(
        PayoutRuleProduct.country_code == code_upper,
        PayoutRuleProduct.product_id == body.product_id,
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="Rule already exists for this product")
    row = PayoutRuleProduct(
        country_code=code_upper,
        product_id=body.product_id,
        payout_rate=body.payout_rate,
        min_amount=body.min_amount,
        max_amount=body.max_amount,
        is_active=body.is_active,
    )
    add_and_flush(db, row)
    commit_and_refresh(db, row)
    return {"message": "Product payout rule created", "id": row.id}


@router.delete("/admin/countries/{code}/payout-rules/products/{rule_id}")
def delete_payout_rule_product(
    code: str,
    rule_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_country_access(code, current_user)
    row = db.query(PayoutRuleProduct).filter(
        PayoutRuleProduct.id == rule_id,
        PayoutRuleProduct.country_code == code.upper(),
    ).first()
    if not row:
        raise HTTPException(status_code=404)
    delete_only(db, row)
    commit_only(db)
    return {"message": "Product payout rule deleted"}

