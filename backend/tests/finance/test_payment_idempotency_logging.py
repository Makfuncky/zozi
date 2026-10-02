"""Regression tests for LOGIC-004: idempotency helpers must log on Valkey failure."""
from __future__ import annotations

import logging
from unittest.mock import MagicMock, patch

import pytest

from domains.finance.services.payments.payment_engine import (
    _check_payment_idempotency_key,
    _store_payment_idempotency_result,
)


def test_check_payment_idempotency_key_logs_on_valkey_failure(caplog: pytest.LogCaptureFixture) -> None:
    """When Valkey raises during idempotency check, the exception is logged and None is returned."""
    fake_valkey = MagicMock()
    fake_valkey.get = MagicMock(side_effect=RuntimeError("valkey down"))
    with patch("domains.finance.services.payments.payment_engine.get_valkey_client", return_value=fake_valkey):
        with caplog.at_level(logging.DEBUG):
            result = _check_payment_idempotency_key("test_key")
    assert result is None
    assert "Idempotency key check failed for test_key" in caplog.text


def test_store_payment_idempotency_result_logs_on_valkey_failure(caplog: pytest.LogCaptureFixture) -> None:
    """When Valkey raises during idempotency store, the exception is logged."""
    fake_valkey = MagicMock()
    fake_valkey.setex = MagicMock(side_effect=RuntimeError("valkey down"))
    with patch("domains.finance.services.payments.payment_engine.get_valkey_client", return_value=fake_valkey):
        with caplog.at_level(logging.WARNING):
            _store_payment_idempotency_result("test_key", {"status": "completed"})
    assert "Idempotency result store failed for test_key" in caplog.text


def test_check_payment_idempotency_key_returns_none_when_valkey_missing() -> None:
    """When no Valkey client is available, return None without logging."""
    with patch("domains.finance.services.payments.payment_engine.get_valkey_client", return_value=None):
        result = _check_payment_idempotency_key("test_key")
    assert result is None


def test_store_payment_idempotency_result_noop_when_valkey_missing() -> None:
    """When no Valkey client is available, store is a no-op without logging."""
    with patch("domains.finance.services.payments.payment_engine.get_valkey_client", return_value=None):
        _store_payment_idempotency_result("test_key", {"status": "completed"})
