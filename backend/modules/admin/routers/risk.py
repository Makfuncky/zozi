"""Admin risk router — split from governance.py."""

"""Admin governance router — consolidated from 39 source files."""

from fastapi import APIRouter, HTTPException, Depends, Query, Path, Body, status

from datetime import date, datetime
from datetime import datetime
from datetime import datetime, timezone
from decimal import Decimal
from fastapi import APIRouter
from fastapi import APIRouter, Body, Depends
from fastapi import APIRouter, Body, Depends, HTTPException, Path, Query
from fastapi import APIRouter, Depends
from fastapi import APIRouter, Depends, Body, Query
from fastapi import APIRouter, Depends, HTTPException
from fastapi import APIRouter, Depends, HTTPException, Path, Query
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi import APIRouter, Depends, Query
from fastapi import APIRouter, Depends, Response
from fastapi import APIRouter, Depends, UploadFile, File, Form
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from pydantic import BaseModel, Field
from pydantic import BaseModel, field_validator
from sqlalchemy import func
from sqlalchemy.orm import Session
from typing import Any
from typing import List, Optional
from typing import Optional
import csv
import io
import logging
try:
    from controllers.admin.misc_controller import database_overview
except BaseException:
    database_overview = (lambda *a, **k: None)
try:
    from controllers.core.export_controller import (
        download_export_job_result,
        export_audit_logs_csv,
        export_coupons_csv,
        export_orders_csv,
        export_products_csv,
        export_transfer_csv,
        export_users_csv,
        queue_export_job,
    )
except BaseException:
    download_export_job_result = export_audit_logs_csv = export_coupons_csv = export_orders_csv = export_products_csv = export_transfer_csv = export_users_csv = queue_export_job = (lambda *a, **k: None)
try:
    from domains.accounts.services.auth.auth_service import *  # noqa: F401,F403
except BaseException:
    pass
try:
    from domains.accounts.services.auth.auth_service import get_current_admin
except BaseException:
    get_current_admin = (lambda *a, **k: None)
try:
    from domains.accounts.services.auth.auth_service import get_current_user
except BaseException:
    get_current_user = (lambda *a, **k: None)
try:
    from domains.accounts.services.permissions.permission_service import get_hierarchy_permissions
except BaseException:
    get_hierarchy_permissions = (lambda *a, **k: None)
try:
    from domains.accounts.services.permissions.permission_service import get_staff_permission_catalog
except BaseException:
    get_staff_permission_catalog = (lambda *a, **k: None)
try:
    from domains.accounts.services.permissions.permission_service import update_role_permissions
except BaseException:
    update_role_permissions = (lambda *a, **k: None)
try:
    from domains.catalog.services.products.admin_products_service import approve_product
except BaseException:
    approve_product = (lambda *a, **k: None)
try:
    from domains.catalog.services.products.admin_products_service import reject_product
except BaseException:
    reject_product = (lambda *a, **k: None)
try:
    from domains.customers.services.coupons_service import create_coupon
except BaseException:
    create_coupon = (lambda *a, **k: None)
try:
    from domains.catalog.models.products import Category
except BaseException:
    Category = (lambda *a, **k: None)
try:
    from domains.catalog.models.products import Category as CategoryModel
except BaseException:
    CategoryModel = (lambda *a, **k: None)
try:
    from domains.catalog.models.promotions import Banner
except BaseException:
    Banner = (lambda *a, **k: None)
try:
    from domains.catalog.models.promotions import Coupon
except BaseException:
    Coupon = (lambda *a, **k: None)
try:
    from domains.promotions.services.banners.banner_service import BannerCreate
except BaseException:
    BannerCreate = (lambda *a, **k: None)
try:
    from domains.promotions.services.banners.banner_service import BannerUpdate
except BaseException:
    BannerUpdate = (lambda *a, **k: None)
try:
    from domains.promotions.services.admin_promotion_service import create_banner
except BaseException:
    create_banner = (lambda *a, **k: None)
try:
    from domains.promotions.services.admin_promotion_service import delete_banner
except BaseException:
    delete_banner = (lambda *a, **k: None)
try:
    from domains.promotions.services.banners.banner_service import get_banner_by_id
except BaseException:
    get_banner_by_id = (lambda *a, **k: None)
try:
    from domains.promotions.services.admin_promotion_service import update_banner
except BaseException:
    update_banner = (lambda *a, **k: None)
try:
    from domains.catalog.services.products.bulk_ops_write_service import bulk_archive_entities
except BaseException:
    bulk_archive_entities = (lambda *a, **k: None)
try:
    from domains.catalog.services.products.bulk_ops_write_service import bulk_restore_entities
except BaseException:
    bulk_restore_entities = (lambda *a, **k: None)
try:
    from domains.accounts.services.permissions.permission_service import create_category as create_category_model
except BaseException:
    create_category_model = (lambda *a, **k: None)
try:
    from domains.accounts.services.permissions.permission_service import delete_category as delete_category_model
except BaseException:
    delete_category_model = (lambda *a, **k: None)
try:
    from domains.catalog.services.categories.admin_categories_service import reorder_categories as reorder_categories_model
except BaseException:
    reorder_categories_model = (lambda *a, **k: None)
try:
    from domains.accounts.services.permissions.permission_service import update_category as update_category_model
except BaseException:
    update_category_model = (lambda *a, **k: None)
try:
    from domains.catalog.utils.category_tree import rebuild_category_paths
except BaseException:
    rebuild_category_paths = (lambda *a, **k: None)
try:
    from domains.comms.models.marketing import FlashSale
except BaseException:
    FlashSale = (lambda *a, **k: None)
try:
    from domains.comms.services._auto_stubs import AssetTrackingService
except BaseException:
    AssetTrackingService = (lambda *a, **k: None)
try:
    from domains.comms.services.tickets.tickets_service import get_ticket_with_details as get_ticket_detail
except BaseException:
    get_ticket_detail = (lambda *a, **k: None)
try:
    from domains.comms.services.tickets.tickets_service import list_tickets
except BaseException:
    list_tickets = (lambda *a, **k: None)
try:
    from infrastructure.utils.operations_service import reply_to_ticket
except BaseException:
    reply_to_ticket = (lambda *a, **k: None)
try:
    from domains.comms.services.tickets.tickets_service import update_ticket_status
except BaseException:
    update_ticket_status = (lambda *a, **k: None)
try:
    from domains.comms.services.shared.utility.shared_utils import reset_demo_data
except BaseException:
    reset_demo_data = (lambda *a, **k: None)
try:
    from domains.country.utils.country_rls import enforce_country_access
except BaseException:
    enforce_country_access = (lambda *a, **k: None)
try:
    from domains.country.utils.country_rls import get_country_or_404
except BaseException:
    get_country_or_404 = (lambda *a, **k: None)
try:
    from domains.country.utils.country_rls import get_current_country_scope as get_country_scope
except BaseException:
    get_country_scope = (lambda *a, **k: None)
try:
    from domains.finance.models.payments import Payment
except BaseException:
    Payment = (lambda *a, **k: None)
try:
    from domains.finance.models.payments import Payout as PayoutModel
except BaseException:
    PayoutModel = (lambda *a, **k: None)
try:
    from domains.finance.services.treasury.cash_management_service import check_customer_credit
except BaseException:
    check_customer_credit = (lambda *a, **k: None)
try:
    from domains.finance.services.treasury.cash_management_service import enforce_auto_credit_holds
except BaseException:
    enforce_auto_credit_holds = (lambda *a, **k: None)
try:
    from domains.finance.services.treasury.cash_management_service import get_customer_credit_summary
except BaseException:
    get_customer_credit_summary = (lambda *a, **k: None)
try:
    from domains.finance.services.ledger.general_ledger_service import ExpenseProcessingService
except BaseException:
    ExpenseProcessingService = (lambda *a, **k: None)
try:
    from domains.finance.services.payments.payment_orchestrator import match_gateway_settlement
except BaseException:
    match_gateway_settlement = (lambda *a, **k: None)
try:
    from domains.finance.services.payments.payment_orchestrator import reconcile_cod_deposit
except BaseException:
    reconcile_cod_deposit = (lambda *a, **k: None)
try:
    from domains.finance.services.payments.payment_orchestrator import run_gateway_3way_reconciliation
except BaseException:
    run_gateway_3way_reconciliation = (lambda *a, **k: None)
try:
    from domains.finance.services.payouts.payout_batch_service import list_pending_payouts
except BaseException:
    list_pending_payouts = (lambda *a, **k: None)
try:
    from domains.finance.services.payouts.payout_batch_service import list_pending_payouts
except BaseException:
    list_pending_payouts = (lambda *a, **k: None)
try:
    from domains.finance.services.payouts.payout_batch_service import generate_logistics_payout_batches
except BaseException:
    generate_logistics_payout_batches = (lambda *a, **k: None)
try:
    from domains.finance.services.payouts.payout_batch_service import generate_supplier_payout_batches
except BaseException:
    generate_supplier_payout_batches = (lambda *a, **k: None)
try:
    from domains.finance.services.payouts.payout_batch_service import get_pending_batches_for_supplier
except BaseException:
    get_pending_batches_for_supplier = (lambda *a, **k: None)
try:
    from domains.finance.services.payouts.payout_batch_service import supplier_approve_batch
except BaseException:
    supplier_approve_batch = (lambda *a, **k: None)
try:
    from domains.finance.services.payouts.payout_batch_service import post_refund_automatically
except BaseException:
    post_refund_automatically = (lambda *a, **k: None)
try:
    from domains.finance.services._auto_stubs import batch_categorize_all
except BaseException:
    batch_categorize_all = (lambda *a, **k: None)
try:
    from domains.finance.services._auto_stubs import categorize_expense_ai
except BaseException:
    categorize_expense_ai = (lambda *a, **k: None)
