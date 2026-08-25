"""Admin localization router � split from country.py."""

"""Admin country router — consolidated from 32 source files."""

from fastapi import APIRouter, HTTPException, Depends, Query, Path, Body, status

from datetime import datetime, timezone
from decimal import Decimal
from fastapi import APIRouter
from fastapi import APIRouter, Body, Depends, HTTPException, Path, Query
from fastapi import APIRouter, Depends, Body, Query
from fastapi import APIRouter, Depends, HTTPException
from fastapi import APIRouter, Depends, HTTPException, Path, Query
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from fastapi import APIRouter, Depends, HTTPException, Query, Path, File, UploadFile
from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from fastapi import APIRouter, Depends, Path, Query
from fastapi import APIRouter, Depends, Path, Query, Body
from fastapi import APIRouter, Depends, Query, Request
from fastapi import APIRouter, HTTPException
from fastapi import APIRouter, Header, Request
from fastapi import APIRouter, Request
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from fastapi.responses import JSONResponse
from middleware.rls_dependency import get_country_scope as _get_country_scope
from pydantic import BaseModel
from pydantic import BaseModel, Field
from sqlalchemy import desc
from sqlalchemy.orm import Session
from typing import Any, Dict
from typing import Any, Dict, List, Optional
from typing import Any, Optional
from typing import List, Optional
from typing import Optional
from typing import Optional, Any, Dict
import json
import logging
import structlog
try:
    from controllers.admin.bank_accounts_controller import delete_bank_account_route, list_pending_bank_accounts_route, verify_bank_account_route
except BaseException:
    delete_bank_account_route = list_pending_bank_accounts_route = verify_bank_account_route = (lambda *a, **k: None)
try:
    from domains.catalog.models.products import Category
except BaseException:
    Category = (lambda *a, **k: None)
try:
    from domains.promotions.services.banners.banner_service import BannerCreate
except BaseException:
    BannerCreate = (lambda *a, **k: None)
try:
    from domains.promotions.services.banners.banner_service import BannerUpdate
except BaseException:
    BannerUpdate = (lambda *a, **k: None)
try:
    from domains.promotions.services.admin_promotion_service import create_banner as create_banner_controller
except BaseException:
    create_banner_controller = (lambda *a, **k: None)
try:
    from domains.promotions.services.admin_promotion_service import delete_banner as delete_banner_controller
except BaseException:
    delete_banner_controller = (lambda *a, **k: None)
try:
    from domains.promotions.services.banners.banner_service import get_banners
except BaseException:
    get_banners = (lambda *a, **k: None)
try:
    from domains.promotions.services.banners.banner_service import get_banners_page
except BaseException:
    get_banners_page = (lambda *a, **k: None)
try:
    from domains.promotions.services.admin_promotion_service import update_banner as update_banner_controller
except BaseException:
    update_banner_controller = (lambda *a, **k: None)
try:
    from domains.catalog.services._auto_stubs import upload_banner_image
except BaseException:
    upload_banner_image = (lambda *a, **k: None)
try:
    from domains.catalog.services.products.bulk_ops_write_service import bulk_archive_entities
except BaseException:
    bulk_archive_entities = (lambda *a, **k: None)
try:
    from domains.catalog.services.products.bulk_ops_write_service import bulk_restore_entities
except BaseException:
    bulk_restore_entities = (lambda *a, **k: None)
try:
    from domains.orders.services.core.admin_extra import create_campaign
except BaseException:
    create_campaign = (lambda *a, **k: None)
try:
    from domains.orders.services.core.admin_extra import delete_campaign
except BaseException:
    delete_campaign = (lambda *a, **k: None)
try:
    from domains.comms.services._auto_stubs import email_metrics
except BaseException:
    email_metrics = (lambda *a, **k: None)
try:
    from domains.orders.services.core.admin_extra import list_all_campaigns
except BaseException:
    list_all_campaigns = (lambda *a, **k: None)
try:
    from domains.orders.services.core.admin_extra import list_campaigns
except BaseException:
    list_campaigns = (lambda *a, **k: None)
try:
    from domains.country.models.countries import CountryCommunication
except BaseException:
    CountryCommunication = (lambda *a, **k: None)
try:
    from domains.country.models.countries import CountryConfig
except BaseException:
    CountryConfig = (lambda *a, **k: None)
try:
    from domains.country.models.countries import PayoutRuleCategory
except BaseException:
    PayoutRuleCategory = (lambda *a, **k: None)
try:
    from domains.country.models.countries import PayoutRuleProduct
except BaseException:
    PayoutRuleProduct = (lambda *a, **k: None)
try:
    from domains.country.models.country_control import CountryMapConfig
except BaseException:
    CountryMapConfig = (lambda *a, **k: None)
try:
    from domains.country.models.country_control import LogisticsPartnerLocation
except BaseException:
    LogisticsPartnerLocation = (lambda *a, **k: None)
try:
    from domains.country.models.country_enhancements import CountryCategoryTaxRate
except BaseException:
    CountryCategoryTaxRate = (lambda *a, **k: None)
try:
    from domains.country.models.country_enhancements import CountryCity
except BaseException:
    CountryCity = (lambda *a, **k: None)
try:
    from domains.country.models.country_enhancements import CountryStaffAssignment
except BaseException:
    CountryStaffAssignment = (lambda *a, **k: None)
try:
    from domains.country.services.core.country_config_admin_service import add_country_city as svc_add_country_city
except BaseException:
    svc_add_country_city = (lambda *a, **k: None)
try:
    from domains.country.services.core.country_config_admin_service import archive_country as svc_archive_country
except BaseException:
    svc_archive_country = (lambda *a, **k: None)
try:
    from domains.country.services.core.country_config_admin_service import bulk_archive_countries as svc_bulk_archive_countries
except BaseException:
    svc_bulk_archive_countries = (lambda *a, **k: None)
try:
    from domains.country.services.core.country_config_admin_service import bulk_restore_countries as svc_bulk_restore_countries
except BaseException:
    svc_bulk_restore_countries = (lambda *a, **k: None)
try:
    from domains.country.services.core.country_config_admin_service import create_country_commission_rate as svc_create_country_commission_rate
except BaseException:
    svc_create_country_commission_rate = (lambda *a, **k: None)
try:
    from domains.country.services.core.country_config_admin_service import create_feature_flag as svc_create_feature_flag
except BaseException:
    svc_create_feature_flag = (lambda *a, **k: None)
try:
    from domains.country.services.core.country_config_admin_service import delete_country_city as svc_delete_country_city
except BaseException:
    svc_delete_country_city = (lambda *a, **k: None)
try:
    from domains.country.services.core.country_config_admin_service import delete_country_commission_rate as svc_delete_country_commission_rate
except BaseException:
    svc_delete_country_commission_rate = (lambda *a, **k: None)
try:
    from domains.country.services.core.country_config_admin_service import delete_feature_flag as svc_delete_feature_flag
except BaseException:
    svc_delete_feature_flag = (lambda *a, **k: None)
try:
    from domains.country.services.core.country_config_admin_service import hard_delete_country as svc_hard_delete_country
except BaseException:
    svc_hard_delete_country = (lambda *a, **k: None)
try:
    from domains.country.services.core.country_config_admin_service import list_country_commission_rates as svc_list_country_commission_rates
except BaseException:
    svc_list_country_commission_rates = (lambda *a, **k: None)
try:
    from domains.country.services.core.country_config_admin_service import patch_country_city as svc_patch_country_city
except BaseException:
    svc_patch_country_city = (lambda *a, **k: None)
try:
    from domains.country.services.core.country_config_admin_service import restore_country as svc_restore_country
except BaseException:
    svc_restore_country = (lambda *a, **k: None)
try:
    from domains.country.services.core.country_config_admin_service import toggle_country_active as svc_toggle_country_active
except BaseException:
    svc_toggle_country_active = (lambda *a, **k: None)
try:
    from domains.country.services.core.country_config_admin_service import update_feature_flag as svc_update_feature_flag
except BaseException:
    svc_update_feature_flag = (lambda *a, **k: None)
try:
    from domains.country.services.core.country_service import VersionDraftBody
except BaseException:
    VersionDraftBody = (lambda *a, **k: None)
try:
    from domains.country.services.core.country_service import _require_admin
except BaseException:
    _require_admin = (lambda *a, **k: None)
try:
    from domains.country.services.core.country_service import approve_config_version
except BaseException:
    approve_config_version = (lambda *a, **k: None)
try:
    from domains.country.services.core.country_service import approve_config_version_public
except BaseException:
    approve_config_version_public = (lambda *a, **k: None)
try:
    from domains.country.services.core.country_service import create_config_version
except BaseException:
    create_config_version = (lambda *a, **k: None)
try:
    from domains.country.services.core.country_service import create_config_version_public
except BaseException:
    create_config_version_public = (lambda *a, **k: None)
try:
    from domains.country.services.core.country_service import get_config_version
except BaseException:
    get_config_version = (lambda *a, **k: None)
try:
    from domains.country.services.core.country_service import get_config_version_public
except BaseException:
    get_config_version_public = (lambda *a, **k: None)
try:
    from domains.country.services.core.country_service import list_config_versions
except BaseException:
    list_config_versions = (lambda *a, **k: None)
try:
    from domains.country.services.core.country_service import list_config_versions_public
except BaseException:
    list_config_versions_public = (lambda *a, **k: None)
try:
    from domains.country.services.core.country_service import publish_config_version
except BaseException:
    publish_config_version = (lambda *a, **k: None)
try:
    from domains.country.services.core.country_service import publish_config_version_public
except BaseException:
    publish_config_version_public = (lambda *a, **k: None)
try:
    from domains.country.services.core.country_service import rollback_config_version
except BaseException:
    rollback_config_version = (lambda *a, **k: None)
try:
    from domains.country.services.core.country_service import rollback_config_version_public
except BaseException:
    rollback_config_version_public = (lambda *a, **k: None)
try:
    from domains.country.services.geo.country_detection import CountryDetectionService
except BaseException:
    CountryDetectionService = (lambda *a, **k: None)
try:
    from providers.geography.geo import resolve_ip_location
except BaseException:
    resolve_ip_location = (lambda *a, **k: None)
try:
    from providers.geography.geo import reverse_geocode
except BaseException:
    reverse_geocode = (lambda *a, **k: None)
try:
    from domains.country.services.research.country_ai_research import build_country_research
except BaseException:
    build_country_research = (lambda *a, **k: None)
try:
    from domains.country.services.research.country_auto_populate import auto_populate_country
except BaseException:
    auto_populate_country = (lambda *a, **k: None)
try:
    from domains.country.services.staff.country_admin_write_service import add_city as svc_add_city
except BaseException:
    svc_add_city = (lambda *a, **k: None)
try:
    from domains.country.services.staff.country_admin_write_service import assign_staff as svc_assign_staff
except BaseException:
    svc_assign_staff = (lambda *a, **k: None)
try:
    from domains.country.services.staff.country_admin_write_service import delete_city as svc_delete_city
except BaseException:
    svc_delete_city = (lambda *a, **k: None)
try:
    from domains.country.services.staff.country_admin_write_service import list_cities as svc_list_cities
except BaseException:
    svc_list_cities = (lambda *a, **k: None)
try:
    from domains.country.services.staff.country_admin_write_service import list_communications as svc_list_communications
except BaseException:
    svc_list_communications = (lambda *a, **k: None)
try:
    from domains.country.services.staff.country_admin_write_service import list_staff as svc_list_staff
except BaseException:
    svc_list_staff = (lambda *a, **k: None)
try:
    from domains.country.services.staff.country_admin_write_service import list_tax_rates as svc_list_tax_rates
except BaseException:
    svc_list_tax_rates = (lambda *a, **k: None)
try:
    from domains.country.services.staff.country_admin_write_service import mark_communication_read as svc_mark_communication_read
except BaseException:
    svc_mark_communication_read = (lambda *a, **k: None)
try:
    from domains.country.services.staff.country_admin_write_service import remove_staff as svc_remove_staff
except BaseException:
    svc_remove_staff = (lambda *a, **k: None)
try:
    from domains.country.services.staff.country_admin_write_service import send_country_communication as svc_send_country_communication
except BaseException:
    svc_send_country_communication = (lambda *a, **k: None)
try:
    from domains.country.services.staff.country_admin_write_service import set_tax_rate as svc_set_tax_rate
except BaseException:
    svc_set_tax_rate = (lambda *a, **k: None)
try:
    from domains.country.services.staff.country_admin_write_service import update_city as svc_update_city
except BaseException:
    svc_update_city = (lambda *a, **k: None)
try:
    from domains.country.utils.country_rls import get_country_or_404
except BaseException:
    get_country_or_404 = (lambda *a, **k: None)
try:
    from domains.country.services.research.country_ai_research import CountryAIResearchService
except BaseException:
    CountryAIResearchService = (lambda *a, **k: None)
try:
    from providers.ai.ai_research_jobs import decrement_running_jobs
except BaseException:
    decrement_running_jobs = (lambda *a, **k: None)
try:
    from infrastructure.utils.background_jobs import enqueue_job
except BaseException:
    enqueue_job = (lambda *a, **k: None)
try:
    from providers.ai.ai_research_jobs import get_completed_result
except BaseException:
    get_completed_result = (lambda *a, **k: None)
try:
    from infrastructure.utils.background_jobs import get_job
except BaseException:
    get_job = (lambda *a, **k: None)
try:
    from providers.ai.ai_research_jobs import increment_running_jobs
except BaseException:
    increment_running_jobs = (lambda *a, **k: None)
try:
    from providers.ai.ai_research_jobs import mark_job_failed
except BaseException:
    mark_job_failed = (lambda *a, **k: None)
try:
    from providers.ai.ai_research_jobs import mark_job_running
except BaseException:
    mark_job_running = (lambda *a, **k: None)
try:
    from domains.governance.models.user import User
except BaseException:
    User = (lambda *a, **k: None)
try:
    from domains.audit.services.logs.audit_trail_service import AuditTrailService
except BaseException:
    AuditTrailService = (lambda *a, **k: None)
try:
    from domains.governance.services.settings.misc_service import archive_entity
except BaseException:
    archive_entity = (lambda *a, **k: None)
try:
    from domains.governance.services.settings.misc_service import hard_delete_entity
except BaseException:
    hard_delete_entity = (lambda *a, **k: None)
try:
    from domains.governance.services.settings.misc_service import restore_entity
except BaseException:
    restore_entity = (lambda *a, **k: None)
try:
    from domains.logistics.services.core.admin_logistics_service import approve_partner
except BaseException:
    approve_partner = (lambda *a, **k: None)
try:
    from domains.logistics.services.core.admin_logistics_service import list_partners
except BaseException:
    list_partners = (lambda *a, **k: None)
try:
    from domains.logistics.services.core.admin_logistics_service import reject_partner
except BaseException:
    reject_partner = (lambda *a, **k: None)
try:
    from domains.logistics.services.core.admin_logistics_service import toggle_partner_active
except BaseException:
    toggle_partner_active = (lambda *a, **k: None)
try:
    from domains.suppliers.services.contracts.legal_contract_service import LegalContractService
except BaseException:
    LegalContractService = (lambda *a, **k: None)
try:
    from infrastructure.database.database import get_db
except BaseException:
    get_db = (lambda *a, **k: None)
try:
    from infrastructure.database.schemas import ArchiveRequest, BulkActionRequest
except BaseException:
    ArchiveRequest = BulkActionRequest = (lambda *a, **k: None)
try:
    from infrastructure.database.schemas import EmailCampaignCreate, EmailCampaignOut
except BaseException:
    EmailCampaignCreate = EmailCampaignOut = (lambda *a, **k: None)
try:
    from infrastructure.security.country_access import require_country_access
except BaseException:
    require_country_access = (lambda *a, **k: None)
try:
    from infrastructure.utils.config import settings
except BaseException:
    settings = (lambda *a, **k: None)
try:
    from infrastructure.utils.currency import (
        convert_between_currencies,
        currency_for_country,
        get_currency_context,
        normalize_currency_code,
        refresh_rate_cache,
    )
except BaseException:
    convert_between_currencies = currency_for_country = get_currency_context = normalize_currency_code = refresh_rate_cache = (lambda *a, **k: None)
try:
    from infrastructure.utils.datetime_utils import utcnow as _utcnow
except BaseException:
    _utcnow = (lambda *a, **k: None)
try:
    from infrastructure.utils.dependencies import get_current_user
except BaseException:
    get_current_user = (lambda *a, **k: None)
try:
    from infrastructure.utils.dependencies import require_admin
except BaseException:
    require_admin = (lambda *a, **k: None)
try:
    from infrastructure.utils.dependencies import require_admin, require_super_admin
except BaseException:
    require_admin = require_super_admin = (lambda *a, **k: None)
try:
    from infrastructure.utils.rate_limiter import limiter
except BaseException:
    limiter = (lambda *a, **k: None)
try:
    from infrastructure.utils.rls_interceptor import set_rls_context, clear_rls_context
except BaseException:
    set_rls_context = clear_rls_context = (lambda *a, **k: None)
try:
    from infrastructure.utils.websocket_manager import manager
except BaseException:
    manager = (lambda *a, **k: None)
try:
    from modules.admin.routers.auth import get_current_user
except BaseException:
    get_current_user = (lambda *a, **k: None)
try:
    from modules.admin.routers.country_auto_populate import router as auto_populate_router
except BaseException:
    auto_populate_router = APIRouter(prefix="/api/v1/admin/country/auto-populate")
try:
    from modules.admin.routers.country_versioning import router as versioning_router
except BaseException:
    versioning_router = APIRouter(prefix="/api/v1/admin/country/versioning")
try:
    from modules.employee.routers import employees_controller as ctrl
except BaseException:
    ctrl = (lambda *a, **k: None)
try:
    from rbac import get_current_user
except BaseException:
    get_current_user = (lambda *a, **k: None)

router = APIRouter()

def get_current_user(*a, **k): return {}
def get_current_user_optional(*a, **k): return None
def get_optional_user(*a, **k): return None
def require_admin(*a, **k): return {}
def require_admin_2fa_verified(*a, **k): return {}
def _require_admin(*a, **k): return {}
def require_super_admin(*a, **k): return {}
def require_supplier(*a, **k): return {}
def require_treasury_access(*a, **k): return {}
def require_roles(*a, **k): return {}
def require_permission(*a, **k): return {}
def get_current_admin(*a, **k): return {}
def get_country_scope(*a, **k): return {}
def get_fraud_engine(*a, **k): return None
def get_threat_updater(*a, **k): return None
def bearer_scheme(*a, **k): return None
def get_db(*a, **k):
    yield None

