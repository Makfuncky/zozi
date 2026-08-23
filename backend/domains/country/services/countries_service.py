"""Auto-migrated service logic from routers/countries.py."""
from __future__ import annotations

from __future__ import annotations

from decimal import Decimal

from typing import Any, Optional

from fastapi import Depends, HTTPException, Query, Response

from pydantic import BaseModel, Field

from sqlalchemy.orm import Session

from domains.country.services import country_controller

from modules.employee.routers import employees_controller as ctrl

from domains.governance.services.auth.auth_controller_service import get_current_user


from infrastructure.database.database import get_db


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
    language: Optional[str] = Field(default="en", max_length=10)
    date_format: Optional[str] = Field(default="DD/MM/YYYY", max_length=20)
    is_active: Optional[bool] = Field(default=True)
    # Extended identity (Phase 1 blueprint)
    official_name: Optional[str] = Field(default=None, max_length=200)
    alpha3: Optional[str] = Field(default=None, max_length=3)
    flag_url: Optional[str] = Field(default=None, max_length=500)
    currency_name: Optional[str] = Field(default=None, max_length=50)
    exchange_rate_to_usd: Optional[float] = Field(default=None)
    capital: Optional[str] = Field(default=None, max_length=100)
    region: Optional[str] = Field(default=None, max_length=60)
    subregion: Optional[str] = Field(default=None, max_length=60)
    # Macro indicators
    population: Optional[int] = Field(default=None)
    internet_penetration_pct: Optional[float] = Field(default=None)
    gdp_per_capita_usd: Optional[float] = Field(default=None)
    urbanization_pct: Optional[float] = Field(default=None)
    mobile_subs_per_100: Optional[float] = Field(default=None)
    public_holidays: Optional[list[dict]] = Field(default=None)
    macro_indicators: Optional[dict] = Field(default=None)
    # Auto-populated arrays
    cities: Optional[list[dict]] = Field(default=None)
    category_tax_rates: Optional[list[dict]] = Field(default=None)
    # Tax settings from auto-populate
    tax_type: Optional[str] = Field(default="VAT", max_length=20)
    tax_rate: Optional[float] = Field(default=None)
    tax_name: Optional[str] = Field(default="VAT", max_length=50)
    tax_inclusive_pricing: Optional[bool] = Field(default=None)
    # Legal & logistics defaults
    legal_rules: Optional[dict] = Field(default=None)
    logistics_defaults: Optional[dict] = Field(default=None)
    # Payment & logistics provider configs
    payment_gateways: Optional[list[dict]] = Field(default=None)
    logistics_providers: Optional[list[dict]] = Field(default=None)
    # Supplier / payout / commission defaults
    supplier_requirements: Optional[dict] = Field(default=None)
    payout_settings: Optional[dict] = Field(default=None)
    commission_tiers: Optional[list[dict]] = Field(default=None)
    product_restrictions: Optional[list[str]] = Field(default=None)
    # ── Phase 1: Heuristic / algorithmic fields ──
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
    # ── Phase 1: COD / settlement ──
    cod_enabled: Optional[bool] = Field(default=None)
    cod_max_amount: Optional[float] = Field(default=None)
    cod_verification_required: Optional[bool] = Field(default=None)
    cod_remittance_days: Optional[int] = Field(default=None)
    settlement_hold_days: Optional[int] = Field(default=None)
    minimum_payout_amount: Optional[float] = Field(default=None)
    payout_currency: Optional[str] = Field(default=None, max_length=10)
    # ── Phase 1: Supplier defaults ──
    supplier_kyc_tier: Optional[str] = Field(default=None, max_length=10)
    supplier_onboarding_fee: Optional[float] = Field(default=None)
    supplier_monthly_fee: Optional[float] = Field(default=None)
    supplier_rating_threshold: Optional[float] = Field(default=None)
    # ── Phase 1: Legal / consumer ──
    legal_entity_required: Optional[bool] = Field(default=None)
    consumer_protection_days: Optional[int] = Field(default=None)
    data_privacy_framework: Optional[str] = Field(default=None, max_length=20)
    # ── Phase 1: Logistics expansion ──
    max_package_weight_kg: Optional[float] = Field(default=None)
    max_package_dimensions_cm: Optional[str] = Field(default=None, max_length=200)
    signature_required_threshold: Optional[float] = Field(default=None)
    # ── Phase 1: Locale ──
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
    type: str = Field(default="card")
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
    sla_standard_days: Optional[str] = Field(default="3-5", max_length=20)
    sla_express_days: Optional[str] = Field(default="1-2", max_length=20)
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
    kyc_level: Optional[str] = Field(default="standard", max_length=40)
    required_documents: Optional[list[str]] = Field(default=None)
    approval_required: Optional[bool] = Field(default=True)