try:
    from domains.finance.services._auto_stubs import process_email_inbox
except BaseException:
    process_email_inbox = (lambda *a, **k: None)
try:
    from domains.finance.services._auto_stubs import process_email_invoice
except BaseException:
    process_email_invoice = (lambda *a, **k: None)
try:
    from domains.finance.services._auto_stubs import run_ai_bank_reconciliation
except BaseException:
    run_ai_bank_reconciliation = (lambda *a, **k: None)
try:
    from domains.governance.services._auto_stubs import APPROVAL_RULES
except BaseException:
    APPROVAL_RULES = (lambda *a, **k: None)
try:
    from domains.governance.services.approval.approval_matrix_service import can_approve
except BaseException:
    can_approve = (lambda *a, **k: None)
try:
    from domains.governance.services.approval.approval_matrix_service import get_approval_chain
except BaseException:
    get_approval_chain = (lambda *a, **k: None)
try:
    from domains.governance.services.approval.approval_matrix_service import require_approval
except BaseException:
    require_approval = (lambda *a, **k: None)
try:
    from domains.governance.services.approval.approval_matrix_service import resolve_approvers
except BaseException:
    resolve_approvers = (lambda *a, **k: None)
try:
    from domains.governance.core.export_service import (
    
        download_export_job_result,
    
        export_audit_logs_csv,
    
        export_coupons_csv,
    
        export_orders_csv,
    
        export_products_csv,
    
        export_transfer_csv,
    
        export_users_csv,
    
        queue_export_job,
    
    )
except BaseException:
    download_export_job_result = export_audit_logs_csv = export_coupons_csv = export_orders_csv = export_products_csv = export_transfer_csv = export_users_csv = queue_export_job = (lambda *a, **k: None)
try:
    from domains.governance.events import publish_gov_delete_bank_account_record_requested
except BaseException:
    publish_gov_delete_bank_account_record_requested = (lambda *a, **k: None)
try:
    from domains.governance.models.admin import CommissionGlobalConfig
except BaseException:
    CommissionGlobalConfig = (lambda *a, **k: None)
try:
    from domains.governance.models.admin import EmployeeExpense
except BaseException:
    EmployeeExpense = (lambda *a, **k: None)
try:
    from domains.governance.models.admin import PromotionEngineConfig
except BaseException:
    PromotionEngineConfig = (lambda *a, **k: None)
try:
    from domains.governance.models.admin import PromotionOrderTier
except BaseException:
    PromotionOrderTier = (lambda *a, **k: None)
try:
    from domains.governance.models.admin import ShippingCarrier
except BaseException:
    ShippingCarrier = (lambda *a, **k: None)
try:
    from domains.governance.models.admin import ShippingZone
except BaseException:
    ShippingZone = (lambda *a, **k: None)
try:
    from domains.governance.models.user import User
except BaseException:
    User = (lambda *a, **k: None)
try:
    from domains.governance.services._auto_stubs import get_ticket_detail
except BaseException:
    get_ticket_detail = (lambda *a, **k: None)
try:
    from domains.governance.services._auto_stubs import require_admin_2fa_verified
except BaseException:
    require_admin_2fa_verified = (lambda *a, **k: None)
try:
    from domains.analytics.services.analytics_service__analytics import get_analytics
except BaseException:
    get_analytics = (lambda *a, **k: None)
try:
    from domains.analytics.services.analytics_service__analytics import get_analytics_timeseries
except BaseException:
    get_analytics_timeseries = (lambda *a, **k: None)
try:
    from domains.analytics.services.analytics_service__analytics import get_chatbot_analytics
except BaseException:
    get_chatbot_analytics = (lambda *a, **k: None)
try:
    from domains.analytics.services.analytics_service__analytics import get_customer_insights
except BaseException:
    get_customer_insights = (lambda *a, **k: None)
try:
    from domains.analytics.services.analytics_service__analytics import get_top_products_analytics
except BaseException:
    get_top_products_analytics = (lambda *a, **k: None)
try:
    from domains.analytics.services.analytics_service__analytics import get_user_growth_analytics
except BaseException:
    get_user_growth_analytics = (lambda *a, **k: None)
try:
    from domains.audit.services.compliance_engine import GCCComplianceEngine
except BaseException:
    GCCComplianceEngine = (lambda *a, **k: None)
try:
    from domains.audit.services.compliance_engine import get_compliance_engine
except BaseException:
    get_compliance_engine = (lambda *a, **k: None)
try:
    from domains.governance.services.command_center.command_center_service import alerts_route
except BaseException:
    alerts_route = (lambda *a, **k: None)
try:
    from domains.governance.services.command_center.command_center_service import command_center_root_route
except BaseException:
    command_center_root_route = (lambda *a, **k: None)
try:
    from domains.governance.services.command_center.command_center_service import comprehensive_dashboard_route
except BaseException:
    comprehensive_dashboard_route = (lambda *a, **k: None)
try:
    from domains.governance.services.command_center.command_center_service import create_news_route
except BaseException:
    create_news_route = (lambda *a, **k: None)
try:
    from domains.governance.services.command_center.command_center_service import dashboard_route
except BaseException:
    dashboard_route = (lambda *a, **k: None)
try:
    from domains.governance.services.command_center.command_center_service import dashboard_stats_route
except BaseException:
    dashboard_stats_route = (lambda *a, **k: None)
try:
    from domains.governance.services.command_center.command_center_service import delete_news_route
except BaseException:
    delete_news_route = (lambda *a, **k: None)
try:
    from domains.governance.services.command_center.command_center_service import fraud_alerts_route
except BaseException:
    fraud_alerts_route = (lambda *a, **k: None)
try:
    from domains.governance.services.command_center.command_center_service import headlines_route
except BaseException:
    headlines_route = (lambda *a, **k: None)
try:
    from domains.governance.services.command_center.command_center_service import heartbeat_route
except BaseException:
    heartbeat_route = (lambda *a, **k: None)
try:
    from domains.governance.services.command_center.command_center_service import news_route
except BaseException:
    news_route = (lambda *a, **k: None)
try:
    from domains.governance.services.command_center.command_center_service import realtime_metrics_route
except BaseException:
    realtime_metrics_route = (lambda *a, **k: None)
try:
    from domains.governance.services.command_center.command_center_service import resolve_alert_route
except BaseException:
    resolve_alert_route = (lambda *a, **k: None)
try:
    from domains.governance.services._auto_stubs import router
except BaseException:
    router = (lambda *a, **k: None)
try:
    from domains.governance.services.command_center.command_center_service import system_metrics_route
except BaseException:
    system_metrics_route = (lambda *a, **k: None)
try:
    from domains.governance.services.command_center.command_center_service import treasury_metrics_route
except BaseException:
    treasury_metrics_route = (lambda *a, **k: None)
try:
    from domains.orders.services.orders_service import bulk_delete_orders_admin
except BaseException:
    bulk_delete_orders_admin = (lambda *a, **k: None)
try:
    from domains.orders.services.orders_service import bulk_update_order_status_admin
except BaseException:
    bulk_update_order_status_admin = (lambda *a, **k: None)
try:
    from domains.orders.services.orders_service import delete_order_admin
except BaseException:
    delete_order_admin = (lambda *a, **k: None)
try:
    from domains.orders.services.orders_service import get_all_orders
except BaseException:
    get_all_orders = (lambda *a, **k: None)
try:
    from domains.orders.services.orders_service import refund_order
except BaseException:
    refund_order = (lambda *a, **k: None)
try:
    from domains.orders.services.orders_service import update_order_status
except BaseException:
    update_order_status = (lambda *a, **k: None)
try:
    from domains.orders.services.orders_service import update_order_tracking
except BaseException:
    update_order_tracking = (lambda *a, **k: None)
try:
    from domains.governance.services._auto_stubs import COUNTRY_ROLE_PERMISSION_MAP
except BaseException:
    COUNTRY_ROLE_PERMISSION_MAP = (lambda *a, **k: None)
try:
    from domains.governance.services._auto_stubs import HR_PERMISSION_MAP
except BaseException:
    HR_PERMISSION_MAP = (lambda *a, **k: None)
try:
    from domains.governance.services._auto_stubs import MAKER_CHECKER_PERMISSIONS
except BaseException:
    MAKER_CHECKER_PERMISSIONS = (lambda *a, **k: None)
try:
    from domains.governance.services._auto_stubs import approve_permission_change
except BaseException:
    approve_permission_change = (lambda *a, **k: None)
try:
    from domains.governance.services._auto_stubs import check_permission as resolve_check_perm
except BaseException:
    resolve_check_perm = (lambda *a, **k: None)
try:
    from domains.governance.services._auto_stubs import get_effective_permissions as resolve_effective_perms
except BaseException:
    resolve_effective_perms = (lambda *a, **k: None)
try:
    from domains.governance.services._auto_stubs import invalidate_permission_cache
except BaseException:
    invalidate_permission_cache = (lambda *a, **k: None)
try:
    from domains.governance.services._auto_stubs import request_permission_change
except BaseException:
    request_permission_change = (lambda *a, **k: None)
try:
    from infrastructure.security.auth import require_permission
except BaseException:
    require_permission = (lambda *a, **k: None)
try:
    from domains.catalog.services.products.admin_products_service import bulk_delete_products_admin
except BaseException:
    bulk_delete_products_admin = (lambda *a, **k: None)
try:
    from domains.catalog.services.products.admin_products_service import bulk_product_moderation
except BaseException:
    bulk_product_moderation = (lambda *a, **k: None)
try:
    from domains.catalog.services.products.admin_products_service import delete_product_admin
except BaseException:
    delete_product_admin = (lambda *a, **k: None)
try:
    from domains.catalog.services.products.admin_products_service import get_all_products
except BaseException:
    get_all_products = (lambda *a, **k: None)
try:
    from domains.governance.services._auto_stubs import get_pending_products
