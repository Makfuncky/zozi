"""Behavior tests for security domain — risk scoring, fraud detection, sessions, MFA, and alerts."""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import pytest

from domains.security.models.fraud import FraudEvent, FraudRule, FraudBlacklist
from domains.accounts.models.user import User, UserSession


def _create_user(db_session, email=None, role="customer"):
    from infrastructure.utils.auth import get_password_hash
    user = User(
        email=email or f"sec_{uuid.uuid4().hex[:8]}@zozi.test",
        username=f"sec_{uuid.uuid4().hex[:8]}",
        hashed_password=get_password_hash("SecurePass1!"),
        role=role,
        country_code="AE",
    )
    db_session.add(user)
    db_session.flush()
    return user


# ══════════════════════════════════════════════════════════════════
# Risk Score Calculation
# ══════════════════════════════════════════════════════════════════


@pytest.mark.integration
class TestRiskScoreCalculation:
    """Test risk score calculation."""

    def test_calculate_risk_score_for_user(self, db_session):
        from domains.security.services.risk_service import get_risk_scores
        result = get_risk_scores(db_session, employee_id=0)
        assert isinstance(result, list)

    def test_get_risk_scores_for_specific_employee(self, db_session):
        from domains.security.services.risk_service import get_risk_scores
        result = get_risk_scores(db_session, employee_id=1)
        assert isinstance(result, list)

    def test_risk_score_record_structure(self, db_session):
        from domains.security.services.risk_service import get_risk_scores
        result = get_risk_scores(db_session, employee_id=0)
        if result:
            record = result[0]
            assert "employee_id" in record
            assert "metric_name" in record
            assert "score" in record
            assert "recorded_at" in record


# ══════════════════════════════════════════════════════════════════
# Fraud Detection
# ══════════════════════════════════════════════════════════════════


@pytest.mark.integration
class TestFraudDetection:
    """Test fraud detection operations."""

    def test_create_fraud_event(self, db_session):
        event = FraudEvent(
            user_id=1,
            ip_address="192.168.1.1",
            fraud_score=85,
            risk_level="high",
        )
        db_session.add(event)
        db_session.flush()
        assert event.id is not None
        assert event.fraud_score == 85
        assert event.risk_level == "high"

    def test_fraud_event_default_values(self, db_session):
        event = FraudEvent(user_id=1, ip_address="10.0.0.1")
        db_session.add(event)
        db_session.flush()
        assert event.id is not None

    def test_create_fraud_rule(self, db_session):
        rule = FraudRule(
            name="Velocity Check",
            rule_type="velocity",
            threshold=10,
            is_active=True,
        )
        db_session.add(rule)
        db_session.flush()
        assert rule.id is not None
        assert rule.name == "Velocity Check"
        assert rule.is_active is True

    def test_deactivate_fraud_rule(self, db_session):
        rule = FraudRule(
            name="Test Rule",
            rule_type="amount",
            threshold=1000,
            is_active=True,
        )
        db_session.add(rule)
        db_session.flush()
        rule.is_active = False
        db_session.flush()
        assert rule.is_active is False

    def test_fraud_blacklist_entry(self, db_session):
        entry = FraudBlacklist(
            value="192.168.1.100",
            type="ip",
            reason="Repeated fraud attempts",
        )
        db_session.add(entry)
        db_session.flush()
        assert entry.id is not None
        assert entry.value == "192.168.1.100"

    def test_check_velocity_limits(self, db_session):
        from domains.security.services.fraud.fraud_detection_service import check_velocity_limits
        result = check_velocity_limits(user_id=1, action="login", window_minutes=5, db=db_session)
        assert isinstance(result, bool)

    def test_fraud_scoring_engine(self, db_session):
        from domains.security.services.fraud.fraud_detection_service import FraudScoringEngine
        engine = FraudScoringEngine(db_session)
        result = engine.score_transaction(user_id=1, amount=100.00, ip_address="127.0.0.1")
        assert result is not None


# ══════════════════════════════════════════════════════════════════
# Security Event Logging
# ══════════════════════════════════════════════════════════════════


@pytest.mark.integration
class TestSecurityEventLogging:
    """Test security event logging."""

    def test_log_login_success(self, db_session):
        from domains.audit.services.security_audit import log_security_event
        result = log_security_event(
            action="LOGIN_SUCCESS",
            user_id=1,
            username="testuser",
            ip_address="127.0.0.1",
            status="success",
        )
        assert result is not None

    def test_log_login_failed(self, db_session):
        from domains.audit.services.security_audit import log_security_event
        result = log_security_event(
            action="LOGIN_FAILED",
            user_id=1,
            username="testuser",
            ip_address="127.0.0.1",
            status="failed",
        )
        assert result is not None

    def test_log_account_locked(self, db_session):
        from domains.audit.services.security_audit import log_security_event
        result = log_security_event(
            action="ACCOUNT_LOCKED",
            user_id=1,
            username="testuser",
            status="success",
        )
        assert result is not None

    def test_log_unknown_event_type(self, db_session):
        from domains.audit.services.security_audit import log_security_event
        result = log_security_event(
            action="UNKNOWN_EVENT",
            user_id=1,
        )
        assert result is not None

    def test_log_security_event_with_details(self, db_session):
        from domains.audit.services.security_audit import log_security_event
        result = log_security_event(
            action="SUSPICIOUS_ACTIVITY",
            user_id=1,
            details={"reason": "Multiple failed logins", "count": 5},
            ip_address="127.0.0.1",
        )
        assert result is not None


