"""Auto-migrated service logic from routers/logistics_health.py."""
from __future__ import annotations

from fastapi import Depends

from sqlalchemy.orm import Session

# TODO: Module not yet created
# from domains.governance.services.auth_controller_service import get_current_user

from infrastructure.database.database import get_db

# Law 1 compliance: lazy import breaks circular dependency between
# logistics_health_service ↔ health.service (LogisticsHealthEngine)
def _get_health_engine(db: Session):
    from domains.logistics.services.health.service import get_logistics_health_engine
    return get_logistics_health_engine(db)

def get_logistics_health(partner_id: int, country_code: str, current_user: dict, db: Session):
    engine = _get_health_engine(db)
    return engine.calculate_health_score(partner_id, country_code)

def list_logistics_health(country_code: str, current_user: dict, db: Session):
    from domains.logistics.models.logistics import LogisticsPartner
    from domains.logistics.models.logistics import LogisticsPartnerProfile
    profiles = db.query(LogisticsPartnerProfile).all()
    results = []
    for p in profiles:
        engine = _get_health_engine(db)
        health = engine.calculate_health_score(p.id, country_code)
        partner = db.query(LogisticsPartner).filter(LogisticsPartner.id == p.partner_id).first()
        health["profile"] = {
            "name": partner.name if partner else None,
            "rating": 0,
        }
        results.append(health)
    results.sort(key=lambda x: x.get("trust_score", 0), reverse=True)
    return {"logistics_partners": results[:50]}

