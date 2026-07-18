"""
Email Gateway Controller
"""
import logging
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from db.database import get_db
from services.email_gateway import EmailGateway, get_email_gateway

logger = logging.getLogger("zozi.api.email")
router = APIRouter()


@router.post("/internal")
def send_internal_email(to: List[int], subject: str, body: str, sender_id: int,
                        db: Session = Depends(get_db)):
    email = get_email_gateway(db)
    return email.send_internal_email(to, subject, body, sender_id)


@router.post("/external")
def send_external_email(to: str, subject: str, body: str, sender_id: int,
                        template_id: str = None, db: Session = Depends(get_db)):
    email = get_email_gateway(db)
    return email.send_external_email(to, subject, body, sender_id, template_id)


@router.get("/templates")
def get_templates(db: Session = Depends(get_db)):
    email = get_email_gateway(db)
    return {"templates": email.get_email_templates()}


@router.post("/track-open")
def track_open(email_id: str, user_id: int, db: Session = Depends(get_db)):
    email = get_email_gateway(db)
    return email.track_open(email_id, user_id)


@router.get("/history/{user_id}")
def get_email_history(
    user_id: int,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    email = get_email_gateway(db)
    return email.get_email_history(user_id, limit, offset)