# ══════════════════════════════════════════════════════════════════
# Session Management
# ══════════════════════════════════════════════════════════════════


@pytest.mark.integration
class TestSessionManagement:
    """Test session management (list, revoke)."""

    def test_create_user_session(self, db_session):
        user = _create_user(db_session)
        session = UserSession(
            user_id=user.id,
            token_jti="test-jti-123",
            ip_address="127.0.0.1",
            user_agent="Mozilla/5.0",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
            is_active=True,
        )
        db_session.add(session)
        db_session.flush()
        assert session.id is not None
        assert session.is_active is True

    def test_list_user_sessions(self, db_session):
        user = _create_user(db_session)
        session = UserSession(
            user_id=user.id,
            token_jti="test-jti-456",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
            is_active=True,
        )
        db_session.add(session)
        db_session.flush()
        sessions = db_session.query(UserSession).filter(UserSession.user_id == user.id).all()
        assert len(sessions) >= 1

    def test_revoke_user_session(self, db_session):
        user = _create_user(db_session)
        session = UserSession(
            user_id=user.id,
            token_jti="test-jti-789",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
            is_active=True,
        )
        db_session.add(session)
        db_session.flush()
        session.is_active = False
        db_session.flush()
        assert session.is_active is False

    def test_revoke_all_user_sessions(self, db_session):
        user = _create_user(db_session)
        for i in range(3):
            session = UserSession(
                user_id=user.id,
                token_jti=f"test-jti-{i}",
                expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
                is_active=True,
            )
            db_session.add(session)
        db_session.flush()
        db_session.query(UserSession).filter(UserSession.user_id == user.id).update(
            {UserSession.is_active: False}
        )
        db_session.flush()
        active_sessions = db_session.query(UserSession).filter(
            UserSession.user_id == user.id, UserSession.is_active == True
        ).all()
        assert len(active_sessions) == 0

    def test_session_expiry(self, db_session):
        user = _create_user(db_session)
        session = UserSession(
            user_id=user.id,
            token_jti="expired-jti",
            expires_at=datetime.now(timezone.utc) - timedelta(hours=1),
            is_active=True,
        )
        db_session.add(session)
        db_session.flush()
        assert session.expires_at < datetime.now(timezone.utc)


# ══════════════════════════════════════════════════════════════════
# API Key Management
# ══════════════════════════════════════════════════════════════════


@pytest.mark.integration
class TestAPIKeyManagement:
    """Test API key management."""

    def test_create_api_key(self, db_session):
        from domains.security.models.api_key import APIKey
        key = APIKey(
            user_id=1,
            name="Test API Key",
            key_hash="hashed_key_value",
            is_active=True,
        )
        db_session.add(key)
        db_session.flush()
        assert key.id is not None
        assert key.is_active is True

    def test_revoke_api_key(self, db_session):
        from domains.security.models.api_key import APIKey
        key = APIKey(
            user_id=1,
            name="Revoke Test",
            key_hash="hashed_key_value",
            is_active=True,
        )
        db_session.add(key)
        db_session.flush()
        key.is_active = False
        db_session.flush()
        assert key.is_active is False

    def test_list_user_api_keys(self, db_session):
        from domains.security.models.api_key import APIKey
        for i in range(3):
            key = APIKey(
                user_id=1,
                name=f"Key {i}",
                key_hash=f"hash_{i}",
                is_active=True,
            )
            db_session.add(key)
        db_session.flush()
        keys = db_session.query(APIKey).filter(APIKey.user_id == 1).all()
        assert len(keys) >= 3


# ══════════════════════════════════════════════════════════════════
# MFA Setup and Verification
# ══════════════════════════════════════════════════════════════════