class PayoutSettingsDraftBody(BaseModel):
    minimum_payout_amount: Optional[float] = Field(default=10.0, ge=0.0)
    payout_schedule: Optional[str] = Field(default="weekly", max_length=20)
    payout_day: Optional[str] = Field(default="sunday", max_length=20)
    batch_size: Optional[int] = Field(default=50, ge=1)
    currency: Optional[str] = Field(default=None, max_length=10)

class CommissionTierItem(BaseModel):
    min_order_value: float = Field(..., ge=0.0)
    max_order_value: Optional[float] = Field(default=None, ge=0.0)
    commission_percentage: float = Field(..., ge=0.0, le=100.0)
    fixed_fee: float = Field(default=0.0, ge=0.0)

class CommissionTiersDraftBody(BaseModel):
    tiers: list[CommissionTierItem]

class PayoutSettingsDraftBody(BaseModel):
    minimum_payout_amount: Optional[float] = Field(default=10.0, ge=0.0)
    payout_schedule: Optional[str] = Field(default="weekly", max_length=20)
    payout_day: Optional[str] = Field(default="sunday", max_length=20)
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
    environment: str = Field(default="test", max_length=20)

class AutoPopulateBody(BaseModel):
    search_term: str = Field(..., min_length=1, max_length=100)

class AssignStaffBody(BaseModel):
    user_id: int
    role_in_country: str = "country_manager"

class SendCommBody(BaseModel):
    to_user_id: Optional[int] = None
    subject: str
    body: str
    priority: str = "normal"
    category: Optional[str] = None

class PayoutRuleItem(BaseModel):
    rule_id: str = Field(..., min_length=1, max_length=80)
    name: str = Field(..., min_length=1, max_length=100)
    type: str = Field(default="category", description="category or product")
    threshold_min: Optional[float] = Field(default=None, ge=0)
    threshold_max: Optional[float] = Field(default=None, ge=0)
    payout_rate: float = Field(..., ge=0, le=100)
    fixed_fee: float = Field(default=0, ge=0)
    currency: Optional[str] = Field(default=None, max_length=10)

class ArchivePayload(BaseModel):
    reason: Optional[str] = None

class BulkIdsPayload(BaseModel):
    ids: list[str]  # country codes
    reason: Optional[str] = None

class CountryCommissionRateItem(BaseModel):
    supplier_tier: str = Field(..., min_length=1, max_length=20)
    name: str = Field(..., min_length=1, max_length=50)
    commission_percentage: float = Field(..., ge=0, le=100)
    fixed_fee: float = Field(default=0, ge=0)































def create_country_feature_flag(code: str, body: dict, current_user: dict, db: Session):
    from domains.country.models.country_enhancements import CountryFeatureFlag

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
    db.refresh(flag)
    return {"id": flag.id, "feature_key": flag.feature_key, "is_enabled": flag.is_enabled}

def update_country_feature_flag(code: str, key: str, body: dict, current_user: dict, db: Session):
    from domains.country.models.country_enhancements import CountryFeatureFlag

    flag = (
        db.query(CountryFeatureFlag)
        .filter(CountryFeatureFlag.country_code == code.upper(), CountryFeatureFlag.feature_key == key)
        .first()
    )
    if not flag:
        raise HTTPException(status_code=404, detail="Feature flag not found")
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
    db.refresh(flag)
    return {"id": flag.id, "feature_key": flag.feature_key, "is_enabled": flag.is_enabled}





def delete_country_feature_flag(code: str, key: str, current_user: dict, db: Session):
    from domains.country.models.country_enhancements import CountryFeatureFlag

    flag = (
        db.query(CountryFeatureFlag)
        .filter(CountryFeatureFlag.country_code == code.upper(), CountryFeatureFlag.feature_key == key)
        .first()
    )
    if not flag:
        raise HTTPException(status_code=404, detail="Feature flag not found")
    db.delete(flag)
    db.commit()
    return {"message": "Feature flag deleted", "feature_key": key}





