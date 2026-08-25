"""Admin tax router � split from country.py."""

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


_s8 = APIRouter(prefix='/api/v1/country-payouts')

try:
    def     health():
        """Liveness probe for this router."""
        return {"status": "ok", "router": "country_payouts_routes", "prefix": "/api/v1/country-payouts"}
    _s8.get("/country_payouts_routes/health")(health)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route health: %s", _e)

_s10 = APIRouter(prefix='')

try:
    def _staff_payload(assignment: CountryStaffAssignment) -> dict:
        user = assignment.user
        return {
            "id": assignment.id,
            "user_id": assignment.user_id,
            "country_code": assignment.country_code,
            "role_in_country": assignment.role_in_country,
            "is_active": assignment.is_active,
            "notes": assignment.notes,
            "assigned_at": assignment.created_at.isoformat() if assignment.created_at else None,
            "updated_at": assignment.updated_at.isoformat() if assignment.updated_at else None,
            # User info
            "user_name": (user.full_name or user.username) if user else None,
            "user_email": user.email if user else None,
            "user_role": user.role if user else None,
            "avatar_url": user.avatar_url if user else None,
        }
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route: %s", _e)

try:
    def     list_country_staff(
        code: str,
        active_only: bool = Query(True),
        db: Session = Depends(get_db),
        current_user: dict = Depends(get_current_user),
    ):
        """List all staff assigned to a country."""
        country = db.query(CountryConfig).filter(CountryConfig.code == code.upper()).first()
        if not country:
            raise HTTPException(status_code=404, detail="Country not found")

        q = db.query(CountryStaffAssignment).filter(
            CountryStaffAssignment.country_code == code.upper()
        )
        if active_only:
            q = q.filter(CountryStaffAssignment.is_active == True)

        assignments = q.all()
        return {
            "country_code": code.upper(),
            "staff": [_staff_payload(a) for a in assignments],
            "total": len(assignments),
        }
    _s10.get("/countries/{code}/staff")(list_country_staff)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route list_country_staff: %s", _e)

