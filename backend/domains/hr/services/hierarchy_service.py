"""Enhanced Employee hierarchy and authority service.
Supports materialized path for org_units, dotted-line/matrix management,
circular reference prevention, and hierarchical subtree operations.
"""
from __future__ import annotations

__all__ = [
    "get_authority_level",
    "get_user_chain",
    "get_all_subordinates",
    "get_team_members",
    "is_in_chain",
    "can_manage",
    "get_org_chart",
    "get_home_org_unit",
    "reassign_manager",
    "backfill_authority_levels",
    # --- New materialized path & matrix ---
    "get_org_unit_subtree",
    "get_org_unit_path",
    "get_employees_in_subtree",
    "assign_matrix_manager",
    "remove_matrix_manager",
    "get_matrix_managers",
    "get_matrix_subordinates",
    "detect_circular_reporting",
    "rebuild_paths",
    "get_approval_chain",
]

from typing import Optional, List, Dict, Any, Set

from fastapi import HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from domains.governance.models.user import User
from domains.hr.models.employee_models import Employee
from domains.hr.models.employee_models import OrgUnit
from domains.hr.models.employee_models import EmployeeRole
from domains.hr.models.employee_models import EmployeeRelation


def _employee_links(db: Session) -> Dict[int, Any]:
    """Load id -> lightweight Employee row mapping for in-memory hierarchy walks.

    Fetches the reporting graph once per call instead of querying each manager
    individually while traversing chains (eliminates the N+1 per-node lookups).
    """
    rows = db.query(
        Employee.id,
        Employee.user_id,
        Employee.employee_code,
        Employee.department,
        Employee.position,
        Employee.authority_level,
        Employee.reporting_manager_id,
    ).all()
    return {r.id: r for r in rows}


def _org_unit_links(db: Session) -> Dict[int, Any]:
    """Load id -> lightweight OrgUnit row mapping for in-memory subtree walks."""
    rows = db.query(
        OrgUnit.id,
        OrgUnit.name,
        OrgUnit.level,
        OrgUnit.parent_id,
        OrgUnit.country_code,
        OrgUnit.is_active,
    ).all()
    return {r.id: r for r in rows}


# ════════════════════════════════════════════════════════════════
#  Existing functions (kept with backward-compatible signatures)
# ════════════════════════════════════════════════════════════════

def get_authority_level(db: Session, user_id: int) -> int:
    employee = (
        db.query(Employee)
        .filter(Employee.user_id == user_id)
        .first()
    )
    if not employee or employee.authority_level is None:
        return 0
    return int(employee.authority_level)


def get_user_chain(db: Session, user_id: int) -> List[Dict[str, Any]]:
    employee = (
        db.query(Employee)
        .filter(Employee.user_id == user_id)
        .first()
    )
    if not employee:
        return []

    emp_map = _employee_links(db)
    chain = []
    current = employee
    visited: Set[int] = set()
    while current and current.id not in visited:
        visited.add(current.id)
        chain.append({
            "id": current.id,
            "user_id": current.user_id,
            "employee_code": current.employee_code,
            "department": current.department,
            "position": current.position,
            "authority_level": current.authority_level,
            "reporting_manager_id": current.reporting_manager_id,
        })
        if current.reporting_manager_id:
            current = emp_map.get(current.reporting_manager_id)
        else:
            current = None
    return chain


def get_all_subordinates(db: Session, user_id: int) -> List[Dict[str, Any]]:
    root = (
        db.query(Employee)
        .filter(Employee.user_id == user_id)
        .first()
    )
    if not root:
        return []

    emp_map = _employee_links(db)
    children_by_manager: Dict[int, list] = {}
    for e in emp_map.values():
        children_by_manager.setdefault(e.reporting_manager_id, []).append(e)

    subordinates: List[Dict[str, Any]] = []
    visited: Set[int] = {root.id}
    level_ids = [root.id]
    while level_ids:
        next_level: List[int] = []
        for mid in level_ids:
            for child in children_by_manager.get(mid, []):
                if child.id in visited:
                    continue
                visited.add(child.id)
                subordinates.append({
                    "id": child.id,
                    "user_id": child.user_id,
                    "employee_code": child.employee_code,
                    "department": child.department,
                    "position": child.position,
                    "authority_level": child.authority_level,
                    "reporting_manager_id": child.reporting_manager_id,
                })
                next_level.append(child.id)
        level_ids = next_level
    return subordinates


