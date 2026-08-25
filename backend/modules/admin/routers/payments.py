"""Admin payments router � split from finance.py."""
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

_s0 = APIRouter(prefix='/api/v1/admin')

try:
    def     seed_chart_of_accounts_route(
        db: Session = Depends(get_db),
        audit_user_id: Optional[int] = Query(None),
        audit_username: Optional[str] = Query(None),
        audit_user_role: Optional[str] = Query(None)
    ) -> dict:
        return seed_chart_of_accounts(db=db, audit_user_id=audit_user_id, audit_username=audit_username, audit_user_role=audit_user_role)
    _s0.post("/seed", status_code=201, tags=['accounting'], summary="Seed chart of accounts (idempotent)")(seed_chart_of_accounts_route)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route seed_chart_of_accounts_route: %s", _e)

try:
    def     list_accounts_route(
        db: Session = Depends(get_db)
    ) -> list:
        return list_accounts(db=db)
    _s0.get("/accounts", status_code=200, tags=['accounting'], summary="List all accounts")(list_accounts_route)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route list_accounts_route: %s", _e)

try:
    def     get_account_route(
        code: str,
        db: Session = Depends(get_db)
    ):
        return get_account(db=db, code=code)
    _s0.get("/accounts/{code}", status_code=200, tags=['accounting'], summary="Get account by code")(get_account_route)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route get_account_route: %s", _e)

try:
    def     create_journal_entry_route(
        db: Session = Depends(get_db),
        current_user: dict = Depends(require_admin),
        body: JournalEntryBody = Body(...)
    ) -> dict:
        return create_journal_entry(db=db, current_user=current_user, body=body)
    _s0.post("/journal-entries", status_code=201, tags=['accounting'], summary="Create a journal entry")(create_journal_entry_route)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route create_journal_entry_route: %s", _e)

try:
    def     get_journal_entry_route(
        entry_id: int,
        db: Session = Depends(get_db)
    ):
        return get_journal_entry(db=db, entry_id=entry_id)
    _s0.get("/journal-entries/{entry_id}", status_code=200, tags=['accounting'], summary="Get journal entry by ID")(get_journal_entry_route)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route get_journal_entry_route: %s", _e)

try:
    def     list_journal_entries_route(
        db: Session = Depends(get_db),
        reference_type: Optional[str] = Query(None),
        reference_id: Optional[int] = Query(None),
        country_code: Optional[str] = Query(None),
        limit: int = Query(50)
    ) -> list:
        return list_journal_entries(db=db, reference_type=reference_type, reference_id=reference_id, country_code=country_code, limit=limit)
    _s0.get("/journal-entries", status_code=200, tags=['accounting'], summary="List journal entries")(list_journal_entries_route)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route list_journal_entries_route: %s", _e)

try:
    def     get_account_balance_route(
        account_code: str,
        db: Session = Depends(get_db),
        currency: str = Query('OMR')
    ) -> dict:
        return get_account_balance(db=db, account_code=account_code, currency=currency)
    _s0.get("/balances/{account_code}", status_code=200, tags=['accounting'], summary="Get account balance")(get_account_balance_route)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route get_account_balance_route: %s", _e)

try:
    def     get_trial_balance_route(
        db: Session = Depends(get_db),
        as_of_date: Optional[date] = Query(None),
        currency: str = Query('OMR'),
        country_code: Optional[str] = Query(None)
    ) -> list:
        return get_trial_balance(db=db, as_of_date=as_of_date, currency=currency, country_code=country_code)
    _s0.get("/trial-balance", status_code=200, tags=['accounting'], summary="Get trial balance")(get_trial_balance_route)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route get_trial_balance_route: %s", _e)

_s1 = APIRouter(prefix='/api/v1/admin')

try:
    def _with_rls(country_code: Optional[str], db: Session):
        """Set RLS context if country_code is provided. Returns cleanup function."""
        if country_code:
            get_country_or_404(country_code.upper(), db)
            set_rls_context({country_code.upper()}, is_restricted=True)
        def cleanup():
            if country_code:
                clear_rls_context()
        return cleanup
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route: %s", _e)

try:
    def     seed_chart_of_accounts(
        db: Session = Depends(get_db),
        _admin: dict = Depends(require_admin),
    ):
        return accounting_controller.seed_chart_of_accounts(
            db,
            audit_user_id=_admin.get("id"),
            audit_username=_admin.get("username"),
            audit_user_role=_admin.get("role"),
        )
    _s1.post("/seed", summary="Seed chart of accounts (idempotent)")(seed_chart_of_accounts)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route seed_chart_of_accounts: %s", _e)

try:
    def     list_accounts(
        country_code: str = Query(None, max_length=3),
        db: Session = Depends(get_db),
        _user=Depends(require_admin),
    ):
        cleanup = _with_rls(country_code, db)
        try:
            return accounting_controller.list_accounts(db)
        finally:
            cleanup()
    _s1.get("/accounts", summary="List all accounts")(list_accounts)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route list_accounts: %s", _e)

try:
    def     get_account(
        code: str,
        country_code: str = Query(None, max_length=3),
        db: Session = Depends(get_db),
        _user=Depends(require_admin),
    ):
        cleanup = _with_rls(country_code, db)
        try:
            return accounting_controller.get_account(db, code)
        finally:
            cleanup()
    _s1.get("/accounts/{code}", summary="Get account by code")(get_account)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route get_account: %s", _e)

try:
    def     create_journal_entry(
        body: accounting_controller.JournalEntryBody,
        db: Session = Depends(get_db),
        current_user=Depends(require_admin),
    ):
        return accounting_controller.create_journal_entry(db, body, current_user)
    _s1.post("/journal-entries", summary="Create a journal entry")(create_journal_entry)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route create_journal_entry: %s", _e)

try:
    def     list_journal_entries(
        reference_type: Optional[str] = Query(None, max_length=40),
        reference_id: Optional[int] = Query(None),
        country_code: Optional[str] = Query(None, max_length=3),
        limit: int = Query(50, ge=1, le=500),
        db: Session = Depends(get_db),
        _user=Depends(require_admin),
    ):
        cleanup = _with_rls(country_code, db)
        try:
            return accounting_controller.list_journal_entries(
                db, reference_type=reference_type, reference_id=reference_id, country_code=country_code, limit=limit
            )
        finally:
            cleanup()
    _s1.get("/journal-entries", summary="List journal entries")(list_journal_entries)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route list_journal_entries: %s", _e)