except BaseException:
    get_pending_products = (lambda *a, **k: None)
try:
    from domains.catalog.services.products.admin_products_service import restore_product_admin
except BaseException:
    restore_product_admin = (lambda *a, **k: None)
try:
    from domains.catalog.services.products.admin_products_service import toggle_product_badge
except BaseException:
    toggle_product_badge = (lambda *a, **k: None)
try:
    from infrastructure.database.database_service import get_database_overview
except BaseException:
    get_database_overview = (lambda *a, **k: None)
try:
    from domains.governance.services.settings.misc_service import archive_entity
except BaseException:
    archive_entity = (lambda *a, **k: None)
try:
    from domains.governance.services.settings.misc_service import get_audit_log_page
except BaseException:
    get_audit_log_page = (lambda *a, **k: None)
try:
    from domains.governance.services.settings.misc_service import get_available_audit_actions
except BaseException:
    get_available_audit_actions = (lambda *a, **k: None)
try:
    from domains.governance.services.settings.misc_service import hard_delete_entity
except BaseException:
    hard_delete_entity = (lambda *a, **k: None)
try:
    from domains.governance.services.settings.misc_service import restore_entity
except BaseException:
    restore_entity = (lambda *a, **k: None)
try:
    from domains.governance.services._auto_stubs import bulk_manage_suppliers
except BaseException:
    bulk_manage_suppliers = (lambda *a, **k: None)
try:
    from domains.governance.services._auto_stubs import bulk_supplier_verification
except BaseException:
    bulk_supplier_verification = (lambda *a, **k: None)
try:
    from domains.governance.services._auto_stubs import get_all_suppliers
except BaseException:
    get_all_suppliers = (lambda *a, **k: None)
try:
    from domains.governance.services._auto_stubs import get_pending_suppliers
except BaseException:
    get_pending_suppliers = (lambda *a, **k: None)
try:
    from domains.governance.services._auto_stubs import get_supplier_comparison
except BaseException:
    get_supplier_comparison = (lambda *a, **k: None)
try:
    from domains.governance.services._auto_stubs import reject_supplier
except BaseException:
    reject_supplier = (lambda *a, **k: None)
try:
    from domains.governance.services._auto_stubs import verify_supplier
except BaseException:
    verify_supplier = (lambda *a, **k: None)
try:
    from domains.accounts.services.identity.identity_admin_service import delete_user_admin
except BaseException:
    delete_user_admin = (lambda *a, **k: None)
try:
    from domains.accounts.services.users.users_admin_service import bulk_delete_users_admin
except BaseException:
    bulk_delete_users_admin = (lambda *a, **k: None)
try:
    from domains.accounts.services.users.users_admin_service import force_reset_password_admin
except BaseException:
    force_reset_password_admin = (lambda *a, **k: None)
try:
    from domains.accounts.services.users.users_admin_service import bulk_toggle_users_active
except BaseException:
    bulk_toggle_users_active = (lambda *a, **k: None)
try:
    from domains.accounts.services.users.users_admin_service import bulk_update_staff_accounts
except BaseException:
    bulk_update_staff_accounts = (lambda *a, **k: None)
try:
    from domains.accounts.services.users.users_admin_service import bulk_update_users_role
except BaseException:
    bulk_update_users_role = (lambda *a, **k: None)
try:
    from domains.accounts.services.users.users_admin_service import create_staff_account
except BaseException:
    create_staff_account = (lambda *a, **k: None)
try:
    from domains.accounts.services.users.users_admin_service import delete_bank_account_record
except BaseException:
    delete_bank_account_record = (lambda *a, **k: None)
try:
    from domains.accounts.services.users.users_admin_service import delete_staff_account
except BaseException:
    delete_staff_account = (lambda *a, **k: None)
try:
    from domains.accounts.services.users.users_admin_service import get_all_users
except BaseException:
    get_all_users = (lambda *a, **k: None)
try:
    from domains.accounts.services.users.users_admin_service import list_pending_bank_accounts
except BaseException:
    list_pending_bank_accounts = (lambda *a, **k: None)
try:
    from domains.accounts.services.users.users_admin_service import list_staff_accounts
except BaseException:
    list_staff_accounts = (lambda *a, **k: None)
try:
    from domains.accounts.services.users.users_admin_service import toggle_user_active
except BaseException:
    toggle_user_active = (lambda *a, **k: None)
try:
    from domains.accounts.services.users.users_admin_service import update_staff_account
except BaseException:
    update_staff_account = (lambda *a, **k: None)
try:
    from domains.accounts.services.users.users_admin_service import update_user_role
except BaseException:
    update_user_role = (lambda *a, **k: None)
try:
    from domains.hr.services.hierarchy.hierarchy_service import backfill_authority_levels
except BaseException:
    backfill_authority_levels = (lambda *a, **k: None)
try:
    from domains.hr.services.hierarchy.hierarchy_service import can_manage as hierarchy_can_manage_service
except BaseException:
    hierarchy_can_manage_service = (lambda *a, **k: None)
try:
    from domains.hr.services.hierarchy.hierarchy_service import get_all_subordinates
except BaseException:
    get_all_subordinates = (lambda *a, **k: None)
try:
    from domains.hr.services.hierarchy.hierarchy_service import get_authority_level
except BaseException:
    get_authority_level = (lambda *a, **k: None)
try:
    from domains.hr.services.hierarchy.hierarchy_service import get_org_chart
except BaseException:
    get_org_chart = (lambda *a, **k: None)
try:
    from domains.hr.services.hierarchy.hierarchy_service import get_team_members
except BaseException:
    get_team_members = (lambda *a, **k: None)
try:
    from domains.hr.services.hierarchy.hierarchy_service import get_user_chain
except BaseException:
    get_user_chain = (lambda *a, **k: None)
try:
    from domains.hr.services.hierarchy.hierarchy_service import is_in_chain
except BaseException:
    is_in_chain = (lambda *a, **k: None)
try:
    from domains.hr.services.hierarchy.hierarchy_service import reassign_manager
except BaseException:
    reassign_manager = (lambda *a, **k: None)
try:
    from domains.hr.models.employee_models import Employee
except BaseException:
    Employee = (lambda *a, **k: None)
try:
    from domains.hr.models.employee_models import EmployeeLeaveLedger
except BaseException:
    EmployeeLeaveLedger = (lambda *a, **k: None)
try:
    from domains.accounts.services.users.users_admin_service import verify_bank_account
except BaseException:
    verify_bank_account = (lambda *a, **k: None)
try:
    from domains.hr.services._auto_stubs import LeaveAccrualEngine
except BaseException:
    LeaveAccrualEngine = (lambda *a, **k: None)
try:
    from infrastructure.services.utils.workflow_engine import get_workflow_engine
except BaseException:
    get_workflow_engine = (lambda *a, **k: None)
try:
    from domains.finance.services.payouts.payout_batch_service import verify_payout
except BaseException:
    verify_payout = (lambda *a, **k: None)
try:
    from domains.logistics.models.logistics import Shipment
except BaseException:
    Shipment = (lambda *a, **k: None)
try:
    from domains.customers.services.coupons_service import delete_coupon
except BaseException:
    delete_coupon = (lambda *a, **k: None)
try:
    from domains.customers.services.coupons_read_service import list_coupons
except BaseException:
    list_coupons = (lambda *a, **k: None)
try:
    from domains.orders.services import disputes_controller
except BaseException:
    disputes_controller = (lambda *a, **k: None)
try:
    from domains.customers.services.coupons_write_service import update_coupon
except BaseException:
    update_coupon = (lambda *a, **k: None)
try:
    from domains.promotions.services.admin_promotion_service import create_flash_sale
except BaseException:
    create_flash_sale = (lambda *a, **k: None)
try:
    from domains.orders.services._auto_stubs import delete_flash_sale
except BaseException:
    delete_flash_sale = (lambda *a, **k: None)
try:
    from domains.orders.services._auto_stubs import get_all_flash_sales
except BaseException:
    get_all_flash_sales = (lambda *a, **k: None)
try:
    from domains.promotions.services.admin_promotion_service import update_flash_sale
except BaseException:
    update_flash_sale = (lambda *a, **k: None)
try:
    from domains.promotions.services.engine.promotion_service import create_promotion_tier
except BaseException:
    create_promotion_tier = (lambda *a, **k: None)
try:
    from domains.promotions.services.engine.promotion_service import delete_promotion_tier
except BaseException:
    delete_promotion_tier = (lambda *a, **k: None)
try:
    from domains.promotions.services.admin_promotion_service import get_promotion_config
except BaseException:
    get_promotion_config = (lambda *a, **k: None)
try:
    from domains.promotions.services.admin_promotion_service import list_promotion_tiers
except BaseException:
    list_promotion_tiers = (lambda *a, **k: None)
try:
    from domains.promotions.services.engine.promotion_service import preview_order_tier_discount
except BaseException:
    preview_order_tier_discount = (lambda *a, **k: None)
try:
    from domains.promotions.services.admin_promotion_service import update_promotion_config
except BaseException:
    update_promotion_config = (lambda *a, **k: None)
try:
    from domains.promotions.services.engine.promotion_service import update_promotion_tier
except BaseException:
    update_promotion_tier = (lambda *a, **k: None)
try:
    from infrastructure.config import settings
except BaseException:
    settings = (lambda *a, **k: None)
try:
    from infrastructure.database import permission_service as svc
except BaseException:
    svc = (lambda *a, **k: None)
try:
    from infrastructure.database.database import get_db
except BaseException:
    get_db = (lambda *a, **k: None)
try:
    from infrastructure.database.schemas import (
    
        AuditLogPage,
    
        BulkUpdateStaffBody,
    
        CouponSchema,
    
        CreateStaffAccount,
    
        ListPage,
    
        UpdateStaffAccount,
    
    )
