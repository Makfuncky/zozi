"""Admin treasury router � split from finance.py."""
"""Admin finance router — consolidated from 37 source files."""

from fastapi import APIRouter, HTTPException, Depends, Query, Path, Body, status

from datetime import date
from datetime import date, datetime
from datetime import date, datetime, timezone
from datetime import datetime
from decimal import Decimal
from fastapi import APIRouter
from fastapi import APIRouter, Body, Depends, HTTPException, Path, Query
from fastapi import APIRouter, Depends
from fastapi import APIRouter, Depends, Body
from fastapi import APIRouter, Depends, Body, Query
from fastapi import APIRouter, Depends, HTTPException, Path
from fastapi import APIRouter, Depends, HTTPException, Path, Query
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi import APIRouter, Depends, HTTPException, Query, Body as FastAPIBody, Path
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body, status
from fastapi import APIRouter, Depends, Path, Query
from fastapi import APIRouter, Depends, Query
from fastapi import Body as FastAPIBody
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from pydantic import BaseModel, field_validator
from sqlalchemy import func, select
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from sqlalchemy.orm import Session, joinedload
from typing import Any
from typing import Any, Optional
from typing import Any, cast
from typing import List, Optional
from typing import Optional
import json
import logging
import structlog
try:
    from domains.accounts.services.permissions.permission_service import get_hierarchy_permissions
except BaseException:
    get_hierarchy_permissions = (lambda *a, **k: None)
try:
    from domains.accounts.services.permissions.permission_service import get_staff_permission_catalog
except BaseException:
    get_staff_permission_catalog = (lambda *a, **k: None)
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
    from domains.comms.services._auto_stubs import create_cash_account as create_cash_account_model
except BaseException:
    create_cash_account_model = (lambda *a, **k: None)
try:
    from domains.comms.services._auto_stubs import create_cash_transaction as create_cash_transaction_model
except BaseException:
    create_cash_transaction_model = (lambda *a, **k: None)
try:
    from domains.comms.services.shared.utility.shared_utils import reset_demo_data
except BaseException:
    reset_demo_data = (lambda *a, **k: None)
try:
    from domains.country.utils.country_rls import get_country_or_404
except BaseException:
    get_country_or_404 = (lambda *a, **k: None)
try:
    from domains.finance.models.commission import CommissionCategoryRate
except BaseException:
    CommissionCategoryRate = (lambda *a, **k: None)
try:
    from domains.finance.models.finance import Account
except BaseException:
    Account = (lambda *a, **k: None)
try:
    from domains.finance.models.finance import AccountBalance
except BaseException:
    AccountBalance = (lambda *a, **k: None)
try:
    from domains.finance.models.finance import BankTransaction
except BaseException:
    BankTransaction = (lambda *a, **k: None)
try:
    from domains.finance.models.finance import CashAccount
except BaseException:
    CashAccount = (lambda *a, **k: None)
try:
    from domains.finance.models.finance import CashFlowForecast
except BaseException:
    CashFlowForecast = (lambda *a, **k: None)
try:
    from domains.finance.models.finance import CashPositionSnapshot
except BaseException:
    CashPositionSnapshot = (lambda *a, **k: None)
try:
    from domains.finance.models.finance import CashTransaction
except BaseException:
    CashTransaction = (lambda *a, **k: None)
try:
    from domains.finance.models.finance import FinanceAutomationLog
except BaseException:
    FinanceAutomationLog = (lambda *a, **k: None)
try:
    from domains.finance.models.finance import GatewaySettlementSchedule
except BaseException:
    GatewaySettlementSchedule = (lambda *a, **k: None)
try:
    from domains.finance.models.finance import Invoice
except BaseException:
    Invoice = (lambda *a, **k: None)
try:
    from domains.finance.models.finance import JournalEntry
except BaseException:
    JournalEntry = (lambda *a, **k: None)
try:
    from domains.finance.models.finance import JournalEntryLine
except BaseException:
    JournalEntryLine = (lambda *a, **k: None)
try:
    from domains.finance.models.finance import PayoutBatch
except BaseException:
    PayoutBatch = (lambda *a, **k: None)
try:
    from domains.finance.models.finance import PayoutBatchItem
except BaseException:
    PayoutBatchItem = (lambda *a, **k: None)
try:
    from domains.finance.models.finance import SupplierSettlement
except BaseException:
    SupplierSettlement = (lambda *a, **k: None)
try:
    from domains.finance.models.finance import TransactionLedger
except BaseException:
    TransactionLedger = (lambda *a, **k: None)
try:
    from domains.finance.models.finance import TreasuryAccount
except BaseException:
    TreasuryAccount = (lambda *a, **k: None)
try:
    from domains.finance.models.finance import VATRemittance
except BaseException:
    VATRemittance = (lambda *a, **k: None)
try:
    from domains.finance.models.payments import LogisticsPartnerPayout
except BaseException:
    LogisticsPartnerPayout = (lambda *a, **k: None)
try:
    from domains.finance.models.payments import Payment
except BaseException:
    Payment = (lambda *a, **k: None)
try:
    from domains.finance.models.payments import Payout
except BaseException:
    Payout = (lambda *a, **k: None)
try:
    from domains.finance.services.payouts.payout_batch_service import get_background_job_status as _get_bg_status
except BaseException:
    _get_bg_status = (lambda *a, **k: None)
try:
    from domains.finance.services.payouts.payout_batch_service import run_auto_logistics_payout_sweep as _run_logistics_sweep
except BaseException:
    _run_logistics_sweep = (lambda *a, **k: None)
try:
    from domains.finance.services.payouts.payout_batch_service import run_auto_payout_sweep as _run_supplier_sweep
except BaseException:
    _run_supplier_sweep = (lambda *a, **k: None)
try:
    from domains.finance.services.payouts.payout_batch_service import start_auto_payout_background_job as _start_bg_job
except BaseException:
    _start_bg_job = (lambda *a, **k: None)
try:
    from domains.finance.services.payouts.payout_batch_service import stop_auto_payout_background_job as _stop_bg_job
except BaseException:
    _stop_bg_job = (lambda *a, **k: None)
try:
    from domains.finance.services.country.admin_commission_service import create_badge_tier
except BaseException:
    create_badge_tier = (lambda *a, **k: None)
try:
    from domains.finance.services.ledger.general_ledger_service import create_category_rate
except BaseException:
    create_category_rate = (lambda *a, **k: None)
try:
    from domains.finance.services.country.admin_commission_service import list_badge_tiers
except BaseException:
    list_badge_tiers = (lambda *a, **k: None)
try:
    from domains.finance.services.finance_service import list_category_rates
except BaseException:
    list_category_rates = (lambda *a, **k: None)
try:
    from domains.finance.services.country.admin_commission_service import update_badge_tier
except BaseException:
    update_badge_tier = (lambda *a, **k: None)
try:
    from domains.finance.services.finance_service import update_category_rate
except BaseException:
    update_category_rate = (lambda *a, **k: None)
try:
    from domains.accounts.services.users.users_admin_service import _build_list_page_payload
except BaseException:
    _build_list_page_payload = (lambda *a, **k: None)
try:
    from domains.finance.services.ledger.general_ledger_service import _category_to_slug
except BaseException:
    _category_to_slug = (lambda *a, **k: None)
try:
    from domains.finance.services.ledger.general_ledger_service import _float_or_none
except BaseException:
    _float_or_none = (lambda *a, **k: None)
try:
    from domains.country.services.core.country_service import _require_admin
except BaseException:
    _require_admin = (lambda *a, **k: None)
try:
    from domains.finance.services.ledger.general_ledger_service import _serialize_agreement
except BaseException:
    _serialize_agreement = (lambda *a, **k: None)
try:
    from domains.finance.services.ledger.general_ledger_service import _serialize_badge_tier
except BaseException:
    _serialize_badge_tier = (lambda *a, **k: None)
try:
    from domains.finance.services.ledger.general_ledger_service import _serialize_category_rate
except BaseException:
    _serialize_category_rate = (lambda *a, **k: None)
try:
    from domains.finance.services.ledger.general_ledger_service import _serialize_global_config
except BaseException:
    _serialize_global_config = (lambda *a, **k: None)
try:
    from domains.finance.services.ledger.general_ledger_service import _serialize_ledger_entry
except BaseException:
    _serialize_ledger_entry = (lambda *a, **k: None)
try:
    from domains.finance.services.ledger.general_ledger_service import _serialize_override
except BaseException:
    _serialize_override = (lambda *a, **k: None)
try:
    from domains.finance.services.ledger.general_ledger_service import _supplier_rate_snapshot
except BaseException:
    _supplier_rate_snapshot = (lambda *a, **k: None)
try:
    from domains.finance.services.ledger.general_ledger_service import create_ledger_adjustment
except BaseException:
    create_ledger_adjustment = (lambda *a, **k: None)
try:
    from domains.finance.services.finance_service import delete_product_commission_override
except BaseException:
    delete_product_commission_override = (lambda *a, **k: None)
try:
    from domains.finance.services.finance_service import delete_supplier_commission_override
except BaseException:
    delete_supplier_commission_override = (lambda *a, **k: None)
try:
    from domains.finance.services.finance_service import get_effective_rate
except BaseException:
    get_effective_rate = (lambda *a, **k: None)
try:
    from domains.finance.services.finance_service import get_global_config
except BaseException:
    get_global_config = (lambda *a, **k: None)
try:
    from domains.finance.services.finance_service import get_product_commission_override
except BaseException:
    get_product_commission_override = (lambda *a, **k: None)
try:
    from domains.finance.services.finance_service import get_supplier_commission
except BaseException:
    get_supplier_commission = (lambda *a, **k: None)
try:
    from domains.finance.services.ledger.general_ledger_service import get_supplier_policy_snapshot
except BaseException:
    get_supplier_policy_snapshot = (lambda *a, **k: None)
try:
    from domains.finance.services.ledger.general_ledger_service import list_all_supplier_commissions
except BaseException:
    list_all_supplier_commissions = (lambda *a, **k: None)
try:
    from domains.finance.services.country.admin_commission_service import list_badge_tiers
except BaseException:
    list_badge_tiers = (lambda *a, **k: None)
try:
    from domains.finance.services.finance_service import list_category_rates
except BaseException:
    list_category_rates = (lambda *a, **k: None)
try:
    from domains.finance.services.finance_service import list_ledger_entries
except BaseException:
    list_ledger_entries = (lambda *a, **k: None)
try:
    from domains.finance.ports import list_product_commission_overrides
except BaseException:
    list_product_commission_overrides = (lambda *a, **k: None)
try:
    from domains.finance.services.finance_service import preview_commission
except BaseException:
    preview_commission = (lambda *a, **k: None)
try:
    from domains.finance.services.finance_service import set_product_commission_override
except BaseException:
    set_product_commission_override = (lambda *a, **k: None)
try:
    from domains.finance.services.finance_service import set_supplier_commission
except BaseException:
    set_supplier_commission = (lambda *a, **k: None)
try:
    from domains.finance.services.country.admin_commission_service import update_badge_tier
except BaseException:
    update_badge_tier = (lambda *a, **k: None)
try:
    from domains.finance.services.finance_service import update_category_rate
except BaseException:
    update_category_rate = (lambda *a, **k: None)
try:
    from domains.finance.services.finance_service import update_global_config
except BaseException:
    update_global_config = (lambda *a, **k: None)
try:
    from domains.finance.services._auto_stubs import accounting_controller
except BaseException:
    accounting_controller = (lambda *a, **k: None)
try:
    from domains.finance.services._auto_stubs import JournalEntryBody
except BaseException:
    JournalEntryBody = (lambda *a, **k: None)
try:
    from domains.finance.services.ledger.general_ledger_service import create_journal_entry
except BaseException:
    create_journal_entry = (lambda *a, **k: None)
try:
    from domains.finance.services._auto_stubs import get_account
except BaseException:
    get_account = (lambda *a, **k: None)
try:
    from domains.finance.services.ledger.general_ledger_service import get_account_balance
except BaseException:
    get_account_balance = (lambda *a, **k: None)
try:
    from domains.finance.services.ledger.general_ledger_service import get_journal_entry
except BaseException:
    get_journal_entry = (lambda *a, **k: None)
try:
    from domains.finance.services.ledger.general_ledger_service import get_trial_balance
except BaseException:
    get_trial_balance = (lambda *a, **k: None)
try:
    from domains.finance.ports import list_accounts
except BaseException:
    list_accounts = (lambda *a, **k: None)
try:
    from domains.finance.services.ledger.general_ledger_service import list_journal_entries
except BaseException:
    list_journal_entries = (lambda *a, **k: None)
try:
    from domains.finance.services.ledger.general_ledger_service import seed_chart_of_accounts
except BaseException:
    seed_chart_of_accounts = (lambda *a, **k: None)
try:
    from domains.finance.services.ledger.general_ledger_service import reverse_journal_entry
except BaseException:
    reverse_journal_entry = (lambda *a, **k: None)
try:
    from domains.finance.services.ledger.general_ledger_service import close_period
except BaseException:
    close_period = (lambda *a, **k: None)
try:
    from domains.finance.services.ledger.general_ledger_service import get_current_fiscal_period
except BaseException:
    get_current_fiscal_period = (lambda *a, **k: None)
try:
    from domains.finance.services.ledger.general_ledger_service import get_or_create_fiscal_period
except BaseException:
    get_or_create_fiscal_period = (lambda *a, **k: None)
try:
    from domains.finance.services.ledger.general_ledger_service import list_periods
except BaseException:
    list_periods = (lambda *a, **k: None)
try:
    from domains.finance.services._auto_stubs import controller_get_ap_summary
except BaseException:
    controller_get_ap_summary = (lambda *a, **k: None)
try:
    from domains.finance.services._auto_stubs import controller_get_ar_summary
except BaseException:
    controller_get_ar_summary = (lambda *a, **k: None)
try:
    from domains.finance.services._auto_stubs import controller_post_ap_payable
except BaseException:
    controller_post_ap_payable = (lambda *a, **k: None)
try:
    from domains.finance.services._auto_stubs import controller_post_ap_payment
except BaseException:
    controller_post_ap_payment = (lambda *a, **k: None)
try:
    from domains.finance.services._auto_stubs import controller_post_ar_invoice
except BaseException:
    controller_post_ar_invoice = (lambda *a, **k: None)
try:
    from domains.finance.services._auto_stubs import controller_post_ar_payment
except BaseException:
    controller_post_ar_payment = (lambda *a, **k: None)
try:
    from domains.finance.services.payouts.payout_batch_service import approve_batch as approve_batch_action
except BaseException:
    approve_batch_action = (lambda *a, **k: None)
try:
    from domains.finance.services.payouts.payout_batch_service import approve_payout as approve_payout_action
except BaseException:
    approve_payout_action = (lambda *a, **k: None)
try:
    from domains.finance.services.payouts.payout_batch_service import dispatch_batch as dispatch_batch_action
except BaseException:
    dispatch_batch_action = (lambda *a, **k: None)
try:
    from domains.finance.services.payouts.payout_batch_service import reject_batch as reject_batch_action
except BaseException:
    reject_batch_action = (lambda *a, **k: None)
try:
    from domains.finance.services.payouts.payout_batch_service import reject_payout as reject_payout_action
except BaseException:
    reject_payout_action = (lambda *a, **k: None)
try:
    from domains.finance.services._auto_stubs import get_payout_by_id, list_pending_payouts
except BaseException:
    get_payout_by_id = list_pending_payouts = (lambda *a, **k: None)
try:
    from domains.finance.services.payouts.payout_batch_service import get_background_job_status as _get_bg_status
except BaseException:
    _get_bg_status = (lambda *a, **k: None)
try:
    from domains.finance.services.payouts.payout_batch_service import run_auto_logistics_payout_sweep as _run_logistics_sweep
except BaseException:
    _run_logistics_sweep = (lambda *a, **k: None)
try:
    from domains.finance.services.payouts.payout_batch_service import run_auto_payout_sweep as _run_supplier_sweep
except BaseException:
    _run_supplier_sweep = (lambda *a, **k: None)
try:
    from domains.finance.services.payouts.payout_batch_service import start_auto_payout_background_job as _start_bg_job
except BaseException:
    _start_bg_job = (lambda *a, **k: None)
try:
    from domains.finance.services.payouts.payout_batch_service import stop_auto_payout_background_job as _stop_bg_job
except BaseException:
    _stop_bg_job = (lambda *a, **k: None)
try:
    from domains.finance.services.payouts.payout_batch_service import approve_batch
except BaseException:
    approve_batch = (lambda *a, **k: None)
try:
    from domains.finance.services.payouts.payout_batch_service import approve_payout
except BaseException:
    approve_payout = (lambda *a, **k: None)
try:
    from domains.finance.services.payouts.payout_batch_service import dispatch_batch
except BaseException:
    dispatch_batch = (lambda *a, **k: None)
try:
    from domains.finance.services.payouts.payout_batch_service import reject_batch
except BaseException:
    reject_batch = (lambda *a, **k: None)
try:
    from domains.finance.services.payouts.payout_batch_service import reject_payout
except BaseException:
    reject_payout = (lambda *a, **k: None)
try:
    from domains.finance.services.payouts.payout_batch_service import list_pending_payouts
except BaseException:
    list_pending_payouts = (lambda *a, **k: None)
try:
    from domains.finance.services.payouts.payout_batch_service import approve_payout, reject_payout, approve_batch, reject_batch, dispatch_batch
except BaseException:
    approve_payout = reject_payout = approve_batch = reject_batch = dispatch_batch = (lambda *a, **k: None)
try:
    from domains.finance.services._auto_stubs import FinancialReportingService
except BaseException:
    FinancialReportingService = (lambda *a, **k: None)
try:
    from domains.finance.services.treasury.cash_management_service import generate_forecast as generate_cash_forecast
except BaseException:
    generate_cash_forecast = (lambda *a, **k: None)
try:
    from domains.finance.services.treasury.cash_management_service import auto_reconcile_transactions
except BaseException:
    auto_reconcile_transactions = (lambda *a, **k: None)
try:
    from domains.finance.services.treasury.cash_management_service import create_bank_transaction
except BaseException:
    create_bank_transaction = (lambda *a, **k: None)
try:
    from domains.finance.services.treasury.cash_management_service import dispatch_transfer_batch
except BaseException:
    dispatch_transfer_batch = (lambda *a, **k: None)
try:
    from domains.finance.services.treasury.cash_management_service import flag_transaction
except BaseException:
    flag_transaction = (lambda *a, **k: None)
try:
    from domains.finance.services.treasury.cash_management_service import import_bank_transactions
except BaseException:
    import_bank_transactions = (lambda *a, **k: None)
try:
    from domains.finance.services._auto_stubs import queue_dispatch_transfer_batch
except BaseException:
    queue_dispatch_transfer_batch = (lambda *a, **k: None)
try:
    from domains.finance.services.treasury.cash_management_service import reconcile_transaction
except BaseException:
    reconcile_transaction = (lambda *a, **k: None)
try:
    from domains.finance.services.treasury.cash_management_service import record_badge_billing_payment
except BaseException:
    record_badge_billing_payment = (lambda *a, **k: None)
try:
    from domains.finance.services.treasury.cash_management_service import record_cod_remittance
except BaseException:
    record_cod_remittance = (lambda *a, **k: None)
try:
    from domains.finance.services.treasury.cash_management_service import record_vat_remittance
except BaseException:
    record_vat_remittance = (lambda *a, **k: None)
try:
    from domains.finance.services.treasury.cash_management_service import reject_cod_remittance_receipt
except BaseException:
    reject_cod_remittance_receipt = (lambda *a, **k: None)
try:
    from domains.finance.services.treasury.cash_management_service import resolve_transaction_exception
except BaseException:
    resolve_transaction_exception = (lambda *a, **k: None)
try:
    from domains.finance.services.treasury.cash_management_service import trigger_logistics_payouts
except BaseException:
    trigger_logistics_payouts = (lambda *a, **k: None)
try:
    from domains.finance.services.treasury.cash_management_service import trigger_supplier_payouts
except BaseException:
    trigger_supplier_payouts = (lambda *a, **k: None)
try:
    from domains.finance.services.treasury.cash_management_service import upsert_bank_settings
except BaseException:
    upsert_bank_settings = (lambda *a, **k: None)
try:
    from domains.finance.services.treasury.cash_management_service import verify_cod_remittance_receipt
except BaseException:
    verify_cod_remittance_receipt = (lambda *a, **k: None)
try:
    from domains.finance.services._auto_stubs import TreasuryEngine
except BaseException:
    TreasuryEngine = (lambda *a, **k: None)
try:
    from domains.finance.services.treasury.treasury_service import get_cash_position
except BaseException:
    get_cash_position = (lambda *a, **k: None)
try:
    from domains.finance.services.treasury.treasury_service import get_supplier_payables
except BaseException:
    get_supplier_payables = (lambda *a, **k: None)
try:
    from domains.finance.services.treasury.treasury_service import get_treasury_metrics
except BaseException:
    get_treasury_metrics = (lambda *a, **k: None)
try:
    from domains.finance.services.treasury.treasury_service import get_vat_liability
except BaseException:
    get_vat_liability = (lambda *a, **k: None)
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
    from domains.governance.models.admin import CommissionBadgeTier
except BaseException:
    CommissionBadgeTier = (lambda *a, **k: None)
try:
    from domains.governance.models.admin import LogisticsCODRemittanceReceipt
except BaseException:
    LogisticsCODRemittanceReceipt = (lambda *a, **k: None)
try:
    from domains.governance.models.user import User
except BaseException:
    User = (lambda *a, **k: None)
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
    from domains.logistics.services.core.service import verify_payout_route
except BaseException:
    verify_payout_route = (lambda *a, **k: None)
try:
    from domains.orders.services.orders_service import get_all_orders
except BaseException:
    get_all_orders = (lambda *a, **k: None)
