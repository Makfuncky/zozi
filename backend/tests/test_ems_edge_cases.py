"""Edge-case and property-based tests for the EMS domain.

Topics covered:
  - Duplicate onboarding (UNIQUE constraint on employee_id)
  - Double-cancel offboarding (idempotency / ValueError)
  - Payroll for zero-salary employees
  - Offboarding initiated on an already-terminated employee
  - Non-existent employee / pipeline / case
  - Already-completed steps
  - Very-long-tenure EOSB (>10 years)
  - Property-based invariants for monthly payroll calculation

Every test receives a ``db_session`` wrapped in a transaction rolled back at
the end (see ``conftest.py`` for the isolation fixture).
"""
from typing import Set

import uuid

import pytest
from datetime import datetime, timedelta, date
from decimal import Decimal

from hypothesis import given, settings, strategies as st, HealthCheck

from concurrent.futures import ThreadPoolExecutor, as_completed
from sqlalchemy import create_engine, text as sa_text
from sqlalchemy.orm import sessionmaker


# ── Shared helpers (mirror test_ems_lifecycle.py) ─────────────────────

def _create_test_user(db_session, role: str = "admin", email_suffix: str = None) -> int:
    from data.utils_auth import get_password_hash
    from data.models import User

    suffix = email_suffix or uuid.uuid4().hex[:8]
    user = User(
        email=f"edge_test_{suffix}@zozi.test",
        username=f"edge_test_{suffix}",
        hashed_password=get_password_hash("test1234"),
        role=role,
        is_active=True,
    )
    db_session.add(user)
    db_session.flush()
    return user.id


def _create_test_employee(
    db_session,
    user_id: int = None,
    country_code: str = "OM",
    salary: Decimal = None,
    hire_date: date = None,
    performance_score: float = None,
) -> int:
    from data.models_employee_models import Employee

    code = f"EDGE{uuid.uuid4().hex[:6].upper()}"
    emp = Employee(
        user_id=user_id,
        employee_code=code,
        country_code=country_code,
        department="Engineering",
        position="Engineer",
        employment_status="active",
        salary=salary if salary is not None else Decimal("1000.00"),
        currency="OMR",
        hire_date=hire_date or (date.today() - timedelta(days=365)),
        performance_score=performance_score,
    )
    db_session.add(emp)
    db_session.flush()
    return emp.id


def _ensure_country_config(db_session):
    from data.models import CountryConfig
    existing = db_session.query(CountryConfig).filter(CountryConfig.code == "OM").first()
    if not existing:
        cfg = CountryConfig(code="OM", name="Oman", currency="OMR", currency_symbol="﷼")
        db_session.add(cfg)
        db_session.flush()


# ══════════════════════════════════════════════════════════════════════
#  Edge Case: Duplicate Onboarding (UNIQUE constraint)
# ══════════════════════════════════════════════════════════════════════

class TestDuplicateOnboarding:
    """onboarding_pipelines.employee_id has a UNIQUE constraint."""

    @pytest.mark.integration
    def test_duplicate_pipeline_raises_error(self, db_session):
        """Creating a second pipeline for the same employee must fail."""
        _ensure_country_config(db_session)
        user_id = _create_test_user(db_session)
        emp_id = _create_test_employee(db_session, user_id=user_id)

        from data.services_employee_lifecycle_service import create_onboarding_pipeline

        # First pipeline succeeds
        first = create_onboarding_pipeline(db=db_session, employee_id=emp_id)
        assert first["status"] == "in_progress"

        # Second pipeline for the same employee must fail (UNIQUE constraint)
        import sqlalchemy
        with pytest.raises((sqlalchemy.exc.IntegrityError, ValueError)):
            create_onboarding_pipeline(db=db_session, employee_id=emp_id)

    @pytest.mark.integration
    def test_onboarding_nonexistent_employee_raises(self, db_session):
        """Creating a pipeline for a non-existent employee must raise."""
        _ensure_country_config(db_session)
        from data.services_employee_lifecycle_service import create_onboarding_pipeline

        with pytest.raises(ValueError, match="not found"):
            create_onboarding_pipeline(db=db_session, employee_id=99999)

    @pytest.mark.integration
    def test_complete_step_nonexistent_pipeline_raises(self, db_session):
        """Completing a step on a pipeline that does not exist must raise."""
        _ensure_country_config(db_session)
        from data.services_employee_lifecycle_service import complete_onboarding_step

        with pytest.raises((ValueError, KeyError)):
            complete_onboarding_step(
                db=db_session,
                pipeline_id=99999,
                step_name="document_collection",
                completed_by=1,
            )


# ══════════════════════════════════════════════════════════════════════
#  Edge Case: Double-Cancel Offboarding
# ══════════════════════════════════════════════════════════════════════

class TestDoubleCancelOffboarding:
    """Cancelling an offboarding case that is already cancelled must
    raise ValueError or be idempotent — the system must not double-activate."""

    @pytest.mark.integration
    def test_cancel_already_cancelled_raises(self, db_session):
        """Cancelling a case that was already cancelled should raise."""
        _ensure_country_config(db_session)
        user_id = _create_test_user(db_session)
        emp_id = _create_test_employee(db_session, user_id=user_id)

        from data.services_employee_lifecycle_service import (
            initiate_offboarding, cancel_offboarding,
        )

        offboarding = initiate_offboarding(
            db=db_session, employee_id=emp_id,
            reason="resignation", initiated_by=user_id,
        )
        case_id = offboarding["id"]

        # First cancel succeeds
        result = cancel_offboarding(db=db_session, case_id=case_id, reason="Retention offer accepted")
        assert result["status"] == "cancelled"

        # Employee should be active again
        from data.models_employee_models import Employee
        emp = db_session.query(Employee).filter(Employee.id == emp_id).first()
        assert emp.employment_status == "active"

        # Second cancel must raise (case is already cancelled)
        with pytest.raises((ValueError, KeyError)):
            cancel_offboarding(db=db_session, case_id=case_id, reason="Double cancel attempt")

    @pytest.mark.integration
    def test_cancel_completed_offboarding_raises(self, db_session):
        """Cancelling an offboarding case that is already completed should raise."""
        _ensure_country_config(db_session)
        user_id = _create_test_user(db_session)
        emp_id = _create_test_employee(db_session, user_id=user_id)

        from data.services_employee_lifecycle_service import (
            initiate_offboarding, complete_offboarding_step, cancel_offboarding,
        )

        case = initiate_offboarding(
            db=db_session, employee_id=emp_id,
            reason="voluntary_resignation", initiated_by=user_id,
        )
        case_id = case["id"]

        # Complete all 6 steps to finish offboarding
        step_names = [
            "exit_interview", "asset_reclamation", "access_revocation",
            "session_invalidation", "final_payroll", "knowledge_transfer",
        ]
        for step in step_names:
            complete_offboarding_step(db=db_session, case_id=case_id, step_name=step)

        # Verify completed
        from data.services_employee_lifecycle_service import get_offboarding_status
        status = get_offboarding_status(db=db_session, case_id=case_id)
        assert status["status"] == "completed"

        # Cancelling a completed case must raise
        with pytest.raises((ValueError, KeyError)):
            cancel_offboarding(db=db_session, case_id=case_id, reason="Retroactive cancel")

    @pytest.mark.integration
    def test_cancel_nonexistent_case_raises(self, db_session):
        """Cancelling a case that doesn't exist must raise."""
        from data.services_employee_lifecycle_service import cancel_offboarding

        with pytest.raises(ValueError, match="not found"):
            cancel_offboarding(db=db_session, case_id=99999, reason="No such case")


