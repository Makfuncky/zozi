"""Referrals router."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from infrastructure.database.database import get_db
from domains.governance.models.user import User
from infrastructure.utils.dependencies import get_current_user
from domains.customers.services.referrals_service import (
    get_or_create_referral_code,
    get_referral_config,
)

router = APIRouter(prefix="/api/v1/customer/referrals")


@router.get("/config")
def referral_config(db: Session = Depends(get_db)):
    """Public, read-only referral feature configuration."""
    config = get_referral_config(db)
    return {
        "enabled": bool(config.get("enabled", False)),
        "referrer_points": config.get("referrer_points", 0),
        "referee_points": config.get("referee_points", 0),
        "monthly_cap": config.get("monthly_cap", 0),
        "verification_delay_days": config.get("verification_delay_days", 0),
    }


@router.get("/my-code")
def get_referral_code(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return get_or_create_referral_code(current_user.id, db)
