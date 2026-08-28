"""Security domain — law-aligned architecture tests.

Maps to ARCHITECTURE_DIAGRAM.md Laws:
  Law 1   : arrows point down only
  Law 3   : events/ports wiring
  Law 4   : features single-sourced
  Laws 6/23/55/152 : schema discipline
  Laws 22/52 : FK ondelete
  Law 32  : no hardcoded secrets
  Law 33  : JWT type-claim verification
  Law 38  : password handling rejects >72 bytes
  Law 43  : security event logging
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

DOMAIN = "security"


def _security_models():
    return list(iter_domain_models(DOMAIN))


# Models missing required audit columns (Law 23/229).
KNOWN_SCHEMA_VIOLATIONS = {
    "FraudEvent",
    "FraudBlacklist",
    "ManualReviewQueue",
    "DeviceFingerprint",
    "CreditCardBin",
    "ReturnAbusePattern",
    "SupplierFraudIndicator",
    "LogisticsFraudIndicator",
    "FraudAlert",
    "IPAccountLinkage",
    "VelocityCounter",
    "FraudScoringLog",
    "FraudCaseAssignment",
    "DLPViolation",
    "MeetingTranscript",
    "MeetingActionItem",
    "MeetingRecording",
}

# Models whose country_code FK lacks ondelete (Law 22/52).
KNOWN_FK_VIOLATIONS = {
    "AlertEscalationRule",
    "DocumentVerification",
    "KYCVerification",
}


class TestSecuritySchemaDiscipline:
    """Laws 6/23/55/152 — schema + audit columns."""

    @pytest.mark.parametrize("model", _security_models(), ids=lambda m: m.__name__)
    def test_model_schema_discipline(self, model):
        if model.__name__ in KNOWN_SCHEMA_VIOLATIONS:
            pytest.xfail(f"{model.__name__}: missing audit columns (Law 23/229)")
        assert_schema_discipline(model)


class TestSecurityForeignKeyOndelete:
    """Laws 22/52 — every ForeignKey declares explicit ondelete."""

    @pytest.mark.parametrize("model", _security_models(), ids=lambda m: m.__name__)
    def test_foreign_keys_have_ondelete(self, model):
        if model.__name__ in KNOWN_FK_VIOLATIONS:
            pytest.xfail(
                f"{model.__name__}: country_code FK missing ondelete (Law 22/52)"
            )
        assert_foreign_keys_have_ondelete(model)


class TestSecurityFeaturesSingleSourced:
    """Law 4 — feature atoms single-sourced + in rbac catalog."""

    def test_features_declared(self):
        from domains.security.features import FEATURES

        assert isinstance(FEATURES, dict)
        assert len(FEATURES) > 0

    @pytest.mark.parametrize(
        "feature",
        [
            "security.read",
            "security.events.read",
            "security.events.manage",
            "security.sessions.read",
            "security.sessions.manage",
            "security.mfa.manage",
            "security.api_keys.read",
            "security.api_keys.manage",
            "security.policies.read",
            "security.policies.manage",
            "security.incident.read",
            "security.incident.manage",
            "fraud.detection.view",
            "fraud.detection.manage",
            "fraud.investigation",
            "threat.monitoring.view",
            "threat.monitoring.manage",
            "threat.response",
        ],
    )
    def test_feature_in_catalog(self, feature):
        assert_feature_in_catalog(feature)


class TestSecurityEventsAndPortsWired:
    """Law 3 — cross-domain writes via events.py, reads via ports.py."""

    def test_events_module_has_security_events(self):
        from domains.security import events

        assert hasattr(events, "EVENT_THREAT_DETECTED")
        assert hasattr(events, "EVENT_DOCUMENT_VERIFIED")
        assert hasattr(events, "EVENT_KYC_COMPLETED")
        assert hasattr(events, "EVENT_FRAUD_ALERT")

    def test_events_has_publish_helpers(self):
        from domains.security import events

        assert callable(events.publish_threat_detected)
        assert callable(events.publish_fraud_alert)

    def test_ports_module_has_read_functions(self):
        from domains.security import ports

        assert callable(ports.get_document_verification_by_id)
        assert callable(ports.get_k_y_c_verification_by_id)
        assert callable(ports.get_alert_escalation_rule_by_id)

    def test_subscribers_have_handlers(self):
        from domains.security import subscribers

        assert callable(subscribers._on_order_created)
        assert callable(subscribers._on_user_login)
        assert callable(subscribers.register_security_subscribers)


class TestSecurityImportLaws:
    """Law 1 — arrows point down only."""

    def test_no_forbidden_imports_in_domain(self):
        source_dir = BACKEND_ROOT / "domains" / DOMAIN
        assert_no_forbidden_imports("domains", source_dir)


# ---------------------------------------------------------------------------
# Law 38 — password handling rejects >72 bytes
# ---------------------------------------------------------------------------
class TestSecurityPasswordHandling:
    """Law 38 — bcrypt password handling must reject passwords >72 bytes."""

    def test_get_password_hash_rejects_long_passwords(self):
        """bcrypt silently truncates >72-byte inputs; our wrapper must reject them."""
        from infrastructure.utils.auth import get_password_hash

        long_password = "a" * 73
        with pytest.raises(ValueError, match="72"):
            get_password_hash(long_password)

    def test_get_password_hash_accepts_valid_password(self):
        from infrastructure.utils.auth import get_password_hash

        hashed = get_password_hash("ValidP@ss1")
        assert hashed is not None
        assert len(hashed) > 0

    def test_hash_password_alias_rejects_long(self):
        """hash_password is an alias of get_password_hash — same contract."""
        from infrastructure.utils.auth import hash_password

        with pytest.raises(ValueError, match="72"):
            hash_password("a" * 73)


# ---------------------------------------------------------------------------
# Law 33 — JWT type-claim verification
# ---------------------------------------------------------------------------
class TestSecurityJwtTypeClaim:
    """Law 33 — JWT tokens must carry and verify a type claim."""

    def test_access_token_has_type_claim(self):
        from infrastructure.utils.auth import create_access_token, decode_token

        token = create_access_token(data={"sub": "1"})
        payload = decode_token(token, check_blacklist=False)
        assert payload.get("type") == "access"

    def test_refresh_token_has_type_claim(self):
        from infrastructure.utils.auth import create_refresh_token, decode_token

        token = create_refresh_token(data={"sub": "1"})
        payload = decode_token(token, check_blacklist=False)
        assert payload.get("type") == "refresh"

    def test_verify_token_rejects_wrong_type(self):
        """verify_token must reject a refresh token (wrong type)."""
        from infrastructure.utils.auth import (
            create_refresh_token,
            verify_token,
        )
        from fastapi import HTTPException

        refresh_tok = create_refresh_token(data={"sub": "1"})
        with pytest.raises(HTTPException):
            verify_token(refresh_tok)

    def test_verify_token_accepts_access_token(self):
        from infrastructure.utils.auth import create_access_token, verify_token

        token = create_access_token(data={"sub": "42"})
        subject = verify_token(token)
        assert subject == "42"


# ---------------------------------------------------------------------------
# Law 32 — no hardcoded secrets
# ---------------------------------------------------------------------------
class TestSecurityNoHardcodedSecrets:
    """Law 32 — no hardcoded secrets in security-sensitive source files."""

    _SECRET_PATTERN = (
        r"(?i)\b(api[_-]?key|apikey|secret|secret[_-]?key|token|auth[_-]?token|"
        r"access[_-]?token|password|passwd|pwd)\b\s*[:=]\s*['\"][^'\"]{12,}['\"]"
    )

    @pytest.mark.parametrize(
        "rel_path",
        [
            "infrastructure/utils/auth.py",
            "infrastructure/utils/config.py",
            "domains/security/services/core/security_service.py",
            "domains/security/services/iam/iam_service.py",
        ],
    )
    def test_no_hardcoded_secret_in_source(self, rel_path):
        import re
        from pathlib import Path

        path = BACKEND_ROOT / rel_path
        if not path.exists():
            pytest.skip(f"{rel_path} does not exist")
        text = path.read_text(encoding="utf-8")
        match = re.search(self._SECRET_PATTERN, text)
        assert match is None, f"Hardcoded secret in {rel_path}: {match.group(0)!r}"


# ---------------------------------------------------------------------------
# Law 43 — security event logging
# ---------------------------------------------------------------------------
class TestSecurityEventLogging:
    """Law 43 — security-relevant actions emit events."""

    def test_threat_detected_publishes_event(self):
        from domains.security.events import publish_threat_detected

        # Should not raise even without a real event bus.
        publish_threat_detected("brute_force", "high", actor_id=1)

    def test_fraud_alert_publishes_event(self):
        from domains.security.events import publish_fraud_alert

        publish_fraud_alert(alert_id=1, order_id=1, risk_score=0.95)

    def test_kyc_completed_publishes_event(self):
        from domains.security.events import publish_kyc_completed

        publish_kyc_completed(user_id=1, status="approved")
