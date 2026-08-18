"""Referrals service — owns all referral read/write orchestration for authenticated users.



Layering contract (ARCHITECTURE_DIAGRAM.md §10):

    routers -> controllers -> services (this module) -> models



The referral feature configuration is sourced from the shared

``PromotionEngineConfig`` model (read-only, with safe defaults when no row

exists). The previous implementation delegated to a promotion controller that

depended on a missing symbol (``services.commerce.promotion_engine_service.get_or_create_config``

is a ``_missing_symbol`` stub), so the router now reads the config model directly

to keep the router/controller thin and dependency-free.

"""

from __future__ import annotations



import secrets

from typing import Any, Dict



from sqlalchemy.orm import Session



from domains.accounts.models.user import Referral
from domains.governance.models.admin import PromotionEngineConfig

import structlog

logger = structlog.get_logger(__name__)





def get_referral_config(db: Session) -> Dict[str, Any]:

    """Return the public, read-only referral feature configuration.



    Falls back to safe defaults when no ``PromotionEngineConfig`` row exists.

    """

    row = db.query(PromotionEngineConfig).order_by(PromotionEngineConfig.id.desc()).first()

    if row is None:

        return {

            "enabled": False,

            "referrer_points": 0,

            "referee_points": 0,

            "monthly_cap": 0,

            "verification_delay_days": 0,

        }

    return {

        "enabled": bool(getattr(row, "allow_referral_rewards", False)),

        "referrer_points": int(getattr(row, "referral_referrer_points", 0) or 0),

        "referee_points": int(getattr(row, "referral_referee_points", 0) or 0),

        "monthly_cap": int(getattr(row, "referral_monthly_cap", 0) or 0),

        "verification_delay_days": int(getattr(row, "referral_verification_delay_days", 0) or 0),

    }





def get_or_create_referral_code(user_id: int, db: Session) -> Dict[str, Any]:

    """Return the user's referral code, creating one on first use."""

    referral = db.query(Referral).filter(Referral.referrer_id == user_id).first()

    if referral is None:

        code = secrets.token_urlsafe(8).upper()

        referral = Referral(referrer_id=user_id, referral_code=code)

        db.add(referral)

        db.commit()

        db.refresh(referral)

    return {

        "referral_code": referral.referral_code,

        "status": referral.status,

        "referral_url": f"/signup?ref={referral.referral_code}",

    }

