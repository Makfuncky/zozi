"""Service methods for employee read operations."""
from typing import Any, Optional
from sqlalchemy.orm import Session
from data.models_employee_models import Employee
from data.models import User, ActivityLog, ApprovalRequest


def get_employee_profile(db: Session, user_id: int) -> Employee | None:
    """Get employee profile by user ID."""
    return db.query(Employee).filter(Employee.user_id == user_id).first()


def get_ess_dashboard_data(db: Session, user_id: int) -> dict:
    """Get ESS dashboard data for an employee."""
    employee = get_employee_profile(db, user_id)
    activities = get_recent_activities(db, user_id, limit=5)
    approvals = get_pending_approvals(db, user_id)
    return {
        "employee": employee,
        "recent_activities": activities,
        "pending_approvals": approvals,
    }


def get_recent_activities(db: Session, user_id: int, limit: int = 10) -> list[ActivityLog]:
    """Get recent activity logs for a user."""
    return (
        db.query(ActivityLog)
        .filter(ActivityLog.user_id == user_id)
        .order_by(ActivityLog.created_at.desc())
        .limit(limit)
        .all()
    )


def get_pending_approvals(db: Session, user_id: int) -> list[ApprovalRequest]:
    """Get pending approval requests for a user."""
    return (
        db.query(ApprovalRequest)
        .filter(ApprovalRequest.assignee_id == user_id, ApprovalRequest.status == "pending")
        .order_by(ApprovalRequest.created_at)
        .all()
    )

def list_office(db: Session, skip: int = 0, limit: int = 100, **filters) -> list[Office]:
    query = db.query(Office)
    for key, value in filters.items():
        query = query.filter(getattr(Office, key) == value)
    return query.offset(skip).limit(limit).all()


def get_office_by_id(db: Session, record_id: int) -> Optional[Office]:
    return db.query(Office).filter(Office.id == record_id).first()


def get_employee_first(db: Session, **filters) -> Optional[Employee]:
    query = db.query(Employee)
    for key, value in filters.items():
        query = query.filter(getattr(Employee, key) == value)
    return query.limit(1).first()


def get_employee_by_id(db: Session, record_id: int) -> Optional[Employee]:
    return db.query(Employee).filter(Employee.id == record_id).first()


def list_employeedocument(db: Session, skip: int = 0, limit: int = 100, **filters) -> list[EmployeeDocument]:
    query = db.query(EmployeeDocument)
    for key, value in filters.items():
        query = query.filter(getattr(EmployeeDocument, key) == value)
    return query.offset(skip).limit(limit).all()


def get_employeedocument_by_id(db: Session, record_id: int) -> Optional[EmployeeDocument]:
    return db.query(EmployeeDocument).filter(EmployeeDocument.id == record_id).first()


def get_employeeattendance_first(db: Session, **filters) -> Optional[EmployeeAttendance]:
    query = db.query(EmployeeAttendance)
    for key, value in filters.items():
        query = query.filter(getattr(EmployeeAttendance, key) == value)
    return query.limit(1).first()


def list_employeerelation(db: Session, skip: int = 0, limit: int = 100, **filters) -> list[EmployeeRelation]:
    query = db.query(EmployeeRelation)
    for key, value in filters.items():
        query = query.filter(getattr(EmployeeRelation, key) == value)
    return query.offset(skip).limit(limit).all()


def get_employeerelation_by_id(db: Session, record_id: int) -> Optional[EmployeeRelation]:
    return db.query(EmployeeRelation).filter(EmployeeRelation.id == record_id).first()


def get_employeeworklog_first(db: Session, **filters) -> Optional[EmployeeWorkLog]:
    query = db.query(EmployeeWorkLog)
    for key, value in filters.items():
        query = query.filter(getattr(EmployeeWorkLog, key) == value)
    return query.limit(1).first()


def get_employeeworklog_by_id(db: Session, record_id: int) -> Optional[EmployeeWorkLog]:
    return db.query(EmployeeWorkLog).filter(EmployeeWorkLog.id == record_id).first()


def get_dynamicqrsession_by_condition(db: Session, **filters) -> Optional[DynamicQRSession]:
    query = db.query(DynamicQRSession)
    for key, value in filters.items():
        query = query.filter(getattr(DynamicQRSession, key) == value)
    return query.first()


def list_employeerole(db: Session, skip: int = 0, limit: int = 100, **filters) -> list[EmployeeRole]:
    query = db.query(EmployeeRole)
    for key, value in filters.items():
        query = query.filter(getattr(EmployeeRole, key) == value)
    return query.offset(skip).limit(limit).all()


def get_dynamicqrsession_first(db: Session, **filters) -> Optional[DynamicQRSession]:
    query = db.query(DynamicQRSession)
    for key, value in filters.items():
        query = query.filter(getattr(DynamicQRSession, key) == value)
    return query.limit(1).first()


def get_employeerelation_first(db: Session, **filters) -> Optional[EmployeeRelation]:
    query = db.query(EmployeeRelation)
    for key, value in filters.items():
        query = query.filter(getattr(EmployeeRelation, key) == value)
    return query.limit(1).first()


def list_disciplinarycase(db: Session, skip: int = 0, limit: int = 100, **filters) -> list[DisciplinaryCase]:
    query = db.query(DisciplinaryCase)
    for key, value in filters.items():
        query = query.filter(getattr(DisciplinaryCase, key) == value)
    return query.offset(skip).limit(limit).all()