def get_team_members(db: Session, user_id: int) -> List[Dict[str, Any]]:
    root = (
        db.query(Employee)
        .filter(Employee.user_id == user_id)
        .first()
    )
    if not root:
        return []

    members = (
        db.query(Employee)
        .filter(Employee.reporting_manager_id == root.id)
        .all()
    )
    return [
        {
            "id": m.id,
            "user_id": m.user_id,
            "employee_code": m.employee_code,
            "department": m.department,
            "position": m.position,
            "authority_level": m.authority_level,
            "reporting_manager_id": m.reporting_manager_id,
        }
        for m in members
    ]


def is_in_chain(db: Session, upper_user_id: int, lower_user_id: int) -> bool:
    if upper_user_id == lower_user_id:
        return True

    lower = (
        db.query(Employee)
        .filter(Employee.user_id == lower_user_id)
        .first()
    )
    if not lower:
        return False

    emp_map = _employee_links(db)
    current = lower
    visited: Set[int] = set()
    while current and current.id not in visited:
        visited.add(current.id)
        if current.reporting_manager_id is None:
            break
        manager = emp_map.get(current.reporting_manager_id)
        if not manager:
            break
        if manager.user_id == upper_user_id:
            return True
        current = manager
    return False


def can_manage(db: Session, manager_user_id: int, target_user_id: int) -> bool:
    manager = (
        db.query(Employee)
        .filter(Employee.user_id == manager_user_id)
        .first()
    )
    target = (
        db.query(Employee)
        .filter(Employee.user_id == target_user_id)
        .first()
    )
    if not manager or not target:
        return False

    if manager.user_id == target.user_id:
        return True

    if manager.authority_level is not None and target.authority_level is not None:
        if manager.authority_level <= target.authority_level:
            return False

    current = target
    visited: Set[int] = set()
    emp_map = _employee_links(db)
    while current and current.id not in visited:
        visited.add(current.id)
        if current.reporting_manager_id == manager.id:
            return True
        current = emp_map.get(current.reporting_manager_id)
    return False


def get_org_chart(db: Session, org_unit_id: Optional[int] = None) -> Dict[str, Any]:
    if org_unit_id is not None:
        root = db.query(OrgUnit).filter(OrgUnit.id == org_unit_id).first()
        if not root:
            return {"unit": None, "children": []}
    else:
        root = db.query(OrgUnit).filter(OrgUnit.parent_id.is_(None)).first()
        if not root:
            return {"unit": None, "children": []}

    def _serialize(unit: OrgUnit) -> Dict[str, Any]:
        children = (
            db.query(OrgUnit)
            .filter(OrgUnit.parent_id == unit.id)
            .order_by(OrgUnit.level, OrgUnit.name)
            .all()
        )
        # Count employees in this unit
        emp_count = (
            db.query(Employee)
            .filter(Employee.org_unit_id == unit.id, Employee.employment_status == "active")
            .count()
        )
        return {
            "id": unit.id,
            "name": unit.name,
            "country_code": unit.country_code,
            "level": unit.level,
            "path": getattr(unit, "path", None),
            "is_active": unit.is_active,
            "employee_count": emp_count,
            "children": [_serialize(child) for child in children],
        }

    return _serialize(root)


def get_home_org_unit(db: Session, user_id: int) -> Optional[Dict[str, Any]]:
    employee = (
        db.query(Employee)
        .filter(Employee.user_id == user_id)
        .first()
    )
    if not employee or not employee.org_unit_id:
        return None

    unit = db.query(OrgUnit).filter(OrgUnit.id == employee.org_unit_id).first()
    if not unit:
        return None

    return {
        "id": unit.id,
        "name": unit.name,
        "country_code": unit.country_code,
        "level": unit.level,
        "path": getattr(unit, "path", None),
    }


