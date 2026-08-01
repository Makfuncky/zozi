"""
Logistics Health API Endpoints
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from db.database import get_db
from dependencies.auth import get_current_user
from services.logistics_health_engine import get_logistics_health_engine

router = APIRouter()


@router.get("/health/logistics/{partner_id}")
def get_logistics_health(
    partner_id: int,
    country_code: str = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    engine = get_logistics_health_engine(db)
    return engine.calculate_health_score(partner_id, country_code)


@router.get("/health/logistics")
def list_logistics_health(
    country_code: str = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from models import LogisticsPartnerProfile, LogisticsPartner
    profiles = db.query(LogisticsPartnerProfile).all()
    results = []
    for p in profiles:
        engine = get_logistics_health_engine(db)
        health = engine.calculate_health_score(p.id, country_code)
        partner = db.query(LogisticsPartner).filter(LogisticsPartner.id == p.partner_id).first()
        health["profile"] = {
            "name": partner.name if partner else None,
            "rating": 0,
        }
        results.append(health)
    results.sort(key=lambda x: x.get("trust_score", 0), reverse=True)
    return {"logistics_partners": results[:50]}
