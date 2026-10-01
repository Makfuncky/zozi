"""Country payout-rule writes + reads (category and product overrides).

Owns every DB read/write for the country-payouts router so the router stays a
thin HTTP adapter. Functions take the injected ``db`` session and own
``add``/``commit``/``delete`` (W1); queries that lived in the router are also
moved here (Q1). Return shapes match the previous router implementation.
"""
from __future__ import annotations

from decimal import Decimal
from typing import Any

from sqlalchemy.orm import Session

from domains.finance.models.tax_rules import PayoutRuleCategory
from domains.finance.models.tax_rules import PayoutRuleProduct
import structlog
logger = structlog.get_logger(__name__)


def _category_row(r: PayoutRuleCategory) -> dict:
    return {
        "id": r.id,
        "country_code": r.country_code,
        "category_slug": r.category_slug,
        "payout_rate": Decimal(str(r.payout_rate)),
        "min_amount": Decimal(str(r.min_amount)) if r.min_amount else None,
        "max_amount": Decimal(str(r.max_amount)) if r.max_amount else None,
        "is_active": r.is_active,
    }


def _product_row(r: PayoutRuleProduct) -> dict:
    return {
        "id": r.id,
        "country_code": r.country_code,
        "product_id": r.product_id,
        "payout_rate": Decimal(str(r.payout_rate)),
        "min_amount": Decimal(str(r.min_amount)) if r.min_amount else None,
        "max_amount": Decimal(str(r.max_amount)) if r.max_amount else None,
        "is_active": r.is_active,
    }


def list_payout_rule_categories(db: Session, code: str) -> list[dict]:
    rows = (
        db.query(PayoutRuleCategory)
        .filter(
            PayoutRuleCategory.country_code == code.upper(),
            PayoutRuleCategory.is_active == True,
        )
        .all()
    )
    return [_category_row(r) for r in rows]


def create_payout_rule_category(db: Session, code: str, body: Any) -> dict:
    code_upper = code.upper()
    existing = (
        db.query(PayoutRuleCategory)
        .filter(
            PayoutRuleCategory.country_code == code_upper,
            PayoutRuleCategory.category_slug == body.category_slug,
        )
        .first()
    )
    if existing:
        from fastapi import HTTPException

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


def delete_payout_rule_category(db: Session, code: str, rule_id: int) -> dict:
    row = (
        db.query(PayoutRuleCategory)
        .filter(
            PayoutRuleCategory.id == rule_id,
            PayoutRuleCategory.country_code == code.upper(),
        )
        .first()
    )
    if not row:
        from fastapi import HTTPException

        raise HTTPException(status_code=404)
    db.delete(row)
    db.commit()
    return {"message": "Category payout rule deleted"}


def list_payout_rule_products(db: Session, code: str) -> list[dict]:
    rows = (
        db.query(PayoutRuleProduct)
        .filter(
            PayoutRuleProduct.country_code == code.upper(),
            PayoutRuleProduct.is_active == True,
        )
        .all()
    )
    return [_product_row(r) for r in rows]


def create_payout_rule_product(db: Session, code: str, body: Any) -> dict:
    code_upper = code.upper()
    existing = (
        db.query(PayoutRuleProduct)
        .filter(
            PayoutRuleProduct.country_code == code_upper,
            PayoutRuleProduct.product_id == body.product_id,
        )
        .first()
    )
    if existing:
        from fastapi import HTTPException

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


def delete_payout_rule_product(db: Session, code: str, rule_id: int) -> dict:
    row = (
        db.query(PayoutRuleProduct)
        .filter(
            PayoutRuleProduct.id == rule_id,
            PayoutRuleProduct.country_code == code.upper(),
        )
        .first()
    )
    if not row:
        from fastapi import HTTPException

        raise HTTPException(status_code=404)
    db.delete(row)
    db.commit()
    return {"message": "Product payout rule deleted"}

# === Merged from country_payouts_service.py ===
# Read-side payout functions preserved for reference
