"""Country auto-populate persistence (write side).

Owns the DB writes for ``save_country_from_suggestion`` (W1) and the existence
check read (Q1). The read-only suggestion fetch stays in
``data.services_country_auto_populate.auto_populate_country``. Return shape
matches the previous router implementation.
"""
from __future__ import annotations

import json
from typing import Any

from sqlalchemy.orm import Session

from data.models_countries import CountryConfig
from data.models_country_enhancements import (
    CountryCity,
    CountryCommissionRate,
    SupplierKYCRequirement,
)
import structlog
logger = structlog.get_logger(__name__)


def save_country_from_suggestion(
    db: Session, country_code: str, payload: dict[str, Any]
) -> dict:
    """Persist an auto-populated country suggestion into CountryConfig + related."""
    existing = (
        db.query(CountryConfig).filter(CountryConfig.code == country_code.upper()).first()
    )
    if existing:
        from fastapi import HTTPException

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
    db.add(config)
    db.flush()

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
        db.add(city)

    country_commissions = payload.get("suggested_commissions", {})
    for cat_name, rates in country_commissions.items():
        commission = CountryCommissionRate(
            country_code=country_code.upper(),
            supplier_tier=cat_name,
            name=cat_name,
            rate_percent=rates.get("suggested_rate", rates.get("min_rate", 0)),
            fixed_fee=0,
        )
        db.add(commission)

    kyc_tier = payload.get("supplier_kyc_tier", "basic")
    kyc = SupplierKYCRequirement(
        country_code=country_code.upper(),
        kyc_tier_required=kyc_tier,
        document_types_required=json.dumps(
            [r["document"] for r in payload.get("supplier_requirements", [])]
        ),
    )
    db.add(kyc)

    db.commit()

    return {
        "status": "created",
        "country_code": country_code.upper(),
        "country_name": config.name,
        "cities_added": len(suggested_cities),
    }