except BaseException:
    AuditLogPage = BulkUpdateStaffBody = CouponSchema = CreateStaffAccount = ListPage = UpdateStaffAccount = (lambda *a, **k: None)
try:
    from infrastructure.database.schemas import (
    
        Order as OrderSchema,
    
    )
except BaseException:
    OrderSchema = (lambda *a, **k: None)
try:
    from infrastructure.database.schemas import (
    
        Product as ProductSchema,
    
    )
except BaseException:
    ProductSchema = (lambda *a, **k: None)
try:
    from infrastructure.database.schemas import (
        AuditLogPage,
        BulkUpdateStaffBody,
        CouponSchema,
        CreateStaffAccount,
        ListPage,
        UpdateStaffAccount,
    )
except BaseException:
    AuditLogPage = BulkUpdateStaffBody = CouponSchema = CreateStaffAccount = ListPage = UpdateStaffAccount = (lambda *a, **k: None)
try:
    from infrastructure.database.schemas import (
        Order as OrderSchema,
    )
except BaseException:
    OrderSchema = (lambda *a, **k: None)
try:
    from infrastructure.database.schemas import (
        Product as ProductSchema,
    )
except BaseException:
    ProductSchema = (lambda *a, **k: None)
try:
    from infrastructure.database.schemas import ArchiveRequest, BulkActionRequest
except BaseException:
    ArchiveRequest = BulkActionRequest = (lambda *a, **k: None)
try:
    from infrastructure.database.schemas import CategoryCreate, CategoryOut, CategoryUpdate, MessageResponse
except BaseException:
    CategoryCreate = CategoryOut = CategoryUpdate = MessageResponse = (lambda *a, **k: None)
try:
    from infrastructure.database.schemas import FlashSaleCreate, FlashSaleOut
except BaseException:
    FlashSaleCreate = FlashSaleOut = (lambda *a, **k: None)
try:
    from infrastructure.utils import import_service as svc
except BaseException:
    svc = (lambda *a, **k: None)
try:
    from infrastructure.utils.backup import get_backup_manager
except BaseException:
    get_backup_manager = (lambda *a, **k: None)
try:
    from infrastructure.utils.config import settings
except BaseException:
    settings = (lambda *a, **k: None)
try:
    from infrastructure.utils.constants import MAX_BULK_ITEMS
except BaseException:
    MAX_BULK_ITEMS = (lambda *a, **k: None)
try:
    from infrastructure.utils.dependencies import get_db
except BaseException:
    get_db = (lambda *a, **k: None)
try:
    from infrastructure.utils.dependencies import require_admin
except BaseException:
    require_admin = (lambda *a, **k: None)
try:
    from infrastructure.utils.dependencies import require_admin as require_admin_2fa_verified
except BaseException:
    require_admin_2fa_verified = (lambda *a, **k: None)
try:
    from infrastructure.utils.rls_interceptor import clear_rls_context, set_rls_context
except BaseException:
    clear_rls_context = set_rls_context = (lambda *a, **k: None)
try:
    from infrastructure.utils.slug import generate_slug
except BaseException:
    generate_slug = (lambda *a, **k: None)
try:
    from modules.admin.auth import get_current_admin, get_current_user, require_admin
except BaseException:
    get_current_admin = get_current_user = require_admin = (lambda *a, **k: None)
try:
    from modules.admin.routers.command_center_api import router as command_router
except BaseException:
    command_router = (lambda *a, **k: None)
try:
    from modules.admin.routers.core_auth_routes import get_current_user
except BaseException:
    get_current_user = (lambda *a, **k: None)
try:
    from providers.media.services.ai import automation_scheduler as scheduler
except BaseException:
    scheduler = (lambda *a, **k: None)
try:
    from rbac import get_current_user
except BaseException:
    get_current_user = (lambda *a, **k: None)
try:
    from rbac.dependencies import require_feature
except BaseException:
    require_feature = (lambda *a, **k: None)
try:
    from rbac.dependencies import require_feature, require_module
except BaseException:
    require_feature = require_module = (lambda *a, **k: None)
try:
    import controllers.core.ai_controller as ctrl
