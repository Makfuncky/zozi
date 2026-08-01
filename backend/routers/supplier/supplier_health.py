"""
Supplier Health API Endpoints
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from db.database import get_db
from dependencies.auth import get_current_user
from services.supplier_health_engine import get_supplier_health_engine

router = APIRouter()


@router.get("/health/suppliers/{supplier_id}")
def get_supplier_health(
    supplier_id: int,
    country_code: str = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Allow admins, or the supplier who owns the profile identified by supplier_id.
    if current_user.get("role") != "admin":
        from models import SupplierProfile
        owns = db.query(SupplierProfile).filter(
            SupplierProfile.id == supplier_id,
            SupplierProfile.user_id == current_user["id"],
        ).first()
        if not owns:
            raise HTTPException(status_code=403, detail="Supplier access required")
    engine = get_supplier_health_engine(db)
    return engine.calculate_health_score(supplier_id, country_code)


@router.get("/health/suppliers")
def list_supplier_health(
    country_code: str = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Admin-only: enumerate supplier health/trust scores. Restricted from
    arbitrary authenticated users (P0.8)."""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    from models import SupplierProfile
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
