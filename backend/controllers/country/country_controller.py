from __future__ import annotations
import json
import os
from decimal import Decimal
from typing import Any, Set, Optional

from fastapi import HTTPException, Depends
from sqlalchemy.orm import Session, Query
from contextvars import ContextVar

from models import (
    CountryCommunication,
    CountryConfig,
    CountryConfigVersion,
    CountryFeatureFlag,
    CountryStaffAssignment,
    CountryCity,
    CrossCountryCustomerSession,
    OmanDeliveryZone,
    SupplierCountryCommission,
)
from services.logistics_partner_pricing import normalize_country_code
from services.tax_service import calculate_tax
from utils.datetime_utils import utcnow as _utcnow
from services.country_write_service import (
    add_country_communication,
    add_country_city,
    add_feature_flag,
    add_oman_delivery_zone,
    add_supplier_commission,
    add_tax_entry,
    add_to_session,
    bulk_replace_country_cities,
    commit_and_refresh_obj,
    commit_country_changes,
    mark_communication_read as ws_mark_communication_read,
    record_admin_change,
)

_country_scope_var: ContextVar[Set[str]] = ContextVar('country_scope', default=set())


def set_country_scope(scope: Set[str]) -> None:
    _country_scope_var.set(scope)


def get_current_country_scope() -> Set[str]:
    return _country_scope_var.get()


def _require_admin(current_user: dict) -> None:
    role = str(current_user.get("role") or "").lower()
    allowed = {"admin", "country_head", "country_manager", "sub_admin"}
    if role not in allowed:
        raise HTTPException(status_code=403, detail="Staff access required")


def _require_full_admin(current_user: dict) -> None:
    """Strict admin-only check for operations like creating/deleting countries."""
    role = str(current_user.get("role") or "").lower()
    if role != "admin":
        raise HTTPException(status_code=403, detail="Admin-only access required for this operation")


def _require_country_access(country_code: str, current_user: dict) -> None:
    """Check country-scoped access for country_head/country_manager roles."""
    role = str(current_user.get("role") or "").lower()
    if role == "admin":
        return
    if role not in ("country_head", "country_manager"):
        raise HTTPException(status_code=403, detail="Country-level access required")
    codes = current_user.get("staff_country_codes", None)
    if not codes or not isinstance(codes, (list, tuple)):
        raise HTTPException(status_code=403, detail="You are not assigned to any country")
    if country_code.upper() not in [str(c).strip().upper() for c in codes]:
        raise HTTPException(
            status_code=403,
            detail=f"You do not have access to country '{country_code}'",
        )


def _to_json(value: Any) -> str:
    return json.dumps(value, default=str)


def _from_json(raw: str | None, *, default: Any) -> Any:
    if not raw:
        return default
    try:
        parsed = json.loads(raw)
    except (TypeError, ValueError, json.JSONDecodeError):
        return default
    return parsed


async def auto_populate_async(search_term: str) -> dict[str, Any]:
    """Async wrapper around the auto-populate service with heuristic engine enrichment."""
    from services.country_auto_populate import auto_populate_country
    from services.country_heuristic_engine import generate_ecommerce_defaults

    base = await auto_populate_country(search_term)
    if "error" in base:
        return base

    code = base.get("code", search_term).upper()
    heuristic = generate_ecommerce_defaults(
        code=code,
        name=base.get("name", ""),
        region=base.get("region"),
        subregion=base.get("subregion"),
        gdp_per_capita=base.get("gdp_per_capita_usd"),
        internet_penetration_pct=base.get("internet_penetration_pct"),
        population=base.get("population"),
    )

    base.setdefault("suggested_gateways", heuristic.get("suggested_gateways", []))
    base.setdefault("suggested_commission_tiers", heuristic.get("suggested_commission_tiers", []))
    base.setdefault("suggested_supplier_requirements", heuristic.get("suggested_supplier_requirements", {}))
    base.setdefault("suggested_payout_settings", heuristic.get("suggested_payout_settings", {}))
    base.setdefault("cod_reliance_estimate", heuristic.get("cod_reliance_estimate", {}))
    base.setdefault("product_restrictions", heuristic.get("product_restrictions", []))
    base.setdefault("consumer_profile", heuristic.get("consumer_profile", {}))
    base.setdefault("suggested_logistics_model", heuristic.get("suggested_logistics_model"))
    base.setdefault("suggested_logistics_zones", heuristic.get("suggested_logistics_zones", []))
    base.setdefault("fraud_risk_tier", heuristic.get("fraud_risk_tier", "medium"))
    base.setdefault("heuristic_region", heuristic.get("heuristic_region"))
    base.setdefault("economic_tier", heuristic.get("economic_tier"))
    base.setdefault("confidence_score", heuristic.get("confidence_score", 0.5))

    return base


def _to_decimal(value: Any, *, field: str) -> Decimal:
    try:
        return Decimal(str(value))
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Invalid decimal for {field}") from exc


def _get_country_or_404(code: str, db: Session) -> CountryConfig:
    normalized = normalize_country_code(code)
    country = db.query(CountryConfig).filter(CountryConfig.code == normalized).first()
    if not country:
        raise HTTPException(status_code=404, detail="Country config not found")
    return country


def _record_admin_change(
    db: Session,
    *,
    actor_id: int | None,
    action: str,
    entity: str,
    entity_key: str | None,
    before: Any,
    after: Any,
    notes: str | None = None,
) -> None:
    record_admin_change(
        db,
        actor_id=actor_id,
        action=action,
        entity=entity,
        entity_key=entity_key,
        before=before,
        after=after,
        notes=notes,
    )


def _next_version(db: Session, country_code: str, config_type: str) -> int:
    latest = (
        db.query(CountryConfigVersion)
        .filter(
            CountryConfigVersion.country_code == country_code,
            CountryConfigVersion.config_type == config_type,
        )
        .order_by(CountryConfigVersion.version.desc())
        .first()
    )
    return int(getattr(latest, "version", 0) or 0) + 1


def _create_draft_version(
    db: Session,
    *,
    country_code: str,
    config_type: str,
    payload: dict[str, Any],
    actor_id: int | None,
) -> CountryConfigVersion:
    version = CountryConfigVersion(
        country_code=country_code,
        config_type=config_type,
        version=_next_version(db, country_code, config_type),
        payload_json=_to_json(payload),
        status="draft",
        draft_by=actor_id,
        created_at=_utcnow(),
    )
    add_to_session(db, version)
    return version


def _country_public_payload(country: CountryConfig, db: Session | None = None) -> dict[str, Any]:
    city_count = 0
    if db is not None:
        try:
            city_count = db.query(CountryCity).filter(
                CountryCity.country_code == country.code,
                CountryCity.is_active == True,
            ).count()
        except Exception:
            city_count = 0

    return {
        "code": country.code,
        "name": country.name,
        "currency": country.currency,
        "currency_symbol": country.currency_symbol,
        "phone_code": country.phone_code,
        "language": country.language or "en",
        "timezone": country.timezone,
        "tax_type": country.tax_type,
        "tax_rate": float(country.tax_rate) if country.tax_rate is not None else 0.0,
        "tax_name": country.tax_name,
        "tax_inclusive": bool(country.tax_inclusive),
        "tax_exempt_categories": _from_json(country.tax_exempt_categories_json, default=[]),
        "tax_reduced_rates": _from_json(country.tax_reduced_rates_json, default={}),
        "logistics_model": country.logistics_model,
        "default_vehicle_type": country.default_vehicle_type,
        "base_rate": float(country.base_rate) if country.base_rate is not None else None,
        "per_km_rate": float(country.per_km_rate) if country.per_km_rate is not None else None,
        "minimum_charge": float(country.minimum_charge) if country.minimum_charge is not None else None,
        "weight_surcharge_rate": float(country.weight_surcharge_rate) if country.weight_surcharge_rate is not None else None,
        "weight_surcharge_threshold_kg": float(country.weight_surcharge_threshold_kg) if country.weight_surcharge_threshold_kg is not None else None,
        "payment_methods": _from_json(country.payment_methods_json, default=[]),
        "payment_gateways": _from_json(country.payment_gateways_json, default=[]),
        "logistics_providers": _from_json(country.logistics_providers_json, default=[]),
    "date_format": country.date_format or "DD/MM/YYYY",
    "address_format": _from_json(country.address_format_json, default={}),
    "legal_rules": _from_json(country.legal_rules_json, default={}),
    "product_restrictions": _from_json(country.product_restrictions_json, default=[]),
    "regions": _from_json(country.regions_json, default=[]),
    "supplier_requirements": _from_json(country.supplier_requirements_json, default={}),
        "payout_settings": _from_json(country.payout_settings_json, default={}),
        "commission_tiers": _from_json(country.commission_tiers_json, default=[]),
        "is_active": bool(country.is_active),
        "city_count": city_count,
        # Ã¢â€�â‚¬Ã¢â€�â‚¬ Phase 1: Heuristic fields Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬
        "economic_tier": country.economic_tier,
        "fraud_risk_tier": country.fraud_risk_tier,
        "suggested_logistics_model": country.suggested_logistics_model,
        "suggested_commission_ranges": _from_json(country.suggested_commission_ranges_json, default={}),
        "suggested_gateway_rankings": _from_json(country.suggested_gateway_rankings_json, default=[]),
        "consumer_behavior_profile": _from_json(country.consumer_behavior_profile_json, default={}),
        # Ã¢â€�â‚¬Ã¢â€�â‚¬ Phase 1: Expanded identity Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬
        "official_name": country.official_name,
        "alpha3": country.alpha3,
        "flag_url": country.flag_url,
        "currency_name": country.currency_name,
        "exchange_rate_to_usd": float(country.exchange_rate_to_usd) if country.exchange_rate_to_usd is not None else None,
        # Ã¢â€�â‚¬Ã¢â€�â‚¬ Phase 1: COD / settlement Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬
        "cod_enabled": bool(country.cod_enabled) if country.cod_enabled is not None else True,
        "cod_max_amount": float(country.cod_max_amount) if country.cod_max_amount is not None else None,
        "cod_verification_required": bool(country.cod_verification_required) if country.cod_verification_required is not None else False,
        "cod_remittance_days": country.cod_remittance_days,
        "settlement_hold_days": country.settlement_hold_days,
        "minimum_payout_amount": float(country.minimum_payout_amount) if country.minimum_payout_amount is not None else None,
        "payout_currency": country.payout_currency,
        # Ã¢â€�â‚¬Ã¢â€�â‚¬ Phase 1: Supplier Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬
        "supplier_kyc_tier": country.supplier_kyc_tier,
        "supplier_onboarding_fee": float(country.supplier_onboarding_fee) if country.supplier_onboarding_fee is not None else None,
        "supplier_monthly_fee": float(country.supplier_monthly_fee) if country.supplier_monthly_fee is not None else None,
        "supplier_rating_threshold": float(country.supplier_rating_threshold) if country.supplier_rating_threshold is not None else None,
        # Ã¢â€�â‚¬Ã¢â€�â‚¬ Phase 1: Legal / consumer Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬
        "legal_entity_required": bool(country.legal_entity_required) if country.legal_entity_required is not None else False,
        "consumer_protection_days": country.consumer_protection_days,
        "data_privacy_framework": country.data_privacy_framework,
        # Ã¢â€�â‚¬Ã¢â€�â‚¬ Phase 1: Logistics Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬
        "max_package_weight_kg": float(country.max_package_weight_kg) if country.max_package_weight_kg is not None else None,
        "max_package_dimensions_cm": country.max_package_dimensions_cm,
        "signature_required_threshold": float(country.signature_required_threshold) if country.signature_required_threshold is not None else None,
        # Ã¢â€�â‚¬Ã¢â€�â‚¬ Phase 1: Locale Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬
        "measurement_system": country.measurement_system or "metric",
        "working_days": _from_json(country.working_days_json, default=[]),
    }