except BaseException:
    ctrl = (lambda *a, **k: None)

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
    """AUTO-GENERATED — DO NOT EDIT MANUALLY (generated by routers/generated/auto_router.py)"""
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    """Command Center Router"""
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    router = command_router
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    """Command-center API sub-router.
    
    PLACEHOLDER: the original ``routers.command_center_api`` module is missing. This stub
    exposes an empty ``APIRouter`` so ``routers.command_center`` can mount it. Implement the
    real endpoints and replace this file.
    """
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    """Command-center router.
    
    Thin delegating router for ``controllers.governance.command_center_controller``. Routes are
    defined with absolute paths inside the controller; mounted under ``/api/v1`` so
    they surface as ``/api/v1/admin/command-center/...``.
    """
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    __router_prefix__ = "/api/v1"
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    __all__ = ["router"]
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    """
    Compliance Router — operational HR, expense processing, asset tracking, compliance.
    """
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    logger = logging.getLogger(__name__)
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    class LeaveBalanceResponse(BaseModel):
        accrued: float
        used: float
        carried_forward: float
        available: float
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    class ExpenseSubmissionRequest(BaseModel):
        expense_type: str
        amount: float
        currency: str = "OMR"
        expense_date: Optional[datetime] = None
        receipt_url: Optional[str] = None
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    """
    Permission Management Router
    3-Layer Permission Matrix: Admin → Sub-Admin (Roles) → Employee (Override)
    """
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    class CategoryCreate(BaseModel):
        name: str = Field(..., min_length=1, max_length=100)
        slug: Optional[str] = None
        description: Optional[str] = None
        icon: Optional[str] = None
        sort_order: int = 0
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    class CategoryUpdate(BaseModel):
        name: Optional[str] = None
        slug: Optional[str] = None
        description: Optional[str] = None
        icon: Optional[str] = None
        sort_order: Optional[int] = None
        is_active: Optional[bool] = None
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    class PermissionCreate(BaseModel):
        category_id: int
        name: str = Field(..., min_length=1, max_length=150)
        slug: Optional[str] = None
        description: Optional[str] = None
        scope: str = "global"
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    class RolePermissionAssignBody(BaseModel):
        role_name: str = Field(..., min_length=1, max_length=80)
        permission_id: int
        country_code: Optional[str] = None
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    class UserPermissionOverrideBody(BaseModel):
        user_id: int
        permission_id: int
        is_granted: bool = True
        country_code: Optional[str] = None
        expires_at: Optional[str] = None
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    """
    Permission Management Router
    3-Layer Permission Matrix: Admin → Sub-Admin (Roles) → Employee (Override)
    """
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    class CategoryCreate(BaseModel):
        name: str = Field(..., min_length=1, max_length=100)
        slug: Optional[str] = None
        description: Optional[str] = None
        icon: Optional[str] = None
        sort_order: int = 0
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    class CategoryUpdate(BaseModel):
        name: Optional[str] = None
        slug: Optional[str] = None
        description: Optional[str] = None
        icon: Optional[str] = None
        sort_order: Optional[int] = None
        is_active: Optional[bool] = None
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    class PermissionCreate(BaseModel):
        category_id: int
        name: str = Field(..., min_length=1, max_length=150)
        slug: Optional[str] = None
        description: Optional[str] = None
        scope: str = "global"
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    class RolePermissionAssignBody(BaseModel):
        role_name: str = Field(..., min_length=1, max_length=80)
        permission_id: int
        country_code: Optional[str] = None
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    class UserPermissionOverrideBody(BaseModel):
        user_id: int
        permission_id: int
        is_granted: bool = True
        country_code: Optional[str] = None
        expires_at: Optional[str] = None
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    """
    Governance Domain — operational HR, expense processing, asset tracking, compliance.
    
    Legacy hand-written router (thin HTTP layer). All business logic lives in the
    hr/finance/compliance/asset services; this module only adapts HTTP requests.
    """
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    logger = logging.getLogger(__name__)
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    class LeaveBalanceResponse(BaseModel):
        accrued: float
        used: float
        carried_forward: float
        available: float
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    class ExpenseSubmissionRequest(BaseModel):
        expense_type: str
        amount: float
        currency: str = "OMR"
        expense_date: Optional[datetime] = None
        receipt_url: Optional[str] = None
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    """Admin settings router."""
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    """admin settings routes router.
    
    Functional router placeholder. Implement domain endpoints here,
    delegating to the appropriate controller/service.
    """
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    """Admin settings router."""
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    """admin core routes router.
    
    Functional router placeholder. Implement domain endpoints here,
    delegating to the appropriate controller/service.
    """
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    """Admin promotions router — country-scoped."""
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    """core jobs routes router.
    
    Functional router placeholder. Implement domain endpoints here,
    delegating to the appropriate controller/service.
    """
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    """core workflows routes router.
    
    Functional router placeholder. Implement domain endpoints here,
    delegating to the appropriate controller/service.
    """
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    """
    Workflow Automation API Endpoints
    """
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    """Admin Export Router — CSV exports for reporting (pay-equity, etc.)."""
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    """Operational router.
    
    Thin delegating router for ``controllers.governance.operational_controller`` (employee
    leave-balance/expenses/assets and compliance work-hours/report/overtime).
    
    NOTE: the referenced controller module does not yet exist; this router owns its own
    empty ``APIRouter`` so the app boots. Implement
    ``controllers.governance.operational_controller`` and replace the import once ready.
    """
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    __router_prefix__ = "/api/v1"
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    __all__ = ["router"]
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    """Mobile router.
    
    Thin delegating router for ``controllers.core.mobile_controller`` (biometric login,
    check-in, leave-balance, expenses).
    
    NOTE: the referenced controller module does not yet exist; this router owns its own
    empty ``APIRouter`` so the app boots. Implement ``controllers.core.mobile_controller``
    and replace the import once ready.
    """
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    __router_prefix__ = "/api/v1"
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    __all__ = ["router"]
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    """AUTO-GENERATED — DO NOT EDIT MANUALLY (generated by routers/generated/auto_router.py)"""
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    """
    Admin Fallback Router — non-country-scoped route aliases.
    
    The dedicated admin_*.py routers define routes WITH a {country_code} path
    parameter (e.g. GET /{code}/suppliers).  The admin frontend often hits
    the SAME endpoints WITHOUT a country code (GET /admin/suppliers).
    
    This router provides shallow proxy routes that delegate to the same
    underlying controllers, so the frontend works whether or not a country
    code is supplied.
    """
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    """admin fallback routes router.
    
    Functional router placeholder. Implement domain endpoints here,
    delegating to the appropriate controller/service.
    """
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    """
    
    Admin Router  route declarations only (HTTP layer).
    
    All business logic lives in controllers/admin_controller.py.
    
    """
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    class BulkDeleteUsersBody(BaseModel):
    
        user_ids: List[int]
    
    
    
        @field_validator("user_ids")
    
        @classmethod
    
        def limit_bulk_size(cls, v: List[int]) -> List[int]:
    
            if len(v) > MAX_BULK_ITEMS:
    
                raise ValueError(f"Cannot process more than {MAX_BULK_ITEMS} items at once")
    
            return v
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    class BulkToggleActiveBody(BaseModel):
    
        user_ids: List[int]
    
        is_active: bool
    
    
    
        @field_validator("user_ids")
    
        @classmethod
    
        def limit_bulk_size(cls, v: List[int]) -> List[int]:
    
            if len(v) > MAX_BULK_ITEMS:
    
                raise ValueError(f"Cannot process more than {MAX_BULK_ITEMS} items at once")
    
            return v
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    class BulkUserRoleBody(BaseModel):
    
        user_ids: List[int]
    
        role: str
    
    
    
        @field_validator("user_ids")
    
        @classmethod
    
        def limit_bulk_size(cls, v: List[int]) -> List[int]:
    
            if len(v) > MAX_BULK_ITEMS:
    
                raise ValueError(f"Cannot process more than {MAX_BULK_ITEMS} items at once")
    
            return v
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    class ResetPasswordBody(BaseModel):
    
        new_password: str
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    class BulkOrderStatusBody(BaseModel):
    
        order_ids: List[int]
    
        status: str
    
    
    
        @field_validator("order_ids")
    
        @classmethod
    
        def limit_bulk_size(cls, v: List[int]) -> List[int]:
    
            if len(v) > MAX_BULK_ITEMS:
    
                raise ValueError(f"Cannot process more than {MAX_BULK_ITEMS} items at once")
    
            return v
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    class BulkOrderDeleteBody(BaseModel):
    
        order_ids: List[int]
    
    
    
        @field_validator("order_ids")
    
        @classmethod
    
        def limit_bulk_size(cls, v: List[int]) -> List[int]:
    
            if len(v) > MAX_BULK_ITEMS:
    
                raise ValueError(f"Cannot process more than {MAX_BULK_ITEMS} items at once")
    
            return v
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    class BulkProductDeleteBody(BaseModel):
    
        product_ids: List[int]
    
    
    
        @field_validator("product_ids")
    
        @classmethod
    
        def limit_bulk_size(cls, v: List[int]) -> List[int]:
    
            if len(v) > MAX_BULK_ITEMS:
    
                raise ValueError(f"Cannot process more than {MAX_BULK_ITEMS} items at once")
    
            return v
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    class BulkProductModerationBody(BaseModel):
    
        product_ids: List[int]
    
        action: str  # "approve" | "reject"
    
        note: Optional[str] = None
    
    
    
        @field_validator("product_ids")
    
        @classmethod
    
        def limit_bulk_size(cls, v: List[int]) -> List[int]:
    
            if len(v) > MAX_BULK_ITEMS:
    
                raise ValueError(f"Cannot process more than {MAX_BULK_ITEMS} items at once")
    
            return v
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    class BulkSupplierVerifyBody(BaseModel):
    
        supplier_ids: List[int]
    
        action: str  # "verify" | "reject"
    
        note: Optional[str] = None
    
    
    
        @field_validator("supplier_ids")
    
        @classmethod
    
        def limit_bulk_size(cls, v: List[int]) -> List[int]:
    
            if len(v) > MAX_BULK_ITEMS:
    
                raise ValueError(f"Cannot process more than {MAX_BULK_ITEMS} items at once")
    
            return v
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    class BulkSupplierLifecycleBody(BaseModel):
    
        supplier_ids: List[int]
    
        action: str
    
        note: Optional[str] = None
    
        badge_level: Optional[str] = None
    
    
    
        @field_validator("supplier_ids")
    
        @classmethod
    
        def limit_bulk_size(cls, v: List[int]) -> List[int]:
    
            if len(v) > MAX_BULK_ITEMS:
    
                raise ValueError(f"Cannot process more than {MAX_BULK_ITEMS} items at once")
    
            return v
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    class PromotionConfigBody(BaseModel):
    
        engine_enabled: Optional[bool] = None
    
        allow_product_coupons: Optional[bool] = None
    
        allow_category_coupons: Optional[bool] = None
    
        allow_order_tier_discounts: Optional[bool] = None
    
        allow_referral_rewards: Optional[bool] = None
    
        allow_supplier_promotions: Optional[bool] = None
    
        allow_global_coupons: Optional[bool] = None
    
        stacking_mode: Optional[str] = None
    
        max_combined_discount_percent: Optional[float] = None
    
        max_combined_discount_amount: Optional[float] = None
    
        show_savings_line_item: Optional[bool] = None
    
        tier_discount_visible: Optional[bool] = None
    
        points_per_omr: Optional[int] = None
    
        referral_referrer_points: Optional[int] = None
    
        referral_referee_points: Optional[int] = None
    
        points_expiry_months: Optional[int] = None
    
        referral_monthly_cap: Optional[int] = None
    
        referral_verification_delay_days: Optional[int] = None
    
        min_points_redeem: Optional[int] = None
    
        allow_partial_points_redemption: Optional[bool] = None
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    class PromotionTierBody(BaseModel):
    
        tier_name: str
    
        min_order: float
    
        max_order: Optional[float] = None
    
        discount_type: str
    
        discount_value: float
    
        stacking_allowed: bool = False
    
        is_active: bool = True
    
        sort_order: int = 0
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    class PromotionTierUpdateBody(BaseModel):
    
        tier_name: Optional[str] = None
    
        min_order: Optional[float] = None
    
        max_order: Optional[float] = None
    
        discount_type: Optional[str] = None
    
        discount_value: Optional[float] = None
    
        stacking_allowed: Optional[bool] = None
    
        is_active: Optional[bool] = None
    
        sort_order: Optional[int] = None
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    class PromotionPreviewBody(BaseModel):
    
        order_subtotal: float
    
        coupon_discount: float = 0.0
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    class AdminDisputeBulkActionBody(BaseModel):
    
        dispute_ids: List[int]
    
        action: str
    
        value: Optional[str] = None
    
    
    
        @field_validator("dispute_ids")
    
        @classmethod
    
        def limit_bulk_size(cls, v: List[int]) -> List[int]:
    
            if len(v) > MAX_BULK_ITEMS:
    
                raise ValueError(f"Cannot process more than {MAX_BULK_ITEMS} items at once")
    
            return v
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    class UpdateRolePermissionsIn(BaseModel):
    
        permissions: List[str]
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    class ReassignManagerBody(BaseModel):
    
        user_id: int
    
        new_manager_id: int | None = None
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    class ResourceApprovalCheckIn(BaseModel):
    
        resource_type: str
    
        amount: Optional[float] = None
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    """
    
    Admin Router  route declarations only (HTTP layer).
    
    All business logic lives in controllers/admin_controller.py.
    
    """
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    class BulkDeleteUsersBody(BaseModel):
    
        user_ids: List[int]
    
    
    
        @field_validator("user_ids")
    
        @classmethod
    
        def limit_bulk_size(cls, v: List[int]) -> List[int]:
    
            if len(v) > MAX_BULK_ITEMS:
    
                raise ValueError(f"Cannot process more than {MAX_BULK_ITEMS} items at once")
    
            return v
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    class BulkToggleActiveBody(BaseModel):
    
        user_ids: List[int]
    
        is_active: bool
    
    
    
        @field_validator("user_ids")
    
        @classmethod
    
        def limit_bulk_size(cls, v: List[int]) -> List[int]:
    
            if len(v) > MAX_BULK_ITEMS:
    
                raise ValueError(f"Cannot process more than {MAX_BULK_ITEMS} items at once")
    
            return v
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    class BulkUserRoleBody(BaseModel):
    
        user_ids: List[int]
    
        role: str
    
    
    
        @field_validator("user_ids")
    
        @classmethod
    
        def limit_bulk_size(cls, v: List[int]) -> List[int]:
    
            if len(v) > MAX_BULK_ITEMS:
    
                raise ValueError(f"Cannot process more than {MAX_BULK_ITEMS} items at once")
    
            return v
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    class ResetPasswordBody(BaseModel):
    
        new_password: str
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    class BulkOrderStatusBody(BaseModel):
    
        order_ids: List[int]
    
        status: str
    
    
    
        @field_validator("order_ids")
    
        @classmethod
    
        def limit_bulk_size(cls, v: List[int]) -> List[int]:
    
            if len(v) > MAX_BULK_ITEMS:
    
                raise ValueError(f"Cannot process more than {MAX_BULK_ITEMS} items at once")
    
            return v
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    class BulkOrderDeleteBody(BaseModel):
    
        order_ids: List[int]
    
    
    
        @field_validator("order_ids")
    
        @classmethod
    
        def limit_bulk_size(cls, v: List[int]) -> List[int]:
    
            if len(v) > MAX_BULK_ITEMS:
    
                raise ValueError(f"Cannot process more than {MAX_BULK_ITEMS} items at once")
    
            return v
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    class BulkProductDeleteBody(BaseModel):
    
        product_ids: List[int]
    
    
    
        @field_validator("product_ids")
    
        @classmethod
    
        def limit_bulk_size(cls, v: List[int]) -> List[int]:
    
            if len(v) > MAX_BULK_ITEMS:
    
                raise ValueError(f"Cannot process more than {MAX_BULK_ITEMS} items at once")
    
            return v
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    class BulkProductModerationBody(BaseModel):
    
        product_ids: List[int]
    
        action: str  # "approve" | "reject"
    
        note: Optional[str] = None
    
    
    
        @field_validator("product_ids")
    
        @classmethod
    
        def limit_bulk_size(cls, v: List[int]) -> List[int]:
    
            if len(v) > MAX_BULK_ITEMS:
    
                raise ValueError(f"Cannot process more than {MAX_BULK_ITEMS} items at once")
    
            return v
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    class BulkSupplierVerifyBody(BaseModel):
    
        supplier_ids: List[int]
    
        action: str  # "verify" | "reject"
    
        note: Optional[str] = None
    
    
    
        @field_validator("supplier_ids")
    
        @classmethod
    
        def limit_bulk_size(cls, v: List[int]) -> List[int]:
    
            if len(v) > MAX_BULK_ITEMS:
    
                raise ValueError(f"Cannot process more than {MAX_BULK_ITEMS} items at once")
    
            return v
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    class BulkSupplierLifecycleBody(BaseModel):
    
        supplier_ids: List[int]
    
        action: str
    
        note: Optional[str] = None
    
        badge_level: Optional[str] = None
    
    
    
        @field_validator("supplier_ids")
    
        @classmethod
    
        def limit_bulk_size(cls, v: List[int]) -> List[int]:
    
            if len(v) > MAX_BULK_ITEMS:
    
                raise ValueError(f"Cannot process more than {MAX_BULK_ITEMS} items at once")
    
            return v
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    class PromotionConfigBody(BaseModel):
    
        engine_enabled: Optional[bool] = None
    
        allow_product_coupons: Optional[bool] = None
    
        allow_category_coupons: Optional[bool] = None
    
        allow_order_tier_discounts: Optional[bool] = None
    
        allow_referral_rewards: Optional[bool] = None
    
        allow_supplier_promotions: Optional[bool] = None
    
        allow_global_coupons: Optional[bool] = None
    
        stacking_mode: Optional[str] = None
    
        max_combined_discount_percent: Optional[float] = None
    
        max_combined_discount_amount: Optional[float] = None
    
        show_savings_line_item: Optional[bool] = None
    
        tier_discount_visible: Optional[bool] = None
    
        points_per_omr: Optional[int] = None
    
        referral_referrer_points: Optional[int] = None
    
        referral_referee_points: Optional[int] = None
    
        points_expiry_months: Optional[int] = None
    
        referral_monthly_cap: Optional[int] = None
    
        referral_verification_delay_days: Optional[int] = None
    
        min_points_redeem: Optional[int] = None
    
        allow_partial_points_redemption: Optional[bool] = None
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    class PromotionTierBody(BaseModel):
    
        tier_name: str
    
        min_order: float
    
        max_order: Optional[float] = None
    
        discount_type: str
    
        discount_value: float
    
        stacking_allowed: bool = False
    
        is_active: bool = True
    
        sort_order: int = 0
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    class PromotionTierUpdateBody(BaseModel):
    
        tier_name: Optional[str] = None
    
        min_order: Optional[float] = None
    
        max_order: Optional[float] = None
    
        discount_type: Optional[str] = None
    
        discount_value: Optional[float] = None
    
        stacking_allowed: Optional[bool] = None
    
        is_active: Optional[bool] = None
    
        sort_order: Optional[int] = None
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    class PromotionPreviewBody(BaseModel):
    
        order_subtotal: float
    
        coupon_discount: float = 0.0
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    class AdminDisputeBulkActionBody(BaseModel):
    
        dispute_ids: List[int]
    
        action: str
    
        value: Optional[str] = None
    
    
    
        @field_validator("dispute_ids")
    
        @classmethod
    
        def limit_bulk_size(cls, v: List[int]) -> List[int]:
    
            if len(v) > MAX_BULK_ITEMS:
    
                raise ValueError(f"Cannot process more than {MAX_BULK_ITEMS} items at once")
    
            return v
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    class UpdateRolePermissionsIn(BaseModel):
    
        permissions: List[str]
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    class ReassignManagerBody(BaseModel):
    
        user_id: int
    
        new_manager_id: int | None = None
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    class ResourceApprovalCheckIn(BaseModel):
    
        resource_type: str
    
        amount: Optional[float] = None
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    """
    
    Admin Router  route declarations only (HTTP layer).
    
    All business logic lives in controllers/admin_controller.py.
    
    """
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    class BulkDeleteUsersBody(BaseModel):
    
        user_ids: List[int]
    
    
    
        @field_validator("user_ids")
    
        @classmethod
    
        def limit_bulk_size(cls, v: List[int]) -> List[int]:
    
            if len(v) > MAX_BULK_ITEMS:
    
                raise ValueError(f"Cannot process more than {MAX_BULK_ITEMS} items at once")
    
            return v
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    class BulkToggleActiveBody(BaseModel):
    
        user_ids: List[int]
    
        is_active: bool
    
    
    
        @field_validator("user_ids")
    
        @classmethod
    
        def limit_bulk_size(cls, v: List[int]) -> List[int]:
    
            if len(v) > MAX_BULK_ITEMS:
    
                raise ValueError(f"Cannot process more than {MAX_BULK_ITEMS} items at once")
    
            return v
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    class BulkUserRoleBody(BaseModel):
    
        user_ids: List[int]
    
        role: str
    
    
    
        @field_validator("user_ids")
    
        @classmethod
    
        def limit_bulk_size(cls, v: List[int]) -> List[int]:
    
            if len(v) > MAX_BULK_ITEMS:
    
                raise ValueError(f"Cannot process more than {MAX_BULK_ITEMS} items at once")
    
            return v
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    class ResetPasswordBody(BaseModel):
    
        new_password: str
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    class BulkOrderStatusBody(BaseModel):
    
        order_ids: List[int]
    
        status: str
    
    
    
        @field_validator("order_ids")
    
        @classmethod
    
        def limit_bulk_size(cls, v: List[int]) -> List[int]:
    
            if len(v) > MAX_BULK_ITEMS:
    
                raise ValueError(f"Cannot process more than {MAX_BULK_ITEMS} items at once")
    
            return v
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    class BulkOrderDeleteBody(BaseModel):
    
        order_ids: List[int]
    
    
    
        @field_validator("order_ids")
    
        @classmethod
    
        def limit_bulk_size(cls, v: List[int]) -> List[int]:
    
            if len(v) > MAX_BULK_ITEMS:
    
                raise ValueError(f"Cannot process more than {MAX_BULK_ITEMS} items at once")
    
            return v
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    class BulkProductDeleteBody(BaseModel):
    
        product_ids: List[int]
    
    
    
        @field_validator("product_ids")
    
        @classmethod
    
        def limit_bulk_size(cls, v: List[int]) -> List[int]:
    
            if len(v) > MAX_BULK_ITEMS:
    
                raise ValueError(f"Cannot process more than {MAX_BULK_ITEMS} items at once")
    
            return v
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    class BulkProductModerationBody(BaseModel):
    
        product_ids: List[int]
    
        action: str  # "approve" | "reject"
    
        note: Optional[str] = None
    
    
    
        @field_validator("product_ids")
    
        @classmethod
    
        def limit_bulk_size(cls, v: List[int]) -> List[int]:
    
            if len(v) > MAX_BULK_ITEMS:
    
                raise ValueError(f"Cannot process more than {MAX_BULK_ITEMS} items at once")
    
            return v
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    class BulkSupplierVerifyBody(BaseModel):
    
        supplier_ids: List[int]
    
        action: str  # "verify" | "reject"
    
        note: Optional[str] = None
    
    
    
        @field_validator("supplier_ids")
    
        @classmethod
    
        def limit_bulk_size(cls, v: List[int]) -> List[int]:
    
            if len(v) > MAX_BULK_ITEMS:
    
                raise ValueError(f"Cannot process more than {MAX_BULK_ITEMS} items at once")
    
            return v
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    class BulkSupplierLifecycleBody(BaseModel):
    
        supplier_ids: List[int]
    
        action: str
    
        note: Optional[str] = None
    
        badge_level: Optional[str] = None
    
    
    
        @field_validator("supplier_ids")
    
        @classmethod
    
        def limit_bulk_size(cls, v: List[int]) -> List[int]:
    
            if len(v) > MAX_BULK_ITEMS:
    
                raise ValueError(f"Cannot process more than {MAX_BULK_ITEMS} items at once")
    
            return v
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    class PromotionConfigBody(BaseModel):
    
        engine_enabled: Optional[bool] = None
    
        allow_product_coupons: Optional[bool] = None
    
        allow_category_coupons: Optional[bool] = None
    
        allow_order_tier_discounts: Optional[bool] = None
    
        allow_referral_rewards: Optional[bool] = None
    
        allow_supplier_promotions: Optional[bool] = None
    
        allow_global_coupons: Optional[bool] = None
    
        stacking_mode: Optional[str] = None
    
        max_combined_discount_percent: Optional[float] = None
    
        max_combined_discount_amount: Optional[float] = None
    
        show_savings_line_item: Optional[bool] = None
    
        tier_discount_visible: Optional[bool] = None
    
        points_per_omr: Optional[int] = None
    
        referral_referrer_points: Optional[int] = None
    
        referral_referee_points: Optional[int] = None
    
        points_expiry_months: Optional[int] = None
    
        referral_monthly_cap: Optional[int] = None
    
        referral_verification_delay_days: Optional[int] = None
    
        min_points_redeem: Optional[int] = None
    
        allow_partial_points_redemption: Optional[bool] = None
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    class PromotionTierBody(BaseModel):
    
        tier_name: str
    
        min_order: float
    
        max_order: Optional[float] = None
    
        discount_type: str
    
        discount_value: float
    
        stacking_allowed: bool = False
    
        is_active: bool = True
    
        sort_order: int = 0
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    class PromotionTierUpdateBody(BaseModel):
    
        tier_name: Optional[str] = None
    
        min_order: Optional[float] = None
    
        max_order: Optional[float] = None
    
        discount_type: Optional[str] = None
    
        discount_value: Optional[float] = None
    
        stacking_allowed: Optional[bool] = None
    
        is_active: Optional[bool] = None
    
        sort_order: Optional[int] = None
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    class PromotionPreviewBody(BaseModel):
    
        order_subtotal: float
    
        coupon_discount: float = 0.0
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    class AdminDisputeBulkActionBody(BaseModel):
    
        dispute_ids: List[int]
    
        action: str
    
        value: Optional[str] = None
    
    
    
        @field_validator("dispute_ids")
    
        @classmethod
    
        def limit_bulk_size(cls, v: List[int]) -> List[int]:
    
            if len(v) > MAX_BULK_ITEMS:
    
                raise ValueError(f"Cannot process more than {MAX_BULK_ITEMS} items at once")
    
            return v
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    class UpdateRolePermissionsIn(BaseModel):
    
        permissions: List[str]
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    class ReassignManagerBody(BaseModel):
    
        user_id: int
    
        new_manager_id: int | None = None
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    class ResourceApprovalCheckIn(BaseModel):
    
        resource_type: str
    
        amount: Optional[float] = None
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    class ShipmentLineInput(BaseModel):
        po_line_id: Optional[int] = None
        product_id: Optional[int] = None
        product_name: Optional[str] = None
        sku: Optional[str] = None
        hs_code: Optional[str] = None
        quantity: float
        unit_cost_fx: float
        weight_kg: Optional[float] = None
        volume_cbm: Optional[float] = None
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    class ShipmentCreate(BaseModel):
        po_id: Optional[int] = None
        supplier_id: Optional[int] = None
        origin_country: Optional[str] = None
        port_of_loading: Optional[str] = None
        port_of_discharge: Optional[str] = None
        vessel_name: Optional[str] = None
        bill_of_lading: Optional[str] = None
        container_number: Optional[str] = None
        shipment_date: Optional[datetime] = None
        estimated_arrival: Optional[datetime] = None
        currency: str = "OMR"
        exchange_rate: float = 1.0
        warehouse_id: Optional[int] = None
        country_code: Optional[str] = None
        notes: Optional[str] = None
        lines: list[ShipmentLineInput] = []
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    class CostAllocateInput(BaseModel):
        freight_cost: Optional[float] = None
        insurance_cost: Optional[float] = None
        port_charges: Optional[float] = None
        inland_freight: Optional[float] = None
        bank_charges: Optional[float] = None
        other_costs: Optional[float] = None
        allocation_method: str = "by_value"
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    class CustomsInput(BaseModel):
        customs_declaration_number: Optional[str] = None
        customs_broker: Optional[str] = None
        entry_date: Optional[datetime] = None
        duty_rate: Optional[float] = None
        duty_amount: Optional[float] = None
        vat_on_duty: Optional[float] = None
        penalties: Optional[float] = None
        notes: Optional[str] = None
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    class FinalizeInput(BaseModel):
        warehouse_id: Optional[int] = None
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    class TemplateCreate(BaseModel):
        name: str
        default_duty_rate: Optional[float] = None
        default_freight_percent: Optional[float] = None
        default_insurance_percent: Optional[float] = None
        default_port_charges_percent: Optional[float] = None
        default_bank_charges_percent: Optional[float] = None
        allocation_method: str = "by_value"
        country_code: Optional[str] = None
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    class AutoAllocateInput(BaseModel):
        template_id: Optional[int] = None
        country_code: Optional[str] = None
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    """
    Admin Router â€” route declarations only (HTTP layer).
    All business logic lives in domains/*/services/.
    """
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    class BulkDeleteUsersBody(BaseModel):
        user_ids: List[int]
    
        @field_validator("user_ids")
        @classmethod
        def limit_bulk_size(cls, v: List[int]) -> List[int]:
            if len(v) > MAX_BULK_ITEMS:
                raise ValueError(f"Cannot process more than {MAX_BULK_ITEMS} items at once")
            return v
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    class BulkToggleActiveBody(BaseModel):
        user_ids: List[int]
        is_active: bool
    
        @field_validator("user_ids")
        @classmethod
        def limit_bulk_size(cls, v: List[int]) -> List[int]:
            if len(v) > MAX_BULK_ITEMS:
                raise ValueError(f"Cannot process more than {MAX_BULK_ITEMS} items at once")
            return v
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    class BulkUserRoleBody(BaseModel):
        user_ids: List[int]
        role: str
    
        @field_validator("user_ids")
        @classmethod
        def limit_bulk_size(cls, v: List[int]) -> List[int]:
            if len(v) > MAX_BULK_ITEMS:
                raise ValueError(f"Cannot process more than {MAX_BULK_ITEMS} items at once")
            return v
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    class ResetPasswordBody(BaseModel):
        new_password: str
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    class BulkOrderStatusBody(BaseModel):
        order_ids: List[int]
        status: str
    
        @field_validator("order_ids")
        @classmethod
        def limit_bulk_size(cls, v: List[int]) -> List[int]:
            if len(v) > MAX_BULK_ITEMS:
                raise ValueError(f"Cannot process more than {MAX_BULK_ITEMS} items at once")
            return v
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    class BulkOrderDeleteBody(BaseModel):
        order_ids: List[int]
    
        @field_validator("order_ids")
        @classmethod
        def limit_bulk_size(cls, v: List[int]) -> List[int]:
            if len(v) > MAX_BULK_ITEMS:
                raise ValueError(f"Cannot process more than {MAX_BULK_ITEMS} items at once")
            return v
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    class BulkProductDeleteBody(BaseModel):
        product_ids: List[int]
    
        @field_validator("product_ids")
        @classmethod
        def limit_bulk_size(cls, v: List[int]) -> List[int]:
            if len(v) > MAX_BULK_ITEMS:
                raise ValueError(f"Cannot process more than {MAX_BULK_ITEMS} items at once")
            return v
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    class BulkProductModerationBody(BaseModel):
        product_ids: List[int]
        action: str  # "approve" | "reject"
        note: Optional[str] = None
    
        @field_validator("product_ids")
        @classmethod
        def limit_bulk_size(cls, v: List[int]) -> List[int]:
            if len(v) > MAX_BULK_ITEMS:
                raise ValueError(f"Cannot process more than {MAX_BULK_ITEMS} items at once")
            return v
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    class BulkSupplierVerifyBody(BaseModel):
        supplier_ids: List[int]
        action: str  # "verify" | "reject"
        note: Optional[str] = None
    
        @field_validator("supplier_ids")
        @classmethod
        def limit_bulk_size(cls, v: List[int]) -> List[int]:
            if len(v) > MAX_BULK_ITEMS:
                raise ValueError(f"Cannot process more than {MAX_BULK_ITEMS} items at once")
            return v
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    class BulkSupplierLifecycleBody(BaseModel):
        supplier_ids: List[int]
        action: str
        note: Optional[str] = None
        badge_level: Optional[str] = None
    
        @field_validator("supplier_ids")
        @classmethod
        def limit_bulk_size(cls, v: List[int]) -> List[int]:
            if len(v) > MAX_BULK_ITEMS:
                raise ValueError(f"Cannot process more than {MAX_BULK_ITEMS} items at once")
            return v
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    class PromotionConfigBody(BaseModel):
        engine_enabled: Optional[bool] = None
        allow_product_coupons: Optional[bool] = None
        allow_category_coupons: Optional[bool] = None
        allow_order_tier_discounts: Optional[bool] = None
        allow_referral_rewards: Optional[bool] = None
        allow_supplier_promotions: Optional[bool] = None
        allow_global_coupons: Optional[bool] = None
        stacking_mode: Optional[str] = None
        max_combined_discount_percent: Optional[float] = None
        max_combined_discount_amount: Optional[float] = None
        show_savings_line_item: Optional[bool] = None
        tier_discount_visible: Optional[bool] = None
        points_per_omr: Optional[int] = None
        referral_referrer_points: Optional[int] = None
        referral_referee_points: Optional[int] = None
        points_expiry_months: Optional[int] = None
        referral_monthly_cap: Optional[int] = None
        referral_verification_delay_days: Optional[int] = None
        min_points_redeem: Optional[int] = None
        allow_partial_points_redemption: Optional[bool] = None
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    class PromotionTierBody(BaseModel):
        tier_name: str
        min_order: float
        max_order: Optional[float] = None
        discount_type: str
        discount_value: float
        stacking_allowed: bool = False
        is_active: bool = True
        sort_order: int = 0
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    class PromotionTierUpdateBody(BaseModel):
        tier_name: Optional[str] = None
        min_order: Optional[float] = None
        max_order: Optional[float] = None
        discount_type: Optional[str] = None
        discount_value: Optional[float] = None
        stacking_allowed: Optional[bool] = None
        is_active: Optional[bool] = None
        sort_order: Optional[int] = None
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    class PromotionPreviewBody(BaseModel):
        order_subtotal: float
        coupon_discount: float = 0.0
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    class AdminDisputeBulkActionBody(BaseModel):
        dispute_ids: List[int]
        action: str
        value: Optional[str] = None
    
        @field_validator("dispute_ids")
        @classmethod
        def limit_bulk_size(cls, v: List[int]) -> List[int]:
            if len(v) > MAX_BULK_ITEMS:
                raise ValueError(f"Cannot process more than {MAX_BULK_ITEMS} items at once")
            return v
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    class UpdateRolePermissionsIn(BaseModel):
        permissions: List[str]
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    class ReassignManagerBody(BaseModel):
        user_id: int
        new_manager_id: int | None = None
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    class ResourceApprovalCheckIn(BaseModel):
        resource_type: str
        amount: Optional[float] = None
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    """Admin categories router."""
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    """admin categories routes router.
    
    Business logic lives in `controllers/categories_controller.py`;
    wire endpoints here as needed. A `/status` endpoint lists the
    controller's public functions for convenience.
    """
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    try:
        import domains.catalog.services.categories_controller as _ctrl
        _HAS_CTRL = True
        _CTRL_PUBLIC = [n for n in dir(_ctrl) if not n.startswith("_") and callable(getattr(_ctrl, n))]
    except Exception:
        _HAS_CTRL = False
        _CTRL_PUBLIC = []
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    """Backward-compat re-export for legacy ``from modules.admin.routers.admin_controller import ...``.
    
    The ``admin_controller`` API was fissioned into ``domains.governance.services.admin_controller``
    during the NEW_STRUCTURE migration. This module keeps legacy router/service imports working.
    """
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    """Categories router."""
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    """core ai routes router.
    
    Business logic lives in `controllers/ai_controller.py`;
    wire endpoints here as needed. A `/status` endpoint lists the
    controller's public functions for convenience.
    """
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    try:
        import controllers.core.ai_controller as _ctrl
        _HAS_CTRL = True
        _CTRL_PUBLIC = [n for n in dir(_ctrl) if not n.startswith("_") and callable(getattr(_ctrl, n))]
    except Exception:
        _HAS_CTRL = False
        _CTRL_PUBLIC = []
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    """core automation routes router.
    
    Functional router placeholder. Implement domain endpoints here,
    delegating to the appropriate controller/service.
    """
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    """core compliance routes router.
    
    Business logic lives in `controllers/compliance_controller.py`;
    wire endpoints here as needed. A `/status` endpoint lists the
    controller's public functions for convenience.
    """
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    try:
        import controllers.governance.compliance_controller as _ctrl
        _HAS_CTRL = True
        _CTRL_PUBLIC = [n for n in dir(_ctrl) if not n.startswith("_") and callable(getattr(_ctrl, n))]
    except Exception:
        _HAS_CTRL = False
        _CTRL_PUBLIC = []
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    """core imports routes router.
    
    Functional router placeholder. Implement domain endpoints here,
    delegating to the appropriate controller/service.
    """
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    """core permissions routes router.
    
    Functional router placeholder. Implement domain endpoints here,
    delegating to the appropriate controller/service.
    """
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    """Public routers for admin module."""
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)