try:
    from infrastructure.security.auth import require_permission
except BaseException:
    require_permission = (lambda *a, **k: None)
try:
    from domains.catalog.services.products.admin_products_service import get_all_products
except BaseException:
    get_all_products = (lambda *a, **k: None)
try:
    from domains.governance.services._auto_stubs import get_pending_products
except BaseException:
    get_pending_products = (lambda *a, **k: None)
try:
    from infrastructure.database.database_service import get_database_overview
except BaseException:
    get_database_overview = (lambda *a, **k: None)
try:
    from domains.governance.services.settings.misc_service import get_audit_log_page
except BaseException:
    get_audit_log_page = (lambda *a, **k: None)
try:
    from domains.governance.services.settings.misc_service import get_available_audit_actions
except BaseException:
    get_available_audit_actions = (lambda *a, **k: None)
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
    from domains.accounts.services.identity.identity_admin_service import delete_user_admin
except BaseException:
    delete_user_admin = (lambda *a, **k: None)
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
    from domains.accounts.services.users.users_admin_service import verify_bank_account
except BaseException:
    verify_bank_account = (lambda *a, **k: None)
try:
    from domains.finance.services.payouts.payout_batch_service import verify_payout
except BaseException:
    verify_payout = (lambda *a, **k: None)
try:
    from domains.logistics.models.logistics import LogisticsPartner
except BaseException:
    LogisticsPartner = (lambda *a, **k: None)
try:
    from domains.customers.services.coupons_service import delete_coupon
except BaseException:
    delete_coupon = (lambda *a, **k: None)
try:
    from domains.customers.services.coupons_read_service import list_coupons
except BaseException:
    list_coupons = (lambda *a, **k: None)
try:
    from domains.orders.models.orders import Order as OrderModel
except BaseException:
    OrderModel = (lambda *a, **k: None)
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
        CashAccountCreate,
        CashAccountOut,
        CashTransactionCreate,
        CashTransactionOut,
    )
except BaseException:
    CashAccountCreate = CashAccountOut = CashTransactionCreate = CashTransactionOut = (lambda *a, **k: None)
try:
    from infrastructure.database.schemas import (
        CommissionBadgeTierCreate,
        CommissionBadgeTierOut,
        CommissionCategoryRateCreate,
        CommissionCategoryRateOut,
    )
except BaseException:
    CommissionBadgeTierCreate = CommissionBadgeTierOut = CommissionCategoryRateCreate = CommissionCategoryRateOut = (lambda *a, **k: None)
try:
    from infrastructure.database.schemas import CashAccountCreate, CashAccountOut, CashTransactionCreate, CashTransactionOut
except BaseException:
    CashAccountCreate = CashAccountOut = CashTransactionCreate = CashTransactionOut = (lambda *a, **k: None)
try:
    from infrastructure.database.schemas import CommissionCategoryRateCreate, CommissionCategoryRateOut, CommissionBadgeTierCreate, CommissionBadgeTierOut
except BaseException:
    CommissionCategoryRateCreate = CommissionCategoryRateOut = CommissionBadgeTierCreate = CommissionBadgeTierOut = (lambda *a, **k: None)
try:
    from infrastructure.database.schemas import FlashSaleCreate, FlashSaleOut
except BaseException:
    FlashSaleCreate = FlashSaleOut = (lambda *a, **k: None)
try:
    from infrastructure.database.schemas import PayoutCreate, PayoutOut
except BaseException:
    PayoutCreate = PayoutOut = (lambda *a, **k: None)
try:
    from infrastructure.routing.route_contract import post
except BaseException:
    post = (lambda *a, **k: None)
try:
    from infrastructure.utils.audit import AuditAction, audit_log
except BaseException:
    AuditAction = audit_log = (lambda *a, **k: None)
try:
    from infrastructure.utils.audit import audit_log, AuditAction
except BaseException:
    audit_log = AuditAction = (lambda *a, **k: None)
try:
    from infrastructure.utils.backup import get_backup_manager
except BaseException:
    get_backup_manager = (lambda *a, **k: None)
try:
    from infrastructure.utils.constants import (
        CASH_ACCOUNT,
        DEFAULT_PAGE_SIZE,
        INPUT_VAT_ACCOUNT,
        MAX_PAGE_SIZE,
        OUTPUT_VAT_ACCOUNT,
        PAYABLES_ACCOUNT,
        TREASURY_ROLES,
    )
except BaseException:
    CASH_ACCOUNT = DEFAULT_PAGE_SIZE = INPUT_VAT_ACCOUNT = MAX_PAGE_SIZE = OUTPUT_VAT_ACCOUNT = PAYABLES_ACCOUNT = TREASURY_ROLES = (lambda *a, **k: None)
try:
    from infrastructure.utils.constants import (
        DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE,
        TREASURY_ROLES, PAYOUT_STATUSES, SETTLEMENT_STATUSES,
        BATCH_STATUSES, COD_REMITTANCE_STATUSES, GATEWAY_SETTLEMENT_STATUSES,
        CASH_ACCOUNT, PAYABLES_ACCOUNT, OUTPUT_VAT_ACCOUNT, INPUT_VAT_ACCOUNT,
    )
except BaseException:
    DEFAULT_PAGE_SIZE = MAX_PAGE_SIZE = TREASURY_ROLES = PAYOUT_STATUSES = SETTLEMENT_STATUSES = BATCH_STATUSES = COD_REMITTANCE_STATUSES = GATEWAY_SETTLEMENT_STATUSES = CASH_ACCOUNT = PAYABLES_ACCOUNT = OUTPUT_VAT_ACCOUNT = INPUT_VAT_ACCOUNT = (lambda *a, **k: None)
try:
    from infrastructure.utils.constants import MAX_BULK_ITEMS
except BaseException:
    MAX_BULK_ITEMS = (lambda *a, **k: None)
try:
    from infrastructure.utils.datetime_utils import utcnow
except BaseException:
    utcnow = (lambda *a, **k: None)
try:
    from infrastructure.utils.dependencies import require_admin
except BaseException:
    require_admin = (lambda *a, **k: None)
try:
    from infrastructure.utils.rls_interceptor import clear_rls_context, set_rls_context
except BaseException:
    clear_rls_context = set_rls_context = (lambda *a, **k: None)
try:
    from infrastructure.utils.rls_interceptor import set_rls_context, clear_rls_context
except BaseException:
    set_rls_context = clear_rls_context = (lambda *a, **k: None)
try:
    from modules.admin.auth import get_current_admin, get_current_user, require_admin
except BaseException:
    get_current_admin = get_current_user = require_admin = (lambda *a, **k: None)
try:
    from rbac import get_current_user
except BaseException:
    get_current_user = (lambda *a, **k: None)
try:
    from rbac.dependencies import require_feature, require_module
except BaseException:
    require_feature = require_module = (lambda *a, **k: None)

_s12 = APIRouter(prefix='')

try:
    def get_engine(db: Session = Depends(get_db)) -> TreasuryEngine:
        return TreasuryEngine(db)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route: %s", _e)

try:
    def require_treasury_access(current_user: dict = Depends(get_current_user)) -> dict:
        if current_user.get("role", "").lower() not in TREASURY_ROLES:
            raise HTTPException(status_code=403, detail="Treasury access required")
        return current_user
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route: %s", _e)

try:
    def     admin_treasury_root(
        db: Session = Depends(get_db),
        current_user: dict = Depends(require_treasury_access),
    ):
        """Treasury root — summary stats (bare /admin/treasury)."""
        total_entries = db.query(JournalEntry).count() or 0
        total_accounts = db.query(Account).count() or 0
        total_cash = db.execute(
            select(func.coalesce(func.sum(AccountBalance.balance), 0))
        ).scalar() or Decimal("0")
        return {
            "total_entries": total_entries,
            "total_accounts": total_accounts,
            "total_cash": float(total_cash),
            "metrics_available_at": "/admin/treasury/metrics",
            "ledger_available_at": "/admin/treasury/ledger",
        }
    _s12.get("/")(admin_treasury_root)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route admin_treasury_root: %s", _e)

try:
    def     admin_treasury_metrics(
        db: Session = Depends(get_db),
        current_user: dict = Depends(require_treasury_access),
    ):
        total_debits = db.execute(
            select(func.coalesce(func.sum(JournalEntryLine.amount), 0))
            .where(JournalEntryLine.side == "debit")
        ).scalar() or Decimal("0")

        total_credits = db.execute(
            select(func.coalesce(func.sum(JournalEntryLine.amount), 0))
            .where(JournalEntryLine.side == "credit")
        ).scalar() or Decimal("0")

        total_entries = db.query(JournalEntry).count()

        return {
            "total_credits": float(total_credits),
            "total_debits": float(total_debits),
            "net_balance": float(total_credits - total_debits),
            "total_entries": total_entries,
        }
    _s12.get("/metrics")(admin_treasury_metrics)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route admin_treasury_metrics: %s", _e)

try:
    def     admin_treasury_ledger(
        start_date: date = Query(...),
        end_date: date = Query(...),
        limit: int = Query(DEFAULT_PAGE_SIZE),
        db: Session = Depends(get_db),
        current_user: dict = Depends(require_treasury_access),
    ):
        entries = db.execute(
            select(JournalEntry)
            .where(JournalEntry.entry_date >= start_date, JournalEntry.entry_date <= end_date)
            .options(joinedload(JournalEntry.lines))
            .order_by(JournalEntry.entry_date.desc())
            .limit(min(limit, MAX_PAGE_SIZE))
        ).unique().scalars().all()

        result = []
        for e in entries:
            total_debit = sum(
                float(line.amount) for line in e.lines if line.side == "debit"
            )
            total_credit = sum(
                float(line.amount) for line in e.lines if line.side == "credit"
            )
            result.append({
                "id": e.id,
                "reference_number": getattr(e, "reference_number", ""),
                "entry_date": e.entry_date.isoformat() if hasattr(e, "entry_date") and e.entry_date else "",
                "description": e.description or "",
                "source": e.source or "",
                "total_debit": total_debit,
                "total_credit": total_credit,
            })
        return result
    _s12.get("/ledger")(admin_treasury_ledger)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route admin_treasury_ledger: %s", _e)

try:
    def     admin_trial_balance(
        as_of_date: Optional[str] = Query(None),
        country_code: Optional[str] = Query(None),
        db: Session = Depends(get_db),
        current_user: dict = Depends(require_treasury_access),
    ):
        engine = TreasuryEngine(db)
        rows = engine.get_trial_balance()
        return rows
    _s12.get("/reports/trial-balance")(admin_trial_balance)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route admin_trial_balance: %s", _e)

try:
    def     admin_cash_position(
        db: Session = Depends(get_db),
        current_user: dict = Depends(require_treasury_access),
    ):
        accounts = db.execute(
            select(TreasuryAccount).where(TreasuryAccount.is_active == True)
        ).scalars().all()

        return [
            {
                "account_name": a.name,
                "balance": float(a.balance),
                "gl_code": a.gl_account_code or a.slug,
            }
            for a in accounts
        ]
    _s12.get("/cash-position")(admin_cash_position)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route admin_cash_position: %s", _e)

try:
    def     admin_payout_batches(
        db: Session = Depends(get_db),
        current_user: dict = Depends(require_treasury_access),
    ):
        batches = db.execute(
            select(PayoutBatch)
            .options(joinedload(PayoutBatch.creator), joinedload(PayoutBatch.approver))
            .order_by(PayoutBatch.created_at.desc())
            .limit(MAX_PAGE_SIZE)
        ).unique().scalars().all()

        return [
            {
                "id": b.id,
                "batch_number": b.batch_number,
                "country_code": b.country_code,
                "total_amount": float(b.total_amount),
                "status": b.status,
                "created_at": b.created_at.isoformat(),
                "created_by": b.created_by,
                "created_by_name": b.creator.full_name if b.creator else None,
                "approved_by": b.approved_by,
                "approved_by_name": b.approver.full_name if b.approver else None,
            }
            for b in batches
        ]
    _s12.get("/payouts/batches")(admin_payout_batches)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route admin_payout_batches: %s", _e)

try:
    def     admin_generate_payout_batch(
        country_code: str = FastAPIBody(...),
        cutoff_date: date = FastAPIBody(...),
        db: Session = Depends(get_db),
        current_user: dict = Depends(require_treasury_access),
    ):
        from domains.finance.models.payments import Payout

        pending_payouts = db.execute(
            select(Payout).where(
                Payout.country_code == country_code,
                Payout.status == "pending",
                Payout.created_at <= cutoff_date,
            )
        ).scalars().all()

        if not pending_payouts:
            raise HTTPException(status_code=404, detail="No pending payouts found for the given criteria")

        total = sum(p.amount for p in pending_payouts)
        batch = PayoutBatch(
            batch_number=f"PB-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            country_code=country_code,
            total_amount=total,
            item_count=len(pending_payouts),
            status="draft",
            created_by=current_user.get("id"),
        )
        db.add(batch)
        db.flush()

        for payout in pending_payouts:
            item = PayoutBatchItem(
                batch_id=batch.id,
                entity_type="payout",
                entity_id=payout.id,
                amount=payout.amount,
                reference=getattr(payout, "reference_number", None),
            )
            db.add(item)
            payout.status = "batched"
        db.commit()
        db.refresh(batch)

        return {
            "id": batch.id,
            "batch_number": batch.batch_number,
            "country_code": batch.country_code,
            "total_amount": float(batch.total_amount),
            "item_count": batch.item_count,
            "status": batch.status,
        }
    _s12.post("/payouts/batches/generate")(admin_generate_payout_batch)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route admin_generate_payout_batch: %s", _e)

try:
    def     admin_approve_payout_batch(
        batch_id: int = Path(...),
        db: Session = Depends(get_db),
        current_user: dict = Depends(require_treasury_access),
    ):
        batch = db.execute(
            select(PayoutBatch).where(PayoutBatch.id == batch_id).with_for_update()
        ).scalar_one_or_none()

        if not batch:
            raise HTTPException(status_code=404, detail="Batch not found")
        if batch.status != "draft":
            raise HTTPException(status_code=400, detail=f"Batch is already {batch.status}")
        if batch.created_by == current_user.get("id"):
            raise HTTPException(status_code=403, detail="Maker-Checker: cannot approve your own batch")

        batch.status = "approved"
        batch.approved_by = current_user.get("id")
        db.commit()

        return {"status": "approved", "batch_id": batch.id, "batch_number": batch.batch_number}
    _s12.post("/payouts/batches/{batch_id}/approve")(admin_approve_payout_batch)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route admin_approve_payout_batch: %s", _e)

try:
    def     admin_dispatch_payout_batch(
        batch_id: int = Path(...),
        db: Session = Depends(get_db),
        current_user: dict = Depends(require_treasury_access),
    ):
        batch = db.execute(
            select(PayoutBatch).where(PayoutBatch.id == batch_id).with_for_update()
        ).scalar_one_or_none()

        if not batch:
            raise HTTPException(status_code=404, detail="Batch not found")
        if batch.status != "approved":
            raise HTTPException(status_code=400, detail=f"Batch must be approved first, current status: {batch.status}")

        engine = TreasuryEngine(db)
        entry = engine.post_journal_entry(
            lines=[
                {"account_code": PAYABLES_ACCOUNT, "debit": float(batch.total_amount), "description": f"Payout batch {batch.batch_number}"},
                {"account_code": CASH_ACCOUNT, "credit": float(batch.total_amount), "description": f"Payout batch {batch.batch_number}"},
            ],
            description=f"Dispatch payout batch {batch.batch_number}",
            source="payout_dispatch",
            country_code=batch.country_code,
            created_by=current_user.get("id"),
        )

        batch.status = "dispatched"
        batch.dispatched_at = datetime.utcnow()
        db.commit()

        return {
            "status": "dispatched",
            "batch_id": batch.id,
            "batch_number": batch.batch_number,
            "journal_entry_id": entry.id,
            "reference_number": entry.reference_number,
        }
    _s12.post("/payouts/batches/{batch_id}/dispatch")(admin_dispatch_payout_batch)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route admin_dispatch_payout_batch: %s", _e)

try:
    def     admin_vat_liability(
        country_code: Optional[str] = Query(None),
        period: str = Query("current"),
        db: Session = Depends(get_db),
        current_user: dict = Depends(require_treasury_access),
    ):
        output_vat = db.execute(
            select(func.coalesce(func.sum(AccountBalance.balance), 0))
            .join(Account, AccountBalance.account_id == Account.id)
            .where(Account.code == OUTPUT_VAT_ACCOUNT)
        ).scalar() or Decimal("0")

        input_vat = db.execute(
            select(func.coalesce(func.sum(AccountBalance.balance), 0))
            .join(Account, AccountBalance.account_id == Account.id)
            .where(Account.code == INPUT_VAT_ACCOUNT)
        ).scalar() or Decimal("0")

        return {
            "output_vat": float(output_vat),
            "input_vat": float(input_vat),
            "net_vat_due": float(output_vat - input_vat),
            "country_code": country_code,
            "period": period,
        }
    _s12.get("/reports/vat-liability")(admin_vat_liability)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route admin_vat_liability: %s", _e)

try:
    def     admin_cod_remittances(
        status: Optional[str] = Query(None),
        db: Session = Depends(get_db),
        current_user: dict = Depends(require_treasury_access),
    ):

        query = (
            select(LogisticsCODRemittanceReceipt, LogisticsPartner.name)
            .outerjoin(LogisticsPartner, LogisticsCODRemittanceReceipt.partner_id == LogisticsPartner.id)
        )
        if status:
            query = query.where(LogisticsCODRemittanceReceipt.status == status)
        query = query.order_by(LogisticsCODRemittanceReceipt.created_at.desc()).limit(MAX_PAGE_SIZE)

        rows = db.execute(query).all()

        return [
            {
                "id": r.id,
                "logistics_partner_id": r.partner_id,
                "logistics_partner_name": partner_name or "Unknown",
                "amount_remitted": float(r.amount or 0),
                "amount_expected": float(r.amount or 0),
                "status": r.status,
                "remitted_at": r.created_at.isoformat() if r.created_at else None,
                "bank_reference": None,
                "proof_url": None,
            }
            for r, partner_name in rows
        ]
    _s12.get("/cod-remittances")(admin_cod_remittances)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route admin_cod_remittances: %s", _e)

try:
    def     admin_gateway_summary(
        db: Session = Depends(get_db),
        current_user: dict = Depends(require_treasury_access),
    ):
        schedules = db.execute(
            select(GatewaySettlementSchedule)
            .order_by(GatewaySettlementSchedule.settlement_date.desc())
            .limit(100)
        ).scalars().all()

        from collections import defaultdict
        by_gateway = defaultdict(lambda: {"total_settled": 0, "total_expected": 0, "count": 0, "last_date": None})

        for s in schedules:
            key = str(s.gateway_id)
            by_gateway[key]["total_expected"] += float(s.amount or 0)
            by_gateway[key]["count"] += 1
            if s.status == "settled":
                by_gateway[key]["total_settled"] += float(s.amount or 0)
            if not by_gateway[key]["last_date"] or (s.settlement_date and s.settlement_date > by_gateway[key]["last_date"]):
                by_gateway[key]["last_date"] = s.settlement_date

        return [
            {
                "gateway_code": gid,
                "total_settled": data["total_settled"],
                "total_expected": data["total_expected"],
                "discrepancy": data["total_expected"] - data["total_settled"],
                "count": data["count"],
                "last_settlement_date": data["last_date"].isoformat() if data["last_date"] else None,
            }
            for gid, data in by_gateway.items()
        ]
    _s12.get("/reconciliation/gateway-summary")(admin_gateway_summary)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route admin_gateway_summary: %s", _e)

try:
    def     admin_snapshot_cash_position(
        db: Session = Depends(get_db),
        current_user: dict = Depends(require_treasury_access),
    ):
        accounts = db.execute(
            select(TreasuryAccount).where(TreasuryAccount.is_active == True)
        ).scalars().all()

        now = datetime.utcnow()
        for a in accounts:
            snap = CashPositionSnapshot(
                snapshot_time=now,
                account_id=a.id,
                balance=a.balance,
                currency=a.currency or "USD",
            )
            db.add(snap)
        db.commit()

        return {"status": "snapshot_recorded", "accounts_snapshotted": len(accounts)}
    _s12.post("/cash-position/snapshot")(admin_snapshot_cash_position)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route admin_snapshot_cash_position: %s", _e)

try:
    def     admin_cash_forecasts(
        db: Session = Depends(get_db),
        current_user: dict = Depends(require_treasury_access),
    ):
        forecasts = db.execute(
            select(CashFlowForecast).order_by(CashFlowForecast.forecast_date.desc()).limit(12)
        ).scalars().all()

        return [
            {
                "id": f.id,
                "forecast_date": f.forecast_date.isoformat(),
                "period_start": f.period_start.isoformat(),
                "period_end": f.period_end.isoformat(),
                "net_cash_flow": float(f.net_cash_flow),
                "opening_balance": float(f.opening_balance),
                "closing_balance": float(f.closing_balance),
            }
            for f in forecasts
        ]
    _s12.get("/forecasts")(admin_cash_forecasts)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route admin_cash_forecasts: %s", _e)

try:
    def     consolidated_treasury_metrics(
        db: Session = Depends(get_db),
        current_user: dict = Depends(require_treasury_access),
    ):
        total_accounts = db.query(TreasuryAccount).count()
        total_je = db.query(JournalEntry).count()
        total_batches = db.query(PayoutBatch).count()
        total_invoices = db.query(Invoice).count()
        return {
            "total_accounts": total_accounts,
            "total_journal_entries": total_je,
            "total_payout_batches": total_batches,
            "total_invoices": total_invoices,
        }
    _s12.get("/consolidated/metrics")(consolidated_treasury_metrics)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route consolidated_treasury_metrics: %s", _e)