async def auto_populate_country(body: AutoPopulateBody, current_user: dict, db: Session):
    """Fetch country data from external APIs and curated profiles."""
    from domains.country.services.country_controller import _require_admin
    _require_admin(current_user)
    return await country_controller.auto_populate_async(body.search_term)


def add_country_city(code: str, body: dict, current_user: dict, db: Session):
    from domains.country.services.country_controller import _require_admin
    _require_admin(current_user)
    from domains.country.models.countries import CountryConfig
    from domains.country.models.country_enhancements import CountryCity
    country = db.query(CountryConfig).filter(CountryConfig.code == code.upper()).first()
    if not country:
        raise HTTPException(status_code=404, detail="Country not found")
    city = CountryCity(
        country_code=code.upper(),
        name=str(body.get("name", "")).strip(),
        region=str(body.get("region", "")).strip() or None,
        latitude=float(body["lat"]) if body.get("lat") is not None else None,
        longitude=float(body["lng"]) if body.get("lng") is not None else None,
        population=int(body["population"]) if body.get("population") is not None else None,
        source=str(body.get("source", "manual")),
    )
    db.add(city)
    db.commit()
    db.refresh(city)
    return {"id": city.id, "name": city.name, "region": city.region, "is_active": city.is_active}

def patch_country_city(code: str, city_id: int, body: dict, current_user: dict, db: Session):
    from domains.country.services.country_controller import _require_admin
    _require_admin(current_user)
    from domains.country.models.country_enhancements import CountryCity
    city = db.query(CountryCity).filter(CountryCity.id == city_id, CountryCity.country_code == code.upper()).first()
    if not city:
        raise HTTPException(status_code=404, detail="City not found")
    for field in ("name", "region", "is_active", "sort_order"):
        if field in body:
            setattr(city, field, body[field])
    db.commit()
    return {"id": city.id, "name": city.name}

def delete_country_city(code: str, city_id: int, current_user: dict, db: Session):
    from domains.country.services.country_controller import _require_admin
    _require_admin(current_user)
    from domains.country.models.country_enhancements import CountryCity
    city = db.query(CountryCity).filter(CountryCity.id == city_id, CountryCity.country_code == code.upper()).first()
    if not city:
        raise HTTPException(status_code=404, detail="City not found")
    db.delete(city)
    db.commit()
    return Response(status_code=204)















def toggle_country_active(code: str, current_user: dict, db: Session):
    from domains.country.services.country_controller import _require_admin
    _require_admin(current_user)
    from domains.country.models.countries import CountryConfig
    c = db.query(CountryConfig).filter(CountryConfig.code == code.upper()).first()
    if not c:
        raise HTTPException(status_code=404, detail="Country not found")
    c.is_active = not c.is_active
    db.commit()
    return {"message": f"Country {'enabled' if c.is_active else 'disabled'}"}

def archive_country(code: str, payload: ArchivePayload, current_user: dict, db: Session):
    from domains.country.services.country_controller import _get_country_or_404
    from domains.country.services.country_controller import _record_admin_change
    from domains.country.services.country_controller import _require_full_admin
    _require_full_admin(current_user)
    c = _get_country_or_404(code, db)
    c.is_deleted = True
    _record_admin_change(db, actor_id=current_user.get("id"), action="archive", entity="country_config",
                         entity_key=code.upper(), before={"is_deleted": False}, after={"is_deleted": True})
    db.commit()
    return {"message": "Country archived"}

def restore_country(code: str, current_user: dict, db: Session):
    from domains.country.services.country_controller import _get_country_or_404
    from domains.country.services.country_controller import _record_admin_change
    from domains.country.services.country_controller import _require_full_admin
    _require_full_admin(current_user)
    c = _get_country_or_404(code, db)
    c.is_deleted = False
    _record_admin_change(db, actor_id=current_user.get("id"), action="restore", entity="country_config",
                         entity_key=code.upper(), before={"is_deleted": True}, after={"is_deleted": False})
    db.commit()
    return {"message": "Country restored"}

def bulk_archive_countries(payload: BulkIdsPayload, current_user: dict, db: Session):
    from domains.country.services.country_controller import _record_admin_change
    from domains.country.services.country_controller import _require_full_admin
    _require_full_admin(current_user)
    from domains.country.models.countries import CountryConfig
    rows = db.query(CountryConfig).filter(CountryConfig.code.in_(payload.ids)).all()
    for c in rows:
        c.is_deleted = True
        _record_admin_change(db, actor_id=current_user.get("id"), action="bulk_archive", entity="country_config",
                             entity_key=c.code, before={"is_deleted": False}, after={"is_deleted": True})
    db.commit()
    return {"message": f"{len(rows)} countries archived"}

