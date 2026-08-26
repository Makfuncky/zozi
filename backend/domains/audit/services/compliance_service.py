"""Canonical cross-cutting audit primitive.

This module is the **single** implementation of `AuditAction` / `audit_log`
for the whole backend. It lives in `utils/` because every layer
(`routers`, `controllers`, `services`, `jobs`, `events`) needs to record audit
events, and the circuit contract (ARCHITECTURE_DIAGRAM.md 10.2) allows every
layer to import `utils` while `utils` imports nothing above it.

Historically two divergent implementations existed:

* ``controllers/audit_controller.py``  rich signature
  (``user_id`` / ``resource_type`` / ``resource_id`` / ``status``) used by ~200
  call sites. Importing it violated rule **W3** (mis-housed controller).
* ``utils/audit.py``  narrow signature (``actor_id`` / ``entity`` /
  ``entity_key``). A previous refactor repointed dozens of call sites at this
  module *without* adapting the keyword arguments, so those calls raised
  ``TypeError`` at runtime and every audit trail silently died.

``audit_log`` below accepts **both** calling conventions so no call site can
break, and ``AuditAction`` carries the union of both catalogues.
"""
from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, Optional, Union
from uuid import UUID

import structlog
from sqlalchemy.orm import Session

from domains.governance.models.core import AuditLog
from infrastructure.utils.logging_config import get_request_id

logger = structlog.get_logger(__name__)

__all__ = ["AuditAction", "audit_log", "coerce_json_safe"]


