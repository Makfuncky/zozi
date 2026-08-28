"""Behavior tests for audit domain — audit logs, compliance, data residency, eDiscovery, retention, and WORM trail."""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timedelta, timezone

import pytest

from domains.audit.models.audit_schema_models import AuditLog
from domains.audit.ports import AuditAction


def _create_audit_log(db_session, action="TEST_ACTION", entity_type="test", entity_id=1, user_id=1):
    log = AuditLog(
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        user_id=user_id,
        username="testuser",
        user_role="admin",
        details={"test": True},
        ip_address="127.0.0.1",
    )
    db_session.add(log)
    db_session.flush()
    return log


# ══════════════════════════════════════════════════════════════════
# Audit Log Creation
# ══════════════════════════════════════════════════════════════════


@pytest.mark.integration
class TestAuditLogCreation:
    """Test audit log creation."""

    def test_create_audit_log(self, db_session):
        log = _create_audit_log(db_session)
        assert log.id is not None
        assert log.action == "TEST_ACTION"
        assert log.entity_type == "test"

    def test_audit_log_timestamp_auto_set(self, db_session):
        log = _create_audit_log(db_session)
        assert log.created_at is not None

    def test_audit_log_with_details(self, db_session):
        log = _create_audit_log(db_session, action="ORDER_CREATED")
        log.details = {"order_id": 123, "amount": 99.99}
        db_session.flush()
        assert log.details is not None

    def test_audit_log_with_ip_address(self, db_session):
        log = _create_audit_log(db_session)
        assert log.ip_address == "127.0.0.1"

    def test_audit_log_user_tracking(self, db_session):
        log = _create_audit_log(db_session, user_id=42, username="admin_user")
        assert log.user_id == 42
        assert log.username == "admin_user"


# ══════════════════════════════════════════════════════════════════
# Audit Log Querying and Filtering
# ══════════════════════════════════════════════════════════════════


@pytest.mark.integration
class TestAuditLogQuerying:
    """Test audit log querying and filtering."""

    def test_query_audit_logs_by_action(self, db_session):
        _create_audit_log(db_session, action="LOGIN_SUCCESS")
        _create_audit_log(db_session, action="LOGIN_FAILED")
        results = db_session.query(AuditLog).filter(AuditLog.action == "LOGIN_SUCCESS").all()
        assert len(results) >= 1
        assert all(r.action == "LOGIN_SUCCESS" for r in results)

    def test_query_audit_logs_by_entity_type(self, db_session):
        _create_audit_log(db_session, entity_type="order")
        _create_audit_log(db_session, entity_type="user")
        results = db_session.query(AuditLog).filter(AuditLog.entity_type == "order").all()
        assert len(results) >= 1
        assert all(r.entity_type == "order" for r in results)

    def test_query_audit_logs_by_user_id(self, db_session):
        _create_audit_log(db_session, user_id=1)
        _create_audit_log(db_session, user_id=2)
        results = db_session.query(AuditLog).filter(AuditLog.user_id == 1).all()
        assert len(results) >= 1
        assert all(r.user_id == 1 for r in results)

    def test_query_audit_logs_by_entity_id(self, db_session):
        _create_audit_log(db_session, entity_id=100)
        _create_audit_log(db_session, entity_id=200)
        results = db_session.query(AuditLog).filter(AuditLog.entity_id == 100).all()
        assert len(results) >= 1
        assert all(r.entity_id == 100 for r in results)

    def test_query_audit_logs_ordered_by_date(self, db_session):
        _create_audit_log(db_session, action="FIRST")
        _create_audit_log(db_session, action="SECOND")
        results = db_session.query(AuditLog).order_by(AuditLog.created_at.desc()).all()
        assert len(results) >= 2

    def test_query_audit_logs_with_limit(self, db_session):
        for i in range(5):
            _create_audit_log(db_session, action=f"ACTION_{i}")
        results = db_session.query(AuditLog).limit(3).all()
        assert len(results) == 3

    def test_filter_audit_logs_by_date_range(self, db_session):
        log = _create_audit_log(db_session)
        now = datetime.now(timezone.utc)
        results = db_session.query(AuditLog).filter(
            AuditLog.created_at >= now - timedelta(hours=1),
            AuditLog.created_at <= now + timedelta(hours=1),
        ).all()
        assert len(results) >= 1


# ══════════════════════════════════════════════════════════════════
# Compliance Engine (GDPR, PCI-DSS checks)
# ══════════════════════════════════════════════════════════════════


@pytest.mark.integration
class TestComplianceEngine:
    """Test compliance engine (GDPR, PCI-DSS checks)."""

    def test_gdpr_compliance_check(self, db_session):
        from domains.audit.services.compliance_engine import get_compliance_engine
        engine = get_compliance_engine(db_session)
        result = engine.check_gdpr_compliance()
        assert result is not None

    def test_pci_dss_compliance_check(self, db_session):
        from domains.audit.services.compliance_engine import get_compliance_engine
        engine = get_compliance_engine(db_session)
        result = engine.check_pci_dss_compliance()
        assert result is not None

    def test_compliance_report_generation(self, db_session):
        from domains.audit.services.compliance_engine import get_compliance_engine
        engine = get_compliance_engine(db_session)
        result = engine.generate_compliance_report()
        assert result is not None

    def test_compliance_violation_logging(self, db_session):
        from domains.audit.services.compliance_engine import get_compliance_engine
        engine = get_compliance_engine(db_session)
        result = engine.log_violation(
            violation_type="gdpr_data_retention",
            description="Data retained beyond policy",
            severity="high",
        )
        assert result is not None