def reassign_manager(db: Session, user_id: int, new_manager_id: int) -> Dict[str, Any]:
    employee = (
        db.query(Employee)
        .filter(Employee.user_id == user_id)
        .first()
    )
    if not employee:
        raise HTTPException(status_code=400, detail="Employee not found")

    if new_manager_id is not None:
        new_manager = (
            db.query(Employee)
            .filter(Employee.user_id == new_manager_id)
            .first()
        )
        if not new_manager:
            raise HTTPException(status_code=400, detail="New manager not found")
        if new_manager.id == employee.id:
            raise HTTPException(status_code=400, detail="Cannot set self as manager")

        if is_in_chain(db, user_id, new_manager_id):
            raise HTTPException(status_code=400, detail="Circular reporting relationship detected")

    employee.reporting_manager_id = new_manager_id
    db.flush()
    db.refresh(employee)

    # Recompute authority levels after reassignment
    backfill_authority_levels(db)
    db.flush()

    return {
        "id": employee.id,
        "user_id": employee.user_id,
        "reporting_manager_id": employee.reporting_manager_id,
    }


def backfill_authority_levels(db: Session) -> int:
    employees = db.query(Employee).all()
    if not employees:
        return 0

    depths: dict[int, int] = {}
    for emp in employees:
        chain = get_user_chain(db, emp.user_id)
        depths[emp.id] = max(0, len(chain) - 1)

    max_depth = max(depths.values()) if depths else 0
    updated = 0
    for emp in employees:
        if emp.authority_level is not None:
            # Only update employees whose authority_level is explicitly stale
            expected = max(0, max_depth - depths.get(emp.id, 0))
            if int(emp.authority_level) != expected:
                emp.authority_level = expected
                updated += 1
        else:
            emp.authority_level = max(0, max_depth - depths.get(emp.id, 0))
            updated += 1
    db.flush()
    return updated


# ════════════════════════════════════════════════════════════════
#  NEW: Materialized Path support for Org Units
# ════════════════════════════════════════════════════════════════

def rebuild_paths(db: Session) -> int:
    """Rebuild materialized paths for all org_units.
    Each org_unit gets a path like '/1/12/45/' where numbers are ancestor IDs.
    """
    roots = db.query(OrgUnit).filter(OrgUnit.parent_id.is_(None)).all()
    updated = 0

    def _assign_path(unit: OrgUnit, parent_path: str = "/") -> None:
        unit.path = f"{parent_path}{unit.id}/"
        db.flush()
        updated_local = 1
        children = (
            db.query(OrgUnit)
            .filter(OrgUnit.parent_id == unit.id)
            .all()
        )
        for child in children:
            updated_local += _assign_path(child, unit.path)
        return updated_local

    for root in roots:
        updated += _assign_path(root)
    db.flush()
    return updated


def get_org_unit_subtree(db: Session, org_unit_id: int) -> List[Dict[str, Any]]:
    """Get all org units under a given unit using materialized path.
    Falls back to recursive traversal if path columns are not populated.
    """
    root = db.query(OrgUnit).filter(OrgUnit.id == org_unit_id).first()
    if not root:
        return []

    path_prefix = getattr(root, "path", None)
    if path_prefix:
        # Fast path: use LIKE on materialized path
        children = (
            db.query(OrgUnit)
            .filter(OrgUnit.path.like(f"{path_prefix}%"))
            .order_by(OrgUnit.level, OrgUnit.name)
            .all()
        )
        return [
            {
                "id": u.id,
                "name": u.name,
                "level": u.level,
                "path": u.path,
                "parent_id": u.parent_id,
                "country_code": u.country_code,
                "is_active": u.is_active,
            }
            for u in children
        ]
    else:
        # Slow fallback: recursive BFS (one org-unit map load instead of per-node queries)
        unit_map = _org_unit_links(db)
        children_by_parent: Dict[int, list] = {}
        for u in unit_map.values():
            children_by_parent.setdefault(u.parent_id, []).append(u)
        result: List[Dict[str, Any]] = [{
            "id": root.id,
            "name": root.name,
            "level": root.level,
            "path": None,
            "parent_id": root.parent_id,
            "country_code": root.country_code,
            "is_active": root.is_active,
        }]
        visited_units: Set[int] = {root.id}
        level_ids = [root.id]
        while level_ids:
            next_level = []
            for pid in level_ids:
                for child in children_by_parent.get(pid, []):
                    if child.id in visited_units:
                        continue
                    visited_units.add(child.id)
                    result.append({
                        "id": child.id,
                        "name": child.name,
                        "level": child.level,
                        "path": None,
                        "parent_id": child.parent_id,
                        "country_code": child.country_code,
                        "is_active": child.is_active,
                    })
                    next_level.append(child.id)
            level_ids = next_level
        return result


