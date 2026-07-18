"""Referrals router."""
import secrets
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from db.database import get_db
from models import Referral, User
from utils.dependencies import get_current_user
from controllers.promotion_controller import get_promotion_config

router = APIRouter()


@router.get("/config")
def referral_config(db: Session = Depends(get_db)):
    """Public, read-only referral feature configuration."""
    config = get_promotion_config(db)
    return {
        "enabled": bool(config.get("allow_referral_rewards", False)),
        "referrer_points": config.get("referral_referrer_points", 0),
        "referee_points": config.get("referral_referee_points", 0),
        "monthly_cap": config.get("referral_monthly_cap", 0),
        "verification_delay_days": config.get("referral_verification_delay_days", 0),
    }


@router.get("/my-code")
def get_referral_code(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    referral = db.query(Referral).filter(Referral.referrer_id == current_user.id).first()
    if not referral:
        code = secrets.token_urlsafe(8).upper()
        referral = Referral(referrer_id=current_user.id, referral_code=code)
        db.add(referral); db.commit(); db.refresh(referral)
    return {"referral_code": referral.referral_code, "status": referral.status, "referral_url": f"/signup?ref={referral.referral_code}"}

