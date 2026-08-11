"""Referrals controller (orchestration only).

Routers call these functions; all data access is delegated to
``services.commerce.referrals_service``. This module performs no DB sessions and imports
no models, keeping the controller layer a thin pass-through (fixes W1/Q1 at the
router boundary and avoids router->controller imports).
"""
from __future__ import annotations

from typing import Any, Dict

from sqlalchemy.orm import Session

from services.commerce.referrals_service import (
    get_or_create_referral_code as svc_get_or_create_referral_code,
    get_referral_config as svc_get_referral_config,
)
import structlog
logger = structlog.get_logger(__name__)


def get_referral_config(db: Session) -> Dict[str, Any]:
    return svc_get_referral_config(db)


def get_referral_code(user_id: int, db: Session) -> Dict[str, Any]:
    return svc_get_or_create_referral_code(user_id, db)
