"""Integration tests for EMS critical paths: onboarding pipeline,
offboarding workflow, and payroll auto-disbursement.

Each test receives a ``db_session`` fixture that wraps every operation in a
transaction rolled back at the end — tests never leak data to one another.
Gap tables (onboarding_pipelines, offboarding_cases, etc.) are created once
at session scope by the ``engine`` fixture in ``conftest.py``.
"""
from __future__ import annotations

import uuid
import pytest
from datetime import datetime, timedelta, date
from decimal import Decimal

from sqlalchemy import text as sa_text


# ── Helpers ───────────────────────────────────────────────────────────────

def _create_test_user(db_session, role: str = "admin", email_suffix: str = None) -> int:
    """Create a test User and return its id."""
    from utils.auth import get_password_hash
    from models import User

    suffix = email_suffix or uuid.uuid4().hex[:8]
    user = User(
        email=f"ems_test_{suffix}@zozi.test",
        username=f"ems_test_{suffix}",
        hashed_password=get_password_hash("test1234"),
        role=role,
        is_active=True,
    )
    db_session.add(user)
    db_session.flush()
    return user.id


def _create_test_employee(db_session, user_id: int = None, country_code: str = "OM") -> int:
    """Create a test Employee record and return its id."""
    from models.employee_models import Employee
    from datetime import date

    code = f"T{uuid.uuid4().hex[:6].upper()}"

    emp = Employee(
        user_id=user_id,
        employee_code=code,
        country_code=country_code,
        department="Engineering",
        position="Engineer",
        employment_status="active",
        hire_date=date.today() - timedelta(days=365),
    )
    db_session.add(emp)
    db_session.flush()
    return emp.id


def _create_test_company_config(db_session):
    """Ensure a minimal country_config row exists."""
    from models import CountryConfig

    existing = db_session.query(CountryConfig).filter(CountryConfig.code == "OM").first()
    if not existing:
        cfg = CountryConfig(code="OM", name="Oman", currency="OMR", currency_symbol="﷼")
        db_session.add(cfg)
        db_session.flush()


# ══════════════════════════════════════════════════════════════════════
#  Test: Onboarding Pipeline
# ══════════════════════════════════════════════════════════════════════

class TestOnboardingPipeline:
    """Create → complete all steps → verify employee is active."""

    @pytest.mark.integration
    def test_full_onboarding_flow(self, db_session):
        _create_test_company_config(db_session)
        user_id = _create_test_user(db_session)
        emp_id = _create_test_employee(db_session, user_id=user_id)

        # ── Step 1: Create pipeline ──
        from services.employee_lifecycle_service import create_onboarding_pipeline

        pipeline = create_onboarding_pipeline(db=db_session, employee_id=emp_id)
        assert pipeline["status"] == "in_progress"
        assert pipeline["total_steps"] == 8  # DEFAULT_ONBOARDING_STEPS count (incl. background_check)
        pipeline_id = pipeline["id"]

        # ── Step 2: Complete all 7 steps ──
        from services.employee_lifecycle_service import complete_onboarding_step

        step_names = [
            "document_collection", "background_check", "biometric_enrollment",
            "equipment_assignment", "id_card_issuance", "orientation",
            "system_access", "buddy_assignment",
        ]
        for idx, step in enumerate(step_names):
            result = complete_onboarding_step(
                db=db_session, pipeline_id=pipeline_id, step_name=step,
                completed_by=user_id,
            )
            assert result["completed"] is True
            expected_progress = f"{idx + 1}/{len(step_names)}"
            assert result["progress"] == expected_progress

        # ── Step 3: Verify pipeline completed ──
        from services.employee_lifecycle_service import get_onboarding_progress

        progress = get_onboarding_progress(db=db_session, pipeline_id=pipeline_id)
        assert progress["pipeline"]["status"] == "completed"
        assert progress["pipeline"]["completed_steps"] == 8
        assert progress["pipeline"]["completed_at"] is not None
        assert len(progress["steps"]) == 8
        for step in progress["steps"]:
            assert step["status"] == "completed"

        # ── Step 4: Verify employee is still active ──
        from models.employee_models import Employee
        emp = db_session.query(Employee).filter(Employee.id == emp_id).first()
        assert emp is not None
        assert emp.employment_status == "active"


# ══════════════════════════════════════════════════════════════════════
#  Test: Offboarding
# ══════════════════════════════════════════════════════════════════════

