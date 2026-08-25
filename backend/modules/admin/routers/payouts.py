"""Admin payouts router � split from finance.py."""
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

_s6 = APIRouter(prefix='/api/v1/admin/finance')

try:
    def     list_pending_payouts_route_route(
        country_code: str,
        page: int = Query(1),
        page_size: int = Query(50),
        current_user: dict = Depends(require_admin),
        db: Session = Depends(get_db)
    ):
        return list_pending_payouts_route(country_code=country_code, page=page, page_size=page_size, current_user=current_user, db=db)
    _s6.get("/payouts/{country_code}/pending", status_code=200, tags=['admin-payouts'])(list_pending_payouts_route_route)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route list_pending_payouts_route_route: %s", _e)

try:
    def     verify_payout_route_route(
        country_code: str,
        payout_id: int,
        current_user: dict = Depends(require_admin),
        db: Session = Depends(get_db),
        status: str = Body('completed'),
        reference: Optional[str] = Body(None),
        notes: Optional[str] = Body(None)
    ):
        return verify_payout_route(country_code=country_code, payout_id=payout_id, current_user=current_user, db=db, status=status, reference=reference, notes=notes)
    _s6.post("/payouts/{country_code}/{payout_id}/verify", status_code=201, tags=['admin-payouts'])(verify_payout_route_route)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route verify_payout_route_route: %s", _e)

try:
    def     list_accounts(country_code: str = Path(..., description="ISO country code"), _: User = Depends(require_admin), db: Session = Depends(get_db)):
        get_country_or_404(country_code.upper(), db)
        set_rls_context({country_code.upper()}, is_restricted=True)
        try:
            return db.query(CashAccount).filter(CashAccount.is_active == True, CashAccount.country_code == country_code.upper()).all()
        finally:
            clear_rls_context()
    _s6.get("/{country_code}/accounts", response_model=list[CashAccountOut])(list_accounts)
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
    _s6.post("/{country_code}/accounts", response_model=CashAccountOut, status_code=201)(create_account)
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
    _s6.post("/{country_code}/transactions", response_model=CashTransactionOut, status_code=201)(create_transaction)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route create_transaction: %s", _e)

try:
    def     health():
        """Liveness probe for this router."""
        return {"status": "ok", "router": "admin_cash_routes", "prefix": "/api/v1/admin"}
    _s6.get("/admin_cash_routes/health")(health)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route health: %s", _e)

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
    _s6.get("/{country_code}/rates")(list_rates)
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
    _s6.post("/{country_code}/rates", response_model=CommissionCategoryRateOut, status_code=201)(create_rate)
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
    _s6.put("/{country_code}/rates/{rate_id}", response_model=CommissionCategoryRateOut)(update_rate)
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
    _s6.get("/{country_code}/badge-tiers")(list_badge_tiers)
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
    _s6.post("/{country_code}/badge-tiers", response_model=CommissionBadgeTierOut, status_code=201)(create_badge_tier)
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
    _s6.put("/{country_code}/badge-tiers/{tier_id}", response_model=CommissionBadgeTierOut)(update_badge_tier)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route update_badge_tier: %s", _e)

try:
    def     health():
        """Liveness probe for this router."""
        return {"status": "ok", "router": "admin_commission_routes", "prefix": "/api/v1/admin"}
    _s6.get("/admin_commission_routes/health")(health)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route health: %s", _e)

try:
    def     status():
        """Report whether a backing controller is importable."""
        return {"router": "admin_commission_routes", "controller": "controllers.finance.commission_controller" if _HAS_CTRL else None,
                "public_functions": _CTRL_PUBLIC}
    _s6.get("/admin_commission_routes/status")(status)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route status: %s", _e)

try:
    def     seed_chart_of_accounts_route(
        db: Session = Depends(get_db),
        audit_user_id: Optional[int] = Query(None),
        audit_username: Optional[str] = Query(None),
        audit_user_role: Optional[str] = Query(None)
    ) -> dict:
        return seed_chart_of_accounts(db=db, audit_user_id=audit_user_id, audit_username=audit_username, audit_user_role=audit_user_role)
    _s6.post("/seed", status_code=201, tags=['accounting'], summary="Seed chart of accounts (idempotent)")(seed_chart_of_accounts_route)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route seed_chart_of_accounts_route: %s", _e)

try:
    def     list_accounts_route(
        db: Session = Depends(get_db)
    ) -> list:
        return list_accounts(db=db)
    _s6.get("/accounts", status_code=200, tags=['accounting'], summary="List all accounts")(list_accounts_route)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route list_accounts_route: %s", _e)

try:
    def     get_account_route(
        code: str,
        db: Session = Depends(get_db)
    ):
        return get_account(db=db, code=code)
    _s6.get("/accounts/{code}", status_code=200, tags=['accounting'], summary="Get account by code")(get_account_route)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route get_account_route: %s", _e)

try:
    def     create_journal_entry_route(
        db: Session = Depends(get_db),
        current_user: dict = Depends(require_admin),
        body: JournalEntryBody = Body(...)
    ) -> dict:
        return create_journal_entry(db=db, current_user=current_user, body=body)
    _s6.post("/journal-entries", status_code=201, tags=['accounting'], summary="Create a journal entry")(create_journal_entry_route)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route create_journal_entry_route: %s", _e)

try:
    def     get_journal_entry_route(
        entry_id: int,
        db: Session = Depends(get_db)
    ):
        return get_journal_entry(db=db, entry_id=entry_id)
    _s6.get("/journal-entries/{entry_id}", status_code=200, tags=['accounting'], summary="Get journal entry by ID")(get_journal_entry_route)
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
    _s6.get("/journal-entries", status_code=200, tags=['accounting'], summary="List journal entries")(list_journal_entries_route)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route list_journal_entries_route: %s", _e)

try:
    def     get_account_balance_route(
        account_code: str,
        db: Session = Depends(get_db),
        currency: str = Query('OMR')
    ) -> dict:
        return get_account_balance(db=db, account_code=account_code, currency=currency)
    _s6.get("/balances/{account_code}", status_code=200, tags=['accounting'], summary="Get account balance")(get_account_balance_route)
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
    _s6.get("/trial-balance", status_code=200, tags=['accounting'], summary="Get trial balance")(get_trial_balance_route)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route get_trial_balance_route: %s", _e)

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
    _s6.post("/seed", summary="Seed chart of accounts (idempotent)")(seed_chart_of_accounts)
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
    _s6.get("/accounts", summary="List all accounts")(list_accounts)
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
    _s6.get("/accounts/{code}", summary="Get account by code")(get_account)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route get_account: %s", _e)

try:
    def     create_journal_entry(
        body: accounting_controller.JournalEntryBody,
        db: Session = Depends(get_db),
        current_user=Depends(require_admin),
    ):
        return accounting_controller.create_journal_entry(db, body, current_user)
    _s6.post("/journal-entries", summary="Create a journal entry")(create_journal_entry)
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
    _s6.get("/journal-entries", summary="List journal entries")(list_journal_entries)
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
    _s6.get("/journal-entries/{entry_id}", summary="Get journal entry by ID")(get_journal_entry)
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
    _s6.get("/balances/{account_code}", summary="Get account balance")(get_balance)
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
    _s6.get("/trial-balance", summary="Get trial balance")(trial_balance)
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
    _s6.post("/reports/income-statement", summary="Generate Income Statement (P&L)")(income_statement)
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
    _s6.post("/reports/balance-sheet", summary="Generate Balance Sheet")(balance_sheet)
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
    _s6.post("/reports/cash-flow", summary="Generate Cash Flow Statement")(cash_flow)
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
    _s6.get("/reports", summary="List saved financial reports")(list_reports)
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
    _s6.post("/periods/get-or-create", summary="Get or create a fiscal period")(get_or_create)
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
    _s6.get("/periods/current", summary="Get current fiscal period")(current_period)
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
    _s6.post("/periods/close", summary="Close a fiscal period")(close_fiscal_period)
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
    _s6.get("/periods", summary="List fiscal periods")(list_fiscal_periods)
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
    _s6.post("/journal-entries/reverse", summary="Reverse a journal entry")(reverse_entry)
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
    _s6.post("/cash-flow-forecast", summary="Generate cash flow forecast")(cash_flow_forecast)
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
    _s6.get("/ar", summary="AR sub-ledger (customer receivables)")(get_ar)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route get_ar: %s", _e)

try:
    def     post_ar_invoice_route(body: ARInvoiceBody, db: Session = Depends(get_db), _admin: dict = Depends(require_admin)):
        cleanup = _with_rls(body.country_code, db)
        try:
            return controller_post_ar_invoice(db, **body.model_dump(), admin_user=_admin)
        finally:
            cleanup()
    _s6.post("/ar-ledger/invoice", summary="Post AR invoice")(post_ar_invoice_route)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route post_ar_invoice_route: %s", _e)

try:
    def     post_ar_payment_route(body: ARPaymentBody, db: Session = Depends(get_db), _admin: dict = Depends(require_admin)):
        cleanup = _with_rls(body.country_code, db)
        try:
            return controller_post_ar_payment(db, **body.model_dump(), admin_user=_admin)
        finally:
            cleanup()
    _s6.post("/ar-ledger/payment", summary="Post AR payment")(post_ar_payment_route)
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
    _s6.get("/ap", summary="AP Sub-ledger alias (Accounts Payable)")(get_ap_alias)
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
    _s6.get("/ap-ledger", summary="AP Sub-ledger (Accounts Payable)")(get_ap)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route get_ap: %s", _e)

try:
    def     post_ap_payable_route(body: APPayableBody, db: Session = Depends(get_db), _admin: dict = Depends(require_admin)):
        cleanup = _with_rls(body.country_code, db)
        try:
            return controller_post_ap_payable(db, **body.model_dump(), admin_user=_admin)
        finally:
            cleanup()
    _s6.post("/ap-ledger/payable", summary="Post AP payable")(post_ap_payable_route)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route post_ap_payable_route: %s", _e)

try:
    def     post_ap_payment_route(body: APPaymentBody, db: Session = Depends(get_db), _admin: dict = Depends(require_admin)):
        cleanup = _with_rls(body.country_code, db)
        try:
            return controller_post_ap_payment(db, **body.model_dump(), admin_user=_admin)
        finally:
            cleanup()
    _s6.post("/ap-ledger/payment", summary="Post AP payment")(post_ap_payment_route)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route post_ap_payment_route: %s", _e)

try:
    def     list_rates(country_code: str = Path(..., description="ISO country code"), _: User = Depends(require_admin), db: Session = Depends(get_db), page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100)):
        get_country_or_404(country_code.upper(), db)
        set_rls_context({country_code.upper()}, is_restricted=True)
        try:
            return list_category_rates(db, country_code, page, page_size)
        finally:
            clear_rls_context()
    _s6.get("/{country_code}/rates")(list_rates)
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
    _s6.post("/{country_code}/rates", response_model=CommissionCategoryRateOut, status_code=201)(create_rate)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route create_rate: %s", _e)

try:
    def     update_rate(country_code: str = Path(..., description="ISO country code"), rate_id: int = Path(..., description="Rate id"), payload: CommissionCategoryRateCreate = None, _: User = Depends(require_admin), db: Session = Depends(get_db)):
        get_country_or_404(country_code.upper(), db)
        return update_category_rate(db, rate_id, country_code, payload)
    _s6.put("/{country_code}/rates/{rate_id}", response_model=CommissionCategoryRateOut)(update_rate)
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
    _s6.get("/{country_code}/badge-tiers")(list_badge_tiers_route)
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
    _s6.post("/{country_code}/badge-tiers", response_model=CommissionBadgeTierOut, status_code=201)(create_badge_tier_route)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route create_badge_tier_route: %s", _e)

try:
    def     update_badge_tier_route(country_code: str = Path(..., description="ISO country code"), tier_id: int = Path(..., description="Badge tier id"), payload: CommissionBadgeTierCreate = None, _: User = Depends(require_admin), db: Session = Depends(get_db)):
        get_country_or_404(country_code.upper(), db)
        return update_badge_tier(db, tier_id, country_code, payload)
    _s6.put("/{country_code}/badge-tiers/{tier_id}", response_model=CommissionBadgeTierOut)(update_badge_tier_route)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route update_badge_tier_route: %s", _e)

try:
    def     controller_get_ar_summary_route(
        db: Session = Depends(get_db),
        customer_id: Optional[int] = Query(None),
        status: Optional[str] = Query(None),
        country_code: Optional[str] = Query(None),
        limit: int = Query(50)
    ) -> dict:
        return controller_get_ar_summary(db=db, customer_id=customer_id, status=status, country_code=country_code, limit=limit)
    _s6.get("/admin/ar", status_code=200, tags=['finance'])(controller_get_ar_summary_route)
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
    _s6.get("/ar", status_code=200, tags=['finance'])(controller_get_ar_summary_route)
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
    _s6.get("/admin/ap", status_code=200, tags=['finance'])(controller_get_ap_summary_route)
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
    _s6.get("/ap", status_code=200, tags=['finance'])(controller_get_ap_summary_route)
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
    _s6.get("/admin/ap-ledger", status_code=200, tags=['finance'])(controller_get_ap_summary_route)
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
    _s6.get("/ap-ledger", status_code=200, tags=['finance'])(controller_get_ap_summary_route)
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
    _s6.post("/admin/ar-ledger/invoice", status_code=201, tags=['finance'])(controller_post_ar_invoice_route)
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
    _s6.post("/ar-ledger/invoice", status_code=201, tags=['finance'])(controller_post_ar_invoice_route)
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
    _s6.post("/admin/ar-ledger/payment", status_code=201, tags=['finance'])(controller_post_ar_payment_route)
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
    _s6.post("/ar-ledger/payment", status_code=201, tags=['finance'])(controller_post_ar_payment_route)
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
    _s6.post("/admin/ap-ledger/payable", status_code=201, tags=['finance'])(controller_post_ap_payable_route)
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
    _s6.post("/ap-ledger/payable", status_code=201, tags=['finance'])(controller_post_ap_payable_route)
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
    _s6.post("/admin/ap-ledger/payment", status_code=201, tags=['finance'])(controller_post_ap_payment_route)
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
    _s6.post("/ap-ledger/payment", status_code=201, tags=['finance'])(controller_post_ap_payment_route)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route controller_post_ap_payment_route: %s", _e)

