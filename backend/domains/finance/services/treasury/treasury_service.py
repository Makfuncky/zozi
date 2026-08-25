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




# === Merged from admin_treasury_identity_service.py ===

"""Admin cash management router."""
from fastapi import Depends, HTTPException, Query, Path
from sqlalchemy.orm import Session
from infrastructure.database.database import get_db
from domains.governance.models.user import User
from domains.finance.models.finance import CashAccount
from domains.finance.models.finance import CashTransaction
from infrastructure.database.schemas import CashAccountCreate, CashAccountOut, CashTransactionCreate, CashTransactionOut
from infrastructure.utils.dependencies import require_admin
from domains.country.utils.country_rls import get_country_or_404
from infrastructure.utils.rls_interceptor import set_rls_context, clear_rls_context
from decimal import Decimal

def list_accounts(country_code: str=Path(..., description='ISO country code'), _: User=Depends(require_admin), db: Session=Depends(get_db)):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return db.query(CashAccount).filter(CashAccount.is_active == True, CashAccount.country_code == country_code.upper()).all()
    finally:
        clear_rls_context()

def create_account(country_code: str=Path(..., description='ISO country code'), payload: CashAccountCreate=None, _: User=Depends(require_admin), db: Session=Depends(get_db)):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        a = CashAccount(**payload.model_dump(), country_code=country_code.upper())
        db.add(a)
        db.commit()
        db.refresh(a)
        return a
    finally:
        clear_rls_context()

def create_transaction(country_code: str=Path(..., description='ISO country code'), payload: CashTransactionCreate=None, current_user: User=Depends(require_admin), db: Session=Depends(get_db)):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        account = db.query(CashAccount).filter(CashAccount.id == payload.account_id, CashAccount.country_code == country_code.upper()).first()
        if not account:
            raise HTTPException(404, 'Account not found')
        if payload.transaction_type == 'debit':
            account.balance -= payload.amount
        else:
            account.balance += payload.amount
        tx = CashTransaction(**payload.model_dump(), balance_after=account.balance, performed_by=current_user.id, country_code=country_code.upper())
        db.add(tx)
        db.commit()
        db.refresh(tx)
        return tx
    finally:
        clear_rls_context()


# === Merged from flat_admin_treasury_reporting_service.py ===

"""Admin Treasury Router — bridges frontend /admin/treasury/* calls to TreasuryEngine."""
from __future__ import annotations
import json
import logging
from decimal import Decimal
from datetime import date, datetime, timezone
from typing import Optional
from fastapi import Depends, HTTPException, Query, Body as FastAPIBody, Path
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select, func
from infrastructure.database.database import get_db
from domains.governance.models.user import User
from domains.finance.models.finance import JournalEntry
from domains.finance.models.finance import JournalEntryLine
from domains.finance.models.finance import Account
from domains.finance.models.finance import AccountBalance
from domains.finance.models.finance import PayoutBatch
from domains.finance.models.finance import PayoutBatchItem
from domains.finance.models.finance import TreasuryAccount
from domains.finance.models.finance import VATRemittance
from domains.finance.models.finance import GatewaySettlementSchedule
from domains.finance.models.finance import CashPositionSnapshot
from domains.finance.models.finance import CashFlowForecast
from domains.finance.models.finance import BankTransaction
from domains.finance.models.finance import Invoice
from domains.finance.models.finance import SupplierSettlement
from domains.finance.models.finance import TransactionLedger
from domains.governance.models.admin import LogisticsCODRemittanceReceipt
from domains.finance.models.payments import Payout
from domains.finance.models.payments import Payment
from domains.finance.models.payments import LogisticsPartnerPayout
from domains.logistics.models.logistics import LogisticsPartner
from domains.orders.models.orders import Order as OrderModel
from domains.hr.models.employee_models import Employee
from domains.finance.services.treasury.treasury_engine import TreasuryEngine
from rbac import get_current_user
from domains.country.utils.country_rls import get_country_or_404
from infrastructure.utils.rls_interceptor import set_rls_context, clear_rls_context
from infrastructure.utils.constants import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE, TREASURY_ROLES, PAYOUT_STATUSES, SETTLEMENT_STATUSES, BATCH_STATUSES, COD_REMITTANCE_STATUSES, GATEWAY_SETTLEMENT_STATUSES, CASH_ACCOUNT, PAYABLES_ACCOUNT, OUTPUT_VAT_ACCOUNT, INPUT_VAT_ACCOUNT
logger = logging.getLogger(__name__)

def require_treasury_access(current_user: dict=Depends(get_current_user)) -> dict:
    if current_user.get('role', '').lower() not in TREASURY_ROLES:
        raise HTTPException(status_code=403, detail='Treasury access required')
    return current_user

def _resolve_stage(order, payment, cod_receipt, settlement, payout) -> str:
    if payout and payout.status == 'paid':
        return 'supplier_paid'
    if settlement and settlement.status in ('paid', 'settled'):
        return 'supplier_settled'
    if payout and payout.status == 'processing':
        return 'payout_processing'
    if cod_receipt and cod_receipt.status == 'remitted':
        return 'cod_remitted'
    if cod_receipt and cod_receipt.status == 'pending':
        return 'cod_pending'
    if payment and payment.status == 'completed':
        return 'payment_received'
    if order.status in ('shipped', 'delivered', 'dispatched'):
        return 'order_dispatched'
    return 'pending'

def admin_treasury_root(db: Session=Depends(get_db), current_user: dict=Depends(require_treasury_access)):
    """Treasury root — summary stats (bare /admin/treasury)."""
    total_entries = db.query(JournalEntry).count() or 0
    total_accounts = db.query(Account).count() or 0
    total_cash = db.execute(select(func.coalesce(func.sum(AccountBalance.balance), 0))).scalar() or Decimal('0')
    return {'total_entries': total_entries, 'total_accounts': total_accounts, 'total_cash': float(total_cash), 'metrics_available_at': '/admin/treasury/metrics', 'ledger_available_at': '/admin/treasury/ledger'}

def admin_treasury_metrics(db: Session=Depends(get_db), current_user: dict=Depends(require_treasury_access)):
    total_debits = db.execute(select(func.coalesce(func.sum(JournalEntryLine.amount), 0)).where(JournalEntryLine.side == 'debit')).scalar() or Decimal('0')
    total_credits = db.execute(select(func.coalesce(func.sum(JournalEntryLine.amount), 0)).where(JournalEntryLine.side == 'credit')).scalar() or Decimal('0')
    total_entries = db.query(JournalEntry).count()
    return {'total_credits': float(total_credits), 'total_debits': float(total_debits), 'net_balance': float(total_credits - total_debits), 'total_entries': total_entries}

def admin_treasury_ledger(start_date: date=Query(...), end_date: date=Query(...), limit: int=Query(DEFAULT_PAGE_SIZE), db: Session=Depends(get_db), current_user: dict=Depends(require_treasury_access)):
    entries = db.execute(select(JournalEntry).where(JournalEntry.entry_date >= start_date, JournalEntry.entry_date <= end_date).options(joinedload(JournalEntry.lines)).order_by(JournalEntry.entry_date.desc()).limit(min(limit, MAX_PAGE_SIZE))).unique().scalars().all()
    result = []
    for e in entries:
        total_debit = sum((float(line.amount) for line in e.lines if line.side == 'debit'))
        total_credit = sum((float(line.amount) for line in e.lines if line.side == 'credit'))
        result.append({'id': e.id, 'reference_number': getattr(e, 'reference_number', ''), 'entry_date': e.entry_date.isoformat() if hasattr(e, 'entry_date') and e.entry_date else '', 'description': e.description or '', 'source': e.source or '', 'total_debit': total_debit, 'total_credit': total_credit})
    return result

def admin_cash_position(db: Session=Depends(get_db), current_user: dict=Depends(require_treasury_access)):
    accounts = db.execute(select(TreasuryAccount).where(TreasuryAccount.is_active == True)).scalars().all()
    return [{'account_name': a.name, 'balance': float(a.balance), 'gl_code': a.gl_account_code or a.slug} for a in accounts]

def admin_payout_batches(db: Session=Depends(get_db), current_user: dict=Depends(require_treasury_access)):
    batches = db.execute(select(PayoutBatch).options(joinedload(PayoutBatch.creator), joinedload(PayoutBatch.approver)).order_by(PayoutBatch.created_at.desc()).limit(MAX_PAGE_SIZE)).unique().scalars().all()
    return [{'id': b.id, 'batch_number': b.batch_number, 'country_code': b.country_code, 'total_amount': float(b.total_amount), 'status': b.status, 'created_at': b.created_at.isoformat(), 'created_by': b.created_by, 'created_by_name': b.creator.full_name if b.creator else None, 'approved_by': b.approved_by, 'approved_by_name': b.approver.full_name if b.approver else None} for b in batches]

