from __future__ import annotations


class TestCustomersDomainImports:
    def test_customers_domain_imports_successfully(self):
        from domains.customers.services import customer_service
        from domains.customers.models.customer_schema_models import (
            Referral,
            ReferralPointEvent,
        )
        from domains.customers.features import FEATURES

        assert customer_service is not None
        assert Referral is not None
        assert ReferralPointEvent is not None
        assert isinstance(FEATURES, dict)
        assert len(FEATURES) > 0


class TestCustomerServiceBehavior:
    def test_customer_service_has_required_functions(self):
        from domains.customers.services.core.customer_service import CustomerService
        assert callable(CustomerService)