class AuditAction:
    """Canonical catalogue of audit action names.

    Values are plain strings; the class is a namespace, not an enum, so that
    ``AuditAction.ANYTHING_NEW`` style additions stay cheap and callers can also
    pass raw strings.
    """

    # -- Generic CRUD / workflow (legacy infrastructure.utils.audit vocabulary) -------------
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    PUBLISH = "publish"
    ROLLBACK = "rollback"
    APPROVE = "approve"
    REJECT = "reject"
    CREATE_DRAFT = "create_draft"
    LOGIN = "login"
    EXPORT = "export"
    VIEW = "view"

    # -- Identity / session --------------------------------------------------
    LOGIN_SUCCESS = "LOGIN_SUCCESS"
    LOGIN_FAILED = "LOGIN_FAILED"
    LOGOUT = "LOGOUT"
    PASSWORD_RESET = "PASSWORD_RESET"
    PASSWORD_CHANGED = "PASSWORD_CHANGED"
    PASSWORD_FORCE_RESET = "PASSWORD_FORCE_RESET"
    EMAIL_VERIFIED = "EMAIL_VERIFIED"
    REGISTER = "REGISTER"
    TOKEN_REFRESH = "TOKEN_REFRESH"
    ACCOUNT_LOCKED = "ACCOUNT_LOCKED"
    MFA_ENABLED = "MFA_ENABLED"
    MFA_DISABLED = "MFA_DISABLED"
    MFA_ENFORCED = "MFA_ENFORCED"
    PROFILE_UPDATED = "PROFILE_UPDATED"
    ROLE_CHANGED = "ROLE_CHANGED"

    # -- User / staff administration -----------------------------------------
    STAFF_CREATED = "STAFF_CREATED"
    STAFF_UPDATED = "STAFF_UPDATED"
    STAFF_DELETED = "STAFF_DELETED"
    USER_DELETE = "USER_DELETE"
    USER_TOGGLED_ACTIVE = "USER_TOGGLED_ACTIVE"
    BULK_USER_TOGGLE_ACTIVE = "BULK_USER_TOGGLE_ACTIVE"
    BULK_USER_ROLE_UPDATE = "BULK_USER_ROLE_UPDATE"

    # -- Permissions / IAM ---------------------------------------------------
    PERMISSION_GRANT = "PERMISSION_GRANT"
    PERMISSION_REVOKE = "PERMISSION_REVOKE"
    PERMISSION_APPROVE = "PERMISSION_APPROVE"
    PERMISSION_REJECT = "PERMISSION_REJECT"

    # -- Catalog -------------------------------------------------------------
    PRODUCT_UPLOAD = "PRODUCT_UPLOAD"
    PRODUCT_BULK_UPLOAD = "PRODUCT_BULK_UPLOAD"
    PRODUCT_UPDATE = "PRODUCT_UPDATE"
    PRODUCT_DELETE = "PRODUCT_DELETE"
    PRODUCT_MODERATED = "PRODUCT_MODERATED"

    # -- Marketing / promotions ----------------------------------------------
    COUPON_CREATED = "COUPON_CREATED"
    COUPON_DELETED = "COUPON_DELETED"
    BANNER_CREATED = "BANNER_CREATED"
    BANNER_UPDATED = "BANNER_UPDATED"
    BANNER_DELETED = "BANNER_DELETED"
    BANNER_IMAGE_UPLOADED = "BANNER_IMAGE_UPLOADED"
    BANNER_REORDERED = "BANNER_REORDERED"
    FLASH_SALE_CREATED = "FLASH_SALE_CREATED"
    FLASH_SALE_UPDATED = "FLASH_SALE_UPDATED"
    FLASH_SALE_DELETED = "FLASH_SALE_DELETED"

    # -- Customer data -------------------------------------------------------
    ADDRESS_CREATED = "ADDRESS_CREATED"
    ADDRESS_UPDATED = "ADDRESS_UPDATED"
    ADDRESS_DELETED = "ADDRESS_DELETED"
    ADDRESS_SET_DEFAULT = "ADDRESS_SET_DEFAULT"

    # -- Orders / fulfilment -------------------------------------------------
    ORDER_CREATED = "ORDER_CREATED"
    ORDER_STATUS_CHANGED = "ORDER_STATUS_CHANGED"
    ORDER_STATUS_UPDATED = "ORDER_STATUS_UPDATED"
    ORDER_REFUNDED = "ORDER_REFUNDED"
    ORDER_DELETE = "ORDER_DELETE"
    SHIPMENT_STATUS_UPDATED = "SHIPMENT_STATUS_UPDATED"
    RETURN_REQUEST_CREATED = "RETURN_REQUEST_CREATED"
    RETURN_REQUEST_UPDATED = "RETURN_REQUEST_UPDATED"

    # -- Supplier / logistics ------------------------------------------------
    SUPPLIER_VERIFIED = "SUPPLIER_VERIFIED"
    SUPPLIER_REJECTED = "SUPPLIER_REJECTED"
    LOGISTICS_PARTNER_CREATED = "LOGISTICS_PARTNER_CREATED"
    COMMISSION_RATE_CHANGED = "COMMISSION_RATE_CHANGED"

    # -- Finance / treasury --------------------------------------------------
    INVOICE_CREATED = "INVOICE_CREATED"
    INVOICE_STATUS_UPDATED = "INVOICE_STATUS_UPDATED"
    PAYOUT_REQUESTED = "PAYOUT_REQUESTED"
    PAYOUT_PROCESSED = "PAYOUT_PROCESSED"
    PAYOUT_VERIFIED = "PAYOUT_VERIFIED"
    PAYOUT_APPROVED = "PAYOUT_APPROVED"
    PAYOUT_REJECTED = "PAYOUT_REJECTED"
    JOURNAL_ENTRY_CREATED = "JOURNAL_ENTRY_CREATED"
    JOURNAL_ENTRY_APPROVED = "JOURNAL_ENTRY_APPROVED"
    JOURNAL_ENTRY_REJECTED = "JOURNAL_ENTRY_REJECTED"
    TREASURY_TRANSACTION_CREATED = "TREASURY_TRANSACTION_CREATED"
    CASH_TRANSACTION_CREATED = "CASH_TRANSACTION_CREATED"
    VAT_REMITTANCE_CREATED = "VAT_REMITTANCE_CREATED"
    BANK_TRANSACTION_CREATED = "BANK_TRANSACTION_CREATED"
    BANK_TRANSACTION_RECONCILED = "BANK_TRANSACTION_RECONCILED"
    BANK_TRANSACTION_FLAGGED = "BANK_TRANSACTION_FLAGGED"
    ACCOUNT_CREATED = "ACCOUNT_CREATED"
    ACCOUNT_GROUP_CREATED = "ACCOUNT_GROUP_CREATED"
    CHART_OF_ACCOUNTS_SEEDED = "CHART_OF_ACCOUNTS_SEEDED"
    TRIAL_BALANCE_VIEWED = "TRIAL_BALANCE_VIEWED"
    FINANCIAL_REPORT_GENERATED = "FINANCIAL_REPORT_GENERATED"
    FINANCIAL_SETTINGS_UPDATED = "FINANCIAL_SETTINGS_UPDATED"
    PERIOD_CLOSED = "PERIOD_CLOSED"
    REFUND_PROCESSED = "REFUND_PROCESSED"
    PAYROLL_PROCESSED = "PAYROLL_PROCESSED"
    EOSB_CALCULATED = "EOSB_CALCULATED"
    CASH_FORECAST_GENERATED = "CASH_FORECAST_GENERATED"

    # -- Risk / compliance / lifecycle ---------------------------------------
    FRAUD_FLAG = "FRAUD_FLAG"
    DATA_EXPORTED = "DATA_EXPORTED"
    ARCHIVE = "ARCHIVE"
    RESTORE = "RESTORE"
    BULK_ARCHIVE = "BULK_ARCHIVE"
    BULK_RESTORE = "BULK_RESTORE"
    PERMANENT_DELETE = "PERMANENT_DELETE"
    INBOX_RESET = "INBOX_RESET"

    @classmethod
    def get_archive_action(cls, entity_name: str) -> str:
        return f"{entity_name.upper()}_ARCHIVE"

    @classmethod
    def get_restore_action(cls, entity_name: str) -> str:
        return f"{entity_name.upper()}_RESTORE"

    @classmethod
    def get_bulk_archive_action(cls, entity_name: str) -> str:
        return f"BULK_{entity_name.upper()}_ARCHIVE"

    @classmethod
    def get_bulk_restore_action(cls, entity_name: str) -> str:
        return f"BULK_{entity_name.upper()}_RESTORE"


