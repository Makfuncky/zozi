"""HR Employee Service — encapsulates all employee management business logic."""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import text, update
from sqlalchemy.orm import Session

from domains.hr.models.employee_models import (
    Employee,
    EmployeeDependent,
    EmployeeDocument,
    EmployeeLeaveRequest,
    EmployeeRelation,
    EmployeeShiftRoster,
    Office,
    OrgUnit,
)
from domains.accounts.models.core import Address
from domains.country.models.countries import CountryConfig
from domains.country.models.country_enhancements import (
    CountryHolidayCalendar,
    CountryLocalization,
)

logger = logging.getLogger(__name__)

_ALLOWED_OFFICE_COLUMNS = {
    col.name for col in Office.__table__.columns
} & {"name", "address", "city", "phone", "email", "latitude", "longitude", "is_active"}
_ALLOWED_EMPLOYEE_COLUMNS = {
    col.name for col in Employee.__table__.columns
} & {"user_id", "employee_code", "office_id", "department", "position",
     "employment_type", "employment_status", "salary", "currency", "hire_date", "notes"}
_ALLOWED_DOCUMENT_COLUMNS = {
    col.name for col in EmployeeDocument.__table__.columns
} & {"document_type", "document_name", "file_url", "expires_at", "notes", "status"}


def _safe_update(db: Session, model, allowed: set, row_id: int, data: dict) -> int:
    """Whitelist columns against the model's table, then issue a parameterised UPDATE.

    Returns the number of rows updated. The model is the SQLAlchemy mapped class;
    `allowed` is the set of column names that may be written (intersected with the
    model's actual columns so the check is anchored to the schema).
    """
    table_columns = {col.name for col in model.__table__.columns}
    safe_data = {
        k: v for k, v in data.items() if k in allowed and k in table_columns
    }
    if not safe_data:
        return 0
    stmt = update(model.__table__).where(model.__table__.c.id == row_id).values(**safe_data)
    result = db.execute(stmt)
    return result.rowcount or 0


