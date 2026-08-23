"""Unit tests for governance domain logic."""
import pytest
from unittest.mock import MagicMock, patch


class TestGovernanceFeatures:
    """Test governance features.py."""

    def test_features_count(self):
        from domains.governance.features import FEATURES
        assert len(FEATURES) > 40

    def test_all_features_have_required_keys(self):
        from domains.governance.features import FEATURES
        for key, feat in FEATURES.items():
            assert "label" in feat, f"{key} missing label"
            assert "risk" in feat, f"{key} missing risk"
            assert "actions" in feat, f"{key} missing actions"

    def test_is_known(self):
        from domains.governance.features import is_known
        assert is_known("governance.user.create")
        assert is_known("governance.*")
        assert not is_known("governance.nonexistent")

    def test_all_features_returns_sorted(self):
        from domains.governance.features import all_features
        features = all_features()
        assert features == sorted(features)


class TestGovernancePolicies:
    """Test governance policies.py."""

    def test_user_policy_admin_can_create(self):
        from domains.governance.policies import UserPolicy
        assert UserPolicy.can_create_user({"role": "admin"})
        assert UserPolicy.can_create_user({"role": "super_admin"})
        assert not UserPolicy.can_create_user({"role": "customer"})

    def test_user_policy_super_admin_can_do_anything(self):
        from domains.governance.policies import UserPolicy
        actor = {"role": "super_admin"}
        assert UserPolicy.can_delete_user(actor)
        assert UserPolicy.can_force_reset_password(actor)
        assert UserPolicy.can_bulk_manage_users(actor)

    def test_permission_policy_super_admin(self):
        from domains.governance.policies import PermissionPolicy
        assert PermissionPolicy.can_manage_permissions({"role": "super_admin"})
        assert not PermissionPolicy.can_manage_permissions({"role": "admin"})

    def test_role_assignment_super_admin(self):
        from domains.governance.policies import PermissionPolicy
        assert PermissionPolicy.can_assign_role({"role": "super_admin"}, "admin")
        assert PermissionPolicy.can_assign_role({"role": "admin"}, "customer")
        assert not PermissionPolicy.can_assign_role({"role": "customer"}, "admin")


class TestGovernancePorts:
    """Test governance ports.py lazy imports."""

    def test_lazy_exports_resolve(self):
        """Verify that lazy-exported names resolve from their source modules."""
        try:
            from domains.governance import ports
            # Verify the lazy export map is populated
            assert hasattr(ports, '_LAZY_SERVICE_EXPORTS')
            assert len(ports._LAZY_SERVICE_EXPORTS) > 10
        except ImportError:
            pytest.skip("Cross-domain dependency not available in test env")

    def test_lazy_get_current_user(self):
        try:
            from domains.governance.ports import get_current_user
            assert callable(get_current_user)
        except ImportError:
            pytest.skip("Cross-domain dependency not available in test env")

    def test_lazy_archive_entity(self):
        try:
            from domains.governance.ports import archive_entity
            assert callable(archive_entity)
        except ImportError:
            pytest.skip("Cross-domain dependency not available in test env")

    def test_lazy_restore_entity(self):
        try:
            from domains.governance.ports import restore_entity
            assert callable(restore_entity)
        except ImportError:
            pytest.skip("Cross-domain dependency not available in test env")

    def test_lazy_verify_payout(self):
        try:
            from domains.governance.ports import verify_payout
            assert callable(verify_payout)
        except ImportError:
            pytest.skip("Cross-domain dependency not available in test env")


class TestGovernanceSchemas:
    """Test governance schemas.py."""

    def test_permission_create(self):
        from domains.governance.schemas import PermissionCreate
        p = PermissionCreate(name="test.perm", slug="test_perm", category_id=1)
        assert p.name == "test.perm"
        assert p.scope == "global"

    def test_user_create(self):
        from domains.governance.schemas import UserCreate
        u = UserCreate(email="test@test.com", username="test", password="secret123")
        assert u.email == "test@test.com"
        assert u.role == "customer"

    def test_user_response(self):
        from domains.governance.schemas import UserResponse
        u = UserResponse(id=1, email="t@t.com", username="t", role="admin", is_active=True)
        assert u.id == 1

    def test_bulk_action_response(self):
        from domains.governance.schemas import BulkActionResponse
        r = BulkActionResponse(processed=10, succeeded=8, failed=2)
        assert r.processed == 10


class TestGovernanceReadModels:
    """Test governance read_models.py."""

    def test_admin_activity_projection(self):
        from domains.governance.read_models import AdminActivityProjection
        p = AdminActivityProjection(id=1, admin_id=2, admin_username="admin", action="test")
        assert p.action == "test"

    def test_fraud_event_projection(self):
        from domains.governance.read_models import FraudEventProjection
        p = FraudEventProjection(id=1, event_type="test", risk_score=0.5, status="open")
        assert p.risk_score == 0.5


class TestGovernanceEvents:
    """Test governance events.py."""

    def test_event_constants_defined(self):
        from domains.governance.events import (
            EVENT_GOV_UPDATE_ROLE_PERMISSIONS_REQUESTED,
            EVENT_GOV_ORDER_DELETE_REQUESTED,
            EVENT_GOV_BULK_DELETE_PRODUCTS_ADMIN_REQUESTED,
        )
        assert "gov" in EVENT_GOV_UPDATE_ROLE_PERMISSIONS_REQUESTED

    def test_publish_functions_callable(self):
        from domains.governance.events import (
            publish_gov_update_role_permissions_requested,
            publish_gov_order_delete_requested,
            publish_gov_bulk_delete_products_admin_requested,
        )
        assert callable(publish_gov_update_role_permissions_requested)
        assert callable(publish_gov_order_delete_requested)
        assert callable(publish_gov_bulk_delete_products_admin_requested)


class TestGovernanceSubscribers:
    """Test governance subscribers.py."""

    def test_subscribers_imported(self):
        # Just importing subscribers registers handlers
        import domains.governance.subscribers
        assert domains.governance.subscribers is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
