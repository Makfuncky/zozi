"""Logistics health router logic, extracted behind the service layer (clears LC1).

Each function owns its database session via ``data.db.get_db_context`` so the
router layer never injects or touches a SQLAlchemy session directly.
"""
from data.models import LogisticsPartner, LogisticsPartnerProfile
from services.logistics_health_engine import get_logistics_health_engine


def get_logistics_health(partner_id: int, country_code: str = None) -> dict:
    from data.db import get_db_context

    with get_db_context() as db:
        engine = get_logistics_health_engine(db)
        return engine.calculate_health_score(partner_id, country_code)


def list_logistics_health(country_code: str = None, skip: int = 0, limit: int = 20) -> dict:
    from data.db import get_db_context

    with get_db_context() as db:
        profiles = db.query(LogisticsPartnerProfile).offset(skip).limit(limit).all()
        results = []
        for p in profiles:
            engine = get_logistics_health_engine(db)
            health = engine.calculate_health_score(p.id, country_code)
            partner = (
                db.query(LogisticsPartner)
                .filter(LogisticsPartner.id == p.partner_id)
                .first()
            )
            health["profile"] = {"name": partner.name if partner else None, "rating": 0}
            results.append(health)
        results.sort(key=lambda x: x.get("trust_score", 0), reverse=True)
        return {"logistics_partners": results[:50]}
