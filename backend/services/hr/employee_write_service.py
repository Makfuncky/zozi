"""Employee write service — DB write operations for HR and employee entities."""
from datetime import datetime

from sqlalchemy.orm import Session

from models import (
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


def create_employee(db: Session, **employee_data) -> Employee:
    emp = Employee(**employee_data)
    db.add(emp)
    db.commit()
    db.refresh(emp)
    return emp


def update_employee(db: Session, emp: Employee, updates: dict) -> Employee:
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