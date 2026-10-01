"""Paired tests for FILE-48: customer_coupons_create_service.py.

Contract: _audit/resolver/contracts/file-48.md
Findings fixed:
  LOGIC-001 — import at line 13 is commented out → FALSE_POSITIVE (import is active)
  LOGIC-002 — bare except Exception at line 34 uses logger.warning → fixed with logger.exception
"""
from __future__ import annotations

import importlib
import logging
import sys
import types
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# ── Paths ────────────────────────────────────────────────────────────────────

REPO_ROOT = Path(__file__).resolve().parents[3]
SERVICE_PATH = REPO_ROOT / "backend" / "domains" / "promotions" / "services" / "customer_coupons_create_service.py"


# ── Module loader ─────────────────────────────────────────────────────────────

def _load_service():
    """Load the service module from path without triggering cross-domain imports."""
    spec = importlib.util.spec_from_file_location("service", SERVICE_PATH)
    mod = importlib.util.module_from_spec(spec)
    # Stub the governance.ports module before loading
    gov_ports = types.ModuleType("domains.governance.ports")
    gov_ports.list_coupons = lambda db, limit=100: []
    sys.modules["domains.governance.ports"] = gov_ports
    spec.loader.exec_module(mod)
    return mod


# ── Tests ─────────────────────────────────────────────────────────────────────


class TestDeleteCoupon:
    """Tests for delete_coupon function."""

    def test_delete_coupon_returns_not_found_when_coupon_missing(self):
        """When coupon is not found, returns deleted=False with note."""
        service = _load_service()
        db = MagicMock()
        with patch.object(service, "list_coupons", return_value=[]):
            result = service.delete_coupon(db, coupon_id=999)
        assert result["deleted"] is False
        assert "not found" in result.get("note", "")

    def test_delete_coupon_deactivates_existing_coupon(self):
        """When coupon exists and is_active, sets is_active=False and flushes."""
        service = _load_service()
        db = MagicMock()
        coupon = MagicMock()
        coupon.id = 1
        coupon.is_active = True
        with patch.object(service, "list_coupons", return_value=[coupon]):
            result = service.delete_coupon(db, coupon_id=1)
        assert result["deleted"] is True
        assert coupon.is_active is False
        db.flush.assert_called_once()

    def test_delete_coupon_logs_exception_on_failure(self):
        """When an exception occurs, logger.exception is called with traceback."""
        service = _load_service()
        db = MagicMock()
        exc = Exception("db error")
        with patch.object(service, "list_coupons", side_effect=exc):
            with patch.object(service.logger, "exception") as mock_exc:
                result = service.delete_coupon(db, coupon_id=1)
        assert result["deleted"] is False
        assert "db error" in result.get("error", "")
        mock_exc.assert_called_once()


# ── Import verification ────────────────────────────────────────────────────────


class TestImports:
    """Verify import at line 13 is active."""

    def test_list_coupons_import_is_active(self):
        """The import at line 13 should be uncommented and working."""
        source = SERVICE_PATH.read_text(encoding="utf-8")
        lines = source.splitlines()
        line_13 = lines[12].strip()
        assert line_13 == "from domains.governance.ports import list_coupons"
        assert not line_13.startswith("#")