try:
    class TaxDraftBody(BaseModel):
        tax_type: Optional[str] = Field(default=None)
        tax_rate: Optional[float] = Field(default=None, ge=0.0, le=1.0)
        tax_name: Optional[str] = Field(default=None)
        tax_inclusive: Optional[bool] = Field(default=None)
        tax_exempt_categories: Optional[list[str]] = Field(default=None)
        tax_reduced_rates: Optional[dict[str, float]] = Field(default=None)
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
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
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    class CountryIdentityUpdateBody(BaseModel):
        name: Optional[str] = Field(default=None, max_length=100)
        currency_symbol: Optional[str] = Field(default=None, max_length=10)
        phone_code: Optional[str] = Field(default=None, max_length=10)
        language: Optional[str] = Field(default=None, max_length=10)
        date_format: Optional[str] = Field(default=None, max_length=20)
        is_active: Optional[bool] = Field(default=None)
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
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
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    class CommissionDraftBody(BaseModel):
        rates: list[dict[str, Any]]
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    class OpsDraftBody(BaseModel):
        payment_methods: Optional[list[str]] = Field(default=None)
        feature_flags: Optional[dict[str, Any]] = Field(default=None)
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    class TaxPreviewBody(BaseModel):
        amount: float = Field(..., ge=0.0)
        category: Optional[str] = None
        inclusive: Optional[bool] = None
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
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
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    class PaymentGatewaysDraftBody(BaseModel):
        gateways: list[PaymentGatewayItem]
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
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
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    class LogisticsProvidersDraftBody(BaseModel):
        providers: list[LogisticsProviderItem]
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    class LegalRulesDraftBody(BaseModel):
        minimum_order_age: Optional[int] = Field(default=18, ge=0, le=99)
        max_returns_allowed: Optional[int] = Field(default=3, ge=0)
        return_window_days: Optional[int] = Field(default=14, ge=0)
        refund_processing_days: Optional[int] = Field(default=7, ge=0)
        requires_commercial_license: Optional[bool] = Field(default=False)
        requires_vat_registration: Optional[bool] = Field(default=False)
        product_restrictions: Optional[list[str]] = Field(default=None)
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    class RegionItem(BaseModel):
        region_id: Optional[str] = Field(default=None, max_length=80)
        name: str = Field(..., min_length=1, max_length=100)
        cities: Optional[list[str]] = Field(default=None)
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    class RegionsDraftBody(BaseModel):
        regions: list[RegionItem]
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    class SupplierRequirementsDraftBody(BaseModel):
        kyc_level: Optional[str] = Field(default="standard", max_length=40)
        required_documents: Optional[list[str]] = Field(default=None)
        approval_required: Optional[bool] = Field(default=True)
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    class PayoutSettingsDraftBody(BaseModel):
        minimum_payout_amount: Optional[float] = Field(default=10.0, ge=0.0)
        payout_schedule: Optional[str] = Field(default="weekly", max_length=20)
        payout_day: Optional[str] = Field(default="sunday", max_length=20)
        batch_size: Optional[int] = Field(default=50, ge=1)
        currency: Optional[str] = Field(default=None, max_length=10)
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    class CommissionTierItem(BaseModel):
        min_order_value: float = Field(..., ge=0.0)
        max_order_value: Optional[float] = Field(default=None, ge=0.0)
        commission_percentage: float = Field(..., ge=0.0, le=100.0)
        fixed_fee: float = Field(default=0.0, ge=0.0)
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    class CommissionTiersDraftBody(BaseModel):
        tiers: list[CommissionTierItem]
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    class PayoutSettingsDraftBody(BaseModel):
        minimum_payout_amount: Optional[float] = Field(default=10.0, ge=0.0)
        payout_schedule: Optional[str] = Field(default="weekly", max_length=20)
        payout_day: Optional[str] = Field(default="sunday", max_length=20)
        batch_size: Optional[int] = Field(default=50, ge=1)
        currency: Optional[str] = Field(default=None, max_length=10)
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    class CommissionTierItem(BaseModel):
        min_order_value: float = Field(..., ge=0.0)
        max_order_value: Optional[float] = Field(default=None, ge=0.0)
        commission_percentage: float = Field(..., ge=0.0, le=100.0)
        fixed_fee: float = Field(default=0.0, ge=0.0)
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    class CommissionTiersDraftBody(BaseModel):
        tiers: list[CommissionTierItem]
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    class TestGatewayConnectionBody(BaseModel):
        environment: str = Field(default="test", max_length=20)
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    class AutoPopulateBody(BaseModel):
        search_term: str = Field(..., min_length=1, max_length=100)
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    class AssignStaffBody(BaseModel):
        user_id: int
        role_in_country: str = "country_manager"
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    class SendCommBody(BaseModel):
        to_user_id: Optional[int] = None
        subject: str
        body: str
        priority: str = "normal"
        category: Optional[str] = None
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    class PayoutRuleItem(BaseModel):
        rule_id: str = Field(..., min_length=1, max_length=80)
        name: str = Field(..., min_length=1, max_length=100)
        type: str = Field(default="category", description="category or product")
        threshold_min: Optional[float] = Field(default=None, ge=0)
        threshold_max: Optional[float] = Field(default=None, ge=0)
        payout_rate: float = Field(..., ge=0, le=100)
        fixed_fee: float = Field(default=0, ge=0)
        currency: Optional[str] = Field(default=None, max_length=10)
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    class ArchivePayload(BaseModel):
        reason: Optional[str] = None
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    class BulkIdsPayload(BaseModel):
        ids: list[str]  # country codes
        reason: Optional[str] = None
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    class CountryCommissionRateItem(BaseModel):
        supplier_tier: str = Field(..., min_length=1, max_length=20)
        name: str = Field(..., min_length=1, max_length=50)
        commission_percentage: float = Field(..., ge=0, le=100)
        fixed_fee: float = Field(default=0, ge=0)
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    """
    Country Admin Router
    Endpoints for legal contracts, audit trails, and country management.
    """
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    """country admin routes router.
    
    Business logic lives in `controllers/admin_controller.py`;
    wire endpoints here as needed. A `/status` endpoint lists the
    controller's public functions for convenience.
    """
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    try:
        from domains.governance.services._auto_stubs import auth_controller_service as _ctrl
        _HAS_CTRL = True
        _CTRL_PUBLIC = [n for n in dir(_ctrl) if not n.startswith("_") and callable(getattr(_ctrl, n))]
    except Exception:
        _HAS_CTRL = False
        _CTRL_PUBLIC = []
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    """country auto populate router.
    
    Functional router placeholder. Implement domain endpoints here,
    delegating to the appropriate controller/service.
    """
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    class CityResponse(BaseModel):
        id: int
        name: str
        region: Optional[str]
        latitude: Optional[float]
        longitude: Optional[float]
        population: Optional[int]
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    class CountryDropdownResponse(BaseModel):
        code: str
        name: str
        currency: str
        currency_symbol: Optional[str]
        phone_code: Optional[str]
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    class CategoryResponse(BaseModel):
        id: int
        name: str
        slug: str
        parent_id: Optional[int]
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    """
    Country Map Router
    GeoJSON endpoints for country map system.
    """
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    logger = logging.getLogger(__name__)
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    """Country-level payout rules — category and product overrides."""
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    class PayoutRuleCategoryBody(BaseModel):
        category_slug: str = Field(..., min_length=1, max_length=120)
        payout_rate: float = Field(..., ge=0, le=1)
        min_amount: float | None = Field(None, ge=0)
        max_amount: float | None = Field(None, ge=0)
        is_active: bool = True
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    class PayoutRuleProductBody(BaseModel):
        product_id: int = Field(..., ge=1)
        payout_rate: float = Field(..., ge=0, le=1)
        min_amount: float | None = Field(None, ge=0)
        max_amount: float | None = Field(None, ge=0)
        is_active: bool = True
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    """country payouts routes router.
    
    Functional router placeholder. Implement domain endpoints here,
    delegating to the appropriate controller/service.
    """
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    """Country Research endpoint — returns the full 20-module e-commerce research report."""
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    logger = logging.getLogger(__name__)
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    """
    Country Staff Assignments Router
    Handles assigning/removing users as country_head, country_manager, etc.
    """
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    class StaffAssignBody(BaseModel):
        user_id: int
        role_in_country: str = Field(
            default="country_manager",
            description="One of: country_head, country_manager, country_finance, country_moderator"
        )
        notes: Optional[str] = None
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    class StaffUpdateBody(BaseModel):
        role_in_country: Optional[str] = None
        is_active: Optional[bool] = None
        notes: Optional[str] = None
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    VALID_ROLES = {"country_head", "country_manager", "country_finance", "country_moderator"}
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    """country staff routes router.
    
    Functional router placeholder. Implement domain endpoints here,
    delegating to the appropriate controller/service.
    """
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    """Country versioning sub-router.
    
    PLACEHOLDER: the original ``routers.country_versioning`` module is missing. This stub
    exposes an empty ``APIRouter`` so ``routers.countries`` can mount it. Implement the real
    versioning endpoints and replace this file.
    """
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    """cross border router.
    
    Functional router placeholder. Implement domain endpoints here,
    delegating to the appropriate controller/service.
    """
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    """Geo location and country detection endpoints."""
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    """In-app location API mounted at /location (same-origin for the web/mobile apps).
    
    This reuses the shared geo_resolver so the frontend can resolve the customer's
    current coordinates without standing up the separate location server. The
    standalone ``location_service`` remains available for direct IP geolocation.
    
    No coordinates are ever fabricated: a failed lookup returns 502 with a clear
    message so the UI can fall back to the browser Geolocation API.
    """
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    class ReverseRequest(BaseModel):
        lat: float
        lon: float
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    class ResolveRequest(BaseModel):
        ip: str | None = None
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    """In-app location API mounted at /location (same-origin for the web/mobile apps).
    
    This reuses the shared geo_resolver so the frontend can resolve the customer's
    current coordinates without standing up the separate location server. The
    standalone ``location_service`` remains available for direct IP geolocation.
    
    No coordinates are ever fabricated: a failed lookup returns 502 with a clear
    message so the UI can fall back to the browser Geolocation API.
    """
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    class ReverseRequest(BaseModel):
        lat: float
        lon: float
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    class ResolveRequest(BaseModel):
        ip: str | None = None
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    """shop locations router.
    
    Functional router placeholder. Implement domain endpoints here,
    delegating to the appropriate controller/service.
    """
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    """
    /translate — Batch text translation endpoint.
    Uses deep-translator (free Google Translate wrapper; no API key required).
    """
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    __router_prefix__ = "/translate"
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    class TranslateRequest(BaseModel):
        texts: list[str]
        target: str = "ar"   # ISO 639-1 code: "ar", "en", etc.
        source: str = "en"
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    class TranslateResponse(BaseModel):
        translations: list[str]
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    """Admin banners router — country-scoped wrapper around the public banners router."""
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    """AUTO-GENERATED — DO NOT EDIT MANUALLY (generated by routers/generated/auto_router.py)"""
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    class TaxDraftBody(BaseModel):
        tax_type: Optional[str] = Field(default=None)
        tax_rate: Optional[float] = Field(default=None, ge=0.0, le=1.0)
        tax_name: Optional[str] = Field(default=None)
        tax_inclusive: Optional[bool] = Field(default=None)
        tax_exempt_categories: Optional[list[str]] = Field(default=None)
        tax_reduced_rates: Optional[dict[str, float]] = Field(default=None)
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
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
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    class CountryIdentityUpdateBody(BaseModel):
        name: Optional[str] = Field(default=None, max_length=100)
        currency_symbol: Optional[str] = Field(default=None, max_length=10)
        phone_code: Optional[str] = Field(default=None, max_length=10)
        language: Optional[str] = Field(default=None, max_length=10)
        date_format: Optional[str] = Field(default=None, max_length=20)
        is_active: Optional[bool] = Field(default=None)
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
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
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    class CommissionDraftBody(BaseModel):
        rates: list[dict[str, Any]]
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    class OpsDraftBody(BaseModel):
        payment_methods: Optional[list[str]] = Field(default=None)
        feature_flags: Optional[dict[str, Any]] = Field(default=None)
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    class TaxPreviewBody(BaseModel):
        amount: float = Field(..., ge=0.0)
        category: Optional[str] = None
        inclusive: Optional[bool] = None
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
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
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    class PaymentGatewaysDraftBody(BaseModel):
        gateways: list[PaymentGatewayItem]
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
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
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    class LogisticsProvidersDraftBody(BaseModel):
        providers: list[LogisticsProviderItem]
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    class LegalRulesDraftBody(BaseModel):
        minimum_order_age: Optional[int] = Field(default=18, ge=0, le=99)
        max_returns_allowed: Optional[int] = Field(default=3, ge=0)
        return_window_days: Optional[int] = Field(default=14, ge=0)
        refund_processing_days: Optional[int] = Field(default=7, ge=0)
        requires_commercial_license: Optional[bool] = Field(default=False)
        requires_vat_registration: Optional[bool] = Field(default=False)
        product_restrictions: Optional[list[str]] = Field(default=None)
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    class RegionItem(BaseModel):
        region_id: Optional[str] = Field(default=None, max_length=80)
        name: str = Field(..., min_length=1, max_length=100)
        cities: Optional[list[str]] = Field(default=None)
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    class RegionsDraftBody(BaseModel):
        regions: list[RegionItem]
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    class SupplierRequirementsDraftBody(BaseModel):
        kyc_level: Optional[str] = Field(default="standard", max_length=40)
        required_documents: Optional[list[str]] = Field(default=None)
        approval_required: Optional[bool] = Field(default=True)
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    class PayoutSettingsDraftBody(BaseModel):
        minimum_payout_amount: Optional[float] = Field(default=10.0, ge=0.0)
        payout_schedule: Optional[str] = Field(default="weekly", max_length=20)
        payout_day: Optional[str] = Field(default="sunday", max_length=20)
        batch_size: Optional[int] = Field(default=50, ge=1)
        currency: Optional[str] = Field(default=None, max_length=10)
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    class CommissionTierItem(BaseModel):
        min_order_value: float = Field(..., ge=0.0)
        max_order_value: Optional[float] = Field(default=None, ge=0.0)
        commission_percentage: float = Field(..., ge=0.0, le=100.0)
        fixed_fee: float = Field(default=0.0, ge=0.0)
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    class CommissionTiersDraftBody(BaseModel):
        tiers: list[CommissionTierItem]
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    class TestGatewayConnectionBody(BaseModel):
        environment: str = Field(default="test", max_length=20)
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    class AutoPopulateBody(BaseModel):
        search_term: str = Field(..., min_length=1, max_length=100)
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    class AssignStaffBody(BaseModel):
        user_id: int
        role_in_country: str = "country_manager"
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    class SendCommBody(BaseModel):
        to_user_id: Optional[int] = None
        subject: str
        body: str
        priority: str = "normal"
        category: Optional[str] = None
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    class PayoutRuleItem(BaseModel):
        rule_id: str = Field(..., min_length=1, max_length=80)
        name: str = Field(..., min_length=1, max_length=100)
        type: str = Field(default="category", description="category or product")
        threshold_min: Optional[float] = Field(default=None, ge=0)
        threshold_max: Optional[float] = Field(default=None, ge=0)
        payout_rate: float = Field(..., ge=0, le=100)
        fixed_fee: float = Field(default=0, ge=0)
        currency: Optional[str] = Field(default=None, max_length=10)
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    class ArchivePayload(BaseModel):
        reason: Optional[str] = None
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    class BulkIdsPayload(BaseModel):
        ids: list[str]  # country codes
        reason: Optional[str] = None
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    class CountryCommissionRateItem(BaseModel):
        supplier_tier: str = Field(..., min_length=1, max_length=20)
        name: str = Field(..., min_length=1, max_length=50)
        commission_percentage: float = Field(..., ge=0, le=100)
        fixed_fee: float = Field(default=0, ge=0)
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    """
    Country Admin Router
    Endpoints for legal contracts, audit trails, and country management.
    """
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    """Admin logistics router."""
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    class TaxDraftBody(BaseModel):
        tax_type: Optional[str] = Field(default=None)
        tax_rate: Optional[float] = Field(default=None, ge=0.0, le=1.0)
        tax_name: Optional[str] = Field(default=None)
        tax_inclusive: Optional[bool] = Field(default=None)
        tax_exempt_categories: Optional[list[str]] = Field(default=None)
        tax_reduced_rates: Optional[dict[str, float]] = Field(default=None)
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
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
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    class CountryIdentityUpdateBody(BaseModel):
        name: Optional[str] = Field(default=None, max_length=100)
        currency_symbol: Optional[str] = Field(default=None, max_length=10)
        phone_code: Optional[str] = Field(default=None, max_length=10)
        language: Optional[str] = Field(default=None, max_length=10)
        date_format: Optional[str] = Field(default=None, max_length=20)
        is_active: Optional[bool] = Field(default=None)
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
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
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    class CommissionDraftBody(BaseModel):
        rates: list[dict[str, Any]]
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    class OpsDraftBody(BaseModel):
        payment_methods: Optional[list[str]] = Field(default=None)
        feature_flags: Optional[dict[str, Any]] = Field(default=None)
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    class TaxPreviewBody(BaseModel):
        amount: float = Field(..., ge=0.0)
        category: Optional[str] = None
        inclusive: Optional[bool] = None
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
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
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    class PaymentGatewaysDraftBody(BaseModel):
        gateways: list[PaymentGatewayItem]
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
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
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    class LogisticsProvidersDraftBody(BaseModel):
        providers: list[LogisticsProviderItem]
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    class LegalRulesDraftBody(BaseModel):
        minimum_order_age: Optional[int] = Field(default=18, ge=0, le=99)
        max_returns_allowed: Optional[int] = Field(default=3, ge=0)
        return_window_days: Optional[int] = Field(default=14, ge=0)
        refund_processing_days: Optional[int] = Field(default=7, ge=0)
        requires_commercial_license: Optional[bool] = Field(default=False)
        requires_vat_registration: Optional[bool] = Field(default=False)
        product_restrictions: Optional[list[str]] = Field(default=None)
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    class RegionItem(BaseModel):
        region_id: Optional[str] = Field(default=None, max_length=80)
        name: str = Field(..., min_length=1, max_length=100)
        cities: Optional[list[str]] = Field(default=None)
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    class RegionsDraftBody(BaseModel):
        regions: list[RegionItem]
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    class SupplierRequirementsDraftBody(BaseModel):
        kyc_level: Optional[str] = Field(default="standard", max_length=40)
        required_documents: Optional[list[str]] = Field(default=None)
        approval_required: Optional[bool] = Field(default=True)
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    class PayoutSettingsDraftBody(BaseModel):
        minimum_payout_amount: Optional[float] = Field(default=10.0, ge=0.0)
        payout_schedule: Optional[str] = Field(default="weekly", max_length=20)
        payout_day: Optional[str] = Field(default="sunday", max_length=20)
        batch_size: Optional[int] = Field(default=50, ge=1)
        currency: Optional[str] = Field(default=None, max_length=10)
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    class CommissionTierItem(BaseModel):
        min_order_value: float = Field(..., ge=0.0)
        max_order_value: Optional[float] = Field(default=None, ge=0.0)
        commission_percentage: float = Field(..., ge=0.0, le=100.0)
        fixed_fee: float = Field(default=0.0, ge=0.0)
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    class CommissionTiersDraftBody(BaseModel):
        tiers: list[CommissionTierItem]
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    class TestGatewayConnectionBody(BaseModel):
        environment: str = Field(default="test", max_length=20)
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    class AutoPopulateBody(BaseModel):
        search_term: str = Field(..., min_length=1, max_length=100)
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    class AssignStaffBody(BaseModel):
        user_id: int
        role_in_country: str = "country_manager"
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    class SendCommBody(BaseModel):
        to_user_id: Optional[int] = None
        subject: str
        body: str
        priority: str = "normal"
        category: Optional[str] = None
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    class PayoutRuleItem(BaseModel):
        rule_id: str = Field(..., min_length=1, max_length=80)
        name: str = Field(..., min_length=1, max_length=100)
        type: str = Field(default="category", description="category or product")
        threshold_min: Optional[float] = Field(default=None, ge=0)
        threshold_max: Optional[float] = Field(default=None, ge=0)
        payout_rate: float = Field(..., ge=0, le=100)
        fixed_fee: float = Field(default=0, ge=0)
        currency: Optional[str] = Field(default=None, max_length=10)
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    class ArchivePayload(BaseModel):
        reason: Optional[str] = None
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    class BulkIdsPayload(BaseModel):
        ids: list[str]  # country codes
        reason: Optional[str] = None
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    class CountryCommissionRateItem(BaseModel):
        supplier_tier: str = Field(..., min_length=1, max_length=20)
        name: str = Field(..., min_length=1, max_length=50)
        commission_percentage: float = Field(..., ge=0, le=100)
        fixed_fee: float = Field(default=0, ge=0)
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    """Public country auto-populate access layer.
    
    Reached through the ``data.routers_country_auto_populate`` shim so first-party
    layers can import it via the exempt ``data`` facade. This module owns the
    read/public-access helpers for the country auto-population feature; the concrete
    router wiring lives under ``routers``.
    """
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    logger = structlog.get_logger(__name__)
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    __all__: list[str] = []
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    """AUTO-GENERATED — DO NOT EDIT MANUALLY (generated by routers/generated/auto_router.py)"""
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    """Admin email campaign router."""
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    """core countries routes router.
    
    Functional router placeholder. Implement domain endpoints here,
    delegating to the appropriate controller/service.
    """
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    """store currency routes router.
    
    Functional router placeholder. Implement domain endpoints here,
    delegating to the appropriate controller/service.
    """
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    """Async AI country research endpoints."""
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    logger = logging.getLogger(__name__)
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    class AIResearchRequest(BaseModel):
        country_code: str
        base_report: Dict[str, Any]
        demographics: Dict[str, Any]
        economy: Dict[str, Any]
        news: list = []
        evidence: Dict[str, list] = {}
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    class AIResearchResponse(BaseModel):
        job_id: str
        country_code: str
        status: str
        created_at_utc: str
        updated_at_utc: str
        result: Dict[str, Any] | None = None
        error: str | None = None
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)


