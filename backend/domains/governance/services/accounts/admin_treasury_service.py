"""Auto-migrated service logic from routers/admin_treasury.py."""
from __future__ import annotations

from __future__ import annotations

import domains.accounts.services as admin_treasury_svc

from domains.accounts.services.admin_treasury_service import _resolve_stage
from domains.accounts.services.admin_treasury_service import admin_approve_payout_batch
from domains.accounts.services.admin_treasury_service import admin_approve_pending
from domains.accounts.services.admin_treasury_service import admin_approve_settlement
from domains.accounts.services.admin_treasury_service import admin_cash_forecasts
from domains.accounts.services.admin_treasury_service import admin_cash_position
from domains.accounts.services.admin_treasury_service import admin_cod_remittances
from domains.accounts.services.admin_treasury_service import admin_detect_orphans
from domains.accounts.services.admin_treasury_service import admin_dispatch_payout_batch
from domains.accounts.services.admin_treasury_service import admin_gateway_exceptions
from domains.accounts.services.admin_treasury_service import admin_gateway_summary
from domains.accounts.services.admin_treasury_service import admin_generate_payout_batch
from domains.accounts.services.admin_treasury_service import admin_liabilities_exposure
from domains.accounts.services.admin_treasury_service import admin_logistics_payouts
from domains.accounts.services.admin_treasury_service import admin_manual_adjustment
from domains.accounts.services.admin_treasury_service import admin_payment_transactions
from domains.accounts.services.admin_treasury_service import admin_payout_batches
from domains.accounts.services.admin_treasury_service import admin_pending_entries
from domains.accounts.services.admin_treasury_service import admin_reconciliation_pipeline
from domains.accounts.services.admin_treasury_service import admin_record_cod_remittance
from domains.accounts.services.admin_treasury_service import admin_reject_pending
from domains.accounts.services.admin_treasury_service import admin_settle_supplier
from domains.accounts.services.admin_treasury_service import admin_snapshot_cash_position
from domains.accounts.services.admin_treasury_service import admin_supplier_earnings
from domains.accounts.services.admin_treasury_service import admin_supplier_payouts
from domains.accounts.services.admin_treasury_service import admin_treasury_ledger
from domains.accounts.services.admin_treasury_service import admin_treasury_metrics
from domains.accounts.services.admin_treasury_service import admin_treasury_root
from domains.accounts.services.admin_treasury_service import admin_trial_balance
from domains.accounts.services.admin_treasury_service import admin_vat_liability
from domains.accounts.services.admin_treasury_service import consolidated_cash_forecasts
from domains.accounts.services.admin_treasury_service import consolidated_cash_position
from domains.accounts.services.admin_treasury_service import consolidated_cod_remittances
from domains.accounts.services.admin_treasury_service import consolidated_gateway_summary
from domains.accounts.services.admin_treasury_service import consolidated_payout_batches
from domains.accounts.services.admin_treasury_service import consolidated_reconciliation_pipeline
from domains.accounts.services.admin_treasury_service import consolidated_treasury_ledger
from domains.accounts.services.admin_treasury_service import consolidated_treasury_metrics
from domains.accounts.services.admin_treasury_service import consolidated_trial_balance
from domains.accounts.services.admin_treasury_service import consolidated_vat_liability
from domains.accounts.services.admin_treasury_service import country_approve_pending
from domains.accounts.services.admin_treasury_service import country_cash_position
from domains.accounts.services.admin_treasury_service import country_cod_remittances
from domains.accounts.services.admin_treasury_service import country_detect_orphans
from domains.accounts.services.admin_treasury_service import country_gateway_exceptions
from domains.accounts.services.admin_treasury_service import country_gateway_summary
from domains.accounts.services.admin_treasury_service import country_liabilities_exposure
from domains.accounts.services.admin_treasury_service import country_logistics_payouts
from domains.accounts.services.admin_treasury_service import country_manual_adjustment
from domains.accounts.services.admin_treasury_service import country_payment_transactions
from domains.accounts.services.admin_treasury_service import country_payout_batches
from domains.accounts.services.admin_treasury_service import country_payroll
from domains.accounts.services.admin_treasury_service import country_pending_entries
from domains.accounts.services.admin_treasury_service import country_reject_pending
from domains.accounts.services.admin_treasury_service import country_supplier_earnings
from domains.accounts.services.admin_treasury_service import country_supplier_payouts
from domains.accounts.services.admin_treasury_service import country_treasury_ledger
from domains.accounts.services.admin_treasury_service import country_treasury_metrics
from domains.accounts.services.admin_treasury_service import country_trial_balance
from domains.accounts.services.admin_treasury_service import country_vat_liability
from domains.accounts.services.admin_treasury_service import get_engine
from domains.accounts.services.admin_treasury_service import logger
from domains.accounts.services.admin_treasury_service import payroll_equity
from domains.accounts.services.admin_treasury_service import require_treasury_access

