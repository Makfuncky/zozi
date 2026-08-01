"""Auto-populate endpoint for the Country Control Plane.

Wires the heuristic engine and external data fetchers to database persistence.
"""
from __future__ import annotations

import json
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from db.database import get_db
from models.countries import CountryConfig
from models.country_enhancements import CountryCategoryTaxRate, CountryCity, CountryCommissionRate, SupplierKYCRequirement
from routers.auth import get_current_user
from services.country_auto_populate import auto_populate_country

from services.write_helpers import add_and_flush, commit_only, flush_only
logger = logging.getLogger(__name__)


def _user_role(user: object) -> str:
    if hasattr(user, "role"):
        return str(getattr(user, "role") or "")
    if isinstance(user, dict):
        return str(user.get("role") or "")
    return ""


router = APIRouter(tags=["country-auto-populate"])


@router.post("/auto-populate")
async def auto_populate(
    search_term: str = Query(..., min_length=2, description="Country name or ISO code"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Search and auto-populate country data from external APIs + heuristic engine.

    Returns the full suggested payload the frontend Ghost Row can render.
    Data is NOT persisted — admin must call POST /admin/countries/{code}/save to commit.
    """
    if _user_role(current_user).lower() not in ("admin", "superadmin"):
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        result = await auto_populate_country(search_term)
        if not result or result.get("status") == "error":
            raise HTTPException(status_code=404, detail=result.get("error", "Country not found"))

        return {
            "status": "success",
            "cached": result.get("cached", False),
            "fetched_at": result.get("fetched_at"),
            "data": result,
        }
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Auto-populate failed for %s", search_term)
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/{country_code}/save")
def save_country_from_suggestion(
    country_code: str,
    payload: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Persist auto-populated country suggestion to the database.

    Accepts the full payload from POST /admin/countries/auto-populate
    and writes it into CountryConfig + related tables.
    """
    if _user_role(current_user).lower() not in ("admin", "superadmin"):
        raise HTTPException(status_code=403, detail="Admin access required")

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
