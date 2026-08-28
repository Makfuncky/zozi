"""Audit domain — law-aligned architecture tests.

Maps to ARCHITECTURE_DIAGRAM.md Laws:
  Law 1   : arrows point down only
  Law 3   : events/ports wiring
  Law 4   : features single-sourced
  Laws 6/23/55/152 : schema discipline
  Laws 22/52 : FK ondelete
  Law 230/278 : WORM-style immutable audit trail writes
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Ensure tests._support is importable (pytest import machinery fix).
_TESTS_DIR = Path(__file__).resolve().parent.parent.parent
if str(_TESTS_DIR) not in sys.path:
    sys.path.insert(0, str(_TESTS_DIR))

from tests._support.laws import (
    BACKEND_ROOT,
    assert_feature_in_catalog,
    assert_foreign_keys_have_ondelete,
    assert_no_forbidden_imports,
    assert_schema_discipline,
    iter_domain_models,
)

DOMAIN = "audit"


def _audit_models():
    return list(iter_domain_models(DOMAIN))


# Both audit models have country_code FK missing ondelete (Law 22/52).
KNOWN_FK_VIOLATIONS = {
    "AuditLog",
    "CommandCenterView",
}


class TestAuditSchemaDiscipline:
    """Laws 6/23/55/152 — schema + audit columns."""

    @pytest.mark.parametrize("model", _audit_models(), ids=lambda m: m.__name__)
    def test_model_schema_discipline(self, model):
        assert_schema_discipline(model)


class TestAuditForeignKeyOndelete:
    """Laws 22/52 — every ForeignKey declares explicit ondelete."""

    @pytest.mark.parametrize("model", _audit_models(), ids=lambda m: m.__name__)
    def test_foreign_keys_have_ondelete(self, model):
        if model.__name__ in KNOWN_FK_VIOLATIONS:
            pytest.xfail(
                f"{model.__name__}: country_code FK missing ondelete (Law 22/52)"
            )
        assert_foreign_keys_have_ondelete(model)


class TestAuditFeaturesSingleSourced:
    """Law 4 — feature atoms single-sourced + in rbac catalog."""

    def test_features_declared(self):
        from domains.audit.features import FEATURES

        assert isinstance(FEATURES, dict)
        assert len(FEATURES) > 0

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
        assert_feature_in_catalog(feature)


class TestAuditEventsAndPortsWired:
    """Law 3 — cross-domain writes via events.py, reads via ports.py."""

    def test_events_module_has_audit_events(self):
        from domains.audit import events

        assert hasattr(events, "EVENT_AUDIT_TRAIL_CREATED")
        assert hasattr(events, "EVENT_AUDIT_TRAIL_EXPORTED")
        assert hasattr(events, "EVENT_COMPLIANCE_CHECK_RUN")
        assert hasattr(events, "EVENT_DATA_RESIDENCY_VIOLATION")

    def test_events_has_publish_helpers(self):
        from domains.audit import events

        assert callable(events.publish_audit_trail_created)
        assert callable(events.publish_compliance_check_run)

    def test_ports_module_exposes_audit_log(self):
        from domains.audit import ports

        assert hasattr(ports, "AuditLog")

    def test_subscribers_have_handlers(self):
        from domains.audit import subscribers

        assert callable(subscribers._on_order_status_changed)
        assert callable(subscribers._on_governance_incident_created)


class TestAuditImportLaws:
    """Law 1 — arrows point down only."""

    def test_no_forbidden_imports_in_domain(self):
        source_dir = BACKEND_ROOT / "domains" / DOMAIN
        assert_no_forbidden_imports("domains", source_dir)


# ---------------------------------------------------------------------------
# Law 230/278 — WORM-style immutable audit trail
# ---------------------------------------------------------------------------
class TestAuditWORM:
    """Laws 230/278 — audit trail is append-only with chain-of-custody."""

    def test_worm_audit_service_exists(self):
        from domains.audit.services.worm_audit import WORMAuditService

        assert WORMAuditService is not None
        assert hasattr(WORMAuditService, "append")
        assert hasattr(WORMAuditService, "get_chain_integrity")

    def test_worm_append_creates_record(self, db_session):
        """WORM append must produce an audit row with a chain hash."""
        from domains.audit.services.worm_audit import WORMAuditService

        svc = WORMAuditService(db_session)
        record = svc.append(
            action="test_action",
            entity_type="test_entity",
            entity_id=1,
            user_id=1,
        )
        assert record.id is not None
        assert record.action == "test_action"
        assert record.entity_type == "test_entity"

    def test_worm_chain_integrity_check(self, db_session):
        """Chain integrity check must return a valid structure."""
        from domains.audit.services.worm_audit import WORMAuditService

        svc = WORMAuditService(db_session)
        svc.append(action="first", entity_type="e", entity_id=1)
        svc.append(action="second", entity_type="e", entity_id=2)
        integrity = svc.get_chain_integrity()
        assert "total_records" in integrity
        assert "chain_valid" in integrity
        assert integrity["total_records"] >= 2

    def test_worm_uses_hmac_chain(self):
        """WORM chain must use HMAC (not plain hash) for tamper evidence."""
        import inspect
        from domains.audit.services.worm_audit import WORMAuditService

        src = inspect.getsource(WORMAuditService._compute_chain_hash)
        assert "hmac" in src.lower(), "WORM chain hash must use HMAC"


class TestAuditServiceProducesRows:
    """State-changing flows produce audit rows when an audit service exists."""

    def test_audit_service_log_action(self, db_session):
        from domains.audit.services.audit_service import audit_log

        log = audit_log(
            db_session,
            action="TEST_ACTION",
            user_id=1,
            resource_type="test",
            resource_id=1,
        )
        assert log.id is not None
        assert log.action == "TEST_ACTION"

    def test_audit_log_model_has_required_fields(self):
        """Law 230 — audit log must capture who, what, when."""
        from domains.audit.models.audit_schema_models import AuditLog

        assert hasattr(AuditLog, "action")
        assert hasattr(AuditLog, "entity_type")
        assert hasattr(AuditLog, "entity_id")
        assert hasattr(AuditLog, "user_id")
        assert hasattr(AuditLog, "created_at")
        assert hasattr(AuditLog, "country_code")