import logging

from datetime import date, datetime

from decimal import Decimal

from typing import Optional

from fastapi import Depends, HTTPException, Path, Query

from fastapi import Body

from sqlalchemy import func, select

from sqlalchemy.orm import Session, joinedload

from domains.governance.services.auth_controller_service import get_current_user

from infrastructure.database.database import get_db

from domains.finance.models.finance import Account
from domains.finance.models.finance import AccountBalance
from domains.finance.models.finance import CashFlowForecast
from domains.finance.models.finance import CashPositionSnapshot
from domains.finance.models.finance import GatewaySettlementSchedule
from domains.finance.models.finance import Invoice
from domains.finance.models.finance import JournalEntry
from domains.finance.models.finance import JournalEntryLine
from domains.finance.models.finance import PayoutBatch
from domains.finance.models.finance import PayoutBatchItem
from domains.finance.models.finance import SupplierSettlement
from domains.finance.models.finance import TreasuryAccount
from domains.finance.models.finance import VATRemittance

from domains.governance.models.admin import LogisticsCODRemittanceReceipt

from domains.hr.models.employee_models import Employee

from domains.logistics.models.logistics import LogisticsPartner

from domains.orders.models import Order as OrderModel

from domains.finance.models.payments import LogisticsPartnerPayout, Payment, Payout

from domains.finance.services.treasury_engine import TreasuryEngine

from infrastructure.utils.constants import (
    CASH_ACCOUNT,
    DEFAULT_PAGE_SIZE,
    INPUT_VAT_ACCOUNT,
    MAX_PAGE_SIZE,
    OUTPUT_VAT_ACCOUNT,
    PAYABLES_ACCOUNT,
    TREASURY_ROLES,
)

from domains.country.utils.country_rls import get_country_or_404

from infrastructure.utils.rls_interceptor import clear_rls_context, set_rls_context

def admin_treasury_root(db: Session, current_user: dict):
    return admin_treasury_svc.admin_treasury_root(db=db, current_user=current_user)

def admin_treasury_metrics(db: Session, current_user: dict):
    return admin_treasury_svc.admin_treasury_metrics(db=db, current_user=current_user)

def admin_treasury_ledger(start_date: date, end_date: date, limit: int, db: Session, current_user: dict):
    return admin_treasury_svc.admin_treasury_ledger(start_date=start_date, end_date=end_date, limit=limit, db=db, current_user=current_user)

def admin_trial_balance(as_of_date: Optional[str], country_code: Optional[str], db: Session, current_user: dict):
    return admin_treasury_svc.admin_trial_balance(as_of_date=as_of_date, country_code=country_code, db=db, current_user=current_user)

def admin_cash_position(db: Session, current_user: dict):
    return admin_treasury_svc.admin_cash_position(db=db, current_user=current_user)

def admin_payout_batches(db: Session, current_user: dict):
    return admin_treasury_svc.admin_payout_batches(db=db, current_user=current_user)

def admin_generate_payout_batch(country_code: str, cutoff_date: date, db: Session, current_user: dict):
    return admin_treasury_svc.admin_generate_payout_batch(country_code=country_code, cutoff_date=cutoff_date, db=db, current_user=current_user)

def admin_approve_payout_batch(batch_id: int, db: Session, current_user: dict):
    return admin_treasury_svc.admin_approve_payout_batch(batch_id=batch_id, db=db, current_user=current_user)

def admin_dispatch_payout_batch(batch_id: int, db: Session, current_user: dict):
    return admin_treasury_svc.admin_dispatch_payout_batch(batch_id=batch_id, db=db, current_user=current_user)

def admin_vat_liability(country_code: Optional[str], period: str, db: Session, current_user: dict):
    return admin_treasury_svc.admin_vat_liability(country_code=country_code, period=period, db=db, current_user=current_user)

def admin_cod_remittances(status: Optional[str], db: Session, current_user: dict):
    return admin_treasury_svc.admin_cod_remittances(status=status, db=db, current_user=current_user)

def admin_gateway_summary(db: Session, current_user: dict):
    return admin_treasury_svc.admin_gateway_summary(db=db, current_user=current_user)

def admin_snapshot_cash_position(db: Session, current_user: dict):
    return admin_treasury_svc.admin_snapshot_cash_position(db=db, current_user=current_user)

def admin_cash_forecasts(db: Session, current_user: dict):
    return admin_treasury_svc.admin_cash_forecasts(db=db, current_user=current_user)

def consolidated_treasury_metrics(db: Session, current_user: dict):
    return admin_treasury_svc.consolidated_treasury_metrics(db=db, current_user=current_user)

