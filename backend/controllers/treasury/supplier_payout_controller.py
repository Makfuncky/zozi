"""Supplier payout controller.

Thin orchestration layer. Delegates all persistence to
services.treasury.payout_approval_write_service and only enforces read scoping
by the calling supplier. It must not call db.add/commit or write_helpers.
"""
from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy.orm import Session
from models import Payout
from services.treasury.payout_approval_write_service import request_supplier_payout as _request_supplier_payout
from services.treasury.payout_read_service import list_supplier_payouts as _list_supplier_payouts


def list_supplier_payouts(current_user, db: Session) -> list[Payout]:
    return _list_supplier_payouts(current_user, db)


def request_supplier_payout(current_user, payload: dict, db: Session) -> dict:
    """Create a supplier-initiated payout request."""
    return _request_supplier_payout(db, current_user, payload)