def bulk_restore_countries(payload: BulkIdsPayload, current_user: dict, db: Session):
    from domains.country.services.country_controller import _record_admin_change
    from domains.country.services.country_controller import _require_full_admin
    _require_full_admin(current_user)
    from domains.country.models.countries import CountryConfig
    rows = db.query(CountryConfig).filter(CountryConfig.code.in_(payload.ids)).all()
    for c in rows:
        c.is_deleted = False
        _record_admin_change(db, actor_id=current_user.get("id"), action="bulk_restore", entity="country_config",
                             entity_key=c.code, before={"is_deleted": True}, after={"is_deleted": False})
    db.commit()
    return {"message": f"{len(rows)} countries restored"}

def hard_delete_country(code: str, current_user: dict, db: Session):
    from domains.country.services.country_controller import _require_full_admin
    _require_full_admin(current_user)
    c = db.query(CountryConfig).filter(CountryConfig.code == code.upper()).first()
    if not c:
        raise HTTPException(status_code=404, detail="Country not found")
    db.delete(c)
    db.commit()
    return Response(status_code=204)

def list_country_commission_rates(code: str, current_user: dict, db: Session):
    from domains.country.services.country_controller import _require_admin
    from domains.country.services.country_controller import _require_country_access
    _require_admin(current_user)
    _require_country_access(code, current_user)
    from domains.country.models.country_enhancements import CountryCommissionRate
    rows = db.query(CountryCommissionRate).filter(
        CountryCommissionRate.country_code == code.upper()
    ).order_by(CountryCommissionRate.supplier_tier, CountryCommissionRate.name).all()
    return [{"supplier_tier": r.supplier_tier, "name": r.name, "commission_percentage": float(r.rate_percent) * 100, "fixed_fee": float(r.fixed_fee) if r.fixed_fee else 0.0} for r in rows]

def create_country_commission_rate(code: str, body: CountryCommissionRateItem, current_user: dict, db: Session):
    from domains.country.services.country_controller import _get_country_or_404
    from domains.country.services.country_controller import _record_admin_change
    from domains.country.services.country_controller import _require_admin
    from domains.country.services.country_controller import _require_country_access
    _require_admin(current_user)
    _require_country_access(code, current_user)
    _get_country_or_404(code, db)
    from domains.country.models.country_enhancements import CountryCommissionRate
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
    if body.fixed_fee:
        rate.fixed_fee = Decimal(str(body.fixed_fee))
    db.add(rate)
    _record_admin_change(db, actor_id=current_user.get("id"), action="create_commission_rate", entity="country_commission_rate", entity_key=f"{code}:{body.supplier_tier}:{body.name}", before=None, after=body.model_dump())
    db.commit()
    db.refresh(rate)
    return {"id": rate.id, **body.model_dump()}

def delete_country_commission_rate(code: str, tier: str, name: str, current_user: dict, db: Session):
    from domains.country.services.country_controller import _record_admin_change
    from domains.country.services.country_controller import _require_admin
    from domains.country.services.country_controller import _require_country_access
    _require_admin(current_user)
    _require_country_access(code, current_user)
    from domains.country.models.country_enhancements import CountryCommissionRate
    rate = db.query(CountryCommissionRate).filter(
        CountryCommissionRate.country_code == code.upper(),
        CountryCommissionRate.supplier_tier == tier,
        CountryCommissionRate.name == name,
    ).first()
    if not rate:
        raise HTTPException(status_code=404, detail="Commission rate not found")
    db.delete(rate)
    _record_admin_change(db, actor_id=current_user.get("id"), action="delete_commission_rate", entity="country_commission_rate", entity_key=f"{code}:{tier}:{name}", before={"commission_percentage": float(rate.rate_percent)}, after=None)
    db.commit()
    return {"message": "Commission rate deleted"}




from domains.governance.services.country.flat_admin_geography_configuration_service import get_public_country_config














from domains.governance.services.country.flat_admin_geography_configuration_service import list_public_country_employees











from domains.governance.services.country.flat_admin_geography_configuration_service import create_admin_country













