"""Admin finance router — canonical."""

from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body, status

from __future__ import annotations
from collections import defaultdict
from datetime import date
from datetime import date, datetime
from datetime import date, datetime, timezone
from datetime import datetime
from datetime import datetime, date
from decimal import Decimal
from domains.accounts.services._auto_stubs import get_hierarchy_permissions
from domains.accounts.services._auto_stubs import get_staff_permission_catalog
from domains.accounts.services.identity.identity_admin_service import delete_user_admin
from domains.accounts.services.users.users_admin_service import _build_list_page_payload
from domains.accounts.services.users.users_admin_service import get_all_users
from domains.accounts.services.users.users_admin_service import list_pending_bank_accounts
from domains.accounts.services.users.users_admin_service import list_staff_accounts
from domains.accounts.services.users.users_admin_service import verify_bank_account
from domains.analytics.services.analytics_service__analytics import get_analytics
from domains.analytics.services.analytics_service__analytics import get_analytics_timeseries
from domains.analytics.services.analytics_service__analytics import get_chatbot_analytics
from domains.analytics.services.analytics_service__analytics import get_customer_insights
from domains.analytics.services.analytics_service__analytics import get_top_products_analytics
from domains.analytics.services.analytics_service__analytics import get_user_growth_analytics
from domains.analytics.services.dashboards.analytics_fallback_service import get_treasury_metrics
from domains.catalog.services.products.admin_products_service import approve_product
from domains.catalog.services.products.admin_products_service import get_all_products
from domains.catalog.services.products.admin_products_service import reject_product
from domains.comms.services._auto_stubs import create_cash_account as create_cash_account_model
from domains.comms.services._auto_stubs import create_cash_transaction as create_cash_transaction_model
from domains.comms.services.shared.utility.shared_utils import reset_demo_data
from domains.comms.services.tickets.tickets_service import get_ticket_with_details as get_ticket_detail
from domains.comms.services.tickets.tickets_service import list_tickets
from domains.comms.services.tickets.tickets_service import update_ticket_status
from domains.country.models.countries import CountryConfig
from domains.country.services.core.country_service import _require_admin
from domains.country.utils.country_rls import get_country_or_404
from domains.customers.services.coupons_read_service import list_coupons
from domains.customers.services.coupons_service import create_coupon
from domains.customers.services.coupons_service import delete_coupon
from domains.customers.services.coupons_write_service import update_coupon
from domains.finance.models.commission import CommissionCategoryRate
from domains.finance.models.general_ledger import Account
from domains.finance.models.general_ledger import AccountBalance
from domains.finance.models.general_ledger import BankTransaction
from domains.finance.models.general_ledger import CashAccount
from domains.finance.models.general_ledger import CashFlowForecast
from domains.finance.models.general_ledger import CashPositionSnapshot
from domains.finance.models.general_ledger import CashTransaction
from domains.finance.models.general_ledger import FinanceAutomationLog
from domains.finance.models.general_ledger import GatewaySettlementSchedule
from domains.finance.models.general_ledger import Invoice
from domains.finance.models.general_ledger import JournalEntry
from domains.finance.models.general_ledger import JournalEntryLine
from domains.finance.models.general_ledger import PayoutBatch
from domains.finance.models.general_ledger import PayoutBatchItem
from domains.finance.models.general_ledger import SupplierSettlement
from domains.finance.models.general_ledger import TransactionLedger
from domains.finance.models.general_ledger import TreasuryAccount
from domains.finance.models.general_ledger import VATRemittance
from domains.finance.models.payments import LogisticsPartnerPayout
from domains.finance.models.payments import Payment
from domains.finance.models.payments import Payment as PaymentModel
from domains.finance.models.payments import Payout
from domains.finance.ports import list_accounts
from domains.finance.ports import list_product_commission_overrides
from domains.finance.services._auto_stubs import FinancialReportingService
from domains.finance.services._auto_stubs import JournalEntryBody
from domains.finance.services._auto_stubs import TreasuryEngine
from domains.finance.services._auto_stubs import accounting_controller
from domains.finance.services._auto_stubs import batch_categorize_all
from domains.finance.services._auto_stubs import categorize_expense_ai
from domains.finance.services._auto_stubs import controller_get_ap_summary
from domains.finance.services._auto_stubs import controller_get_ar_summary
from domains.finance.services._auto_stubs import controller_post_ap_payable
from domains.finance.services._auto_stubs import controller_post_ap_payment
from domains.finance.services._auto_stubs import controller_post_ar_invoice
from domains.finance.services._auto_stubs import controller_post_ar_payment
from domains.finance.services._auto_stubs import get_account
from domains.finance.services._auto_stubs import get_cash_position
from domains.finance.services._auto_stubs import get_payout_by_id, list_pending_payouts
from domains.finance.services._auto_stubs import get_supplier_payables
from domains.finance.services._auto_stubs import get_vat_liability
from domains.finance.services._auto_stubs import process_email_inbox
from domains.finance.services._auto_stubs import process_email_invoice
from domains.finance.services._auto_stubs import process_mobile_scan
from domains.finance.services._auto_stubs import queue_dispatch_transfer_batch
from domains.finance.services._auto_stubs import run_ai_bank_reconciliation
from domains.finance.services._auto_stubs import trading_service as trading
from domains.finance.services.country.admin_commission_service import create_badge_tier
from domains.finance.services.country.admin_commission_service import list_badge_tiers
from domains.finance.services.country.admin_commission_service import update_badge_tier
from domains.finance.services.finance_service import delete_product_commission_override
from domains.finance.services.finance_service import delete_supplier_commission_override
from domains.finance.services.finance_service import get_effective_rate
from domains.finance.services.finance_service import get_global_config
from domains.finance.services.finance_service import get_product_commission_override
from domains.finance.services.finance_service import get_supplier_commission
from domains.finance.services.finance_service import list_category_rates
from domains.finance.services.finance_service import list_ledger_entries
from domains.finance.services.finance_service import preview_commission
from domains.finance.services.finance_service import set_product_commission_override
from domains.finance.services.finance_service import set_supplier_commission
from domains.finance.services.finance_service import update_category_rate
from domains.finance.services.finance_service import update_global_config
from domains.finance.services.ledger.general_ledger_service import _category_to_slug
from domains.finance.services.ledger.general_ledger_service import _float_or_none
from domains.finance.services.ledger.general_ledger_service import _serialize_agreement
from domains.finance.services.ledger.general_ledger_service import _serialize_badge_tier
from domains.finance.services.ledger.general_ledger_service import _serialize_category_rate
from domains.finance.services.ledger.general_ledger_service import _serialize_global_config
from domains.finance.services.ledger.general_ledger_service import _serialize_ledger_entry
from domains.finance.services.ledger.general_ledger_service import _serialize_override
from domains.finance.services.ledger.general_ledger_service import _supplier_rate_snapshot
from domains.finance.services.ledger.general_ledger_service import close_period
from domains.finance.services.ledger.general_ledger_service import create_category_rate
from domains.finance.services.ledger.general_ledger_service import create_journal_entry
from domains.finance.services.ledger.general_ledger_service import create_ledger_adjustment
from domains.finance.services.ledger.general_ledger_service import get_account_balance
from domains.finance.services.ledger.general_ledger_service import get_current_fiscal_period
from domains.finance.services.ledger.general_ledger_service import get_journal_entry
from domains.finance.services.ledger.general_ledger_service import get_or_create_fiscal_period
from domains.finance.services.ledger.general_ledger_service import get_supplier_policy_snapshot
from domains.finance.services.ledger.general_ledger_service import get_trial_balance
from domains.finance.services.ledger.general_ledger_service import list_all_supplier_commissions
from domains.finance.services.ledger.general_ledger_service import list_journal_entries
from domains.finance.services.ledger.general_ledger_service import list_periods
from domains.finance.services.ledger.general_ledger_service import post_logistics_cod_remittance_journal
from domains.finance.services.ledger.general_ledger_service import post_supplier_settlement_journal
from domains.finance.services.ledger.general_ledger_service import reverse_journal_entry
from domains.finance.services.ledger.general_ledger_service import seed_chart_of_accounts
from domains.finance.services.payments.payment_orchestrator import match_gateway_settlement
from domains.finance.services.payments.payment_orchestrator import reconcile_cod_deposit
from domains.finance.services.payments.payment_orchestrator import run_gateway_3way_reconciliation
from domains.finance.services.payouts.payout_batch_service import approve_batch
from domains.finance.services.payouts.payout_batch_service import approve_batch as approve_batch_action
from domains.finance.services.payouts.payout_batch_service import approve_payout
from domains.finance.services.payouts.payout_batch_service import approve_payout as approve_payout_action
from domains.finance.services.payouts.payout_batch_service import approve_payout, reject_payout, approve_batch, reject_batch, dispatch_batch
from domains.finance.services.payouts.payout_batch_service import dispatch_batch
from domains.finance.services.payouts.payout_batch_service import dispatch_batch as dispatch_batch_action
from domains.finance.services.payouts.payout_batch_service import generate_logistics_payout_batches
from domains.finance.services.payouts.payout_batch_service import generate_supplier_payout_batches
from domains.finance.services.payouts.payout_batch_service import get_background_job_status as _get_bg_status
from domains.finance.services.payouts.payout_batch_service import get_pending_batches_for_supplier
from domains.finance.services.payouts.payout_batch_service import list_pending_payouts
from domains.finance.services.payouts.payout_batch_service import post_refund_automatically
from domains.finance.services.payouts.payout_batch_service import reject_batch
from domains.finance.services.payouts.payout_batch_service import reject_batch as reject_batch_action
from domains.finance.services.payouts.payout_batch_service import reject_payout
from domains.finance.services.payouts.payout_batch_service import reject_payout as reject_payout_action
from domains.finance.services.payouts.payout_batch_service import run_auto_logistics_payout_sweep as _run_logistics_sweep
from domains.finance.services.payouts.payout_batch_service import run_auto_payout_sweep as _run_supplier_sweep
from domains.finance.services.payouts.payout_batch_service import start_auto_payout_background_job as _start_bg_job
from domains.finance.services.payouts.payout_batch_service import stop_auto_payout_background_job as _stop_bg_job
from domains.finance.services.payouts.payout_batch_service import supplier_approve_batch
from domains.finance.services.payouts.payout_batch_service import update_background_status
from domains.finance.services.payouts.payout_batch_service import verify_payout
from domains.finance.services.treasury.cash_management_service import auto_reconcile_transactions
from domains.finance.services.treasury.cash_management_service import check_customer_credit
from domains.finance.services.treasury.cash_management_service import create_bank_transaction
from domains.finance.services.treasury.cash_management_service import dispatch_transfer_batch
from domains.finance.services.treasury.cash_management_service import enforce_auto_credit_holds
from domains.finance.services.treasury.cash_management_service import flag_transaction
from domains.finance.services.treasury.cash_management_service import generate_forecast as generate_cash_forecast
from domains.finance.services.treasury.cash_management_service import get_customer_credit_summary
from domains.finance.services.treasury.cash_management_service import import_bank_transactions
from domains.finance.services.treasury.cash_management_service import reconcile_transaction
from domains.finance.services.treasury.cash_management_service import record_badge_billing_payment
from domains.finance.services.treasury.cash_management_service import record_cod_remittance
from domains.finance.services.treasury.cash_management_service import record_vat_remittance
from domains.finance.services.treasury.cash_management_service import reject_cod_remittance_receipt
from domains.finance.services.treasury.cash_management_service import resolve_transaction_exception
from domains.finance.services.treasury.cash_management_service import trigger_logistics_payouts
from domains.finance.services.treasury.cash_management_service import trigger_supplier_payouts
from domains.finance.services.treasury.cash_management_service import upsert_bank_settings
from domains.finance.services.treasury.cash_management_service import verify_cod_remittance_receipt
from domains.governance.core.export_service import (
from domains.governance.models.admin import CommissionBadgeTier
from domains.governance.models.admin import LogisticsCODRemittanceReceipt
from domains.governance.models.user import User
from domains.governance.services._auto_stubs import APPROVAL_RULES
from domains.governance.services._auto_stubs import get_all_suppliers
from domains.governance.services._auto_stubs import get_pending_products
from domains.governance.services._auto_stubs import get_pending_suppliers
from domains.governance.services._auto_stubs import get_supplier_comparison
from domains.governance.services._auto_stubs import require_admin_2fa_verified
from domains.governance.services.approval.approval_matrix_service import can_approve
from domains.governance.services.approval.approval_matrix_service import get_approval_chain
from domains.governance.services.approval.approval_matrix_service import require_approval
from domains.governance.services.approval.approval_matrix_service import resolve_approvers
from domains.governance.services.settings.misc_service import get_audit_log_page
from domains.governance.services.settings.misc_service import get_available_audit_actions
from domains.hr.models.employee_models import Employee
from domains.hr.services.hierarchy.hierarchy_service import backfill_authority_levels
from domains.hr.services.hierarchy.hierarchy_service import can_manage as hierarchy_can_manage_service
from domains.hr.services.hierarchy.hierarchy_service import get_all_subordinates
from domains.hr.services.hierarchy.hierarchy_service import get_authority_level
from domains.hr.services.hierarchy.hierarchy_service import get_org_chart
from domains.hr.services.hierarchy.hierarchy_service import get_team_members
from domains.hr.services.hierarchy.hierarchy_service import get_user_chain
from domains.hr.services.hierarchy.hierarchy_service import is_in_chain
from domains.hr.services.hierarchy.hierarchy_service import reassign_manager
from domains.logistics.models.logistics_entities import LogisticsPartner
from domains.logistics.models.logistics_entities import Shipment
from domains.logistics.models.logistics_entities import Shipment as ShipmentModel
from domains.logistics.services.core.service import verify_payout_route
from domains.media.services.ai import automation_scheduler as scheduler
from domains.orders.models.order_entities import Order as OrderModel
from domains.orders.models.order_entities import OrderItem
from domains.orders.services._auto_stubs import delete_flash_sale
from domains.orders.services._auto_stubs import disputes_controller
from domains.orders.services._auto_stubs import get_all_flash_sales
from domains.orders.services.orders_service import get_all_orders
from domains.promotions.services.admin_promotion_service import create_banner
from domains.promotions.services.admin_promotion_service import create_flash_sale
from domains.promotions.services.admin_promotion_service import delete_banner
from domains.promotions.services.admin_promotion_service import get_promotion_config
from domains.promotions.services.admin_promotion_service import list_promotion_tiers
from domains.promotions.services.admin_promotion_service import update_banner
from domains.promotions.services.admin_promotion_service import update_flash_sale
from domains.promotions.services.admin_promotion_service import update_promotion_config
from domains.promotions.services.banners.banner_service import BannerCreate
from domains.promotions.services.banners.banner_service import BannerUpdate
from domains.promotions.services.banners.banner_service import get_banner_by_id
from domains.promotions.services.engine.promotion_service import create_promotion_tier
from domains.promotions.services.engine.promotion_service import delete_promotion_tier
from domains.promotions.services.engine.promotion_service import preview_order_tier_discount
from domains.promotions.services.engine.promotion_service import update_promotion_tier
from domains.suppliers.models.suppliers import SupplierProfile
from infrastructure.config import settings
from infrastructure.database.database import get_db
from infrastructure.database.database_service import get_database_overview
from infrastructure.database.schemas import (
from infrastructure.database.schemas import CashAccountCreate, CashAccountOut, CashTransactionCreate, CashTransactionOut
from infrastructure.database.schemas import CommissionCategoryRateCreate, CommissionCategoryRateOut, CommissionBadgeTierCreate, CommissionBadgeTierOut
from infrastructure.database.schemas import FlashSaleCreate, FlashSaleOut
from infrastructure.database.schemas import PayoutCreate, PayoutOut
from infrastructure.routing.route_contract import post
from infrastructure.security.auth import require_permission
from infrastructure.utils.audit import AuditAction, audit_log
from infrastructure.utils.audit import audit_log, AuditAction
from infrastructure.utils.backup import get_backup_manager
from infrastructure.utils.constants import (
from infrastructure.utils.constants import MAX_BULK_ITEMS
from infrastructure.utils.datetime_utils import utcnow
from infrastructure.utils.dependencies import require_admin
from infrastructure.utils.operations_service import reply_to_ticket
from infrastructure.utils.rls_interceptor import clear_rls_context, set_rls_context
from infrastructure.utils.rls_interceptor import set_rls_context, clear_rls_context
from modules.admin.auth import get_current_admin, get_current_user, require_admin
from pydantic import BaseModel
from pydantic import BaseModel, field_validator
from rbac import get_current_user
from rbac.dependencies import require_feature, require_module
from sqlalchemy import func, select
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from sqlalchemy.orm import Session, joinedload
from typing import Any
from typing import Any, Optional
from typing import Any, cast
from typing import List, Optional
from typing import Optional
import domains.finance.services.ledger.invoice_controller as _ic
import json
import logging
import logging as _l; _l.getLogger(__name__).warning("skip route admin_approve_payout_batch: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route admin_approve_pending: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route admin_approve_settlement: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route admin_cash_forecasts: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route admin_cash_position: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route admin_cod_remittances: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route admin_detect_orphans: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route admin_dispatch_payout_batch: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route admin_gateway_exceptions: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route admin_gateway_summary: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route admin_generate_payout_batch: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route admin_invoices_overview: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route admin_liabilities_exposure: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route admin_logistics_payouts: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route admin_manual_adjustment: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route admin_payment_transactions: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route admin_payout_batches: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route admin_pending_entries: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route admin_reconciliation_pipeline: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route admin_record_cod_remittance: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route admin_reject_pending: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route admin_settle_supplier: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route admin_snapshot_cash_position: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route admin_supplier_earnings: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route admin_supplier_payouts: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route admin_treasury_ledger: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route admin_treasury_metrics: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route admin_treasury_root: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route admin_trial_balance: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route admin_vat_liability: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route approve_batch: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route approve_batch_route: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route approve_payout: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route approve_payout_route: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route auto_reconcile_transactions_route: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route balance_sheet: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route bulk_admin_dispute_action: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route cash_flow: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route cash_flow_forecast: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route cash_position: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route close_fiscal_period: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route consolidated_cash_forecasts: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route consolidated_cash_position: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route consolidated_cod_remittances: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route consolidated_gateway_summary: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route consolidated_payout_batches: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route consolidated_reconciliation_pipeline: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route consolidated_treasury_ledger: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route consolidated_treasury_metrics: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route consolidated_trial_balance: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route consolidated_vat_liability: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route controller_get_ap_summary_route: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route controller_get_ar_summary_route: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route controller_post_ap_payable_route: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route controller_post_ap_payment_route: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route controller_post_ar_invoice_route: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route controller_post_ar_payment_route: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route country_approve_pending: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route country_cash_position: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route country_cod_remittances: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route country_detect_orphans: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route country_gateway_exceptions: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route country_gateway_summary: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route country_liabilities_exposure: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route country_logistics_payouts: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route country_manual_adjustment: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route country_payment_transactions: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route country_payout_batches: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route country_payroll: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route country_pending_entries: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route country_reject_pending: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route country_supplier_earnings: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route country_supplier_payouts: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route country_treasury_ledger: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route country_treasury_metrics: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route country_trial_balance: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route country_vat_liability: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route create_account: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route create_badge_tier: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route create_badge_tier_route: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route create_bank_transaction_route: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route create_journal_entry: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route create_journal_entry_route: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route create_payout: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route create_rate: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route create_transaction: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route current_period: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route dispatch_batch: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route dispatch_batch_route: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route dispatch_transfer_batch_route: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route flag_transaction_route: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route get_account: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route get_account_balance_route: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route get_account_route: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route get_admin_dispute: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route get_ap: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route get_ap_alias: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route get_ar: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route get_background_job_status_endpoint: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route get_balance: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route get_journal_entry: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route get_journal_entry_route: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route get_or_create: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route get_pending_payouts: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route get_pending_payouts_route: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route get_trial_balance_route: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route health: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route import_bank_transactions_route: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route income_statement: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route list_accounts: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route list_accounts_route: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route list_admin_disputes: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route list_badge_tiers: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route list_badge_tiers_route: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route list_fiscal_periods: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route list_journal_entries: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route list_journal_entries_route: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route list_payouts: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route list_pending_payouts: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route list_pending_payouts_by_country: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route list_pending_payouts_route_route: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route list_rates: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route list_reports: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route patch_admin_dispute: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route payroll_equity: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route post_ap_payable_route: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route post_ap_payment_route: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route post_ar_invoice_route: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route post_ar_payment_route: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route process_payout: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route queue_dispatch_transfer_batch_route: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route reconcile_transaction_route: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route record_badge_billing_payment_route: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route record_cod_remittance_route: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route record_vat_remittance_route: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route reject_batch: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route reject_batch_route: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route reject_cod_remittance_receipt_route: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route reject_payout: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route reject_payout_route: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route resolve_transaction_exception_route: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route reverse_entry: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route run_auto_payout_sweep: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route seed_chart_of_accounts: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route seed_chart_of_accounts_route: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route start_background_job: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route status: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route stop_background_job: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route supplier_payables: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route treasury_metrics: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route trial_balance: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route trigger_background_job: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route trigger_background_job_kind: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route trigger_logistics_payouts_route: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route trigger_supplier_payouts_route: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route update_badge_tier: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route update_badge_tier_route: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route update_rate: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route upsert_bank_settings_route: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route vat_liability: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route verify_cod_remittance_receipt_route: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route verify_payout: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route verify_payout_route: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip route verify_payout_route_route: %s", _e)
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
import logging as _l; _l.getLogger(__name__).warning("skip subrouter _s31: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip subrouter _s32: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip subrouter _s33: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip subrouter _s34: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip subrouter _s3: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip subrouter _s4: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip subrouter _s5: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip subrouter _s6: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip subrouter _s7: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip subrouter _s8: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip subrouter _s9: %s", _e)
import structlog

router = APIRouter(prefix="/api/v1/admin/finance", tags=["admin", "finance"])

@router.get("/{country_code}/accounts", response_model=list[CashAccountOut])
def list_accounts(country_code: str = Path(..., description="ISO country code"), _: User = Depends(require_admin), db: Session = Depends(get_db)):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return db.query(CashAccount).filter(CashAccount.is_active == True, CashAccount.country_code == country_code.upper()).all()
    finally:
        clear_rls_context()




@router.post("/{country_code}/accounts", response_model=CashAccountOut, status_code=201)
def create_account(country_code: str = Path(..., description="ISO country code"), payload: CashAccountCreate = None, _: User = Depends(require_admin), db: Session = Depends(get_db)):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        account_data = payload.model_dump()
        account_data["country_code"] = country_code.upper()
        a = create_cash_account_model(db, **account_data)
        return a
    finally:
        clear_rls_context()




@router.post("/{country_code}/transactions", response_model=CashTransactionOut, status_code=201)
def create_transaction(country_code: str = Path(..., description="ISO country code"), payload: CashTransactionCreate = None, current_user: User = Depends(require_admin), db: Session = Depends(get_db)):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        account = db.query(CashAccount).filter(CashAccount.id == payload.account_id, CashAccount.country_code == country_code.upper()).first()
        if not account: raise HTTPException(404, "Account not found")
        if payload.transaction_type == "debit":
            account.balance -= payload.amount
        else:
            account.balance += payload.amount
        tx_data = payload.model_dump()
        tx_data["balance_after"] = account.balance
        tx_data["performed_by"] = current_user.id
        tx_data["country_code"] = country_code.upper()
        tx = create_cash_transaction_model(db, **tx_data)
        return tx
    finally:
        clear_rls_context()




@router.post("/seed", status_code=201, tags=['accounting'], summary="Seed chart of accounts (idempotent)")
def seed_chart_of_accounts_route(
    db: Session = Depends(get_db),
    audit_user_id: Optional[int] = Query(None),
    audit_username: Optional[str] = Query(None),
    audit_user_role: Optional[str] = Query(None)


@router.get("/accounts", status_code=200, tags=['accounting'], summary="List all accounts")
def list_accounts_route(
    db: Session = Depends(get_db)


@router.get("/accounts/{code}", status_code=200, tags=['accounting'], summary="Get account by code")
def get_account_route(
    code: str,
    db: Session = Depends(get_db)


@router.post("/journal-entries", status_code=201, tags=['accounting'], summary="Create a journal entry")
def create_journal_entry_route(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
    body: JournalEntryBody = Body(...)


@router.get("/journal-entries/{entry_id}", status_code=200, tags=['accounting'], summary="Get journal entry by ID")
def get_journal_entry_route(
    entry_id: int,
    db: Session = Depends(get_db)


@router.get("/journal-entries", status_code=200, tags=['accounting'], summary="List journal entries")
def list_journal_entries_route(
    db: Session = Depends(get_db),
    reference_type: Optional[str] = Query(None),
    reference_id: Optional[int] = Query(None),
    country_code: Optional[str] = Query(None),
    limit: int = Query(50)


@router.get("/balances/{account_code}", status_code=200, tags=['accounting'], summary="Get account balance")
def get_account_balance_route(
    account_code: str,
    db: Session = Depends(get_db),
    currency: str = Query('OMR')


@router.get("/trial-balance", status_code=200, tags=['accounting'], summary="Get trial balance")
def get_trial_balance_route(
    db: Session = Depends(get_db),
    as_of_date: Optional[date] = Query(None),
    currency: str = Query('OMR'),
    country_code: Optional[str] = Query(None)


@router.post("/seed", summary="Seed chart of accounts (idempotent)")
def seed_chart_of_accounts(
    db: Session = Depends(get_db),
    _admin: dict = Depends(require_admin),


@router.get("/accounts", summary="List all accounts")
def list_accounts(
    country_code: str = Query(None, max_length=3),
    db: Session = Depends(get_db),
    _user=Depends(require_admin),


@router.get("/accounts/{code}", summary="Get account by code")
def get_account(
    code: str,
    country_code: str = Query(None, max_length=3),
    db: Session = Depends(get_db),
    _user=Depends(require_admin),


@router.post("/journal-entries", summary="Create a journal entry")
def create_journal_entry(
    body: accounting_controller.JournalEntryBody,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),


@router.get("/journal-entries", summary="List journal entries")
def list_journal_entries(
    reference_type: Optional[str] = Query(None, max_length=40),
    reference_id: Optional[int] = Query(None),
    country_code: Optional[str] = Query(None, max_length=3),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
    _user=Depends(require_admin),


@router.get("/journal-entries/{entry_id}", summary="Get journal entry by ID")
def get_journal_entry(
    entry_id: int,
    country_code: str = Query(None, max_length=3),
    db: Session = Depends(get_db),
    _user=Depends(require_admin),


@router.get("/balances/{account_code}", summary="Get account balance")
def get_balance(
    account_code: str,
    currency: str = Query("OMR", max_length=10),
    country_code: str = Query(None, max_length=3),
    db: Session = Depends(get_db),
    _user=Depends(require_admin),


@router.get("/trial-balance", summary="Get trial balance")
def trial_balance(
    as_of_date: Optional[date] = Query(None),
    currency: str = Query("OMR", max_length=10),
    country_code: Optional[str] = Query(None, max_length=3),
    db: Session = Depends(get_db),
    _user=Depends(require_admin),


@router.post("/reports/income-statement", summary="Generate Income Statement (P&L)")
def income_statement(
    body: ReportPeriod,
    db: Session = Depends(get_db),
    _admin: dict = Depends(require_admin),


@router.post("/reports/balance-sheet", summary="Generate Balance Sheet")
def balance_sheet(
    as_of_date: Optional[datetime] = Query(None, description="Defaults to now"),
    currency: str = Query("OMR", max_length=10),
    persist: bool = Query(False),
    country_code: Optional[str] = Query(None, max_length=3),
    db: Session = Depends(get_db),
    _admin: dict = Depends(require_admin),


@router.post("/reports/cash-flow", summary="Generate Cash Flow Statement")
def cash_flow(
    body: ReportPeriod,
    db: Session = Depends(get_db),
    _admin: dict = Depends(require_admin),


@router.get("/reports", summary="List saved financial reports")
def list_reports(
    report_type: Optional[str] = Query(None, description="Filter by report type"),
    country_code: Optional[str] = Query(None, max_length=3),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    _user=Depends(require_admin),


@router.post("/periods/get-or-create", summary="Get or create a fiscal period")
def get_or_create(
    country_code: str = Query(..., max_length=3),
    year: int = Query(..., ge=2020, le=2100),
    month: int = Query(..., ge=1, le=12),
    db: Session = Depends(get_db),
    _admin: dict = Depends(require_admin),


@router.get("/periods/current", summary="Get current fiscal period")
def current_period(
    country_code: str = Query(..., max_length=3),
    db: Session = Depends(get_db),
    _user=Depends(require_admin),


@router.post("/periods/close", summary="Close a fiscal period")
def close_fiscal_period(
    body: ClosePeriodBody,
    db: Session = Depends(get_db),
    _admin: dict = Depends(require_admin),


@router.get("/periods", summary="List fiscal periods")
def list_fiscal_periods(
    country_code: Optional[str] = Query(None, max_length=3),
    status: Optional[str] = Query(None),
    limit: int = Query(24, ge=1, le=120),
    db: Session = Depends(get_db),
    _user=Depends(require_admin),


@router.post("/journal-entries/reverse", summary="Reverse a journal entry")
def reverse_entry(
    body: ReversalBody,
    db: Session = Depends(get_db),
    _admin: dict = Depends(require_admin),


@router.post("/cash-flow-forecast", summary="Generate cash flow forecast")
def cash_flow_forecast(
    days: int = Query(90, ge=1, le=365),
    currency: str = Query("OMR", max_length=10),
    country_code: Optional[str] = Query(None, max_length=3),
    db: Session = Depends(get_db),
    _admin: dict = Depends(require_admin),


@router.get("/ar", summary="AR sub-ledger (customer receivables)")
def get_ar(
    customer_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    country_code: Optional[str] = Query(None, max_length=3),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
    _admin: dict = Depends(require_admin),


@router.post("/ar-ledger/invoice", summary="Post AR invoice")
def post_ar_invoice_route(body: ARInvoiceBody, db: Session = Depends(get_db), _admin: dict = Depends(require_admin)):
    cleanup = _with_rls(body.country_code, db)
    try:
        return controller_post_ar_invoice(db, **body.model_dump(), admin_user=_admin)
    finally:
        cleanup()




@router.post("/ar-ledger/payment", summary="Post AR payment")
def post_ar_payment_route(body: ARPaymentBody, db: Session = Depends(get_db), _admin: dict = Depends(require_admin)):
    cleanup = _with_rls(body.country_code, db)
    try:
        return controller_post_ar_payment(db, **body.model_dump(), admin_user=_admin)
    finally:
        cleanup()




@router.get("/ap", summary="AP Sub-ledger alias (Accounts Payable)")
def get_ap_alias(
    supplier_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    country_code: Optional[str] = Query(None, max_length=3),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
    _admin: dict = Depends(require_admin),


@router.get("/ap-ledger", summary="AP Sub-ledger (Accounts Payable)")
def get_ap(
    supplier_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    country_code: Optional[str] = Query(None, max_length=3),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
    _admin: dict = Depends(require_admin),


@router.post("/ap-ledger/payable", summary="Post AP payable")
def post_ap_payable_route(body: APPayableBody, db: Session = Depends(get_db), _admin: dict = Depends(require_admin)):
    cleanup = _with_rls(body.country_code, db)
    try:
        return controller_post_ap_payable(db, **body.model_dump(), admin_user=_admin)
    finally:
        cleanup()




@router.post("/ap-ledger/payment", summary="Post AP payment")
def post_ap_payment_route(body: APPaymentBody, db: Session = Depends(get_db), _admin: dict = Depends(require_admin)):
    cleanup = _with_rls(body.country_code, db)
    try:
        return controller_post_ap_payment(db, **body.model_dump(), admin_user=_admin)
    finally:
        cleanup()




@router.get("/{country_code}/rates")
def list_rates(country_code: str = Path(..., description="ISO country code"), _: User = Depends(require_admin), db: Session = Depends(get_db), page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100)):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return list_category_rates(db, country_code, page, page_size)
    finally:
        clear_rls_context()




@router.post("/{country_code}/rates", response_model=CommissionCategoryRateOut, status_code=201)
def create_rate(country_code: str = Path(..., description="ISO country code"), payload: CommissionCategoryRateCreate = None, _: User = Depends(require_admin), db: Session = Depends(get_db)):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return create_category_rate(db, payload, country_code)
    finally:
        clear_rls_context()




@router.put("/{country_code}/rates/{rate_id}", response_model=CommissionCategoryRateOut)
def update_rate(country_code: str = Path(..., description="ISO country code"), rate_id: int = Path(..., description="Rate id"), payload: CommissionCategoryRateCreate = None, _: User = Depends(require_admin), db: Session = Depends(get_db)):
    get_country_or_404(country_code.upper(), db)
    return update_category_rate(db, rate_id, country_code, payload)




@router.get("/{country_code}/badge-tiers")
def list_badge_tiers_route(country_code: str = Path(..., description="ISO country code"), _: User = Depends(require_admin), db: Session = Depends(get_db), page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100)):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return list_badge_tiers(db, country_code, page, page_size)
    finally:
        clear_rls_context()




@router.post("/{country_code}/badge-tiers", response_model=CommissionBadgeTierOut, status_code=201)
def create_badge_tier_route(country_code: str = Path(..., description="ISO country code"), payload: CommissionBadgeTierCreate = None, _: User = Depends(require_admin), db: Session = Depends(get_db)):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return create_badge_tier(db, payload, country_code)
    finally:
        clear_rls_context()




@router.put("/{country_code}/badge-tiers/{tier_id}", response_model=CommissionBadgeTierOut)
def update_badge_tier_route(country_code: str = Path(..., description="ISO country code"), tier_id: int = Path(..., description="Badge tier id"), payload: CommissionBadgeTierCreate = None, _: User = Depends(require_admin), db: Session = Depends(get_db)):
    get_country_or_404(country_code.upper(), db)
    return update_badge_tier(db, tier_id, country_code, payload)



@router.get("/admin/ar", status_code=200, tags=['finance'])
def controller_get_ar_summary_route(
    db: Session = Depends(get_db),
    customer_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    country_code: Optional[str] = Query(None),
    limit: int = Query(50)


@router.get("/ar", status_code=200, tags=['finance'])
def controller_get_ar_summary_route(
    db: Session = Depends(get_db),
    customer_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    country_code: Optional[str] = Query(None),
    limit: int = Query(50)


@router.get("/admin/ap", status_code=200, tags=['finance'])
def controller_get_ap_summary_route(
    db: Session = Depends(get_db),
    supplier_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    country_code: Optional[str] = Query(None),
    limit: int = Query(50)


@router.get("/ap", status_code=200, tags=['finance'])
def controller_get_ap_summary_route(
    db: Session = Depends(get_db),
    supplier_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    country_code: Optional[str] = Query(None),
    limit: int = Query(50)


@router.get("/admin/ap-ledger", status_code=200, tags=['finance'])
def controller_get_ap_summary_route(
    db: Session = Depends(get_db),
    supplier_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    country_code: Optional[str] = Query(None),
    limit: int = Query(50)


@router.get("/ap-ledger", status_code=200, tags=['finance'])
def controller_get_ap_summary_route(
    db: Session = Depends(get_db),
    supplier_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    country_code: Optional[str] = Query(None),
    limit: int = Query(50)


@router.post("/admin/ar-ledger/invoice", status_code=201, tags=['finance'])
def controller_post_ar_invoice_route(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
    customer_id: int = Body(...),
    amount: float = Body(...),
    order_id: Optional[int] = Body(None),
    invoice_id: Optional[int] = Body(None),
    due_date: Optional[str] = Body(None),
    description: Optional[str] = Body(None),
    currency: str = Body('OMR'),
    country_code: Optional[str] = Body(None)


@router.post("/ar-ledger/invoice", status_code=201, tags=['finance'])
def controller_post_ar_invoice_route(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
    customer_id: int = Body(...),
    amount: float = Body(...),
    order_id: Optional[int] = Body(None),
    invoice_id: Optional[int] = Body(None),
    due_date: Optional[str] = Body(None),
    description: Optional[str] = Body(None),
    currency: str = Body('OMR'),
    country_code: Optional[str] = Body(None)


@router.post("/admin/ar-ledger/payment", status_code=201, tags=['finance'])
def controller_post_ar_payment_route(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
    customer_id: int = Body(...),
    amount: float = Body(...),
    invoice_id: Optional[int] = Body(None),
    order_id: Optional[int] = Body(None),
    description: Optional[str] = Body(None),
    currency: str = Body('OMR'),
    country_code: Optional[str] = Body(None)


@router.post("/ar-ledger/payment", status_code=201, tags=['finance'])
def controller_post_ar_payment_route(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
    customer_id: int = Body(...),
    amount: float = Body(...),
    invoice_id: Optional[int] = Body(None),
    order_id: Optional[int] = Body(None),
    description: Optional[str] = Body(None),
    currency: str = Body('OMR'),
    country_code: Optional[str] = Body(None)


@router.post("/admin/ap-ledger/payable", status_code=201, tags=['finance'])
def controller_post_ap_payable_route(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
    supplier_id: int = Body(...),
    amount: float = Body(...),
    order_id: Optional[int] = Body(None),
    settlement_id: Optional[int] = Body(None),
    due_date: Optional[str] = Body(None),
    description: Optional[str] = Body(None),
    currency: str = Body('OMR'),
    country_code: Optional[str] = Body(None)


@router.post("/ap-ledger/payable", status_code=201, tags=['finance'])
def controller_post_ap_payable_route(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
    supplier_id: int = Body(...),
    amount: float = Body(...),
    order_id: Optional[int] = Body(None),
    settlement_id: Optional[int] = Body(None),
    due_date: Optional[str] = Body(None),
    description: Optional[str] = Body(None),
    currency: str = Body('OMR'),
    country_code: Optional[str] = Body(None)


@router.post("/admin/ap-ledger/payment", status_code=201, tags=['finance'])
def controller_post_ap_payment_route(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
    supplier_id: int = Body(...),
    amount: float = Body(...),
    settlement_id: Optional[int] = Body(None),
    description: Optional[str] = Body(None),
    currency: str = Body('OMR'),
    country_code: Optional[str] = Body(None)


@router.post("/ap-ledger/payment", status_code=201, tags=['finance'])
def controller_post_ap_payment_route(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
    supplier_id: int = Body(...),
    amount: float = Body(...),
    settlement_id: Optional[int] = Body(None),
    description: Optional[str] = Body(None),
    currency: str = Body('OMR'),
    country_code: Optional[str] = Body(None)


@router.get("/payouts/{country_code}")
def list_payouts(country_code: str = Path(..., description="ISO country code"), _: User = Depends(require_admin), db: Session = Depends(get_db), page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100)):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        q = db.query(Payout).filter(Payout.country_code == country_code.upper())
        total = q.count()
        rows = q.order_by(Payout.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
        return {"data": rows, "total": total, "page": page, "page_size": page_size}
    finally:
        clear_rls_context()




@router.post("/payouts/{country_code}", response_model=PayoutOut, status_code=201)
def create_payout(
    country_code: str = Path(..., description="ISO country code"),
    payload: PayoutCreate = None,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db),


@router.get("/pending")
def list_pending_payouts(
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),


@router.get("/payouts/{country_code}/pending")
def list_pending_payouts_by_country(
    country_code: str = Path(..., description="ISO country code"),
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),


@router.post("/payouts/{country_code}/{payout_id}/verify")
def verify_payout(
    country_code: str = Path(..., description="ISO country code"),
    payout_id: int = Path(...),
    payload: PayoutVerifyRequest = None,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db),


@router.post("/payouts/run-auto-sweep")
def run_auto_payout_sweep(
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin),


@router.put("/payouts/{country_code}/{payout_id}/process")
def process_payout(
    country_code: str = Path(..., description="ISO country code"),
    payout_id: int = Path(...),
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db),


@router.get("/background-job-status")
def get_background_job_status_endpoint(
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin),


@router.post("/background-job/start")
def start_background_job(
    current_admin: User = Depends(require_admin),


@router.post("/background-job/stop")
def stop_background_job(
    current_admin: User = Depends(require_admin),


@router.post("/background-job/trigger")
def trigger_background_job(
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin),


@router.post("/background-job/trigger/{kind}")
def trigger_background_job_kind(
    kind: str = Path(..., description="'supplier' or 'logistics'"),
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin),


@router.post("/purchase-orders", summary="Create a purchase order")
def create_po(payload: POInput, db: Session = Depends(get_db),
              _admin: dict = Depends(require_admin)):
    try:
        po = trading.create_purchase_order(
            db, supplier_id=payload.supplier_id,
            order_date=payload.order_date,
            expected_delivery_date=payload.expected_delivery_date,
            warehouse_id=payload.warehouse_id,
            currency=payload.currency,
            notes=payload.notes, terms=payload.terms,
            shipping_address=payload.shipping_address,
            country_code=payload.country_code,
            lines=[l.model_dump() for l in payload.lines],
            created_by=_admin.get("id"),
        )
    except ValueError as e:
        raise HTTPException(400, str(e))
    return po




@router.get("/purchase-orders", summary="List purchase orders")
def list_pos(status: str = None, supplier_id: int = None,
             country_code: str = None, limit: int = 50, offset: int = 0,
             db: Session = Depends(get_db), _admin: dict = Depends(require_admin)):
    return trading.list_purchase_orders(db, status=status, supplier_id=supplier_id,
                                         country_code=country_code, limit=limit, offset=offset)




@router.get("/purchase-orders/{po_id}", summary="Get a purchase order")
def get_po(po_id: int, db: Session = Depends(get_db),
           _admin: dict = Depends(require_admin)):
    po = db.query(trading.PurchaseOrder).filter(
        trading.PurchaseOrder.id == po_id
    ).first()
    if not po:
        raise HTTPException(404, "Purchase order not found")
    return po




@router.post("/purchase-orders/{po_id}/confirm", summary="Confirm a purchase order")
def confirm_po(po_id: int, db: Session = Depends(get_db),
               _admin: dict = Depends(require_admin)):
    try:
        po = trading.confirm_purchase_order(db, po_id)
    except ValueError as e:
        raise HTTPException(400, str(e))
    return po




@router.post("/purchase-orders/{po_id}/receive", summary="Receive goods against a PO")
def receive_po(po_id: int, payload: GRNCreate, db: Session = Depends(get_db),
               _admin: dict = Depends(require_admin)):
    try:
        grn = trading.receive_purchase_order(db, po_id, payload.model_dump())
    except ValueError as e:
        raise HTTPException(400, str(e))
    return grn




@router.get("/goods-receipts", summary="List goods receipt notes")
def list_grns(po_id: int = None, status: str = None,
              country_code: str = None, limit: int = 50, offset: int = 0,
              db: Session = Depends(get_db), _admin: dict = Depends(require_admin)):
    return trading.list_goods_receipts(db, po_id=po_id, status=status,
                                        country_code=country_code, limit=limit, offset=offset)




@router.get("/goods-receipts/{grn_id}", summary="Get a goods receipt note")
def get_grn(grn_id: int, db: Session = Depends(get_db),
            _admin: dict = Depends(require_admin)):
    grn = db.query(trading.GoodsReceiptNote).filter(
        trading.GoodsReceiptNote.id == grn_id
    ).first()
    if not grn:
        raise HTTPException(404, "Goods receipt note not found")
    return grn




@router.post("/three-way-match", summary="Run 3-way match (PO vs GRN vs Bill)")
def three_way_match(payload: ThreeWayMatchInput, db: Session = Depends(get_db),
                    _admin: dict = Depends(require_admin)):
    try:
        result = trading.three_way_match(
            db, po_id=payload.po_id, grn_id=payload.grn_id, bill_id=payload.bill_id,
        )
    except ValueError as e:
        raise HTTPException(400, str(e))
    return result




@router.post("/sales-orders", summary="Create a sales order")
def create_so(payload: SOInput, db: Session = Depends(get_db),
              _admin: dict = Depends(require_admin)):
    try:
        so = trading.create_sales_order(
            db, customer_id=payload.customer_id,
            order_date=payload.order_date,
            expected_delivery_date=payload.expected_delivery_date,
            warehouse_id=payload.warehouse_id,
            currency=payload.currency,
            customer_po_number=payload.customer_po_number,
            shipping_address=payload.shipping_address,
            billing_address=payload.billing_address,
            notes=payload.notes, terms=payload.terms,
            country_code=payload.country_code,
            lines=[l.model_dump() for l in payload.lines],
            created_by=_admin.get("id"),
        )
    except ValueError as e:
        raise HTTPException(400, str(e))
    return so




@router.get("/sales-orders", summary="List sales orders")
def list_sos(status: str = None, customer_id: int = None,
             country_code: str = None, limit: int = 50, offset: int = 0,
             db: Session = Depends(get_db), _admin: dict = Depends(require_admin)):
    return trading.list_sales_orders(db, status=status, customer_id=customer_id,
                                      country_code=country_code, limit=limit, offset=offset)




@router.get("/sales-orders/{so_id}", summary="Get a sales order")
def get_so(so_id: int, db: Session = Depends(get_db),
           _admin: dict = Depends(require_admin)):
    so = db.query(trading.SalesOrder).filter(
        trading.SalesOrder.id == so_id
    ).first()
    if not so:
        raise HTTPException(404, "Sales order not found")
    return so




@router.post("/sales-orders/{so_id}/confirm", summary="Confirm a sales order")
def confirm_so(so_id: int, db: Session = Depends(get_db),
               _admin: dict = Depends(require_admin)):
    try:
        so = trading.confirm_sales_order(db, so_id)
    except ValueError as e:
        raise HTTPException(400, str(e))
    return so




@router.post("/sales-orders/{so_id}/invoice", summary="Generate AR invoice from sales order")
def invoice_so(so_id: int, db: Session = Depends(get_db),
               _admin: dict = Depends(require_admin)):
    try:
        inv = trading.invoice_sales_order(db, so_id, created_by=_admin.get("id"))
    except ValueError as e:
        raise HTTPException(400, str(e))
    return inv




@router.post("/sales-orders/{so_id}/dispatch", summary="Dispatch goods & post COGS")
def dispatch_so(so_id: int, payload: DispatchInput = DispatchInput(),
                db: Session = Depends(get_db),
                _admin: dict = Depends(require_admin)):
    try:
        so = trading.dispatch_sales_order(db, so_id, payload.model_dump(),
                                           created_by=_admin.get("id"))
    except ValueError as e:
        raise HTTPException(400, str(e))
    return so




@router.post("/warehouses", summary="Create a warehouse")
def create_warehouse(payload: WarehouseInput, db: Session = Depends(get_db),
                     _admin: dict = Depends(require_admin)):
    try:
        wh = trading.create_warehouse(
            db, name=payload.name, code=payload.code,
            address=payload.address, city=payload.city,
            country_code=payload.country_code,
        )
    except ValueError as e:
        raise HTTPException(400, str(e))
    return wh




@router.get("/warehouses", summary="List warehouses")
def list_warehouses(country_code: str = None,
                    db: Session = Depends(get_db),
                    _admin: dict = Depends(require_admin)):
    return trading.list_warehouses(db, country_code=country_code)




@router.get("/stock", summary="Get stock levels")
def stock_levels(product_id: int = None, warehouse_id: int = None,
                 db: Session = Depends(get_db),
                 _admin: dict = Depends(require_admin)):
    return trading.get_stock_level(db, product_id=product_id, warehouse_id=warehouse_id)




@router.get("/stock/movements", summary="List stock movements")
def stock_movements(product_id: int = None, limit: int = 100, offset: int = 0,
                    db: Session = Depends(get_db),
                    _admin: dict = Depends(require_admin)):
    q = db.query(trading.StockMovement)
    if product_id:
        q = q.filter(trading.StockMovement.product_id == product_id)
    total = q.count()
    rows = q.order_by(trading.StockMovement.id.desc()).offset(offset).limit(limit).all()
    return {"total": total, "items": rows}




@router.post("/dunning/run", summary="Run dunning engine")
def run_dunning(as_of: date = None, db: Session = Depends(get_db),
                _admin: dict = Depends(require_admin)):
    return trading.run_dunning_engine(db, as_of=as_of)


@router.get("/")
def admin_treasury_root(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_treasury_access),


@router.get("/metrics")
def admin_treasury_metrics(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_treasury_access),


@router.get("/ledger")
def admin_treasury_ledger(
    start_date: date = Query(...),
    end_date: date = Query(...),
    limit: int = Query(DEFAULT_PAGE_SIZE),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_treasury_access),


@router.get("/reports/trial-balance")
def admin_trial_balance(
    as_of_date: Optional[str] = Query(None),
    country_code: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_treasury_access),


@router.get("/cash-position")
def admin_cash_position(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_treasury_access),


@router.get("/payouts/batches")
def admin_payout_batches(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_treasury_access),


@router.post("/payouts/batches/generate")
def admin_generate_payout_batch(
    country_code: str = FastAPIBody(...),
    cutoff_date: date = FastAPIBody(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_treasury_access),


@router.post("/payouts/batches/{batch_id}/approve")
def admin_approve_payout_batch(
    batch_id: int = Path(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_treasury_access),


@router.post("/payouts/batches/{batch_id}/dispatch")
def admin_dispatch_payout_batch(
    batch_id: int = Path(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_treasury_access),


@router.get("/reports/vat-liability")
def admin_vat_liability(
    country_code: Optional[str] = Query(None),
    period: str = Query("current"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_treasury_access),


@router.get("/cod-remittances")
def admin_cod_remittances(
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_treasury_access),


@router.get("/reconciliation/gateway-summary")
def admin_gateway_summary(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_treasury_access),


@router.post("/cash-position/snapshot")
def admin_snapshot_cash_position(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_treasury_access),


@router.get("/forecasts")
def admin_cash_forecasts(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_treasury_access),


@router.get("/consolidated/metrics")
def consolidated_treasury_metrics(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_treasury_access),


@router.get("/consolidated/ledger")
def consolidated_treasury_ledger(
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_treasury_access),


@router.get("/consolidated/reports/trial-balance")
def consolidated_trial_balance(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_treasury_access),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),


@router.get("/consolidated/cash-position")
def consolidated_cash_position(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_treasury_access),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),


@router.get("/consolidated/payouts/batches")
def consolidated_payout_batches(
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_treasury_access),


@router.get("/consolidated/reports/vat-liability")
def consolidated_vat_liability(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_treasury_access),


@router.get("/consolidated/cod-remittances")
def consolidated_cod_remittances(
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_treasury_access),


@router.get("/consolidated/reconciliation/gateway-summary")
def consolidated_gateway_summary(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_treasury_access),


@router.get("/consolidated/forecasts")
def consolidated_cash_forecasts(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_treasury_access),


@router.get("/consolidated/reconciliation/pipeline")
def consolidated_reconciliation_pipeline(
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_treasury_access),


@router.get("/{country_code}/metrics")
def country_treasury_metrics(
    country_code: str = Path(..., description="ISO country code"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_treasury_access),


@router.get("/{country_code}/ledger")
def country_treasury_ledger(
    country_code: str = Path(..., description="ISO country code"),
    start_date: date = Query(...),
    end_date: date = Query(...),
    limit: int = Query(50),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_treasury_access),


@router.get("/{country_code}/reports/trial-balance")
def country_trial_balance(
    country_code: str = Path(..., description="ISO country code"),
    as_of_date: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_treasury_access),


@router.get("/{country_code}/cash-position")
def country_cash_position(
    country_code: str = Path(..., description="ISO country code"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_treasury_access),


@router.get("/{country_code}/payouts/batches")
def country_payout_batches(
    country_code: str = Path(..., description="ISO country code"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_treasury_access),


@router.get("/{country_code}/reports/vat-liability")
def country_vat_liability(
    country_code: str = Path(..., description="ISO country code"),
    period: str = Query("current"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_treasury_access),


@router.get("/{country_code}/cod-remittances")
def country_cod_remittances(
    country_code: str = Path(..., description="ISO country code"),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_treasury_access),


@router.get("/{country_code}/reconciliation/gateway-summary")
def country_gateway_summary(
    country_code: str = Path(..., description="ISO country code"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_treasury_access),


@router.get("/{country_code}/reconciliation/pipeline")
def admin_reconciliation_pipeline(
    country_code: str = Path(..., description="ISO country code"),
    status: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_treasury_access),


@router.post("/{country_code}/reconciliation/record-cod-remittance")
def admin_record_cod_remittance(
    country_code: str = Path(..., description="ISO country code"),
    order_id: int = FastAPIBody(...),
    partner_id: int = FastAPIBody(...),
    amount: float = FastAPIBody(...),
    bank_reference: str = FastAPIBody(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_treasury_access),


@router.post("/{country_code}/reconciliation/settle-supplier")
def admin_settle_supplier(
    country_code: str = Path(..., description="ISO country code"),
    order_id: int = FastAPIBody(...),
    supplier_id: int = FastAPIBody(...),
    net_amount: float = FastAPIBody(...),
    gross_amount: Optional[float] = FastAPIBody(None),
    commission_amount: Optional[float] = FastAPIBody(None),
    currency: Optional[str] = FastAPIBody(None),
    payout_id: Optional[int] = FastAPIBody(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_treasury_access),


@router.post("/{country_code}/reconciliation/approve-settlement")
def admin_approve_settlement(
    country_code: str = Path(..., description="ISO country code"),
    settlement_id: int = FastAPIBody(..., embed=True),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_treasury_access),


@router.get("/reconciliation/gateway-exceptions")
def admin_gateway_exceptions(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_treasury_access),


@router.get("/{country_code}/reconciliation/gateway-exceptions")
def country_gateway_exceptions(
    country_code: str = Path(..., description="ISO country code"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_treasury_access),


@router.get("/payments/transactions")
def admin_payment_transactions(
    start_date: date = Query(...),
    end_date: date = Query(...),
    gateway: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_treasury_access),


@router.get("/{country_code}/payments/transactions")
def country_payment_transactions(
    country_code: str = Path(..., description="ISO country code"),
    start_date: date = Query(...),
    end_date: date = Query(...),
    gateway: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_treasury_access),


@router.get("/supplier-payouts")
def admin_supplier_payouts(
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_treasury_access),


@router.get("/{country_code}/supplier-payouts")
def country_supplier_payouts(
    country_code: str = Path(..., description="ISO country code"),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_treasury_access),


@router.get("/logistics-payouts")
def admin_logistics_payouts(
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_treasury_access),


@router.get("/{country_code}/logistics-payouts")
def country_logistics_payouts(
    country_code: str = Path(..., description="ISO country code"),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_treasury_access),


@router.get("/reports/supplier-earnings")
def admin_supplier_earnings(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_treasury_access),


@router.get("/{country_code}/reports/supplier-earnings")
def country_supplier_earnings(
    country_code: str = Path(..., description="ISO country code"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_treasury_access),


@router.get("/liabilities/exposure")
def admin_liabilities_exposure(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_treasury_access),


@router.get("/{country_code}/liabilities/exposure")
def country_liabilities_exposure(
    country_code: str = Path(..., description="ISO country code"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_treasury_access),


@router.post("/ledger/manual-adjustment")
def admin_manual_adjustment(
    debit_account: str = FastAPIBody(...),
    credit_account: str = FastAPIBody(...),
    amount: float = FastAPIBody(...),
    reason: str = FastAPIBody(...),
    created_by: int = FastAPIBody(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_treasury_access),


@router.post("/{country_code}/ledger/manual-adjustment")
def country_manual_adjustment(
    country_code: str = Path(..., description="ISO country code"),
    debit_account: str = FastAPIBody(...),
    credit_account: str = FastAPIBody(...),
    amount: float = FastAPIBody(...),
    reason: str = FastAPIBody(...),
    created_by: int = FastAPIBody(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_treasury_access),


@router.get("/ledger/pending")
def admin_pending_entries(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_treasury_access),


@router.get("/{country_code}/ledger/pending")
def country_pending_entries(
    country_code: str = Path(..., description="ISO country code"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_treasury_access),


@router.post("/ledger/pending/{pending_id}/approve")
def admin_approve_pending(
    pending_id: int = Path(...),
    approver_id: int = FastAPIBody(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_treasury_access),


@router.post("/{country_code}/ledger/pending/{pending_id}/approve")
def country_approve_pending(
    country_code: str = Path(..., description="ISO country code"),
    pending_id: int = Path(...),
    approver_id: int = FastAPIBody(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_treasury_access),


@router.post("/ledger/pending/{pending_id}/reject")
def admin_reject_pending(
    pending_id: int = Path(...),
    rejected_by: int = FastAPIBody(...),
    reason: str = FastAPIBody(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_treasury_access),


@router.post("/{country_code}/ledger/pending/{pending_id}/reject")
def country_reject_pending(
    country_code: str = Path(..., description="ISO country code"),
    pending_id: int = Path(...),
    rejected_by: int = FastAPIBody(...),
    reason: str = FastAPIBody(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_treasury_access),


@router.post("/detect-orphans")
def admin_detect_orphans(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_treasury_access),


@router.post("/{country_code}/detect-orphans")
def country_detect_orphans(
    country_code: str = Path(..., description="ISO country code"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_treasury_access),


@router.get("/payroll/equity")
def payroll_equity(db: Session = Depends(get_db)):
    """Pay-equity snapshot by department (avg male vs female salary)."""
    rows = (
        db.query(
            Employee.department,
            Employee.gender,
            func.avg(Employee.salary),
        ).filter(Employee.salary.isnot(None), Employee.department.isnot(None))
        .group_by(Employee.department, Employee.gender)
        .all()
    )
    by_dept = {}
    for dept, gender, avg_sal in rows:
        by_dept.setdefault(dept, {})[gender or "unknown"] = float(avg_sal or 0)
    metrics = []
    for dept, vals in by_dept.items():
        avg_male = vals.get("male", 0.0)
        avg_female = vals.get("female", 0.0)
        if avg_male > 0 and avg_female > 0:
            disparity = (avg_male - avg_female) / avg_male * 100
        else:
            disparity = 0.0
        metrics.append({
            "category": dept,
            "avg_male": round(avg_male, 2),
            "avg_female": round(avg_female, 2),
            "disparity_percent": round(disparity, 2),
            "flagged": disparity > 10,
        })
    return metrics




@router.get("/{country_code}/payroll")
def country_payroll(country_code: str, db: Session = Depends(get_db)):
    """Aggregate payroll totals for a country (employee headcount + gross/tax/net)."""
    rows = (
        db.query(func.count(Employee.id), func.coalesce(func.sum(Employee.salary), 0))
        .filter(Employee.country_code == country_code.upper())
        .all()
    )
    employee_count = int(rows[0][0] or 0)
    total_gross = float(rows[0][1] or 0)
    total_tax = round(total_gross * 0.05, 2)
    total_net = round(total_gross - total_tax, 2)
    return {
        "employee_count": employee_count,
        "total_gross": round(total_gross, 2),
        "total_tax": total_tax,
        "total_net": total_net,
    }





@router.post("/treasury/badge-billing/{billing_id}/payments", status_code=201, tags=['treasury'])
def record_badge_billing_payment_route(
    billing_id: int,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    payment_method: str = Body(..., embed=True),
    transaction_ref: Optional[str] = Body(None, embed=True),
    notes: Optional[str] = Body(None, embed=True)


@router.put("/treasury/bank-settings", status_code=200, tags=['treasury'])
def upsert_bank_settings_route(
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    data: dict = Body(...)


@router.post("/treasury/vat-remittances", status_code=201, tags=['treasury'])
def record_vat_remittance_route(
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    data: dict = Body(...)


@router.post("/treasury/bank-transactions", status_code=201, tags=['treasury'])
def create_bank_transaction_route(
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    data: dict = Body(...)


@router.post("/treasury/bank-transactions/import", status_code=201, tags=['treasury'])
def import_bank_transactions_route(
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    items: list[dict] = Body(..., embed=True),
    auto_reconcile: bool = Body(False, embed=True)


@router.post("/treasury/bank-transactions/{txn_id}/reconcile", status_code=201, tags=['treasury'])
def reconcile_transaction_route(
    txn_id: int,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)


@router.post("/treasury/bank-transactions/{txn_id}/flag", status_code=201, tags=['treasury'])
def flag_transaction_route(
    txn_id: int,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    reason: str = Body(...)


@router.post("/treasury/bank-transactions/{txn_id}/resolve", status_code=201, tags=['treasury'])
def resolve_transaction_exception_route(
    txn_id: int,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    data: dict = Body(...)


@router.post("/treasury/bank-transactions/auto-reconcile", status_code=201, tags=['treasury'])
def auto_reconcile_transactions_route(
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    limit: int = Body(100, embed=True),
    source: Optional[str] = Body(None, embed=True),
    category: Optional[str] = Body(None, embed=True)


@router.post("/treasury/payouts/supplier", status_code=201, tags=['treasury'])
def trigger_supplier_payouts_route(
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    settlement_ids: Optional[list[int]] = Body(None)


@router.post("/treasury/payouts/logistics", status_code=201, tags=['treasury'])
def trigger_logistics_payouts_route(
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    settlement_ids: Optional[list[int]] = Body(None)


@router.post("/treasury/transfers/dispatch", status_code=201, tags=['treasury'])
def dispatch_transfer_batch_route(
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    kind: str = Body(..., embed=True),
    provider: Optional[str] = Body(None, embed=True),
    dry_run: bool = Body(True, embed=True)


@router.post("/treasury/transfers/dispatch/queue", status_code=201, tags=['treasury'])
def queue_dispatch_transfer_batch_route(
    current_user: dict = Depends(require_admin),
    kind: str = Body(..., embed=True),
    provider: Optional[str] = Body(None, embed=True),
    dry_run: bool = Body(False, embed=True)


@router.post("/treasury/cod/{settlement_id}/remittance", status_code=201, tags=['treasury'])
def record_cod_remittance_route(
    settlement_id: int,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    amount: float = Body(...)


@router.post("/treasury/cod/receipts/{receipt_id}/verify", status_code=201, tags=['treasury'])
def verify_cod_remittance_receipt_route(
    receipt_id: int,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    note: Optional[str] = Body(None)


@router.post("/treasury/cod/receipts/{receipt_id}/reject", status_code=201, tags=['treasury'])
def reject_cod_remittance_receipt_route(
    receipt_id: int,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    note: str = Body(...)


@router.get("/metrics")
def treasury_metrics(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),


@router.get("/cash-position")
def cash_position(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),


@router.get("/vat-liability")
def vat_liability(
    country_code: str = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),


@router.get("/supplier-payables")
def supplier_payables(
    country_code: str = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),


@router.get("/{country_code}/accounts", response_model=list[CashAccountOut])
def list_accounts(country_code: str = Path(..., description="ISO country code"), _: User = Depends(require_admin), db: Session = Depends(get_db)):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return db.query(CashAccount).filter(CashAccount.is_active == True, CashAccount.country_code == country_code.upper()).all()
    finally:
        clear_rls_context()




@router.post("/{country_code}/accounts", response_model=CashAccountOut, status_code=201)
def create_account(country_code: str = Path(..., description="ISO country code"), payload: CashAccountCreate = None, _: User = Depends(require_admin), db: Session = Depends(get_db)):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        a = CashAccount(**payload.model_dump(), country_code=country_code.upper())
        db.add(a); db.commit(); db.refresh(a)
        return a
    finally:
        clear_rls_context()




@router.post("/{country_code}/transactions", response_model=CashTransactionOut, status_code=201)
def create_transaction(country_code: str = Path(..., description="ISO country code"), payload: CashTransactionCreate = None, current_user: User = Depends(require_admin), db: Session = Depends(get_db)):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        account = db.query(CashAccount).filter(CashAccount.id == payload.account_id, CashAccount.country_code == country_code.upper()).first()
        if not account: raise HTTPException(404, "Account not found")
        if payload.transaction_type == "debit":
            account.balance -= payload.amount
        else:
            account.balance += payload.amount
        tx = CashTransaction(**payload.model_dump(), balance_after=account.balance, performed_by=current_user.id, country_code=country_code.upper())
        db.add(tx); db.commit(); db.refresh(tx)
        return tx
    finally:
        clear_rls_context()




@router.get("/pending")
def get_pending_payouts(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db),


@router.post("/payouts/{payout_id}/approve")
def approve_payout(
    payout_id: int,
    payload: ActionRequest | None = None,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db),


@router.post("/payouts/{payout_id}/reject")
def reject_payout(
    payout_id: int,
    payload: ActionRequest | None = None,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db),


@router.post("/batches/{batch_id}/approve")
def approve_batch(
    batch_id: int,
    payload: ActionRequest | None = None,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db),


@router.post("/batches/{batch_id}/reject")
def reject_batch(
    batch_id: int,
    payload: ActionRequest | None = None,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db),


@router.post("/batches/{batch_id}/dispatch")
def dispatch_batch(
    batch_id: int,
    payload: ActionRequest | None = None,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db),


@router.post("/payouts/{payout_id}/approve", status_code=201, tags=['treasury-payouts'])
def approve_payout_route(
    payout_id: int,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    payload: Any = Body(...)


@router.post("/payouts/{payout_id}/reject", status_code=201, tags=['treasury-payouts'])
def reject_payout_route(
    payout_id: int,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    payload: Any = Body(...)


@router.post("/batches/{batch_id}/approve", status_code=201, tags=['treasury-payouts'])
def approve_batch_route(
    batch_id: int,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    payload: Any = Body(...)


@router.post("/batches/{batch_id}/reject", status_code=201, tags=['treasury-payouts'])
def reject_batch_route(
    batch_id: int,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    payload: Any = Body(...)


@router.post("/batches/{batch_id}/dispatch", status_code=201, tags=['treasury-payouts'])
def dispatch_batch_route(
    batch_id: int,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    payload: Any = Body(...)


@router.get("/")
def admin_treasury_root(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_treasury_access),


@router.get("/metrics")
def admin_treasury_metrics(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_treasury_access),


@router.get("/ledger")
def admin_treasury_ledger(
    start_date: date = Query(...),
    end_date: date = Query(...),
    limit: int = Query(DEFAULT_PAGE_SIZE),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_treasury_access),


@router.get("/reports/trial-balance")
def admin_trial_balance(
    as_of_date: Optional[str] = Query(None),
    country_code: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_treasury_access),


@router.get("/cash-position")
def admin_cash_position(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_treasury_access),


@router.get("/payouts/batches")
def admin_payout_batches(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_treasury_access),


@router.post("/payouts/batches/generate")
def admin_generate_payout_batch(
    country_code: str = FastAPIBody(...),
    cutoff_date: date = FastAPIBody(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_treasury_access),


@router.post("/payouts/batches/{batch_id}/approve")
def admin_approve_payout_batch(
    batch_id: int = Path(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_treasury_access),


@router.post("/payouts/batches/{batch_id}/dispatch")
def admin_dispatch_payout_batch(
    batch_id: int = Path(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_treasury_access),


@router.get("/reports/vat-liability")
def admin_vat_liability(
    country_code: Optional[str] = Query(None),
    period: str = Query("current"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_treasury_access),


@router.get("/cod-remittances")
def admin_cod_remittances(
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_treasury_access),


@router.get("/reconciliation/gateway-summary")
def admin_gateway_summary(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_treasury_access),


@router.post("/cash-position/snapshot")
def admin_snapshot_cash_position(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_treasury_access),


@router.get("/forecasts")
def admin_cash_forecasts(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_treasury_access),


@router.get("/consolidated/metrics")
def consolidated_treasury_metrics(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_treasury_access),


@router.get("/consolidated/ledger")
def consolidated_treasury_ledger(
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_treasury_access),


@router.get("/consolidated/reports/trial-balance")
def consolidated_trial_balance(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_treasury_access),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),


@router.get("/consolidated/cash-position")
def consolidated_cash_position(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_treasury_access),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),


@router.get("/consolidated/payouts/batches")
def consolidated_payout_batches(
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_treasury_access),


@router.get("/consolidated/reports/vat-liability")
def consolidated_vat_liability(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_treasury_access),


@router.get("/consolidated/cod-remittances")
def consolidated_cod_remittances(
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_treasury_access),


@router.get("/consolidated/reconciliation/gateway-summary")
def consolidated_gateway_summary(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_treasury_access),


@router.get("/consolidated/forecasts")
def consolidated_cash_forecasts(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_treasury_access),


@router.get("/consolidated/reconciliation/pipeline")
def consolidated_reconciliation_pipeline(
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_treasury_access),


@router.get("/{country_code}/metrics")
def country_treasury_metrics(
    country_code: str = Path(..., description="ISO country code"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_treasury_access),


@router.get("/{country_code}/ledger")
def country_treasury_ledger(
    country_code: str = Path(..., description="ISO country code"),
    start_date: date = Query(...),
    end_date: date = Query(...),
    limit: int = Query(50),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_treasury_access),


@router.get("/{country_code}/reports/trial-balance")
def country_trial_balance(
    country_code: str = Path(..., description="ISO country code"),
    as_of_date: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_treasury_access),


@router.get("/{country_code}/cash-position")
def country_cash_position(
    country_code: str = Path(..., description="ISO country code"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_treasury_access),


@router.get("/{country_code}/payouts/batches")
def country_payout_batches(
    country_code: str = Path(..., description="ISO country code"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_treasury_access),


@router.get("/{country_code}/reports/vat-liability")
def country_vat_liability(
    country_code: str = Path(..., description="ISO country code"),
    period: str = Query("current"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_treasury_access),


@router.get("/{country_code}/cod-remittances")
def country_cod_remittances(
    country_code: str = Path(..., description="ISO country code"),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_treasury_access),


@router.get("/{country_code}/reconciliation/gateway-summary")
def country_gateway_summary(
    country_code: str = Path(..., description="ISO country code"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_treasury_access),


@router.get("/{country_code}/reconciliation/pipeline")
def admin_reconciliation_pipeline(
    country_code: str = Path(..., description="ISO country code"),
    status: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_treasury_access),


@router.post("/{country_code}/reconciliation/record-cod-remittance")
def admin_record_cod_remittance(
    country_code: str = Path(..., description="ISO country code"),
    order_id: int = FastAPIBody(...),
    partner_id: int = FastAPIBody(...),
    amount: float = FastAPIBody(...),
    bank_reference: str = FastAPIBody(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_treasury_access),


@router.post("/{country_code}/reconciliation/settle-supplier")
def admin_settle_supplier(
    country_code: str = Path(..., description="ISO country code"),
    order_id: int = FastAPIBody(...),
    supplier_id: int = FastAPIBody(...),
    net_amount: float = FastAPIBody(...),
    gross_amount: Optional[float] = FastAPIBody(None),
    commission_amount: Optional[float] = FastAPIBody(None),
    currency: Optional[str] = FastAPIBody(None),
    payout_id: Optional[int] = FastAPIBody(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_treasury_access),


@router.post("/{country_code}/reconciliation/approve-settlement")
def admin_approve_settlement(
    country_code: str = Path(..., description="ISO country code"),
    settlement_id: int = FastAPIBody(..., embed=True),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_treasury_access),


@router.get("/reconciliation/gateway-exceptions")
def admin_gateway_exceptions(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_treasury_access),


@router.get("/{country_code}/reconciliation/gateway-exceptions")
def country_gateway_exceptions(
    country_code: str = Path(..., description="ISO country code"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_treasury_access),


@router.get("/payments/transactions")
def admin_payment_transactions(
    start_date: date = Query(...),
    end_date: date = Query(...),
    gateway: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_treasury_access),


@router.get("/{country_code}/payments/transactions")
def country_payment_transactions(
    country_code: str = Path(..., description="ISO country code"),
    start_date: date = Query(...),
    end_date: date = Query(...),
    gateway: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_treasury_access),


@router.get("/supplier-payouts")
def admin_supplier_payouts(
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_treasury_access),


@router.get("/{country_code}/supplier-payouts")
def country_supplier_payouts(
    country_code: str = Path(..., description="ISO country code"),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_treasury_access),


@router.get("/logistics-payouts")
def admin_logistics_payouts(
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_treasury_access),


@router.get("/{country_code}/logistics-payouts")
def country_logistics_payouts(
    country_code: str = Path(..., description="ISO country code"),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_treasury_access),


@router.get("/reports/supplier-earnings")
def admin_supplier_earnings(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_treasury_access),


@router.get("/{country_code}/reports/supplier-earnings")
def country_supplier_earnings(
    country_code: str = Path(..., description="ISO country code"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_treasury_access),


@router.get("/liabilities/exposure")
def admin_liabilities_exposure(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_treasury_access),


@router.get("/{country_code}/liabilities/exposure")
def country_liabilities_exposure(
    country_code: str = Path(..., description="ISO country code"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_treasury_access),


@router.post("/ledger/manual-adjustment")
def admin_manual_adjustment(
    debit_account: str = FastAPIBody(...),
    credit_account: str = FastAPIBody(...),
    amount: float = FastAPIBody(...),
    reason: str = FastAPIBody(...),
    created_by: int = FastAPIBody(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_treasury_access),


@router.post("/{country_code}/ledger/manual-adjustment")
def country_manual_adjustment(
    country_code: str = Path(..., description="ISO country code"),
    debit_account: str = FastAPIBody(...),
    credit_account: str = FastAPIBody(...),
    amount: float = FastAPIBody(...),
    reason: str = FastAPIBody(...),
    created_by: int = FastAPIBody(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_treasury_access),


@router.get("/ledger/pending")
def admin_pending_entries(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_treasury_access),


@router.get("/{country_code}/ledger/pending")
def country_pending_entries(
    country_code: str = Path(..., description="ISO country code"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_treasury_access),


@router.post("/ledger/pending/{pending_id}/approve")
def admin_approve_pending(
    pending_id: int = Path(...),
    approver_id: int = FastAPIBody(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_treasury_access),


@router.post("/{country_code}/ledger/pending/{pending_id}/approve")
def country_approve_pending(
    country_code: str = Path(..., description="ISO country code"),
    pending_id: int = Path(...),
    approver_id: int = FastAPIBody(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_treasury_access),


@router.post("/ledger/pending/{pending_id}/reject")
def admin_reject_pending(
    pending_id: int = Path(...),
    rejected_by: int = FastAPIBody(...),
    reason: str = FastAPIBody(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_treasury_access),


@router.post("/{country_code}/ledger/pending/{pending_id}/reject")
def country_reject_pending(
    country_code: str = Path(..., description="ISO country code"),
    pending_id: int = Path(...),
    rejected_by: int = FastAPIBody(...),
    reason: str = FastAPIBody(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_treasury_access),


@router.post("/detect-orphans")
def admin_detect_orphans(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_treasury_access),


@router.post("/{country_code}/detect-orphans")
def country_detect_orphans(
    country_code: str = Path(..., description="ISO country code"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_treasury_access),


@router.get("/payroll/equity")
def payroll_equity(db: Session = Depends(get_db)):
    """Pay-equity snapshot by department (avg male vs female salary)."""
    rows = (
        db.query(
            Employee.department,
            Employee.gender,
            func.avg(Employee.salary),
        ).filter(Employee.salary.isnot(None), Employee.department.isnot(None))
        .group_by(Employee.department, Employee.gender)
        .all()
    )
    by_dept = {}
    for dept, gender, avg_sal in rows:
        by_dept.setdefault(dept, {})[gender or "unknown"] = float(avg_sal or 0)
    metrics = []
    for dept, vals in by_dept.items():
        avg_male = vals.get("male", 0.0)
        avg_female = vals.get("female", 0.0)
        if avg_male > 0 and avg_female > 0:
            disparity = (avg_male - avg_female) / avg_male * 100
        else:
            disparity = 0.0
        metrics.append({
            "category": dept,
            "avg_male": round(avg_male, 2),
            "avg_female": round(avg_female, 2),
            "disparity_percent": round(disparity, 2),
            "flagged": disparity > 10,
        })
    return metrics




@router.get("/{country_code}/payroll")
def country_payroll(country_code: str, db: Session = Depends(get_db)):
    """Aggregate payroll totals for a country (employee headcount + gross/tax/net)."""
    rows = (
        db.query(func.count(Employee.id), func.coalesce(func.sum(Employee.salary), 0))
        .filter(Employee.country_code == country_code.upper())
        .all()
    )
    employee_count = int(rows[0][0] or 0)
    total_gross = float(rows[0][1] or 0)
    total_tax = round(total_gross * 0.05, 2)
    total_net = round(total_gross - total_tax, 2)
    return {
        "employee_count": employee_count,
        "total_gross": round(total_gross, 2),
        "total_tax": total_tax,
        "total_net": total_net,
    }





@router.get("/payouts/{country_code}")
def list_payouts(country_code: str = Path(..., description="ISO country code"), _: User = Depends(require_admin), db: Session = Depends(get_db), page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100)):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        q = db.query(Payout).filter(Payout.country_code == country_code.upper())
        total = q.count()
        rows = q.order_by(Payout.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
        return {"data": rows, "total": total, "page": page, "page_size": page_size}
    finally:
        clear_rls_context()




@router.post("/payouts/{country_code}", response_model=PayoutOut, status_code=201)
def create_payout(
    country_code: str = Path(..., description="ISO country code"),
    payload: PayoutCreate = None,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db),


@router.get("/pending")
def list_pending_payouts(
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),


@router.get("/payouts/{country_code}/pending")
def list_pending_payouts_by_country(
    country_code: str = Path(..., description="ISO country code"),
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),


@router.post("/payouts/{country_code}/{payout_id}/verify")
def verify_payout(
    country_code: str = Path(..., description="ISO country code"),
    payout_id: int = Path(...),
    payload: PayoutVerifyRequest = None,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db),


@router.post("/payouts/run-auto-sweep")
def run_auto_payout_sweep(
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin),


@router.put("/payouts/{country_code}/{payout_id}/process")
def process_payout(
    country_code: str = Path(..., description="ISO country code"),
    payout_id: int = Path(...),
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db),


@router.get("/background-job-status")
def get_background_job_status_endpoint(
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin),


@router.post("/background-job/start")
def start_background_job(
    current_admin: User = Depends(require_admin),


@router.post("/background-job/stop")
def stop_background_job(
    current_admin: User = Depends(require_admin),


@router.post("/background-job/trigger")
def trigger_background_job(
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin),


@router.post("/background-job/trigger/{kind}")
def trigger_background_job_kind(
    kind: str = Path(..., description="'supplier' or 'logistics'"),
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin),


@router.post("/run", summary="Run full automation suite")
def run_automation(country_code: str = None, period_year: int = None,
                    period_month: int = None, db: Session = Depends(get_db),
                    _admin: dict = Depends(require_admin)):
    return scheduler.run_full_automation(db, country_code=country_code,
                                          period_year=period_year,
                                          period_month=period_month)




@router.post("/cash-snapshot", summary="Take cash position snapshot")
def cash_snapshot(country_code: str = None, db: Session = Depends(get_db),
                   _admin: dict = Depends(require_admin)):
    return scheduler.take_cash_snapshot(db, country_code=country_code)




@router.post("/vat", summary="Compute VAT remittance for a period")
def compute_vat(period_year: int, period_month: int, country_code: str = None,
                db: Session = Depends(get_db), _admin: dict = Depends(require_admin)):
    return scheduler.compute_vat_remittance(db, period_year, period_month, country_code)




@router.post("/reports", summary="Generate period financial reports")
def generate_reports(period_year: int, period_month: int, country_code: str = None,
                      db: Session = Depends(get_db), _admin: dict = Depends(require_admin)):
    return scheduler.generate_period_reports(db, period_year, period_month, country_code)




@router.post("/statements/distributors", summary="Generate distributor statements")
def distributor_statements(period_year: int, period_month: int, country_code: str = None,
                            db: Session = Depends(get_db),
                            _admin: dict = Depends(require_admin)):
    return scheduler.generate_distributor_statements(db, period_year, period_month, country_code)




@router.post("/statements/suppliers", summary="Generate supplier statements")
def supplier_statements(period_year: int, period_month: int, country_code: str = None,
                         db: Session = Depends(get_db),
                         _admin: dict = Depends(require_admin)):
    return scheduler.generate_supplier_statements(db, period_year, period_month, country_code)




@router.post("/alerts", summary="Run alert engine")
def run_alerts(country_code: str = None, db: Session = Depends(get_db),
               _admin: dict = Depends(require_admin)):
    return scheduler.run_alert_engine(db, country_code=country_code)




@router.post("/gateway-reconciliation/run", summary="Run 3-way gateway reconciliation")
def run_gateway_reconciliation(country_code: str = None, db: Session = Depends(get_db),
                                _admin: dict = Depends(require_admin)):
    """Run 3-way gateway reconciliation (order vs gateway vs bank)."""
    return run_gateway_3way_reconciliation(db, country_code)




@router.post("/gateway-reconciliation/match/{settlement_id}", summary="Match a gateway settlement")
def match_settlement(settlement_id: int, bank_statement_line_id: int = None,
                      country_code: str = None, db: Session = Depends(get_db),
                      _admin: dict = Depends(require_admin)):
    """Manually match a specific gateway settlement."""
    return match_gateway_settlement(db, settlement_id, bank_statement_line_id, country_code)




@router.post("/cod-reconcile/{order_id}", summary="Reconcile COD deposit for an order")
def cod_reconcile(order_id: int, deposited_amount: float, logistics_partner_id: int = None,
                   bank_transaction_id: int = None, country_code: str = None,
                   db: Session = Depends(get_db), _admin: dict = Depends(require_admin)):
    """Reconcile COD cash deposit from logistics partner."""
    from decimal import Decimal
    return reconcile_cod_deposit(
        db, order_id, Decimal(str(deposited_amount)),
        logistics_partner_id, bank_transaction_id, country_code
    )




@router.post("/payout-batches/generate", summary="Generate supplier payout batches")
def generate_payout_batches(country_code: str = None, holding_days: int = 7,
                             db: Session = Depends(get_db),
                             _admin: dict = Depends(require_admin)):
    """Nightly cron: Generate payout batches from eligible settlements."""
    return generate_supplier_payout_batches(db, country_code, holding_days)




@router.post("/payout-batches/logistics", summary="Generate logistics payout batches")
def generate_logistics_batches(country_code: str = None, holding_days: int = 7,
                                db: Session = Depends(get_db),
                                _admin: dict = Depends(require_admin)):
    """Generate payout batches for logistics partners."""
    return generate_logistics_payout_batches(db, country_code, holding_days)




@router.get("/payout-batches/pending/{supplier_id}", summary="Get pending batches for supplier")
def pending_supplier_batches(supplier_id: int, db: Session = Depends(get_db)):
    """Get payout batches pending supplier approval."""
    return get_pending_batches_for_supplier(db, supplier_id)




@router.post("/payout-batches/{batch_id}/approve", summary="Supplier approves payout batch")
def approve_batch(batch_id: int, supplier_id: int, approved: bool = True,
                   notes: str = None, db: Session = Depends(get_db)):
    """Supplier self-approval for payout batch."""
    return supplier_approve_batch(db, batch_id, supplier_id, approved, notes)




@router.post("/refunds/{refund_id}/post", summary="Auto-post refund journal entries")
def post_refund(refund_id: int, approved_by: int = None, country_code: str = None,
                db: Session = Depends(get_db), _admin: dict = Depends(require_admin)):
    """Auto-post journal entries when a refund is approved."""
    return post_refund_automatically(db, refund_id, approved_by, country_code)




@router.get("/credit-check/{customer_id}", summary="Check customer credit status")
def credit_check(customer_id: int, order_amount: float = None,
                  db: Session = Depends(get_db)):
    """Pre-dispatch credit check for a customer."""
    from decimal import Decimal
    return check_customer_credit(
        db, customer_id,
        Decimal(str(order_amount)) if order_amount else None
    )




@router.post("/credit-control/enforce", summary="Enforce auto credit holds")
def enforce_credit_holds(country_code: str = None, db: Session = Depends(get_db),
                          _admin: dict = Depends(require_admin)):
    """Daily cron: Auto-place/release credit holds."""
    return enforce_auto_credit_holds(db, country_code)




@router.get("/credit-summary/{customer_id}", summary="Get customer credit summary")
def credit_summary(customer_id: int, db: Session = Depends(get_db)):
    """Get comprehensive credit summary for a customer."""
    return get_customer_credit_summary(db, customer_id)




@router.post("/ai/bank-reconciliation", summary="Run AI fuzzy bank reconciliation")
def ai_bank_recon(country_code: str = None, db: Session = Depends(get_db),
                    _admin: dict = Depends(require_admin)):
    """AI-powered fuzzy bank reconciliation using semantic matching."""
    return run_ai_bank_reconciliation(db, country_code)




@router.post("/email/inbox", summary="Process email inbox for invoices")
def process_email_inbox_endpoint(country_code: str = None,
                                  db: Session = Depends(get_db),
                                  _admin: dict = Depends(require_admin)):
    """Batch process email inbox for invoice emails."""
    return process_email_inbox(db, country_code)




@router.post("/email/process", summary="Process an invoice email")
def process_email_endpoint(email_text: str = Body(..., embed=True), sender: str = None,
                             country_code: str = None,
                             db: Session = Depends(get_db),
                             _admin: dict = Depends(require_admin)):
    """Process a single invoice email through OCR-to-ledger pipeline."""
    return process_email_invoice(db, email_text, sender, country_code)




@router.post("/mobile/scan", summary="Process mobile receipt scan")
def mobile_scan_endpoint(country_code: str = None,
                           db: Session = Depends(get_db),
                           _admin: dict = Depends(require_admin)):
    """Mobile upload endpoint - process receipt image through OCR to GL.
    Note: For binary upload, send as multipart/form-data with 'image' field.
    This endpoint returns the processing pipeline definition."""
    return {
        "status": "ready",
        "endpoint": "/automation/mobile/scan/upload",
        "method": "POST multipart/form-data",
        "fields": ["image (binary)", "vendor_name (optional)", "country_code (optional)"],
    }




@router.post("/ai/categorize/{expense_id}", summary="AI categorize a scanned expense")
def categorize_expense(expense_id: int, db: Session = Depends(get_db),
                         _admin: dict = Depends(require_admin)):
    """Use AI to categorize a scanned expense and auto-post to GL."""
    return categorize_expense_ai(db, expense_id)




@router.post("/ai/categorize/batch", summary="Batch categorize all uncategorized expenses")
def batch_categorize_endpoint(country_code: str = None,
                                db: Session = Depends(get_db),
                                _admin: dict = Depends(require_admin)):
    """Batch categorize all uncategorized scanned expenses."""
    return batch_categorize_all(db, country_code)


@router.post("/seed", summary="Seed chart of accounts (idempotent)")
def seed_chart_of_accounts(
    db: Session = Depends(get_db),
    _admin: dict = Depends(require_admin),


@router.get("/accounts", summary="List all accounts")
def list_accounts(
    country_code: str = Query(None, max_length=3),
    db: Session = Depends(get_db),
    _user=Depends(require_admin),


@router.get("/accounts/{code}", summary="Get account by code")
def get_account(
    code: str,
    country_code: str = Query(None, max_length=3),
    db: Session = Depends(get_db),
    _user=Depends(require_admin),


@router.post("/journal-entries", summary="Create a journal entry")
def create_journal_entry(
    body: accounting_controller.JournalEntryBody,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),


@router.get("/journal-entries", summary="List journal entries")
def list_journal_entries(
    reference_type: Optional[str] = Query(None, max_length=40),
    reference_id: Optional[int] = Query(None),
    country_code: Optional[str] = Query(None, max_length=3),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
    _user=Depends(require_admin),


@router.get("/journal-entries/{entry_id}", summary="Get journal entry by ID")
def get_journal_entry(
    entry_id: int,
    country_code: str = Query(None, max_length=3),
    db: Session = Depends(get_db),
    _user=Depends(require_admin),


@router.get("/balances/{account_code}", summary="Get account balance")
def get_balance(
    account_code: str,
    currency: str = Query("OMR", max_length=10),
    country_code: str = Query(None, max_length=3),
    db: Session = Depends(get_db),
    _user=Depends(require_admin),


@router.get("/trial-balance", summary="Get trial balance")
def trial_balance(
    as_of_date: Optional[date] = Query(None),
    currency: str = Query("OMR", max_length=10),
    country_code: Optional[str] = Query(None, max_length=3),
    db: Session = Depends(get_db),
    _user=Depends(require_admin),


@router.post("/reports/income-statement", summary="Generate Income Statement (P&L)")
def income_statement(
    body: ReportPeriod,
    db: Session = Depends(get_db),
    _admin: dict = Depends(require_admin),


@router.post("/reports/balance-sheet", summary="Generate Balance Sheet")
def balance_sheet(
    as_of_date: Optional[datetime] = Query(None, description="Defaults to now"),
    currency: str = Query("OMR", max_length=10),
    persist: bool = Query(False),
    country_code: Optional[str] = Query(None, max_length=3),
    db: Session = Depends(get_db),
    _admin: dict = Depends(require_admin),


@router.post("/reports/cash-flow", summary="Generate Cash Flow Statement")
def cash_flow(
    body: ReportPeriod,
    db: Session = Depends(get_db),
    _admin: dict = Depends(require_admin),


@router.get("/reports", summary="List saved financial reports")
def list_reports(
    report_type: Optional[str] = Query(None, description="Filter by report type"),
    country_code: Optional[str] = Query(None, max_length=3),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    _user=Depends(require_admin),


@router.post("/periods/get-or-create", summary="Get or create a fiscal period")
def get_or_create(
    country_code: str = Query(..., max_length=3),
    year: int = Query(..., ge=2020, le=2100),
    month: int = Query(..., ge=1, le=12),
    db: Session = Depends(get_db),
    _admin: dict = Depends(require_admin),


@router.get("/periods/current", summary="Get current fiscal period")
def current_period(
    country_code: str = Query(..., max_length=3),
    db: Session = Depends(get_db),
    _user=Depends(require_admin),


@router.post("/periods/close", summary="Close a fiscal period")
def close_fiscal_period(
    body: ClosePeriodBody,
    db: Session = Depends(get_db),
    _admin: dict = Depends(require_admin),


@router.get("/periods", summary="List fiscal periods")
def list_fiscal_periods(
    country_code: Optional[str] = Query(None, max_length=3),
    status: Optional[str] = Query(None),
    limit: int = Query(24, ge=1, le=120),
    db: Session = Depends(get_db),
    _user=Depends(require_admin),


@router.post("/journal-entries/reverse", summary="Reverse a journal entry")
def reverse_entry(
    body: ReversalBody,
    db: Session = Depends(get_db),
    _admin: dict = Depends(require_admin),


@router.post("/cash-flow-forecast", summary="Generate cash flow forecast")
def cash_flow_forecast(
    days: int = Query(90, ge=1, le=365),
    currency: str = Query("OMR", max_length=10),
    country_code: Optional[str] = Query(None, max_length=3),
    db: Session = Depends(get_db),
    _admin: dict = Depends(require_admin),


@router.get("/ar", summary="AR sub-ledger (customer receivables)")
def get_ar(
    customer_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    country_code: Optional[str] = Query(None, max_length=3),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
    _admin: dict = Depends(require_admin),


@router.post("/ar-ledger/invoice", summary="Post AR invoice")
def post_ar_invoice_route(body: ARInvoiceBody, db: Session = Depends(get_db), _admin: dict = Depends(require_admin)):
    cleanup = _with_rls(body.country_code, db)
    try:
        return controller_post_ar_invoice(db, **body.model_dump(), admin_user=_admin)
    finally:
        cleanup()




@router.post("/ar-ledger/payment", summary="Post AR payment")
def post_ar_payment_route(body: ARPaymentBody, db: Session = Depends(get_db), _admin: dict = Depends(require_admin)):
    cleanup = _with_rls(body.country_code, db)
    try:
        return controller_post_ar_payment(db, **body.model_dump(), admin_user=_admin)
    finally:
        cleanup()




@router.get("/ap", summary="AP Sub-ledger alias (Accounts Payable)")
def get_ap_alias(
    supplier_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    country_code: Optional[str] = Query(None, max_length=3),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
    _admin: dict = Depends(require_admin),


@router.get("/ap-ledger", summary="AP Sub-ledger (Accounts Payable)")
def get_ap(
    supplier_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    country_code: Optional[str] = Query(None, max_length=3),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
    _admin: dict = Depends(require_admin),


@router.post("/ap-ledger/payable", summary="Post AP payable")
def post_ap_payable_route(body: APPayableBody, db: Session = Depends(get_db), _admin: dict = Depends(require_admin)):
    cleanup = _with_rls(body.country_code, db)
    try:
        return controller_post_ap_payable(db, **body.model_dump(), admin_user=_admin)
    finally:
        cleanup()




@router.post("/ap-ledger/payment", summary="Post AP payment")
def post_ap_payment_route(body: APPaymentBody, db: Session = Depends(get_db), _admin: dict = Depends(require_admin)):
    cleanup = _with_rls(body.country_code, db)
    try:
        return controller_post_ap_payment(db, **body.model_dump(), admin_user=_admin)
    finally:
        cleanup()




@router.get("/metrics")
def treasury_metrics(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),


@router.get("/cash-position")
def cash_position(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),


@router.get("/vat-liability")
def vat_liability(
    country_code: str = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),


@router.get("/supplier-payables")
def supplier_payables(
    country_code: str = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),


@router.get("/pending")
def get_pending_payouts(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db),


@router.post("/payouts/{payout_id}/approve")
def approve_payout(
    payout_id: int,
    payload: ActionRequest | None = None,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db),


@router.post("/payouts/{payout_id}/reject")
def reject_payout(
    payout_id: int,
    payload: ActionRequest | None = None,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db),


@router.post("/batches/{batch_id}/approve")
def approve_batch(
    batch_id: int,
    payload: ActionRequest | None = None,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db),


@router.post("/batches/{batch_id}/reject")
def reject_batch(
    batch_id: int,
    payload: ActionRequest | None = None,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db),


@router.post("/batches/{batch_id}/dispatch")
def dispatch_batch(
    batch_id: int,
    payload: ActionRequest | None = None,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db),


@router.post("/run", summary="Run full automation suite")
def run_automation(country_code: str = None, period_year: int = None,
                    period_month: int = None, db: Session = Depends(get_db),
                    _admin: dict = Depends(require_admin)):
    return scheduler.run_full_automation(db, country_code=country_code,
                                          period_year=period_year,
                                          period_month=period_month)




@router.post("/cash-snapshot", summary="Take cash position snapshot")
def cash_snapshot(country_code: str = None, db: Session = Depends(get_db),
                   _admin: dict = Depends(require_admin)):
    return scheduler.take_cash_snapshot(db, country_code=country_code)




@router.post("/vat", summary="Compute VAT remittance for a period")
def compute_vat(period_year: int, period_month: int, country_code: str = None,
                db: Session = Depends(get_db), _admin: dict = Depends(require_admin)):
    return scheduler.compute_vat_remittance(db, period_year, period_month, country_code)




@router.post("/reports", summary="Generate period financial reports")
def generate_reports(period_year: int, period_month: int, country_code: str = None,
                      db: Session = Depends(get_db), _admin: dict = Depends(require_admin)):
    return scheduler.generate_period_reports(db, period_year, period_month, country_code)




@router.post("/statements/distributors", summary="Generate distributor statements")
def distributor_statements(period_year: int, period_month: int, country_code: str = None,
                            db: Session = Depends(get_db),
                            _admin: dict = Depends(require_admin)):
    return scheduler.generate_distributor_statements(db, period_year, period_month, country_code)




@router.post("/statements/suppliers", summary="Generate supplier statements")
def supplier_statements(period_year: int, period_month: int, country_code: str = None,
                         db: Session = Depends(get_db),
                         _admin: dict = Depends(require_admin)):
    return scheduler.generate_supplier_statements(db, period_year, period_month, country_code)




@router.post("/alerts", summary="Run alert engine")
def run_alerts(country_code: str = None, db: Session = Depends(get_db),
               _admin: dict = Depends(require_admin)):
    return scheduler.run_alert_engine(db, country_code=country_code)




@router.post("/gateway-reconciliation/run", summary="Run 3-way gateway reconciliation")
def run_gateway_reconciliation(country_code: str = None, db: Session = Depends(get_db),
                                _admin: dict = Depends(require_admin)):
    """Run 3-way gateway reconciliation (order vs gateway vs bank)."""
    return run_gateway_3way_reconciliation(db, country_code)




@router.post("/gateway-reconciliation/match/{settlement_id}", summary="Match a gateway settlement")
def match_settlement(settlement_id: int, bank_statement_line_id: int = None,
                      country_code: str = None, db: Session = Depends(get_db),
                      _admin: dict = Depends(require_admin)):
    """Manually match a specific gateway settlement."""
    return match_gateway_settlement(db, settlement_id, bank_statement_line_id, country_code)




@router.post("/cod-reconcile/{order_id}", summary="Reconcile COD deposit for an order")
def cod_reconcile(order_id: int, deposited_amount: float, logistics_partner_id: int = None,
                   bank_transaction_id: int = None, country_code: str = None,
                   db: Session = Depends(get_db), _admin: dict = Depends(require_admin)):
    """Reconcile COD cash deposit from logistics partner."""
    from decimal import Decimal
    return reconcile_cod_deposit(
        db, order_id, Decimal(str(deposited_amount)),
        logistics_partner_id, bank_transaction_id, country_code
    )




@router.post("/payout-batches/generate", summary="Generate supplier payout batches")
def generate_payout_batches(country_code: str = None, holding_days: int = 7,
                             db: Session = Depends(get_db),
                             _admin: dict = Depends(require_admin)):
    """Nightly cron: Generate payout batches from eligible settlements."""
    return generate_supplier_payout_batches(db, country_code, holding_days)




@router.post("/payout-batches/logistics", summary="Generate logistics payout batches")
def generate_logistics_batches(country_code: str = None, holding_days: int = 7,
                                db: Session = Depends(get_db),
                                _admin: dict = Depends(require_admin)):
    """Generate payout batches for logistics partners."""
    return generate_logistics_payout_batches(db, country_code, holding_days)




@router.get("/payout-batches/pending/{supplier_id}", summary="Get pending batches for supplier")
def pending_supplier_batches(supplier_id: int, db: Session = Depends(get_db)):
    """Get payout batches pending supplier approval."""
    return get_pending_batches_for_supplier(db, supplier_id)




@router.post("/payout-batches/{batch_id}/approve", summary="Supplier approves payout batch")
def approve_batch(batch_id: int, supplier_id: int, approved: bool = True,
                   notes: str = None, db: Session = Depends(get_db)):
    """Supplier self-approval for payout batch."""
    return supplier_approve_batch(db, batch_id, supplier_id, approved, notes)




@router.post("/refunds/{refund_id}/post", summary="Auto-post refund journal entries")
def post_refund(refund_id: int, approved_by: int = None, country_code: str = None,
                db: Session = Depends(get_db), _admin: dict = Depends(require_admin)):
    """Auto-post journal entries when a refund is approved."""
    return post_refund_automatically(db, refund_id, approved_by, country_code)




@router.get("/credit-check/{customer_id}", summary="Check customer credit status")
def credit_check(customer_id: int, order_amount: float = None,
                  db: Session = Depends(get_db)):
    """Pre-dispatch credit check for a customer."""
    from decimal import Decimal
    return check_customer_credit(
        db, customer_id,
        Decimal(str(order_amount)) if order_amount else None
    )




@router.post("/credit-control/enforce", summary="Enforce auto credit holds")
def enforce_credit_holds(country_code: str = None, db: Session = Depends(get_db),
                          _admin: dict = Depends(require_admin)):
    """Daily cron: Auto-place/release credit holds."""
    return enforce_auto_credit_holds(db, country_code)




@router.get("/credit-summary/{customer_id}", summary="Get customer credit summary")
def credit_summary(customer_id: int, db: Session = Depends(get_db)):
    """Get comprehensive credit summary for a customer."""
    return get_customer_credit_summary(db, customer_id)




@router.post("/ai/bank-reconciliation", summary="Run AI fuzzy bank reconciliation")
def ai_bank_recon(country_code: str = None, db: Session = Depends(get_db),
                    _admin: dict = Depends(require_admin)):
    """AI-powered fuzzy bank reconciliation using semantic matching."""
    return run_ai_bank_reconciliation(db, country_code)




@router.post("/email/inbox", summary="Process email inbox for invoices")
def process_email_inbox_endpoint(country_code: str = None,
                                  db: Session = Depends(get_db),
                                  _admin: dict = Depends(require_admin)):
    """Batch process email inbox for invoice emails."""
    return process_email_inbox(db, country_code)




@router.post("/email/process", summary="Process an invoice email")
def process_email_endpoint(email_text: str = Body(..., embed=True), sender: str = None,
                             country_code: str = None,
                             db: Session = Depends(get_db),
                             _admin: dict = Depends(require_admin)):
    """Process a single invoice email through OCR-to-ledger pipeline."""
    return process_email_invoice(db, email_text, sender, country_code)




@router.post("/mobile/scan", summary="Process mobile receipt scan")
def mobile_scan_endpoint(country_code: str = None,
                           db: Session = Depends(get_db),
                           _admin: dict = Depends(require_admin)):
    """Mobile upload endpoint - process receipt image through OCR to GL.
    Note: For binary upload, send as multipart/form-data with 'image' field.
    This endpoint returns the processing pipeline definition."""
    return {
        "status": "ready",
        "endpoint": "/automation/mobile/scan/upload",
        "method": "POST multipart/form-data",
        "fields": ["image (binary)", "vendor_name (optional)", "country_code (optional)"],
    }




@router.post("/ai/categorize/{expense_id}", summary="AI categorize a scanned expense")
def categorize_expense(expense_id: int, db: Session = Depends(get_db),
                         _admin: dict = Depends(require_admin)):
    """Use AI to categorize a scanned expense and auto-post to GL."""
    from decimal import Decimal
    return categorize_expense_ai(db, expense_id)




@router.post("/ai/categorize/batch", summary="Batch categorize all uncategorized expenses")
def batch_categorize_endpoint(country_code: str = None,
                                db: Session = Depends(get_db),
                                _admin: dict = Depends(require_admin)):
    """Batch categorize all uncategorized scanned expenses."""
    return batch_categorize_all(db, country_code)



# === MERGED FROM modules/treasury/routers/cash_management_controller.py ===
from __future__ import annotations


def admin_get_financial_summary(db):
    return {}


def admin_get_reconciliation_summary(db):
    return {}


def admin_list_ledger_entries(db, **kwargs):
    return []


def admin_list_badge_billing_records(db, **kwargs):
    return []


def admin_record_badge_billing_payment(**kwargs):
    return {}


def admin_list_supplier_settlements(db, **kwargs):
    return []


def admin_list_logistics_settlements(db, **kwargs):
    return []


def admin_list_bank_transactions(db, **kwargs):
    return []


def admin_list_refunds(db, **kwargs):
    return []


def admin_list_vat_remittance_records(db, **kwargs):
    return []


def admin_get_finance_bank_settings(db):
    return {}


def admin_list_transfer_providers(db):
    return []


def admin_test_finance_bank_connection(db):
    return {}


def admin_upsert_finance_bank_settings(data, current_admin, db):
    return {}


def admin_record_vat_remittance(data, current_admin, db):
    return {}


def admin_create_bank_transaction(data, db):
    return {}


def admin_import_bank_transactions(data, db):
    return {}


def admin_reconcile_transaction(txn_id, current_admin, db):
    return {}


def admin_flag_transaction(txn_id, reason, db):
    return {}


def admin_resolve_transaction_exception(txn_id, data, current_admin, db):
    return {}


def admin_auto_reconcile_transactions(db, **kwargs):
    return {}


def admin_trigger_supplier_payouts(db, **kwargs):
    return {}


def admin_trigger_logistics_payouts(db, **kwargs):
    return {}


def admin_queue_dispatch_transfer_batch(data, current_admin, db):
    return {}


def admin_dispatch_transfer_batch(data, current_admin, db):
    return {}


def admin_record_cod_remittance(settlement_id, amount, current_admin, db):
    return {}


def admin_list_cod_remittance_receipts(db, **kwargs):
    return []


def admin_verify_cod_remittance_receipt(receipt_id, current_admin, db, **kwargs):
    return {}


def admin_reject_cod_remittance_receipt(receipt_id, current_admin, db, **kwargs):
    return {}


def supplier_get_financial_summary(supplier_id, db):
    return {}


def supplier_list_settlements(supplier_id, db, **kwargs):
    return []


def supplier_list_ledger_entries(supplier_id, db, **kwargs):
    return []


def logistics_get_financial_summary(partner_id, db):
    return {}


def logistics_list_settlements(partner_id, db, **kwargs):
    return []


def logistics_list_ledger_entries(partner_id, db, **kwargs):
    return []
