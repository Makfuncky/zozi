"""Law regression and WORM column backfill tests for worm_audit.py.

TST-060 — security/logic regression tests for the WORM audit service.
"""
from __future__ import annotations

import ast
import hashlib
import pathlib
from unittest.mock import MagicMock, patch

import pytest

from domains.audit.services.worm_audit import WORMAuditService
from domains.audit.models.audit_schema_models import AuditLog


_WORM_AUDIT_PATH = (
    pathlib.Path(__file__).resolve().parent.parent.parent.parent
    / "domains"
    / "audit"
    / "services"
    / "worm_audit.py"
)

_GENESIS_HASH = hashlib.sha256("genesis".encode()).hexdigest()


class TestLaw34WormAuditNoFStringSQL:
    """Law 34: worm_audit.py must not use f-string interpolation in SQL."""

    def test_no_fstring_sql_in_worm_audit(self):
        src = _WORM_AUDIT_PATH.read_text(encoding="utf-8")
        tree = ast.parse(src)
        offenders: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func = node.func
                func_name = ""
                if isinstance(func, ast.Attribute):
                    func_name = func.attr
                elif isinstance(func, ast.Name):
                    func_name = func.id
                if func_name in {"execute", "text"}:
                    for arg in node.args:
                        if isinstance(arg, ast.JoinedStr):
                            offenders.append(
                                f"f-string SQL at line {arg.lineno}"
                            )
                            break
        assert not offenders, "Law 34 violation in worm_audit.py: " + "; ".join(offenders)


class TestLaw92WormAuditStructlogLogger:
    """Law 92: worm_audit.py must use structlog, not stdlib logging."""

    def test_logger_is_structlog(self):
        import domains.audit.services.worm_audit as mod
        assert hasattr(mod, "logger"), "worm_audit module has no logger attribute"
        logger = mod.logger
        assert type(logger).__name__ == "BoundLoggerLazyProxy", (
            f"worm_audit logger is {type(logger).__name__}, not structlog"
        )

    def test_no_stdlib_logging_import(self):
        src = _WORM_AUDIT_PATH.read_text(encoding="utf-8")
        tree = ast.parse(src)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name == "logging":
                        pytest.fail("stdlib logging imported in worm_audit.py")
            elif isinstance(node, ast.ImportFrom):
                if node.module == "logging":
                    pytest.fail("stdlib logging imported in worm_audit.py")


class TestWORMHashColumns:
    """Finding 3: AuditLog ORM must map worm_hash columns and append() must
    populate them. Read path must serve both column-first and details-fallback."""

    def test_model_declares_worm_hash_columns(self):
        assert hasattr(AuditLog, "worm_hash"), "AuditLog missing worm_hash column"
        assert hasattr(AuditLog, "worm_prev_hash"), "AuditLog missing worm_prev_hash column"

    def test_append_populates_columns_and_details(self):
        mock_record = MagicMock()
        mock_record.id = 1
        mock_record.action = "test.action"
        mock_record.entity_type = "test_entity"
        mock_record.user_id = 1
        mock_record.username = "test_user"
        mock_record.details = {"key": "value"}

        db_session = MagicMock()
        db_session.execute.return_value.scalar.return_value = 1

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

        assert record.worm_hash is not None
        assert record.worm_prev_hash == "fixed_hash"
        sealed = dict(record.details or {})
        assert "worm_hash" in sealed
        assert "worm_prev_hash" in sealed

    def test_get_chain_tail_hash_prefers_column(self):
        mock_record = MagicMock()
        mock_record.id = 1
        mock_record.worm_hash = "col_hash"
        mock_record.details = {"worm_hash": "details_hash"}

        db_session = MagicMock()
        db_session.query.return_value.order_by.return_value.all.return_value = [mock_record]

        service = WORMAuditService(db_session)
        tail = service._get_chain_tail_hash()
        assert tail == "col_hash"

    def test_get_chain_tail_hash_falls_back_to_details(self):
        mock_record = MagicMock()
        mock_record.id = 1
        mock_record.worm_hash = None
        mock_record.details = {"worm_hash": "details_hash"}

        db_session = MagicMock()
        db_session.query.return_value.order_by.return_value.all.return_value = [mock_record]

        service = WORMAuditService(db_session)
        tail = service._get_chain_tail_hash()
        assert tail == "details_hash"

    def test_get_chain_integrity_mixed_vintage(self):
        first = MagicMock()
        first.id = 1
        first.action = "a"
        first.entity_type = "e"
        first.entity_id = 1
        first.created_at = None
        first.worm_hash = None
        first.worm_prev_hash = None
        first.details = {"worm_hash": "valid_hash", "worm_prev_hash": _GENESIS_HASH}

        second = MagicMock()
        second.id = 2
        second.action = "b"
        second.entity_type = "e"
        second.entity_id = 2
        second.created_at = None
        second.worm_hash = "valid_hash"
        second.worm_prev_hash = "valid_hash"
        second.details = {}

        db_session = MagicMock()
        db_session.query.return_value.order_by.return_value.all.return_value = [
            first, second
        ]

        with patch.object(
            WORMAuditService, "_compute_record_hash", return_value="record_hash"
        ), patch.object(
            WORMAuditService,
            "_compute_chain_hash_for",
            return_value="valid_hash",
        ):
            service = WORMAuditService(db_session)
            service._last_hash = "valid_hash"
            integrity = service.get_chain_integrity()
            assert integrity["chain_valid"] is True
            assert integrity["total_records"] == 2


