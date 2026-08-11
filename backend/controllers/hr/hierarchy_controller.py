"""Thin controller for org-hierarchy write endpoints.

W1 contract: controllers orchestrate only — they must never call
``db.add/commit/delete/flush/...``. Every mutation is delegated to
``services.hierarchy.org_hierarchy_write_service``. ``HTTPException`` raised by
the service is allowed to propagate untouched.
"""
from __future__ import annotations

from typing import Any

from services.hierarchy import org_hierarchy_write_service as write_service
import structlog
logger = structlog.get_logger(__name__)


def create_org_unit(payload: Any, current_user: dict, db) -> dict:
    return write_service.create_org_unit(db, payload)


def update_org_unit(unit_id: int, payload: Any, current_user: dict, db) -> dict:
    return write_service.update_org_unit(db, unit_id, payload)


def rebuild_org_unit_paths(current_user: dict, db) -> dict:
    return write_service.rebuild_org_unit_paths(db)


def reassign_employee_manager(payload: Any, current_user: dict, db) -> dict:
    return write_service.reassign_employee_manager(
        db,
        payload.employee_user_id,
        payload.new_manager_user_id,
    )


def refresh_authority_levels(current_user: dict, db) -> dict:
    return write_service.refresh_authority_levels(db)


def assign_matrix(payload: Any, current_user: dict, db) -> dict:
    return write_service.assign_matrix_relation(
        db,
        employee_id=payload.employee_id,
        matrix_manager_id=payload.matrix_manager_id,
        relation_type=payload.relation_type,
        notes=payload.notes,
    )


def remove_matrix(relation_id: int, current_user: dict, db) -> dict:
    return write_service.remove_matrix_relation(db, relation_id)
