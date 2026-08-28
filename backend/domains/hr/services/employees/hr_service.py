"""HR core service — COI, disciplinary, offboarding, alumni, HSE incidents,
employee addresses/dependents/risk scores, and HR dashboard read model.

Consolidates hr_service.py, hr_write_service.py, and hr_dashboard_service.py.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from infrastructure.database.database import get_db
from domains.hr.models.employee_models import AlumniNetwork, Employee
from domains.hr.models.employee_models import EmployeeAddress
from domains.hr.models.employee_models import EmployeeDependent
from domains.hr.models.employee_models import EmployeeRiskScore
from domains.country.utils.country_rls import enforce_country_access
logger = logging.getLogger(__name__)


def check_coi_conflict(employee_id: int, db: Session) -> list[dict]:
    rows = db.execute(text("""
        SELECT cr.id, cr.employee_id, cr.conflict_type, cr.description, cr.status
        FROM coi_reports cr
        WHERE cr.employee_id = :eid AND cr.status IN ('open', 'under_review')
        ORDER BY cr.created_at DESC
    """), {"eid": employee_id}).fetchall()
    return [
        {
            "id": r[0],
            "employee_id": r[1],
            "conflict_type": r[2],
            "description": r[3],
            "status": r[4],
        }
        for r in rows
    ]


def create_coi_report(employee_id: int, report_data: dict, db: Session) -> dict:
    db.execute(text("""
        INSERT INTO coi_reports (employee_id, conflict_type, description, status, created_at)
        VALUES (:eid, :ctype, :desc, 'open', :now)
    """), {
        "eid": employee_id,
        "ctype": report_data.get("conflict_type", "general"),
        "desc": report_data.get("description", ""),
        "now": datetime.now(timezone.utc).replace(tzinfo=None),
    })
    db.commit()
    return {"employee_id": employee_id, "status": "open"}


def create_disciplinary_case(employee_id: int, case_data: dict, db: Session) -> dict:
    db.execute(text("""
        INSERT INTO disciplinary_cases (employee_id, case_type, description, severity, status, created_at)
        VALUES (:eid, :ctype, :desc, :sev, 'open', :now)
    """), {
        "eid": employee_id,
        "ctype": case_data.get("case_type", "verbal_warning"),
        "desc": case_data.get("description", ""),
        "sev": case_data.get("severity", "low"),
        "now": datetime.now(timezone.utc).replace(tzinfo=None),
    })
    db.commit()
    return {"employee_id": employee_id, "status": "open"}


def get_disciplinary_cases(db: Session) -> list[dict]:
    rows = db.execute(text("""
        SELECT id, employee_id, case_type, description, severity, status, created_at
        FROM disciplinary_cases ORDER BY created_at DESC LIMIT 200
    """)).fetchall()
    return [
        {
            "id": r[0],
            "employee_id": r[1],
            "case_type": r[2],
            "description": r[3],
            "severity": r[4],
            "status": r[5],
        }
        for r in rows
    ]


def create_offboarding_case(employee_id: int, case_data: dict, db: Session) -> dict:
    db.execute(text("""
        INSERT INTO offboarding_cases (employee_id, reason, last_day, status, created_at)
        VALUES (:eid, :reason, :last_day, 'pending', :now)
    """), {
        "eid": employee_id,
        "reason": case_data.get("reason", "resignation"),
        "last_day": case_data.get("last_day"),
        "now": datetime.now(timezone.utc).replace(tzinfo=None),
    })
    db.commit()
    return {"employee_id": employee_id, "status": "pending"}


def get_offboarding_cases(db: Session) -> list[dict]:
    rows = db.execute(text("""
        SELECT id, employee_id, reason, last_day, status, created_at
        FROM offboarding_cases ORDER BY created_at DESC LIMIT 200
    """)).fetchall()
    return [
        {
            "id": r[0],
            "employee_id": r[1],
            "reason": r[2],
            "last_day": r[3],
            "status": r[4],
        }
        for r in rows
    ]


def register_address(employee_id: int, address_data: dict, db: Session) -> dict:
    db.execute(text("""
        INSERT INTO addresses (user_id, label, full_name, phone, address_line1, address_line2,
                               city, state, postal_code, country, is_default, created_at)
        SELECT e.user_id, :label, :full_name, :phone, :line1, :line2, :city, :state, :postal, :country, :is_def, :now
        FROM employees e WHERE e.id = :eid
    """), {
        "eid": employee_id,
        "label": address_data.get("label", "home"),
        "full_name": address_data.get("full_name", ""),
        "phone": address_data.get("phone"),
        "line1": address_data.get("address_line1", ""),
        "line2": address_data.get("address_line2"),
        "city": address_data.get("city"),
        "state": address_data.get("state"),
        "postal": address_data.get("postal_code"),
        "country": address_data.get("country", "OM"),
        "is_def": address_data.get("is_default", False),
        "now": datetime.now(timezone.utc).replace(tzinfo=None),
    })
    db.commit()
    return {"employee_id": employee_id, "status": "registered"}


def register_dependent(employee_id: int, dependent_data: dict, db: Session) -> dict:
    db.execute(text("""
        INSERT INTO employee_dependents (employee_id, name, relation, dob, is_insured, created_at)
        VALUES (:eid, :name, :relation, :dob, :insured, :now)
    """), {
        "eid": employee_id,
        "name": dependent_data.get("name", ""),
        "relation": dependent_data.get("relation", "child"),
        "dob": dependent_data.get("dob"),
        "insured": dependent_data.get("is_insured", False),
        "now": datetime.now(timezone.utc).replace(tzinfo=None),
    })
    db.commit()
    return {"employee_id": employee_id, "status": "registered"}


def validate_gcc_compliance(employee_id: int, db: Session) -> dict:
    """Validate GCC compliance checks: Nitaqat, WPS, and Iqama."""
    from datetime import date

    emp = db.query(Employee).filter(Employee.id == employee_id).first()
    if not emp:
        return {"employee_id": employee_id, "compliant": None, "reason": "Employee not found"}

    checks = {}
    today = date.today()

    iqama_doc = db.execute(text("""
        SELECT ed.id, ed.expiry_date, ed.status
        FROM employee_documents ed
        WHERE ed.employee_id = :eid AND ed.document_type = 'iqama'
        ORDER BY ed.created_at DESC LIMIT 1
    """), {"eid": employee_id}).fetchone()

    if iqama_doc:
        iqama_valid = iqama_doc[2] == "verified" and (iqama_doc[1] is None or iqama_doc[1] >= today)
        checks["iqama"] = {"status": "pass" if iqama_valid else "fail", "verified": iqama_doc[2] == "verified", "expired": iqama_doc[1] is not None and iqama_doc[1] < today}
    else:
        checks["iqama"] = {"status": "fail", "reason": "No iqama document on file"}

    wps_check = db.execute(text("""
        SELECT COUNT(*) FROM payroll_records pr
        WHERE pr.employee_id = :eid AND pr.wps_submitted = 1
        AND pr.period_month = :month AND pr.period_year = :year
    """), {"eid": employee_id, "month": today.month, "year": today.year}).fetchone()
    checks["wps"] = {"status": "pass" if wps_check and wps_check[0] > 0 else "pending", "current_month_submitted": wps_check[0] > 0 if wps_check else False}

    nitaqat_valid = emp.employment_status == "active" and emp.is_verified
    checks["nitaqat"] = {"status": "pass" if nitaqat_valid else "review", "active": emp.employment_status == "active", "verified": emp.is_verified}

    all_pass = all(c.get("status") == "pass" for c in checks.values())
    return {"employee_id": employee_id, "compliant": all_pass, "checks": checks}


def get_employee_graph(employee_id: int, db: Session) -> dict:
    emp = db.query(Employee).filter(Employee.id == employee_id).first()
    if not emp:
        return {"error": "Employee not found"}
    return {
        "employee_id": employee_id,
        "employee_code": emp.employee_code,
        "department": emp.department,
        "reporting_manager_id": emp.reporting_manager_id,
    }


def add_address(employee_id: int, address_data: dict, db: Session):
    return register_address(employee_id, address_data, db)


def add_dependent(employee_id: int, dependent_data: dict, db: Session):
    return register_dependent(employee_id, dependent_data, db)


def check_coi(employee_id: int, db: Session):
    return {"conflicts": check_coi_conflict(employee_id, db)}


def create_coi(employee_id: int, report_data: dict, db: Session):
    return create_coi_report(employee_id, report_data, db)


def check_compliance(employee_id: int, db: Session):
    return validate_gcc_compliance(employee_id, db)


def get_graph(employee_id: int, db: Session):
    return get_employee_graph(employee_id, db)


def list_disciplinary(db: Session):
    return get_disciplinary_cases(db)


def add_disciplinary(case_data: dict, db: Session):
    employee_id = case_data.get("employee_id")
    if not employee_id:
        raise HTTPException(status_code=400, detail="employee_id required")
    return create_disciplinary_case(employee_id, case_data, db)


def list_offboarding(db: Session):
    return get_offboarding_cases(db)


def add_offboarding(case_data: dict, db: Session):
    employee_id = case_data.get("employee_id")
    if not employee_id:
        raise HTTPException(status_code=400, detail="employee_id required")
    return create_offboarding_case(employee_id, case_data, db)


def list_alumni(db: Session):
    rows = (
        db.query(AlumniNetwork, Employee)
        .join(Employee, Employee.id == AlumniNetwork.employee_id)
        .all()
    )
    return [
        {
            "id": a.id,
            "employee_id": a.employee_id,
            "full_name": getattr(emp, "full_name", None) or getattr(emp, "name", None)
            or getattr(emp, "employee_code", None),
            "reason": a.notes or a.status,
            "end_date": (a.eligibility_expires_at or a.granted_at).isoformat()
            if (a.eligibility_expires_at or a.granted_at)
            else None,
            "status": a.status,
        }
        for a, emp in rows
    ]


def list_hse_incidents(db: Session):
    rows = db.execute(text("""
        SELECT i.id, i.employee_id, e.employee_code, i.incident_type,
               i.description, i.date_occurred, i.severity, i.status
        FROM hse_incidents i
        LEFT JOIN employees e ON e.id = i.employee_id
        ORDER BY i.created_at DESC
    """)).fetchall()
    return [
        {
            "id": r[0],
            "employee_id": r[1],
            "employee_name": r[2],
            "incident_type": r[3],
            "description": r[4],
            "date_occurred": r[5],
            "severity": r[6],
            "status": r[7],
        }
        for r in rows
    ]


def create_hse_incident(incident: dict, db: Session):
    employee_id = incident.get("employee_id")
    if not employee_id:
        raise HTTPException(status_code=400, detail="employee_id required")
    db.execute(text("""
        INSERT INTO hse_incidents
            (employee_id, incident_type, description, date_occurred, severity, status, created_at)
        VALUES (:eid, :itype, :desc, :docc, :sev, :status, :created)
    """), {
        "eid": employee_id,
        "itype": incident.get("incident_type", "near_miss"),
        "desc": incident.get("description", ""),
        "docc": incident.get("date_occurred"),
        "sev": incident.get("severity", "low"),
        "status": incident.get("status", "open"),
        "created": datetime.now(timezone.utc).replace(tzinfo=None),
    })
    db.commit()
    return {"message": "HSE incident recorded", "employee_id": employee_id}


# ── Employee Addresses, Dependents, Risk Scores (merged from hr_write_service) ──

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


# ── HR Dashboard Read Model (merged from hr_dashboard_service.py) ────────────

def _country_filter(country_code: Optional[str]) -> tuple[str, Dict[str, Any]]:
    """Return (where_clause, params) for optional country filtering."""
    if country_code:
        return " AND country_code = :country_code", {"country_code": country_code}
    return "", {}


def _apply_country_where(sql: str, country_where: str) -> str:
    """Safely inject a pre-validated WHERE fragment into a SQL string.

    The fragment comes from ``_country_filter`` which only returns
    hardcoded strings — never user input.
    """
    return sql.replace("{country_where}", country_where)


def get_hr_dashboard(
    db: Session,
    *,
    country_code: Optional[str] = None,
    days: int = 7,
    current_user: Optional[dict] = None,
) -> Dict[str, Any]:
    """Return HR dashboard data: onboarding pipeline, performance health, activity feed."""
    enforce_country_access(country_code, db=db)
    result: Dict[str, Any] = {}
    country_where, country_params = _country_filter(country_code)

    now = _utcnow()
    base_params = {"days": days, "now": now, **country_params}

    # ── Onboarding Pipeline Stats ──
    try:
        pipeline_counts = db.execute(
            text(_apply_country_where("""
                SELECT
                    SUM(CASE WHEN status = 'in_progress' THEN 1 ELSE 0 END) as active,
                    SUM(CASE WHEN status = 'in_progress' AND due_date < :now THEN 1 ELSE 0 END) as overdue,
                    SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
                    SUM(CASE WHEN status = 'cancelled' THEN 1 ELSE 0 END) as cancelled
                FROM onboarding_pipelines
                WHERE 1=1 {country_where}
            """, country_where)),
            {**base_params},
        ).mappings().first()

        overdue_items = db.execute(
            text(_apply_country_where("""
                SELECT p.id, p.employee_id, p.current_step, p.total_steps,
                       p.completed_steps, p.due_date,
                       e.employee_code, e.department, e.position
                FROM onboarding_pipelines p
                LEFT JOIN hr.employees e ON e.id = p.employee_id
                WHERE p.status = 'in_progress' AND p.due_date < :now {country_where}
                ORDER BY p.due_date ASC
                LIMIT 20
            """, country_where)),
            {**base_params},
        ).mappings().all()

        result["onboarding"] = {
            "stats": dict(pipeline_counts) if pipeline_counts else {"active": 0, "overdue": 0, "completed": 0, "cancelled": 0},
            "overdue_items": [dict(r) for r in overdue_items],
        }
    except Exception as e:
        logger.warning("Onboarding data unavailable (migration may not be run): %s", e)
        result["onboarding"] = {"stats": {"active": 0, "overdue": 0, "completed": 0, "cancelled": 0}, "overdue_items": []}

    # ── Performance Health Board ──
    try:
        health_data = db.execute(
            text(_apply_country_where("""
                SELECT
                    SUM(CASE WHEN performance_score >= 4.0 THEN 1 ELSE 0 END) as green,
                    SUM(CASE WHEN performance_score >= 2.5 AND performance_score < 4.0 THEN 1 ELSE 0 END) as amber,
                    SUM(CASE WHEN performance_score < 2.5 AND performance_score IS NOT NULL THEN 1 ELSE 0 END) as red,
                    SUM(CASE WHEN performance_score IS NULL THEN 1 ELSE 0 END) as not_scored,
                    ROUND(AVG(performance_score), 2) as avg_score
                FROM hr.employees
                WHERE employment_status = 'active' {country_where}
            """, country_where)),
            {**base_params},
        ).mappings().first()

        top_performers = db.execute(
            text(_apply_country_where("""
                SELECT e.id, e.employee_code, e.department, e.position, e.performance_score
                FROM hr.employees e
                WHERE e.employment_status = 'active'
                  AND e.performance_score IS NOT NULL {country_where}
                ORDER BY e.performance_score DESC
                LIMIT 10
            """, country_where)),
            {**base_params},
        ).mappings().all()

        bottom_performers = db.execute(
            text(_apply_country_where("""
                SELECT e.id, e.employee_code, e.department, e.position, e.performance_score
                FROM hr.employees e
                WHERE e.employment_status = 'active'
                  AND e.performance_score IS NOT NULL {country_where}
                ORDER BY e.performance_score ASC
                LIMIT 5
            """, country_where)),
            {**base_params},
        ).mappings().all()

        result["performance"] = {
            "stats": dict(health_data) if health_data else {"green": 0, "amber": 0, "red": 0, "not_scored": 0, "avg_score": None},
            "top_performers": [dict(r) for r in top_performers],
            "bottom_performers": [dict(r) for r in bottom_performers],
        }
    except Exception as e:
        logger.warning("Performance data unavailable (performance_score column may not exist): %s", e)
        result["performance"] = {"stats": {"green": 0, "amber": 0, "red": 0, "not_scored": 0, "avg_score": None}, "top_performers": [], "bottom_performers": []}

    # ── Recent Activity Feed ──
    try:
        since_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        params = {**base_params, "since": since_date}

        activity = db.execute(
            text(_apply_country_where("""
                SELECT al.id, al.actor_employee_id, al.action, al.entity_type,
                       al.entity_id, al.target_employee_id, al.metadata_json, al.created_at,
                       ae.employee_code as actor_code,
                       te.employee_code as target_code
                FROM employee_activity_logs al
                LEFT JOIN hr.employees ae ON ae.id = al.actor_employee_id
                LEFT JOIN hr.employees te ON te.id = al.target_employee_id
                WHERE al.created_at >= :since {country_where}
                ORDER BY al.created_at DESC
                LIMIT 50
            """, country_where)),
            params,
        ).mappings().all()

        total_recent = len(activity)
        action_breakdown: Dict[str, int] = {}
        for a in activity:
            action = a["action"]
            action_breakdown[action] = action_breakdown.get(action, 0) + 1

        result["activity"] = {
            "total_events": total_recent,
            "action_breakdown": action_breakdown,
            "events": [
                {
                    "id": e["id"],
                    "actor_employee_id": e["actor_employee_id"],
                    "actor_code": e["actor_code"],
                    "action": e["action"],
                    "entity_type": e["entity_type"],
                    "target_code": e["target_code"],
                    "timestamp": e["created_at"].isoformat() if e["created_at"] else None,
                }
                for e in activity
            ],
        }
    except Exception as e:
        logger.warning("Activity data unavailable (table may not exist): %s", e)
        result["activity"] = {"total_events": 0, "action_breakdown": {}, "events": []}

    # ── Employee Counts ──
    try:
        emp_counts = db.execute(
            text(_apply_country_where("""
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN employment_status = 'active' THEN 1 ELSE 0 END) as active,
                    SUM(CASE WHEN employment_status = 'terminating' THEN 1 ELSE 0 END) as terminating,
                    SUM(CASE WHEN employment_status = 'terminated' THEN 1 ELSE 0 END) as terminated
                FROM hr.employees
                WHERE 1=1 {country_where}
            """, country_where)),
            {**base_params},
        ).mappings().first()
        result["employees"] = dict(emp_counts) if emp_counts else {"total": 0, "active": 0, "terminating": 0, "terminated": 0}
    except Exception as e:
        logger.warning("Employee counts unavailable: %s", e)
        result["employees"] = {"total": 0, "active": 0, "terminating": 0, "terminated": 0}

    result["dashboard_date"] = now.isoformat()
    return result


# ── Ghost Employee Watchdog (merged from ghost_watchdog_service.py) ───────────

def _ghost_to_iso(value):
    """Safely coerce a datetime-or-string value to an ISO string."""
    if value is None:
        return None
    if isinstance(value, str):
        return value
    try:
        return value.isoformat()
    except AttributeError:
        return str(value)


class GhostEmployeeWatchdog:
    """Detects employees with no activity but still active in payroll."""

    def __init__(self, db: Session):
        self.db = db

    def find_ghost_employees(self, days_threshold: int = 90) -> List[dict]:
        from datetime import datetime, timedelta, timezone
        from sqlalchemy import and_, func
        from domains.hr.models.employee_models import EmployeeAttendance
        from domains.hr.models.employee_models import EmployeeWorkLog
        from domains.finance.models.finance import TreasuryAccount

        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_threshold)

        recent_attendance = (
            self.db.query(EmployeeAttendance.employee_id)
            .filter(EmployeeAttendance.scan_in_time >= cutoff_date)
            .distinct()
            .subquery()
        )

        recent_work_logs = (
            self.db.query(EmployeeWorkLog.employee_id)
            .filter(EmployeeWorkLog.work_date >= cutoff_date)
            .distinct()
            .subquery()
        )

        ghosts = (
            self.db.query(Employee)
            .filter(
                Employee.employment_status == "active",
                and_(
                    ~Employee.id.in_(recent_attendance),
                    ~Employee.id.in_(recent_work_logs),
                ),
            )
            .all()
        )

        ghost_ids = [emp.id for emp in ghosts]

        treasury_map: dict = {}
        if ghost_ids:
            treasury_map = {
                t.employee_id: t
                for t in self.db.query(TreasuryAccount)
                .filter(TreasuryAccount.employee_id.in_(ghost_ids))
                .all()
            }

        last_attendance_map: dict = {}
        last_worklog_map: dict = {}
        if ghost_ids:
            att_rows = (
                self.db.query(
                    EmployeeAttendance.employee_id,
                    func.max(EmployeeAttendance.scan_in_time).label("max_scan"),
                )
                .filter(EmployeeAttendance.employee_id.in_(ghost_ids))
                .group_by(EmployeeAttendance.employee_id)
                .all()
            )
            last_attendance_map = {row.employee_id: row.max_scan for row in att_rows}

            wl_rows = (
                self.db.query(
                    EmployeeWorkLog.employee_id,
                    func.max(EmployeeWorkLog.work_date).label("max_date"),
                )
                .filter(EmployeeWorkLog.employee_id.in_(ghost_ids))
                .group_by(EmployeeWorkLog.employee_id)
                .all()
            )
            last_worklog_map = {row.employee_id: row.max_date for row in wl_rows}

        results = []
        for emp in ghosts:
            treasury = treasury_map.get(emp.id)
            last_attendance = last_attendance_map.get(emp.id)
            last_worklog = last_worklog_map.get(emp.id)
            activities = [a for a in [last_attendance, last_worklog] if a]
            last_active = max(activities) if activities else None

            results.append({
                "employee_id": emp.id,
                "employee_code": emp.employee_code,
                "name": f"{emp.first_name} {emp.last_name}",
                "last_active": last_active,
                "payroll_active": treasury is not None,
                "risk_level": "high" if treasury else "medium",
            })

        return results

    def flag_for_review(self, employee_id: int, reason: str) -> dict:
        return {
            "employee_id": employee_id,
            "flagged": True,
            "reason": reason,
            "requires_review": True,
        }

    def generate_ghost_report(self, days_threshold: int = 90) -> dict:
        from datetime import datetime, timezone
        ghosts = self.find_ghost_employees(days_threshold)
        return {
            "report_generated_at": datetime.now(timezone.utc).isoformat(),
            "threshold_days": days_threshold,
            "ghost_count": len(ghosts),
            "ghosts": ghosts,
        }


def get_ghost_watchdog(db: Session) -> GhostEmployeeWatchdog:
    return GhostEmployeeWatchdog(db)


def get_leave_balance(employee_id: int, current_user: dict, db: Session) -> list[dict]:
    rows = db.execute(text("""
        SELECT leave_type, year, allocated_days, used_days,
               carried_forward_days, pending_days,
               (allocated_days + carried_forward_days - used_days - pending_days) as remaining_days
        FROM employee_leave_ledgers
        WHERE employee_id = :eid
        ORDER BY year DESC, leave_type
    """), {"eid": employee_id}).mappings().all()
    return [dict(r) for r in rows]


def submit_expense(employee_id: int, expense_data: dict, current_user: dict, db: Session) -> dict:
    db.execute(text("""
        INSERT INTO expense_claims (employee_id, amount, currency, category, description, status, created_at)
        VALUES (:eid, :amount, :currency, :category, :description, 'pending', :now)
    """), {
        "eid": employee_id,
        "amount": expense_data.get("amount", 0),
        "currency": expense_data.get("currency", "USD"),
        "category": expense_data.get("category", "general"),
        "description": expense_data.get("description", ""),
        "now": datetime.now(timezone.utc).replace(tzinfo=None),
    })
    db.commit()
    return {"employee_id": employee_id, "status": "submitted"}


def assign_asset(employee_id: int, asset_type: str, asset_tag: str | None, current_user: dict, db: Session) -> dict:
    db.execute(text("""
        INSERT INTO employee_assets (employee_id, asset_type, asset_tag, assigned_at, status)
        VALUES (:eid, :atype, :tag, :now, 'assigned')
    """), {
        "eid": employee_id,
        "atype": asset_type,
        "tag": asset_tag or "",
        "now": datetime.now(timezone.utc).replace(tzinfo=None),
    })
    db.commit()
    return {"employee_id": employee_id, "asset_type": asset_type, "status": "assigned"}


def list_disciplinary_cases(db: Session, limit: int, cursor: str | None) -> dict:
    from domains.hr.models.employee_models import DisciplinaryCase
    from infrastructure.utils.pagination import keyset_paginate
    query = db.query(DisciplinaryCase)
    return keyset_paginate(query, sort_keys=[(DisciplinaryCase.id, "asc")], cursor=cursor, page_size=limit)


def list_offboarding_cases(db: Session, limit: int, cursor: str | None) -> dict:
    from domains.hr.models.employee_models import OffboardingCase
    from infrastructure.utils.pagination import keyset_paginate
    query = db.query(OffboardingCase)
    return keyset_paginate(query, sort_keys=[(OffboardingCase.id, "asc")], cursor=cursor, page_size=limit)