try:
    def     consolidated_treasury_ledger(
        limit: int = Query(50, ge=1, le=500),
        db: Session = Depends(get_db),
        current_user: dict = Depends(require_treasury_access),
    ):
        entries = db.query(JournalEntry).order_by(JournalEntry.created_at.desc()).limit(limit).all()
        return [
            {
                "id": e.id,
                "description": e.description,
                "entry_type": e.entry_type,
                "amount": float(e.amount),
                "status": e.status,
                "created_at": e.created_at.isoformat(),
            }
            for e in entries
        ]
    _s12.get("/consolidated/ledger")(consolidated_treasury_ledger)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route consolidated_treasury_ledger: %s", _e)

try:
    def     consolidated_trial_balance(
        db: Session = Depends(get_db),
        current_user: dict = Depends(require_treasury_access),
        page: int = Query(1, ge=1),
        page_size: int = Query(20, ge=1, le=100),
    ):
        query = db.query(Account).filter(Account.is_active == True)
        total = query.count()
        accounts = query.order_by(Account.code).offset((page - 1) * page_size).limit(page_size).all()
        return {
            "data": [
                {
                    "id": a.id,
                    "code": a.code,
                    "name": a.name,
                    "normal_side": a.normal_side,
                    "total_debits": float(db.query(func.coalesce(func.sum(JournalEntryLine.amount), 0)).filter(JournalEntryLine.account_id == a.id, JournalEntryLine.side == "debit").scalar() or 0),
                    "total_credits": float(db.query(func.coalesce(func.sum(JournalEntryLine.amount), 0)).filter(JournalEntryLine.account_id == a.id, JournalEntryLine.side == "credit").scalar() or 0),
                }
                for a in accounts
            ],
            "total": total,
            "page": page,
            "page_size": page_size,
        }
    _s12.get("/consolidated/reports/trial-balance")(consolidated_trial_balance)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route consolidated_trial_balance: %s", _e)

try:
    def     consolidated_cash_position(
        db: Session = Depends(get_db),
        current_user: dict = Depends(require_treasury_access),
        page: int = Query(1, ge=1),
        page_size: int = Query(20, ge=1, le=100),
    ):
        query = db.query(TreasuryAccount).filter(TreasuryAccount.is_active == True)
        total = query.count()
        accounts = query.offset((page - 1) * page_size).limit(page_size).all()
        total_balance = float(db.query(func.coalesce(func.sum(TreasuryAccount.balance), 0)).filter(TreasuryAccount.is_active == True).scalar() or 0)
        return {
            "accounts": [
                {
                    "id": a.id,
                    "name": a.name,
                    "balance": float(a.balance or 0),
                    "currency": a.currency or "USD",
                }
                for a in accounts
            ],
            "total_balance": total_balance,
            "total": total,
            "page": page,
            "page_size": page_size,
        }
    _s12.get("/consolidated/cash-position")(consolidated_cash_position)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route consolidated_cash_position: %s", _e)

try:
    def     consolidated_payout_batches(
        limit: int = Query(50, ge=1, le=200),
        db: Session = Depends(get_db),
        current_user: dict = Depends(require_treasury_access),
    ):
        batches = db.query(PayoutBatch).order_by(PayoutBatch.created_at.desc()).limit(limit).all()
        return [
            {
                "id": b.id,
                "batch_ref": b.batch_number,
                "status": b.status,
                "total_amount": float(b.total_amount or 0),
                "item_count": b.item_count,
                "country_code": b.country_code,
                "created_at": b.created_at.isoformat(),
            }
            for b in batches
        ]
    _s12.get("/consolidated/payouts/batches")(consolidated_payout_batches)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route consolidated_payout_batches: %s", _e)

try:
    def     consolidated_vat_liability(
        db: Session = Depends(get_db),
        current_user: dict = Depends(require_treasury_access),
    ):
        vats = db.query(VATRemittance).order_by(VATRemittance.period_start.desc()).limit(12).all()
        return [
            {
                "id": v.id,
                "country_code": v.country_code,
                "period_start": v.period_start.isoformat(),
                "period_end": v.period_end.isoformat(),
                "total_collected": float(v.vat_collected_amount or 0),
                "total_deducted": float(v.vat_adjustment_amount or 0),
                "net_due": float(v.amount_due or 0),
                "status": v.status,
            }
            for v in vats
        ]
    _s12.get("/consolidated/reports/vat-liability")(consolidated_vat_liability)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route consolidated_vat_liability: %s", _e)