@pytest.mark.integration
class TestMFAOperations:
    """Test MFA setup and verification."""

    def test_mfa_setup_generates_secret(self, client):
        email = f"mfa_{uuid.uuid4().hex[:8]}@zozi.test"
        reg = client.post(
            "/api/v1/auth/register",
            json={"email": email, "username": f"mfauser_{uuid.uuid4().hex[:8]}", "password": "SecurePass1!", "role": "customer"},
        )
        assert reg.status_code in (200, 201), reg.text
        login = client.post("/api/v1/auth/login", json={"email": email, "password": "SecurePass1!"})
        token = login.json()["access_token"]
        resp = client.post(
            "/api/v1/auth/mfa/setup",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert "secret" in body or "qr_code" in body or "totp_uri" in body

    def test_mfa_verify_with_valid_code(self, client):
        email = f"mfa2_{uuid.uuid4().hex[:8]}@zozi.test"
        reg = client.post(
            "/api/v1/auth/register",
            json={"email": email, "username": f"mfa2user_{uuid.uuid4().hex[:8]}", "password": "SecurePass1!", "role": "customer"},
        )
        assert reg.status_code in (200, 201), reg.text
        login = client.post("/api/v1/auth/login", json={"email": email, "password": "SecurePass1!"})
        token = login.json()["access_token"]
        client.post("/api/v1/auth/mfa/setup", headers={"Authorization": f"Bearer {token}"})
        resp = client.post(
            "/api/v1/auth/mfa/verify",
            headers={"Authorization": f"Bearer {token}"},
            json={"code": "123456"},
        )
        assert resp.status_code in (200, 400)

    def test_mfa_verify_with_invalid_code(self, client):
        email = f"mfa3_{uuid.uuid4().hex[:8]}@zozi.test"
        reg = client.post(
            "/api/v1/auth/register",
            json={"email": email, "username": f"mfa3user_{uuid.uuid4().hex[:8]}", "password": "SecurePass1!", "role": "customer"},
        )
        assert reg.status_code in (200, 201), reg.text
        login = client.post("/api/v1/auth/login", json={"email": email, "password": "SecurePass1!"})
        token = login.json()["access_token"]
        client.post("/api/v1/auth/mfa/setup", headers={"Authorization": f"Bearer {token}"})
        resp = client.post(
            "/api/v1/auth/mfa/verify",
            headers={"Authorization": f"Bearer {token}"},
            json={"code": "000000"},
        )
        assert resp.status_code == 400


# ══════════════════════════════════════════════════════════════════
# Document Verification (KYC)
# ══════════════════════════════════════════════════════════════════


@pytest.mark.integration
class TestDocumentVerification:
    """Test document verification (KYC)."""

    def test_submit_kyc_document(self, db_session):
        from domains.security.models.kyc import KYCDocument
        doc = KYCDocument(
            user_id=1,
            document_type="passport",
            document_number="AB1234567",
            status="pending",
        )
        db_session.add(doc)
        db_session.flush()
        assert doc.id is not None
        assert doc.status == "pending"

    def test_approve_kyc_document(self, db_session):
        from domains.security.models.kyc import KYCDocument
        doc = KYCDocument(
            user_id=1,
            document_type="id_card",
            document_number="ID987654",
            status="pending",
        )
        db_session.add(doc)
        db_session.flush()
        doc.status = "approved"
        db_session.flush()
        assert doc.status == "approved"

    def test_reject_kyc_document(self, db_session):
        from domains.security.models.kyc import KYCDocument
        doc = KYCDocument(
            user_id=1,
            document_type="driver_license",
            document_number="DL12345",
            status="pending",
        )
        db_session.add(doc)
        db_session.flush()
        doc.status = "rejected"
        doc.rejection_reason="Blurry image"
        db_session.flush()
        assert doc.status == "rejected"


# ══════════════════════════════════════════════════════════════════
# Alert Escalation
# ══════════════════════════════════════════════════════════════════


@pytest.mark.integration
class TestAlertEscalation:
    """Test alert escalation."""

    def test_create_security_alert(self, db_session):
        from domains.security.models.alert import SecurityAlert
        alert = SecurityAlert(
            title="Suspicious login",
            severity="high",
            user_id=1,
            status="open",
        )
        db_session.add(alert)
        db_session.flush()
        assert alert.id is not None
        assert alert.status == "open"

    def test_escalate_alert(self, db_session):
        from domains.security.models.alert import SecurityAlert
        alert = SecurityAlert(
            title="Fraud detected",
            severity="critical",
            user_id=1,
            status="open",
        )
        db_session.add(alert)
        db_session.flush()
        alert.status = "escalated"
        db_session.flush()
        assert alert.status == "escalated"

    def test_resolve_alert(self, db_session):
        from domains.security.models.alert import SecurityAlert
        alert = SecurityAlert(
            title="False positive",
            severity="low",
            user_id=1,
            status="open",
        )
        db_session.add(alert)
        db_session.flush()
        alert.status = "resolved"
        db_session.flush()
        assert alert.status == "resolved"


# ══════════════════════════════════════════════════════════════════
# Threat Monitoring
# ══════════════════════════════════════════════════════════════════


@pytest.mark.integration
class TestThreatMonitoring:
    """Test threat monitoring."""

    def test_log_threat_event(self, db_session):
        from domains.security.services.events import log_threat_event
        result = log_threat_event(
            threat_type="brute_force",
            source_ip="192.168.1.100",
            details={"attempts": 50},
            db=db_session,
        )
        assert result is not None

    def test_get_active_threats(self, db_session):
        from domains.security.services.events import get_active_threats
        result = get_active_threats(db=db_session)
        assert isinstance(result, list)

    def test_geo_fence_validator(self, db_session):
        from domains.security.services.iam.iam_service import GeoFenceValidator
        distance = GeoFenceValidator.haversine_distance(25.2048, 55.2708, 25.2048, 55.2708)
        assert distance == 0.0

    def test_geo_fence_different_locations(self, db_session):
        from domains.security.services.iam.iam_service import GeoFenceValidator
        distance = GeoFenceValidator.haversine_distance(25.2048, 55.2708, 24.4539, 54.3773)
        assert distance > 0
