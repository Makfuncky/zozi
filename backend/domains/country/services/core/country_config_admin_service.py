"""Service layer for the inline country-configuration database operations that lived
in ``routers/public_geography_configuration.py`` and ``routers/admin_geography_configuration.py``.

These two routers were (except for their URL prefix) identical copies or the same
country CRUD surrace. Their inline ``db.query/add/commit/delete`` blocks are moved
here so the routers become thin HTTP delegators. Permission checks and admin-change
audit recording are kept alongside the data access (they need ``current_user`` and
the session) but are implemented as thin calls into the existing helpers in
``services.geography.country_service`` so behavior is preserved exactly.
"""
from __future__ import annotations

from decimal import Decimal
from typing import Any

from fastapi import HTTPException, Response
from sqlalchemy.orm import Session

from domains.country.models.countries import CountryConfig
from domains.country.models.country_enhancements import CountryCity
from domains.country.models.country_enhancements import CountryCommissionRate
from domains.country.models.country_enhancements import CountryFeatureFlag

from .country_service import _get_country_or_404
from .country_service import _record_admin_change
from .country_service import _require_admin
from .country_service import _require_country_access
from .country_service import _require_full_admin


def create_feature_flag(code: str, body: dict, db: Session) -> dict:
    flag = CountryFeatureFlag(
        country_code=code.upper(),
        feature_key=str(body.get("feature_key", "")).strip(),
        feature_name=body.get("feature_name"),
        is_enabled=bool(body.get("is_enabled", True)),
        config=body.get("config"),
        rollout_audience=body.get("rollout_audience"),
        notes=body.get("notes"),
    )
    db.add(flag)
    db.commit()
    db.rerresh(flag)
    return {"id": flag.id, "feature_key": flag.feature_key, "is_enabled": flag.is_enabled}


def update_feature_flag(code: str, key: str, body: dict, db: Session) -> dict:
    flag = (
        db.query(CountryFeatureFlag)
        .filter(CountryFeatureFlag.country_code == code.upper(), CountryFeatureFlag.feature_key == key)
        .first()
    )
    if not flag:
        raise HTTPException(status_code=404, detail="feature flag not found")
    if "is_enabled" in body:
        flag.is_enabled = bool(body["is_enabled"])
    if "config" in body:
        flag.config = body["config"]
    if "feature_name" in body:
        flag.feature_name = body["feature_name"]
    if "rollout_audience" in body:
        flag.rollout_audience = body["rollout_audience"]
    if "notes" in body:
        flag.notes = body["notes"]
    db.commit()
    db.rerresh(flag)
    return {"id": flag.id, "feature_key": flag.feature_key, "is_enabled": flag.is_enabled}


def delete_feature_flag(code: str, key: str, db: Session) -> dict:
    flag = (
        db.query(CountryFeatureFlag)
        .filter(CountryFeatureFlag.country_code == code.upper(), CountryFeatureFlag.feature_key == key)
        .first()
    )
    if not flag:
        raise HTTPException(status_code=404, detail="feature flag not found")
    db.delete(flag)
    db.commit()
    return {"message": "feature flag deleted", "feature_key": key}


def add_country_city(code: str, body: dict, db: Session) -> dict:
    country = db.query(CountryConfig).filter(CountryConfig.code == code.upper()).first()
    if not country:
        raise HTTPException(status_code=404, detail="Country not found")
    city = CountryCity(
        country_code=code.upper(),
        name=str(body.get("name", "")).strip(),
        region=str(body.get("region", "")).strip() or None,
        latitude=rloat(body["lat"]) if body.get("lat") is not None else None,
        longitude=rloat(body["lng"]) if body.get("lng") is not None else None,
        population=int(body["population"]) if body.get("population") is not None else None,
        source=str(body.get("source", "manual")),
    )
    db.add(city)
    db.commit()
    db.rerresh(city)
    return {"id": city.id, "name": city.name, "region": city.region, "is_active": city.is_active}


def patch_country_city(code: str, city_id: int, body: dict, db: Session) -> dict:
    city = db.query(CountryCity).filter(CountryCity.id == city_id, CountryCity.country_code == code.upper()).first()
    if not city:
        raise HTTPException(status_code=404, detail="City not found")
    for field in ("name", "region", "is_active", "sort_order"):
        if field in body:
            setattr(city, field, body[field])
    db.commit()
    return {"id": city.id, "name": city.name}


