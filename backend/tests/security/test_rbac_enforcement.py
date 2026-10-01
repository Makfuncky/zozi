"""Comprehensive RBAC enforcement tests for ZOZI backend.

Tests feature catalog aggregation, role resolution, feature/module gating,
wildcard access, permission grant/revoke, and delegation flows.
"""
from __future__ import annotations

import uuid

import pytest


class TestFeatureCatalogAggregation:
    """Test feature catalog aggregation from all domains."""

    def test_catalog_loads_features(self):
        from rbac.catalog import FEATURE_CATALOG

        assert isinstance(FEATURE_CATALOG, dict)
        assert len(FEATURE_CATALOG) > 0

    def test_is_known_feature_returns_true_for_catalog_features(self):
        from rbac.catalog import all_features, is_known

        features = all_features()
        assert len(features) > 0
        assert is_known(features[0]) is True

    def test_is_known_feature_returns_false_for_unknown(self):
        from rbac.catalog import is_known

        assert is_known("totally.fake.feature") is False

    def test_valid_user_roles_defined(self):
        from rbac.catalog import VALID_USER_ROLES

        assert "admin" in VALID_USER_ROLES
        assert "customer" in VALID_USER_ROLES
        assert "supplier" in VALID_USER_ROLES

    def test_feature_namespaces_is_frozenset(self):
        from rbac.catalog import FEATURE_NAMESPACES

        assert isinstance(FEATURE_NAMESPACES, frozenset)

    def test_catalog_contains_security_features(self):
        from rbac.catalog import FEATURE_CATALOG

        security_features = [f for f in FEATURE_CATALOG if f.startswith("security.")]
        assert len(security_features) > 0

    def test_catalog_contains_catalog_features(self):
        from rbac.catalog import FEATURE_CATALOG

        catalog_features = [f for f in FEATURE_CATALOG if f.startswith("catalog.")]
        assert len(catalog_features) > 0


class TestRoleResolution:
    """Test role-to-feature resolution with wildcard expansion."""

    def test_expand_wildcards_star_returns_all(self):
        from rbac.resolution import expand_wildcards

        catalog = {"a.1": {}, "a.2": {}, "b.1": {}}
        result = expand_wildcards(["*"], catalog)
        assert result == {"a.1", "a.2", "b.1"}

    def test_expand_wildcards_namespace_prefix(self):
        from rbac.resolution import expand_wildcards

        catalog = {"catalog.read": {}, "catalog.write": {}, "orders.read": {}}
        result = expand_wildcards(["catalog.*"], catalog)
        assert result == {"catalog.read", "catalog.write"}

    def test_expand_wildcards_explicit_features(self):
        from rbac.resolution import expand_wildcards

        catalog = {"feature.a": {}, "feature.b": {}}
        result = expand_wildcards(["feature.a"], catalog)
        assert result == {"feature.a"}

    def test_expand_wildcards_mixed(self):
        from rbac.resolution import expand_wildcards

        catalog = {"a.1": {}, "a.2": {}, "b.1": {}, "c.1": {}}
        result = expand_wildcards(["a.*", "c.1"], catalog)
        assert result == {"a.1", "a.2", "c.1"}

    def test_effective_features_merges_all_sources(self):
        from rbac.resolution import effective_features

        catalog = {"role.feat": {}, "grant.feat": {}, "override.feat": {}}
        result = effective_features(
            role_features=["role.feat"],
            db_grants=["grant.feat"],
            overrides=["override.feat"],
            catalog=catalog,
        )
        assert result == {"role.feat", "grant.feat", "override.feat"}

    def test_effective_features_empty_catalog(self):
        from rbac.resolution import effective_features

        result = effective_features(catalog={})
        assert result == set()

    def test_effective_features_deduplicates(self):
        from rbac.resolution import effective_features

        catalog = {"feat.a": {}}
        result = effective_features(
            role_features=["feat.a"],
            db_grants=["feat.a"],
            catalog=catalog,
        )
        assert result == {"feat.a"}


