"""Thin write controller for cash management (W1 remediation).

The finance router previously owned the transaction boundary (``db.commit()``)
for every admin mutation. Those commits now live in
``services.finance.cash_management_write_service``; this controller only
orchestrates: it forwards arguments, reuses the existing read/serialization
helpers of ``controllers.treasury.cash_management_controller``, and lets service-raised
``HTTPException``s propagate. It performs **no** DB writes.
"""
from __future__ import annotations

from typing import Any, Optional

from sqlalchemy.orm import Session

from modules.treasury.routers.cash_management_controller import (
    _serialize_finance_bank_settings,
    admin_queue_dispatch_transfer_batch,
)
from domains.finance.services import cash_management_write_service as write_service
import structlog
from routers.generated.auto_router import post, put, delete

logger = structlog.get_logger(__name__)


# ── Badge billing ─────────────────────────────────────────────────────────────

@post("/api/v1/admin/treasury/badge-billing/{billing_id}/payments", deps=["admin", "db"], tags=["treasury"])
def record_badge_billing_payment(
    billing_id: int,
    payment_method: str,
    current_user: dict,
    db: Session,
    transaction_ref: Optional[str] = None,
    notes: Optional[str] = None,
) -> Any:
    return write_service.record_badge_billing_payment(
        db,
        billing_id=billing_id,
        payment_method=payment_method,
        current_admin=current_user,
        transaction_ref=transaction_ref,
        notes=notes,
    )


# ── Bank settings ─────────────────────────────────────────────────────────────

@put("/api/v1/admin/treasury/bank-settings", deps=["admin", "db"], tags=["treasury"])
def upsert_bank_settings(data: dict, current_user: dict, db: Session) -> dict[str, Any]:
    record = write_service.upsert_bank_settings(db, data=data, admin_id=current_user.get("id"))
    return _serialize_finance_bank_settings(record)


# ── VAT ───────────────────────────────────────────────────────────────────────

@post("/api/v1/admin/treasury/vat-remittances", deps=["admin", "db"], tags=["treasury"])
def record_vat_remittance(data: dict, current_user: dict, db: Session) -> Any:
    return write_service.record_vat_remittance(db, data=data, admin_id=current_user.get("id"))


# ── Bank transactions ─────────────────────────────────────────────────────────

@post("/api/v1/admin/treasury/bank-transactions", deps=["admin", "db"], tags=["treasury"])
def create_bank_transaction(data: dict, current_user: dict, db: Session) -> Any:
    return write_service.create_bank_transaction(db, data=data)


@post("/api/v1/admin/treasury/bank-transactions/import", deps=["admin", "db"], tags=["treasury"])
def import_bank_transactions(
    items: list[dict],
    current_user: dict,
    db: Session,
    *,
    auto_reconcile: bool = False,
) -> dict:
    return write_service.import_bank_transactions(
        db,
        items=items,
        admin_id=current_user.get("id"),
        auto_reconcile=auto_reconcile,
    )


@post("/api/v1/admin/treasury/bank-transactions/{txn_id}/reconcile", deps=["admin", "db"], tags=["treasury"])
def reconcile_transaction(txn_id: int, current_user: dict, db: Session) -> Any:
    return write_service.reconcile_transaction(db, txn_id=txn_id, admin_id=current_user["id"])


@post("/api/v1/admin/treasury/bank-transactions/{txn_id}/flag", deps=["admin", "db"], tags=["treasury"])
def flag_transaction(txn_id: int, reason: str, current_user: dict, db: Session) -> Any:
    return write_service.flag_transaction(db, txn_id=txn_id, reason=reason)


@post("/api/v1/admin/treasury/bank-transactions/{txn_id}/resolve", deps=["admin", "db"], tags=["treasury"])
def resolve_transaction_exception(
    txn_id: int,
    data: dict,
    current_user: dict,
    db: Session,
) -> Any:
    return write_service.resolve_transaction_exception(
        db,
        txn_id=txn_id,
        data=data,
        admin_id=current_user.get("id"),
    )


@post("/api/v1/admin/treasury/bank-transactions/auto-reconcile", deps=["admin", "db"], tags=["treasury"])
def auto_reconcile_transactions(
    current_user: dict,
    db: Session,
    *,
    limit: int = 100,
    source: Optional[str] = None,
    category: Optional[str] = None,
) -> dict:
    return write_service.auto_reconcile_transactions(
        db,
        admin_id=current_user["id"],
        limit=limit,
        source=source,
        category=category,
    )


# ── Payouts ───────────────────────────────────────────────────────────────────

@post("/api/v1/admin/treasury/payouts/supplier", deps=["admin", "db"], tags=["treasury"])
def trigger_supplier_payouts(current_user: dict, db: Session, settlement_ids: Optional[list[int]] = None) -> list[dict]:
    return write_service.trigger_supplier_payouts(db, settlement_ids=settlement_ids)


@post("/api/v1/admin/treasury/payouts/logistics", deps=["admin", "db"], tags=["treasury"])
def trigger_logistics_payouts(current_user: dict, db: Session, settlement_ids: Optional[list[int]] = None) -> list[dict]:
    return write_service.trigger_logistics_payouts(db, settlement_ids=settlement_ids)


@post("/api/v1/admin/treasury/transfers/dispatch", deps=["admin", "db"], tags=["treasury"])
def dispatch_transfer_batch(
    kind: str,
    current_user: dict,
    db: Session,
    *,
    provider: Optional[str] = None,
    dry_run: bool = True,
) -> dict[str, Any]:
    return write_service.dispatch_transfer_batch(
        db,
        kind=kind,
        admin_user=current_user,
        provider=provider,
        dry_run=dry_run,
    )


@post("/api/v1/admin/treasury/transfers/dispatch/queue", deps=["admin"], tags=["treasury"])
def queue_dispatch_transfer_batch(
    kind: str,
    current_user: dict,
    *,
    provider: Optional[str] = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Background dispatch — enqueued job, no request-scoped DB work."""
    return admin_queue_dispatch_transfer_batch(
        kind,
        current_user,
        provider=provider,
        dry_run=dry_run,
    )


# ── COD remittance ────────────────────────────────────────────────────────────

@post("/api/v1/admin/treasury/cod/{settlement_id}/remittance", deps=["admin", "db"], tags=["treasury"])
def record_cod_remittance(settlement_id: int, amount: float, current_user: dict, db: Session) -> Any:
    return write_service.record_cod_remittance(
        db,
        settlement_id=settlement_id,
        amount=amount,
        admin_id=current_user["id"],
    )


@post("/api/v1/admin/treasury/cod/receipts/{receipt_id}/verify", deps=["admin", "db"], tags=["treasury"])
def verify_cod_remittance_receipt(
    receipt_id: int,
    current_user: dict,
    db: Session,
    note: Optional[str] = None,
) -> dict[str, Any]:
    return write_service.verify_cod_remittance_receipt(
        db,
        receipt_id=receipt_id,
        admin_id=current_user["id"],
        note=note,
    )


@post("/api/v1/admin/treasury/cod/receipts/{receipt_id}/reject", deps=["admin", "db"], tags=["treasury"])
def reject_cod_remittance_receipt(
    receipt_id: int,
    current_user: dict,
    db: Session,
    note: str,
) -> dict[str, Any]:
    return write_service.reject_cod_remittance_receipt(
        db,
        receipt_id=receipt_id,
        admin_id=current_user["id"],
        note=note,
    )
