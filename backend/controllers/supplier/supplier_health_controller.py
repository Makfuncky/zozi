"""Supplier health controller (CONTROLLERS layer).

Coordinates supplier health/trust-score reads and delegates the persistence and
permission checks to ``services.supplier.supplier_health_service``. It must not
issue ``db.query`` directly.

The HTTP contract is declared with ``routers.generated.auto_router`` decorators
so the auto-router emits ``routers/supplier_supplier_supplier_health.py`` as a
faithful, lossless replacement for the legacy ``routers/supplier_health_list.py``.
"""
from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from routers.generated.auto_router import get

from services.supplier.supplier_health_service import (
    get_supplier_health_for_user,
    list_supplier_health_for_admin,
)
import structlog
logger = structlog.get_logger(__name__)


@get("/api/v1/supplier/health/suppliers/{supplier_id}", deps=["user", "db"], tags=["supplier-health"])
def get_supplier_health(supplier_id: int, country_code: Optional[str] = None, current_user: dict = None, db: Session = None) -> dict:
    return get_supplier_health_for_user(db, current_user, supplier_id, country_code)


@get("/api/v1/supplier/health/suppliers", deps=["user", "db"], tags=["supplier-health"])
def list_supplier_health(country_code: Optional[str] = None, current_user: dict = None, db: Session = None) -> dict:
    return list_supplier_health_for_admin(db, current_user, country_code)
