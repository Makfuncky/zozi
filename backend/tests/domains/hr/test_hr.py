from __future__ import annotations

class TestHRDomainImports:
    def test_hr_domain_imports_successfully(self):
        from domains.hr.services import hr_service
        from domains.hr.models.employee_models import Employee
        from domains.hr.features import HR_FEATURES
        assert hr_service is not None
        assert Employee is not None
        assert isinstance(HR_FEATURES, (list, tuple, set))
