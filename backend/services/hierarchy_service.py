"""Employee hierarchy and authority service."""
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
]

from typing import Optional, List, Dict, Any

from fastapi import HTTPException
from sqlalchemy.orm import Session

from models import Employee, OrgUnit, User, EmployeeRole


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
    visited = set()
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
    visited = {root.id}
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
    visited = set()
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
    visited = set()
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
        return {
            "id": unit.id,
            "name": unit.name,
            "country_code": unit.country_code,
            "level": unit.level,
            "is_active": unit.is_active,
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
            continue
        emp.authority_level = max(0, max_depth - depths[emp.id])
        updated += 1
    db.flush()
    return updated