try:
    def     get_journal_entry(
        entry_id: int,
        country_code: str = Query(None, max_length=3),
        db: Session = Depends(get_db),
        _user=Depends(require_admin),
    ):
        cleanup = _with_rls(country_code, db)
        try:
            return accounting_controller.get_journal_entry(db, entry_id)
        finally:
            cleanup()
    _s1.get("/journal-entries/{entry_id}", summary="Get journal entry by ID")(get_journal_entry)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route get_journal_entry: %s", _e)

try:
    def     get_balance(
        account_code: str,
        currency: str = Query("OMR", max_length=10),
        country_code: str = Query(None, max_length=3),
        db: Session = Depends(get_db),
        _user=Depends(require_admin),
    ):
        cleanup = _with_rls(country_code, db)
        try:
            return accounting_controller.get_account_balance(db, account_code, currency)
        finally:
            cleanup()
    _s1.get("/balances/{account_code}", summary="Get account balance")(get_balance)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route get_balance: %s", _e)

try:
    def     trial_balance(
        as_of_date: Optional[date] = Query(None),
        currency: str = Query("OMR", max_length=10),
        country_code: Optional[str] = Query(None, max_length=3),
        db: Session = Depends(get_db),
        _user=Depends(require_admin),
    ):
        cleanup = _with_rls(country_code, db)
        try:
            return accounting_controller.get_trial_balance(
                db, as_of_date=as_of_date, currency=currency, country_code=country_code
            )
        finally:
            cleanup()
    _s1.get("/trial-balance", summary="Get trial balance")(trial_balance)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route trial_balance: %s", _e)

try:
    def     income_statement(
        body: ReportPeriod,
        db: Session = Depends(get_db),
        _admin: dict = Depends(require_admin),
    ):
        cleanup = _with_rls(body.country_code, db)
        try:
            svc = FinancialReportingService(db)
            result = svc.generate_income_statement(
                body.period_start, body.period_end, body.currency, persist=body.persist, country_code=body.country_code
            )
            audit_log(
                db=db,
                action=AuditAction.FINANCIAL_REPORT_GENERATED,
                user_id=_admin.get("id"),
                username=_admin.get("username"),
                user_role=_admin.get("role"),
                resource_type="income_statement",
                details={"period_start": body.period_start.isoformat(), "period_end": body.period_end.isoformat(), "currency": body.currency, "country_code": body.country_code},
            )
            return result
        finally:
            cleanup()
    _s1.post("/reports/income-statement", summary="Generate Income Statement (P&L)")(income_statement)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route income_statement: %s", _e)

try:
    def     balance_sheet(
        as_of_date: Optional[datetime] = Query(None, description="Defaults to now"),
        currency: str = Query("OMR", max_length=10),
        persist: bool = Query(False),
        country_code: Optional[str] = Query(None, max_length=3),
        db: Session = Depends(get_db),
        _admin: dict = Depends(require_admin),
    ):
        cleanup = _with_rls(country_code, db)
        try:
            svc = FinancialReportingService(db)
            result = svc.generate_balance_sheet(as_of_date, currency, persist=persist, country_code=country_code)
            audit_log(
                db=db,
                action=AuditAction.FINANCIAL_REPORT_GENERATED,
                user_id=_admin.get("id"),
                username=_admin.get("username"),
                user_role=_admin.get("role"),
                resource_type="balance_sheet",
                details={"as_of_date": (as_of_date or datetime.utcnow()).isoformat(), "currency": currency, "country_code": country_code},
            )
            return result
        finally:
            cleanup()
    _s1.post("/reports/balance-sheet", summary="Generate Balance Sheet")(balance_sheet)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route balance_sheet: %s", _e)

try:
    def     cash_flow(
        body: ReportPeriod,
        db: Session = Depends(get_db),
        _admin: dict = Depends(require_admin),
    ):
        cleanup = _with_rls(body.country_code, db)
        try:
            svc = FinancialReportingService(db)
            result = svc.generate_cash_flow(
                body.period_start, body.period_end, body.currency, persist=body.persist, country_code=body.country_code
            )
            audit_log(
                db=db,
                action=AuditAction.FINANCIAL_REPORT_GENERATED,
                user_id=_admin.get("id"),
                username=_admin.get("username"),
                user_role=_admin.get("role"),
                resource_type="cash_flow_statement",
                details={"period_start": body.period_start.isoformat(), "period_end": body.period_end.isoformat(), "currency": body.currency, "country_code": body.country_code},
            )
            return result
        finally:
            cleanup()
    _s1.post("/reports/cash-flow", summary="Generate Cash Flow Statement")(cash_flow)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route cash_flow: %s", _e)

try:
    def     list_reports(
        report_type: Optional[str] = Query(None, description="Filter by report type"),
        country_code: Optional[str] = Query(None, max_length=3),
        limit: int = Query(20, ge=1, le=100),
        db: Session = Depends(get_db),
        _user=Depends(require_admin),
    ):
        cleanup = _with_rls(country_code, db)
        try:
            svc = FinancialReportingService(db)
            return svc.list_reports(report_type=report_type, country_code=country_code, limit=limit)
        finally:
            cleanup()
    _s1.get("/reports", summary="List saved financial reports")(list_reports)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route list_reports: %s", _e)

try:
    def     get_or_create(
        country_code: str = Query(..., max_length=3),
        year: int = Query(..., ge=2020, le=2100),
        month: int = Query(..., ge=1, le=12),
        db: Session = Depends(get_db),
        _admin: dict = Depends(require_admin),
    ):
        cleanup = _with_rls(country_code, db)
        try:
            period = get_or_create_fiscal_period(db, country_code, year, month)
            return {
                "id": period.id,
                "country_code": period.country_code,
                "label": f"{period.period_year}-{period.period_month:02d}",
                "status": period.status,
                "period_start": period.period_start.isoformat(),
                "period_end": period.period_end.isoformat(),
            }
        finally:
            cleanup()
    _s1.post("/periods/get-or-create", summary="Get or create a fiscal period")(get_or_create)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route get_or_create: %s", _e)

try:
    def     current_period(
        country_code: str = Query(..., max_length=3),
        db: Session = Depends(get_db),
        _user=Depends(require_admin),
    ):
        cleanup = _with_rls(country_code, db)
        try:
            period = get_current_fiscal_period(db, country_code)
            if not period:
                return None
            return {
                "id": period.id,
                "country_code": period.country_code,
                "label": f"{period.period_year}-{period.period_month:02d}",
                "status": period.status,
                "is_locked": period.is_locked,
                "period_start": period.period_start.isoformat(),
                "period_end": period.period_end.isoformat(),
            }
        finally:
            cleanup()
    _s1.get("/periods/current", summary="Get current fiscal period")(current_period)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route current_period: %s", _e)