def get_org_unit_path(db: Session, org_unit_id: int) -> List[Dict[str, Any]]:
    """Get the ancestor chain from root to the given org unit."""
    unit = db.query(OrgUnit).filter(OrgUnit.id == org_unit_id).first()
    if not unit:
        return []

    unit_map = _org_unit_links(db)
    path_list: List[Dict[str, Any]] = []
    current = unit
    visited: Set[int] = set()
    while current and current.id not in visited:
        visited.add(current.id)
        path_list.insert(0, {
            "id": current.id,
            "name": current.name,
            "level": current.level,
        })
        if current.parent_id:
            current = unit_map.get(current.parent_id)
        else:
            current = None
    return path_list


def get_employees_in_subtree(db: Session, org_unit_id: int) -> List[Dict[str, Any]]:
    """Get all employees belonging to a unit or any of its descendants."""
    subtree = get_org_unit_subtree(db, org_unit_id)
    unit_ids = [u["id"] for u in subtree]
    if not unit_ids:
        return []

    employees = (
        db.query(Employee)
        .filter(Employee.org_unit_id.in_(unit_ids), Employee.employment_status == "active")
        .all()
    )
    return [
        {
            "id": e.id,
            "user_id": e.user_id,
            "employee_code": e.employee_code,
            "department": e.department,
            "position": e.position,
            "authority_level": e.authority_level,
        }
        for e in employees
    ]


# ════════════════════════════════════════════════════════════════
#  NEW: Matrix/Dotted-Line Management
# ════════════════════════════════════════════════════════════════

def assign_matrix_manager(
    db: Session,
    employee_id: int,
    matrix_manager_id: int,
    relation_type: str = "matrix_manager",
    notes: Optional[str] = None,
) -> Dict[str, Any]:
    """Assign a dotted-line/matrix manager to an employee.
    The employee's solid-line reporting_manager_id remains unchanged.
    """
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    matrix_mgr = db.query(Employee).filter(Employee.id == matrix_manager_id).first()
    if not matrix_mgr:
        raise HTTPException(status_code=404, detail="Matrix manager not found")

    if matrix_manager_id == employee.reporting_manager_id:
        raise HTTPException(status_code=400, detail="Matrix manager is already the solid-line manager")

    # Check circular: if the matrix manager reports to the employee (solid or dotted)
    if is_in_chain(db, employee.user_id, matrix_mgr.user_id):
        raise HTTPException(status_code=400, detail="Circular matrix relationship detected")

    # Check if this matrix relation already exists
    existing = (
        db.query(EmployeeRelation)
        .filter(
            EmployeeRelation.employee_id == employee_id,
            EmployeeRelation.internal_employee_id == matrix_manager_id,
            EmployeeRelation.relation_type == relation_type,
        )
        .first()
    )
    if existing:
        return {"id": existing.id, "relation_type": relation_type, "message": "Already exists"}

    relation = EmployeeRelation(
        employee_id=employee_id,
        related_person_name=matrix_mgr.employee_code or f"Employee #{matrix_manager_id}",
        relation_type=relation_type,
        is_internal_employee=True,
        internal_employee_id=matrix_manager_id,
        notes=notes,
    )
    db.add(relation)
    db.flush()
    db.refresh(relation)
    return {"id": relation.id, "relation_type": relation_type, "status": "assigned"}


def remove_matrix_manager(db: Session, relation_id: int) -> Dict[str, Any]:
    """Remove a matrix management relationship."""
    relation = (
        db.query(EmployeeRelation)
        .filter(EmployeeRelation.id == relation_id, EmployeeRelation.relation_type == "matrix_manager")
        .first()
    )
    if not relation:
        raise HTTPException(status_code=404, detail="Matrix relation not found")
    db.delete(relation)
    db.flush()
    return {"status": "removed", "relation_id": relation_id}


