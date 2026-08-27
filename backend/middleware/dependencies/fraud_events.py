"""Fraud-event adapter for the middleware layer.

Middleware may not import ``models``/``services``; this adapter used to
own the DB reads and writes (including the session lifecycle) so
``middleware.impossible_travel_middleware`` stayed inside the circuit.

TODO: All underlying ORM/service calls lived in ``domains/`` (security,
audit, hr, governance). They have been removed from this file because
the middleware circuit must not reach ``domains/`` (Law 1). The active
fraud detection is therefore currently a no-op; the real checks will be
re-introduced via an infrastructure-layer adapter (e.g.
``infrastructure.security.fraud``) so the middleware pipeline can call
back into them without crossing layers.
"""
from __future__ import annotations

import logging
from typing import Optional

logger = logging.getLogger(__name__)


def record_impossible_travel_event(
    user_id: int,
    ip: str,
    distance: float,
    speed: float,
) -> None:
    """Persist an impossible-travel fraud event.

    Currently a no-op: the FraudEvent model lives in
    ``domains.security.models`` and must not be imported from the
    middleware layer. Re-implement when an infrastructure adapter exists.
    """
    logger.debug(
        "record_impossible_travel_event no-op user_id=%s distance=%.1f speed=%.1f",
        user_id, distance, speed,
    )
    return None


def detect_impossible_travel(
    user_id: int,
    country_code: str,
) -> bool:
    """Return True if a login from a different country occurred in the last hour.

    No-op until the audit-log reader is re-introduced via infrastructure.
    """
    return False


def detect_ghost_employee(user_id: int) -> bool:
    """Return True if the employee has zero activity for 5+ days.

    No-op until the audit-log + employee readers are re-introduced.
    """
    return False


def check_country_coi(user_id: int, related_entity_id: int) -> bool:
    """Return True if the user and related entity share a country (COI).

    No-op until the User/Employee readers are re-introduced.
    """
    return False


def calculate_fraud_score(
    user_id: Optional[int],
    ip_address: Optional[str],
    device_hash: Optional[str],
    event_type: str,
    request_headers: dict,
) -> dict:
    """Return a default allow verdict.

    The real ``FraudScoringEngine`` lives in
    ``domains.security.services.fraud`` and must not be imported from
    the middleware layer.
    """
    return {
        "is_blocked": False,
        "score": 0,
        "action": "allow",
        "triggered_rules": [],
    }
