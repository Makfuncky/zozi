"""
Admin Payout Approval Router
=============================
Endpoints for the Admin Payout Approval Dashboard — lists all pending payouts
and batches with supplier/logistics context, and provides an approve/reject/dispatch
workflow.

Routes (mounted at /admin/payout-approval):
  GET  /pending                       → pending payouts + batches with enrichment
  POST /payouts/{payout_id}/approve   → approve an individual (unbatched) payout
  POST /payouts/{payout_id}/reject    → reject an individual payout
  POST /batches/{batch_id}/approve    → approve a batch (draft→approved)
  POST /batches/{batch_id}/reject     → reject a batch
  POST /batches/{batch_id}/dispatch   → mark batch + its payouts as paid
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from data.db import get_db
from sqlalchemy.orm import Session

from data.models import User
from utils.dependencies import require_admin

from services.treasury.treasury_router_service import (
    get_pending_payouts as get_pending_payouts_svc,
    approve_payout as approve_payout_svc,
    reject_payout as reject_payout_svc,
    approve_batch as approve_batch_svc,
    reject_batch as reject_batch_svc,
    dispatch_batch as dispatch_batch_svc,
)

router = APIRouter()


class ActionRequest(BaseModel):
    """Optional note payload attached to an approve/reject/dispatch action."""

    notes: str | None = None


@router.get("/pending")
def get_pending_payouts(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Return all pending payout batches and unbatched payouts for admin review."""
    return get_pending_payouts_svc(db, page, page_size)


@router.post("/payouts/{payout_id}/approve")
def approve_payout(
    payout_id: int,
    payload: ActionRequest | None = None,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Approve an individual pending payout record."""
    return approve_payout_svc(
        db=db,
        payout_id=payout_id,
        notes=payload.notes if payload else None,
        current_admin=current_admin,
    )


@router.post("/payouts/{payout_id}/reject")
def reject_payout(
    payout_id: int,
    payload: ActionRequest | None = None,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Reject an individual pending payout record."""
    return reject_payout_svc(
        db=db,
        payout_id=payout_id,
        notes=payload.notes if payload else None,
        current_admin=current_admin,
    )


@router.post("/batches/{batch_id}/approve")
def approve_batch(
    batch_id: int,
    payload: ActionRequest | None = None,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Approve a payout batch — moves it from draft → approved."""
    return approve_batch_svc(
        db=db,
        batch_id=batch_id,
        notes=payload.notes if payload else None,
        current_admin=current_admin,
    )


@router.post("/batches/{batch_id}/reject")
def reject_batch(
    batch_id: int,
    payload: ActionRequest | None = None,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Reject a payout batch — moves it from draft → rejected."""
    return reject_batch_svc(
        db=db,
        batch_id=batch_id,
        notes=payload.notes if payload else None,
        current_admin=current_admin,
    )


@router.post("/batches/{batch_id}/dispatch")
def dispatch_batch(
    batch_id: int,
    payload: ActionRequest | None = None,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Dispatch (mark as paid) an approved payout batch."""
    return dispatch_batch_svc(
        db=db,
        batch_id=batch_id,
        notes=payload.notes if payload else None,
        current_admin=current_admin,
    )