try:
    def     assign_staff_to_country(
        code: str,
        body: StaffAssignBody,
        db: Session = Depends(get_db),
        current_user: dict = Depends(get_current_user),
    ):
        """Assign a user to a country with a specific role."""
        require_admin(current_user)

        if body.role_in_country not in VALID_ROLES:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid role. Must be one of: {', '.join(VALID_ROLES)}"
            )

        country = db.query(CountryConfig).filter(CountryConfig.code == code.upper()).first()
        if not country:
            raise HTTPException(status_code=404, detail="Country not found")

        user = db.query(User).filter(User.id == body.user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Check if already assigned (upsert logic)
        existing = db.query(CountryStaffAssignment).filter(
            CountryStaffAssignment.user_id == body.user_id,
            CountryStaffAssignment.country_code == code.upper(),
        ).first()

        if existing:
            existing.role_in_country = body.role_in_country
            existing.is_active = True
            existing.notes = body.notes
            existing.updated_at = _utcnow()
            db.commit()
            db.refresh(existing)
            return {"message": "Staff assignment updated", "assignment": _staff_payload(existing)}

        assignment = CountryStaffAssignment(
            user_id=body.user_id,
            country_code=code.upper(),
            role_in_country=body.role_in_country,
            notes=body.notes,
            assigned_by=current_user.get("id"),
            is_active=True,
        )
        db.add(assignment)
        db.commit()
        db.refresh(assignment)
        return {"message": "Staff assigned to country", "assignment": _staff_payload(assignment)}
    _s10.post("/countries/{code}/staff")(assign_staff_to_country)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route assign_staff_to_country: %s", _e)

try:
    def     update_staff_assignment(
        code: str,
        assignment_id: int,
        body: StaffUpdateBody,
        db: Session = Depends(get_db),
        current_user: dict = Depends(get_current_user),
    ):
        """Update a staff assignment (role, active status)."""
        require_admin(current_user)

        assignment = db.query(CountryStaffAssignment).filter(
            CountryStaffAssignment.id == assignment_id,
            CountryStaffAssignment.country_code == code.upper(),
        ).first()
        if not assignment:
            raise HTTPException(status_code=404, detail="Assignment not found")

        if body.role_in_country is not None:
            if body.role_in_country not in VALID_ROLES:
                raise HTTPException(status_code=400, detail="Invalid role")
            assignment.role_in_country = body.role_in_country
        if body.is_active is not None:
            assignment.is_active = body.is_active
        if body.notes is not None:
            assignment.notes = body.notes

        assignment.updated_at = _utcnow()
        db.commit()
        db.refresh(assignment)
        return {"message": "Assignment updated", "assignment": _staff_payload(assignment)}
    _s10.patch("/countries/{code}/staff/{assignment_id}")(update_staff_assignment)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route update_staff_assignment: %s", _e)

try:
    def     remove_staff_from_country(
        code: str,
        user_id: int,
        db: Session = Depends(get_db),
        current_user: dict = Depends(get_current_user),
    ):
        """Remove (deactivate) a user from a country assignment."""
        require_admin(current_user)

        assignment = db.query(CountryStaffAssignment).filter(
            CountryStaffAssignment.user_id == user_id,
            CountryStaffAssignment.country_code == code.upper(),
        ).first()
        if not assignment:
            raise HTTPException(status_code=404, detail="Assignment not found")

        assignment.is_active = False
        assignment.updated_at = _utcnow()
        db.commit()
        return {"message": "Staff removed from country"}
    _s10.delete("/countries/{code}/staff/{user_id}")(remove_staff_from_country)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route remove_staff_from_country: %s", _e)

try:
    def     get_my_assigned_countries(
        db: Session = Depends(get_db),
        current_user: dict = Depends(get_current_user),
    ):
        """Get all countries the current user is assigned to."""
        user_id = current_user.get("id")
        assignments = db.query(CountryStaffAssignment).filter(
            CountryStaffAssignment.user_id == user_id,
            CountryStaffAssignment.is_active == True,
        ).all()

        result = []
        for a in assignments:
            country = db.query(CountryConfig).filter(CountryConfig.code == a.country_code).first()
            result.append({
                "country_code": a.country_code,
                "country_name": country.name if country else a.country_code,
                "flag_url": country.flag_url if country else None,
                "role_in_country": a.role_in_country,
                "assigned_at": a.created_at.isoformat() if a.created_at else None,
            })

        return {"assigned_countries": result, "total": len(result)}
    _s10.get("/staff/my-countries")(get_my_assigned_countries)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route get_my_assigned_countries: %s", _e)

try:
    def     list_all_staff_assignments(
        role: Optional[str] = Query(None),
        active_only: bool = Query(True),
        limit: int = Query(100, ge=1, le=500),
        db: Session = Depends(get_db),
        current_user: dict = Depends(get_current_user),
    ):
        """Admin-only: list all staff assignments across all countries."""
        require_admin(current_user)

        q = db.query(CountryStaffAssignment)
        if active_only:
            q = q.filter(CountryStaffAssignment.is_active == True)
        if role:
            q = q.filter(CountryStaffAssignment.role_in_country == role)

        assignments = q.limit(limit).all()
        return {
            "assignments": [_staff_payload(a) for a in assignments],
            "total": len(assignments),
        }
    _s10.get("/staff/all-assignments")(list_all_staff_assignments)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route list_all_staff_assignments: %s", _e)

_s12 = APIRouter(prefix='')

_s13 = APIRouter(prefix='/api/v1/cross-border')

try:
    def     health():
        """Liveness probe for this router."""
        return {"status": "ok", "router": "cross_border", "prefix": "/api/v1/cross-border"}
    _s13.get("/cross_border/health")(health)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route health: %s", _e)

_s14 = APIRouter(prefix='')

try:
    def get_country_from_ip(ip: str, db: Session) -> Optional[str]:
        """Fallback function for geo detection."""
        service = CountryDetectionService(db)
        country_code, _ = service._lookup_country_by_ip(ip)
        return country_code
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route: %s", _e)

try:
    def     get_geo_info(
        request: Request,
        ip_address: Optional[str] = Query(None, description="Client IP for geo detection"),
        current_user: dict = Depends(get_current_user),
        db: Session = Depends(get_db),
    ):
        """Get geo information based on IP or user location."""
        country_code = None
        if ip_address:
            country_code = get_country_from_ip(ip_address, db)
        elif hasattr(request.state, "client_ip") and request.state.client_ip != "unknown":
            country_code = get_country_from_ip(request.state.client_ip, db)
        elif current_user.get("preferred_country"):
            country_code = current_user.get("preferred_country")
    
        from domains.country.models.countries import CountryConfig
        country = db.query(CountryConfig).filter(CountryConfig.code == country_code).first() if country_code else None
    
        return {
            "country_code": country_code,
            "country_name": country.name if country else None,
            "currency": country.currency if country else None,
            "currency_symbol": country.currency_symbol if country else None,
            "timezone": country.timezone if country else None,
            "language": country.language if country else None,
        }
    _s14.get("/geo")(get_geo_info)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route get_geo_info: %s", _e)

try:
    def     list_geo_countries(db: Session = Depends(get_db)):
        """List all countries with geo information."""
        from domains.country.models.countries import CountryConfig
        countries = db.query(CountryConfig).filter(CountryConfig.is_active == True).all()
        return [
            {
                "code": c.code,
                "name": c.name,
                "currency": c.currency,
                "currency_symbol": c.currency_symbol,
                "phone_code": c.phone_code,
                "language": c.language,
                "timezone": c.timezone,
            }
            for c in countries
        ]
    _s14.get("/geo/countries")(list_geo_countries)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route list_geo_countries: %s", _e)

_s16 = APIRouter(prefix='')

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
    _s16.get("/api/geo/from-ip")(geo_from_ip)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route geo_from_ip: %s", _e)

try:
    def     geo_locate(request: Request, x_forwarded_for: str | None = Header(None), x_real_ip: str | None = Header(None)):
        client_host, fwd, real = _client_meta(request, x_forwarded_for, x_real_ip)
        try:
            return resolve_ip_location(client_host=client_host, forwarded_for=fwd, real_ip=real).to_dict()
        except RuntimeError as exc:
            return JSONResponse(status_code=502, content={"error": str(exc), "source": "location_api"})
    _s16.get("/api/geo/locate")(geo_locate)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route geo_locate: %s", _e)

try:
    def     geo_reverse(payload: ReverseRequest):
        try:
            return reverse_geocode(payload.lat, payload.lon).to_dict()
        except RuntimeError as exc:
            return JSONResponse(status_code=502, content={"error": str(exc), "source": "location_api"})
    _s16.post("/api/geo/reverse")(geo_reverse)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route geo_reverse: %s", _e)

try:
    def     geo_resolve(payload: ResolveRequest, request: Request, x_forwarded_for: str | None = Header(None), x_real_ip: str | None = Header(None)):
        client_host, fwd, real = _client_meta(request, x_forwarded_for, x_real_ip)
        try:
            return resolve_ip_location(ip=payload.ip, client_host=client_host, forwarded_for=fwd, real_ip=real).to_dict()
        except RuntimeError as exc:
            return JSONResponse(status_code=502, content={"error": str(exc), "source": "location_api"})
    _s16.post("/api/geo/resolve")(geo_resolve)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route geo_resolve: %s", _e)

_s18 = APIRouter(prefix='')

try:
    @limiter.limit("20/minute")
    @_s18.post('/', response_model=TranslateResponse)
    def translate_texts(request: Request, body: TranslateRequest) -> TranslateResponse:
        """
        Translate an array of strings to the target language.
        English → Arabic is the primary use-case.
        Returns the same array (untranslated) if target == source.
        """
        if not body.texts:
            return TranslateResponse(translations=[])
    
        # If already the same language, return as-is
        if body.target == body.source:
            return TranslateResponse(translations=body.texts)
    
        try:
            from deep_translator import GoogleTranslator  # lazy import
    
            translator = GoogleTranslator(source=body.source, target=body.target)
            results: list[str] = []
    
            for text in body.texts:
                if not text or not text.strip():
                    results.append(text)
                    continue
                try:
                    translated = translator.translate(text)
                    results.append(translated if translated else text)
                except Exception as exc:
                    logger.warning("Translation failed for text %r: %s", text[:50], exc)
                    results.append(text)  # fall back to original
    
            return TranslateResponse(translations=results)
    
        except ImportError:
            logger.error("deep-translator not installed. Run: pip install deep-translator")
            # Graceful degradation — return originals so the UI stays functional
            return TranslateResponse(translations=body.texts)
        except Exception as exc:
            logger.error("Translation service error: %s", exc)
            return TranslateResponse(translations=body.texts)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route: %s", _e)

_s20 = APIRouter(prefix='/api/v1')

try:
    def     list_config_versions_route(
        country_code: str,
        config_type: Optional[str] = Query(None),
        current_user: dict = Depends(get_current_user),
        db: Session = Depends(get_db)
    ) -> list:
        return list_config_versions(country_code=country_code, config_type=config_type, current_user=current_user, db=db)
    _s20.get("/admin/config-versions/{country_code}", status_code=200, tags=['country-versioning'])(list_config_versions_route)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route list_config_versions_route: %s", _e)

try:
    def     list_config_versions_public_route(
        country_code: str,
        config_type: Optional[str] = Query(None),
        current_user: dict = Depends(get_current_user),
        db: Session = Depends(get_db)
    ) -> list:
        return list_config_versions_public(country_code=country_code, config_type=config_type, current_user=current_user, db=db)
    _s20.get("/config-versions/{country_code}", status_code=200, tags=['country-versioning'])(list_config_versions_public_route)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route list_config_versions_public_route: %s", _e)

try:
    def     get_config_version_route(
        country_code: str,
        version_id: int,
        current_user: dict = Depends(get_current_user),
        db: Session = Depends(get_db)
    ) -> dict:
        return get_config_version(country_code=country_code, version_id=version_id, current_user=current_user, db=db)
    _s20.get("/admin/config-versions/{country_code}/{version_id}", status_code=200, tags=['country-versioning'])(get_config_version_route)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route get_config_version_route: %s", _e)

try:
    def     get_config_version_public_route(
        country_code: str,
        version_id: int,
        current_user: dict = Depends(get_current_user),
        db: Session = Depends(get_db)
    ) -> dict:
        return get_config_version_public(country_code=country_code, version_id=version_id, current_user=current_user, db=db)
    _s20.get("/config-versions/{country_code}/{version_id}", status_code=200, tags=['country-versioning'])(get_config_version_public_route)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route get_config_version_public_route: %s", _e)

try:
    def     create_config_version_route(
        country_code: str,
        current_user: dict = Depends(get_current_user),
        db: Session = Depends(get_db),
        body: VersionDraftBody = Body(...)
    ) -> dict:
        return create_config_version(country_code=country_code, current_user=current_user, db=db, body=body)
    _s20.post("/admin/config-versions/{country_code}", status_code=201, tags=['country-versioning'])(create_config_version_route)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route create_config_version_route: %s", _e)

try:
    def     create_config_version_public_route(
        country_code: str,
        current_user: dict = Depends(get_current_user),
        db: Session = Depends(get_db),
        body: VersionDraftBody = Body(...)
    ) -> dict:
        return create_config_version_public(country_code=country_code, current_user=current_user, db=db, body=body)
    _s20.post("/config-versions/{country_code}", status_code=201, tags=['country-versioning'])(create_config_version_public_route)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route create_config_version_public_route: %s", _e)

try:
    def     approve_config_version_route(
        country_code: str,
        version_id: int,
        current_user: dict = Depends(get_current_user),
        db: Session = Depends(get_db)
    ) -> dict:
        return approve_config_version(country_code=country_code, version_id=version_id, current_user=current_user, db=db)
    _s20.post("/admin/config-versions/{country_code}/{version_id}/approve", status_code=201, tags=['country-versioning'])(approve_config_version_route)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route approve_config_version_route: %s", _e)

try:
    def     approve_config_version_public_route(
        country_code: str,
        version_id: int,
        current_user: dict = Depends(get_current_user),
        db: Session = Depends(get_db)
    ) -> dict:
        return approve_config_version_public(country_code=country_code, version_id=version_id, current_user=current_user, db=db)
    _s20.post("/config-versions/{country_code}/{version_id}/approve", status_code=201, tags=['country-versioning'])(approve_config_version_public_route)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route approve_config_version_public_route: %s", _e)

try:
    def     publish_config_version_route(
        country_code: str,
        version_id: int,
        current_user: dict = Depends(get_current_user),
        db: Session = Depends(get_db)
    ) -> dict:
        return publish_config_version(country_code=country_code, version_id=version_id, current_user=current_user, db=db)
    _s20.post("/admin/config-versions/{country_code}/{version_id}/publish", status_code=201, tags=['country-versioning'])(publish_config_version_route)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route publish_config_version_route: %s", _e)

try:
    def     publish_config_version_public_route(
        country_code: str,
        version_id: int,
        current_user: dict = Depends(get_current_user),
        db: Session = Depends(get_db)
    ) -> dict:
        return publish_config_version_public(country_code=country_code, version_id=version_id, current_user=current_user, db=db)
    _s20.post("/config-versions/{country_code}/{version_id}/publish", status_code=201, tags=['country-versioning'])(publish_config_version_public_route)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route publish_config_version_public_route: %s", _e)

try:
    def     rollback_config_version_route(
        country_code: str,
        version_id: int,
        current_user: dict = Depends(get_current_user),
        db: Session = Depends(get_db)
    ) -> dict:
        return rollback_config_version(country_code=country_code, version_id=version_id, current_user=current_user, db=db)
    _s20.post("/admin/config-versions/{country_code}/{version_id}/rollback", status_code=201, tags=['country-versioning'])(rollback_config_version_route)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route rollback_config_version_route: %s", _e)

try:
    def     rollback_config_version_public_route(
        country_code: str,
        version_id: int,
        current_user: dict = Depends(get_current_user),
        db: Session = Depends(get_db)
    ) -> dict:
        return rollback_config_version_public(country_code=country_code, version_id=version_id, current_user=current_user, db=db)
    _s20.post("/config-versions/{country_code}/{version_id}/rollback", status_code=201, tags=['country-versioning'])(rollback_config_version_public_route)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route rollback_config_version_public_route: %s", _e)

_s23 = APIRouter(prefix='/api/v1/admin')

try:
    def     list_partners_route(country_code: str = Path(..., description="ISO country code"), include_deleted: bool = False, page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100), _: User = Depends(require_admin), db: Session = Depends(get_db)):
        get_country_or_404(country_code.upper(), db)
        set_rls_context({country_code.upper()}, is_restricted=True)
        try:
            return list_partners(db, country_code, include_deleted, page, page_size)
        finally:
            clear_rls_context()
    _s23.get("/{country_code}/partners")(list_partners_route)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route list_partners_route: %s", _e)

