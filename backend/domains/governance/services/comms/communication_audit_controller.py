"""controllers.comms.communication_audit_controller (CONTROLLERS layer).

Wraps ``services.comms.communication_audit`` and exposes the communication
audit endpoints. The HTTP contract is declared with ``infrastructure.routing.route_contract``
decorators so ``routers/generated/auto_router.py`` can auto-generate the thin
router — the previous hand-written ``routers/audit.py`` only instantiated the
service and passed query params through, which is controller-level
orchestration that now lives here.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from infrastructure.routing.route_contract import get

from domains.comms.services.admin.communication_audit import get_communication_audit_service

@get("/audit", deps=["db"], query=["user_id", "entity_type", "entity_id", "action", "limit", "offset"], tags=["communication-audit"])
def get_audit_trail(
    user_id: Optional[int] = None,
    entity_type: Optional[str] = None,
    entity_id: Optional[int] = None,
    action: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = None,
):
    """Return the communication audit trail filtered by the supplied criteria."""
    service = get_communication_audit_service(db)
    return service.get_audit_trail(
        user_id=user_id,
        entity_type=entity_type,
        entity_id=entity_id,
        action=action,
        limit=limit,
        offset=offset,
    )

@get("/audit/export", deps=["db"], query=["user_id", "date_from", "date_to"], tags=["communication-audit"])
def export_for_ediscovery(
    user_id: Optional[int] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    db: Session = None,
):
    """Export the communication audit trail for e-discovery."""
    service = get_communication_audit_service(db)
    return service.export_for_ediscovery(
        user_id=user_id,
        date_from=date_from,
        date_to=date_to,
    )

__all__ = ["get_audit_trail", "export_for_ediscovery"]