def coerce_json_safe(value: Any) -> Any:
    """Recursively convert `value` into something a JSON column accepts."""
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, Enum):
        return coerce_json_safe(value.value)
    if isinstance(value, dict):
        return {str(k): coerce_json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set, frozenset)):
        return [coerce_json_safe(v) for v in value]
    return str(value)


def _as_entity_id(raw: Any) -> Optional[int]:
    if raw is None or isinstance(raw, bool):
        return None
    if isinstance(raw, int):
        return raw
    text = str(raw).strip()
    if text.isdigit() or (text.startswith("-") and text[1:].isdigit()):
        try:
            return int(text)
        except ValueError:
            return None
    return None


def audit_log(
    db: Session,
    action: str = "",
    user_id: Optional[int] = None,
    username: Optional[str] = None,
    user_role: Optional[str] = None,
    resource_type: Optional[str] = None,
    resource_id: Optional[Union[int, str]] = None,
    details: Optional[Dict[str, Any]] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    status: str = "success",
    *,
    actor_id: Optional[int] = None,
    entity: Optional[str] = None,
    entity_key: Optional[Union[int, str]] = None,
    before: Optional[Dict[str, Any]] = None,
    after: Optional[Dict[str, Any]] = None,
    country_code: Optional[str] = None,
) -> bool:
    """Persist one audit event. Never raises.

    Two equivalent calling conventions are supported:

    ``audit_log(db, action=..., user_id=..., resource_type=..., resource_id=...)``
    ``audit_log(db, action=..., actor_id=..., entity=..., entity_key=...)``

    Returns ``True`` when the row was committed, ``False`` otherwise. Failures
    are logged and swallowed: auditing must never break the business flow.
    """
    effective_user_id = user_id if user_id is not None else actor_id
    if effective_user_id is not None and effective_user_id <= 0:
        effective_user_id = None
    effective_type = resource_type or entity or "unknown"
    effective_key = resource_id if resource_id is not None else entity_key

    payload: Dict[str, Any] = {}
    if before is not None:
        payload["before"] = coerce_json_safe(before)
    if after is not None:
        payload["after"] = coerce_json_safe(after)
    if details:
        payload.update(coerce_json_safe(details))
    if status and status != "success":
        payload.setdefault("status", status)
    entity_id = _as_entity_id(effective_key)
    if entity_id is None and effective_key not in (None, ""):
        # Preserve non-numeric identifiers (uuid / slug) instead of dropping them.
        payload.setdefault("resource_id", str(effective_key))
    if user_agent:
        payload.setdefault("user_agent", user_agent)
    if country_code:
        payload.setdefault("country_code", country_code)
    request_id = get_request_id()
    if request_id:
        payload.setdefault("request_id", request_id)

    try:
        entry = AuditLog(
            action=action or AuditAction.UPDATE,
            entity_type=effective_type,
            entity_id=entity_id,
            user_id=effective_user_id,
            username=username or (details or {}).get("username"),
            user_role=user_role or (details or {}).get("role"),
            details=payload or None,
            ip_address=ip_address,
            created_at=datetime.now(timezone.utc).replace(tzinfo=None),
        )
        db.add(entry)
        db.commit()
        return True
    except Exception as exc:  # pragma: no cover - defensive, audit must not raise
        logger.warning(
            "audit_log_failed",
            action=action,
            entity=effective_type,
            error=str(exc),
        )
        try:
            db.rollback()
        except Exception:
            pass
        return False



