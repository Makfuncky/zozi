"""
HR Domain — employee management, QR auth, attendance.

Models and DB dependencies are imported lazily to avoid circular imports
with db.database and SQLAlchemy metadata conflicts with the main models package.
"""
import logging
from datetime import datetime
from typing import Generator, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

router = APIRouter()


def get_db_session() -> Generator[Session, None, None]:
    from db.database import get_db
    yield from get_db()


def _get_qr_auth():
    from utils.qr_auth import get_qr_auth
    from utils.config import settings
    return get_qr_auth(settings.secret_key)


@router.get("/employees/{employee_id}")
def get_employee(employee_id: int, db: Session = Depends(get_db_session)):
    from db.employee_models import Employee
    emp = db.query(Employee).filter(Employee.id == employee_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    return emp


@router.post("/employees")
def create_employee(emp_data: dict, db: Session = Depends(get_db_session)):
    from db.employee_models import Employee
    emp = Employee(**emp_data)
    db.add(emp)
    db.commit()
    db.refresh(emp)
    return emp


@router.post("/employees/{employee_id}/qr-login")
def generate_qr_login(employee_id: int, db: Session = Depends(get_db_session)):
    qr_service = _get_qr_auth()
    return qr_service.generate_login_qr(employee_id)


@router.post("/auth/validate-qr")
def validate_qr_login(qr_data: str):
    qr_service = _get_qr_auth()
    result = qr_service.validate_qr(qr_data)
    if not result["valid"]:
        raise HTTPException(status_code=401, detail=result["error"])
    return result


@router.post("/employees/{employee_id}/attendance/scan")
def record_attendance(
    employee_id: int,
    scan_type: str,
    lat: Optional[float] = None,
    long: Optional[float] = None,
    device_fp: Optional[str] = None,
    db: Session = Depends(get_db_session)
):
    from db.employee_models import EmployeeAttendance
    attendance = EmployeeAttendance(
        employee_id=employee_id,
        scan_in_time=datetime.utcnow(),
        scan_type=scan_type,
        location_lat=lat,
        location_long=long,
        device_fingerprint=device_fp
    )
    db.add(attendance)
    db.commit()
    db.refresh(attendance)
    return attendance
