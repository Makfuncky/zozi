"""Impossible-travel fraud event write service.

Owns the DB transaction for the fraud event raised when a user session is locked
by ``middleware.impossible_travel_middleware.ImpossibleTravelMiddleware``.

The middleware runs outside any request-scoped ``Session`` dependency, so this
module exposes two entry points:

* :func:`record_impossible_travel_lock` — the write itself, taking an existing
  ``db: Session`` first (the standard service-layer contract).
* :func:`log_impossible_travel_lock` — a session-owning wrapper for callers that
  have no ``Session`` of their own (the middleware), so Layer-1 code never
  opens, writes to, or commits a DB session directly.
"""
from __future__ import annotations

import logging
from typing import Any, Optional

from sqlalchemy.orm import Session

from models import FraudEvent
import structlog
logger = structlog.get_logger(__name__)

logger = logging.getLogger(__name__)

IMPOSSIBLE_TRAVEL_EVENT_TYPE = "impossible_travel"
IMPOSSIBLE_TRAVEL_FRAUD_SCORE = 85


def record_impossible_travel_lock(
    db: Session,
    *,
    user_id: Optional[int],
    ip_address: Optional[str],
    distance_km: float,
    speed_kmh: float,
) -> FraudEvent:
    """Persist the fraud event for a session locked by impossible travel.

    Mirrors the payload the middleware previously wrote inline: a flagged
    ``impossible_travel`` event carrying the offending IP plus the computed
    distance and speed that tripped the threshold.
    """
    details: dict[str, Any] = {
        "ip": ip_address,
        "distance_km": round(distance_km, 1),
        "speed_kmh": round(speed_kmh, 1),
        "action": "session_locked",
    }
    event = FraudEvent(
        user_id=user_id,
        event_type=IMPOSSIBLE_TRAVEL_EVENT_TYPE,
        ip_address=ip_address,
        fraud_score=IMPOSSIBLE_TRAVEL_FRAUD_SCORE,
        details=details,
        is_flagged=True,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def log_impossible_travel_lock(
    *,
    user_id: Optional[int],
    ip_address: Optional[str],
    distance_km: float,
    speed_kmh: float,
) -> None:
    """Record an impossible-travel lock using a short-lived service session.

    Safe to call from non-request contexts (e.g. middleware): this function owns
    the session lifecycle end to end, so the caller never touches a ``Session``.
    """
    from db.database import get_service_session

    with get_service_session() as db:
        record_impossible_travel_lock(
            db,
            user_id=user_id,
            ip_address=ip_address,
            distance_km=distance_km,
            speed_kmh=speed_kmh,
        )
