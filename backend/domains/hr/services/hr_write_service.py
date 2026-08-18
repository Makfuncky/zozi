"""Backward-compatible re-export shim for HR write operations.

This module intentionally performs NO imports at module-load time. It used to
re-export handler functions from `controllers.hr.hr_controller`, which created an
import-time circular-import cycle (`hr_controller` -> `hr_write_service` ->
`hr_controller`). Resolving names lazily via module-level `__getattr__` breaks
that cycle: the underlying controller module is only imported on first
attribute access, by which point the importing module is fully initialised.
"""
from __future__ import annotations

import importlib
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session


_REEXPORTS: dict[str, tuple[str, str]] = {
    "create_coi_report": ("controllers.hr.hr_controller", "create_coi_report"),
    "create_disciplinary_case": ("controllers.hr.hr_controller", "create_disciplinary_case"),
    "create_offboarding_case": ("controllers.hr.hr_controller", "create_offboarding_case"),
}


def __getattr__(name: str) -> Any:
    if name in _REEXPORTS:
        module_path, attr = _REEXPORTS[name]
        return getattr(importlib.import_module(module_path), attr)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


from datetime import datetime, timezone
from typing import Optional

from domains.hr.models.employee_models import EmployeeAddress
from domains.hr.models.employee_models import EmployeeDependent
from domains.hr.models.employee_models import EmployeeRiskScore
import structlog
logger = structlog.get_logger(__name__)


def _is_orm(obj, Model) -> bool:
    return isinstance(obj, Model)


def _apply_changes(record, changes):
    for field, value in (changes or {}).items():
        if value is None:
            continue
        if hasattr(record, field):
            setattr(record, field, value)
    return record


def _level_from_score(score: float) -> str:
    if score >= 80:
        return "low"
    if score >= 50:
        return "medium"
    return "high"


def create_employee_address(
    db: Session,
    *,
    employee_id: int,
    address_type: str,
    street: str,
    city: str,
    state: Optional[str] = None,
    postal_code: Optional[str] = None,
    country_code: Optional[str] = None,
    is_primary: bool = False,
    **data,
) -> EmployeeAddress:
    record = EmployeeAddress(
        employee_id=employee_id,
        address_type=address_type,
        street=street,
        city=city,
        state=state,
        postal_code=postal_code,
        country_code=country_code,
        is_primary=is_primary,
        **data,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def create_employee_dependent(
    db: Session,
    *,
    employee_id: int,
    name: str,
    relation: str,
    dob: Optional[object] = None,
    is_insured: bool = False,
    **data,
) -> EmployeeDependent:
    record = EmployeeDependent(
        employee_id=employee_id,
        name=name,
        relation=relation,
        dob=dob,
        is_insured=is_insured,
        **data,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def upsert_employee_risk_score(
    db: Session,
    *args,
    employee_id: Optional[int] = None,
    assessment_date=None,
    score: float = 0.0,
    risk_level: Optional[str] = None,
    factors: Optional[dict] = None,
    notes: Optional[str] = None,
    country_code: Optional[str] = None,
    **data,
) -> EmployeeRiskScore:
    # Support the legacy controller form ``upsert_employee_risk_score(db, employee_id, metric, score)``.
    if args:
        if employee_id is None and len(args) >= 1:
            employee_id = args[0]
        if len(args) >= 2:
            score = args[1]
        if len(args) >= 3 and not factors:
            factors = {"metric": args[2]}
    if assessment_date is None:
        assessment_date = datetime.now(timezone.utc).date()
    risk_level = risk_level or _level_from_score(float(score))
    existing = (
        db.query(EmployeeRiskScore)
        .filter(
            EmployeeRiskScore.employee_id == employee_id,
            EmployeeRiskScore.assessment_date == assessment_date,
        )
        .first()
    )
    if existing is not None:
        _apply_changes(
            existing,
            {
                "score": score,
                "risk_level": risk_level,
                "factors": factors,
                "notes": notes,
                "country_code": country_code,
                **data,
            },
        )
        db.commit()
        db.refresh(existing)
        return existing

    record = EmployeeRiskScore(
        employee_id=employee_id,
        assessment_date=assessment_date,
        score=score,
        risk_level=risk_level,
        factors=factors,
        notes=notes,
        country_code=country_code,
        **data,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def create_hse_incident(
    db: Session,
    employee_id: int,
    incident_type: str = "near_miss",
    description: str = "",
    date_occurred: str | None = None,
    severity: str = "low",
    status: str = "open",
) -> dict:
    """Create an HSE incident record."""
    created = datetime.now(timezone.utc).replace(tzinfo=None)
    result = db.execute(
        text("""
            INSERT INTO hse_incidents
                (employee_id, incident_type, description, date_occurred, severity, status, created_at)
            VALUES (:eid, :itype, :desc, :docc, :sev, :status, :created)
            RETURNING id
        """),
        {
            "eid": employee_id,
            "itype": incident_type,
            "desc": description,
            "docc": date_occurred,
            "sev": severity,
            "status": status,
            "created": created,
        },
    )
    incident_id = result.fetchone()[0]
    db.commit()
    return {"message": "HSE incident recorded", "employee_id": employee_id, "incident_id": incident_id}