def consolidated_treasury_ledger(limit: int, db: Session, current_user: dict):
    return admin_treasury_svc.consolidated_treasury_ledger(limit=limit, db=db, current_user=current_user)

def consolidated_trial_balance(db: Session, current_user: dict, page: int, page_size: int):
    return admin_treasury_svc.consolidated_trial_balance(db=db, current_user=current_user, page=page, page_size=page_size)

def consolidated_cash_position(db: Session, current_user: dict, page: int, page_size: int):
    return admin_treasury_svc.consolidated_cash_position(db=db, current_user=current_user, page=page, page_size=page_size)

def consolidated_payout_batches(limit: int, db: Session, current_user: dict):
    return admin_treasury_svc.consolidated_payout_batches(limit=limit, db=db, current_user=current_user)

def consolidated_vat_liability(db: Session, current_user: dict):
    return admin_treasury_svc.consolidated_vat_liability(db=db, current_user=current_user)

def consolidated_cod_remittances(limit: int, db: Session, current_user: dict):
    return admin_treasury_svc.consolidated_cod_remittances(limit=limit, db=db, current_user=current_user)

def consolidated_gateway_summary(db: Session, current_user: dict):
    return admin_treasury_svc.consolidated_gateway_summary(db=db, current_user=current_user)

def consolidated_cash_forecasts(db: Session, current_user: dict):
    return admin_treasury_svc.consolidated_cash_forecasts(db=db, current_user=current_user)

def consolidated_reconciliation_pipeline(limit: int, db: Session, current_user: dict):
    return admin_treasury_svc.consolidated_reconciliation_pipeline(limit=limit, db=db, current_user=current_user)

def country_treasury_metrics(country_code: str, db: Session, current_user: dict):
    return admin_treasury_svc.country_treasury_metrics(country_code=country_code, db=db, current_user=current_user)

def country_treasury_ledger(country_code: str, start_date: date, end_date: date, limit: int, db: Session, current_user: dict):
    return admin_treasury_svc.country_treasury_ledger(country_code=country_code, start_date=start_date, end_date=end_date, limit=limit, db=db, current_user=current_user)

def country_trial_balance(country_code: str, as_of_date: Optional[str], db: Session, current_user: dict):
    return admin_treasury_svc.country_trial_balance(country_code=country_code, as_of_date=as_of_date, db=db, current_user=current_user)

def country_cash_position(country_code: str, db: Session, current_user: dict):
    return admin_treasury_svc.country_cash_position(country_code=country_code, db=db, current_user=current_user)

def country_payout_batches(country_code: str, db: Session, current_user: dict):
    return admin_treasury_svc.country_payout_batches(country_code=country_code, db=db, current_user=current_user)

def country_vat_liability(country_code: str, period: str, db: Session, current_user: dict):
    return admin_treasury_svc.country_vat_liability(country_code=country_code, period=period, db=db, current_user=current_user)

def country_cod_remittances(country_code: str, status: Optional[str], db: Session, current_user: dict):
    return admin_treasury_svc.country_cod_remittances(country_code=country_code, status=status, db=db, current_user=current_user)

def country_gateway_summary(country_code: str, db: Session, current_user: dict):
    return admin_treasury_svc.country_gateway_summary(country_code=country_code, db=db, current_user=current_user)

def admin_reconciliation_pipeline(country_code: str, status: Optional[str], limit: int, db: Session, current_user: dict):
    return admin_treasury_svc.admin_reconciliation_pipeline(country_code=country_code, status=status, limit=limit, db=db, current_user=current_user)

def admin_record_cod_remittance(country_code: str, order_id: int, partner_id: int, amount: float, bank_reference: str, db: Session, current_user: dict):
    return admin_treasury_svc.admin_record_cod_remittance(country_code=country_code, order_id=order_id, partner_id=partner_id, amount=amount, bank_reference=bank_reference, db=db, current_user=current_user)

def admin_settle_supplier(country_code: str, order_id: int, supplier_id: int, net_amount: float, gross_amount: Optional[float], commission_amount: Optional[float], currency: Optional[str], payout_id: Optional[int], db: Session, current_user: dict):
    return admin_treasury_svc.admin_settle_supplier(country_code=country_code, order_id=order_id, supplier_id=supplier_id, net_amount=net_amount, gross_amount=gross_amount, commission_amount=commission_amount, currency=currency, payout_id=payout_id, db=db, current_user=current_user)

def admin_approve_settlement(country_code: str, settlement_id: int, db: Session, current_user: dict):
    return admin_treasury_svc.admin_approve_settlement(country_code=country_code, settlement_id=settlement_id, db=db, current_user=current_user)

def admin_gateway_exceptions(db: Session, current_user: dict):
    return admin_treasury_svc.admin_gateway_exceptions(db=db, current_user=current_user)

