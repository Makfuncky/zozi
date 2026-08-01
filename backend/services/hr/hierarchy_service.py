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
from sqlalchemy.orm import Session

from models import Employee, OrgUnit, User, EmployeeRole
from models.employee_models import EmployeeRelation


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
            current = (
                db.query(Employee)
                .filter(Employee.id == current.reporting_manager_id)
                .first()
            )
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

    subordinates: List[Dict[str, Any]] = []
    queue = [root.id]
    visited: Set[int] = {root.id}
    while queue:
        current_id = queue.pop(0)
        children = (
            db.query(Employee)
            .filter(Employee.reporting_manager_id == current_id)
            .all()
        )
        for child in children:
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
            queue.append(child.id)
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

    current = lower
    visited: Set[int] = set()
    while current and current.id not in visited:
        visited.add(current.id)
        if current.reporting_manager_id is None:
            break
        manager = (
            db.query(Employee)
            .filter(Employee.id == current.reporting_manager_id)
            .first()
        )
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
    while current and current.id not in visited:
        visited.add(current.id)
        if current.reporting_manager_id == manager.id:
            return True
        current = (
            db.query(Employee)
            .filter(Employee.id == current.reporting_manager_id)
            .first()
        )
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
        # Slow fallback: recursive BFS
        result: List[Dict[str, Any]] = [{
            "id": root.id,
            "name": root.name,
            "level": root.level,
            "path": None,
            "parent_id": root.parent_id,
            "country_code": root.country_code,
            "is_active": root.is_active,
        }]
        queue = [root.id]
        while queue:
            pid = queue.pop(0)
            children = (
                db.query(OrgUnit)
                .filter(OrgUnit.parent_id == pid)
                .order_by(OrgUnit.level, OrgUnit.name)
                .all()
            )
            for child in children:
                result.append({
                    "id": child.id,
                    "name": child.name,
                    "level": child.level,
                    "path": None,
                    "parent_id": child.parent_id,
                    "country_code": child.country_code,
                    "is_active": child.is_active,
                })
                queue.append(child.id)
        return result


def get_org_unit_path(db: Session, org_unit_id: int) -> List[Dict[str, Any]]:
    """Get the ancestor chain from root to the given org unit."""
    unit = db.query(OrgUnit).filter(OrgUnit.id == org_unit_id).first()
    if not unit:
        return []

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
            current = db.query(OrgUnit).filter(OrgUnit.id == current.parent_id).first()
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
    result = []
    for r in relations:
        mgr = db.query(Employee).filter(Employee.id == r.internal_employee_id).first() if r.internal_employee_id else None
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
    result = []
    for r in relations:
        emp = db.query(Employee).filter(Employee.id == r.employee_id).first()
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
    current = db.query(Employee).filter(Employee.id == proposed_manager_id).first()
    visited: Set[int] = set()
    while current and current.id not in visited:
        visited.add(current.id)
        if current.reporting_manager_id == employee_id:
            return True
        if current.reporting_manager_id:
            current = db.query(Employee).filter(Employee.id == current.reporting_manager_id).first()
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
    current = employee
    visited: Set[int] = set()
    while current and current.id not in visited:
        visited.add(current.id)
        if current.reporting_manager_id:
            manager = db.query(Employee).filter(Employee.id == current.reporting_manager_id).first()
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
    for r in matrix_relations:
        mgr = db.query(Employee).filter(Employee.id == r.internal_employee_id).first() if r.internal_employee_id else None
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
