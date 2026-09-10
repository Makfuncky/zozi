"""Customer-initiated return helpers — pure service layer so module routers
stay thin (Law 2: routers do not write to the DB directly)."""
from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy.orm import Session

from domains.orders.models.order_entities import ReturnRequest


def cancel_return_request(db: Session, *, return_id: int, user_id: int) -> ReturnRequest:
    """Cancel a return request owned by ``user_id``.

    Only allowed when the return is still in the ``requested`` (or pending)
    state. Raises ``HTTPException(404/403/400)`` on policy violations.
    """
    req = db.query(ReturnRequest).filter(ReturnRequest.id == return_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Return request not found")
    if int(getattr(req, "user_id", 0) or 0) != int(user_id):
        raise HTTPException(status_code=403, detail="Not allowed")
    current_status = getattr(req, "status_code", None)
    if current_status not in ("requested", "pending", None):
        raise HTTPException(
            status_code=400,
            detail=f"Return cannot be cancelled in status '{current_status}'",
        )
    req.status_code = "cancelled"
    db.commit()
    db.refresh(req)
    return req
