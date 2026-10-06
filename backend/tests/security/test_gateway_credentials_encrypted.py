"""Fail-before + paired tests for PROV-001 fix (P1 — payment gateway credentials in plaintext).

Law 275: AES-256-GCM encryption at rest via EncryptedString TypeDecorator.
Law 313: PCI-DSS compliance — API keys encrypted at rest.
§10.1 Key Rule 1: Payment gateway secrets NEVER stored in plaintext.

Run: pytest backend/tests/security/test_gateway_credentials_encrypted.py -v
"""
from __future__ import annotations

import os
import sys

_BACKEND_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _BACKEND_ROOT not in sys.path:
    sys.path.insert(0, _BACKEND_ROOT)

# FIELD_ENCRYPTION_KEY must be set before any module that imports
# infrastructure.security.encryption is loaded (field_encryptor is created at
# module-import time from the env var).
os.environ.setdefault("FIELD_ENCRYPTION_KEY", "x" * 64)
os.environ.setdefault("FIELD_ENCRYPTION_SALT", "a" * 64)

from sqlalchemy import text
from sqlalchemy.orm import Session

from domains.finance.models.payments import PaymentGatewayConnection
from infrastructure.security.encryption import EncryptedString, _ENCRYPTED_PREFIX


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_TEST_SECRET = "sk_test_plaintext_secret_value_12345"
_TEST_WEBHOOK = "whsec_test_plaintext_webhook_value_67890"


def _col_type(model, col_name):
    """Return the SQLAlchemy type object for a named column."""
    return model.__table__.c[col_name].type


# ---------------------------------------------------------------------------
# Fail-before: column must not be plain String
# ---------------------------------------------------------------------------

class TestColumnIsNotPlainString:
    """FAILS before fix: secret_key and webhook_secret are bare String(1000).
    PASSES after fix: both columns are EncryptedString."""

    def test_secret_key_column_is_encrypted_string(self):
        assert isinstance(
            _col_type(PaymentGatewayConnection, "secret_key"), EncryptedString
        ), (
            f"secret_key column type is {type(_col_type(PaymentGatewayConnection, 'secret_key'))!r}; "
            "expected EncryptedString per Law 275 / Law 313 / §10.1 Key Rule 1"
        )

    def test_webhook_secret_column_is_encrypted_string(self):
        assert isinstance(
            _col_type(PaymentGatewayConnection, "webhook_secret"), EncryptedString
        ), (
            f"webhook_secret column type is {type(_col_type(PaymentGatewayConnection, 'webhook_secret'))!r}; "
            "expected EncryptedString per Law 275 / Law 313 / §10.1 Key Rule 1"
        )


# ---------------------------------------------------------------------------
# Paired: save then read back (ORM round-trip)
# ---------------------------------------------------------------------------

class TestOrmRoundTrip:
    """Encrypt on write, transparently decrypt on read."""

    def test_secret_key_round_trip_via_orm(self, db_session: Session):
        record = PaymentGatewayConnection(
            provider_code="stripe",
            gateway_name="Stripe Test",
            country_code=None,
            environment="test",
            provider_kind="custom",
            display_name="Stripe Test",
            is_enabled=True,
            secret_key=_TEST_SECRET,
            webhook_secret=_TEST_WEBHOOK,
        )
        db_session.add(record)
        db_session.flush()

        fetched = (
            db_session.query(PaymentGatewayConnection)
            .filter_by(id=record.id)
            .first()
        )
        assert fetched is not None
        assert fetched.secret_key == _TEST_SECRET, (
            f"ORM round-trip failed: {fetched.secret_key!r} != {_TEST_SECRET!r}"
        )

    def test_webhook_secret_round_trip_via_orm(self, db_session: Session):
        record = PaymentGatewayConnection(
            provider_code="stripe",
            gateway_name="Stripe Test",
            country_code=None,
            environment="test",
            provider_kind="custom",
            display_name="Stripe Test",
            is_enabled=True,
            secret_key=_TEST_SECRET,
            webhook_secret=_TEST_WEBHOOK,
        )
        db_session.add(record)
        db_session.flush()

        fetched = (
            db_session.query(PaymentGatewayConnection)
            .filter_by(id=record.id)
            .first()
        )
        assert fetched is not None
        assert fetched.webhook_secret == _TEST_WEBHOOK, (
            f"ORM round-trip failed: {fetched.webhook_secret!r} != {_TEST_WEBHOOK!r}"
        )