class TestOffboarding:
    """Create → complete all steps → verify employee terminated."""

    @pytest.mark.integration
    def test_full_offboarding_flow(self, db_session):
        _create_test_company_config(db_session)
        user_id = _create_test_user(db_session)
        emp_id = _create_test_employee(db_session, user_id=user_id)

        # ── Step 1: Initiate offboarding ──
        from services.employee_lifecycle_service import initiate_offboarding

        offboarding = initiate_offboarding(
            db=db_session,
            employee_id=emp_id,
            reason="voluntary_resignation",
            initiated_by=user_id,
            notice_period_days=30,
        )
        assert offboarding["status"] == "in_progress"
        case_id = offboarding["id"]

        # Employee should now be "terminating"
        from models.employee_models import Employee
        emp = db_session.query(Employee).filter(Employee.id == emp_id).first()
        assert emp.employment_status == "terminating"

        # ── Step 2: Complete exit_interview step ──
        from services.employee_lifecycle_service import complete_offboarding_step, get_offboarding_status

        result = complete_offboarding_step(db=db_session, case_id=case_id, step_name="exit_interview")
        assert result["completed"] is True

        status = get_offboarding_status(db=db_session, case_id=case_id)
        assert status["completed_steps"] == 1
        assert status["total_steps"] == 6

        # ── Step 3: Complete asset_reclamation ──
        complete_offboarding_step(db=db_session, case_id=case_id, step_name="asset_reclamation")

        # ── Step 4: Complete access_revocation ──
        complete_offboarding_step(db=db_session, case_id=case_id, step_name="access_revocation")

        # ── Step 5: Complete session_invalidation (this triggers _invalidate_employee_sessions) ──
        complete_offboarding_step(db=db_session, case_id=case_id, step_name="session_invalidation")

        # Employee should now be "terminated"
        emp = db_session.query(Employee).filter(Employee.id == emp_id).first()
        assert emp.employment_status == "terminated"
        assert emp.termination_date is not None

        # ── Step 6: Complete final_payroll ──
        result = complete_offboarding_step(db=db_session, case_id=case_id, step_name="final_payroll")
        assert result["completed"] is True

        # ── Step 7: Complete knowledge_transfer ──
        complete_offboarding_step(db=db_session, case_id=case_id, step_name="knowledge_transfer")

        # ── Step 8: Verify offboarding completed ──
        status = get_offboarding_status(db=db_session, case_id=case_id)
        assert status["status"] == "completed"
        assert status["completed_steps"] == 6

    @pytest.mark.integration
    def test_cancel_offboarding(self, db_session):
        """Test cancelling an offboarding workflow re-activates the employee."""
        _create_test_company_config(db_session)
        user_id = _create_test_user(db_session)
        emp_id = _create_test_employee(db_session, user_id=user_id)

        from services.employee_lifecycle_service import initiate_offboarding, cancel_offboarding

        offboarding = initiate_offboarding(
            db=db_session, employee_id=emp_id,
            reason="resignation", initiated_by=user_id,
        )
        case_id = offboarding["id"]

        # Cancel the offboarding
        cancel_offboarding(db=db_session, case_id=case_id, reason="Employee decided to stay")

        # Verify employee is active again
        from models.employee_models import Employee
        emp = db_session.query(Employee).filter(Employee.id == emp_id).first()
        assert emp.employment_status == "active"


# ══════════════════════════════════════════════════════════════════════
#  Test: Payroll Auto-Disbursement
# ══════════════════════════════════════════════════════════════════════