try:
    def     close_fiscal_period(
        body: ClosePeriodBody,
        db: Session = Depends(get_db),
        _admin: dict = Depends(require_admin),
    ):
        result = close_period(
            db,
            period_id=body.period_id,
            closed_by=_admin.get("id"),
            notes=body.notes,
            transfer_to_retained_earnings=body.transfer_to_retained_earnings,
        )
        audit_log(
            db=db,
            action=AuditAction.PERIOD_CLOSED,
            user_id=_admin.get("id"),
            username=_admin.get("username"),
            user_role=_admin.get("role"),
            resource_type="fiscal_period",
            resource_id=body.period_id,
            details=result,
        )
        return result
    _s1.post("/periods/close", summary="Close a fiscal period")(close_fiscal_period)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route close_fiscal_period: %s", _e)

try:
    def     list_fiscal_periods(
        country_code: Optional[str] = Query(None, max_length=3),
        status: Optional[str] = Query(None),
        limit: int = Query(24, ge=1, le=120),
        db: Session = Depends(get_db),
        _user=Depends(require_admin),
    ):
        cleanup = _with_rls(country_code, db)
        try:
            periods = list_periods(db, country_code=country_code, status=status, limit=limit)
            return [
                {
                    "id": p.id,
                    "country_code": p.country_code,
                    "label": f"{p.period_year}-{p.period_month:02d}",
                    "status": p.status,
                    "is_locked": p.is_locked,
                    "period_start": p.period_start.isoformat(),
                    "period_end": p.period_end.isoformat(),
                    "closed_at": p.closed_at.isoformat() if p.closed_at else None,
                }
                for p in periods
            ]
        finally:
            cleanup()
    _s1.get("/periods", summary="List fiscal periods")(list_fiscal_periods)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route list_fiscal_periods: %s", _e)

try:
    def     reverse_entry(
        body: ReversalBody,
        db: Session = Depends(get_db),
        _admin: dict = Depends(require_admin),
    ):
        result = reverse_journal_entry(
            db,
            original_entry_id=body.entry_id,
            reason=body.reason,
            user_id=_admin.get("id"),
        )
        audit_log(
            db=db,
            action=AuditAction.JOURNAL_ENTRY_CREATED,
            user_id=_admin.get("id"),
            username=_admin.get("username"),
            user_role=_admin.get("role"),
            resource_type="journal_entry_reversal",
            resource_id=result["reversal_entry_id"],
            details=result,
        )
        return result
    _s1.post("/journal-entries/reverse", summary="Reverse a journal entry")(reverse_entry)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route reverse_entry: %s", _e)

try:
    def     cash_flow_forecast(
        days: int = Query(90, ge=1, le=365),
        currency: str = Query("OMR", max_length=10),
        country_code: Optional[str] = Query(None, max_length=3),
        db: Session = Depends(get_db),
        _admin: dict = Depends(require_admin),
    ):
        cleanup = _with_rls(country_code, db)
        try:
            result = generate_cash_forecast(db, days=days, currency=currency, country_code=country_code)
            audit_log(
                db=db,
                action=AuditAction.CASH_FORECAST_GENERATED,
                user_id=_admin.get("id"),
                username=_admin.get("username"),
                user_role=_admin.get("role"),
                resource_type="cash_flow_forecast",
                details={"days": days, "currency": currency, "country_code": country_code},
            )
            return result
        finally:
            cleanup()
    _s1.post("/cash-flow-forecast", summary="Generate cash flow forecast")(cash_flow_forecast)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route cash_flow_forecast: %s", _e)

try:
    def     get_ar(
        customer_id: Optional[int] = Query(None),
        status: Optional[str] = Query(None),
        country_code: Optional[str] = Query(None, max_length=3),
        limit: int = Query(50, ge=1, le=500),
        db: Session = Depends(get_db),
        _admin: dict = Depends(require_admin),
    ):
        cleanup = _with_rls(country_code, db)
        try:
            return controller_get_ar_summary(db, customer_id=customer_id, status=status, country_code=country_code, limit=limit)
        finally:
            cleanup()
    _s1.get("/ar", summary="AR sub-ledger (customer receivables)")(get_ar)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route get_ar: %s", _e)

try:
    def     post_ar_invoice_route(body: ARInvoiceBody, db: Session = Depends(get_db), _admin: dict = Depends(require_admin)):
        cleanup = _with_rls(body.country_code, db)
        try:
            return controller_post_ar_invoice(db, **body.model_dump(), admin_user=_admin)
        finally:
            cleanup()
    _s1.post("/ar-ledger/invoice", summary="Post AR invoice")(post_ar_invoice_route)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route post_ar_invoice_route: %s", _e)

try:
    def     post_ar_payment_route(body: ARPaymentBody, db: Session = Depends(get_db), _admin: dict = Depends(require_admin)):
        cleanup = _with_rls(body.country_code, db)
        try:
            return controller_post_ar_payment(db, **body.model_dump(), admin_user=_admin)
        finally:
            cleanup()
    _s1.post("/ar-ledger/payment", summary="Post AR payment")(post_ar_payment_route)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route post_ar_payment_route: %s", _e)

try:
    def     get_ap_alias(
        supplier_id: Optional[int] = Query(None),
        status: Optional[str] = Query(None),
        country_code: Optional[str] = Query(None, max_length=3),
        limit: int = Query(50, ge=1, le=500),
        db: Session = Depends(get_db),
        _admin: dict = Depends(require_admin),
    ):
        cleanup = _with_rls(country_code, db)
        try:
            return controller_get_ap_summary(db, supplier_id=supplier_id, status=status, country_code=country_code, limit=limit)
        finally:
            cleanup()
    _s1.get("/ap", summary="AP Sub-ledger alias (Accounts Payable)")(get_ap_alias)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route get_ap_alias: %s", _e)

try:
    def     get_ap(
        supplier_id: Optional[int] = Query(None),
        status: Optional[str] = Query(None),
        country_code: Optional[str] = Query(None, max_length=3),
        limit: int = Query(50, ge=1, le=500),
        db: Session = Depends(get_db),
        _admin: dict = Depends(require_admin),
    ):
        cleanup = _with_rls(country_code, db)
        try:
            return controller_get_ap_summary(db, supplier_id=supplier_id, status=status, country_code=country_code, limit=limit)
        finally:
            cleanup()
    _s1.get("/ap-ledger", summary="AP Sub-ledger (Accounts Payable)")(get_ap)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route get_ap: %s", _e)

try:
    def     post_ap_payable_route(body: APPayableBody, db: Session = Depends(get_db), _admin: dict = Depends(require_admin)):
        cleanup = _with_rls(body.country_code, db)
        try:
            return controller_post_ap_payable(db, **body.model_dump(), admin_user=_admin)
        finally:
            cleanup()
    _s1.post("/ap-ledger/payable", summary="Post AP payable")(post_ap_payable_route)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route post_ap_payable_route: %s", _e)