# ---------------------------------------------------------------------------
# Paired: raw column value is NOT plaintext (the actual P1 check)
# ---------------------------------------------------------------------------

class TestNotPlaintextAtRest:
    """After save, the raw DB column value must not equal the plaintext secret."""

    def test_secret_key_not_plaintext_in_raw_column(self, db_session: Session):
        record = PaymentGatewayConnection(
            provider_code="stripe",
            gateway_name="Stripe Test",
            country_code=None,
            environment="test",
            provider_kind="custom",
            display_name="Stripe Test",
            is_enabled=True,
            secret_key=_TEST_SECRET,
        )
        db_session.add(record)
        db_session.flush()

        raw = db_session.execute(
            text("SELECT secret_key FROM payment_gateway_connections WHERE id = :id"),
            {"id": record.id},
        ).scalar_one_or_none()

        assert raw is not None, "Row not found after flush"
        assert raw != _TEST_SECRET, (
            f"P1 DEFECT: secret_key stored as plaintext in DB: {raw!r}"
        )
        assert raw.startswith(_ENCRYPTED_PREFIX), (
            f"Expected enc:: prefix, got: {raw!r}"
        )

    def test_webhook_secret_not_plaintext_in_raw_column(self, db_session: Session):
        record = PaymentGatewayConnection(
            provider_code="stripe",
            gateway_name="Stripe Test",
            country_code=None,
            environment="test",
            provider_kind="custom",
            display_name="Stripe Test",
            is_enabled=True,
            webhook_secret=_TEST_WEBHOOK,
        )
        db_session.add(record)
        db_session.flush()

        raw = db_session.execute(
            text("SELECT webhook_secret FROM payment_gateway_connections WHERE id = :id"),
            {"id": record.id},
        ).scalar_one_or_none()

        assert raw is not None, "Row not found after flush"
        assert raw != _TEST_WEBHOOK, (
            f"P1 DEFECT: webhook_secret stored as plaintext in DB: {raw!r}"
        )
        assert raw.startswith(_ENCRYPTED_PREFIX), (
            f"Expected enc:: prefix, got: {raw!r}"
        )


# ---------------------------------------------------------------------------
# Paired: legacy plaintext row still readable (backward compat)
# ---------------------------------------------------------------------------

class TestLegacyPlaintextBackwardCompatibility:
    """Rows with plaintext values (pre-migration) must still decrypt correctly."""

    def test_legacy_plaintext_secret_key_still_readable(self, db_session: Session):
        record = PaymentGatewayConnection(
            provider_code="tap",
            gateway_name="Tap Legacy",
            country_code=None,
            environment="test",
            provider_kind="custom",
            display_name="Tap Legacy",
            is_enabled=True,
            secret_key="legacy_plaintext_secret_abc",
            webhook_secret=None,
        )
        db_session.add(record)
        db_session.flush()

        db_session.execute(
            text(
                f"UPDATE {_TABLE_FCN()} SET secret_key = :sk WHERE id = :id"
            ),
            {"sk": "legacy_plaintext_secret_abc", "id": record.id},
        )
        db_session.flush()

        fetched = (
            db_session.query(PaymentGatewayConnection)
            .filter_by(id=record.id)
            .first()
        )
        assert fetched is not None
        assert fetched.secret_key == "legacy_plaintext_secret_abc", (
            f"Legacy plaintext not readable: {fetched.secret_key!r}"
        )

    def test_legacy_plaintext_webhook_secret_still_readable(self, db_session: Session):
        record = PaymentGatewayConnection(
            provider_code="thawani",
            gateway_name="Thawani Legacy",
            country_code=None,
            environment="test",
            provider_kind="custom",
            display_name="Thawani Legacy",
            is_enabled=True,
            secret_key=None,
            webhook_secret="legacy_plaintext_webhook_xyz",
        )
        db_session.add(record)
        db_session.flush()

        db_session.execute(
            text(
                f"UPDATE {_TABLE_FCN()} SET webhook_secret = :whs WHERE id = :id"
            ),
            {"whs": "legacy_plaintext_webhook_xyz", "id": record.id},
        )
        db_session.flush()

        fetched = (
            db_session.query(PaymentGatewayConnection)
            .filter_by(id=record.id)
            .first()
        )
        assert fetched is not None
        assert fetched.webhook_secret == "legacy_plaintext_webhook_xyz", (
            f"Legacy plaintext webhook not readable: {fetched.webhook_secret!r}"
        )