def admin_generate_payout_batch(country_code: str=FastAPIBody(...), cutoff_date: date=FastAPIBody(...), db: Session=Depends(get_db), current_user: dict=Depends(require_treasury_access)):
    from domains.finance.models.payments import Payout
    from domains.comms.models.suppliers import SupplierProfile
    pending_payouts = db.execute(select(Payout).where(Payout.country_code == country_code, Payout.status == 'pending', Payout.created_at <= cutoff_date)).scalars().all()
    if not pending_payouts:
        raise HTTPException(status_code=404, detail='No pending payouts found for the given criteria')
    total = sum((p.amount for p in pending_payouts))
    batch = PayoutBatch(batch_number=f"PB-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}", country_code=country_code, total_amount=total, item_count=len(pending_payouts), status='draft', created_by=current_user.get('id'))
    db.add(batch)
    db.flush()
    for payout in pending_payouts:
        item = PayoutBatchItem(batch_id=batch.id, entity_type='payout', entity_id=payout.id, amount=payout.amount, reference=getattr(payout, 'reference_number', None))
        db.add(item)
        payout.status = 'batched'
    db.commit()
    db.refresh(batch)
    return {'id': batch.id, 'batch_number': batch.batch_number, 'country_code': batch.country_code, 'total_amount': float(batch.total_amount), 'item_count': batch.item_count, 'status': batch.status}

def admin_approve_payout_batch(batch_id: int=Path(...), db: Session=Depends(get_db), current_user: dict=Depends(require_treasury_access)):
    batch = db.execute(select(PayoutBatch).where(PayoutBatch.id == batch_id).with_for_update()).scalar_one_or_none()
    if not batch:
        raise HTTPException(status_code=404, detail='Batch not found')
    if batch.status != 'draft':
        raise HTTPException(status_code=400, detail=f'Batch is already {batch.status}')
    if batch.created_by == current_user.get('id'):
        raise HTTPException(status_code=403, detail='Maker-Checker: cannot approve your own batch')
    batch.status = 'approved'
    batch.approved_by = current_user.get('id')
    db.commit()
    return {'status': 'approved', 'batch_id': batch.id, 'batch_number': batch.batch_number}

def admin_dispatch_payout_batch(batch_id: int=Path(...), db: Session=Depends(get_db), current_user: dict=Depends(require_treasury_access)):
    batch = db.execute(select(PayoutBatch).where(PayoutBatch.id == batch_id).with_for_update()).scalar_one_or_none()
    if not batch:
        raise HTTPException(status_code=404, detail='Batch not found')
    if batch.status != 'approved':
        raise HTTPException(status_code=400, detail=f'Batch must be approved first, current status: {batch.status}')
    engine = TreasuryEngine(db)
    entry = engine.post_journal_entry(lines=[{'account_code': PAYABLES_ACCOUNT, 'debit': float(batch.total_amount), 'description': f'Payout batch {batch.batch_number}'}, {'account_code': CASH_ACCOUNT, 'credit': float(batch.total_amount), 'description': f'Payout batch {batch.batch_number}'}], description=f'Dispatch payout batch {batch.batch_number}', source='payout_dispatch', country_code=batch.country_code, created_by=current_user.get('id'))
    batch.status = 'dispatched'
    batch.dispatched_at = datetime.utcnow()
    db.commit()
    return {'status': 'dispatched', 'batch_id': batch.id, 'batch_number': batch.batch_number, 'journal_entry_id': entry.id, 'reference_number': entry.reference_number}

def admin_vat_liability(country_code: Optional[str]=Query(None), period: str=Query('current'), db: Session=Depends(get_db), current_user: dict=Depends(require_treasury_access)):
    output_vat = db.execute(select(func.coalesce(func.sum(AccountBalance.balance), 0)).join(Account, AccountBalance.account_id == Account.id).where(Account.code == OUTPUT_VAT_ACCOUNT)).scalar() or Decimal('0')
    input_vat = db.execute(select(func.coalesce(func.sum(AccountBalance.balance), 0)).join(Account, AccountBalance.account_id == Account.id).where(Account.code == INPUT_VAT_ACCOUNT)).scalar() or Decimal('0')
    return {'output_vat': float(output_vat), 'input_vat': float(input_vat), 'net_vat_due': float(output_vat - input_vat), 'country_code': country_code, 'period': period}

def admin_cod_remittances(status: Optional[str]=Query(None), db: Session=Depends(get_db), current_user: dict=Depends(require_treasury_access)):
    from domains.logistics.models.logistics import LogisticsPartner
    query = select(LogisticsCODRemittanceReceipt, LogisticsPartner.name).outerjoin(LogisticsPartner, LogisticsCODRemittanceReceipt.partner_id == LogisticsPartner.id)
    if status:
        query = query.where(LogisticsCODRemittanceReceipt.status == status)
    query = query.order_by(LogisticsCODRemittanceReceipt.created_at.desc()).limit(MAX_PAGE_SIZE)
    rows = db.execute(query).all()
    return [{'id': r.id, 'logistics_partner_id': r.partner_id, 'logistics_partner_name': partner_name or 'Unknown', 'amount_remitted': float(r.amount or 0), 'amount_expected': float(r.amount or 0), 'status': r.status, 'remitted_at': r.created_at.isoformat() if r.created_at else None, 'bank_reference': None, 'proof_url': None} for (r, partner_name) in rows]

def admin_gateway_summary(db: Session=Depends(get_db), current_user: dict=Depends(require_treasury_access)):
    schedules = db.execute(select(GatewaySettlementSchedule).order_by(GatewaySettlementSchedule.settlement_date.desc()).limit(100)).scalars().all()
    from collections import defaultdict
    by_gateway = defaultdict(lambda : {'total_settled': 0, 'total_expected': 0, 'count': 0, 'last_date': None})
    for s in schedules:
        key = str(s.gateway_id)
        by_gateway[key]['total_expected'] += float(s.amount or 0)
        by_gateway[key]['count'] += 1
        if s.status == 'settled':
            by_gateway[key]['total_settled'] += float(s.amount or 0)
        if not by_gateway[key]['last_date'] or (s.settlement_date and s.settlement_date > by_gateway[key]['last_date']):
            by_gateway[key]['last_date'] = s.settlement_date
    return [{'gateway_code': gid, 'total_settled': data['total_settled'], 'total_expected': data['total_expected'], 'discrepancy': data['total_expected'] - data['total_settled'], 'count': data['count'], 'last_settlement_date': data['last_date'].isoformat() if data['last_date'] else None} for (gid, data) in by_gateway.items()]

def admin_snapshot_cash_position(db: Session=Depends(get_db), current_user: dict=Depends(require_treasury_access)):
    accounts = db.execute(select(TreasuryAccount).where(TreasuryAccount.is_active == True)).scalars().all()
    now = datetime.utcnow()
    for a in accounts:
        snap = CashPositionSnapshot(snapshot_time=now, account_id=a.id, balance=a.balance, currency=a.currency or 'USD')
        db.add(snap)
    db.commit()
    return {'status': 'snapshot_recorded', 'accounts_snapshotted': len(accounts)}

def admin_cash_forecasts(db: Session=Depends(get_db), current_user: dict=Depends(require_treasury_access)):
    forecasts = db.execute(select(CashFlowForecast).order_by(CashFlowForecast.forecast_date.desc()).limit(12)).scalars().all()
    return [{'id': f.id, 'forecast_date': f.forecast_date.isoformat(), 'period_start': f.period_start.isoformat(), 'period_end': f.period_end.isoformat(), 'net_cash_flow': float(f.net_cash_flow), 'opening_balance': float(f.opening_balance), 'closing_balance': float(f.closing_balance)} for f in forecasts]

def consolidated_treasury_metrics(db: Session=Depends(get_db), current_user: dict=Depends(require_treasury_access)):
    total_accounts = db.query(TreasuryAccount).count()
    total_je = db.query(JournalEntry).count()
    total_batches = db.query(PayoutBatch).count()
    total_invoices = db.query(Invoice).count()
    return {'total_accounts': total_accounts, 'total_journal_entries': total_je, 'total_payout_batches': total_batches, 'total_invoices': total_invoices}

def consolidated_treasury_ledger(limit: int=Query(50, ge=1, le=500), db: Session=Depends(get_db), current_user: dict=Depends(require_treasury_access)):
    entries = db.query(JournalEntry).order_by(JournalEntry.created_at.desc()).limit(limit).all()
    return [{'id': e.id, 'description': e.description, 'entry_type': e.entry_type, 'amount': float(e.amount), 'status': e.status, 'created_at': e.created_at.isoformat()} for e in entries]

