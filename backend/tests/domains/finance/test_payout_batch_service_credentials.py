"""Fail-before + paired test for DEFECT-05 (P1 — payout credential attribute).

Before the fix, ``PaymentEngine._load_credentials`` accesses
``record.encrypted_credentials``, which does not exist on the
``CountryGatewayCredentials`` model.  The actual column is ``credentials``
(JSON).  This module demonstrates the AttributeError and verifies the
corrected behavior.

The live SQLite test environment has pre-existing mapper-configuration
failures (broken ``ShippingCarrier`` / ``logistics.shipments`` references
in ``_remove_broken_fk_tables``) that prevent ORM instantiation, so the
paired test exercises the method via a mocked session/record pair.
"""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from domains.finance.services.payouts.payout_batch_service import PaymentEngine


def _make_engine_with_record(record):
    """Build a PaymentEngine whose db returns the supplied record from first()."""
    engine = PaymentEngine.__new__(PaymentEngine)
    engine.db = MagicMock()
    engine.db.query.return_value.filter.return_value.first.return_value = record
    return engine


class TestPaymentEngineLoadCredentials:
    """_load_credentials must read the real ``credentials`` column."""

    def test_load_credentials_raises_attribute_error_before_fix(self) -> None:
        """Fail-before: accessing ``encrypted_credentials`` raises AttributeError."""
        record = MagicMock()
        # Simulate the model state: has `credentials` but NOT `encrypted_credentials`
        record.credentials = None
        del record.encrypted_credentials  # ensure access raises AttributeError
        engine = _make_engine_with_record(record)
        with pytest.raises(AttributeError):
            engine._load_credentials("SA", "stripe", "test")

    def test_load_credentials_returns_dict_after_fix(self) -> None:
        """Paired test: after fix, returns parsed credential dict."""
        stored = {"secret_key": "sk_test_123", "webhook_secret": "whsec_456"}
        record = MagicMock()
        record.credentials = stored
        engine = _make_engine_with_record(record)
        result = engine._load_credentials("SA", "stripe", "test")
        assert result == stored

    def test_load_credentials_returns_empty_when_no_record(self) -> None:
        """Paired test: missing credentials record returns empty dict."""
        engine = _make_engine_with_record(None)
        result = engine._load_credentials("XX", "nonexistent", "test")
        assert result == {}

    def test_load_credentials_returns_empty_when_inactive(self) -> None:
        """Paired test: query filters inactive records, so first() returns None."""
        engine = _make_engine_with_record(None)
        result = engine._load_credentials("AE", "tap", "test")
        assert result == {}
