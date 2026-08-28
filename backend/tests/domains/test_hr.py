"""Domain tests for HR — employee operations, payroll, and compliance."""
from __future__ import annotations

import pytest


class TestHRServiceImports:
    """Smoke tests: verify HR service modules are importable."""

    def test_import_employee_service(self):
        from domains.hr.services.employees import employee_service

        assert employee_service is not None

    def test_import_payroll_service(self):
        from domains.hr.services.payroll import payroll_service

        assert payroll_service is not None

    def test_import_hr_employee_service(self):
        from domains.hr.services import hr_employee_service

        assert hr_employee_service is not None

    def test_import_hr_models(self):
        from domains.hr.models.employee_models import Employee, Office, PayrollRecord

        assert Employee is not None
        assert Office is not None
        assert PayrollRecord is not None

    def test_import_hr_events(self):
        from domains.hr.events import EmployeeCreatedEvent

        assert EmployeeCreatedEvent is not None

    def test_import_hr_ports(self):
        from domains.hr.ports import get_employee_by_id

        assert callable(get_employee_by_id)

    def test_import_hr_features(self):
        from domains.hr.features import HR_FEATURES

        assert isinstance(HR_FEATURES, (list, tuple, set))


class TestEmployeeOperations:
    """Tests for employee service operations."""

    def test_employee_service_class(self):
        from domains.hr.services.employees.employee_service import EmployeeService

        assert EmployeeService is not None
        assert hasattr(EmployeeService, "list_offices")

    def test_employee_service_init(self, db_session):
        from domains.hr.services.employees.employee_service import EmployeeService

        service = EmployeeService(db=db_session)
        assert service.db is db_session

    def test_employee_model_fields(self, db_session):
        from domains.hr.models.employee_models import Employee

        employee = Employee(
            first_name="John",
            last_name="Doe",
            email="john.doe@zozi.com",
            employee_id="EMP-001",
        )
        db_session.add(employee)
        db_session.flush()

        assert employee.id is not None
        assert employee.first_name == "John"
        assert employee.last_name == "Doe"
        assert employee.employee_id == "EMP-001"

    def test_office_model_fields(self, db_session):
        from domains.hr.models.employee_models import Office

        office = Office(
            name="Main Office",
            city="Dubai",
            country_code="AE",
        )
        db_session.add(office)
        db_session.flush()

        assert office.id is not None
        assert office.name == "Main Office"
        assert office.country_code == "AE"


class TestPayrollOperations:
    """Tests for payroll service operations."""

    def test_payroll_service_has_engine(self):
        from domains.hr.services.payroll.payroll_engine import PayrollEngine

        assert PayrollEngine is not None

    def test_payroll_service_has_calculate(self):
        from domains.hr.services.payroll.payroll_service import calculate_payroll

        assert callable(calculate_payroll)

    def test_payroll_record_model_fields(self, db_session):
        from domains.hr.models.employee_models import PayrollRecord

        record = PayrollRecord(
            employee_id=1,
            period_start="2026-01-01",
            period_end="2026-01-31",
            gross_amount=5000.00,
            net_amount=4500.00,
            currency="USD",
        )
        db_session.add(record)
        db_session.flush()

        assert record.id is not None
        assert record.employee_id == 1
        assert record.gross_amount == 5000.00

    def test_payroll_wrapper_exists(self):
        from domains.hr.services.payroll_wrapper import PayrollWrapper

        assert PayrollWrapper is not None