try:
    def     list_payouts(country_code: str = Path(..., description="ISO country code"), _: User = Depends(require_admin), db: Session = Depends(get_db), page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100)):
        get_country_or_404(country_code.upper(), db)
        set_rls_context({country_code.upper()}, is_restricted=True)
        try:
            q = db.query(Payout).filter(Payout.country_code == country_code.upper())
            total = q.count()
            rows = q.order_by(Payout.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
            return {"data": rows, "total": total, "page": page, "page_size": page_size}
        finally:
            clear_rls_context()
    _s6.get("/payouts/{country_code}")(list_payouts)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route list_payouts: %s", _e)

try:
    def     create_payout(
        country_code: str = Path(..., description="ISO country code"),
        payload: PayoutCreate = None,
        current_admin: User = Depends(require_admin),
        db: Session = Depends(get_db),
    ):
        get_country_or_404(country_code.upper(), db)
        set_rls_context({country_code.upper()}, is_restricted=True)
        try:
            model_cols = {c.name for c in Payout.__table__.columns}
            data = {k: v for k, v in payload.model_dump().items() if k in model_cols}
            p = Payout(**data, country_code=country_code.upper())
            db.add(p); db.commit(); db.refresh(p)
            audit_log(
                db=db, action=AuditAction.PAYOUT_PROCESSED,
                user_id=current_admin.id, username=current_admin.username,
                user_role="admin", resource_type="payout",
                resource_id=p.id,
                details={"amount": str(p.amount) if p.amount else None, "method": p.method},
            )
            return p
        finally:
            clear_rls_context()
    _s6.post("/payouts/{country_code}", response_model=PayoutOut, status_code=201)(create_payout)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route create_payout: %s", _e)

try:
    def     list_pending_payouts(
        current_admin: User = Depends(require_admin),
        db: Session = Depends(get_db),
        page: int = Query(1, ge=1),
        page_size: int = Query(20, ge=1, le=100),
    ):
        """List all pending payouts (RLS-scoped if context is set)."""
        q = db.query(Payout).filter(Payout.status == "pending")
        total = q.count()
        rows = q.order_by(Payout.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
        return {"data": rows, "total": total, "page": page, "page_size": page_size}
    _s6.get("/pending")(list_pending_payouts)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route list_pending_payouts: %s", _e)

try:
    def     list_pending_payouts_by_country(
        country_code: str = Path(..., description="ISO country code"),
        current_admin: User = Depends(require_admin),
        db: Session = Depends(get_db),
        page: int = Query(1, ge=1),
        page_size: int = Query(20, ge=1, le=100),
    ):
        """List pending payouts for a specific country."""
        get_country_or_404(country_code.upper(), db)
        set_rls_context({country_code.upper()}, is_restricted=True)
        try:
            q = db.query(Payout).filter(Payout.status == "pending", Payout.country_code == country_code.upper())
            total = q.count()
            rows = q.order_by(Payout.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
            return {"data": rows, "total": total, "page": page, "page_size": page_size}
        finally:
            clear_rls_context()
    _s6.get("/payouts/{country_code}/pending")(list_pending_payouts_by_country)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route list_pending_payouts_by_country: %s", _e)

try:
    def     verify_payout(
        country_code: str = Path(..., description="ISO country code"),
        payout_id: int = Path(...),
        payload: PayoutVerifyRequest = None,
        current_admin: User = Depends(require_admin),
        db: Session = Depends(get_db),
    ):
        """Verify a payout."""
        get_country_or_404(country_code.upper(), db)
        set_rls_context({country_code.upper()}, is_restricted=True)
        try:
            p = db.query(Payout).filter(Payout.id == payout_id, Payout.country_code == country_code.upper()).first()
            if not p:
                raise HTTPException(404, "Payout not found")
            p.status = payload.status if payload and payload.status else "verified"
            p.processed_at = utcnow()
            if payload:
                if payload.note:
                    p.notes = payload.note
                if payload.bank_reference:
                    p.reference = payload.bank_reference
            db.commit()
            audit_log(
                db=db, action=AuditAction.PAYOUT_PROCESSED,
                user_id=current_admin.id, username=current_admin.username,
                user_role="admin", resource_type="payout",
                resource_id=payout_id,
                details={"status": p.status, "reference": p.reference, "notes": p.notes},
            )
            return {"verified": True, "payout_id": payout_id}
        finally:
            clear_rls_context()
    _s6.post("/payouts/{country_code}/{payout_id}/verify")(verify_payout)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route verify_payout: %s", _e)

try:
    def     run_auto_payout_sweep(
        db: Session = Depends(get_db),
        current_admin: User = Depends(require_admin),
    ):
        """Manually trigger the auto-payout sweep for eligible settlements.

        Runs both supplier and logistics settlement sweeps:
          1. Finds pending SupplierSettlements where ``eligible_at`` has passed
             → creates Payout records + PayoutBatchItems (entity_type="supplier")
          2. Finds pending LogisticsSettlements where ``eligible_at`` has passed
             → creates LogisticsPartnerPayout records + PayoutBatchItems (entity_type="logistics")

        Returns a combined summary dict.
        """
        admin_ref = f"Manually triggered by admin #{getattr(current_admin, 'id', '?')}"

        supplier_result = _run_supplier_sweep(db, batch_notes=admin_ref)
        if supplier_result.get("status") == "error":
            raise HTTPException(status_code=500, detail=supplier_result.get("error", "Supplier sweep failed"))

        logistics_result = _run_logistics_sweep(db, batch_notes=admin_ref)
        if logistics_result.get("status") == "error":
            raise HTTPException(status_code=500, detail=logistics_result.get("error", "Logistics sweep failed"))

        return {
            "supplier": supplier_result,
            "logistics": logistics_result,
            "total_processed": (supplier_result.get("processed", 0) + logistics_result.get("processed", 0)),
            "status": "ok",
        }
    _s6.post("/payouts/run-auto-sweep")(run_auto_payout_sweep)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route run_auto_payout_sweep: %s", _e)

try:
    def     process_payout(
        country_code: str = Path(..., description="ISO country code"),
        payout_id: int = Path(...),
        current_admin: User = Depends(require_admin),
        db: Session = Depends(get_db),
    ):
        get_country_or_404(country_code.upper(), db)
        set_rls_context({country_code.upper()}, is_restricted=True)
        try:
            p = db.query(Payout).filter(Payout.id == payout_id, Payout.country_code == country_code.upper()).first()
            if not p: raise HTTPException(404)
            p.status = "paid"; p.processed_at = utcnow()
            db.commit()
            audit_log(
                db=db, action=AuditAction.PAYOUT_PROCESSED,
                user_id=current_admin.id, username=current_admin.username,
                user_role="admin", resource_type="payout",
                resource_id=payout_id,
                details={"status": "paid"},
            )
            return {"message": "Payout processed"}
        finally:
            clear_rls_context()
    _s6.put("/payouts/{country_code}/{payout_id}/process")(process_payout)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route process_payout: %s", _e)

try:
    def     get_background_job_status_endpoint(
        db: Session = Depends(get_db),
        current_admin: User = Depends(require_admin),
    ):
        """Return the current state of the auto-payout background job:
        is_running, last_run_at, last_run_status, last_error, total counts,
        and recent FinanceAutomationLog entries.
        """
        status = _get_bg_status()

        # Enrich with recent history from FinanceAutomationLog
        history = (
            db.query(FinanceAutomationLog)
            .filter(
                FinanceAutomationLog.kind.in_(["auto_payout", "auto_logistics_payout"]),
            )
            .order_by(FinanceAutomationLog.created_at.desc())
            .limit(20)
            .all()
        )

        return {
            "status": status,
            "history": [
                {
                    "id": h.id,
                    "kind": h.kind,
                    "records_processed": h.records_processed,
                    "records_changed": h.records_changed,
                    "detail": h.detail,
                    "created_at": h.created_at.isoformat() if h.created_at else None,
                }
                for h in history
            ],
        }
    _s6.get("/background-job-status")(get_background_job_status_endpoint)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route get_background_job_status_endpoint: %s", _e)

try:
    def     start_background_job(
        current_admin: User = Depends(require_admin),
    ):
        """Start the auto-payout scheduler background thread."""
        _start_bg_job()
        return {"status": "ok", "message": "Background job started"}
    _s6.post("/background-job/start")(start_background_job)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route start_background_job: %s", _e)

try:
    def     stop_background_job(
        current_admin: User = Depends(require_admin),
    ):
        """Stop the auto-payout scheduler background thread gracefully."""
        _stop_bg_job()
        return {"status": "ok", "message": "Background job stopping"}
    _s6.post("/background-job/stop")(stop_background_job)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route stop_background_job: %s", _e)

try:
    def     trigger_background_job(
        db: Session = Depends(get_db),
        current_admin: User = Depends(require_admin),
    ):
        """Run the auto-payout sweep immediately (both supplier and logistics).

        Returns the combined sweep result.
        """
        admin_ref = f"Manually triggered by admin #{getattr(current_admin, 'id', '?')}"

        supplier_result = _run_supplier_sweep(db, batch_notes=admin_ref)
        if supplier_result.get("status") == "error":
            raise HTTPException(status_code=500, detail=supplier_result.get("error", "Supplier sweep failed"))

        logistics_result = _run_logistics_sweep(db, batch_notes=admin_ref)
        if logistics_result.get("status") == "error":
            raise HTTPException(status_code=500, detail=logistics_result.get("error", "Logistics sweep failed"))

        # Update in-memory status after the manual trigger
        _update_bg_status_after_manual_trigger(supplier_result, logistics_result)

        return {
            "supplier": supplier_result,
            "logistics": logistics_result,
            "total_processed": (supplier_result.get("processed", 0) + logistics_result.get("processed", 0)),
            "status": "ok",
        }
    _s6.post("/background-job/trigger")(trigger_background_job)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route trigger_background_job: %s", _e)

try:
    def     trigger_background_job_kind(
        kind: str = Path(..., description="'supplier' or 'logistics'"),
        db: Session = Depends(get_db),
        current_admin: User = Depends(require_admin),
    ):
        """Run ONLY the supplier OR logistics sweep individually.

        Use this from the history table "Run Now" buttons to re-run a specific
        sweep type without touching the other.
        """
        if kind not in ("supplier", "logistics"):
            raise HTTPException(status_code=400, detail="kind must be 'supplier' or 'logistics'")

        admin_ref = f"Manually triggered by admin #{getattr(current_admin, 'id', '?')} — single sweep"

        if kind == "supplier":
            result = _run_supplier_sweep(db, batch_notes=admin_ref)
            if result.get("status") == "error":
                raise HTTPException(status_code=500, detail=result.get("error", "Supplier sweep failed"))
            # Update in-memory status for just supplier
            _update_bg_status_after_manual_trigger(result, {"status": "no_eligible_settlements", "processed": 0})
        else:
            result = _run_logistics_sweep(db, batch_notes=admin_ref)
            if result.get("status") == "error":
                raise HTTPException(status_code=500, detail=result.get("error", "Logistics sweep failed"))
            _update_bg_status_after_manual_trigger({"status": "no_eligible_settlements", "processed": 0}, result)

        return result
    _s6.post("/background-job/trigger/{kind}")(trigger_background_job_kind)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route trigger_background_job_kind: %s", _e)

try:
    def _update_bg_status_after_manual_trigger(
        supplier_result: dict,
        logistics_result: dict,
    ) -> None:
        """Update the in-memory background job status after a manual trigger."""
        from domains.finance.services.payouts.payout_batch_service import update_background_status
    
        supplier_status = supplier_result.get("status", "error")
        logistics_status = logistics_result.get("status", "error")
        has_error = supplier_status == "error" or logistics_status == "error"
        overall_error = supplier_result.get("error") or logistics_result.get("error") if has_error else None
    
        now = utcnow()
        update_background_status(
            last_run_at=now.isoformat(),
            last_run_status="error" if overall_error else "ok",
            last_error=overall_error,
            last_supplier_result=supplier_result,
            last_logistics_result=logistics_result,
            total_sweep_count=(_get_bg_status().get("total_sweep_count", 0) + 1),
            total_settlements_processed=(
                _get_bg_status().get("total_settlements_processed", 0)
                + supplier_result.get("processed", 0)
                + logistics_result.get("processed", 0)
            ),
            is_running=True,
        )
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route: %s", _e)

_s7 = APIRouter(prefix='')

try:
    def     get_pending_payouts_route(

        limit: int = 200,

        offset: int = 0,

        db: Session = Depends(get_db),

        current_admin: dict = Depends(get_current_admin),

    ):

        require_permission("payouts.verify", current_admin)

        return list_pending_payouts(db, limit=limit, offset=offset)
    _s7.get("/payouts/pending")(get_pending_payouts_route)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route get_pending_payouts_route: %s", _e)

try:
    def     verify_payout_route(

        payout_id: int,

        data: dict,

        db: Session = Depends(get_db),

        current_admin: dict = Depends(require_admin_2fa_verified),

    ):

        require_permission("payouts.verify", current_admin)

        payout = get_payout_by_id(db, payout_id)

        amount = float(payout.amount) if payout and payout.amount is not None else None

        require_approval(db, current_admin["id"], "payout", amount=amount)

        return verify_payout(payout_id, data, current_admin, db)
    _s7.post("/payouts/{payout_id}/verify")(verify_payout_route)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route verify_payout_route: %s", _e)

try:
    def     health():
        """Liveness probe for this router."""
        return {"status": "ok", "router": "admin_payouts_routes", "prefix": "/api/v1/admin"}
    _s7.get("/admin_payouts_routes/health")(health)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route health: %s", _e)

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
    _s7.get("/")(admin_treasury_root)
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
    _s7.get("/metrics")(admin_treasury_metrics)
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
    _s7.get("/ledger")(admin_treasury_ledger)
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
    _s7.get("/reports/trial-balance")(admin_trial_balance)
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
    _s7.get("/cash-position")(admin_cash_position)
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
    _s7.get("/payouts/batches")(admin_payout_batches)
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
    _s7.post("/payouts/batches/generate")(admin_generate_payout_batch)
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
    _s7.post("/payouts/batches/{batch_id}/approve")(admin_approve_payout_batch)
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
    _s7.post("/payouts/batches/{batch_id}/dispatch")(admin_dispatch_payout_batch)
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
    _s7.get("/reports/vat-liability")(admin_vat_liability)
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
    _s7.get("/cod-remittances")(admin_cod_remittances)
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
    _s7.get("/reconciliation/gateway-summary")(admin_gateway_summary)
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
    _s7.post("/cash-position/snapshot")(admin_snapshot_cash_position)
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
    _s7.get("/forecasts")(admin_cash_forecasts)
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
    _s7.get("/consolidated/metrics")(consolidated_treasury_metrics)
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
    _s7.get("/consolidated/ledger")(consolidated_treasury_ledger)
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
    _s7.get("/consolidated/reports/trial-balance")(consolidated_trial_balance)
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
    _s7.get("/consolidated/cash-position")(consolidated_cash_position)
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
    _s7.get("/consolidated/payouts/batches")(consolidated_payout_batches)
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
    _s7.get("/consolidated/reports/vat-liability")(consolidated_vat_liability)
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
    _s7.get("/consolidated/cod-remittances")(consolidated_cod_remittances)
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
    _s7.get("/consolidated/reconciliation/gateway-summary")(consolidated_gateway_summary)
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
    _s7.get("/consolidated/forecasts")(consolidated_cash_forecasts)
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
    _s7.get("/consolidated/reconciliation/pipeline")(consolidated_reconciliation_pipeline)
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
    _s7.get("/{country_code}/metrics")(country_treasury_metrics)
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
    _s7.get("/{country_code}/ledger")(country_treasury_ledger)
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
    _s7.get("/{country_code}/reports/trial-balance")(country_trial_balance)
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
    _s7.get("/{country_code}/cash-position")(country_cash_position)
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
    _s7.get("/{country_code}/payouts/batches")(country_payout_batches)
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
    _s7.get("/{country_code}/reports/vat-liability")(country_vat_liability)
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
    _s7.get("/{country_code}/cod-remittances")(country_cod_remittances)
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
    _s7.get("/{country_code}/reconciliation/gateway-summary")(country_gateway_summary)
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
    _s7.get("/{country_code}/reconciliation/pipeline")(admin_reconciliation_pipeline)
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
    _s7.post("/{country_code}/reconciliation/record-cod-remittance")(admin_record_cod_remittance)
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
    _s7.post("/{country_code}/reconciliation/settle-supplier")(admin_settle_supplier)
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
    _s7.post("/{country_code}/reconciliation/approve-settlement")(admin_approve_settlement)
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
    _s7.get("/reconciliation/gateway-exceptions")(admin_gateway_exceptions)
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
    _s7.get("/{country_code}/reconciliation/gateway-exceptions")(country_gateway_exceptions)
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
    _s7.get("/payments/transactions")(admin_payment_transactions)
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
    _s7.get("/{country_code}/payments/transactions")(country_payment_transactions)
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
    _s7.get("/supplier-payouts")(admin_supplier_payouts)
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
    _s7.get("/{country_code}/supplier-payouts")(country_supplier_payouts)
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
    _s7.get("/logistics-payouts")(admin_logistics_payouts)
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
    _s7.get("/{country_code}/logistics-payouts")(country_logistics_payouts)
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
    _s7.get("/reports/supplier-earnings")(admin_supplier_earnings)
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
    _s7.get("/{country_code}/reports/supplier-earnings")(country_supplier_earnings)
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
    _s7.get("/liabilities/exposure")(admin_liabilities_exposure)
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
    _s7.get("/{country_code}/liabilities/exposure")(country_liabilities_exposure)
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
    _s7.post("/ledger/manual-adjustment")(admin_manual_adjustment)
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
    _s7.post("/{country_code}/ledger/manual-adjustment")(country_manual_adjustment)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route country_manual_adjustment: %s", _e)

try:
    def     admin_pending_entries(
        db: Session = Depends(get_db),
        current_user: dict = Depends(require_treasury_access),
    ):
        engine = TreasuryEngine(db)
        return {"entries": engine.list_pending_entries()}
    _s7.get("/ledger/pending")(admin_pending_entries)
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
    _s7.get("/{country_code}/ledger/pending")(country_pending_entries)
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
    _s7.post("/ledger/pending/{pending_id}/approve")(admin_approve_pending)
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
    _s7.post("/{country_code}/ledger/pending/{pending_id}/approve")(country_approve_pending)
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
    _s7.post("/ledger/pending/{pending_id}/reject")(admin_reject_pending)
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
    _s7.post("/{country_code}/ledger/pending/{pending_id}/reject")(country_reject_pending)
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
    _s7.post("/detect-orphans")(admin_detect_orphans)
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
    _s7.post("/{country_code}/detect-orphans")(country_detect_orphans)
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
    _s7.get("/payroll/equity")(payroll_equity)
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
    _s7.get("/{country_code}/payroll")(country_payroll)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route country_payroll: %s", _e)

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
    _s7.post("/treasury/badge-billing/{billing_id}/payments", status_code=201, tags=['treasury'])(record_badge_billing_payment_route)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route record_badge_billing_payment_route: %s", _e)

try:
    def     upsert_bank_settings_route(
        current_user: dict = Depends(require_admin),
        db: Session = Depends(get_db),
        data: dict = Body(...)
    ) -> dict[str, Any]:
        return upsert_bank_settings(current_user=current_user, db=db, data=data)
    _s7.put("/treasury/bank-settings", status_code=200, tags=['treasury'])(upsert_bank_settings_route)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route upsert_bank_settings_route: %s", _e)

try:
    def     record_vat_remittance_route(
        current_user: dict = Depends(require_admin),
        db: Session = Depends(get_db),
        data: dict = Body(...)
    ) -> Any:
        return record_vat_remittance(current_user=current_user, db=db, data=data)
    _s7.post("/treasury/vat-remittances", status_code=201, tags=['treasury'])(record_vat_remittance_route)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route record_vat_remittance_route: %s", _e)

try:
    def     create_bank_transaction_route(
        current_user: dict = Depends(require_admin),
        db: Session = Depends(get_db),
        data: dict = Body(...)
    ) -> Any:
        return create_bank_transaction(current_user=current_user, db=db, data=data)
    _s7.post("/treasury/bank-transactions", status_code=201, tags=['treasury'])(create_bank_transaction_route)
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
    _s7.post("/treasury/bank-transactions/import", status_code=201, tags=['treasury'])(import_bank_transactions_route)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route import_bank_transactions_route: %s", _e)

try:
    def     reconcile_transaction_route(
        txn_id: int,
        current_user: dict = Depends(require_admin),
        db: Session = Depends(get_db)
    ) -> Any:
        return reconcile_transaction(txn_id=txn_id, current_user=current_user, db=db)
    _s7.post("/treasury/bank-transactions/{txn_id}/reconcile", status_code=201, tags=['treasury'])(reconcile_transaction_route)
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
    _s7.post("/treasury/bank-transactions/{txn_id}/flag", status_code=201, tags=['treasury'])(flag_transaction_route)
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
    _s7.post("/treasury/bank-transactions/{txn_id}/resolve", status_code=201, tags=['treasury'])(resolve_transaction_exception_route)
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
    _s7.post("/treasury/bank-transactions/auto-reconcile", status_code=201, tags=['treasury'])(auto_reconcile_transactions_route)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route auto_reconcile_transactions_route: %s", _e)

try:
    def     trigger_supplier_payouts_route(
        current_user: dict = Depends(require_admin),
        db: Session = Depends(get_db),
        settlement_ids: Optional[list[int]] = Body(None)
    ) -> list[dict]:
        return trigger_supplier_payouts(current_user=current_user, db=db, settlement_ids=settlement_ids)
    _s7.post("/treasury/payouts/supplier", status_code=201, tags=['treasury'])(trigger_supplier_payouts_route)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route trigger_supplier_payouts_route: %s", _e)

try:
    def     trigger_logistics_payouts_route(
        current_user: dict = Depends(require_admin),
        db: Session = Depends(get_db),
        settlement_ids: Optional[list[int]] = Body(None)
    ) -> list[dict]:
        return trigger_logistics_payouts(current_user=current_user, db=db, settlement_ids=settlement_ids)
    _s7.post("/treasury/payouts/logistics", status_code=201, tags=['treasury'])(trigger_logistics_payouts_route)
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
    _s7.post("/treasury/transfers/dispatch", status_code=201, tags=['treasury'])(dispatch_transfer_batch_route)
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
    _s7.post("/treasury/transfers/dispatch/queue", status_code=201, tags=['treasury'])(queue_dispatch_transfer_batch_route)
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
    _s7.post("/treasury/cod/{settlement_id}/remittance", status_code=201, tags=['treasury'])(record_cod_remittance_route)
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
    _s7.post("/treasury/cod/receipts/{receipt_id}/verify", status_code=201, tags=['treasury'])(verify_cod_remittance_receipt_route)
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
    _s7.post("/treasury/cod/receipts/{receipt_id}/reject", status_code=201, tags=['treasury'])(reject_cod_remittance_receipt_route)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route reject_cod_remittance_receipt_route: %s", _e)

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
    _s7.get("/metrics")(treasury_metrics)
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
    _s7.get("/cash-position")(cash_position)
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
    _s7.get("/vat-liability")(vat_liability)
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
    _s7.get("/supplier-payables")(supplier_payables)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route supplier_payables: %s", _e)

try:
    def     list_accounts(country_code: str = Path(..., description="ISO country code"), _: User = Depends(require_admin), db: Session = Depends(get_db)):
        get_country_or_404(country_code.upper(), db)
        set_rls_context({country_code.upper()}, is_restricted=True)
        try:
            return db.query(CashAccount).filter(CashAccount.is_active == True, CashAccount.country_code == country_code.upper()).all()
        finally:
            clear_rls_context()
    _s7.get("/{country_code}/accounts", response_model=list[CashAccountOut])(list_accounts)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route list_accounts: %s", _e)

try:
    def     create_account(country_code: str = Path(..., description="ISO country code"), payload: CashAccountCreate = None, _: User = Depends(require_admin), db: Session = Depends(get_db)):
        get_country_or_404(country_code.upper(), db)
        set_rls_context({country_code.upper()}, is_restricted=True)
        try:
            a = CashAccount(**payload.model_dump(), country_code=country_code.upper())
            db.add(a); db.commit(); db.refresh(a)
            return a
        finally:
            clear_rls_context()
    _s7.post("/{country_code}/accounts", response_model=CashAccountOut, status_code=201)(create_account)
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
            tx = CashTransaction(**payload.model_dump(), balance_after=account.balance, performed_by=current_user.id, country_code=country_code.upper())
            db.add(tx); db.commit(); db.refresh(tx)
            return tx
        finally:
            clear_rls_context()
    _s7.post("/{country_code}/transactions", response_model=CashTransactionOut, status_code=201)(create_transaction)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route create_transaction: %s", _e)

try:
    def _serialize_payout(p: Payout) -> dict[str, Any]:
        return {
            "id": cast(int, p.id),
            "supplier_id": cast(int | None, p.supplier_id),
            "order_id": cast(int | None, p.order_id),
            "amount": float(cast(Decimal, p.amount or 0)),
            "currency": cast(str | None, p.currency) or "OMR",
            "method": cast(str | None, p.method) or "",
            "status": cast(str | None, p.status) or "",
            "reference": cast(str | None, p.reference),
            "notes": cast(str | None, p.notes),
            "country_code": cast(str | None, p.country_code) or "",
            "created_at": cast(Any, p.created_at).isoformat() if getattr(p, "created_at", None) else None,
            "processed_at": cast(Any, p.processed_at).isoformat() if getattr(p, "processed_at", None) else None,
        }
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route: %s", _e)

try:
    def _serialize_batch_item(item: PayoutBatchItem) -> dict[str, Any]:
        return {
            "id": cast(int, item.id),
            "entity_type": cast(str, item.entity_type),
            "entity_id": cast(int, item.entity_id),
            "amount": float(cast(Decimal, item.amount or 0)),
            "currency": cast(str | None, item.currency) or "OMR",
            "reference": cast(str | None, item.reference),
            "status": cast(str | None, item.status) or "",
        }
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route: %s", _e)

try:
    def _serialize_batch(batch: PayoutBatch) -> dict[str, Any]:
        return {
            "id": cast(int, batch.id),
            "batch_number": cast(str, batch.batch_number),
            "country_code": cast(str, batch.country_code),
            "total_amount": float(cast(Decimal, batch.total_amount or 0)),
            "item_count": cast(int, batch.item_count or 0),
            "status": cast(str, batch.status),
            "notes": cast(str | None, batch.notes),
            "created_at": cast(Any, batch.created_at).isoformat() if getattr(batch, "created_at", None) else None,
            "items": [_serialize_batch_item(item) for item in (batch.items or [])],
        }
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route: %s", _e)

try:
    def _resolve_supplier_names(entity_ids: set[int], db: Session) -> dict[int, str]:
        """Return {entity_id: display_name} for supplier IDs."""
        if not entity_ids:
            return {}
        users = db.query(User).filter(User.id.in_(entity_ids)).all()
        return {cast(int, u.id): cast(str, u.username or u.email or f"Supplier #{u.id}") for u in users}
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route: %s", _e)

try:
    def _resolve_logistics_names(entity_ids: set[int], db: Session) -> dict[int, str]:
        """Return {entity_id: display_name} for logistics partner IDs."""
        if not entity_ids:
            return {}
        partners = db.query(LogisticsPartner).filter(LogisticsPartner.id.in_(entity_ids)).all()
        return {cast(int, p.id): cast(str, p.name or f"Partner #{p.id}") for p in partners}
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route: %s", _e)

try:
    def _enrich_batch_items(batch: PayoutBatch, db: Session) -> list[dict[str, Any]]:
        """Return batch items with resolved entity_name fields."""
        items = list(batch.items or [])
        supplier_ids = {cast(int, it.entity_id) for it in items if cast(str, it.entity_type) == "supplier"}
        logistics_ids = {cast(int, it.entity_id) for it in items if cast(str, it.entity_type) == "logistics"}
        supplier_names = _resolve_supplier_names(supplier_ids, db)
        logistics_names = _resolve_logistics_names(logistics_ids, db)
    
        enriched = []
        for item in items:
            e = _serialize_batch_item(item)
            eid = cast(int, item.entity_id)
            etype = cast(str, item.entity_type)
            if etype == "supplier":
                e["entity_name"] = supplier_names.get(eid, f"Supplier #{eid}")
            elif etype == "logistics":
                e["entity_name"] = logistics_names.get(eid, f"Partner #{eid}")
            else:
                e["entity_name"] = f"#{eid}"
            enriched.append(e)
        return enriched
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route: %s", _e)

try:
    def _load_unbatched_payouts(db: Session, page: int, page_size: int) -> tuple[list[dict[str, Any]], int]:
        """Return paginated individual Payout records with supplier names."""
        query = db.query(Payout).filter(Payout.status.in_(["pending", "draft"]))
        total = query.count()
        payouts = query.order_by(Payout.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    
        supplier_ids = {cast(int, p.supplier_id) for p in payouts if p.supplier_id}
        supplier_names = _resolve_supplier_names(supplier_ids, db) if supplier_ids else {}
    
        result = []
        for payout in payouts:
            s = _serialize_payout(payout)
            sid = cast(int | None, payout.supplier_id)
            s["supplier_name"] = supplier_names.get(cast(int, sid), f"Supplier #{sid}") if sid else None
            result.append(s)
        return result, total
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route: %s", _e)

try:
    def _load_pending_batches_with_items(db: Session, page: int, page_size: int) -> tuple[list[dict[str, Any]], int]:
        """Return paginated batches in draft/pending status with enriched items."""
        query = db.query(PayoutBatch).options(joinedload(PayoutBatch.items)).filter(
            PayoutBatch.status.in_(["draft", "pending"])
        )
        total = query.count()
        batches = query.order_by(PayoutBatch.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    
        result = []
        for batch in batches:
            enriched_items = _enrich_batch_items(batch, db)
            s = _serialize_batch(batch)
            s["items"] = enriched_items
            result.append(s)
        return result, total
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route: %s", _e)

try:
    def     get_pending_payouts(
        page: int = Query(1, ge=1),
        page_size: int = Query(20, ge=1, le=100),
        current_admin: User = Depends(require_admin),
        db: Session = Depends(get_db),
    ) -> dict[str, Any]:
        """Return all pending payout batches and unbatched payouts for admin review.

        Pagination is applied independently to batches and unbatched payouts.
        """
        batches, batch_total = _load_pending_batches_with_items(db, page, page_size)
        unbatched, payout_total = _load_unbatched_payouts(db, page, page_size)

        # ── Also load standalone logistics partner payouts ──
        logistics_payout_q = db.query(LogisticsPartnerPayout).filter(
            LogisticsPartnerPayout.status.in_(["pending", "draft"]),
        )
        logistics_payout_total = logistics_payout_q.count()
        logistics_payouts = logistics_payout_q.order_by(LogisticsPartnerPayout.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

        logistics_ids = {cast(int, lp.partner_id) for lp in logistics_payouts if lp.partner_id}
        logistics_names = _resolve_logistics_names(logistics_ids, db) if logistics_ids else {}

        unbatched_logistics = []
        for lp in logistics_payouts:
            pid = cast(int | None, lp.partner_id)
            unbatched_logistics.append({
                "id": cast(int, lp.id),
                "partner_id": pid,
                "partner_name": logistics_names.get(cast(int, pid), f"Partner #{pid}") if pid else None,
                "amount": float(cast(Decimal, lp.amount or 0)),
                "currency": cast(str | None, lp.currency) or "OMR",
                "status": cast(str | None, lp.status) or "",
                "reference": cast(str | None, lp.reference),
                "notes": cast(str | None, lp.notes),
                "created_at": cast(Any, lp.created_at).isoformat() if getattr(lp, "created_at", None) else None,
            })

        total_amount = sum(b["total_amount"] for b in batches)
        total_items = sum(b["item_count"] for b in batches)

        return {
            "pending_batches": batches,
            "unbatched_payouts": unbatched,
            "unbatched_logistics_payouts": unbatched_logistics,
            "summary": {
                "total_batches": batch_total,
                "total_amount": round(total_amount, 2),
                "total_items": total_items,
                "pending_payouts_count": payout_total,
                "pending_logistics_payouts_count": logistics_payout_total,
            },
            "pagination": {"page": page, "page_size": page_size},
        }
    _s7.get("/pending")(get_pending_payouts)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route get_pending_payouts: %s", _e)

try:
    def     approve_payout(
        payout_id: int,
        payload: ActionRequest | None = None,
        current_admin: User = Depends(require_admin),
        db: Session = Depends(get_db),
    ) -> dict[str, Any]:
        """Approve an individual pending payout record."""
        return approve_payout_action(db, payout_id, current_admin, payload)
    _s7.post("/payouts/{payout_id}/approve")(approve_payout)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route approve_payout: %s", _e)

try:
    def     reject_payout(
        payout_id: int,
        payload: ActionRequest | None = None,
        current_admin: User = Depends(require_admin),
        db: Session = Depends(get_db),
    ) -> dict[str, Any]:
        """Reject an individual pending payout record."""
        return reject_payout_action(db, payout_id, current_admin, payload)
    _s7.post("/payouts/{payout_id}/reject")(reject_payout)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route reject_payout: %s", _e)

try:
    def     approve_batch(
        batch_id: int,
        payload: ActionRequest | None = None,
        current_admin: User = Depends(require_admin),
        db: Session = Depends(get_db),
    ) -> dict[str, Any]:
        """Approve a payout batch — moves it from draft → approved."""
        return approve_batch_action(db, batch_id, current_admin, payload)
    _s7.post("/batches/{batch_id}/approve")(approve_batch)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route approve_batch: %s", _e)

try:
    def     reject_batch(
        batch_id: int,
        payload: ActionRequest | None = None,
        current_admin: User = Depends(require_admin),
        db: Session = Depends(get_db),
    ) -> dict[str, Any]:
        """Reject a payout batch — moves it from draft → rejected."""
        return reject_batch_action(db, batch_id, current_admin, payload)
    _s7.post("/batches/{batch_id}/reject")(reject_batch)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route reject_batch: %s", _e)

try:
    def     dispatch_batch(
        batch_id: int,
        payload: ActionRequest | None = None,
        current_admin: User = Depends(require_admin),
        db: Session = Depends(get_db),
    ) -> dict[str, Any]:
        """Dispatch (mark as paid) an approved payout batch."""
        return dispatch_batch_action(db, batch_id, current_admin, payload)
    _s7.post("/batches/{batch_id}/dispatch")(dispatch_batch)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route dispatch_batch: %s", _e)

try:
    def     approve_payout_route(
        payout_id: int,
        current_user: dict = Depends(require_admin),
        db: Session = Depends(get_db),
        payload: Any = Body(...)
    ) -> dict[str, Any]:
        return approve_payout(payout_id=payout_id, current_user=current_user, db=db, payload=payload)
    _s7.post("/payouts/{payout_id}/approve", status_code=201, tags=['treasury-payouts'])(approve_payout_route)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route approve_payout_route: %s", _e)

try:
    def     reject_payout_route(
        payout_id: int,
        current_user: dict = Depends(require_admin),
        db: Session = Depends(get_db),
        payload: Any = Body(...)
    ) -> dict[str, Any]:
        return reject_payout(payout_id=payout_id, current_user=current_user, db=db, payload=payload)
    _s7.post("/payouts/{payout_id}/reject", status_code=201, tags=['treasury-payouts'])(reject_payout_route)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route reject_payout_route: %s", _e)

try:
    def     approve_batch_route(
        batch_id: int,
        current_user: dict = Depends(require_admin),
        db: Session = Depends(get_db),
        payload: Any = Body(...)
    ) -> dict[str, Any]:
        return approve_batch(batch_id=batch_id, current_user=current_user, db=db, payload=payload)
    _s7.post("/batches/{batch_id}/approve", status_code=201, tags=['treasury-payouts'])(approve_batch_route)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route approve_batch_route: %s", _e)

try:
    def     reject_batch_route(
        batch_id: int,
        current_user: dict = Depends(require_admin),
        db: Session = Depends(get_db),
        payload: Any = Body(...)
    ) -> dict[str, Any]:
        return reject_batch(batch_id=batch_id, current_user=current_user, db=db, payload=payload)
    _s7.post("/batches/{batch_id}/reject", status_code=201, tags=['treasury-payouts'])(reject_batch_route)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route reject_batch_route: %s", _e)

try:
    def     dispatch_batch_route(
        batch_id: int,
        current_user: dict = Depends(require_admin),
        db: Session = Depends(get_db),
        payload: Any = Body(...)
    ) -> dict[str, Any]:
        return dispatch_batch(batch_id=batch_id, current_user=current_user, db=db, payload=payload)
    _s7.post("/batches/{batch_id}/dispatch", status_code=201, tags=['treasury-payouts'])(dispatch_batch_route)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route dispatch_batch_route: %s", _e)

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
    _s7.get("/")(admin_treasury_root)
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
    _s7.get("/metrics")(admin_treasury_metrics)
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
    _s7.get("/ledger")(admin_treasury_ledger)
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
    _s7.get("/reports/trial-balance")(admin_trial_balance)
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
    _s7.get("/cash-position")(admin_cash_position)
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
    _s7.get("/payouts/batches")(admin_payout_batches)
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
    _s7.post("/payouts/batches/generate")(admin_generate_payout_batch)
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
    _s7.post("/payouts/batches/{batch_id}/approve")(admin_approve_payout_batch)
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
    _s7.post("/payouts/batches/{batch_id}/dispatch")(admin_dispatch_payout_batch)
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
    _s7.get("/reports/vat-liability")(admin_vat_liability)
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
    _s7.get("/cod-remittances")(admin_cod_remittances)
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
    _s7.get("/reconciliation/gateway-summary")(admin_gateway_summary)
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
    _s7.post("/cash-position/snapshot")(admin_snapshot_cash_position)
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
    _s7.get("/forecasts")(admin_cash_forecasts)
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
    _s7.get("/consolidated/metrics")(consolidated_treasury_metrics)
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
    _s7.get("/consolidated/ledger")(consolidated_treasury_ledger)
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
    _s7.get("/consolidated/reports/trial-balance")(consolidated_trial_balance)
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
    _s7.get("/consolidated/cash-position")(consolidated_cash_position)
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
    _s7.get("/consolidated/payouts/batches")(consolidated_payout_batches)
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
    _s7.get("/consolidated/reports/vat-liability")(consolidated_vat_liability)
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
    _s7.get("/consolidated/cod-remittances")(consolidated_cod_remittances)
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
    _s7.get("/consolidated/reconciliation/gateway-summary")(consolidated_gateway_summary)
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
    _s7.get("/consolidated/forecasts")(consolidated_cash_forecasts)
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
    _s7.get("/consolidated/reconciliation/pipeline")(consolidated_reconciliation_pipeline)
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
    _s7.get("/{country_code}/metrics")(country_treasury_metrics)
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
    _s7.get("/{country_code}/ledger")(country_treasury_ledger)
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
    _s7.get("/{country_code}/reports/trial-balance")(country_trial_balance)
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
    _s7.get("/{country_code}/cash-position")(country_cash_position)
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
    _s7.get("/{country_code}/payouts/batches")(country_payout_batches)
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
    _s7.get("/{country_code}/reports/vat-liability")(country_vat_liability)
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
    _s7.get("/{country_code}/cod-remittances")(country_cod_remittances)
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
    _s7.get("/{country_code}/reconciliation/gateway-summary")(country_gateway_summary)
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
    _s7.get("/{country_code}/reconciliation/pipeline")(admin_reconciliation_pipeline)
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
    _s7.post("/{country_code}/reconciliation/record-cod-remittance")(admin_record_cod_remittance)
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
    _s7.post("/{country_code}/reconciliation/settle-supplier")(admin_settle_supplier)
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
    _s7.post("/{country_code}/reconciliation/approve-settlement")(admin_approve_settlement)
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
    _s7.get("/reconciliation/gateway-exceptions")(admin_gateway_exceptions)
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
    _s7.get("/{country_code}/reconciliation/gateway-exceptions")(country_gateway_exceptions)
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
    _s7.get("/payments/transactions")(admin_payment_transactions)
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
    _s7.get("/{country_code}/payments/transactions")(country_payment_transactions)
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
    _s7.get("/supplier-payouts")(admin_supplier_payouts)
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
    _s7.get("/{country_code}/supplier-payouts")(country_supplier_payouts)
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
    _s7.get("/logistics-payouts")(admin_logistics_payouts)
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
    _s7.get("/{country_code}/logistics-payouts")(country_logistics_payouts)
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
    _s7.get("/reports/supplier-earnings")(admin_supplier_earnings)
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
    _s7.get("/{country_code}/reports/supplier-earnings")(country_supplier_earnings)
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
    _s7.get("/liabilities/exposure")(admin_liabilities_exposure)
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
    _s7.get("/{country_code}/liabilities/exposure")(country_liabilities_exposure)
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
    _s7.post("/ledger/manual-adjustment")(admin_manual_adjustment)
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
    _s7.post("/{country_code}/ledger/manual-adjustment")(country_manual_adjustment)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route country_manual_adjustment: %s", _e)

try:
    def     admin_pending_entries(
        db: Session = Depends(get_db),
        current_user: dict = Depends(require_treasury_access),
    ):
        engine = TreasuryEngine(db)
        return {"entries": engine.list_pending_entries()}
    _s7.get("/ledger/pending")(admin_pending_entries)
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
    _s7.get("/{country_code}/ledger/pending")(country_pending_entries)
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
    _s7.post("/ledger/pending/{pending_id}/approve")(admin_approve_pending)
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
    _s7.post("/{country_code}/ledger/pending/{pending_id}/approve")(country_approve_pending)
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
    _s7.post("/ledger/pending/{pending_id}/reject")(admin_reject_pending)
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
    _s7.post("/{country_code}/ledger/pending/{pending_id}/reject")(country_reject_pending)
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
    _s7.post("/detect-orphans")(admin_detect_orphans)
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
    _s7.post("/{country_code}/detect-orphans")(country_detect_orphans)
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
    _s7.get("/payroll/equity")(payroll_equity)
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
    _s7.get("/{country_code}/payroll")(country_payroll)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route country_payroll: %s", _e)

try:
    def     health():
        """Liveness probe for this router."""
        return {"status": "ok", "router": "admin_treasury_routes", "prefix": "/api/v1/admin/treasury"}
    _s7.get("/admin_treasury_routes/health")(health)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route health: %s", _e)

try:
    def     list_payouts(country_code: str = Path(..., description="ISO country code"), _: User = Depends(require_admin), db: Session = Depends(get_db), page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100)):
        get_country_or_404(country_code.upper(), db)
        set_rls_context({country_code.upper()}, is_restricted=True)
        try:
            q = db.query(Payout).filter(Payout.country_code == country_code.upper())
            total = q.count()
            rows = q.order_by(Payout.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
            return {"data": rows, "total": total, "page": page, "page_size": page_size}
        finally:
            clear_rls_context()
    _s7.get("/payouts/{country_code}")(list_payouts)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route list_payouts: %s", _e)

try:
    def     create_payout(
        country_code: str = Path(..., description="ISO country code"),
        payload: PayoutCreate = None,
        current_admin: User = Depends(require_admin),
        db: Session = Depends(get_db),
    ):
        get_country_or_404(country_code.upper(), db)
        set_rls_context({country_code.upper()}, is_restricted=True)
        try:
            model_cols = {c.name for c in Payout.__table__.columns}
            data = {k: v for k, v in payload.model_dump().items() if k in model_cols}
            p = Payout(**data, country_code=country_code.upper())
            db.add(p); db.commit(); db.refresh(p)
            audit_log(
                db=db, action=AuditAction.PAYOUT_PROCESSED,
                user_id=current_admin.id, username=current_admin.username,
                user_role="admin", resource_type="payout",
                resource_id=p.id,
                details={"amount": str(p.amount) if p.amount else None, "method": p.method},
            )
            return p
        finally:
            clear_rls_context()
    _s7.post("/payouts/{country_code}", response_model=PayoutOut, status_code=201)(create_payout)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route create_payout: %s", _e)

try:
    def     list_pending_payouts(
        current_admin: User = Depends(require_admin),
        db: Session = Depends(get_db),
        page: int = Query(1, ge=1),
        page_size: int = Query(20, ge=1, le=100),
    ):
        """List all pending payouts (RLS-scoped if context is set)."""
        q = db.query(Payout).filter(Payout.status == "pending")
        total = q.count()
        rows = q.order_by(Payout.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
        return {"data": rows, "total": total, "page": page, "page_size": page_size}
    _s7.get("/pending")(list_pending_payouts)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route list_pending_payouts: %s", _e)

try:
    def     list_pending_payouts_by_country(
        country_code: str = Path(..., description="ISO country code"),
        current_admin: User = Depends(require_admin),
        db: Session = Depends(get_db),
        page: int = Query(1, ge=1),
        page_size: int = Query(20, ge=1, le=100),
    ):
        """List pending payouts for a specific country."""
        get_country_or_404(country_code.upper(), db)
        set_rls_context({country_code.upper()}, is_restricted=True)
        try:
            q = db.query(Payout).filter(Payout.status == "pending", Payout.country_code == country_code.upper())
            total = q.count()
            rows = q.order_by(Payout.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
            return {"data": rows, "total": total, "page": page, "page_size": page_size}
        finally:
            clear_rls_context()
    _s7.get("/payouts/{country_code}/pending")(list_pending_payouts_by_country)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route list_pending_payouts_by_country: %s", _e)

try:
    def     verify_payout(
        country_code: str = Path(..., description="ISO country code"),
        payout_id: int = Path(...),
        payload: PayoutVerifyRequest = None,
        current_admin: User = Depends(require_admin),
        db: Session = Depends(get_db),
    ):
        """Verify a payout."""
        get_country_or_404(country_code.upper(), db)
        set_rls_context({country_code.upper()}, is_restricted=True)
        try:
            p = db.query(Payout).filter(Payout.id == payout_id, Payout.country_code == country_code.upper()).first()
            if not p:
                raise HTTPException(404, "Payout not found")
            p.status = payload.status if payload and payload.status else "verified"
            p.processed_at = utcnow()
            if payload:
                if payload.note:
                    p.notes = payload.note
                if payload.bank_reference:
                    p.reference = payload.bank_reference
            db.commit()
            audit_log(
                db=db, action=AuditAction.PAYOUT_PROCESSED,
                user_id=current_admin.id, username=current_admin.username,
                user_role="admin", resource_type="payout",
                resource_id=payout_id,
                details={"status": p.status, "reference": p.reference, "notes": p.notes},
            )
            return {"verified": True, "payout_id": payout_id}
        finally:
            clear_rls_context()
    _s7.post("/payouts/{country_code}/{payout_id}/verify")(verify_payout)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route verify_payout: %s", _e)

try:
    def     run_auto_payout_sweep(
        db: Session = Depends(get_db),
        current_admin: User = Depends(require_admin),
    ):
        """Manually trigger the auto-payout sweep for eligible settlements.

        Runs both supplier and logistics settlement sweeps:
          1. Finds pending SupplierSettlements where ``eligible_at`` has passed
             → creates Payout records + PayoutBatchItems (entity_type="supplier")
          2. Finds pending LogisticsSettlements where ``eligible_at`` has passed
             → creates LogisticsPartnerPayout records + PayoutBatchItems (entity_type="logistics")

        Returns a combined summary dict.
        """
        admin_ref = f"Manually triggered by admin #{getattr(current_admin, 'id', '?')}"

        supplier_result = _run_supplier_sweep(db, batch_notes=admin_ref)
        if supplier_result.get("status") == "error":
            raise HTTPException(status_code=500, detail=supplier_result.get("error", "Supplier sweep failed"))

        logistics_result = _run_logistics_sweep(db, batch_notes=admin_ref)
        if logistics_result.get("status") == "error":
            raise HTTPException(status_code=500, detail=logistics_result.get("error", "Logistics sweep failed"))

        return {
            "supplier": supplier_result,
            "logistics": logistics_result,
            "total_processed": (supplier_result.get("processed", 0) + logistics_result.get("processed", 0)),
            "status": "ok",
        }
    _s7.post("/payouts/run-auto-sweep")(run_auto_payout_sweep)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route run_auto_payout_sweep: %s", _e)

try:
    def     process_payout(
        country_code: str = Path(..., description="ISO country code"),
        payout_id: int = Path(...),
        current_admin: User = Depends(require_admin),
        db: Session = Depends(get_db),
    ):
        get_country_or_404(country_code.upper(), db)
        set_rls_context({country_code.upper()}, is_restricted=True)
        try:
            p = db.query(Payout).filter(Payout.id == payout_id, Payout.country_code == country_code.upper()).first()
            if not p: raise HTTPException(404)
            p.status = "paid"; p.processed_at = utcnow()
            db.commit()
            audit_log(
                db=db, action=AuditAction.PAYOUT_PROCESSED,
                user_id=current_admin.id, username=current_admin.username,
                user_role="admin", resource_type="payout",
                resource_id=payout_id,
                details={"status": "paid"},
            )
            return {"message": "Payout processed"}
        finally:
            clear_rls_context()
    _s7.put("/payouts/{country_code}/{payout_id}/process")(process_payout)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route process_payout: %s", _e)

try:
    def     get_background_job_status_endpoint(
        db: Session = Depends(get_db),
        current_admin: User = Depends(require_admin),
    ):
        """Return the current state of the auto-payout background job:
        is_running, last_run_at, last_run_status, last_error, total counts,
        and recent FinanceAutomationLog entries.
        """
        status = _get_bg_status()

        # Enrich with recent history from FinanceAutomationLog
        history = (
            db.query(FinanceAutomationLog)
            .filter(
                FinanceAutomationLog.kind.in_(["auto_payout", "auto_logistics_payout"]),
            )
            .order_by(FinanceAutomationLog.created_at.desc())
            .limit(20)
            .all()
        )

        return {
            "status": status,
            "history": [
                {
                    "id": h.id,
                    "kind": h.kind,
                    "records_processed": h.records_processed,
                    "records_changed": h.records_changed,
                    "detail": h.detail,
                    "created_at": h.created_at.isoformat() if h.created_at else None,
                }
                for h in history
            ],
        }
    _s7.get("/background-job-status")(get_background_job_status_endpoint)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route get_background_job_status_endpoint: %s", _e)

try:
    def     start_background_job(
        current_admin: User = Depends(require_admin),
    ):
        """Start the auto-payout scheduler background thread."""
        _start_bg_job()
        return {"status": "ok", "message": "Background job started"}
    _s7.post("/background-job/start")(start_background_job)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route start_background_job: %s", _e)

try:
    def     stop_background_job(
        current_admin: User = Depends(require_admin),
    ):
        """Stop the auto-payout scheduler background thread gracefully."""
        _stop_bg_job()
        return {"status": "ok", "message": "Background job stopping"}
    _s7.post("/background-job/stop")(stop_background_job)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route stop_background_job: %s", _e)

try:
    def     trigger_background_job(
        db: Session = Depends(get_db),
        current_admin: User = Depends(require_admin),
    ):
        """Run the auto-payout sweep immediately (both supplier and logistics).

        Returns the combined sweep result.
        """
        admin_ref = f"Manually triggered by admin #{getattr(current_admin, 'id', '?')}"

        supplier_result = _run_supplier_sweep(db, batch_notes=admin_ref)
        if supplier_result.get("status") == "error":
            raise HTTPException(status_code=500, detail=supplier_result.get("error", "Supplier sweep failed"))

        logistics_result = _run_logistics_sweep(db, batch_notes=admin_ref)
        if logistics_result.get("status") == "error":
            raise HTTPException(status_code=500, detail=logistics_result.get("error", "Logistics sweep failed"))

        # Update in-memory status after the manual trigger
        _update_bg_status_after_manual_trigger(supplier_result, logistics_result)

        return {
            "supplier": supplier_result,
            "logistics": logistics_result,
            "total_processed": (supplier_result.get("processed", 0) + logistics_result.get("processed", 0)),
            "status": "ok",
        }
    _s7.post("/background-job/trigger")(trigger_background_job)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route trigger_background_job: %s", _e)

try:
    def     trigger_background_job_kind(
        kind: str = Path(..., description="'supplier' or 'logistics'"),
        db: Session = Depends(get_db),
        current_admin: User = Depends(require_admin),
    ):
        """Run ONLY the supplier OR logistics sweep individually.

        Use this from the history table "Run Now" buttons to re-run a specific
        sweep type without touching the other.
        """
        if kind not in ("supplier", "logistics"):
            raise HTTPException(status_code=400, detail="kind must be 'supplier' or 'logistics'")

        admin_ref = f"Manually triggered by admin #{getattr(current_admin, 'id', '?')} — single sweep"

        if kind == "supplier":
            result = _run_supplier_sweep(db, batch_notes=admin_ref)
            if result.get("status") == "error":
                raise HTTPException(status_code=500, detail=result.get("error", "Supplier sweep failed"))
            # Update in-memory status for just supplier
            _update_bg_status_after_manual_trigger(result, {"status": "no_eligible_settlements", "processed": 0})
        else:
            result = _run_logistics_sweep(db, batch_notes=admin_ref)
            if result.get("status") == "error":
                raise HTTPException(status_code=500, detail=result.get("error", "Logistics sweep failed"))
            _update_bg_status_after_manual_trigger({"status": "no_eligible_settlements", "processed": 0}, result)

        return result
    _s7.post("/background-job/trigger/{kind}")(trigger_background_job_kind)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route trigger_background_job_kind: %s", _e)

try:
    def _update_bg_status_after_manual_trigger(
        supplier_result: dict,
        logistics_result: dict,
    ) -> None:
        """Update the in-memory background job status after a manual trigger."""
        from domains.finance.services.payouts.payout_batch_service import update_background_status
    
        supplier_status = supplier_result.get("status", "error")
        logistics_status = logistics_result.get("status", "error")
        has_error = supplier_status == "error" or logistics_status == "error"
        overall_error = supplier_result.get("error") or logistics_result.get("error") if has_error else None
    
        now = utcnow()
        update_background_status(
            last_run_at=now.isoformat(),
            last_run_status="error" if overall_error else "ok",
            last_error=overall_error,
            last_supplier_result=supplier_result,
            last_logistics_result=logistics_result,
            total_sweep_count=(_get_bg_status().get("total_sweep_count", 0) + 1),
            total_settlements_processed=(
                _get_bg_status().get("total_settlements_processed", 0)
                + supplier_result.get("processed", 0)
                + logistics_result.get("processed", 0)
            ),
            is_running=True,
        )
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route: %s", _e)

try:
    def     health():
        """Liveness probe for this router."""
        return {"status": "ok", "router": "core_accounting_routes", "prefix": "/api/v1/accounting"}
    _s7.get("/core_accounting_routes/health")(health)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route health: %s", _e)

try:
    def     status():
        """Report whether a backing controller is importable."""
        return {"router": "core_accounting_routes", "controller": "controllers.finance.accounting_controller" if _HAS_CTRL else None,
                "public_functions": _CTRL_PUBLIC}
    _s7.get("/core_accounting_routes/status")(status)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route status: %s", _e)

try:
    def     health():
        """Liveness probe for this router."""
        return {"status": "ok", "router": "core_commission_routes", "prefix": "/api/v1/commission"}
    _s7.get("/core_commission_routes/health")(health)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route health: %s", _e)

try:
    def     status():
        """Report whether a backing controller is importable."""
        return {"router": "core_commission_routes", "controller": "controllers.finance.commission_controller" if _HAS_CTRL else None,
                "public_functions": _CTRL_PUBLIC}
    _s7.get("/core_commission_routes/status")(status)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route status: %s", _e)

try:
    def     health():
        """Liveness probe for this router."""
        return {"status": "ok", "router": "core_invoices_routes", "prefix": "/api/v1/invoices"}
    _s7.get("/core_invoices_routes/health")(health)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route health: %s", _e)

try:
    def     health():
        """Liveness probe for this router."""
        return {"status": "ok", "router": "core_payroll_routes", "prefix": "/api/v1/payroll"}
    _s7.get("/core_payroll_routes/health")(health)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route health: %s", _e)

try:
    def     health():
        """Liveness probe for this router."""
        return {"status": "ok", "router": "core_treasury_routes", "prefix": "/api/v1/treasury"}
    _s7.get("/core_treasury_routes/health")(health)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route health: %s", _e)

try:
    def     health():
        """Liveness probe for this router."""
        return {"status": "ok", "router": "payout_approval", "prefix": "/api/v1/admin/payout-approval"}
    _s7.get("/payout_approval/health")(health)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route health: %s", _e)

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
    _s7.post("/seed", summary="Seed chart of accounts (idempotent)")(seed_chart_of_accounts)
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
    _s7.get("/accounts", summary="List all accounts")(list_accounts)
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
    _s7.get("/accounts/{code}", summary="Get account by code")(get_account)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route get_account: %s", _e)

try:
    def     create_journal_entry(
        body: accounting_controller.JournalEntryBody,
        db: Session = Depends(get_db),
        current_user=Depends(require_admin),
    ):
        return accounting_controller.create_journal_entry(db, body, current_user)
    _s7.post("/journal-entries", summary="Create a journal entry")(create_journal_entry)
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
    _s7.get("/journal-entries", summary="List journal entries")(list_journal_entries)
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
    _s7.get("/journal-entries/{entry_id}", summary="Get journal entry by ID")(get_journal_entry)
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
    _s7.get("/balances/{account_code}", summary="Get account balance")(get_balance)
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
    _s7.get("/trial-balance", summary="Get trial balance")(trial_balance)
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
    _s7.post("/reports/income-statement", summary="Generate Income Statement (P&L)")(income_statement)
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
    _s7.post("/reports/balance-sheet", summary="Generate Balance Sheet")(balance_sheet)
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
    _s7.post("/reports/cash-flow", summary="Generate Cash Flow Statement")(cash_flow)
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
    _s7.get("/reports", summary="List saved financial reports")(list_reports)
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
    _s7.post("/periods/get-or-create", summary="Get or create a fiscal period")(get_or_create)
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
    _s7.get("/periods/current", summary="Get current fiscal period")(current_period)
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
    _s7.post("/periods/close", summary="Close a fiscal period")(close_fiscal_period)
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
    _s7.get("/periods", summary="List fiscal periods")(list_fiscal_periods)
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
    _s7.post("/journal-entries/reverse", summary="Reverse a journal entry")(reverse_entry)
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
    _s7.post("/cash-flow-forecast", summary="Generate cash flow forecast")(cash_flow_forecast)
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
    _s7.get("/ar", summary="AR sub-ledger (customer receivables)")(get_ar)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route get_ar: %s", _e)

try:
    def     post_ar_invoice_route(body: ARInvoiceBody, db: Session = Depends(get_db), _admin: dict = Depends(require_admin)):
        cleanup = _with_rls(body.country_code, db)
        try:
            return controller_post_ar_invoice(db, **body.model_dump(), admin_user=_admin)
        finally:
            cleanup()
    _s7.post("/ar-ledger/invoice", summary="Post AR invoice")(post_ar_invoice_route)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route post_ar_invoice_route: %s", _e)

try:
    def     post_ar_payment_route(body: ARPaymentBody, db: Session = Depends(get_db), _admin: dict = Depends(require_admin)):
        cleanup = _with_rls(body.country_code, db)
        try:
            return controller_post_ar_payment(db, **body.model_dump(), admin_user=_admin)
        finally:
            cleanup()
    _s7.post("/ar-ledger/payment", summary="Post AR payment")(post_ar_payment_route)
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
    _s7.get("/ap", summary="AP Sub-ledger alias (Accounts Payable)")(get_ap_alias)
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
    _s7.get("/ap-ledger", summary="AP Sub-ledger (Accounts Payable)")(get_ap)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route get_ap: %s", _e)

try:
    def     post_ap_payable_route(body: APPayableBody, db: Session = Depends(get_db), _admin: dict = Depends(require_admin)):
        cleanup = _with_rls(body.country_code, db)
        try:
            return controller_post_ap_payable(db, **body.model_dump(), admin_user=_admin)
        finally:
            cleanup()
    _s7.post("/ap-ledger/payable", summary="Post AP payable")(post_ap_payable_route)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route post_ap_payable_route: %s", _e)

try:
    def     post_ap_payment_route(body: APPaymentBody, db: Session = Depends(get_db), _admin: dict = Depends(require_admin)):
        cleanup = _with_rls(body.country_code, db)
        try:
            return controller_post_ap_payment(db, **body.model_dump(), admin_user=_admin)
        finally:
            cleanup()
    _s7.post("/ap-ledger/payment", summary="Post AP payment")(post_ap_payment_route)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route post_ap_payment_route: %s", _e)

try:
    def     health():
        """Liveness probe for this router."""
        return {"status": "ok", "router": "public_treasury_api_access", "prefix": ""}
    _s7.get("/public_treasury_api_access/health")(health)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route health: %s", _e)

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
    _s7.get("/metrics")(treasury_metrics)
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
    _s7.get("/cash-position")(cash_position)
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
    _s7.get("/vat-liability")(vat_liability)
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
    _s7.get("/supplier-payables")(supplier_payables)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route supplier_payables: %s", _e)

try:
    def _serialize_payout(p: Payout) -> dict[str, Any]:
        return {
            "id": cast(int, p.id),
            "supplier_id": cast(int | None, p.supplier_id),
            "order_id": cast(int | None, p.order_id),
            "amount": float(cast(Decimal, p.amount or 0)),
            "currency": cast(str | None, p.currency) or "OMR",
            "method": cast(str | None, p.method) or "",
            "status": cast(str | None, p.status) or "",
            "reference": cast(str | None, p.reference),
            "notes": cast(str | None, p.notes),
            "country_code": cast(str | None, p.country_code) or "",
            "created_at": cast(Any, p.created_at).isoformat() if getattr(p, "created_at", None) else None,
            "processed_at": cast(Any, p.processed_at).isoformat() if getattr(p, "processed_at", None) else None,
        }
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route: %s", _e)

try:
    def _serialize_batch_item(item: PayoutBatchItem) -> dict[str, Any]:
        return {
            "id": cast(int, item.id),
            "entity_type": cast(str, item.entity_type),
            "entity_id": cast(int, item.entity_id),
            "amount": float(cast(Decimal, item.amount or 0)),
            "currency": cast(str | None, item.currency) or "OMR",
            "reference": cast(str | None, item.reference),
            "status": cast(str | None, item.status) or "",
        }
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route: %s", _e)

try:
    def _serialize_batch(batch: PayoutBatch) -> dict[str, Any]:
        return {
            "id": cast(int, batch.id),
            "batch_number": cast(str, batch.batch_number),
            "country_code": cast(str, batch.country_code),
            "total_amount": float(cast(Decimal, batch.total_amount or 0)),
            "item_count": cast(int, batch.item_count or 0),
            "status": cast(str, batch.status),
            "notes": cast(str | None, batch.notes),
            "created_at": cast(Any, batch.created_at).isoformat() if getattr(batch, "created_at", None) else None,
            "items": [_serialize_batch_item(item) for item in (batch.items or [])],
        }
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route: %s", _e)

try:
    def _resolve_supplier_names(entity_ids: set[int], db: Session) -> dict[int, str]:
        """Return {entity_id: display_name} for supplier IDs."""
        if not entity_ids:
            return {}
        users = db.query(User).filter(User.id.in_(entity_ids)).all()
        return {cast(int, u.id): cast(str, u.username or u.email or f"Supplier #{u.id}") for u in users}
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route: %s", _e)

try:
    def _resolve_logistics_names(entity_ids: set[int], db: Session) -> dict[int, str]:
        """Return {entity_id: display_name} for logistics partner IDs."""
        if not entity_ids:
            return {}
        partners = db.query(LogisticsPartner).filter(LogisticsPartner.id.in_(entity_ids)).all()
        return {cast(int, p.id): cast(str, p.name or f"Partner #{p.id}") for p in partners}
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route: %s", _e)

try:
    def _enrich_batch_items(batch: PayoutBatch, db: Session) -> list[dict[str, Any]]:
        """Return batch items with resolved entity_name fields."""
        items = list(batch.items or [])
        supplier_ids = {cast(int, it.entity_id) for it in items if cast(str, it.entity_type) == "supplier"}
        logistics_ids = {cast(int, it.entity_id) for it in items if cast(str, it.entity_type) == "logistics"}
        supplier_names = _resolve_supplier_names(supplier_ids, db)
        logistics_names = _resolve_logistics_names(logistics_ids, db)
    
        enriched = []
        for item in items:
            e = _serialize_batch_item(item)
            eid = cast(int, item.entity_id)
            etype = cast(str, item.entity_type)
            if etype == "supplier":
                e["entity_name"] = supplier_names.get(eid, f"Supplier #{eid}")
            elif etype == "logistics":
                e["entity_name"] = logistics_names.get(eid, f"Partner #{eid}")
            else:
                e["entity_name"] = f"#{eid}"
            enriched.append(e)
        return enriched
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route: %s", _e)

try:
    def _load_unbatched_payouts(
        db: Session, page: int, page_size: int
    ) -> tuple[list[dict[str, Any]], int]:
        """Return paginated individual Payout records with supplier names.
    
        Shows ALL pending/draft payouts — the frontend distinguishes batched
        vs unbatched by cross-referencing batch items.
        """
        query = db.query(Payout).filter(Payout.status.in_(["pending", "draft"]))
        total = query.count()
        payouts = query.order_by(Payout.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    
        supplier_ids = {cast(int, p.supplier_id) for p in payouts if p.supplier_id}
        supplier_names = _resolve_supplier_names(supplier_ids, db) if supplier_ids else {}
    
        result = []
        for payout in payouts:
            s = _serialize_payout(payout)
            sid = cast(int | None, payout.supplier_id)
            s["supplier_name"] = supplier_names.get(cast(int, sid), f"Supplier #{sid}") if sid else None
            result.append(s)
        return result, total
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route: %s", _e)

try:
    def _load_pending_batches_with_items(db: Session, page: int, page_size: int) -> tuple[list[dict[str, Any]], int]:
        """Return paginated batches in draft/pending status with enriched items."""
        query = db.query(PayoutBatch).options(joinedload(PayoutBatch.items)).filter(
            PayoutBatch.status.in_(["draft", "pending"])
        )
        total = query.count()
        batches = query.order_by(PayoutBatch.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    
        result = []
        for batch in batches:
            enriched_items = _enrich_batch_items(batch, db)
            s = _serialize_batch(batch)
            s["items"] = enriched_items
            result.append(s)
        return result, total
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route: %s", _e)

try:
    def _update_payout_status_by_ids(payout_ids: list[int], status: str, db: Session) -> None:
        """Update status for specific Payout records by their primary key."""
        if payout_ids:
            now = utcnow()
            db.query(Payout).filter(
                Payout.id.in_(payout_ids),
                Payout.status.in_(["pending", "draft", "approved"]),
            ).update({"status": status, "processed_at": now}, synchronize_session=False)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route: %s", _e)

try:
    def     get_pending_payouts(
        page: int = Query(1, ge=1),
        page_size: int = Query(20, ge=1, le=100),
        current_admin: User = Depends(require_admin),
        db: Session = Depends(get_db),
    ) -> dict[str, Any]:
        """Return all pending payout batches and unbatched payouts for admin review.

        Pagination is applied independently to batches and unbatched payouts.
        """
        batches, batch_total = _load_pending_batches_with_items(db, page, page_size)
        unbatched, payout_total = _load_unbatched_payouts(db, page, page_size)

        # ── Also load standalone logistics partner payouts ──
        logistics_payout_q = db.query(LogisticsPartnerPayout).filter(
            LogisticsPartnerPayout.status.in_(["pending", "draft"]),
        )
        logistics_payout_total = logistics_payout_q.count()
        logistics_payouts = logistics_payout_q.order_by(LogisticsPartnerPayout.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

        logistics_ids = {cast(int, lp.partner_id) for lp in logistics_payouts if lp.partner_id}
        logistics_names = _resolve_logistics_names(logistics_ids, db) if logistics_ids else {}

        unbatched_logistics = []
        for lp in logistics_payouts:
            pid = cast(int | None, lp.partner_id)
            unbatched_logistics.append({
                "id": cast(int, lp.id),
                "partner_id": pid,
                "partner_name": logistics_names.get(cast(int, pid), f"Partner #{pid}") if pid else None,
                "amount": float(cast(Decimal, lp.amount or 0)),
                "currency": cast(str | None, lp.currency) or "OMR",
                "status": cast(str | None, lp.status) or "",
                "reference": cast(str | None, lp.reference),
                "notes": cast(str | None, lp.notes),
                "created_at": cast(Any, lp.created_at).isoformat() if getattr(lp, "created_at", None) else None,
            })

        total_amount = sum(b["total_amount"] for b in batches)
        total_items = sum(b["item_count"] for b in batches)

        return {
            "pending_batches": batches,
            "unbatched_payouts": unbatched,
            "unbatched_logistics_payouts": unbatched_logistics,
            "summary": {
                "total_batches": batch_total,
                "total_amount": round(total_amount, 2),
                "total_items": total_items,
                "pending_payouts_count": payout_total,
                "pending_logistics_payouts_count": logistics_payout_total,
            },
            "pagination": {"page": page, "page_size": page_size},
        }
    _s7.get("/pending")(get_pending_payouts)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route get_pending_payouts: %s", _e)

try:
    def     approve_payout(
        payout_id: int,
        payload: ActionRequest | None = None,
        current_admin: User = Depends(require_admin),
        db: Session = Depends(get_db),
    ) -> dict[str, Any]:
        """Approve an individual pending payout record."""
        payout = db.query(Payout).filter(Payout.id == payout_id).first()
        if not payout:
            raise HTTPException(status_code=404, detail="Payout not found")
        if payout.status not in ("pending", "draft"):
            raise HTTPException(
                status_code=409,
                detail=f"Cannot approve payout in '{payout.status}' status.",
            )
        payout.status = "approved"
        if payload and payload.notes:
            payout.notes = (payout.notes or "") + f"\nApproved: {payload.notes}"

        db.commit()
        audit_log(
            db=db, action=AuditAction.PAYOUT_PROCESSED,
            user_id=current_admin.id, username=current_admin.username,
            user_role="admin", resource_type="payout",
            resource_id=payout_id,
            details={"action": "approve", "amount": float(cast(Decimal, payout.amount or 0))},
        )
        return {"message": "Payout approved", "payout_id": payout_id, "status": "approved"}
    _s7.post("/payouts/{payout_id}/approve")(approve_payout)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route approve_payout: %s", _e)

try:
    def     reject_payout(
        payout_id: int,
        payload: ActionRequest | None = None,
        current_admin: User = Depends(require_admin),
        db: Session = Depends(get_db),
    ) -> dict[str, Any]:
        """Reject an individual pending payout record."""
        payout = db.query(Payout).filter(Payout.id == payout_id).first()
        if not payout:
            raise HTTPException(status_code=404, detail="Payout not found")
        if payout.status not in ("pending", "draft", "approved"):
            raise HTTPException(
                status_code=409,
                detail=f"Cannot reject payout in '{payout.status}' status.",
            )
        payout.status = "rejected"
        if payload and payload.notes:
            payout.notes = (payout.notes or "") + f"\nRejected: {payload.notes}"

        db.commit()
        audit_log(
            db=db, action=AuditAction.PAYOUT_PROCESSED,
            user_id=current_admin.id, username=current_admin.username,
            user_role="admin", resource_type="payout",
            resource_id=payout_id,
            details={"action": "reject", "amount": float(cast(Decimal, payout.amount or 0))},
        )
        return {"message": "Payout rejected", "payout_id": payout_id, "status": "rejected"}
    _s7.post("/payouts/{payout_id}/reject")(reject_payout)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route reject_payout: %s", _e)

try:
    def     approve_batch(
        batch_id: int,
        payload: ActionRequest | None = None,
        current_admin: User = Depends(require_admin),
        db: Session = Depends(get_db),
    ) -> dict[str, Any]:
        """Approve a payout batch — moves it from draft → approved."""
        batch = (
            db.query(PayoutBatch)
            .options(joinedload(PayoutBatch.items))
            .filter(PayoutBatch.id == batch_id)
            .first()
        )
        if not batch:
            raise HTTPException(status_code=404, detail="Payout batch not found")
        if batch.status not in ("draft", "pending"):
            raise HTTPException(
                status_code=409,
                detail=f"Cannot approve batch in '{batch.status}' status. Only draft/pending batches can be approved.",
            )
        now = utcnow()
        batch.status = "approved"
        batch.approved_by = cast(int, current_admin.id)
        batch.notes = (batch.notes or "") + (
            f"\nApproved by admin #{current_admin.id} at {now.isoformat()}."
            + (f" Notes: {payload.notes}" if payload and payload.notes else "")
        )
        for item in batch.items or []:
            item.status = "approved"

        db.commit()
        audit_log(
            db=db, action=AuditAction.PAYOUT_PROCESSED,
            user_id=current_admin.id, username=current_admin.username,
            user_role="admin", resource_type="payout_batch",
            resource_id=batch_id,
            details={"action": "approve", "batch_number": batch.batch_number},
        )
        return {"message": "Batch approved", "batch_id": batch_id, "status": "approved"}
    _s7.post("/batches/{batch_id}/approve")(approve_batch)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route approve_batch: %s", _e)

try:
    def     reject_batch(
        batch_id: int,
        payload: ActionRequest | None = None,
        current_admin: User = Depends(require_admin),
        db: Session = Depends(get_db),
    ) -> dict[str, Any]:
        """Reject a payout batch — moves it from draft → rejected."""
        batch = (
            db.query(PayoutBatch)
            .options(joinedload(PayoutBatch.items))
            .filter(PayoutBatch.id == batch_id)
            .first()
        )
        if not batch:
            raise HTTPException(status_code=404, detail="Payout batch not found")
        if batch.status not in ("draft", "pending", "approved"):
            raise HTTPException(
                status_code=409,
                detail=f"Cannot reject batch in '{batch.status}' status.",
            )
        now = utcnow()
        old_status = batch.status
        batch.status = "rejected"
        batch.notes = (batch.notes or "") + (
            f"\nRejected by admin #{current_admin.id} at {now.isoformat()}."
            + (f" Reason: {payload.notes}" if payload and payload.notes else "")
        )
        for item in batch.items or []:
            item.status = "pending"

        db.commit()
        audit_log(
            db=db, action=AuditAction.PAYOUT_PROCESSED,
            user_id=current_admin.id, username=current_admin.username,
            user_role="admin", resource_type="payout_batch",
            resource_id=batch_id,
            details={"action": "reject", "batch_number": batch.batch_number, "previous_status": old_status},
        )
        return {"message": "Batch rejected", "batch_id": batch_id, "status": "rejected"}
    _s7.post("/batches/{batch_id}/reject")(reject_batch)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route reject_batch: %s", _e)

try:
    def     dispatch_batch(
        batch_id: int,
        payload: ActionRequest | None = None,
        current_admin: User = Depends(require_admin),
        db: Session = Depends(get_db),
    ) -> dict[str, Any]:
        """Dispatch (mark as paid) an approved payout batch.

        Updates the batch status to dispatched, marks all batch items as paid,
        and updates the underlying Payout / LogisticsPartnerPayout records to paid.
        """
        batch = (
            db.query(PayoutBatch)
            .options(joinedload(PayoutBatch.items))
            .filter(PayoutBatch.id == batch_id)
            .first()
        )
        if not batch:
            raise HTTPException(status_code=404, detail="Payout batch not found")
        if batch.status != "approved":
            raise HTTPException(
                status_code=409,
                detail=f"Cannot dispatch batch in '{batch.status}' status. Only approved batches can be dispatched.",
            )
        now = utcnow()
        batch.status = "dispatched"
        batch.dispatched_at = now
        batch.notes = (batch.notes or "") + (
            f"\nDispatched by admin #{current_admin.id} at {now.isoformat()}."
            + (f" Notes: {payload.notes}" if payload and payload.notes else "")
        )

        supplier_payout_ids: list[int] = []
        logistics_payout_ids: list[int] = []

        for item in batch.items or []:
            item.status = "paid"
            etype = cast(str, item.entity_type)
            eid = cast(int, item.entity_id)
            if etype == "supplier":
                supplier_payout_ids.append(eid)
            elif etype == "logistics":
                logistics_payout_ids.append(eid)

        # --- Bulk-update Payout records for suppliers in this batch ---
        # Batch items store entity_id = supplier_id (set by the auto-payout
        # scheduler).  We match by Payout.supplier_id, which is the correct
        # column.  This is safe because the status filter (pending/approved)
        # prevents touching already-paid payouts from prior batches.
        if supplier_payout_ids:
            updated = db.query(Payout).filter(
                Payout.supplier_id.in_(supplier_payout_ids),
                Payout.status.in_(["pending", "approved"]),
            ).update({"status": "paid", "processed_at": now}, synchronize_session=False)

        if logistics_payout_ids:
            db.query(LogisticsPartnerPayout).filter(
                LogisticsPartnerPayout.partner_id.in_(logistics_payout_ids),
                LogisticsPartnerPayout.status.in_(["pending", "approved"]),
            ).update({"status": "paid", "processed_at": now}, synchronize_session=False)

        db.commit()
        audit_log(
            db=db, action=AuditAction.PAYOUT_PROCESSED,
            user_id=current_admin.id, username=current_admin.username,
            user_role="admin", resource_type="payout_batch",
            resource_id=batch_id,
            details={"action": "dispatch", "batch_number": batch.batch_number},
        )
        return {"message": "Batch dispatched", "batch_id": batch_id, "status": "dispatched"}
    _s7.post("/batches/{batch_id}/dispatch")(dispatch_batch)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route dispatch_batch: %s", _e)

_s8 = APIRouter(prefix='/api/v1/admin/payout-approval')

try:
    def     health():
        """Liveness probe for this router."""
        return {"status": "ok", "router": "payout_approval", "prefix": "/api/v1/admin/payout-approval"}
    _s8.get("/payout_approval/health")(health)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route health: %s", _e)

_s9 = APIRouter(prefix='')

try:
    def     list_payouts(country_code: str = Path(..., description="ISO country code"), _: User = Depends(require_admin), db: Session = Depends(get_db), page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100)):
        get_country_or_404(country_code.upper(), db)
        set_rls_context({country_code.upper()}, is_restricted=True)
        try:
            q = db.query(Payout).filter(Payout.country_code == country_code.upper())
            total = q.count()
            rows = q.order_by(Payout.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
            return {"data": rows, "total": total, "page": page, "page_size": page_size}
        finally:
            clear_rls_context()
    _s9.get("/payouts/{country_code}")(list_payouts)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route list_payouts: %s", _e)

try:
    def     create_payout(
        country_code: str = Path(..., description="ISO country code"),
        payload: PayoutCreate = None,
        current_admin: User = Depends(require_admin),
        db: Session = Depends(get_db),
    ):
        get_country_or_404(country_code.upper(), db)
        set_rls_context({country_code.upper()}, is_restricted=True)
        try:
            model_cols = {c.name for c in Payout.__table__.columns}
            data = {k: v for k, v in payload.model_dump().items() if k in model_cols}
            p = Payout(**data, country_code=country_code.upper())
            db.add(p); db.commit(); db.refresh(p)
            audit_log(
                db=db, action=AuditAction.PAYOUT_PROCESSED,
                user_id=current_admin.id, username=current_admin.username,
                user_role="admin", resource_type="payout",
                resource_id=p.id,
                details={"amount": str(p.amount) if p.amount else None, "method": p.method},
            )
            return p
        finally:
            clear_rls_context()
    _s9.post("/payouts/{country_code}", response_model=PayoutOut, status_code=201)(create_payout)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route create_payout: %s", _e)

try:
    def     list_pending_payouts(
        current_admin: User = Depends(require_admin),
        db: Session = Depends(get_db),
        page: int = Query(1, ge=1),
        page_size: int = Query(20, ge=1, le=100),
    ):
        """List all pending payouts (RLS-scoped if context is set)."""
        q = db.query(Payout).filter(Payout.status == "pending")
        total = q.count()
        rows = q.order_by(Payout.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
        return {"data": rows, "total": total, "page": page, "page_size": page_size}
    _s9.get("/pending")(list_pending_payouts)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route list_pending_payouts: %s", _e)

try:
    def     list_pending_payouts_by_country(
        country_code: str = Path(..., description="ISO country code"),
        current_admin: User = Depends(require_admin),
        db: Session = Depends(get_db),
        page: int = Query(1, ge=1),
        page_size: int = Query(20, ge=1, le=100),
    ):
        """List pending payouts for a specific country."""
        get_country_or_404(country_code.upper(), db)
        set_rls_context({country_code.upper()}, is_restricted=True)
        try:
            q = db.query(Payout).filter(Payout.status == "pending", Payout.country_code == country_code.upper())
            total = q.count()
            rows = q.order_by(Payout.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
            return {"data": rows, "total": total, "page": page, "page_size": page_size}
        finally:
            clear_rls_context()
    _s9.get("/payouts/{country_code}/pending")(list_pending_payouts_by_country)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route list_pending_payouts_by_country: %s", _e)

try:
    def     verify_payout(
        country_code: str = Path(..., description="ISO country code"),
        payout_id: int = Path(...),
        payload: PayoutVerifyRequest = None,
        current_admin: User = Depends(require_admin),
        db: Session = Depends(get_db),
    ):
        """Verify a payout."""
        get_country_or_404(country_code.upper(), db)
        set_rls_context({country_code.upper()}, is_restricted=True)
        try:
            p = db.query(Payout).filter(Payout.id == payout_id, Payout.country_code == country_code.upper()).first()
            if not p:
                raise HTTPException(404, "Payout not found")
            p.status = payload.status if payload and payload.status else "verified"
            p.processed_at = utcnow()
            if payload:
                if payload.note:
                    p.notes = payload.note
                if payload.bank_reference:
                    p.reference = payload.bank_reference
            db.commit()
            audit_log(
                db=db, action=AuditAction.PAYOUT_PROCESSED,
                user_id=current_admin.id, username=current_admin.username,
                user_role="admin", resource_type="payout",
                resource_id=payout_id,
                details={"status": p.status, "reference": p.reference, "notes": p.notes},
            )
            return {"verified": True, "payout_id": payout_id}
        finally:
            clear_rls_context()
    _s9.post("/payouts/{country_code}/{payout_id}/verify")(verify_payout)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route verify_payout: %s", _e)

try:
    def     run_auto_payout_sweep(
        db: Session = Depends(get_db),
        current_admin: User = Depends(require_admin),
    ):
        """Manually trigger the auto-payout sweep for eligible settlements.

        Runs both supplier and logistics settlement sweeps:
          1. Finds pending SupplierSettlements where ``eligible_at`` has passed
             → creates Payout records + PayoutBatchItems (entity_type="supplier")
          2. Finds pending LogisticsSettlements where ``eligible_at`` has passed
             → creates LogisticsPartnerPayout records + PayoutBatchItems (entity_type="logistics")

        Returns a combined summary dict.
        """
        admin_ref = f"Manually triggered by admin #{getattr(current_admin, 'id', '?')}"

        supplier_result = _run_supplier_sweep(db, batch_notes=admin_ref)
        if supplier_result.get("status") == "error":
            raise HTTPException(status_code=500, detail=supplier_result.get("error", "Supplier sweep failed"))

        logistics_result = _run_logistics_sweep(db, batch_notes=admin_ref)
        if logistics_result.get("status") == "error":
            raise HTTPException(status_code=500, detail=logistics_result.get("error", "Logistics sweep failed"))

        return {
            "supplier": supplier_result,
            "logistics": logistics_result,
            "total_processed": (supplier_result.get("processed", 0) + logistics_result.get("processed", 0)),
            "status": "ok",
        }
    _s9.post("/payouts/run-auto-sweep")(run_auto_payout_sweep)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route run_auto_payout_sweep: %s", _e)

try:
    def     process_payout(
        country_code: str = Path(..., description="ISO country code"),
        payout_id: int = Path(...),
        current_admin: User = Depends(require_admin),
        db: Session = Depends(get_db),
    ):
        get_country_or_404(country_code.upper(), db)
        set_rls_context({country_code.upper()}, is_restricted=True)
        try:
            p = db.query(Payout).filter(Payout.id == payout_id, Payout.country_code == country_code.upper()).first()
            if not p: raise HTTPException(404)
            p.status = "paid"; p.processed_at = utcnow()
            db.commit()
            audit_log(
                db=db, action=AuditAction.PAYOUT_PROCESSED,
                user_id=current_admin.id, username=current_admin.username,
                user_role="admin", resource_type="payout",
                resource_id=payout_id,
                details={"status": "paid"},
            )
            return {"message": "Payout processed"}
        finally:
            clear_rls_context()
    _s9.put("/payouts/{country_code}/{payout_id}/process")(process_payout)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route process_payout: %s", _e)

try:
    def     get_background_job_status_endpoint(
        db: Session = Depends(get_db),
        current_admin: User = Depends(require_admin),
    ):
        """Return the current state of the auto-payout background job:
        is_running, last_run_at, last_run_status, last_error, total counts,
        and recent FinanceAutomationLog entries.
        """
        status = _get_bg_status()

        # Enrich with recent history from FinanceAutomationLog
        history = (
            db.query(FinanceAutomationLog)
            .filter(
                FinanceAutomationLog.kind.in_(["auto_payout", "auto_logistics_payout"]),
            )
            .order_by(FinanceAutomationLog.created_at.desc())
            .limit(20)
            .all()
        )

        return {
            "status": status,
            "history": [
                {
                    "id": h.id,
                    "kind": h.kind,
                    "records_processed": h.records_processed,
                    "records_changed": h.records_changed,
                    "detail": h.detail,
                    "created_at": h.created_at.isoformat() if h.created_at else None,
                }
                for h in history
            ],
        }
    _s9.get("/background-job-status")(get_background_job_status_endpoint)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route get_background_job_status_endpoint: %s", _e)

try:
    def     start_background_job(
        current_admin: User = Depends(require_admin),
    ):
        """Start the auto-payout scheduler background thread."""
        _start_bg_job()
        return {"status": "ok", "message": "Background job started"}
    _s9.post("/background-job/start")(start_background_job)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route start_background_job: %s", _e)

try:
    def     stop_background_job(
        current_admin: User = Depends(require_admin),
    ):
        """Stop the auto-payout scheduler background thread gracefully."""
        _stop_bg_job()
        return {"status": "ok", "message": "Background job stopping"}
    _s9.post("/background-job/stop")(stop_background_job)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route stop_background_job: %s", _e)

try:
    def     trigger_background_job(
        db: Session = Depends(get_db),
        current_admin: User = Depends(require_admin),
    ):
        """Run the auto-payout sweep immediately (both supplier and logistics).

        Returns the combined sweep result.
        """
        admin_ref = f"Manually triggered by admin #{getattr(current_admin, 'id', '?')}"

        supplier_result = _run_supplier_sweep(db, batch_notes=admin_ref)
        if supplier_result.get("status") == "error":
            raise HTTPException(status_code=500, detail=supplier_result.get("error", "Supplier sweep failed"))

        logistics_result = _run_logistics_sweep(db, batch_notes=admin_ref)
        if logistics_result.get("status") == "error":
            raise HTTPException(status_code=500, detail=logistics_result.get("error", "Logistics sweep failed"))

        # Update in-memory status after the manual trigger
        _update_bg_status_after_manual_trigger(supplier_result, logistics_result)

        return {
            "supplier": supplier_result,
            "logistics": logistics_result,
            "total_processed": (supplier_result.get("processed", 0) + logistics_result.get("processed", 0)),
            "status": "ok",
        }
    _s9.post("/background-job/trigger")(trigger_background_job)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route trigger_background_job: %s", _e)

try:
    def     trigger_background_job_kind(
        kind: str = Path(..., description="'supplier' or 'logistics'"),
        db: Session = Depends(get_db),
        current_admin: User = Depends(require_admin),
    ):
        """Run ONLY the supplier OR logistics sweep individually.

        Use this from the history table "Run Now" buttons to re-run a specific
        sweep type without touching the other.
        """
        if kind not in ("supplier", "logistics"):
            raise HTTPException(status_code=400, detail="kind must be 'supplier' or 'logistics'")

        admin_ref = f"Manually triggered by admin #{getattr(current_admin, 'id', '?')} — single sweep"

        if kind == "supplier":
            result = _run_supplier_sweep(db, batch_notes=admin_ref)
            if result.get("status") == "error":
                raise HTTPException(status_code=500, detail=result.get("error", "Supplier sweep failed"))
            # Update in-memory status for just supplier
            _update_bg_status_after_manual_trigger(result, {"status": "no_eligible_settlements", "processed": 0})
        else:
            result = _run_logistics_sweep(db, batch_notes=admin_ref)
            if result.get("status") == "error":
                raise HTTPException(status_code=500, detail=result.get("error", "Logistics sweep failed"))
            _update_bg_status_after_manual_trigger({"status": "no_eligible_settlements", "processed": 0}, result)

        return result
    _s9.post("/background-job/trigger/{kind}")(trigger_background_job_kind)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route trigger_background_job_kind: %s", _e)

try:
    def _update_bg_status_after_manual_trigger(
        supplier_result: dict,
        logistics_result: dict,
    ) -> None:
        """Update the in-memory background job status after a manual trigger."""
        from domains.finance.services.payouts.payout_batch_service import update_background_status
    
        supplier_status = supplier_result.get("status", "error")
        logistics_status = logistics_result.get("status", "error")
        has_error = supplier_status == "error" or logistics_status == "error"
        overall_error = supplier_result.get("error") or logistics_result.get("error") if has_error else None
    
        now = utcnow()
        update_background_status(
            last_run_at=now.isoformat(),
            last_run_status="error" if overall_error else "ok",
            last_error=overall_error,
            last_supplier_result=supplier_result,
            last_logistics_result=logistics_result,
            total_sweep_count=(_get_bg_status().get("total_sweep_count", 0) + 1),
            total_settlements_processed=(
                _get_bg_status().get("total_settlements_processed", 0)
                + supplier_result.get("processed", 0)
                + logistics_result.get("processed", 0)
            ),
            is_running=True,
        )
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route: %s", _e)

_s10 = APIRouter(prefix='')

try:
    def     get_pending_payouts_route(

        limit: int = 200,

        offset: int = 0,

        db: Session = Depends(get_db),

        current_admin: dict = Depends(get_current_admin),

    ):

        require_permission("payouts.verify", current_admin)

        return list_pending_payouts(db, limit=limit, offset=offset)
    _s10.get("/payouts/pending")(get_pending_payouts_route)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route get_pending_payouts_route: %s", _e)

try:
    def     verify_payout_route(

        payout_id: int,

        data: dict,

        db: Session = Depends(get_db),

        current_admin: dict = Depends(require_admin_2fa_verified),

    ):

        require_permission("payouts.verify", current_admin)

        payout = get_payout_by_id(db, payout_id)

        amount = float(payout.amount) if payout and payout.amount is not None else None

        require_approval(db, current_admin["id"], "payout", amount=amount)

        return verify_payout(payout_id, data, current_admin, db)
    _s10.post("/payouts/{payout_id}/verify")(verify_payout_route)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route verify_payout_route: %s", _e)

_s11 = APIRouter(prefix='/api/v1/admin')

try:
    def     health():
        """Liveness probe for this router."""
        return {"status": "ok", "router": "admin_payouts_routes", "prefix": "/api/v1/admin"}
    _s11.get("/admin_payouts_routes/health")(health)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route health: %s", _e)

_s15 = APIRouter(prefix='/api/v1/admin')

try:
    def     list_accounts(country_code: str = Path(..., description="ISO country code"), _: User = Depends(require_admin), db: Session = Depends(get_db)):
        get_country_or_404(country_code.upper(), db)
        set_rls_context({country_code.upper()}, is_restricted=True)
        try:
            return db.query(CashAccount).filter(CashAccount.is_active == True, CashAccount.country_code == country_code.upper()).all()
        finally:
            clear_rls_context()
    _s15.get("/{country_code}/accounts", response_model=list[CashAccountOut])(list_accounts)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route list_accounts: %s", _e)

try:
    def     create_account(country_code: str = Path(..., description="ISO country code"), payload: CashAccountCreate = None, _: User = Depends(require_admin), db: Session = Depends(get_db)):
        get_country_or_404(country_code.upper(), db)
        set_rls_context({country_code.upper()}, is_restricted=True)
        try:
            a = CashAccount(**payload.model_dump(), country_code=country_code.upper())
            db.add(a); db.commit(); db.refresh(a)
            return a
        finally:
            clear_rls_context()
    _s15.post("/{country_code}/accounts", response_model=CashAccountOut, status_code=201)(create_account)
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
            tx = CashTransaction(**payload.model_dump(), balance_after=account.balance, performed_by=current_user.id, country_code=country_code.upper())
            db.add(tx); db.commit(); db.refresh(tx)
            return tx
        finally:
            clear_rls_context()
    _s15.post("/{country_code}/transactions", response_model=CashTransactionOut, status_code=201)(create_transaction)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route create_transaction: %s", _e)

_s16 = APIRouter(prefix='/api/v1/admin')

try:
    def _serialize_payout(p: Payout) -> dict[str, Any]:
        return {
            "id": cast(int, p.id),
            "supplier_id": cast(int | None, p.supplier_id),
            "order_id": cast(int | None, p.order_id),
            "amount": float(cast(Decimal, p.amount or 0)),
            "currency": cast(str | None, p.currency) or "OMR",
            "method": cast(str | None, p.method) or "",
            "status": cast(str | None, p.status) or "",
            "reference": cast(str | None, p.reference),
            "notes": cast(str | None, p.notes),
            "country_code": cast(str | None, p.country_code) or "",
            "created_at": cast(Any, p.created_at).isoformat() if getattr(p, "created_at", None) else None,
            "processed_at": cast(Any, p.processed_at).isoformat() if getattr(p, "processed_at", None) else None,
        }
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route: %s", _e)

try:
    def _serialize_batch_item(item: PayoutBatchItem) -> dict[str, Any]:
        return {
            "id": cast(int, item.id),
            "entity_type": cast(str, item.entity_type),
            "entity_id": cast(int, item.entity_id),
            "amount": float(cast(Decimal, item.amount or 0)),
            "currency": cast(str | None, item.currency) or "OMR",
            "reference": cast(str | None, item.reference),
            "status": cast(str | None, item.status) or "",
        }
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route: %s", _e)

try:
    def _serialize_batch(batch: PayoutBatch) -> dict[str, Any]:
        return {
            "id": cast(int, batch.id),
            "batch_number": cast(str, batch.batch_number),
            "country_code": cast(str, batch.country_code),
            "total_amount": float(cast(Decimal, batch.total_amount or 0)),
            "item_count": cast(int, batch.item_count or 0),
            "status": cast(str, batch.status),
            "notes": cast(str | None, batch.notes),
            "created_at": cast(Any, batch.created_at).isoformat() if getattr(batch, "created_at", None) else None,
            "items": [_serialize_batch_item(item) for item in (batch.items or [])],
        }
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route: %s", _e)

try:
    def _resolve_supplier_names(entity_ids: set[int], db: Session) -> dict[int, str]:
        """Return {entity_id: display_name} for supplier IDs."""
        if not entity_ids:
            return {}
        users = db.query(User).filter(User.id.in_(entity_ids)).all()
        return {cast(int, u.id): cast(str, u.username or u.email or f"Supplier #{u.id}") for u in users}
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route: %s", _e)

try:
    def _resolve_logistics_names(entity_ids: set[int], db: Session) -> dict[int, str]:
        """Return {entity_id: display_name} for logistics partner IDs."""
        if not entity_ids:
            return {}
        partners = db.query(LogisticsPartner).filter(LogisticsPartner.id.in_(entity_ids)).all()
        return {cast(int, p.id): cast(str, p.name or f"Partner #{p.id}") for p in partners}
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route: %s", _e)

try:
    def _enrich_batch_items(batch: PayoutBatch, db: Session) -> list[dict[str, Any]]:
        """Return batch items with resolved entity_name fields."""
        items = list(batch.items or [])
        supplier_ids = {cast(int, it.entity_id) for it in items if cast(str, it.entity_type) == "supplier"}
        logistics_ids = {cast(int, it.entity_id) for it in items if cast(str, it.entity_type) == "logistics"}
        supplier_names = _resolve_supplier_names(supplier_ids, db)
        logistics_names = _resolve_logistics_names(logistics_ids, db)
    
        enriched = []
        for item in items:
            e = _serialize_batch_item(item)
            eid = cast(int, item.entity_id)
            etype = cast(str, item.entity_type)
            if etype == "supplier":
                e["entity_name"] = supplier_names.get(eid, f"Supplier #{eid}")
            elif etype == "logistics":
                e["entity_name"] = logistics_names.get(eid, f"Partner #{eid}")
            else:
                e["entity_name"] = f"#{eid}"
            enriched.append(e)
        return enriched
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route: %s", _e)

try:
    def _load_unbatched_payouts(db: Session, page: int, page_size: int) -> tuple[list[dict[str, Any]], int]:
        """Return paginated individual Payout records with supplier names."""
        query = db.query(Payout).filter(Payout.status.in_(["pending", "draft"]))
        total = query.count()
        payouts = query.order_by(Payout.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    
        supplier_ids = {cast(int, p.supplier_id) for p in payouts if p.supplier_id}
        supplier_names = _resolve_supplier_names(supplier_ids, db) if supplier_ids else {}
    
        result = []
        for payout in payouts:
            s = _serialize_payout(payout)
            sid = cast(int | None, payout.supplier_id)
            s["supplier_name"] = supplier_names.get(cast(int, sid), f"Supplier #{sid}") if sid else None
            result.append(s)
        return result, total
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route: %s", _e)

try:
    def _load_pending_batches_with_items(db: Session, page: int, page_size: int) -> tuple[list[dict[str, Any]], int]:
        """Return paginated batches in draft/pending status with enriched items."""
        query = db.query(PayoutBatch).options(joinedload(PayoutBatch.items)).filter(
            PayoutBatch.status.in_(["draft", "pending"])
        )
        total = query.count()
        batches = query.order_by(PayoutBatch.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    
        result = []
        for batch in batches:
            enriched_items = _enrich_batch_items(batch, db)
            s = _serialize_batch(batch)
            s["items"] = enriched_items
            result.append(s)
        return result, total
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route: %s", _e)

try:
    def     get_pending_payouts(
        page: int = Query(1, ge=1),
        page_size: int = Query(20, ge=1, le=100),
        current_admin: User = Depends(require_admin),
        db: Session = Depends(get_db),
    ) -> dict[str, Any]:
        """Return all pending payout batches and unbatched payouts for admin review.

        Pagination is applied independently to batches and unbatched payouts.
        """
        batches, batch_total = _load_pending_batches_with_items(db, page, page_size)
        unbatched, payout_total = _load_unbatched_payouts(db, page, page_size)

        # ── Also load standalone logistics partner payouts ──
        logistics_payout_q = db.query(LogisticsPartnerPayout).filter(
            LogisticsPartnerPayout.status.in_(["pending", "draft"]),
        )
        logistics_payout_total = logistics_payout_q.count()
        logistics_payouts = logistics_payout_q.order_by(LogisticsPartnerPayout.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

        logistics_ids = {cast(int, lp.partner_id) for lp in logistics_payouts if lp.partner_id}
        logistics_names = _resolve_logistics_names(logistics_ids, db) if logistics_ids else {}

        unbatched_logistics = []
        for lp in logistics_payouts:
            pid = cast(int | None, lp.partner_id)
            unbatched_logistics.append({
                "id": cast(int, lp.id),
                "partner_id": pid,
                "partner_name": logistics_names.get(cast(int, pid), f"Partner #{pid}") if pid else None,
                "amount": float(cast(Decimal, lp.amount or 0)),
                "currency": cast(str | None, lp.currency) or "OMR",
                "status": cast(str | None, lp.status) or "",
                "reference": cast(str | None, lp.reference),
                "notes": cast(str | None, lp.notes),
                "created_at": cast(Any, lp.created_at).isoformat() if getattr(lp, "created_at", None) else None,
            })

        total_amount = sum(b["total_amount"] for b in batches)
        total_items = sum(b["item_count"] for b in batches)

        return {
            "pending_batches": batches,
            "unbatched_payouts": unbatched,
            "unbatched_logistics_payouts": unbatched_logistics,
            "summary": {
                "total_batches": batch_total,
                "total_amount": round(total_amount, 2),
                "total_items": total_items,
                "pending_payouts_count": payout_total,
                "pending_logistics_payouts_count": logistics_payout_total,
            },
            "pagination": {"page": page, "page_size": page_size},
        }
    _s16.get("/pending")(get_pending_payouts)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route get_pending_payouts: %s", _e)

try:
    def     approve_payout(
        payout_id: int,
        payload: ActionRequest | None = None,
        current_admin: User = Depends(require_admin),
        db: Session = Depends(get_db),
    ) -> dict[str, Any]:
        """Approve an individual pending payout record."""
        return approve_payout_action(db, payout_id, current_admin, payload)
    _s16.post("/payouts/{payout_id}/approve")(approve_payout)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route approve_payout: %s", _e)

try:
    def     reject_payout(
        payout_id: int,
        payload: ActionRequest | None = None,
        current_admin: User = Depends(require_admin),
        db: Session = Depends(get_db),
    ) -> dict[str, Any]:
        """Reject an individual pending payout record."""
        return reject_payout_action(db, payout_id, current_admin, payload)
    _s16.post("/payouts/{payout_id}/reject")(reject_payout)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route reject_payout: %s", _e)

try:
    def     approve_batch(
        batch_id: int,
        payload: ActionRequest | None = None,
        current_admin: User = Depends(require_admin),
        db: Session = Depends(get_db),
    ) -> dict[str, Any]:
        """Approve a payout batch — moves it from draft → approved."""
        return approve_batch_action(db, batch_id, current_admin, payload)
    _s16.post("/batches/{batch_id}/approve")(approve_batch)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route approve_batch: %s", _e)

try:
    def     reject_batch(
        batch_id: int,
        payload: ActionRequest | None = None,
        current_admin: User = Depends(require_admin),
        db: Session = Depends(get_db),
    ) -> dict[str, Any]:
        """Reject a payout batch — moves it from draft → rejected."""
        return reject_batch_action(db, batch_id, current_admin, payload)
    _s16.post("/batches/{batch_id}/reject")(reject_batch)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route reject_batch: %s", _e)

try:
    def     dispatch_batch(
        batch_id: int,
        payload: ActionRequest | None = None,
        current_admin: User = Depends(require_admin),
        db: Session = Depends(get_db),
    ) -> dict[str, Any]:
        """Dispatch (mark as paid) an approved payout batch."""
        return dispatch_batch_action(db, batch_id, current_admin, payload)
    _s16.post("/batches/{batch_id}/dispatch")(dispatch_batch)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route dispatch_batch: %s", _e)

_s17 = APIRouter(prefix='/api/v1/admin')

try:
    def     approve_payout_route(
        payout_id: int,
        current_user: dict = Depends(require_admin),
        db: Session = Depends(get_db),
        payload: Any = Body(...)
    ) -> dict[str, Any]:
        return approve_payout(payout_id=payout_id, current_user=current_user, db=db, payload=payload)
    _s17.post("/payouts/{payout_id}/approve", status_code=201, tags=['treasury-payouts'])(approve_payout_route)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route approve_payout_route: %s", _e)

try:
    def     reject_payout_route(
        payout_id: int,
        current_user: dict = Depends(require_admin),
        db: Session = Depends(get_db),
        payload: Any = Body(...)
    ) -> dict[str, Any]:
        return reject_payout(payout_id=payout_id, current_user=current_user, db=db, payload=payload)
    _s17.post("/payouts/{payout_id}/reject", status_code=201, tags=['treasury-payouts'])(reject_payout_route)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route reject_payout_route: %s", _e)

try:
    def     approve_batch_route(
        batch_id: int,
        current_user: dict = Depends(require_admin),
        db: Session = Depends(get_db),
        payload: Any = Body(...)
    ) -> dict[str, Any]:
        return approve_batch(batch_id=batch_id, current_user=current_user, db=db, payload=payload)
    _s17.post("/batches/{batch_id}/approve", status_code=201, tags=['treasury-payouts'])(approve_batch_route)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route approve_batch_route: %s", _e)

try:
    def     reject_batch_route(
        batch_id: int,
        current_user: dict = Depends(require_admin),
        db: Session = Depends(get_db),
        payload: Any = Body(...)
    ) -> dict[str, Any]:
        return reject_batch(batch_id=batch_id, current_user=current_user, db=db, payload=payload)
    _s17.post("/batches/{batch_id}/reject", status_code=201, tags=['treasury-payouts'])(reject_batch_route)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route reject_batch_route: %s", _e)

try:
    def     dispatch_batch_route(
        batch_id: int,
        current_user: dict = Depends(require_admin),
        db: Session = Depends(get_db),
        payload: Any = Body(...)
    ) -> dict[str, Any]:
        return dispatch_batch(batch_id=batch_id, current_user=current_user, db=db, payload=payload)
    _s17.post("/batches/{batch_id}/dispatch", status_code=201, tags=['treasury-payouts'])(dispatch_batch_route)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route dispatch_batch_route: %s", _e)

_s20 = APIRouter(prefix='/api/v1/admin')

try:
    def     list_payouts(country_code: str = Path(..., description="ISO country code"), _: User = Depends(require_admin), db: Session = Depends(get_db), page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100)):
        get_country_or_404(country_code.upper(), db)
        set_rls_context({country_code.upper()}, is_restricted=True)
        try:
            q = db.query(Payout).filter(Payout.country_code == country_code.upper())
            total = q.count()
            rows = q.order_by(Payout.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
            return {"data": rows, "total": total, "page": page, "page_size": page_size}
        finally:
            clear_rls_context()
    _s20.get("/payouts/{country_code}")(list_payouts)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route list_payouts: %s", _e)

try:
    def     create_payout(
        country_code: str = Path(..., description="ISO country code"),
        payload: PayoutCreate = None,
        current_admin: User = Depends(require_admin),
        db: Session = Depends(get_db),
    ):
        get_country_or_404(country_code.upper(), db)
        set_rls_context({country_code.upper()}, is_restricted=True)
        try:
            model_cols = {c.name for c in Payout.__table__.columns}
            data = {k: v for k, v in payload.model_dump().items() if k in model_cols}
            p = Payout(**data, country_code=country_code.upper())
            db.add(p); db.commit(); db.refresh(p)
            audit_log(
                db=db, action=AuditAction.PAYOUT_PROCESSED,
                user_id=current_admin.id, username=current_admin.username,
                user_role="admin", resource_type="payout",
                resource_id=p.id,
                details={"amount": str(p.amount) if p.amount else None, "method": p.method},
            )
            return p
        finally:
            clear_rls_context()
    _s20.post("/payouts/{country_code}", response_model=PayoutOut, status_code=201)(create_payout)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route create_payout: %s", _e)

try:
    def     list_pending_payouts(
        current_admin: User = Depends(require_admin),
        db: Session = Depends(get_db),
        page: int = Query(1, ge=1),
        page_size: int = Query(20, ge=1, le=100),
    ):
        """List all pending payouts (RLS-scoped if context is set)."""
        q = db.query(Payout).filter(Payout.status == "pending")
        total = q.count()
        rows = q.order_by(Payout.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
        return {"data": rows, "total": total, "page": page, "page_size": page_size}
    _s20.get("/pending")(list_pending_payouts)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route list_pending_payouts: %s", _e)

try:
    def     list_pending_payouts_by_country(
        country_code: str = Path(..., description="ISO country code"),
        current_admin: User = Depends(require_admin),
        db: Session = Depends(get_db),
        page: int = Query(1, ge=1),
        page_size: int = Query(20, ge=1, le=100),
    ):
        """List pending payouts for a specific country."""
        get_country_or_404(country_code.upper(), db)
        set_rls_context({country_code.upper()}, is_restricted=True)
        try:
            q = db.query(Payout).filter(Payout.status == "pending", Payout.country_code == country_code.upper())
            total = q.count()
            rows = q.order_by(Payout.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
            return {"data": rows, "total": total, "page": page, "page_size": page_size}
        finally:
            clear_rls_context()
    _s20.get("/payouts/{country_code}/pending")(list_pending_payouts_by_country)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route list_pending_payouts_by_country: %s", _e)

try:
    def     verify_payout(
        country_code: str = Path(..., description="ISO country code"),
        payout_id: int = Path(...),
        payload: PayoutVerifyRequest = None,
        current_admin: User = Depends(require_admin),
        db: Session = Depends(get_db),
    ):
        """Verify a payout."""
        get_country_or_404(country_code.upper(), db)
        set_rls_context({country_code.upper()}, is_restricted=True)
        try:
            p = db.query(Payout).filter(Payout.id == payout_id, Payout.country_code == country_code.upper()).first()
            if not p:
                raise HTTPException(404, "Payout not found")
            p.status = payload.status if payload and payload.status else "verified"
            p.processed_at = utcnow()
            if payload:
                if payload.note:
                    p.notes = payload.note
                if payload.bank_reference:
                    p.reference = payload.bank_reference
            db.commit()
            audit_log(
                db=db, action=AuditAction.PAYOUT_PROCESSED,
                user_id=current_admin.id, username=current_admin.username,
                user_role="admin", resource_type="payout",
                resource_id=payout_id,
                details={"status": p.status, "reference": p.reference, "notes": p.notes},
            )
            return {"verified": True, "payout_id": payout_id}
        finally:
            clear_rls_context()
    _s20.post("/payouts/{country_code}/{payout_id}/verify")(verify_payout)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route verify_payout: %s", _e)

try:
    def     run_auto_payout_sweep(
        db: Session = Depends(get_db),
        current_admin: User = Depends(require_admin),
    ):
        """Manually trigger the auto-payout sweep for eligible settlements.

        Runs both supplier and logistics settlement sweeps:
          1. Finds pending SupplierSettlements where ``eligible_at`` has passed
             → creates Payout records + PayoutBatchItems (entity_type="supplier")
          2. Finds pending LogisticsSettlements where ``eligible_at`` has passed
             → creates LogisticsPartnerPayout records + PayoutBatchItems (entity_type="logistics")

        Returns a combined summary dict.
        """
        admin_ref = f"Manually triggered by admin #{getattr(current_admin, 'id', '?')}"

        supplier_result = _run_supplier_sweep(db, batch_notes=admin_ref)
        if supplier_result.get("status") == "error":
            raise HTTPException(status_code=500, detail=supplier_result.get("error", "Supplier sweep failed"))

        logistics_result = _run_logistics_sweep(db, batch_notes=admin_ref)
        if logistics_result.get("status") == "error":
            raise HTTPException(status_code=500, detail=logistics_result.get("error", "Logistics sweep failed"))

        return {
            "supplier": supplier_result,
            "logistics": logistics_result,
            "total_processed": (supplier_result.get("processed", 0) + logistics_result.get("processed", 0)),
            "status": "ok",
        }
    _s20.post("/payouts/run-auto-sweep")(run_auto_payout_sweep)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route run_auto_payout_sweep: %s", _e)

try:
    def     process_payout(
        country_code: str = Path(..., description="ISO country code"),
        payout_id: int = Path(...),
        current_admin: User = Depends(require_admin),
        db: Session = Depends(get_db),
    ):
        get_country_or_404(country_code.upper(), db)
        set_rls_context({country_code.upper()}, is_restricted=True)
        try:
            p = db.query(Payout).filter(Payout.id == payout_id, Payout.country_code == country_code.upper()).first()
            if not p: raise HTTPException(404)
            p.status = "paid"; p.processed_at = utcnow()
            db.commit()
            audit_log(
                db=db, action=AuditAction.PAYOUT_PROCESSED,
                user_id=current_admin.id, username=current_admin.username,
                user_role="admin", resource_type="payout",
                resource_id=payout_id,
                details={"status": "paid"},
            )
            return {"message": "Payout processed"}
        finally:
            clear_rls_context()
    _s20.put("/payouts/{country_code}/{payout_id}/process")(process_payout)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route process_payout: %s", _e)

try:
    def     get_background_job_status_endpoint(
        db: Session = Depends(get_db),
        current_admin: User = Depends(require_admin),
    ):
        """Return the current state of the auto-payout background job:
        is_running, last_run_at, last_run_status, last_error, total counts,
        and recent FinanceAutomationLog entries.
        """
        status = _get_bg_status()

        # Enrich with recent history from FinanceAutomationLog
        history = (
            db.query(FinanceAutomationLog)
            .filter(
                FinanceAutomationLog.kind.in_(["auto_payout", "auto_logistics_payout"]),
            )
            .order_by(FinanceAutomationLog.created_at.desc())
            .limit(20)
            .all()
        )

        return {
            "status": status,
            "history": [
                {
                    "id": h.id,
                    "kind": h.kind,
                    "records_processed": h.records_processed,
                    "records_changed": h.records_changed,
                    "detail": h.detail,
                    "created_at": h.created_at.isoformat() if h.created_at else None,
                }
                for h in history
            ],
        }
    _s20.get("/background-job-status")(get_background_job_status_endpoint)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route get_background_job_status_endpoint: %s", _e)

try:
    def     start_background_job(
        current_admin: User = Depends(require_admin),
    ):
        """Start the auto-payout scheduler background thread."""
        _start_bg_job()
        return {"status": "ok", "message": "Background job started"}
    _s20.post("/background-job/start")(start_background_job)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route start_background_job: %s", _e)

try:
    def     stop_background_job(
        current_admin: User = Depends(require_admin),
    ):
        """Stop the auto-payout scheduler background thread gracefully."""
        _stop_bg_job()
        return {"status": "ok", "message": "Background job stopping"}
    _s20.post("/background-job/stop")(stop_background_job)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route stop_background_job: %s", _e)

try:
    def     trigger_background_job(
        db: Session = Depends(get_db),
        current_admin: User = Depends(require_admin),
    ):
        """Run the auto-payout sweep immediately (both supplier and logistics).

        Returns the combined sweep result.
        """
        admin_ref = f"Manually triggered by admin #{getattr(current_admin, 'id', '?')}"

        supplier_result = _run_supplier_sweep(db, batch_notes=admin_ref)
        if supplier_result.get("status") == "error":
            raise HTTPException(status_code=500, detail=supplier_result.get("error", "Supplier sweep failed"))

        logistics_result = _run_logistics_sweep(db, batch_notes=admin_ref)
        if logistics_result.get("status") == "error":
            raise HTTPException(status_code=500, detail=logistics_result.get("error", "Logistics sweep failed"))

        # Update in-memory status after the manual trigger
        _update_bg_status_after_manual_trigger(supplier_result, logistics_result)

        return {
            "supplier": supplier_result,
            "logistics": logistics_result,
            "total_processed": (supplier_result.get("processed", 0) + logistics_result.get("processed", 0)),
            "status": "ok",
        }
    _s20.post("/background-job/trigger")(trigger_background_job)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route trigger_background_job: %s", _e)

try:
    def     trigger_background_job_kind(
        kind: str = Path(..., description="'supplier' or 'logistics'"),
        db: Session = Depends(get_db),
        current_admin: User = Depends(require_admin),
    ):
        """Run ONLY the supplier OR logistics sweep individually.

        Use this from the history table "Run Now" buttons to re-run a specific
        sweep type without touching the other.
        """
        if kind not in ("supplier", "logistics"):
            raise HTTPException(status_code=400, detail="kind must be 'supplier' or 'logistics'")

        admin_ref = f"Manually triggered by admin #{getattr(current_admin, 'id', '?')} — single sweep"

        if kind == "supplier":
            result = _run_supplier_sweep(db, batch_notes=admin_ref)
            if result.get("status") == "error":
                raise HTTPException(status_code=500, detail=result.get("error", "Supplier sweep failed"))
            # Update in-memory status for just supplier
            _update_bg_status_after_manual_trigger(result, {"status": "no_eligible_settlements", "processed": 0})
        else:
            result = _run_logistics_sweep(db, batch_notes=admin_ref)
            if result.get("status") == "error":
                raise HTTPException(status_code=500, detail=result.get("error", "Logistics sweep failed"))
            _update_bg_status_after_manual_trigger({"status": "no_eligible_settlements", "processed": 0}, result)

        return result
    _s20.post("/background-job/trigger/{kind}")(trigger_background_job_kind)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route trigger_background_job_kind: %s", _e)

try:
    def _update_bg_status_after_manual_trigger(
        supplier_result: dict,
        logistics_result: dict,
    ) -> None:
        """Update the in-memory background job status after a manual trigger."""
        from domains.finance.services.payouts.payout_batch_service import update_background_status
    
        supplier_status = supplier_result.get("status", "error")
        logistics_status = logistics_result.get("status", "error")
        has_error = supplier_status == "error" or logistics_status == "error"
        overall_error = supplier_result.get("error") or logistics_result.get("error") if has_error else None
    
        now = utcnow()
        update_background_status(
            last_run_at=now.isoformat(),
            last_run_status="error" if overall_error else "ok",
            last_error=overall_error,
            last_supplier_result=supplier_result,
            last_logistics_result=logistics_result,
            total_sweep_count=(_get_bg_status().get("total_sweep_count", 0) + 1),
            total_settlements_processed=(
                _get_bg_status().get("total_settlements_processed", 0)
                + supplier_result.get("processed", 0)
                + logistics_result.get("processed", 0)
            ),
            is_running=True,
        )
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route: %s", _e)

_s23 = APIRouter(prefix='/api/v1/admin')

try:
    def     list_pending_payouts_route_route(
        country_code: str,
        page: int = Query(1),
        page_size: int = Query(50),
        current_user: dict = Depends(require_admin),
        db: Session = Depends(get_db)
    ):
        return list_pending_payouts_route(country_code=country_code, page=page, page_size=page_size, current_user=current_user, db=db)
    _s23.get("/payouts/{country_code}/pending", status_code=200, tags=['admin-payouts'])(list_pending_payouts_route_route)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route list_pending_payouts_route_route: %s", _e)

try:
    def     verify_payout_route_route(
        country_code: str,
        payout_id: int,
        current_user: dict = Depends(require_admin),
        db: Session = Depends(get_db),
        status: str = Body('completed'),
        reference: Optional[str] = Body(None),
        notes: Optional[str] = Body(None)
    ):
        return verify_payout_route(country_code=country_code, payout_id=payout_id, current_user=current_user, db=db, status=status, reference=reference, notes=notes)
    _s23.post("/payouts/{country_code}/{payout_id}/verify", status_code=201, tags=['admin-payouts'])(verify_payout_route_route)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route verify_payout_route_route: %s", _e)

_s33 = APIRouter(prefix='/api/v1')

try:
    def _serialize_payout(p: Payout) -> dict[str, Any]:
        return {
            "id": cast(int, p.id),
            "supplier_id": cast(int | None, p.supplier_id),
            "order_id": cast(int | None, p.order_id),
            "amount": float(cast(Decimal, p.amount or 0)),
            "currency": cast(str | None, p.currency) or "OMR",
            "method": cast(str | None, p.method) or "",
            "status": cast(str | None, p.status) or "",
            "reference": cast(str | None, p.reference),
            "notes": cast(str | None, p.notes),
            "country_code": cast(str | None, p.country_code) or "",
            "created_at": cast(Any, p.created_at).isoformat() if getattr(p, "created_at", None) else None,
            "processed_at": cast(Any, p.processed_at).isoformat() if getattr(p, "processed_at", None) else None,
        }
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route: %s", _e)

try:
    def _serialize_batch_item(item: PayoutBatchItem) -> dict[str, Any]:
        return {
            "id": cast(int, item.id),
            "entity_type": cast(str, item.entity_type),
            "entity_id": cast(int, item.entity_id),
            "amount": float(cast(Decimal, item.amount or 0)),
            "currency": cast(str | None, item.currency) or "OMR",
            "reference": cast(str | None, item.reference),
            "status": cast(str | None, item.status) or "",
        }
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route: %s", _e)

try:
    def _serialize_batch(batch: PayoutBatch) -> dict[str, Any]:
        return {
            "id": cast(int, batch.id),
            "batch_number": cast(str, batch.batch_number),
            "country_code": cast(str, batch.country_code),
            "total_amount": float(cast(Decimal, batch.total_amount or 0)),
            "item_count": cast(int, batch.item_count or 0),
            "status": cast(str, batch.status),
            "notes": cast(str | None, batch.notes),
            "created_at": cast(Any, batch.created_at).isoformat() if getattr(batch, "created_at", None) else None,
            "items": [_serialize_batch_item(item) for item in (batch.items or [])],
        }
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route: %s", _e)

try:
    def _resolve_supplier_names(entity_ids: set[int], db: Session) -> dict[int, str]:
        """Return {entity_id: display_name} for supplier IDs."""
        if not entity_ids:
            return {}
        users = db.query(User).filter(User.id.in_(entity_ids)).all()
        return {cast(int, u.id): cast(str, u.username or u.email or f"Supplier #{u.id}") for u in users}
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route: %s", _e)

try:
    def _resolve_logistics_names(entity_ids: set[int], db: Session) -> dict[int, str]:
        """Return {entity_id: display_name} for logistics partner IDs."""
        if not entity_ids:
            return {}
        partners = db.query(LogisticsPartner).filter(LogisticsPartner.id.in_(entity_ids)).all()
        return {cast(int, p.id): cast(str, p.name or f"Partner #{p.id}") for p in partners}
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route: %s", _e)

try:
    def _enrich_batch_items(batch: PayoutBatch, db: Session) -> list[dict[str, Any]]:
        """Return batch items with resolved entity_name fields."""
        items = list(batch.items or [])
        supplier_ids = {cast(int, it.entity_id) for it in items if cast(str, it.entity_type) == "supplier"}
        logistics_ids = {cast(int, it.entity_id) for it in items if cast(str, it.entity_type) == "logistics"}
        supplier_names = _resolve_supplier_names(supplier_ids, db)
        logistics_names = _resolve_logistics_names(logistics_ids, db)
    
        enriched = []
        for item in items:
            e = _serialize_batch_item(item)
            eid = cast(int, item.entity_id)
            etype = cast(str, item.entity_type)
            if etype == "supplier":
                e["entity_name"] = supplier_names.get(eid, f"Supplier #{eid}")
            elif etype == "logistics":
                e["entity_name"] = logistics_names.get(eid, f"Partner #{eid}")
            else:
                e["entity_name"] = f"#{eid}"
            enriched.append(e)
        return enriched
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route: %s", _e)

try:
    def _load_unbatched_payouts(
        db: Session, page: int, page_size: int
    ) -> tuple[list[dict[str, Any]], int]:
        """Return paginated individual Payout records with supplier names.
    
        Shows ALL pending/draft payouts — the frontend distinguishes batched
        vs unbatched by cross-referencing batch items.
        """
        query = db.query(Payout).filter(Payout.status.in_(["pending", "draft"]))
        total = query.count()
        payouts = query.order_by(Payout.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    
        supplier_ids = {cast(int, p.supplier_id) for p in payouts if p.supplier_id}
        supplier_names = _resolve_supplier_names(supplier_ids, db) if supplier_ids else {}
    
        result = []
        for payout in payouts:
            s = _serialize_payout(payout)
            sid = cast(int | None, payout.supplier_id)
            s["supplier_name"] = supplier_names.get(cast(int, sid), f"Supplier #{sid}") if sid else None
            result.append(s)
        return result, total
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route: %s", _e)

try:
    def _load_pending_batches_with_items(db: Session, page: int, page_size: int) -> tuple[list[dict[str, Any]], int]:
        """Return paginated batches in draft/pending status with enriched items."""
        query = db.query(PayoutBatch).options(joinedload(PayoutBatch.items)).filter(
            PayoutBatch.status.in_(["draft", "pending"])
        )
        total = query.count()
        batches = query.order_by(PayoutBatch.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    
        result = []
        for batch in batches:
            enriched_items = _enrich_batch_items(batch, db)
            s = _serialize_batch(batch)
            s["items"] = enriched_items
            result.append(s)
        return result, total
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route: %s", _e)

try:
    def _update_payout_status_by_ids(payout_ids: list[int], status: str, db: Session) -> None:
        """Update status for specific Payout records by their primary key."""
        if payout_ids:
            now = utcnow()
            db.query(Payout).filter(
                Payout.id.in_(payout_ids),
                Payout.status.in_(["pending", "draft", "approved"]),
            ).update({"status": status, "processed_at": now}, synchronize_session=False)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route: %s", _e)

try:
    def     get_pending_payouts(
        page: int = Query(1, ge=1),
        page_size: int = Query(20, ge=1, le=100),
        current_admin: User = Depends(require_admin),
        db: Session = Depends(get_db),
    ) -> dict[str, Any]:
        """Return all pending payout batches and unbatched payouts for admin review.

        Pagination is applied independently to batches and unbatched payouts.
        """
        batches, batch_total = _load_pending_batches_with_items(db, page, page_size)
        unbatched, payout_total = _load_unbatched_payouts(db, page, page_size)

        # ── Also load standalone logistics partner payouts ──
        logistics_payout_q = db.query(LogisticsPartnerPayout).filter(
            LogisticsPartnerPayout.status.in_(["pending", "draft"]),
        )
        logistics_payout_total = logistics_payout_q.count()
        logistics_payouts = logistics_payout_q.order_by(LogisticsPartnerPayout.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

        logistics_ids = {cast(int, lp.partner_id) for lp in logistics_payouts if lp.partner_id}
        logistics_names = _resolve_logistics_names(logistics_ids, db) if logistics_ids else {}

        unbatched_logistics = []
        for lp in logistics_payouts:
            pid = cast(int | None, lp.partner_id)
            unbatched_logistics.append({
                "id": cast(int, lp.id),
                "partner_id": pid,
                "partner_name": logistics_names.get(cast(int, pid), f"Partner #{pid}") if pid else None,
                "amount": float(cast(Decimal, lp.amount or 0)),
                "currency": cast(str | None, lp.currency) or "OMR",
                "status": cast(str | None, lp.status) or "",
                "reference": cast(str | None, lp.reference),
                "notes": cast(str | None, lp.notes),
                "created_at": cast(Any, lp.created_at).isoformat() if getattr(lp, "created_at", None) else None,
            })

        total_amount = sum(b["total_amount"] for b in batches)
        total_items = sum(b["item_count"] for b in batches)

        return {
            "pending_batches": batches,
            "unbatched_payouts": unbatched,
            "unbatched_logistics_payouts": unbatched_logistics,
            "summary": {
                "total_batches": batch_total,
                "total_amount": round(total_amount, 2),
                "total_items": total_items,
                "pending_payouts_count": payout_total,
                "pending_logistics_payouts_count": logistics_payout_total,
            },
            "pagination": {"page": page, "page_size": page_size},
        }
    _s33.get("/pending")(get_pending_payouts)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route get_pending_payouts: %s", _e)

try:
    def     approve_payout(
        payout_id: int,
        payload: ActionRequest | None = None,
        current_admin: User = Depends(require_admin),
        db: Session = Depends(get_db),
    ) -> dict[str, Any]:
        """Approve an individual pending payout record."""
        payout = db.query(Payout).filter(Payout.id == payout_id).first()
        if not payout:
            raise HTTPException(status_code=404, detail="Payout not found")
        if payout.status not in ("pending", "draft"):
            raise HTTPException(
                status_code=409,
                detail=f"Cannot approve payout in '{payout.status}' status.",
            )
        payout.status = "approved"
        if payload and payload.notes:
            payout.notes = (payout.notes or "") + f"\nApproved: {payload.notes}"

        db.commit()
        audit_log(
            db=db, action=AuditAction.PAYOUT_PROCESSED,
            user_id=current_admin.id, username=current_admin.username,
            user_role="admin", resource_type="payout",
            resource_id=payout_id,
            details={"action": "approve", "amount": float(cast(Decimal, payout.amount or 0))},
        )
        return {"message": "Payout approved", "payout_id": payout_id, "status": "approved"}
    _s33.post("/payouts/{payout_id}/approve")(approve_payout)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route approve_payout: %s", _e)

try:
    def     reject_payout(
        payout_id: int,
        payload: ActionRequest | None = None,
        current_admin: User = Depends(require_admin),
        db: Session = Depends(get_db),
    ) -> dict[str, Any]:
        """Reject an individual pending payout record."""
        payout = db.query(Payout).filter(Payout.id == payout_id).first()
        if not payout:
            raise HTTPException(status_code=404, detail="Payout not found")
        if payout.status not in ("pending", "draft", "approved"):
            raise HTTPException(
                status_code=409,
                detail=f"Cannot reject payout in '{payout.status}' status.",
            )
        payout.status = "rejected"
        if payload and payload.notes:
            payout.notes = (payout.notes or "") + f"\nRejected: {payload.notes}"

        db.commit()
        audit_log(
            db=db, action=AuditAction.PAYOUT_PROCESSED,
            user_id=current_admin.id, username=current_admin.username,
            user_role="admin", resource_type="payout",
            resource_id=payout_id,
            details={"action": "reject", "amount": float(cast(Decimal, payout.amount or 0))},
        )
        return {"message": "Payout rejected", "payout_id": payout_id, "status": "rejected"}
    _s33.post("/payouts/{payout_id}/reject")(reject_payout)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route reject_payout: %s", _e)

try:
    def     approve_batch(
        batch_id: int,
        payload: ActionRequest | None = None,
        current_admin: User = Depends(require_admin),
        db: Session = Depends(get_db),
    ) -> dict[str, Any]:
        """Approve a payout batch — moves it from draft → approved."""
        batch = (
            db.query(PayoutBatch)
            .options(joinedload(PayoutBatch.items))
            .filter(PayoutBatch.id == batch_id)
            .first()
        )
        if not batch:
            raise HTTPException(status_code=404, detail="Payout batch not found")
        if batch.status not in ("draft", "pending"):
            raise HTTPException(
                status_code=409,
                detail=f"Cannot approve batch in '{batch.status}' status. Only draft/pending batches can be approved.",
            )
        now = utcnow()
        batch.status = "approved"
        batch.approved_by = cast(int, current_admin.id)
        batch.notes = (batch.notes or "") + (
            f"\nApproved by admin #{current_admin.id} at {now.isoformat()}."
            + (f" Notes: {payload.notes}" if payload and payload.notes else "")
        )
        for item in batch.items or []:
            item.status = "approved"

        db.commit()
        audit_log(
            db=db, action=AuditAction.PAYOUT_PROCESSED,
            user_id=current_admin.id, username=current_admin.username,
            user_role="admin", resource_type="payout_batch",
            resource_id=batch_id,
            details={"action": "approve", "batch_number": batch.batch_number},
        )
        return {"message": "Batch approved", "batch_id": batch_id, "status": "approved"}
    _s33.post("/batches/{batch_id}/approve")(approve_batch)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route approve_batch: %s", _e)

try:
    def     reject_batch(
        batch_id: int,
        payload: ActionRequest | None = None,
        current_admin: User = Depends(require_admin),
        db: Session = Depends(get_db),
    ) -> dict[str, Any]:
        """Reject a payout batch — moves it from draft → rejected."""
        batch = (
            db.query(PayoutBatch)
            .options(joinedload(PayoutBatch.items))
            .filter(PayoutBatch.id == batch_id)
            .first()
        )
        if not batch:
            raise HTTPException(status_code=404, detail="Payout batch not found")
        if batch.status not in ("draft", "pending", "approved"):
            raise HTTPException(
                status_code=409,
                detail=f"Cannot reject batch in '{batch.status}' status.",
            )
        now = utcnow()
        old_status = batch.status
        batch.status = "rejected"
        batch.notes = (batch.notes or "") + (
            f"\nRejected by admin #{current_admin.id} at {now.isoformat()}."
            + (f" Reason: {payload.notes}" if payload and payload.notes else "")
        )
        for item in batch.items or []:
            item.status = "pending"

        db.commit()
        audit_log(
            db=db, action=AuditAction.PAYOUT_PROCESSED,
            user_id=current_admin.id, username=current_admin.username,
            user_role="admin", resource_type="payout_batch",
            resource_id=batch_id,
            details={"action": "reject", "batch_number": batch.batch_number, "previous_status": old_status},
        )
        return {"message": "Batch rejected", "batch_id": batch_id, "status": "rejected"}
    _s33.post("/batches/{batch_id}/reject")(reject_batch)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route reject_batch: %s", _e)

try:
    def     dispatch_batch(
        batch_id: int,
        payload: ActionRequest | None = None,
        current_admin: User = Depends(require_admin),
        db: Session = Depends(get_db),
    ) -> dict[str, Any]:
        """Dispatch (mark as paid) an approved payout batch.

        Updates the batch status to dispatched, marks all batch items as paid,
        and updates the underlying Payout / LogisticsPartnerPayout records to paid.
        """
        batch = (
            db.query(PayoutBatch)
            .options(joinedload(PayoutBatch.items))
            .filter(PayoutBatch.id == batch_id)
            .first()
        )
        if not batch:
            raise HTTPException(status_code=404, detail="Payout batch not found")
        if batch.status != "approved":
            raise HTTPException(
                status_code=409,
                detail=f"Cannot dispatch batch in '{batch.status}' status. Only approved batches can be dispatched.",
            )
        now = utcnow()
        batch.status = "dispatched"
        batch.dispatched_at = now
        batch.notes = (batch.notes or "") + (
            f"\nDispatched by admin #{current_admin.id} at {now.isoformat()}."
            + (f" Notes: {payload.notes}" if payload and payload.notes else "")
        )

        supplier_payout_ids: list[int] = []
        logistics_payout_ids: list[int] = []

        for item in batch.items or []:
            item.status = "paid"
            etype = cast(str, item.entity_type)
            eid = cast(int, item.entity_id)
            if etype == "supplier":
                supplier_payout_ids.append(eid)
            elif etype == "logistics":
                logistics_payout_ids.append(eid)

        # --- Bulk-update Payout records for suppliers in this batch ---
        # Batch items store entity_id = supplier_id (set by the auto-payout
        # scheduler).  We match by Payout.supplier_id, which is the correct
        # column.  This is safe because the status filter (pending/approved)
        # prevents touching already-paid payouts from prior batches.
        if supplier_payout_ids:
            updated = db.query(Payout).filter(
                Payout.supplier_id.in_(supplier_payout_ids),
                Payout.status.in_(["pending", "approved"]),
            ).update({"status": "paid", "processed_at": now}, synchronize_session=False)

        if logistics_payout_ids:
            db.query(LogisticsPartnerPayout).filter(
                LogisticsPartnerPayout.partner_id.in_(logistics_payout_ids),
                LogisticsPartnerPayout.status.in_(["pending", "approved"]),
            ).update({"status": "paid", "processed_at": now}, synchronize_session=False)

        db.commit()
        audit_log(
            db=db, action=AuditAction.PAYOUT_PROCESSED,
            user_id=current_admin.id, username=current_admin.username,
            user_role="admin", resource_type="payout_batch",
            resource_id=batch_id,
            details={"action": "dispatch", "batch_number": batch.batch_number},
        )
        return {"message": "Batch dispatched", "batch_id": batch_id, "status": "dispatched"}
    _s33.post("/batches/{batch_id}/dispatch")(dispatch_batch)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip route dispatch_batch: %s", _e)

router = APIRouter()try:    router.include_router(_s6)except Exception as _e:    import logging as _l; _l.getLogger(__name__).warning("skip subrouter _s6: %s", _e)try:    router.include_router(_s7)except Exception as _e:    import logging as _l; _l.getLogger(__name__).warning("skip subrouter _s7: %s", _e)try:    router.include_router(_s8)except Exception as _e:    import logging as _l; _l.getLogger(__name__).warning("skip subrouter _s8: %s", _e)try:    router.include_router(_s9)except Exception as _e:    import logging as _l; _l.getLogger(__name__).warning("skip subrouter _s9: %s", _e)try:    router.include_router(_s10)except Exception as _e:    import logging as _l; _l.getLogger(__name__).warning("skip subrouter _s10: %s", _e)try:    router.include_router(_s11)except Exception as _e:    import logging as _l; _l.getLogger(__name__).warning("skip subrouter _s11: %s", _e)try:    router.include_router(_s15)except Exception as _e:    import logging as _l; _l.getLogger(__name__).warning("skip subrouter _s15: %s", _e)try:    router.include_router(_s16)except Exception as _e:    import logging as _l; _l.getLogger(__name__).warning("skip subrouter _s16: %s", _e)try:    router.include_router(_s17)except Exception as _e:    import logging as _l; _l.getLogger(__name__).warning("skip subrouter _s17: %s", _e)try:    router.include_router(_s20)except Exception as _e:    import logging as _l; _l.getLogger(__name__).warning("skip subrouter _s20: %s", _e)try:    router.include_router(_s23)except Exception as _e:    import logging as _l; _l.getLogger(__name__).warning("skip subrouter _s23: %s", _e)try:    router.include_router(_s33)except Exception as _e:    import logging as _l; _l.getLogger(__name__).warning("skip subrouter _s33: %s", _e)