def consolidated_trial_balance(db: Session=Depends(get_db), current_user: dict=Depends(require_treasury_access), page: int=Query(1, ge=1), page_size: int=Query(20, ge=1, le=100)):
    query = db.query(Account).filter(Account.is_active == True)
    total = query.count()
    accounts = query.order_by(Account.code).offset((page - 1) * page_size).limit(page_size).all()
    return {'data': [{'id': a.id, 'code': a.code, 'name': a.name, 'normal_side': a.normal_side, 'total_debits': float(db.query(func.coalesce(func.sum(JournalEntryLine.amount), 0)).filter(JournalEntryLine.account_id == a.id, JournalEntryLine.side == 'debit').scalar() or 0), 'total_credits': float(db.query(func.coalesce(func.sum(JournalEntryLine.amount), 0)).filter(JournalEntryLine.account_id == a.id, JournalEntryLine.side == 'credit').scalar() or 0)} for a in accounts], 'total': total, 'page': page, 'page_size': page_size}

def consolidated_cash_position(db: Session=Depends(get_db), current_user: dict=Depends(require_treasury_access), page: int=Query(1, ge=1), page_size: int=Query(20, ge=1, le=100)):
    query = db.query(TreasuryAccount).filter(TreasuryAccount.is_active == True)
    total = query.count()
    accounts = query.offset((page - 1) * page_size).limit(page_size).all()
    total_balance = float(db.query(func.coalesce(func.sum(TreasuryAccount.balance), 0)).filter(TreasuryAccount.is_active == True).scalar() or 0)
    return {'accounts': [{'id': a.id, 'name': a.name, 'balance': float(a.balance or 0), 'currency': a.currency or 'USD'} for a in accounts], 'total_balance': total_balance, 'total': total, 'page': page, 'page_size': page_size}

def consolidated_payout_batches(limit: int=Query(50, ge=1, le=200), db: Session=Depends(get_db), current_user: dict=Depends(require_treasury_access)):
    batches = db.query(PayoutBatch).order_by(PayoutBatch.created_at.desc()).limit(limit).all()
    return [{'id': b.id, 'batch_ref': b.batch_number, 'status': b.status, 'total_amount': float(b.total_amount or 0), 'item_count': b.item_count, 'country_code': b.country_code, 'created_at': b.created_at.isoformat()} for b in batches]

def consolidated_vat_liability(db: Session=Depends(get_db), current_user: dict=Depends(require_treasury_access)):
    vats = db.query(VATRemittance).order_by(VATRemittance.period_start.desc()).limit(12).all()
    return [{'id': v.id, 'country_code': v.country_code, 'period_start': v.period_start.isoformat(), 'period_end': v.period_end.isoformat(), 'total_collected': float(v.vat_collected_amount or 0), 'total_deducted': float(v.vat_adjustment_amount or 0), 'net_due': float(v.amount_due or 0), 'status': v.status} for v in vats]

def consolidated_cod_remittances(limit: int=Query(50, ge=1, le=200), db: Session=Depends(get_db), current_user: dict=Depends(require_treasury_access)):
    from domains.logistics.models.logistics import Shipment as ShipmentModel
    receipts = db.query(LogisticsCODRemittanceReceipt).order_by(LogisticsCODRemittanceReceipt.created_at.desc()).limit(limit).all()
    return [{'id': r.id, 'shipment_id': r.shipment_id, 'order_id': db.query(ShipmentModel.order_id).filter(ShipmentModel.id == r.shipment_id).scalar() if r.shipment_id else None, 'partner_id': r.partner_id, 'amount': float(r.amount), 'bank_reference': r.bank_reference, 'status': r.status, 'country_code': r.country_code, 'created_at': r.created_at.isoformat() if r.created_at else None} for r in receipts]

def consolidated_gateway_summary(db: Session=Depends(get_db), current_user: dict=Depends(require_treasury_access)):
    schedules = db.query(GatewaySettlementSchedule).order_by(GatewaySettlementSchedule.settlement_date.desc()).limit(12).all()
    return [{'id': s.id, 'gateway': s.gateway_id, 'settlement_date': s.settlement_date.isoformat() if s.settlement_date else None, 'amount': float(s.amount or 0), 'currency': s.currency, 'status': s.status} for s in schedules]

def consolidated_cash_forecasts(db: Session=Depends(get_db), current_user: dict=Depends(require_treasury_access)):
    forecasts = db.execute(select(CashFlowForecast).order_by(CashFlowForecast.forecast_date.desc()).limit(12)).scalars().all()
    return [{'id': f.id, 'forecast_date': f.forecast_date.isoformat(), 'period_start': f.period_start.isoformat(), 'period_end': f.period_end.isoformat(), 'net_cash_flow': float(f.net_cash_flow), 'opening_balance': float(f.opening_balance), 'closing_balance': float(f.closing_balance)} for f in forecasts]

def consolidated_reconciliation_pipeline(limit: int=Query(50, ge=1, le=200), db: Session=Depends(get_db), current_user: dict=Depends(require_treasury_access)):
    from domains.orders.models.orders import Order as OrderModel
    from domains.finance.models.payments import Payment as PaymentModel
    from domains.finance.models.payments import Payout
    pipeline = []
    orders = db.query(OrderModel).filter(OrderModel.status.in_(['shipped', 'delivered', 'completed', 'dispatched'])).order_by(OrderModel.updated_at.desc()).limit(limit).all()
    for order in orders:
        payment = db.query(PaymentModel).filter(PaymentModel.order_id == order.id).first()
        settlement = db.query(SupplierSettlement).filter(SupplierSettlement.order_id == order.id).first()
        payout = db.query(Payout).filter(Payout.id == settlement.payout_id).first() if settlement and settlement.payout_id else None
        pipeline.append({'order_id': order.id, 'order_status': order.status, 'order_total': float(getattr(order, 'total_amount', None) or getattr(order, 'total', 0) or 0), 'country_code': order.country_code or '', 'payment_method': payment.payment_method if payment else None, 'payment_status': payment.status if payment else None, 'supplier_settlement_status': settlement.status if settlement else None, 'supplier_payout_status': payout.status if payout else None, 'stage': _resolve_stage(order, payment, None, settlement, payout)})
    return {'pipeline': pipeline, 'total': len(pipeline), 'consolidated': True}

def country_treasury_metrics(country_code: str=Path(..., description='ISO country code'), db: Session=Depends(get_db), current_user: dict=Depends(require_treasury_access)):
    cc = country_code.upper()
    total_debits = db.execute(select(func.coalesce(func.sum(JournalEntryLine.amount), 0)).join(JournalEntry, JournalEntryLine.entry_id == JournalEntry.id).where(JournalEntryLine.side == 'debit', JournalEntry.country_code == cc)).scalar() or Decimal('0')
    total_credits = db.execute(select(func.coalesce(func.sum(JournalEntryLine.amount), 0)).join(JournalEntry, JournalEntryLine.entry_id == JournalEntry.id).where(JournalEntryLine.side == 'credit', JournalEntry.country_code == cc)).scalar() or Decimal('0')
    total_entries = db.query(JournalEntry).filter(JournalEntry.country_code == cc).count()
    return {'total_credits': float(total_credits), 'total_debits': float(total_debits), 'net_balance': float(total_credits - total_debits), 'total_entries': total_entries, 'country_code': cc}

def country_treasury_ledger(country_code: str=Path(..., description='ISO country code'), start_date: date=Query(...), end_date: date=Query(...), limit: int=Query(50), db: Session=Depends(get_db), current_user: dict=Depends(require_treasury_access)):
    cc = country_code.upper()
    entries = db.execute(select(JournalEntry).where(JournalEntry.entry_date >= start_date, JournalEntry.entry_date <= end_date, JournalEntry.country_code == cc).options(joinedload(JournalEntry.lines)).order_by(JournalEntry.entry_date.desc()).limit(limit)).unique().scalars().all()
    result = []
    for e in entries:
        result.append({'id': e.id, 'reference_number': getattr(e, 'reference_number', ''), 'entry_date': e.entry_date.isoformat() if hasattr(e, 'entry_date') and e.entry_date else '', 'description': e.description or '', 'source': e.source or '', 'total_debit': sum((float(line.amount) for line in e.lines if line.side == 'debit')), 'total_credit': sum((float(line.amount) for line in e.lines if line.side == 'credit'))})
    return result

def country_cash_position(country_code: str=Path(..., description='ISO country code'), db: Session=Depends(get_db), current_user: dict=Depends(require_treasury_access)):
    cc = country_code.upper()
    accounts = db.execute(select(TreasuryAccount).where(TreasuryAccount.is_active == True, TreasuryAccount.country_code == cc)).scalars().all()
    if not accounts:
        accounts = db.execute(select(TreasuryAccount).where(TreasuryAccount.is_active == True, TreasuryAccount.country_code.is_(None))).scalars().all()
    return [{'account_name': a.name, 'balance': float(a.balance), 'gl_code': a.gl_account_code or a.slug} for a in accounts]

