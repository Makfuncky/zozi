"""Logistics partner health read service.

Holds the DB read/serialization logic for partner health endpoints so the
surface router stays a thin delegator (routers -> controllers -> services).
"""
from __future__ import annotations

from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from models import LogisticsPartner, LogisticsPartnerProfile
from services.logistics.logistics_health_engine import get_logistics_health_engine

# Number of partners returned by the list endpoint.
LIST_LIMIT = 50


def get_partner_health(
    db: Session, partner_id: int, country_code: Optional[str] = None
) -> Dict[str, Any]:
    """Compute the health score for a single logistics partner.

    Returns the engine's score dict. Callers should treat a dict containing an
    ``"error"`` key as "partner not found".
    """
    engine = get_logistics_health_engine(db)
    return engine.calculate_health_score(partner_id, country_code)


def list_logistics_health(
    db: Session, country_code: Optional[str] = None
) -> Dict[str, Any]:
    """Return a trust-score-ranked snapshot of every logistics partner profile.

    The engine is instantiated once and reused across profiles to avoid
    per-iteration connection churn.
    """
    engine = get_logistics_health_engine(db)
    profiles = db.query(LogisticsPartnerProfile).all()

    results: list[Dict[str, Any]] = []
    for profile in profiles:
        health = dict(engine.calculate_health_score(profile.id, country_code))
        partner = (
            db.query(LogisticsPartner)
            .filter(LogisticsPartner.id == profile.partner_id)
            .first()
        )
        health["profile"] = {
            "name": partner.name if partner else None,
            "rating": 0,
        }
        results.append(health)

    results.sort(key=lambda item: item.get("trust_score", 0), reverse=True)
    return {"logistics_partners": results[:LIST_LIMIT]}