try:
    def     consolidated_cod_remittances(
        limit: int = Query(50, ge=1, le=200),
        db: Session = Depends(get_db),
        current_user: dict = Depends(require_treasury_access),
    ):
        from domains.logistics.models.logistics import Shipment as ShipmentModel
        receipts = db.query(LogisticsCODRemittanceReceipt).order_by(LogisticsCODRemittanceReceipt.created_at.desc()).limit(limit).all()
        return [
            {
                "id": r.id,
                "shipment_id": r.shipment_id,
                "order_id": (db.query(ShipmentModel.order_id).filter(ShipmentModel.id == r.shipment_id).scalar() if r.shipment_id else None),
                "partner_id": r.partner_id,
                "amount": float(r.amount),
                "bank_reference": r.bank_reference,
                "status": r.status,
                "country_code": r.country_code,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in receipts
        ]
    _s12.get("/consolidated/cod-remittances")(consolidated_cod_remittances)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route consolidated_cod_remittances: %s", _e)

try:
    def     consolidated_gateway_summary(
        db: Session = Depends(get_db),
        current_user: dict = Depends(require_treasury_access),
    ):
        schedules = db.query(GatewaySettlementSchedule).order_by(GatewaySettlementSchedule.settlement_date.desc()).limit(12).all()
        return [
            {
                "id": s.id,
                "gateway": s.gateway_id,
                "settlement_date": s.settlement_date.isoformat() if s.settlement_date else None,
                "amount": float(s.amount or 0),
                "currency": s.currency,
                "status": s.status,
            }
            for s in schedules
        ]
    _s12.get("/consolidated/reconciliation/gateway-summary")(consolidated_gateway_summary)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route consolidated_gateway_summary: %s", _e)

try:
    def     consolidated_cash_forecasts(
        db: Session = Depends(get_db),
        current_user: dict = Depends(require_treasury_access),
    ):
        forecasts = db.execute(
            select(CashFlowForecast).order_by(CashFlowForecast.forecast_date.desc()).limit(12)
        ).scalars().all()
        return [
            {
                "id": f.id,
                "forecast_date": f.forecast_date.isoformat(),
                "period_start": f.period_start.isoformat(),
                "period_end": f.period_end.isoformat(),
                "net_cash_flow": float(f.net_cash_flow),
                "opening_balance": float(f.opening_balance),
                "closing_balance": float(f.closing_balance),
            }
            for f in forecasts
        ]
    _s12.get("/consolidated/forecasts")(consolidated_cash_forecasts)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route consolidated_cash_forecasts: %s", _e)

try:
    def     consolidated_reconciliation_pipeline(
        limit: int = Query(50, ge=1, le=200),
        db: Session = Depends(get_db),
        current_user: dict = Depends(require_treasury_access),
    ):
        from domains.finance.models.payments import Payment as PaymentModel
        from domains.finance.models.payments import Payout

        pipeline = []
        orders = db.query(OrderModel).filter(
            OrderModel.status.in_(["shipped", "delivered", "completed", "dispatched"])
        ).order_by(OrderModel.updated_at.desc()).limit(limit).all()

        for order in orders:
            payment = db.query(PaymentModel).filter(PaymentModel.order_id == order.id).first()
            settlement = db.query(SupplierSettlement).filter(SupplierSettlement.order_id == order.id).first()
            payout = db.query(Payout).filter(Payout.id == settlement.payout_id).first() if (settlement and settlement.payout_id) else None

            pipeline.append({
                "order_id": order.id,
                "order_status": order.status,
                "order_total": float(getattr(order, "total_amount", None) or getattr(order, "total", 0) or 0),
                "country_code": order.country_code or "",
                "payment_method": payment.payment_method if payment else None,
                "payment_status": payment.status if payment else None,
                "supplier_settlement_status": settlement.status if settlement else None,
                "supplier_payout_status": payout.status if payout else None,
                "stage": _resolve_stage(order, payment, None, settlement, payout),
            })

        return {"pipeline": pipeline, "total": len(pipeline), "consolidated": True}
    _s12.get("/consolidated/reconciliation/pipeline")(consolidated_reconciliation_pipeline)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route consolidated_reconciliation_pipeline: %s", _e)

try:
    def     country_treasury_metrics(
        country_code: str = Path(..., description="ISO country code"),
        db: Session = Depends(get_db),
        current_user: dict = Depends(require_treasury_access),
    ):
        cc = country_code.upper()
        total_debits = db.execute(
            select(func.coalesce(func.sum(JournalEntryLine.amount), 0))
            .join(JournalEntry, JournalEntryLine.entry_id == JournalEntry.id)
            .where(JournalEntryLine.side == "debit", JournalEntry.country_code == cc)
        ).scalar() or Decimal("0")
        total_credits = db.execute(
            select(func.coalesce(func.sum(JournalEntryLine.amount), 0))
            .join(JournalEntry, JournalEntryLine.entry_id == JournalEntry.id)
            .where(JournalEntryLine.side == "credit", JournalEntry.country_code == cc)
        ).scalar() or Decimal("0")
        total_entries = db.query(JournalEntry).filter(JournalEntry.country_code == cc).count()
        return {
            "total_credits": float(total_credits),
            "total_debits": float(total_debits),
            "net_balance": float(total_credits - total_debits),
            "total_entries": total_entries,
            "country_code": cc,
        }
    _s12.get("/{country_code}/metrics")(country_treasury_metrics)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route country_treasury_metrics: %s", _e)

try:
    def     country_treasury_ledger(
        country_code: str = Path(..., description="ISO country code"),
        start_date: date = Query(...),
        end_date: date = Query(...),
        limit: int = Query(50),
        db: Session = Depends(get_db),
        current_user: dict = Depends(require_treasury_access),
    ):
        cc = country_code.upper()
        entries = db.execute(
            select(JournalEntry)
            .where(
                JournalEntry.entry_date >= start_date,
                JournalEntry.entry_date <= end_date,
                JournalEntry.country_code == cc,
            )
            .options(joinedload(JournalEntry.lines))
            .order_by(JournalEntry.entry_date.desc())
            .limit(limit)
        ).unique().scalars().all()
        result = []
        for e in entries:
            result.append({
                "id": e.id,
                "reference_number": getattr(e, "reference_number", ""),
                "entry_date": e.entry_date.isoformat() if hasattr(e, "entry_date") and e.entry_date else "",
                "description": e.description or "",
                "source": e.source or "",
                "total_debit": sum(float(line.amount) for line in e.lines if line.side == "debit"),
                "total_credit": sum(float(line.amount) for line in e.lines if line.side == "credit"),
            })
        return result
    _s12.get("/{country_code}/ledger")(country_treasury_ledger)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route country_treasury_ledger: %s", _e)

try:
    def     country_trial_balance(
        country_code: str = Path(..., description="ISO country code"),
        as_of_date: Optional[str] = Query(None),
        db: Session = Depends(get_db),
        current_user: dict = Depends(require_treasury_access),
    ):
        engine = TreasuryEngine(db)
        return engine.get_trial_balance()
    _s12.get("/{country_code}/reports/trial-balance")(country_trial_balance)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route country_trial_balance: %s", _e)

try:
    def     country_cash_position(
        country_code: str = Path(..., description="ISO country code"),
        db: Session = Depends(get_db),
        current_user: dict = Depends(require_treasury_access),
    ):
        cc = country_code.upper()
        accounts = db.execute(
            select(TreasuryAccount).where(TreasuryAccount.is_active == True, TreasuryAccount.country_code == cc)
        ).scalars().all()
        if not accounts:
            accounts = db.execute(
                select(TreasuryAccount).where(TreasuryAccount.is_active == True, TreasuryAccount.country_code.is_(None))
            ).scalars().all()
        return [
            {"account_name": a.name, "balance": float(a.balance), "gl_code": a.gl_account_code or a.slug}
            for a in accounts
        ]
    _s12.get("/{country_code}/cash-position")(country_cash_position)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route country_cash_position: %s", _e)

try:
    def     country_payout_batches(
        country_code: str = Path(..., description="ISO country code"),
        db: Session = Depends(get_db),
        current_user: dict = Depends(require_treasury_access),
    ):
        cc = country_code.upper()
        batches = db.execute(
            select(PayoutBatch)
            .options(joinedload(PayoutBatch.creator), joinedload(PayoutBatch.approver))
            .where(PayoutBatch.country_code == cc)
            .order_by(PayoutBatch.created_at.desc())
            .limit(100)
        ).unique().scalars().all()
        return [
            {
                "id": b.id,
                "batch_number": b.batch_number,
                "country_code": b.country_code,
                "total_amount": float(b.total_amount),
                "status": b.status,
                "created_at": b.created_at.isoformat(),
                "created_by": b.created_by,
                "created_by_name": b.creator.full_name if b.creator else None,
                "approved_by": b.approved_by,
                "approved_by_name": b.approver.full_name if b.approver else None,
            }
            for b in batches
        ]
    _s12.get("/{country_code}/payouts/batches")(country_payout_batches)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route country_payout_batches: %s", _e)

try:
    def     country_vat_liability(
        country_code: str = Path(..., description="ISO country code"),
        period: str = Query("current"),
        db: Session = Depends(get_db),
        current_user: dict = Depends(require_treasury_access),
    ):
        output_vat = db.execute(
            select(func.coalesce(func.sum(AccountBalance.balance), 0))
            .join(Account, AccountBalance.account_id == Account.id)
            .where(Account.code == OUTPUT_VAT_ACCOUNT)
        ).scalar() or Decimal("0")
        input_vat = db.execute(
            select(func.coalesce(func.sum(AccountBalance.balance), 0))
            .join(Account, AccountBalance.account_id == Account.id)
            .where(Account.code == INPUT_VAT_ACCOUNT)
        ).scalar() or Decimal("0")
        return {
            "output_vat": float(output_vat),
            "input_vat": float(input_vat),
            "net_vat_due": float(output_vat - input_vat),
            "country_code": country_code.upper(),
            "period": period,
        }
    _s12.get("/{country_code}/reports/vat-liability")(country_vat_liability)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route country_vat_liability: %s", _e)

try:
    def     country_cod_remittances(
        country_code: str = Path(..., description="ISO country code"),
        status: Optional[str] = Query(None),
        db: Session = Depends(get_db),
        current_user: dict = Depends(require_treasury_access),
    ):

        cc = country_code.upper()
        query = (
            select(LogisticsCODRemittanceReceipt, LogisticsPartner.name)
            .outerjoin(LogisticsPartner, LogisticsCODRemittanceReceipt.partner_id == LogisticsPartner.id)
            .where(LogisticsCODRemittanceReceipt.country_code == cc)
        )
        if status:
            query = query.where(LogisticsCODRemittanceReceipt.status == status)
        query = query.order_by(LogisticsCODRemittanceReceipt.created_at.desc()).limit(100)
        rows = db.execute(query).all()
        return [
            {
                "id": r.id,
                "logistics_partner_id": r.partner_id,
                "logistics_partner_name": partner_name or "Unknown",
                "amount_remitted": float(r.amount or 0),
                "amount_expected": float(r.amount or 0),
                "status": r.status,
                "remitted_at": r.created_at.isoformat() if r.created_at else None,
                "bank_reference": None,
                "proof_url": None,
            }
            for r, partner_name in rows
        ]
    _s12.get("/{country_code}/cod-remittances")(country_cod_remittances)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route country_cod_remittances: %s", _e)

try:
    def     country_gateway_summary(
        country_code: str = Path(..., description="ISO country code"),
        db: Session = Depends(get_db),
        current_user: dict = Depends(require_treasury_access),
    ):
        cc = country_code.upper()
        schedules = db.execute(
            select(GatewaySettlementSchedule)
            .where(GatewaySettlementSchedule.country_code == cc)
            .order_by(GatewaySettlementSchedule.settlement_date.desc())
            .limit(100)
        ).scalars().all()

        from collections import defaultdict
        by_gateway = defaultdict(lambda: {"total_settled": 0, "total_expected": 0, "count": 0, "last_date": None})

        for s in schedules:
            key = str(s.gateway_id)
            by_gateway[key]["total_expected"] += float(s.amount or 0)
            by_gateway[key]["count"] += 1
            if s.status == "settled":
                by_gateway[key]["total_settled"] += float(s.amount or 0)
            if not by_gateway[key]["last_date"] or (s.settlement_date and s.settlement_date > by_gateway[key]["last_date"]):
                by_gateway[key]["last_date"] = s.settlement_date

        return [
            {
                "gateway_code": gid,
                "total_settled": data["total_settled"],
                "total_expected": data["total_expected"],
                "discrepancy": data["total_expected"] - data["total_settled"],
                "count": data["count"],
                "last_settlement_date": data["last_date"].isoformat() if data["last_date"] else None,
            }
            for gid, data in by_gateway.items()
        ]
    _s12.get("/{country_code}/reconciliation/gateway-summary")(country_gateway_summary)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route country_gateway_summary: %s", _e)

try:
    def     admin_reconciliation_pipeline(
        country_code: str = Path(..., description="ISO country code"),
        status: Optional[str] = Query(None),
        limit: int = Query(50, ge=1, le=200),
        db: Session = Depends(get_db),
        current_user: dict = Depends(require_treasury_access),
    ):
        get_country_or_404(country_code.upper(), db)
        set_rls_context({country_code.upper()}, is_restricted=True)
        cc = country_code.upper()
        try:
            from domains.governance.models.admin import LogisticsCODRemittanceReceipt
            from domains.orders.models.orders import Order as OrderModel
            from domains.orders.models.orders import OrderItem
            from domains.finance.models.payments import Payment as PaymentModel
            from domains.finance.models.payments import Payout
            from domains.finance.services.finance_service import get_effective_rate

            pipeline = []
            orders = db.query(OrderModel).filter(
                OrderModel.country_code == cc,
                OrderModel.status.in_(["shipped", "delivered", "completed", "dispatched"])
            ).order_by(OrderModel.updated_at.desc()).limit(limit).all()

            for order in orders:
                order_total = float(getattr(order, "total_amount", None) or getattr(order, "total", 0) or 0)
                payment = db.query(PaymentModel).filter(
                    PaymentModel.order_id == order.id
                ).first()

                from domains.logistics.models.logistics import Shipment
                shipment = db.query(Shipment).filter(
                    Shipment.order_id == order.id
                ).first()

                logistics_partner_name = None
                if shipment and shipment.carrier_name:
                    logistics_partner_name = shipment.carrier_name

                cod_receipt = None
                if payment and payment.payment_method == "cod":
                    cod_receipt = db.query(LogisticsCODRemittanceReceipt).filter(
                        LogisticsCODRemittanceReceipt.order_id == order.id
                    ).first()

                settlement = db.query(SupplierSettlement).filter(
                    SupplierSettlement.order_id == order.id
                ).first()

                payout = None
                if settlement:
                    payout = db.query(Payout).filter(
                        Payout.id == settlement.payout_id
                    ).first() if settlement.payout_id else None

                supplier_id = None
                first_item = db.query(OrderItem).filter(OrderItem.order_id == order.id).first()
                if first_item:
                    supplier_id = first_item.supplier_id

                commission_preview = None
                if supplier_id:
                    try:
                        rate = get_effective_rate(supplier_id=supplier_id, product_id=None, db=db)
                        commission_preview = {
                            "rate": float(rate.applied_rate),
                            "amount": float(rate.applied_rate) * order_total if hasattr(rate, 'applied_rate') else 0,
                        }
                    except Exception:
                        pass

                pipeline.append({
                    "order_id": order.id,
                    "order_status": order.status,
                    "order_total": order_total,
                    "supplier_id": supplier_id,
                    "payment_method": payment.payment_method if payment else None,
                    "payment_status": payment.status if payment else None,
                    "payment_amount": float(payment.amount) if payment else None,
                    "logistics_partner": logistics_partner_name,
                    "cod_remitted": float(cod_receipt.amount) if cod_receipt else None,
                    "cod_remittance_status": cod_receipt.status if cod_receipt else None,
                    "supplier_settlement_status": settlement.status if settlement else None,
                    "supplier_settlement_id": settlement.id if settlement else None,
                    "supplier_net_amount": float(settlement.net_amount) if settlement else None,
                    "supplier_payout_status": payout.status if payout else None,
                    "supplier_payout_amount": float(payout.amount) if payout else None,
                    "commission": commission_preview,
                    "stage": _resolve_stage(order, payment, cod_receipt, settlement, payout),
                })

            if status == "settled":
                pipeline = [p for p in pipeline if p["supplier_settlement_status"] in ("paid", "settled")]
            elif status == "unsettled":
                pipeline = [p for p in pipeline if not p["supplier_settlement_status"]]

            return {"pipeline": pipeline, "total": len(pipeline), "country_code": cc}
        finally:
            clear_rls_context()
    _s12.get("/{country_code}/reconciliation/pipeline")(admin_reconciliation_pipeline)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route admin_reconciliation_pipeline: %s", _e)

try:
    def _resolve_stage(order, payment, cod_receipt, settlement, payout) -> str:
        if payout and payout.status == "paid":
            return "supplier_paid"
        if settlement and settlement.status in ("paid", "settled"):
            return "supplier_settled"
        if payout and payout.status == "processing":
            return "payout_processing"
        if cod_receipt and cod_receipt.status == "remitted":
            return "cod_remitted"
        if cod_receipt and cod_receipt.status == "pending":
            return "cod_pending"
        if payment and payment.status == "completed":
            return "payment_received"
        if order.status in ("shipped", "delivered", "dispatched"):
            return "order_dispatched"
        return "pending"
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route: %s", _e)

try:
    def     admin_record_cod_remittance(
        country_code: str = Path(..., description="ISO country code"),
        order_id: int = FastAPIBody(...),
        partner_id: int = FastAPIBody(...),
        amount: float = FastAPIBody(...),
        bank_reference: str = FastAPIBody(...),
        db: Session = Depends(get_db),
        current_user: dict = Depends(require_treasury_access),
    ):
        get_country_or_404(country_code.upper(), db)
        set_rls_context({country_code.upper()}, is_restricted=True)
        cc = country_code.upper()
        try:
            from domains.logistics.models.logistics import Shipment as ShipmentModel
            from domains.orders.models.orders import Order as OrderModel
            shipment = db.query(ShipmentModel).filter(ShipmentModel.order_id == order_id).first()
            receipt = LogisticsCODRemittanceReceipt(
                shipment_id=shipment.id if shipment else None,
                partner_id=partner_id,
                amount=amount,
                bank_reference=bank_reference,
                status="remitted",
                country_code=cc,
            )
            db.add(receipt)
            db.flush()
            order = db.query(OrderModel).filter(OrderModel.id == order_id).first()
            if order:
                setattr(order, "settlement_status", "cod_remitted")
            db.commit()
            db.refresh(receipt)
            # Keep the double-entry ledger in sync with the reconciliation engine.
            try:
                from domains.finance.services.ledger.general_ledger_service import post_logistics_cod_remittance_journal
                post_logistics_cod_remittance_journal(db, receipt.id, Decimal(str(amount)), country_code=cc)
            except Exception as gl_err:
                logger.warning(f"COD remittance GL post skipped: {gl_err}")
            return {"status": "ok", "receipt_id": receipt.id, "country_code": cc}
        finally:
            clear_rls_context()
    _s12.post("/{country_code}/reconciliation/record-cod-remittance")(admin_record_cod_remittance)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route admin_record_cod_remittance: %s", _e)

try:
    def     admin_settle_supplier(
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
    ):
        get_country_or_404(country_code.upper(), db)
        set_rls_context({country_code.upper()}, is_restricted=True)
        cc = country_code.upper()
        try:
            from domains.country.models.countries import CountryConfig
            from domains.orders.models.orders import Order as OrderModel
            gross = gross_amount if gross_amount is not None else net_amount
            resolved_currency = currency or "USD"
            ccfg = db.query(CountryConfig).filter(CountryConfig.code == cc).first()
            if ccfg and ccfg.currency:
                resolved_currency = ccfg.currency
            settlement = SupplierSettlement(
                order_id=order_id,
                supplier_id=supplier_id,
                gross_amount=gross,
                commission_amount=commission_amount,
                net_amount=net_amount,
                status="settled",
                payout_id=payout_id,
                currency=resolved_currency,
                country_code=cc,
            )
            db.add(settlement)
            db.flush()
            order = db.query(OrderModel).filter(OrderModel.id == order_id).first()
            if order:
                setattr(order, "settlement_status", "settled")
            db.commit()
            db.refresh(settlement)
            return {"status": "ok", "settlement_id": settlement.id, "country_code": cc}
        finally:
            clear_rls_context()
    _s12.post("/{country_code}/reconciliation/settle-supplier")(admin_settle_supplier)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route admin_settle_supplier: %s", _e)

try:
    def     admin_approve_settlement(
        country_code: str = Path(..., description="ISO country code"),
        settlement_id: int = FastAPIBody(..., embed=True),
        db: Session = Depends(get_db),
        current_user: dict = Depends(require_treasury_access),
    ):
        get_country_or_404(country_code.upper(), db)
        set_rls_context({country_code.upper()}, is_restricted=True)
        try:
            settlement = db.query(SupplierSettlement).filter(
                SupplierSettlement.id == settlement_id,
                SupplierSettlement.country_code == country_code.upper(),
            ).first()
            if not settlement:
                raise HTTPException(status_code=404, detail="Settlement not found")
            settlement.status = "paid"
            db.commit()
            try:
                from domains.finance.services.ledger.general_ledger_service import post_supplier_settlement_journal
                post_supplier_settlement_journal(
                    db,
                    settlement.id,
                    Decimal(str(settlement.net_amount or 0)),
                    supplier_id=settlement.supplier_id,
                    country_code=country_code.upper(),
                )
            except Exception as gl_err:
                logger.warning(f"Supplier settlement GL post skipped: {gl_err}")
            return {"status": "ok", "settlement_id": settlement.id}
        finally:
            clear_rls_context()
    _s12.post("/{country_code}/reconciliation/approve-settlement")(admin_approve_settlement)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route admin_approve_settlement: %s", _e)

try:
    def     admin_gateway_exceptions(
        db: Session = Depends(get_db),
        current_user: dict = Depends(require_treasury_access),
    ):
        issues = db.execute(
            select(GatewaySettlementSchedule).where(
                GatewaySettlementSchedule.status.in_(["pending", "flagged"])
            ).order_by(GatewaySettlementSchedule.settlement_date.desc()).limit(100)
        ).scalars().all()
        return [
            {
                "id": s.id,
                "gateway_id": s.gateway_id,
                "settlement_date": s.settlement_date.isoformat() if s.settlement_date else None,
                "amount": float(s.amount or 0),
                "currency": s.currency,
                "status": s.status,
                "country_code": getattr(s, "country_code", None),
            }
            for s in issues
        ]
    _s12.get("/reconciliation/gateway-exceptions")(admin_gateway_exceptions)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route admin_gateway_exceptions: %s", _e)

try:
    def     country_gateway_exceptions(
        country_code: str = Path(..., description="ISO country code"),
        db: Session = Depends(get_db),
        current_user: dict = Depends(require_treasury_access),
    ):
        get_country_or_404(country_code.upper(), db)
        set_rls_context({country_code.upper()}, is_restricted=True)
        try:
            issues = db.execute(
                select(GatewaySettlementSchedule).where(
                    GatewaySettlementSchedule.status.in_(["pending", "flagged"]),
                    GatewaySettlementSchedule.country_code == country_code.upper(),
                ).order_by(GatewaySettlementSchedule.settlement_date.desc()).limit(100)
            ).scalars().all()
            return [
                {
                    "id": s.id,
                    "gateway_id": s.gateway_id,
                    "settlement_date": s.settlement_date.isoformat() if s.settlement_date else None,
                    "amount": float(s.amount or 0),
                    "currency": s.currency,
                    "status": s.status,
                    "country_code": s.country_code,
                }
                for s in issues
            ]
        finally:
            clear_rls_context()
    _s12.get("/{country_code}/reconciliation/gateway-exceptions")(country_gateway_exceptions)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route country_gateway_exceptions: %s", _e)

try:
    def     admin_payment_transactions(
        start_date: date = Query(...),
        end_date: date = Query(...),
        gateway: Optional[str] = Query(None),
        status: Optional[str] = Query(None),
        db: Session = Depends(get_db),
        current_user: dict = Depends(require_treasury_access),
    ):
        query = (
            select(Payment)
            .where(Payment.created_at >= start_date, Payment.created_at <= end_date)
            .order_by(Payment.created_at.desc())
        )
        if gateway:
            query = query.where(Payment.provider == gateway)
        if status:
            query = query.where(Payment.status == status)
        rows = db.execute(query.limit(200)).scalars().all()
        return [
            {
                "id": p.id,
                "order_id": p.order_id,
                "amount": float(p.amount),
                "payment_method": p.payment_method,
                "provider": p.provider,
                "status": p.status,
                "created_at": p.created_at.isoformat() if p.created_at else None,
                "country_code": p.country_code,
            }
            for p in rows
        ]
    _s12.get("/payments/transactions")(admin_payment_transactions)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route admin_payment_transactions: %s", _e)

try:
    def     country_payment_transactions(
        country_code: str = Path(..., description="ISO country code"),
        start_date: date = Query(...),
        end_date: date = Query(...),
        gateway: Optional[str] = Query(None),
        status: Optional[str] = Query(None),
        db: Session = Depends(get_db),
        current_user: dict = Depends(require_treasury_access),
    ):
        get_country_or_404(country_code.upper(), db)
        set_rls_context({country_code.upper()}, is_restricted=True)
        try:
            query = (
                select(Payment)
                .where(
                    Payment.country_code == country_code.upper(),
                    Payment.created_at >= start_date,
                    Payment.created_at <= end_date,
                )
                .order_by(Payment.created_at.desc())
            )
            if gateway:
                query = query.where(Payment.provider == gateway)
            if status:
                query = query.where(Payment.status == status)
            rows = db.execute(query.limit(200)).scalars().all()
            return [
                {
                    "id": p.id,
                    "order_id": p.order_id,
                    "amount": float(p.amount),
                    "payment_method": p.payment_method,
                    "provider": p.provider,
                    "status": p.status,
                    "created_at": p.created_at.isoformat() if p.created_at else None,
                    "country_code": p.country_code,
                }
                for p in rows
            ]
        finally:
            clear_rls_context()
    _s12.get("/{country_code}/payments/transactions")(country_payment_transactions)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route country_payment_transactions: %s", _e)

try:
    def     admin_supplier_payouts(
        status: Optional[str] = Query(None),
        db: Session = Depends(get_db),
        current_user: dict = Depends(require_treasury_access),
    ):
        from domains.comms.models.suppliers import SupplierProfile
        query = (
            select(Payout, SupplierProfile)
            .outerjoin(SupplierProfile, Payout.supplier_id == SupplierProfile.id)
            .order_by(Payout.created_at.desc())
        )
        if status:
            query = query.where(Payout.status == status)
        rows = db.execute(query.limit(200)).all()
        return [
            {
                "id": p.id,
                "supplier_id": p.supplier_id,
                "supplier_name": s.company_name if s else f"Supplier #{p.supplier_id}",
                "amount": float(p.amount),
                "currency": p.currency,
                "method": p.method,
                "status": p.status,
                "reference": p.reference,
                "created_at": p.created_at.isoformat() if p.created_at else None,
                "country_code": p.country_code,
            }
            for p, s in rows
        ]
    _s12.get("/supplier-payouts")(admin_supplier_payouts)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route admin_supplier_payouts: %s", _e)

try:
    def     country_supplier_payouts(
        country_code: str = Path(..., description="ISO country code"),
        status: Optional[str] = Query(None),
        db: Session = Depends(get_db),
        current_user: dict = Depends(require_treasury_access),
    ):
        get_country_or_404(country_code.upper(), db)
        set_rls_context({country_code.upper()}, is_restricted=True)
        try:
            from domains.comms.models.suppliers import SupplierProfile
            query = (
                select(Payout, SupplierProfile)
                .outerjoin(SupplierProfile, Payout.supplier_id == SupplierProfile.id)
                .where(Payout.country_code == country_code.upper())
                .order_by(Payout.created_at.desc())
            )
            if status:
                query = query.where(Payout.status == status)
            rows = db.execute(query.limit(200)).all()
            return [
                {
                    "id": p.id,
                    "supplier_id": p.supplier_id,
                    "supplier_name": s.company_name if s else f"Supplier #{p.supplier_id}",
                    "amount": float(p.amount),
                    "currency": p.currency,
                    "method": p.method,
                    "status": p.status,
                    "reference": p.reference,
                    "created_at": p.created_at.isoformat() if p.created_at else None,
                    "country_code": p.country_code,
                }
                for p, s in rows
            ]
        finally:
            clear_rls_context()
    _s12.get("/{country_code}/supplier-payouts")(country_supplier_payouts)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route country_supplier_payouts: %s", _e)

try:
    def     admin_logistics_payouts(
        status: Optional[str] = Query(None),
        db: Session = Depends(get_db),
        current_user: dict = Depends(require_treasury_access),
    ):
        query = select(LogisticsPartnerPayout).order_by(LogisticsPartnerPayout.created_at.desc())
        if status:
            query = query.where(LogisticsPartnerPayout.status == status)
        rows = db.execute(query.limit(200)).scalars().all()
        return [
            {
                "id": p.id,
                "partner_id": p.partner_id,
                "amount": float(p.amount),
                "currency": p.currency,
                "status": p.status,
                "reference_id": p.reference_id,
                "period_start": p.period_start.isoformat() if p.period_start else None,
                "period_end": p.period_end.isoformat() if p.period_end else None,
                "created_at": p.created_at.isoformat() if p.created_at else None,
                "country_code": p.country_code,
            }
            for p in rows
        ]
    _s12.get("/logistics-payouts")(admin_logistics_payouts)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route admin_logistics_payouts: %s", _e)

try:
    def     country_logistics_payouts(
        country_code: str = Path(..., description="ISO country code"),
        status: Optional[str] = Query(None),
        db: Session = Depends(get_db),
        current_user: dict = Depends(require_treasury_access),
    ):
        get_country_or_404(country_code.upper(), db)
        set_rls_context({country_code.upper()}, is_restricted=True)
        try:
            query = (
                select(LogisticsPartnerPayout)
                .where(LogisticsPartnerPayout.country_code == country_code.upper())
                .order_by(LogisticsPartnerPayout.created_at.desc())
            )
            if status:
                query = query.where(LogisticsPartnerPayout.status == status)
            rows = db.execute(query.limit(200)).scalars().all()
            return [
                {
                    "id": p.id,
                    "partner_id": p.partner_id,
                    "amount": float(p.amount),
                    "currency": p.currency,
                    "status": p.status,
                    "reference_id": p.reference_id,
                    "period_start": p.period_start.isoformat() if p.period_start else None,
                    "period_end": p.period_end.isoformat() if p.period_end else None,
                    "created_at": p.created_at.isoformat() if p.created_at else None,
                    "country_code": p.country_code,
                }
                for p in rows
            ]
        finally:
            clear_rls_context()
    _s12.get("/{country_code}/logistics-payouts")(country_logistics_payouts)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route country_logistics_payouts: %s", _e)

try:
    def     admin_supplier_earnings(
        db: Session = Depends(get_db),
        current_user: dict = Depends(require_treasury_access),
    ):
        rows = db.execute(
            select(
                SupplierSettlement.supplier_id,
                func.sum(SupplierSettlement.gross_amount).label("gross"),
                func.sum(SupplierSettlement.commission_amount).label("commission"),
                func.sum(SupplierSettlement.net_amount).label("net"),
            ).group_by(SupplierSettlement.supplier_id)
        ).all()
        return [
            {
                "supplier_id": r.supplier_id,
                "gross": float(r.gross or 0),
                "commission": float(r.commission or 0),
                "net": float(r.net or 0),
            }
            for r in rows
        ]
    _s12.get("/reports/supplier-earnings")(admin_supplier_earnings)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route admin_supplier_earnings: %s", _e)

try:
    def     country_supplier_earnings(
        country_code: str = Path(..., description="ISO country code"),
        db: Session = Depends(get_db),
        current_user: dict = Depends(require_treasury_access),
    ):
        get_country_or_404(country_code.upper(), db)
        set_rls_context({country_code.upper()}, is_restricted=True)
        try:
            rows = db.execute(
                select(
                    SupplierSettlement.supplier_id,
                    func.sum(SupplierSettlement.gross_amount).label("gross"),
                    func.sum(SupplierSettlement.commission_amount).label("commission"),
                    func.sum(SupplierSettlement.net_amount).label("net"),
                ).where(SupplierSettlement.country_code == country_code.upper())
                .group_by(SupplierSettlement.supplier_id)
            ).all()
            return [
                {
                    "supplier_id": r.supplier_id,
                    "gross": float(r.gross or 0),
                    "commission": float(r.commission or 0),
                    "net": float(r.net or 0),
                }
                for r in rows
            ]
        finally:
            clear_rls_context()
    _s12.get("/{country_code}/reports/supplier-earnings")(country_supplier_earnings)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route country_supplier_earnings: %s", _e)

try:
    def     admin_liabilities_exposure(
        db: Session = Depends(get_db),
        current_user: dict = Depends(require_treasury_access),
    ):
        codes = {"2010": "supplier_payables", "2020": "logistics_payables", "2040": "vat_payable"}
        exposure = {}
        for code, label in codes.items():
            bal = db.execute(
                select(func.coalesce(func.sum(AccountBalance.balance), 0))
                .join(Account, AccountBalance.account_id == Account.id)
                .where(Account.code == code)
            ).scalar() or Decimal("0")
            exposure[label] = float(bal)
        return exposure
    _s12.get("/liabilities/exposure")(admin_liabilities_exposure)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route admin_liabilities_exposure: %s", _e)

try:
    def     country_liabilities_exposure(
        country_code: str = Path(..., description="ISO country code"),
        db: Session = Depends(get_db),
        current_user: dict = Depends(require_treasury_access),
    ):
        get_country_or_404(country_code.upper(), db)
        set_rls_context({country_code.upper()}, is_restricted=True)
        try:
            codes = {"2010": "supplier_payables", "2020": "logistics_payables", "2030": "vat_payable"}
            exposure = {}
            for code, label in codes.items():
                bal = db.execute(
                    select(func.coalesce(func.sum(AccountBalance.balance), 0))
                    .join(Account, AccountBalance.account_id == Account.id)
                    .where(Account.code == code, AccountBalance.country_code == country_code.upper())
                ).scalar() or Decimal("0")
                exposure[label] = float(bal)
            return exposure
        finally:
            clear_rls_context()
    _s12.get("/{country_code}/liabilities/exposure")(country_liabilities_exposure)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route country_liabilities_exposure: %s", _e)

try:
    def     admin_manual_adjustment(
        debit_account: str = FastAPIBody(...),
        credit_account: str = FastAPIBody(...),
        amount: float = FastAPIBody(...),
        reason: str = FastAPIBody(...),
        created_by: int = FastAPIBody(...),
        db: Session = Depends(get_db),
        current_user: dict = Depends(require_treasury_access),
    ):
        engine = TreasuryEngine(db)
        threshold = Decimal("10000")
        amount_dec = Decimal(str(amount))
        lines = [
            {"account_code": debit_account, "debit": float(amount_dec), "description": reason},
            {"account_code": credit_account, "credit": float(amount_dec), "description": reason},
        ]
        if amount_dec > threshold:
            pending = engine.submit_pending_entry(
                lines=lines, description=reason, created_by=created_by, source="manual_adjustment",
            )
            return {"status": "pending_approval", "pending_id": pending["pending_id"]}
        entry = engine.post_journal_entry(
            lines=lines, description=reason, source="manual_adjustment", created_by=created_by,
        )
        return {"entry_id": entry.id, "reference_number": entry.reference_number}
    _s12.post("/ledger/manual-adjustment")(admin_manual_adjustment)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route admin_manual_adjustment: %s", _e)

try:
    def     country_manual_adjustment(
        country_code: str = Path(..., description="ISO country code"),
        debit_account: str = FastAPIBody(...),
        credit_account: str = FastAPIBody(...),
        amount: float = FastAPIBody(...),
        reason: str = FastAPIBody(...),
        created_by: int = FastAPIBody(...),
        db: Session = Depends(get_db),
        current_user: dict = Depends(require_treasury_access),
    ):
        get_country_or_404(country_code.upper(), db)
        set_rls_context({country_code.upper()}, is_restricted=True)
        try:
            engine = TreasuryEngine(db)
            threshold = Decimal("10000")
            amount_dec = Decimal(str(amount))
            lines = [
                {"account_code": debit_account, "debit": float(amount_dec), "description": reason},
                {"account_code": credit_account, "credit": float(amount_dec), "description": reason},
            ]
            if amount_dec > threshold:
                pending = engine.submit_pending_entry(
                    lines=lines, description=reason, created_by=created_by, source="manual_adjustment",
                    country_code=country_code.upper(),
                )
                return {"status": "pending_approval", "pending_id": pending["pending_id"]}
            entry = engine.post_journal_entry(
                lines=lines, description=reason, source="manual_adjustment", created_by=created_by,
                country_code=country_code.upper(),
            )
            return {"entry_id": entry.id, "reference_number": entry.reference_number}
        finally:
            clear_rls_context()
    _s12.post("/{country_code}/ledger/manual-adjustment")(country_manual_adjustment)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route country_manual_adjustment: %s", _e)

try:
    def     admin_pending_entries(
        db: Session = Depends(get_db),
        current_user: dict = Depends(require_treasury_access),
    ):
        engine = TreasuryEngine(db)
        return {"entries": engine.list_pending_entries()}
    _s12.get("/ledger/pending")(admin_pending_entries)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route admin_pending_entries: %s", _e)

try:
    def     country_pending_entries(
        country_code: str = Path(..., description="ISO country code"),
        db: Session = Depends(get_db),
        current_user: dict = Depends(require_treasury_access),
    ):
        get_country_or_404(country_code.upper(), db)
        set_rls_context({country_code.upper()}, is_restricted=True)
        try:
            engine = TreasuryEngine(db)
            all_entries = engine.list_pending_entries()
            filtered = [e for e in all_entries if e.get("country_code") == country_code.upper()]
            return {"entries": filtered}
        finally:
            clear_rls_context()
    _s12.get("/{country_code}/ledger/pending")(country_pending_entries)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route country_pending_entries: %s", _e)

try:
    def     admin_approve_pending(
        pending_id: int = Path(...),
        approver_id: int = FastAPIBody(...),
        db: Session = Depends(get_db),
        current_user: dict = Depends(require_treasury_access),
    ):
        engine = TreasuryEngine(db)
        result = engine.approve_pending_entry(pending_id, approver_id)
        return result
    _s12.post("/ledger/pending/{pending_id}/approve")(admin_approve_pending)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route admin_approve_pending: %s", _e)

try:
    def     country_approve_pending(
        country_code: str = Path(..., description="ISO country code"),
        pending_id: int = Path(...),
        approver_id: int = FastAPIBody(...),
        db: Session = Depends(get_db),
        current_user: dict = Depends(require_treasury_access),
    ):
        get_country_or_404(country_code.upper(), db)
        set_rls_context({country_code.upper()}, is_restricted=True)
        try:
            engine = TreasuryEngine(db)
            result = engine.approve_pending_entry(pending_id, approver_id)
            return result
        finally:
            clear_rls_context()
    _s12.post("/{country_code}/ledger/pending/{pending_id}/approve")(country_approve_pending)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route country_approve_pending: %s", _e)

try:
    def     admin_reject_pending(
        pending_id: int = Path(...),
        rejected_by: int = FastAPIBody(...),
        reason: str = FastAPIBody(...),
        db: Session = Depends(get_db),
        current_user: dict = Depends(require_treasury_access),
    ):
        engine = TreasuryEngine(db)
        result = engine.reject_pending_entry(pending_id, rejected_by, reason)
        return result
    _s12.post("/ledger/pending/{pending_id}/reject")(admin_reject_pending)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route admin_reject_pending: %s", _e)

try:
    def     country_reject_pending(
        country_code: str = Path(..., description="ISO country code"),
        pending_id: int = Path(...),
        rejected_by: int = FastAPIBody(...),
        reason: str = FastAPIBody(...),
        db: Session = Depends(get_db),
        current_user: dict = Depends(require_treasury_access),
    ):
        get_country_or_404(country_code.upper(), db)
        set_rls_context({country_code.upper()}, is_restricted=True)
        try:
            engine = TreasuryEngine(db)
            result = engine.reject_pending_entry(pending_id, rejected_by, reason)
            return result
        finally:
            clear_rls_context()
    _s12.post("/{country_code}/ledger/pending/{pending_id}/reject")(country_reject_pending)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route country_reject_pending: %s", _e)

try:
    def     admin_detect_orphans(
        db: Session = Depends(get_db),
        current_user: dict = Depends(require_treasury_access),
    ):
        engine = TreasuryEngine(db)
        alerts = engine.run_orphan_detector()
        return {"alerts": alerts, "count": len(alerts)}
    _s12.post("/detect-orphans")(admin_detect_orphans)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route admin_detect_orphans: %s", _e)

try:
    def     country_detect_orphans(
        country_code: str = Path(..., description="ISO country code"),
        db: Session = Depends(get_db),
        current_user: dict = Depends(require_treasury_access),
    ):
        get_country_or_404(country_code.upper(), db)
        set_rls_context({country_code.upper()}, is_restricted=True)
        try:
            engine = TreasuryEngine(db)
            alerts = engine.run_orphan_detector()
            filtered = [a for a in alerts if a.get("country_code") == country_code.upper()]
            return {"alerts": filtered, "count": len(filtered)}
        finally:
            clear_rls_context()
    _s12.post("/{country_code}/detect-orphans")(country_detect_orphans)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route country_detect_orphans: %s", _e)

try:
    def     payroll_equity(db: Session = Depends(get_db)):
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
    _s12.get("/payroll/equity")(payroll_equity)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route payroll_equity: %s", _e)

try:
    def     country_payroll(country_code: str, db: Session = Depends(get_db)):
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
    _s12.get("/{country_code}/payroll")(country_payroll)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route country_payroll: %s", _e)

_s13 = APIRouter(prefix='/api/v1/admin')

try:
    def     record_badge_billing_payment_route(
        billing_id: int,
        current_user: dict = Depends(require_admin),
        db: Session = Depends(get_db),
        payment_method: str = Body(..., embed=True),
        transaction_ref: Optional[str] = Body(None, embed=True),
        notes: Optional[str] = Body(None, embed=True)
    ) -> Any:
        return record_badge_billing_payment(billing_id=billing_id, current_user=current_user, db=db, payment_method=payment_method, transaction_ref=transaction_ref, notes=notes)
    _s13.post("/treasury/badge-billing/{billing_id}/payments", status_code=201, tags=['treasury'])(record_badge_billing_payment_route)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route record_badge_billing_payment_route: %s", _e)

try:
    def     upsert_bank_settings_route(
        current_user: dict = Depends(require_admin),
        db: Session = Depends(get_db),
        data: dict = Body(...)
    ) -> dict[str, Any]:
        return upsert_bank_settings(current_user=current_user, db=db, data=data)
    _s13.put("/treasury/bank-settings", status_code=200, tags=['treasury'])(upsert_bank_settings_route)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route upsert_bank_settings_route: %s", _e)

try:
    def     record_vat_remittance_route(
        current_user: dict = Depends(require_admin),
        db: Session = Depends(get_db),
        data: dict = Body(...)
    ) -> Any:
        return record_vat_remittance(current_user=current_user, db=db, data=data)
    _s13.post("/treasury/vat-remittances", status_code=201, tags=['treasury'])(record_vat_remittance_route)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route record_vat_remittance_route: %s", _e)

try:
    def     create_bank_transaction_route(
        current_user: dict = Depends(require_admin),
        db: Session = Depends(get_db),
        data: dict = Body(...)
    ) -> Any:
        return create_bank_transaction(current_user=current_user, db=db, data=data)
    _s13.post("/treasury/bank-transactions", status_code=201, tags=['treasury'])(create_bank_transaction_route)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route create_bank_transaction_route: %s", _e)

try:
    def     import_bank_transactions_route(
        current_user: dict = Depends(require_admin),
        db: Session = Depends(get_db),
        items: list[dict] = Body(..., embed=True),
        auto_reconcile: bool = Body(False, embed=True)
    ) -> dict:
        return import_bank_transactions(current_user=current_user, db=db, items=items, auto_reconcile=auto_reconcile)
    _s13.post("/treasury/bank-transactions/import", status_code=201, tags=['treasury'])(import_bank_transactions_route)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route import_bank_transactions_route: %s", _e)

try:
    def     reconcile_transaction_route(
        txn_id: int,
        current_user: dict = Depends(require_admin),
        db: Session = Depends(get_db)
    ) -> Any:
        return reconcile_transaction(txn_id=txn_id, current_user=current_user, db=db)
    _s13.post("/treasury/bank-transactions/{txn_id}/reconcile", status_code=201, tags=['treasury'])(reconcile_transaction_route)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route reconcile_transaction_route: %s", _e)

try:
    def     flag_transaction_route(
        txn_id: int,
        current_user: dict = Depends(require_admin),
        db: Session = Depends(get_db),
        reason: str = Body(...)
    ) -> Any:
        return flag_transaction(txn_id=txn_id, current_user=current_user, db=db, reason=reason)
    _s13.post("/treasury/bank-transactions/{txn_id}/flag", status_code=201, tags=['treasury'])(flag_transaction_route)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route flag_transaction_route: %s", _e)

try:
    def     resolve_transaction_exception_route(
        txn_id: int,
        current_user: dict = Depends(require_admin),
        db: Session = Depends(get_db),
        data: dict = Body(...)
    ) -> Any:
        return resolve_transaction_exception(txn_id=txn_id, current_user=current_user, db=db, data=data)
    _s13.post("/treasury/bank-transactions/{txn_id}/resolve", status_code=201, tags=['treasury'])(resolve_transaction_exception_route)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route resolve_transaction_exception_route: %s", _e)

try:
    def     auto_reconcile_transactions_route(
        current_user: dict = Depends(require_admin),
        db: Session = Depends(get_db),
        limit: int = Body(100, embed=True),
        source: Optional[str] = Body(None, embed=True),
        category: Optional[str] = Body(None, embed=True)
    ) -> dict:
        return auto_reconcile_transactions(current_user=current_user, db=db, limit=limit, source=source, category=category)
    _s13.post("/treasury/bank-transactions/auto-reconcile", status_code=201, tags=['treasury'])(auto_reconcile_transactions_route)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route auto_reconcile_transactions_route: %s", _e)

try:
    def     trigger_supplier_payouts_route(
        current_user: dict = Depends(require_admin),
        db: Session = Depends(get_db),
        settlement_ids: Optional[list[int]] = Body(None)
    ) -> list[dict]:
        return trigger_supplier_payouts(current_user=current_user, db=db, settlement_ids=settlement_ids)
    _s13.post("/treasury/payouts/supplier", status_code=201, tags=['treasury'])(trigger_supplier_payouts_route)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route trigger_supplier_payouts_route: %s", _e)

try:
    def     trigger_logistics_payouts_route(
        current_user: dict = Depends(require_admin),
        db: Session = Depends(get_db),
        settlement_ids: Optional[list[int]] = Body(None)
    ) -> list[dict]:
        return trigger_logistics_payouts(current_user=current_user, db=db, settlement_ids=settlement_ids)
    _s13.post("/treasury/payouts/logistics", status_code=201, tags=['treasury'])(trigger_logistics_payouts_route)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route trigger_logistics_payouts_route: %s", _e)

try:
    def     dispatch_transfer_batch_route(
        current_user: dict = Depends(require_admin),
        db: Session = Depends(get_db),
        kind: str = Body(..., embed=True),
        provider: Optional[str] = Body(None, embed=True),
        dry_run: bool = Body(True, embed=True)
    ) -> dict[str, Any]:
        return dispatch_transfer_batch(current_user=current_user, db=db, kind=kind, provider=provider, dry_run=dry_run)
    _s13.post("/treasury/transfers/dispatch", status_code=201, tags=['treasury'])(dispatch_transfer_batch_route)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route dispatch_transfer_batch_route: %s", _e)

try:
    def     queue_dispatch_transfer_batch_route(
        current_user: dict = Depends(require_admin),
        kind: str = Body(..., embed=True),
        provider: Optional[str] = Body(None, embed=True),
        dry_run: bool = Body(False, embed=True)
    ) -> dict[str, Any]:
        return queue_dispatch_transfer_batch(current_user=current_user, kind=kind, provider=provider, dry_run=dry_run)
    _s13.post("/treasury/transfers/dispatch/queue", status_code=201, tags=['treasury'])(queue_dispatch_transfer_batch_route)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route queue_dispatch_transfer_batch_route: %s", _e)

try:
    def     record_cod_remittance_route(
        settlement_id: int,
        current_user: dict = Depends(require_admin),
        db: Session = Depends(get_db),
        amount: float = Body(...)
    ) -> Any:
        return record_cod_remittance(settlement_id=settlement_id, current_user=current_user, db=db, amount=amount)
    _s13.post("/treasury/cod/{settlement_id}/remittance", status_code=201, tags=['treasury'])(record_cod_remittance_route)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route record_cod_remittance_route: %s", _e)

try:
    def     verify_cod_remittance_receipt_route(
        receipt_id: int,
        current_user: dict = Depends(require_admin),
        db: Session = Depends(get_db),
        note: Optional[str] = Body(None)
    ) -> dict[str, Any]:
        return verify_cod_remittance_receipt(receipt_id=receipt_id, current_user=current_user, db=db, note=note)
    _s13.post("/treasury/cod/receipts/{receipt_id}/verify", status_code=201, tags=['treasury'])(verify_cod_remittance_receipt_route)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route verify_cod_remittance_receipt_route: %s", _e)

try:
    def     reject_cod_remittance_receipt_route(
        receipt_id: int,
        current_user: dict = Depends(require_admin),
        db: Session = Depends(get_db),
        note: str = Body(...)
    ) -> dict[str, Any]:
        return reject_cod_remittance_receipt(receipt_id=receipt_id, current_user=current_user, db=db, note=note)
    _s13.post("/treasury/cod/receipts/{receipt_id}/reject", status_code=201, tags=['treasury'])(reject_cod_remittance_receipt_route)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route reject_cod_remittance_receipt_route: %s", _e)

_s14 = APIRouter(prefix='/api/v1/admin')

try:
    def     treasury_metrics(
        current_user: dict = Depends(get_current_user),
        db: Session = Depends(get_db),
    ):
        result = get_treasury_metrics(db)
        audit_log(
            db=db,
            action=AuditAction.TRIAL_BALANCE_VIEWED,
            user_id=current_user.get("id"),
            username=current_user.get("username"),
            user_role=current_user.get("role"),
            resource_type="treasury_metrics",
        )
        return result
    _s14.get("/metrics")(treasury_metrics)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route treasury_metrics: %s", _e)

try:
    def     cash_position(
        current_user: dict = Depends(get_current_user),
        db: Session = Depends(get_db),
    ):
        result = get_cash_position(db)
        audit_log(
            db=db,
            action=AuditAction.FINANCIAL_REPORT_GENERATED,
            user_id=current_user.get("id"),
            username=current_user.get("username"),
            user_role=current_user.get("role"),
            resource_type="cash_position",
        )
        return result
    _s14.get("/cash-position")(cash_position)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route cash_position: %s", _e)

try:
    def     vat_liability(
        country_code: str = None,
        current_user: dict = Depends(get_current_user),
        db: Session = Depends(get_db),
    ):
        result = get_vat_liability(db, country_code)
        audit_log(
            db=db,
            action=AuditAction.FINANCIAL_REPORT_GENERATED,
            user_id=current_user.get("id"),
            username=current_user.get("username"),
            user_role=current_user.get("role"),
            resource_type="vat_liability",
            details={"country_code": country_code},
        )
        return result
    _s14.get("/vat-liability")(vat_liability)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route vat_liability: %s", _e)

try:
    def     supplier_payables(
        country_code: str = None,
        current_user: dict = Depends(get_current_user),
        db: Session = Depends(get_db),
    ):
        result = get_supplier_payables(db, country_code)
        audit_log(
            db=db,
            action=AuditAction.FINANCIAL_REPORT_GENERATED,
            user_id=current_user.get("id"),
            username=current_user.get("username"),
            user_role=current_user.get("role"),
            resource_type="supplier_payables",
            details={"country_code": country_code},
        )
        return result
    _s14.get("/supplier-payables")(supplier_payables)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route supplier_payables: %s", _e)

_s18 = APIRouter(prefix='/api/v1/admin')

try:
    def get_engine(db: Session = Depends(get_db)) -> TreasuryEngine:
        return TreasuryEngine(db)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route: %s", _e)

try:
    def require_treasury_access(current_user: dict = Depends(get_current_user)) -> dict:
        if current_user.get("role", "").lower() not in TREASURY_ROLES:
            raise HTTPException(status_code=403, detail="Treasury access required")
        return current_user
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route: %s", _e)

try:
    def     admin_treasury_root(
        db: Session = Depends(get_db),
        current_user: dict = Depends(require_treasury_access),
    ):
        """Treasury root — summary stats (bare /admin/treasury)."""
        total_entries = db.query(JournalEntry).count() or 0
        total_accounts = db.query(Account).count() or 0
        total_cash = db.execute(
            select(func.coalesce(func.sum(AccountBalance.balance), 0))
        ).scalar() or Decimal("0")
        return {
            "total_entries": total_entries,
            "total_accounts": total_accounts,
            "total_cash": float(total_cash),
            "metrics_available_at": "/admin/treasury/metrics",
            "ledger_available_at": "/admin/treasury/ledger",
        }
    _s18.get("/")(admin_treasury_root)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route admin_treasury_root: %s", _e)

try:
    def     admin_treasury_metrics(
        db: Session = Depends(get_db),
        current_user: dict = Depends(require_treasury_access),
    ):
        total_debits = db.execute(
            select(func.coalesce(func.sum(JournalEntryLine.amount), 0))
            .where(JournalEntryLine.side == "debit")
        ).scalar() or Decimal("0")

        total_credits = db.execute(
            select(func.coalesce(func.sum(JournalEntryLine.amount), 0))
            .where(JournalEntryLine.side == "credit")
        ).scalar() or Decimal("0")

        total_entries = db.query(JournalEntry).count()

        return {
            "total_credits": float(total_credits),
            "total_debits": float(total_debits),
            "net_balance": float(total_credits - total_debits),
            "total_entries": total_entries,
        }
    _s18.get("/metrics")(admin_treasury_metrics)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route admin_treasury_metrics: %s", _e)

try:
    def     admin_treasury_ledger(
        start_date: date = Query(...),
        end_date: date = Query(...),
        limit: int = Query(DEFAULT_PAGE_SIZE),
        db: Session = Depends(get_db),
        current_user: dict = Depends(require_treasury_access),
    ):
        entries = db.execute(
            select(JournalEntry)
            .where(JournalEntry.entry_date >= start_date, JournalEntry.entry_date <= end_date)
            .options(joinedload(JournalEntry.lines))
            .order_by(JournalEntry.entry_date.desc())
            .limit(min(limit, MAX_PAGE_SIZE))
        ).unique().scalars().all()

        result = []
        for e in entries:
            total_debit = sum(
                float(line.amount) for line in e.lines if line.side == "debit"
            )
            total_credit = sum(
                float(line.amount) for line in e.lines if line.side == "credit"
            )
            result.append({
                "id": e.id,
                "reference_number": getattr(e, "reference_number", ""),
                "entry_date": e.entry_date.isoformat() if hasattr(e, "entry_date") and e.entry_date else "",
                "description": e.description or "",
                "source": e.source or "",
                "total_debit": total_debit,
                "total_credit": total_credit,
            })
        return result
    _s18.get("/ledger")(admin_treasury_ledger)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route admin_treasury_ledger: %s", _e)

try:
    def     admin_trial_balance(
        as_of_date: Optional[str] = Query(None),
        country_code: Optional[str] = Query(None),
        db: Session = Depends(get_db),
        current_user: dict = Depends(require_treasury_access),
    ):
        engine = TreasuryEngine(db)
        rows = engine.get_trial_balance()
        return rows
    _s18.get("/reports/trial-balance")(admin_trial_balance)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route admin_trial_balance: %s", _e)

try:
    def     admin_cash_position(
        db: Session = Depends(get_db),
        current_user: dict = Depends(require_treasury_access),
    ):
        accounts = db.execute(
            select(TreasuryAccount).where(TreasuryAccount.is_active == True)
        ).scalars().all()

        return [
            {
                "account_name": a.name,
                "balance": float(a.balance),
                "gl_code": a.gl_account_code or a.slug,
            }
            for a in accounts
        ]
    _s18.get("/cash-position")(admin_cash_position)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route admin_cash_position: %s", _e)

try:
    def     admin_payout_batches(
        db: Session = Depends(get_db),
        current_user: dict = Depends(require_treasury_access),
    ):
        batches = db.execute(
            select(PayoutBatch)
            .options(joinedload(PayoutBatch.creator), joinedload(PayoutBatch.approver))
            .order_by(PayoutBatch.created_at.desc())
            .limit(MAX_PAGE_SIZE)
        ).unique().scalars().all()

        return [
            {
                "id": b.id,
                "batch_number": b.batch_number,
                "country_code": b.country_code,
                "total_amount": float(b.total_amount),
                "status": b.status,
                "created_at": b.created_at.isoformat(),
                "created_by": b.created_by,
                "created_by_name": b.creator.full_name if b.creator else None,
                "approved_by": b.approved_by,
                "approved_by_name": b.approver.full_name if b.approver else None,
            }
            for b in batches
        ]
    _s18.get("/payouts/batches")(admin_payout_batches)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route admin_payout_batches: %s", _e)

try:
    def     admin_generate_payout_batch(
        country_code: str = FastAPIBody(...),
        cutoff_date: date = FastAPIBody(...),
        db: Session = Depends(get_db),
        current_user: dict = Depends(require_treasury_access),
    ):
        from domains.finance.models.payments import Payout
        from domains.comms.models.suppliers import SupplierProfile

        pending_payouts = db.execute(
            select(Payout).where(
                Payout.country_code == country_code,
                Payout.status == "pending",
                Payout.created_at <= cutoff_date,
            )
        ).scalars().all()

        if not pending_payouts:
            raise HTTPException(status_code=404, detail="No pending payouts found for the given criteria")

        total = sum(p.amount for p in pending_payouts)
        batch = PayoutBatch(
            batch_number=f"PB-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            country_code=country_code,
            total_amount=total,
            item_count=len(pending_payouts),
            status="draft",
            created_by=current_user.get("id"),
        )
        db.add(batch)
        db.flush()

        for payout in pending_payouts:
            item = PayoutBatchItem(
                batch_id=batch.id,
                entity_type="payout",
                entity_id=payout.id,
                amount=payout.amount,
                reference=getattr(payout, "reference_number", None),
            )
            db.add(item)
            payout.status = "batched"
        db.commit()
        db.refresh(batch)

        return {
            "id": batch.id,
            "batch_number": batch.batch_number,
            "country_code": batch.country_code,
            "total_amount": float(batch.total_amount),
            "item_count": batch.item_count,
            "status": batch.status,
        }
    _s18.post("/payouts/batches/generate")(admin_generate_payout_batch)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route admin_generate_payout_batch: %s", _e)

try:
    def     admin_approve_payout_batch(
        batch_id: int = Path(...),
        db: Session = Depends(get_db),
        current_user: dict = Depends(require_treasury_access),
    ):
        batch = db.execute(
            select(PayoutBatch).where(PayoutBatch.id == batch_id).with_for_update()
        ).scalar_one_or_none()

        if not batch:
            raise HTTPException(status_code=404, detail="Batch not found")
        if batch.status != "draft":
            raise HTTPException(status_code=400, detail=f"Batch is already {batch.status}")
        if batch.created_by == current_user.get("id"):
            raise HTTPException(status_code=403, detail="Maker-Checker: cannot approve your own batch")

        batch.status = "approved"
        batch.approved_by = current_user.get("id")
        db.commit()

        return {"status": "approved", "batch_id": batch.id, "batch_number": batch.batch_number}
    _s18.post("/payouts/batches/{batch_id}/approve")(admin_approve_payout_batch)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route admin_approve_payout_batch: %s", _e)

try:
    def     admin_dispatch_payout_batch(
        batch_id: int = Path(...),
        db: Session = Depends(get_db),
        current_user: dict = Depends(require_treasury_access),
    ):
        batch = db.execute(
            select(PayoutBatch).where(PayoutBatch.id == batch_id).with_for_update()
        ).scalar_one_or_none()

        if not batch:
            raise HTTPException(status_code=404, detail="Batch not found")
        if batch.status != "approved":
            raise HTTPException(status_code=400, detail=f"Batch must be approved first, current status: {batch.status}")

        engine = TreasuryEngine(db)
        entry = engine.post_journal_entry(
            lines=[
                {"account_code": PAYABLES_ACCOUNT, "debit": float(batch.total_amount), "description": f"Payout batch {batch.batch_number}"},
                {"account_code": CASH_ACCOUNT, "credit": float(batch.total_amount), "description": f"Payout batch {batch.batch_number}"},
            ],
            description=f"Dispatch payout batch {batch.batch_number}",
            source="payout_dispatch",
            country_code=batch.country_code,
            created_by=current_user.get("id"),
        )

        batch.status = "dispatched"
        batch.dispatched_at = datetime.utcnow()
        db.commit()

        return {
            "status": "dispatched",
            "batch_id": batch.id,
            "batch_number": batch.batch_number,
            "journal_entry_id": entry.id,
            "reference_number": entry.reference_number,
        }
    _s18.post("/payouts/batches/{batch_id}/dispatch")(admin_dispatch_payout_batch)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route admin_dispatch_payout_batch: %s", _e)

try:
    def     admin_vat_liability(
        country_code: Optional[str] = Query(None),
        period: str = Query("current"),
        db: Session = Depends(get_db),
        current_user: dict = Depends(require_treasury_access),
    ):
        output_vat = db.execute(
            select(func.coalesce(func.sum(AccountBalance.balance), 0))
            .join(Account, AccountBalance.account_id == Account.id)
            .where(Account.code == OUTPUT_VAT_ACCOUNT)
        ).scalar() or Decimal("0")

        input_vat = db.execute(
            select(func.coalesce(func.sum(AccountBalance.balance), 0))
            .join(Account, AccountBalance.account_id == Account.id)
            .where(Account.code == INPUT_VAT_ACCOUNT)
        ).scalar() or Decimal("0")

        return {
            "output_vat": float(output_vat),
            "input_vat": float(input_vat),
            "net_vat_due": float(output_vat - input_vat),
            "country_code": country_code,
            "period": period,
        }
    _s18.get("/reports/vat-liability")(admin_vat_liability)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route admin_vat_liability: %s", _e)

try:
    def     admin_cod_remittances(
        status: Optional[str] = Query(None),
        db: Session = Depends(get_db),
        current_user: dict = Depends(require_treasury_access),
    ):
        from domains.logistics.models.logistics import LogisticsPartner

        query = (
            select(LogisticsCODRemittanceReceipt, LogisticsPartner.name)
            .outerjoin(LogisticsPartner, LogisticsCODRemittanceReceipt.partner_id == LogisticsPartner.id)
        )
        if status:
            query = query.where(LogisticsCODRemittanceReceipt.status == status)
        query = query.order_by(LogisticsCODRemittanceReceipt.created_at.desc()).limit(MAX_PAGE_SIZE)

        rows = db.execute(query).all()

        return [
            {
                "id": r.id,
                "logistics_partner_id": r.partner_id,
                "logistics_partner_name": partner_name or "Unknown",
                "amount_remitted": float(r.amount or 0),
                "amount_expected": float(r.amount or 0),
                "status": r.status,
                "remitted_at": r.created_at.isoformat() if r.created_at else None,
                "bank_reference": None,
                "proof_url": None,
            }
            for r, partner_name in rows
        ]
    _s18.get("/cod-remittances")(admin_cod_remittances)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route admin_cod_remittances: %s", _e)

try:
    def     admin_gateway_summary(
        db: Session = Depends(get_db),
        current_user: dict = Depends(require_treasury_access),
    ):
        schedules = db.execute(
            select(GatewaySettlementSchedule)
            .order_by(GatewaySettlementSchedule.settlement_date.desc())
            .limit(100)
        ).scalars().all()

        from collections import defaultdict
        by_gateway = defaultdict(lambda: {"total_settled": 0, "total_expected": 0, "count": 0, "last_date": None})

        for s in schedules:
            key = str(s.gateway_id)
            by_gateway[key]["total_expected"] += float(s.amount or 0)
            by_gateway[key]["count"] += 1
            if s.status == "settled":
                by_gateway[key]["total_settled"] += float(s.amount or 0)
            if not by_gateway[key]["last_date"] or (s.settlement_date and s.settlement_date > by_gateway[key]["last_date"]):
                by_gateway[key]["last_date"] = s.settlement_date

        return [
            {
                "gateway_code": gid,
                "total_settled": data["total_settled"],
                "total_expected": data["total_expected"],
                "discrepancy": data["total_expected"] - data["total_settled"],
                "count": data["count"],
                "last_settlement_date": data["last_date"].isoformat() if data["last_date"] else None,
            }
            for gid, data in by_gateway.items()
        ]
    _s18.get("/reconciliation/gateway-summary")(admin_gateway_summary)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route admin_gateway_summary: %s", _e)

try:
    def     admin_snapshot_cash_position(
        db: Session = Depends(get_db),
        current_user: dict = Depends(require_treasury_access),
    ):
        accounts = db.execute(
            select(TreasuryAccount).where(TreasuryAccount.is_active == True)
        ).scalars().all()

        now = datetime.utcnow()
        for a in accounts:
            snap = CashPositionSnapshot(
                snapshot_time=now,
                account_id=a.id,
                balance=a.balance,
                currency=a.currency or "USD",
            )
            db.add(snap)
        db.commit()

        return {"status": "snapshot_recorded", "accounts_snapshotted": len(accounts)}
    _s18.post("/cash-position/snapshot")(admin_snapshot_cash_position)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route admin_snapshot_cash_position: %s", _e)

try:
    def     admin_cash_forecasts(
        db: Session = Depends(get_db),
        current_user: dict = Depends(require_treasury_access),
    ):
        forecasts = db.execute(
            select(CashFlowForecast).order_by(CashFlowForecast.forecast_date.desc()).limit(12)
        ).scalars().all()

        return [
            {
                "id": f.id,
                "forecast_date": f.forecast_date.isoformat(),
                "period_start": f.period_start.isoformat(),
                "period_end": f.period_end.isoformat(),
                "net_cash_flow": float(f.net_cash_flow),
                "opening_balance": float(f.opening_balance),
                "closing_balance": float(f.closing_balance),
            }
            for f in forecasts
        ]
    _s18.get("/forecasts")(admin_cash_forecasts)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route admin_cash_forecasts: %s", _e)

try:
    def     consolidated_treasury_metrics(
        db: Session = Depends(get_db),
        current_user: dict = Depends(require_treasury_access),
    ):
        total_accounts = db.query(TreasuryAccount).count()
        total_je = db.query(JournalEntry).count()
        total_batches = db.query(PayoutBatch).count()
        total_invoices = db.query(Invoice).count()
        return {
            "total_accounts": total_accounts,
            "total_journal_entries": total_je,
            "total_payout_batches": total_batches,
            "total_invoices": total_invoices,
        }
    _s18.get("/consolidated/metrics")(consolidated_treasury_metrics)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route consolidated_treasury_metrics: %s", _e)

try:
    def     consolidated_treasury_ledger(
        limit: int = Query(50, ge=1, le=500),
        db: Session = Depends(get_db),
        current_user: dict = Depends(require_treasury_access),
    ):
        entries = db.query(JournalEntry).order_by(JournalEntry.created_at.desc()).limit(limit).all()
        return [
            {
                "id": e.id,
                "description": e.description,
                "entry_type": e.entry_type,
                "amount": float(e.amount),
                "status": e.status,
                "created_at": e.created_at.isoformat(),
            }
            for e in entries
        ]
    _s18.get("/consolidated/ledger")(consolidated_treasury_ledger)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route consolidated_treasury_ledger: %s", _e)

try:
    def     consolidated_trial_balance(
        db: Session = Depends(get_db),
        current_user: dict = Depends(require_treasury_access),
        page: int = Query(1, ge=1),
        page_size: int = Query(20, ge=1, le=100),
    ):
        query = db.query(Account).filter(Account.is_active == True)
        total = query.count()
        accounts = query.order_by(Account.code).offset((page - 1) * page_size).limit(page_size).all()
        return {
            "data": [
                {
                    "id": a.id,
                    "code": a.code,
                    "name": a.name,
                    "normal_side": a.normal_side,
                    "total_debits": float(db.query(func.coalesce(func.sum(JournalEntryLine.amount), 0)).filter(JournalEntryLine.account_id == a.id, JournalEntryLine.side == "debit").scalar() or 0),
                    "total_credits": float(db.query(func.coalesce(func.sum(JournalEntryLine.amount), 0)).filter(JournalEntryLine.account_id == a.id, JournalEntryLine.side == "credit").scalar() or 0),
                }
                for a in accounts
            ],
            "total": total,
            "page": page,
            "page_size": page_size,
        }
    _s18.get("/consolidated/reports/trial-balance")(consolidated_trial_balance)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route consolidated_trial_balance: %s", _e)

try:
    def     consolidated_cash_position(
        db: Session = Depends(get_db),
        current_user: dict = Depends(require_treasury_access),
        page: int = Query(1, ge=1),
        page_size: int = Query(20, ge=1, le=100),
    ):
        query = db.query(TreasuryAccount).filter(TreasuryAccount.is_active == True)
        total = query.count()
        accounts = query.offset((page - 1) * page_size).limit(page_size).all()
        total_balance = float(db.query(func.coalesce(func.sum(TreasuryAccount.balance), 0)).filter(TreasuryAccount.is_active == True).scalar() or 0)
        return {
            "accounts": [
                {
                    "id": a.id,
                    "name": a.name,
                    "balance": float(a.balance or 0),
                    "currency": a.currency or "USD",
                }
                for a in accounts
            ],
            "total_balance": total_balance,
            "total": total,
            "page": page,
            "page_size": page_size,
        }
    _s18.get("/consolidated/cash-position")(consolidated_cash_position)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route consolidated_cash_position: %s", _e)

try:
    def     consolidated_payout_batches(
        limit: int = Query(50, ge=1, le=200),
        db: Session = Depends(get_db),
        current_user: dict = Depends(require_treasury_access),
    ):
        batches = db.query(PayoutBatch).order_by(PayoutBatch.created_at.desc()).limit(limit).all()
        return [
            {
                "id": b.id,
                "batch_ref": b.batch_number,
                "status": b.status,
                "total_amount": float(b.total_amount or 0),
                "item_count": b.item_count,
                "country_code": b.country_code,
                "created_at": b.created_at.isoformat(),
            }
            for b in batches
        ]
    _s18.get("/consolidated/payouts/batches")(consolidated_payout_batches)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route consolidated_payout_batches: %s", _e)

try:
    def     consolidated_vat_liability(
        db: Session = Depends(get_db),
        current_user: dict = Depends(require_treasury_access),
    ):
        vats = db.query(VATRemittance).order_by(VATRemittance.period_start.desc()).limit(12).all()
        return [
            {
                "id": v.id,
                "country_code": v.country_code,
                "period_start": v.period_start.isoformat(),
                "period_end": v.period_end.isoformat(),
                "total_collected": float(v.vat_collected_amount or 0),
                "total_deducted": float(v.vat_adjustment_amount or 0),
                "net_due": float(v.amount_due or 0),
                "status": v.status,
            }
            for v in vats
        ]
    _s18.get("/consolidated/reports/vat-liability")(consolidated_vat_liability)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route consolidated_vat_liability: %s", _e)

try:
    def     consolidated_cod_remittances(
        limit: int = Query(50, ge=1, le=200),
        db: Session = Depends(get_db),
        current_user: dict = Depends(require_treasury_access),
    ):
        from domains.logistics.models.logistics import Shipment as ShipmentModel
        receipts = db.query(LogisticsCODRemittanceReceipt).order_by(LogisticsCODRemittanceReceipt.created_at.desc()).limit(limit).all()
        return [
            {
                "id": r.id,
                "shipment_id": r.shipment_id,
                "order_id": (db.query(ShipmentModel.order_id).filter(ShipmentModel.id == r.shipment_id).scalar() if r.shipment_id else None),
                "partner_id": r.partner_id,
                "amount": float(r.amount),
                "bank_reference": r.bank_reference,
                "status": r.status,
                "country_code": r.country_code,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in receipts
        ]
    _s18.get("/consolidated/cod-remittances")(consolidated_cod_remittances)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route consolidated_cod_remittances: %s", _e)

try:
    def     consolidated_gateway_summary(
        db: Session = Depends(get_db),
        current_user: dict = Depends(require_treasury_access),
    ):
        schedules = db.query(GatewaySettlementSchedule).order_by(GatewaySettlementSchedule.settlement_date.desc()).limit(12).all()
        return [
            {
                "id": s.id,
                "gateway": s.gateway_id,
                "settlement_date": s.settlement_date.isoformat() if s.settlement_date else None,
                "amount": float(s.amount or 0),
                "currency": s.currency,
                "status": s.status,
            }
            for s in schedules
        ]
    _s18.get("/consolidated/reconciliation/gateway-summary")(consolidated_gateway_summary)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route consolidated_gateway_summary: %s", _e)

try:
    def     consolidated_cash_forecasts(
        db: Session = Depends(get_db),
        current_user: dict = Depends(require_treasury_access),
    ):
        forecasts = db.execute(
            select(CashFlowForecast).order_by(CashFlowForecast.forecast_date.desc()).limit(12)
        ).scalars().all()
        return [
            {
                "id": f.id,
                "forecast_date": f.forecast_date.isoformat(),
                "period_start": f.period_start.isoformat(),
                "period_end": f.period_end.isoformat(),
                "net_cash_flow": float(f.net_cash_flow),
                "opening_balance": float(f.opening_balance),
                "closing_balance": float(f.closing_balance),
            }
            for f in forecasts
        ]
    _s18.get("/consolidated/forecasts")(consolidated_cash_forecasts)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route consolidated_cash_forecasts: %s", _e)

try:
    def     consolidated_reconciliation_pipeline(
        limit: int = Query(50, ge=1, le=200),
        db: Session = Depends(get_db),
        current_user: dict = Depends(require_treasury_access),
    ):
        from domains.orders.models.orders import Order as OrderModel
        from domains.finance.models.payments import Payment as PaymentModel
        from domains.finance.models.payments import Payout

        pipeline = []
        orders = db.query(OrderModel).filter(
            OrderModel.status.in_(["shipped", "delivered", "completed", "dispatched"])
        ).order_by(OrderModel.updated_at.desc()).limit(limit).all()

        for order in orders:
            payment = db.query(PaymentModel).filter(PaymentModel.order_id == order.id).first()
            settlement = db.query(SupplierSettlement).filter(SupplierSettlement.order_id == order.id).first()
            payout = db.query(Payout).filter(Payout.id == settlement.payout_id).first() if (settlement and settlement.payout_id) else None

            pipeline.append({
                "order_id": order.id,
                "order_status": order.status,
                "order_total": float(getattr(order, "total_amount", None) or getattr(order, "total", 0) or 0),
                "country_code": order.country_code or "",
                "payment_method": payment.payment_method if payment else None,
                "payment_status": payment.status if payment else None,
                "supplier_settlement_status": settlement.status if settlement else None,
                "supplier_payout_status": payout.status if payout else None,
                "stage": _resolve_stage(order, payment, None, settlement, payout),
            })

        return {"pipeline": pipeline, "total": len(pipeline), "consolidated": True}
    _s18.get("/consolidated/reconciliation/pipeline")(consolidated_reconciliation_pipeline)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route consolidated_reconciliation_pipeline: %s", _e)

try:
    def     country_treasury_metrics(
        country_code: str = Path(..., description="ISO country code"),
        db: Session = Depends(get_db),
        current_user: dict = Depends(require_treasury_access),
    ):
        cc = country_code.upper()
        total_debits = db.execute(
            select(func.coalesce(func.sum(JournalEntryLine.amount), 0))
            .join(JournalEntry, JournalEntryLine.entry_id == JournalEntry.id)
            .where(JournalEntryLine.side == "debit", JournalEntry.country_code == cc)
        ).scalar() or Decimal("0")
        total_credits = db.execute(
            select(func.coalesce(func.sum(JournalEntryLine.amount), 0))
            .join(JournalEntry, JournalEntryLine.entry_id == JournalEntry.id)
            .where(JournalEntryLine.side == "credit", JournalEntry.country_code == cc)
        ).scalar() or Decimal("0")
        total_entries = db.query(JournalEntry).filter(JournalEntry.country_code == cc).count()
        return {
            "total_credits": float(total_credits),
            "total_debits": float(total_debits),
            "net_balance": float(total_credits - total_debits),
            "total_entries": total_entries,
            "country_code": cc,
        }
    _s18.get("/{country_code}/metrics")(country_treasury_metrics)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route country_treasury_metrics: %s", _e)

try:
    def     country_treasury_ledger(
        country_code: str = Path(..., description="ISO country code"),
        start_date: date = Query(...),
        end_date: date = Query(...),
        limit: int = Query(50),
        db: Session = Depends(get_db),
        current_user: dict = Depends(require_treasury_access),
    ):
        cc = country_code.upper()
        entries = db.execute(
            select(JournalEntry)
            .where(
                JournalEntry.entry_date >= start_date,
                JournalEntry.entry_date <= end_date,
                JournalEntry.country_code == cc,
            )
            .options(joinedload(JournalEntry.lines))
            .order_by(JournalEntry.entry_date.desc())
            .limit(limit)
        ).unique().scalars().all()
        result = []
        for e in entries:
            result.append({
                "id": e.id,
                "reference_number": getattr(e, "reference_number", ""),
                "entry_date": e.entry_date.isoformat() if hasattr(e, "entry_date") and e.entry_date else "",
                "description": e.description or "",
                "source": e.source or "",
                "total_debit": sum(float(line.amount) for line in e.lines if line.side == "debit"),
                "total_credit": sum(float(line.amount) for line in e.lines if line.side == "credit"),
            })
        return result
    _s18.get("/{country_code}/ledger")(country_treasury_ledger)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route country_treasury_ledger: %s", _e)

try:
    def     country_trial_balance(
        country_code: str = Path(..., description="ISO country code"),
        as_of_date: Optional[str] = Query(None),
        db: Session = Depends(get_db),
        current_user: dict = Depends(require_treasury_access),
    ):
        engine = TreasuryEngine(db)
        return engine.get_trial_balance()
    _s18.get("/{country_code}/reports/trial-balance")(country_trial_balance)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route country_trial_balance: %s", _e)

try:
    def     country_cash_position(
        country_code: str = Path(..., description="ISO country code"),
        db: Session = Depends(get_db),
        current_user: dict = Depends(require_treasury_access),
    ):
        cc = country_code.upper()
        accounts = db.execute(
            select(TreasuryAccount).where(TreasuryAccount.is_active == True, TreasuryAccount.country_code == cc)
        ).scalars().all()
        if not accounts:
            accounts = db.execute(
                select(TreasuryAccount).where(TreasuryAccount.is_active == True, TreasuryAccount.country_code.is_(None))
            ).scalars().all()
        return [
            {"account_name": a.name, "balance": float(a.balance), "gl_code": a.gl_account_code or a.slug}
            for a in accounts
        ]
    _s18.get("/{country_code}/cash-position")(country_cash_position)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route country_cash_position: %s", _e)

try:
    def     country_payout_batches(
        country_code: str = Path(..., description="ISO country code"),
        db: Session = Depends(get_db),
        current_user: dict = Depends(require_treasury_access),
    ):
        cc = country_code.upper()
        batches = db.execute(
            select(PayoutBatch)
            .options(joinedload(PayoutBatch.creator), joinedload(PayoutBatch.approver))
            .where(PayoutBatch.country_code == cc)
            .order_by(PayoutBatch.created_at.desc())
            .limit(100)
        ).unique().scalars().all()
        return [
            {
                "id": b.id,
                "batch_number": b.batch_number,
                "country_code": b.country_code,
                "total_amount": float(b.total_amount),
                "status": b.status,
                "created_at": b.created_at.isoformat(),
                "created_by": b.created_by,
                "created_by_name": b.creator.full_name if b.creator else None,
                "approved_by": b.approved_by,
                "approved_by_name": b.approver.full_name if b.approver else None,
            }
            for b in batches
        ]
    _s18.get("/{country_code}/payouts/batches")(country_payout_batches)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route country_payout_batches: %s", _e)

try:
    def     country_vat_liability(
        country_code: str = Path(..., description="ISO country code"),
        period: str = Query("current"),
        db: Session = Depends(get_db),
        current_user: dict = Depends(require_treasury_access),
    ):
        output_vat = db.execute(
            select(func.coalesce(func.sum(AccountBalance.balance), 0))
            .join(Account, AccountBalance.account_id == Account.id)
            .where(Account.code == OUTPUT_VAT_ACCOUNT)
        ).scalar() or Decimal("0")
        input_vat = db.execute(
            select(func.coalesce(func.sum(AccountBalance.balance), 0))
            .join(Account, AccountBalance.account_id == Account.id)
            .where(Account.code == INPUT_VAT_ACCOUNT)
        ).scalar() or Decimal("0")
        return {
            "output_vat": float(output_vat),
            "input_vat": float(input_vat),
            "net_vat_due": float(output_vat - input_vat),
            "country_code": country_code.upper(),
            "period": period,
        }
    _s18.get("/{country_code}/reports/vat-liability")(country_vat_liability)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route country_vat_liability: %s", _e)

try:
    def     country_cod_remittances(
        country_code: str = Path(..., description="ISO country code"),
        status: Optional[str] = Query(None),
        db: Session = Depends(get_db),
        current_user: dict = Depends(require_treasury_access),
    ):
        from domains.logistics.models.logistics import LogisticsPartner

        cc = country_code.upper()
        query = (
            select(LogisticsCODRemittanceReceipt, LogisticsPartner.name)
            .outerjoin(LogisticsPartner, LogisticsCODRemittanceReceipt.partner_id == LogisticsPartner.id)
            .where(LogisticsCODRemittanceReceipt.country_code == cc)
        )
        if status:
            query = query.where(LogisticsCODRemittanceReceipt.status == status)
        query = query.order_by(LogisticsCODRemittanceReceipt.created_at.desc()).limit(100)
        rows = db.execute(query).all()
        return [
            {
                "id": r.id,
                "logistics_partner_id": r.partner_id,
                "logistics_partner_name": partner_name or "Unknown",
                "amount_remitted": float(r.amount or 0),
                "amount_expected": float(r.amount or 0),
                "status": r.status,
                "remitted_at": r.created_at.isoformat() if r.created_at else None,
                "bank_reference": None,
                "proof_url": None,
            }
            for r, partner_name in rows
        ]
    _s18.get("/{country_code}/cod-remittances")(country_cod_remittances)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route country_cod_remittances: %s", _e)

try:
    def     country_gateway_summary(
        country_code: str = Path(..., description="ISO country code"),
        db: Session = Depends(get_db),
        current_user: dict = Depends(require_treasury_access),
    ):
        cc = country_code.upper()
        schedules = db.execute(
            select(GatewaySettlementSchedule)
            .where(GatewaySettlementSchedule.country_code == cc)
            .order_by(GatewaySettlementSchedule.settlement_date.desc())
            .limit(100)
        ).scalars().all()

        from collections import defaultdict
        by_gateway = defaultdict(lambda: {"total_settled": 0, "total_expected": 0, "count": 0, "last_date": None})

        for s in schedules:
            key = str(s.gateway_id)
            by_gateway[key]["total_expected"] += float(s.amount or 0)
            by_gateway[key]["count"] += 1
            if s.status == "settled":
                by_gateway[key]["total_settled"] += float(s.amount or 0)
            if not by_gateway[key]["last_date"] or (s.settlement_date and s.settlement_date > by_gateway[key]["last_date"]):
                by_gateway[key]["last_date"] = s.settlement_date

        return [
            {
                "gateway_code": gid,
                "total_settled": data["total_settled"],
                "total_expected": data["total_expected"],
                "discrepancy": data["total_expected"] - data["total_settled"],
                "count": data["count"],
                "last_settlement_date": data["last_date"].isoformat() if data["last_date"] else None,
            }
            for gid, data in by_gateway.items()
        ]
    _s18.get("/{country_code}/reconciliation/gateway-summary")(country_gateway_summary)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route country_gateway_summary: %s", _e)

try:
    def     admin_reconciliation_pipeline(
        country_code: str = Path(..., description="ISO country code"),
        status: Optional[str] = Query(None),
        limit: int = Query(50, ge=1, le=200),
        db: Session = Depends(get_db),
        current_user: dict = Depends(require_treasury_access),
    ):
        get_country_or_404(country_code.upper(), db)
        set_rls_context({country_code.upper()}, is_restricted=True)
        cc = country_code.upper()
        try:
            from domains.orders.models.orders import Order as OrderModel
            from domains.orders.models.orders import OrderItem
            from domains.finance.models.payments import Payment as PaymentModel
            from domains.finance.models.payments import Payout
            from domains.logistics.models.logistics import LogisticsPartner
            from domains.governance.models.admin import LogisticsCODRemittanceReceipt
            from domains.finance.services.finance_service import get_effective_rate

            pipeline = []
            orders = db.query(OrderModel).filter(
                OrderModel.country_code == cc,
                OrderModel.status.in_(["shipped", "delivered", "completed", "dispatched"])
            ).order_by(OrderModel.updated_at.desc()).limit(limit).all()

            for order in orders:
                order_total = float(getattr(order, "total_amount", None) or getattr(order, "total", 0) or 0)
                payment = db.query(PaymentModel).filter(
                    PaymentModel.order_id == order.id
                ).first()

                from domains.logistics.models.logistics import Shipment
                shipment = db.query(Shipment).filter(
                    Shipment.order_id == order.id
                ).first()

                logistics_partner_name = None
                if shipment and shipment.carrier_name:
                    logistics_partner_name = shipment.carrier_name

                cod_receipt = None
                if payment and payment.payment_method == "cod":
                    cod_receipt = db.query(LogisticsCODRemittanceReceipt).filter(
                        LogisticsCODRemittanceReceipt.order_id == order.id
                    ).first()

                settlement = db.query(SupplierSettlement).filter(
                    SupplierSettlement.order_id == order.id
                ).first()

                payout = None
                if settlement:
                    payout = db.query(Payout).filter(
                        Payout.id == settlement.payout_id
                    ).first() if settlement.payout_id else None

                supplier_id = None
                first_item = db.query(OrderItem).filter(OrderItem.order_id == order.id).first()
                if first_item:
                    supplier_id = first_item.supplier_id

                commission_preview = None
                if supplier_id:
                    try:
                        rate = get_effective_rate(supplier_id=supplier_id, product_id=None, db=db)
                        commission_preview = {
                            "rate": float(rate.applied_rate),
                            "amount": float(rate.applied_rate) * order_total if hasattr(rate, 'applied_rate') else 0,
                        }
                    except Exception:
                        pass

                pipeline.append({
                    "order_id": order.id,
                    "order_status": order.status,
                    "order_total": order_total,
                    "supplier_id": supplier_id,
                    "payment_method": payment.payment_method if payment else None,
                    "payment_status": payment.status if payment else None,
                    "payment_amount": float(payment.amount) if payment else None,
                    "logistics_partner": logistics_partner_name,
                    "cod_remitted": float(cod_receipt.amount) if cod_receipt else None,
                    "cod_remittance_status": cod_receipt.status if cod_receipt else None,
                    "supplier_settlement_status": settlement.status if settlement else None,
                    "supplier_settlement_id": settlement.id if settlement else None,
                    "supplier_net_amount": float(settlement.net_amount) if settlement else None,
                    "supplier_payout_status": payout.status if payout else None,
                    "supplier_payout_amount": float(payout.amount) if payout else None,
                    "commission": commission_preview,
                    "stage": _resolve_stage(order, payment, cod_receipt, settlement, payout),
                })

            if status == "settled":
                pipeline = [p for p in pipeline if p["supplier_settlement_status"] in ("paid", "settled")]
            elif status == "unsettled":
                pipeline = [p for p in pipeline if not p["supplier_settlement_status"]]

            return {"pipeline": pipeline, "total": len(pipeline), "country_code": cc}
        finally:
            clear_rls_context()
    _s18.get("/{country_code}/reconciliation/pipeline")(admin_reconciliation_pipeline)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route admin_reconciliation_pipeline: %s", _e)

try:
    def _resolve_stage(order, payment, cod_receipt, settlement, payout) -> str:
        if payout and payout.status == "paid":
            return "supplier_paid"
        if settlement and settlement.status in ("paid", "settled"):
            return "supplier_settled"
        if payout and payout.status == "processing":
            return "payout_processing"
        if cod_receipt and cod_receipt.status == "remitted":
            return "cod_remitted"
        if cod_receipt and cod_receipt.status == "pending":
            return "cod_pending"
        if payment and payment.status == "completed":
            return "payment_received"
        if order.status in ("shipped", "delivered", "dispatched"):
            return "order_dispatched"
        return "pending"
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route: %s", _e)

try:
    def     admin_record_cod_remittance(
        country_code: str = Path(..., description="ISO country code"),
        order_id: int = FastAPIBody(...),
        partner_id: int = FastAPIBody(...),
        amount: float = FastAPIBody(...),
        bank_reference: str = FastAPIBody(...),
        db: Session = Depends(get_db),
        current_user: dict = Depends(require_treasury_access),
    ):
        get_country_or_404(country_code.upper(), db)
        set_rls_context({country_code.upper()}, is_restricted=True)
        cc = country_code.upper()
        try:
            from domains.orders.models.orders import Order as OrderModel
            from domains.logistics.models.logistics import Shipment as ShipmentModel
            shipment = db.query(ShipmentModel).filter(ShipmentModel.order_id == order_id).first()
            receipt = LogisticsCODRemittanceReceipt(
                shipment_id=shipment.id if shipment else None,
                partner_id=partner_id,
                amount=amount,
                bank_reference=bank_reference,
                status="remitted",
                country_code=cc,
            )
            db.add(receipt)
            db.flush()
            order = db.query(OrderModel).filter(OrderModel.id == order_id).first()
            if order:
                setattr(order, "settlement_status", "cod_remitted")
            db.commit()
            db.refresh(receipt)
            # Keep the double-entry ledger in sync with the reconciliation engine.
            try:
                from domains.finance.services.ledger.general_ledger_service import post_logistics_cod_remittance_journal
                post_logistics_cod_remittance_journal(db, receipt.id, Decimal(str(amount)), country_code=cc)
            except Exception as gl_err:
                logger.warning(f"COD remittance GL post skipped: {gl_err}")
            return {"status": "ok", "receipt_id": receipt.id, "country_code": cc}
        finally:
            clear_rls_context()
    _s18.post("/{country_code}/reconciliation/record-cod-remittance")(admin_record_cod_remittance)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route admin_record_cod_remittance: %s", _e)

try:
    def     admin_settle_supplier(
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
    ):
        get_country_or_404(country_code.upper(), db)
        set_rls_context({country_code.upper()}, is_restricted=True)
        cc = country_code.upper()
        try:
            from domains.orders.models.orders import Order as OrderModel
            from domains.country.models.countries import CountryConfig
            gross = gross_amount if gross_amount is not None else net_amount
            resolved_currency = currency or "USD"
            ccfg = db.query(CountryConfig).filter(CountryConfig.code == cc).first()
            if ccfg and ccfg.currency:
                resolved_currency = ccfg.currency
            settlement = SupplierSettlement(
                order_id=order_id,
                supplier_id=supplier_id,
                gross_amount=gross,
                commission_amount=commission_amount,
                net_amount=net_amount,
                status="settled",
                payout_id=payout_id,
                currency=resolved_currency,
                country_code=cc,
            )
            db.add(settlement)
            db.flush()
            order = db.query(OrderModel).filter(OrderModel.id == order_id).first()
            if order:
                setattr(order, "settlement_status", "settled")
            db.commit()
            db.refresh(settlement)
            return {"status": "ok", "settlement_id": settlement.id, "country_code": cc}
        finally:
            clear_rls_context()
    _s18.post("/{country_code}/reconciliation/settle-supplier")(admin_settle_supplier)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route admin_settle_supplier: %s", _e)

try:
    def     admin_approve_settlement(
        country_code: str = Path(..., description="ISO country code"),
        settlement_id: int = FastAPIBody(..., embed=True),
        db: Session = Depends(get_db),
        current_user: dict = Depends(require_treasury_access),
    ):
        get_country_or_404(country_code.upper(), db)
        set_rls_context({country_code.upper()}, is_restricted=True)
        try:
            settlement = db.query(SupplierSettlement).filter(
                SupplierSettlement.id == settlement_id,
                SupplierSettlement.country_code == country_code.upper(),
            ).first()
            if not settlement:
                raise HTTPException(status_code=404, detail="Settlement not found")
            settlement.status = "paid"
            db.commit()
            try:
                from domains.finance.services.ledger.general_ledger_service import post_supplier_settlement_journal
                post_supplier_settlement_journal(
                    db,
                    settlement.id,
                    Decimal(str(settlement.net_amount or 0)),
                    supplier_id=settlement.supplier_id,
                    country_code=country_code.upper(),
                )
            except Exception as gl_err:
                logger.warning(f"Supplier settlement GL post skipped: {gl_err}")
            return {"status": "ok", "settlement_id": settlement.id}
        finally:
            clear_rls_context()
    _s18.post("/{country_code}/reconciliation/approve-settlement")(admin_approve_settlement)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route admin_approve_settlement: %s", _e)

try:
    def     admin_gateway_exceptions(
        db: Session = Depends(get_db),
        current_user: dict = Depends(require_treasury_access),
    ):
        issues = db.execute(
            select(GatewaySettlementSchedule).where(
                GatewaySettlementSchedule.status.in_(["pending", "flagged"])
            ).order_by(GatewaySettlementSchedule.settlement_date.desc()).limit(100)
        ).scalars().all()
        return [
            {
                "id": s.id,
                "gateway_id": s.gateway_id,
                "settlement_date": s.settlement_date.isoformat() if s.settlement_date else None,
                "amount": float(s.amount or 0),
                "currency": s.currency,
                "status": s.status,
                "country_code": getattr(s, "country_code", None),
            }
            for s in issues
        ]
    _s18.get("/reconciliation/gateway-exceptions")(admin_gateway_exceptions)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route admin_gateway_exceptions: %s", _e)

try:
    def     country_gateway_exceptions(
        country_code: str = Path(..., description="ISO country code"),
        db: Session = Depends(get_db),
        current_user: dict = Depends(require_treasury_access),
    ):
        get_country_or_404(country_code.upper(), db)
        set_rls_context({country_code.upper()}, is_restricted=True)
        try:
            issues = db.execute(
                select(GatewaySettlementSchedule).where(
                    GatewaySettlementSchedule.status.in_(["pending", "flagged"]),
                    GatewaySettlementSchedule.country_code == country_code.upper(),
                ).order_by(GatewaySettlementSchedule.settlement_date.desc()).limit(100)
            ).scalars().all()
            return [
                {
                    "id": s.id,
                    "gateway_id": s.gateway_id,
                    "settlement_date": s.settlement_date.isoformat() if s.settlement_date else None,
                    "amount": float(s.amount or 0),
                    "currency": s.currency,
                    "status": s.status,
                    "country_code": s.country_code,
                }
                for s in issues
            ]
        finally:
            clear_rls_context()
    _s18.get("/{country_code}/reconciliation/gateway-exceptions")(country_gateway_exceptions)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route country_gateway_exceptions: %s", _e)

try:
    def     admin_payment_transactions(
        start_date: date = Query(...),
        end_date: date = Query(...),
        gateway: Optional[str] = Query(None),
        status: Optional[str] = Query(None),
        db: Session = Depends(get_db),
        current_user: dict = Depends(require_treasury_access),
    ):
        query = (
            select(Payment)
            .where(Payment.created_at >= start_date, Payment.created_at <= end_date)
            .order_by(Payment.created_at.desc())
        )
        if gateway:
            query = query.where(Payment.provider == gateway)
        if status:
            query = query.where(Payment.status == status)
        rows = db.execute(query.limit(200)).scalars().all()
        return [
            {
                "id": p.id,
                "order_id": p.order_id,
                "amount": float(p.amount),
                "payment_method": p.payment_method,
                "provider": p.provider,
                "status": p.status,
                "created_at": p.created_at.isoformat() if p.created_at else None,
                "country_code": p.country_code,
            }
            for p in rows
        ]
    _s18.get("/payments/transactions")(admin_payment_transactions)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route admin_payment_transactions: %s", _e)

try:
    def     country_payment_transactions(
        country_code: str = Path(..., description="ISO country code"),
        start_date: date = Query(...),
        end_date: date = Query(...),
        gateway: Optional[str] = Query(None),
        status: Optional[str] = Query(None),
        db: Session = Depends(get_db),
        current_user: dict = Depends(require_treasury_access),
    ):
        get_country_or_404(country_code.upper(), db)
        set_rls_context({country_code.upper()}, is_restricted=True)
        try:
            query = (
                select(Payment)
                .where(
                    Payment.country_code == country_code.upper(),
                    Payment.created_at >= start_date,
                    Payment.created_at <= end_date,
                )
                .order_by(Payment.created_at.desc())
            )
            if gateway:
                query = query.where(Payment.provider == gateway)
            if status:
                query = query.where(Payment.status == status)
            rows = db.execute(query.limit(200)).scalars().all()
            return [
                {
                    "id": p.id,
                    "order_id": p.order_id,
                    "amount": float(p.amount),
                    "payment_method": p.payment_method,
                    "provider": p.provider,
                    "status": p.status,
                    "created_at": p.created_at.isoformat() if p.created_at else None,
                    "country_code": p.country_code,
                }
                for p in rows
            ]
        finally:
            clear_rls_context()
    _s18.get("/{country_code}/payments/transactions")(country_payment_transactions)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route country_payment_transactions: %s", _e)

try:
    def     admin_supplier_payouts(
        status: Optional[str] = Query(None),
        db: Session = Depends(get_db),
        current_user: dict = Depends(require_treasury_access),
    ):
        from domains.comms.models.suppliers import SupplierProfile
        query = (
            select(Payout, SupplierProfile)
            .outerjoin(SupplierProfile, Payout.supplier_id == SupplierProfile.id)
            .order_by(Payout.created_at.desc())
        )
        if status:
            query = query.where(Payout.status == status)
        rows = db.execute(query.limit(200)).all()
        return [
            {
                "id": p.id,
                "supplier_id": p.supplier_id,
                "supplier_name": s.company_name if s else f"Supplier #{p.supplier_id}",
                "amount": float(p.amount),
                "currency": p.currency,
                "method": p.method,
                "status": p.status,
                "reference": p.reference,
                "created_at": p.created_at.isoformat() if p.created_at else None,
                "country_code": p.country_code,
            }
            for p, s in rows
        ]
    _s18.get("/supplier-payouts")(admin_supplier_payouts)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route admin_supplier_payouts: %s", _e)

try:
    def     country_supplier_payouts(
        country_code: str = Path(..., description="ISO country code"),
        status: Optional[str] = Query(None),
        db: Session = Depends(get_db),
        current_user: dict = Depends(require_treasury_access),
    ):
        get_country_or_404(country_code.upper(), db)
        set_rls_context({country_code.upper()}, is_restricted=True)
        try:
            from domains.comms.models.suppliers import SupplierProfile
            query = (
                select(Payout, SupplierProfile)
                .outerjoin(SupplierProfile, Payout.supplier_id == SupplierProfile.id)
                .where(Payout.country_code == country_code.upper())
                .order_by(Payout.created_at.desc())
            )
            if status:
                query = query.where(Payout.status == status)
            rows = db.execute(query.limit(200)).all()
            return [
                {
                    "id": p.id,
                    "supplier_id": p.supplier_id,
                    "supplier_name": s.company_name if s else f"Supplier #{p.supplier_id}",
                    "amount": float(p.amount),
                    "currency": p.currency,
                    "method": p.method,
                    "status": p.status,
                    "reference": p.reference,
                    "created_at": p.created_at.isoformat() if p.created_at else None,
                    "country_code": p.country_code,
                }
                for p, s in rows
            ]
        finally:
            clear_rls_context()
    _s18.get("/{country_code}/supplier-payouts")(country_supplier_payouts)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route country_supplier_payouts: %s", _e)

try:
    def     admin_logistics_payouts(
        status: Optional[str] = Query(None),
        db: Session = Depends(get_db),
        current_user: dict = Depends(require_treasury_access),
    ):
        query = select(LogisticsPartnerPayout).order_by(LogisticsPartnerPayout.created_at.desc())
        if status:
            query = query.where(LogisticsPartnerPayout.status == status)
        rows = db.execute(query.limit(200)).scalars().all()
        return [
            {
                "id": p.id,
                "partner_id": p.partner_id,
                "amount": float(p.amount),
                "currency": p.currency,
                "status": p.status,
                "reference_id": p.reference_id,
                "period_start": p.period_start.isoformat() if p.period_start else None,
                "period_end": p.period_end.isoformat() if p.period_end else None,
                "created_at": p.created_at.isoformat() if p.created_at else None,
                "country_code": p.country_code,
            }
            for p in rows
        ]
    _s18.get("/logistics-payouts")(admin_logistics_payouts)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route admin_logistics_payouts: %s", _e)

try:
    def     country_logistics_payouts(
        country_code: str = Path(..., description="ISO country code"),
        status: Optional[str] = Query(None),
        db: Session = Depends(get_db),
        current_user: dict = Depends(require_treasury_access),
    ):
        get_country_or_404(country_code.upper(), db)
        set_rls_context({country_code.upper()}, is_restricted=True)
        try:
            query = (
                select(LogisticsPartnerPayout)
                .where(LogisticsPartnerPayout.country_code == country_code.upper())
                .order_by(LogisticsPartnerPayout.created_at.desc())
            )
            if status:
                query = query.where(LogisticsPartnerPayout.status == status)
            rows = db.execute(query.limit(200)).scalars().all()
            return [
                {
                    "id": p.id,
                    "partner_id": p.partner_id,
                    "amount": float(p.amount),
                    "currency": p.currency,
                    "status": p.status,
                    "reference_id": p.reference_id,
                    "period_start": p.period_start.isoformat() if p.period_start else None,
                    "period_end": p.period_end.isoformat() if p.period_end else None,
                    "created_at": p.created_at.isoformat() if p.created_at else None,
                    "country_code": p.country_code,
                }
                for p in rows
            ]
        finally:
            clear_rls_context()
    _s18.get("/{country_code}/logistics-payouts")(country_logistics_payouts)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route country_logistics_payouts: %s", _e)

try:
    def     admin_supplier_earnings(
        db: Session = Depends(get_db),
        current_user: dict = Depends(require_treasury_access),
    ):
        rows = db.execute(
            select(
                SupplierSettlement.supplier_id,
                func.sum(SupplierSettlement.gross_amount).label("gross"),
                func.sum(SupplierSettlement.commission_amount).label("commission"),
                func.sum(SupplierSettlement.net_amount).label("net"),
            ).group_by(SupplierSettlement.supplier_id)
        ).all()
        return [
            {
                "supplier_id": r.supplier_id,
                "gross": float(r.gross or 0),
                "commission": float(r.commission or 0),
                "net": float(r.net or 0),
            }
            for r in rows
        ]
    _s18.get("/reports/supplier-earnings")(admin_supplier_earnings)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route admin_supplier_earnings: %s", _e)

try:
    def     country_supplier_earnings(
        country_code: str = Path(..., description="ISO country code"),
        db: Session = Depends(get_db),
        current_user: dict = Depends(require_treasury_access),
    ):
        get_country_or_404(country_code.upper(), db)
        set_rls_context({country_code.upper()}, is_restricted=True)
        try:
            rows = db.execute(
                select(
                    SupplierSettlement.supplier_id,
                    func.sum(SupplierSettlement.gross_amount).label("gross"),
                    func.sum(SupplierSettlement.commission_amount).label("commission"),
                    func.sum(SupplierSettlement.net_amount).label("net"),
                ).where(SupplierSettlement.country_code == country_code.upper())
                .group_by(SupplierSettlement.supplier_id)
            ).all()
            return [
                {
                    "supplier_id": r.supplier_id,
                    "gross": float(r.gross or 0),
                    "commission": float(r.commission or 0),
                    "net": float(r.net or 0),
                }
                for r in rows
            ]
        finally:
            clear_rls_context()
    _s18.get("/{country_code}/reports/supplier-earnings")(country_supplier_earnings)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route country_supplier_earnings: %s", _e)

try:
    def     admin_liabilities_exposure(
        db: Session = Depends(get_db),
        current_user: dict = Depends(require_treasury_access),
    ):
        codes = {"2010": "supplier_payables", "2020": "logistics_payables", "2040": "vat_payable"}
        exposure = {}
        for code, label in codes.items():
            bal = db.execute(
                select(func.coalesce(func.sum(AccountBalance.balance), 0))
                .join(Account, AccountBalance.account_id == Account.id)
                .where(Account.code == code)
            ).scalar() or Decimal("0")
            exposure[label] = float(bal)
        return exposure
    _s18.get("/liabilities/exposure")(admin_liabilities_exposure)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route admin_liabilities_exposure: %s", _e)

try:
    def     country_liabilities_exposure(
        country_code: str = Path(..., description="ISO country code"),
        db: Session = Depends(get_db),
        current_user: dict = Depends(require_treasury_access),
    ):
        get_country_or_404(country_code.upper(), db)
        set_rls_context({country_code.upper()}, is_restricted=True)
        try:
            codes = {"2010": "supplier_payables", "2020": "logistics_payables", "2030": "vat_payable"}
            exposure = {}
            for code, label in codes.items():
                bal = db.execute(
                    select(func.coalesce(func.sum(AccountBalance.balance), 0))
                    .join(Account, AccountBalance.account_id == Account.id)
                    .where(Account.code == code, AccountBalance.country_code == country_code.upper())
                ).scalar() or Decimal("0")
                exposure[label] = float(bal)
            return exposure
        finally:
            clear_rls_context()
    _s18.get("/{country_code}/liabilities/exposure")(country_liabilities_exposure)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route country_liabilities_exposure: %s", _e)

try:
    def     admin_manual_adjustment(
        debit_account: str = FastAPIBody(...),
        credit_account: str = FastAPIBody(...),
        amount: float = FastAPIBody(...),
        reason: str = FastAPIBody(...),
        created_by: int = FastAPIBody(...),
        db: Session = Depends(get_db),
        current_user: dict = Depends(require_treasury_access),
    ):
        engine = TreasuryEngine(db)
        threshold = Decimal("10000")
        amount_dec = Decimal(str(amount))
        lines = [
            {"account_code": debit_account, "debit": float(amount_dec), "description": reason},
            {"account_code": credit_account, "credit": float(amount_dec), "description": reason},
        ]
        if amount_dec > threshold:
            pending = engine.submit_pending_entry(
                lines=lines, description=reason, created_by=created_by, source="manual_adjustment",
            )
            return {"status": "pending_approval", "pending_id": pending["pending_id"]}
        entry = engine.post_journal_entry(
            lines=lines, description=reason, source="manual_adjustment", created_by=created_by,
        )
        return {"entry_id": entry.id, "reference_number": entry.reference_number}
    _s18.post("/ledger/manual-adjustment")(admin_manual_adjustment)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route admin_manual_adjustment: %s", _e)

try:
    def     country_manual_adjustment(
        country_code: str = Path(..., description="ISO country code"),
        debit_account: str = FastAPIBody(...),
        credit_account: str = FastAPIBody(...),
        amount: float = FastAPIBody(...),
        reason: str = FastAPIBody(...),
        created_by: int = FastAPIBody(...),
        db: Session = Depends(get_db),
        current_user: dict = Depends(require_treasury_access),
    ):
        get_country_or_404(country_code.upper(), db)
        set_rls_context({country_code.upper()}, is_restricted=True)
        try:
            engine = TreasuryEngine(db)
            threshold = Decimal("10000")
            amount_dec = Decimal(str(amount))
            lines = [
                {"account_code": debit_account, "debit": float(amount_dec), "description": reason},
                {"account_code": credit_account, "credit": float(amount_dec), "description": reason},
            ]
            if amount_dec > threshold:
                pending = engine.submit_pending_entry(
                    lines=lines, description=reason, created_by=created_by, source="manual_adjustment",
                    country_code=country_code.upper(),
                )
                return {"status": "pending_approval", "pending_id": pending["pending_id"]}
            entry = engine.post_journal_entry(
                lines=lines, description=reason, source="manual_adjustment", created_by=created_by,
                country_code=country_code.upper(),
            )
            return {"entry_id": entry.id, "reference_number": entry.reference_number}
        finally:
            clear_rls_context()
    _s18.post("/{country_code}/ledger/manual-adjustment")(country_manual_adjustment)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route country_manual_adjustment: %s", _e)

try:
    def     admin_pending_entries(
        db: Session = Depends(get_db),
        current_user: dict = Depends(require_treasury_access),
    ):
        engine = TreasuryEngine(db)
        return {"entries": engine.list_pending_entries()}
    _s18.get("/ledger/pending")(admin_pending_entries)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route admin_pending_entries: %s", _e)

try:
    def     country_pending_entries(
        country_code: str = Path(..., description="ISO country code"),
        db: Session = Depends(get_db),
        current_user: dict = Depends(require_treasury_access),
    ):
        get_country_or_404(country_code.upper(), db)
        set_rls_context({country_code.upper()}, is_restricted=True)
        try:
            engine = TreasuryEngine(db)
            all_entries = engine.list_pending_entries()
            filtered = [e for e in all_entries if e.get("country_code") == country_code.upper()]
            return {"entries": filtered}
        finally:
            clear_rls_context()
    _s18.get("/{country_code}/ledger/pending")(country_pending_entries)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route country_pending_entries: %s", _e)

try:
    def     admin_approve_pending(
        pending_id: int = Path(...),
        approver_id: int = FastAPIBody(...),
        db: Session = Depends(get_db),
        current_user: dict = Depends(require_treasury_access),
    ):
        engine = TreasuryEngine(db)
        result = engine.approve_pending_entry(pending_id, approver_id)
        return result
    _s18.post("/ledger/pending/{pending_id}/approve")(admin_approve_pending)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route admin_approve_pending: %s", _e)

try:
    def     country_approve_pending(
        country_code: str = Path(..., description="ISO country code"),
        pending_id: int = Path(...),
        approver_id: int = FastAPIBody(...),
        db: Session = Depends(get_db),
        current_user: dict = Depends(require_treasury_access),
    ):
        get_country_or_404(country_code.upper(), db)
        set_rls_context({country_code.upper()}, is_restricted=True)
        try:
            engine = TreasuryEngine(db)
            result = engine.approve_pending_entry(pending_id, approver_id)
            return result
        finally:
            clear_rls_context()
    _s18.post("/{country_code}/ledger/pending/{pending_id}/approve")(country_approve_pending)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route country_approve_pending: %s", _e)

try:
    def     admin_reject_pending(
        pending_id: int = Path(...),
        rejected_by: int = FastAPIBody(...),
        reason: str = FastAPIBody(...),
        db: Session = Depends(get_db),
        current_user: dict = Depends(require_treasury_access),
    ):
        engine = TreasuryEngine(db)
        result = engine.reject_pending_entry(pending_id, rejected_by, reason)
        return result
    _s18.post("/ledger/pending/{pending_id}/reject")(admin_reject_pending)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route admin_reject_pending: %s", _e)

try:
    def     country_reject_pending(
        country_code: str = Path(..., description="ISO country code"),
        pending_id: int = Path(...),
        rejected_by: int = FastAPIBody(...),
        reason: str = FastAPIBody(...),
        db: Session = Depends(get_db),
        current_user: dict = Depends(require_treasury_access),
    ):
        get_country_or_404(country_code.upper(), db)
        set_rls_context({country_code.upper()}, is_restricted=True)
        try:
            engine = TreasuryEngine(db)
            result = engine.reject_pending_entry(pending_id, rejected_by, reason)
            return result
        finally:
            clear_rls_context()
    _s18.post("/{country_code}/ledger/pending/{pending_id}/reject")(country_reject_pending)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route country_reject_pending: %s", _e)

try:
    def     admin_detect_orphans(
        db: Session = Depends(get_db),
        current_user: dict = Depends(require_treasury_access),
    ):
        engine = TreasuryEngine(db)
        alerts = engine.run_orphan_detector()
        return {"alerts": alerts, "count": len(alerts)}
    _s18.post("/detect-orphans")(admin_detect_orphans)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route admin_detect_orphans: %s", _e)

try:
    def     country_detect_orphans(
        country_code: str = Path(..., description="ISO country code"),
        db: Session = Depends(get_db),
        current_user: dict = Depends(require_treasury_access),
    ):
        get_country_or_404(country_code.upper(), db)
        set_rls_context({country_code.upper()}, is_restricted=True)
        try:
            engine = TreasuryEngine(db)
            alerts = engine.run_orphan_detector()
            filtered = [a for a in alerts if a.get("country_code") == country_code.upper()]
            return {"alerts": filtered, "count": len(filtered)}
        finally:
            clear_rls_context()
    _s18.post("/{country_code}/detect-orphans")(country_detect_orphans)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route country_detect_orphans: %s", _e)

try:
    def     payroll_equity(db: Session = Depends(get_db)):
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
    _s18.get("/payroll/equity")(payroll_equity)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route payroll_equity: %s", _e)

try:
    def     country_payroll(country_code: str, db: Session = Depends(get_db)):
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
    _s18.get("/{country_code}/payroll")(country_payroll)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route country_payroll: %s", _e)

_s19 = APIRouter(prefix='/api/v1/admin/treasury')

try:
    def     health():
        """Liveness probe for this router."""
        return {"status": "ok", "router": "admin_treasury_routes", "prefix": "/api/v1/admin/treasury"}
    _s19.get("/admin_treasury_routes/health")(health)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route health: %s", _e)

_s21 = APIRouter(prefix='')

try:
    def _build_category_rate(payload: CommissionCategoryRateCreate, country_code: str) -> CommissionCategoryRate:
        data = payload.model_dump() if payload else {}
        return CommissionCategoryRate(
            category_id=data.get("category_id"),
            category_slug=data.get("category_slug"),
            category_display_name=data.get("category_display_name"),
            rate_percent=data.get("rate", 0),
            is_active=data.get("is_active", True),
            country_code=country_code.upper(),
        )
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route: %s", _e)

try:
    def _build_badge_tier(payload: CommissionBadgeTierCreate, country_code: str) -> CommissionBadgeTier:
        data = payload.model_dump() if payload else {}
        return CommissionBadgeTier(
            badge_level=data.get("badge_level"),
            commission_rate=data.get("commission_rate", 0),
            min_fulfilled_orders=data.get("min_fulfilled_orders", 0),
            is_active=data.get("is_active", True),
            country_code=country_code.upper(),
        )
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route: %s", _e)

try:
    def     list_rates(country_code: str = Path(..., description="ISO country code"), _: User = Depends(require_admin), db: Session = Depends(get_db), page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100)):
        get_country_or_404(country_code.upper(), db)
        set_rls_context({country_code.upper()}, is_restricted=True)
        try:
            q = db.query(CommissionCategoryRate).filter(CommissionCategoryRate.country_code == country_code.upper())
            total = q.count()
            rows = q.offset((page - 1) * page_size).limit(page_size).all()
            return {"data": rows, "total": total, "page": page, "page_size": page_size}
        finally:
            clear_rls_context()
    _s21.get("/{country_code}/rates")(list_rates)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route list_rates: %s", _e)

try:
    def     create_rate(country_code: str = Path(..., description="ISO country code"), payload: CommissionCategoryRateCreate = None, _: User = Depends(require_admin), db: Session = Depends(get_db)):
        get_country_or_404(country_code.upper(), db)
        set_rls_context({country_code.upper()}, is_restricted=True)
        try:
            r = _build_category_rate(payload, country_code)
            db.add(r); db.commit(); db.refresh(r)
            return r
        finally:
            clear_rls_context()
    _s21.post("/{country_code}/rates", response_model=CommissionCategoryRateOut, status_code=201)(create_rate)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route create_rate: %s", _e)

try:
    def     update_rate(country_code: str = Path(..., description="ISO country code"), rate_id: int = Path(..., description="Rate id"), payload: CommissionCategoryRateCreate = None, _: User = Depends(require_admin), db: Session = Depends(get_db)):
        get_country_or_404(country_code.upper(), db)
        r = db.query(CommissionCategoryRate).filter(CommissionCategoryRate.id == rate_id, CommissionCategoryRate.country_code == country_code.upper()).first()
        if not r:
            raise HTTPException(status_code=404, detail="Category rate not found")
        data = payload.model_dump() if payload else {}
        r.category_id = data.get("category_id", r.category_id)
        r.category_slug = data.get("category_slug", r.category_slug)
        r.category_display_name = data.get("category_display_name", r.category_display_name)
        if "rate" in data:
            r.rate_percent = data["rate"]
        r.is_active = data.get("is_active", r.is_active)
        db.commit(); db.refresh(r)
        return r
    _s21.put("/{country_code}/rates/{rate_id}", response_model=CommissionCategoryRateOut)(update_rate)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route update_rate: %s", _e)

try:
    def     list_badge_tiers(country_code: str = Path(..., description="ISO country code"), _: User = Depends(require_admin), db: Session = Depends(get_db), page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100)):
        get_country_or_404(country_code.upper(), db)
        set_rls_context({country_code.upper()}, is_restricted=True)
        try:
            q = db.query(CommissionBadgeTier).filter(CommissionBadgeTier.country_code == country_code.upper())
            total = q.count()
            rows = q.offset((page - 1) * page_size).limit(page_size).all()
            return {"data": rows, "total": total, "page": page, "page_size": page_size}
        finally:
            clear_rls_context()
    _s21.get("/{country_code}/badge-tiers")(list_badge_tiers)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route list_badge_tiers: %s", _e)