def country_payout_batches(country_code: str=Path(..., description='ISO country code'), db: Session=Depends(get_db), current_user: dict=Depends(require_treasury_access)):
    cc = country_code.upper()
    batches = db.execute(select(PayoutBatch).options(joinedload(PayoutBatch.creator), joinedload(PayoutBatch.approver)).where(PayoutBatch.country_code == cc).order_by(PayoutBatch.created_at.desc()).limit(100)).unique().scalars().all()
    return [{'id': b.id, 'batch_number': b.batch_number, 'country_code': b.country_code, 'total_amount': float(b.total_amount), 'status': b.status, 'created_at': b.created_at.isoformat(), 'created_by': b.created_by, 'created_by_name': b.creator.full_name if b.creator else None, 'approved_by': b.approved_by, 'approved_by_name': b.approver.full_name if b.approver else None} for b in batches]

def country_vat_liability(country_code: str=Path(..., description='ISO country code'), period: str=Query('current'), db: Session=Depends(get_db), current_user: dict=Depends(require_treasury_access)):
    output_vat = db.execute(select(func.coalesce(func.sum(AccountBalance.balance), 0)).join(Account, AccountBalance.account_id == Account.id).where(Account.code == OUTPUT_VAT_ACCOUNT)).scalar() or Decimal('0')
    input_vat = db.execute(select(func.coalesce(func.sum(AccountBalance.balance), 0)).join(Account, AccountBalance.account_id == Account.id).where(Account.code == INPUT_VAT_ACCOUNT)).scalar() or Decimal('0')
    return {'output_vat': float(output_vat), 'input_vat': float(input_vat), 'net_vat_due': float(output_vat - input_vat), 'country_code': country_code.upper(), 'period': period}

def country_cod_remittances(country_code: str=Path(..., description='ISO country code'), status: Optional[str]=Query(None), db: Session=Depends(get_db), current_user: dict=Depends(require_treasury_access)):
    from domains.logistics.models.logistics import LogisticsPartner
    cc = country_code.upper()
    query = select(LogisticsCODRemittanceReceipt, LogisticsPartner.name).outerjoin(LogisticsPartner, LogisticsCODRemittanceReceipt.partner_id == LogisticsPartner.id).where(LogisticsCODRemittanceReceipt.country_code == cc)
    if status:
        query = query.where(LogisticsCODRemittanceReceipt.status == status)
    query = query.order_by(LogisticsCODRemittanceReceipt.created_at.desc()).limit(100)
    rows = db.execute(query).all()
    return [{'id': r.id, 'logistics_partner_id': r.partner_id, 'logistics_partner_name': partner_name or 'Unknown', 'amount_remitted': float(r.amount or 0), 'amount_expected': float(r.amount or 0), 'status': r.status, 'remitted_at': r.created_at.isoformat() if r.created_at else None, 'bank_reference': None, 'proof_url': None} for (r, partner_name) in rows]

def country_gateway_summary(country_code: str=Path(..., description='ISO country code'), db: Session=Depends(get_db), current_user: dict=Depends(require_treasury_access)):
    cc = country_code.upper()
    schedules = db.execute(select(GatewaySettlementSchedule).where(GatewaySettlementSchedule.country_code == cc).order_by(GatewaySettlementSchedule.settlement_date.desc()).limit(100)).scalars().all()
    from collections import defaultdict
    by_gateway = defaultdict(lambda : {'total_settled': 0, 'total_expected': 0, 'count': 0, 'last_date': None})
    for s in schedules:
        key = str(s.gateway_id)
        by_gateway[key]['total_expected'] += float(s.amount or 0)
        by_gateway[key]['count'] += 1
        if s.status == 'settled':
            by_gateway[key]['total_settled'] += float(s.amount or 0)
        if not by_gateway[key]['last_date'] or (s.settlement_date and s.settlement_date > by_gateway[key]['last_date']):
            by_gateway[key]['last_date'] = s.settlement_date
    return [{'gateway_code': gid, 'total_settled': data['total_settled'], 'total_expected': data['total_expected'], 'discrepancy': data['total_expected'] - data['total_settled'], 'count': data['count'], 'last_settlement_date': data['last_date'].isoformat() if data['last_date'] else None} for (gid, data) in by_gateway.items()]

def admin_reconciliation_pipeline(country_code: str=Path(..., description='ISO country code'), status: Optional[str]=Query(None), limit: int=Query(50, ge=1, le=200), db: Session=Depends(get_db), current_user: dict=Depends(require_treasury_access)):
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
        from domains.finance.services.commission.commission_engine import get_effective_rate
        pipeline = []
        orders = db.query(OrderModel).filter(OrderModel.country_code == cc, OrderModel.status.in_(['shipped', 'delivered', 'completed', 'dispatched'])).order_by(OrderModel.updated_at.desc()).limit(limit).all()
        for order in orders:
            order_total = float(getattr(order, 'total_amount', None) or getattr(order, 'total', 0) or 0)
            payment = db.query(PaymentModel).filter(PaymentModel.order_id == order.id).first()
            from domains.logistics.models.logistics import Shipment
            shipment = db.query(Shipment).filter(Shipment.order_id == order.id).first()
            logistics_partner_name = None
            if shipment and shipment.carrier_name:
                logistics_partner_name = shipment.carrier_name
            cod_receipt = None
            if payment and payment.payment_method == 'cod':
                cod_receipt = db.query(LogisticsCODRemittanceReceipt).filter(LogisticsCODRemittanceReceipt.order_id == order.id).first()
            settlement = db.query(SupplierSettlement).filter(SupplierSettlement.order_id == order.id).first()
            payout = None
            if settlement:
                payout = db.query(Payout).filter(Payout.id == settlement.payout_id).first() if settlement.payout_id else None
            supplier_id = None
            first_item = db.query(OrderItem).filter(OrderItem.order_id == order.id).first()
            if first_item:
                supplier_id = first_item.supplier_id
            commission_preview = None
            if supplier_id:
                try:
                    rate = get_effective_rate(supplier_id=supplier_id, product_id=None, db=db)
                    commission_preview = {'rate': float(rate.applied_rate), 'amount': float(rate.applied_rate) * order_total if hasattr(rate, 'applied_rate') else 0}
                except Exception:
                    pass
            pipeline.append({'order_id': order.id, 'order_status': order.status, 'order_total': order_total, 'supplier_id': supplier_id, 'payment_method': payment.payment_method if payment else None, 'payment_status': payment.status if payment else None, 'payment_amount': float(payment.amount) if payment else None, 'logistics_partner': logistics_partner_name, 'cod_remitted': float(cod_receipt.amount) if cod_receipt else None, 'cod_remittance_status': cod_receipt.status if cod_receipt else None, 'supplier_settlement_status': settlement.status if settlement else None, 'supplier_settlement_id': settlement.id if settlement else None, 'supplier_net_amount': float(settlement.net_amount) if settlement else None, 'supplier_payout_status': payout.status if payout else None, 'supplier_payout_amount': float(payout.amount) if payout else None, 'commission': commission_preview, 'stage': _resolve_stage(order, payment, cod_receipt, settlement, payout)})
        if status == 'settled':
            pipeline = [p for p in pipeline if p['supplier_settlement_status'] in ('paid', 'settled')]
        elif status == 'unsettled':
            pipeline = [p for p in pipeline if not p['supplier_settlement_status']]
        return {'pipeline': pipeline, 'total': len(pipeline), 'country_code': cc}
    finally:
        clear_rls_context()

def admin_record_cod_remittance(country_code: str=Path(..., description='ISO country code'), order_id: int=FastAPIBody(...), partner_id: int=FastAPIBody(...), amount: float=FastAPIBody(...), bank_reference: str=FastAPIBody(...), db: Session=Depends(get_db), current_user: dict=Depends(require_treasury_access)):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    cc = country_code.upper()
    try:
        from domains.orders.models.orders import Order as OrderModel
        from domains.logistics.models.logistics import Shipment as ShipmentModel
        shipment = db.query(ShipmentModel).filter(ShipmentModel.order_id == order_id).first()
        receipt = LogisticsCODRemittanceReceipt(shipment_id=shipment.id if shipment else None, partner_id=partner_id, amount=amount, bank_reference=bank_reference, status='remitted', country_code=cc)
        db.add(receipt)
        db.flush()
        order = db.query(OrderModel).filter(OrderModel.id == order_id).first()
        if order:
            setattr(order, 'settlement_status', 'cod_remitted')
        db.commit()
        db.refresh(receipt)
        try:
            from domains.finance.services.ledger.general_ledger_service import post_logistics_cod_remittance_journal
            post_logistics_cod_remittance_journal(db, receipt.id, Decimal(str(amount)), country_code=cc)
        except Exception as gl_err:
            logger.warning(f'COD remittance GL post skipped: {gl_err}')
        return {'status': 'ok', 'receipt_id': receipt.id, 'country_code': cc}
    finally:
        clear_rls_context()