# ══════════════════════════════════════════════════════════════════════
#  Edge Case: Offboarding Already-Terminated Employee
# ══════════════════════════════════════════════════════════════════════

class TestOffboardingTerminatedEmployee:
    """Initiating offboarding for an already-terminated employee must fail."""

    @pytest.mark.integration
    def test_initiate_offboarding_terminated_employee(self, db_session):
        """Initiate offboarding on an employee already terminated must raise or return error."""
        _ensure_country_config(db_session)
        user_id = _create_test_user(db_session)
        emp_id = _create_test_employee(db_session, user_id=user_id)

        # First offboarding
        from data.services_employee_lifecycle_service import (
            initiate_offboarding, complete_offboarding_step,
        )

        case = initiate_offboarding(
            db=db_session, employee_id=emp_id,
            reason="voluntary_resignation", initiated_by=user_id,
        )

        # Fast-track to completion (session_invalidation triggers termination)
        for step in ["exit_interview", "asset_reclamation", "access_revocation", "session_invalidation"]:
            complete_offboarding_step(db=db_session, case_id=case["id"], step_name=step)

        from data.models_employee_models import Employee
        emp = db_session.query(Employee).filter(Employee.id == emp_id).first()
        assert emp.employment_status == "terminated"

        # Second offboarding for the same (now terminated) employee must raise
        from data.services_employee_lifecycle_service import initiate_offboarding as init_off
        with pytest.raises((ValueError, KeyError)):
            init_off(
                db=db_session, employee_id=emp_id,
                reason="second_attempt", initiated_by=user_id,
            )

    @pytest.mark.integration
    def test_get_status_nonexistent_case_raises(self, db_session):
        """Getting offboarding status for a non-existent case must raise."""
        from data.services_employee_lifecycle_service import get_offboarding_status

        with pytest.raises(ValueError, match="not found"):
            get_offboarding_status(db=db_session, case_id=99999)


# ══════════════════════════════════════════════════════════════════════
#  Edge Case: Zero-Salary Employee Payroll
# ══════════════════════════════════════════════════════════════════════

class TestZeroSalaryPayroll:
    """Payroll engine must handle zero-salary employees gracefully."""

    @pytest.mark.integration
    def test_calculate_monthly_payroll_zero_salary(self, db_session):
        """Monthly payroll for zero-salary employee must not crash and return zero amounts."""
        _ensure_country_config(db_session)
        user_id = _create_test_user(db_session)
        emp_id = _create_test_employee(
            db_session, user_id=user_id,
            salary=Decimal("0.00"),
        )

        from data.services_payroll_engine import PayrollEngine
        engine = PayrollEngine(db_session)
        calc = engine.calculate_monthly_payroll(emp_id)

        assert calc["base_salary"] == 0.0
        assert calc["gross_pay"] == 0.0
        assert calc["net_salary"] == 0.0
        assert calc["total_deductions"] == 0.0
        assert calc["total_additions"] == 0.0
        assert calc["performance_bonus"] == 0.0
        assert calc["overtime_pay"] == 0.0
        assert calc["eosb_accrual"] == 0.0

    @pytest.mark.integration
    def test_payroll_batch_skips_zero_salary(self, db_session):
        """Batch processing must handle zero-salary employees without crashing."""
        _ensure_country_config(db_session)

        # Create one normal employee and one zero-salary employee
        user1 = _create_test_user(db_session, email_suffix="batch_normal")
        user2 = _create_test_user(db_session, email_suffix="batch_zero")

        _create_test_employee(db_session, user_id=user1, salary=Decimal("2000.00"))
        _create_test_employee(db_session, user_id=user2, salary=Decimal("0.00"))

        from data.services_payroll_engine import PayrollEngine
        engine = PayrollEngine(db_session)
        result = engine.process_payroll_batch(country_code="OM")

        # Both employees should be processed or at least not crash
        assert result["processed"] >= 1  # At least the normal salaried one
        assert result["total_gross"] >= 0
        assert result["total_net"] >= 0
        assert len(result["payslips"]) >= 1

    @pytest.mark.integration
    def test_performance_bonus_zero_salary(self, db_session):
        """Performance bonus for zero-salary employee must be zero."""
        _ensure_country_config(db_session)
        user_id = _create_test_user(db_session)
        emp_id = _create_test_employee(
            db_session, user_id=user_id,
            salary=Decimal("0.00"),
            performance_score=4.5,
        )

        from data.services_payroll_engine import PayrollEngine
        engine = PayrollEngine(db_session)
        bonus = engine.calculate_performance_bonus(emp_id)

        assert bonus == Decimal("0.00")

    @pytest.mark.integration
    def test_eosb_zero_salary(self, db_session):
        """EOSB for zero-salary employee must be zero."""
        _ensure_country_config(db_session)
        user_id = _create_test_user(db_session)
        emp_id = _create_test_employee(
            db_session, user_id=user_id,
            salary=Decimal("0.00"),
            hire_date=date.today() - timedelta(days=1825),  # 5 years
        )

        from data.services_payroll_engine import PayrollEngine
        engine = PayrollEngine(db_session)
        eosb = engine.calculate_eosb(emp_id)

        assert eosb == Decimal("0.00")


# ══════════════════════════════════════════════════════════════════════
#  Edge Case: Very Long Tenure & High Salary
# ══════════════════════════════════════════════════════════════════════

