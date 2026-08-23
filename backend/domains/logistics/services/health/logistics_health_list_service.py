"""Auto-extracted service layer for logistics_health_list (migrated from router)."""
from __future__ import annotations

from sqlalchemy.orm import Session

from domains.logistics.services.health.logistics_health_engine import get_logistics_health_engine


def list_logistics_health(db: Session, country_code: str | None = None) -> dict:
    """Return health scores for all logistics partners (capped at 50)."""
    from domains.logistics.models.logistics import LogisticsPartnerProfile
    from domains.logistics.models.logistics import LogisticsPartner

    profiles = db.query(LogisticsPartnerProfile).all()
    results = []
    for p in profiles:
        engine = get_logistics_health_engine(db)
        health = engine.calculate_health_score(p.partner_id, country_code)
        partner = db.query(LogisticsPartner).filter(LogisticsPartner.id == p.partner_id).first()
        health["profile"] = {"name": partner.name if partner else None, "rating": 0}
        results.append(health)
    results.sort(key=lambda x: x.get("trust_score", 0), reverse=True)
    return {"logistics_partners": results[:50]}
