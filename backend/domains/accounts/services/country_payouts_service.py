"""Auto-migrated service logic from routers/country_payouts.py."""
from __future__ import annotations

from __future__ import annotations

from fastapi import Depends, HTTPException

from pydantic import BaseModel, Field

from sqlalchemy.orm import Session

from infrastructure.security.country_access import require_country_access
from infrastructure.database.database import get_db

from _legacy.models import PayoutRuleCategory, PayoutRuleProduct

from infrastructure.utils.dependencies import get_current_user

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

def list_payout_rule_categories(code: str, current_user: dict, db: Session):
    require_country_access(code, current_user)
    rows = db.query(PayoutRuleCategory).filter(
        PayoutRuleCategory.country_code == code.upper(),
        PayoutRuleCategory.is_active == True,
    ).all()
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

def create_payout_rule_category(code: str, body: PayoutRuleCategoryBody, current_user: dict, db: Session):
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
    db.add(row)
    db.commit()
    db.refresh(row)
    return {"message": "Category payout rule created", "id": row.id}

def delete_payout_rule_category(code: str, rule_id: int, current_user: dict, db: Session):
    require_country_access(code, current_user)
    row = db.query(PayoutRuleCategory).filter(
        PayoutRuleCategory.id == rule_id,
        PayoutRuleCategory.country_code == code.upper(),
    ).first()
    if not row:
        raise HTTPException(status_code=404)
    db.delete(row)
    db.commit()
    return {"message": "Category payout rule deleted"}

def list_payout_rule_products(code: str, current_user: dict, db: Session):
    require_country_access(code, current_user)
    rows = db.query(PayoutRuleProduct).filter(
        PayoutRuleProduct.country_code == code.upper(),
        PayoutRuleProduct.is_active == True,
    ).all()
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

def create_payout_rule_product(code: str, body: PayoutRuleProductBody, current_user: dict, db: Session):
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
    db.add(row)
    db.commit()
    db.refresh(row)
    return {"message": "Product payout rule created", "id": row.id}

def delete_payout_rule_product(code: str, rule_id: int, current_user: dict, db: Session):
    require_country_access(code, current_user)
    row = db.query(PayoutRuleProduct).filter(
        PayoutRuleProduct.id == rule_id,
        PayoutRuleProduct.country_code == code.upper(),
    ).first()
    if not row:
        raise HTTPException(status_code=404)
    db.delete(row)
    db.commit()
    return {"message": "Product payout rule deleted"}


