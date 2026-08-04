from datetime import date, datetime
from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from data.models_employee_models import Employee, EmployeeShiftRoster
from data.models import EmployeeLeaveLedger


def create_shift_roster(employee_id: int, shift_date: date, shift_name: str, start_time: str, end_time: str, db: Session) -> dict:
    existing = db.query(EmployeeShiftRoster).filter(
        and_(
            EmployeeShiftRoster.employee_id == employee_id,
            EmployeeShiftRoster.shift_date == shift_date,
        )
    ).first()
    
    if existing:
        raise ValueError("Shift roster already exists for this date")
    
    roster = EmployeeShiftRoster(
        employee_id=employee_id,
        shift_date=shift_date,
        shift_name=shift_name,
        start_time=start_time,
        end_time=end_time,
        is_active=True,
    )
    db.add(roster)
    db.commit()
    db.refresh(roster)
    
    return {
        "id": roster.id,
        "employee_id": roster.employee_id,
        "shift_date": roster.shift_date.isoformat(),
        "shift_name": roster.shift_name,
        "start_time": roster.start_time,
        "end_time": roster.end_time,
    }


def get_employee_shift_roster(employee_id: int, db: Session, month: Optional[int] = None, year: Optional[int] = None) -> list[dict]:
    query = db.query(EmployeeShiftRoster).filter(EmployeeShiftRoster.employee_id == employee_id)
    
    if month and year:
        query = query.filter(
            and_(
                EmployeeShiftRoster.shift_date >= date(year, month, 1),
                EmployeeShiftRoster.shift_date <= date(year, month, 28) if month == 2 else (
                    date(year, month, 31) if month in [1,3,5,7,8,10,12] else date(year, month, 30)
                ),
            )
        )
    
    rosters = query.order_by(EmployeeShiftRoster.shift_date).all()
    return [{
        "id": r.id,
        "shift_date": r.shift_date.isoformat(),
        "shift_name": r.shift_name,
        "start_time": r.start_time,
        "end_time": r.end_time,
        "is_active": r.is_active,
    } for r in rosters]


def accrue_leave_days(employee_id: int, db: Session, country_code: str) -> dict:
    emp = db.query(Employee).filter(Employee.id == employee_id).first()
    if not emp:
        raise ValueError("Employee not found")
    
    annual_days = 30 if emp.employment_type == "full_time" else 15
    sick_days = 15
    maternity_days = 90 if emp.gender == "female" else 0
    
    year = datetime.utcnow().year
    
    for leave_type, total in [("annual", annual_days), ("sick", sick_days), ("maternity", maternity_days)]:
        existing = db.query(EmployeeLeaveLedger).filter(
            and_(
                EmployeeLeaveLedger.employee_id == employee_id,
                EmployeeLeaveLedger.leave_type == leave_type,
                EmployeeLeaveLedger.year == year,
            )
        ).first()
        
        if not existing:
            ledger = EmployeeLeaveLedger(
                employee_id=employee_id,
                leave_type=leave_type,
                total_days=total,
                used_days=0,
                accrued_days=total,
                year=year,
            )
            db.add(ledger)
    
    db.commit()
    
    return {
        "employee_id": employee_id,
        "year": year,
        "annual_total": annual_days,
        "sick_total": sick_days,
        "maternity_total": maternity_days,
    }


def request_leave(employee_id: int, leave_type: str, start_date: date, end_date: date, db: Session) -> dict:
    ledger = db.query(EmployeeLeaveLedger).filter(
        and_(
            EmployeeLeaveLedger.employee_id == employee_id,
            EmployeeLeaveLedger.leave_type == leave_type,
            EmployeeLeaveLedger.year == start_date.year,
        )
    ).first()
    
    if not ledger:
        raise ValueError("Leave ledger not found for this year")
    
    requested_days = (end_date - start_date).days + 1
    if ledger.accrued_days - ledger.used_days < requested_days:
        raise ValueError("Insufficient leave balance")
    
    attendance = db.query(EmployeeAttendance).filter(
        and_(
            EmployeeAttendance.employee_id == employee_id,
            EmployeeAttendance.date >= start_date,
            EmployeeAttendance.date <= end_date,
            EmployeeAttendance.status != "present",
        )
    ).first()
    
    if attendance:
        raise ValueError("Cannot request leave during already non-working days")
    
    return {
        "employee_id": employee_id,
        "leave_type": leave_type,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "requested_days": requested_days,
        "status": "pending_approval",
    }


def get_leave_balance(employee_id: int, db: Session) -> dict:
    ledgers = db.query(EmployeeLeaveLedger).filter(EmployeeLeaveLedger.employee_id == employee_id).all()
    
    return {
        "employee_id": employee_id,
        "balances": [{
            "leave_type": l.leave_type,
            "total_days": float(l.total_days),
            "used_days": float(l.used_days),
            "accrued_days": float(l.accrued_days),
            "remaining_days": float(l.accrued_days - l.used_days),
        } for l in ledgers]
    }