# === Merged from auth_service.py ===

"""Auto-migrated service logic from routers/auth.py."""

import domains.country.services as auth_svc

from domains.governance.services.auth.auth_service_accounts import LoginRequest
from domains.governance.services.auth.auth_service_accounts import RefreshRequest
from domains.governance.services.auth.auth_service_accounts import _find_user
from domains.governance.services.auth.auth_service_accounts import _record_login_history
from domains.governance.services.auth.auth_service_accounts import bearer_scheme
from domains.governance.services.auth.auth_service_accounts import csrf_token
from domains.governance.services.auth.auth_service_accounts import logger
from domains.governance.services.auth.auth_service_accounts import login
from domains.governance.services.auth.auth_service_accounts import logout
from domains.governance.services.auth.auth_service_accounts import me
from domains.governance.services.auth.auth_service_accounts import refresh
from domains.governance.services.auth.auth_service_accounts import register

import logging

import uuid

from datetime import datetime, timezone

from fastapi import Depends, HTTPException, Request, status

from fastapi.encoders import jsonable_encoder

from fastapi.responses import JSONResponse

from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from pydantic import BaseModel

from sqlalchemy.orm import Session

from infrastructure.database.database import get_db

from infrastructure.database.schemas import RegisterRequest, TokenResponse, UserOut

from middleware.csrf_middleware import generate_csrf_token

from domains.governance.models.user import User
from domains.governance.models.user import UserLoginHistory

from infrastructure.utils.audit import AuditAction, audit_log

from infrastructure.utils.auth import (
    blacklist_token,
    create_access_token,
    create_refresh_token,
    decode_token,
    get_password_hash,
    verify_password,
)

from infrastructure.utils.config import settings

from infrastructure.utils.dependencies import get_current_user

from infrastructure.utils.ip_utils import get_request_ip

def login(payload: LoginRequest, db: Session, request: Request):
    return auth_svc.login(payload=payload, db=db, request=request)

def register(payload: RegisterRequest, db: Session):
    return auth_svc.register(payload=payload, db=db)

def refresh(payload: RefreshRequest | None, request: Request, db: Session):
    return auth_svc.refresh(payload=payload, request=request, db=db)

def me(current_user: User):
    return auth_svc.me(current_user=current_user)

def csrf_token(request: Request):
    return auth_svc.csrf_token(request=request)

def logout(credentials: HTTPAuthorizationCredentials | None, current_user: User):
    return auth_svc.logout(credentials=credentials, current_user=current_user)