def list_public_countries(db: Session) -> list[dict[str, Any]]:
    rows = (
        db.query(CountryConfig)
        .filter(CountryConfig.is_active == True)  # noqa: E712
        .order_by(CountryConfig.code.asc())
        .all()
    )
    return [{"code": row.code, "name": row.name, "currency": row.currency} for row in rows]


def list_public_cities(code: str, db: Session) -> dict[str, Any]:
    """Public cities list Ã¢â‚¬â€� no auth, active cities only, for dropdowns."""
    cc = code.upper()
    country = db.query(CountryConfig).filter(
        CountryConfig.code == cc,
        CountryConfig.is_active == True,  # noqa: E712
    ).first()
    if not country:
        raise HTTPException(status_code=404, detail="Country not found or inactive")

    cities = (
        db.query(CountryCity)
        .filter(CountryCity.country_code == cc, CountryCity.is_active == True)
        .order_by(CountryCity.population.desc().nullslast(), CountryCity.name.asc())
        .all()
    )
    return {
        "code": cc,
        "cities": [
            {
                "id": c.id,
                "name": c.name,
                "region": c.region or "",
                "latitude": float(c.latitude) if c.latitude is not None else None,
                "longitude": float(c.longitude) if c.longitude is not None else None,
                "population": c.population,
            }
            for c in cities
        ],
    }


def get_public_country_config(code: str, db: Session) -> dict[str, Any]:
    country = _get_country_or_404(code, db)
    if not country.is_active:
        raise HTTPException(status_code=404, detail="Country is inactive")
    return _country_public_payload(country, db)


def list_admin_countries(current_user: dict, db: Session) -> list[dict[str, Any]]:
    _require_admin(current_user)
    query = db.query(CountryConfig)
    role = str(current_user.get("role") or "").lower()
    if role in ("country_head", "country_manager"):
        assigned = [str(c).strip().upper() for c in (current_user.get("staff_country_codes") or [])]
        if assigned:
            query = query.filter(CountryConfig.code.in_(assigned))
    rows = query.order_by(CountryConfig.code.asc()).all()
    return [_country_public_payload(row, db) for row in rows]


def get_admin_country(code: str, current_user: dict, db: Session) -> dict[str, Any]:
    _require_admin(current_user)
    _require_country_access(code, current_user)
    return _country_public_payload(_get_country_or_404(code, db), db)


def create_admin_country(payload: dict[str, Any], current_user: dict, db: Session) -> dict[str, Any]:
    _require_full_admin(current_user)
    normalized_code = normalize_country_code(str(payload.get("code") or ""))
    if not normalized_code:
        raise HTTPException(status_code=422, detail="Invalid country code")

    existing = db.query(CountryConfig).filter(CountryConfig.code == normalized_code).first()
    if existing:
        raise HTTPException(status_code=409, detail="Country already exists")

    name = str(payload.get("name") or "").strip()
    currency = str(payload.get("currency") or "").strip().upper()
    timezone = str(payload.get("timezone") or "").strip()
    is_active = bool(payload.get("is_active", True))

    if not name or not currency or not timezone:
        raise HTTPException(status_code=422, detail="Name, currency, and timezone are required")

    # Resolve logistics defaults from payload
    logistics_defaults = payload.get("logistics_defaults") or {}
    legal_rules = payload.get("legal_rules") or {}

    country = CountryConfig(
        code=normalized_code,
        name=name,
        currency=currency,
        currency_symbol=str(payload.get("currency_symbol") or "").strip() or None,
        phone_code=str(payload.get("phone_code") or "").strip() or None,
        language=str(payload.get("language") or "en").strip().lower() or "en",
        timezone=timezone,
        tax_type=str(payload.get("tax_type") or "VAT"),
        tax_rate=Decimal(str(payload["tax_rate"])) if payload.get("tax_rate") is not None else Decimal("0.0000"),
        tax_name=str(payload.get("tax_name") or "Tax"),
        tax_inclusive=False,
        tax_exempt_categories_json="[]",
        tax_reduced_rates_json="{}",
        logistics_model=str(logistics_defaults.get("logistics_model") or "fixed"),
        default_vehicle_type=logistics_defaults.get("default_vehicle_type"),
        base_rate=logistics_defaults.get("base_rate"),
        per_km_rate=logistics_defaults.get("per_km_rate"),
        minimum_charge=logistics_defaults.get("minimum_charge"),
        weight_surcharge_rate=logistics_defaults.get("weight_surcharge_rate"),
        weight_surcharge_threshold_kg=logistics_defaults.get("weight_surcharge_threshold_kg"),
        payment_methods_json="[]",
        payment_gateways_json=_to_json(payload.get("payment_gateways")),
        logistics_providers_json=_to_json(payload.get("logistics_providers")),
        legal_rules_json=_to_json(legal_rules),
        product_restrictions_json=_to_json(payload.get("product_restrictions")),
        address_format_json='{"fields":["street","city","postal_code"],"required":["street","city"]}',
        date_format=str(payload.get("date_format") or "DD/MM/YYYY").strip(),
        regions_json="[]",
        supplier_requirements_json=_to_json(payload.get("supplier_requirements")),
        payout_settings_json=_to_json(payload.get("payout_settings")),
        commission_tiers_json=_to_json(payload.get("commission_tiers")),
        is_active=is_active,
        # Macro indicators
        population=payload.get("population"),
        internet_penetration_pct=payload.get("internet_penetration_pct"),
        gdp_per_capita_usd=payload.get("gdp_per_capita_usd"),
        urbanization_pct=payload.get("urbanization_pct"),
        mobile_subs_per_100=payload.get("mobile_subs_per_100"),
        public_holidays_json=_to_json(payload.get("public_holidays")),
        macro_indicators_json=_to_json(payload.get("macro_indicators")),
        # Ã¢â€�â‚¬Ã¢â€�â‚¬ Phase 1: Heuristic fields Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬
        economic_tier=str(payload.get("economic_tier") or "").strip() or None,
        fraud_risk_tier=str(payload.get("fraud_risk_tier") or "").strip() or None,
        suggested_logistics_model=str(payload.get("suggested_logistics_model") or "").strip() or None,
        suggested_commission_ranges_json=_to_json(payload.get("suggested_commission_ranges")),
        suggested_gateway_rankings_json=_to_json(payload.get("suggested_gateway_rankings")),
        consumer_behavior_profile_json=_to_json(payload.get("consumer_behavior_profile")),
        # Ã¢â€�â‚¬Ã¢â€�â‚¬ Phase 1: Expanded identity Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬
        official_name=str(payload.get("official_name") or "").strip() or None,
        alpha3=str(payload.get("alpha3") or "").strip().upper() or None,
        flag_url=str(payload.get("flag_url") or "").strip() or None,
        currency_name=str(payload.get("currency_name") or "").strip() or None,
        exchange_rate_to_usd=payload.get("exchange_rate_to_usd"),
        # Ã¢â€�â‚¬Ã¢â€�â‚¬ Phase 1: COD / settlement Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬
        cod_enabled=payload.get("cod_enabled"),
        cod_max_amount=payload.get("cod_max_amount"),
        cod_verification_required=payload.get("cod_verification_required"),
        cod_remittance_days=payload.get("cod_remittance_days"),
        settlement_hold_days=payload.get("settlement_hold_days") or 3,
        minimum_payout_amount=payload.get("minimum_payout_amount"),
        payout_currency=str(payload.get("payout_currency") or "").strip().upper() or None,
        # Ã¢â€�â‚¬Ã¢â€�â‚¬ Phase 1: Supplier defaults Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬
        supplier_kyc_tier=str(payload.get("supplier_kyc_tier") or "").strip() or None,
        supplier_onboarding_fee=payload.get("supplier_onboarding_fee"),
        supplier_monthly_fee=payload.get("supplier_monthly_fee"),
        supplier_rating_threshold=payload.get("supplier_rating_threshold"),
        # Ã¢â€�â‚¬Ã¢â€�â‚¬ Phase 1: Legal / consumer Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬
        legal_entity_required=payload.get("legal_entity_required"),
        consumer_protection_days=payload.get("consumer_protection_days") or 14,
        data_privacy_framework=str(payload.get("data_privacy_framework") or "").strip() or None,
        # Ã¢â€�â‚¬Ã¢â€�â‚¬ Phase 1: Logistics expansion Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬
        max_package_weight_kg=payload.get("max_package_weight_kg"),
        max_package_dimensions_cm=str(payload.get("max_package_dimensions_cm") or "").strip() or None,
        signature_required_threshold=payload.get("signature_required_threshold"),
        # Ã¢â€�â‚¬Ã¢â€�â‚¬ Phase 1: Locale Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬
        measurement_system=str(payload.get("measurement_system") or "metric").strip().lower(),
        working_days_json=_to_json(payload.get("working_days")),
    )
    add_to_session(db, country)
    _record_admin_change(
        db,
        actor_id=current_user.get("id"),
        action="create",
        entity="country",
        entity_key=country.code,
        before=None,
        after=_country_public_payload(country, db),
    )
    commit_and_refresh_obj(db, country)

    # Persist cities
    cities_data = payload.get("cities") or []
    for c in cities_data:
        city = CountryCity(
            country_code=normalized_code,
            name=str(c.get("name", "")).strip(),
            region=str(c.get("region", "")).strip() or None,
            latitude=float(c["lat"]) if c.get("lat") is not None else None,
            longitude=float(c["lng"]) if c.get("lng") is not None else None,
            population=int(c["population"]) if c.get("population") is not None else None,
            source=str(c.get("source", "openmeteo")),
        )
        add_country_city(db, city)

    # Persist category tax rates
    tax_rates_data = payload.get("category_tax_rates") or []
    for tr in tax_rates_data:
        tax_entry = CountryCategoryTaxRate(
            country_code=normalized_code,
            category_slug=str(tr.get("category_slug", "")).strip(),
            rate=Decimal(str(round(float(tr.get("rate", 0.0)), 4))),
            is_exempt=bool(tr.get("is_exempt", False)),
            is_reduced=bool(tr.get("is_reduced", False)),
            notes=str(tr.get("notes", "")) or None,
            source=str(tr.get("source", "curated")),
        )
        add_tax_entry(db, tax_entry)

    # Set macro fields on country
    if payload.get("population") is not None:
        country.population = int(payload["population"])
    if payload.get("internet_penetration_pct") is not None:
        country.internet_penetration_pct = Decimal(str(payload["internet_penetration_pct"]))
    if payload.get("gdp_per_capita_usd") is not None:
        country.gdp_per_capita_usd = Decimal(str(payload["gdp_per_capita_usd"]))
    if payload.get("urbanization_pct") is not None:
        country.urbanization_pct = Decimal(str(payload["urbanization_pct"]))
    if payload.get("mobile_subs_per_100") is not None:
        country.mobile_subs_per_100 = Decimal(str(payload["mobile_subs_per_100"]))

    # Ã¢â€�â‚¬Ã¢â€�â‚¬ Persist heuristic engine metadata Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬
    if payload.get("suggested_gateways"):
        country.suggested_gateway_rankings_json = _to_json(payload["suggested_gateways"])
    if payload.get("suggested_commission_tiers"):
        country.suggested_commission_ranges_json = _to_json(payload["suggested_commission_tiers"])
    if payload.get("suggested_supplier_requirements"):
        country.supplier_requirements_json = _to_json(payload["suggested_supplier_requirements"])
    if payload.get("suggested_payout_settings"):
        country.payout_settings_json = _to_json(payload["suggested_payout_settings"])
    if payload.get("consumer_profile"):
        country.consumer_behavior_profile_json = _to_json(payload["consumer_profile"])
    if payload.get("cod_reliance_estimate"):
        cod_est = payload["cod_reliance_estimate"]
        if cod_est.get("cod_pct") is not None:
            country.cod_enabled = True
    if payload.get("heuristic_region"):
        region = str(payload["heuristic_region"]).strip()
        if region and not country.regions_json or country.regions_json == "[]":
            country.regions_json = _to_json([{"region_id": "default", "name": region, "cities": []}])

    commit_and_refresh_obj(db, country)
    return _country_public_payload(country, db)



