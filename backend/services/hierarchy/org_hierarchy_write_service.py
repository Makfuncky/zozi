"""Write-side service for the org hierarchy surface.

W1 contract: only ``services/**`` may own DB transactions. Every mutation that
used to live inside ``routers/hierarchy.py`` (org unit create/update,
materialized path rebuilds, manager reassignment, authority backfill and matrix
relation assign/remove) is implemented here.

The read/compute primitives still live in ``services.hierarchy_service``; this
module wraps them with the transaction boundary (``db.commit()``) plus the org
unit CRUD that previously sat in the router.
"""
from __future__ import annotations

from typing import Any, Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from data.models import OrgUnit
from services.hierarchy_service import (
    assign_matrix_manager,
    backfill_authority_levels,
    reassign_manager,
    rebuild_paths,
    remove_matrix_manager,
)
import structlog
logger = structlog.get_logger(__name__)

__all__ = [
    "update_org_unit_path",
    "create_org_unit",
    "update_org_unit",
    "rebuild_org_unit_paths",
    "reassign_employee_manager",
    "refresh_authority_levels",
    "assign_matrix_relation",
    "remove_matrix_relation",
]


def update_org_unit_path(db: Session, unit: OrgUnit) -> None:
    """Compute the materialized path and depth for a unit based on its parent."""
    if unit.parent_id:
        parent = db.query(OrgUnit).filter(OrgUnit.id == unit.parent_id).first()
        if parent:
            unit.path = f"{parent.path}{unit.id}/" if parent.path else f"/{parent.id}/{unit.id}/"
            unit.depth = (parent.depth or 0) + 1
        else:
            unit.path = f"/{unit.id}/"
            unit.depth = 0
    else:
        unit.path = f"/{unit.id}/"
        unit.depth = 0
    db.flush()


def create_org_unit(db: Session, payload: Any) -> dict:
    """Create an org unit and materialize its path/depth."""
    unit = OrgUnit(
        name=payload.name,
        parent_id=payload.parent_id,
        country_code=payload.country_code,
        level=payload.level,
    )
    db.add(unit)
    db.flush()
    update_org_unit_path(db, unit)
    db.commit()
    db.refresh(unit)
    return {
        "id": unit.id,
        "name": unit.name,
        "path": unit.path,
        "depth": unit.depth,
    }


def update_org_unit(db: Session, unit_id: int, payload: Any) -> dict:
    """Patch an org unit and recompute its materialized path/depth."""
    unit = db.query(OrgUnit).filter(OrgUnit.id == unit_id).first()
    if not unit:
        raise HTTPException(status_code=404, detail="Org unit not found")

    if payload.name is not None:
        unit.name = payload.name
    if payload.level is not None:
        unit.level = payload.level
    if payload.is_active is not None:
        unit.is_active = payload.is_active
    if payload.parent_id is not None:
        unit.parent_id = payload.parent_id

    db.flush()
    update_org_unit_path(db, unit)
    db.commit()
    return {"id": unit.id, "path": unit.path, "depth": unit.depth}


def rebuild_org_unit_paths(db: Session) -> dict:
    """Rebuild materialized paths for every org unit."""
    updated = rebuild_paths(db)
    db.commit()
    return {"message": f"Rebuilt paths for {updated} org units"}


def reassign_employee_manager(
    db: Session,
    employee_user_id: int,
    new_manager_user_id: int,
) -> dict:
    """Move an employee under a new solid-line manager."""
    result = reassign_manager(db, employee_user_id, new_manager_user_id)
    db.commit()
    return result


def refresh_authority_levels(db: Session) -> dict:
    """Recompute authority levels for all employees."""
    updated = backfill_authority_levels(db)
    db.commit()
    return {"message": f"Recomputed {updated} employee authority levels"}


def assign_matrix_relation(
    db: Session,
    employee_id: int,
    matrix_manager_id: int,
    relation_type: str = "matrix_manager",
    notes: Optional[str] = None,
) -> dict:
    """Assign a dotted-line/matrix manager to an employee."""
    result = assign_matrix_manager(
        db,
        employee_id=employee_id,
        matrix_manager_id=matrix_manager_id,
        relation_type=relation_type,
        notes=notes,
    )
    db.commit()
    return result


def remove_matrix_relation(db: Session, relation_id: int) -> dict:
    """Remove a matrix management relationship."""
    result = remove_matrix_manager(db, relation_id)
    db.commit()
    return result
