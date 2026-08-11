"""Fraud-event adapter for the middleware layer.

Middleware may not import ``models``/``services``; this adapter owns the
``FraudEvent`` write (including the session lifecycle) so
``middleware.impossible_travel_middleware`` stays inside the circuit.
"""
from __future__ import annotations

from typing import Any


def record_impossible_travel_event(
    user_id: int,
    ip: str,
    distance: float,
    speed: float,
) -> None:
    """Persist an impossible-travel fraud event (best-effort, never raises)."""
    try:
        from db.database import get_service_session
        from db.models import FraudEvent
        from services.common import db_write

        db = get_service_session()
        try:
            event = FraudEvent(
                user_id=user_id,
                event_type="impossible_travel",
                risk_score=85,
                details={
                    "ip": ip,
                    "distance_km": round(distance, 1),
                    "speed_kmh": round(speed, 1),
                    "action": "session_locked",
                },
                is_flagged=True,
            )
            db_write.add(db, event)
            db_write.commit(db)
        finally:
            db.close()
    except Exception:
        # Middleware must never break the request for an audit write.
        pass