try:
    def     create_badge_tier(country_code: str = Path(..., description="ISO country code"), payload: CommissionBadgeTierCreate = None, _: User = Depends(require_admin), db: Session = Depends(get_db)):
        get_country_or_404(country_code.upper(), db)
        set_rls_context({country_code.upper()}, is_restricted=True)
        try:
            t = _build_badge_tier(payload, country_code)
            db.add(t); db.commit(); db.refresh(t)
            return t
        finally:
            clear_rls_context()
    _s21.post("/{country_code}/badge-tiers", response_model=CommissionBadgeTierOut, status_code=201)(create_badge_tier)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route create_badge_tier: %s", _e)

try:
    def     update_badge_tier(country_code: str = Path(..., description="ISO country code"), tier_id: int = Path(..., description="Badge tier id"), payload: CommissionBadgeTierCreate = None, _: User = Depends(require_admin), db: Session = Depends(get_db)):
        get_country_or_404(country_code.upper(), db)
        t = db.query(CommissionBadgeTier).filter(CommissionBadgeTier.id == tier_id, CommissionBadgeTier.country_code == country_code.upper()).first()
        if not t:
            raise HTTPException(status_code=404, detail="Badge tier not found")
        data = payload.model_dump() if payload else {}
        t.badge_level = data.get("badge_level", t.badge_level)
        t.commission_rate = data.get("commission_rate", t.commission_rate)
        t.min_fulfilled_orders = data.get("min_fulfilled_orders", t.min_fulfilled_orders)
        t.is_active = data.get("is_active", t.is_active)
        db.commit(); db.refresh(t)
        return t
    _s21.put("/{country_code}/badge-tiers/{tier_id}", response_model=CommissionBadgeTierOut)(update_badge_tier)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route update_badge_tier: %s", _e)

