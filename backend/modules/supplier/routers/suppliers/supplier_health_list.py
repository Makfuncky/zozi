# === From supplier_health_list.py ===
from suppliers.router import router  # noqa: F401
"""
Supplier Health API Endpoints
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from infrastructure.database.database import get_db
from rbac import get_current_user
from domains.suppliers.services.health.supplier_health_service import get_supplier_health_for_user
from domains.suppliers.services.health.supplier_health_service import list_supplier_health_for_admin


@router.get("/health/suppliers/{supplier_id}")
def get_supplier_health(
    supplier_id: int,
    country_code: str = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return get_supplier_health_for_user(db, current_user, supplier_id, country_code)


@router.get("/health/suppliers")
def list_supplier_health(
    country_code: str = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Admin-only: enumerate supplier health/trust scores. Restricted from
    arbitrary authenticated users (P0.8)."""
    return list_supplier_health_for_admin(db, current_user, country_code)