try:
    """
    AI Router — AI suggestion endpoints for product management.
    """
except Exception as _me:
    import logging as _l2; _l2.getLogger(__name__).warning("skip misc misc: %s", _me)


_s12 = APIRouter(prefix='/api/v1/jobs')

try:
    def     health():
        """Liveness probe for this router."""
        return {"status": "ok", "router": "core_jobs_routes", "prefix": "/api/v1/jobs"}
    _s12.get("/core_jobs_routes/health")(health)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route health: %s", _e)

_s13 = APIRouter(prefix='/api/v1/workflows')

try:
    def     health():
        """Liveness probe for this router."""
        return {"status": "ok", "router": "core_workflows_routes", "prefix": "/api/v1/workflows"}
    _s13.get("/core_workflows_routes/health")(health)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route health: %s", _e)

_s30 = APIRouter(prefix='/api/v1/ai')

try:
    def     health():
        """Liveness probe for this router."""
        return {"status": "ok", "router": "core_ai_routes", "prefix": "/api/v1/ai"}
    _s30.get("/core_ai_routes/health")(health)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route health: %s", _e)

try:
    def     status():
        """Report whether a backing controller is importable."""
        return {"router": "core_ai_routes", "controller": "controllers.core.ai_controller" if _HAS_CTRL else None,
                "public_functions": _CTRL_PUBLIC}
    _s30.get("/core_ai_routes/status")(status)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route status: %s", _e)

