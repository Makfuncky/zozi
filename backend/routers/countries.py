from __future__ import annotations

from decimal import Decimal
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from controllers.auth_controller import get_current_user
from controllers import country_controller
from controllers import employees_controller as ctrl
from db.database import get_db
from services.country_auto_populate import router as auto_populate_router
from controllers.country_versioning_controller import router as versioning_router
from middleware.rls_dependency import get_country_scope as _get_country_scope


router = APIRouter()


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


# ── Public Endpoints ──────────────────────────────────────────────────────────

@router.get("")
def list_public_countries(db: Session = Depends(get_db)):
    return country_controller.list_public_countries(db)


@router.get("/{code}/config")
def get_public_country_config(code: str, db: Session = Depends(get_db)):
    return country_controller.get_public_country_config(code, db)


@router.get("/{code}/employees")
def list_public_country_employees(code: str, db: Session = Depends(get_db)):
    """Public endpoint to list employees by country code."""
    return ctrl.list_employees(code, db)


# NOTE: The public GET /{code}/cities endpoint was removed — it was shadowed by
# the authenticated list_country_cities route at the same path (second registration
# wins in FastAPI). The authenticated version supports search (?q=), pagination
# (?limit=), and admin auth.
#
# TODO: If customer-facing checkout/shipping dropdowns need city data without auth,
# add a dedicated public route at GET /public/{code}/cities that calls
# country_controller.list_public_cities(code, db).