from domains.governance.services.country.flat_admin_geography_configuration_service import get_admin_country














from domains.governance.services.country.flat_admin_geography_configuration_service import update_admin_country_identity
from domains.governance.services.country.flat_admin_geography_configuration_service import create_tax_draft


# === auto-wiring re-exports (migration repair) ===
from domains.governance.services.country.flat_admin_geography_configuration_service import approve_country_version
from domains.governance.services.country.flat_admin_geography_configuration_service import create_commission_draft
from domains.governance.services.country.flat_admin_geography_configuration_service import create_commission_tiers_draft
from domains.governance.services.country.flat_admin_geography_configuration_service import create_legal_rules_draft
from domains.governance.services.country.flat_admin_geography_configuration_service import create_logistics_draft
from domains.governance.services.country.flat_admin_geography_configuration_service import create_logistics_providers_draft
from domains.governance.services.country.flat_admin_geography_configuration_service import create_ops_draft
from domains.governance.services.country.flat_admin_geography_configuration_service import create_payment_gateways_draft
from domains.governance.services.country.flat_admin_geography_configuration_service import create_payout_rule_category
from domains.governance.services.country.flat_admin_geography_configuration_service import create_payout_rule_product
from domains.governance.services.country.flat_admin_geography_configuration_service import create_payout_settings_draft
from domains.governance.services.country.flat_admin_geography_configuration_service import create_regions_draft
from domains.governance.services.country.flat_admin_geography_configuration_service import create_supplier_requirements_draft
from domains.governance.services.country.flat_admin_geography_configuration_service import delete_country_promotion
from domains.governance.services.country.flat_admin_geography_configuration_service import delete_payout_rule_category
from domains.governance.services.country.flat_admin_geography_configuration_service import delete_payout_rule_product
from domains.governance.services.country.flat_admin_geography_configuration_service import get_commission_tiers
from domains.governance.services.country.flat_admin_geography_configuration_service import get_country_feature_flags
from domains.governance.services.country.flat_admin_geography_configuration_service import get_country_localization
from domains.governance.services.country.flat_admin_geography_configuration_service import get_legal_rules
from domains.governance.services.country.flat_admin_geography_configuration_service import get_logistics_providers
from domains.governance.services.country.flat_admin_geography_configuration_service import get_payment_gateways
from domains.governance.services.country.flat_admin_geography_configuration_service import get_payout_settings
from domains.governance.services.country.flat_admin_geography_configuration_service import get_regions
from domains.governance.services.country.flat_admin_geography_configuration_service import get_supplier_requirements
from domains.governance.services.country.flat_admin_geography_configuration_service import list_country_cities
from domains.governance.services.country.flat_admin_geography_configuration_service import list_country_commissions
from domains.governance.services.country.flat_admin_geography_configuration_service import list_country_delivery_zones
from domains.governance.services.country.flat_admin_geography_configuration_service import list_country_promotions
from domains.governance.services.country.flat_admin_geography_configuration_service import list_country_versions
from domains.governance.services.country.flat_admin_geography_configuration_service import list_cross_country_sessions
from domains.governance.services.country.flat_admin_geography_configuration_service import list_oman_delivery_zones_compat
from domains.governance.services.country.flat_admin_geography_configuration_service import list_payout_rules_categories
from domains.governance.services.country.flat_admin_geography_configuration_service import list_payout_rules_products
from domains.governance.services.country.flat_admin_geography_configuration_service import preview_country_tax
from domains.governance.services.country.flat_admin_geography_configuration_service import publish_country_version
from domains.governance.services.country.flat_admin_geography_configuration_service import rollback_country_to_version
from domains.governance.services.country.flat_admin_geography_configuration_service import send_communication
from domains.governance.services.country.flat_admin_geography_configuration_service import test_gateway_connection
from domains.governance.services.country.flat_admin_geography_configuration_service import unassign_staff
from domains.governance.services.country.flat_admin_geography_configuration_service import update_country_cities_bulk
from domains.governance.services.country.flat_admin_geography_configuration_service import update_country_localization
from domains.governance.services.country.flat_admin_geography_audit_service import assign_staff
from domains.governance.services.country.flat_admin_geography_audit_service import list_communications
from domains.governance.services.country.flat_admin_geography_audit_service import list_staff
from domains.governance.services.country.flat_admin_geography_audit_service import mark_communication_read