def create_tax_draft(code: str, payload: dict[str, Any], current_user: dict, db: Session) -> dict[str, Any]:
    _require_admin(current_user)
    _require_country_access(code, current_user)
    country = _get_country_or_404(code, db)

    draft_payload = {
        "tax_type": str(payload.get("tax_type") or country.tax_type).strip().upper(),
        "tax_rate": str(_to_decimal(payload.get("tax_rate", country.tax_rate), field="tax_rate")),
        "tax_name": str(payload.get("tax_name") or country.tax_name).strip() or country.tax_name,
        "tax_inclusive": bool(payload.get("tax_inclusive", country.tax_inclusive)),
        "tax_exempt_categories": payload.get("tax_exempt_categories", _from_json(country.tax_exempt_categories_json, default=[])),
        "tax_reduced_rates": payload.get("tax_reduced_rates", _from_json(country.tax_reduced_rates_json, default={})),
    }

    version = _create_draft_version(
        db,
        country_code=country.code,
        config_type="tax",
        payload=draft_payload,
        actor_id=current_user.get("id"),
    )
    _record_admin_change(
        db,
        actor_id=current_user.get("id"),
        action="create_draft",
        entity="country_tax",
        entity_key=f"{country.code}:v{version.version}",
        before=_country_public_payload(country, db),
        after=draft_payload,
    )
    commit_country_changes(db)
    return {"message": "Tax draft created", "version_id": version.id, "version": version.version}


def create_logistics_draft(code: str, payload: dict[str, Any], current_user: dict, db: Session) -> dict[str, Any]:
    _require_admin(current_user)
    _require_country_access(code, current_user)
    country = _get_country_or_404(code, db)
    delivery_zones = payload.get("delivery_zones")
    if delivery_zones is None:
        # Backward compatibility with previous Oman-specific payload key.
        delivery_zones = payload.get("oman_zones")

    draft_payload = {
        "logistics_model": str(payload.get("logistics_model") or country.logistics_model).strip().lower(),
        "default_vehicle_type": str(payload.get("default_vehicle_type") or country.default_vehicle_type or "").strip() or None,
        "base_rate": payload.get("base_rate", float(country.base_rate) if country.base_rate is not None else None),
        "per_km_rate": payload.get("per_km_rate", float(country.per_km_rate) if country.per_km_rate is not None else None),
        "minimum_charge": payload.get("minimum_charge", float(country.minimum_charge) if country.minimum_charge is not None else None),
        "weight_surcharge_rate": payload.get("weight_surcharge_rate", float(country.weight_surcharge_rate) if country.weight_surcharge_rate is not None else None),
        "weight_surcharge_threshold_kg": payload.get("weight_surcharge_threshold_kg", float(country.weight_surcharge_threshold_kg) if country.weight_surcharge_threshold_kg is not None else None),
        "delivery_zones": delivery_zones if isinstance(delivery_zones, list) else [],
    }

    version = _create_draft_version(
        db,
        country_code=country.code,
        config_type="logistics",
        payload=draft_payload,
        actor_id=current_user.get("id"),
    )
    _record_admin_change(
        db,
        actor_id=current_user.get("id"),
        action="create_draft",
        entity="country_logistics",
        entity_key=f"{country.code}:v{version.version}",
        before=_country_public_payload(country, db),
        after=draft_payload,
    )
    commit_country_changes(db)
    return {"message": "Logistics draft created", "version_id": version.id, "version": version.version}


def create_commission_draft(code: str, payload: dict[str, Any], current_user: dict, db: Session) -> dict[str, Any]:
    _require_admin(current_user)
    _require_country_access(code, current_user)
    country = _get_country_or_404(code, db)
    rates = payload.get("rates")
    if not isinstance(rates, list):
        raise HTTPException(status_code=422, detail="rates must be a list")

    normalized_rates: list[dict[str, Any]] = []
    for row in rates:
        if not isinstance(row, dict):
            continue
        slug = str(row.get("category_slug") or "").strip().lower()
        if not slug:
            continue
        normalized_rates.append(
            {
                "category_slug": slug,
                "commission_rate": str(_to_decimal(row.get("commission_rate", 0), field=f"commission_rate[{slug}]")),
                "notes": str(row.get("notes") or "").strip() or None,
                "is_active": bool(row.get("is_active", True)),
            }
        )

    version = _create_draft_version(
        db,
        country_code=country.code,
        config_type="commission",
        payload={"rates": normalized_rates},
        actor_id=current_user.get("id"),
    )
    _record_admin_change(
        db,
        actor_id=current_user.get("id"),
        action="create_draft",
        entity="country_commission",
        entity_key=f"{country.code}:v{version.version}",
        before=None,
        after=normalized_rates,
    )
    commit_country_changes(db)
    return {"message": "Commission draft created", "version_id": version.id, "version": version.version}


