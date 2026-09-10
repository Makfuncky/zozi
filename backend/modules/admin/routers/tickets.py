"""Admin support tickets router — thin HTTP layer delegating to comms domain services.

Mounted at root (no prefix) so the frontend's ``/admin/tickets/*`` path resolves
directly. The admin guard middleware (which already protects ``/admin/*``)
enforces admin-role authentication before this router is reached.

Per Law 2: routers are THIN — only auth context, require_feature, ONE service
call, and serialization. All DB queries and payload shape logic live in the
``domains.comms.services.tickets`` module.
"""
from __future__ import annotations
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body
from sqlalchemy.orm import Session

from infrastructure.database.database import get_db
from infrastructure.security.dependencies import require_admin
from rbac.dependencies import require_feature
from domains.comms.services.tickets.tickets_service import (
    get_ticket_by_id,
    get_ticket_messages,
    get_ticket_with_details,
    create_ticket_reply,
    update_ticket_status,
    list_tickets,
    build_ticket_payload,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["admin-tickets"])


@router.get("/admin/tickets")
def admin_list_tickets(
    _: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    status_filter: Optional[str] = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    _rf_gate: None = Depends(require_feature("support.read")),
):
    items = list_tickets(db=db, status=status_filter, limit=page_size)
    out = []
    for t in items:
        first_msg = next(iter(getattr(t, "messages", []) or []), None)
        out.append({
            "id": t.id,
            "user_id": t.user_id,
            "subject": t.subject,
            "message": getattr(first_msg, "message", "") if first_msg else "",
            "status": t.status,
            "priority": t.priority,
            "created_at": t.created_at.isoformat() if t.created_at else None,
            "updated_at": t.updated_at.isoformat() if t.updated_at else None,
        })
    return {"data": out, "total": len(out), "page": page, "page_size": page_size}


@router.get("/admin/tickets/{ticket_id}")
def admin_get_ticket(
    ticket_id: int = Path(...),
    _: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("support.read")),
):
    ticket = get_ticket_with_details(db, ticket_id) or get_ticket_by_id(db, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    messages = getattr(ticket, "messages", []) or get_ticket_messages(db, ticket_id) or []
    return build_ticket_payload(db, ticket, messages)


@router.post("/admin/tickets/{ticket_id}/reply")
def admin_reply_to_ticket(
    ticket_id: int = Path(...),
    payload: dict = Body(...),
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("support.reply")),
):
    ticket = get_ticket_by_id(db, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    message = str(payload.get("message") or payload.get("body") or "").strip()
    if len(message) < 1:
        raise HTTPException(status_code=422, detail="message is required")
    sender_id = current_user.get("id") if isinstance(current_user, dict) else 0
    create_ticket_reply(
        db=db,
        ticket_id=ticket_id,
        sender_id=sender_id,
        message=message,
        is_admin=True,
    )
    updated = get_ticket_with_details(db, ticket_id) or ticket
    messages = getattr(updated, "messages", []) or get_ticket_messages(db, ticket_id) or []
    return build_ticket_payload(db, updated, messages)


@router.put("/admin/tickets/{ticket_id}/status")
def admin_update_ticket_status(
    ticket_id: int = Path(...),
    payload: dict = Body(...),
    _: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("support.update")),
):
    new_status = str(payload.get("status") or "").strip().lower()
    allowed = {"open", "pending", "in_progress", "resolved", "closed"}
    if new_status not in allowed:
        raise HTTPException(
            status_code=422,
            detail=f"status must be one of: {', '.join(sorted(allowed))}",
        )
    ticket = get_ticket_by_id(db, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    update_ticket_status(db, ticket, new_status)
    updated = get_ticket_with_details(db, ticket_id) or ticket
    messages = getattr(updated, "messages", []) or get_ticket_messages(db, ticket_id) or []
    return build_ticket_payload(db, updated, messages)
