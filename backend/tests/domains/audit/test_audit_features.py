"""Audit domain — feature + service smoke tests.

Laws 4 (features), 2 (thin routers), 230/278 (WORM audit trail).
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Ensure tests._support is importable (pytest import machinery fix).
_TESTS_DIR = Path(__file__).resolve().parent.parent.parent
if str(_TESTS_DIR) not in sys.path:
    sys.path.insert(0, str(_TESTS_DIR))


class TestAuditFeatureAtoms:
    """Law 4 — representative audit feature atoms in rbac catalog."""

    @pytest.mark.parametrize(
        "feature",
        [
            "audit.read",
            "audit.logs.read",
            "audit.logs.export",
            "audit.compliance.read",
            "audit.compliance.manage",
            "audit.config.read",
            "audit.config.manage",
            "audit.anomalies.read",
            "audit.anomalies.manage",
            "audit.command_center.read",
            "audit.command_center.configure",
        ],
    )
    def test_feature_in_catalog(self, feature):
        from tests._support.laws import assert_feature_in_catalog

        assert_feature_in_catalog(feature)


class TestAuditServiceImports:
    """Law 2 — service layer is importable."""

    def test_import_audit_service(self):
        from domains.audit.services import audit_service as svc

        assert svc is not None

    def test_import_worm_audit(self):
        from domains.audit.services import worm_audit

        assert worm_audit is not None

    def test_import_compliance_engine(self):
        from domains.audit.services import compliance_engine

        assert compliance_engine is not None

    def test_import_audit_trail_service(self):
        from domains.audit.services.logs import audit_trail_service

        assert audit_trail_service is not None


class TestAuditModelPersistence:
    """Laws 6/23 — models persist with audit columns."""

    def test_audit_log_persists(self, db_session):
        from domains.audit.models.audit_schema_models import AuditLog

        log = AuditLog(
            action="test_action",
            entity_type="test_entity",
            entity_id=1,
            user_id=1,
        )
        db_session.add(log)
        db_session.flush()

        assert log.id is not None
        assert log.created_at is not None
        assert log.is_deleted is False

    def test_command_center_view_persists(self, db_session):
        from domains.audit.models.audit_schema_models import CommandCenterView

        view = CommandCenterView(user_id=1, view_name="test_view")
        db_session.add(view)
        db_session.flush()

        assert view.id is not None
        assert view.created_at is not None


class TestAuditActionCatalog:
    """Law 4 — AuditAction catalog covers the security event vocabulary."""

    def test_audit_action_has_security_actions(self):
        from domains.audit.services.audit_service import AuditAction

        assert hasattr(AuditAction, "LOGIN_SUCCESS")
        assert hasattr(AuditAction, "LOGIN_FAILED")
        assert hasattr(AuditAction, "PASSWORD_CHANGED")
        assert hasattr(AuditAction, "ACCOUNT_LOCKED")
        assert hasattr(AuditAction, "FRAUD_FLAG")

    def test_audit_action_has_crud_actions(self):
        from domains.audit.services.audit_service import AuditAction

        assert hasattr(AuditAction, "CREATE")
        assert hasattr(AuditAction, "UPDATE")
        assert hasattr(AuditAction, "DELETE")


class TestAuditCompliance:
    """Laws 230/278 — compliance service is functional."""

    def test_compliance_service_exists(self):
        from domains.audit.services import compliance_service

        assert compliance_service is not None

    def test_data_residency_service_exists(self):
        from domains.audit.services import data_residency_service

        assert data_residency_service is not None
