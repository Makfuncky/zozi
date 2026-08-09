"""Thin controller for admin supplier write endpoints.

W1 contract: controllers orchestrate only — they must never call
``db.add/commit/delete/flush/...``. Country-scope permission checks stay here;
every mutation is delegated to
``services.supplier.admin_supplier_write_service``. ``HTTPException`` raised by
the permission check or the service propagates untouched.
"""
from __future__ import annotations

from typing import Any, Optional

from services.supplier import admin_supplier_write_service as write_service
from utils.country_access import enforce_country_access
import structlog
logger = structlog.get_logger(__name__)


def update_supplier(
    code: str,
    supplier_id: int,
    business_name: Optional[str],
    verification_status: Optional[str],
    badge_level: Optional[str],
    current_user: Any,
    db,
):
    enforce_country_access(code, db=db)
    return write_service.update_supplier_profile(
        db,
        code,
        supplier_id,
        business_name=business_name,
        verification_status=verification_status,
        badge_level=badge_level,
    )


def approve_kyc(code: str, supplier_id: int, current_user: Any, db) -> dict:
    enforce_country_access(code, db=db)
    return write_service.approve_supplier_kyc(
        db,
        code,
        supplier_id,
        getattr(current_user, "id", None),
    )


def reject_kyc(
    code: str,
    supplier_id: int,
    reason: Optional[str],
    current_user: Any,
    db,
) -> dict:
    enforce_country_access(code, db=db)
    return write_service.reject_supplier_kyc(db, code, supplier_id, reason)


def suspend(code: str, supplier_id: int, current_user: Any, db) -> dict:
    enforce_country_access(code, db=db)
    return write_service.suspend_supplier(db, code, supplier_id)


def activate(code: str, supplier_id: int, current_user: Any, db) -> dict:
    enforce_country_access(code, db=db)
    return write_service.activate_supplier(db, code, supplier_id)


def bulk_action(payload: dict, current_user: Any, db) -> dict:
    return write_service.bulk_supplier_action(db, payload)


def bulk_restore(payload: dict, current_user: Any, db) -> dict:
    return write_service.bulk_restore_suppliers(db, payload)


def restore(supplier_id: int, current_user: Any, db) -> dict:
    return write_service.restore_supplier(db, supplier_id)
