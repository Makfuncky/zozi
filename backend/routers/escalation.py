"""
Escalation SLA Router
"""
from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from data.db import get_db
from data.dependencies_auth import get_current_user
from services.escalation_sla import EscalationSLAService, get_escalation_sla_service

router = APIRouter(tags=["escalation"])


@router.post("/track")
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


@router.post("/check")
def check_escalations(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = get_escalation_sla_service(db)
    return {"escalated": service.check_and_escalate()}


@router.post("/{tracking_id}/acknowledge")
def acknowledge_escalation(
    tracking_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = get_escalation_sla_service(db)
    return service.acknowledge_escalation(tracking_id)
