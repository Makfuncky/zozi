"""Employee write service — DB write operations for HR and employee entities."""
from datetime import datetime

from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from data.models import (
    AlumniNetwork,
    DynamicQRSession,
    Employee,
    EmployeeAttendance,
    EmployeeDocument,
    EmployeeLeaveRequest,
    EmployeeRelation,
    EmployeeRole,
    EmployeeShiftRoster,
    EmployeeWorkLog,
    Office,
    RevokedToken,
)


def create_office(db: Session, code: str, **office_data) -> Office:
    office = Office(country_code=code, **office_data)
    db.add(office)
    db.commit()
    db.refresh(office)
    return office


def update_office(db: Session, office: Office, updates: dict) -> Office:
    for key, value in updates.items():
        setattr(office, key, value)
    db.commit()
    db.refresh(office)
    return office


def delete_office(db: Session, office: Office) -> None:
    db.delete(office)
    db.commit()


def list_employees_public(db: Session) -> list[dict]:
    query = "SELECT id, employee_code, department, position, employment_status, salary, currency, country_code, hire_date, created_at FROM employees ORDER BY created_at DESC LIMIT 50"
    result = db.execute(text(query))
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


def _validate_employee_data(
    db: Session, data: dict, is_update: bool = False
) -> None:
    required = ["employee_code"] if not is_update else []
    for field in required:
        if field not in data or not data[field]:
            raise HTTPException(
                status_code=422, detail=f"Missing required field: {field}"
            )

    if "employment_status" in data and data["employment_status"]:
        allowed_statuses = {"active", "inactive", "terminated", "on_leave"}
        if data["employment_status"] not in allowed_statuses:
            raise HTTPException(
                status_code=422,
                detail=f"Invalid employment_status. Must be one of: {', '.join(sorted(allowed_statuses))}",
            )

    if "employment_type" in data and data["employment_type"]:
        allowed_types = {"full_time", "part_time", "contract", "temporary"}
        if data["employment_type"] not in allowed_types:
            raise HTTPException(
                status_code=422,
                detail=f"Invalid employment_type. Must be one of: {', '.join(sorted(allowed_types))}",
            )

    if "employee_code" in data and data["employee_code"]:
        existing = (
            db.query(Employee)
            .filter(Employee.employee_code == data["employee_code"])
            .first()
        )
        if existing and (is_update is False or (is_update and "id" in data and existing.id != data.get("id"))):
            raise HTTPException(
                status_code=409,
                detail=f"Employee code '{data['employee_code']}' already exists",
            )

    if "user_id" in data and data["user_id"]:
        existing = (
            db.query(Employee)
            .filter(Employee.user_id == data["user_id"])
            .first()
        )
        if existing and (is_update is False or (is_update and "id" in data and existing.id != data.get("id"))):
            raise HTTPException(
                status_code=409,
                detail=f"Employee with user_id {data['user_id']} already exists",
            )


def create_employee(db: Session, **employee_data) -> Employee:
    _validate_employee_data(db, employee_data, is_update=False)
    emp = Employee(**employee_data)
    db.add(emp)
    db.commit()
    db.refresh(emp)
    return emp


def update_employee(db: Session, emp: Employee, updates: dict) -> Employee:
    _validate_employee_data(db, {**updates, "id": emp.id}, is_update=True)
    for key, value in updates.items():
        setattr(emp, key, value)
    db.commit()
    db.refresh(emp)
    return emp


def delete_employee(db: Session, emp: Employee) -> None:
    db.delete(emp)
    db.commit()


def create_employee_document(db: Session, employee_id: int, **doc_data) -> EmployeeDocument:
    doc = EmployeeDocument(employee_id=employee_id, **doc_data)
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


def update_employee_document(db: Session, doc: EmployeeDocument, updates: dict) -> EmployeeDocument:
    for key, value in updates.items():
        setattr(doc, key, value)
    db.commit()
    db.refresh(doc)
    return doc


def create_employee_attendance(db: Session, employee_id: int, **attendance_data) -> EmployeeAttendance:
    attendance = EmployeeAttendance(employee_id=employee_id, **attendance_data)
    db.add(attendance)
    db.commit()
    db.refresh(attendance)
    return attendance


def update_employee_attendance(db: Session, record: EmployeeAttendance, updates: dict) -> EmployeeAttendance:
    for key, value in updates.items():
        setattr(record, key, value)
    db.commit()
    db.refresh(record)
    return record


def create_employee_relation(db: Session, employee_id: int, **relation_data) -> EmployeeRelation:
    relation = EmployeeRelation(employee_id=employee_id, **relation_data)
    db.add(relation)
    db.commit()
    db.refresh(relation)
    return relation


def delete_employee_relation(db: Session, relation: EmployeeRelation) -> None:
    db.delete(relation)
    db.commit()


def create_employee_work_log(db: Session, employee_id: int, **log_data) -> EmployeeWorkLog:
    log = EmployeeWorkLog(employee_id=employee_id, **log_data)
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


def update_employee_work_log(db: Session, log: EmployeeWorkLog, updates: dict) -> EmployeeWorkLog:
    for key, value in updates.items():
        setattr(log, key, value)
    db.commit()
    db.refresh(log)
    return log


def approve_work_log(db: Session, log: EmployeeWorkLog, status: str = "approved") -> EmployeeWorkLog:
    log.status = status
    db.commit()
    db.refresh(log)
    return log


