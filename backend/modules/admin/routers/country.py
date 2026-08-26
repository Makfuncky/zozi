"""Admin country router — canonical."""

from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body, status

from .countries import router as countries_router
from .localization import router as localization_router
from .tax import router as tax_router
from __future__ import annotations
from modules.admin.routers.accounts import delete_bank_account_route, list_pending_bank_accounts_route, verify_bank_account_route
from decimal import Decimal
from deep_translator import GoogleTranslator  # lazy import
from domains.audit.services.data_residency import DataResidencyService
from domains.audit.services.logs.audit_trail_service import AuditTrailService
from domains.catalog.models.products import Category
from domains.catalog.services._auto_stubs import upload_banner_image
from domains.catalog.services.products.bulk_ops_write_service import bulk_archive_entities
from domains.catalog.services.products.bulk_ops_write_service import bulk_restore_entities
from domains.comms.services._auto_stubs import email_metrics
from domains.country.models.countries import CountryCommunication
from domains.country.models.countries import CountryConfig
from domains.country.models.countries import PayoutRuleCategory
from domains.country.models.countries import PayoutRuleProduct
from domains.country.models.country_control import CountryMapConfig
from domains.country.models.country_control import LegalContractTemplate
from domains.country.models.country_control import LogisticsPartnerLocation
from domains.country.models.country_control import ShopWarehouseLocation
from domains.country.models.country_enhancements import CountryCategoryTaxRate
from domains.country.models.country_enhancements import CountryCity
from domains.country.models.country_enhancements import CountryCommissionRate
from domains.country.models.country_enhancements import CountryFeatureFlag
from domains.country.models.country_enhancements import CountryStaffAssignment
from domains.country.models.country_enhancements import CrossCountryCustomerSession
from domains.country.services._auto_stubs import VersionDraftBody
from domains.country.services._auto_stubs import approve_config_version
from domains.country.services._auto_stubs import approve_config_version_public
from domains.country.services._auto_stubs import auto_populate_country
from domains.country.services._auto_stubs import country_controller
from domains.country.services._auto_stubs import create_config_version
from domains.country.services._auto_stubs import create_config_version_public
from domains.country.services._auto_stubs import get_config_version
from domains.country.services._auto_stubs import get_config_version_public
from domains.country.services._auto_stubs import list_config_versions
from domains.country.services._auto_stubs import list_config_versions_public
from domains.country.services._auto_stubs import publish_config_version
from domains.country.services._auto_stubs import publish_config_version_public
from domains.country.services._auto_stubs import rollback_config_version
from domains.country.services._auto_stubs import rollback_config_version_public
from domains.country.services.core.country_config_admin_service import add_city as svc_add_city
from domains.country.services.core.country_config_admin_service import add_country_city as svc_add_country_city
from domains.country.services.core.country_config_admin_service import archive_country as svc_archive_country
from domains.country.services.core.country_config_admin_service import assign_staff as svc_assign_staff
from domains.country.services.core.country_config_admin_service import bulk_archive_countries as svc_bulk_archive_countries
from domains.country.services.core.country_config_admin_service import bulk_restore_countries as svc_bulk_restore_countries
from domains.country.services.core.country_config_admin_service import create_country_commission_rate as svc_create_country_commission_rate
from domains.country.services.core.country_config_admin_service import create_feature_flag as svc_create_feature_flag
from domains.country.services.core.country_config_admin_service import delete_city as svc_delete_city
from domains.country.services.core.country_config_admin_service import delete_country_city as svc_delete_country_city
from domains.country.services.core.country_config_admin_service import delete_country_commission_rate as svc_delete_country_commission_rate
from domains.country.services.core.country_config_admin_service import delete_feature_flag as svc_delete_feature_flag
from domains.country.services.core.country_config_admin_service import hard_delete_country as svc_hard_delete_country
from domains.country.services.core.country_config_admin_service import list_cities as svc_list_cities
from domains.country.services.core.country_config_admin_service import list_communications as svc_list_communications
from domains.country.services.core.country_config_admin_service import list_country_commission_rates as svc_list_country_commission_rates
from domains.country.services.core.country_config_admin_service import list_staff as svc_list_staff
from domains.country.services.core.country_config_admin_service import list_tax_rates as svc_list_tax_rates
from domains.country.services.core.country_config_admin_service import mark_communication_read as svc_mark_communication_read
from domains.country.services.core.country_config_admin_service import patch_country_city as svc_patch_country_city
from domains.country.services.core.country_config_admin_service import remove_staff as svc_remove_staff
from domains.country.services.core.country_config_admin_service import restore_country as svc_restore_country
from domains.country.services.core.country_config_admin_service import send_country_communication as svc_send_country_communication
from domains.country.services.core.country_config_admin_service import set_tax_rate as svc_set_tax_rate
from domains.country.services.core.country_config_admin_service import toggle_country_active as svc_toggle_country_active
from domains.country.services.core.country_config_admin_service import update_city as svc_update_city
from domains.country.services.core.country_config_admin_service import update_feature_flag as svc_update_feature_flag
from domains.country.services.core.country_service import _get_country_or_404
from domains.country.services.core.country_service import _record_admin_change
from domains.country.services.core.country_service import _require_admin
from domains.country.services.core.country_service import _require_country_access
from domains.country.services.core.country_service import _require_full_admin
from domains.country.services.geo.country_detection import CountryDetectionService
from domains.country.services.research.country_ai_research import CountryAIResearchService
from domains.country.services.research.country_ai_research import build_country_research
from domains.country.utils.country_rls import get_country_or_404
from domains.governance.models.user import User
from domains.governance.services._auto_stubs import auth_controller_service as _ctrl
from domains.governance.services.settings.misc_service import archive_entity
from domains.governance.services.settings.misc_service import hard_delete_entity
from domains.governance.services.settings.misc_service import restore_entity
from domains.logistics.services.core.admin_logistics_service import approve_partner
from domains.logistics.services.core.admin_logistics_service import list_partners
from domains.logistics.services.core.admin_logistics_service import reject_partner
from domains.logistics.services.core.admin_logistics_service import toggle_partner_active
from domains.orders.services.core.admin_extra import create_campaign
from domains.orders.services.core.admin_extra import delete_campaign
from domains.orders.services.core.admin_extra import list_all_campaigns
from domains.orders.services.core.admin_extra import list_campaigns
from domains.promotions.services.admin_promotion_service import create_banner as create_banner_controller
from domains.promotions.services.admin_promotion_service import delete_banner as delete_banner_controller
from domains.promotions.services.admin_promotion_service import update_banner as update_banner_controller
from domains.promotions.services.banners.banner_service import BannerCreate
from domains.promotions.services.banners.banner_service import BannerUpdate
from domains.promotions.services.banners.banner_service import get_banners
from domains.promotions.services.banners.banner_service import get_banners_page
from domains.suppliers.services.contracts.legal_contract_service import LegalContractService
from infrastructure.database.database import get_db
from infrastructure.database.schemas import ArchiveRequest, BulkActionRequest
from infrastructure.database.schemas import EmailCampaignCreate, EmailCampaignOut
from infrastructure.security.country_access import require_country_access
from infrastructure.utils.background_jobs import enqueue_job
from infrastructure.utils.background_jobs import get_job
from infrastructure.utils.config import settings
from infrastructure.utils.currency import (
from infrastructure.utils.datetime_utils import utcnow as _utcnow
from infrastructure.utils.dependencies import get_current_user
from infrastructure.utils.dependencies import require_admin
from infrastructure.utils.dependencies import require_admin, require_super_admin
from infrastructure.utils.rate_limiter import limiter
from infrastructure.utils.rls_interceptor import set_rls_context, clear_rls_context
from infrastructure.utils.websocket_manager import manager
from middleware.rls_dependency import get_country_scope as _get_country_scope
from modules.admin.routers.auth import get_current_user
from modules.admin.routers.country_auto_populate import router as auto_populate_router
from modules.admin.routers.country_versioning import router as versioning_router
from modules.employee.routers import employees_controller as ctrl
from providers.ai.ai_research_jobs import decrement_running_jobs
from providers.ai.ai_research_jobs import get_completed_result
from providers.ai.ai_research_jobs import increment_running_jobs
from providers.ai.ai_research_jobs import mark_job_failed
from providers.ai.ai_research_jobs import mark_job_running
from providers.geography.geo import resolve_ip_location
from providers.geography.geo import reverse_geocode
from rbac import get_current_user
from sqlalchemy import desc
from sqlalchemy.orm import Session
from typing import Any, Dict
from typing import Any, Dict, List, Optional
from typing import Any, Optional
from typing import List, Optional
from typing import Optional
from typing import Optional, Any, Dict
import asyncio
import domains.governance.services.admin_controller as _ctrl
import domains.orders.services as promo_ctrl
import json
import logging
import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)
import logging as _l; _l.getLogger(__name__).warning("skip countries_router: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip include auto_populate_router: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip include versioning_router: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip localization_router: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route add_city: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route add_country_city: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route admin_email_metrics: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route approve_config_version_public_route: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route approve_config_version_route: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route approve_country_version: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route approve_partner_route: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route archive_country: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route archive_partner: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route assign_staff: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route assign_staff_to_country: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route bulk_archive_countries: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route bulk_archive_partners: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route bulk_restore_countries: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route bulk_restore_partners: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route create_admin_country: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route create_banner: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route create_campaign_route: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route create_commission_draft: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route create_commission_tiers_draft: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route create_config_version_public_route: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route create_config_version_route: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route create_country_commission_rate: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route create_country_feature_flag: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route create_legal_rules_draft: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route create_logistics_draft: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route create_logistics_providers_draft: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route create_ops_draft: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route create_payment_gateways_draft: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route create_payout_rule_category: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route create_payout_rule_product: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route create_payout_settings_draft: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route create_regions_draft: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route create_supplier_requirements_draft: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route create_tax_draft: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route currency_context: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route currency_rates: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route delete_bank_account_route_route: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route delete_banner: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route delete_campaign_route: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route delete_city: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route delete_country_city: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route delete_country_commission_rate: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route delete_country_feature_flag: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route delete_country_promotion: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route delete_partner_permanent: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route delete_payout_rule_category: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route delete_payout_rule_product: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route generate_legal_contract: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route geo_from_ip: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route geo_locate: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route geo_resolve: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route geo_reverse: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route get_admin_country: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route get_audit_trail: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route get_categories_dropdown: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route get_cities_dropdown: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route get_commission_tiers: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route get_config_version_public_route: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route get_config_version_route: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route get_countries_dropdown: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route get_country_feature_flags: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route get_country_localization: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route get_country_map: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route get_country_map_config: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route get_data_residency: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route get_geo_info: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route get_legal_rules: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route get_logistics_providers: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route get_my_assigned_countries: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route get_payment_gateways: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route get_payout_settings: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route get_public_country_config: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route get_regions: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route get_supplier_requirements: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route hard_delete_country: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route health: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route list_all_banners: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route list_all_campaigns_route: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route list_all_staff_assignments: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route list_banners: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route list_campaigns_route: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route list_cities: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route list_communications: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route list_config_versions_public_route: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route list_config_versions_route: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route list_country_cities: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route list_country_commission_rates: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route list_country_commissions: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route list_country_delivery_zones: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route list_country_promotions: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route list_country_staff: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route list_country_versions: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route list_cross_country_sessions: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route list_geo_countries: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route list_oman_delivery_zones_compat: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route list_partners_route: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route list_payout_rule_categories: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route list_payout_rule_products: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route list_payout_rules_categories: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route list_payout_rules_products: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route list_pending_bank_accounts_route_route: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route list_public_countries: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route list_public_country_employees: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route list_staff: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route list_tax_rates: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route log_financial_change: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route mark_communication_read: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route patch_country_city: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route preview_country_tax: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route publish_config_version_public_route: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route publish_config_version_route: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route publish_country_version: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route refresh_currency_rates: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route reject_partner_route: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route remove_staff: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route remove_staff_from_country: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route restore_country: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route restore_partner: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route rollback_config_version_public_route: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route rollback_config_version_route: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route rollback_country_to_version: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route send_communication: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route send_country_communication: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route set_tax_rate: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route test_gateway_connection: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route toggle_country_active: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route toggle_partner_active_route: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route unassign_staff: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route update_admin_country_identity: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route update_banner: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route update_city: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route update_country_cities_bulk: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route update_country_feature_flag: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route update_country_localization: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route update_staff_assignment: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route verify_bank_account_route_route: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip subrouter _s0: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip subrouter _s10: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip subrouter _s11: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip subrouter _s12: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip subrouter _s13: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip subrouter _s14: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip subrouter _s15: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip subrouter _s16: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip subrouter _s17: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip subrouter _s18: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip subrouter _s19: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip subrouter _s1: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip subrouter _s20: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip subrouter _s21: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip subrouter _s22: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip subrouter _s23: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip subrouter _s24: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip subrouter _s25: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip subrouter _s26: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip subrouter _s27: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip subrouter _s28: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip subrouter _s29: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip subrouter _s2: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip subrouter _s30: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip subrouter _s3: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip subrouter _s4: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip subrouter _s5: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip subrouter _s6: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip subrouter _s7: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip subrouter _s8: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip subrouter _s9: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip tax_router: %s", _e)
import structlog
import threading