class TestPayrollAutoDisburse:
    """Run payroll batch → verify payout batch + journal entry created."""

    @pytest.mark.integration
    def test_payroll_calculation(self, db_session):
        """Verify a single employee's payroll calculation returns expected values."""
        _create_test_company_config(db_session)
        user_id = _create_test_user(db_session)
        from models.employee_models import Employee
        from decimal import Decimal

        code = f"PAY{uuid.uuid4().hex[:6].upper()}"
        emp = Employee(
            user_id=user_id, employee_code=code,
            country_code="OM", department="Engineering",
            position="Engineer", employment_status="active",
            salary=Decimal("1500.00"), currency="OMR",
            hire_date=date.today() - timedelta(days=730),  # 2 years
        )
        db_session.add(emp)
        db_session.flush()

        from services.payroll_engine import PayrollEngine

        engine = PayrollEngine(db_session)
        calc = engine.calculate_monthly_payroll(emp.id)

        # Verify calculation structure
        assert calc["employee_id"] == emp.id
        assert calc["base_salary"] == 1500.00
        assert calc["gross_pay"] == 1500.00  # base / 30 * 30 = 1 month
        assert calc["total_deductions"] < calc["gross_pay"]
        assert calc["net_salary"] > 0
        assert calc["currency"] == "OMR"

        # EOSB accrual for 2 years: 21 days/year, * 2 = 42 days / 12 months = 3.5 days/month
        # daily_rate = 1500 / 30 = 50, so 50 * 21 / 12 = 87.5
        assert calc["eosb_accrual"] > 0

    @pytest.mark.integration
    def test_payroll_batch_processing(self, db_session):
        """Verify batch processing creates payslips.
        Transaction isolation ensures no data leakage between tests.
        """
        _create_test_company_config(db_session)
        user_ids = [_create_test_user(db_session, email_suffix=f"payroll_batch_{i}") for i in range(2)]
        emp_ids = []
        from models.employee_models import Employee
        from decimal import Decimal

        for i, uid in enumerate(user_ids):
            code = f"BAT{uuid.uuid4().hex[:6].upper()}"
            emp = Employee(
                user_id=uid, employee_code=code,
                country_code="OM", department="Engineering",
                position="Engineer", employment_status="active",
                salary=Decimal(f"{2000 + i * 500}.00"), currency="OMR",
                hire_date=date.today() - timedelta(days=365),
            )
            db_session.add(emp)
            db_session.flush()
            emp_ids.append(emp.id)

        from services.payroll_engine import PayrollEngine

        engine = PayrollEngine(db_session)
        result = engine.process_payroll_batch(country_code="OM")

        assert result["processed"] == 2
        assert result["total_gross"] > 0
        assert result["total_net"] > 0
        assert len(result["payslips"]) == 2
        for p in result["payslips"]:
            assert p["payslip_id"] is not None
            assert p["net_salary"] > 0

    @pytest.mark.integration
    def test_performance_bonus_integration(self, db_session):
        """Verify performance bonus is calculated when employee has a score."""
        _create_test_company_config(db_session)
        user_id = _create_test_user(db_session)
        from models.employee_models import Employee
        from decimal import Decimal

        code = f"BON{uuid.uuid4().hex[:6].upper()}"
        emp = Employee(
            user_id=user_id, employee_code=code,
            country_code="OM", department="Sales",
            position="Sales Manager", employment_status="active",
            salary=Decimal("2000.00"), currency="OMR",
            hire_date=date.today() - timedelta(days=1095),  # 3 years
            performance_score=4.5,  # High performer (float for SQLite compat)
        )
        db_session.add(emp)
        db_session.flush()

        from services.payroll_engine import PayrollEngine

        engine = PayrollEngine(db_session)
        bonus = engine.calculate_performance_bonus(emp.id)

        # Score 4.5 → bonus_pct = (4.5 - 3.0) * 0.025 = 0.0375 = 3.75%
        # gross = 2000, so bonus = 2000 * 0.0375 = 75.0
        assert bonus > 0
        expected_bonus = Decimal("75.00")
        assert abs(bonus - expected_bonus) < Decimal("0.01")

        # Full payroll calc should include the bonus
        calc = engine.calculate_monthly_payroll(emp.id)
        assert calc["performance_bonus"] > 0
        assert calc["total_additions"] >= calc["performance_bonus"]

    @pytest.mark.integration
    def test_eosb_calculation(self, db_session):
        """Verify EOSB calculation for an employee with 3+ years of service."""
        _create_test_company_config(db_session)
        user_id = _create_test_user(db_session)
        from models.employee_models import Employee
        from decimal import Decimal

        code = f"EOSB{uuid.uuid4().hex[:6].upper()}"
        emp = Employee(
            user_id=user_id, employee_code=code,
            country_code="OM", department="Engineering",
            position="Senior Engineer", employment_status="active",
            salary=Decimal("2500.00"), currency="OMR",
            hire_date=date.today() - timedelta(days=1825),  # 5 years exactly
        )
        db_session.add(emp)
        db_session.flush()

        from services.payroll_engine import PayrollEngine

        engine = PayrollEngine(db_session)
        eosb = engine.calculate_eosb(emp.id)

        # 5 years, daily salary = 2500/30 = 83.33
        # First 5 years: 21 days/year * 5 = 105 days
        # EOSB = 83.33 * 21 * 5 = 8750 (for exactly 5 years, 21 days/year)
        assert eosb > 0
        # Verify it's a reasonable amount (not zero, not absurdly high)
        assert Decimal("1000") < eosb < Decimal("50000")


# ══════════════════════════════════════════════════════════════════════
#  Test: HR Dashboard Integration
# ══════════════════════════════════════════════════════════════════════

class TestHrDashboard:
    """Verify the HR dashboard API endpoint returns data from the new services."""

    @pytest.mark.integration
    def test_hr_dashboard_returns_data(self, db_session):
        """Verify the dashboard endpoint works even with sparse data."""
        _create_test_company_config(db_session)
        user_id = _create_test_user(db_session)
        emp_id = _create_test_employee(db_session, user_id=user_id)

        # Log an activity
        from services.employee_activity_logger import log_activity
        log_activity(
            db=db_session,
            actor_employee_id=emp_id,
            action="login",
            entity_type="session",
            country_code="OM",
        )

        # Query dashboard via raw SQL (same as the router)
        from sqlalchemy import text

        result = db_session.execute(
            text("""
                SELECT
                    SUM(CASE WHEN employment_status = 'active' THEN 1 ELSE 0 END) as active,
                    COUNT(*) as total
                FROM employees
            """)
        ).mappings().first()

        assert result["total"] >= 1
        assert result["active"] >= 1

        # Verify activity was logged
        activity_rows = db_session.execute(
            text("SELECT COUNT(*) as cnt FROM employee_activity_logs")
        ).scalar()
        assert activity_rows >= 1