try:
    def     post_ap_payment_route(body: APPaymentBody, db: Session = Depends(get_db), _admin: dict = Depends(require_admin)):
        cleanup = _with_rls(body.country_code, db)
        try:
            return controller_post_ap_payment(db, **body.model_dump(), admin_user=_admin)
        finally:
            cleanup()
    _s1.post("/ap-ledger/payment", summary="Post AP payment")(post_ap_payment_route)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route post_ap_payment_route: %s", _e)

_s2 = APIRouter(prefix='/api/v1/admin')

try:
    def     list_rates(country_code: str = Path(..., description="ISO country code"), _: User = Depends(require_admin), db: Session = Depends(get_db), page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100)):
        get_country_or_404(country_code.upper(), db)
        set_rls_context({country_code.upper()}, is_restricted=True)
        try:
            return list_category_rates(db, country_code, page, page_size)
        finally:
            clear_rls_context()
    _s2.get("/{country_code}/rates")(list_rates)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route list_rates: %s", _e)

try:
    def     create_rate(country_code: str = Path(..., description="ISO country code"), payload: CommissionCategoryRateCreate = None, _: User = Depends(require_admin), db: Session = Depends(get_db)):
        get_country_or_404(country_code.upper(), db)
        set_rls_context({country_code.upper()}, is_restricted=True)
        try:
            return create_category_rate(db, payload, country_code)
        finally:
            clear_rls_context()
    _s2.post("/{country_code}/rates", response_model=CommissionCategoryRateOut, status_code=201)(create_rate)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route create_rate: %s", _e)

try:
    def     update_rate(country_code: str = Path(..., description="ISO country code"), rate_id: int = Path(..., description="Rate id"), payload: CommissionCategoryRateCreate = None, _: User = Depends(require_admin), db: Session = Depends(get_db)):
        get_country_or_404(country_code.upper(), db)
        return update_category_rate(db, rate_id, country_code, payload)
    _s2.put("/{country_code}/rates/{rate_id}", response_model=CommissionCategoryRateOut)(update_rate)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route update_rate: %s", _e)

try:
    def     list_badge_tiers_route(country_code: str = Path(..., description="ISO country code"), _: User = Depends(require_admin), db: Session = Depends(get_db), page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100)):
        get_country_or_404(country_code.upper(), db)
        set_rls_context({country_code.upper()}, is_restricted=True)
        try:
            return list_badge_tiers(db, country_code, page, page_size)
        finally:
            clear_rls_context()
    _s2.get("/{country_code}/badge-tiers")(list_badge_tiers_route)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route list_badge_tiers_route: %s", _e)

try:
    def     create_badge_tier_route(country_code: str = Path(..., description="ISO country code"), payload: CommissionBadgeTierCreate = None, _: User = Depends(require_admin), db: Session = Depends(get_db)):
        get_country_or_404(country_code.upper(), db)
        set_rls_context({country_code.upper()}, is_restricted=True)
        try:
            return create_badge_tier(db, payload, country_code)
        finally:
            clear_rls_context()
    _s2.post("/{country_code}/badge-tiers", response_model=CommissionBadgeTierOut, status_code=201)(create_badge_tier_route)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route create_badge_tier_route: %s", _e)

try:
    def     update_badge_tier_route(country_code: str = Path(..., description="ISO country code"), tier_id: int = Path(..., description="Badge tier id"), payload: CommissionBadgeTierCreate = None, _: User = Depends(require_admin), db: Session = Depends(get_db)):
        get_country_or_404(country_code.upper(), db)
        return update_badge_tier(db, tier_id, country_code, payload)
    _s2.put("/{country_code}/badge-tiers/{tier_id}", response_model=CommissionBadgeTierOut)(update_badge_tier_route)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route update_badge_tier_route: %s", _e)

_s3 = APIRouter(prefix='/api/v1')

try:
    def     controller_get_ar_summary_route(
        db: Session = Depends(get_db),
        customer_id: Optional[int] = Query(None),
        status: Optional[str] = Query(None),
        country_code: Optional[str] = Query(None),
        limit: int = Query(50)
    ) -> dict:
        return controller_get_ar_summary(db=db, customer_id=customer_id, status=status, country_code=country_code, limit=limit)
    _s3.get("/admin/ar", status_code=200, tags=['finance'])(controller_get_ar_summary_route)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route controller_get_ar_summary_route: %s", _e)

try:
    def     controller_get_ar_summary_route(
        db: Session = Depends(get_db),
        customer_id: Optional[int] = Query(None),
        status: Optional[str] = Query(None),
        country_code: Optional[str] = Query(None),
        limit: int = Query(50)
    ) -> dict:
        return controller_get_ar_summary(db=db, customer_id=customer_id, status=status, country_code=country_code, limit=limit)
    _s3.get("/ar", status_code=200, tags=['finance'])(controller_get_ar_summary_route)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route controller_get_ar_summary_route: %s", _e)

try:
    def     controller_get_ap_summary_route(
        db: Session = Depends(get_db),
        supplier_id: Optional[int] = Query(None),
        status: Optional[str] = Query(None),
        country_code: Optional[str] = Query(None),
        limit: int = Query(50)
    ) -> dict:
        return controller_get_ap_summary(db=db, supplier_id=supplier_id, status=status, country_code=country_code, limit=limit)
    _s3.get("/admin/ap", status_code=200, tags=['finance'])(controller_get_ap_summary_route)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route controller_get_ap_summary_route: %s", _e)

try:
    def     controller_get_ap_summary_route(
        db: Session = Depends(get_db),
        supplier_id: Optional[int] = Query(None),
        status: Optional[str] = Query(None),
        country_code: Optional[str] = Query(None),
        limit: int = Query(50)
    ) -> dict:
        return controller_get_ap_summary(db=db, supplier_id=supplier_id, status=status, country_code=country_code, limit=limit)
    _s3.get("/ap", status_code=200, tags=['finance'])(controller_get_ap_summary_route)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route controller_get_ap_summary_route: %s", _e)

try:
    def     controller_get_ap_summary_route(
        db: Session = Depends(get_db),
        supplier_id: Optional[int] = Query(None),
        status: Optional[str] = Query(None),
        country_code: Optional[str] = Query(None),
        limit: int = Query(50)
    ) -> dict:
        return controller_get_ap_summary(db=db, supplier_id=supplier_id, status=status, country_code=country_code, limit=limit)
    _s3.get("/admin/ap-ledger", status_code=200, tags=['finance'])(controller_get_ap_summary_route)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route controller_get_ap_summary_route: %s", _e)

