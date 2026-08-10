"""
Escalation SLA Router
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from controllers.auth_controller import get_current_user
from db.database import get_db
from data.services_escalation_sla import get_escalation_sla_service
import structlog
logger = structlog.get_logger(__name__)

router = APIRouter(tags=["escalation"])


@router.post("/track", response_model=dict)
def track_message(
    message_id: int,
    message_type: str,
    recipient_id: int,
    priority: str = "normal",
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = get_escalation_sla_service(db)
    return service.track_message(message_id, message_type, recipient_id, priority)


@router.post("/check", response_model=dict)
def check_escalations(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = get_escalation_sla_service(db)
    return {"escalated": service.check_and_escalate()}


@router.post("/{tracking_id}/acknowledge", response_model=dict)
def acknowledge_escalation(
    tracking_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = get_escalation_sla_service(db)
    return service.acknowledge_escalation(tracking_id)
