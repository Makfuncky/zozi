"""Supplier health read operations.

Owns the DB reads and permission checks for supplier health endpoints. Routers
must not query the session directly for these operations.
"""
from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy.orm import Session

from domains.comms.models.suppliers import SupplierProfile
from domains.suppliers.services.health.supplier_health_engine import get_supplier_health_engine
import structlog
logger = structlog.get_logger(__name__)


def _get_health_engine(db: Session):
    return get_supplier_health_engine(db)


def get_supplier_health_for_user(db: Session, current_user: dict, supplier_id: int, country_code: str | None) -> dict:
    """Single-supplier health score; admins allowed, suppliers restricted to owned profile."""
    if current_user.get("role") != "admin":
        owns = db.query(SupplierProfile).filter(
            SupplierProfile.id == supplier_id,
            SupplierProfile.user_id == current_user["id"],
        ).first()
        if not owns:
            raise HTTPException(status_code=403, detail="Supplier access required")
    engine = _get_health_engine(db)
    return engine.calculate_health_score(supplier_id, country_code)


def list_supplier_health_for_admin(db: Session, current_user: dict, country_code: str | None) -> dict:
    """Admin-only enumeration of supplier health/trust scores."""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    profiles = db.query(SupplierProfile).all()
    results = []
    for p in profiles:
        engine = _get_health_engine(db)
        health = engine.calculate_health_score(p.id, country_code)
        avg_rating = getattr(p, "average_rating", None)
        health["profile"] = {
            "name": p.business_name,
            "rating": float(avg_rating) if avg_rating is not None else 0,
        }
        results.append(health)
    results.sort(key=lambda x: x.get("trust_score", 0), reverse=True)
    return {"suppliers": results[:50]}


def get_supplier_health(supplier_id: int, country_code: str, current_user: dict, db: Session):
    """Compatibility wrapper (accounts migration). See get_supplier_health_for_user."""
    return get_supplier_health_for_user(db, current_user, supplier_id, country_code)


def list_supplier_health(country_code: str, current_user: dict, db: Session):
    """Compatibility wrapper (accounts migration). See list_supplier_health_for_admin."""
    return list_supplier_health_for_admin(db, current_user, country_code)