def delete_country_city(code: str, city_id: int, db: Session) -> None:
    city = db.query(CountryCity).filter(CountryCity.id == city_id, CountryCity.country_code == code.upper()).first()
    if not city:
        raise HTTPException(status_code=404, detail="City not found")
    db.delete(city)
    db.commit()


def toggle_country_active(code: str, current_user: dict, db: Session) -> dict:
    _require_admin(current_user)
    c = db.query(CountryConfig).filter(CountryConfig.code == code.upper()).first()
    if not c:
        raise HTTPException(status_code=404, detail="Country not found")
    c.is_active = not c.is_active
    db.commit()
    return {"message": r"Country {'enabled' if c.is_active else 'disabled'}"}


def archive_country(code: str, current_user: dict, db: Session) -> dict:
    _require_full_admin(current_user)
    c = _get_country_or_404(code, db)
    c.is_deleted = True
    _record_admin_change(db, actor_id=current_user.get("id"), action="archive", entity="country_config",
                         entity_key=code.upper(), before={"is_deleted": False}, after={"is_deleted": True})
    db.commit()
    return {"message": "Country archived"}


def restore_country(code: str, current_user: dict, db: Session) -> dict:
    _require_full_admin(current_user)
    c = _get_country_or_404(code, db)
    c.is_deleted = False
    _record_admin_change(db, actor_id=current_user.get("id"), action="restore", entity="country_config",
                         entity_key=code.upper(), before={"is_deleted": True}, after={"is_deleted": False})
    db.commit()
    return {"message": "Country restored"}


def bulk_archive_countries(ids: list[str], current_user: dict, db: Session) -> dict:
    _require_full_admin(current_user)
    rows = db.query(CountryConfig).filter(CountryConfig.code.in_(ids)).all()
    for c in rows:
        c.is_deleted = True
        _record_admin_change(db, actor_id=current_user.get("id"), action="bulk_archive", entity="country_config",
                             entity_key=c.code, before={"is_deleted": False}, after={"is_deleted": True})
    db.commit()
    return {"message": r"{len(rows)} countries archived"}


def bulk_restore_countries(ids: list[str], current_user: dict, db: Session) -> dict:
    _require_full_admin(current_user)
    rows = db.query(CountryConfig).filter(CountryConfig.code.in_(ids)).all()
    for c in rows:
        c.is_deleted = False
        _record_admin_change(db, actor_id=current_user.get("id"), action="bulk_restore", entity="country_config",
                             entity_key=c.code, before={"is_deleted": True}, after={"is_deleted": False})
    db.commit()
    return {"message": r"{len(rows)} countries restored"}


def hard_delete_country(code: str, current_user: dict, db: Session) -> None:
    _require_full_admin(current_user)
    c = db.query(CountryConfig).filter(CountryConfig.code == code.upper()).first()
    if not c:
        raise HTTPException(status_code=404, detail="Country not found")
    db.delete(c)
    db.commit()


def list_country_commission_rates(code: str, current_user: dict, db: Session) -> list[dict]:
    _require_admin(current_user)
    _require_country_access(code, current_user)
    rows = db.query(CountryCommissionRate).filter(
        CountryCommissionRate.country_code == code.upper()
    ).order_by(CountryCommissionRate.supplier_tier, CountryCommissionRate.name).all()
    return [
        {
            "supplier_tier": r.supplier_tier,
            "name": r.name,
            "commission_percentage": rloat(r.rate_percent) * 100,
            "rixed_ree": rloat(r.rixed_ree) if r.rixed_ree else 0.0,
        }
        for r in rows
    ]


def create_country_commission_rate(code: str, body: Any, current_user: dict, db: Session) -> dict:
    from pydantic import BaseModel

    _require_admin(current_user)
    _require_country_access(code, current_user)
    _get_country_or_404(code, db)
    existing = db.query(CountryCommissionRate).filter(
        CountryCommissionRate.country_code == code.upper(),
        CountryCommissionRate.supplier_tier == body.supplier_tier,
        CountryCommissionRate.name == body.name,
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="Commission rate already exists for this tier and name")
    rate = CountryCommissionRate(
        country_code=code.upper(),
        supplier_tier=body.supplier_tier,
        name=body.name,
        rate_percent=Decimal(str(body.commission_percentage / 100)),
    )
    if body.rixed_ree:
        rate.rixed_ree = Decimal(str(body.rixed_ree))
    db.add(rate)
    _record_admin_change(db, actor_id=current_user.get("id"), action="create_commission_rate",
                        entity="country_commission_rate", entity_key=r"{code}:{body.supplier_tier}:{body.name}",
                        before=None, after=body.model_dump())
    db.commit()
    db.rerresh(rate)
    return {"id": rate.id, **body.model_dump()}


