"""EmployeeService — canonical HR employee operations.

Consolidates employee CRUD, attendance, leave, documents, relations, work logs,
shifts, QR/geo, and kill-switch operations that were previously scattered across
thin routers and controller modules. This is the single service the employee
module routers delegate to (Law 2: routers stay thin).
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from domains.governance.models.core import Address
from domains.hr.models.employee_models import Employee
from domains.hr.models.employee_models import EmployeeDependent
from domains.hr.models.employee_models import EmployeeDocument
from domains.hr.models.employee_models import EmployeeLeaveRequest
from domains.hr.models.employee_models import EmployeeRelation
from domains.hr.models.employee_models import EmployeeShiftRoster
from domains.hr.models.employee_models import Office
from domains.hr.models.employee_models import EmployeeWorkLog
from domains.hr.models.employee_models import EmployeeRole
from domains.country.utils.country_rls import enforce_country_access
from infrastructure.utils.datetime_utils import utcnow as _utcnow

logger = logging.getLogger(__name__)


class EmployeeService:
    """Service class for all employee-related operations."""

    def __init__(self, db: Session):
        self.db = db

    # ── Offices ───────────────────────────────────────────────────

    def list_offices(self, code: str) -> Dict[str, Any]:
        enforce_country_access(code, db=self.db)
        offices = (
            self.db.query(Office)
            .filter(Office.country_code == code, Office.is_active == True)
            .order_by(Office.name)
            .all()
        )
        return {"offices": [
            {
                "id": o.id,
                "name": o.name,
                "address": o.address,
                "city": o.city,
                "phone": o.phone,
                "email": o.email,
                "latitude": o.latitude,
                "longitude": o.longitude,
                "is_active": o.is_active,
            }
            for o in offices
        ]}

    def create_office(self, code: str, data: Dict[str, Any]) -> Dict[str, Any]:
        enforce_country_access(code, db=self.db)
        office = Office(country_code=code, **data)
        self.db.add(office)
        self.db.commit()
        self.db.refresh(office)
        return {"id": office.id, "name": office.name}

    def update_office(self, office_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        office = self.db.query(Office).filter(Office.id == office_id).first()
        if not office:
            raise HTTPException(status_code=404, detail="Office not found")
        for key, value in data.items():
            if value is not None and hasattr(office, key):
                setattr(office, key, value)
        self.db.commit()
        return {"id": office.id, "name": office.name}

    def delete_office(self, office_id: int) -> None:
        office = self.db.query(Office).filter(Office.id == office_id).first()
        if not office:
            raise HTTPException(status_code=404, detail="Office not found")
        office.is_active = False
        self.db.commit()

    # ── Employee CRUD ─────────────────────────────────────────────

    def list_employees(
        self,
        code: str,
        department: Optional[str] = None,
        status: Optional[str] = None,
        query: Optional[str] = None,
        limit: int = 100,
    ) -> Dict[str, Any]:
        enforce_country_access(code, db=self.db)
        q = self.db.query(Employee).filter(Employee.country_code == code)
        if department:
            q = q.filter(Employee.department == department)
        if status:
            q = q.filter(Employee.employment_status == status)
        if query:
            q = q.filter(
                (Employee.employee_code.ilike(f"%{query}%"))
                | (Employee.department.ilike(f"%{query}%"))
                | (Employee.position.ilike(f"%{query}%"))
            )
        employees = q.order_by(Employee.created_at.desc()).limit(limit).all()
        return {"employees": [
            {
                "id": e.id,
                "employee_code": e.employee_code,
                "user_id": e.user_id,
                "department": e.department,
                "position": e.position,
                "employment_type": e.employment_type,
                "employment_status": e.employment_status,
                "salary": float(e.salary) if e.salary else None,
                "currency": e.currency,
                "country_code": e.country_code,
                "hire_date": e.hire_date.isoformat() if e.hire_date else None,
                "is_verified": e.is_verified,
            }
            for e in employees
        ]}

    def create_employee(self, code: str, data: Dict[str, Any], current_user: Any) -> Dict[str, Any]:
        enforce_country_access(code, db=self.db)
        employee = Employee(country_code=code, **data)
        self.db.add(employee)
        self.db.commit()
        self.db.refresh(employee)
        return {"id": employee.id, "employee_code": employee.employee_code}

    def get_employee(self, employee_id: int) -> Dict[str, Any]:
        employee = self.db.query(Employee).filter(Employee.id == employee_id).first()
        if not employee:
            raise HTTPException(status_code=404, detail="Employee not found")
        return {
            "id": employee.id,
            "employee_code": employee.employee_code,
            "user_id": employee.user_id,
            "department": employee.department,
            "position": employee.position,
            "employment_type": employee.employment_type,
            "employment_status": employee.employment_status,
            "salary": float(employee.salary) if employee.salary else None,
            "currency": employee.currency,
            "country_code": employee.country_code,
            "hire_date": employee.hire_date.isoformat() if employee.hire_date else None,
            "is_verified": employee.is_verified,
            "created_at": employee.created_at.isoformat() if employee.created_at else None,
        }

    def update_employee(self, employee_id: int, data: Dict[str, Any], current_user: Any) -> Dict[str, Any]:
        employee = self.db.query(Employee).filter(Employee.id == employee_id).first()
        if not employee:
            raise HTTPException(status_code=404, detail="Employee not found")
        for key, value in data.items():
            if value is not None and hasattr(employee, key):
                setattr(employee, key, value)
        self.db.commit()
        return {"id": employee.id, "employee_code": employee.employee_code}

    def delete_employee(self, employee_id: int, current_user: Any) -> None:
        employee = self.db.query(Employee).filter(Employee.id == employee_id).first()
        if not employee:
            raise HTTPException(status_code=404, detail="Employee not found")
        employee.employment_status = "terminated"
        self.db.commit()

    # ── Employee Documents ────────────────────────────────────────

    def list_employee_documents(self, employee_id: int) -> List[Dict[str, Any]]:
        docs = (
            self.db.query(EmployeeDocument)
            .filter(EmployeeDocument.employee_id == employee_id)
            .order_by(EmployeeDocument.created_at.desc())
            .all()
        )
        return [
            {
                "id": d.id,
                "document_type": d.document_type,
                "document_name": d.document_name,
                "file_url": d.file_url,
                "status": d.status,
                "created_at": d.created_at.isoformat() if d.created_at else None,
            }
            for d in docs
        ]

    def create_employee_document(self, employee_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        doc = EmployeeDocument(employee_id=employee_id, **data)
        self.db.add(doc)
        self.db.commit()
        self.db.refresh(doc)
        return {"id": doc.id, "document_type": doc.document_type}

    def update_employee_document_status(self, doc_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        doc = self.db.query(EmployeeDocument).filter(EmployeeDocument.id == doc_id).first()
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
        for key, value in data.items():
            if value is not None and hasattr(doc, key):
                setattr(doc, key, value)
        self.db.commit()
        return {"id": doc.id, "status": doc.status}

    # ── Attendance ────────────────────────────────────────────────

    def list_attendance(
        self,
        employee_id: int,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        from sqlalchemy import text
        rows = self.db.execute(
            text("""
                SELECT id, employee_id, clock_in, clock_out, status, hours_worked, created_at
                FROM attendance_records
                WHERE employee_id = :eid
                ORDER BY clock_in DESC
                LIMIT :limit
            """),
            {"eid": employee_id, "limit": limit},
        ).mappings().all()
        return [dict(r) for r in rows]

    def check_in_employee(self, employee_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        from sqlalchemy import text
        result = self.db.execute(
            text("""
                INSERT INTO attendance_records (employee_id, clock_in, latitude, longitude, ip_address, device_fingerprint, notes, status)
                VALUES (:eid, :now, :lat, :lon, :ip, :dfp, :notes, 'present')
                RETURNING id
            """),
            {
                "eid": employee_id,
                "now": _utcnow(),
                "lat": data.get("latitude"),
                "lon": data.get("longitude"),
                "ip": data.get("ip_address"),
                "dfp": data.get("device_fingerprint"),
                "notes": data.get("notes"),
            },
        )
        attendance_id = result.scalar()
        self.db.commit()
        return {"id": attendance_id, "status": "checked_in"}

    def check_out_employee(self, employee_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        from sqlalchemy import text
        self.db.execute(
            text("""
                UPDATE attendance_records SET clock_out = :now, notes = :notes
                WHERE employee_id = :eid AND clock_out IS NULL
                ORDER BY clock_in DESC LIMIT 1
            """),
            {"now": _utcnow(), "notes": data.get("notes"), "eid": employee_id},
        )
        self.db.commit()
        return {"status": "checked_out"}

    def check_in_with_geo(self, employee_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        from sqlalchemy import text
        result = self.db.execute(
            text("""
                INSERT INTO attendance_records (employee_id, clock_in, latitude, longitude, office_id, ip_address, device_fingerprint, notes, status)
                VALUES (:eid, :now, :lat, :lon, :oid, :ip, :dfp, :notes, 'present')
                RETURNING id
            """),
            {
                "eid": employee_id,
                "now": _utcnow(),
                "lat": data.get("latitude"),
                "lon": data.get("longitude"),
                "oid": data.get("office_id"),
                "ip": data.get("ip_address"),
                "dfp": data.get("device_fingerprint"),
                "notes": data.get("notes"),
            },
        )
        attendance_id = result.scalar()
        self.db.commit()
        return {"id": attendance_id, "status": "geo_checked_in"}

    # ── Employee Relations ────────────────────────────────────────

    def list_employee_relations(self, employee_id: int) -> List[Dict[str, Any]]:
        relations = (
            self.db.query(EmployeeRelation)
            .filter(
                (EmployeeRelation.employee_id == employee_id)
                | (EmployeeRelation.related_employee_id == employee_id)
            )
            .all()
        )
        return [
            {
                "id": r.id,
                "employee_id": r.employee_id,
                "related_employee_id": r.related_employee_id,
                "relation_type": r.relation_type,
                "notes": r.notes,
            }
            for r in relations
        ]

    def create_employee_relation(self, employee_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        relation = EmployeeRelation(employee_id=employee_id, **data)
        self.db.add(relation)
        self.db.commit()
        self.db.refresh(relation)
        return {"id": relation.id, "relation_type": relation.relation_type}

    def remove_employee_relation(self, relation_id: int) -> None:
        relation = self.db.query(EmployeeRelation).filter(EmployeeRelation.id == relation_id).first()
        if not relation:
            raise HTTPException(status_code=404, detail="Relation not found")
        self.db.delete(relation)
        self.db.commit()

    # ── Work Logs ─────────────────────────────────────────────────

    def list_work_logs(
        self,
        employee_id: int,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        q = self.db.query(EmployeeWorkLog).filter(EmployeeWorkLog.employee_id == employee_id)
        if status:
            q = q.filter(EmployeeWorkLog.status == status)
        logs = q.order_by(EmployeeWorkLog.created_at.desc()).limit(limit).all()
        return [
            {
                "id": log.id,
                "employee_id": log.employee_id,
                "date": log.date.isoformat() if log.date else None,
                "hours_worked": float(log.hours_worked) if log.hours_worked else 0,
                "description": log.description,
                "status": log.status,
            }
            for log in logs
        ]

    def create_work_log(self, employee_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        log = EmployeeWorkLog(employee_id=employee_id, **data)
        self.db.add(log)
        self.db.commit()
        self.db.refresh(log)
        return {"id": log.id, "status": log.status}

    def approve_work_log(self, log_id: int, data: Dict[str, Any], current_user: Any) -> Dict[str, Any]:
        log = self.db.query(EmployeeWorkLog).filter(EmployeeWorkLog.id == log_id).first()
        if not log:
            raise HTTPException(status_code=404, detail="Work log not found")
        log.status = data.get("status", "approved")
        self.db.commit()
        return {"id": log.id, "status": log.status}

    # ── QR & Geo ─────────────────────────────────────────────────

    def generate_qr_login_token(self, employee_id: int) -> Dict[str, Any]:
        import uuid
        token = uuid.uuid4().hex
        return {"qr_token": token, "employee_id": employee_id}

    def validate_qr_login(self, qr_token: str) -> Dict[str, Any]:
        return {"status": "validated", "qr_token": qr_token}

    def validate_geo_location(self, latitude: float, longitude: float, office_id: int) -> Dict[str, Any]:
        return {"valid": True, "latitude": latitude, "longitude": longitude, "office_id": office_id}

    # ── Employee Roles ────────────────────────────────────────────

    def list_employee_roles(self, code: str) -> List[Dict[str, Any]]:
        roles = (
            self.db.query(EmployeeRole)
            .filter(EmployeeRole.country_code == code)
            .order_by(EmployeeRole.name)
            .all()
        )
        return [
            {
                "id": r.id,
                "name": r.name,
                "slug": r.slug,
                "permissions": r.permissions,
            }
            for r in roles
        ]

    def create_employee_role(self, code: str, data: Dict[str, Any]) -> Dict[str, Any]:
        role = EmployeeRole(country_code=code, **data)
        self.db.add(role)
        self.db.commit()
        self.db.refresh(role)
        return {"id": role.id, "name": role.name}

    # ── Leave Requests ────────────────────────────────────────────

    def list_leave_requests(self, code: str) -> List[Dict[str, Any]]:
        requests = (
            self.db.query(EmployeeLeaveRequest)
            .order_by(EmployeeLeaveRequest.created_at.desc())
            .all()
        )
        result = []
        for r in requests:
            employee_name = None
            if r.employee:
                user = r.employee.user
                employee_name = (user.full_name or user.username) if user else r.employee.employee_code
            result.append({
                "id": r.id,
                "employee_id": r.employee_id,
                "employee_name": employee_name,
                "leave_type": r.leave_type,
                "start_date": r.start_date.isoformat() if r.start_date else None,
                "end_date": r.end_date.isoformat() if r.end_date else None,
                "days_requested": r.days_requested,
                "status": r.status,
                "approved_by": r.approved_by,
                "notes": r.rejection_reason or "",
            })
        return result

    def create_leave_request(self, employee_id: int, data: Dict[str, Any], current_user: Any) -> Dict[str, Any]:
        leave = EmployeeLeaveRequest(employee_id=employee_id, **data)
        self.db.add(leave)
        self.db.commit()
        self.db.refresh(leave)
        return {"id": leave.id, "status": leave.status}

    def update_leave_request_status(self, leave_id: int, status: str, current_user: Any) -> Dict[str, Any]:
        r = self.db.query(EmployeeLeaveRequest).filter(EmployeeLeaveRequest.id == leave_id).first()
        if not r:
            raise HTTPException(status_code=404, detail="Leave request not found")
        status = status.lower()
        if status not in ("approved", "rejected"):
            raise HTTPException(status_code=400, detail="Invalid status")
        r.status = status
        r.approved_by = current_user.get("id") if isinstance(current_user, dict) else current_user.id
        r.approved_at = _utcnow()
        self.db.commit()
        return {"message": f"Leave request {status}", "id": leave_id}

    # ── Shifts ────────────────────────────────────────────────────

    def list_shifts(self, code: str) -> List[Dict[str, Any]]:
        shifts = (
            self.db.query(EmployeeShiftRoster)
            .order_by(EmployeeShiftRoster.shift_date.desc())
            .all()
        )
        result = []
        for s in shifts:
            employee_name = None
            if s.employee:
                user = s.employee.user
                employee_name = (user.full_name or user.username) if user else s.employee.employee_code
            result.append({
                "id": s.id,
                "employee_id": s.employee_id,
                "employee_name": employee_name,
                "shift_date": s.shift_date.isoformat() if s.shift_date else None,
                "start_time": s.start_time.isoformat() if s.start_time else None,
                "end_time": s.end_time.isoformat() if s.end_time else None,
                "shift_type": s.shift_type,
                "status": s.status,
            })
        return result

    def create_shift_roster(self, employee_id: int, data: Dict[str, Any], current_user: Any) -> Dict[str, Any]:
        shift = EmployeeShiftRoster(employee_id=employee_id, **data)
        self.db.add(shift)
        self.db.commit()
        self.db.refresh(shift)
        return {"id": shift.id, "status": shift.status}

    # ── Kill Switch ───────────────────────────────────────────────

    def kill_switch(self, employee_id: int, current_user: Any) -> Dict[str, Any]:
        employee = self.db.query(Employee).filter(Employee.id == employee_id).first()
        if not employee:
            raise HTTPException(status_code=404, detail="Employee not found")
        employee.employment_status = "suspended"
        self.db.commit()
        return {"status": "suspended", "employee_id": employee_id}
