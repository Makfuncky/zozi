"""Referrals router (thin orchestration).

Delegates all referral logic to ``controllers.referrals_controller``; performs
no DB access and imports no other controllers (fixes W1/Q1 at the router
boundary). Response shapes are unchanged from the previous implementation so
existing frontend clients keep working.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

import controllers.referrals_controller as referrals_ctrl
from db.database import get_db
from data.models import User
from data.schemas import ReferralCodeOut, ReferralConfigOut
from utils.dependencies import get_current_user
import structlog
logger = structlog.get_logger(__name__)

router = APIRouter()


@router.get("/config", response_model=ReferralConfigOut)
def referral_config(db: Session = Depends(get_db)):
    """Public, read-only referral feature configuration."""
    return referrals_ctrl.get_referral_config(db)


@router.get("/my-code", response_model=ReferralCodeOut)
def get_referral_code(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return referrals_ctrl.get_referral_code(current_user.id, db)