class HREmployeeService:
    """Service for employee management operations."""

    def __init__(self, db: Session):
        self.db = db

    def list_offices(self, country_code: str, db: Session) -> List[dict]:
        rows = db.execute(
            text("SELECT * FROM offices WHERE country_code = :code ORDER BY name"),
            {"code": country_code},
        ).mappings().all()
        return [dict(r) for r in rows]

    def create_office(self, country_code: str, data: dict, db: Session) -> dict:
        result = db.execute(
            text("""
                INSERT INTO offices (name, address, city, phone, email, latitude, longitude, is_active, country_code)
                VALUES (:name, :address, :city, :phone, :email, :latitude, :longitude, :is_active, :country_code)
                RETURNING id
            """),
            {**data, "country_code": country_code},
        )
        office_id = result.scalar()
        db.commit()
        return {"id": office_id, "country_code": country_code, **data}

    def update_office(self, office_id: int, data: dict, db: Session) -> dict:
        safe_data = {k: v for k, v in data.items() if k in _ALLOWED_OFFICE_COLUMNS}
        if not safe_data:
            return {"id": office_id, **data}
        _safe_update(db, Office, _ALLOWED_OFFICE_COLUMNS, office_id, data)
        db.commit()
        return {"id": office_id, **safe_data}

    def delete_office(self, office_id: int, db: Session) -> None:
        db.execute(text("DELETE FROM offices WHERE id = :id"), {"id": office_id})
        db.commit()

    def list_employees(self, country_code: str, db: Session, **filters) -> List[dict]:
        query = "SELECT * FROM employees WHERE country_code = :code"
        params = {"code": country_code}
        if filters.get("department"):
            query += " AND department = :department"
            params["department"] = filters["department"]
        if filters.get("status"):
            query += " AND employment_status = :status"
            params["status"] = filters["status"]
        if filters.get("query"):
            query += " AND (employee_code LIKE :q OR position LIKE :q)"
            params["q"] = f"%{filters['query']}%"
        query += " ORDER BY created_at DESC LIMIT :limit"
        params["limit"] = filters.get("limit", 100)
        rows = db.execute(text(query), params).mappings().all()
        return [dict(r) for r in rows]

    def create_employee(self, country_code: str, data: dict, current_user: dict, db: Session) -> dict:
        result = db.execute(
            text("""
                INSERT INTO employees (user_id, employee_code, office_id, department, position,
                    employment_type, employment_status, salary, currency, hire_date, notes, country_code)
                VALUES (:user_id, :employee_code, :office_id, :department, :position,
                    :employment_type, :employment_status, :salary, :currency, :hire_date, :notes, :country_code)
                RETURNING id
            """),
            {**data, "country_code": country_code},
        )
        emp_id = result.scalar()
        db.commit()
        return {"id": emp_id, "country_code": country_code, **data}

    def get_employee(self, employee_id: int, db: Session) -> Optional[dict]:
        row = db.execute(
            text("SELECT * FROM employees WHERE id = :id"),
            {"id": employee_id},
        ).mappings().first()
        return dict(row) if row else None

    def get_employee_by_user_id(self, user_id: int) -> Optional[dict]:
        """Get employee record by user_id."""
        row = self.db.execute(
            text("SELECT * FROM employees WHERE user_id = :uid"),
            {"uid": user_id},
        ).mappings().first()
        return dict(row) if row else None

    def update_employee(self, employee_id: int, data: dict, current_user: dict, db: Session) -> dict:
        safe_data = {k: v for k, v in data.items() if k in _ALLOWED_EMPLOYEE_COLUMNS}
        if not safe_data:
            return {"id": employee_id, **data}
        _safe_update(db, Employee, _ALLOWED_EMPLOYEE_COLUMNS, employee_id, data)
        db.commit()
        return {"id": employee_id, **safe_data}

    def delete_employee(self, employee_id: int, current_user: dict, db: Session) -> None:
        db.execute(text("DELETE FROM employees WHERE id = :id"), {"id": employee_id})
        db.commit()

    def list_employee_documents(self, employee_id: int, db: Session) -> List[dict]:
        rows = db.execute(
            text("SELECT * FROM employee_documents WHERE employee_id = :eid ORDER BY created_at DESC"),
            {"eid": employee_id},
        ).mappings().all()
        return [dict(r) for r in rows]

    def create_employee_document(self, employee_id: int, data: dict, db: Session) -> dict:
        result = db.execute(
            text("""
                INSERT INTO employee_documents (employee_id, document_type, document_name, file_url, expires_at, notes)
                VALUES (:employee_id, :document_type, :document_name, :file_url, :expires_at, :notes)
                RETURNING id
            """),
            {"employee_id": employee_id, **data},
        )
        doc_id = result.scalar()
        db.commit()
        return {"id": doc_id, "employee_id": employee_id, **data}

    def update_employee_document_status(self, doc_id: int, data: dict, db: Session) -> dict:
        safe_data = {k: v for k, v in data.items() if k in _ALLOWED_DOCUMENT_COLUMNS}
        if not safe_data:
            return {"id": doc_id, **data}
        _safe_update(db, EmployeeDocument, _ALLOWED_DOCUMENT_COLUMNS, doc_id, data)
        db.commit()
        return {"id": doc_id, **safe_data}

    def list_attendance(self, employee_id: int, db: Session, **filters) -> List[dict]:
        query = "SELECT * FROM attendance_records WHERE employee_id = :eid"
        params = {"eid": employee_id}
        if filters.get("from_date"):
            query += " AND created_at >= :from_date"
            params["from_date"] = filters["from_date"]
        if filters.get("to_date"):
            query += " AND created_at <= :to_date"
            params["to_date"] = filters["to_date"]
        query += " ORDER BY created_at DESC LIMIT :limit"
        params["limit"] = filters.get("limit", 50)
        rows = db.execute(text(query), params).mappings().all()
        return [dict(r) for r in rows]

    def check_in_employee(self, employee_id: int, data: dict, db: Session) -> dict:
        result = db.execute(
            text("""
                INSERT INTO attendance_records (employee_id, clock_in, latitude, longitude, ip_address, device_fingerprint, notes, status)
                VALUES (:eid, :now, :latitude, :longitude, :ip_address, :device_fingerprint, :notes, 'checked_in')
                RETURNING id
            """),
            {
                "eid": employee_id,
                "now": datetime.now(timezone.utc),
                "latitude": data.get("latitude"),
                "longitude": data.get("longitude"),
                "ip_address": data.get("ip_address"),
                "device_fingerprint": data.get("device_fingerprint"),
                "notes": data.get("notes"),
            },
        )
        record_id = result.scalar()
        db.commit()
        return {"id": record_id, "employee_id": employee_id, "status": "checked_in"}

    def check_out_employee(self, employee_id: int, data: dict, db: Session) -> dict:
        db.execute(
            text("""
                UPDATE attendance_records SET clock_out = :now, notes = COALESCE(notes, '') || ' ' || :notes
                WHERE employee_id = :eid AND clock_out IS NULL
                ORDER BY clock_in DESC LIMIT 1
            """),
            {"now": datetime.now(timezone.utc), "notes": data.get("notes", ""), "eid": employee_id},
        )
        db.commit()
        return {"employee_id": employee_id, "status": "checked_out"}

    def check_in_with_geo(self, employee_id: int, data: dict, db: Session) -> dict:
        return self.check_in_employee(employee_id, data, db)

    def list_employee_relations(self, employee_id: int, db: Session) -> List[dict]:
        rows = db.execute(
            text("SELECT * FROM employee_relations WHERE employee_id = :eid OR related_employee_id = :eid"),
            {"eid": employee_id},
        ).mappings().all()
        return [dict(r) for r in rows]

    def create_employee_relation(self, employee_id: int, data: dict, db: Session) -> dict:
        result = db.execute(
            text("""
                INSERT INTO employee_relations (employee_id, related_employee_id, relation_type, notes)
                VALUES (:employee_id, :related_employee_id, :relation_type, :notes)
                RETURNING id
            """),
            {"employee_id": employee_id, **data},
        )
        rel_id = result.scalar()
        db.commit()
        return {"id": rel_id, "employee_id": employee_id, **data}

    def remove_employee_relation(self, relation_id: int, db: Session) -> None:
        db.execute(text("DELETE FROM employee_relations WHERE id = :id"), {"id": relation_id})
        db.commit()

    def list_work_logs(self, employee_id: int, db: Session, **filters) -> List[dict]:
        query = "SELECT * FROM work_logs WHERE employee_id = :eid"
        params = {"eid": employee_id}
        if filters.get("from_date"):
            query += " AND date >= :from_date"
            params["from_date"] = filters["from_date"]
        if filters.get("to_date"):
            query += " AND date <= :to_date"
            params["to_date"] = filters["to_date"]
        if filters.get("status"):
            query += " AND status = :status"
            params["status"] = filters["status"]
        query += " ORDER BY date DESC LIMIT :limit"
        params["limit"] = filters.get("limit", 50)
        rows = db.execute(text(query), params).mappings().all()
        return [dict(r) for r in rows]

    def create_work_log(self, employee_id: int, data: dict, db: Session) -> dict:
        result = db.execute(
            text("""
                INSERT INTO work_logs (employee_id, date, hours_worked, description, status)
                VALUES (:eid, :date, :hours_worked, :description, 'pending')
                RETURNING id
            """),
            {
                "eid": employee_id,
                "date": data.get("date"),
                "hours_worked": data.get("hours_worked", 0),
                "description": data.get("description"),
            },
        )
        log_id = result.scalar()
        db.commit()
        return {"id": log_id, "employee_id": employee_id, **data, "status": "pending"}

    def approve_work_log(self, log_id: int, data: dict, current_user: dict, db: Session) -> dict:
        db.execute(
            text("UPDATE work_logs SET status = :status WHERE id = :id"),
            {"status": data.get("status", "approved"), "id": log_id},
        )
        db.commit()
        return {"id": log_id, "status": data.get("status", "approved")}

    def generate_qr_login_token(self, employee_id: int, db: Session) -> dict:
        import secrets
        token = secrets.token_urlsafe(32)
        db.execute(
            text("INSERT INTO qr_login_tokens (employee_id, token, expires_at) VALUES (:eid, :token, :expires)"),
            {"eid": employee_id, "token": token, "expires": datetime.now(timezone.utc)},
        )
        db.commit()
        return {"token": token, "employee_id": employee_id}

    def validate_qr_login(self, qr_token: str, db: Session) -> dict:
        row = db.execute(
            text("SELECT * FROM qr_login_tokens WHERE token = :token AND expires_at > :now"),
            {"token": qr_token, "now": datetime.now(timezone.utc)},
        ).mappings().first()
        return {"valid": row is not None, "employee_id": row["employee_id"] if row else None}

    def validate_geo_location(self, latitude: float, longitude: float, office_id: int, db: Session) -> dict:
        return {"valid": True, "latitude": latitude, "longitude": longitude, "office_id": office_id}

    def list_employee_roles(self, country_code: str, db: Session) -> List[dict]:
        rows = db.execute(
            text("SELECT * FROM employee_roles WHERE country_code = :code ORDER BY name"),
            {"code": country_code},
        ).mappings().all()
        return [dict(r) for r in rows]

    def create_employee_role(self, country_code: str, data: dict, db: Session) -> dict:
        result = db.execute(
            text("""
                INSERT INTO employee_roles (name, slug, permissions, country_code)
                VALUES (:name, :slug, :permissions, :country_code)
                RETURNING id
            """),
            {**data, "country_code": country_code},
        )
        role_id = result.scalar()
        db.commit()
        return {"id": role_id, "country_code": country_code, **data}

    def create_leave_request(self, employee_id: int, data: dict, current_user: dict, db: Session) -> dict:
        result = db.execute(
            text("""
                INSERT INTO leave_requests (employee_id, leave_type, start_date, end_date, reason, status, created_at)
                VALUES (:eid, :leave_type, :start_date, :end_date, :reason, 'pending', :now)
                RETURNING id
            """),
            {
                "eid": employee_id,
                "leave_type": data.get("leave_type", "annual"),
                "start_date": data.get("start_date"),
                "end_date": data.get("end_date"),
                "reason": data.get("notes", ""),
                "now": datetime.now(timezone.utc),
            },
        )
        req_id = result.scalar()
        db.commit()
        return {"id": req_id, "employee_id": employee_id, "status": "pending"}

    def create_shift_roster(self, employee_id: int, data: dict, current_user: dict, db: Session) -> dict:
        result = db.execute(
            text("""
                INSERT INTO employee_shift_rosters (employee_id, shift_date, start_time, end_time, shift_type, status)
                VALUES (:eid, :shift_date, :start_time, :end_time, :shift_type, :status)
                RETURNING id
            """),
            {
                "eid": employee_id,
                "shift_date": data.get("shift_date"),
                "start_time": data.get("start_time"),
                "end_time": data.get("end_time"),
                "shift_type": data.get("shift_type", "scheduled"),
                "status": data.get("status", "scheduled"),
            },
        )
        shift_id = result.scalar()
        db.commit()
        return {"id": shift_id, "employee_id": employee_id, **data}

    def kill_switch(self, employee_id: int, current_user: dict, db: Session) -> dict:
        db.execute(
            text("UPDATE employees SET employment_status = 'suspended' WHERE id = :id"),
            {"id": employee_id},
        )
        db.commit()
        return {"employee_id": employee_id, "status": "suspended"}

    def list_leave_requests(self, db: Session, code: str, page: int = 1, limit: int = 50) -> dict:
        """List leave requests with pagination."""
        from infrastructure.utils.pagination import paginated_response
        query = db.query(EmployeeLeaveRequest).order_by(EmployeeLeaveRequest.created_at.desc())
        return paginated_response(query, page=page, size=limit, max_size=100)

    def update_leave_request_status(self, db: Session, leave_id: int, status: str, current_user: dict) -> dict:
        """Approve or reject a leave request."""
        r = db.query(EmployeeLeaveRequest).filter(EmployeeLeaveRequest.id == leave_id).first()
        if not r:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="Leave request not found")
        if status not in ("approved", "rejected"):
            from fastapi import HTTPException
            raise HTTPException(status_code=400, detail="Invalid status")
        r.status = status
        r.approved_by = current_user.get("id")
        r.approved_at = datetime.now(timezone.utc)
        db.commit()
        return {"message": f"Leave request {status}", "id": leave_id}

    def list_shifts(self, db: Session, code: str, page: int = 1, limit: int = 50) -> dict:
        """List shift rosters with pagination."""
        from infrastructure.utils.pagination import paginated_response
        query = db.query(EmployeeShiftRoster).order_by(EmployeeShiftRoster.shift_date.desc())
        return paginated_response(query, page=page, size=limit, max_size=100)

    def list_org_units(self, db: Session, country_code: Optional[str] = None) -> dict:
        """List org units, optionally filtered by country."""
        q = db.query(OrgUnit).filter(OrgUnit.is_active == True)
        if country_code:
            q = q.filter(OrgUnit.country_code == country_code)
        units = q.order_by(OrgUnit.path, OrgUnit.name).all()
        return {"units": [{"id": u.id, "name": u.name, "parent_id": u.parent_id, "path": u.path, "depth": u.depth, "level": u.level, "country_code": u.country_code, "is_active": u.is_active} for u in units]}

    def create_org_unit(self, db: Session, payload: dict) -> dict:
        """Create a new org unit."""
        unit = OrgUnit(name=payload["name"], parent_id=payload.get("parent_id"), country_code=payload["country_code"], level=payload.get("level", 1))
        db.add(unit)
        db.flush()
        _update_unit_path(db, unit)
        db.commit()
        db.refresh(unit)
        return {"id": unit.id, "name": unit.name, "path": unit.path, "depth": unit.depth}

    def update_org_unit(self, db: Session, unit_id: int, payload: dict) -> dict:
        """Update an org unit."""
        unit = db.query(OrgUnit).filter(OrgUnit.id == unit_id).first()
        if not unit:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="Org unit not found")
        if "name" in payload:
            unit.name = payload["name"]
        if "level" in payload:
            unit.level = payload["level"]
        if "is_active" in payload:
            unit.is_active = payload["is_active"]
        if "parent_id" in payload:
            unit.parent_id = payload["parent_id"]
        db.flush()
        _update_unit_path(db, unit)
        db.commit()
        return {"id": unit.id, "path": unit.path, "depth": unit.depth}

    def get_user_country_scope(self, db: Session, user_id: int) -> dict:
        """Get country assignments for a user."""
        assignments = db.query(CountryStaffAssignment).filter(CountryStaffAssignment.user_id == user_id, CountryStaffAssignment.is_active == True).all()
        return {"countries": [{"id": a.id, "country_code": a.country_code, "role_in_country": a.role_in_country} for a in assignments]}

    def switch_country_scope(self, db: Session, user_id: int, country_code: str, role: str) -> dict:
        """Switch active country scope."""
        from infrastructure.database.rls_interceptor import set_rls_context
        assignment = db.query(CountryStaffAssignment).filter(CountryStaffAssignment.user_id == user_id, CountryStaffAssignment.country_code == country_code, CountryStaffAssignment.is_active == True).first()
        if not assignment and role not in ("admin", "super_admin"):
            from fastapi import HTTPException
            raise HTTPException(status_code=403, detail=f"No access to country '{country_code}'")
        set_rls_context(country_code)
        return {"active_country": country_code, "message": f"Switched to {country_code}"}

    def get_country_localization(self, db: Session, country_code: str) -> dict:
        """Get country localization data including holidays and config."""
        country = db.query(CountryConfig).filter(CountryConfig.code == country_code).first()
        if not country:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="Country not found")
        holidays = db.query(CountryHolidayCalendar).filter(CountryHolidayCalendar.country_code == country_code).order_by(CountryHolidayCalendar.date).limit(500).all()
        localization = db.query(CountryLocalization).filter(CountryLocalization.country_code == country_code).limit(500).all()
        return {
            "country": {"code": country.code, "name": country.name, "currency": country.currency, "timezone": country.timezone, "language": country.language},
            "holidays": [{"id": h.id, "name": h.holiday_name, "date": str(h.date), "type": h.holiday_type} for h in holidays],
            "localization": {loc.key: loc.value for loc in localization},
        }

    def list_employee_payslips(self, db: Session, employee_id: int, page: int = 1, limit: int = 50) -> dict:
        """List employee payslip documents."""
        from infrastructure.utils.pagination import paginated_response
        query = db.query(EmployeeDocument).filter(EmployeeDocument.employee_id == employee_id, EmployeeDocument.doc_type == "payslip").order_by(EmployeeDocument.created_at.desc())
        return paginated_response(query, page=page, size=limit, max_size=100)

    def list_employee_addresses(self, employee_id: int) -> list:
        """List addresses for an employee."""
        employee = self.db.query(Employee).filter(Employee.id == employee_id).first()
        if not employee:
            return []
        addresses = self.db.query(Address).filter(Address.user_id == employee.user_id).all()
        return [
            {
                "id": a.id,
                "label": a.label,
                "full_name": a.full_name,
                "phone": a.phone,
                "address_line1": a.address_line1,
                "address_line2": a.address_line2,
                "city": a.city,
                "state": a.state,
                "postal_code": a.postal_code,
                "country": a.country,
                "is_default": a.is_default,
            }
            for a in addresses
        ]

    def list_employee_dependents(self, employee_id: int) -> list:
        """List dependents for an employee."""
        dependents = (
            self.db.query(EmployeeDependent).filter(EmployeeDependent.employee_id == employee_id).all()
        )
        return [
            {
                "id": d.id,
                "name": d.name,
                "relation": d.relation,
                "dob": str(d.dob) if d.dob else None,
                "is_insured": d.is_insured,
            }
            for d in dependents
        ]

    def list_employees_public(self) -> list:
        """Public endpoint to list employees."""
        query = "SELECT id, employee_code, department, position, employment_status, salary, currency, country_code, hire_date, created_at FROM employees ORDER BY created_at DESC LIMIT 50"
        result = self.db.execute(text(query))
        employees = []
        for row in result:
            employees.append({
                "id": row[0],
                "employee_code": row[1],
                "department": row[2],
                "position": row[3],
                "employment_status": row[4],
                "salary": float(row[5]) if row[5] else None,
                "currency": row[6],
                "country_code": row[7],
                "hire_date": row[8].isoformat() if row[8] else None,
            })
        return employees

    def coi_check(self, employee_id: int) -> dict:
        """Run a conflict-of-interest check for an employee."""
        from sqlalchemy import or_

        employee = self.db.query(Employee).filter(Employee.id == employee_id).first()
        if not employee:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="Employee not found")

        conflicts = []

        try:
            relations = (
                self.db.query(EmployeeRelation)
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
            other = self.db.query(Employee).filter(Employee.id == other_id).first()
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

        if employee.reporting_manager_id:
            manager = self.db.query(Employee).filter(Employee.id == employee.reporting_manager_id).first()
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


def _update_unit_path(db: Session, unit: OrgUnit) -> None:
    """Recalculate path and depth for an org unit."""
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


def get_hr_employee_service(db: Session) -> HREmployeeService:
    return HREmployeeService(db)
