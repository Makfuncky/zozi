"Supplier payout controller.\n\nRead/write logic for a supplier's own payout records. Previously inline in\n``routers.supplier_payouts_pay`` (CG1: ``Payout`` instantiation in router,\nW1: ``db.add``/``db.commit`` in router). Routers now delegate here.\n"
from __future__ import annotations
from fastapi import HTTPException
from services.db_read import query as db_read_query, execute as db_read_execute
from sqlalchemy.orm import Session
from models import Payout, SupplierProfile
from services.write_helpers import commit_and_refresh

def list_supplier_payouts(current_user, db: Session) -> list[Payout]:
    """Return all payouts for the calling supplier's profile."""
    supplier = db_read_query(db, SupplierProfile).filter(SupplierProfile.user_id == current_user.id).first()
    if not supplier:
        raise HTTPException(404)
    return db_read_query(db, Payout).filter(Payout.supplier_id == supplier.id).order_by(Payout.created_at.desc()).all()

def request_supplier_payout(current_user, payload: dict, db: Session) -> dict:
    """Create a supplier-initiated payout request."""
    supplier = db_read_query(db, SupplierProfile).filter(SupplierProfile.user_id == current_user.id).first()
    if not supplier:
        raise HTTPException(404, 'Supplier profile not found')
    amount = payload.get('amount')
    if not amount or float(amount) <= 0:
        raise HTTPException(400, 'A positive payout amount is required')
    payout = Payout(supplier_id=supplier.id, amount=float(amount), method=payload.get('method', 'bank'), notes=payload.get('notes', 'Supplier-initiated payout request'), status='pending')
    payout = commit_and_refresh(db, payout)
    return {'status': 'success', 'payout': {'id': payout.id, 'amount': float(payout.amount), 'status': payout.status}}