def get_matrix_managers(db: Session, employee_id: int) -> List[Dict[str, Any]]:
    """Get all dotted-line/matrix managers for an employee."""
    relations = (
        db.query(EmployeeRelation)
        .filter(
            EmployeeRelation.employee_id == employee_id,
            EmployeeRelation.is_internal_employee == True,
            EmployeeRelation.relation_type.in_(["matrix_manager", "project_manager", "dotted_line"]),
        )
        .all()
    )
    mgr_ids = [r.internal_employee_id for r in relations if r.internal_employee_id]
    mgr_map: Dict[int, Any] = {}
    if mgr_ids:
        mgr_rows = db.query(Employee).filter(Employee.id.in_(mgr_ids)).all()
        mgr_map = {m.id: m for m in mgr_rows}
    result = []
    for r in relations:
        mgr = mgr_map.get(r.internal_employee_id) if r.internal_employee_id else None
        result.append({
            "id": r.id,
            "manager_id": r.internal_employee_id,
            "manager_name": mgr.employee_code if mgr else None,
            "relation_type": r.relation_type,
            "notes": r.notes,
        })
    return result


def get_matrix_subordinates(db: Session, manager_id: int) -> List[Dict[str, Any]]:
    """Get all employees who have this manager as a dotted-line/matrix manager."""
    relations = (
        db.query(EmployeeRelation)
        .filter(
            EmployeeRelation.internal_employee_id == manager_id,
            EmployeeRelation.is_internal_employee == True,
            EmployeeRelation.relation_type.in_(["matrix_manager", "project_manager", "dotted_line"]),
        )
        .all()
    )
    emp_ids = [r.employee_id for r in relations]
    emp_map: Dict[int, Any] = {}
    if emp_ids:
        emp_rows = db.query(Employee).filter(Employee.id.in_(emp_ids)).all()
        emp_map = {e.id: e for e in emp_rows}
    result = []
    for r in relations:
        emp = emp_map.get(r.employee_id)
        if emp:
            result.append({
                "id": r.id,
                "employee_id": emp.id,
                "employee_code": emp.employee_code,
                "department": emp.department,
                "position": emp.position,
                "relation_type": r.relation_type,
            })
    return result


# ════════════════════════════════════════════════════════════════
#  NEW: Circular Reference Detection & Approval Chain
# ════════════════════════════════════════════════════════════════

def detect_circular_reporting(db: Session, employee_id: int, proposed_manager_id: int) -> bool:
    """Check if assigning proposed_manager_id as manager would create a cycle."""
    if employee_id == proposed_manager_id:
        return True

    # Walk up from the proposed manager — if we ever hit employee_id, it's circular
    emp_map = _employee_links(db)
    current = emp_map.get(proposed_manager_id)
    visited: Set[int] = set()
    while current and current.id not in visited:
        visited.add(current.id)
        if current.reporting_manager_id == employee_id:
            return True
        if current.reporting_manager_id:
            current = emp_map.get(current.reporting_manager_id)
        else:
            break
    return False