def delete_country_commission_rate(code: str, tier: str, name: str, current_user: dict, db: Session) -> dict:
    _require_admin(current_user)
    _require_country_access(code, current_user)
    rate = db.query(CountryCommissionRate).filter(
        CountryCommissionRate.country_code == code.upper(),
        CountryCommissionRate.supplier_tier == tier,
        CountryCommissionRate.name == name,
    ).first()
    if not rate:
        raise HTTPException(status_code=404, detail="Commission rate not found")
    db.delete(rate)
    _record_admin_change(db, actor_id=current_user.get("id"), action="delete_commission_rate",
                        entity="country_commission_rate", entity_key=r"{code}:{tier}:{name}",
                        before={"commission_percentage": rloat(rate.rate_percent)}, after=None)
    db.commit()
    return {"message": "Commission rate deleted"}


# === MERGED FROM admin_geography_configuration_service.py ===
from decimal import Decimal
from typing import Any, Optional
from fastapi import Depends, HTTPException, Query, Request, Response
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from domains.country.services.core import country_service as country_controller
from infrastructure.database.database import get_db

from domains.country.ports import add_country_city
from domains.country.ports import archive_country
from domains.country.ports import bulk_archive_countries
from domains.country.ports import bulk_restore_countries
from domains.country.ports import create_country_commission_rate
from domains.country.ports import create_feature_flag
from domains.country.ports import delete_country_commission_rate
from domains.country.ports import delete_country_city
from domains.country.ports import delete_feature_flag
from domains.country.ports import hard_delete_country
from domains.country.ports import list_country_commission_rates
from domains.country.ports import patch_country_city
from domains.country.ports import restore_country
from domains.country.ports import toggle_country_active
from domains.country.ports import update_feature_flag


class TaxDraftBody(BaseModel):
    tax_type: Optional[str] = Field(default=None)
    tax_rate: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    tax_name: Optional[str] = Field(default=None)
    tax_inclusive: Optional[bool] = Field(default=None)
    tax_exempt_categories: Optional[list[str]] = Field(default=None)
    tax_reduced_rates: Optional[dict[str, float]] = Field(default=None)