_s25 = APIRouter(prefix='')

try:
    def     admin_invoices_overview(

        db: Session = Depends(get_db),

        current_admin: dict = Depends(get_current_admin),

    ):

        """Admin overview of supply chain invoices."""

        require_permission("orders.manage", current_admin)

        import domains.finance.services.ledger.invoice_controller as _ic

        return _ic.get_invoice_overview(db)
    _s25.get("/invoices/overview")(admin_invoices_overview)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route admin_invoices_overview: %s", _e)

_s26 = APIRouter(prefix='/api/v1/accounting')

try:
    def     health():
        """Liveness probe for this router."""
        return {"status": "ok", "router": "core_accounting_routes", "prefix": "/api/v1/accounting"}
    _s26.get("/core_accounting_routes/health")(health)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route health: %s", _e)

try:
    def     status():
        """Report whether a backing controller is importable."""
        return {"router": "core_accounting_routes", "controller": "controllers.finance.accounting_controller" if _HAS_CTRL else None,
                "public_functions": _CTRL_PUBLIC}
    _s26.get("/core_accounting_routes/status")(status)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route status: %s", _e)

_s28 = APIRouter(prefix='/api/v1/invoices')

try:
    def     health():
        """Liveness probe for this router."""
        return {"status": "ok", "router": "core_invoices_routes", "prefix": "/api/v1/invoices"}
    _s28.get("/core_invoices_routes/health")(health)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route health: %s", _e)

