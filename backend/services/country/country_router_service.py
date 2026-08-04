"""Service layer for country router DB operations.

This module contains all SQLAlchemy DB write/read operations moved from
the country-related router files to comply with the service layer architecture.
"""
from typing import List

import json

from fastapi import HTTPException
from sqlalchemy.orm import Session

from data.models import CountryConfig, CountryCity, CountryCommissionRate, PayoutRuleCategory, PayoutRuleProduct, SupplierKYCRequirement
from data.services_write_helpers import add_and_flush, commit_only, flush_only, commit_and_refresh, delete_only


def save_country_from_suggestion(
    db: Session,
    country_code: str,
    payload: dict,
    current_user: dict | None = None,
) -> dict:
    """Persist auto-populated country suggestion to the database."""
    existing = db.query(CountryConfig).filter(CountryConfig.code == country_code.upper()).first()
    if existing:
        raise HTTPException(status_code=409, detail=f"Country {country_code} already exists")

    config = CountryConfig(
        code=country_code.upper(),
        name=payload.get("name", country_code.upper()),
        official_name=payload.get("official_name", ""),
        alpha3=payload.get("alpha3", ""),
        phone_code=payload.get("phone_code", ""),
        flag_url=payload.get("flag_url", ""),
        status="draft",
        currency=payload.get("currency_code", ""),
        currency_symbol=payload.get("currency_symbol", ""),
        currency_name=payload.get("currency_name", ""),
        language=payload.get("default_language", "en"),
        timezone=payload.get("timezone", "UTC"),
        tax_type=payload.get("tax_type", "VAT"),
        tax_name=payload.get("tax_name", "VAT"),
        tax_rate=payload.get("default_tax_rate", 0.0),
        cod_enabled=payload.get("cod_enabled", True),
        population=payload.get("population"),
        gdp_per_capita_usd=payload.get("gdp_per_capita_usd"),
    )
    add_and_flush(db, config)
    flush_only(db)

    suggested_cities = payload.get("suggested_cities", [])
    for city_data in suggested_cities:
        city = CountryCity(
            country_code=country_code.upper(),
            name=city_data.get("name", ""),
            name_local=city_data.get("name_local"),
            population=city_data.get("population", 0),
            is_capital=city_data.get("is_capital", False),
            latitude=city_data.get("latitude"),
            longitude=city_data.get("longitude"),
            status="active",
            is_active=True,
        )
        add_and_flush(db, city)

    country_commissions = payload.get("suggested_commissions", {})
    for cat_name, rates in country_commissions.items():
        commission = CountryCommissionRate(
            country_code=country_code.upper(),
            supplier_tier=cat_name,
            name=cat_name,
            rate_percent=rates.get("suggested_rate", rates.get("min_rate", 0)),
            fixed_fee=0,
        )
        add_and_flush(db, commission)

    kyc_tier = payload.get("supplier_kyc_tier", "basic")
    kyc = SupplierKYCRequirement(
        country_code=country_code.upper(),
        kyc_tier_required=kyc_tier,
        document_types_required=json.dumps(
            [r["document"] for r in payload.get("supplier_requirements", [])]
        ),
    )
    add_and_flush(db, kyc)

    commit_only(db)

    return {
        "status": "created",
        "country_code": country_code.upper(),
        "country_name": config.name,
        "cities_added": len(suggested_cities),
    }


# --- Payout Rule Category Operations ---

def get_payout_rule_categories(db: Session, code: str, skip: int = 0, limit: int = 20) -> list[dict]:
    """List payout rule categories for a country."""
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


def create_payout_rule_category(db: Session, code: str, body: dict, current_user: dict | None = None) -> dict:
    """Create a payout rule category."""
    code_upper = code.upper()
    existing = db.query(PayoutRuleCategory).filter(
        PayoutRuleCategory.country_code == code_upper,
        PayoutRuleCategory.category_slug == body["category_slug"],
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="Rule already exists for this category")
    row = PayoutRuleCategory(
        country_code=code_upper,
        category_slug=body["category_slug"],
        payout_rate=body["payout_rate"],
        min_amount=body.get("min_amount"),
        max_amount=body.get("max_amount"),
        is_active=body.get("is_active", True),
    )
    add_and_flush(db, row)
    commit_and_refresh(db, row)
    return {"message": "Category payout rule created", "id": row.id}


def delete_payout_rule_category(db: Session, code: str, rule_id: int, current_user: dict | None = None) -> dict:
    """Delete a payout rule category."""
    row = db.query(PayoutRuleCategory).filter(
        PayoutRuleCategory.id == rule_id,
        PayoutRuleCategory.country_code == code.upper(),
    ).first()
    if not row:
        raise HTTPException(status_code=404)
    delete_only(db, row)
    commit_only(db)
    return {"message": "Category payout rule deleted"}


# --- Payout Rule Product Operations ---

def get_payout_rule_products(db: Session, code: str, skip: int = 0, limit: int = 20) -> list[dict]:
    """List payout rule products for a country."""
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


def create_payout_rule_product(db: Session, code: str, body: dict, current_user: dict | None = None) -> dict:
    """Create a payout rule product."""
    code_upper = code.upper()
    existing = db.query(PayoutRuleProduct).filter(
        PayoutRuleProduct.country_code == code_upper,
        PayoutRuleProduct.product_id == body["product_id"],
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="Rule already exists for this product")
    row = PayoutRuleProduct(
        country_code=code_upper,
        product_id=body["product_id"],
        payout_rate=body["payout_rate"],
        min_amount=body.get("min_amount"),
        max_amount=body.get("max_amount"),
        is_active=body.get("is_active", True),
    )
    add_and_flush(db, row)
    commit_and_refresh(db, row)
    return {"message": "Product payout rule created", "id": row.id}


def delete_payout_rule_product(db: Session, code: str, rule_id: int, current_user: dict | None = None) -> dict:
    """Delete a payout rule product."""
    row = db.query(PayoutRuleProduct).filter(
        PayoutRuleProduct.id == rule_id,
        PayoutRuleProduct.country_code == code.upper(),
    ).first()
    if not row:
        raise HTTPException(status_code=404)
    delete_only(db, row)
    commit_only(db)
    return {"message": "Product payout rule deleted"}