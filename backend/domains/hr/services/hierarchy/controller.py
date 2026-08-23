"""Thin controller for org-hierarchy write endpoints.

W1 contract: controllers orchestrate only — they must never call
``db.add/commit/delete/flush/...``. Every mutation is delegated to
``services.hierarchy.org_hierarchy_write_service``. ``HTTPException`` raised by
the service is allowed to propagate untouched.

HTTP contract declared with ``infrastructure.routing.route_contract`` decorators so the
routes can be auto-generated into ``routers/``.
"""
from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from infrastructure.routing.route_contract import delete, post, put

from modules.employee.routers import org_hierarchy_write_service as write_service
import structlog
logger = structlog.get_logger(__name__)


@post("/api/v1/hierarchy/org-units", deps=["db", "admin"], body=Any,
      tags=["hierarchy"], summary="Create an org unit")
def create_org_unit(payload: Any, current_user: dict, db) -> dict:
    return write_service.create_org_unit(db, payload)


@put("/api/v1/hierarchy/org-units/{unit_id}", deps=["db", "admin"], body=Any,
     tags=["hierarchy"], summary="Update an org unit")
def update_org_unit(unit_id: int, payload: Any, current_user: dict, db) -> dict:
    return write_service.update_org_unit(db, unit_id, payload)


@post("/api/v1/hierarchy/org-units/rebuild-paths", deps=["db", "admin"],
      tags=["hierarchy"], summary="Rebuild org unit materialized paths")
def rebuild_org_unit_paths(current_user: dict, db) -> dict:
    return write_service.rebuild_org_unit_paths(db)


@post("/api/v1/hierarchy/employees/reassign-manager", deps=["db", "admin"], body=Any,
      tags=["hierarchy"], summary="Reassign an employee's manager")
def reassign_employee_manager(payload: Any, current_user: dict, db) -> dict:
    return write_service.reassign_employee_manager(
        db,
        payload.employee_user_id,
        payload.new_manager_user_id,
    )


@post("/api/v1/hierarchy/authority-levels/refresh", deps=["db", "admin"],
      tags=["hierarchy"], summary="Refresh authority levels")
def refresh_authority_levels(current_user: dict, db) -> dict:
    return write_service.refresh_authority_levels(db)


@post("/api/v1/hierarchy/matrix", deps=["db", "admin"], body=Any,
      tags=["hierarchy"], summary="Assign a matrix (dotted-line) relation")
def assign_matrix(payload: Any, current_user: dict, db) -> dict:
    return write_service.assign_matrix_relation(
        db,
        employee_id=payload.employee_id,
        matrix_manager_id=payload.matrix_manager_id,
        relation_type=payload.relation_type,
        notes=payload.notes,
    )


@delete("/api/v1/hierarchy/matrix/{relation_id}", deps=["db", "admin"],
        tags=["hierarchy"], summary="Remove a matrix relation")
def remove_matrix(relation_id: int, current_user: dict, db) -> dict:
    return write_service.remove_matrix_relation(db, relation_id)