_s29 = APIRouter(prefix='/api/v1/treasury')

try:
    def     health():
        """Liveness probe for this router."""
        return {"status": "ok", "router": "core_treasury_routes", "prefix": "/api/v1/treasury"}
    _s29.get("/core_treasury_routes/health")(health)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route health: %s", _e)

_s32 = APIRouter(prefix='/api/v1')

try:
    def     treasury_metrics(
        current_user: dict = Depends(get_current_user),
        db: Session = Depends(get_db),
    ):
        result = get_treasury_metrics(db)
        audit_log(
            db=db,
            action=AuditAction.TRIAL_BALANCE_VIEWED,
            user_id=current_user.get("id"),
            username=current_user.get("username"),
            user_role=current_user.get("role"),
            resource_type="treasury_metrics",
        )
        return result
    _s32.get("/metrics")(treasury_metrics)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route treasury_metrics: %s", _e)

try:
    def     cash_position(
        current_user: dict = Depends(get_current_user),
        db: Session = Depends(get_db),
    ):
        result = get_cash_position(db)
        audit_log(
            db=db,
            action=AuditAction.FINANCIAL_REPORT_GENERATED,
            user_id=current_user.get("id"),
            username=current_user.get("username"),
            user_role=current_user.get("role"),
            resource_type="cash_position",
        )
        return result
    _s32.get("/cash-position")(cash_position)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route cash_position: %s", _e)

