"""Cash-management write service (W1 remediation).

``routers/cash_management.py`` used to own the transaction boundary for every
finance mutation (15 inline ``db.commit()`` calls). Per the layer contract only
``services/**`` may own DB transactions, so each admin write flow gets a
function here that:

    1. calls the underlying domain service (``services.treasury.cash_management_service``,
       ``services.treasury.payout_dispatch_service``, ``services.supplier.supplier_badge_service``),
    2. translates domain ``ValueError``s into ``HTTPException``s, and
    3. commits.

Every function takes the SQLAlchemy ``Session`` as its first positional
argument. Callers (controller/router) stay read-only orchestration.
"""
from __future__ import annotations

from typing import Any, Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from domains.finance.services.treasury.cash_management_service import auto_reconcile_bank_transactions as _auto_reconcile_bank_transactions
from domains.finance.services.treasury.cash_management_service import flag_bank_transaction as _flag_bank_transaction
from domains.finance.services.treasury.cash_management_service import import_bank_transactions as _import_bank_transactions
from domains.finance.services.treasury.cash_management_service import log_bank_transaction as _log_bank_transaction
from domains.finance.services.treasury.cash_management_service import process_logistics_payout_batch as _process_logistics_payout_batch
from domains.finance.services.treasury.cash_management_service import process_supplier_payout_batch as _process_supplier_payout_batch
from domains.finance.services.treasury.cash_management_service import reconcile_bank_transaction as _reconcile_bank_transaction
from domains.finance.services.treasury.cash_management_service import record_cod_remittance as _record_cod_remittance
from domains.finance.services.treasury.cash_management_service import record_vat_remittance as _record_vat_remittance
from domains.finance.services.treasury.cash_management_service import reject_cod_remittance_receipt as _reject_cod_remittance_receipt
from domains.finance.services.treasury.cash_management_service import resolve_bank_transaction_exception as _resolve_bank_transaction_exception
from domains.finance.services.treasury.cash_management_service import serialize_cod_remittance_receipt as _serialize_cod_remittance_receipt
from domains.finance.services.treasury.cash_management_service import upsert_finance_bank_settings as _upsert_finance_bank_settings
from domains.finance.services.treasury.cash_management_service import verify_cod_remittance_receipt as _verify_cod_remittance_receipt
from domains.finance.services.payouts.payout_dispatch_service import dispatch_transfer_batch_with_audit as _dispatch_transfer_batch_with_audit
from kernel.money import to_decimal
import structlog
logger = structlog.get_logger(__name__)


def _receipt_review_error(exc: ValueError) -> HTTPException:
    detail = str(exc)
    status_code = 404 if "not found" in detail.lower() else 400
    return HTTPException(status_code=status_code, detail=detail)


# ── Badge billing ─────────────────────────────────────────────────────────────

def record_badge_billing_payment(
    db: Session,
    *,
    billing_id: int,
    payment_method: str,
    current_admin: dict,
    transaction_ref: Optional[str] = None,
    notes: Optional[str] = None,
) -> Any:
    """Record a badge billing payment and commit."""
    from domains.suppliers.services.supplier_badge_service import record_badge_billing_payment as _impl

    record = _impl(
        billing_id=billing_id,
        payment_method=payment_method,
        current_admin=current_admin,
        db=db,
        transaction_ref=transaction_ref,
        notes=notes,
    )
    db.commit()
    return record


# ── Bank settings ─────────────────────────────────────────────────────────────

def upsert_bank_settings(db: Session, *, data: dict, admin_id: Optional[int]) -> Any:
    """Create/update the primary finance bank account and commit."""
    record = _upsert_finance_bank_settings(data=data, admin_id=admin_id, db=db)
    db.commit()
    return record


# ── VAT ───────────────────────────────────────────────────────────────────────

def record_vat_remittance(db: Session, *, data: dict, admin_id: Optional[int]) -> Any:
    """Record a VAT remittance and commit."""
    record = _record_vat_remittance(
        period_start=data["period_start"],
        period_end=data["period_end"],
        amount_remitted=to_decimal(data["amount_remitted"]),
        admin_id=admin_id,
        db=db,
        notes=data.get("notes"),
        transaction_ref=data.get("transaction_ref"),
        remitted_at=data.get("remitted_at"),
    )
    db.commit()
    return record


# ── Bank transactions ─────────────────────────────────────────────────────────

def create_bank_transaction(db: Session, *, data: dict) -> Any:
    """Manually create a bank transaction entry and commit."""
    txn = _log_bank_transaction(
        source=data["source"],
        transaction_type=data["transaction_type"],
        category=data["category"],
        amount=to_decimal(data["amount"]),
        db=db,
        currency=data.get("currency", "OMR"),
        order_id=data.get("linked_order_id"),
        supplier_id=data.get("linked_supplier_id"),
        logistics_id=data.get("linked_logistics_id"),
        payout_id=data.get("linked_payout_id"),
        refund_id=data.get("linked_refund_id"),
        description=data.get("description"),
        transaction_ref=data.get("transaction_ref"),
        transaction_date=data.get("transaction_date"),
    )
    db.commit()
    return txn