def create_payment_and_flags_draft(code: str, payload: dict[str, Any], current_user: dict, db: Session) -> dict[str, Any]:
    _require_admin(current_user)
    _require_country_access(code, current_user)
    country = _get_country_or_404(code, db)

    draft_payload = {
        "payment_methods": payload.get("payment_methods", _from_json(country.payment_methods_json, default=[])),
        "feature_flags": payload.get("feature_flags", {}),
    }
    version = _create_draft_version(
        db,
        country_code=country.code,
        config_type="ops",
        payload=draft_payload,
        actor_id=current_user.get("id"),
    )
    _record_admin_change(
        db,
        actor_id=current_user.get("id"),
        action="create_draft",
        entity="country_ops",
        entity_key=f"{country.code}:v{version.version}",
        before=None,
        after=draft_payload,
    )
    commit_country_changes(db)
    return {"message": "Ops draft created", "version_id": version.id, "version": version.version}


def list_country_versions(code: str, current_user: dict, db: Session, config_type: str | None = None) -> list[dict[str, Any]]:
    _require_admin(current_user)
    _require_country_access(code, current_user)
    normalized_code = normalize_country_code(code)
    query = db.query(CountryConfigVersion).filter(CountryConfigVersion.country_code == normalized_code)
    if config_type:
        query = query.filter(CountryConfigVersion.config_type == config_type)
    rows = query.order_by(CountryConfigVersion.created_at.desc(), CountryConfigVersion.version.desc()).all()
    return [
        {
            "id": row.id,
            "country_code": row.country_code,
            "config_type": row.config_type,
            "version": row.version,
            "status": row.status,
            "draft_by": row.draft_by,
            "approved_by": row.approved_by,
            "published_at": row.published_at,
            "effective_from": row.effective_from,
            "created_at": row.created_at,
            "payload": _from_json(row.payload_json, default={}),
        }
        for row in rows
    ]


def approve_country_version(code: str, version_id: int, current_user: dict, db: Session) -> dict[str, Any]:
    _require_admin(current_user)
    _require_country_access(code, current_user)
    normalized_code = normalize_country_code(code)
    row = (
        db.query(CountryConfigVersion)
        .filter(CountryConfigVersion.id == version_id, CountryConfigVersion.country_code == normalized_code)
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="Config version not found")

    if row.status != "draft":
        raise HTTPException(status_code=409, detail="Only draft versions can be approved")

    row.status = "approved"
    row.approved_by = current_user.get("id")
    _record_admin_change(
        db,
        actor_id=current_user.get("id"),
        action="approve",
        entity="country_config_version",
        entity_key=f"{row.country_code}:{row.config_type}:v{row.version}",
        before={"status": "draft"},
        after={"status": "approved"},
    )
    commit_country_changes(db)
    return {"message": "Version approved", "version_id": row.id, "status": row.status}


def _apply_version_payload(row: CountryConfigVersion, db: Session) -> None:
    country = _get_country_or_404(row.country_code, db)
    payload = _from_json(row.payload_json, default={})

    if row.config_type == "tax":
        country.tax_type = str(payload.get("tax_type") or country.tax_type).upper()
        country.tax_rate = _to_decimal(payload.get("tax_rate", country.tax_rate), field="tax_rate")
        country.tax_name = str(payload.get("tax_name") or country.tax_name)
        country.tax_inclusive = bool(payload.get("tax_inclusive", country.tax_inclusive))
        country.tax_exempt_categories_json = _to_json(payload.get("tax_exempt_categories", []))
        country.tax_reduced_rates_json = _to_json(payload.get("tax_reduced_rates", {}))
    elif row.config_type == "logistics":
        country.logistics_model = str(payload.get("logistics_model") or country.logistics_model).lower()
        country.default_vehicle_type = payload.get("default_vehicle_type")
        country.base_rate = _to_decimal(payload["base_rate"], field="base_rate") if payload.get("base_rate") is not None else None
        country.per_km_rate = _to_decimal(payload["per_km_rate"], field="per_km_rate") if payload.get("per_km_rate") is not None else None
        country.minimum_charge = _to_decimal(payload["minimum_charge"], field="minimum_charge") if payload.get("minimum_charge") is not None else None
        country.weight_surcharge_rate = _to_decimal(payload["weight_surcharge_rate"], field="weight_surcharge_rate") if payload.get("weight_surcharge_rate") is not None else None
        country.weight_surcharge_threshold_kg = (
            _to_decimal(payload["weight_surcharge_threshold_kg"], field="weight_surcharge_threshold_kg")
            if payload.get("weight_surcharge_threshold_kg") is not None
            else None
        )
        zones = payload.get("delivery_zones")
        if zones is None:
            zones = payload.get("oman_zones")
        if isinstance(zones, list) and country.logistics_model == "zone":
            existing = {zone.zone_code: zone for zone in db.query(OmanDeliveryZone).all()}
            for zone_payload in zones:
                if not isinstance(zone_payload, dict):
                    continue
                zone_code = str(zone_payload.get("zone_code") or "").strip().upper()
                if not zone_code:
                    continue
                zone = existing.get(zone_code) or OmanDeliveryZone(zone_code=zone_code, zone_name=zone_code)
                zone.zone_name = str(zone_payload.get("zone_name") or zone.zone_name)
                zone.description = str(zone_payload.get("description") or "").strip() or None
                zone.car_rate = _to_decimal(zone_payload.get("car_rate", zone.car_rate), field=f"{zone_code}.car_rate")
                zone.van_rate = _to_decimal(zone_payload.get("van_rate", zone.van_rate), field=f"{zone_code}.van_rate")
                zone.truck_rate = _to_decimal(zone_payload.get("truck_rate", zone.truck_rate), field=f"{zone_code}.truck_rate")
                zone.weight_surcharge_rate = _to_decimal(zone_payload.get("weight_surcharge_rate", zone.weight_surcharge_rate), field=f"{zone_code}.weight_surcharge_rate") if zone_payload.get("weight_surcharge_rate") is not None else None
                zone.weight_surcharge_threshold_kg = _to_decimal(zone_payload.get("weight_surcharge_threshold_kg", zone.weight_surcharge_threshold_kg), field=f"{zone_code}.weight_surcharge_threshold_kg") if zone_payload.get("weight_surcharge_threshold_kg") is not None else None
                zone.cities_json = _to_json(zone_payload.get("cities", []))
                zone.is_active = bool(zone_payload.get("is_active", True))
                zone.sort_order = int(zone_payload.get("sort_order", 0) or 0)
                if zone.id is None:
                    add_oman_delivery_zone(db, zone)
    elif row.config_type == "commission":
        rates = payload.get("rates") or []
        if isinstance(rates, list):
            existing_rows = {
                (entry.country_code, entry.category_slug): entry
                for entry in db.query(SupplierCountryCommission)
                .filter(SupplierCountryCommission.country_code == row.country_code)
                .all()
            }
            for item in rates:
                if not isinstance(item, dict):
                    continue
                slug = str(item.get("category_slug") or "").strip().lower()
                if not slug:
                    continue
                key = (row.country_code, slug)
                entry = existing_rows.get(key)
                if entry is None:
                    entry = SupplierCountryCommission(country_code=row.country_code, category_slug=slug)
                    add_supplier_commission(db, entry)
                entry.commission_rate = _to_decimal(item.get("commission_rate", entry.commission_rate or 0), field=f"commission_rate[{slug}]")
                entry.notes = str(item.get("notes") or "").strip() or None
                entry.is_active = bool(item.get("is_active", True))
    elif row.config_type == "ops":
        payment_methods = payload.get("payment_methods", [])
        country.payment_methods_json = _to_json(payment_methods if isinstance(payment_methods, list) else [])

        feature_flags = payload.get("feature_flags", {})
        if isinstance(feature_flags, dict):
            existing_flags = {
                flag.feature_key: flag
                for flag in db.query(CountryFeatureFlag)
                .filter(CountryFeatureFlag.country_code == row.country_code)
                .all()
            }
            for feature_key, value in feature_flags.items():
                key = str(feature_key).strip()
                if not key:
                    continue
                flag = existing_flags.get(key)
                if flag is None:
                    flag = CountryFeatureFlag(country_code=row.country_code, feature_key=key)
                    add_feature_flag(db, flag)
                if isinstance(value, dict):
                    flag.is_enabled = bool(value.get("is_enabled", False))
                    flag.rollout_audience = str(value.get("rollout_audience") or "").strip() or None
                    flag.notes = str(value.get("notes") or "").strip() or None
                else:
                    flag.is_enabled = bool(value)
                flag.updated_at = _utcnow()
    elif row.config_type == "payment_gateways":
        gateways = payload.get("gateways") if isinstance(payload, dict) else payload
        if isinstance(gateways, list):
            country.payment_gateways_json = _to_json(gateways)
        elif isinstance(payload, list):
            country.payment_gateways_json = _to_json(payload)
    elif row.config_type == "logistics_providers":
        providers = payload.get("providers") if isinstance(payload, dict) else payload
        if isinstance(providers, list):
            country.logistics_providers_json = _to_json(providers)
        elif isinstance(payload, list):
            country.logistics_providers_json = _to_json(payload)
    elif row.config_type == "legal_rules":
        if isinstance(payload, dict):
            country.legal_rules_json = _to_json(payload)
    elif row.config_type == "regions":
        regions = payload.get("regions") if isinstance(payload, dict) else payload
        if isinstance(regions, list):
            country.regions_json = _to_json(regions)
        elif isinstance(payload, list):
            country.regions_json = _to_json(payload)
    elif row.config_type == "supplier_requirements":
        if isinstance(payload, dict):
            country.supplier_requirements_json = _to_json(payload)
    elif row.config_type == "payout_settings":
        if isinstance(payload, dict):
            country.payout_settings_json = _to_json(payload)
    elif row.config_type == "commission_tiers":
        tiers = payload.get("tiers") if isinstance(payload, dict) else payload
        if isinstance(tiers, list):
            country.commission_tiers_json = _to_json(tiers)
        elif isinstance(payload, list):
            country.commission_tiers_json = _to_json(payload)
    elif row.config_type == "product_restrictions":
        restrictions = payload.get("restrictions") if isinstance(payload, dict) else payload
        if isinstance(restrictions, list):
            country.product_restrictions_json = _to_json(restrictions)
        elif isinstance(payload, list):
            country.product_restrictions_json = _to_json(payload)
    elif row.config_type == "address_format":
        if isinstance(payload, dict):
            fmt = payload.get("address_format", payload)
            if isinstance(fmt, dict):
                country.address_format_json = _to_json(fmt)
    elif row.config_type == "date_format":
        if isinstance(payload, dict):
            fmt = str(payload.get("date_format", country.date_format) or "DD/MM/YYYY").strip()
            country.date_format = fmt

    country.updated_at = _utcnow()