class TestWORMChainIntegrityBehavior:
    """Outcome, error-path, and concurrency cases for chain integrity."""

    def test_intact_chain_reports_valid(self):
        first = MagicMock()
        first.id = 1
        first.action = "a"
        first.entity_type = "e"
        first.entity_id = 1
        first.created_at = None
        first.worm_hash = "valid_hash"
        first.worm_prev_hash = _GENESIS_HASH
        first.details = {}

        second = MagicMock()
        second.id = 2
        second.action = "b"
        second.entity_type = "e"
        second.entity_id = 2
        second.created_at = None
        second.worm_hash = "valid_hash"
        second.worm_prev_hash = "valid_hash"
        second.details = {}

        db_session = MagicMock()
        db_session.query.return_value.order_by.return_value.all.return_value = [
            first, second
        ]

        with patch.object(
            WORMAuditService, "_compute_record_hash", return_value="record_hash"
        ), patch.object(
            WORMAuditService,
            "_compute_chain_hash_for",
            return_value="valid_hash",
        ):
            service = WORMAuditService(db_session)
            service._last_hash = "valid_hash"
            integrity = service.get_chain_integrity()
            assert integrity["chain_valid"] is True
            assert integrity["total_records"] == 2
            assert integrity["first_break"] is None

    def test_tampered_chain_reports_break(self):
        first = MagicMock()
        first.id = 1
        first.action = "a"
        first.entity_type = "e"
        first.entity_id = 1
        first.created_at = None
        first.worm_hash = "tampered"
        first.worm_prev_hash = _GENESIS_HASH
        first.details = {}

        db_session = MagicMock()
        db_session.query.return_value.order_by.return_value.all.return_value = [first]

        with patch.object(
            WORMAuditService, "_compute_record_hash", return_value="record_hash"
        ), patch.object(
            WORMAuditService,
            "_compute_chain_hash",
            return_value="expected_chain",
        ):
            service = WORMAuditService(db_session)
            integrity = service.get_chain_integrity()
            assert integrity["chain_valid"] is False
            assert integrity["first_break"] is not None
            assert integrity["first_break"]["record_id"] == 1

    def test_concurrent_appends_do_not_share_id(self):
        db_session = MagicMock()
        db_session.execute.return_value.scalar.side_effect = [100, 101]

        with patch.object(
            WORMAuditService, "_get_chain_tail_hash", return_value=_GENESIS_HASH
        ), patch(
            "domains.audit.services.worm_audit.AuditLog"
        ) as mock_audit_log:
            mock_records = [MagicMock(), MagicMock()]
            mock_records[0].id = 100
            mock_records[0].action = "c1"
            mock_records[0].entity_type = "e"
            mock_records[0].entity_id = 1
            mock_records[0].created_at = None
            mock_records[1].id = 101
            mock_records[1].action = "c2"
            mock_records[1].entity_type = "e"
            mock_records[1].entity_id = 2
            mock_records[1].created_at = None
            mock_audit_log.side_effect = mock_records
            service = WORMAuditService(db_session)
            r1 = service.append(action="c1", entity_type="e", entity_id=1)
            r2 = service.append(action="c2", entity_type="e", entity_id=2)

        assert r1.id == 100
        assert r2.id == 101
        assert r1.worm_hash != r2.worm_hash

        db_session.query.return_value.order_by.return_value.all.return_value = [r1, r2]

        service._last_hash = r2.worm_hash
        integrity = service.get_chain_integrity()
        assert integrity["chain_valid"] is True
        assert integrity["total_records"] == 2
