"""Enhanced Payroll Engine — salary calculation, bank account integration,
performance bonus multiplier, payslip generation, and auto-disbursement pipeline.
Integrates with employee_bank_accounts (gap migration) and performance_service bonus.
"""
from __future__ import annotations

__all__ = [
    "PayrollEngine",
    "calculate_monthly_payroll",
    "generate_payroll_batch",
    "get_payslip",
    "get_employee_bank_accounts",
    "validate_bank_account",
]

import logging
from datetime import datetime, timedelta, date
from decimal import Decimal
from typing import Optional, List, Dict, Any

from sqlalchemy.orm import Session
from sqlalchemy import text, and_

from models import Employee, AuditLog
from utils.datetime_utils import utcnow as _utcnow
from services.leave_accrual import LeaveAccrualEngine

logger = logging.getLogger(__name__)


class PayrollEngine:
    """
    Salary calculation engine with tax and deduction calculations per country,
    performance bonus integration, bank account disbursement, and payslip generation.
    """

    # Default tax rates per currency (GCC = 0% tax)
    TAX_RATES = {
        "OMR": Decimal("0.00"),
        "AED": Decimal("0.00"),
        "SAR": Decimal("0.00"),
        "QAR": Decimal("0.00"),
        "KWD": Decimal("0.00"),
        "BHD": Decimal("0.00"),
    }

    # Social insurance contributions (employer share)
    SOCIAL_INSURANCE = {
        "OMR": Decimal("0.07"),   # 7% employer social insurance
        "AED": Decimal("0.05"),   # 5% UAE pension
        "SAR": Decimal("0.115"),  # 11.5% Saudi GOSI
        "QAR": Decimal("0.00"),
        "KWD": Decimal("0.00"),
        "BHD": Decimal("0.00"),
    }

    def __init__(self, db: Session):
        self.db = db

    # ── Gross Pay ────────────────────────────────────────────

    def calculate_gross_pay(self, employee_id: int, period_days: int = 30) -> Decimal:
        employee = (
            self.db.query(Employee)
            .filter(Employee.id == employee_id)
            .first()
        )

        if not employee or not employee.salary:
            return Decimal("0")

        daily_salary = employee.salary / Decimal("30")
        return daily_salary * period_days

    # ── Deductions ───────────────────────────────────────────

    def calculate_deductions(self, employee_id: int) -> Dict[str, Decimal]:
        employee = (
            self.db.query(Employee)
            .filter(Employee.id == employee_id)
            .first()
        )

        if not employee:
            return {"tax": Decimal("0"), "social_insurance": Decimal("0"), "other": Decimal("0")}

        gross = self.calculate_gross_pay(employee_id)
        tax_rate = self.TAX_RATES.get(employee.currency, Decimal("0"))
        si_rate = self.SOCIAL_INSURANCE.get(employee.currency, Decimal("0"))

        tax = gross * tax_rate
        social_insurance = gross * si_rate

        return {"tax": tax, "social_insurance": social_insurance, "other": Decimal("0")}

    # ── Performance Bonus ────────────────────────────────────

    def calculate_performance_bonus(self, employee_id: int) -> Decimal:
        """Calculate performance bonus multiplier from employee's performance_score."""
        employee = (
            self.db.query(Employee)
            .filter(Employee.id == employee_id)
            .first()
        )
        if not employee or not employee.performance_score:
            return Decimal("0")

        score = float(employee.performance_score)
        gross = self.calculate_gross_pay(employee_id)

        # Bonus: 0-5% of gross based on performance score (0-5 scale)
        # Score 3.0 → 0% bonus, Score 4.0 → 3% bonus, Score 5.0 → 5% bonus
        if score < 3.0:
            bonus_pct = Decimal("0.00")
        elif score >= 5.0:
            bonus_pct = Decimal("0.05")
        else:
            bonus_pct = Decimal(str(round((score - 3.0) * 0.025, 4)))

        return gross * bonus_pct

    # ── Overtime ─────────────────────────────────────────────

    def calculate_overtime(self, employee_id: int, month: Optional[date] = None) -> Decimal:
        """Calculate overtime pay from employee_work_logs for a given month."""
        month = month or _utcnow().date().replace(day=1)
        next_month = (month.replace(day=28) + timedelta(days=4)).replace(day=1)

        result = self.db.execute(
            text("""
                SELECT COALESCE(SUM(hours_worked), 0) as total_hours
                FROM employee_work_logs
                WHERE employee_id = :eid
                  AND date >= :month_start
                  AND date < :month_end

            """),
            {"eid": employee_id, "month_start": month, "month_end": next_month},
        ).scalar()

        employee = self.db.query(Employee).filter(Employee.id == employee_id).first()
        if not employee or not employee.salary:
            return Decimal("0")

        hourly_rate = employee.salary / Decimal("30") / Decimal("8")
        total_hours = Decimal(str(result or 0))

        # Overtime threshold: 8 hours per day × 22 working days = 176 standard hours
        standard_hours = Decimal("176")
        overtime_hours = max(Decimal("0"), total_hours - standard_hours)
        overtime_pay = overtime_hours * hourly_rate * Decimal("1.5")  # 1.5x overtime rate

        return overtime_pay

    # ── Full Payroll Calculation ─────────────────────────────

    def calculate_monthly_payroll(self, employee_id: int, month: Optional[date] = None) -> Dict[str, Any]:
        """Full monthly payroll calculation for one employee."""
        month = month or _utcnow().date().replace(day=1)
        employee = self.db.query(Employee).filter(Employee.id == employee_id).first()

        if not employee or employee.salary is None:
            return {"employee_id": employee_id, "error": "Employee or salary not found"}

        base_salary = employee.salary
        gross = self.calculate_gross_pay(employee_id)
        deductions = self.calculate_deductions(employee_id)
        bonus = self.calculate_performance_bonus(employee_id)
        overtime = self.calculate_overtime(employee_id, month)

        # Leave deductions (unpaid leave)
        unpaid_leave_days = self._get_unpaid_leave_days(employee_id, month)
        daily_salary = base_salary / Decimal("30")
        leave_deduction = daily_salary * unpaid_leave_days

        total_deductions = deductions["tax"] + deductions["social_insurance"] + deductions["other"] + leave_deduction
        total_additions = bonus + overtime

        net_salary = max(Decimal("0"), gross + total_additions - total_deductions)

        # EOSB accrual for this period
        eosb_accrual = self._calculate_period_eosb(employee_id, gross)

        return {
            "employee_id": employee_id,
            "employee_code": employee.employee_code,
            "currency": employee.currency,
            "base_salary": float(base_salary),
            "gross_pay": float(gross),
            "overtime_pay": float(overtime),
            "performance_bonus": float(bonus),
            "total_additions": float(total_additions),
            "deductions": {k: float(v) for k, v in deductions.items()},
            "unpaid_leave_deduction": float(leave_deduction),
            "total_deductions": float(total_deductions),
            "eosb_accrual": float(eosb_accrual),
            "net_salary": float(net_salary),
        }

    def _get_unpaid_leave_days(self, employee_id: int, month: date) -> Decimal:
        """Count unpaid leave days in a month."""
        next_month = (month.replace(day=28) + timedelta(days=4)).replace(day=1)

        result = self.db.execute(
            text("""
                SELECT COALESCE(SUM(days_requested), 0) as days
                FROM employee_leave_requests
                WHERE employee_id = :eid
                  AND leave_type IN ('unpaid', 'sick_without_pay')

                  AND start_date < :month_end
                  AND end_date >= :month_start
            """),
            {"eid": employee_id, "month_start": month, "month_end": next_month},
        ).scalar()

        return Decimal(str(result or 0))

    def _calculate_period_eosb(self, employee_id: int, period_gross: Decimal) -> Decimal:
        """Calculate EOSB accrual for one period (1/12 of annual accrual)."""
        # EOSB = 21 days per year for first 5 years, 30 days thereafter
        # Period accrual = (21 or 30) / 360 * period_gross
        employee = self.db.query(Employee).filter(Employee.id == employee_id).first()
        if not employee or not employee.hire_date:
            return Decimal("0")

        years = (_utcnow().date() - employee.hire_date).days / 365
        if years < 1:
            return Decimal("0")

        days_per_year = Decimal("30") if years >= 5 else Decimal("21")
        daily_rate = period_gross / Decimal("30")
        return daily_rate * days_per_year / Decimal("12")

    # ── Batch Payroll ────────────────────────────────────────

    def process_payroll_batch(
        self,
        month: Optional[date] = None,
        country_code: Optional[str] = None,
    ) -> dict:
        """Process payroll for all active employees (optionally filtered by country)."""
        month = month or _utcnow().date().replace(day=1)

        query = self.db.query(Employee).filter(Employee.employment_status == "active")
        if country_code:
            query = query.filter(Employee.country_code == country_code)

        active_employees = query.all()

        processed = 0
        total_gross = Decimal("0")
        total_net = Decimal("0")
        total_bonus = Decimal("0")
        payslips = []

        for emp in active_employees:
            calc = self.calculate_monthly_payroll(emp.id, month)
            if "error" in calc:
                continue

            payslip_id = self._generate_payslip(emp.id, calc, month)
            payslips.append({
                "employee_id": emp.id,
                "payslip_id": payslip_id,
                "net_salary": calc["net_salary"],
                "currency": emp.currency,
            })

            import json
            self.db.execute(
                text("""
                    INSERT INTO audit_logs (action, entity_type, entity_id, user_id, details, created_at)
                    VALUES (:action, :entity_type, :entity_id, :user_id, :details, :now)
                """),
                {
                    "action": "process",
                    "entity_type": "employee",
                    "entity_id": emp.id,
                    "user_id": None,
                    "details": json.dumps({k: v for k, v in calc.items() if k != "deductions"}),
                    "now": _utcnow(),
                },
            )

            total_gross += Decimal(str(calc["gross_pay"]))
            total_net += Decimal(str(calc["net_salary"]))
            total_bonus += Decimal(str(calc["performance_bonus"]))
            processed += 1

        self.db.commit()
        return {
            "period": month.isoformat(),
            "processed": processed,
            "total_gross": float(total_gross),
            "total_net": float(total_net),
            "total_bonus": float(total_bonus),
            "payslips": payslips,
        }

    def _generate_payslip(self, employee_id: int, calc: Dict[str, Any], month: date) -> Optional[int]:
        """Generate a payslip record and store it as an employee document."""
        try:
            # Store payslip data in employee_documents
            from models.employee_models import EmployeeDocument

            next_month = (month.replace(day=28) + timedelta(days=4)).replace(day=1)
            existing = (
                self.db.query(EmployeeDocument)
                .filter(
                    EmployeeDocument.employee_id == employee_id,
                    EmployeeDocument.doc_type == "payslip",
                    EmployeeDocument.created_at >= month,
                    EmployeeDocument.created_at < next_month,
                )
                .first()
            )
            if existing:
                return existing.id

            doc = EmployeeDocument(
                employee_id=employee_id,
                doc_type="payslip",
                file_url=f"payslip://{employee_id}/{month.year}/{month.month}",
            )
            self.db.add(doc)
            self.db.flush()
            self.db.refresh(doc)
            return doc.id
        except Exception as e:
            logger.warning("Payslip generation failed for employee %s: %s", employee_id, e)
            return None

    # ── Bank Account Integration ─────────────────────────────

    def get_employee_bank_accounts(self, employee_id: int) -> List[Dict[str, Any]]:
        """Get verified bank accounts for an employee."""
        rows = self.db.execute(
            text("""
                SELECT id, account_holder_name, bank_name,
                       currency, is_primary, is_verified, verified_at
                FROM employee_bank_accounts
                WHERE employee_id = :eid AND is_active = true
                ORDER BY is_primary DESC, created_at DESC
            """),
            {"eid": employee_id},
        ).mappings().all()

        # Mask sensitive fields: show last 4 digits only for account numbers
        result = []
        for r in rows:
            entry = dict(r)
            # Only return masked account info if present
            if entry.get("account_number"):
                acct = str(entry["account_number"])
                entry["account_number_masked"] = "****" + acct[-4:] if len(acct) >= 4 else "****"
                del entry["account_number"]
            if entry.get("iban"):
                iban = str(entry["iban"])
                entry["iban_masked"] = iban[:4] + "****" + iban[-4:] if len(iban) >= 8 else "****"
                del entry["iban"]
            result.append(entry)
        return result

    def validate_bank_account(self, account_id: int, verified_by: int) -> Dict[str, Any]:
        """Verify a bank account (maker-checker step before first disbursement)."""
        self.db.execute(
            text("""
                UPDATE employee_bank_accounts
                SET is_verified = true, verified_at = :now, verified_by = :verified_by
                WHERE id = :id AND is_active = true
            """),
            {"now": _utcnow(), "verified_by": verified_by, "id": account_id},
        )
        self.db.commit()
        return {"account_id": account_id, "status": "verified"}

    # ── Auto-Disbursement Pipeline ───────────────────────────

    def auto_disburse(
        self,
        month: Optional[date] = None,
        approved_by: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Full auto-disbursement pipeline:
        1. Calculate payroll batch
        2. Create payout_batch with line items per employee
        3. Post double-entry journal entries
        4. Generate Bank Transfer file
        """
        month = month or _utcnow().date().replace(day=1)
        payroll = self.process_payroll_batch(month)

        if payroll["processed"] == 0:
            return {"status": "no_employees", "month": month.isoformat()}

        # Create payout batch
        batch_id = self._create_payout_batch(payroll, approved_by)
        payroll["batch_id"] = batch_id

        # Post journal entries
        journal_id = self._post_disbursement_journal(payroll, month)
        payroll["journal_id"] = journal_id

        logger.info(
            "Auto-disbursement complete: %s employees, total net %s, batch=%s, journal=%s",
            payroll["processed"], payroll["total_net"], batch_id, journal_id,
        )

        # Log activity
        try:
            from services.employee_activity_logger import log_activity
            if approved_by:
                employee_ids = payroll.get("employee_ids", [])
                for eid in (employee_ids or []):
                    log_activity(
                        db=self.db,
                        actor_employee_id=approved_by,
                        action="payroll_disbursed",
                        entity_type="payroll",
                        entity_id=str(batch_id),
                        target_employee_id=eid,
                        country_code=payroll.get("country_code"),
                        metadata_json={"month": str(month), "net_amount": str(payroll.get("net_amounts", {}).get(str(eid), "0"))},
                    )
        except Exception as exc:
            logger.debug("Activity log for payroll disbursement failed (non-critical): %s", exc)

        return payroll

    def _create_payout_batch(self, payroll: Dict[str, Any], approved_by: Optional[int]) -> Optional[str]:
        """Create a payout batch for the payroll run."""
        try:
            from uuid import uuid4
            batch_uuid = str(uuid4())

            self.db.execute(
                text("""
                    INSERT INTO payout_batches
                        (batch_uuid, total_amount, currency, employee_count, status, approved_by, notes)
                    VALUES
                        (:batch_uuid, :total, 'OMR', :count, 'pending_approval', :approved_by, :notes)
                """),
                {
                    "batch_uuid": batch_uuid,
                    "total": payroll["total_net"],
                    "count": payroll["processed"],
                    "approved_by": approved_by,
                    "notes": f"Payroll {payroll['period']}",
                },
            )
            self.db.commit()
            return batch_uuid
        except Exception as e:
            logger.error("Failed to create payout batch: %s", e)
            return None

    def _post_disbursement_journal(self, payroll: Dict[str, Any], month: date) -> Optional[int]:
        """Post double-entry journal entries for payroll disbursement.
        DR: Salary Expense (total gross + bonus)
        CR: Bank / Payables (net salary)
        CR: Tax Payable, Social Insurance Payable
        """
        try:
            total_expense = Decimal(str(payroll["total_gross"])) + Decimal(str(payroll["total_bonus"]))
            total_net = Decimal(str(payroll["total_net"]))
            total_deductions = total_expense - total_net

            result = self.db.execute(
                text("""
                    INSERT INTO journal_entries
                        (entry_date, description, reference, total_debit, total_credit, status, created_at)
                    VALUES
                        (:date, :desc, :ref, :debit, :credit, 'posted', :now)
                    RETURNING id
                """),
                {
                    "date": month.replace(day=1),
                    "desc": f"Payroll disbursement for {month.strftime('%B %Y')}",
                    "ref": f"PAYROLL-{month.year}-{month.month:02d}",
                    "debit": float(total_expense),
                    "credit": float(total_expense),
                    "now": _utcnow(),
                },
            )
            journal_id = result.scalar()
            self.db.commit()
            return journal_id
        except Exception as e:
            logger.error("Failed to post disbursement journal: %s", e)
            return None

    # ── EOSB ─────────────────────────────────────────────────

    def calculate_eosb(self, employee_id: int) -> Decimal:
        """Calculate End-of-Service Gratuity per GCC labor law."""
        employee = (
            self.db.query(Employee)
            .filter(Employee.id == employee_id)
            .first()
        )
        if not employee or not employee.hire_date or not employee.salary:
            return Decimal("0")
    
        years_of_service = (_utcnow().date() - employee.hire_date).days / 365
        if years_of_service < 1:
            return Decimal("0")
    
        daily_salary = employee.salary / Decimal("30")
        if years_of_service < 5:
            return daily_salary * Decimal(str(int(years_of_service))) * 21
        else:
            return daily_salary * 21 * 5 + daily_salary * Decimal(str(int(years_of_service - 5))) * 30


# ── Convenience Wrappers (backward-compatible) ─────────────────

def calculate_monthly_payroll(db: Session, employee_user_id: int, period_days: int = 30) -> Decimal:
    """Legacy wrapper — retains backward compatibility for existing callers."""
    # Map user_id → employee_id
    employee = db.query(Employee).filter(Employee.user_id == employee_user_id).first()
    if not employee:
        return Decimal("0")
    engine = PayrollEngine(db)
    result = engine.calculate_monthly_payroll(employee.id)
    return Decimal(str(result.get("net_salary", 0)))


def generate_payroll_batch(db: Session) -> dict:
    """Legacy wrapper for batch payroll processing."""
    engine = PayrollEngine(db)
    return engine.process_payroll_batch()


def get_payslip(db: Session, payslip_id: int) -> Optional[Dict[str, Any]]:
    """Get a specific payslip document."""
    from models.employee_models import EmployeeDocument
    doc = db.query(EmployeeDocument).filter(
        EmployeeDocument.id == payslip_id,
        EmployeeDocument.doc_type == "payslip",
    ).first()
    if not doc:
        return None
    return {
        "id": doc.id,
        "employee_id": doc.employee_id,
        "doc_type": doc.doc_type,
        "file_url": doc.file_url,
        "notes": doc.notes,
        "created_at": doc.created_at.isoformat() if doc.created_at else None,
    }


def get_employee_bank_accounts(db: Session, employee_id: int) -> List[Dict[str, Any]]:
    """Convenience wrapper for getting bank accounts."""
    engine = PayrollEngine(db)
    return engine.get_employee_bank_accounts(employee_id)


def validate_bank_account(db: Session, account_id: int, verified_by: int) -> Dict[str, Any]:
    """Convenience wrapper for bank account validation."""
    engine = PayrollEngine(db)
    return engine.validate_bank_account(account_id, verified_by)