# === Merged from performance_service.py ===

"""Auto-migrated service logic from routers/performance.py."""

import logging

from typing import Any, Dict, List, Optional

from fastapi import Depends, HTTPException, Path, Query

from pydantic import BaseModel, Field

from sqlalchemy.orm import Session

from domains.accounts.services.auth.auth_service import get_current_user

from infrastructure.database.database import get_db

logger = logging.getLogger(__name__)

class ObjectiveCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=300, description="OKR objective title")
    cascade_level: str = Field(..., description="One of: company, department, team, individual")
    owner_employee_id: int = Field(..., description="Employee ID who owns this objective")
    quarter: Optional[str] = Field(None, description="e.g. Q1, Q2, Q3, Q4")
    year: Optional[int] = None
    parent_objective_id: Optional[int] = None
    org_unit_id: Optional[int] = None
    description: Optional[str] = None
    key_results: Optional[List[Dict[str, Any]]] = None
    weight: float = 1.0

class KpiCreate(BaseModel):
    objective_id: int
    employee_id: int
    metric_name: str = Field(..., min_length=1, max_length=200)
    target_value: float
    unit: str = "number"
    weight: float = 1.0
    auto_source_query: Optional[str] = None

class KpiValueUpdate(BaseModel):
    value: float
    source: Optional[str] = None

class ReviewSubmit(BaseModel):
    employee_id: int
    reviewer_id: int
    review_type: str = Field(..., description="One of: self, manager, peer, subordinate")
    score: float = Field(..., ge=0, le=5, description="Score 0-5")
    strengths: Optional[str] = None
    areas_for_improvement: Optional[str] = None
    comments: Optional[str] = None

class ObjectiveProgressUpdate(BaseModel):
    progress_pct: Optional[float] = None
    status: Optional[str] = None