def publish_country_version(code: str, version_id: int, current_user: dict, db: Session) -> dict[str, Any]:
    _require_admin(current_user)
    _require_country_access(code, current_user)
    normalized_code = normalize_country_code(code)
    row = (
        db.query(CountryConfigVersion)
        .filter(CountryConfigVersion.id == version_id, CountryConfigVersion.country_code == normalized_code)
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="Config version not found")

    if row.status not in {"approved", "draft"}:
        raise HTTPException(status_code=409, detail="Version cannot be published")

    _apply_version_payload(row, db)
    row.status = "published"
    row.approved_by = row.approved_by or current_user.get("id")
    row.published_at = _utcnow()
    _record_admin_change(
        db,
        actor_id=current_user.get("id"),
        action="publish",
        entity="country_config_version",
        entity_key=f"{row.country_code}:{row.config_type}:v{row.version}",
        before={"status": "approved" if row.approved_by else "draft"},
        after={"status": "published"},
    )
    commit_country_changes(db)
    return {"message": "Version published", "version_id": row.id, "status": row.status, "published_at": row.published_at}


def rollback_country_to_version(code: str, version_id: int, current_user: dict, db: Session) -> dict[str, Any]:
    _require_admin(current_user)
    _require_country_access(code, current_user)
    normalized_code = normalize_country_code(code)
    row = (
        db.query(CountryConfigVersion)
        .filter(
            CountryConfigVersion.id == version_id,
            CountryConfigVersion.country_code == normalized_code,
            CountryConfigVersion.status == "published",
        )
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="Published version not found")

    _apply_version_payload(row, db)
    rollback_row = CountryConfigVersion(
        country_code=row.country_code,
        config_type=row.config_type,
        version=_next_version(db, row.country_code, row.config_type),
        payload_json=row.payload_json,
        status="rolled_back",
        draft_by=current_user.get("id"),
        approved_by=current_user.get("id"),
        published_at=_utcnow(),
        created_at=_utcnow(),
    )
    add_to_session(db, rollback_row)
    _record_admin_change(
        db,
        actor_id=current_user.get("id"),
        action="rollback",
        entity="country_config_version",
        entity_key=f"{row.country_code}:{row.config_type}:v{row.version}",
        before=None,
        after={"rollback_to_version": row.version},
    )
    commit_country_changes(db)
    return {
        "message": "Rollback applied",
        "rolled_back_to": row.version,
        "new_version": rollback_row.version,
        "status": rollback_row.status,
    }


def list_country_commissions(code: str, current_user: dict, db: Session) -> list[dict[str, Any]]:
    _require_admin(current_user)
    _require_country_access(code, current_user)
    normalized_code = normalize_country_code(code)
    rows = (
        db.query(SupplierCountryCommission)
        .filter(SupplierCountryCommission.country_code == normalized_code)
        .order_by(SupplierCountryCommission.category_slug.asc())
        .all()
    )
    return [
        {
            "id": row.id,
            "country_code": row.country_code,
            "category_slug": row.category_slug,
            "commission_rate": float(row.commission_rate),
            "notes": row.notes,
            "is_active": bool(row.is_active),
            "updated_at": row.updated_at,
        }
        for row in rows
    ]


def preview_country_tax(code: str, payload: dict[str, Any], current_user: dict, db: Session) -> dict[str, Any]:
    _require_admin(current_user)
    _require_country_access(code, current_user)
    amount = _to_decimal(payload.get("amount", "0"), field="amount")
    category = str(payload.get("category") or "").strip() or None
    inclusive = payload.get("inclusive")
    if inclusive is not None:
        inclusive = bool(inclusive)

    result = calculate_tax(amount, code, db, category=category, inclusive=inclusive)
    result["tax_rate"] = float(result["tax_rate"])
    result["tax_amount"] = float(result["tax_amount"])
    result["net_amount"] = float(result["net_amount"])
    result["total_amount"] = float(result["total_amount"])
    return result


def get_country_feature_flags(code: str, current_user: dict, db: Session) -> list[dict[str, Any]]:
    _require_admin(current_user)
    _require_country_access(code, current_user)
    normalized_code = normalize_country_code(code)
    rows = (
        db.query(CountryFeatureFlag)
        .filter(CountryFeatureFlag.country_code == normalized_code)
        .order_by(CountryFeatureFlag.feature_key.asc())
        .all()
    )
    return [
        {
            "id": row.id,
            "country_code": row.country_code,
            "feature_key": row.feature_key,
            "is_enabled": bool(row.is_enabled),
            "rollout_audience": row.rollout_audience,
            "notes": row.notes,
            "updated_at": row.updated_at,
        }
        for row in rows
    ]


def list_country_delivery_zones(code: str, current_user: dict, db: Session) -> list[dict[str, Any]]:
    _require_admin(current_user)
    _require_country_access(code, current_user)
    country = _get_country_or_404(code, db)
    if str(country.logistics_model or "").lower() != "zone":
        return []

    rows = db.query(OmanDeliveryZone).order_by(OmanDeliveryZone.sort_order.asc(), OmanDeliveryZone.zone_code.asc()).all()
    return [
        {
            "zone_code": row.zone_code,
            "zone_name": row.zone_name,
            "description": row.description,
            "car_rate": float(row.car_rate),
            "van_rate": float(row.van_rate),
            "truck_rate": float(row.truck_rate),
            "weight_surcharge_rate": float(row.weight_surcharge_rate) if row.weight_surcharge_rate is not None else None,
            "weight_surcharge_threshold_kg": float(row.weight_surcharge_threshold_kg) if row.weight_surcharge_threshold_kg is not None else None,
            "cities": _from_json(row.cities_json, default=[]),
            "is_active": bool(row.is_active),
            "sort_order": row.sort_order,
        }
        for row in rows
    ]


# Ã¢â€�â‚¬Ã¢â€�â‚¬ New GCC Config Sections Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬

def update_country_identity(code: str, payload: dict[str, Any], current_user: dict, db: Session) -> dict[str, Any]:
    """Update non-versioned identity fields (name, currency_symbol, phone_code, language, is_active)."""
    _require_admin(current_user)
    _require_country_access(code, current_user)
    country = _get_country_or_404(code, db)
    before = _country_public_payload(country, db)

    if "name" in payload and payload["name"]:
        country.name = str(payload["name"]).strip()
    if "currency_symbol" in payload:
        country.currency_symbol = str(payload["currency_symbol"] or "").strip() or None
    if "phone_code" in payload:
        country.phone_code = str(payload["phone_code"] or "").strip() or None
    if "language" in payload:
        country.language = str(payload["language"] or "en").strip().lower() or "en"
    if "date_format" in payload:
        country.date_format = str(payload["date_format"] or "DD/MM/YYYY").strip()
    if "is_active" in payload:
        country.is_active = bool(payload["is_active"])
    # Ã¢â€�â‚¬Ã¢â€�â‚¬ Phase 1 identity fields Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬
    if "official_name" in payload:
        country.official_name = str(payload["official_name"] or "").strip() or None
    if "alpha3" in payload:
        country.alpha3 = str(payload["alpha3"] or "").strip().upper() or None
    if "flag_url" in payload:
        country.flag_url = str(payload["flag_url"] or "").strip() or None
    if "currency_name" in payload:
        country.currency_name = str(payload["currency_name"] or "").strip() or None
    if "exchange_rate_to_usd" in payload:
        country.exchange_rate_to_usd = payload["exchange_rate_to_usd"]
    # Ã¢â€�â‚¬Ã¢â€�â‚¬ Phase 1 COD fields Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬
    if "cod_enabled" in payload:
        country.cod_enabled = bool(payload["cod_enabled"])
    if "cod_max_amount" in payload:
        country.cod_max_amount = payload["cod_max_amount"]
    if "cod_verification_required" in payload:
        country.cod_verification_required = bool(payload["cod_verification_required"])
    if "cod_remittance_days" in payload:
        country.cod_remittance_days = int(payload["cod_remittance_days"])
    if "settlement_hold_days" in payload:
        country.settlement_hold_days = int(payload["settlement_hold_days"])
    if "minimum_payout_amount" in payload:
        country.minimum_payout_amount = payload["minimum_payout_amount"]
    if "payout_currency" in payload:
        country.payout_currency = str(payload["payout_currency"] or "").strip().upper() or None
    # Ã¢â€�â‚¬Ã¢â€�â‚¬ Phase 1 locale Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬
    if "measurement_system" in payload:
        country.measurement_system = str(payload["measurement_system"] or "metric").strip().lower()
    if "working_days" in payload:
        country.working_days_json = _to_json(payload["working_days"])
    if "data_privacy_framework" in payload:
        country.data_privacy_framework = str(payload["data_privacy_framework"] or "").strip() or None
    # Ã¢â€�â‚¬Ã¢â€�â‚¬ Phase 1 supplier Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬
    if "supplier_kyc_tier" in payload:
        country.supplier_kyc_tier = str(payload["supplier_kyc_tier"] or "").strip() or None
    if "supplier_onboarding_fee" in payload:
        country.supplier_onboarding_fee = payload["supplier_onboarding_fee"]
    if "supplier_monthly_fee" in payload:
        country.supplier_monthly_fee = payload["supplier_monthly_fee"]
    if "supplier_rating_threshold" in payload:
        country.supplier_rating_threshold = payload["supplier_rating_threshold"]
    # Ã¢â€�â‚¬Ã¢â€�â‚¬ Phase 1 legal / consumer Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬
    if "legal_entity_required" in payload:
        country.legal_entity_required = bool(payload["legal_entity_required"])
    if "consumer_protection_days" in payload:
        country.consumer_protection_days = int(payload["consumer_protection_days"])
    # Ã¢â€�â‚¬Ã¢â€�â‚¬ Phase 1 logistics expansion Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬
    if "max_package_weight_kg" in payload:
        country.max_package_weight_kg = payload["max_package_weight_kg"]
    if "max_package_dimensions_cm" in payload:
        country.max_package_dimensions_cm = str(payload["max_package_dimensions_cm"] or "").strip() or None
    if "signature_required_threshold" in payload:
        country.signature_required_threshold = payload["signature_required_threshold"]
    # Ã¢â€�â‚¬Ã¢â€�â‚¬ Phase 1 heuristic fields Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬
    if "economic_tier" in payload:
        country.economic_tier = str(payload["economic_tier"] or "").strip() or None
    if "fraud_risk_tier" in payload:
        country.fraud_risk_tier = str(payload["fraud_risk_tier"] or "").strip() or None
    if "suggested_logistics_model" in payload:
        country.suggested_logistics_model = str(payload["suggested_logistics_model"] or "").strip() or None

    country.updated_at = _utcnow()
    _record_admin_change(
        db,
        actor_id=current_user.get("id"),
        action="update",
        entity="country_identity",
        entity_key=country.code,
        before=before,
        after=_country_public_payload(country, db),
    )
    commit_and_refresh_obj(db, country)
    return _country_public_payload(country, db)