def admin_settle_supplier(country_code: str=Path(..., description='ISO country code'), order_id: int=FastAPIBody(...), supplier_id: int=FastAPIBody(...), net_amount: float=FastAPIBody(...), gross_amount: Optional[float]=FastAPIBody(None), commission_amount: Optional[float]=FastAPIBody(None), currency: Optional[str]=FastAPIBody(None), payout_id: Optional[int]=FastAPIBody(None), db: Session=Depends(get_db), current_user: dict=Depends(require_treasury_access)):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    cc = country_code.upper()
    try:
        from domains.orders.models.orders import Order as OrderModel
        from domains.country.models.countries import CountryConfig
        gross = gross_amount if gross_amount is not None else net_amount
        resolved_currency = currency or 'USD'
        ccfg = db.query(CountryConfig).filter(CountryConfig.code == cc).first()
        if ccfg and ccfg.currency:
            resolved_currency = ccfg.currency
        settlement = SupplierSettlement(order_id=order_id, supplier_id=supplier_id, gross_amount=gross, commission_amount=commission_amount, net_amount=net_amount, status='settled', payout_id=payout_id, currency=resolved_currency, country_code=cc)
        db.add(settlement)
        db.flush()
        order = db.query(OrderModel).filter(OrderModel.id == order_id).first()
        if order:
            setattr(order, 'settlement_status', 'settled')
        db.commit()
        db.refresh(settlement)
        return {'status': 'ok', 'settlement_id': settlement.id, 'country_code': cc}
    finally:
        clear_rls_context()

def admin_approve_settlement(country_code: str=Path(..., description='ISO country code'), settlement_id: int=FastAPIBody(..., embed=True), db: Session=Depends(get_db), current_user: dict=Depends(require_treasury_access)):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        settlement = db.query(SupplierSettlement).filter(SupplierSettlement.id == settlement_id, SupplierSettlement.country_code == country_code.upper()).first()
        if not settlement:
            raise HTTPException(status_code=404, detail='Settlement not found')
        settlement.status = 'paid'
        db.commit()
        try:
            from domains.finance.services.ledger.general_ledger_service import post_supplier_settlement_journal
            post_supplier_settlement_journal(db, settlement.id, Decimal(str(settlement.net_amount or 0)), supplier_id=settlement.supplier_id, country_code=country_code.upper())
        except Exception as gl_err:
            logger.warning(f'Supplier settlement GL post skipped: {gl_err}')
        return {'status': 'ok', 'settlement_id': settlement.id}
    finally:
        clear_rls_context()

def admin_gateway_exceptions(db: Session=Depends(get_db), current_user: dict=Depends(require_treasury_access)):
    issues = db.execute(select(GatewaySettlementSchedule).where(GatewaySettlementSchedule.status.in_(['pending', 'flagged'])).order_by(GatewaySettlementSchedule.settlement_date.desc()).limit(100)).scalars().all()
    return [{'id': s.id, 'gateway_id': s.gateway_id, 'settlement_date': s.settlement_date.isoformat() if s.settlement_date else None, 'amount': float(s.amount or 0), 'currency': s.currency, 'status': s.status, 'country_code': getattr(s, 'country_code', None)} for s in issues]

def country_gateway_exceptions(country_code: str=Path(..., description='ISO country code'), db: Session=Depends(get_db), current_user: dict=Depends(require_treasury_access)):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        issues = db.execute(select(GatewaySettlementSchedule).where(GatewaySettlementSchedule.status.in_(['pending', 'flagged']), GatewaySettlementSchedule.country_code == country_code.upper()).order_by(GatewaySettlementSchedule.settlement_date.desc()).limit(100)).scalars().all()
        return [{'id': s.id, 'gateway_id': s.gateway_id, 'settlement_date': s.settlement_date.isoformat() if s.settlement_date else None, 'amount': float(s.amount or 0), 'currency': s.currency, 'status': s.status, 'country_code': s.country_code} for s in issues]
    finally:
        clear_rls_context()

def admin_payment_transactions(start_date: date=Query(...), end_date: date=Query(...), gateway: Optional[str]=Query(None), status: Optional[str]=Query(None), db: Session=Depends(get_db), current_user: dict=Depends(require_treasury_access)):
    query = select(Payment).where(Payment.created_at >= start_date, Payment.created_at <= end_date).order_by(Payment.created_at.desc())
    if gateway:
        query = query.where(Payment.provider == gateway)
    if status:
        query = query.where(Payment.status == status)
    rows = db.execute(query.limit(200)).scalars().all()
    return [{'id': p.id, 'order_id': p.order_id, 'amount': float(p.amount), 'payment_method': p.payment_method, 'provider': p.provider, 'status': p.status, 'created_at': p.created_at.isoformat() if p.created_at else None, 'country_code': p.country_code} for p in rows]

def country_payment_transactions(country_code: str=Path(..., description='ISO country code'), start_date: date=Query(...), end_date: date=Query(...), gateway: Optional[str]=Query(None), status: Optional[str]=Query(None), db: Session=Depends(get_db), current_user: dict=Depends(require_treasury_access)):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        query = select(Payment).where(Payment.country_code == country_code.upper(), Payment.created_at >= start_date, Payment.created_at <= end_date).order_by(Payment.created_at.desc())
        if gateway:
            query = query.where(Payment.provider == gateway)
        if status:
            query = query.where(Payment.status == status)
        rows = db.execute(query.limit(200)).scalars().all()
        return [{'id': p.id, 'order_id': p.order_id, 'amount': float(p.amount), 'payment_method': p.payment_method, 'provider': p.provider, 'status': p.status, 'created_at': p.created_at.isoformat() if p.created_at else None, 'country_code': p.country_code} for p in rows]
    finally:
        clear_rls_context()

def admin_supplier_payouts(status: Optional[str]=Query(None), db: Session=Depends(get_db), current_user: dict=Depends(require_treasury_access)):
    from domains.comms.models.suppliers import SupplierProfile
    query = select(Payout, SupplierProfile).outerjoin(SupplierProfile, Payout.supplier_id == SupplierProfile.id).order_by(Payout.created_at.desc())
    if status:
        query = query.where(Payout.status == status)
    rows = db.execute(query.limit(200)).all()
    return [{'id': p.id, 'supplier_id': p.supplier_id, 'supplier_name': s.company_name if s else f'Supplier #{p.supplier_id}', 'amount': float(p.amount), 'currency': p.currency, 'method': p.method, 'status': p.status, 'reference': p.reference, 'created_at': p.created_at.isoformat() if p.created_at else None, 'country_code': p.country_code} for (p, s) in rows]

def country_supplier_payouts(country_code: str=Path(..., description='ISO country code'), status: Optional[str]=Query(None), db: Session=Depends(get_db), current_user: dict=Depends(require_treasury_access)):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        from domains.comms.models.suppliers import SupplierProfile
        query = select(Payout, SupplierProfile).outerjoin(SupplierProfile, Payout.supplier_id == SupplierProfile.id).where(Payout.country_code == country_code.upper()).order_by(Payout.created_at.desc())
        if status:
            query = query.where(Payout.status == status)
        rows = db.execute(query.limit(200)).all()
        return [{'id': p.id, 'supplier_id': p.supplier_id, 'supplier_name': s.company_name if s else f'Supplier #{p.supplier_id}', 'amount': float(p.amount), 'currency': p.currency, 'method': p.method, 'status': p.status, 'reference': p.reference, 'created_at': p.created_at.isoformat() if p.created_at else None, 'country_code': p.country_code} for (p, s) in rows]
    finally:
        clear_rls_context()

def admin_logistics_payouts(status: Optional[str]=Query(None), db: Session=Depends(get_db), current_user: dict=Depends(require_treasury_access)):
    query = select(LogisticsPartnerPayout).order_by(LogisticsPartnerPayout.created_at.desc())
    if status:
        query = query.where(LogisticsPartnerPayout.status == status)
    rows = db.execute(query.limit(200)).scalars().all()
    return [{'id': p.id, 'partner_id': p.partner_id, 'amount': float(p.amount), 'currency': p.currency, 'status': p.status, 'reference_id': p.reference_id, 'period_start': p.period_start.isoformat() if p.period_start else None, 'period_end': p.period_end.isoformat() if p.period_end else None, 'created_at': p.created_at.isoformat() if p.created_at else None, 'country_code': p.country_code} for p in rows]

def country_logistics_payouts(country_code: str=Path(..., description='ISO country code'), status: Optional[str]=Query(None), db: Session=Depends(get_db), current_user: dict=Depends(require_treasury_access)):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        query = select(LogisticsPartnerPayout).where(LogisticsPartnerPayout.country_code == country_code.upper()).order_by(LogisticsPartnerPayout.created_at.desc())
        if status:
            query = query.where(LogisticsPartnerPayout.status == status)
        rows = db.execute(query.limit(200)).scalars().all()
        return [{'id': p.id, 'partner_id': p.partner_id, 'amount': float(p.amount), 'currency': p.currency, 'status': p.status, 'reference_id': p.reference_id, 'period_start': p.period_start.isoformat() if p.period_start else None, 'period_end': p.period_end.isoformat() if p.period_end else None, 'created_at': p.created_at.isoformat() if p.created_at else None, 'country_code': p.country_code} for p in rows]
    finally:
        clear_rls_context()

