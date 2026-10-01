"""Regression tests for FILE-86: missing admin sub-roles in rbac/dependencies.py.

Law 162 requires all admin module roles (super_admin, sub_admin, moderator,
finance_officer, country_manager, auditor) to be defined in _ROLE_FEATURES and
_ROLE_MODULES so that require_feature / require_module enforce access correctly.
"""
from __future__ import annotations

import sys
from pathlib import Path

_BACKEND_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

from rbac.dependencies import _ROLE_FEATURES, _ROLE_MODULES, _resolve_effective_features

MISSING_ROLES = ["sub_admin", "moderator", "finance_officer", "country_manager", "auditor"]


class TestAdminSubRolesDefined:
    """Regression: all 5 admin sub-roles must be present in _ROLE_FEATURES and _ROLE_MODULES."""

    def test_all_sub_roles_in_role_features(self):
        for role in MISSING_ROLES:
            assert role in _ROLE_FEATURES, f"Role '{role}' missing from _ROLE_FEATURES"
            assert len(_ROLE_FEATURES[role]) > 0, f"Role '{role}' has empty feature list"

    def test_all_sub_roles_in_role_modules(self):
        for role in MISSING_ROLES:
            assert role in _ROLE_MODULES, f"Role '{role}' missing from _ROLE_MODULES"
            assert len(_ROLE_MODULES[role]) > 0, f"Role '{role}' has empty module list"

    def test_sub_admin_has_sensible_features(self):
        features = _ROLE_FEATURES.get("sub_admin", [])
        assert "accounts.user.read" in features
        assert "orders.manage" in features
        assert "audit.read" in features

    def test_moderator_has_sensible_features(self):
        features = _ROLE_FEATURES.get("moderator", [])
        assert "catalog.list" in features
        assert "audit.read" in features

    def test_finance_officer_has_sensible_features(self):
        features = _ROLE_FEATURES.get("finance_officer", [])
        assert "finance.ledger.read" in features
        assert "finance.reporting.read" in features
        assert "finance.payout.approve" in features

    def test_country_manager_has_sensible_features(self):
        features = _ROLE_FEATURES.get("country_manager", [])
        assert "country.configure" in features
        assert "country.staff.assign" in features
        assert "country.reports.view" in features

    def test_auditor_has_sensible_features(self):
        features = _ROLE_FEATURES.get("auditor", [])
        assert "audit.read" in features
        assert "audit.logs.read" in features
        assert "audit.compliance.read" in features


class TestSubRoleResolutionBehavior:
    """Regression: sub-roles resolve to their feature set via _resolve_effective_features."""

    def test_sub_admin_resolves_features(self):
        user = {"role": "sub_admin", "feature_overrides": []}
        features = _resolve_effective_features(user)
        assert "accounts.user.read" in features
        assert "orders.manage" in features
        assert "audit.read" in features

    def test_moderator_resolves_features(self):
        user = {"role": "moderator", "feature_overrides": []}
        features = _resolve_effective_features(user)
        assert "catalog.list" in features
        assert "audit.read" in features

    def test_finance_officer_resolves_features(self):
        user = {"role": "finance_officer", "feature_overrides": []}
        features = _resolve_effective_features(user)
        assert "finance.ledger.read" in features
        assert "finance.reporting.read" in features

    def test_country_manager_resolves_features(self):
        user = {"role": "country_manager", "feature_overrides": []}
        features = _resolve_effective_features(user)
        assert "country.configure" in features
        assert "country.staff.assign" in features

    def test_auditor_resolves_features(self):
        user = {"role": "auditor", "feature_overrides": []}
        features = _resolve_effective_features(user)
        assert "audit.read" in features
        assert "audit.logs.read" in features

    def test_unknown_role_returns_empty_features(self):
        """Error-path: unknown role returns empty feature set (no KeyError)."""
        user = {"role": "nonexistent_role", "feature_overrides": []}
        features = _resolve_effective_features(user)
        assert features == set()