def create_payment_gateways_draft(code: str, payload: dict[str, Any], current_user: dict, db: Session) -> dict[str, Any]:
    _require_admin(current_user)
    _require_country_access(code, current_user)
    country = _get_country_or_404(code, db)
    gateways = payload.get("gateways") if isinstance(payload, dict) else payload
    if not isinstance(gateways, list):
        raise HTTPException(status_code=422, detail="gateways must be a list")

    normalized: list[dict[str, Any]] = []
    for gw in gateways:
        if not isinstance(gw, dict):
            continue
        normalized.append({
            "gateway_id": str(gw.get("gateway_id") or "").strip().lower(),
            "name": str(gw.get("name") or "").strip(),
            "type": str(gw.get("type") or "card").strip().lower(),
            "enabled": bool(gw.get("enabled", True)),
            "credential_ref": str(gw.get("credential_ref") or "").strip() or None,
            "supports_cod": bool(gw.get("supports_cod", False)),
            "supports_installments": bool(gw.get("supports_installments", False)),
            "fee_percentage": float(gw.get("fee_percentage") or 0),
            "fee_fixed": float(gw.get("fee_fixed") or 0),
        })

    draft_payload = {"gateways": normalized}
    version = _create_draft_version(db, country_code=country.code, config_type="payment_gateways", payload=draft_payload, actor_id=current_user.get("id"))
    _record_admin_change(db, actor_id=current_user.get("id"), action="create_draft", entity="country_payment_gateways", entity_key=f"{country.code}:v{version.version}", before=None, after=draft_payload)
    commit_country_changes(db)
    return {"message": "Payment gateways draft created", "version_id": version.id, "version": version.version}


def get_payment_gateways(code: str, current_user: dict, db: Session) -> list[dict[str, Any]]:
    _require_admin(current_user)
    _require_country_access(code, current_user)
    country = _get_country_or_404(code, db)
    return _from_json(country.payment_gateways_json, default=[])


def create_logistics_providers_draft(code: str, payload: dict[str, Any], current_user: dict, db: Session) -> dict[str, Any]:
    _require_admin(current_user)
    _require_country_access(code, current_user)
    country = _get_country_or_404(code, db)
    providers = payload.get("providers") if isinstance(payload, dict) else payload
    if not isinstance(providers, list):
        raise HTTPException(status_code=422, detail="providers must be a list")

    normalized: list[dict[str, Any]] = []
    for prov in providers:
        if not isinstance(prov, dict):
            continue
        normalized.append({
            "provider_id": str(prov.get("provider_id") or "").strip().lower(),
            "name": str(prov.get("name") or "").strip(),
            "enabled": bool(prov.get("enabled", True)),
            "service_areas": prov.get("service_areas") if isinstance(prov.get("service_areas"), list) else ["all_regions"],
            "sla_standard_days": str(prov.get("sla_standard_days") or "3-5").strip(),
            "sla_express_days": str(prov.get("sla_express_days") or "1-2").strip(),
            "base_rate": float(prov.get("base_rate") or 0),
            "per_kg_rate": float(prov.get("per_kg_rate") or 0),
            "currency": str(prov.get("currency") or "").strip().upper() or None,
        })

    draft_payload = {"providers": normalized}
    version = _create_draft_version(db, country_code=country.code, config_type="logistics_providers", payload=draft_payload, actor_id=current_user.get("id"))
    _record_admin_change(db, actor_id=current_user.get("id"), action="create_draft", entity="country_logistics_providers", entity_key=f"{country.code}:v{version.version}", before=None, after=draft_payload)
    commit_country_changes(db)
    return {"message": "Logistics providers draft created", "version_id": version.id, "version": version.version}


def get_logistics_providers(code: str, current_user: dict, db: Session) -> list[dict[str, Any]]:
    _require_admin(current_user)
    _require_country_access(code, current_user)
    country = _get_country_or_404(code, db)
    return _from_json(country.logistics_providers_json, default=[])


def create_legal_rules_draft(code: str, payload: dict[str, Any], current_user: dict, db: Session) -> dict[str, Any]:
    _require_admin(current_user)
    _require_country_access(code, current_user)
    country = _get_country_or_404(code, db)
    existing = _from_json(country.legal_rules_json, default={})

    draft_payload: dict[str, Any] = {
        "minimum_order_age": int(payload.get("minimum_order_age", existing.get("minimum_order_age", 18)) or 18),
        "max_returns_allowed": int(payload.get("max_returns_allowed", existing.get("max_returns_allowed", 3)) or 3),
        "return_window_days": int(payload.get("return_window_days", existing.get("return_window_days", 14)) or 14),
        "refund_processing_days": int(payload.get("refund_processing_days", existing.get("refund_processing_days", 7)) or 7),
        "requires_commercial_license": bool(payload.get("requires_commercial_license", existing.get("requires_commercial_license", False))),
        "requires_vat_registration": bool(payload.get("requires_vat_registration", existing.get("requires_vat_registration", False))),
        "product_restrictions": payload.get("product_restrictions", existing.get("product_restrictions", [])) if isinstance(payload.get("product_restrictions", existing.get("product_restrictions", [])), list) else [],
    }

    version = _create_draft_version(db, country_code=country.code, config_type="legal_rules", payload=draft_payload, actor_id=current_user.get("id"))
    _record_admin_change(db, actor_id=current_user.get("id"), action="create_draft", entity="country_legal_rules", entity_key=f"{country.code}:v{version.version}", before=existing, after=draft_payload)
    commit_country_changes(db)
    return {"message": "Legal rules draft created", "version_id": version.id, "version": version.version}


def get_legal_rules(code: str, current_user: dict, db: Session) -> dict[str, Any]:
    _require_admin(current_user)
    _require_country_access(code, current_user)
    country = _get_country_or_404(code, db)
    return _from_json(country.legal_rules_json, default={})


def create_regions_draft(code: str, payload: dict[str, Any], current_user: dict, db: Session) -> dict[str, Any]:
    _require_admin(current_user)
    _require_country_access(code, current_user)
    country = _get_country_or_404(code, db)
    regions = payload.get("regions") if isinstance(payload, dict) else payload
    if not isinstance(regions, list):
        raise HTTPException(status_code=422, detail="regions must be a list")

    normalized: list[dict[str, Any]] = []
    for region in regions:
        if not isinstance(region, dict):
            continue
        region_id = str(region.get("region_id") or region.get("name") or "").strip().lower().replace(" ", "_")
        cities = region.get("cities") if isinstance(region.get("cities"), list) else []
        normalized.append({
            "region_id": region_id,
            "name": str(region.get("name") or region_id).strip(),
            "cities": [str(c).strip() for c in cities if str(c).strip()],
        })

    draft_payload = {"regions": normalized}
    version = _create_draft_version(db, country_code=country.code, config_type="regions", payload=draft_payload, actor_id=current_user.get("id"))
    _record_admin_change(db, actor_id=current_user.get("id"), action="create_draft", entity="country_regions", entity_key=f"{country.code}:v{version.version}", before=None, after=draft_payload)
    commit_country_changes(db)
    return {"message": "Regions draft created", "version_id": version.id, "version": version.version}


def get_regions(code: str, current_user: dict, db: Session) -> list[dict[str, Any]]:
    _require_admin(current_user)
    _require_country_access(code, current_user)
    country = _get_country_or_404(code, db)
    return _from_json(country.regions_json, default=[])