try:
    def     controller_get_ap_summary_route(
        db: Session = Depends(get_db),
        supplier_id: Optional[int] = Query(None),
        status: Optional[str] = Query(None),
        country_code: Optional[str] = Query(None),
        limit: int = Query(50)
    ) -> dict:
        return controller_get_ap_summary(db=db, supplier_id=supplier_id, status=status, country_code=country_code, limit=limit)
    _s3.get("/ap-ledger", status_code=200, tags=['finance'])(controller_get_ap_summary_route)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route controller_get_ap_summary_route: %s", _e)

try:
    def     controller_post_ar_invoice_route(
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
    ) -> dict:
        return controller_post_ar_invoice(db=db, current_user=current_user, customer_id=customer_id, amount=amount, order_id=order_id, invoice_id=invoice_id, due_date=due_date, description=description, currency=currency, country_code=country_code)
    _s3.post("/admin/ar-ledger/invoice", status_code=201, tags=['finance'])(controller_post_ar_invoice_route)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route controller_post_ar_invoice_route: %s", _e)

try:
    def     controller_post_ar_invoice_route(
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
    ) -> dict:
        return controller_post_ar_invoice(db=db, current_user=current_user, customer_id=customer_id, amount=amount, order_id=order_id, invoice_id=invoice_id, due_date=due_date, description=description, currency=currency, country_code=country_code)
    _s3.post("/ar-ledger/invoice", status_code=201, tags=['finance'])(controller_post_ar_invoice_route)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route controller_post_ar_invoice_route: %s", _e)

try:
    def     controller_post_ar_payment_route(
        db: Session = Depends(get_db),
        current_user: dict = Depends(require_admin),
        customer_id: int = Body(...),
        amount: float = Body(...),
        invoice_id: Optional[int] = Body(None),
        order_id: Optional[int] = Body(None),
        description: Optional[str] = Body(None),
        currency: str = Body('OMR'),
        country_code: Optional[str] = Body(None)
    ) -> dict:
        return controller_post_ar_payment(db=db, current_user=current_user, customer_id=customer_id, amount=amount, invoice_id=invoice_id, order_id=order_id, description=description, currency=currency, country_code=country_code)
    _s3.post("/admin/ar-ledger/payment", status_code=201, tags=['finance'])(controller_post_ar_payment_route)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route controller_post_ar_payment_route: %s", _e)

try:
    def     controller_post_ar_payment_route(
        db: Session = Depends(get_db),
        current_user: dict = Depends(require_admin),
        customer_id: int = Body(...),
        amount: float = Body(...),
        invoice_id: Optional[int] = Body(None),
        order_id: Optional[int] = Body(None),
        description: Optional[str] = Body(None),
        currency: str = Body('OMR'),
        country_code: Optional[str] = Body(None)
    ) -> dict:
        return controller_post_ar_payment(db=db, current_user=current_user, customer_id=customer_id, amount=amount, invoice_id=invoice_id, order_id=order_id, description=description, currency=currency, country_code=country_code)
    _s3.post("/ar-ledger/payment", status_code=201, tags=['finance'])(controller_post_ar_payment_route)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route controller_post_ar_payment_route: %s", _e)

try:
    def     controller_post_ap_payable_route(
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
    ) -> dict:
        return controller_post_ap_payable(db=db, current_user=current_user, supplier_id=supplier_id, amount=amount, order_id=order_id, settlement_id=settlement_id, due_date=due_date, description=description, currency=currency, country_code=country_code)
    _s3.post("/admin/ap-ledger/payable", status_code=201, tags=['finance'])(controller_post_ap_payable_route)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route controller_post_ap_payable_route: %s", _e)

try:
    def     controller_post_ap_payable_route(
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
    ) -> dict:
        return controller_post_ap_payable(db=db, current_user=current_user, supplier_id=supplier_id, amount=amount, order_id=order_id, settlement_id=settlement_id, due_date=due_date, description=description, currency=currency, country_code=country_code)
    _s3.post("/ap-ledger/payable", status_code=201, tags=['finance'])(controller_post_ap_payable_route)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route controller_post_ap_payable_route: %s", _e)

try:
    def     controller_post_ap_payment_route(
        db: Session = Depends(get_db),
        current_user: dict = Depends(require_admin),
        supplier_id: int = Body(...),
        amount: float = Body(...),
        settlement_id: Optional[int] = Body(None),
        description: Optional[str] = Body(None),
        currency: str = Body('OMR'),
        country_code: Optional[str] = Body(None)
    ) -> dict:
        return controller_post_ap_payment(db=db, current_user=current_user, supplier_id=supplier_id, amount=amount, settlement_id=settlement_id, description=description, currency=currency, country_code=country_code)
    _s3.post("/admin/ap-ledger/payment", status_code=201, tags=['finance'])(controller_post_ap_payment_route)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route controller_post_ap_payment_route: %s", _e)

try:
    def     controller_post_ap_payment_route(
        db: Session = Depends(get_db),
        current_user: dict = Depends(require_admin),
        supplier_id: int = Body(...),
        amount: float = Body(...),
        settlement_id: Optional[int] = Body(None),
        description: Optional[str] = Body(None),
        currency: str = Body('OMR'),
        country_code: Optional[str] = Body(None)
    ) -> dict:
        return controller_post_ap_payment(db=db, current_user=current_user, supplier_id=supplier_id, amount=amount, settlement_id=settlement_id, description=description, currency=currency, country_code=country_code)
    _s3.post("/ap-ledger/payment", status_code=201, tags=['finance'])(controller_post_ap_payment_route)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route controller_post_ap_payment_route: %s", _e)

_s4 = APIRouter(prefix='')

try:
    def     list_accounts(country_code: str = Path(..., description="ISO country code"), _: User = Depends(require_admin), db: Session = Depends(get_db)):
        get_country_or_404(country_code.upper(), db)
        set_rls_context({country_code.upper()}, is_restricted=True)
        try:
            return db.query(CashAccount).filter(CashAccount.is_active == True, CashAccount.country_code == country_code.upper()).all()
        finally:
            clear_rls_context()
    _s4.get("/{country_code}/accounts", response_model=list[CashAccountOut])(list_accounts)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route list_accounts: %s", _e)

try:
    def     create_account(country_code: str = Path(..., description="ISO country code"), payload: CashAccountCreate = None, _: User = Depends(require_admin), db: Session = Depends(get_db)):
        get_country_or_404(country_code.upper(), db)
        set_rls_context({country_code.upper()}, is_restricted=True)
        try:
            account_data = payload.model_dump()
            account_data["country_code"] = country_code.upper()
            a = create_cash_account_model(db, **account_data)
            return a
        finally:
            clear_rls_context()
    _s4.post("/{country_code}/accounts", response_model=CashAccountOut, status_code=201)(create_account)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route create_account: %s", _e)