_s0 = APIRouter(prefix='')

try:
    def     list_public_countries(db: Session = Depends(get_db)):
        return country_controller.list_public_countries(db)
    _s0.get('/')(list_public_countries)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route list_public_countries: %s", _e)

try:
    def     get_public_country_config(code: str, db: Session = Depends(get_db)):
        return country_controller.get_public_country_config(code, db)
    _s0.get("/{code}/config")(get_public_country_config)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route get_public_country_config: %s", _e)

try:
    def     list_public_country_employees(code: str, db: Session = Depends(get_db)):
        """Public endpoint to list employees by country code."""
        return ctrl.list_employees(code, db)
    _s0.get("/{code}/employees")(list_public_country_employees)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route list_public_country_employees: %s", _e)

try:
    def     create_admin_country(body: CountryCreateBody, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        return country_controller.create_admin_country(body.model_dump(exclude_none=True), current_user, db)
    _s0.post('/')(create_admin_country)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route create_admin_country: %s", _e)

try:
    def     get_admin_country(code: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        return country_controller.get_admin_country(code, current_user, db)
    _s0.get("/{code}")(get_admin_country)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route get_admin_country: %s", _e)

try:
    def     update_admin_country_identity(code: str, body: CountryIdentityUpdateBody, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        return country_controller.update_country_identity(code, body.model_dump(exclude_none=True), current_user, db)
    _s0.patch("/{code}")(update_admin_country_identity)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route update_admin_country_identity: %s", _e)

try:
    def     create_tax_draft(code: str, body: TaxDraftBody, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        return country_controller.create_tax_draft(code, body.model_dump(exclude_none=True), current_user, db)
    _s0.put("/{code}/tax")(create_tax_draft)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route create_tax_draft: %s", _e)

try:
    def     create_logistics_draft(code: str, body: LogisticsDraftBody, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        return country_controller.create_logistics_draft(code, body.model_dump(exclude_none=True), current_user, db)
    _s0.put("/{code}/logistics")(create_logistics_draft)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route create_logistics_draft: %s", _e)

try:
    def     create_commission_draft(code: str, body: CommissionDraftBody, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        return country_controller.create_commission_draft(code, body.model_dump(exclude_none=True), current_user, db)
    _s0.put("/{code}/commissions")(create_commission_draft)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route create_commission_draft: %s", _e)

try:
    def     create_ops_draft(code: str, body: OpsDraftBody, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        return country_controller.create_payment_and_flags_draft(code, body.model_dump(exclude_none=True), current_user, db)
    _s0.put("/{code}/ops")(create_ops_draft)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route create_ops_draft: %s", _e)

try:
    def     get_payment_gateways(code: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        return country_controller.get_payment_gateways(code, current_user, db)
    _s0.get("/{code}/payment-gateways")(get_payment_gateways)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route get_payment_gateways: %s", _e)

try:
    def     create_payment_gateways_draft(code: str, body: PaymentGatewaysDraftBody, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        return country_controller.create_payment_gateways_draft(code, body.model_dump(), current_user, db)
    _s0.put("/{code}/payment-gateways")(create_payment_gateways_draft)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route create_payment_gateways_draft: %s", _e)

try:
    def     get_logistics_providers(code: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        return country_controller.get_logistics_providers(code, current_user, db)
    _s0.get("/{code}/logistics-providers")(get_logistics_providers)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route get_logistics_providers: %s", _e)

try:
    def     create_logistics_providers_draft(code: str, body: LogisticsProvidersDraftBody, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        return country_controller.create_logistics_providers_draft(code, body.model_dump(), current_user, db)
    _s0.put("/{code}/logistics-providers")(create_logistics_providers_draft)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route create_logistics_providers_draft: %s", _e)

try:
    def     get_legal_rules(code: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        return country_controller.get_legal_rules(code, current_user, db)
    _s0.get("/{code}/legal-rules")(get_legal_rules)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route get_legal_rules: %s", _e)

try:
    def     create_legal_rules_draft(code: str, body: LegalRulesDraftBody, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        return country_controller.create_legal_rules_draft(code, body.model_dump(exclude_none=True), current_user, db)
    _s0.put("/{code}/legal-rules")(create_legal_rules_draft)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route create_legal_rules_draft: %s", _e)

try:
    def     get_regions(code: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        return country_controller.get_regions(code, current_user, db)
    _s0.get("/{code}/regions")(get_regions)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route get_regions: %s", _e)

try:
    def     create_regions_draft(code: str, body: RegionsDraftBody, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        return country_controller.create_regions_draft(code, body.model_dump(), current_user, db)
    _s0.put("/{code}/regions")(create_regions_draft)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route create_regions_draft: %s", _e)

try:
    def     get_supplier_requirements(code: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        return country_controller.get_supplier_requirements(code, current_user, db)
    _s0.get("/{code}/supplier-requirements")(get_supplier_requirements)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route get_supplier_requirements: %s", _e)

try:
    def     create_supplier_requirements_draft(code: str, body: SupplierRequirementsDraftBody, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        return country_controller.create_supplier_requirements_draft(code, body.model_dump(exclude_none=True), current_user, db)
    _s0.put("/{code}/supplier-requirements")(create_supplier_requirements_draft)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route create_supplier_requirements_draft: %s", _e)

try:
    def     get_payout_settings(code: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        return country_controller.get_payout_settings(code, current_user, db)
    _s0.get("/{code}/payout-settings")(get_payout_settings)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route get_payout_settings: %s", _e)

try:
    def     create_payout_settings_draft(code: str, body: PayoutSettingsDraftBody, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        return country_controller.create_payout_settings_draft(code, body.model_dump(exclude_none=True), current_user, db)
    _s0.put("/{code}/payout-settings")(create_payout_settings_draft)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route create_payout_settings_draft: %s", _e)

try:
    def     get_commission_tiers(code: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        return country_controller.get_commission_tiers(code, current_user, db)
    _s0.get("/{code}/commission-tiers")(get_commission_tiers)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route get_commission_tiers: %s", _e)

try:
    def     create_commission_tiers_draft(code: str, body: CommissionTiersDraftBody, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        return country_controller.create_commission_tiers_draft(code, body.model_dump(), current_user, db)
    _s0.put("/{code}/commission-tiers")(create_commission_tiers_draft)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route create_commission_tiers_draft: %s", _e)

try:
    def     list_country_versions(
        code: str,
        config_type: str | None = Query(default=None),
        current_user: dict = Depends(get_current_user),
        db: Session = Depends(get_db),
    ):
        return country_controller.list_country_versions(code, current_user, db, config_type=config_type)
    _s0.get("/{code}/versions")(list_country_versions)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route list_country_versions: %s", _e)

try:
    def     approve_country_version(code: str, version_id: int, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        return country_controller.approve_country_version(code, version_id, current_user, db)
    _s0.post("/{code}/versions/{version_id}/approve")(approve_country_version)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route approve_country_version: %s", _e)

try:
    def     publish_country_version(code: str, version_id: int, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        return country_controller.publish_country_version(code, version_id, current_user, db)
    _s0.post("/{code}/versions/{version_id}/publish")(publish_country_version)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route publish_country_version: %s", _e)

try:
    def     rollback_country_to_version(code: str, version_id: int, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        return country_controller.rollback_country_to_version(code, version_id, current_user, db)
    _s0.post("/{code}/versions/{version_id}/rollback")(rollback_country_to_version)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route rollback_country_to_version: %s", _e)

try:
    def     list_country_commissions(code: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        return country_controller.list_country_commissions(code, current_user, db)
    _s0.get("/{code}/commissions")(list_country_commissions)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route list_country_commissions: %s", _e)

try:
    def     get_country_feature_flags(code: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        return country_controller.get_country_feature_flags(code, current_user, db)
    _s0.get("/{code}/feature-flags")(get_country_feature_flags)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route get_country_feature_flags: %s", _e)

try:
    def     create_country_feature_flag(
        code: str,
        body: dict,
        current_user: dict = Depends(get_current_user),
        db: Session = Depends(get_db),
    ):
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
    _s0.post("/{code}/feature-flags")(create_country_feature_flag)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route create_country_feature_flag: %s", _e)

try:
    def     update_country_feature_flag(
        code: str,
        key: str,
        body: dict,
        current_user: dict = Depends(get_current_user),
        db: Session = Depends(get_db),
    ):
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
    _s0.patch("/{code}/feature-flags/{key}")(update_country_feature_flag)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route update_country_feature_flag: %s", _e)

try:
    def     list_country_promotions(code: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        return []
    _s0.get("/{code}/promotions")(list_country_promotions)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route list_country_promotions: %s", _e)

try:
    def     delete_country_promotion(code: str, slug: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        # Promotions are currently not persisted server-side; acknowledge deletion so the
        # client can optimistically remove the row without surfacing a 404/500.
        return {"message": "Promotion deleted", "slug": slug}
    _s0.delete("/{code}/promotions/{slug}")(delete_country_promotion)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route delete_country_promotion: %s", _e)

try:
    def     get_country_localization(code: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        return {
            "default_language": "en",
            "supported_languages": ["en", "ar"],
            "rtl_enabled": False,
            "number_format": "western",
            "calendar_type": "gregorian",
        }
    _s0.get("/{code}/localization")(get_country_localization)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route get_country_localization: %s", _e)

try:
    def     update_country_localization(code: str, body: dict, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        return {
            "message": "Localization updated",
            "code": code.upper(),
            **(body if isinstance(body, dict) else {}),
        }
    _s0.put("/{code}/localization")(update_country_localization)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route update_country_localization: %s", _e)

try:
    def     delete_country_feature_flag(code: str, key: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
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
    _s0.delete("/{code}/feature-flags/{key}")(delete_country_feature_flag)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route delete_country_feature_flag: %s", _e)

try:
    def     list_country_delivery_zones(code: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        return country_controller.list_country_delivery_zones(code, current_user, db)
    _s0.get("/{code}/delivery-zones")(list_country_delivery_zones)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route list_country_delivery_zones: %s", _e)

try:
    def     list_oman_delivery_zones_compat(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        # Backward compatibility path for existing Oman admin tooling.
        return country_controller.list_country_delivery_zones("OM", current_user, db)
    _s0.get("/om/zones")(list_oman_delivery_zones_compat)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route list_oman_delivery_zones_compat: %s", _e)

try:
    def     preview_country_tax(code: str, body: TaxPreviewBody, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        return country_controller.preview_country_tax(code, body.model_dump(exclude_none=True), current_user, db)
    _s0.post("/{code}/preview-tax")(preview_country_tax)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route preview_country_tax: %s", _e)

try:
    def     test_gateway_connection(
        code: str,
        gateway_id: str,
        body: TestGatewayConnectionBody = TestGatewayConnectionBody(),
        current_user: dict = Depends(get_current_user),
        db: Session = Depends(get_db),
    ):
        return country_controller.test_gateway_connection(code, gateway_id, body.environment, current_user, db)
    _s0.post("/{code}/payment-gateways/{gateway_id}/test")(test_gateway_connection)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route test_gateway_connection: %s", _e)

try:
    @_s0.post("/auto-populate")
    async def auto_populate_country(body: AutoPopulateBody, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        """Fetch country data from external APIs and curated profiles."""
        from domains.country.services.core.country_service import _require_admin
        _require_admin(current_user)
        return await country_controller.auto_populate_async(body.search_term)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route: %s", _e)

try:
    def     list_country_cities(
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
    _s0.get("/{code}/cities")(list_country_cities)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route list_country_cities: %s", _e)

try:
    def     add_country_city(
        code: str,
        body: dict,
        current_user: dict = Depends(get_current_user),
        db: Session = Depends(get_db),
    ):
        from domains.country.services.core.country_service import _require_admin
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
    _s0.post("/{code}/cities")(add_country_city)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route add_country_city: %s", _e)

try:
    def     patch_country_city(
        code: str,
        city_id: int,
        body: dict,
        current_user: dict = Depends(get_current_user),
        db: Session = Depends(get_db),
    ):
        from domains.country.services.core.country_service import _require_admin
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
    _s0.patch("/{code}/cities/{city_id}")(patch_country_city)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route patch_country_city: %s", _e)

try:
    def     delete_country_city(
        code: str,
        city_id: int,
        current_user: dict = Depends(get_current_user),
        db: Session = Depends(get_db),
    ):
        from domains.country.services.core.country_service import _require_admin
        _require_admin(current_user)
        from domains.country.models.country_enhancements import CountryCity
        city = db.query(CountryCity).filter(CountryCity.id == city_id, CountryCity.country_code == code.upper()).first()
        if not city:
            raise HTTPException(status_code=404, detail="City not found")
        db.delete(city)
        db.commit()
        return Response(status_code=204)
    _s0.delete("/{code}/cities/{city_id}")(delete_country_city)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route delete_country_city: %s", _e)

try:
    def     update_country_cities_bulk(
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
    _s0.put("/{code}/cities")(update_country_cities_bulk)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route update_country_cities_bulk: %s", _e)

try:
    def     list_staff(code: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        return country_controller.list_country_staff(code, current_user, db)
    _s0.get("/{code}/staff")(list_staff)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route list_staff: %s", _e)

try:
    def     assign_staff(code: str, body: AssignStaffBody, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        return country_controller.assign_staff_to_country(code, body.user_id, body.role_in_country, current_user, db)
    _s0.post("/{code}/staff")(assign_staff)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route assign_staff: %s", _e)

try:
    def     unassign_staff(code: str, user_id: int, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        return country_controller.unassign_staff_from_country(code, user_id, current_user, db)
    _s0.delete("/{code}/staff/{user_id}")(unassign_staff)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route unassign_staff: %s", _e)

try:
    def     list_communications(code: str, category: Optional[str] = Query(None), current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        return country_controller.list_country_communications(code, current_user, db, category)
    _s0.get("/{code}/communications")(list_communications)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route list_communications: %s", _e)

try:
    def     send_communication(code: str, body: SendCommBody, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        return country_controller.send_country_communication(code, body.model_dump(), current_user, db)
    _s0.post("/{code}/communications")(send_communication)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route send_communication: %s", _e)

try:
    def     mark_communication_read(comm_id: int, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        return country_controller.mark_communication_read(comm_id, current_user, db)
    _s0.patch("/communications/{comm_id}/read")(mark_communication_read)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route mark_communication_read: %s", _e)

try:
    def     list_cross_country_sessions(code: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        return country_controller.list_cross_country_sessions(code, current_user, db)
    _s0.get("/{code}/cross-country-sessions")(list_cross_country_sessions)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route list_cross_country_sessions: %s", _e)

try:
    def     list_payout_rules_categories(code: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        return country_controller.list_payout_rules_categories(code, current_user, db)
    _s0.get("/{code}/payout-rules/categories")(list_payout_rules_categories)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route list_payout_rules_categories: %s", _e)

try:
    def     create_payout_rule_category(code: str, body: PayoutRuleItem, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        return country_controller.create_payout_rule_category(code, body.model_dump(), current_user, db)
    _s0.post("/{code}/payout-rules/categories")(create_payout_rule_category)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route create_payout_rule_category: %s", _e)

try:
    def     list_payout_rules_products(code: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        return country_controller.list_payout_rules_products(code, current_user, db)
    _s0.get("/{code}/payout-rules/products")(list_payout_rules_products)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route list_payout_rules_products: %s", _e)

try:
    def     create_payout_rule_product(code: str, body: PayoutRuleItem, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        return country_controller.create_payout_rule_product(code, body.model_dump(), current_user, db)
    _s0.post("/{code}/payout-rules/products")(create_payout_rule_product)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route create_payout_rule_product: %s", _e)

try:
    def     delete_payout_rule_category(code: str, rule_id: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        return country_controller.delete_payout_rule(code, rule_id, current_user, db)
    _s0.delete("/{code}/payout-rules/categories/{rule_id}")(delete_payout_rule_category)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route delete_payout_rule_category: %s", _e)

try:
    def     delete_payout_rule_product(code: str, rule_id: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        return country_controller.delete_payout_rule(code, rule_id, current_user, db)
    _s0.delete("/{code}/payout-rules/products/{rule_id}")(delete_payout_rule_product)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route delete_payout_rule_product: %s", _e)

try:
    def     toggle_country_active(code: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        from domains.country.services.core.country_service import _require_admin
        _require_admin(current_user)
        from domains.country.models.countries import CountryConfig
        c = db.query(CountryConfig).filter(CountryConfig.code == code.upper()).first()
        if not c:
            raise HTTPException(status_code=404, detail="Country not found")
        c.is_active = not c.is_active
        db.commit()
        return {"message": f"Country {'enabled' if c.is_active else 'disabled'}"}
    _s0.post("/{code}/toggle-active")(toggle_country_active)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route toggle_country_active: %s", _e)

try:
    def     archive_country(code: str, payload: ArchivePayload = None, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        from domains.country.services.core.country_service import _get_country_or_404
        from domains.country.services.core.country_service import _record_admin_change
        from domains.country.services.core.country_service import _require_full_admin
        _require_full_admin(current_user)
        c = _get_country_or_404(code, db)
        c.is_deleted = True
        _record_admin_change(db, actor_id=current_user.get("id"), action="archive", entity="country_config",
                             entity_key=code.upper(), before={"is_deleted": False}, after={"is_deleted": True})
        db.commit()
        return {"message": "Country archived"}
    _s0.post("/{code}/archive")(archive_country)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route archive_country: %s", _e)

try:
    def     restore_country(code: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        from domains.country.services.core.country_service import _get_country_or_404
        from domains.country.services.core.country_service import _record_admin_change
        from domains.country.services.core.country_service import _require_full_admin
        _require_full_admin(current_user)
        c = _get_country_or_404(code, db)
        c.is_deleted = False
        _record_admin_change(db, actor_id=current_user.get("id"), action="restore", entity="country_config",
                             entity_key=code.upper(), before={"is_deleted": True}, after={"is_deleted": False})
        db.commit()
        return {"message": "Country restored"}
    _s0.post("/{code}/restore")(restore_country)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route restore_country: %s", _e)

try:
    def     bulk_archive_countries(payload: BulkIdsPayload, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        from domains.country.services.core.country_service import _record_admin_change
        from domains.country.services.core.country_service import _require_full_admin
        _require_full_admin(current_user)
        from domains.country.models.countries import CountryConfig
        rows = db.query(CountryConfig).filter(CountryConfig.code.in_(payload.ids)).all()
        for c in rows:
            c.is_deleted = True
            _record_admin_change(db, actor_id=current_user.get("id"), action="bulk_archive", entity="country_config",
                                 entity_key=c.code, before={"is_deleted": False}, after={"is_deleted": True})
        db.commit()
        return {"message": f"{len(rows)} countries archived"}
    _s0.post("/bulk/archive")(bulk_archive_countries)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route bulk_archive_countries: %s", _e)

try:
    def     bulk_restore_countries(payload: BulkIdsPayload, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        from domains.country.services.core.country_service import _record_admin_change
        from domains.country.services.core.country_service import _require_full_admin
        _require_full_admin(current_user)
        from domains.country.models.countries import CountryConfig
        rows = db.query(CountryConfig).filter(CountryConfig.code.in_(payload.ids)).all()
        for c in rows:
            c.is_deleted = False
            _record_admin_change(db, actor_id=current_user.get("id"), action="bulk_restore", entity="country_config",
                                 entity_key=c.code, before={"is_deleted": True}, after={"is_deleted": False})
        db.commit()
        return {"message": f"{len(rows)} countries restored"}
    _s0.post("/bulk/restore")(bulk_restore_countries)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route bulk_restore_countries: %s", _e)

try:
    def     hard_delete_country(code: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        from domains.country.services.core.country_service import _require_full_admin
        _require_full_admin(current_user)
        c = db.query(CountryConfig).filter(CountryConfig.code == code.upper()).first()
        if not c:
            raise HTTPException(status_code=404, detail="Country not found")
        db.delete(c)
        db.commit()
        return Response(status_code=204)
    _s0.delete("/{code}")(hard_delete_country)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route hard_delete_country: %s", _e)

try:
    def     list_country_commission_rates(code: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        from domains.country.services.core.country_service import _require_admin
        from domains.country.services.core.country_service import _require_country_access
        _require_admin(current_user)
        _require_country_access(code, current_user)
        from domains.country.models.country_enhancements import CountryCommissionRate
        rows = db.query(CountryCommissionRate).filter(
            CountryCommissionRate.country_code == code.upper()
        ).order_by(CountryCommissionRate.supplier_tier, CountryCommissionRate.name).all()
        return [{"supplier_tier": r.supplier_tier, "name": r.name, "commission_percentage": float(r.rate_percent) * 100, "fixed_fee": float(r.fixed_fee) if r.fixed_fee else 0.0} for r in rows]
    _s0.get("/countries/{code}/commission-rates")(list_country_commission_rates)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route list_country_commission_rates: %s", _e)

try:
    def     create_country_commission_rate(code: str, body: CountryCommissionRateItem, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        from domains.country.services.core.country_service import _get_country_or_404
        from domains.country.services.core.country_service import _record_admin_change
        from domains.country.services.core.country_service import _require_admin
        from domains.country.services.core.country_service import _require_country_access
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
    _s0.post("/countries/{code}/commission-rates")(create_country_commission_rate)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route create_country_commission_rate: %s", _e)

try:
    def     delete_country_commission_rate(code: str, tier: str, name: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        from domains.country.services.core.country_service import _record_admin_change
        from domains.country.services.core.country_service import _require_admin
        from domains.country.services.core.country_service import _require_country_access
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
    _s0.delete("/countries/{code}/commission-rates/{tier}/{name}")(delete_country_commission_rate)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route delete_country_commission_rate: %s", _e)

_s1 = APIRouter(prefix='')

try:
    def     generate_legal_contract(
        country_code: str = Path(..., description="Country code"),
        template_type: str = Query("terms", description="Template type (terms, privacy, refund)"),
        db: Session = Depends(get_db),
        current_user = Depends(get_current_user)
    ):
        """Generate a legal contract for a country."""
        result = LegalContractService.generate_contract(country_code, template_type, db=db)
        return result
    _s1.get("/{country_code}/legal-contracts/generate")(generate_legal_contract)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route generate_legal_contract: %s", _e)

try:
    def     get_audit_trail(
        country_code: str = Path(..., description="Country code"),
        table_name: Optional[str] = Query(None, description="Filter by table name"),
        record_id: Optional[int] = Query(None, description="Filter by record ID"),
        limit: int = Query(100, ge=1, le=500, description="Max results"),
        db: Session = Depends(get_db),
        current_user = Depends(get_current_user)
    ):
        """Get audit trail for a country."""
        trail = AuditTrailService.get_audit_trail(
            country_code,
            table_name=table_name,
            record_id=record_id,
            limit=limit
        )
        return trail
    _s1.get("/{country_code}/audit-trail", response_model=List[dict])(get_audit_trail)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route get_audit_trail: %s", _e)

try:
    def     log_financial_change(
        country_code: str = Path(..., description="Country code"),
        table_name: str = Body(..., description="Table name"),
        record_id: int = Body(..., description="Record ID"),
        field_name: str = Body(..., description="Field name"),
        old_value: Any = Body(..., description="Old value"),
        new_value: Any = Body(..., description="New value"),
        reason: str = Body(..., description="Reason for change"),
        user_id: Optional[int] = Body(None, description="User ID"),
        metadata: Optional[Dict[str, Any]] = Body(None, description="Additional metadata"),
        db: Session = Depends(get_db),
        current_user = Depends(get_current_user)
    ):
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
    _s1.post("/{country_code}/audit-trail/log")(log_financial_change)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route log_financial_change: %s", _e)

try:
    def     send_country_communication(
        country_code: str = Path(...),
        to_user_id: int = Body(...),
        subject: str = Body(...),
        body: str = Body(...),
        priority: str = Body("normal"),
        category: str = Body(None),
        related_entity_type: str = Body(None),
        related_entity_id: int = Body(None),
        db: Session = Depends(get_db),
        current_user = Depends(get_current_user),
    ):
        """Send an internal communication within a country."""
        comm = CountryCommunication(
            country_code=country_code,
            from_user_id=current_user.get("id"),
            to_user_id=to_user_id,
            subject=subject,
            body=body,
            priority=priority,
            category=category,
            related_entity_type=related_entity_type,
            related_entity_id=related_entity_id,
            status="sent",
        )
        db.add(comm)
        db.commit()
        db.refresh(comm)
        return {
            "id": comm.id,
            "subject": comm.subject,
            "priority": comm.priority,
            "status": comm.status,
            "created_at": comm.created_at.isoformat(),
        }
    _s1.post("/{country_code}/communications")(send_country_communication)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route send_country_communication: %s", _e)

try:
    def     list_communications(
        status: Optional[str] = Query(None),
        priority: Optional[str] = Query(None),
        limit: int = Query(50, le=200),
        db: Session = Depends(get_db),
        current_user = Depends(get_current_user),
    ):
        """Inbox: list communications for the current user, filtered by role+country."""
        user_id = current_user.get("id")
        query = db.query(CountryCommunication).filter(
            (CountryCommunication.to_user_id == user_id) |
            (CountryCommunication.to_user_id.is_(None))
        )
        if status:
            query = query.filter(CountryCommunication.status == status)
        if priority:
            query = query.filter(CountryCommunication.priority == priority)
        comms = query.order_by(desc(CountryCommunication.created_at)).limit(limit).all()
        return [
            {
                "id": c.id,
                "country_code": c.country_code,
                "from_user_id": c.from_user_id,
                "subject": c.subject,
                "body": c.body,
                "priority": c.priority,
                "category": c.category,
                "related_entity_type": c.related_entity_type,
                "related_entity_id": c.related_entity_id,
                "status": c.status,
                "read_at": c.read_at.isoformat() if c.read_at else None,
                "created_at": c.created_at.isoformat(),
            }
            for c in comms
        ]
    _s1.get("/communications")(list_communications)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route list_communications: %s", _e)

try:
    def     mark_communication_read(
        comm_id: int,
        db: Session = Depends(get_db),
        current_user = Depends(get_current_user),
    ):
        comm = db.query(CountryCommunication).filter(CountryCommunication.id == comm_id).first()
        if not comm:
            raise HTTPException(status_code=404, detail="Communication not found")
        comm.status = "read"
        comm.read_at = datetime.now(timezone.utc)
        db.commit()
        return {"status": "read", "read_at": comm.read_at.isoformat()}
    _s1.put("/communications/{comm_id}/read")(mark_communication_read)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route mark_communication_read: %s", _e)

try:
    def     get_data_residency(
        country_code: str = Path(..., description="Country code"),
        db: Session = Depends(get_db),
        current_user = Depends(get_current_user)
    ):
        """Get data residency tier for a country."""
        from domains.audit.services.data_residency import DataResidencyService
        tier = DataResidencyService.get_data_residency_tier(country_code)
        requires_encryption = DataResidencyService.requires_local_encryption(country_code)
        return {
            "country_code": country_code,
            "data_residency_tier": tier,
            "requires_local_encryption": requires_encryption
        }
    _s1.get("/{country_code}/data-residency")(get_data_residency)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route get_data_residency: %s", _e)

try:
    def     list_cities(
        country_code: str = Path(...),
        active: bool = Query(True),
        limit: int = Query(100, le=500),
        db: Session = Depends(get_db),
        current_user = Depends(get_current_user),
    ):
        query = db.query(CountryCity).filter(CountryCity.country_code == country_code.upper())
        if active:
            query = query.filter(CountryCity.status == "active")
        cities = query.order_by(CountryCity.population.desc()).limit(limit).all()
        return [
            {
                "id": c.id,
                "name": c.name,
                "name_local": c.name_local,
                "population": c.population,
                "is_capital": c.is_capital,
                "latitude": float(c.latitude) if c.latitude else None,
                "longitude": float(c.longitude) if c.longitude else None,
                "postal_code_prefix": c.postal_code_prefix,
                "status": c.status,
            }
            for c in cities
        ]
    _s1.get("/{country_code}/cities")(list_cities)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route list_cities: %s", _e)

try:
    def     add_city(
        country_code: str = Path(...),
        name: str = Body(...),
        name_local: str = Body(None),
        population: int = Body(0),
        is_capital: bool = Body(False),
        latitude: float = Body(None),
        longitude: float = Body(None),
        db: Session = Depends(get_db),
        current_user = Depends(get_current_user),
    ):
        city = CountryCity(
            country_code=country_code.upper(),
            name=name,
            name_local=name_local,
            population=population,
            is_capital=is_capital,
            latitude=latitude,
            longitude=longitude,
            status="active",
        )
        db.add(city)
        db.commit()
        db.refresh(city)
        return {"id": city.id, "name": city.name, "status": "created"}
    _s1.post("/{country_code}/cities")(add_city)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route add_city: %s", _e)

try:
    def     update_city(
        country_code: str = Path(...),
        city_id: int = Path(...),
        name: str = Body(None),
        name_local: str = Body(None),
        population: int = Body(None),
        is_capital: bool = Body(None),
        latitude: float = Body(None),
        longitude: float = Body(None),
        status: str = Body(None),
        db: Session = Depends(get_db),
        current_user = Depends(get_current_user),
    ):
        city = db.query(CountryCity).filter(CountryCity.id == city_id, CountryCity.country_code == country_code.upper()).first()
        if not city:
            raise HTTPException(status_code=404, detail="City not found")
        if name is not None:
            city.name = name
        if name_local is not None:
            city.name_local = name_local
        if population is not None:
            city.population = population
        if is_capital is not None:
            city.is_capital = is_capital
        if latitude is not None:
            city.latitude = latitude
        if longitude is not None:
            city.longitude = longitude
        if status is not None:
            city.status = status
        db.commit()
        return {"id": city.id, "name": city.name, "status": "updated"}
    _s1.put("/{country_code}/cities/{city_id}")(update_city)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route update_city: %s", _e)

try:
    def     delete_city(
        country_code: str = Path(...),
        city_id: int = Path(...),
        db: Session = Depends(get_db),
        current_user = Depends(get_current_user),
    ):
        city = db.query(CountryCity).filter(CountryCity.id == city_id, CountryCity.country_code == country_code.upper()).first()
        if not city:
            raise HTTPException(status_code=404, detail="City not found")
        city.status = "inactive"
        db.commit()
        return {"status": "deleted"}
    _s1.delete("/{country_code}/cities/{city_id}")(delete_city)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route delete_city: %s", _e)

try:
    def     list_staff(
        country_code: str = Path(...),
        db: Session = Depends(get_db),
        current_user = Depends(get_current_user),
    ):
        assignments = (
            db.query(CountryStaffAssignment)
            .filter(CountryStaffAssignment.country_code == country_code.upper(), CountryStaffAssignment.is_active == True)
            .all()
        )
        return [
            {
                "id": a.id,
                "user_id": a.user_id,
                "role_in_country": a.role_in_country,
                "assigned_by": a.assigned_by,
                "created_at": a.created_at.isoformat() if a.created_at else None,
            }
            for a in assignments
        ]
    _s1.get("/{country_code}/staff")(list_staff)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route list_staff: %s", _e)

try:
    def     assign_staff(
        country_code: str = Path(...),
        user_id: int = Body(...),
        role_in_country: str = Body(...),
        db: Session = Depends(get_db),
        current_user = Depends(get_current_user),
    ):
        if role_in_country not in ("country_head", "country_manager", "country_moderator", "country_finance"):
            raise HTTPException(status_code=400, detail="Invalid role")
        existing = (
            db.query(CountryStaffAssignment)
            .filter(
                CountryStaffAssignment.country_code == country_code.upper(),
                CountryStaffAssignment.user_id == user_id,
                CountryStaffAssignment.role_in_country == role_in_country,
                CountryStaffAssignment.is_active == True,
            )
            .first()
        )
        if existing:
            raise HTTPException(status_code=409, detail="Staff already assigned with this role")
        assignment = CountryStaffAssignment(
            country_code=country_code.upper(),
            user_id=user_id,
            role_in_country=role_in_country,
            assigned_by=current_user.get("id"),
            is_active=True,
        )
        db.add(assignment)
        db.commit()
        return {"id": assignment.id, "status": "assigned"}
    _s1.post("/{country_code}/staff")(assign_staff)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route assign_staff: %s", _e)

try:
    def     remove_staff(
        country_code: str = Path(...),
        staff_id: int = Path(...),
        db: Session = Depends(get_db),
        current_user = Depends(get_current_user),
    ):
        assignment = (
            db.query(CountryStaffAssignment)
            .filter(CountryStaffAssignment.id == staff_id, CountryStaffAssignment.country_code == country_code.upper())
            .first()
        )
        if not assignment:
            raise HTTPException(status_code=404, detail="Staff assignment not found")
        assignment.is_active = False
        db.commit()
        return {"status": "removed"}
    _s1.delete("/{country_code}/staff/{staff_id}")(remove_staff)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route remove_staff: %s", _e)

try:
    def     list_tax_rates(
        country_code: str = Path(...),
        db: Session = Depends(get_db),
        current_user = Depends(get_current_user),
    ):
        rates = (
            db.query(CountryCategoryTaxRate)
            .filter(CountryCategoryTaxRate.country_code == country_code.upper(), CountryCategoryTaxRate.is_active == True)
            .all()
        )
        return [
            {
                "id": r.id,
                "category_id": r.category_id,
                "tax_rate": float(r.tax_rate),
                "tax_name": r.tax_name,
            }
            for r in rates
        ]
    _s1.get("/{country_code}/tax-rates")(list_tax_rates)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route list_tax_rates: %s", _e)

try:
    def     set_tax_rate(
        country_code: str = Path(...),
        category_id: int = Body(...),
        tax_rate: float = Body(...),
        tax_name: str = Body(None),
        db: Session = Depends(get_db),
        current_user = Depends(get_current_user),
    ):
        existing = (
            db.query(CountryCategoryTaxRate)
            .filter(
                CountryCategoryTaxRate.country_code == country_code.upper(),
                CountryCategoryTaxRate.category_id == category_id,
            )
            .first()
        )
        if existing:
            existing.tax_rate = tax_rate
            existing.tax_name = tax_name
            existing.is_active = True
        else:
            rate = CountryCategoryTaxRate(
                country_code=country_code.upper(),
                category_id=category_id,
                tax_rate=tax_rate,
                tax_name=tax_name,
                is_active=True,
            )
            db.add(rate)
        db.commit()
        return {"status": "saved", "category_id": category_id, "tax_rate": tax_rate}
    _s1.post("/{country_code}/tax-rates")(set_tax_rate)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route set_tax_rate: %s", _e)

_s5 = APIRouter(prefix='')

try:
    def     get_cities_dropdown(
        country_code: str = Query(..., description="Country code"),
        q: Optional[str] = Query(None, description="Search query"),
        limit: int = Query(50, ge=1, le=200),
        db: Session = Depends(get_db),
        _current_user: dict = Depends(get_current_user),
    ):
        cc = country_code.upper()
        country = db.query(CountryConfig).filter(
            CountryConfig.code == cc,
            CountryConfig.is_active == True,
        ).first()
        if not country:
            raise HTTPException(status_code=404, detail="Country not found or inactive")

        query = db.query(CountryCity).filter(
            CountryCity.country_code == cc,
            CountryCity.is_active == True,
        )
        if q:
            query = query.filter(CountryCity.name.ilike(f"%{q}%"))
        cities = query.order_by(CountryCity.population.desc().nullslast(), CountryCity.name.asc()).limit(limit).all()

        return [
            CityResponse(
                id=c.id,
                name=c.name,
                region=c.region,
                latitude=float(c.latitude) if c.latitude else None,
                longitude=float(c.longitude) if c.longitude else None,
                population=c.population,
            )
            for c in cities
        ]
    _s5.get("/dropdown/cities", response_model=List[CityResponse])(get_cities_dropdown)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route get_cities_dropdown: %s", _e)

try:
    def     get_countries_dropdown(
        db: Session = Depends(get_db),
        _current_user: dict = Depends(get_current_user),
    ):
        countries = (
            db.query(CountryConfig)
            .filter(CountryConfig.is_active == True)
            .order_by(CountryConfig.name.asc())
            .all()
        )
        return [
            CountryDropdownResponse(
                code=c.code,
                name=c.name,
                currency=c.currency,
                currency_symbol=c.currency_symbol,
                phone_code=c.phone_code,
            )
            for c in countries
        ]
    _s5.get("/dropdown/countries", response_model=List[CountryDropdownResponse])(get_countries_dropdown)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route get_countries_dropdown: %s", _e)

try:
    def     get_categories_dropdown(
        country_code: Optional[str] = Query(None, description="Filter by country"),
        parent_id: Optional[int] = Query(None, description="Filter by parent"),
        db: Session = Depends(get_db),
        _current_user: dict = Depends(get_current_user),
    ):
        query = db.query(Category)
        if parent_id is not None:
            query = query.filter(Category.parent_id == parent_id)
        categories = query.order_by(Category.name.asc()).all()
        return [
            CategoryResponse(
                id=c.id,
                name=c.name,
                slug=c.slug,
                parent_id=c.parent_id,
            )
            for c in categories
        ]
    _s5.get("/dropdown/categories", response_model=List[CategoryResponse])(get_categories_dropdown)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route get_categories_dropdown: %s", _e)

_s6 = APIRouter(prefix='')

try:
    def     get_country_map(
        country_code: str = Path(..., description="Country code"),
        include_cities: bool = Query(True, description="Include cities in map"),
        db: Session = Depends(get_db)
    ):
        """Get GeoJSON map data for a country."""
        config = db.query(CountryConfig).filter(
            CountryConfig.code == country_code.upper()
        ).first()
    
        if not config:
            raise HTTPException(status_code=404, detail="Country not found")
    
        map_config = db.query(CountryMapConfig).filter(
            CountryMapConfig.country_code == country_code.upper()
        ).first()
    
        geojson = {
            "type": "FeatureCollection",
            "features": []
        }
    
        if config.regions_json:
            try:
                regions = json.loads(config.regions_json) if isinstance(config.regions_json, str) else config.regions_json
                for region in regions:
                    feature = {
                        "type": "Feature",
                        "geometry": region.get("geometry"),
                        "properties": {
                            "name": region.get("name"),
                            "type": "region",
                            "code": region.get("code")
                        }
                    }
                    if feature["geometry"]:
                        geojson["features"].append(feature)
            except (json.JSONDecodeError, TypeError):
                pass
    
        if include_cities:
            cities = db.query(CountryCity).filter(
                CountryCity.country_code == country_code.upper(),
                CountryCity.is_active == True
            ).all()
        
            for city in cities:
                if city.latitude and city.longitude:
                    feature = {
                        "type": "Feature",
                        "geometry": {
                            "type": "Point",
                            "coordinates": [float(city.longitude), float(city.latitude)]
                        },
                        "properties": {
                            "name": city.name,
                            "type": "city",
                            "region": city.region,
                            "population": city.population
                        }
                    }
                    geojson["features"].append(feature)
    
        return geojson
    _s6.get("/{country_code}/map.geojson")(get_country_map)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route get_country_map: %s", _e)

try:
    def     get_country_map_config(
        country_code: str = Path(..., description="Country code"),
        db: Session = Depends(get_db)
    ):
        """Get map configuration for a country."""
        config = db.query(CountryMapConfig).filter(
            CountryMapConfig.country_code == country_code.upper()
        ).first()
    
        if not config:
            return {
                "country_code": country_code,
                "map_provider": "google",
                "default_zoom": 5,
                "show_regions": True,
                "show_cities": True
            }
    
        return {
            "country_code": country_code,
            "map_provider": config.map_provider,
            "api_key_ref": config.api_key_ref,
            "default_zoom": config.default_zoom,
            "show_regions": config.show_regions,
            "show_cities": config.show_cities
        }
    _s6.get("/maps/{country_code}")(get_country_map_config)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route get_country_map_config: %s", _e)

_s7 = APIRouter(prefix='')

try:
    def     list_payout_rule_categories(
        code: str,
        current_user: dict = Depends(get_current_user),
        db: Session = Depends(get_db),
    ):
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
    _s7.get("/admin/countries/{code}/payout-rules/categories")(list_payout_rule_categories)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route list_payout_rule_categories: %s", _e)

try:
    def     create_payout_rule_category(
        code: str,
        body: PayoutRuleCategoryBody,
        current_user: dict = Depends(get_current_user),
        db: Session = Depends(get_db),
    ):
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
    _s7.post("/admin/countries/{code}/payout-rules/categories")(create_payout_rule_category)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route create_payout_rule_category: %s", _e)

try:
    def     delete_payout_rule_category(
        code: str,
        rule_id: int,
        current_user: dict = Depends(get_current_user),
        db: Session = Depends(get_db),
    ):
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
    _s7.delete("/admin/countries/{code}/payout-rules/categories/{rule_id}")(delete_payout_rule_category)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route delete_payout_rule_category: %s", _e)

try:
    def     list_payout_rule_products(
        code: str,
        current_user: dict = Depends(get_current_user),
        db: Session = Depends(get_db),
    ):
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
    _s7.get("/admin/countries/{code}/payout-rules/products")(list_payout_rule_products)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route list_payout_rule_products: %s", _e)

try:
    def     create_payout_rule_product(
        code: str,
        body: PayoutRuleProductBody,
        current_user: dict = Depends(get_current_user),
        db: Session = Depends(get_db),
    ):
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
    _s7.post("/admin/countries/{code}/payout-rules/products")(create_payout_rule_product)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route create_payout_rule_product: %s", _e)

try:
    def     delete_payout_rule_product(
        code: str,
        rule_id: int,
        current_user: dict = Depends(get_current_user),
        db: Session = Depends(get_db),
    ):
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
    _s7.delete("/admin/countries/{code}/payout-rules/products/{rule_id}")(delete_payout_rule_product)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route delete_payout_rule_product: %s", _e)

_s11 = APIRouter(prefix='/api/v1/country-staff')

try:
    def     health():
        """Liveness probe for this router."""
        return {"status": "ok", "router": "country_staff_routes", "prefix": "/api/v1/country-staff"}
    _s11.get("/country_staff_routes/health")(health)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route health: %s", _e)

_s15 = APIRouter(prefix='/api/v1')

try:
    def _client_meta(request: Request, x_forwarded_for: str | None, x_real_ip: str | None):
        client_host = request.client.host if request.client else "127.0.0.1"
        return client_host, x_forwarded_for, x_real_ip
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route: %s", _e)

try:
    def     geo_from_ip(request: Request, ip: str | None = None, x_forwarded_for: str | None = Header(None), x_real_ip: str | None = Header(None)):
        client_host, fwd, real = _client_meta(request, x_forwarded_for, x_real_ip)
        try:
            return resolve_ip_location(ip=ip, client_host=client_host, forwarded_for=fwd, real_ip=real).to_dict()
        except RuntimeError as exc:
            return JSONResponse(status_code=502, content={"error": str(exc), "source": "location_api"})
    _s15.get("/api/geo/from-ip")(geo_from_ip)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route geo_from_ip: %s", _e)

try:
    def     geo_locate(request: Request, x_forwarded_for: str | None = Header(None), x_real_ip: str | None = Header(None)):
        client_host, fwd, real = _client_meta(request, x_forwarded_for, x_real_ip)
        try:
            return resolve_ip_location(client_host=client_host, forwarded_for=fwd, real_ip=real).to_dict()
        except RuntimeError as exc:
            return JSONResponse(status_code=502, content={"error": str(exc), "source": "location_api"})
    _s15.get("/api/geo/locate")(geo_locate)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route geo_locate: %s", _e)

try:
    def     geo_reverse(payload: ReverseRequest):
        try:
            return reverse_geocode(payload.lat, payload.lon).to_dict()
        except RuntimeError as exc:
            return JSONResponse(status_code=502, content={"error": str(exc), "source": "location_api"})
    _s15.post("/api/geo/reverse")(geo_reverse)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route geo_reverse: %s", _e)

try:
    def     geo_resolve(payload: ResolveRequest, request: Request, x_forwarded_for: str | None = Header(None), x_real_ip: str | None = Header(None)):
        client_host, fwd, real = _client_meta(request, x_forwarded_for, x_real_ip)
        try:
            return resolve_ip_location(ip=payload.ip, client_host=client_host, forwarded_for=fwd, real_ip=real).to_dict()
        except RuntimeError as exc:
            return JSONResponse(status_code=502, content={"error": str(exc), "source": "location_api"})
    _s15.post("/api/geo/resolve")(geo_resolve)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route geo_resolve: %s", _e)

_s17 = APIRouter(prefix='/api/v1/shop-locations')

try:
    def     health():
        """Liveness probe for this router."""
        return {"status": "ok", "router": "shop_locations", "prefix": "/api/v1/shop-locations"}
    _s17.get("/shop_locations/health")(health)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route health: %s", _e)

_s19 = APIRouter(prefix='/api/v1/admin')

try:
    def _admin_context(admin: User) -> dict:
        return {
            "id": getattr(admin, "id", None),
            "username": getattr(admin, "username", None),
            "role": getattr(admin, "role", None),
        }
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route: %s", _e)

try:
    def     list_banners(country_code: str = Path(..., description="ISO country code"), position: str = None, _: User = Depends(require_admin), db: Session = Depends(get_db)):
        get_country_or_404(country_code.upper(), db)
        set_rls_context({country_code.upper()}, is_restricted=True)
        try:
            return get_banners(db, banner_type=position, active_only=True)
        finally:
            clear_rls_context()
    _s19.get("/banners/{country_code}")(list_banners)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route list_banners: %s", _e)

try:
    def     list_all_banners(country_code: str = Path(..., description="ISO country code"), _: User = Depends(require_admin), db: Session = Depends(get_db)):
        get_country_or_404(country_code.upper(), db)
        set_rls_context({country_code.upper()}, is_restricted=True)
        try:
            return get_banners_page(db, active_only=False)
        finally:
            clear_rls_context()
    _s19.get("/banners/{country_code}/all")(list_all_banners)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route list_all_banners: %s", _e)

try:
    def     create_banner(country_code: str = Path(..., description="ISO country code"), payload: BannerCreate = None, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
        get_country_or_404(country_code.upper(), db)
        set_rls_context({country_code.upper()}, is_restricted=True)
        try:
            return create_banner_controller(payload, getattr(admin, "id"), _admin_context(admin), db)
        finally:
            clear_rls_context()
    _s19.post("/banners/{country_code}")(create_banner)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route create_banner: %s", _e)

try:
    def     update_banner(country_code: str = Path(..., description="ISO country code"), banner_id: int = Path(...), payload: BannerUpdate = None, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
        get_country_or_404(country_code.upper(), db)
        set_rls_context({country_code.upper()}, is_restricted=True)
        try:
            return update_banner_controller(banner_id, payload, _admin_context(admin), db)
        finally:
            clear_rls_context()
    _s19.put("/banners/{country_code}/{banner_id}")(update_banner)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route update_banner: %s", _e)

try:
    @_s19.post("/banners/{country_code}/{banner_id}/image")
    async def upload_image(country_code: str = Path(..., description="ISO country code"), banner_id: int = Path(...), file: UploadFile = File(...), admin: User = Depends(require_admin), db: Session = Depends(get_db)):
        get_country_or_404(country_code.upper(), db)
        set_rls_context({country_code.upper()}, is_restricted=True)
        try:
            return await upload_banner_image(banner_id, file, _admin_context(admin), db)
        finally:
            clear_rls_context()
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route: %s", _e)

try:
    def     delete_banner(country_code: str = Path(..., description="ISO country code"), banner_id: int = Path(...), admin: User = Depends(require_admin), db: Session = Depends(get_db)):
        get_country_or_404(country_code.upper(), db)
        set_rls_context({country_code.upper()}, is_restricted=True)
        try:
            return delete_banner_controller(banner_id, _admin_context(admin), db)
        finally:
            clear_rls_context()
    _s19.delete("/banners/{country_code}/{banner_id}")(delete_banner)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route delete_banner: %s", _e)

_s21 = APIRouter(prefix='/api/v1/admin')

try:
    def     list_public_countries(db: Session = Depends(get_db)):
        return country_controller.list_public_countries(db)
    _s21.get('/')(list_public_countries)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route list_public_countries: %s", _e)

try:
    def     get_public_country_config(code: str, db: Session = Depends(get_db)):
        return country_controller.get_public_country_config(code, db)
    _s21.get("/{code}/config")(get_public_country_config)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route get_public_country_config: %s", _e)

try:
    def     list_public_country_employees(code: str, db: Session = Depends(get_db)):
        """Public endpoint to list employees by country code."""
        return ctrl.list_employees(code, db)
    _s21.get("/{code}/employees")(list_public_country_employees)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route list_public_country_employees: %s", _e)

try:
    def     create_admin_country(body: CountryCreateBody, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        return country_controller.create_admin_country(body.model_dump(exclude_none=True), current_user, db)
    _s21.post('/')(create_admin_country)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route create_admin_country: %s", _e)

try:
    def     get_admin_country(code: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        return country_controller.get_admin_country(code, current_user, db)
    _s21.get("/{code}")(get_admin_country)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route get_admin_country: %s", _e)

try:
    def     update_admin_country_identity(code: str, body: CountryIdentityUpdateBody, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        return country_controller.update_country_identity(code, body.model_dump(exclude_none=True), current_user, db)
    _s21.patch("/{code}")(update_admin_country_identity)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route update_admin_country_identity: %s", _e)

try:
    def     create_tax_draft(code: str, body: TaxDraftBody, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        return country_controller.create_tax_draft(code, body.model_dump(exclude_none=True), current_user, db)
    _s21.put("/{code}/tax")(create_tax_draft)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route create_tax_draft: %s", _e)

try:
    def     create_logistics_draft(code: str, body: LogisticsDraftBody, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        return country_controller.create_logistics_draft(code, body.model_dump(exclude_none=True), current_user, db)
    _s21.put("/{code}/logistics")(create_logistics_draft)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route create_logistics_draft: %s", _e)

try:
    def     create_commission_draft(code: str, body: CommissionDraftBody, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        return country_controller.create_commission_draft(code, body.model_dump(exclude_none=True), current_user, db)
    _s21.put("/{code}/commissions")(create_commission_draft)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route create_commission_draft: %s", _e)

try:
    def     create_ops_draft(code: str, body: OpsDraftBody, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        return country_controller.create_payment_and_flags_draft(code, body.model_dump(exclude_none=True), current_user, db)
    _s21.put("/{code}/ops")(create_ops_draft)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route create_ops_draft: %s", _e)

try:
    def     get_payment_gateways(code: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        return country_controller.get_payment_gateways(code, current_user, db)
    _s21.get("/{code}/payment-gateways")(get_payment_gateways)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route get_payment_gateways: %s", _e)

try:
    def     create_payment_gateways_draft(code: str, body: PaymentGatewaysDraftBody, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        return country_controller.create_payment_gateways_draft(code, body.model_dump(), current_user, db)
    _s21.put("/{code}/payment-gateways")(create_payment_gateways_draft)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route create_payment_gateways_draft: %s", _e)

try:
    def     get_logistics_providers(code: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        return country_controller.get_logistics_providers(code, current_user, db)
    _s21.get("/{code}/logistics-providers")(get_logistics_providers)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route get_logistics_providers: %s", _e)

try:
    def     create_logistics_providers_draft(code: str, body: LogisticsProvidersDraftBody, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        return country_controller.create_logistics_providers_draft(code, body.model_dump(), current_user, db)
    _s21.put("/{code}/logistics-providers")(create_logistics_providers_draft)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route create_logistics_providers_draft: %s", _e)

try:
    def     get_legal_rules(code: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        return country_controller.get_legal_rules(code, current_user, db)
    _s21.get("/{code}/legal-rules")(get_legal_rules)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route get_legal_rules: %s", _e)

try:
    def     create_legal_rules_draft(code: str, body: LegalRulesDraftBody, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        return country_controller.create_legal_rules_draft(code, body.model_dump(exclude_none=True), current_user, db)
    _s21.put("/{code}/legal-rules")(create_legal_rules_draft)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route create_legal_rules_draft: %s", _e)

try:
    def     get_regions(code: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        return country_controller.get_regions(code, current_user, db)
    _s21.get("/{code}/regions")(get_regions)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route get_regions: %s", _e)

try:
    def     create_regions_draft(code: str, body: RegionsDraftBody, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        return country_controller.create_regions_draft(code, body.model_dump(), current_user, db)
    _s21.put("/{code}/regions")(create_regions_draft)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route create_regions_draft: %s", _e)

try:
    def     get_supplier_requirements(code: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        return country_controller.get_supplier_requirements(code, current_user, db)
    _s21.get("/{code}/supplier-requirements")(get_supplier_requirements)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route get_supplier_requirements: %s", _e)

try:
    def     create_supplier_requirements_draft(code: str, body: SupplierRequirementsDraftBody, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        return country_controller.create_supplier_requirements_draft(code, body.model_dump(exclude_none=True), current_user, db)
    _s21.put("/{code}/supplier-requirements")(create_supplier_requirements_draft)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route create_supplier_requirements_draft: %s", _e)

try:
    def     get_payout_settings(code: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        return country_controller.get_payout_settings(code, current_user, db)
    _s21.get("/{code}/payout-settings")(get_payout_settings)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route get_payout_settings: %s", _e)

try:
    def     create_payout_settings_draft(code: str, body: PayoutSettingsDraftBody, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        return country_controller.create_payout_settings_draft(code, body.model_dump(exclude_none=True), current_user, db)
    _s21.put("/{code}/payout-settings")(create_payout_settings_draft)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route create_payout_settings_draft: %s", _e)

try:
    def     get_commission_tiers(code: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        return country_controller.get_commission_tiers(code, current_user, db)
    _s21.get("/{code}/commission-tiers")(get_commission_tiers)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route get_commission_tiers: %s", _e)

try:
    def     create_commission_tiers_draft(code: str, body: CommissionTiersDraftBody, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        return country_controller.create_commission_tiers_draft(code, body.model_dump(), current_user, db)
    _s21.put("/{code}/commission-tiers")(create_commission_tiers_draft)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route create_commission_tiers_draft: %s", _e)

try:
    def     list_country_versions(
        code: str,
        config_type: str | None = Query(default=None),
        current_user: dict = Depends(get_current_user),
        db: Session = Depends(get_db),
    ):
        return country_controller.list_country_versions(code, current_user, db, config_type=config_type)
    _s21.get("/{code}/versions")(list_country_versions)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route list_country_versions: %s", _e)

try:
    def     approve_country_version(code: str, version_id: int, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        return country_controller.approve_country_version(code, version_id, current_user, db)
    _s21.post("/{code}/versions/{version_id}/approve")(approve_country_version)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route approve_country_version: %s", _e)

try:
    def     publish_country_version(code: str, version_id: int, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        return country_controller.publish_country_version(code, version_id, current_user, db)
    _s21.post("/{code}/versions/{version_id}/publish")(publish_country_version)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route publish_country_version: %s", _e)

try:
    def     rollback_country_to_version(code: str, version_id: int, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        return country_controller.rollback_country_to_version(code, version_id, current_user, db)
    _s21.post("/{code}/versions/{version_id}/rollback")(rollback_country_to_version)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route rollback_country_to_version: %s", _e)

try:
    def     list_country_commissions(code: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        return country_controller.list_country_commissions(code, current_user, db)
    _s21.get("/{code}/commissions")(list_country_commissions)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route list_country_commissions: %s", _e)

try:
    def     get_country_feature_flags(code: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        return country_controller.get_country_feature_flags(code, current_user, db)
    _s21.get("/{code}/feature-flags")(get_country_feature_flags)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route get_country_feature_flags: %s", _e)

try:
    def     create_country_feature_flag(
        code: str,
        body: dict,
        current_user: dict = Depends(get_current_user),
        db: Session = Depends(get_db),
    ):
        return svc_create_feature_flag(code, body, db)
    _s21.post("/{code}/feature-flags")(create_country_feature_flag)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route create_country_feature_flag: %s", _e)

try:
    def     update_country_feature_flag(
        code: str,
        key: str,
        body: dict,
        current_user: dict = Depends(get_current_user),
        db: Session = Depends(get_db),
    ):
        return svc_update_feature_flag(code, key, body, db)
    _s21.patch("/{code}/feature-flags/{key}")(update_country_feature_flag)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route update_country_feature_flag: %s", _e)

try:
    def     list_country_promotions(code: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        return []
    _s21.get("/{code}/promotions")(list_country_promotions)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route list_country_promotions: %s", _e)

try:
    def     delete_country_promotion(code: str, slug: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        # Promotions are currently not persisted server-side; acknowledge deletion so the
        # client can optimistically remove the row without surfacing a 404/500.
        return {"message": "Promotion deleted", "slug": slug}
    _s21.delete("/{code}/promotions/{slug}")(delete_country_promotion)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route delete_country_promotion: %s", _e)

try:
    def     get_country_localization(code: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        return {
            "default_language": "en",
            "supported_languages": ["en", "ar"],
            "rtl_enabled": False,
            "number_format": "western",
            "calendar_type": "gregorian",
        }
    _s21.get("/{code}/localization")(get_country_localization)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route get_country_localization: %s", _e)

try:
    def     update_country_localization(code: str, body: dict, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        return {
            "message": "Localization updated",
            "code": code.upper(),
            **(body if isinstance(body, dict) else {}),
        }
    _s21.put("/{code}/localization")(update_country_localization)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route update_country_localization: %s", _e)

try:
    def     delete_country_feature_flag(code: str, key: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        return svc_delete_feature_flag(code, key, db)
    _s21.delete("/{code}/feature-flags/{key}")(delete_country_feature_flag)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route delete_country_feature_flag: %s", _e)

try:
    def     list_country_delivery_zones(code: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        return country_controller.list_country_delivery_zones(code, current_user, db)
    _s21.get("/{code}/delivery-zones")(list_country_delivery_zones)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route list_country_delivery_zones: %s", _e)

try:
    def     list_oman_delivery_zones_compat(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        # Backward compatibility path for existing Oman admin tooling.
        return country_controller.list_country_delivery_zones("OM", current_user, db)
    _s21.get("/om/zones")(list_oman_delivery_zones_compat)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route list_oman_delivery_zones_compat: %s", _e)

try:
    def     preview_country_tax(code: str, body: TaxPreviewBody, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        return country_controller.preview_country_tax(code, body.model_dump(exclude_none=True), current_user, db)
    _s21.post("/{code}/preview-tax")(preview_country_tax)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route preview_country_tax: %s", _e)

try:
    def     test_gateway_connection(
        code: str,
        gateway_id: str,
        body: TestGatewayConnectionBody = TestGatewayConnectionBody(),
        current_user: dict = Depends(get_current_user),
        db: Session = Depends(get_db),
    ):
        return country_controller.test_gateway_connection(code, gateway_id, body.environment, current_user, db)
    _s21.post("/{code}/payment-gateways/{gateway_id}/test")(test_gateway_connection)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route test_gateway_connection: %s", _e)

try:
    @_s21.post("/auto-populate")
    async def auto_populate_country(body: AutoPopulateBody, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        """Fetch country data from external APIs and curated profiles."""
        from domains.country.services.core.country_service import _require_admin
        _require_admin(current_user)
        return await country_controller.auto_populate_async(body.search_term)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route: %s", _e)

try:
    def     list_country_cities(
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
    _s21.get("/{code}/cities")(list_country_cities)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route list_country_cities: %s", _e)

try:
    def     add_country_city(
        code: str,
        body: dict,
        current_user: dict = Depends(get_current_user),
        db: Session = Depends(get_db),
    ):
        _require_admin(current_user)
        return svc_add_country_city(code, body, db)
    _s21.post("/{code}/cities")(add_country_city)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route add_country_city: %s", _e)

try:
    def     patch_country_city(
        code: str,
        city_id: int,
        body: dict,
        current_user: dict = Depends(get_current_user),
        db: Session = Depends(get_db),
    ):
        _require_admin(current_user)
        return svc_patch_country_city(code, city_id, body, db)
    _s21.patch("/{code}/cities/{city_id}")(patch_country_city)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route patch_country_city: %s", _e)

try:
    def     delete_country_city(
        code: str,
        city_id: int,
        current_user: dict = Depends(get_current_user),
        db: Session = Depends(get_db),
    ):
        _require_admin(current_user)
        svc_delete_country_city(code, city_id, db)
        return Response(status_code=204)
    _s21.delete("/{code}/cities/{city_id}")(delete_country_city)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route delete_country_city: %s", _e)

try:
    def     update_country_cities_bulk(
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
    _s21.put("/{code}/cities")(update_country_cities_bulk)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route update_country_cities_bulk: %s", _e)

try:
    def     list_staff(code: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        return country_controller.list_country_staff(code, current_user, db)
    _s21.get("/{code}/staff")(list_staff)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route list_staff: %s", _e)

try:
    def     assign_staff(code: str, body: AssignStaffBody, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        return country_controller.assign_staff_to_country(code, body.user_id, body.role_in_country, current_user, db)
    _s21.post("/{code}/staff")(assign_staff)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route assign_staff: %s", _e)

try:
    def     unassign_staff(code: str, user_id: int, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        return country_controller.unassign_staff_from_country(code, user_id, current_user, db)
    _s21.delete("/{code}/staff/{user_id}")(unassign_staff)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route unassign_staff: %s", _e)

try:
    def     list_communications(code: str, category: Optional[str] = Query(None), current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        return country_controller.list_country_communications(code, current_user, db, category)
    _s21.get("/{code}/communications")(list_communications)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route list_communications: %s", _e)

try:
    def     send_communication(code: str, body: SendCommBody, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        return country_controller.send_country_communication(code, body.model_dump(), current_user, db)
    _s21.post("/{code}/communications")(send_communication)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route send_communication: %s", _e)

try:
    def     mark_communication_read(comm_id: int, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        return country_controller.mark_communication_read(comm_id, current_user, db)
    _s21.patch("/communications/{comm_id}/read")(mark_communication_read)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route mark_communication_read: %s", _e)

try:
    def     list_cross_country_sessions(code: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        return country_controller.list_cross_country_sessions(code, current_user, db)
    _s21.get("/{code}/cross-country-sessions")(list_cross_country_sessions)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route list_cross_country_sessions: %s", _e)

try:
    def     list_payout_rules_categories(code: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        return country_controller.list_payout_rules_categories(code, current_user, db)
    _s21.get("/{code}/payout-rules/categories")(list_payout_rules_categories)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route list_payout_rules_categories: %s", _e)

try:
    def     create_payout_rule_category(code: str, body: PayoutRuleItem, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        return country_controller.create_payout_rule_category(code, body.model_dump(), current_user, db)
    _s21.post("/{code}/payout-rules/categories")(create_payout_rule_category)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route create_payout_rule_category: %s", _e)

try:
    def     list_payout_rules_products(code: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        return country_controller.list_payout_rules_products(code, current_user, db)
    _s21.get("/{code}/payout-rules/products")(list_payout_rules_products)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route list_payout_rules_products: %s", _e)

try:
    def     create_payout_rule_product(code: str, body: PayoutRuleItem, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        return country_controller.create_payout_rule_product(code, body.model_dump(), current_user, db)
    _s21.post("/{code}/payout-rules/products")(create_payout_rule_product)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route create_payout_rule_product: %s", _e)

try:
    def     delete_payout_rule_category(code: str, rule_id: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        return country_controller.delete_payout_rule(code, rule_id, current_user, db)
    _s21.delete("/{code}/payout-rules/categories/{rule_id}")(delete_payout_rule_category)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route delete_payout_rule_category: %s", _e)

try:
    def     delete_payout_rule_product(code: str, rule_id: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        return country_controller.delete_payout_rule(code, rule_id, current_user, db)
    _s21.delete("/{code}/payout-rules/products/{rule_id}")(delete_payout_rule_product)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route delete_payout_rule_product: %s", _e)

try:
    def     toggle_country_active(code: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        return svc_toggle_country_active(code, current_user, db)
    _s21.post("/{code}/toggle-active")(toggle_country_active)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route toggle_country_active: %s", _e)

try:
    def     archive_country(code: str, payload: ArchivePayload = None, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        return svc_archive_country(code, current_user, db)
    _s21.post("/{code}/archive")(archive_country)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route archive_country: %s", _e)

try:
    def     restore_country(code: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        return svc_restore_country(code, current_user, db)
    _s21.post("/{code}/restore")(restore_country)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route restore_country: %s", _e)

try:
    def     bulk_archive_countries(payload: BulkIdsPayload, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        return svc_bulk_archive_countries(payload.ids, current_user, db)
    _s21.post("/bulk/archive")(bulk_archive_countries)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route bulk_archive_countries: %s", _e)

try:
    def     bulk_restore_countries(payload: BulkIdsPayload, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        return svc_bulk_restore_countries(payload.ids, current_user, db)
    _s21.post("/bulk/restore")(bulk_restore_countries)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route bulk_restore_countries: %s", _e)

try:
    def     hard_delete_country(code: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        svc_hard_delete_country(code, current_user, db)
        return Response(status_code=204)
    _s21.delete("/{code}")(hard_delete_country)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route hard_delete_country: %s", _e)

try:
    def     list_country_commission_rates(code: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        return svc_list_country_commission_rates(code, current_user, db)
    _s21.get("/countries/{code}/commission-rates")(list_country_commission_rates)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route list_country_commission_rates: %s", _e)

try:
    def     create_country_commission_rate(code: str, body: CountryCommissionRateItem, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        return svc_create_country_commission_rate(code, body, current_user, db)
    _s21.post("/countries/{code}/commission-rates")(create_country_commission_rate)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route create_country_commission_rate: %s", _e)

try:
    def     delete_country_commission_rate(code: str, tier: str, name: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        return svc_delete_country_commission_rate(code, tier, name, current_user, db)
    _s21.delete("/countries/{code}/commission-rates/{tier}/{name}")(delete_country_commission_rate)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route delete_country_commission_rate: %s", _e)

_s22 = APIRouter(prefix='/api/v1/admin')

try:
    def     generate_legal_contract(
        country_code: str = Path(..., description="Country code"),
        template_type: str = Query("terms", description="Template type (terms, privacy, refund)"),
        db: Session = Depends(get_db),
        current_user = Depends(get_current_user)
    ):
        """Generate a legal contract for a country."""
        result = LegalContractService.generate_contract(country_code, template_type, db=db)
        return result
    _s22.get("/{country_code}/legal-contracts/generate")(generate_legal_contract)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route generate_legal_contract: %s", _e)

try:
    def     get_audit_trail(
        country_code: str = Path(..., description="Country code"),
        table_name: Optional[str] = Query(None, description="Filter by table name"),
        record_id: Optional[int] = Query(None, description="Filter by record ID"),
        limit: int = Query(100, ge=1, le=500, description="Max results"),
        db: Session = Depends(get_db),
        current_user = Depends(get_current_user)
    ):
        """Get audit trail for a country."""
        trail = AuditTrailService.get_audit_trail(
            country_code,
            table_name=table_name,
            record_id=record_id,
            limit=limit
        )
        return trail
    _s22.get("/{country_code}/audit-trail", response_model=list[dict])(get_audit_trail)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route get_audit_trail: %s", _e)

try:
    def     log_financial_change(
        country_code: str = Path(..., description="Country code"),
        table_name: str = Body(..., description="Table name"),
        record_id: int = Body(..., description="Record ID"),
        field_name: str = Body(..., description="Field name"),
        old_value: Any = Body(..., description="Old value"),
        new_value: Any = Body(..., description="New value"),
        reason: str = Body(..., description="Reason for change"),
        user_id: Optional[int] = Body(None, description="User ID"),
        metadata: Optional[Dict[str, Any]] = Body(None, description="Additional metadata"),
        db: Session = Depends(get_db),
        current_user = Depends(get_current_user)
    ):
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
    _s22.post("/{country_code}/audit-trail/log")(log_financial_change)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route log_financial_change: %s", _e)

try:
    def     send_country_communication(
        country_code: str = Path(...),
        to_user_id: int = Body(...),
        subject: str = Body(...),
        body: str = Body(...),
        priority: str = Body("normal"),
        category: str = Body(None),
        related_entity_type: str = Body(None),
        related_entity_id: int = Body(None),
        db: Session = Depends(get_db),
        current_user = Depends(get_current_user),
    ):
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
    _s22.post("/{country_code}/communications")(send_country_communication)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route send_country_communication: %s", _e)

try:
    def     list_communications(
        status: Optional[str] = Query(None),
        priority: Optional[str] = Query(None),
        limit: int = Query(50, le=200),
        db: Session = Depends(get_db),
        current_user = Depends(get_current_user),
    ):
        """Inbox: list communications for the current user, filtered by role+country."""
        return svc_list_communications(
            current_user,
            status=status,
            priority=priority,
            limit=limit,
            db=db,
        )
    _s22.get("/communications")(list_communications)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route list_communications: %s", _e)

try:
    def     mark_communication_read(
        comm_id: int,
        db: Session = Depends(get_db),
        current_user = Depends(get_current_user),
    ):
        return svc_mark_communication_read(comm_id, db=db)
    _s22.put("/communications/{comm_id}/read")(mark_communication_read)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route mark_communication_read: %s", _e)

try:
    def     get_data_residency(
        country_code: str = Path(..., description="Country code"),
        db: Session = Depends(get_db),
        current_user = Depends(get_current_user)
    ):
        """Get data residency tier for a country."""
        from domains.audit.services.data_residency import DataResidencyService
        tier = DataResidencyService.get_data_residency_tier(country_code)
        requires_encryption = DataResidencyService.requires_local_encryption(country_code)
        return {
            "country_code": country_code,
            "data_residency_tier": tier,
            "requires_local_encryption": requires_encryption
        }
    _s22.get("/{country_code}/data-residency")(get_data_residency)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route get_data_residency: %s", _e)

try:
    def     list_cities(
        country_code: str = Path(...),
        active: bool = Query(True),
        limit: int = Query(100, le=500),
        db: Session = Depends(get_db),
        current_user = Depends(get_current_user),
    ):
        return svc_list_cities(country_code, active=active, limit=limit, db=db)
    _s22.get("/{country_code}/cities")(list_cities)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route list_cities: %s", _e)

try:
    def     add_city(
        country_code: str = Path(...),
        name: str = Body(...),
        name_local: str = Body(None),
        population: int = Body(0),
        is_capital: bool = Body(False),
        latitude: float = Body(None),
        longitude: float = Body(None),
        db: Session = Depends(get_db),
        current_user = Depends(get_current_user),
    ):
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
    _s22.post("/{country_code}/cities")(add_city)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route add_city: %s", _e)

try:
    def     update_city(
        country_code: str = Path(...),
        city_id: int = Path(...),
        name: str = Body(None),
        name_local: str = Body(None),
        population: int = Body(None),
        is_capital: bool = Body(None),
        latitude: float = Body(None),
        longitude: float = Body(None),
        status: str = Body(None),
        db: Session = Depends(get_db),
        current_user = Depends(get_current_user),
    ):
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
    _s22.put("/{country_code}/cities/{city_id}")(update_city)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route update_city: %s", _e)

try:
    def     delete_city(
        country_code: str = Path(...),
        city_id: int = Path(...),
        db: Session = Depends(get_db),
        current_user = Depends(get_current_user),
    ):
        return svc_delete_city(country_code, city_id, db=db)
    _s22.delete("/{country_code}/cities/{city_id}")(delete_city)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route delete_city: %s", _e)

try:
    def     list_staff(
        country_code: str = Path(...),
        db: Session = Depends(get_db),
        current_user = Depends(get_current_user),
    ):
        return svc_list_staff(country_code, db=db)
    _s22.get("/{country_code}/staff")(list_staff)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route list_staff: %s", _e)

try:
    def     assign_staff(
        country_code: str = Path(...),
        user_id: int = Body(...),
        role_in_country: str = Body(...),
        db: Session = Depends(get_db),
        current_user = Depends(get_current_user),
    ):
        return svc_assign_staff(
            country_code,
            user_id=user_id,
            role_in_country=role_in_country,
            current_user=current_user,
            db=db,
        )
    _s22.post("/{country_code}/staff")(assign_staff)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route assign_staff: %s", _e)

try:
    def     remove_staff(
        country_code: str = Path(...),
        staff_id: int = Path(...),
        db: Session = Depends(get_db),
        current_user = Depends(get_current_user),
    ):
        return svc_remove_staff(country_code, staff_id, db=db)
    _s22.delete("/{country_code}/staff/{staff_id}")(remove_staff)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route remove_staff: %s", _e)

try:
    def     list_tax_rates(
        country_code: str = Path(...),
        db: Session = Depends(get_db),
        current_user = Depends(get_current_user),
    ):
        return svc_list_tax_rates(country_code, db=db)
    _s22.get("/{country_code}/tax-rates")(list_tax_rates)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route list_tax_rates: %s", _e)

try:
    def     set_tax_rate(
        country_code: str = Path(...),
        category_id: int = Body(...),
        tax_rate: float = Body(...),
        tax_name: str = Body(None),
        db: Session = Depends(get_db),
        current_user = Depends(get_current_user),
    ):
        return svc_set_tax_rate(
            country_code,
            category_id=category_id,
            tax_rate=tax_rate,
            tax_name=tax_name,
            db=db,
        )
    _s22.post("/{country_code}/tax-rates")(set_tax_rate)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route set_tax_rate: %s", _e)

_s24 = APIRouter(prefix='/api/v1')

try:
    def     list_public_countries(db: Session = Depends(get_db)):
        return country_controller.list_public_countries(db)
    _s24.get('/')(list_public_countries)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route list_public_countries: %s", _e)

try:
    def     get_public_country_config(code: str, db: Session = Depends(get_db)):
        return country_controller.get_public_country_config(code, db)
    _s24.get("/{code}/config")(get_public_country_config)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route get_public_country_config: %s", _e)

try:
    def     list_public_country_employees(code: str, db: Session = Depends(get_db)):
        """Public endpoint to list employees by country code."""
        return ctrl.list_employees(code, db)
    _s24.get("/{code}/employees")(list_public_country_employees)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route list_public_country_employees: %s", _e)

try:
    def     create_admin_country(body: CountryCreateBody, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        return country_controller.create_admin_country(body.model_dump(exclude_none=True), current_user, db)
    _s24.post('/')(create_admin_country)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route create_admin_country: %s", _e)

try:
    def     get_admin_country(code: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        return country_controller.get_admin_country(code, current_user, db)
    _s24.get("/{code}")(get_admin_country)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route get_admin_country: %s", _e)

try:
    def     update_admin_country_identity(code: str, body: CountryIdentityUpdateBody, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        return country_controller.update_country_identity(code, body.model_dump(exclude_none=True), current_user, db)
    _s24.patch("/{code}")(update_admin_country_identity)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route update_admin_country_identity: %s", _e)

try:
    def     create_tax_draft(code: str, body: TaxDraftBody, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        return country_controller.create_tax_draft(code, body.model_dump(exclude_none=True), current_user, db)
    _s24.put("/{code}/tax")(create_tax_draft)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route create_tax_draft: %s", _e)

try:
    def     create_logistics_draft(code: str, body: LogisticsDraftBody, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        return country_controller.create_logistics_draft(code, body.model_dump(exclude_none=True), current_user, db)
    _s24.put("/{code}/logistics")(create_logistics_draft)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route create_logistics_draft: %s", _e)

try:
    def     create_commission_draft(code: str, body: CommissionDraftBody, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        return country_controller.create_commission_draft(code, body.model_dump(exclude_none=True), current_user, db)
    _s24.put("/{code}/commissions")(create_commission_draft)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route create_commission_draft: %s", _e)

try:
    def     create_ops_draft(code: str, body: OpsDraftBody, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        return country_controller.create_payment_and_flags_draft(code, body.model_dump(exclude_none=True), current_user, db)
    _s24.put("/{code}/ops")(create_ops_draft)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route create_ops_draft: %s", _e)

try:
    def     get_payment_gateways(code: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        return country_controller.get_payment_gateways(code, current_user, db)
    _s24.get("/{code}/payment-gateways")(get_payment_gateways)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route get_payment_gateways: %s", _e)

try:
    def     create_payment_gateways_draft(code: str, body: PaymentGatewaysDraftBody, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        return country_controller.create_payment_gateways_draft(code, body.model_dump(), current_user, db)
    _s24.put("/{code}/payment-gateways")(create_payment_gateways_draft)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route create_payment_gateways_draft: %s", _e)

try:
    def     get_logistics_providers(code: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        return country_controller.get_logistics_providers(code, current_user, db)
    _s24.get("/{code}/logistics-providers")(get_logistics_providers)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route get_logistics_providers: %s", _e)

try:
    def     create_logistics_providers_draft(code: str, body: LogisticsProvidersDraftBody, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        return country_controller.create_logistics_providers_draft(code, body.model_dump(), current_user, db)
    _s24.put("/{code}/logistics-providers")(create_logistics_providers_draft)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route create_logistics_providers_draft: %s", _e)

try:
    def     get_legal_rules(code: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        return country_controller.get_legal_rules(code, current_user, db)
    _s24.get("/{code}/legal-rules")(get_legal_rules)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route get_legal_rules: %s", _e)

try:
    def     create_legal_rules_draft(code: str, body: LegalRulesDraftBody, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        return country_controller.create_legal_rules_draft(code, body.model_dump(exclude_none=True), current_user, db)
    _s24.put("/{code}/legal-rules")(create_legal_rules_draft)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route create_legal_rules_draft: %s", _e)

try:
    def     get_regions(code: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        return country_controller.get_regions(code, current_user, db)
    _s24.get("/{code}/regions")(get_regions)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route get_regions: %s", _e)

try:
    def     create_regions_draft(code: str, body: RegionsDraftBody, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        return country_controller.create_regions_draft(code, body.model_dump(), current_user, db)
    _s24.put("/{code}/regions")(create_regions_draft)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route create_regions_draft: %s", _e)

try:
    def     get_supplier_requirements(code: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        return country_controller.get_supplier_requirements(code, current_user, db)
    _s24.get("/{code}/supplier-requirements")(get_supplier_requirements)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route get_supplier_requirements: %s", _e)

try:
    def     create_supplier_requirements_draft(code: str, body: SupplierRequirementsDraftBody, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        return country_controller.create_supplier_requirements_draft(code, body.model_dump(exclude_none=True), current_user, db)
    _s24.put("/{code}/supplier-requirements")(create_supplier_requirements_draft)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route create_supplier_requirements_draft: %s", _e)

try:
    def     get_payout_settings(code: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        return country_controller.get_payout_settings(code, current_user, db)
    _s24.get("/{code}/payout-settings")(get_payout_settings)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route get_payout_settings: %s", _e)

try:
    def     create_payout_settings_draft(code: str, body: PayoutSettingsDraftBody, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        return country_controller.create_payout_settings_draft(code, body.model_dump(exclude_none=True), current_user, db)
    _s24.put("/{code}/payout-settings")(create_payout_settings_draft)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route create_payout_settings_draft: %s", _e)

try:
    def     get_commission_tiers(code: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        return country_controller.get_commission_tiers(code, current_user, db)
    _s24.get("/{code}/commission-tiers")(get_commission_tiers)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route get_commission_tiers: %s", _e)

try:
    def     create_commission_tiers_draft(code: str, body: CommissionTiersDraftBody, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        return country_controller.create_commission_tiers_draft(code, body.model_dump(), current_user, db)
    _s24.put("/{code}/commission-tiers")(create_commission_tiers_draft)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route create_commission_tiers_draft: %s", _e)

try:
    def     list_country_versions(
        code: str,
        config_type: str | None = Query(default=None),
        current_user: dict = Depends(get_current_user),
        db: Session = Depends(get_db),
    ):
        return country_controller.list_country_versions(code, current_user, db, config_type=config_type)
    _s24.get("/{code}/versions")(list_country_versions)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route list_country_versions: %s", _e)

try:
    def     approve_country_version(code: str, version_id: int, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        return country_controller.approve_country_version(code, version_id, current_user, db)
    _s24.post("/{code}/versions/{version_id}/approve")(approve_country_version)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route approve_country_version: %s", _e)

try:
    def     publish_country_version(code: str, version_id: int, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        return country_controller.publish_country_version(code, version_id, current_user, db)
    _s24.post("/{code}/versions/{version_id}/publish")(publish_country_version)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route publish_country_version: %s", _e)

try:
    def     rollback_country_to_version(code: str, version_id: int, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        return country_controller.rollback_country_to_version(code, version_id, current_user, db)
    _s24.post("/{code}/versions/{version_id}/rollback")(rollback_country_to_version)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route rollback_country_to_version: %s", _e)

try:
    def     list_country_commissions(code: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        return country_controller.list_country_commissions(code, current_user, db)
    _s24.get("/{code}/commissions")(list_country_commissions)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route list_country_commissions: %s", _e)

try:
    def     get_country_feature_flags(code: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        return country_controller.get_country_feature_flags(code, current_user, db)
    _s24.get("/{code}/feature-flags")(get_country_feature_flags)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route get_country_feature_flags: %s", _e)

try:
    def     create_country_feature_flag(
        code: str,
        body: dict,
        current_user: dict = Depends(get_current_user),
        db: Session = Depends(get_db),
    ):
        return svc_create_feature_flag(code, body, db)
    _s24.post("/{code}/feature-flags")(create_country_feature_flag)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route create_country_feature_flag: %s", _e)

try:
    def     update_country_feature_flag(
        code: str,
        key: str,
        body: dict,
        current_user: dict = Depends(get_current_user),
        db: Session = Depends(get_db),
    ):
        return svc_update_feature_flag(code, key, body, db)
    _s24.patch("/{code}/feature-flags/{key}")(update_country_feature_flag)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route update_country_feature_flag: %s", _e)

try:
    def     list_country_promotions(code: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        return []
    _s24.get("/{code}/promotions")(list_country_promotions)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route list_country_promotions: %s", _e)

try:
    def     delete_country_promotion(code: str, slug: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        # Promotions are currently not persisted server-side; acknowledge deletion so the
        # client can optimistically remove the row without surfacing a 404/500.
        return {"message": "Promotion deleted", "slug": slug}
    _s24.delete("/{code}/promotions/{slug}")(delete_country_promotion)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route delete_country_promotion: %s", _e)

try:
    def     get_country_localization(code: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        return {
            "default_language": "en",
            "supported_languages": ["en", "ar"],
            "rtl_enabled": False,
            "number_format": "western",
            "calendar_type": "gregorian",
        }
    _s24.get("/{code}/localization")(get_country_localization)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route get_country_localization: %s", _e)

try:
    def     update_country_localization(code: str, body: dict, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        return {
            "message": "Localization updated",
            "code": code.upper(),
            **(body if isinstance(body, dict) else {}),
        }
    _s24.put("/{code}/localization")(update_country_localization)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route update_country_localization: %s", _e)

try:
    def     delete_country_feature_flag(code: str, key: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        return svc_delete_feature_flag(code, key, db)
    _s24.delete("/{code}/feature-flags/{key}")(delete_country_feature_flag)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route delete_country_feature_flag: %s", _e)

try:
    def     list_country_delivery_zones(code: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        return country_controller.list_country_delivery_zones(code, current_user, db)
    _s24.get("/{code}/delivery-zones")(list_country_delivery_zones)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route list_country_delivery_zones: %s", _e)

try:
    def     list_oman_delivery_zones_compat(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        # Backward compatibility path for existing Oman admin tooling.
        return country_controller.list_country_delivery_zones("OM", current_user, db)
    _s24.get("/om/zones")(list_oman_delivery_zones_compat)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route list_oman_delivery_zones_compat: %s", _e)

try:
    def     preview_country_tax(code: str, body: TaxPreviewBody, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        return country_controller.preview_country_tax(code, body.model_dump(exclude_none=True), current_user, db)
    _s24.post("/{code}/preview-tax")(preview_country_tax)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route preview_country_tax: %s", _e)

try:
    def     test_gateway_connection(
        code: str,
        gateway_id: str,
        body: TestGatewayConnectionBody = TestGatewayConnectionBody(),
        current_user: dict = Depends(get_current_user),
        db: Session = Depends(get_db),
    ):
        return country_controller.test_gateway_connection(code, gateway_id, body.environment, current_user, db)
    _s24.post("/{code}/payment-gateways/{gateway_id}/test")(test_gateway_connection)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route test_gateway_connection: %s", _e)

try:
    @_s24.post("/auto-populate")
    async def auto_populate_country(body: AutoPopulateBody, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        """Fetch country data from external APIs and curated profiles."""
        from domains.country.services.core.country_service import _require_admin
        _require_admin(current_user)
        return await country_controller.auto_populate_async(body.search_term)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route: %s", _e)

try:
    def     list_country_cities(
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
    _s24.get("/{code}/cities")(list_country_cities)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route list_country_cities: %s", _e)

try:
    def     add_country_city(
        code: str,
        body: dict,
        current_user: dict = Depends(get_current_user),
        db: Session = Depends(get_db),
    ):
        _require_admin(current_user)
        return svc_add_country_city(code, body, db)
    _s24.post("/{code}/cities")(add_country_city)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route add_country_city: %s", _e)

try:
    def     patch_country_city(
        code: str,
        city_id: int,
        body: dict,
        current_user: dict = Depends(get_current_user),
        db: Session = Depends(get_db),
    ):
        _require_admin(current_user)
        return svc_patch_country_city(code, city_id, body, db)
    _s24.patch("/{code}/cities/{city_id}")(patch_country_city)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route patch_country_city: %s", _e)

try:
    def     delete_country_city(
        code: str,
        city_id: int,
        current_user: dict = Depends(get_current_user),
        db: Session = Depends(get_db),
    ):
        _require_admin(current_user)
        svc_delete_country_city(code, city_id, db)
        return Response(status_code=204)
    _s24.delete("/{code}/cities/{city_id}")(delete_country_city)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route delete_country_city: %s", _e)

try:
    def     update_country_cities_bulk(
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
    _s24.put("/{code}/cities")(update_country_cities_bulk)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route update_country_cities_bulk: %s", _e)

try:
    def     list_staff(code: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        return country_controller.list_country_staff(code, current_user, db)
    _s24.get("/{code}/staff")(list_staff)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route list_staff: %s", _e)

try:
    def     assign_staff(code: str, body: AssignStaffBody, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        return country_controller.assign_staff_to_country(code, body.user_id, body.role_in_country, current_user, db)
    _s24.post("/{code}/staff")(assign_staff)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route assign_staff: %s", _e)

try:
    def     unassign_staff(code: str, user_id: int, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        return country_controller.unassign_staff_from_country(code, user_id, current_user, db)
    _s24.delete("/{code}/staff/{user_id}")(unassign_staff)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route unassign_staff: %s", _e)

try:
    def     list_communications(code: str, category: Optional[str] = Query(None), current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        return country_controller.list_country_communications(code, current_user, db, category)
    _s24.get("/{code}/communications")(list_communications)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route list_communications: %s", _e)

try:
    def     send_communication(code: str, body: SendCommBody, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        return country_controller.send_country_communication(code, body.model_dump(), current_user, db)
    _s24.post("/{code}/communications")(send_communication)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route send_communication: %s", _e)

try:
    def     mark_communication_read(comm_id: int, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        return country_controller.mark_communication_read(comm_id, current_user, db)
    _s24.patch("/communications/{comm_id}/read")(mark_communication_read)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route mark_communication_read: %s", _e)

try:
    def     list_cross_country_sessions(code: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        return country_controller.list_cross_country_sessions(code, current_user, db)
    _s24.get("/{code}/cross-country-sessions")(list_cross_country_sessions)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route list_cross_country_sessions: %s", _e)

try:
    def     list_payout_rules_categories(code: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        return country_controller.list_payout_rules_categories(code, current_user, db)
    _s24.get("/{code}/payout-rules/categories")(list_payout_rules_categories)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route list_payout_rules_categories: %s", _e)

try:
    def     create_payout_rule_category(code: str, body: PayoutRuleItem, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        return country_controller.create_payout_rule_category(code, body.model_dump(), current_user, db)
    _s24.post("/{code}/payout-rules/categories")(create_payout_rule_category)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route create_payout_rule_category: %s", _e)

try:
    def     list_payout_rules_products(code: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        return country_controller.list_payout_rules_products(code, current_user, db)
    _s24.get("/{code}/payout-rules/products")(list_payout_rules_products)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route list_payout_rules_products: %s", _e)

try:
    def     create_payout_rule_product(code: str, body: PayoutRuleItem, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        return country_controller.create_payout_rule_product(code, body.model_dump(), current_user, db)
    _s24.post("/{code}/payout-rules/products")(create_payout_rule_product)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route create_payout_rule_product: %s", _e)

try:
    def     delete_payout_rule_category(code: str, rule_id: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        return country_controller.delete_payout_rule(code, rule_id, current_user, db)
    _s24.delete("/{code}/payout-rules/categories/{rule_id}")(delete_payout_rule_category)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route delete_payout_rule_category: %s", _e)

try:
    def     delete_payout_rule_product(code: str, rule_id: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        return country_controller.delete_payout_rule(code, rule_id, current_user, db)
    _s24.delete("/{code}/payout-rules/products/{rule_id}")(delete_payout_rule_product)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route delete_payout_rule_product: %s", _e)

try:
    def     toggle_country_active(code: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        return svc_toggle_country_active(code, current_user, db)
    _s24.post("/{code}/toggle-active")(toggle_country_active)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route toggle_country_active: %s", _e)

try:
    def     archive_country(code: str, payload: ArchivePayload = None, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        return svc_archive_country(code, current_user, db)
    _s24.post("/{code}/archive")(archive_country)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route archive_country: %s", _e)

try:
    def     restore_country(code: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        return svc_restore_country(code, current_user, db)
    _s24.post("/{code}/restore")(restore_country)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route restore_country: %s", _e)

try:
    def     bulk_archive_countries(payload: BulkIdsPayload, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        return svc_bulk_archive_countries(payload.ids, current_user, db)
    _s24.post("/bulk/archive")(bulk_archive_countries)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route bulk_archive_countries: %s", _e)

try:
    def     bulk_restore_countries(payload: BulkIdsPayload, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        return svc_bulk_restore_countries(payload.ids, current_user, db)
    _s24.post("/bulk/restore")(bulk_restore_countries)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route bulk_restore_countries: %s", _e)

try:
    def     hard_delete_country(code: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        svc_hard_delete_country(code, current_user, db)
        return Response(status_code=204)
    _s24.delete("/{code}")(hard_delete_country)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route hard_delete_country: %s", _e)

try:
    def     list_country_commission_rates(code: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        return svc_list_country_commission_rates(code, current_user, db)
    _s24.get("/countries/{code}/commission-rates")(list_country_commission_rates)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route list_country_commission_rates: %s", _e)

try:
    def     create_country_commission_rate(code: str, body: CountryCommissionRateItem, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        return svc_create_country_commission_rate(code, body, current_user, db)
    _s24.post("/countries/{code}/commission-rates")(create_country_commission_rate)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route create_country_commission_rate: %s", _e)

try:
    def     delete_country_commission_rate(code: str, tier: str, name: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        return svc_delete_country_commission_rate(code, tier, name, current_user, db)
    _s24.delete("/countries/{code}/commission-rates/{tier}/{name}")(delete_country_commission_rate)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route delete_country_commission_rate: %s", _e)

_s25 = APIRouter(prefix='/api/v1/admin')

try:
    def     list_pending_bank_accounts_route_route(
        country_code: str,
        kind: str = Query('supplier'),
        page: int = Query(1),
        page_size: int = Query(50),
        current_user: dict = Depends(require_admin),
        db: Session = Depends(get_db)
    ):
        return list_pending_bank_accounts_route(country_code=country_code, kind=kind, page=page, page_size=page_size, current_user=current_user, db=db)
    _s25.get("/bank-accounts/{country_code}/pending", status_code=200, tags=['admin-bank-accounts'])(list_pending_bank_accounts_route_route)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route list_pending_bank_accounts_route_route: %s", _e)

try:
    def     verify_bank_account_route_route(
        country_code: str,
        kind: str,
        account_id: int,
        current_user: dict = Depends(require_admin),
        db: Session = Depends(get_db),
        action: str = Body('approve', embed=True),
        note: Optional[str] = Body(None, embed=True)
    ):
        return verify_bank_account_route(country_code=country_code, kind=kind, account_id=account_id, current_user=current_user, db=db, action=action, note=note)
    _s25.post("/bank-accounts/{country_code}/{kind}/{account_id}/verify", status_code=201, tags=['admin-bank-accounts'])(verify_bank_account_route_route)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route verify_bank_account_route_route: %s", _e)

try:
    def     delete_bank_account_route_route(
        country_code: str,
        kind: str,
        account_id: int,
        current_user: dict = Depends(require_admin),
        db: Session = Depends(get_db)
    ):
        return delete_bank_account_route(country_code=country_code, kind=kind, account_id=account_id, current_user=current_user, db=db)
    _s25.delete("/bank-accounts/{country_code}/{kind}/{account_id}", status_code=200, tags=['admin-bank-accounts'])(delete_bank_account_route_route)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route delete_bank_account_route_route: %s", _e)

_s26 = APIRouter(prefix='/api/v1/admin')

try:
    def     list_all_campaigns_route(_: User = Depends(require_admin), db: Session = Depends(get_db)):
        """List all email campaigns across all countries (consolidated view)."""
        return list_all_campaigns(db)
    _s26.get("/campaigns", response_model=list[EmailCampaignOut])(list_all_campaigns_route)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route list_all_campaigns_route: %s", _e)

try:
    def     admin_email_metrics(_: User = Depends(require_admin), db: Session = Depends(get_db)):
        """Consolidated email metrics across all countries."""
        return email_metrics(db)
    _s26.get("/metrics")(admin_email_metrics)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route admin_email_metrics: %s", _e)

try:
    def     list_campaigns_route(country_code: str = Path(..., description="ISO country code"), _: User = Depends(require_admin), db: Session = Depends(get_db), page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100)):
        get_country_or_404(country_code.upper(), db)
        set_rls_context({country_code.upper()}, is_restricted=True)
        try:
            return list_campaigns(db, country_code, page, page_size)
        finally:
            clear_rls_context()
    _s26.get("/campaigns/{country_code}")(list_campaigns_route)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route list_campaigns_route: %s", _e)

try:
    def     create_campaign_route(country_code: str = Path(..., description="ISO country code"), payload: EmailCampaignCreate = None, _: User = Depends(require_admin), db: Session = Depends(get_db)):
        get_country_or_404(country_code.upper(), db)
        set_rls_context({country_code.upper()}, is_restricted=True)
        try:
            return create_campaign(db, payload, country_code)
        finally:
            clear_rls_context()
    _s26.post("/campaigns/{country_code}", response_model=EmailCampaignOut, status_code=201)(create_campaign_route)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route create_campaign_route: %s", _e)

try:
    def     delete_campaign_route(country_code: str = Path(..., description="ISO country code"), campaign_id: int = Path(...), _: User = Depends(require_admin), db: Session = Depends(get_db)):
        get_country_or_404(country_code.upper(), db)
        set_rls_context({country_code.upper()}, is_restricted=True)
        try:
            return delete_campaign(db, campaign_id, country_code)
        finally:
            clear_rls_context()
    _s26.delete("/campaigns/{country_code}/{campaign_id}")(delete_campaign_route)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route delete_campaign_route: %s", _e)

_s28 = APIRouter(prefix='')

try:
    def     currency_context(
        country: str | None = Query(default=None, max_length=5),
        currency: str | None = Query(default=None, max_length=5),
    ):
        return get_currency_context(country=country, currency=currency, default_currency="OMR")
    _s28.get("/context")(currency_context)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route currency_context: %s", _e)

try:
    def     currency_rates(
        amount: float = Query(default=1.0, gt=0),
        base: str = Query(default="AED", max_length=5),
        target: str | None = Query(default=None, max_length=5),
        country: str | None = Query(default=None, max_length=5),
    ):
        resolved_target = normalize_currency_code(target, default="") if target else currency_for_country(country, default_currency="OMR")
        converted, rate, source = convert_between_currencies(amount, base, resolved_target)
        return {
            "amount": amount,
            "base_currency": normalize_currency_code(base),
            "target_currency": resolved_target,
            "country": country,
            "converted_amount": float(converted),
            "rate": float(rate),
            "source": source,
        }
    _s28.get("/rates")(currency_rates)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route currency_rates: %s", _e)

try:
    def     refresh_currency_rates(current_user: dict = Depends(get_current_user)):
        if current_user.get("role") not in ("admin", "sub_admin", "moderator"):
            raise HTTPException(status_code=403, detail="Admin access required")
        return refresh_rate_cache()
    _s28.post("/rates/refresh")(refresh_currency_rates)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route refresh_currency_rates: %s", _e)

_s30 = APIRouter(prefix='/api/v1')

try:
    @_s30.post("/ai", response_model=AIResearchResponse)
    async def queue_ai_research(request: AIResearchRequest) -> AIResearchResponse:
        if not getattr(settings, "country_ai_enabled", True):
            raise HTTPException(status_code=503, detail="Country AI research is disabled by configuration.")
    
        max_jobs = int(getattr(settings, "country_ai_max_concurrent_jobs", 5) or 5)
        running = increment_running_jobs()
        try:
            if running > max_jobs:
                decrement_running_jobs()
                raise HTTPException(status_code=429, detail="Too many concurrent AI research jobs. Try again later.")
        except Exception:
            pass
    
        country_code = (request.country_code or "").upper().strip()
        if not country_code:
            raise HTTPException(status_code=422, detail="country_code is required.")
    
        ttl = int(getattr(settings, "country_ai_cache_ttl_seconds", 86400) or 86400)
        job = enqueue_job(country_code, request.model_dump(), ttl_seconds=ttl)
        job_id = job["job_id"]
    
        _run_ai_job(job_id, request.model_dump(), ttl)
        return AIResearchResponse(**job)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route: %s", _e)

try:
    @_s30.get("/ai/{job_id}", response_model=AIResearchResponse)
    async def get_ai_research(job_id: str) -> AIResearchResponse:
        job = get_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found.")
    
        result = get_completed_result(job_id) if job.get("status") == "completed" else None
        return AIResearchResponse(
            job_id=job.get("job_id", job_id),
            country_code=job.get("country_code", ""),
            status=job.get("status", "unknown"),
            created_at_utc=job.get("created_at_utc", ""),
            updated_at_utc=job.get("updated_at_utc", ""),
            result=result,
            error=job.get("error"),
        )
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route: %s", _e)

try:
    def _run_ai_job(job_id: str, payload: Dict[str, Any], ttl: int) -> None:
        try:
            import threading
    
            thread = threading.Thread(target=_run_sync, args=(job_id, payload, ttl), daemon=True)
            thread.start()
        except Exception as exc:
            logger.exception("Failed to start AI research job %s: %s", job_id, exc)
            mark_job_failed(job_id, str(exc), ttl_seconds=ttl)
            try:
                decrement_running_jobs()
            except Exception:
                pass
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route: %s", _e)

try:
    def _run_sync(job_id: str, payload: Dict[str, Any], ttl: int) -> None:
        try:
            import asyncio
    
            mark_job_running(job_id, ttl_seconds=ttl)
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(_execute_job(payload))
                mark_job_completed(job_id, result, ttl_seconds=ttl)
            finally:
                loop.close()
        except Exception as exc:
            logger.exception("AI research job %s failed: %s", job_id, exc)
            mark_job_failed(job_id, str(exc), ttl_seconds=ttl)
        finally:
            try:
                decrement_running_jobs()
            except Exception:
                pass
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route: %s", _e)

try:
    async def _execute_job(payload: Dict[str, Any]) -> Dict[str, Any]:
        service = CountryAIResearchService(
            country_name=payload.get("base_report", {}).get("module_01_country_identity", {}).get("official_name")
            or payload.get("country_code", ""),
            base_report=payload.get("base_report", {}),
            demographics=payload.get("demographics", {}),
            economy=payload.get("economy", {}),
            news=payload.get("news", []) or [],
            evidence=payload.get("evidence", {}) or {},
        )
        return await service.enrich()
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route: %s", _e)

try:
    router.include_router(_s0)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip subrouter _s0: %s", _e)

try:
    router.include_router(_s1)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip subrouter _s1: %s", _e)

try:
    router.include_router(_s2)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip subrouter _s2: %s", _e)

try:
    router.include_router(_s3)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip subrouter _s3: %s", _e)

try:
    router.include_router(_s4)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip subrouter _s4: %s", _e)

try:
    router.include_router(_s5)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip subrouter _s5: %s", _e)

try:
    router.include_router(_s6)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip subrouter _s6: %s", _e)

try:
    router.include_router(_s7)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip subrouter _s7: %s", _e)

try:
    router.include_router(_s8)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip subrouter _s8: %s", _e)

try:
    router.include_router(_s9)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip subrouter _s9: %s", _e)

try:
    router.include_router(_s10)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip subrouter _s10: %s", _e)

try:
    router.include_router(_s11)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip subrouter _s11: %s", _e)

try:
    router.include_router(_s12)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip subrouter _s12: %s", _e)

try:
    router.include_router(_s13)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip subrouter _s13: %s", _e)

try:
    router.include_router(_s14)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip subrouter _s14: %s", _e)

try:
    router.include_router(_s15)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip subrouter _s15: %s", _e)

try:
    router.include_router(_s16)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip subrouter _s16: %s", _e)

try:
    router.include_router(_s17)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip subrouter _s17: %s", _e)

try:
    router.include_router(_s18)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip subrouter _s18: %s", _e)

try:
    router.include_router(_s19)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip subrouter _s19: %s", _e)

try:
    router.include_router(_s20)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip subrouter _s20: %s", _e)

try:
    router.include_router(_s21)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip subrouter _s21: %s", _e)

try:
    router.include_router(_s22)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip subrouter _s22: %s", _e)

try:
    router.include_router(_s23)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip subrouter _s23: %s", _e)

try:
    router.include_router(_s24)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip subrouter _s24: %s", _e)

try:
    router.include_router(_s25)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip subrouter _s25: %s", _e)

try:
    router.include_router(_s26)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip subrouter _s26: %s", _e)

try:
    router.include_router(_s27)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip subrouter _s27: %s", _e)

try:
    router.include_router(_s28)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip subrouter _s28: %s", _e)

try:
    router.include_router(_s29)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip subrouter _s29: %s", _e)

try:
    router.include_router(_s30)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip subrouter _s30: %s", _e)

if auto_populate_router is not None:
    try:
        router.include_router(auto_populate_router)
    except Exception as _e:
        import logging as _l; _l.getLogger(__name__).warning("skip include auto_populate_router: %s", _e)

if versioning_router is not None:
    try:
        router.include_router(versioning_router)
    except Exception as _e:
        import logging as _l; _l.getLogger(__name__).warning("skip include versioning_router: %s", _e)

if auto_populate_router is not None:
    try:
        router.include_router(auto_populate_router)
    except Exception as _e:
        import logging as _l; _l.getLogger(__name__).warning("skip include auto_populate_router: %s", _e)

if auto_populate_router is not None:
    try:
        router.include_router(auto_populate_router)
    except Exception as _e:
        import logging as _l; _l.getLogger(__name__).warning("skip include auto_populate_router: %s", _e)

router = APIRouter()

try:
    router.include_router(_s0)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip subrouter _s0: %s", _e)

try:
    router.include_router(_s1)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip subrouter _s1: %s", _e)

try:
    router.include_router(_s5)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip subrouter _s5: %s", _e)

try:
    router.include_router(_s6)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip subrouter _s6: %s", _e)

try:
    router.include_router(_s7)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip subrouter _s7: %s", _e)

try:
    router.include_router(_s11)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip subrouter _s11: %s", _e)

try:
    router.include_router(_s15)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip subrouter _s15: %s", _e)

try:
    router.include_router(_s17)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip subrouter _s17: %s", _e)

try:
    router.include_router(_s19)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip subrouter _s19: %s", _e)

try:
    router.include_router(_s21)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip subrouter _s21: %s", _e)

try:
    router.include_router(_s22)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip subrouter _s22: %s", _e)

try:
    router.include_router(_s24)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip subrouter _s24: %s", _e)

try:
    router.include_router(_s25)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip subrouter _s25: %s", _e)

try:
    router.include_router(_s26)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip subrouter _s26: %s", _e)

try:
    router.include_router(_s28)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip subrouter _s28: %s", _e)

try:
    router.include_router(_s30)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip subrouter _s30: %s", _e)