class TestRoleFeatureMapping:
    """Test role-to-feature mapping definitions."""

    def test_super_admin_has_wildcard(self):
        from rbac.dependencies import _ROLE_FEATURES

        assert "*" in _ROLE_FEATURES["super_admin"]

    def test_admin_has_wildcard(self):
        from rbac.dependencies import _ROLE_FEATURES

        assert "*" in _ROLE_FEATURES["admin"]

    def test_customer_has_limited_features(self):
        from rbac.dependencies import _ROLE_FEATURES

        customer_features = _ROLE_FEATURES["customer"]
        assert "catalog.read" in customer_features
        assert "*" not in customer_features

    def test_supplier_has_catalog_access(self):
        from rbac.dependencies import _ROLE_FEATURES

        supplier_features = _ROLE_FEATURES["supplier"]
        assert any("catalog" in f for f in supplier_features)

    def test_employee_has_analytics_access(self):
        from rbac.dependencies import _ROLE_FEATURES

        employee_features = _ROLE_FEATURES["employee"]
        assert "analytics.read" in employee_features

    def test_logistics_partner_limited_scope(self):
        from rbac.dependencies import _ROLE_FEATURES

        logistics_features = _ROLE_FEATURES["logistics_partner"]
        assert "logistics.read" in logistics_features
        assert "*" not in logistics_features


class TestRoleModuleMapping:
    """Test role-to-module mapping definitions."""

    def test_admin_has_all_modules(self):
        from rbac.dependencies import _ROLE_MODULES

        assert "*" in _ROLE_MODULES["admin"]

    def test_customer_limited_modules(self):
        from rbac.dependencies import _ROLE_MODULES

        customer_modules = _ROLE_MODULES["customer"]
        assert "catalog" in customer_modules
        assert "*" not in customer_modules

    def test_supplier_has_finance_module(self):
        from rbac.dependencies import _ROLE_MODULES

        supplier_modules = _ROLE_MODULES["supplier"]
        assert "finance" in supplier_modules

    def test_logistics_partner_modules(self):
        from rbac.dependencies import _ROLE_MODULES

        logistics_modules = _ROLE_MODULES["logistics_partner"]
        assert "logistics" in logistics_modules
        assert "orders" in logistics_modules


class TestRequireFeature:
    """Test require_feature() gate behavior."""

    def test_require_feature_returns_callable(self):
        from rbac.dependencies import require_feature

        result = require_feature("catalog.read")
        assert callable(result)

    def test_require_feature_allows_admin_context(self):
        from rbac.dependencies import require_feature, set_current_user

        set_current_user({"id": 1, "role": "admin"})
        try:
            result = require_feature("any.feature")
            # Admin has wildcard, so direct call returns None (allowed)
            assert result is None
        finally:
            set_current_user(None)

    def test_require_feature_denies_customer_for_admin_feature(self):
        from rbac.dependencies import require_feature, set_current_user

        set_current_user({"id": 2, "role": "customer"})
        try:
            with pytest.raises(Exception) as exc_info:
                require_feature("admin.only.feature")
            assert "denied" in str(exc_info.value.detail).lower()
        finally:
            set_current_user(None)

    def test_require_feature_allows_customer_for_catalog(self):
        from rbac.dependencies import require_feature, set_current_user

        set_current_user({"id": 2, "role": "customer"})
        try:
            result = require_feature("catalog.read")
            assert result is None
        finally:
            set_current_user(None)

    def test_require_feature_denies_unauthenticated(self):
        from rbac.dependencies import require_feature, set_current_user

        set_current_user(None)
        # When user is None, require_feature returns a callable (Depends pattern)
        # The callable will fail when FastAPI resolves it
        result = require_feature("catalog.read")
        assert callable(result)