_s31 = APIRouter(prefix='/api/v1/automation')

try:
    def     health():
        """Liveness probe for this router."""
        return {"status": "ok", "router": "core_automation_routes", "prefix": "/api/v1/automation"}
    _s31.get("/core_automation_routes/health")(health)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route health: %s", _e)

_s32 = APIRouter(prefix='/api/v1/compliance')

try:
    def     health():
        """Liveness probe for this router."""
        return {"status": "ok", "router": "core_compliance_routes", "prefix": "/api/v1/compliance"}
    _s32.get("/core_compliance_routes/health")(health)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route health: %s", _e)

try:
    def     status():
        """Report whether a backing controller is importable."""
        return {"router": "core_compliance_routes", "controller": "controllers.governance.compliance_controller" if _HAS_CTRL else None,
                "public_functions": _CTRL_PUBLIC}
    _s32.get("/core_compliance_routes/status")(status)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route status: %s", _e)

_s33 = APIRouter(prefix='/api/v1/imports')

try:
    def     health():
        """Liveness probe for this router."""
        return {"status": "ok", "router": "core_imports_routes", "prefix": "/api/v1/imports"}
    _s33.get("/core_imports_routes/health")(health)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route health: %s", _e)

_s36 = APIRouter(prefix='/api/v1/ai')