def create_objective_endpoint(body: ObjectiveCreate, db: Session, current_user: dict):
    """Create an OKR objective at any cascade level (company → individual).
    Optionally accepts key_results to create KPIs in the same call.
    """
    from domains.hr.performance_service import create_objective
    try:
        result = create_objective(
            db=db,
            title=body.title,
            cascade_level=body.cascade_level,
            owner_employee_id=body.owner_employee_id,
            quarter=body.quarter,
            year=body.year,
            parent_objective_id=body.parent_objective_id,
            org_unit_id=body.org_unit_id,
            description=body.description,
            key_results=body.key_results,
            weight=body.weight,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

def get_objective_tree_endpoint(objective_id: int, db: Session, current_user: dict):
    """Get an objective with all its child objectives (aligned cascade)."""
    from domains.hr.performance_service import get_objective_tree
    result = get_objective_tree(db, objective_id)
    if not result:
        raise HTTPException(status_code=404, detail="Objective not found")
    return result

def update_objective_progress_endpoint(objective_id: int, body: ObjectiveProgressUpdate, db: Session, current_user: dict):
    """Update objective progress. Auto-computes from child KPIs if progress_pct not provided."""
    from domains.hr.performance_service import update_objective_progress
    return update_objective_progress(
        db, objective_id,
        progress_pct=body.progress_pct if body else None,
        status=body.status if body else None,
    )

def create_kpi_endpoint(body: KpiCreate, db: Session, current_user: dict):
    """Create a KPI metric tied to an objective."""
    from domains.hr.performance_service import create_kpi_metric
    return create_kpi_metric(
        db=db,
        objective_id=body.objective_id,
        employee_id=body.employee_id,
        metric_name=body.metric_name,
        target_value=body.target_value,
        unit=body.unit,
        weight=body.weight,
        auto_source_query=body.auto_source_query,
    )

def record_kpi_value_endpoint(kpi_id: int, body: KpiValueUpdate, db: Session, current_user: dict):
    """Record a new current value for a KPI metric and recalc objective progress."""
    if body is None:
        raise HTTPException(status_code=422, detail="Request body required")
    from domains.hr.performance_service import record_kpi_value
    return record_kpi_value(db, kpi_id, value=body.value, source=body.source)

def get_kpi_dashboard_endpoint(employee_id: int, db: Session, current_user: dict):
    """Get all KPIs and objectives for an employee."""
    from domains.hr.performance_service import get_kpi_dashboard
    return get_kpi_dashboard(db, employee_id)

def submit_review_endpoint(body: ReviewSubmit, db: Session, current_user: dict):
    """Submit a 360° performance review entry (self, manager, peer, subordinate)."""
    from domains.hr.performance_service import submit_performance_review
    try:
        return submit_performance_review(
            db=db,
            employee_id=body.employee_id,
            reviewer_id=body.reviewer_id,
            review_type=body.review_type,
            score=body.score,
            strengths=body.strengths,
            areas_for_improvement=body.areas_for_improvement,
            comments=body.comments,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

def get_employee_reviews_endpoint(employee_id: int, review_cycle: Optional[str], db: Session, current_user: dict):
    """Get all reviews for an employee, grouped by review type."""
    from domains.hr.performance_service import get_employee_reviews
    return get_employee_reviews(db, employee_id, review_cycle=review_cycle)

def compute_health_endpoint(employee_id: int, db: Session, current_user: dict):
    """Compute a Performance Health Score (red/amber/green) from multiple signals."""
    from domains.hr.performance_service import compute_performance_health
    result = compute_performance_health(db, employee_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result

def coi_check_endpoint(employee_id: int, db: Session, current_user: dict):
    """Run a simple conflict-of-interest check by examining employee relations
    and shared departments. Returns any detected conflicts."""
    try:
        from domains.hr.models.employee_models import Employee, EmployeeRelation
    except Exception as exc:
        logger.warning("EmployeeRelation model not available: %s", exc)
        return {"employee_id": employee_id, "has_conflicts": False, "conflicts": []}

    from sqlalchemy import or_

    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    conflicts = []

    # Check employee relations for potential conflicts
    try:
        relations = (
            db.query(EmployeeRelation)
            .filter(
                or_(
                    EmployeeRelation.employee_id == employee_id,
                    EmployeeRelation.internal_employee_id == employee_id,
                )
            )
            .all()
        )
    except Exception as exc:
        logger.warning("EmployeeRelation query failed (table may not exist): %s", exc)
        return {"employee_id": employee_id, "has_conflicts": False, "conflicts": []}

    for rel in relations:
        other_id = (
            rel.internal_employee_id
            if rel.employee_id == employee_id
            else rel.employee_id
        )
        other = db.query(Employee).filter(Employee.id == other_id).first()
        if other and other.department and employee.department:
            if other.department == employee.department:
                conflicts.append({
                    "type": "same_department",
                    "employee_id": other.id,
                    "employee_code": other.employee_code,
                    "relation_type": rel.relation_type,
                    "description": f"{employee.employee_code} and {other.employee_code} are in the same department ({employee.department}) with a {rel.relation_type} relation",
                    "severity": "medium",
                })

    # Check if employee's manager is a relative
    if employee.reporting_manager_id:
        manager = db.query(Employee).filter(Employee.id == employee.reporting_manager_id).first()
        if manager:
            for rel in relations:
                other_id = (
                    rel.internal_employee_id
                    if rel.employee_id == employee_id
                    else rel.employee_id
                )
                if other_id == manager.id:
                    conflicts.append({
                        "type": "manager_relation",
                        "employee_id": manager.id,
                        "employee_code": manager.employee_code,
                        "relation_type": rel.relation_type,
                        "description": f"{employee.employee_code}'s {rel.relation_type} ({manager.employee_code}) is their direct manager",
                        "severity": "high",
                    })

    return {
        "employee_id": employee_id,
        "employee_code": employee.employee_code,
        "has_conflicts": len(conflicts) > 0,
        "conflicts": conflicts,
    }

def health_board_endpoint(manager_employee_id: int, department: Optional[str], db: Session, current_user: dict):
    """Get a performance health board for all subordinates of a manager."""
    from domains.hr.performance_service import get_performance_health_board
    return get_performance_health_board(db, manager_employee_id, department=department)

