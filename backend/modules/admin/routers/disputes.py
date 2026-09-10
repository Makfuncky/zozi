"""Admin disputes router — thin proxy at /admin/disputes for the supplier disputes UI.

The /admin/disputes Next.js page calls:
  GET    /admin/disputes           — list all disputes (with status/priority filters)
  PATCH  /admin/disputes/{id}      — update a dispute (status, priority, resolution_notes)
  POST   /admin/disputes/bulk      — bulk update status/priority

These wrap domains.suppliers.services.disputes_service admin functions.
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query, Body
from sqlalchemy.orm import Session

from infrastructure.database.database import get_db
from infrastructure.security.dependencies import require_admin
from rbac.dependencies import require_feature

router = APIRouter(tags=["admin", "disputes"])


@router.get("/admin/disputes", status_code=200)
def list_admin_disputes_route(
    status: Optional[str] = Query(None, description="Filter by status: open|under_review|resolved|rejected|closed"),
    priority: Optional[str] = Query(None, description="Filter by priority: low|medium|high|urgent"),
    type: Optional[str] = Query(None, description="Filter by dispute_type (return|payment|quality|other)"),
    supplier_id: Optional[int] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("moderation.suppliers")),
):
    """List all supplier disputes (admin view, cross-supplier)."""
    from domains.suppliers.services.disputes_service import list_admin_disputes

    limit = page_size
    offset = (page - 1) * page_size
    result = list_admin_disputes(
        db,
        status=status,
        priority=priority,
        supplier_id=supplier_id,
        limit=limit,
        offset=offset,
    )

    if type:
        wanted = type.strip().lower()
        result["data"] = [d for d in result.get("data", []) if (d.get("dispute_type") or "").lower() == wanted]

    return result["data"]


@router.patch("/admin/disputes/{dispute_id}", status_code=200)
def patch_admin_dispute_route(
    dispute_id: int,
    payload: dict = Body(...),
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("moderation.suppliers")),
):
    """Update a dispute (status, priority, resolution_notes, admin_notes)."""
    from domains.suppliers.services.disputes_service import update_admin_dispute

    return update_admin_dispute(dispute_id, payload, current_user, db)


@router.post("/admin/disputes/bulk", status_code=200)
def bulk_update_admin_disputes_route(
    body: dict = Body(...),
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("moderation.suppliers")),
):
    """Bulk update dispute status or priority.

    Body shape (from frontend):
      { "dispute_ids": [int], "status": str?, "priority": str? }

    Internally calls domains.suppliers.services.disputes_service.bulk_update_admin_disputes
    which expects (ids, action, value, admin, db).
    """
    from domains.suppliers.services.disputes_service import bulk_update_admin_disputes

    dispute_ids = body.get("dispute_ids") or []
    if not isinstance(dispute_ids, list) or not dispute_ids:
        from fastapi import HTTPException
        raise HTTPException(status_code=422, detail="dispute_ids must be a non-empty list")

    if body.get("status"):
        return bulk_update_admin_disputes(
            dispute_ids, "set_status", body["status"], current_user, db
        )
    if body.get("priority"):
        return bulk_update_admin_disputes(
            dispute_ids, "set_priority", body["priority"], current_user, db
        )
    from fastapi import HTTPException
    raise HTTPException(status_code=422, detail="Either status or priority must be provided")