def _TABLE_FCN():
    """Fully-qualified table name for raw SQL (no schema in test SQLite)."""
    return "payment_gateway_connections"


# ---------------------------------------------------------------------------
# Paired: None / empty stays None / empty
# ---------------------------------------------------------------------------

class TestNoneAndEmptyPassthrough:
    """None and empty string must survive the encrypt/decrypt cycle unchanged."""

    def test_none_secret_key_stays_none(self, db_session: Session):
        record = PaymentGatewayConnection(
            provider_code="paypal",
            gateway_name="PayPal None Test",
            country_code=None,
            environment="test",
            provider_kind="custom",
            display_name="PayPal None Test",
            is_enabled=True,
            secret_key=None,
            webhook_secret=None,
        )
        db_session.add(record)
        db_session.flush()

        fetched = (
            db_session.query(PaymentGatewayConnection)
            .filter_by(id=record.id)
            .first()
        )
        assert fetched is not None
        assert fetched.secret_key is None
        assert fetched.webhook_secret is None

    def test_empty_string_secret_key_stays_empty(self, db_session: Session):
        record = PaymentGatewayConnection(
            provider_code="paypal",
            gateway_name="PayPal Empty Test",
            country_code=None,
            environment="test",
            provider_kind="custom",
            display_name="PayPal Empty Test",
            is_enabled=True,
            secret_key="",
            webhook_secret="",
        )
        db_session.add(record)
        db_session.flush()

        fetched = (
            db_session.query(PaymentGatewayConnection)
            .filter_by(id=record.id)
            .first()
        )
        assert fetched is not None
        assert fetched.secret_key == ""
        assert fetched.webhook_secret == ""


# ---------------------------------------------------------------------------
# Paired: webhook / auth-header read path still works
# ---------------------------------------------------------------------------

class TestConsumerReadPathsStillWork:
    """The webhook handler does getattr(record, 'webhook_secret', None).
    The auth-header path does getattr(record, 'secret_key', None).
    After EncryptedString, the ORM returns decrypted plaintext — same as before."""

    def test_webhook_secret_getattr_after_round_trip(self, db_session: Session):
        record = PaymentGatewayConnection(
            provider_code="paytabs",
            gateway_name="PayTabs Webhook Test",
            country_code=None,
            environment="test",
            provider_kind="custom",
            display_name="PayTabs Webhook Test",
            is_enabled=True,
            webhook_secret=_TEST_WEBHOOK,
        )
        db_session.add(record)
        db_session.flush()

        fetched = (
            db_session.query(PaymentGatewayConnection)
            .filter_by(id=record.id)
            .first()
        )
        assert fetched is not None

        retrieved = getattr(fetched, "webhook_secret", None)
        assert retrieved == _TEST_WEBHOOK, (
            f"Webhook path broken: getattr returned {retrieved!r}, "
            f"expected {_TEST_WEBHOOK!r}"
        )

    def test_secret_key_getattr_after_round_trip(self, db_session: Session):
        record = PaymentGatewayConnection(
            provider_code="stripe",
            gateway_name="Stripe Auth Test",
            country_code=None,
            environment="test",
            provider_kind="custom",
            display_name="Stripe Auth Test",
            is_enabled=True,
            secret_key=_TEST_SECRET,
        )
        db_session.add(record)
        db_session.flush()

        fetched = (
            db_session.query(PaymentGatewayConnection)
            .filter_by(id=record.id)
            .first()
        )
        assert fetched is not None

        retrieved = getattr(fetched, "secret_key", None)
        assert retrieved == _TEST_SECRET, (
            f"Auth-header path broken: getattr returned {retrieved!r}, "
            f"expected {_TEST_SECRET!r}"
        )