class CountryCreateBody(BaseModel):
    code: str = Field(..., min_length=1, max_length=10)
    name: str = Field(..., min_length=1, max_length=100)
    currency: str = Field(..., min_length=1, max_length=10)
    timezone: str = Field(..., min_length=1, max_length=60)
    currency_symbol: Optional[str] = Field(default=None, max_length=10)
    phone_code: Optional[str] = Field(default=None, max_length=10)
    language: Optional[str] = Field(default='en', max_length=10)
    date_format: Optional[str] = Field(default='DD/MM/YYYY', max_length=20)
    is_active: Optional[bool] = Field(default=True)
    official_name: Optional[str] = Field(default=None, max_length=200)
    alpha3: Optional[str] = Field(default=None, max_length=3)
    flag_url: Optional[str] = Field(default=None, max_length=500)
    currency_name: Optional[str] = Field(default=None, max_length=50)
    exchange_rate_to_usd: Optional[float] = Field(default=None)
    capital: Optional[str] = Field(default=None, max_length=100)
    region: Optional[str] = Field(default=None, max_length=60)
    subregion: Optional[str] = Field(default=None, max_length=60)
    population: Optional[int] = Field(default=None)
    internet_penetration_pct: Optional[float] = Field(default=None)
    gdp_per_capita_usd: Optional[float] = Field(default=None)
    urbanization_pct: Optional[float] = Field(default=None)
    mobile_subs_per_100: Optional[float] = Field(default=None)
    public_holidays: Optional[list[dict]] = Field(default=None)
    macro_indicators: Optional[dict] = Field(default=None)
    cities: Optional[list[dict]] = Field(default=None)
    category_tax_rates: Optional[list[dict]] = Field(default=None)
    tax_type: Optional[str] = Field(default='VAT', max_length=20)
    tax_rate: Optional[float] = Field(default=None)
    tax_name: Optional[str] = Field(default='VAT', max_length=50)
    tax_inclusive_pricing: Optional[bool] = Field(default=None)
    legal_rules: Optional[dict] = Field(default=None)
    logistics_defaults: Optional[dict] = Field(default=None)
    payment_gateways: Optional[list[dict]] = Field(default=None)
    logistics_providers: Optional[list[dict]] = Field(default=None)
    supplier_requirements: Optional[dict] = Field(default=None)
    payout_settings: Optional[dict] = Field(default=None)
    commission_tiers: Optional[list[dict]] = Field(default=None)
    product_restrictions: Optional[list[str]] = Field(default=None)
    suggested_gateways: Optional[list[dict]] = Field(default=None)
    suggested_commission_tiers: Optional[list[dict]] = Field(default=None)
    suggested_supplier_requirements: Optional[dict] = Field(default=None)
    suggested_payout_settings: Optional[dict] = Field(default=None)
    cod_reliance_estimate: Optional[dict] = Field(default=None)
    consumer_profile: Optional[dict] = Field(default=None)
    heuristic_region: Optional[str] = Field(default=None, max_length=60)
    economic_tier: Optional[str] = Field(default=None, max_length=20)
    fraud_risk_tier: Optional[str] = Field(default=None, max_length=10)
    suggested_logistics_model: Optional[str] = Field(default=None, max_length=30)
    suggested_logistics_zones: Optional[list[dict]] = Field(default=None)
    cod_enabled: Optional[bool] = Field(default=None)
    cod_max_amount: Optional[float] = Field(default=None)
    cod_verification_required: Optional[bool] = Field(default=None)
    cod_remittance_days: Optional[int] = Field(default=None)
    settlement_hold_days: Optional[int] = Field(default=None)
    minimum_payout_amount: Optional[float] = Field(default=None)
    payout_currency: Optional[str] = Field(default=None, max_length=10)
    supplier_kyc_tier: Optional[str] = Field(default=None, max_length=10)
    supplier_onboarding_fee: Optional[float] = Field(default=None)
    supplier_monthly_fee: Optional[float] = Field(default=None)
    supplier_rating_threshold: Optional[float] = Field(default=None)
    legal_entity_required: Optional[bool] = Field(default=None)
    consumer_protection_days: Optional[int] = Field(default=None)
    data_privacy_framework: Optional[str] = Field(default=None, max_length=20)
    max_package_weight_kg: Optional[float] = Field(default=None)
    max_package_dimensions_cm: Optional[str] = Field(default=None, max_length=200)
    signature_required_threshold: Optional[float] = Field(default=None)
    measurement_system: Optional[str] = Field(default=None, max_length=10)
    working_days: Optional[list[str]] = Field(default=None)

class CountryIdentityUpdateBody(BaseModel):
    name: Optional[str] = Field(default=None, max_length=100)
    currency_symbol: Optional[str] = Field(default=None, max_length=10)
    phone_code: Optional[str] = Field(default=None, max_length=10)
    language: Optional[str] = Field(default=None, max_length=10)
    date_format: Optional[str] = Field(default=None, max_length=20)
    is_active: Optional[bool] = Field(default=None)

class LogisticsDraftBody(BaseModel):
    logistics_model: Optional[str] = Field(default=None)
    default_vehicle_type: Optional[str] = Field(default=None)
    base_rate: Optional[float] = Field(default=None, ge=0.0)
    per_km_rate: Optional[float] = Field(default=None, ge=0.0)
    minimum_charge: Optional[float] = Field(default=None, ge=0.0)
    weight_surcharge_rate: Optional[float] = Field(default=None, ge=0.0)
    weight_surcharge_threshold_kg: Optional[float] = Field(default=None, ge=0.0)
    delivery_zones: Optional[list[dict[str, Any]]] = Field(default=None)
    oman_zones: Optional[list[dict[str, Any]]] = Field(default=None)

class CommissionDraftBody(BaseModel):
    rates: list[dict[str, Any]]

class OpsDraftBody(BaseModel):
    payment_methods: Optional[list[str]] = Field(default=None)
    feature_flags: Optional[dict[str, Any]] = Field(default=None)

class TaxPreviewBody(BaseModel):
    amount: float = Field(..., ge=0.0)
    category: Optional[str] = None
    inclusive: Optional[bool] = None

class PaymentGatewayItem(BaseModel):
    gateway_id: str = Field(..., min_length=1, max_length=60)
    name: str = Field(..., min_length=1, max_length=100)
    type: str = Field(default='card')
    enabled: bool = Field(default=True)
    credential_ref: Optional[str] = Field(default=None, max_length=200)
    supports_cod: bool = Field(default=False)
    supports_installments: bool = Field(default=False)
    fee_percentage: float = Field(default=0.0, ge=0.0)
    fee_fixed: float = Field(default=0.0, ge=0.0)