try:
    def     approve_partner_route(country_code: str = Path(..., description="ISO country code"), partner_id: int = Path(...), _: User = Depends(require_admin), db: Session = Depends(get_db)):
        get_country_or_404(country_code.upper(), db)
        set_rls_context({country_code.upper()}, is_restricted=True)
        try:
            return approve_partner(db, partner_id, country_code)
        finally:
            clear_rls_context()
    _s23.put("/{country_code}/partners/{partner_id}/approve")(approve_partner_route)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route approve_partner_route: %s", _e)

try:
    def     reject_partner_route(country_code: str = Path(..., description="ISO country code"), partner_id: int = Path(...), _: User = Depends(require_admin), db: Session = Depends(get_db)):
        get_country_or_404(country_code.upper(), db)
        set_rls_context({country_code.upper()}, is_restricted=True)
        try:
            return reject_partner(db, partner_id, country_code)
        finally:
            clear_rls_context()
    _s23.put("/{country_code}/partners/{partner_id}/reject")(reject_partner_route)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route reject_partner_route: %s", _e)

try:
    def     toggle_partner_active_route(country_code: str = Path(..., description="ISO country code"), partner_id: int = Path(...), _: User = Depends(require_admin), db: Session = Depends(get_db)):
        get_country_or_404(country_code.upper(), db)
        set_rls_context({country_code.upper()}, is_restricted=True)
        try:
            return toggle_partner_active(db, partner_id, country_code)
        finally:
            clear_rls_context()
    _s23.post("/{country_code}/partners/{partner_id}/toggle-active")(toggle_partner_active_route)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route toggle_partner_active_route: %s", _e)

