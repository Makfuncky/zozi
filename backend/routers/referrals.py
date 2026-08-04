"""Referrals router."""
import secrets
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from data.db import get_db
from data.models import User
from services.core.users_write_service import get_referral_by_referrer_id, get_or_create_referral
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
    referral = get_referral_by_referrer_id(db, current_user.id)
    if not referral:
        code = secrets.token_urlsafe(8).upper()
        referral = get_or_create_referral(db, current_user.id, code)
    return {"referral_code": referral.referral_code, "status": referral.status, "referral_url": f"/signup?ref={referral.referral_code}"}