def create_supplier_requirements_draft(code: str, payload: dict[str, Any], current_user: dict, db: Session) -> dict[str, Any]:
    _require_admin(current_user)
    _require_country_access(code, current_user)
    country = _get_country_or_404(code, db)
    existing = _from_json(country.supplier_requirements_json, default={})

    required_docs = payload.get("required_documents", existing.get("required_documents", []))
    draft_payload: dict[str, Any] = {
        "kyc_level": str(payload.get("kyc_level", existing.get("kyc_level", "standard")) or "standard").strip().lower(),
        "required_documents": required_docs if isinstance(required_docs, list) else [],
        "approval_required": bool(payload.get("approval_required", existing.get("approval_required", True))),
    }

    version = _create_draft_version(db, country_code=country.code, config_type="supplier_requirements", payload=draft_payload, actor_id=current_user.get("id"))
    _record_admin_change(db, actor_id=current_user.get("id"), action="create_draft", entity="country_supplier_requirements", entity_key=f"{country.code}:v{version.version}", before=existing, after=draft_payload)
    commit_country_changes(db)
    return {"message": "Supplier requirements draft created", "version_id": version.id, "version": version.version}


def get_supplier_requirements(code: str, current_user: dict, db: Session) -> dict[str, Any]:
    _require_admin(current_user)
    _require_country_access(code, current_user)
    country = _get_country_or_404(code, db)
    return _from_json(country.supplier_requirements_json, default={})


def create_payout_settings_draft(code: str, payload: dict[str, Any], current_user: dict, db: Session) -> dict[str, Any]:
    _require_admin(current_user)
    _require_country_access(code, current_user)
    country = _get_country_or_404(code, db)
    existing = _from_json(country.payout_settings_json, default={})

    draft_payload: dict[str, Any] = {
        "minimum_payout_amount": float(payload.get("minimum_payout_amount", existing.get("minimum_payout_amount", 10)) or 10),
        "payout_schedule": str(payload.get("payout_schedule", existing.get("payout_schedule", "weekly")) or "weekly").strip().lower(),
        "payout_day": str(payload.get("payout_day", existing.get("payout_day", "sunday")) or "sunday").strip().lower(),
        "batch_size": int(payload.get("batch_size", existing.get("batch_size", 50)) or 50),
        "currency": str(payload.get("currency", existing.get("currency", "")) or "").strip().upper() or None,
    }

    version = _create_draft_version(db, country_code=country.code, config_type="payout_settings", payload=draft_payload, actor_id=current_user.get("id"))
    _record_admin_change(db, actor_id=current_user.get("id"), action="create_draft", entity="country_payout_settings", entity_key=f"{country.code}:v{version.version}", before=existing, after=draft_payload)
    commit_country_changes(db)
    return {"message": "Payout settings draft created", "version_id": version.id, "version": version.version}


def get_payout_settings(code: str, current_user: dict, db: Session) -> dict[str, Any]:
    _require_admin(current_user)
    _require_country_access(code, current_user)
    country = _get_country_or_404(code, db)
    return _from_json(country.payout_settings_json, default={})


def create_commission_tiers_draft(code: str, payload: dict[str, Any], current_user: dict, db: Session) -> dict[str, Any]:
    _require_admin(current_user)
    _require_country_access(code, current_user)
    country = _get_country_or_404(code, db)
    tiers = payload.get("tiers") if isinstance(payload, dict) else payload
    if not isinstance(tiers, list):
        raise HTTPException(status_code=422, detail="tiers must be a list")

    normalized: list[dict[str, Any]] = []
    for tier in tiers:
        if not isinstance(tier, dict):
            continue
        normalized.append({
            "min_order_value": float(tier.get("min_order_value") or 0),
            "max_order_value": float(tier.get("max_order_value") or 0) if tier.get("max_order_value") is not None else None,
            "commission_percentage": float(tier.get("commission_percentage") or 0),
            "fixed_fee": float(tier.get("fixed_fee") or 0),
        })

    draft_payload = {"tiers": normalized}
    version = _create_draft_version(db, country_code=country.code, config_type="commission_tiers", payload=draft_payload, actor_id=current_user.get("id"))
    _record_admin_change(db, actor_id=current_user.get("id"), action="create_draft", entity="country_commission_tiers", entity_key=f"{country.code}:v{version.version}", before=None, after=draft_payload)
    commit_country_changes(db)
    return {"message": "Commission tiers draft created", "version_id": version.id, "version": version.version}


def get_commission_tiers(code: str, current_user: dict, db: Session) -> list[dict[str, Any]]:
    _require_admin(current_user)
    _require_country_access(code, current_user)
    country = _get_country_or_404(code, db)
    return _from_json(country.commission_tiers_json, default=[])


def test_gateway_connection(code: str, gateway_id: str, environment: str, current_user: dict, db: Session) -> dict[str, Any]:
    _require_admin(current_user)
    _require_country_access(code, current_user)
    from services.payment_engine import PaymentEngine

    engine = PaymentEngine(db)
    result = engine.test_gateway_connection(country_code=code, gateway_id=gateway_id, environment=environment)
    return {
        "success": result.success,
        "message": result.message,
        "latency_ms": result.latency_ms,
        "country_code": code,
        "gateway_id": gateway_id,
        "environment": environment,
    }


def list_country_cities(
    code: str,
    current_user: dict,
    db: Session,
    *,
    query: str | None = None,
    limit: int = 50,
    include_inactive: bool = False,
) -> dict[str, Any]:
    """Return known cities for a country code from the normalized CountryCity table.

    Supports search query (`q` param), pagination (`limit`), and optional include_inactive.
    Returns objects: {id, name, region, latitude, longitude, population, is_active}.
    Falls back to CITY_SUGGESTIONS + open-meteo if the table is empty (seeding path).
    """
    _require_admin(current_user)
    _require_country_access(code, current_user)

    cc = code.upper()

    # 1. Try the normalized CountryCity table first
    q = db.query(CountryCity).filter(CountryCity.country_code == cc)
    if not include_inactive:
        q = q.filter(CountryCity.is_active == True)
    if query:
        like = f"%{query.strip()}%"
        q = q.filter(CountryCity.name.ilike(like))
    q = q.order_by(CountryCity.population.desc().nullslast(), CountryCity.name.asc())
    q = q.limit(limit)

    db_cities = q.all()
    if db_cities:
        return {
            "code": cc,
            "cities": [
                {
                    "id": c.id,
                    "name": c.name,
                    "region": c.region or "",
                    "latitude": float(c.latitude) if c.latitude is not None else None,
                    "longitude": float(c.longitude) if c.longitude is not None else None,
                    "population": c.population,
                    "is_active": bool(c.is_active),
                }
                for c in db_cities
            ],
            "source": "database",
        }

    # 2. Fallback: CITY_SUGGESTIONS + open-meteo (for seeding new countries)
    from data.vat_rates import CITY_SUGGESTIONS

    cities = list(CITY_SUGGESTIONS.get(cc, []))
    if not cities:
        import httpx
        try:
            resp = httpx.get(
                "https://geocoding-api.open-meteo.com/v1/search",
                params={"name": code, "count": min(limit, 50), "language": "en", "format": "json"},
                timeout=8.0,
            )
            if resp.is_success:
                results = resp.json().get("results", [])
                seen: set[str] = set()
                for r in results:
                    name = (r.get("name") or "").strip()
                    country = (r.get("country_code") or "").strip().upper()
                    if name and country == cc and name not in seen:
                        cities.append({
                            "name": name,
                            "region": r.get("admin1") or "",
                            "latitude": r.get("latitude"),
                            "longitude": r.get("longitude"),
                            "population": r.get("population") or 0,
                        })
                        seen.add(name)
        except Exception:
            pass

    return {"code": cc, "cities": cities, "source": "fallback"}


# Ã¢â€�â‚¬Ã¢â€�â‚¬ Staff Assignments Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬

def assign_staff_to_country(country_code: str, user_id: int, role_in_country: str, current_user: dict, db: Session) -> dict:
    _require_full_admin(current_user)
    from models import User
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    _get_country_or_404(country_code, db)
    existing = db.query(CountryStaffAssignment).filter(
        CountryStaffAssignment.user_id == user_id,
        CountryStaffAssignment.country_code == country_code.upper(),
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="Staff already assigned to this country")
    assignment = CountryStaffAssignment(
        user_id=user_id,
        country_code=country_code.upper(),
        role_in_country=role_in_country,
        assigned_by=current_user.get("id"),
    )
    add_to_session(db, assignment)
    _record_admin_change(db, actor_id=current_user.get("id"), action="assign_staff", entity="country_staff", entity_key=f"{country_code}:{user_id}", before=None, after={"user_id": user_id, "role": role_in_country})
    commit_and_refresh_obj(db, assignment)
    return {"id": assignment.id, "user_id": user_id, "country_code": country_code.upper(), "role_in_country": role_in_country}


def list_country_staff(country_code: str, current_user: dict, db: Session) -> list[dict]:
    _require_admin(current_user)
    _require_country_access(country_code, current_user)
    rows = db.query(CountryStaffAssignment).filter(
        CountryStaffAssignment.country_code == country_code.upper(),
        CountryStaffAssignment.is_active == True,
    ).order_by(CountryStaffAssignment.created_at.desc()).all()
    from models import User
    user_ids = [r.user_id for r in rows]
    users = {u.id: u for u in db.query(User).filter(User.id.in_(user_ids)).all()} if user_ids else {}
    return [
        {
            "id": r.id,
            "user_id": r.user_id,
            "country_code": r.country_code,
            "role_in_country": r.role_in_country,
            "user_name": users.get(r.user_id, {}).username if isinstance(users.get(r.user_id, {}), User) else getattr(users.get(r.user_id), "username", ""),
            "user_email": users.get(r.user_id, {}).email if isinstance(users.get(r.user_id, {}), User) else getattr(users.get(r.user_id), "email", ""),
            "is_active": r.is_active,
            "assigned_by": r.assigned_by,
            "created_at": r.created_at,
        }
        for r in rows
        if r.user_id in users
    ]