def get_approval_chain(
    db: Session,
    employee_id: int,
    resource_type: str = "leave",
    min_authority_level: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """Get the ordered chain of approvers for an employee, considering
    both solid-line managers and matrix managers, with authority threshold.
    Returns a list of approvers sorted by authority (lowest→highest).
    """
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        return []

    approvers: List[Dict[str, Any]] = []

    # Solid-line chain
    emp_map = _employee_links(db)
    current = employee
    visited: Set[int] = set()
    while current and current.id not in visited:
        visited.add(current.id)
        if current.reporting_manager_id:
            manager = emp_map.get(current.reporting_manager_id)
            if manager and manager.id not in visited:
                if min_authority_level is None or (manager.authority_level and int(manager.authority_level) >= min_authority_level):
                    approvers.append({
                        "id": manager.id,
                        "user_id": manager.user_id,
                        "employee_code": manager.employee_code,
                        "authority_level": int(manager.authority_level) if manager.authority_level else 0,
                        "type": "solid_line",
                    })
                    visited.add(manager.id)
                current = manager
            else:
                break
        else:
            break

    # Matrix managers (lower priority than solid-line)
    matrix_relations = (
        db.query(EmployeeRelation)
        .filter(
            EmployeeRelation.employee_id == employee_id,
            EmployeeRelation.is_internal_employee == True,
            EmployeeRelation.relation_type.in_(["matrix_manager", "project_manager", "dotted_line"]),
        )
        .all()
    )
    mgr_ids = [r.internal_employee_id for r in matrix_relations if r.internal_employee_id]
    mgr_map: Dict[int, Any] = {}
    if mgr_ids:
        mgr_rows = db.query(Employee).filter(Employee.id.in_(mgr_ids)).all()
        mgr_map = {m.id: m for m in mgr_rows}
    for r in matrix_relations:
        mgr = mgr_map.get(r.internal_employee_id) if r.internal_employee_id else None
        if mgr and mgr.id not in visited:
            if min_authority_level is None or (mgr.authority_level and int(mgr.authority_level) >= min_authority_level):
                approvers.append({
                    "id": mgr.id,
                    "user_id": mgr.user_id,
                    "employee_code": mgr.employee_code,
                    "authority_level": int(mgr.authority_level) if mgr.authority_level else 0,
                    "type": "matrix",
                })
                visited.add(mgr.id)

    return approvers


# === Merged from accounts/services/hierarchy_service.py ===

class ApprovalChainQuery(BaseModel):

    employee_id: int

    resource_type: str = "leave"

    min_authority_level: Optional[int] = None




class ManagerReassign(BaseModel):

    employee_user_id: int

    new_manager_user_id: int




class MatrixAssign(BaseModel):

    employee_id: int

    matrix_manager_id: int

    relation_type: str = "matrix_manager"

    notes: Optional[str] = None




class OrgUnitCreate(BaseModel):

    name: str = Field(..., min_length=1, max_length=200)

    parent_id: Optional[int] = None

    country_code: str

    level: int = 1




class OrgUnitUpdate(BaseModel):

    name: Optional[str] = None

    parent_id: Optional[int] = None

    is_active: Optional[bool] = None

    level: Optional[int] = None




def _update_unit_path(db: Session, unit: OrgUnit) -> None:

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




def approval_chain(payload: ApprovalChainQuery, db: Session, current_user: dict):

    return {

        "approvers": get_approval_chain(

            db,

            employee_id=payload.employee_id,

            resource_type=payload.resource_type,

            min_authority_level=payload.min_authority_level,

        )

    }




def assign_matrix(payload: MatrixAssign, db: Session, current_user: dict):

    result = assign_matrix_manager(

        db,

        employee_id=payload.employee_id,

        matrix_manager_id=payload.matrix_manager_id,

        relation_type=payload.relation_type,

        notes=payload.notes,

    )

    db.commit()

    return result




def check_can_manage(user_id: int, target_user_id: int, db: Session, current_user: dict):

    return {"can_manage": can_manage(db, user_id, target_user_id)}




def country_localization(country_code: str, db: Session, current_user: dict):

    """Get localization settings for a country (leave policies, holidays, labor rules)."""

    normalized = country_code.upper()

    country = db.query(CountryConfig).filter(CountryConfig.code == normalized).first()

    if not country:

        raise HTTPException(status_code=404, detail="Country not found")



    holidays = (

        db.query(CountryHolidayCalendar)

        .filter(CountryHolidayCalendar.country_code == normalized)

        .order_by(CountryHolidayCalendar.date)

        .all()

    )

    localization = (

        db.query(CountryLocalization)

        .filter(CountryLocalization.country_code == normalized)

        .all()

    )



    return {

        "country": {

            "code": country.code,

            "name": country.name,

            "currency": country.currency,

            "timezone": country.timezone,

            "language": country.language,

        },

        "holidays": [

            {

                "id": h.id,

                "name": h.holiday_name,

                "date": str(h.date),

                "type": h.holiday_type,

            }

            for h in holidays

        ],

        "localization": {

            loc.key: loc.value

            for loc in localization

        },

    }




def create_org_unit(payload: OrgUnitCreate, db: Session, current_user: dict):

    unit = OrgUnit(

        name=payload.name,

        parent_id=payload.parent_id,

        country_code=payload.country_code,

        level=payload.level,

    )

    db.add(unit)

    db.flush()

    _update_unit_path(db, unit)

    db.commit()

    db.refresh(unit)

    return {

        "id": unit.id,

        "name": unit.name,

        "path": unit.path,

        "depth": unit.depth,

    }




def detect_circular(employee_id: int, proposed_manager_id: int, db: Session, current_user: dict):

    is_circular = detect_circular_reporting(db, employee_id, proposed_manager_id)

    return {

        "is_circular": is_circular,

        "message": "Circular reporting detected" if is_circular else "No circular relationship",

    }




def employee_chain(user_id: int, db: Session, current_user: dict):

    return {"chain": get_user_chain(db, user_id)}




def employee_subordinates(user_id: int, direct_only: bool, db: Session, current_user: dict):

    if direct_only:

        return {"subordinates": get_team_members(db, user_id)}

    return {"subordinates": get_all_subordinates(db, user_id)}




def employees_in_subtree(unit_id: int, db: Session, current_user: dict):

    return {"employees": get_employees_in_subtree(db, unit_id)}




def list_org_units(country_code: Optional[str], db: Session, current_user: dict):

    q = db.query(OrgUnit).filter(OrgUnit.is_active == True)

    if country_code:

        q = q.filter(OrgUnit.country_code == country_code)

    units = q.order_by(OrgUnit.path, OrgUnit.name).all()

    return {

        "units": [

            {

                "id": u.id,

                "name": u.name,

                "parent_id": u.parent_id,

                "path": u.path,

                "depth": u.depth,

                "level": u.level,

                "country_code": u.country_code,

                "is_active": u.is_active,

            }

            for u in units

        ]

    }




def matrix_managers(employee_id: int, db: Session, current_user: dict):

    return {"matrix_managers": get_matrix_managers(db, employee_id)}




def matrix_subordinates(manager_id: int, db: Session, current_user: dict):

    return {"matrix_subordinates": get_matrix_subordinates(db, manager_id)}




def org_chart(org_unit_id: Optional[int], db: Session, current_user: dict):

    return get_org_chart(db, org_unit_id)




def org_unit_ancestor_path(unit_id: int, db: Session, current_user: dict):

    return {"path": get_org_unit_path(db, unit_id)}




def org_unit_subtree(unit_id: int, db: Session, current_user: dict):

    return {"subtree": get_org_unit_subtree(db, unit_id)}




def reassign_employee_manager(payload: ManagerReassign, db: Session, current_user: dict):

    result = reassign_manager(db, payload.employee_user_id, payload.new_manager_user_id)

    db.commit()

    return result




def rebuild_org_unit_paths(db: Session, current_user: dict):

    updated = rebuild_paths(db)

    db.commit()

    return {"message": f"Rebuilt paths for {updated} org units"}




def refresh_authority_levels(db: Session, current_user: dict):

    updated = backfill_authority_levels(db)

    db.commit()

    return {"message": f"Updated {updated} employee authority levels"}




def remove_matrix(relation_id: int, db: Session, current_user: dict):

    result = remove_matrix_manager(db, relation_id)

    db.commit()

    return result




def required_authority_for_resource(resource_type: str, db: Session, current_user: dict):

    thresholds = {

        "leave": 1,

        "expense_500": 2,

        "expense_2000": 3,

        "expense_10000": 4,

        "payroll_release": 4,

        "offboarding_approve": 3,

        "disciplinary_final": 4,

        "hiring_approve": 3,

    }

    return {

        "resource_type": resource_type,

        "required_authority_level": thresholds.get(resource_type, 1),

    }






def switch_country_scope(country_code: str, db: Session, current_user: dict):

    """Switch the active country scope for the current user (sets RLS context)."""

    user_id = int(current_user.get("id", 0))

    normalized = country_code.upper()



    # Verify the user has access to this country

    assignment = (

        db.query(CountryStaffAssignment)

        .filter(

            CountryStaffAssignment.user_id == user_id,

            CountryStaffAssignment.country_code == normalized,

            CountryStaffAssignment.is_active == True,

        )

        .first()

    )

    role = str(current_user.get("role", "")).lower()

    if not assignment and role not in ("admin", "super_admin"):

        raise HTTPException(status_code=403, detail=f"No access to country '{normalized}'")



    # Set RLS context

    from infrastructure.utils.rls_interceptor import set_rls_context

    set_rls_context(normalized)



    return {"active_country": normalized, "message": f"Switched to {normalized}"}




def update_org_unit(unit_id: int, payload: OrgUnitUpdate, db: Session, current_user: dict):

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

    _update_unit_path(db, unit)

    db.commit()

    return {"id": unit.id, "path": unit.path, "depth": unit.depth}




def user_country_scope(user_id: int, db: Session, current_user: dict):

    """Get all country assignments for a user."""

    assignments = (

        db.query(CountryStaffAssignment)

        .filter(

            CountryStaffAssignment.user_id == user_id,

            CountryStaffAssignment.is_active == True,

        )

        .all()

    )

    return {

        "countries": [

            {

                "id": a.id,

                "country_code": a.country_code,

                "role_in_country": a.role_in_country,

            }

            for a in assignments

        ]

    }