def list_offboardingcase(db: Session, skip: int = 0, limit: int = 100, **filters) -> list[OffboardingCase]:
    query = db.query(OffboardingCase)
    for key, value in filters.items():
        query = query.filter(getattr(OffboardingCase, key) == value)
    return query.offset(skip).limit(limit).all()

def _db_office_all_0(db: Session, code: Any, country_code: Any) -> Optional[Any]:
    result = db.query(Office).filter(Office.country_code == code).all()
    return result
    """Read-only query delegated from controller."""

def _db_office_first_1(db: Session, id: Any, office_id: Any) -> Optional[Any]:
    result = db.query(Office).filter(Office.id == office_id).first()
    return result
    """Read-only query delegated from controller."""

def _db_office_first_2(db: Session, id: Any, office_id: Any) -> Optional[Any]:
    result = db.query(Office).filter(Office.id == office_id).first()
    return result
    """Read-only query delegated from controller."""

def _db_employee_query_3(db: Session, code: Any, country_code: Any) -> Optional[Any]:
    result = db.query(Employee).filter(Employee.country_code == code)
    return result
    """Read-only query delegated from controller."""

def _db_employeedocument_all_4(db: Session, employee_id: Any) -> Optional[Any]:
    result = db.query(EmployeeDocument).filter(EmployeeDocument.employee_id == employee_id).all()
    return result
    """Read-only query delegated from controller."""

def _db_employeedocument_first_5(db: Session, doc_id: Any, id: Any) -> Optional[Any]:
    result = db.query(EmployeeDocument).filter(EmployeeDocument.id == doc_id).first()
    return result
    """Read-only query delegated from controller."""

def _db_employeeattendance_query_6(db: Session, employee_id: Any) -> Optional[Any]:
    result = db.query(EmployeeAttendance).filter(EmployeeAttendance.employee_id == employee_id)
    return result
    """Read-only query delegated from controller."""

def _db_employeeattendance_first_7(db: Session, date: Any, employee_id: Any, today: Any) -> Optional[Any]:
    result = db.query(EmployeeAttendance).filter( EmployeeAttendance.employee_id == employee_id, EmployeeAttendance.date == today ).first()
    return result
    """Read-only query delegated from controller."""

def _db_office_first_8(db: Session, id: Any, office_id: Any) -> Optional[Any]:
    result = db.query(Office).filter(Office.id == office_id).first()
    return result
    """Read-only query delegated from controller."""

def _db_employeerelation_all_9(db: Session, employee_id: Any) -> Optional[Any]:
    result = db.query(EmployeeRelation).filter(EmployeeRelation.employee_id == employee_id).all()
    return result
    """Read-only query delegated from controller."""

def _db_employeerelation_first_10(db: Session, id: Any, relation_id: Any) -> Optional[Any]:
    result = db.query(EmployeeRelation).filter(EmployeeRelation.id == relation_id).first()
    return result
    """Read-only query delegated from controller."""

def _db_employeeworklog_query_11(db: Session, employee_id: Any) -> Optional[Any]:
    result = db.query(EmployeeWorkLog).filter(EmployeeWorkLog.employee_id == employee_id)
    return result
    """Read-only query delegated from controller."""

def _db_employeeworklog_first_12(db: Session, id: Any, log_id: Any) -> Optional[Any]:
    result = db.query(EmployeeWorkLog).filter(EmployeeWorkLog.id == log_id).first()
    return result
    """Read-only query delegated from controller."""

def _db_dynamicqrsession_first_13(db: Session, qr_token: Any, token: Any) -> Optional[Any]:
    result = db.query(DynamicQRSession).filter(DynamicQRSession.qr_token == token).first()
    return result
    """Read-only query delegated from controller."""

def _db_employeerole_all_14(db: Session) -> Optional[Any]:
    result = db.query(EmployeeRole).all()
    return result
    """Read-only query delegated from controller."""

def _db_dynamicqrsession_query_15(db: Session, employee_id: Any) -> Optional[Any]:
    result = db.query(DynamicQRSession).filter(DynamicQRSession.employee_id == employee_id)
    return result
    """Read-only query delegated from controller."""

def _db_dynamicqrsession_query_16(db: Session, employee_id: Any) -> Optional[Any]:
    result = db.query(DynamicQRSession).filter(DynamicQRSession.employee_id == employee_id)
    return result
    """Read-only query delegated from controller."""

def _db_employeerelation_all_0(db: Session, employee_id: Any) -> Optional[Any]:
    result = db.query(EmployeeRelation).filter( ((EmployeeRelation.employee_id == employee_id) | (EmployeeRelation.internal_employee_id == employee_id)) ).all()
    return result
    """Read-only query delegated from controller."""

def _db_employeerelation_all_1(db: Session, employee_id: Any) -> Optional[Any]:
    result = db.query(EmployeeRelation).filter( (EmployeeRelation.employee_id == employee_id) | (EmployeeRelation.internal_employee_id == employee_id) ).all()
    return result
    """Read-only query delegated from controller."""

def _db_disciplinarycase_all_2(db: Session) -> Optional[Any]:
    result = db.query(DisciplinaryCase).all()
    return result
    """Read-only query delegated from controller."""

def _db_offboardingcase_all_3(db: Session) -> Optional[Any]:
    result = db.query(OffboardingCase).all()
    return result
    """Read-only query delegated from controller."""
