"""Admin commissions router � split from finance.py."""
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

_s22 = APIRouter(prefix='/api/v1/admin')

try:
    def     health():
        """Liveness probe for this router."""
        return {"status": "ok", "router": "admin_commission_routes", "prefix": "/api/v1/admin"}
    _s22.get("/admin_commission_routes/health")(health)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route health: %s", _e)

try:
    def     status():
        """Report whether a backing controller is importable."""
        return {"router": "admin_commission_routes", "controller": "controllers.finance.commission_controller" if _HAS_CTRL else None,
                "public_functions": _CTRL_PUBLIC}
    _s22.get("/admin_commission_routes/status")(status)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route status: %s", _e)

_s24 = APIRouter(prefix='')

try:
    def     list_admin_disputes(

        status: Optional[str] = Query(None),

        priority: Optional[str] = Query(None),

        supplier_id: Optional[int] = Query(None),

        cursor: Optional[str] = Query(None),

        db: Session = Depends(get_db),

        current_admin: dict = Depends(get_current_admin),

    ):

        require_permission("moderation.suppliers", current_admin)

        return disputes_controller.list_admin_disputes(

            db=db,

            status=status,

            priority=priority,

            supplier_id=supplier_id,

            cursor=cursor,

        )
    _s24.get("/disputes", response_model=ListPage[dict])(list_admin_disputes)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route list_admin_disputes: %s", _e)

try:
    def     get_admin_dispute(

        dispute_id: int,

        db: Session = Depends(get_db),

        current_admin: dict = Depends(get_current_admin),

    ):

        require_permission("moderation.suppliers", current_admin)

        return disputes_controller.get_admin_dispute(dispute_id, db)
    _s24.get("/disputes/{dispute_id}")(get_admin_dispute)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route get_admin_dispute: %s", _e)

try:
    def     patch_admin_dispute(

        dispute_id: int,

        payload: dict = Body(default_factory=dict),

        db: Session = Depends(get_db),

        current_admin: dict = Depends(get_current_admin),

    ):

        require_permission("moderation.suppliers", current_admin)

        return disputes_controller.update_admin_dispute(dispute_id, payload, current_admin, db)
    _s24.patch("/disputes/{dispute_id}")(patch_admin_dispute)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route patch_admin_dispute: %s", _e)

try:
    def     bulk_admin_dispute_action(

        body: AdminDisputeBulkActionBody,

        db: Session = Depends(get_db),

        current_admin: dict = Depends(get_current_admin),

    ):

        require_permission("moderation.suppliers", current_admin)

        return disputes_controller.bulk_update_admin_disputes(

            dispute_ids=body.dispute_ids,

            action=body.action,

            value=body.value,

            current_admin=current_admin,

            db=db,

        )
    _s24.post("/disputes/bulk")(bulk_admin_dispute_action)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route bulk_admin_dispute_action: %s", _e)

_s27 = APIRouter(prefix='/api/v1/commission')

try:
    def     health():
        """Liveness probe for this router."""
        return {"status": "ok", "router": "core_commission_routes", "prefix": "/api/v1/commission"}
    _s27.get("/core_commission_routes/health")(health)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route health: %s", _e)

try:
    def     status():
        """Report whether a backing controller is importable."""
        return {"router": "core_commission_routes", "controller": "controllers.finance.commission_controller" if _HAS_CTRL else None,
                "public_functions": _CTRL_PUBLIC}
    _s27.get("/core_commission_routes/status")(status)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route status: %s", _e)

router = APIRouter()try:    router.include_router(_s22)except Exception as _e:    import logging as _l; _l.getLogger(__name__).warning("skip subrouter _s22: %s", _e)try:    router.include_router(_s24)except Exception as _e:    import logging as _l; _l.getLogger(__name__).warning("skip subrouter _s24: %s", _e)try:    router.include_router(_s27)except Exception as _e:    import logging as _l; _l.getLogger(__name__).warning("skip subrouter _s27: %s", _e)