# ══════════════════════════════════════════════════════════════════
# Data Residency Enforcement
# ══════════════════════════════════════════════════════════════════


@pytest.mark.integration
class TestDataResidency:
    """Test data residency enforcement."""

    def test_check_data_residency(self, db_session):
        from domains.audit.services.data_residency_service import check_data_residency
        result = check_data_residency(user_id=1, country_code="AE", db=db_session)
        assert isinstance(result, bool)

    def test_enforce_data_residency(self, db_session):
        from domains.audit.services.data_residency_service import enforce_data_residency
        result = enforce_data_residency(user_id=1, target_country="AE", db=db_session)
        assert result is not None

    def test_flat_data_residency_check(self, db_session):
        from domains.audit.services.flat_data_residency_service import check_flat_residency
        result = check_flat_residency(entity_type="user", entity_id=1, db=db_session)
        assert result is not None


# ══════════════════════════════════════════════════════════════════
# eDiscovery Search
# ══════════════════════════════════════════════════════════════════


@pytest.mark.integration
class TestEDiscoverySearch:
    """Test eDiscovery search."""

    def test_search_audit_trail_by_entity(self, db_session):
        from domains.audit.services.ediscovery import EDiscoveryService
        service = EDiscoveryService(db_session)
        _create_audit_log(db_session, entity_type="order", entity_id=100)
        results = service.search_audit_trail(entity_type="order", entity_id=100)
        assert isinstance(results, list)
        assert len(results) >= 1

    def test_search_audit_trail_by_user(self, db_session):
        from domains.audit.services.ediscovery import EDiscoveryService
        service = EDiscoveryService(db_session)
        _create_audit_log(db_session, user_id=42)
        results = service.search_audit_trail(user_id=42)
        assert isinstance(results, list)
        assert len(results) >= 1

    def test_search_audit_trail_by_action(self, db_session):
        from domains.audit.services.ediscovery import EDiscoveryService
        service = EDiscoveryService(db_session)
        _create_audit_log(db_session, action="ORDER_CREATED")
        results = service.search_audit_trail(action="ORDER_CREATED")
        assert isinstance(results, list)

    def test_search_audit_trail_with_date_range(self, db_session):
        from domains.audit.services.ediscovery import EDiscoveryService
        service = EDiscoveryService(db_session)
        now = datetime.now(timezone.utc)
        results = service.search_audit_trail(
            start_date=(now - timedelta(days=1)).isoformat(),
            end_date=(now + timedelta(days=1)).isoformat(),
        )
        assert isinstance(results, list)

    def test_get_entity_timeline(self, db_session):
        from domains.audit.services.ediscovery import EDiscoveryService
        service = EDiscoveryService(db_session)
        _create_audit_log(db_session, entity_type="order", entity_id=50)
        _create_audit_log(db_session, entity_type="order", entity_id=50)
        results = service.get_entity_timeline(entity_type="order", entity_id=50)
        assert isinstance(results, list)
        assert len(results) >= 2

    def test_export_for_legal(self, db_session):
        from domains.audit.services.ediscovery import EDiscoveryService
        service = EDiscoveryService(db_session)
        _create_audit_log(db_session, entity_type="order", entity_id=75)
        result = service.export_for_legal(entity_type="order", entity_id=75)
        assert "export_format" in result
        assert "records" in result
        assert "record_count" in result

    def test_search_audit_trail_with_limit(self, db_session):
        from domains.audit.services.ediscovery import EDiscoveryService
        service = EDiscoveryService(db_session)
        results = service.search_audit_trail(limit=5)
        assert isinstance(results, list)
        assert len(results) <= 5


# ══════════════════════════════════════════════════════════════════
# Retention Policy Enforcement
# ══════════════════════════════════════════════════════════════════


@pytest.mark.integration
class TestRetentionPolicy:
    """Test retention policy enforcement."""

    def test_run_retention_cycle(self, db_session):
        from domains.audit.services.retention_service import run_operational_retention_cycle
        result = run_operational_retention_cycle(db_session)
        assert "targets" in result
        assert isinstance(result["targets"], list)

    def test_retention_policies_defined(self):
        from domains.audit.services.retention_service import _RETENTION_POLICIES
        assert len(_RETENTION_POLICIES) > 0
        for policy in _RETENTION_POLICIES:
            assert "target" in policy
            assert "days" in policy
            assert "model" in policy

    def test_retention_audit_log_policy(self):
        from domains.audit.services.retention_service import _RETENTION_POLICIES
        audit_policy = next((p for p in _RETENTION_POLICIES if p["target"] == "audit_logs"), None)
        assert audit_policy is not None
        assert audit_policy["days"] == 365

    def test_retention_shipment_events_policy(self):
        from domains.audit.services.retention_service import _RETENTION_POLICIES
        shipment_policy = next((p for p in _RETENTION_POLICIES if p["target"] == "shipment_events"), None)
        assert shipment_policy is not None
        assert shipment_policy["days"] == 180

    def test_retention_skips_recent_run(self, db_session):
        from domains.audit.services.retention_service import _should_skip_recent_run
        result = _should_skip_recent_run("audit_logs", db_session)
        assert isinstance(result, bool)