def create_dynamic_qr_session(
    db: Session, employee_id: int, qr_token: str, expires_at: datetime
) -> DynamicQRSession:
    session = DynamicQRSession(
        employee_id=employee_id,
        qr_token=qr_token,
        expires_at=expires_at,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def update_dynamic_qr_session(db: Session, session: DynamicQRSession, updates: dict) -> DynamicQRSession:
    for key, value in updates.items():
        setattr(session, key, value)
    db.commit()
    db.refresh(session)
    return session


def create_employee_role(db: Session, **role_data) -> EmployeeRole:
    role = EmployeeRole(**role_data)
    db.add(role)
    db.commit()
    db.refresh(role)
    return role


def create_leave_request(db: Session, employee_id: int, **leave_data) -> EmployeeLeaveRequest:
    leave = EmployeeLeaveRequest(employee_id=employee_id, **leave_data)
    db.add(leave)
    db.commit()
    db.refresh(leave)
    return leave


def create_shift_roster(db: Session, employee_id: int, **shift_data) -> EmployeeShiftRoster:
    shift = EmployeeShiftRoster(employee_id=employee_id, **shift_data)
    db.add(shift)
    db.commit()
    db.refresh(shift)
    return shift


def create_revoked_token(
    db: Session, jti: str, user_id: int, expires_at: datetime
) -> RevokedToken:
    revoked = RevokedToken(
        jti=jti,
        user_id=user_id,
        expires_at=expires_at,
    )
    db.add(revoked)
    db.commit()
    db.refresh(revoked)
    return revoked


def update_qr_sessions_expiry(
    db: Session, sessions, expires_at: datetime
) -> None:
    for session in sessions:
        session.expires_at = expires_at
    db.commit()


def apply_kill_switch(
    db: Session,
    *,
    jti: str,
    user_id: int,
    expires_at: datetime,
    qr_sessions,
) -> None:
    """Stage a revoked token and expire QR sessions in a single transaction."""
    revoked = RevokedToken(
        jti=jti,
        user_id=user_id,
        expires_at=expires_at,
    )
    db.add(revoked)
    for session in qr_sessions:
        session.expires_at = expires_at
    db.commit()


def get_employee_by_user_id(db: Session, user_id: int) -> Employee | None:
    return db.query(Employee).filter(Employee.user_id == user_id).first()


def list_employee_documents(
    db: Session, employee_id: int, skip: int = 0, limit: int = 20
) -> list[EmployeeDocument]:
    return (
        db.query(EmployeeDocument)
        .filter(EmployeeDocument.employee_id == employee_id, EmployeeDocument.doc_type == "payslip")
        .order_by(EmployeeDocument.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def list_alumni_network(db: Session, skip: int = 0, limit: int = 20):
    return (
        db.query(AlumniNetwork, Employee)
        .join(Employee, Employee.id == AlumniNetwork.employee_id)
        .offset(skip)
        .limit(limit)
        .all()
    )


def list_hse_incidents(db: Session):
    return (
        db.execute(
            text(
                "SELECT i.id, i.employee_id, e.employee_code, i.incident_type, "
                "i.description, i.date_occurred, i.severity, i.status "
                "FROM hse_incidents i "
                "LEFT JOIN employees e ON e.id = i.employee_id "
                "ORDER BY i.created_at DESC"
            )
        )
        .fetchall()
    )


def create_hse_incident(db: Session, incident: dict, employee_id: int) -> None:
    from datetime import datetime, timezone

    db.execute(
        text(
            "INSERT INTO hse_incidents "
            "(employee_id, incident_type, description, date_occurred, severity, status, created_at) "
            "VALUES (:eid, :itype, :desc, :docc, :sev, :status, :created)"
        ),
        {
            "eid": employee_id,
            "itype": incident.get("incident_type", "near_miss"),
            "desc": incident.get("description", ""),
            "docc": incident.get("date_occurred"),
            "sev": incident.get("severity", "low"),
            "status": incident.get("status", "open"),
            "created": datetime.now(timezone.utc).replace(tzinfo=None),
        },
    )
    db.commit()


def get_employee_by_id(db: Session, employee_id: int) -> Employee | None:
    return db.query(Employee).filter(Employee.id == employee_id).first()


def check_employee_conflicts(db: Session, employee_id: int, skip: int = 0, limit: int = 20) -> dict:
    from sqlalchemy import or_

    employee = get_employee_by_id(db, employee_id)
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    conflicts = []

    try:
        relations = (
            db.query(EmployeeRelation)
            .filter(
                or_(
                    EmployeeRelation.employee_id == employee_id,
                    EmployeeRelation.internal_employee_id == employee_id,
                )
            )
            .offset(skip)
            .limit(limit)
            .all()
        )
    except Exception as exc:
        import logging
        logging.getLogger(__name__).warning("EmployeeRelation query failed: %s", exc)
        return {"employee_id": employee_id, "has_conflicts": False, "conflicts": []}

    for rel in relations:
        other_id = (
            rel.internal_employee_id
            if rel.employee_id == employee_id
            else rel.employee_id
        )
        other = get_employee_by_id(db, other_id) if other_id else None
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
        manager = get_employee_by_id(db, employee.reporting_manager_id)
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