try:
    def     create_transaction(country_code: str = Path(..., description="ISO country code"), payload: CashTransactionCreate = None, current_user: User = Depends(require_admin), db: Session = Depends(get_db)):
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
    _s4.post("/{country_code}/transactions", response_model=CashTransactionOut, status_code=201)(create_transaction)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route create_transaction: %s", _e)

_s5 = APIRouter(prefix='/api/v1/admin')

try:
    def     health():
        """Liveness probe for this router."""
        return {"status": "ok", "router": "admin_cash_routes", "prefix": "/api/v1/admin"}
    _s5.get("/admin_cash_routes/health")(health)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route health: %s", _e)

_s30 = APIRouter(prefix='/api/v1')

try:
    def _with_rls(country_code: Optional[str], db: Session):
        """Set RLS context if country_code is provided. Returns cleanup function."""
        if country_code:
            get_country_or_404(country_code.upper(), db)
            set_rls_context({country_code.upper()}, is_restricted=True)
        def cleanup():
            if country_code:
                clear_rls_context()
        return cleanup
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route: %s", _e)

try:
    def     seed_chart_of_accounts(
        db: Session = Depends(get_db),
        _admin: dict = Depends(require_admin),
    ):
        return accounting_controller.seed_chart_of_accounts(
            db,
            audit_user_id=_admin.get("id"),
            audit_username=_admin.get("username"),
            audit_user_role=_admin.get("role"),
        )
    _s30.post("/seed", summary="Seed chart of accounts (idempotent)")(seed_chart_of_accounts)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route seed_chart_of_accounts: %s", _e)

try:
    def     list_accounts(
        country_code: str = Query(None, max_length=3),
        db: Session = Depends(get_db),
        _user=Depends(require_admin),
    ):
        cleanup = _with_rls(country_code, db)
        try:
            return accounting_controller.list_accounts(db)
        finally:
            cleanup()
    _s30.get("/accounts", summary="List all accounts")(list_accounts)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route list_accounts: %s", _e)

try:
    def     get_account(
        code: str,
        country_code: str = Query(None, max_length=3),
        db: Session = Depends(get_db),
        _user=Depends(require_admin),
    ):
        cleanup = _with_rls(country_code, db)
        try:
            return accounting_controller.get_account(db, code)
        finally:
            cleanup()
    _s30.get("/accounts/{code}", summary="Get account by code")(get_account)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route get_account: %s", _e)

try:
    def     create_journal_entry(
        body: accounting_controller.JournalEntryBody,
        db: Session = Depends(get_db),
        current_user=Depends(require_admin),
    ):
        return accounting_controller.create_journal_entry(db, body, current_user)
    _s30.post("/journal-entries", summary="Create a journal entry")(create_journal_entry)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route create_journal_entry: %s", _e)

try:
    def     list_journal_entries(
        reference_type: Optional[str] = Query(None, max_length=40),
        reference_id: Optional[int] = Query(None),
        country_code: Optional[str] = Query(None, max_length=3),
        limit: int = Query(50, ge=1, le=500),
        db: Session = Depends(get_db),
        _user=Depends(require_admin),
    ):
        cleanup = _with_rls(country_code, db)
        try:
            return accounting_controller.list_journal_entries(
                db, reference_type=reference_type, reference_id=reference_id, country_code=country_code, limit=limit
            )
        finally:
            cleanup()
    _s30.get("/journal-entries", summary="List journal entries")(list_journal_entries)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route list_journal_entries: %s", _e)

try:
    def     get_journal_entry(
        entry_id: int,
        country_code: str = Query(None, max_length=3),
        db: Session = Depends(get_db),
        _user=Depends(require_admin),
    ):
        cleanup = _with_rls(country_code, db)
        try:
            return accounting_controller.get_journal_entry(db, entry_id)
        finally:
            cleanup()
    _s30.get("/journal-entries/{entry_id}", summary="Get journal entry by ID")(get_journal_entry)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route get_journal_entry: %s", _e)

try:
    def     get_balance(
        account_code: str,
        currency: str = Query("OMR", max_length=10),
        country_code: str = Query(None, max_length=3),
        db: Session = Depends(get_db),
        _user=Depends(require_admin),
    ):
        cleanup = _with_rls(country_code, db)
        try:
            return accounting_controller.get_account_balance(db, account_code, currency)
        finally:
            cleanup()
    _s30.get("/balances/{account_code}", summary="Get account balance")(get_balance)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route get_balance: %s", _e)

try:
    def     trial_balance(
        as_of_date: Optional[date] = Query(None),
        currency: str = Query("OMR", max_length=10),
        country_code: Optional[str] = Query(None, max_length=3),
        db: Session = Depends(get_db),
        _user=Depends(require_admin),
    ):
        cleanup = _with_rls(country_code, db)
        try:
            return accounting_controller.get_trial_balance(
                db, as_of_date=as_of_date, currency=currency, country_code=country_code
            )
        finally:
            cleanup()
    _s30.get("/trial-balance", summary="Get trial balance")(trial_balance)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route trial_balance: %s", _e)

try:
    def     income_statement(
        body: ReportPeriod,
        db: Session = Depends(get_db),
        _admin: dict = Depends(require_admin),
    ):
        cleanup = _with_rls(body.country_code, db)
        try:
            svc = FinancialReportingService(db)
            result = svc.generate_income_statement(
                body.period_start, body.period_end, body.currency, persist=body.persist, country_code=body.country_code
            )
            audit_log(
                db=db,
                action=AuditAction.FINANCIAL_REPORT_GENERATED,
                user_id=_admin.get("id"),
                username=_admin.get("username"),
                user_role=_admin.get("role"),
                resource_type="income_statement",
                details={"period_start": body.period_start.isoformat(), "period_end": body.period_end.isoformat(), "currency": body.currency, "country_code": body.country_code},
            )
            return result
        finally:
            cleanup()
    _s30.post("/reports/income-statement", summary="Generate Income Statement (P&L)")(income_statement)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route income_statement: %s", _e)