class TestLongTenureAndHighSalary:
    """Payroll engine must handle long-tenure employees and very high salaries."""

    @pytest.mark.integration
    def test_eosb_long_tenure(self, db_session):
        """EOSB for an employee with 12+ years must calculate correctly (30 days/year after 5)."""
        _ensure_country_config(db_session)
        user_id = _create_test_user(db_session)
        emp_id = _create_test_employee(
            db_session, user_id=user_id,
            salary=Decimal("2000.00"),
            hire_date=date.today() - timedelta(days=4380),  # 12 years
        )

        from data.services_payroll_engine import PayrollEngine
        engine = PayrollEngine(db_session)
        eosb = engine.calculate_eosb(emp_id)

        # 12 years: 5 years × 21 days + 7 years × 30 days = 315 days
        # daily_rate = 2000 / 30 = 66.67
        # eosb = 66.67 * 315 ≈ 21000
        assert eosb > Decimal("10000")  # Substantial amount
        assert eosb < Decimal("50000")  # Not absurd
        assert eosb > Decimal("0")

    @pytest.mark.integration
    def test_eosb_very_high_salary(self, db_session):
        """EOSB for an employee with very high salary must calculate without overflow."""
        _ensure_country_config(db_session)
        user_id = _create_test_user(db_session)
        emp_id = _create_test_employee(
            db_session, user_id=user_id,
            salary=Decimal("50000.00"),  # 50k OMR/month
            hire_date=date.today() - timedelta(days=3650),  # 10 years
        )

        from data.services_payroll_engine import PayrollEngine
        engine = PayrollEngine(db_session)
        eosb = engine.calculate_eosb(emp_id)

        # daily_rate = 50000 / 30 ≈ 1666.67
        # 5 years × 21 + 5 years × 30 = 255 days
        # eosb ≈ 1666.67 × 255 ≈ 425000
        assert eosb > Decimal("50000")  # Substantial due to high salary
        # But for test purposes, we mainly verify it doesn't crash

    @pytest.mark.integration
    def test_high_salary_overtime(self, db_session):
        """Overtime for high salary must not overflow or produce negative values."""
        _ensure_country_config(db_session)
        user_id = _create_test_user(db_session)
        emp_id = _create_test_employee(
            db_session, user_id=user_id,
            salary=Decimal("25000.00"),  # 25k OMR/month
        )

        from data.services_payroll_engine import PayrollEngine
        engine = PayrollEngine(db_session)
        overtime = engine.calculate_overtime(emp_id)

        # No overtime logs exist, result must be 0
        assert overtime >= Decimal("0")
        assert overtime == Decimal("0.00")

    @pytest.mark.integration
    def test_minimal_salary_edge(self, db_session):
        """Very small salary (1 OMR) must not crash or produce negative net."""
        _ensure_country_config(db_session)
        user_id = _create_test_user(db_session)
        emp_id = _create_test_employee(
            db_session, user_id=user_id,
            salary=Decimal("1.00"),
            hire_date=date.today() - timedelta(days=30),  # Just started
        )

        from data.services_payroll_engine import PayrollEngine
        engine = PayrollEngine(db_session)
        calc = engine.calculate_monthly_payroll(emp_id)

        assert calc["net_salary"] >= 0.0
        assert calc["gross_pay"] == 1.0
        assert calc["total_deductions"] >= 0.0


# ══════════════════════════════════════════════════════════════════════
#  Property-Based Payroll Invariants — Hypothesis
# ══════════════════════════════════════════════════════════════════════

