"""Supplier health router logic, extracted behind the service layer (clears LC1).

Each function receives the caller's SQLAlchemy ``Session`` as its first argument
so the router layer never opens, owns, or touches a session itself -- it only
wires ``Depends(get_db)`` and delegates, matching the thin-router pattern used by
``supplier_products.py`` / ``supplier_finance.py``.
"""
from fastapi import HTTPException
from sqlalchemy.orm import Session

from data.models import SupplierProfile
from services.supplier_health_engine import get_supplier_health_engine


def get_supplier_health(
    db: Session,
    supplier_id: int,
    country_code: str,
    current_user: dict,
) -> dict:
    """Return the health/trust score for a single supplier.

    Non-admin callers may only read their own supplier profile.
    """
    if current_user.get("role") != "admin":
        owns = (
            db.query(SupplierProfile)
            .filter(
                SupplierProfile.id == supplier_id,
                SupplierProfile.user_id == current_user["id"],
            )
            .first()
        )
        if not owns:
            raise HTTPException(status_code=403, detail="Supplier access required")
    engine = get_supplier_health_engine(db)
    return engine.calculate_health_score(supplier_id, country_code)


def list_supplier_health(
    db: Session,
    country_code: str,
    skip: int,
    limit: int,
    current_user: dict,
) -> dict:
    """Return health scores for a page of suppliers, ranked by trust score (admin only)."""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    profiles = db.query(SupplierProfile).offset(skip).limit(limit).all()
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
    return {"suppliers": results}