def unassign_staff_from_country(country_code: str, user_id: int, current_user: dict, db: Session) -> dict:
    _require_full_admin(current_user)
    a = db.query(CountryStaffAssignment).filter(
        CountryStaffAssignment.user_id == user_id,
        CountryStaffAssignment.country_code == country_code.upper(),
    ).first()
    if not a:
        raise HTTPException(status_code=404, detail="Assignment not found")
    a.is_active = False
    _record_admin_change(db, actor_id=current_user.get("id"), action="unassign_staff", entity="country_staff", entity_key=f"{country_code}:{a.user_id}", before={"active": True}, after={"active": False})
    commit_country_changes(db)
    return {"message": "Staff unassigned"}


# Ã¢â€�â‚¬Ã¢â€�â‚¬ Communications Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬

def send_country_communication(country_code: str, payload: dict, current_user: dict, db: Session) -> dict:
    _require_admin(current_user)
    _require_country_access(country_code, current_user)
    _get_country_or_404(country_code, db)
    comm = CountryCommunication(
        country_code=country_code.upper(),
        from_user_id=current_user.get("id"),
        to_user_id=payload.get("to_user_id"),
        subject=str(payload.get("subject", "")).strip(),
        body=str(payload.get("body", "")).strip(),
        priority=str(payload.get("priority", "normal")).lower(),
        category=str(payload.get("category", "")).strip() or None,
    )
    if not comm.subject or not comm.body:
        raise HTTPException(status_code=422, detail="Subject and body are required")
    comm = add_country_communication(db, comm)
    return {"id": comm.id, "status": comm.status, "created_at": comm.created_at}


def list_country_communications(country_code: str, current_user: dict, db: Session, category: str | None = None) -> list[dict]:
    _require_admin(current_user)
    _require_country_access(country_code, current_user)
    q = db.query(CountryCommunication).filter(CountryCommunication.country_code == country_code.upper())
    if category:
        q = q.filter(CountryCommunication.category == category)
    rows = q.order_by(CountryCommunication.created_at.desc()).limit(100).all()
    return [
        {
            "id": r.id,
            "from_user_id": r.from_user_id,
            "to_user_id": r.to_user_id,
            "subject": r.subject,
            "body": r.body,
            "priority": r.priority,
            "status": r.status,
            "category": r.category,
            "created_at": r.created_at,
            "read_at": r.read_at,
        }
        for r in rows
    ]


def mark_communication_read(comm_id: int, current_user: dict, db: Session) -> dict:
    _require_admin(current_user)
    comm = db.query(CountryCommunication).filter(CountryCommunication.id == comm_id).first()
    if not comm:
        raise HTTPException(status_code=404, detail="Communication not found")
    if comm.to_user_id and comm.to_user_id != current_user.get("id"):
        # Only the recipient (or admin) can mark as read
        role = str(current_user.get("role") or "").lower()
        if role != "admin":
            raise HTTPException(status_code=403, detail="Only recipient or admin can mark as read")
    ws_mark_communication_read(db, comm)
    return {"message": "Marked as read"}


# Ã¢â€�â‚¬Ã¢â€�â‚¬ Cross-Country Customer Sessions Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬

def list_cross_country_sessions(country_code: str, current_user: dict, db: Session) -> list[dict]:
    _require_admin(current_user)
    _require_country_access(country_code, current_user)
    q = db.query(CrossCountryCustomerSession).filter(
        CrossCountryCustomerSession.target_country_code == country_code.upper(),
    ).order_by(CrossCountryCustomerSession.created_at.desc()).limit(50).all()
    return [
        {
            "id": r.id,
            "user_id": r.user_id,
            "source_country_code": r.source_country_code,
            "target_country_code": r.target_country_code,
            "conversion": r.conversion,
            "order_id": r.order_id,
            "created_at": r.created_at,
        }
        for r in q
    ]


# Ã¢â€�â‚¬Ã¢â€�â‚¬ Auto-populate country data from external API Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬
# (delegated to services.country_auto_populate.auto_populate via auto_populate_async)


# Ã¢â€�â‚¬Ã¢â€�â‚¬ Product restriction checking (used by product & admin controllers) Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬

def is_product_restricted_for_country(
    category_slug: str,
    country_code: str | None,
    db: Session,
) -> bool:
    """Check if a product category is restricted in a given country."""
    if not country_code:
        return False
    from services.logistics_partner_pricing import normalize_country_code
    code = normalize_country_code(country_code)
    if not code:
        return False
    country = db.query(CountryConfig).filter(
        CountryConfig.code == code,
        CountryConfig.is_active == True,
    ).first()
    if not country:
        return False
    raw = country.product_restrictions_json
    if not raw:
        return False
    try:
        restricted = json.loads(raw) if isinstance(raw, str) else raw
    except (json.JSONDecodeError, TypeError):
        return False
    if not isinstance(restricted, list):
        return False
    slug = category_slug.strip().lower()
    return any(str(r).strip().lower() == slug for r in restricted)


# Ã¢â€�â‚¬Ã¢â€�â‚¬ Payout Rules Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬Ã¢â€�â‚¬

def list_payout_rules_categories(country_code: str, current_user: dict, db: Session) -> list[dict]:
    _require_admin(current_user)
    _require_country_access(country_code, current_user)
    normalized_code = normalize_country_code(country_code)
    country = db.query(CountryConfig).filter(CountryConfig.code == normalized_code).first()
    if not country:
        return []
    payout_rules_raw = _from_json(country.payout_settings_json, default=[])
    return payout_rules_raw if isinstance(payout_rules_raw, list) else []


def create_payout_rule_category(country_code: str, payload: dict, current_user: dict, db: Session) -> dict:
    _require_admin(current_user)
    _require_country_access(country_code, current_user)
    country = _get_country_or_404(country_code, db)
    rule_id = str(payload.get("rule_id") or payload.get("category_slug") or "")
    if not rule_id:
        raise HTTPException(status_code=422, detail="rule_id or category_slug is required")
    rule = {
        "rule_id": rule_id,
        "name": payload.get("name") or rule_id,
        "type": payload.get("type") or "category",
        "threshold_min": payload.get("threshold_min"),
        "threshold_max": payload.get("threshold_max"),
        "payout_rate": float(payload.get("payout_rate", 0)),
        "fixed_fee": float(payload.get("fixed_fee", 0)),
        "currency": payload.get("currency"),
    }
    existing = _from_json(country.payout_settings_json, default=[])
    if not isinstance(existing, list):
        existing = []
    existing = [r for r in existing if r.get("rule_id") != rule_id]
    existing.append(rule)
    country.payout_settings_json = _to_json(existing)
    country.updated_at = _utcnow()
    commit_country_changes(db)
    return {"message": "Payout rule created", "rule": rule}


def list_payout_rules_products(country_code: str, current_user: dict, db: Session) -> list[dict]:
    return list_payout_rules_categories(country_code, current_user, db)


def create_payout_rule_product(country_code: str, payload: dict, current_user: dict, db: Session) -> dict:
    payload_copy = payload.copy()
    payload_copy["type"] = "product"
    return create_payout_rule_category(country_code, payload_copy, current_user, db)


def delete_payout_rule(country_code: str, rule_id: str, current_user: dict, db: Session) -> dict:
    _require_admin(current_user)
    _require_country_access(country_code, current_user)
    country = _get_country_or_404(country_code, db)
    existing = _from_json(country.payout_settings_json, default=[])
    if not isinstance(existing, list):
        existing = []
    remaining = [r for r in existing if str(r.get("rule_id")) != str(rule_id)]
    if len(remaining) == len(existing):
        raise HTTPException(status_code=404, detail="Payout rule not found")
    country.payout_settings_json = _to_json(remaining)
    country.updated_at = _utcnow()
    commit_country_changes(db)
    return {"message": "Payout rule deleted", "rule_id": rule_id}

def update_country_cities_bulk(code: str, payload: dict, current_user: dict, db):
    _require_admin(current_user)
    _require_country_access(code, current_user)
    country = _get_country_or_404(code, db)
    cc = country.code
    cities_data = payload.get('cities')
    if not isinstance(cities_data, list):
        raise HTTPException(status_code=422, detail='cities must be a list')
    cities_to_save = []
    for idx, city_data in enumerate(cities_data):
        if not isinstance(city_data, dict):
            continue
        cities_to_save.append(CountryCity(
            country_code=cc,
            name=str(city_data.get('name', '')).strip(),
            region=str(city_data.get('region', '')).strip() or None,
            latitude=float(city_data['latitude']) if city_data.get('latitude') is not None else None,
            longitude=float(city_data['longitude']) if city_data.get('longitude') is not None else None,
            population=int(city_data['population']) if city_data.get('population') is not None else None,
            is_active=bool(city_data.get('is_active', True)),
            sort_order=int(city_data.get('sort_order', idx)),
            source=str(city_data.get('source', 'bulk_update')),
        ))
    bulk_replace_country_cities(db, cc, cities_to_save)
    all_cities = db.query(CountryCity).filter(CountryCity.country_code == cc).order_by(CountryCity.sort_order.asc(), CountryCity.name.asc()).all()
    return {
        'code': cc,
        'updated_count': len(all_cities),
        'cities': [{'id': c.id, 'name': c.name, 'region': c.region or '', 'latitude': float(c.latitude) if c.latitude is not None else None, 'longitude': float(c.longitude) if c.longitude is not None else None, 'population': c.population, 'is_active': bool(c.is_active), 'sort_order': c.sort_order} for c in all_cities],
    }

