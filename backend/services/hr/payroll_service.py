from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy import and_, func

from data.models_employee_models import Employee, EmployeeAttendance, EmployeeWorkLog, EmployeeLeaveRequest, EmployeeLeaveLedger


def calculate_monthly_payroll(employee_id: int, month: int, year: int, db: Session) -> dict:
    emp = db.query(Employee).filter(Employee.id == employee_id).first()
    if not emp:
        raise ValueError("Employee not found")
    
    start_date = date(year, month, 1)
    if month == 12:
        end_date = date(year + 1, 1, 1) - __import__('datetime').timedelta(days=1)
    else:
        end_date = date(year, month + 1, 1) - __import__('datetime').timedelta(days=1)
    
    attendance_records = db.query(EmployeeAttendance).filter(
        and_(
            EmployeeAttendance.employee_id == employee_id,
            EmployeeAttendance.date >= start_date,
            EmployeeAttendance.date <= end_date,
            EmployeeAttendance.status == "present",
        )
    ).count()
    
    total_work_logs = db.query(EmployeeWorkLog).filter(
        and_(
            EmployeeWorkLog.employee_id == employee_id,
            EmployeeWorkLog.date >= start_date,
            EmployeeWorkLog.date <= end_date,
        )
    ).first()
    
    hours_worked = float(total_work_logs.hours_logged) if total_work_logs else 0
    
    leave_ledger = db.query(EmployeeLeaveLedger).filter(
        and_(
            EmployeeLeaveLedger.employee_id == employee_id,
            EmployeeLeaveLedger.year == year,
        )
    ).all()
    
    total_leave_taken = sum(float(l.used_days) for l in leave_ledger)
    
    base_salary = emp.salary or Decimal("0")
    daily_rate = base_salary / 30 if base_salary else Decimal("0")
    
    gross_salary = daily_rate * attendance_records
    
    tax_deduction = gross_salary * Decimal("0.05") if emp.tax_bracket else Decimal("0")
    eosb_accrual = daily_rate * Decimal("15")
    
    net_salary = gross_salary - tax_deduction
    
    return {
        "employee_id": employee_id,
        "employee_code": emp.employee_code,
        "payroll_period": f"{year}-{month:02d}",
        "gross_salary": float(gross_salary),
        "tax_deduction": float(tax_deduction),
        "eosb_accrual": float(eosb_accrual),
        "net_salary": float(net_salary),
        "working_days": attendance_records,
        "hours_worked": hours_worked,
        "leave_taken": total_leave_taken,
        "currency": emp.currency or "OMR",
        "calculated_at": datetime.utcnow().isoformat(),
    }


def generate_payroll_batch(country_code: str, month: int, year: int, db: Session) -> dict:
    employees = db.query(Employee).filter(Employee.country_code == country_code.upper()).all()
    
    payroll_items = []
    total_gross = Decimal("0")
    total_tax = Decimal("0")
    total_net = Decimal("0")
    total_eosb = Decimal("0")
    
    for emp in employees:
        try:
            item = calculate_monthly_payroll(emp.id, month, year, db)
            payroll_items.append(item)
            total_gross += Decimal(str(item["gross_salary"]))
            total_tax += Decimal(str(item["tax_deduction"]))
            total_net += Decimal(str(item["net_salary"]))
            total_eosb += Decimal(str(item["eosb_accrual"]))
        except Exception as e:
            payroll_items.append({
                "employee_id": emp.id,
                "error": str(e),
            })
    
    return {
        "batch_id": f"PAYROLL-{country_code}-{year}-{month:02d}",
        "country_code": country_code,
        "period": f"{year}-{month:02d}",
        "total_employees": len(employees),
        "total_gross_salary": float(total_gross),
        "total_tax_deduction": float(total_tax),
        "total_net_salary": float(total_net),
        "total_eosb_accrual": float(total_eosb),
        "items": payroll_items,
        "generated_at": datetime.utcnow().isoformat(),
    }


def freeze_payroll_for_employee(employee_id: int, reason: str, db: Session) -> dict:
    emp = db.query(Employee).filter(Employee.id == employee_id).first()
    if not emp:
        raise ValueError("Employee not found")
    
    return {
        "employee_id": employee_id,
        "status": "frozen",
        "reason": reason,
        "frozen_at": datetime.utcnow().isoformat(),
    }


def unfreeze_payroll_for_employee(employee_id: int, db: Session) -> dict:
    emp = db.query(Employee).filter(Employee.id == employee_id).first()
    if not emp:
        raise ValueError("Employee not found")
    
    return {
        "employee_id": employee_id,
        "status": "active",
        "unfrozen_at": datetime.utcnow().isoformat(),
    }