try:
    def     vat_liability(
        country_code: str = None,
        current_user: dict = Depends(get_current_user),
        db: Session = Depends(get_db),
    ):
        result = get_vat_liability(db, country_code)
        audit_log(
            db=db,
            action=AuditAction.FINANCIAL_REPORT_GENERATED,
            user_id=current_user.get("id"),
            username=current_user.get("username"),
            user_role=current_user.get("role"),
            resource_type="vat_liability",
            details={"country_code": country_code},
        )
        return result
    _s32.get("/vat-liability")(vat_liability)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route vat_liability: %s", _e)

try:
    def     supplier_payables(
        country_code: str = None,
        current_user: dict = Depends(get_current_user),
        db: Session = Depends(get_db),
    ):
        result = get_supplier_payables(db, country_code)
        audit_log(
            db=db,
            action=AuditAction.FINANCIAL_REPORT_GENERATED,
            user_id=current_user.get("id"),
            username=current_user.get("username"),
            user_role=current_user.get("role"),
            resource_type="supplier_payables",
            details={"country_code": country_code},
        )
        return result
    _s32.get("/supplier-payables")(supplier_payables)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route supplier_payables: %s", _e)

router = APIRouter()try:    router.include_router(_s12)except Exception as _e:    import logging as _l; _l.getLogger(__name__).warning("skip subrouter _s12: %s", _e)try:    router.include_router(_s13)except Exception as _e:    import logging as _l; _l.getLogger(__name__).warning("skip subrouter _s13: %s", _e)try:    router.include_router(_s14)except Exception as _e:    import logging as _l; _l.getLogger(__name__).warning("skip subrouter _s14: %s", _e)try:    router.include_router(_s18)except Exception as _e:    import logging as _l; _l.getLogger(__name__).warning("skip subrouter _s18: %s", _e)try:    router.include_router(_s19)except Exception as _e:    import logging as _l; _l.getLogger(__name__).warning("skip subrouter _s19: %s", _e)try:    router.include_router(_s21)except Exception as _e:    import logging as _l; _l.getLogger(__name__).warning("skip subrouter _s21: %s", _e)try:    router.include_router(_s25)except Exception as _e:    import logging as _l; _l.getLogger(__name__).warning("skip subrouter _s25: %s", _e)try:    router.include_router(_s26)except Exception as _e:    import logging as _l; _l.getLogger(__name__).warning("skip subrouter _s26: %s", _e)try:    router.include_router(_s28)except Exception as _e:    import logging as _l; _l.getLogger(__name__).warning("skip subrouter _s28: %s", _e)try:    router.include_router(_s29)except Exception as _e:    import logging as _l; _l.getLogger(__name__).warning("skip subrouter _s29: %s", _e)try:    router.include_router(_s32)except Exception as _e:    import logging as _l; _l.getLogger(__name__).warning("skip subrouter _s32: %s", _e)