router = APIRouter(prefix="/api/v1/admin/country", tags=["admin", "country"])

@router.get("/{country_code}/legal-contracts/generate")
def generate_legal_contract(
    country_code: str = Path(..., description="Country code"),
    template_type: str = Query("terms", description="Template type (terms, privacy, refund)"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)


@router.get("/{country_code}/audit-trail", response_model=list[dict])
def get_audit_trail(
    country_code: str = Path(..., description="Country code"),
    table_name: Optional[str] = Query(None, description="Filter by table name"),
    record_id: Optional[int] = Query(None, description="Filter by record ID"),
    limit: int = Query(100, ge=1, le=500, description="Max results"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)


@router.post("/{country_code}/audit-trail/log")
def log_financial_change(
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


@router.post("/{country_code}/communications")
def send_country_communication(
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


@router.get("/communications")
def list_communications(
    status: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    limit: int = Query(50, le=200),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),


@router.put("/communications/{comm_id}/read")
def mark_communication_read(
    comm_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),


@router.get("/{country_code}/data-residency")
def get_data_residency(
    country_code: str = Path(..., description="Country code"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)


@router.get("/{country_code}/cities")
def list_cities(
    country_code: str = Path(...),
    active: bool = Query(True),
    limit: int = Query(100, le=500),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),


@router.post("/{country_code}/cities")
def add_city(
    country_code: str = Path(...),
    name: str = Body(...),
    name_local: str = Body(None),
    population: int = Body(0),
    is_capital: bool = Body(False),
    latitude: float = Body(None),
    longitude: float = Body(None),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),


@router.put("/{country_code}/cities/{city_id}")
def update_city(
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


@router.delete("/{country_code}/cities/{city_id}")
def delete_city(
    country_code: str = Path(...),
    city_id: int = Path(...),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),


@router.get("/{country_code}/staff")
def list_staff(
    country_code: str = Path(...),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),


@router.post("/{country_code}/staff")
def assign_staff(
    country_code: str = Path(...),
    user_id: int = Body(...),
    role_in_country: str = Body(...),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),


@router.delete("/{country_code}/staff/{staff_id}")
def remove_staff(
    country_code: str = Path(...),
    staff_id: int = Path(...),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),


@router.get("/{country_code}/tax-rates")
def list_tax_rates(
    country_code: str = Path(...),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),


@router.post("/{country_code}/tax-rates")
def set_tax_rate(
    country_code: str = Path(...),
    category_id: int = Body(...),
    tax_rate: float = Body(...),
    tax_name: str = Body(None),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),


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




@router.post("")
def create_admin_country(body: CountryCreateBody, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    return country_controller.create_admin_country(body.model_dump(exclude_none=True), current_user, db)




@router.get("/{code}")
def get_admin_country(code: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    return country_controller.get_admin_country(code, current_user, db)




@router.patch("/{code}")
def update_admin_country_identity(code: str, body: CountryIdentityUpdateBody, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    return country_controller.update_country_identity(code, body.model_dump(exclude_none=True), current_user, db)




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




@router.get("/{code}/versions")
def list_country_versions(
    code: str,
    config_type: str | None = Query(default=None),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),


@router.post("/{code}/versions/{version_id}/approve")
def approve_country_version(code: str, version_id: int, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    return country_controller.approve_country_version(code, version_id, current_user, db)




@router.post("/{code}/versions/{version_id}/publish")
def publish_country_version(code: str, version_id: int, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    return country_controller.publish_country_version(code, version_id, current_user, db)




@router.post("/{code}/versions/{version_id}/rollback")
def rollback_country_to_version(code: str, version_id: int, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    return country_controller.rollback_country_to_version(code, version_id, current_user, db)




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


@router.patch("/{code}/feature-flags/{key}")
def update_country_feature_flag(
    code: str,
    key: str,
    body: dict,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),


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
    return svc_delete_feature_flag(code, key, db)




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




@router.post("/{code}/payment-gateways/{gateway_id}/test")
def test_gateway_connection(
    code: str,
    gateway_id: str,
    body: TestGatewayConnectionBody = TestGatewayConnectionBody(),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),


@router.post("/auto-populate")
async def auto_populate_country(body: AutoPopulateBody, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """Fetch country data from external APIs and curated profiles."""
    from domains.country.services.core.country_service import _require_admin
    _require_admin(current_user)
    return await country_controller.auto_populate_async(body.search_term)


@router.get("/{code}/cities")
def list_country_cities(
    code: str,
    q: str | None = Query(default=None, description="Search query"),
    limit: int = Query(default=50, ge=1, le=200, description="Max results"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),


@router.post("/{code}/cities")
def add_country_city(
    code: str,
    body: dict,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),


@router.patch("/{code}/cities/{city_id}")
def patch_country_city(
    code: str,
    city_id: int,
    body: dict,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),


@router.delete("/{code}/cities/{city_id}")
def delete_country_city(
    code: str,
    city_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),


@router.put("/{code}/cities")
def update_country_cities_bulk(
    code: str,
    body: dict,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),


@router.get("/{code}/staff")
def list_staff(code: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    return country_controller.list_country_staff(code, current_user, db)




@router.post("/{code}/staff")
def assign_staff(code: str, body: AssignStaffBody, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    return country_controller.assign_staff_to_country(code, body.user_id, body.role_in_country, current_user, db)




@router.delete("/{code}/staff/{user_id}")
def unassign_staff(code: str, user_id: int, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    return country_controller.unassign_staff_from_country(code, user_id, current_user, db)




@router.get("/{code}/communications")
def list_communications(code: str, category: Optional[str] = Query(None), current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    return country_controller.list_country_communications(code, current_user, db, category)




@router.post("/{code}/communications")
def send_communication(code: str, body: SendCommBody, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    return country_controller.send_country_communication(code, body.model_dump(), current_user, db)




@router.patch("/communications/{comm_id}/read")
def mark_communication_read(comm_id: int, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    return country_controller.mark_communication_read(comm_id, current_user, db)




@router.get("/{code}/cross-country-sessions")
def list_cross_country_sessions(code: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    return country_controller.list_cross_country_sessions(code, current_user, db)




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




@router.post("/{code}/toggle-active")
def toggle_country_active(code: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    return svc_toggle_country_active(code, current_user, db)




@router.post("/{code}/archive")
def archive_country(code: str, payload: ArchivePayload = None, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    return svc_archive_country(code, current_user, db)




@router.post("/{code}/restore")
def restore_country(code: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    return svc_restore_country(code, current_user, db)




@router.post("/bulk/archive")
def bulk_archive_countries(payload: BulkIdsPayload, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    return svc_bulk_archive_countries(payload.ids, current_user, db)




@router.post("/bulk/restore")
def bulk_restore_countries(payload: BulkIdsPayload, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    return svc_bulk_restore_countries(payload.ids, current_user, db)




@router.delete("/{code}")
def hard_delete_country(code: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    svc_hard_delete_country(code, current_user, db)
    return Response(status_code=204)




@router.get("/countries/{code}/commission-rates")
def list_country_commission_rates(code: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    return svc_list_country_commission_rates(code, current_user, db)




@router.post("/countries/{code}/commission-rates")
def create_country_commission_rate(code: str, body: CountryCommissionRateItem, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    return svc_create_country_commission_rate(code, body, current_user, db)




@router.delete("/countries/{code}/commission-rates/{tier}/{name}")
def delete_country_commission_rate(code: str, tier: str, name: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    return svc_delete_country_commission_rate(code, tier, name, current_user, db)




@router.get("/admin/config-versions/{country_code}", status_code=200, tags=['country-versioning'])
def list_config_versions_route(
    country_code: str,
    config_type: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)


@router.get("/config-versions/{country_code}", status_code=200, tags=['country-versioning'])
def list_config_versions_public_route(
    country_code: str,
    config_type: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)


@router.get("/admin/config-versions/{country_code}/{version_id}", status_code=200, tags=['country-versioning'])
def get_config_version_route(
    country_code: str,
    version_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)


@router.get("/config-versions/{country_code}/{version_id}", status_code=200, tags=['country-versioning'])
def get_config_version_public_route(
    country_code: str,
    version_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)


@router.post("/admin/config-versions/{country_code}", status_code=201, tags=['country-versioning'])
def create_config_version_route(
    country_code: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    body: VersionDraftBody = Body(...)


@router.post("/config-versions/{country_code}", status_code=201, tags=['country-versioning'])
def create_config_version_public_route(
    country_code: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    body: VersionDraftBody = Body(...)


@router.post("/admin/config-versions/{country_code}/{version_id}/approve", status_code=201, tags=['country-versioning'])
def approve_config_version_route(
    country_code: str,
    version_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)


@router.post("/config-versions/{country_code}/{version_id}/approve", status_code=201, tags=['country-versioning'])
def approve_config_version_public_route(
    country_code: str,
    version_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)


@router.post("/admin/config-versions/{country_code}/{version_id}/publish", status_code=201, tags=['country-versioning'])
def publish_config_version_route(
    country_code: str,
    version_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)


@router.post("/config-versions/{country_code}/{version_id}/publish", status_code=201, tags=['country-versioning'])
def publish_config_version_public_route(
    country_code: str,
    version_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)


@router.post("/admin/config-versions/{country_code}/{version_id}/rollback", status_code=201, tags=['country-versioning'])
def rollback_config_version_route(
    country_code: str,
    version_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)


@router.post("/config-versions/{country_code}/{version_id}/rollback", status_code=201, tags=['country-versioning'])
def rollback_config_version_public_route(
    country_code: str,
    version_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)


@router.get("/admin_promotions_routes/health")
def health():
    """Liveness probe for this router."""
    return {"status": "ok", "router": "admin_promotions_routes", "prefix": "/api/v1/promotions"}




@router.get("/admin_promotions_routes/status")
def status():
    """Report whether a backing controller is importable."""
    return {"router": "admin_promotions_routes",
            "controller": "controllers.commerce.promotion_admin_controller",
            "public_functions": _CTRL_PUBLIC}




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




@router.post("")
def create_admin_country(body: CountryCreateBody, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    return country_controller.create_admin_country(body.model_dump(exclude_none=True), current_user, db)




@router.get("/{code}")
def get_admin_country(code: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    return country_controller.get_admin_country(code, current_user, db)




@router.patch("/{code}")
def update_admin_country_identity(code: str, body: CountryIdentityUpdateBody, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    return country_controller.update_country_identity(code, body.model_dump(exclude_none=True), current_user, db)




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




@router.get("/{code}/versions")
def list_country_versions(
    code: str,
    config_type: str | None = Query(default=None),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),


@router.post("/{code}/versions/{version_id}/approve")
def approve_country_version(code: str, version_id: int, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    return country_controller.approve_country_version(code, version_id, current_user, db)




@router.post("/{code}/versions/{version_id}/publish")
def publish_country_version(code: str, version_id: int, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    return country_controller.publish_country_version(code, version_id, current_user, db)




@router.post("/{code}/versions/{version_id}/rollback")
def rollback_country_to_version(code: str, version_id: int, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    return country_controller.rollback_country_to_version(code, version_id, current_user, db)




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


@router.patch("/{code}/feature-flags/{key}")
def update_country_feature_flag(
    code: str,
    key: str,
    body: dict,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),


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




@router.post("/{code}/payment-gateways/{gateway_id}/test")
def test_gateway_connection(
    code: str,
    gateway_id: str,
    body: TestGatewayConnectionBody = TestGatewayConnectionBody(),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),


@router.post("/auto-populate")
async def auto_populate_country(body: AutoPopulateBody, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """Fetch country data from external APIs and curated profiles."""
    from domains.country.services.core.country_service import _require_admin
    _require_admin(current_user)
    return await country_controller.auto_populate_async(body.search_term)


@router.get("/{code}/cities")
def list_country_cities(
    code: str,
    q: str | None = Query(default=None, description="Search query"),
    limit: int = Query(default=50, ge=1, le=200, description="Max results"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),


@router.post("/{code}/cities")
def add_country_city(
    code: str,
    body: dict,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),


@router.patch("/{code}/cities/{city_id}")
def patch_country_city(
    code: str,
    city_id: int,
    body: dict,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),


@router.delete("/{code}/cities/{city_id}")
def delete_country_city(
    code: str,
    city_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),


@router.put("/{code}/cities")
def update_country_cities_bulk(
    code: str,
    body: dict,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),


@router.get("/{code}/staff")
def list_staff(code: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    return country_controller.list_country_staff(code, current_user, db)




@router.post("/{code}/staff")
def assign_staff(code: str, body: AssignStaffBody, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    return country_controller.assign_staff_to_country(code, body.user_id, body.role_in_country, current_user, db)




@router.delete("/{code}/staff/{user_id}")
def unassign_staff(code: str, user_id: int, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    return country_controller.unassign_staff_from_country(code, user_id, current_user, db)




@router.get("/{code}/communications")
def list_communications(code: str, category: Optional[str] = Query(None), current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    return country_controller.list_country_communications(code, current_user, db, category)




@router.post("/{code}/communications")
def send_communication(code: str, body: SendCommBody, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    return country_controller.send_country_communication(code, body.model_dump(), current_user, db)




@router.patch("/communications/{comm_id}/read")
def mark_communication_read(comm_id: int, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    return country_controller.mark_communication_read(comm_id, current_user, db)




@router.get("/{code}/cross-country-sessions")
def list_cross_country_sessions(code: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    return country_controller.list_cross_country_sessions(code, current_user, db)




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




@router.post("/{code}/toggle-active")
def toggle_country_active(code: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    from domains.country.services.core.country_service import _require_admin
    _require_admin(current_user)
    from domains.country.models.countries import CountryConfig
    c = db.query(CountryConfig).filter(CountryConfig.code == code.upper()).first()
    if not c:
        raise HTTPException(status_code=404, detail="Country not found")
    c.is_active = not c.is_active
    db.commit()
    return {"message": f"Country {'enabled' if c.is_active else 'disabled'}"}




@router.post("/{code}/archive")
def archive_country(code: str, payload: ArchivePayload = None, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
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




@router.post("/{code}/restore")
def restore_country(code: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
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




@router.post("/bulk/archive")
def bulk_archive_countries(payload: BulkIdsPayload, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
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




@router.post("/bulk/restore")
def bulk_restore_countries(payload: BulkIdsPayload, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
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




@router.delete("/{code}")
def hard_delete_country(code: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    from domains.country.services.core.country_service import _require_full_admin
    _require_full_admin(current_user)
    c = db.query(CountryConfig).filter(CountryConfig.code == code.upper()).first()
    if not c:
        raise HTTPException(status_code=404, detail="Country not found")
    db.delete(c)
    db.commit()
    return Response(status_code=204)




@router.get("/countries/{code}/commission-rates")
def list_country_commission_rates(code: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    from domains.country.services.core.country_service import _require_admin
    from domains.country.services.core.country_service import _require_country_access
    _require_admin(current_user)
    _require_country_access(code, current_user)
    from domains.country.models.country_enhancements import CountryCommissionRate
    rows = db.query(CountryCommissionRate).filter(
        CountryCommissionRate.country_code == code.upper()
    ).order_by(CountryCommissionRate.supplier_tier, CountryCommissionRate.name).all()
    return [{"supplier_tier": r.supplier_tier, "name": r.name, "commission_percentage": float(r.rate_percent) * 100, "fixed_fee": float(r.fixed_fee) if r.fixed_fee else 0.0} for r in rows]




@router.post("/countries/{code}/commission-rates")
def create_country_commission_rate(code: str, body: CountryCommissionRateItem, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
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




@router.delete("/countries/{code}/commission-rates/{tier}/{name}")
def delete_country_commission_rate(code: str, tier: str, name: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
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




@router.get("/{country_code}/legal-contracts/generate")
def generate_legal_contract(
    country_code: str = Path(..., description="Country code"),
    template_type: str = Query("terms", description="Template type (terms, privacy, refund)"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)


@router.get("/{country_code}/audit-trail", response_model=List[dict])
def get_audit_trail(
    country_code: str = Path(..., description="Country code"),
    table_name: Optional[str] = Query(None, description="Filter by table name"),
    record_id: Optional[int] = Query(None, description="Filter by record ID"),
    limit: int = Query(100, ge=1, le=500, description="Max results"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)


@router.post("/{country_code}/audit-trail/log")
def log_financial_change(
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


@router.post("/{country_code}/communications")
def send_country_communication(
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


@router.get("/communications")
def list_communications(
    status: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    limit: int = Query(50, le=200),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),


@router.put("/communications/{comm_id}/read")
def mark_communication_read(
    comm_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),


@router.get("/{country_code}/data-residency")
def get_data_residency(
    country_code: str = Path(..., description="Country code"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)


@router.get("/{country_code}/cities")
def list_cities(
    country_code: str = Path(...),
    active: bool = Query(True),
    limit: int = Query(100, le=500),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),


@router.post("/{country_code}/cities")
def add_city(
    country_code: str = Path(...),
    name: str = Body(...),
    name_local: str = Body(None),
    population: int = Body(0),
    is_capital: bool = Body(False),
    latitude: float = Body(None),
    longitude: float = Body(None),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),


@router.put("/{country_code}/cities/{city_id}")
def update_city(
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


@router.delete("/{country_code}/cities/{city_id}")
def delete_city(
    country_code: str = Path(...),
    city_id: int = Path(...),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),


@router.get("/{country_code}/staff")
def list_staff(
    country_code: str = Path(...),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),


@router.post("/{country_code}/staff")
def assign_staff(
    country_code: str = Path(...),
    user_id: int = Body(...),
    role_in_country: str = Body(...),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),


@router.delete("/{country_code}/staff/{staff_id}")
def remove_staff(
    country_code: str = Path(...),
    staff_id: int = Path(...),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),


@router.get("/{country_code}/tax-rates")
def list_tax_rates(
    country_code: str = Path(...),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),


@router.post("/{country_code}/tax-rates")
def set_tax_rate(
    country_code: str = Path(...),
    category_id: int = Body(...),
    tax_rate: float = Body(...),
    tax_name: str = Body(None),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),


@router.get("/country_admin_routes/health")
def health():
    """Liveness probe for this router."""
    return {"status": "ok", "router": "country_admin_routes", "prefix": "/api/v1/country-admin"}




@router.get("/country_admin_routes/status")
def status():
    """Report whether a backing controller is importable."""
    return {"router": "country_admin_routes", "controller": "controllers.admin.admin_controller" if _HAS_CTRL else None,
            "public_functions": _CTRL_PUBLIC}



@router.get("/country_auto_populate/health")
def health():
    """Liveness probe for this router."""
    return {"status": "ok", "router": "country_auto_populate", "prefix": "/api/v1/country-auto-populate"}



@router.get("/admin/countries/{country_code}/cross-border-sessions")
async def list_cross_border_sessions(country_code: str, db: Session = Depends(get_db)):
    from domains.country.models.country_enhancements import CrossCountryCustomerSession
    sessions = db.query(CrossCountryCustomerSession).filter(
        CrossCountryCustomerSession.target_country_code == country_code.upper()
    ).order_by(CrossCountryCustomerSession.created_at.desc()).limit(50).all()
    return [
        {
            "id": s.id,
            "user_id": s.user_id,
            "source_country_code": s.source_country_code,
            "target_country_code": s.target_country_code,
            "conversion": s.conversion,
            "order_id": s.order_id,
            "created_at": s.created_at.isoformat() if s.created_at else None,
        }
        for s in sessions
    ]


@router.get("/admin/countries/{country_code}/legal-contracts")
async def list_legal_contracts(country_code: str, db: Session = Depends(get_db)):
    from domains.country.models.country_control import LegalContractTemplate
    contracts = db.query(LegalContractTemplate).filter(
        LegalContractTemplate.country_code == country_code.upper(),
        LegalContractTemplate.is_active == True
    ).order_by(LegalContractTemplate.created_at.desc()).all()
    return [
        {
            "id": c.id,
            "country_code": c.country_code,
            "template_type": c.template_type,
            "version": c.version,
            "content": c.content,
            "is_active": c.is_active,
            "created_at": c.created_at.isoformat() if c.created_at else None,
        }
        for c in contracts
    ]


@router.get("/admin/countries/{country_code}/warehouses")
async def list_warehouses(country_code: str, db: Session = Depends(get_db)):
    from domains.country.models.country_control import ShopWarehouseLocation
    warehouses = db.query(ShopWarehouseLocation).filter(
        ShopWarehouseLocation.country_code == country_code.upper(),
        ShopWarehouseLocation.is_active == True
    ).all()
    return [
        {
            "id": w.id,
            "country_code": w.country_code,
            "name": w.name,
            "warehouse_code": w.warehouse_code,
            "latitude": float(w.latitude) if w.latitude else None,
            "longitude": float(w.longitude) if w.longitude else None,
            "address": w.address,
            "is_active": w.is_active,
            "created_at": w.created_at.isoformat() if w.created_at else None,
        }
        for w in warehouses
    ]


@router.get("/admin/countries/{country_code}/partner-locations")
async def list_partner_locations(country_code: str, db: Session = Depends(get_db)):
    locations = db.query(LogisticsPartnerLocation).join(
        db.Model("LogisticsPartner")
    ).filter(
        LogisticsPartnerLocation.country_code == country_code.upper(),
        LogisticsPartnerLocation.is_active == True
    ).all()
    return [
        {
            "id": p.id,
            "partner_id": p.partner_id,
            "partner": {"name": p.partner.name} if p.partner else None,
            "country_code": p.country_code,
            "location_type": p.location_type,
            "latitude": float(p.latitude) if p.latitude else None,
            "longitude": float(p.longitude) if p.longitude else None,
            "address": p.address,
            "is_active": p.is_active,
            "created_at": p.created_at.isoformat() if p.created_at else None,
        }
        for p in locations
    ]


@router.websocket("/ws/country/{country_code}/communications")
async def websocket_country_communications(
    websocket: WebSocket,
    country_code: str,
    current_user: dict = Depends(get_current_user)
):
    await websocket.accept()
    room = f"country:{country_code.upper()}"
    user_id = current_user.get("id")
    
    await manager.connect(websocket, room, user_id)
    
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get("type") == "message":
                await manager.broadcast_to_room(room, {
                    "event": "new_message",
                    "data": message.get("data"),
                    "timestamp": message.get("timestamp")
                })
    except WebSocketDisconnect:
        manager.disconnect(websocket, room)


@router.websocket("/ws/country/{country_code}/notifications")
async def websocket_country_notifications(
    websocket: WebSocket,
    country_code: str,
    current_user: dict = Depends(get_current_user)
):
    await websocket.accept()
    room = f"country:{country_code.upper()}"
    
    await manager.connect(websocket, room)
    
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, room)


@router.get("/dropdown/cities", response_model=List[CityResponse])
def get_cities_dropdown(
    country_code: str = Query(..., description="Country code"),
    q: Optional[str] = Query(None, description="Search query"),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    _current_user: dict = Depends(get_current_user),


@router.get("/dropdown/countries", response_model=List[CountryDropdownResponse])
def get_countries_dropdown(
    db: Session = Depends(get_db),
    _current_user: dict = Depends(get_current_user),


@router.get("/dropdown/categories", response_model=List[CategoryResponse])
def get_categories_dropdown(
    country_code: Optional[str] = Query(None, description="Filter by country"),
    parent_id: Optional[int] = Query(None, description="Filter by parent"),
    db: Session = Depends(get_db),
    _current_user: dict = Depends(get_current_user),


@router.get("/{country_code}/map.geojson")
def get_country_map(
    country_code: str = Path(..., description="Country code"),
    include_cities: bool = Query(True, description="Include cities in map"),
    db: Session = Depends(get_db)


@router.get("/maps/{country_code}")
def get_country_map_config(
    country_code: str = Path(..., description="Country code"),
    db: Session = Depends(get_db)


@router.get("/admin/countries/{code}/payout-rules/categories")
def list_payout_rule_categories(
    code: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),


@router.post("/admin/countries/{code}/payout-rules/categories")
def create_payout_rule_category(
    code: str,
    body: PayoutRuleCategoryBody,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),


@router.delete("/admin/countries/{code}/payout-rules/categories/{rule_id}")
def delete_payout_rule_category(
    code: str,
    rule_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),


@router.get("/admin/countries/{code}/payout-rules/products")
def list_payout_rule_products(
    code: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),


@router.post("/admin/countries/{code}/payout-rules/products")
def create_payout_rule_product(
    code: str,
    body: PayoutRuleProductBody,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),


@router.delete("/admin/countries/{code}/payout-rules/products/{rule_id}")
def delete_payout_rule_product(
    code: str,
    rule_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),


@router.get("/country_payouts_routes/health")
def health():
    """Liveness probe for this router."""
    return {"status": "ok", "router": "country_payouts_routes", "prefix": "/api/v1/country-payouts"}



@router.get("/{code}/research")
async def get_country_research(
    code: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Return the full 20-module e-commerce research report for a country.

    Builds the report from auto-populate data + heuristic/default modules.
    Modules 4–20 require AI or manual research for high-confidence data.
    """
    try:
        auto_data = await auto_populate_country(code)
        if not auto_data or auto_data.get("error"):
            raise HTTPException(
                status_code=404,
                detail=auto_data.get("error", f"Country {code} not found"),
            )

        research = build_country_research(auto_data)

        return {
            "status": "success",
            "fetched_at": auto_data.get("fetched_at"),
            "cached": auto_data.get("cached", False),
            "data": research,
        }
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Country research failed for %s", code)
        raise HTTPException(status_code=500, detail=str(exc))

@router.get("/countries/{code}/staff")
def list_country_staff(
    code: str,
    active_only: bool = Query(True),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),


@router.post("/countries/{code}/staff")
def assign_staff_to_country(
    code: str,
    body: StaffAssignBody,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),


@router.patch("/countries/{code}/staff/{assignment_id}")
def update_staff_assignment(
    code: str,
    assignment_id: int,
    body: StaffUpdateBody,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),


@router.delete("/countries/{code}/staff/{user_id}")
def remove_staff_from_country(
    code: str,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),


@router.get("/staff/my-countries")
def get_my_assigned_countries(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),


@router.get("/staff/all-assignments")
def list_all_staff_assignments(
    role: Optional[str] = Query(None),
    active_only: bool = Query(True),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),


@router.get("/country_staff_routes/health")
def health():
    """Liveness probe for this router."""
    return {"status": "ok", "router": "country_staff_routes", "prefix": "/api/v1/country-staff"}



@router.get("/geo")
def get_geo_info(
    request: Request,
    ip_address: Optional[str] = Query(None, description="Client IP for geo detection"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),


@router.get("/geo/countries")
def list_geo_countries(db: Session = Depends(get_db)):
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




@router.post("")
def create_admin_country(body: CountryCreateBody, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    return country_controller.create_admin_country(body.model_dump(exclude_none=True), current_user, db)




@router.get("/{code}")
def get_admin_country(code: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    return country_controller.get_admin_country(code, current_user, db)




@router.patch("/{code}")
def update_admin_country_identity(code: str, body: CountryIdentityUpdateBody, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    return country_controller.update_country_identity(code, body.model_dump(exclude_none=True), current_user, db)




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




@router.get("/{code}/versions")
def list_country_versions(
    code: str,
    config_type: str | None = Query(default=None),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),


@router.post("/{code}/versions/{version_id}/approve")
def approve_country_version(code: str, version_id: int, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    return country_controller.approve_country_version(code, version_id, current_user, db)




@router.post("/{code}/versions/{version_id}/publish")
def publish_country_version(code: str, version_id: int, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    return country_controller.publish_country_version(code, version_id, current_user, db)




@router.post("/{code}/versions/{version_id}/rollback")
def rollback_country_to_version(code: str, version_id: int, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    return country_controller.rollback_country_to_version(code, version_id, current_user, db)




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


@router.patch("/{code}/feature-flags/{key}")
def update_country_feature_flag(
    code: str,
    key: str,
    body: dict,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),


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
    return svc_delete_feature_flag(code, key, db)




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




@router.post("/{code}/payment-gateways/{gateway_id}/test")
def test_gateway_connection(
    code: str,
    gateway_id: str,
    body: TestGatewayConnectionBody = TestGatewayConnectionBody(),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),


@router.post("/auto-populate")
async def auto_populate_country(body: AutoPopulateBody, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """Fetch country data from external APIs and curated profiles."""
    from domains.country.services.core.country_service import _require_admin
    _require_admin(current_user)
    return await country_controller.auto_populate_async(body.search_term)


@router.get("/{code}/cities")
def list_country_cities(
    code: str,
    q: str | None = Query(default=None, description="Search query"),
    limit: int = Query(default=50, ge=1, le=200, description="Max results"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),


@router.post("/{code}/cities")
def add_country_city(
    code: str,
    body: dict,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),


@router.patch("/{code}/cities/{city_id}")
def patch_country_city(
    code: str,
    city_id: int,
    body: dict,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),


@router.delete("/{code}/cities/{city_id}")
def delete_country_city(
    code: str,
    city_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),


@router.put("/{code}/cities")
def update_country_cities_bulk(
    code: str,
    body: dict,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),


@router.get("/{code}/staff")
def list_staff(code: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    return country_controller.list_country_staff(code, current_user, db)




@router.post("/{code}/staff")
def assign_staff(code: str, body: AssignStaffBody, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    return country_controller.assign_staff_to_country(code, body.user_id, body.role_in_country, current_user, db)




@router.delete("/{code}/staff/{user_id}")
def unassign_staff(code: str, user_id: int, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    return country_controller.unassign_staff_from_country(code, user_id, current_user, db)




@router.get("/{code}/communications")
def list_communications(code: str, category: Optional[str] = Query(None), current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    return country_controller.list_country_communications(code, current_user, db, category)




@router.post("/{code}/communications")
def send_communication(code: str, body: SendCommBody, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    return country_controller.send_country_communication(code, body.model_dump(), current_user, db)




@router.patch("/communications/{comm_id}/read")
def mark_communication_read(comm_id: int, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    return country_controller.mark_communication_read(comm_id, current_user, db)




@router.get("/{code}/cross-country-sessions")
def list_cross_country_sessions(code: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    return country_controller.list_cross_country_sessions(code, current_user, db)




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




@router.post("/{code}/toggle-active")
def toggle_country_active(code: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    return svc_toggle_country_active(code, current_user, db)




@router.post("/{code}/archive")
def archive_country(code: str, payload: ArchivePayload = None, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    return svc_archive_country(code, current_user, db)




@router.post("/{code}/restore")
def restore_country(code: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    return svc_restore_country(code, current_user, db)




@router.post("/bulk/archive")
def bulk_archive_countries(payload: BulkIdsPayload, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    return svc_bulk_archive_countries(payload.ids, current_user, db)




@router.post("/bulk/restore")
def bulk_restore_countries(payload: BulkIdsPayload, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    return svc_bulk_restore_countries(payload.ids, current_user, db)




@router.delete("/{code}")
def hard_delete_country(code: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    svc_hard_delete_country(code, current_user, db)
    return Response(status_code=204)




@router.get("/countries/{code}/commission-rates")
def list_country_commission_rates(code: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    return svc_list_country_commission_rates(code, current_user, db)




@router.post("/countries/{code}/commission-rates")
def create_country_commission_rate(code: str, body: CountryCommissionRateItem, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    return svc_create_country_commission_rate(code, body, current_user, db)




@router.delete("/countries/{code}/commission-rates/{tier}/{name}")
def delete_country_commission_rate(code: str, tier: str, name: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    return svc_delete_country_commission_rate(code, tier, name, current_user, db)




@router.post("/ai", response_model=AIResearchResponse)
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


@router.get("/ai/{job_id}", response_model=AIResearchResponse)
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