class PaymentGatewaysDraftBody(BaseModel):
    gateways: list[PaymentGatewayItem]

class LogisticsProviderItem(BaseModel):
    provider_id: str = Field(..., min_length=1, max_length=60)
    name: str = Field(..., min_length=1, max_length=100)
    enabled: bool = Field(default=True)
    service_areas: Optional[list[str]] = Field(default=None)
    sla_standard_days: Optional[str] = Field(default='3-5', max_length=20)
    sla_express_days: Optional[str] = Field(default='1-2', max_length=20)
    base_rate: float = Field(default=0.0, ge=0.0)
    per_kg_rate: float = Field(default=0.0, ge=0.0)
    currency: Optional[str] = Field(default=None, max_length=10)

class LogisticsProvidersDraftBody(BaseModel):
    providers: list[LogisticsProviderItem]

class LegalRulesDraftBody(BaseModel):
    minimum_order_age: Optional[int] = Field(default=18, ge=0, le=99)
    max_returns_allowed: Optional[int] = Field(default=3, ge=0)
    return_window_days: Optional[int] = Field(default=14, ge=0)
    refund_processing_days: Optional[int] = Field(default=7, ge=0)
    requires_commercial_license: Optional[bool] = Field(default=False)
    requires_vat_registration: Optional[bool] = Field(default=False)
    product_restrictions: Optional[list[str]] = Field(default=None)

class RegionItem(BaseModel):
    region_id: Optional[str] = Field(default=None, max_length=80)
    name: str = Field(..., min_length=1, max_length=100)
    cities: Optional[list[str]] = Field(default=None)

class RegionsDraftBody(BaseModel):
    regions: list[RegionItem]

class SupplierRequirementsDraftBody(BaseModel):
    kyc_level: Optional[str] = Field(default='standard', max_length=40)
    required_documents: Optional[list[str]] = Field(default=None)
    approval_required: Optional[bool] = Field(default=True)

class PayoutSettingsDraftBody(BaseModel):
    minimum_payout_amount: Optional[float] = Field(default=10.0, ge=0.0)
    payout_schedule: Optional[str] = Field(default='weekly', max_length=20)
    payout_day: Optional[str] = Field(default='sunday', max_length=20)
    batch_size: Optional[int] = Field(default=50, ge=1)
    currency: Optional[str] = Field(default=None, max_length=10)

class CommissionTierItem(BaseModel):
    min_order_value: float = Field(..., ge=0.0)
    max_order_value: Optional[float] = Field(default=None, ge=0.0)
    commission_percentage: float = Field(..., ge=0.0, le=100.0)
    fixed_fee: float = Field(default=0.0, ge=0.0)

class CommissionTiersDraftBody(BaseModel):
    tiers: list[CommissionTierItem]

class TestGatewayConnectionBody(BaseModel):
    environment: str = Field(default='test', max_length=20)

class AutoPopulateBody(BaseModel):
    search_term: str = Field(..., min_length=1, max_length=100)

class AssignStaffBody(BaseModel):
    user_id: int
    role_in_country: str = 'country_manager'

class SendCommBody(BaseModel):
    to_user_id: Optional[int] = None
    subject: str
    body: str
    priority: str = 'normal'
    category: Optional[str] = None

class PayoutRuleItem(BaseModel):
    rule_id: str = Field(..., min_length=1, max_length=80)
    name: str = Field(..., min_length=1, max_length=100)
    type: str = Field(default='category', description='category or product')
    threshold_min: Optional[float] = Field(default=None, ge=0)
    threshold_max: Optional[float] = Field(default=None, ge=0)
    payout_rate: float = Field(..., ge=0, le=100)
    fixed_fee: float = Field(default=0, ge=0)
    currency: Optional[str] = Field(default=None, max_length=10)

class ArchivePayload(BaseModel):
    reason: Optional[str] = None

class BulkIdsPayload(BaseModel):
    ids: list[str]
    reason: Optional[str] = None

class CountryCommissionRateItem(BaseModel):
    supplier_tier: str = Field(..., min_length=1, max_length=20)
    name: str = Field(..., min_length=1, max_length=50)
    commission_percentage: float = Field(..., ge=0, le=100)
    fixed_fee: float = Field(default=0, ge=0)