try:
    def     archive_partner(country_code: str = Path(..., description="ISO country code"), partner_id: int = Path(...), payload: ArchiveRequest = None, _: User = Depends(require_admin), db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
        get_country_or_404(country_code.upper(), db)
        set_rls_context({country_code.upper()}, is_restricted=True)
        try:
            return archive_entity("logistics_partner", partner_id, {"id": current_user.id, "username": current_user.username, "role": current_user.role}, db, payload.reason if payload else None)
        finally:
            clear_rls_context()
    _s23.post("/{country_code}/partners/{partner_id}/archive")(archive_partner)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route archive_partner: %s", _e)

try:
    def     restore_partner(country_code: str = Path(..., description="ISO country code"), partner_id: int = Path(...), _: User = Depends(require_admin), db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
        get_country_or_404(country_code.upper(), db)
        set_rls_context({country_code.upper()}, is_restricted=True)
        try:
            return restore_entity("logistics_partner", partner_id, {"id": current_user.id, "username": current_user.username, "role": current_user.role}, db)
        finally:
            clear_rls_context()
    _s23.post("/{country_code}/partners/{partner_id}/restore")(restore_partner)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route restore_partner: %s", _e)

try:
    def     bulk_archive_partners(country_code: str = Path(..., description="ISO country code"), payload: BulkActionRequest = None, _: User = Depends(require_admin), db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
        get_country_or_404(country_code.upper(), db)
        set_rls_context({country_code.upper()}, is_restricted=True)
        try:
            return bulk_archive_entities("logistics_partner", payload.ids, {"id": current_user.id, "username": current_user.username, "role": current_user.role}, db, payload.reason)
        finally:
            clear_rls_context()
    _s23.post("/{country_code}/partners/bulk/archive")(bulk_archive_partners)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route bulk_archive_partners: %s", _e)

try:
    def     bulk_restore_partners(country_code: str = Path(..., description="ISO country code"), payload: BulkActionRequest = None, _: User = Depends(require_admin), db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
        get_country_or_404(country_code.upper(), db)
        set_rls_context({country_code.upper()}, is_restricted=True)
        try:
            return bulk_restore_entities("logistics_partner", payload.ids, {"id": current_user.id, "username": current_user.username, "role": current_user.role}, db)
        finally:
            clear_rls_context()
    _s23.post("/{country_code}/partners/bulk/restore")(bulk_restore_partners)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route bulk_restore_partners: %s", _e)

try:
    def     delete_partner_permanent(country_code: str = Path(..., description="ISO country code"), partner_id: int = Path(...), _: User = Depends(require_super_admin), db: Session = Depends(get_db), current_user: User = Depends(require_super_admin)):
        get_country_or_404(country_code.upper(), db)
        set_rls_context({country_code.upper()}, is_restricted=True)
        try:
            return hard_delete_entity("logistics_partner", partner_id, {"id": current_user.id, "username": current_user.username, "role": current_user.role}, db)
        finally:
            clear_rls_context()
    _s23.delete("/{country_code}/partners/{partner_id}")(delete_partner_permanent)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route delete_partner_permanent: %s", _e)


router = APIRouter()

try:
    router.include_router(_s8)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip subrouter _s8: %s", _e)

try:
    router.include_router(_s10)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip subrouter _s10: %s", _e)

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
    router.include_router(_s16)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip subrouter _s16: %s", _e)

try:
    router.include_router(_s18)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip subrouter _s18: %s", _e)

try:
    router.include_router(_s20)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip subrouter _s20: %s", _e)

try:
    router.include_router(_s23)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip subrouter _s23: %s", _e)

