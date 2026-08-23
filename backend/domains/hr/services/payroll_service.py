from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import and_, func

from domains.hr.models.employee_models import Employee
from domains.hr.models.employee_models import EmployeeAttendance
from domains.hr.models.employee_models import EmployeeWorkLog
from domains.hr.models.employee_models import EmployeeLeaveRequest
from domains.hr.models.employee_models import EmployeeLeaveLedger
from domains.hr.ports import PayrollEngine


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


def verify_bank_account(account_id: int, db: Session, current_user: dict):
    """Validate and verify an employee bank account for payroll disbursement."""
    user_id = int(current_user.get("id", 0))
    engine = PayrollEngine(db)
    return engine.validate_bank_account(account_id, verified_by=user_id)



# === Merged from accounts/services/payroll_service.py ===

class PayrollApproveBody(BaseModel):

    batch_id: str

    approved: bool = True

    notes: Optional[str] = None




def approve_payroll_batch(body: PayrollApproveBody, db: Session, current_user: dict):

    """Approve payroll for disbursement (Checker step - cannot be same user as Maker)."""

    parts = body.batch_id.split("-")

    if len(parts) < 3:

        raise HTTPException(status_code=400, detail="Invalid batch_id format")

    country_code = parts[1]

    year = parts[2]

    month = parts[3] if len(parts) > 3 else "01"

    batch_key = f"{country_code}:{year}:{month}"



    user_id = int(current_user.get("id", 0))

    if not check_permission(user_id, "hr.payroll.approve", country_code.upper(), db):

        raise HTTPException(status_code=403, detail="Missing hr.payroll.approve permission")



    pending = PENDING_PAYROLL_APPROVALS.get(batch_key)

    if not pending or pending.get("status") != "pending_approval":

        raise HTTPException(status_code=400, detail="No pending payroll batch found for this period")



    maker_user_id = pending.get("maker_user_id")

    if maker_user_id and maker_user_id == user_id:

        raise HTTPException(status_code=400, detail="Cannot approve your own payroll batch")



    if not body.approved:

        PENDING_PAYROLL_APPROVALS[batch_key]["status"] = "rejected"

        return {"status": "rejected", "batch_id": body.batch_id}



    # Execute auto-disbursement

    engine = PayrollEngine(db)

    period = date(int(year), int(month), 1)

    disbursement = engine.auto_disburse(period, approved_by=user_id)

    disbursement["batch_id"] = body.batch_id

    disbursement["status"] = "disbursed"

    disbursement["approved_by"] = user_id

    disbursement["approved_at"] = datetime.utcnow().isoformat()



    PENDING_PAYROLL_APPROVALS[batch_key] = disbursement

    return disbursement




def calculate_employee_payroll(employee_id: int, month: int, year: int, db: Session, current_user: dict):

    engine = PayrollEngine(db)

    period = date(year, month, 1)

    result = engine.calculate_monthly_payroll(employee_id, period)

    return result




def employee_bank_accounts(employee_id: int, db: Session, current_user: dict):

    engine = PayrollEngine(db)

    return {"bank_accounts": engine.get_employee_bank_accounts(employee_id)}




def get_employee_payslips(employee_id: int, db: Session, current_user: dict):

    docs = (

        db.query(EmployeeDocument)

        .filter(

            EmployeeDocument.employee_id == employee_id,

            EmployeeDocument.doc_type == "payslip",

        )

        .order_by(EmployeeDocument.created_at.desc())

        .all()

    )

    return {

        "payslips": [

            {

                "id": d.id,

                "doc_type": d.doc_type,

                "file_url": d.file_url,

                "created_at": d.created_at.isoformat() if d.created_at else None,

            }

            for d in docs

        ]

    }




def payroll_status(country_code: str, db: Session):

    """Get current payroll batch status for a country."""

    results = {}

    for key, value in PENDING_PAYROLL_APPROVALS.items():

        if key.startswith(country_code.upper()):

            results[key] = {

                "status": value.get("status"),

                "processed": value.get("processed"),

                "total_net": value.get("total_net"),

            }

    return {"payroll_batches": results}




def process_payroll_batch(country_code: str, month: int, year: int, db: Session, current_user: dict):

    """Generate payroll batch (Maker step)."""

    user_id = int(current_user.get("id", 0))

    if not check_permission(user_id, "hr.payroll.release", country_code.upper(), db):

        raise HTTPException(status_code=403, detail="Missing hr.payroll.release permission")



    engine = PayrollEngine(db)

    period = date(year, month, 1)



    # Check if already approved

    batch_key = f"{country_code}:{year}:{month:02d}"

    existing = PENDING_PAYROLL_APPROVALS.get(batch_key)

    if existing and existing.get("status") == "disbursed":

        raise HTTPException(status_code=400, detail="This period has already been disbursed")



    payroll = engine.process_payroll_batch(period, country_code.upper())

    payroll["country_code"] = country_code.upper()

    payroll["status"] = "pending_approval"

    PENDING_PAYROLL_APPROVALS[batch_key] = payroll

    return payroll



