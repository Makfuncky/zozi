"""Employee hierarchy approval matrix service."""

__all__ = [
    "APPROVAL_RULES",
    "can_approve",
    "require_approval",
    "resolve_approvers",
    "get_approval_chain",
]

from fastapi import HTTPException
from typing import Optional, List, Dict, Any

from sqlalchemy.orm import Session

from data.models import Employee
from services.hierarchy_service import (
    get_authority_level,
    get_user_chain,
    get_all_subordinates,
)


def require_approval(
    db: Session,
    user_id: int,
    resource_type: str,
    amount: Optional[float] = None,
) -> None:
    result = can_approve(db, user_id, resource_type, amount=amount)
    if not result["can_approve"]:
        raise HTTPException(
            status_code=403,
            detail=result.get("reason", "Not authorized for this approval"),
        )


APPROVAL_RULES: Dict[str, Dict[str, Any]] = {
    "order": {
        "label": "Order Approval",
        "min_authority_level": 2,
        "department": None,
        "org_unit_required": False,
        "description": "Orders above the default threshold require manager approval.",
    },
    "payout": {
        "label": "Payout Approval",
        "min_authority_level": 3,
        "department": None,
        "org_unit_required": False,
        "amount_threshold": 10000.0,
        "description": "Payouts require finance head or above approval.",
    },
    "product": {
        "label": "Product Approval",
        "min_authority_level": 2,
        "department": "operations",
        "org_unit_required": False,
        "description": "New products require operations manager approval.",
    },
    "supplier": {
        "label": "Supplier Approval",
        "min_authority_level": 3,
        "department": None,
        "org_unit_required": False,
        "description": "New supplier onboarding requires senior approval.",
    },
    "leave": {
        "label": "Leave Approval",
        "min_authority_level": 1,
        "department": None,
        "org_unit_required": True,
        "description": "Leave requests require manager or HR approval.",
    },
    "expense": {
        "label": "Expense Approval",
        "min_authority_level": 2,
        "department": "finance",
        "org_unit_required": False,
        "description": "Expense claims require finance manager approval.",
    },
    "promotion": {
        "label": "Promotion Approval",
        "min_authority_level": 4,
        "department": "human_resources",
        "org_unit_required": False,
        "description": "Employee promotions require HR head approval.",
    },
    "refund": {
        "label": "Refund Approval",
        "min_authority_level": 2,
        "department": None,
        "org_unit_required": False,
        "description": "Refunds above threshold require manager approval.",
    },
}


def _get_employee_by_user_id(db: Session, user_id: int) -> Optional[Employee]:
    return db.query(Employee).filter(Employee.user_id == user_id).first()


def can_approve(
    db: Session,
    user_id: int,
    resource_type: str,
    amount: Optional[float] = None,
) -> Dict[str, Any]:
    rule = APPROVAL_RULES.get(resource_type)
    if not rule:
        return {
            "user_id": user_id,
            "resource_type": resource_type,
            "can_approve": False,
            "reason": f"Unknown resource type '{resource_type}'",
        }

    employee = _get_employee_by_user_id(db, user_id)
    if not employee:
        return {
            "user_id": user_id,
            "resource_type": resource_type,
            "can_approve": True,
            "reason": "No employee record found, approval bypassed",
        }

    authority = get_authority_level(db, user_id)
    if authority < rule["min_authority_level"]:
        return {
            "user_id": user_id,
            "resource_type": resource_type,
            "can_approve": False,
            "reason": (
                f"Authority level {authority} is below required level "
                f"{rule['min_authority_level']}"
            ),
            "authority_level": authority,
            "required_level": rule["min_authority_level"],
        }

    if rule.get("department"):
        emp_dept = (employee.department or "").lower()
        if emp_dept != rule["department"].lower():
            return {
                "user_id": user_id,
                "resource_type": resource_type,
                "can_approve": False,
                "reason": (
                    f"Department '{employee.department}' does not match "
                    f"required department '{rule['department']}'"
                ),
                "authority_level": authority,
                "required_department": rule["department"],
            }

    if rule.get("org_unit_required") and not employee.org_unit_id:
        return {
            "user_id": user_id,
            "resource_type": resource_type,
            "can_approve": False,
            "reason": "Org unit assignment required for this approval type",
            "authority_level": authority,
        }

    if resource_type == "expense" and amount is not None:
        if amount > 5000 and authority < 4:
            return {
                "user_id": user_id,
                "resource_type": resource_type,
                "can_approve": False,
                "reason": "Expenses above 5000 require level 4+ authority",
                "authority_level": authority,
                "amount": amount,
            }

    if resource_type == "refund" and amount is not None:
        if amount > 2000 and authority < 3:
            return {
                "user_id": user_id,
                "resource_type": resource_type,
                "can_approve": False,
                "reason": "Refunds above 2000 require level 3+ authority",
                "authority_level": authority,
                "amount": amount,
            }

    if rule.get("amount_threshold") is not None and amount is not None:
        if amount > float(rule["amount_threshold"]) and authority < rule["min_authority_level"] + 1:
            return {
                "user_id": user_id,
                "resource_type": resource_type,
                "can_approve": False,
                "reason": (
                    f"Amount {amount} exceeds threshold {rule['amount_threshold']} "
                    f"and requires level {rule['min_authority_level'] + 1}+ authority"
                ),
                "authority_level": authority,
                "amount": amount,
                "threshold": rule["amount_threshold"],
            }

    return {
        "user_id": user_id,
        "resource_type": resource_type,
        "can_approve": True,
        "reason": "All approval criteria met",
        "authority_level": authority,
        "rule": rule["label"],
    }


def resolve_approvers(
    db: Session,
    resource_type: str,
    org_unit_id: Optional[int] = None,
) -> List[Dict[str, Any]]:
    rule = APPROVAL_RULES.get(resource_type)
    if not rule:
        return []

    min_level = rule["min_authority_level"]
    required_dept = rule.get("department")

    query = db.query(Employee).filter(
        Employee.authority_level.isnot(None),
        Employee.authority_level >= min_level,
    )

    if required_dept:
        query = query.filter(
            Employee.department.ilike(f"%{required_dept}%")
        )

    if org_unit_id is not None and rule.get("org_unit_required"):
        query = query.filter(Employee.org_unit_id == org_unit_id)

    approvers = query.order_by(Employee.authority_level.desc()).all()

    return [
        {
            "id": emp.id,
            "user_id": emp.user_id,
            "employee_code": emp.employee_code,
            "department": emp.department,
            "position": emp.position,
            "authority_level": emp.authority_level,
            "org_unit_id": emp.org_unit_id,
            "reporting_manager_id": emp.reporting_manager_id,
        }
        for emp in approvers
    ]


def get_approval_chain(
    db: Session,
    user_id: int,
    resource_type: str,
) -> List[Dict[str, Any]]:
    rule = APPROVAL_RULES.get(resource_type)
    if not rule:
        return []

    chain = get_user_chain(db, user_id)
    min_level = rule["min_authority_level"]

    approvers: List[Dict[str, Any]] = []
    for entry in chain:
        level = entry.get("authority_level") or 0
        if level >= min_level:
            approvers.append(entry)

    return approvers

