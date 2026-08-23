"""Referrals controller (orchestration only).

Routers call these functions; all data access is delegated to
``services.commerce.referrals_service``. This module performs no DB sessions and imports
no models, keeping the controller layer a thin pass-through (fixes W1/Q1 at the
router boundary and avoids router->controller imports).

The HTTP contract is declared with the stackable decorators from
``infrastructure.routing.route_contract`` (``@get`` + composable ``@deps``/``@query``/
``@tags``/``@summary``/``@query`` as keyword arguments on the route decorator. See
``routers/generated/auto_router.py`` for the contract and the generator that turns
these declarations into the mounted surface router.
"""
from __future__ import annotations

from typing import Any, Dict

from sqlalchemy.orm import Session

from infrastructure.routing.route_contract import get

from domains.orders.services.referrals_service import get_or_create_referral_code as svc_get_or_create_referral_code
from domains.orders.services.referrals_service import get_referral_config as svc_get_referral_config
import structlog
logger = structlog.get_logger(__name__)


@get("/api/v1/referrals/config", deps=["db"], tags=["referrals"],
      summary="Get the active referral-program configuration")
def get_referral_config(db: Session) -> Dict[str, Any]:
    return svc_get_referral_config(db)


@get("/api/v1/referrals/code", deps=["db"], query=["user_id"], tags=["referrals"],
      summary="Get or create the referral code for a user")
def get_referral_code(user_id: int, db: Session) -> Dict[str, Any]:
    return svc_get_or_create_referral_code(user_id, db)