def admin_supplier_earnings(db: Session=Depends(get_db), current_user: dict=Depends(require_treasury_access)):
    rows = db.execute(select(SupplierSettlement.supplier_id, func.sum(SupplierSettlement.gross_amount).label('gross'), func.sum(SupplierSettlement.commission_amount).label('commission'), func.sum(SupplierSettlement.net_amount).label('net')).group_by(SupplierSettlement.supplier_id)).all()
    return [{'supplier_id': r.supplier_id, 'gross': float(r.gross or 0), 'commission': float(r.commission or 0), 'net': float(r.net or 0)} for r in rows]

def country_supplier_earnings(country_code: str=Path(..., description='ISO country code'), db: Session=Depends(get_db), current_user: dict=Depends(require_treasury_access)):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        rows = db.execute(select(SupplierSettlement.supplier_id, func.sum(SupplierSettlement.gross_amount).label('gross'), func.sum(SupplierSettlement.commission_amount).label('commission'), func.sum(SupplierSettlement.net_amount).label('net')).where(SupplierSettlement.country_code == country_code.upper()).group_by(SupplierSettlement.supplier_id)).all()
        return [{'supplier_id': r.supplier_id, 'gross': float(r.gross or 0), 'commission': float(r.commission or 0), 'net': float(r.net or 0)} for r in rows]
    finally:
        clear_rls_context()

def admin_liabilities_exposure(db: Session=Depends(get_db), current_user: dict=Depends(require_treasury_access)):
    codes = {'2010': 'supplier_payables', '2020': 'logistics_payables', '2040': 'vat_payable'}
    exposure = {}
    for (code, label) in codes.items():
        bal = db.execute(select(func.coalesce(func.sum(AccountBalance.balance), 0)).join(Account, AccountBalance.account_id == Account.id).where(Account.code == code)).scalar() or Decimal('0')
        exposure[label] = float(bal)
    return exposure

def country_liabilities_exposure(country_code: str=Path(..., description='ISO country code'), db: Session=Depends(get_db), current_user: dict=Depends(require_treasury_access)):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        codes = {'2010': 'supplier_payables', '2020': 'logistics_payables', '2030': 'vat_payable'}
        exposure = {}
        for (code, label) in codes.items():
            bal = db.execute(select(func.coalesce(func.sum(AccountBalance.balance), 0)).join(Account, AccountBalance.account_id == Account.id).where(Account.code == code, AccountBalance.country_code == country_code.upper())).scalar() or Decimal('0')
            exposure[label] = float(bal)
        return exposure
    finally:
        clear_rls_context()

def payroll_equity(db: Session=Depends(get_db)):
    """Pay-equity snapshot by department (avg male vs female salary)."""
    rows = db.query(Employee.department, Employee.gender, func.avg(Employee.salary)).filter(Employee.salary.isnot(None), Employee.department.isnot(None)).group_by(Employee.department, Employee.gender).all()
    by_dept = {}
    for (dept, gender, avg_sal) in rows:
        by_dept.setdefault(dept, {})[gender or 'unknown'] = float(avg_sal or 0)
    metrics = []
    for (dept, vals) in by_dept.items():
        avg_male = vals.get('male', 0.0)
        avg_female = vals.get('female', 0.0)
        if avg_male > 0 and avg_female > 0:
            disparity = (avg_male - avg_female) / avg_male * 100
        else:
            disparity = 0.0
        metrics.append({'category': dept, 'avg_male': round(avg_male, 2), 'avg_female': round(avg_female, 2), 'disparity_percent': round(disparity, 2), 'flagged': disparity > 10})
    return metrics

def country_payroll(country_code: str, db: Session=Depends(get_db)):
    """Aggregate payroll totals for a country (employee headcount + gross/tax/net)."""
    rows = db.query(func.count(Employee.id), func.coalesce(func.sum(Employee.salary), 0)).filter(Employee.country_code == country_code.upper()).all()
    employee_count = int(rows[0][0] or 0)
    total_gross = float(rows[0][1] or 0)
    total_tax = round(total_gross * 0.05, 2)
    total_net = round(total_gross - total_tax, 2)
    return {'employee_count': employee_count, 'total_gross': round(total_gross, 2), 'total_tax': total_tax, 'total_net': total_net}


# === Merged from flat_admin_treasury_status_service.py ===

"""Admin payouts router."""
from fastapi import Depends, HTTPException, Path, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from infrastructure.database.database import get_db
from domains.governance.models.user import User
from domains.finance.models.finance import FinanceAutomationLog
from domains.finance.models.payments import Payout
from infrastructure.database.schemas import PayoutCreate, PayoutOut
from infrastructure.utils.dependencies import require_admin
from domains.country.utils.country_rls import get_country_or_404
from infrastructure.utils.rls_interceptor import set_rls_context, clear_rls_context
from infrastructure.utils.datetime_utils import utcnow
from infrastructure.utils.audit import audit_log, AuditAction
from domains.finance.services.payments.auto_payout_scheduler import get_background_job_status as _get_bg_status
from domains.finance.services.payments.auto_payout_scheduler import start_auto_payout_background_job as _start_bg_job
from domains.finance.services.payments.auto_payout_scheduler import stop_auto_payout_background_job as _stop_bg_job
from domains.finance.services.payments.auto_payout_scheduler import run_auto_payout_sweep as _run_supplier_sweep
from domains.finance.services.payments.auto_payout_scheduler import run_auto_logistics_payout_sweep as _run_logistics_sweep

class PayoutVerifyRequest(BaseModel):
    note: str | None = None
    bank_reference: str | None = None
    transfer_date: str | None = None
    status: str = 'verified'