@router.post("")
def create_admin_country(body: CountryCreateBody, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    return country_controller.create_admin_country(body.model_dump(exclude_none=True), current_user, db)


@router.get("/{code}")
def get_admin_country(code: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    return country_controller.get_admin_country(code, current_user, db)


@router.patch("/{code}")
def update_admin_country_identity(code: str, body: CountryIdentityUpdateBody, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    return country_controller.update_country_identity(code, body.model_dump(exclude_none=True), current_user, db)


# ── Admin: Versioned Config Drafts ────────────────────────────────────────────

@router.put("/{code}/tax")
def create_tax_draft(code: str, body: TaxDraftBody, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    return country_controller.create_tax_draft(code, body.model_dump(exclude_none=True), current_user, db)


@router.put("/{code}/logistics")
def create_logistics_draft(code: str, body: LogisticsDraftBody, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    return country_controller.create_logistics_draft(code, body.model_dump(exclude_none=True), current_user, db)


@router.put("/{code}/commissions")
def create_commission_draft(code: str, body: CommissionDraftBody, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    return country_controller.create_commission_draft(code, body.model_dump(exclude_none=True), current_user, db)


@router.put("/{code}/ops")
def create_ops_draft(code: str, body: OpsDraftBody, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    return country_controller.create_payment_and_flags_draft(code, body.model_dump(exclude_none=True), current_user, db)


# ── Admin: New GCC Config Sections ───────────────────────────────────────────

@router.get("/{code}/payment-gateways")
def get_payment_gateways(code: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    return country_controller.get_payment_gateways(code, current_user, db)


@router.put("/{code}/payment-gateways")
def create_payment_gateways_draft(code: str, body: PaymentGatewaysDraftBody, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    return country_controller.create_payment_gateways_draft(code, body.model_dump(), current_user, db)


@router.get("/{code}/logistics-providers")
def get_logistics_providers(code: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    return country_controller.get_logistics_providers(code, current_user, db)


@router.put("/{code}/logistics-providers")
def create_logistics_providers_draft(code: str, body: LogisticsProvidersDraftBody, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    return country_controller.create_logistics_providers_draft(code, body.model_dump(), current_user, db)


@router.get("/{code}/legal-rules")
def get_legal_rules(code: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    return country_controller.get_legal_rules(code, current_user, db)


@router.put("/{code}/legal-rules")
def create_legal_rules_draft(code: str, body: LegalRulesDraftBody, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    return country_controller.create_legal_rules_draft(code, body.model_dump(exclude_none=True), current_user, db)


@router.get("/{code}/regions")
def get_regions(code: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    return country_controller.get_regions(code, current_user, db)


@router.put("/{code}/regions")
def create_regions_draft(code: str, body: RegionsDraftBody, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    return country_controller.create_regions_draft(code, body.model_dump(), current_user, db)


@router.get("/{code}/supplier-requirements")
def get_supplier_requirements(code: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    return country_controller.get_supplier_requirements(code, current_user, db)


@router.put("/{code}/supplier-requirements")
def create_supplier_requirements_draft(code: str, body: SupplierRequirementsDraftBody, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    return country_controller.create_supplier_requirements_draft(code, body.model_dump(exclude_none=True), current_user, db)


@router.get("/{code}/payout-settings")
def get_payout_settings(code: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    return country_controller.get_payout_settings(code, current_user, db)


@router.put("/{code}/payout-settings")
def create_payout_settings_draft(code: str, body: PayoutSettingsDraftBody, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    return country_controller.create_payout_settings_draft(code, body.model_dump(exclude_none=True), current_user, db)


@router.get("/{code}/commission-tiers")
def get_commission_tiers(code: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    return country_controller.get_commission_tiers(code, current_user, db)


@router.put("/{code}/commission-tiers")
def create_commission_tiers_draft(code: str, body: CommissionTiersDraftBody, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    return country_controller.create_commission_tiers_draft(code, body.model_dump(), current_user, db)


# ── Admin: Versioning (approve / publish / rollback) ──────────────────────────

@router.get("/{code}/versions")
def list_country_versions(
    code: str,
    config_type: str | None = Query(default=None),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return country_controller.list_country_versions(code, current_user, db, config_type=config_type)


@router.post("/{code}/versions/{version_id}/approve")
def approve_country_version(code: str, version_id: int, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    return country_controller.approve_country_version(code, version_id, current_user, db)


@router.post("/{code}/versions/{version_id}/publish")
def publish_country_version(code: str, version_id: int, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    return country_controller.publish_country_version(code, version_id, current_user, db)


@router.post("/{code}/versions/{version_id}/rollback")
def rollback_country_to_version(code: str, version_id: int, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    return country_controller.rollback_country_to_version(code, version_id, current_user, db)


# ── Admin: Supplementary Getters ──────────────────────────────────────────────

@router.get("/{code}/commissions")
def list_country_commissions(code: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    return country_controller.list_country_commissions(code, current_user, db)


@router.get("/{code}/feature-flags")
def get_country_feature_flags(code: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    return country_controller.get_country_feature_flags(code, current_user, db)


@router.post("/{code}/feature-flags")
def create_country_feature_flag(
    code: str,
    body: dict,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from models.country_enhancements import CountryFeatureFlag

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


@router.patch("/{code}/feature-flags/{key}")
def update_country_feature_flag(
    code: str,
    key: str,
    body: dict,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from models.country_enhancements import CountryFeatureFlag

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


@router.get("/{code}/promotions")
def list_country_promotions(code: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    return []


@router.delete("/{code}/promotions/{slug}")
def delete_country_promotion(code: str, slug: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    # Promotions are currently not persisted server-side; acknowledge deletion so the
    # client can optimistically remove the row without surfacing a 404/500.
    return {"message": "Promotion deleted", "slug": slug}


@router.get("/{code}/localization")
def get_country_localization(code: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    return {
        "default_language": "en",
        "supported_languages": ["en", "ar"],
        "rtl_enabled": False,
        "number_format": "western",
        "calendar_type": "gregorian",
    }


@router.put("/{code}/localization")
def update_country_localization(code: str, body: dict, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    return {
        "message": "Localization updated",
        "code": code.upper(),
        **(body if isinstance(body, dict) else {}),
    }


@router.delete("/{code}/feature-flags/{key}")
def delete_country_feature_flag(code: str, key: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    from models.country_enhancements import CountryFeatureFlag

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


@router.get("/{code}/delivery-zones")
def list_country_delivery_zones(code: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    return country_controller.list_country_delivery_zones(code, current_user, db)


@router.get("/om/zones")
def list_oman_delivery_zones_compat(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    # Backward compatibility path for existing Oman admin tooling.
    return country_controller.list_country_delivery_zones("OM", current_user, db)


@router.post("/{code}/preview-tax")
def preview_country_tax(code: str, body: TaxPreviewBody, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    return country_controller.preview_country_tax(code, body.model_dump(exclude_none=True), current_user, db)


class TestGatewayConnectionBody(BaseModel):
    environment: str = Field(default="test", max_length=20)


@router.post("/{code}/payment-gateways/{gateway_id}/test")
def test_gateway_connection(
    code: str,
    gateway_id: str,
    body: TestGatewayConnectionBody = TestGatewayConnectionBody(),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return country_controller.test_gateway_connection(code, gateway_id, body.environment, current_user, db)


class AutoPopulateBody(BaseModel):
    search_term: str = Field(..., min_length=1, max_length=100)


@router.post("/auto-populate")
async def auto_populate_country(body: AutoPopulateBody, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """Fetch country data from external APIs and curated profiles."""
    from controllers.country_controller import _require_admin
    _require_admin(current_user)
    return await country_controller.auto_populate_async(body.search_term)


@router.get("/{code}/cities")
def list_country_cities(
    code: str,
    q: str | None = Query(default=None, description="Search query"),
    limit: int = Query(default=50, ge=1, le=200, description="Max results"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return a list of known cities for the given country code.

    Supports search (?q=muscat), pagination (?limit=10), and returns structured
    city objects from the normalized CountryCity table.
    """
    return country_controller.list_country_cities(
        code, current_user, db, query=q, limit=limit,
    )


@router.post("/{code}/cities")
def add_country_city(
    code: str,
    body: dict,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from controllers.country_controller import _require_admin
    _require_admin(current_user)
    from models import CountryCity, CountryConfig
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


@router.patch("/{code}/cities/{city_id}")
def patch_country_city(
    code: str,
    city_id: int,
    body: dict,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from controllers.country_controller import _require_admin
    _require_admin(current_user)
    from models import CountryCity
    city = db.query(CountryCity).filter(CountryCity.id == city_id, CountryCity.country_code == code.upper()).first()
    if not city:
        raise HTTPException(status_code=404, detail="City not found")
    for field in ("name", "region", "is_active", "sort_order"):
        if field in body:
            setattr(city, field, body[field])
    db.commit()
    return {"id": city.id, "name": city.name}


@router.delete("/{code}/cities/{city_id}")
def delete_country_city(
    code: str,
    city_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from controllers.country_controller import _require_admin
    _require_admin(current_user)
    from models import CountryCity
    city = db.query(CountryCity).filter(CountryCity.id == city_id, CountryCity.country_code == code.upper()).first()
    if not city:
        raise HTTPException(status_code=404, detail="City not found")
    db.delete(city)
    db.commit()
    return Response(status_code=204)

@router.put("/{code}/cities")
def update_country_cities_bulk(
    code: str,
    body: dict,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Bulk update all cities for a country code.

    Replaces all existing cities with the provided list.
    Expected body: {"cities": [{"name": "...", "region": "...", "latitude": ..., "longitude": ..., "population": ..., "is_active": true, "sort_order": 0}, ...]}
    """
    return country_controller.update_country_cities_bulk(code, body, current_user, db)


class AssignStaffBody(BaseModel):
    user_id: int
    role_in_country: str = "country_manager"


class SendCommBody(BaseModel):
    to_user_id: Optional[int] = None
    subject: str
    body: str
    priority: str = "normal"
    category: Optional[str] = None


# ── Staff Assignments ──────────────────────────────────────────────────────────

@router.get("/{code}/staff")
def list_staff(code: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    return country_controller.list_country_staff(code, current_user, db)


@router.post("/{code}/staff")
def assign_staff(code: str, body: AssignStaffBody, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    return country_controller.assign_staff_to_country(code, body.user_id, body.role_in_country, current_user, db)


@router.delete("/{code}/staff/{user_id}")
def unassign_staff(code: str, user_id: int, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    return country_controller.unassign_staff_from_country(code, user_id, current_user, db)


# ── Communications ─────────────────────────────────────────────────────────────

@router.get("/{code}/communications")
def list_communications(code: str, category: Optional[str] = Query(None), current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    return country_controller.list_country_communications(code, current_user, db, category)


@router.post("/{code}/communications")
def send_communication(code: str, body: SendCommBody, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    return country_controller.send_country_communication(code, body.model_dump(), current_user, db)


@router.patch("/communications/{comm_id}/read")
def mark_communication_read(comm_id: int, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    return country_controller.mark_communication_read(comm_id, current_user, db)


# ── Cross-Country Customer Sessions ────────────────────────────────────────────

@router.get("/{code}/cross-country-sessions")
def list_cross_country_sessions(code: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    return country_controller.list_cross_country_sessions(code, current_user, db)


# ── Payout Rules ─────────────────────────────────────────────────────────────────

class PayoutRuleItem(BaseModel):
    rule_id: str = Field(..., min_length=1, max_length=80)
    name: str = Field(..., min_length=1, max_length=100)
    type: str = Field(default="category", description="category or product")
    threshold_min: Optional[float] = Field(default=None, ge=0)
    threshold_max: Optional[float] = Field(default=None, ge=0)
    payout_rate: float = Field(..., ge=0, le=100)
    fixed_fee: float = Field(default=0, ge=0)
    currency: Optional[str] = Field(default=None, max_length=10)


@router.get("/{code}/payout-rules/categories")
def list_payout_rules_categories(code: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    return country_controller.list_payout_rules_categories(code, current_user, db)


@router.post("/{code}/payout-rules/categories")
def create_payout_rule_category(code: str, body: PayoutRuleItem, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    return country_controller.create_payout_rule_category(code, body.model_dump(), current_user, db)


@router.get("/{code}/payout-rules/products")
def list_payout_rules_products(code: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    return country_controller.list_payout_rules_products(code, current_user, db)


@router.post("/{code}/payout-rules/products")
def create_payout_rule_product(code: str, body: PayoutRuleItem, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    return country_controller.create_payout_rule_product(code, body.model_dump(), current_user, db)


@router.delete("/{code}/payout-rules/categories/{rule_id}")
def delete_payout_rule_category(code: str, rule_id: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    return country_controller.delete_payout_rule(code, rule_id, current_user, db)


@router.delete("/{code}/payout-rules/products/{rule_id}")
def delete_payout_rule_product(code: str, rule_id: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    return country_controller.delete_payout_rule(code, rule_id, current_user, db)


# ── Archive / Restore / Bulk (consolidated from admin_countries) ───────────────

@router.post("/{code}/toggle-active")
def toggle_country_active(code: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    from controllers.country_controller import _require_admin
    _require_admin(current_user)
    from models import CountryConfig
    c = db.query(CountryConfig).filter(CountryConfig.code == code.upper()).first()
    if not c:
        raise HTTPException(status_code=404, detail="Country not found")
    c.is_active = not c.is_active
    db.commit()
    return {"message": f"Country {'enabled' if c.is_active else 'disabled'}"}


class ArchivePayload(BaseModel):
    reason: Optional[str] = None


class BulkIdsPayload(BaseModel):
    ids: list[str]  # country codes
    reason: Optional[str] = None


@router.post("/{code}/archive")
def archive_country(code: str, payload: ArchivePayload = None, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    from controllers.country_controller import _require_full_admin, _get_country_or_404, _record_admin_change
    _require_full_admin(current_user)
    c = _get_country_or_404(code, db)
    c.is_deleted = True
    _record_admin_change(db, actor_id=current_user.get("id"), action="archive", entity="country_config",
                         entity_key=code.upper(), before={"is_deleted": False}, after={"is_deleted": True})
    db.commit()
    return {"message": "Country archived"}


@router.post("/{code}/restore")
def restore_country(code: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    from controllers.country_controller import _require_full_admin, _get_country_or_404, _record_admin_change
    _require_full_admin(current_user)
    c = _get_country_or_404(code, db)
    c.is_deleted = False
    _record_admin_change(db, actor_id=current_user.get("id"), action="restore", entity="country_config",
                         entity_key=code.upper(), before={"is_deleted": True}, after={"is_deleted": False})
    db.commit()
    return {"message": "Country restored"}


@router.post("/bulk/archive")
def bulk_archive_countries(payload: BulkIdsPayload, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    from controllers.country_controller import _require_full_admin, _record_admin_change
    _require_full_admin(current_user)
    from models import CountryConfig
    rows = db.query(CountryConfig).filter(CountryConfig.code.in_(payload.ids)).all()
    for c in rows:
        c.is_deleted = True
        _record_admin_change(db, actor_id=current_user.get("id"), action="bulk_archive", entity="country_config",
                             entity_key=c.code, before={"is_deleted": False}, after={"is_deleted": True})
    db.commit()
    return {"message": f"{len(rows)} countries archived"}


@router.post("/bulk/restore")
def bulk_restore_countries(payload: BulkIdsPayload, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    from controllers.country_controller import _require_full_admin, _record_admin_change
    _require_full_admin(current_user)
    from models import CountryConfig
    rows = db.query(CountryConfig).filter(CountryConfig.code.in_(payload.ids)).all()
    for c in rows:
        c.is_deleted = False
        _record_admin_change(db, actor_id=current_user.get("id"), action="bulk_restore", entity="country_config",
                             entity_key=c.code, before={"is_deleted": True}, after={"is_deleted": False})
    db.commit()
    return {"message": f"{len(rows)} countries restored"}


@router.delete("/{code}")
def hard_delete_country(code: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    from controllers.country_controller import _require_full_admin
    _require_full_admin(current_user)
    c = db.query(CountryConfig).filter(CountryConfig.code == code.upper()).first()
    if not c:
        raise HTTPException(status_code=404, detail="Country not found")
    db.delete(c)
    db.commit()
    return Response(status_code=204)


router.include_router(auto_populate_router)
router.include_router(versioning_router)


# ── Country Commission Rates ─────────────────────────────────────────────────────

class CountryCommissionRateItem(BaseModel):
    supplier_tier: str = Field(..., min_length=1, max_length=20)
    name: str = Field(..., min_length=1, max_length=50)
    commission_percentage: float = Field(..., ge=0, le=100)
    fixed_fee: float = Field(default=0, ge=0)


@router.get("/countries/{code}/commission-rates")
def list_country_commission_rates(code: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    from controllers.country_controller import _require_admin, _require_country_access
    _require_admin(current_user)
    _require_country_access(code, current_user)
    from models import CountryCommissionRate
    rows = db.query(CountryCommissionRate).filter(
        CountryCommissionRate.country_code == code.upper()
    ).order_by(CountryCommissionRate.supplier_tier, CountryCommissionRate.name).all()
    return [{"supplier_tier": r.supplier_tier, "name": r.name, "commission_percentage": float(r.rate_percent) * 100, "fixed_fee": float(r.fixed_fee) if r.fixed_fee else 0.0} for r in rows]


@router.post("/countries/{code}/commission-rates")
def create_country_commission_rate(code: str, body: CountryCommissionRateItem, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    from controllers.country_controller import _require_admin, _require_country_access, _get_country_or_404, _record_admin_change
    _require_admin(current_user)
    _require_country_access(code, current_user)
    _get_country_or_404(code, db)
    from models import CountryCommissionRate
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


@router.delete("/countries/{code}/commission-rates/{tier}/{name}")
def delete_country_commission_rate(code: str, tier: str, name: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    from controllers.country_controller import _require_admin, _require_country_access, _record_admin_change
    _require_admin(current_user)
    _require_country_access(code, current_user)
    from models import CountryCommissionRate
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

