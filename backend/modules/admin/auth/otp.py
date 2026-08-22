"""OTP / MFA challenge endpoints for the admin auth surface.

Router is thin: all challenge logic lives in ``domains.accounts.services.otp_service``.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from domains.accounts.ports import User
from domains.accounts.services.otp_service import start_otp, verify_otp
from infrastructure.database.database import get_db
from infrastructure.security.dependencies import get_current_user
from modules.admin.auth.schemas import OtpRequest

router = APIRouter(prefix="/otp", tags=["auth", "otp"])


@router.post("/start")
def start_otp_challenge(payload: OtpRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    start_otp(current_user, purpose=payload.purpose, channel=payload.channel, destination=payload.destination, db=db)
    return {"status": "sent", "channel": payload.channel, "purpose": payload.purpose}


@router.post("/verify")
def verify_otp_challenge(payload: OtpRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    verified = verify_otp(current_user, purpose=payload.purpose, code=payload.code or "", db=db)
    return {"verified": verified}