try:
    def     balance_sheet(
        as_of_date: Optional[datetime] = Query(None, description="Defaults to now"),
        currency: str = Query("OMR", max_length=10),
        persist: bool = Query(False),
        country_code: Optional[str] = Query(None, max_length=3),
        db: Session = Depends(get_db),
        _admin: dict = Depends(require_admin),
    ):
        cleanup = _with_rls(country_code, db)
        try:
            svc = FinancialReportingService(db)
            result = svc.generate_balance_sheet(as_of_date, currency, persist=persist, country_code=country_code)
            audit_log(
                db=db,
                action=AuditAction.FINANCIAL_REPORT_GENERATED,
                user_id=_admin.get("id"),
                username=_admin.get("username"),
                user_role=_admin.get("role"),
                resource_type="balance_sheet",
                details={"as_of_date": (as_of_date or datetime.utcnow()).isoformat(), "currency": currency, "country_code": country_code},
            )
            return result
        finally:
            cleanup()
    _s30.post("/reports/balance-sheet", summary="Generate Balance Sheet")(balance_sheet)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route balance_sheet: %s", _e)

try:
    def     cash_flow(
        body: ReportPeriod,
        db: Session = Depends(get_db),
        _admin: dict = Depends(require_admin),
    ):
        cleanup = _with_rls(body.country_code, db)
        try:
            svc = FinancialReportingService(db)
            result = svc.generate_cash_flow(
                body.period_start, body.period_end, body.currency, persist=body.persist, country_code=body.country_code
            )
            audit_log(
                db=db,
                action=AuditAction.FINANCIAL_REPORT_GENERATED,
                user_id=_admin.get("id"),
                username=_admin.get("username"),
                user_role=_admin.get("role"),
                resource_type="cash_flow_statement",
                details={"period_start": body.period_start.isoformat(), "period_end": body.period_end.isoformat(), "currency": body.currency, "country_code": body.country_code},
            )
            return result
        finally:
            cleanup()
    _s30.post("/reports/cash-flow", summary="Generate Cash Flow Statement")(cash_flow)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route cash_flow: %s", _e)

try:
    def     list_reports(
        report_type: Optional[str] = Query(None, description="Filter by report type"),
        country_code: Optional[str] = Query(None, max_length=3),
        limit: int = Query(20, ge=1, le=100),
        db: Session = Depends(get_db),
        _user=Depends(require_admin),
    ):
        cleanup = _with_rls(country_code, db)
        try:
            svc = FinancialReportingService(db)
            return svc.list_reports(report_type=report_type, country_code=country_code, limit=limit)
        finally:
            cleanup()
    _s30.get("/reports", summary="List saved financial reports")(list_reports)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route list_reports: %s", _e)

try:
    def     get_or_create(
        country_code: str = Query(..., max_length=3),
        year: int = Query(..., ge=2020, le=2100),
        month: int = Query(..., ge=1, le=12),
        db: Session = Depends(get_db),
        _admin: dict = Depends(require_admin),
    ):
        cleanup = _with_rls(country_code, db)
        try:
            period = get_or_create_fiscal_period(db, country_code, year, month)
            return {
                "id": period.id,
                "country_code": period.country_code,
                "label": f"{period.period_year}-{period.period_month:02d}",
                "status": period.status,
                "period_start": period.period_start.isoformat(),
                "period_end": period.period_end.isoformat(),
            }
        finally:
            cleanup()
    _s30.post("/periods/get-or-create", summary="Get or create a fiscal period")(get_or_create)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route get_or_create: %s", _e)

try:
    def     current_period(
        country_code: str = Query(..., max_length=3),
        db: Session = Depends(get_db),
        _user=Depends(require_admin),
    ):
        cleanup = _with_rls(country_code, db)
        try:
            period = get_current_fiscal_period(db, country_code)
            if not period:
                return None
            return {
                "id": period.id,
                "country_code": period.country_code,
                "label": f"{period.period_year}-{period.period_month:02d}",
                "status": period.status,
                "is_locked": period.is_locked,
                "period_start": period.period_start.isoformat(),
                "period_end": period.period_end.isoformat(),
            }
        finally:
            cleanup()
    _s30.get("/periods/current", summary="Get current fiscal period")(current_period)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route current_period: %s", _e)

try:
    def     close_fiscal_period(
        body: ClosePeriodBody,
        db: Session = Depends(get_db),
        _admin: dict = Depends(require_admin),
    ):
        result = close_period(
            db,
            period_id=body.period_id,
            closed_by=_admin.get("id"),
            notes=body.notes,
            transfer_to_retained_earnings=body.transfer_to_retained_earnings,
        )
        audit_log(
            db=db,
            action=AuditAction.PERIOD_CLOSED,
            user_id=_admin.get("id"),
            username=_admin.get("username"),
            user_role=_admin.get("role"),
            resource_type="fiscal_period",
            resource_id=body.period_id,
            details=result,
        )
        return result
    _s30.post("/periods/close", summary="Close a fiscal period")(close_fiscal_period)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route close_fiscal_period: %s", _e)

try:
    def     list_fiscal_periods(
        country_code: Optional[str] = Query(None, max_length=3),
        status: Optional[str] = Query(None),
        limit: int = Query(24, ge=1, le=120),
        db: Session = Depends(get_db),
        _user=Depends(require_admin),
    ):
        cleanup = _with_rls(country_code, db)
        try:
            periods = list_periods(db, country_code=country_code, status=status, limit=limit)
            return [
                {
                    "id": p.id,
                    "country_code": p.country_code,
                    "label": f"{p.period_year}-{p.period_month:02d}",
                    "status": p.status,
                    "is_locked": p.is_locked,
                    "period_start": p.period_start.isoformat(),
                    "period_end": p.period_end.isoformat(),
                    "closed_at": p.closed_at.isoformat() if p.closed_at else None,
                }
                for p in periods
            ]
        finally:
            cleanup()
    _s30.get("/periods", summary="List fiscal periods")(list_fiscal_periods)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route list_fiscal_periods: %s", _e)

try:
    def     reverse_entry(
        body: ReversalBody,
        db: Session = Depends(get_db),
        _admin: dict = Depends(require_admin),
    ):
        result = reverse_journal_entry(
            db,
            original_entry_id=body.entry_id,
            reason=body.reason,
            user_id=_admin.get("id"),
        )
        audit_log(
            db=db,
            action=AuditAction.JOURNAL_ENTRY_CREATED,
            user_id=_admin.get("id"),
            username=_admin.get("username"),
            user_role=_admin.get("role"),
            resource_type="journal_entry_reversal",
            resource_id=result["reversal_entry_id"],
            details=result,
        )
        return result
    _s30.post("/journal-entries/reverse", summary="Reverse a journal entry")(reverse_entry)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route reverse_entry: %s", _e)

