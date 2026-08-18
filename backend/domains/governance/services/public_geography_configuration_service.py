from __future__ import annotations
from decimal import Decimal
from typing import Any, Optional
from fastapi import Depends, HTTPException, Query, Request, Response
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from rbac import get_current_user
from domains.country.services.country_controller import country_controller
from domains.country.services.country_controller import _require_admin
from modules.employee.routers import employees_controller as ctrl
from infrastructure.database.database import get_db

from domains.country.services.country_config_admin_service import add_country_city as svc_add_country_city
from domains.country.services.country_config_admin_service import archive_country as svc_archive_country
from domains.country.services.country_config_admin_service import bulk_archive_countries as svc_bulk_archive_countries
from domains.country.services.country_config_admin_service import bulk_restore_countries as svc_bulk_restore_countries
from domains.country.services.country_config_admin_service import create_country_commission_rate as svc_create_country_commission_rate
from domains.country.services.country_config_admin_service import create_feature_flag as svc_create_feature_flag
from domains.country.services.country_config_admin_service import delete_country_commission_rate as svc_delete_country_commission_rate
from domains.country.services.country_config_admin_service import delete_country_city as svc_delete_country_city
from domains.country.services.country_config_admin_service import delete_feature_flag as svc_delete_feature_flag
from domains.country.services.country_config_admin_service import hard_delete_country as svc_hard_delete_country
from domains.country.services.country_config_admin_service import list_country_commission_rates as svc_list_country_commission_rates
from domains.country.services.country_config_admin_service import patch_country_city as svc_patch_country_city
from domains.country.services.country_config_admin_service import restore_country as svc_restore_country
from domains.country.services.country_config_admin_service import toggle_country_active as svc_toggle_country_active
from domains.country.services.country_config_admin_service import update_feature_flag as svc_update_feature_flag
from middleware.country_context import get_country_scope as _get_country_scope


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