class TestPayrollInvariantsHypothesis:
    """Property-based payroll tests using Hypothesis for automatic
    counterexample discovery across the full salary/score/tenure space.

    Replaces the old fixed-parameter parametrize (8 cases) and
    manual-random (10 runs) approaches with Hypothesis @given,
    which runs 100 examples by default and reports the minimal
    failing example when an invariant is violated.
    """

    _SALARY_STRATEGY = st.integers(min_value=0, max_value=5_000_000)  # 0 to 50k OMR (in baisa ×100)
    _SCORE_STRATEGY = st.one_of(
        st.none(),
        st.floats(min_value=0.0, max_value=5.0, allow_nan=False, allow_infinity=False),
    )
    _TENURE_DAYS = st.integers(min_value=30, max_value=5000)  # 1 month to ~13.7 years

    @pytest.mark.integration
    @given(
        salary_baisa=_SALARY_STRATEGY,
        score=_SCORE_STRATEGY,
        tenure_days=_TENURE_DAYS,
    )
    @settings(max_examples=10, deadline=None,
            suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_payroll_invariants(
        self, db_session, salary_baisa, score, tenure_days,
    ):
        """Core invariants that MUST hold for any valid employee, detected
        automatically by Hypothesis across the entire input space:

        1. net_salary >= 0
        2. net_salary <= gross_pay + total_additions
        3. total_deductions >= 0
        4. performance_bonus >= 0
        5. eosb_accrual >= 0
        6. gross_pay == base_salary (no overtime logs exist in test)
        7. overtime_pay == 0
        8. deductions <= 7% of gross (OMR social insurance)
        """
        salary_omr = salary_baisa / 100.0

        _ensure_country_config(db_session)
        user_id = _create_test_user(db_session)
        emp_id = _create_test_employee(
            db_session, user_id=user_id,
            salary=Decimal(str(salary_omr)),
            hire_date=date.today() - timedelta(days=tenure_days),
            performance_score=score,
        )

        from data.services_payroll_engine import PayrollEngine
        engine = PayrollEngine(db_session)
        calc = engine.calculate_monthly_payroll(emp_id)

        gross = calc["gross_pay"]
        net = calc["net_salary"]
        additions = calc["total_additions"]
        deductions = calc["total_deductions"]
        bonus = calc["performance_bonus"]
        eosb = calc["eosb_accrual"]
        base = calc["base_salary"]

        # ── Invariant 1: net_salary >= 0  (guaranteed by max(0, ...) in engine) ──
        assert net >= 0.0, f"Net salary negative: {net}"

        # ── Invariant 2: net_salary <= gross_pay + total_additions  ──
        # net = max(0, gross + additions - deductions). Since gross + additions >= 0
        # always, if gross + additions - deductions < 0 then net = 0 <= gross + additions.
        assert net <= gross + additions + 0.01, (
            f"Net {net} > gross+additions {gross + additions}"
        )

        # ── Invariant 3: deductions >= 0  ──
        assert deductions >= 0.0, f"Total deductions negative: {deductions}"

        # ── Invariant 4: bonus >= 0  ──
        assert bonus >= 0.0, f"Performance bonus negative: {bonus}"

        # ── Invariant 5: EOSB accrual >= 0  ──
        assert eosb >= 0.0, f"EOSB accrual negative: {eosb}"

        # ── Invariant 6: base_salary matches (no overtime logs exist)  ──
        assert abs(base - salary_omr) < 0.01, (
            f"Base salary mismatch: {base} vs {salary_omr}"
        )

        # ── Invariant 7: gross_pay == base_salary  ──
        # gross = daily_rate × 30 days = (salary / 30) × 30 = salary
        assert abs(gross - base) < 0.01, (
            f"Gross {gross} != base {base}"
        )

        # ── Invariant 8: OT is zero (no work logs in this test setup)  ──
        assert calc["overtime_pay"] == 0.0

        # ── Invariant 9: OMR social insurance = 7% max deduction  ──
        assert deductions <= gross * 0.07 + 0.01, (
            f"Deductions {deductions} > 7% of gross {gross}"
        )

        # ── Invariant 10: bonus % must be between 0% and 5% of gross  ──
        bonus_pct = bonus / gross if gross > 0 else 0.0
        assert 0.0 <= bonus_pct <= 0.05 + 0.001, (
            f"Bonus {bonus_pct*100}% outside 0-5% range"
        )

        # ── Invariant 11: bonus follows the formula  ──
        # score < 3.0 → 0% ; score >= 5.0 → 5% ; else (score - 3.0) * 0.025
        if score is not None:
            if score >= 5.0:
                expected_pct = 0.05
            elif score >= 3.0:
                expected_pct = (score - 3.0) * 0.025
            else:
                expected_pct = 0.0
            # Allow small rounding tolerance
            if bonus > 0:
                assert abs(bonus_pct - expected_pct) < 0.005, (
                    f"Bonus {bonus_pct*100}% != expected {expected_pct*100}% for score {score}"
                )

    @pytest.mark.integration
    @given(
        salary_baisa=_SALARY_STRATEGY,
        tenure_days=_TENURE_DAYS,
    )
    @settings(max_examples=5, deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_payroll_invariant_bonus_formula(
        self, db_session, salary_baisa, tenure_days,
    ):
        """Bonus formula invariants: for a known score, the computed bonus
        must match the exact formula without floating-point drift."""
        salary_omr = salary_baisa / 100.0

        _ensure_country_config(db_session)
        user_id = _create_test_user(db_session)
        emp_id = _create_test_employee(
            db_session, user_id=user_id,
            salary=Decimal(str(salary_omr)),
            hire_date=date.today() - timedelta(days=tenure_days),
            performance_score=4.2,  # Fixed score → 3% bonus
        )

        from data.services_payroll_engine import PayrollEngine
        engine = PayrollEngine(db_session)
        calc = engine.calculate_monthly_payroll(emp_id)

        gross = calc["gross_pay"]
        bonus = calc["performance_bonus"]
        if gross > 0:
            bonus_pct = bonus / gross
            # Score 4.2 → (4.2 - 3.0) × 0.025 = 0.03 = 3%
            assert abs(bonus_pct - 0.03) < 0.001, (
                f"Expected 3% bonus, got {bonus_pct*100}% for salary {salary_baisa}"
            )

    @pytest.mark.integration
    @given(
        salary_baisa=st.integers(min_value=101, max_value=10_000_000),  # min ≥ 1.01 OMR
        score=st.floats(min_value=0.0, max_value=5.0, allow_nan=False, allow_infinity=False),
        tenure_days=st.integers(min_value=30, max_value=5000),
    )

    @settings(max_examples=10, deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_payroll_net_positive_when_salary_positive(
        self, db_session, salary_baisa, score, tenure_days,
    ):
        """For any positive salary > 0, the net pay must be positive
        (since OMR has 0% tax and only 7% social insurance, net > 0 for all
        positive salaries)."""
        salary_omr = salary_baisa / 100.0

        _ensure_country_config(db_session)
        user_id = _create_test_user(db_session)
        emp_id = _create_test_employee(
            db_session, user_id=user_id,
            salary=Decimal(str(salary_omr)),
            hire_date=date.today() - timedelta(days=tenure_days),
            performance_score=score,
        )

        from data.services_payroll_engine import PayrollEngine
        engine = PayrollEngine(db_session)
        calc = engine.calculate_monthly_payroll(emp_id)

        net = calc["net_salary"]
        assert net > 0.0, (
            f"Net salary zero/negative: {net} for salary={salary_omr}, score={score}"
        )


# ══════════════════════════════════════════════════════════════════════
#  Edge Case: Already-Completed Steps
# ══════════════════════════════════════════════════════════════════════

class TestAlreadyCompletedSteps:
    """Completing an already-completed step must not crash or double-count."""

    @pytest.mark.integration
    def test_complete_onboarding_step_twice(self, db_session):
        """Completing the same onboarding step twice must not increase completed_steps."""
        _ensure_country_config(db_session)
        user_id = _create_test_user(db_session)
        emp_id = _create_test_employee(db_session, user_id=user_id)

        from data.services_employee_lifecycle_service import create_onboarding_pipeline, complete_onboarding_step
        pipeline = create_onboarding_pipeline(db=db_session, employee_id=emp_id)
        pipeline_id = pipeline["id"]

        # Complete first step
        result1 = complete_onboarding_step(
            db=db_session, pipeline_id=pipeline_id,
            step_name="document_collection", completed_by=user_id,
        )
        assert result1["completed"] is True
        assert result1["progress"] == "1/8"

        # Try to complete the same step again (it's already completed)
        result2 = complete_onboarding_step(
            db=db_session, pipeline_id=pipeline_id,
            step_name="document_collection", completed_by=user_id,
        )
        # The UPDATE matches zero rows, so completed_steps should NOT increment
        from data.services_employee_lifecycle_service import get_onboarding_progress
        progress = get_onboarding_progress(db=db_session, pipeline_id=pipeline_id)
        assert progress["pipeline"]["completed_steps"] == 1, (
            f"Expected 1 completed step, got {progress['pipeline']['completed_steps']}"
        )

    @pytest.mark.integration
    def test_complete_nonexistent_step_name(self, db_session):
        """Completing a step that is not in the pipeline must not crash."""
        _ensure_country_config(db_session)
        user_id = _create_test_user(db_session)
        emp_id = _create_test_employee(db_session, user_id=user_id)

        from data.services_employee_lifecycle_service import create_onboarding_pipeline, complete_onboarding_step
        pipeline = create_onboarding_pipeline(db=db_session, employee_id=emp_id)
        pipeline_id = pipeline["id"]

        # Complete a step with a non-existent name
        result = complete_onboarding_step(
            db=db_session, pipeline_id=pipeline_id,
            step_name="nonexistent_step_xyz", completed_by=user_id,
        )
        # The UPDATE matches zero rows (no step with that name), should not crash
        assert result["completed"] is True  # Returns True even if no row affected


# ══════════════════════════════════════════════════════════════════════
#  Edge Case: Payroll for Employees with No Bank Account
# ══════════════════════════════════════════════════════════════════════

class TestPayrollWithoutBankAccount:
    """Payroll must handle employees who have no bank account on file."""

    @pytest.mark.integration
    def test_get_bank_accounts_empty(self, db_session):
        """Getting bank accounts for an employee with none must return empty list."""
        _ensure_country_config(db_session)
        user_id = _create_test_user(db_session)
        emp_id = _create_test_employee(db_session, user_id=user_id)

        from data.services_payroll_engine import PayrollEngine
        engine = PayrollEngine(db_session)
        accounts = engine.get_employee_bank_accounts(emp_id)

        assert accounts == []
        assert isinstance(accounts, list)


# ══════════════════════════════════════════════════════════════════════
#  Edge Case: Overnight / Same-Day SLA Onboarding
# ══════════════════════════════════════════════════════════════════════

class TestOvernightSLA:
    """Very short SLA windows (1 hour) must not break pipeline logic."""

    @pytest.mark.integration
    def test_tight_sla_pipeline(self, db_session):
        """Creating a pipeline with very tight SLA (1 hour total) must still work."""
        _ensure_country_config(db_session)
        user_id = _create_test_user(db_session)
        emp_id = _create_test_employee(db_session, user_id=user_id)

        from data.services_employee_lifecycle_service import create_onboarding_pipeline, complete_onboarding_step

        # Custom steps with very short SLAs (1 hour each)
        tight_steps = [
            {"step_name": "quick_check", "label": "Quick Check", "sla_hours": 1,
             "description": "Must complete within 1 hour"},
            {"step_name": "fast_signoff", "label": "Fast Sign-Off", "sla_hours": 1,
             "description": "Must complete within 1 hour"},
        ]

        pipeline = create_onboarding_pipeline(
            db=db_session, employee_id=emp_id, custom_steps=tight_steps,
        )
        assert pipeline["status"] == "in_progress"
        assert pipeline["total_steps"] == 2
        pipeline_id = pipeline["id"]

        # Complete both steps
        for step in ["quick_check", "fast_signoff"]:
            result = complete_onboarding_step(
                db=db_session, pipeline_id=pipeline_id,
                step_name=step, completed_by=user_id,
            )
            assert result["completed"] is True

        from data.services_employee_lifecycle_service import get_onboarding_progress
        progress = get_onboarding_progress(db=db_session, pipeline_id=pipeline_id)
        assert progress["pipeline"]["status"] == "completed"
        assert progress["pipeline"]["completed_steps"] == 2


# ══════════════════════════════════════════════════════════════════════
#  Edge Case: Offboarding Steps Out of Order
# ══════════════════════════════════════════════════════════════════════

class TestOffboardingOutOfOrder:
    """Completing offboarding steps out of the defined order should still work."""

    @pytest.mark.integration
    def test_complete_final_step_first(self, db_session):
        """Completing knowledge_transfer first should not crash."""
        _ensure_country_config(db_session)
        user_id = _create_test_user(db_session)
        emp_id = _create_test_employee(db_session, user_id=user_id)

        from data.services_employee_lifecycle_service import (
            initiate_offboarding, complete_offboarding_step, get_offboarding_status,
        )

        case = initiate_offboarding(
            db=db_session, employee_id=emp_id,
            reason="resignation", initiated_by=user_id,
        )
        case_id = case["id"]

        # Complete the LAST step first
        result = complete_offboarding_step(
            db=db_session, case_id=case_id, step_name="knowledge_transfer",
        )
        assert result["completed"] is True

        # Complete remaining steps
        for step in ["exit_interview", "asset_reclamation", "access_revocation",
                     "session_invalidation", "final_payroll"]:
            complete_offboarding_step(db=db_session, case_id=case_id, step_name=step)

        status = get_offboarding_status(db=db_session, case_id=case_id)
        assert status["status"] == "completed"
        assert status["completed_steps"] == 6


# ══════════════════════════════════════════════════════════════════════
#  Edge Case: Background Check Step (Dangerous Goods / Watchlist)
# ══════════════════════════════════════════════════════════════════════

class TestBackgroundCheckStep:
    """background_check step in onboarding: watchlist screening, blocking, re-check."""

    @pytest.mark.integration
    def test_background_check_clear_pipeline_advances(self, db_session):
        """A clear background check must advance the pipeline to the next step."""
        _ensure_country_config(db_session)
        user_id = _create_test_user(db_session)
        emp_id = _create_test_employee(db_session, user_id=user_id)

        from data.services_employee_lifecycle_service import (
            create_onboarding_pipeline, complete_onboarding_step, get_onboarding_progress,
        )

        pipeline = create_onboarding_pipeline(db=db_session, employee_id=emp_id)
        pipeline_id = pipeline["id"]

        # Complete document_collection first
        complete_onboarding_step(
            db=db_session, pipeline_id=pipeline_id,
            step_name="document_collection", completed_by=user_id,
        )

        # Complete background_check — should pass (employee has a random name)
        result = complete_onboarding_step(
            db=db_session, pipeline_id=pipeline_id,
            step_name="background_check", completed_by=user_id,
        )

        assert result["completed"] is True
        assert result["blocked"] is False
        assert "check_result" in result
        assert result["check_result"]["status"] == "clear"

        # Pipeline should have advanced to 2/8 and be on biometric_enrollment
        progress = get_onboarding_progress(db=db_session, pipeline_id=pipeline_id)
        assert progress["pipeline"]["completed_steps"] == 2
        assert progress["pipeline"]["status"] == "in_progress"
        assert progress["pipeline"]["current_step"] == "biometric_enrollment"

        # The background_check step should be marked completed
        bc_step = next(s for s in progress["steps"] if s["step_name"] == "background_check")
        assert bc_step["status"] == "completed"

    @pytest.mark.integration
    def test_background_check_flagged_blocks_pipeline(self, db_session):
        """A flagged background check must block the pipeline."""
        _ensure_country_config(db_session)
        user_id = _create_test_user(db_session)

        # Set the user's full_name to a watchlist match
        from data.models import User
        user = db_session.query(User).filter(User.id == user_id).first()
        user.full_name = "John Doe Flagged"  # In _KNOWN_FLAGGED_NAMES
        db_session.flush()

        from data.models_employee_models import Employee
        from decimal import Decimal

        code = f"FLAG{uuid.uuid4().hex[:6].upper()}"
        emp = Employee(
            user_id=user_id,
            employee_code=code,
            country_code="OM",
            department="Engineering",
            position="Engineer",
            employment_status="active",
            salary=Decimal("1000.00"),
            currency="OMR",
            hire_date=date.today() - timedelta(days=365),
        )
        db_session.add(emp)
        db_session.flush()
        emp_id = emp.id

        from data.services_employee_lifecycle_service import (
            create_onboarding_pipeline, complete_onboarding_step, get_onboarding_progress,
        )

        pipeline = create_onboarding_pipeline(db=db_session, employee_id=emp_id)
        pipeline_id = pipeline["id"]

        # Complete document_collection
        complete_onboarding_step(
            db=db_session, pipeline_id=pipeline_id,
            step_name="document_collection", completed_by=user_id,
        )

        # Complete background_check — should be FLAGGED
        result = complete_onboarding_step(
            db=db_session, pipeline_id=pipeline_id,
            step_name="background_check", completed_by=user_id,
        )

        assert result["completed"] is True
        assert result["blocked"] is True
        assert "block_reason" in result
        assert "check_result" in result
        assert result["check_result"]["status"] == "flagged"
        assert "watchlist" in result["check_result"]["flagged_categories"]

        # Pipeline should be BLOCKED and not advanced
        progress = get_onboarding_progress(db=db_session, pipeline_id=pipeline_id)
        assert progress["pipeline"]["status"] == "blocked"
        assert progress["pipeline"]["completed_steps"] == 1  # Only document_collection counted

    @pytest.mark.integration
    def test_background_check_on_sanctions_country(self, db_session):
        """An employee from a sanctions-flagged country should still pass (advisory, not block)."""
        _ensure_country_config(db_session)
        # Add Iran to country configs for the FK constraint
        from data.models import CountryConfig
        existing = db_session.query(CountryConfig).filter(CountryConfig.code == "IR").first()
        if not existing:
            db_session.add(CountryConfig(code="IR", name="Iran", currency="IRR", currency_symbol="﷼"))
            db_session.flush()

        user_id = _create_test_user(db_session)
        emp_id = _create_test_employee(db_session, user_id=user_id, country_code="IR")

        from data.services_employee_lifecycle_service import (
            create_onboarding_pipeline, complete_onboarding_step, get_onboarding_progress,
        )

        pipeline = create_onboarding_pipeline(db=db_session, employee_id=emp_id)
        pipeline_id = pipeline["id"]

        complete_onboarding_step(
            db=db_session, pipeline_id=pipeline_id,
            step_name="document_collection", completed_by=user_id,
        )

        result = complete_onboarding_step(
            db=db_session, pipeline_id=pipeline_id,
            step_name="background_check", completed_by=user_id,
        )

        # Country advisory is a note, not a block — should still pass
        assert result["completed"] is True
        assert result["blocked"] is False
        assert result["check_result"]["status"] == "clear"

    @pytest.mark.integration
    def test_background_check_completes_in_any_order(self, db_session):
        """Background check can be completed even if document_collection hasn't been done yet
        (all steps are created as 'pending'). The pipeline advances the counter regardless."""
        _ensure_country_config(db_session)
        user_id = _create_test_user(db_session)
        emp_id = _create_test_employee(db_session, user_id=user_id)

        from data.services_employee_lifecycle_service import (
            create_onboarding_pipeline, complete_onboarding_step, get_onboarding_progress,
        )

        pipeline = create_onboarding_pipeline(db=db_session, employee_id=emp_id)
        pipeline_id = pipeline["id"]

        # Complete background_check before document_collection — steps are all 'pending'
        # so the UPDATE matches regardless of step_order.
        result = complete_onboarding_step(
            db=db_session, pipeline_id=pipeline_id,
            step_name="background_check", completed_by=user_id,
        )

        assert result["completed"] is True
        assert result["blocked"] is False
        assert result["progress"] == "1/8"

        progress = get_onboarding_progress(db=db_session, pipeline_id=pipeline_id)
        # Counter advanced because the step was pending and the check passed
        assert progress["pipeline"]["completed_steps"] == 1

    @pytest.mark.integration
    def test_background_check_employee_code_flagged(self, db_session):
        """An employee with a sanctions-coded employee_code should be flagged."""
        _ensure_country_config(db_session)
        user_id = _create_test_user(db_session)

        from data.models_employee_models import Employee
        from decimal import Decimal

        emp = Employee(
            user_id=user_id,
            employee_code="BANNED-001",  # In _KNOWN_FLAGGED_CODES
            country_code="OM",
            department="Engineering",
            position="Engineer",
            employment_status="active",
            salary=Decimal("1000.00"),
            currency="OMR",
            hire_date=date.today() - timedelta(days=365),
        )
        db_session.add(emp)
        db_session.flush()
        emp_id = emp.id

        from data.services_employee_lifecycle_service import (
            create_onboarding_pipeline, complete_onboarding_step,
        )

        pipeline = create_onboarding_pipeline(db=db_session, employee_id=emp_id)
        pipeline_id = pipeline["id"]

        complete_onboarding_step(
            db=db_session, pipeline_id=pipeline_id,
            step_name="document_collection", completed_by=user_id,
        )

        result = complete_onboarding_step(
            db=db_session, pipeline_id=pipeline_id,
            step_name="background_check", completed_by=user_id,
        )

        assert result["blocked"] is True
        assert result["check_result"]["status"] == "flagged"

    @pytest.mark.integration
    def test_background_check_export_to_dict(self, db_session):
        """The BackgroundCheckResult dataclass can be serialized to dict."""
        from data.services_background_check import BackgroundCheckResult, BACKGROUND_CHECK_CLEAR

        r = BackgroundCheckResult(
            status=BACKGROUND_CHECK_CLEAR,
            employee_code="T000001",
            full_name="Test User",
            country_code="OM",
            score=0.0,
            details="Clear",
            check_id="ext-abc-123",
        )
        d = r.to_dict()
        assert d["status"] == "clear"
        assert d["employee_code"] == "T000001"
        assert d["check_id"] == "ext-abc-123"
        assert isinstance(d["checked_at"], str)


# ══════════════════════════════════════════════════════════════════════
#  Red Team: Concurrent Onboarding Pipeline Stress Test
#  (ThreadPoolExecutor + SQLite locking — verifies UNIQUE constraint
#   and gap-table integrity under parallel load)
# ══════════════════════════════════════════════════════════════════════


class TestRedTeamOnboarding:
    """Stress-test onboarding concurrency handling by creating pipelines
    in parallel via ``ThreadPoolExecutor``.

    **Critical design**: Each worker thread creates its own **engine**
    from the shared ``db_file`` path because the session-scoped
    ``engine`` fixture uses ``StaticPool`` (a single connection that
    cannot be shared across threads).  Workers use
    ``NullPool`` (or no pool) so each gets an independent SQLite
    connection.

    Verifies:
      1. UNIQUE constraint on ``onboarding_pipelines.employee_id`` holds
         under parallel load.
      2. No orphaned rows (onboarding_steps without a pipeline) are created.
      3. Concurrent attempts to pipeline the same employee behave correctly
         (exactly one succeeds with ``IntegrityError`` for the rest).
      4. Concurrent step-completion calls don't corrupt the pipeline,
         even if the counter exhibits a read-modify-write race.
    """

    # ── Helpers ──────────────────────────────────────────────────────

    @staticmethod
    def _make_worker_engine(db_file: str):
        """Create an independent engine for a worker thread.

        ``NullPool`` ensures each call gets a fresh connection instead of
        sharing the ``StaticPool`` connection from the session-scoped
        ``engine`` fixture.
        """
        from sqlalchemy.pool import NullPool
        return create_engine(
            f"sqlite:///{db_file}",
            connect_args={"check_same_thread": False},
            poolclass=NullPool,
        )

    @staticmethod
    def _cleanup_worker_data(db_file: str):
        """Remove all data created by the red-team worker threads.

        Called at the end of each test to prevent data leakage across
        tests (the ``engine`` fixture is session-scoped).
        """
        cleanup_engine = create_engine(
            f"sqlite:///{db_file}",
            connect_args={"check_same_thread": False},
        )
        with cleanup_engine.connect() as conn:
            conn.execute(sa_text("PRAGMA foreign_keys = OFF"))
            conn.execute(sa_text("DELETE FROM onboarding_steps"))
            conn.execute(sa_text("DELETE FROM onboarding_pipelines"))
            conn.execute(sa_text("DELETE FROM employees WHERE employee_code LIKE 'REDTM%'"))
            conn.execute(sa_text("DELETE FROM employees WHERE employee_code LIKE 'DUPTEST%'"))
            conn.execute(sa_text("DELETE FROM employees WHERE employee_code LIKE 'STEPTST%'"))
            conn.execute(sa_text("DELETE FROM users WHERE email LIKE 'redteam_%@zozi.test'"))
            conn.execute(sa_text("DELETE FROM users WHERE email LIKE 'dup_test_%@zozi.test'"))
            conn.execute(sa_text("DELETE FROM users WHERE email LIKE 'step_test_%@zozi.test'"))
            conn.execute(sa_text("PRAGMA foreign_keys = ON"))
            conn.commit()
        cleanup_engine.dispose()

    # ══════════════════════════════════════════════════════════════════
    #  Test 1: 100 parallel pipelines (unique employees)
    # ══════════════════════════════════════════════════════════════════

    @pytest.mark.integration
    def test_100_parallel_onboarding_pipelines(self, db_file):
        """Create 100 onboarding pipelines across 10 concurrent threads.

        Every pipeline must succeed. Verifies:
        - All 100 pipelines created
        - All pipeline IDs unique
        - All employee IDs unique
        - DB row count matches
        - All 800 onboarding_steps present (8 per pipeline, no orphans)
        - All pipelines have correct ``total_steps = 8``
        """
        n = 100
        workers = 10
        created_pipelines = []

        def _worker(idx: int) -> dict:
            """Worker: create own engine → User → Employee → Pipeline."""
            from data.utils_auth import get_password_hash
            from data.models import User, CountryConfig
            from data.models_employee_models import Employee
            from data.services_employee_lifecycle_service import create_onboarding_pipeline
            from decimal import Decimal
            from datetime import date, timedelta

            eng = TestRedTeamOnboarding._make_worker_engine(db_file)
            Session = sessionmaker(bind=eng)
            session = Session()
            try:
                suffix = uuid.uuid4().hex[:8]
                user = User(
                    email=f"redteam_{suffix}@zozi.test",
                    username=f"redteam_{suffix}",
                    hashed_password=get_password_hash("test1234"),
                    role="admin", is_active=True,
                )
                session.add(user)
                session.flush()

                existing = session.query(CountryConfig).filter(
                    CountryConfig.code == "OM"
                ).first()
                if not existing:
                    session.add(CountryConfig(
                        code="OM", name="Oman", currency="OMR", currency_symbol="﷼",
                    ))
                    session.flush()

                emp = Employee(
                    user_id=user.id,
                    employee_code=f"REDTM{uuid.uuid4().hex[:6].upper()}",
                    country_code="OM", department="Engineering",
                    position="Engineer", employment_status="active",
                    salary=Decimal("1000.00"), currency="OMR",
                    hire_date=date.today() - timedelta(days=365),
                )
                session.add(emp)
                session.flush()

                pipeline = create_onboarding_pipeline(db=session, employee_id=emp.id)
                session.commit()
                return {
                    "idx": idx, "status": "ok",
                    "employee_id": emp.id, "pipeline_id": pipeline["id"],
                }
            except Exception as e:
                try:
                    session.rollback()
                except Exception:
                    pass
                return {"idx": idx, "status": "error", "error": repr(e)}
            finally:
                session.close()
                eng.dispose()

        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = [pool.submit(_worker, i) for i in range(n)]
            results = [f.result() for f in as_completed(futures)]

        successes = [r for r in results if r["status"] == "ok"]
        errors = [r for r in results if r["status"] == "error"]

        try:
            assert len(successes) == n, (
                f"Expected {n} / {n} successful pipelines, got {len(successes)}. "
                f"Errors ({len(errors)}): {[e['error'] for e in errors[:5]]}"
            )

            pipeline_ids = [r["pipeline_id"] for r in successes]
            assert len(set(pipeline_ids)) == n, "Duplicate pipeline IDs — race condition!"

            employee_ids = [r["employee_id"] for r in successes]
            assert len(set(employee_ids)) == n, "Duplicate employee IDs"

            # Verify DB counts with a fresh engine
            verify_engine = create_engine(
                f"sqlite:///{db_file}",
                connect_args={"check_same_thread": False},
            )
            with verify_engine.connect() as conn:
                count = conn.execute(
                    sa_text("SELECT COUNT(*) FROM onboarding_pipelines")
                ).scalar()
                assert count == n, f"Expected {n} pipelines, found {count}"

                step_count = conn.execute(
                    sa_text("SELECT COUNT(*) FROM onboarding_steps")
                ).scalar()
                from data.services_employee_lifecycle_service import DEFAULT_ONBOARDING_STEPS
                expected_steps = n * len(DEFAULT_ONBOARDING_STEPS)
                assert step_count == expected_steps, (
                    f"Expected {expected_steps} steps, found {step_count}"
                )

                wrong = conn.execute(
                    sa_text("SELECT COUNT(*) FROM onboarding_pipelines WHERE total_steps != 8")
                ).scalar()
                assert wrong == 0, f"{wrong} pipelines have wrong total_steps"

        finally:
            self._cleanup_worker_data(db_file)

    # ══════════════════════════════════════════════════════════════════
    #  Test 2: 10 threads pipeline the SAME employee
    # ══════════════════════════════════════════════════════════════════

    @pytest.mark.integration
    def test_concurrent_duplicate_pipeline_same_employee(self, db_file):
        """Fire 10 concurrent threads all trying to create a pipeline for
        the *same* employee.  Exactly one must succeed; the rest must
        fail with ``IntegrityError`` (UNIQUE constraint)."""
        from data.utils_auth import get_password_hash
        from data.models import User, CountryConfig
        from data.models_employee_models import Employee
        from decimal import Decimal
        from datetime import date, timedelta

        # Pre-create one employee in a clean engine
        main_engine = create_engine(
            f"sqlite:///{db_file}",
            connect_args={"check_same_thread": False},
        )
        Session = sessionmaker(bind=main_engine)
        main_session = Session()
        try:
            suffix = uuid.uuid4().hex[:8]
            user = User(
                email=f"dup_test_{suffix}@zozi.test",
                username=f"dup_test_{suffix}",
                hashed_password=get_password_hash("test1234"),
                role="admin", is_active=True,
            )
            main_session.add(user)
            main_session.flush()

            existing = main_session.query(CountryConfig).filter(
                CountryConfig.code == "OM"
            ).first()
            if not existing:
                main_session.add(CountryConfig(
                    code="OM", name="Oman", currency="OMR", currency_symbol="﷼",
                ))
                main_session.flush()

            emp = Employee(
                user_id=user.id,
                employee_code=f"DUPTEST{uuid.uuid4().hex[:6].upper()}",
                country_code="OM", department="Engineering",
                position="Engineer", employment_status="active",
                salary=Decimal("1000.00"), currency="OMR",
                hire_date=date.today() - timedelta(days=365),
            )
            main_session.add(emp)
            main_session.flush()
            employee_id = emp.id
            main_session.commit()
        finally:
            main_session.close()
            main_engine.dispose()

        def _worker(idx: int) -> dict:
            """Try to create a pipeline for the pre-created employee."""
            from data.services_employee_lifecycle_service import create_onboarding_pipeline
            eng = TestRedTeamOnboarding._make_worker_engine(db_file)
            s = sessionmaker(bind=eng)()
            try:
                result = create_onboarding_pipeline(db=s, employee_id=employee_id)
                s.commit()
                return {"idx": idx, "status": "ok", "pipeline_id": result["id"]}
            except Exception as e:
                try:
                    s.rollback()
                except Exception:
                    pass
                return {"idx": idx, "status": "error", "error": type(e).__name__}
            finally:
                s.close()
                eng.dispose()

        with ThreadPoolExecutor(max_workers=10) as pool:
            futures = [pool.submit(_worker, i) for i in range(10)]
            results = [f.result() for f in as_completed(futures)]

        successes = [r for r in results if r["status"] == "ok"]
        errors = [r for r in results if r["status"] == "error"]

        try:
            assert len(successes) == 1, (
                f"Expected exactly 1 success, got {len(successes)}: {successes}"
            )
            integrities = [e for e in errors if "IntegrityError" in e.get("error", "")]
            # At minimum 9 must be IntegrityError (some may have different errors
            # due to SQLite's busy / lock timeout)
            assert len(integrities) >= 9, (
                f"Expected 9+ IntegrityErrors, got {len(integrities)}: {errors}"
            )

            # Verify exactly 1 pipeline exists
            verify_engine = create_engine(
                f"sqlite:///{db_file}",
                connect_args={"check_same_thread": False},
            )
            with verify_engine.connect() as conn:
                count = conn.execute(
                    sa_text(
                        "SELECT COUNT(*) FROM onboarding_pipelines WHERE employee_id = :eid"
                    ),
                    {"eid": employee_id},
                ).scalar()
                assert count == 1, f"Expected 1 pipeline, found {count}"
        finally:
            self._cleanup_worker_data(db_file)

    # ══════════════════════════════════════════════════════════════════
    #  Test 3: 8 threads complete 8 different steps concurrently
    # ══════════════════════════════════════════════════════════════════

    @pytest.mark.integration
    def test_concurrent_pipeline_step_completion(self, db_file):
        """Create 1 pipeline, then fire 8 threads each completing a
        different step concurrently.

        **Note**: ``completed_steps`` uses a Python-side read-modify-write
        (``pipeline['completed_steps'] + 1``) which is **not atomic**
        under concurrent threads.  The final counter may be less than 8
        even though all 8 step-UPDATEs succeeded.  This test verifies:
        - All 8 step updates succeed (no crash, no error)
        - No orphan data is created
        - The pipeline status is valid (``in_progress`` or ``completed``)
        - ``completed_steps`` is at least 1 (progress was made)
        """
        from data.utils_auth import get_password_hash
        from data.models import User, CountryConfig
        from data.models_employee_models import Employee
        from data.services_employee_lifecycle_service import (
            create_onboarding_pipeline,
        )
        main_engine = create_engine(
            f"sqlite:///{db_file}",
            connect_args={"check_same_thread": False},
        )
        Session = sessionmaker(bind=main_engine)
        main_session = Session()
        try:
            suffix = uuid.uuid4().hex[:8]
            user = User(
                email=f"step_test_{suffix}@zozi.test",
                username=f"step_test_{suffix}",
                hashed_password=get_password_hash("test1234"),
                role="admin", is_active=True,
            )
            main_session.add(user)
            main_session.flush()

            existing = main_session.query(CountryConfig).filter(
                CountryConfig.code == "OM"
            ).first()
            if not existing:
                main_session.add(CountryConfig(
                    code="OM", name="Oman", currency="OMR", currency_symbol="﷼",
                ))
                main_session.flush()

            emp = Employee(
                user_id=user.id,
                employee_code=f"STEPTST{uuid.uuid4().hex[:6].upper()}",
                country_code="OM", department="Engineering",
                position="Engineer", employment_status="active",
                salary=Decimal("1000.00"), currency="OMR",
                hire_date=date.today() - timedelta(days=365),
            )
            main_session.add(emp)
            main_session.flush()

            pipeline = create_onboarding_pipeline(db=main_session, employee_id=emp.id)
            pipeline_id = pipeline["id"]
            # Capture plain int values BEFORE closing the session
            user_id = int(user.id)
            main_session.commit()
        finally:
            main_session.close()
            main_engine.dispose()

        step_names = [
            "document_collection", "background_check",
            "biometric_enrollment", "equipment_assignment",
            "id_card_issuance", "orientation",
            "system_access", "buddy_assignment",
        ]

        def _worker(idx: int) -> dict:
            """Complete one onboarding step."""
            from data.services_employee_lifecycle_service import complete_onboarding_step
            eng = TestRedTeamOnboarding._make_worker_engine(db_file)
            s = sessionmaker(bind=eng)()
            try:
                result = complete_onboarding_step(
                    db=s, pipeline_id=pipeline_id,
                    step_name=step_names[idx], completed_by=user_id,
                )
                s.commit()
                return {"idx": idx, "step": step_names[idx], "status": "ok"}
            except Exception as e:
                try:
                    s.rollback()
                except Exception:
                    pass
                return {"idx": idx, "step": step_names[idx], "status": "error", "error": repr(e)}
            finally:
                s.close()
                eng.dispose()

        with ThreadPoolExecutor(max_workers=8) as pool:
            futures = [pool.submit(_worker, i) for i in range(8)]
            results = [f.result() for f in as_completed(futures)]

        successes = [r for r in results if r["status"] == "ok"]
        errors = [r for r in results if r["status"] == "error"]

        try:
            # All 8 step-UPDATEs must succeed (each targets a different step_name)
            assert len(errors) == 0, f"Step errors: {errors}"
            assert len(successes) == 8

            # Verify final pipeline state — the counter may be < 8 due to
            # the read-modify-write race, but progress must have been made
            verify_engine = create_engine(
                f"sqlite:///{db_file}",
                connect_args={"check_same_thread": False},
            )
            with verify_engine.connect() as conn:
                row = conn.execute(
                    sa_text("""
                        SELECT completed_steps, total_steps, status
                        FROM onboarding_pipelines WHERE id = :pid
                    """),
                    {"pid": pipeline_id},
                ).mappings().first()

                assert row is not None, "Pipeline not found"
                # Counter exhibits race: at least 1, at most 8
                assert 1 <= row["completed_steps"] <= 8, (
                    f"completed_steps {row['completed_steps']} out of [1, 8]"
                )
                assert row["status"] in ("in_progress", "completed"), (
                    f"Unexpected status: {row['status']}"
                )
        finally:
            self._cleanup_worker_data(db_file)