# ══════════════════════════════════════════════════════════════════
# Security Audit Execution
# ══════════════════════════════════════════════════════════════════


@pytest.mark.integration
class TestSecurityAudit:
    """Test security audit execution."""

    def test_execute_security_audit(self, db_session):
        from domains.audit.services.security_audit import log_security_event
        result = log_security_event(
            action="LOGIN_SUCCESS",
            user_id=1,
            username="testuser",
            ip_address="127.0.0.1",
        )
        assert result is not None

    def test_security_event_types_defined(self):
        from domains.audit.services.security_audit import SECURITY_EVENTS
        assert "LOGIN_SUCCESS" in SECURITY_EVENTS
        assert "LOGIN_FAILED" in SECURITY_EVENTS
        assert "ACCOUNT_LOCKED" in SECURITY_EVENTS
        assert "PASSWORD_CHANGE" in SECURITY_EVENTS

    def test_log_all_security_event_types(self, db_session):
        from domains.audit.services.security_audit import log_security_event, SECURITY_EVENTS
        for event_type in list(SECURITY_EVENTS)[:5]:
            result = log_security_event(
                action=event_type,
                user_id=1,
                status="success",
            )
            assert result is not None

    def test_security_audit_with_details(self, db_session):
        from domains.audit.services.security_audit import log_security_event
        result = log_security_event(
            action="SUSPICIOUS_ACTIVITY",
            user_id=1,
            details={"reason": "Multiple IPs", "count": 3},
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0",
        )
        assert result is not None


# ══════════════════════════════════════════════════════════════════
# WORM Audit Trail
# ══════════════════════════════════════════════════════════════════


@pytest.mark.integration
class TestWORMuditTrail:
    """Test WORM (Write-Once-Read-Many) audit trail."""

    def test_worm_service_initialization(self, db_session):
        from domains.audit.services.worm_audit import WORMAuditService
        service = WORMAuditService(db_session)
        assert service is not None
        assert service.db is not None

    def test_worm_append_audit_record(self, db_session):
        from domains.audit.services.worm_audit import WORMAuditService
        service = WORMAuditService(db_session)
        result = service.append(
            action="TEST_ACTION",
            entity_type="test_entity",
            entity_id=1,
            user_id=1,
            username="testuser",
        )
        assert result is not None
        assert result.id is not None

    def test_worm_chain_integrity(self, db_session):
        from domains.audit.services.worm_audit import WORMAuditService
        service = WORMAuditService(db_session)
        result = service.get_chain_integrity()
        assert "total_records" in result
        assert "chain_valid" in result
        assert "last_hash" in result

    def test_worm_multiple_appends(self, db_session):
        from domains.audit.services.worm_audit import WORMAuditService
        service = WORMAuditService(db_session)
        service.append(action="ACTION_1", entity_type="test", entity_id=1)
        service.append(action="ACTION_2", entity_type="test", entity_id=2)
        result = service.get_chain_integrity()
        assert result["total_records"] >= 2

    def test_worm_record_hash_computation(self, db_session):
        from domains.audit.services.worm_audit import WORMAuditService
        service = WORMAuditService(db_session)
        log = _create_audit_log(db_session)
        record_hash = service._compute_record_hash(log)
        assert isinstance(record_hash, str)
        assert len(record_hash) == 64

    def test_worm_chain_hash_computation(self, db_session):
        from domains.audit.services.worm_audit import WORMAuditService
        service = WORMAuditService(db_session)
        record_hash = "abc123"
        chain_hash = service._compute_chain_hash(record_hash)
        assert isinstance(chain_hash, str)
        assert len(chain_hash) == 64

    def test_worm_chain_tail_hash(self, db_session):
        from domains.audit.services.worm_audit import WORMAuditService
        service = WORMAuditService(db_session)
        tail_hash = service._get_chain_tail_hash()
        assert isinstance(tail_hash, str)


# ══════════════════════════════════════════════════════════════════
# Audit Action Constants
# ══════════════════════════════════════════════════════════════════


@pytest.mark.integration
class TestAuditActionConstants:
    """Test audit action constants."""

    def test_audit_action_has_order_actions(self):
        assert hasattr(AuditAction, "ORDER_CREATED") or hasattr(AuditAction, "ORDER_STATUS_CHANGED")

    def test_audit_action_has_user_actions(self):
        assert hasattr(AuditAction, "USER_CREATED") or hasattr(AuditAction, "USER_UPDATED")

    def test_audit_action_has_security_actions(self):
        assert hasattr(AuditAction, "LOGIN_SUCCESS") or hasattr(AuditAction, "LOGIN_FAILED")