def list_payouts(country_code: str=Path(..., description='ISO country code'), _: User=Depends(require_admin), db: Session=Depends(get_db), page: int=Query(1, ge=1), page_size: int=Query(20, ge=1, le=100)):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        q = db.query(Payout).filter(Payout.country_code == country_code.upper())
        total = q.count()
        rows = q.order_by(Payout.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
        return {'data': rows, 'total': total, 'page': page, 'page_size': page_size}
    finally:
        clear_rls_context()

def create_payout(country_code: str=Path(..., description='ISO country code'), payload: PayoutCreate=None, current_admin: User=Depends(require_admin), db: Session=Depends(get_db)):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        model_cols = {c.name for c in Payout.__table__.columns}
        data = {k: v for (k, v) in payload.model_dump().items() if k in model_cols}
        p = Payout(**data, country_code=country_code.upper())
        db.add(p)
        db.commit()
        db.refresh(p)
        audit_log(db=db, action=AuditAction.PAYOUT_PROCESSED, user_id=current_admin.id, username=current_admin.username, user_role='admin', resource_type='payout', resource_id=p.id, details={'amount': str(p.amount) if p.amount else None, 'method': p.method})
        return p
    finally:
        clear_rls_context()

def list_pending_payouts(current_admin: User=Depends(require_admin), db: Session=Depends(get_db), page: int=Query(1, ge=1), page_size: int=Query(20, ge=1, le=100)):
    """List all pending payouts (RLS-scoped if context is set)."""
    q = db.query(Payout).filter(Payout.status == 'pending')
    total = q.count()
    rows = q.order_by(Payout.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return {'data': rows, 'total': total, 'page': page, 'page_size': page_size}

def list_pending_payouts_by_country(country_code: str=Path(..., description='ISO country code'), current_admin: User=Depends(require_admin), db: Session=Depends(get_db), page: int=Query(1, ge=1), page_size: int=Query(20, ge=1, le=100)):
    """List pending payouts for a specific country."""
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        q = db.query(Payout).filter(Payout.status == 'pending', Payout.country_code == country_code.upper())
        total = q.count()
        rows = q.order_by(Payout.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
        return {'data': rows, 'total': total, 'page': page, 'page_size': page_size}
    finally:
        clear_rls_context()

def verify_payout(country_code: str=Path(..., description='ISO country code'), payout_id: int=Path(...), payload: PayoutVerifyRequest=None, current_admin: User=Depends(require_admin), db: Session=Depends(get_db)):
    """Verify a payout."""
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        p = db.query(Payout).filter(Payout.id == payout_id, Payout.country_code == country_code.upper()).first()
        if not p:
            raise HTTPException(404, 'Payout not found')
        p.status = payload.status if payload and payload.status else 'verified'
        p.processed_at = utcnow()
        if payload:
            if payload.note:
                p.notes = payload.note
            if payload.bank_reference:
                p.reference = payload.bank_reference
        db.commit()
        audit_log(db=db, action=AuditAction.PAYOUT_PROCESSED, user_id=current_admin.id, username=current_admin.username, user_role='admin', resource_type='payout', resource_id=payout_id, details={'status': p.status, 'reference': p.reference, 'notes': p.notes})
        return {'verified': True, 'payout_id': payout_id}
    finally:
        clear_rls_context()

def process_payout(country_code: str=Path(..., description='ISO country code'), payout_id: int=Path(...), current_admin: User=Depends(require_admin), db: Session=Depends(get_db)):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        p = db.query(Payout).filter(Payout.id == payout_id, Payout.country_code == country_code.upper()).first()
        if not p:
            raise HTTPException(404)
        p.status = 'paid'
        p.processed_at = utcnow()
        db.commit()
        audit_log(db=db, action=AuditAction.PAYOUT_PROCESSED, user_id=current_admin.id, username=current_admin.username, user_role='admin', resource_type='payout', resource_id=payout_id, details={'status': 'paid'})
        return {'message': 'Payout processed'}
    finally:
        clear_rls_context()

def get_background_job_status_endpoint(db: Session=Depends(get_db), current_admin: User=Depends(require_admin)):
    """Return the current state of the auto-payout background job:
    is_running, last_run_at, last_run_status, last_error, total counts,
    and recent FinanceAutomationLog entries.
    """
    status = _get_bg_status()
    history = db.query(FinanceAutomationLog).filter(FinanceAutomationLog.kind.in_(['auto_payout', 'auto_logistics_payout'])).order_by(FinanceAutomationLog.created_at.desc()).limit(20).all()
    return {'status': status, 'history': [{'id': h.id, 'kind': h.kind, 'records_processed': h.records_processed, 'records_changed': h.records_changed, 'detail': h.detail, 'created_at': h.created_at.isoformat() if h.created_at else None} for h in history]}


# === Merged from public_treasury_payments_service.py ===

"""
Admin Payout Approval Router
=============================
Endpoints for the Admin Payout Approval Dashboard — lists all pending payouts
and batches with supplier/logistics context, and provides an approve/reject/dispatch
workflow.

Routes (mounted at /admin/payout-approval):
  GET  /pending                       ? pending payouts + batches with enrichment
  POST /payouts/{payout_id}/approve   ? approve an individual (unbatched) payout
  POST /payouts/{payout_id}/reject    ? reject an individual payout
  POST /batches/{batch_id}/approve    ? approve a batch (draft?approved)
  POST /batches/{batch_id}/reject     ? reject a batch
  POST /batches/{batch_id}/dispatch   ? mark batch + its payouts as paid
"""
from __future__ import annotations
import logging
from decimal import Decimal
from typing import Any, cast
from fastapi import Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session, joinedload
from infrastructure.database.database import get_db
from domains.accounts.models.user import User
from domains.finance.models.finance import PayoutBatch
from domains.finance.models.finance import PayoutBatchItem
from domains.finance.models.finance import SupplierSettlement
from domains.logistics.models.logistics import LogisticsPartner
from domains.finance.models.payments import LogisticsPartnerPayout
from domains.finance.models.payments import Payout
from infrastructure.utils.dependencies import require_admin
from infrastructure.utils.datetime_utils import utcnow
from infrastructure.utils.audit import audit_log, AuditAction
logger = logging.getLogger(__name__)

class ActionRequest(BaseModel):
    notes: str | None = None

def _serialize_batch_item(item: PayoutBatchItem) -> dict[str, Any]:
    return {'id': cast(int, item.id), 'entity_type': cast(str, item.entity_type), 'entity_id': cast(int, item.entity_id), 'amount': float(cast(Decimal, item.amount or 0)), 'currency': cast(str | None, item.currency) or 'OMR', 'reference': cast(str | None, item.reference), 'status': cast(str | None, item.status) or ''}

def _serialize_batch(batch: PayoutBatch) -> dict[str, Any]:
    return {'id': cast(int, batch.id), 'batch_number': cast(str, batch.batch_number), 'country_code': cast(str, batch.country_code), 'total_amount': float(cast(Decimal, batch.total_amount or 0)), 'item_count': cast(int, batch.item_count or 0), 'status': cast(str, batch.status), 'notes': cast(str | None, batch.notes), 'created_at': cast(Any, batch.created_at).isoformat() if getattr(batch, 'created_at', None) else None, 'items': [_serialize_batch_item(item) for item in batch.items or []]}

def _load_pending_batches_with_items(db: Session, page: int, page_size: int) -> tuple[list[dict[str, Any]], int]:
    """Return paginated batches in draft/pending status with enriched items."""
    query = db.query(PayoutBatch).options(joinedload(PayoutBatch.items)).filter(PayoutBatch.status.in_(['draft', 'pending']))
    total = query.count()
    batches = query.order_by(PayoutBatch.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    result = []
    for batch in batches:
        enriched_items = _enrich_batch_items(batch, db)
        s = _serialize_batch(batch)
        s['items'] = enriched_items
        result.append(s)
    return (result, total)

def _resolve_supplier_names(entity_ids: set[int], db: Session) -> dict[int, str]:
    """Return {entity_id: display_name} for supplier IDs."""
    if not entity_ids:
        return {}
    users = db.query(User).filter(User.id.in_(entity_ids)).all()
    return {cast(int, u.id): cast(str, u.username or u.email or f'Supplier #{u.id}') for u in users}

def _resolve_logistics_names(entity_ids: set[int], db: Session) -> dict[int, str]:
    """Return {entity_id: display_name} for logistics partner IDs."""
    if not entity_ids:
        return {}
    partners = db.query(LogisticsPartner).filter(LogisticsPartner.id.in_(entity_ids)).all()
    return {cast(int, p.id): cast(str, p.name or f'Partner #{p.id}') for p in partners}

def _enrich_batch_items(batch: PayoutBatch, db: Session) -> list[dict[str, Any]]:
    """Return batch items with resolved entity_name fields."""
    items = list(batch.items or [])
    supplier_ids = {cast(int, it.entity_id) for it in items if cast(str, it.entity_type) == 'supplier'}
    logistics_ids = {cast(int, it.entity_id) for it in items if cast(str, it.entity_type) == 'logistics'}
    supplier_names = _resolve_supplier_names(supplier_ids, db)
    logistics_names = _resolve_logistics_names(logistics_ids, db)
    enriched = []
    for item in items:
        e = _serialize_batch_item(item)
        eid = cast(int, item.entity_id)
        etype = cast(str, item.entity_type)
        if etype == 'supplier':
            e['entity_name'] = supplier_names.get(eid, f'Supplier #{eid}')
        elif etype == 'logistics':
            e['entity_name'] = logistics_names.get(eid, f'Partner #{eid}')
        else:
            e['entity_name'] = f'#{eid}'
        enriched.append(e)
    return enriched

def _serialize_payout(p: Payout) -> dict[str, Any]:
    return {'id': cast(int, p.id), 'supplier_id': cast(int | None, p.supplier_id), 'order_id': cast(int | None, p.order_id), 'amount': float(cast(Decimal, p.amount or 0)), 'currency': cast(str | None, p.currency) or 'OMR', 'method': cast(str | None, p.method) or '', 'status': cast(str | None, p.status) or '', 'reference': cast(str | None, p.reference), 'notes': cast(str | None, p.notes), 'country_code': cast(str | None, p.country_code) or '', 'created_at': cast(Any, p.created_at).isoformat() if getattr(p, 'created_at', None) else None, 'processed_at': cast(Any, p.processed_at).isoformat() if getattr(p, 'processed_at', None) else None}

def _load_unbatched_payouts(db: Session, page: int, page_size: int) -> tuple[list[dict[str, Any]], int]:
    """Return paginated individual Payout records with supplier names.

    Shows ALL pending/draft payouts — the frontend distinguishes batched
    vs unbatched by cross-referencing batch items.
    """
    query = db.query(Payout).filter(Payout.status.in_(['pending', 'draft']))
    total = query.count()
    payouts = query.order_by(Payout.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    supplier_ids = {cast(int, p.supplier_id) for p in payouts if p.supplier_id}
    supplier_names = _resolve_supplier_names(supplier_ids, db) if supplier_ids else {}
    result = []
    for payout in payouts:
        s = _serialize_payout(payout)
        sid = cast(int | None, payout.supplier_id)
        s['supplier_name'] = supplier_names.get(cast(int, sid), f'Supplier #{sid}') if sid else None
        result.append(s)
    return (result, total)

def get_pending_payouts(page: int=Query(1, ge=1), page_size: int=Query(20, ge=1, le=100), current_admin: User=Depends(require_admin), db: Session=Depends(get_db)) -> dict[str, Any]:
    """Return all pending payout batches and unbatched payouts for admin review.

    Pagination is applied independently to batches and unbatched payouts.
    """
    (batches, batch_total) = _load_pending_batches_with_items(db, page, page_size)
    (unbatched, payout_total) = _load_unbatched_payouts(db, page, page_size)
    logistics_payout_q = db.query(LogisticsPartnerPayout).filter(LogisticsPartnerPayout.status.in_(['pending', 'draft']))
    logistics_payout_total = logistics_payout_q.count()
    logistics_payouts = logistics_payout_q.order_by(LogisticsPartnerPayout.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    logistics_ids = {cast(int, lp.partner_id) for lp in logistics_payouts if lp.partner_id}
    logistics_names = _resolve_logistics_names(logistics_ids, db) if logistics_ids else {}
    unbatched_logistics = []
    for lp in logistics_payouts:
        pid = cast(int | None, lp.partner_id)
        unbatched_logistics.append({'id': cast(int, lp.id), 'partner_id': pid, 'partner_name': logistics_names.get(cast(int, pid), f'Partner #{pid}') if pid else None, 'amount': float(cast(Decimal, lp.amount or 0)), 'currency': cast(str | None, lp.currency) or 'OMR', 'status': cast(str | None, lp.status) or '', 'reference': cast(str | None, lp.reference), 'notes': cast(str | None, lp.notes), 'created_at': cast(Any, lp.created_at).isoformat() if getattr(lp, 'created_at', None) else None})
    total_amount = sum((b['total_amount'] for b in batches))
    total_items = sum((b['item_count'] for b in batches))
    return {'pending_batches': batches, 'unbatched_payouts': unbatched, 'unbatched_logistics_payouts': unbatched_logistics, 'summary': {'total_batches': batch_total, 'total_amount': round(total_amount, 2), 'total_items': total_items, 'pending_payouts_count': payout_total, 'pending_logistics_payouts_count': logistics_payout_total}, 'pagination': {'page': page, 'page_size': page_size}}

def approve_payout(payout_id: int, payload: ActionRequest | None=None, current_admin: User=Depends(require_admin), db: Session=Depends(get_db)) -> dict[str, Any]:
    """Approve an individual pending payout record."""
    payout = db.query(Payout).filter(Payout.id == payout_id).first()
    if not payout:
        raise HTTPException(status_code=404, detail='Payout not found')
    if payout.status not in ('pending', 'draft'):
        raise HTTPException(status_code=409, detail=f"Cannot approve payout in '{payout.status}' status.")
    payout.status = 'approved'
    if payload and payload.notes:
        payout.notes = (payout.notes or '') + f'\nApproved: {payload.notes}'
    db.commit()
    audit_log(db=db, action=AuditAction.PAYOUT_PROCESSED, user_id=current_admin.id, username=current_admin.username, user_role='admin', resource_type='payout', resource_id=payout_id, details={'action': 'approve', 'amount': float(cast(Decimal, payout.amount or 0))})
    return {'message': 'Payout approved', 'payout_id': payout_id, 'status': 'approved'}

def reject_payout(payout_id: int, payload: ActionRequest | None=None, current_admin: User=Depends(require_admin), db: Session=Depends(get_db)) -> dict[str, Any]:
    """Reject an individual pending payout record."""
    payout = db.query(Payout).filter(Payout.id == payout_id).first()
    if not payout:
        raise HTTPException(status_code=404, detail='Payout not found')
    if payout.status not in ('pending', 'draft', 'approved'):
        raise HTTPException(status_code=409, detail=f"Cannot reject payout in '{payout.status}' status.")
    payout.status = 'rejected'
    if payload and payload.notes:
        payout.notes = (payout.notes or '') + f'\nRejected: {payload.notes}'
    db.commit()
    audit_log(db=db, action=AuditAction.PAYOUT_PROCESSED, user_id=current_admin.id, username=current_admin.username, user_role='admin', resource_type='payout', resource_id=payout_id, details={'action': 'reject', 'amount': float(cast(Decimal, payout.amount or 0))})
    return {'message': 'Payout rejected', 'payout_id': payout_id, 'status': 'rejected'}

def approve_batch(batch_id: int, payload: ActionRequest | None=None, current_admin: User=Depends(require_admin), db: Session=Depends(get_db)) -> dict[str, Any]:
    """Approve a payout batch — moves it from draft ? approved."""
    batch = db.query(PayoutBatch).options(joinedload(PayoutBatch.items)).filter(PayoutBatch.id == batch_id).first()
    if not batch:
        raise HTTPException(status_code=404, detail='Payout batch not found')
    if batch.status not in ('draft', 'pending'):
        raise HTTPException(status_code=409, detail=f"Cannot approve batch in '{batch.status}' status. Only draft/pending batches can be approved.")
    now = utcnow()
    batch.status = 'approved'
    batch.approved_by = cast(int, current_admin.id)
    batch.notes = (batch.notes or '') + (f'\nApproved by admin #{current_admin.id} at {now.isoformat()}.' + (f' Notes: {payload.notes}' if payload and payload.notes else ''))
    for item in batch.items or []:
        item.status = 'approved'
    db.commit()
    audit_log(db=db, action=AuditAction.PAYOUT_PROCESSED, user_id=current_admin.id, username=current_admin.username, user_role='admin', resource_type='payout_batch', resource_id=batch_id, details={'action': 'approve', 'batch_number': batch.batch_number})
    return {'message': 'Batch approved', 'batch_id': batch_id, 'status': 'approved'}

def reject_batch(batch_id: int, payload: ActionRequest | None=None, current_admin: User=Depends(require_admin), db: Session=Depends(get_db)) -> dict[str, Any]:
    """Reject a payout batch — moves it from draft ? rejected."""
    batch = db.query(PayoutBatch).options(joinedload(PayoutBatch.items)).filter(PayoutBatch.id == batch_id).first()
    if not batch:
        raise HTTPException(status_code=404, detail='Payout batch not found')
    if batch.status not in ('draft', 'pending', 'approved'):
        raise HTTPException(status_code=409, detail=f"Cannot reject batch in '{batch.status}' status.")
    now = utcnow()
    old_status = batch.status
    batch.status = 'rejected'
    batch.notes = (batch.notes or '') + (f'\nRejected by admin #{current_admin.id} at {now.isoformat()}.' + (f' Reason: {payload.notes}' if payload and payload.notes else ''))
    for item in batch.items or []:
        item.status = 'pending'
    db.commit()
    audit_log(db=db, action=AuditAction.PAYOUT_PROCESSED, user_id=current_admin.id, username=current_admin.username, user_role='admin', resource_type='payout_batch', resource_id=batch_id, details={'action': 'reject', 'batch_number': batch.batch_number, 'previous_status': old_status})
    return {'message': 'Batch rejected', 'batch_id': batch_id, 'status': 'rejected'}

def dispatch_batch(batch_id: int, payload: ActionRequest | None=None, current_admin: User=Depends(require_admin), db: Session=Depends(get_db)) -> dict[str, Any]:
    """Dispatch (mark as paid) an approved payout batch.

    Updates the batch status to dispatched, marks all batch items as paid,
    and updates the underlying Payout / LogisticsPartnerPayout records to paid.
    """
    batch = db.query(PayoutBatch).options(joinedload(PayoutBatch.items)).filter(PayoutBatch.id == batch_id).first()
    if not batch:
        raise HTTPException(status_code=404, detail='Payout batch not found')
    if batch.status != 'approved':
        raise HTTPException(status_code=409, detail=f"Cannot dispatch batch in '{batch.status}' status. Only approved batches can be dispatched.")
    now = utcnow()
    batch.status = 'dispatched'
    batch.dispatched_at = now
    batch.notes = (batch.notes or '') + (f'\nDispatched by admin #{current_admin.id} at {now.isoformat()}.' + (f' Notes: {payload.notes}' if payload and payload.notes else ''))
    supplier_payout_ids: list[int] = []
    logistics_payout_ids: list[int] = []
    for item in batch.items or []:
        item.status = 'paid'
        etype = cast(str, item.entity_type)
        eid = cast(int, item.entity_id)
        if etype == 'supplier':
            supplier_payout_ids.append(eid)
        elif etype == 'logistics':
            logistics_payout_ids.append(eid)
    if supplier_payout_ids:
        updated = db.query(Payout).filter(Payout.supplier_id.in_(supplier_payout_ids), Payout.status.in_(['pending', 'approved'])).update({'status': 'paid', 'processed_at': now}, synchronize_session=False)
    if logistics_payout_ids:
        db.query(LogisticsPartnerPayout).filter(LogisticsPartnerPayout.partner_id.in_(logistics_payout_ids), LogisticsPartnerPayout.status.in_(['pending', 'approved'])).update({'status': 'paid', 'processed_at': now}, synchronize_session=False)
    db.commit()
    audit_log(db=db, action=AuditAction.PAYOUT_PROCESSED, user_id=current_admin.id, username=current_admin.username, user_role='admin', resource_type='payout_batch', resource_id=batch_id, details={'action': 'dispatch', 'batch_number': batch.batch_number})
    return {'message': 'Batch dispatched', 'batch_id': batch_id, 'status': 'dispatched'}