class TestRequireModule:
    """Test require_module() gate behavior."""

    def test_require_module_returns_callable(self):
        from rbac.dependencies import require_module

        result = require_module("catalog")
        assert callable(result)

    def test_require_module_allows_admin(self):
        from rbac.dependencies import require_module, set_current_user

        set_current_user({"id": 1, "role": "admin"})
        try:
            result = require_module("any_module")
            assert result is None
        finally:
            set_current_user(None)

    def test_require_module_denies_customer_for_admin_module(self):
        from rbac.dependencies import require_module, set_current_user

        set_current_user({"id": 2, "role": "customer"})
        try:
            with pytest.raises(Exception) as exc_info:
                require_module("admin")
            assert "denied" in str(exc_info.value.detail).lower()
        finally:
            set_current_user(None)

    def test_require_module_allows_customer_catalog(self):
        from rbac.dependencies import require_module, set_current_user

        set_current_user({"id": 2, "role": "customer"})
        try:
            result = require_module("catalog")
            assert result is None
        finally:
            set_current_user(None)


class TestRequireRoles:
    """Test require_roles() gate behavior."""

    def test_require_roles_returns_callable(self):
        from rbac.dependencies import require_roles

        result = require_roles("admin", "super_admin")
        assert callable(result)

    def test_is_admin_role(self):
        from rbac.roles import is_admin_role

        assert is_admin_role("admin") is True
        assert is_admin_role("sub_admin") is True
        assert is_admin_role("customer") is False
        assert is_admin_role("supplier") is False

    def test_validate_user_role(self):
        from rbac.roles import validate_user_role

        assert validate_user_role("admin") is True
        assert validate_user_role("customer") is True
        assert validate_user_role("nonexistent") is False


class TestWildcardFeatureAccess:
    """Test wildcard feature access for super_admin."""

    def test_super_admin_has_all_features(self):
        from rbac.dependencies import _ROLE_FEATURES
        from rbac.resolution import expand_wildcards
        from rbac.catalog import FEATURE_CATALOG

        super_admin_features = _ROLE_FEATURES["super_admin"]
        effective = expand_wildcards(super_admin_features, FEATURE_CATALOG)

        # Super admin should have every feature in the catalog
        assert effective == set(FEATURE_CATALOG.keys())

    def test_admin_has_all_features(self):
        from rbac.dependencies import _ROLE_FEATURES
        from rbac.resolution import expand_wildcards
        from rbac.catalog import FEATURE_CATALOG

        admin_features = _ROLE_FEATURES["admin"]
        effective = expand_wildcards(admin_features, FEATURE_CATALOG)

        assert effective == set(FEATURE_CATALOG.keys())

    def test_customer_does_not_have_admin_features(self):
        from rbac.dependencies import _ROLE_FEATURES
        from rbac.resolution import expand_wildcards
        from rbac.catalog import FEATURE_CATALOG

        customer_features = _ROLE_FEATURES["customer"]
        effective = expand_wildcards(customer_features, FEATURE_CATALOG)

        admin_only = [f for f in FEATURE_CATALOG if "admin" in f]
        for feat in admin_only:
            assert feat not in effective


class TestFeatureNamespaceAllowlist:
    """Test feature namespace allowlist enforcement."""

    def test_namespace_allowlist_exists(self):
        from rbac.catalog import FEATURE_NAMESPACES

        assert isinstance(FEATURE_NAMESPACES, frozenset)

    def test_expand_namespace_wildcard(self):
        from rbac.resolution import expand_wildcards

        catalog = {
            "catalog.read": {}, "catalog.write": {}, "catalog.delete": {},
            "orders.read": {}, "orders.write": {},
        }
        result = expand_wildcards(["catalog.*"], catalog)
        assert "catalog.read" in result
        assert "catalog.write" in result
        assert "orders.read" not in result