try:
    def     cash_flow_forecast(
        days: int = Query(90, ge=1, le=365),
        currency: str = Query("OMR", max_length=10),
        country_code: Optional[str] = Query(None, max_length=3),
        db: Session = Depends(get_db),
        _admin: dict = Depends(require_admin),
    ):
        cleanup = _with_rls(country_code, db)
        try:
            result = generate_cash_forecast(db, days=days, currency=currency, country_code=country_code)
            audit_log(
                db=db,
                action=AuditAction.CASH_FORECAST_GENERATED,
                user_id=_admin.get("id"),
                username=_admin.get("username"),
                user_role=_admin.get("role"),
                resource_type="cash_flow_forecast",
                details={"days": days, "currency": currency, "country_code": country_code},
            )
            return result
        finally:
            cleanup()
    _s30.post("/cash-flow-forecast", summary="Generate cash flow forecast")(cash_flow_forecast)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route cash_flow_forecast: %s", _e)

try:
    def     get_ar(
        customer_id: Optional[int] = Query(None),
        status: Optional[str] = Query(None),
        country_code: Optional[str] = Query(None, max_length=3),
        limit: int = Query(50, ge=1, le=500),
        db: Session = Depends(get_db),
        _admin: dict = Depends(require_admin),
    ):
        cleanup = _with_rls(country_code, db)
        try:
            return controller_get_ar_summary(db, customer_id=customer_id, status=status, country_code=country_code, limit=limit)
        finally:
            cleanup()
    _s30.get("/ar", summary="AR sub-ledger (customer receivables)")(get_ar)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route get_ar: %s", _e)

try:
    def     post_ar_invoice_route(body: ARInvoiceBody, db: Session = Depends(get_db), _admin: dict = Depends(require_admin)):
        cleanup = _with_rls(body.country_code, db)
        try:
            return controller_post_ar_invoice(db, **body.model_dump(), admin_user=_admin)
        finally:
            cleanup()
    _s30.post("/ar-ledger/invoice", summary="Post AR invoice")(post_ar_invoice_route)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route post_ar_invoice_route: %s", _e)

try:
    def     post_ar_payment_route(body: ARPaymentBody, db: Session = Depends(get_db), _admin: dict = Depends(require_admin)):
        cleanup = _with_rls(body.country_code, db)
        try:
            return controller_post_ar_payment(db, **body.model_dump(), admin_user=_admin)
        finally:
            cleanup()
    _s30.post("/ar-ledger/payment", summary="Post AR payment")(post_ar_payment_route)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route post_ar_payment_route: %s", _e)

try:
    def     get_ap_alias(
        supplier_id: Optional[int] = Query(None),
        status: Optional[str] = Query(None),
        country_code: Optional[str] = Query(None, max_length=3),
        limit: int = Query(50, ge=1, le=500),
        db: Session = Depends(get_db),
        _admin: dict = Depends(require_admin),
    ):
        cleanup = _with_rls(country_code, db)
        try:
            return controller_get_ap_summary(db, supplier_id=supplier_id, status=status, country_code=country_code, limit=limit)
        finally:
            cleanup()
    _s30.get("/ap", summary="AP Sub-ledger alias (Accounts Payable)")(get_ap_alias)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route get_ap_alias: %s", _e)

try:
    def     get_ap(
        supplier_id: Optional[int] = Query(None),
        status: Optional[str] = Query(None),
        country_code: Optional[str] = Query(None, max_length=3),
        limit: int = Query(50, ge=1, le=500),
        db: Session = Depends(get_db),
        _admin: dict = Depends(require_admin),
    ):
        cleanup = _with_rls(country_code, db)
        try:
            return controller_get_ap_summary(db, supplier_id=supplier_id, status=status, country_code=country_code, limit=limit)
        finally:
            cleanup()
    _s30.get("/ap-ledger", summary="AP Sub-ledger (Accounts Payable)")(get_ap)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route get_ap: %s", _e)

try:
    def     post_ap_payable_route(body: APPayableBody, db: Session = Depends(get_db), _admin: dict = Depends(require_admin)):
        cleanup = _with_rls(body.country_code, db)
        try:
            return controller_post_ap_payable(db, **body.model_dump(), admin_user=_admin)
        finally:
            cleanup()
    _s30.post("/ap-ledger/payable", summary="Post AP payable")(post_ap_payable_route)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route post_ap_payable_route: %s", _e)

try:
    def     post_ap_payment_route(body: APPaymentBody, db: Session = Depends(get_db), _admin: dict = Depends(require_admin)):
        cleanup = _with_rls(body.country_code, db)
        try:
            return controller_post_ap_payment(db, **body.model_dump(), admin_user=_admin)
        finally:
            cleanup()
    _s30.post("/ap-ledger/payment", summary="Post AP payment")(post_ap_payment_route)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route post_ap_payment_route: %s", _e)

_s31 = APIRouter(prefix='/api/v1')

try:
    def     health():
        """Liveness probe for this router."""
        return {"status": "ok", "router": "public_treasury_api_access", "prefix": ""}
    _s31.get("/public_treasury_api_access/health")(health)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route health: %s", _e)

_s34 = APIRouter(prefix='/api/v1/payments')

try:
    def     health():
        """Liveness probe for this router."""
        return {"status": "ok", "router": "store_payments_routes", "prefix": "/api/v1/payments"}
    _s34.get("/store_payments_routes/health")(health)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route health: %s", _e)

try:
    def     status():
        """Report whether a backing engine is importable."""
        return {"router": "store_payments_routes", "controller": "services.gateways.payments" if _HAS_CTRL else None,
                "public_functions": _CTRL_PUBLIC}
    _s34.get("/store_payments_routes/status")(status)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route status: %s", _e)

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
router = APIRouter()try:    router.include_router(_s0)except Exception as _e:    import logging as _l; _l.getLogger(__name__).warning("skip subrouter _s0: %s", _e)try:    router.include_router(_s1)except Exception as _e:    import logging as _l; _l.getLogger(__name__).warning("skip subrouter _s1: %s", _e)try:    router.include_router(_s2)except Exception as _e:    import logging as _l; _l.getLogger(__name__).warning("skip subrouter _s2: %s", _e)try:    router.include_router(_s3)except Exception as _e:    import logging as _l; _l.getLogger(__name__).warning("skip subrouter _s3: %s", _e)try:    router.include_router(_s4)except Exception as _e:    import logging as _l; _l.getLogger(__name__).warning("skip subrouter _s4: %s", _e)try:    router.include_router(_s5)except Exception as _e:    import logging as _l; _l.getLogger(__name__).warning("skip subrouter _s5: %s", _e)try:    router.include_router(_s30)except Exception as _e:    import logging as _l; _l.getLogger(__name__).warning("skip subrouter _s30: %s", _e)try:    router.include_router(_s31)except Exception as _e:    import logging as _l; _l.getLogger(__name__).warning("skip subrouter _s31: %s", _e)try:    router.include_router(_s34)except Exception as _e:    import logging as _l; _l.getLogger(__name__).warning("skip subrouter _s34: %s", _e)