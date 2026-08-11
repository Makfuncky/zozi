"""Controller for the supplier profile router.

Thin orchestration between `routers.supplier_profile_create` and
`services.supplier.supplier_profile_write_service`. 400/404 handling stays in
the controller so the router remains a thin boundary (no db writes).
"""
from __future__ import annotations

from typing import Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from data.models import SupplierProfile, User
from services.db_read import exists
from services.supplier.supplier_profile_write_service import (
    create_supplier_profile,
    update_supplier_profile,
)
import structlog
logger = structlog.get_logger(__name__)


def create_profile(current_user: User, payload, db: Session):
    existing = exists(db, SupplierProfile, [SupplierProfile.user_id == current_user.id])
    if existing:
        raise HTTPException(400, "Profile already exists")
    return create_supplier_profile(current_user, payload, db)


def update_profile(current_user: User, payload, db: Session):
    profile = update_supplier_profile(current_user, payload, db)
    if profile is None:
        raise HTTPException(404)
    return profile