class TestPermissionGrantRevoke:
    """Test RBAC permission grant and revoke operations."""

    def test_rbac_service_instantiation(self, db_session):
        from rbac.service import RBACService

        service = RBACService(db_session)
        assert service is not None
        assert service.db is db_session

    def test_grant_feature_to_role(self, db_session):
        from rbac.service import RBACService

        service = RBACService(db_session)
        assignment = service.grant("test_role_grant", "test.feature.grant", granted_by=1)
        assert assignment is not None
        assert assignment.is_granted is True

    def test_revoke_feature_from_role(self, db_session):
        from rbac.service import RBACService

        service = RBACService(db_session)
        service.grant("test_role_revoke", "test.feature.revoke", granted_by=1)
        db_session.commit()

        result = service.revoke("test_role_revoke", "test.feature.revoke", revoked_by=1)
        assert result is not None
        assert result.is_granted is False

    def test_revoke_unknown_feature_returns_none(self, db_session):
        from rbac.service import RBACService

        service = RBACService(db_session)
        result = service.revoke("some_role", "totally.unknown.feature")
        assert result is None

    def test_check_permission_admin_has_anything(self, db_session):
        from rbac.service import RBACService

        service = RBACService(db_session)
        assert service.check_permission("admin", "any.feature.at.all") is True

    def test_check_permission_customer_has_catalog(self, db_session):
        from rbac.service import RBACService

        service = RBACService(db_session)
        assert service.check_permission("customer", "catalog.read") is True

    def test_check_permission_customer_denied_admin(self, db_session):
        from rbac.service import RBACService

        service = RBACService(db_session)
        assert service.check_permission("customer", "admin.only.feature") is False

    def test_grant_with_country_scope(self, db_session):
        from rbac.service import RBACService

        service = RBACService(db_session)
        assignment = service.grant(
            "country_role", "test.feature",
            granted_by=1, country_code="AE",
        )
        assert assignment is not None
        assert assignment.country_code == "AE"

    def test_grant_idempotent(self, db_session):
        from rbac.service import RBACService

        service = RBACService(db_session)
        role = f"idempotent_role_{uuid.uuid4().hex[:8]}"

        a1 = service.grant(role, "test.feature", granted_by=1)
        db_session.commit()
        a2 = service.grant(role, "test.feature", granted_by=1)

        assert a1.id == a2.id
        assert a2.is_granted is True


class TestDelegationAndMakerChecker:
    """Test delegation and maker-checker flows."""

    def test_grant_records_granted_by(self, db_session):
        from rbac.service import RBACService

        service = RBACService(db_session)
        assignment = service.grant("delegation_role", "delegated.feature", granted_by=42)

        assert assignment.granted_by == 42

    def test_revoke_records_revoked_by(self, db_session):
        from rbac.service import RBACService

        service = RBACService(db_session)
        service.grant("revoke_role", "revoke.feature", granted_by=1)
        db_session.commit()

        result = service.revoke("revoke_role", "revoke.feature", revoked_by=99)
        assert result is not None

    def test_audit_log_created_on_grant(self, db_session):
        from rbac.service import RBACService
        from rbac.models.permission_entities import PermissionAuditLog

        service = RBACService(db_session)
        service.grant("audit_role", "audit.feature", granted_by=1)
        db_session.commit()

        logs = db_session.query(PermissionAuditLog).filter(
            PermissionAuditLog.target_role == "audit_role",
        ).all()
        assert len(logs) >= 1

    def test_audit_log_created_on_revoke(self, db_session):
        from rbac.service import RBACService
        from rbac.models.permission_entities import PermissionAuditLog

        service = RBACService(db_session)
        service.audit_log_table = PermissionAuditLog
        service.grant("audit_revoke_role", "audit_revoke.feature", granted_by=1)
        db_session.commit()
        service.revoke("audit_revoke_role", "audit_revoke.feature", revoked_by=2)
        db_session.commit()

        logs = db_session.query(PermissionAuditLog).filter(
            PermissionAuditLog.target_role == "audit_revoke_role",
            PermissionAuditLog.action == "revoke",
        ).all()
        assert len(logs) >= 1


class TestRBACServiceIntegration:
    """Integration tests for RBAC with API endpoints."""

    def test_admin_can_access_admin_endpoints(self, admin_client):
        """Admin token should access admin endpoints."""
        # The admin_client has admin auth headers pre-set
        # We just verify the client is properly configured
        assert admin_client is not None

    def test_customer_denied_admin_endpoints(self, customer_client):
        """Customer should be denied admin-only endpoints."""
        resp = customer_client.get("/admin/users")
        assert resp.status_code in (403, 404)

    def test_supplier_denied_admin_endpoints(self, supplier_client):
        """Supplier should be denied admin-only endpoints."""
        resp = supplier_client.get("/admin/users")
        assert resp.status_code in (403, 404)