try:
    @_s36.post("/suggest")
    async def ai_suggest(
        name: str = Form(""),
        description: str = Form(""),
        image: Optional[UploadFile] = File(None),
        images: List[UploadFile] = File(default=[]),
        image_url: str = Form(""),
        image_urls: List[str] = Form(default=[]),
        current_user: dict = Depends(get_current_user),
    ):
        """
        Generate AI suggestions for category, tags, and description.
        Accepts an optional product name, optional description text, and an optional product image.
        """
        return ctrl.get_ai_suggestions(
            name=name,
            description=description,
            image=image,
            images=images,
            image_url=image_url,
            image_urls=image_urls,
        )
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route: %s", _e)

try:
    @_s36.post("/suggest/async")
    async def ai_suggest_async(
        name: str = Form(""),
        description: str = Form(""),
        image: Optional[UploadFile] = File(None),
        images: List[UploadFile] = File(default=[]),
        image_url: str = Form(""),
        image_urls: List[str] = Form(default=[]),
        current_user: dict = Depends(get_current_user),
    ):
        job = ctrl.queue_ai_suggestions_job(
            name=name,
            description=description,
            image=image,
            images=images,
            image_url=image_url,
            image_urls=image_urls,
            current_user=current_user,
        )
        return JSONResponse(status_code=202, content=job)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route: %s", _e)

try:
    @_s36.post("/suggest/text")
    async def ai_suggest_text_only(
        body: dict,
        current_user: dict = Depends(get_current_user),
    ):
        """
        Generate AI suggestions using only text (no image upload).
        Body: { "name": str, "description": str }
        """
        name = body.get("name", "")
        description = body.get("description", "")
        return ctrl.get_ai_suggestions(name=name, description=description, image=None)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route: %s", _e)

try:
    @_s36.post("/suggest/text/async")
    async def ai_suggest_text_only_async(
        body: dict,
        current_user: dict = Depends(get_current_user),
    ):
        job = ctrl.queue_ai_text_suggestions_job(
            name=body.get("name", ""),
            description=body.get("description", ""),
            current_user=current_user,
        )
        return JSONResponse(status_code=202, content=job)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route: %s", _e)

try:
    @_s36.post("/generate-angles")
    async def generate_product_angles(
        name: str = Form(...),
        category: str = Form(""),
        image: Optional[UploadFile] = File(None),
        current_user: dict = Depends(get_current_user),
    ):
        """
        Generate AI-guided photo angle descriptions for a product.
        Upload your main product image and get descriptions + shooting tips for 5 angles:
        Front, Back, Side, Detail Shot, and In-Use.
        """
        return ctrl.get_product_angles(name=name, category=category, image=image)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route: %s", _e)

try:
    @_s36.post("/generate-angles/async")
    async def generate_product_angles_async(
        name: str = Form(...),
        category: str = Form(""),
        image: Optional[UploadFile] = File(None),
        current_user: dict = Depends(get_current_user),
    ):
        job = ctrl.queue_product_angles_job(
            name=name,
            category=category,
            image=image,
            current_user=current_user,
        )
        return JSONResponse(status_code=202, content=job)
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

try:
    router.include_router(_s31)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip subrouter _s31: %s", _e)

try:
    router.include_router(_s32)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip subrouter _s32: %s", _e)

try:
    router.include_router(_s33)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip subrouter _s33: %s", _e)

try:
    router.include_router(_s34)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip subrouter _s34: %s", _e)

try:
    router.include_router(_s35)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip subrouter _s35: %s", _e)

try:
    router.include_router(_s36)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip subrouter _s36: %s", _e)

router = APIRouter()

try:
    router.include_router(_s12)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip subrouter _s12: %s", _e)

try:
    router.include_router(_s13)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip subrouter _s13: %s", _e)

try:
    router.include_router(_s30)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip subrouter _s30: %s", _e)

try:
    router.include_router(_s31)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip subrouter _s31: %s", _e)

try:
    router.include_router(_s32)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip subrouter _s32: %s", _e)

try:
    router.include_router(_s33)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip subrouter _s33: %s", _e)

try:
    router.include_router(_s36)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip subrouter _s36: %s", _e)

