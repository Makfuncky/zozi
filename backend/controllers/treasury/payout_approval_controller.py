"""Admin payout-approval controller.

Thin orchestration layer between ``routers/payout_approval.py`` and
``services.treasury.payout_approval_write_service``. Holds no DB writes of its
own (audit rule W1) and lets ``HTTPException`` raised by the service propagate
untouched so the router keeps returning the same status codes.
"""
from __future__ import annotations

from typing import Any

from routers.generated.auto_router import post
from services.treasury import payout_approval_write_service as svc
import structlog
logger = structlog.get_logger(__name__)


def _notes(payload: Any) -> str | None:
    """Extract the optional free-text note from the request body."""
    return payload.notes if payload and payload.notes else None


def _actor(current_user: Any) -> tuple[int | None, str | None]:
    """Return (id, username) for the acting admin."""
    return getattr(current_user, "id", None), getattr(current_user, "username", None)


@post("/api/v1/admin/payouts/{payout_id}/approve", deps=["admin", "db"], tags=["treasury-payouts"])
def approve_payout(payout_id: int, payload: Any, current_user: Any, db) -> dict[str, Any]:
    actor_id, actor_username = _actor(current_user)
    return svc.approve_payout(
        db, payout_id, _notes(payload), actor_id=actor_id, actor_username=actor_username
    )


@post("/api/v1/admin/payouts/{payout_id}/reject", deps=["admin", "db"], tags=["treasury-payouts"])
def reject_payout(payout_id: int, payload: Any, current_user: Any, db) -> dict[str, Any]:
    actor_id, actor_username = _actor(current_user)
    return svc.reject_payout(
        db, payout_id, _notes(payload), actor_id=actor_id, actor_username=actor_username
    )


@post("/api/v1/admin/batches/{batch_id}/approve", deps=["admin", "db"], tags=["treasury-payouts"])
def approve_batch(batch_id: int, payload: Any, current_user: Any, db) -> dict[str, Any]:
    actor_id, actor_username = _actor(current_user)
    return svc.approve_batch(
        db, batch_id, _notes(payload), actor_id=actor_id, actor_username=actor_username
    )


@post("/api/v1/admin/batches/{batch_id}/reject", deps=["admin", "db"], tags=["treasury-payouts"])
def reject_batch(batch_id: int, payload: Any, current_user: Any, db) -> dict[str, Any]:
    actor_id, actor_username = _actor(current_user)
    return svc.reject_batch(
        db, batch_id, _notes(payload), actor_id=actor_id, actor_username=actor_username
    )


@post("/api/v1/admin/batches/{batch_id}/dispatch", deps=["admin", "db"], tags=["treasury-payouts"])
def dispatch_batch(batch_id: int, payload: Any, current_user: Any, db) -> dict[str, Any]:
    actor_id, actor_username = _actor(current_user)
    return svc.dispatch_batch(
        db, batch_id, _notes(payload), actor_id=actor_id, actor_username=actor_username
    )


def update_payout_status_by_ids(payout_ids: list[int], status: str, db) -> None:
    """Bulk status maintenance for specific Payout rows (caller owns the commit)."""
    svc.update_payout_status_by_ids(db, payout_ids, status)
