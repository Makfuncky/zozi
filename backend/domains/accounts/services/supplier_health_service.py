"""Auto-migrated service logic from routers/supplier_health.py."""
from __future__ import annotations

from fastapi import Depends, HTTPException

from sqlalchemy.orm import Session

from rbac.routers.auth_controller import get_current_user

from infrastructure.database.database import get_db

from services.supplier.supplier_health_engine import get_supplier_health_engine

def get_supplier_health(supplier_id: int, country_code: str, current_user: dict, db: Session):
    if current_user.get("role") != "admin":
        from _legacy.models import SupplierProfile
        owns = db.query(SupplierProfile).filter(
            SupplierProfile.id == supplier_id,
            SupplierProfile.user_id == current_user["id"],
        ).first()
        if not owns:
            raise HTTPException(status_code=403, detail="Supplier access required")
    engine = get_supplier_health_engine(db)
    return engine.calculate_health_score(supplier_id, country_code)

def list_supplier_health(country_code: str, current_user: dict, db: Session):
    """Admin-only: enumerate supplier health/trust scores. Restricted from
    arbitrary authenticated users (P0.8)."""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    from _legacy.models import SupplierProfile
    profiles = db.query(SupplierProfile).all()
    results = []
    for p in profiles:
        engine = get_supplier_health_engine(db)
        health = engine.calculate_health_score(p.id, country_code)
        avg_rating = getattr(p, "average_rating", None)
        health["profile"] = {
            "name": p.business_name,
            "rating": float(avg_rating) if avg_rating is not None else 0,
        }
        results.append(health)
    results.sort(key=lambda x: x.get("trust_score", 0), reverse=True)
    return {"suppliers": results[:50]}