def country_gateway_exceptions(country_code: str, db: Session, current_user: dict):
    return admin_treasury_svc.country_gateway_exceptions(country_code=country_code, db=db, current_user=current_user)

def admin_payment_transactions(start_date: date, end_date: date, gateway: Optional[str], status: Optional[str], db: Session, current_user: dict):
    return admin_treasury_svc.admin_payment_transactions(start_date=start_date, end_date=end_date, gateway=gateway, status=status, db=db, current_user=current_user)

def country_payment_transactions(country_code: str, start_date: date, end_date: date, gateway: Optional[str], status: Optional[str], db: Session, current_user: dict):
    return admin_treasury_svc.country_payment_transactions(country_code=country_code, start_date=start_date, end_date=end_date, gateway=gateway, status=status, db=db, current_user=current_user)

def admin_supplier_payouts(status: Optional[str], db: Session, current_user: dict):
    return admin_treasury_svc.admin_supplier_payouts(status=status, db=db, current_user=current_user)

def country_supplier_payouts(country_code: str, status: Optional[str], db: Session, current_user: dict):
    return admin_treasury_svc.country_supplier_payouts(country_code=country_code, status=status, db=db, current_user=current_user)

def admin_logistics_payouts(status: Optional[str], db: Session, current_user: dict):
    return admin_treasury_svc.admin_logistics_payouts(status=status, db=db, current_user=current_user)

def country_logistics_payouts(country_code: str, status: Optional[str], db: Session, current_user: dict):
    return admin_treasury_svc.country_logistics_payouts(country_code=country_code, status=status, db=db, current_user=current_user)

def admin_supplier_earnings(db: Session, current_user: dict):
    return admin_treasury_svc.admin_supplier_earnings(db=db, current_user=current_user)

def country_supplier_earnings(country_code: str, db: Session, current_user: dict):
    return admin_treasury_svc.country_supplier_earnings(country_code=country_code, db=db, current_user=current_user)

def admin_liabilities_exposure(db: Session, current_user: dict):
    return admin_treasury_svc.admin_liabilities_exposure(db=db, current_user=current_user)

def country_liabilities_exposure(country_code: str, db: Session, current_user: dict):
    return admin_treasury_svc.country_liabilities_exposure(country_code=country_code, db=db, current_user=current_user)

def admin_manual_adjustment(debit_account: str, credit_account: str, amount: float, reason: str, created_by: int, db: Session, current_user: dict):
    return admin_treasury_svc.admin_manual_adjustment(debit_account=debit_account, credit_account=credit_account, amount=amount, reason=reason, created_by=created_by, db=db, current_user=current_user)

def country_manual_adjustment(country_code: str, debit_account: str, credit_account: str, amount: float, reason: str, created_by: int, db: Session, current_user: dict):
    return admin_treasury_svc.country_manual_adjustment(country_code=country_code, debit_account=debit_account, credit_account=credit_account, amount=amount, reason=reason, created_by=created_by, db=db, current_user=current_user)

def admin_pending_entries(db: Session, current_user: dict):
    return admin_treasury_svc.admin_pending_entries(db=db, current_user=current_user)

def country_pending_entries(country_code: str, db: Session, current_user: dict):
    return admin_treasury_svc.country_pending_entries(country_code=country_code, db=db, current_user=current_user)

def admin_approve_pending(pending_id: int, approver_id: int, db: Session, current_user: dict):
    return admin_treasury_svc.admin_approve_pending(pending_id=pending_id, approver_id=approver_id, db=db, current_user=current_user)

def country_approve_pending(country_code: str, pending_id: int, approver_id: int, db: Session, current_user: dict):
    return admin_treasury_svc.country_approve_pending(country_code=country_code, pending_id=pending_id, approver_id=approver_id, db=db, current_user=current_user)

def admin_reject_pending(pending_id: int, rejected_by: int, reason: str, db: Session, current_user: dict):
    return admin_treasury_svc.admin_reject_pending(pending_id=pending_id, rejected_by=rejected_by, reason=reason, db=db, current_user=current_user)

def country_reject_pending(country_code: str, pending_id: int, rejected_by: int, reason: str, db: Session, current_user: dict):
    return admin_treasury_svc.country_reject_pending(country_code=country_code, pending_id=pending_id, rejected_by=rejected_by, reason=reason, db=db, current_user=current_user)

def admin_detect_orphans(db: Session, current_user: dict):
    return admin_treasury_svc.admin_detect_orphans(db=db, current_user=current_user)

def country_detect_orphans(country_code: str, db: Session, current_user: dict):
    return admin_treasury_svc.country_detect_orphans(country_code=country_code, db=db, current_user=current_user)

def payroll_equity(db: Session):
    return admin_treasury_svc.payroll_equity(db=db)

def country_payroll(country_code: str, db: Session):
    return admin_treasury_svc.country_payroll(country_code=country_code, db=db)