def import_bank_transactions(
    db: Session,
    *,
    items: list[dict],
    admin_id: Optional[int],
    auto_reconcile: bool = False,
) -> dict:
    """Import a bank statement batch and commit."""
    result = _import_bank_transactions(
        items,
        db,
        admin_id=admin_id,
        auto_reconcile=auto_reconcile,
    )
    db.commit()
    return result


def reconcile_transaction(db: Session, *, txn_id: int, admin_id: Any) -> Any:
    """Mark a bank transaction reconciled and commit."""
    try:
        txn = _reconcile_bank_transaction(txn_id, admin_id, db)
    except ValueError as exc:
        logger.exception("reconcile_transaction_failed", error=str(exc))
        raise HTTPException(status_code=404, detail=str(exc))
    db.commit()
    return txn


def flag_transaction(db: Session, *, txn_id: int, reason: str) -> Any:
    """Flag a bank transaction for manual review and commit."""
    try:
        txn = _flag_bank_transaction(txn_id, reason, db)
    except ValueError as exc:
        logger.exception("flag_transaction_failed", error=str(exc))
        raise HTTPException(status_code=404, detail=str(exc))
    db.commit()
    return txn


def resolve_transaction_exception(
    db: Session,
    *,
    txn_id: int,
    data: dict,
    admin_id: Optional[int],
) -> Any:
    """Resolve a flagged/unmatched bank transaction and commit."""
    try:
        txn = _resolve_bank_transaction_exception(
            txn_id,
            db,
            admin_id=admin_id,
            order_id=data.get("linked_order_id"),
            supplier_id=data.get("linked_supplier_id"),
            logistics_id=data.get("linked_logistics_id"),
            payout_id=data.get("linked_payout_id"),
            refund_id=data.get("linked_refund_id"),
            resolution_note=data.get("resolution_note"),
            mark_reconciled=data.get("mark_reconciled", True),
            clear_flag=data.get("clear_flag", True),
        )
    except ValueError as exc:
        logger.exception("resolve_transaction_exception_failed", error=str(exc))
        raise HTTPException(status_code=404, detail=str(exc))
    db.commit()
    return txn


def auto_reconcile_transactions(
    db: Session,
    *,
    admin_id: Any,
    limit: int = 100,
    source: Optional[str] = None,
    category: Optional[str] = None,
) -> dict:
    """Run the auto-reconciliation sweep and commit."""
    result = _auto_reconcile_bank_transactions(
        admin_id,
        db,
        limit=limit,
        source=source,
        category=category,
    )
    db.commit()
    return result


# ── Payouts ───────────────────────────────────────────────────────────────────

def trigger_supplier_payouts(db: Session, *, settlement_ids: Optional[list[int]] = None) -> list[dict]:
    """Process the supplier payout batch and commit."""
    results = _process_supplier_payout_batch(db, settlement_ids=settlement_ids)
    db.commit()
    return results


def trigger_logistics_payouts(db: Session, *, settlement_ids: Optional[list[int]] = None) -> list[dict]:
    """Process the logistics payout batch and commit."""
    results = _process_logistics_payout_batch(db, settlement_ids=settlement_ids)
    db.commit()
    return results


def dispatch_transfer_batch(
    db: Session,
    *,
    kind: str,
    admin_user: dict,
    provider: Optional[str] = None,
    dry_run: bool = True,
) -> dict[str, Any]:
    """Dispatch a payout transfer batch (with audit) and commit."""
    result = _dispatch_transfer_batch_with_audit(
        kind,
        admin_user,
        db,
        provider=provider,
        dry_run=dry_run,
    )
    db.commit()
    return result


# ── COD remittance ────────────────────────────────────────────────────────────

def record_cod_remittance(db: Session, *, settlement_id: int, amount: float, admin_id: Any) -> Any:
    """Record COD cash remittance from a logistics partner and commit."""
    if amount <= 0:
        raise HTTPException(status_code=400, detail="Remittance amount must be positive")
    try:
        settlement = _record_cod_remittance(settlement_id, amount, admin_id, db)
    except ValueError as exc:
        logger.exception("record_cod_remittance_failed", error=str(exc))
        raise HTTPException(status_code=404, detail=str(exc))
    db.commit()
    return settlement


def verify_cod_remittance_receipt(
    db: Session,
    *,
    receipt_id: int,
    admin_id: Any,
    note: Optional[str] = None,
) -> dict[str, Any]:
    """Verify a COD remittance receipt, commit, and return its serialized form."""
    try:
        receipt = _verify_cod_remittance_receipt(receipt_id, admin_id, db, review_note=note)
    except ValueError as exc:
        logger.exception("verify_cod_remittance_receipt_failed", error=str(exc))
        raise _receipt_review_error(exc)
    db.commit()
    return _serialize_cod_remittance_receipt(receipt, db)


def reject_cod_remittance_receipt(
    db: Session,
    *,
    receipt_id: int,
    admin_id: Any,
    note: str,
) -> dict[str, Any]:
    """Reject a COD remittance receipt, commit, and return its serialized form."""
    try:
        receipt = _reject_cod_remittance_receipt(receipt_id, admin_id, db, review_note=note)
    except ValueError as exc:
        logger.exception("reject_cod_remittance_receipt_failed", error=str(exc))
        raise _receipt_review_error(exc)
    db.commit()
    return _serialize_cod_remittance_receipt(receipt, db)
