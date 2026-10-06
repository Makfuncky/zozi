"""Fail-before reproduction for WORMAuditService db session bug.

When WORMAuditService is instantiated without an explicit db session,
get_service_session() returns a context manager rather than a Session,
so every self.db.query(...) raises AttributeError. This test proves
the bug and will also serve as the paired test after the fix.
"""
from __future__ import annotations

from contextlib import nullcontext
from unittest.mock import MagicMock, patch

import pytest

from domains.audit.services.worm_audit import WORMAuditService


class TestWORMAuditServiceFailBefore:
    """Reproduce the P0: get_chain_integrity() cannot execute at all."""

    def test_get_chain_integrity_without_explicit_db_returns_result(self):
        """After fix: calling get_chain_integrity() without passing db
        must return a dict without raising AttributeError."""
        from contextlib import nullcontext

        mock_session = MagicMock()
        mock_session.query.return_value.order_by.return_value.all.return_value = []
        mock_cm = nullcontext(mock_session)

        with patch(
            "infrastructure.database.database.get_service_session",
            return_value=mock_cm,
        ):
            service = WORMAuditService()
            result = service.get_chain_integrity()
            assert isinstance(result, dict)
            assert "chain_valid" in result
            assert "total_records" in result


class TestWORMAuditServiceIntegrityPaired:
    """Paired tests: prove tamper detection works after the fix."""

    def test_empty_ledger_reports_valid(self, db_session):
        """Empty ledger is a valid (vacuous) chain."""
        from domains.audit.services.worm_audit import get_worm_audit_service

        svc = get_worm_audit_service(db_session)
        integrity = svc.get_chain_integrity()
        assert integrity["chain_valid"] is True
        assert integrity["total_records"] == 0
        assert integrity["first_break"] is None

    def test_single_record_chain_is_valid(self, db_session):
        """A single record whose prev_hash matches genesis is valid."""
        from domains.audit.services.worm_audit import get_worm_audit_service

        svc = get_worm_audit_service(db_session)
        svc.append(action="test.action", entity_type="test_entity", entity_id=1)
        integrity = svc.get_chain_integrity()
        assert integrity["chain_valid"] is True
        assert integrity["total_records"] == 1
        assert integrity["first_break"] is None

    def test_intact_multi_record_chain_reports_valid(self, db_session):
        """Multiple records forming an unbroken chain are valid."""
        from domains.audit.services.worm_audit import get_worm_audit_service

        svc = get_worm_audit_service(db_session)
        svc.append(action="a1", entity_type="e", entity_id=1)
        svc.append(action="a2", entity_type="e", entity_id=2)
        svc.append(action="a3", entity_type="e", entity_id=3)
        integrity = svc.get_chain_integrity()
        assert integrity["chain_valid"] is True
        assert integrity["total_records"] == 3
        assert integrity["first_break"] is None

    def test_tampered_payload_detected(self, db_session):
        """Modifying a record's action breaks its hash; integrity check
        must report chain_valid=False and identify the tampered record."""
        from domains.audit.services.worm_audit import get_worm_audit_service
        from domains.audit.models.audit_schema_models import AuditLog

        svc = get_worm_audit_service(db_session)
        svc.append(action="original", entity_type="e", entity_id=1)

        # Tamper with the stored record directly
        stored = db_session.query(AuditLog).first()
        assert stored is not None
        stored.action = "modified"
        db_session.flush()

        integrity = svc.get_chain_integrity()
        assert integrity["chain_valid"] is False
        assert integrity["first_break"] is not None
        assert integrity["first_break"]["record_id"] == stored.id

    def test_broken_prev_hash_link_detected(self, db_session):
        """Breaking the prev_hash link between two records must be detected."""
        from domains.audit.services.worm_audit import get_worm_audit_service
        from domains.audit.models.audit_schema_models import AuditLog

        svc = get_worm_audit_service(db_session)
        svc.append(action="a1", entity_type="e", entity_id=1)
        svc.append(action="a2", entity_type="e", entity_id=2)

        # Break the second record's prev_hash
        records = db_session.query(AuditLog).order_by(AuditLog.id.asc()).all()
        assert len(records) == 2
        records[1].worm_prev_hash = "broken_link"
        db_session.flush()

        integrity = svc.get_chain_integrity()
        assert integrity["chain_valid"] is False
        assert integrity["first_break"] is not None
        assert integrity["first_break"]["record_id"] == records[1].id
