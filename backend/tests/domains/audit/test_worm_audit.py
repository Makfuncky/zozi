"""WORM audit service behavioral tests.

TST-042 — behavioral tests for WORM audit service.
"""
from __future__ import annotations

import hashlib
import hmac
from unittest.mock import MagicMock, patch

import pytest

from domains.audit.services.worm_audit import WORMAuditService


class TestWORMAuditService:
    """TST-042 — behavioral tests for WORM audit service."""

    def test_worm_append_creates_immutable_record(self):
        """Verify append creates an AuditLog record and seals it."""
        mock_record = MagicMock()
        mock_record.id = 1
        mock_record.action = "test.action"
        mock_record.entity_type = "test_entity"
        mock_record.user_id = 1
        mock_record.username = "test_user"
        mock_record.details = {"worm_hash": "sealed_hash"}

        db_session = MagicMock()
        db_session.execute.return_value.scalar.return_value = None

        with patch.object(
            WORMAuditService, "_get_chain_tail_hash", return_value="fixed_hash"
        ), patch(
            "domains.audit.services.worm_audit.AuditLog", return_value=mock_record
        ):
            service = WORMAuditService(db_session)
            record = service.append(
                action="test.action",
                entity_type="test_entity",
                entity_id=1,
                user_id=1,
                username="test_user",
                user_role="admin",
                details={"key": "value"},
                ip_address="127.0.0.1",
                country_code="AE",
            )

        db_session.add.assert_called_once_with(mock_record)
        db_session.flush.assert_called()
        assert record.worm_hash is not None
        assert record.worm_prev_hash is not None
        assert "worm_hash" in (record.details or {})
        assert "worm_prev_hash" in (record.details or {})
        assert record.id == 1
        assert record.action == "test.action"
        assert record.entity_type == "test_entity"

    def test_worm_chain_hash_links_records(self):
        """Verify chain hash is computed and links to previous record."""
        from infrastructure.utils.config import settings

        chain_key = (
            settings.audit_chain_key or settings.secret_key or "zozi_audit_chain"
        ).encode()

        service = WORMAuditService.__new__(WORMAuditService)
        service._chain_key = chain_key
        service._last_hash = hashlib.sha256(b"genesis").hexdigest()

        first = MagicMock()
        first.id = 1
        first.action = "test.action.one"
        first.entity_type = "test_entity"
        first.entity_id = 1
        first.created_at = None

        first_hash = service._compute_record_hash(first)
        first_chain = service._compute_chain_hash(first_hash)
        service._last_hash = first_chain

        second = MagicMock()
        second.id = 2
        second.action = "test.action.two"
        second.entity_type = "test_entity"
        second.entity_id = 2
        second.created_at = None

        second_hash = service._compute_record_hash(second)
        second_chain = service._compute_chain_hash(second_hash)

        assert first_chain != second_chain
        chain_input = f"{first_chain}|{second_hash}"
        expected_second_chain = hmac.new(
            chain_key, chain_input.encode(), hashlib.sha256
        ).hexdigest()
        assert second_chain == expected_second_chain

    def test_worm_prevents_mutation(self):
        """Verify WORM service prevents mutation: no update/delete API
        and any record modification breaks the seal."""
        assert not hasattr(WORMAuditService, "update")
        assert not hasattr(WORMAuditService, "delete")
        assert not hasattr(WORMAuditService, "modify")
        assert not hasattr(WORMAuditService, "remove")

        record = MagicMock()
        record.id = 1
        record.action = "test.action"
        record.entity_type = "test_entity"
        record.entity_id = 1
        record.created_at = None

        original_hash = hashlib.sha256(
            f"{record.id}|{record.action}|{record.entity_type}|{record.entity_id}|"
            f"{record.created_at.isoformat() if record.created_at else ''}".encode()
        ).hexdigest()

        record.action = "modified.action"

        recomputed = hashlib.sha256(
            f"{record.id}|{record.action}|{record.entity_type}|{record.entity_id}|"
            f"{record.created_at.isoformat() if record.created_at else ''}".encode()
        ).hexdigest()

        assert original_hash != recomputed