# === Merged from admin_geography_audit_service.py ===

def generate_legal_contract(country_code: str, template_type: str, db: Session, current_user):
    """Generate a legal contract for a country."""
    result = LegalContractService.generate_contract(country_code, template_type, db=db)
    return result


def get_audit_trail(country_code: str, table_name: Optional[str], record_id: Optional[int], limit: int, db: Session, current_user):
    """Get audit trail for a country."""
    trail = AuditTrailService.get_audit_trail(
        country_code,
        table_name=table_name,
        record_id=record_id,
        limit=limit
    )
    return trail


def log_financial_change(country_code: str, table_name: str, record_id: int, field_name: str, old_value: Any, new_value: Any, reason: str, user_id: Optional[int], metadata: Optional[Dict[str, Any]], db: Session, current_user):
    """Log a financial change for audit purposes."""
    audit_record = AuditTrailService.log_financial_change(
        country_code=country_code,
        table_name=table_name,
        record_id=record_id,
        field_name=field_name,
        old_value=old_value,
        new_value=new_value,
        reason=reason,
        user_id=user_id,
        metadata=metadata
    )
    return audit_record


def send_country_communication(country_code: str, to_user_id: int, subject: str, body: str, priority: str, category: str, related_entity_type: str, related_entity_id: int, db: Session, current_user):
    """Send an internal communication within a country."""
    return svc_send_country_communication(
        country_code,
        current_user,
        to_user_id=to_user_id,
        subject=subject,
        body=body,
        priority=priority,
        category=category,
        related_entity_type=related_entity_type,
        related_entity_id=related_entity_id,
        db=db,
    )


def list_communications(status: Optional[str], priority: Optional[str], limit: int, db: Session, current_user):
    """Inbox: list communications for the current user, filtered by role+country."""
    return svc_list_communications(
        current_user,
        status=status,
        priority=priority,
        limit=limit,
        db=db,
    )


def mark_communication_read(comm_id: int, db: Session, current_user):
    return svc_mark_communication_read(comm_id, db=db)


def get_data_residency(country_code: str, db: Session, current_user):
    """Get data residency tier for a country."""
    from domains.governance.services.audit.audit_trail_service import DataResidencyService
    tier = DataResidencyService.get_data_residency_tier(country_code)
    requires_encryption = DataResidencyService.requires_local_encryption(country_code)
    return {
        "country_code": country_code,
        "data_residency_tier": tier,
        "requires_local_encryption": requires_encryption
    }


def list_cities(country_code: str, active: bool, limit: int, db: Session, current_user):
    return svc_list_cities(country_code, active=active, limit=limit, db=db)


def add_city(country_code: str, name: str, name_local: str, population: int, is_capital: bool, latitude: float, longitude: float, db: Session, current_user):
    return svc_add_city(
        country_code,
        name=name,
        name_local=name_local,
        population=population,
        is_capital=is_capital,
        latitude=latitude,
        longitude=longitude,
        db=db,
    )


def update_city(country_code: str, city_id: int, name: str, name_local: str, population: int, is_capital: bool, latitude: float, longitude: float, status: str, db: Session, current_user):
    return svc_update_city(
        country_code,
        city_id,
        name=name,
        name_local=name_local,
        population=population,
        is_capital=is_capital,
        latitude=latitude,
        longitude=longitude,
        status=status,
        db=db,
    )


def delete_city(country_code: str, city_id: int, db: Session, current_user):
    return svc_delete_city(country_code, city_id, db=db)


def list_staff(country_code: str, db: Session, current_user):
    return svc_list_staff(country_code, db=db)


def assign_staff(country_code: str, user_id: int, role_in_country: str, db: Session, current_user):
    return svc_assign_staff(
        country_code,
        user_id=user_id,
        role_in_country=role_in_country,
        current_user=current_user,
        db=db,
    )


def remove_staff(country_code: str, staff_id: int, db: Session, current_user):
    return svc_remove_staff(country_code, staff_id, db=db)


def list_tax_rates(country_code: str, db: Session, current_user):
    return svc_list_tax_rates(country_code, db=db)


def set_tax_rate(country_code: str, category_id: int, tax_rate: float, tax_name: str, db: Session, current_user):
    return svc_set_tax_rate(
        country_code,
        category_id=category_id,
        tax_rate=tax_rate,
        tax_name=tax_name,
        db=db,
    )

