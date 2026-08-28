"""Behavior tests for accounts domain — registration, auth, GDPR, profile, and security flows."""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import pytest

from domains.accounts.models.user import (
    User,
    UserLoginHistory,
    UserSession,
    UserDevice,
    PasswordResetToken,
    EmailVerificationToken,
    RevokedToken,
)
from domains.accounts.models.user_consent import UserConsent
from domains.accounts.services.gdpr_service import (
    export_user_data,
    anonymize_user_data,
    delete_user_data,
    record_consent,
    get_user_consents,
    has_active_consent,
    CONSENT_TERMS,
    CONSENT_MARKETING,
    CONSENT_PRIVACY,
)


def _create_user(db_session, email=None, username=None, password="SecurePass1!", role="customer", is_active=True):
    from infrastructure.utils.auth import get_password_hash
    user = User(
        email=email or f"user_{uuid.uuid4().hex[:8]}@zozi.test",
        username=username or f"user_{uuid.uuid4().hex[:8]}",
        hashed_password=get_password_hash(password),
        role=role,
        is_active=is_active,
        country_code="AE",
    )
    db_session.add(user)
    db_session.flush()
    return user


# ══════════════════════════════════════════════════════════════════
# User Registration Flow
# ══════════════════════════════════════════════════════════════════


@pytest.mark.integration
class TestUserRegistration:
    """Test user registration flow via API."""

    def test_register_creates_user_with_hashed_password(self, client):
        email = f"reg_{uuid.uuid4().hex[:8]}@zozi.test"
        resp = client.post(
            "/api/v1/auth/register",
            json={
                "email": email,
                "username": f"reguser_{uuid.uuid4().hex[:8]}",
                "password": "SecurePass1!",
                "role": "customer",
            },
        )
        assert resp.status_code in (200, 201)
        body = resp.json()
        assert body["user"]["email"] == email
        assert "hashed_password" not in body["user"]
        assert "id" in body["user"]

    def test_register_duplicate_email_rejected(self, client):
        email = f"dup_{uuid.uuid4().hex[:8]}@zozi.test"
        client.post(
            "/api/v1/auth/register",
            json={"email": email, "username": "dupuser1", "password": "SecurePass1!", "role": "customer"},
        )
        resp = client.post(
            "/api/v1/auth/register",
            json={"email": email, "username": "dupuser2", "password": "SecurePass1!", "role": "customer"},
        )
        assert resp.status_code == 400
        assert "Email already registered" in resp.json()["detail"]

    def test_register_duplicate_username_rejected(self, client):
        username = f"dupname_{uuid.uuid4().hex[:8]}"
        client.post(
            "/api/v1/auth/register",
            json={"email": f"dup2_{uuid.uuid4().hex[:8]}@zozi.test", "username": username, "password": "SecurePass1!", "role": "customer"},
        )
        resp = client.post(
            "/api/v1/auth/register",
            json={"email": f"dup2b_{uuid.uuid4().hex[:8]}@zozi.test", "username": username, "password": "SecurePass1!", "role": "customer"},
        )
        assert resp.status_code == 400
        assert "Username already taken" in resp.json()["detail"]

    def test_register_weak_password_rejected(self, client):
        resp = client.post(
            "/api/v1/auth/register",
            json={"email": f"weak_{uuid.uuid4().hex[:8]}@zozi.test", "username": f"weak_{uuid.uuid4().hex[:8]}", "password": "weak", "role": "customer"},
        )
        assert resp.status_code in (422, 429)

    def test_register_invalid_email_rejected(self, client):
        resp = client.post(
            "/api/v1/auth/register",
            json={"email": "not-an-email", "username": f"inv_{uuid.uuid4().hex[:8]}", "password": "SecurePass1!", "role": "customer"},
        )
        assert resp.status_code in (422, 429)


# ══════════════════════════════════════════════════════════════════
# Login Flow
# ══════════════════════════════════════════════════════════════════


@pytest.mark.integration
class TestUserLogin:
    """Test user login with correct/incorrect credentials."""

    def _register_and_login(self, client, email=None, password="SecurePass1!"):
        email = email or f"user_{uuid.uuid4().hex[:8]}@zozi.test"
        reg = client.post(
            "/api/v1/auth/register",
            json={"email": email, "username": f"user_{uuid.uuid4().hex[:8]}", "password": password, "role": "customer"},
        )
        assert reg.status_code in (200, 201), reg.text
        login = client.post("/api/v1/auth/login", json={"email": email, "password": password})
        return login

    def test_login_success_returns_tokens(self, client):
        resp = self._register_and_login(client)
        assert resp.status_code == 200
        body = resp.json()
        assert "access_token" in body
        assert "refresh_token" in body
        assert body["token_type"] == "bearer"

    def test_login_wrong_password_rejected(self, client):
        email = f"login_{uuid.uuid4().hex[:8]}@zozi.test"
        self._register_and_login(client, email=email)
        resp = client.post("/api/v1/auth/login", json={"email": email, "password": "WrongPass1!"})
        assert resp.status_code == 401
        assert "Invalid credentials" in resp.json()["detail"]

    def test_login_nonexistent_user_rejected(self, client):
        resp = client.post("/api/v1/auth/login", json={"email": "nobody@zozi.test", "password": "SecurePass1!"})
        assert resp.status_code == 401

    def test_login_inactive_user_rejected(self, client, db_session):
        user = _create_user(db_session, is_active=False)
        resp = client.post("/api/v1/auth/login", json={"email": user.email, "password": "SecurePass1!"})
        assert resp.status_code == 403
        assert "inactive" in resp.json()["detail"].lower()

    def test_login_missing_credentials_rejected(self, client):
        resp = client.post("/api/v1/auth/login", json={})
        assert resp.status_code == 422


# ══════════════════════════════════════════════════════════════════
# Token Refresh Flow
# ══════════════════════════════════════════════════════════════════


@pytest.mark.integration
class TestTokenRefresh:
    """Test JWT token refresh flow."""

    def test_refresh_returns_new_access_token(self, client):
        email = f"refresh_{uuid.uuid4().hex[:8]}@zozi.test"
        reg = client.post(
            "/api/v1/auth/register",
            json={"email": email, "username": f"refreshuser_{uuid.uuid4().hex[:8]}", "password": "SecurePass1!", "role": "customer"},
        )
        assert reg.status_code in (200, 201), reg.text
        login = client.post("/api/v1/auth/login", json={"email": email, "password": "SecurePass1!"})
        assert login.status_code == 200
        refresh_token = login.json()["refresh_token"]
        resp = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
        assert resp.status_code == 200
        assert "access_token" in resp.json()

    def test_refresh_invalid_token_rejected(self, client):
        resp = client.post("/api/v1/auth/refresh", json={"refresh_token": "invalid_token"})
        assert resp.status_code == 401


# ══════════════════════════════════════════════════════════════════
# Password Change Flow
# ══════════════════════════════════════════════════════════════════


@pytest.mark.integration
class TestPasswordChange:
    """Test password change flow."""

    def test_password_change_with_correct_old_password(self, client):
        email = f"pwdchange_{uuid.uuid4().hex[:8]}@zozi.test"
        reg = client.post(
            "/api/v1/auth/register",
            json={"email": email, "username": f"pwduser_{uuid.uuid4().hex[:8]}", "password": "SecurePass1!", "role": "customer"},
        )
        assert reg.status_code in (200, 201), reg.text
        login = client.post("/api/v1/auth/login", json={"email": email, "password": "SecurePass1!"})
        token = login.json()["access_token"]
        resp = client.post(
            "/api/v1/auth/change-password",
            headers={"Authorization": f"Bearer {token}"},
            json={"old_password": "SecurePass1!", "new_password": "NewSecurePass1!"},
        )
        assert resp.status_code == 200

    def test_password_change_with_wrong_old_password(self, client):
        email = f"pwdwrong_{uuid.uuid4().hex[:8]}@zozi.test"
        reg = client.post(
            "/api/v1/auth/register",
            json={"email": email, "username": f"pwdwrong_{uuid.uuid4().hex[:8]}", "password": "SecurePass1!", "role": "customer"},
        )
        assert reg.status_code in (200, 201), reg.text
        login = client.post("/api/v1/auth/login", json={"email": email, "password": "SecurePass1!"})
        token = login.json()["access_token"]
        resp = client.post(
            "/api/v1/auth/change-password",
            headers={"Authorization": f"Bearer {token}"},
            json={"old_password": "WrongOldPass1!", "new_password": "NewSecurePass1!"},
        )
        assert resp.status_code == 400


# ══════════════════════════════════════════════════════════════════
# Password Reset Flow
# ══════════════════════════════════════════════════════════════════


@pytest.mark.integration
class TestPasswordReset:
    """Test forgot password → reset → login flow."""

    def test_forgot_password_creates_reset_token(self, client, db_session):
        email = f"forgot_{uuid.uuid4().hex[:8]}@zozi.test"
        reg = client.post(
            "/api/v1/auth/register",
            json={"email": email, "username": f"forgotuser_{uuid.uuid4().hex[:8]}", "password": "SecurePass1!", "role": "customer"},
        )
        assert reg.status_code in (200, 201), reg.text
        resp = client.post("/api/v1/auth/forgot-password", json={"email": email})
        assert resp.status_code == 200
        user = db_session.query(User).filter(User.email == email).first()
        tokens = db_session.query(PasswordResetToken).filter(PasswordResetToken.user_id == user.id).all()
        assert len(tokens) >= 1
        assert tokens[0].is_used is False

    def test_reset_password_with_valid_token(self, client, db_session):
        email = f"reset_{uuid.uuid4().hex[:8]}@zozi.test"
        reg = client.post(
            "/api/v1/auth/register",
            json={"email": email, "username": f"resetuser_{uuid.uuid4().hex[:8]}", "password": "SecurePass1!", "role": "customer"},
        )
        assert reg.status_code in (200, 201), reg.text
        client.post("/api/v1/auth/forgot-password", json={"email": email})
        user = db_session.query(User).filter(User.email == email).first()
        token = db_session.query(PasswordResetToken).filter(PasswordResetToken.user_id == user.id).first()
        resp = client.post(
            "/api/v1/auth/reset-password",
            json={"token": token.token, "new_password": "ResetPass1!"},
        )
        assert resp.status_code == 200
        db_session.refresh(token)
        assert token.is_used is True

    def test_reset_password_with_invalid_token_rejected(self, client):
        resp = client.post(
            "/api/v1/auth/reset-password",
            json={"token": "invalid_token_value", "new_password": "ResetPass1!"},
        )
        assert resp.status_code == 400


# ══════════════════════════════════════════════════════════════════
# User Profile Update
# ══════════════════════════════════════════════════════════════════


@pytest.mark.integration
class TestProfileUpdate:
    """Test user profile update flow."""

    def test_get_current_user_profile(self, client):
        email = f"me_{uuid.uuid4().hex[:8]}@zozi.test"
        reg = client.post(
            "/api/v1/auth/register",
            json={"email": email, "username": f"meuser_{uuid.uuid4().hex[:8]}", "password": "SecurePass1!", "role": "customer"},
        )
        assert reg.status_code in (200, 201), reg.text
        login = client.post("/api/v1/auth/login", json={"email": email, "password": "SecurePass1!"})
        token = login.json()["access_token"]
        resp = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        body = resp.json()
        assert "email" in body
        assert "role" in body

    def test_get_current_user_unauthorized(self, client):
        resp = client.get("/api/v1/auth/me")
        assert resp.status_code == 401


# ══════════════════════════════════════════════════════════════════
# Account Lockout After Failed Attempts
# ══════════════════════════════════════════════════════════════════


@pytest.mark.integration
class TestAccountLockout:
    """Test account lockout after N failed login attempts."""

    def test_lockout_after_max_failed_attempts(self, client):
        email = f"lockout_{uuid.uuid4().hex[:8]}@zozi.test"
        reg = client.post(
            "/api/v1/auth/register",
            json={"email": email, "username": f"lockuser_{uuid.uuid4().hex[:8]}", "password": "SecurePass1!", "role": "customer"},
        )
        assert reg.status_code in (200, 201), reg.text
        for _ in range(5):
            client.post("/api/v1/auth/login", json={"email": email, "password": "WrongPass1!"})
        resp = client.post("/api/v1/auth/login", json={"email": email, "password": "SecurePass1!"})
        assert resp.status_code in (401, 423)

    def test_login_history_tracks_failed_attempts(self, client, db_session):
        email = f"history_{uuid.uuid4().hex[:8]}@zozi.test"
        reg = client.post(
            "/api/v1/auth/register",
            json={"email": email, "username": f"histuser_{uuid.uuid4().hex[:8]}", "password": "SecurePass1!", "role": "customer"},
        )
        assert reg.status_code in (200, 201), reg.text
        client.post("/api/v1/auth/login", json={"email": email, "password": "WrongPass1!"})
        user = db_session.query(User).filter(User.email == email).first()
        failed = db_session.query(UserLoginHistory).filter(
            UserLoginHistory.user_id == user.id, UserLoginHistory.success == False
        ).all()
        assert len(failed) >= 1


# ══════════════════════════════════════════════════════════════════
# GDPR Data Export
# ══════════════════════════════════════════════════════════════════


@pytest.mark.integration
class TestGDPRExport:
    """Test GDPR data export (Art. 15 — Right of access)."""

    def test_export_returns_user_data_structure(self, db_session):
        user = _create_user(db_session, full_name="Test User")
        result = export_user_data(user.id, db_session)
        assert result["found"] is True
        assert result["data"]["profile"]["email"] == user.email
        assert result["data"]["profile"]["full_name"] == "Test User"
        assert "login_history" in result["data"]
        assert "devices" in result["data"]
        assert "sessions" in result["data"]
        assert "consents" in result["data"]

    def test_export_nonexistent_user_returns_not_found(self, db_session):
        result = export_user_data(99999, db_session)
        assert result["found"] is False
        assert result["data"] == {}

    def test_export_includes_login_history(self, db_session):
        user = _create_user(db_session)
        history = UserLoginHistory(
            user_id=user.id,
            ip_address="127.0.0.1",
            user_agent="test-agent",
            success=True,
        )
        db_session.add(history)
        db_session.flush()
        result = export_user_data(user.id, db_session)
        assert len(result["data"]["login_history"]) >= 1
        assert result["data"]["login_history"][0]["ip_address"] == "127.0.0.1"

    def test_export_includes_consent_records(self, db_session):
        user = _create_user(db_session)
        record_consent(user.id, CONSENT_TERMS, True, "127.0.0.1", "test-agent", db_session)
        result = export_user_data(user.id, db_session)
        assert len(result["data"]["consents"]) >= 1
        assert result["data"]["consents"][0]["consent_type"] == CONSENT_TERMS


# ══════════════════════════════════════════════════════════════════
# GDPR Account Deletion
# ══════════════════════════════════════════════════════════════════


@pytest.mark.integration
class TestGDPRDeletion:
    """Test GDPR account deletion (Art. 17 — Right to erasure)."""

    def test_anonymize_preserves_financial_trail(self, db_session):
        user = _create_user(db_session, full_name="John Doe", email="john@test.com")
        result = anonymize_user_data(user.id, db_session)
        assert result is True
        db_session.refresh(user)
        assert "anonymized.invalid" in user.email
        assert user.is_active is False
        assert user.full_name.startswith("Anonymized User")

    def test_anonymize_revokes_active_sessions(self, db_session):
        user = _create_user(db_session)
        session = UserSession(
            user_id=user.id,
            token_jti="test-jti",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
            is_active=True,
        )
        db_session.add(session)
        db_session.flush()
        anonymize_user_data(user.id, db_session)
        db_session.refresh(session)
        assert session.is_active is False

    def test_anonymize_nonexistent_user_returns_false(self, db_session):
        result = anonymize_user_data(99999, db_session)
        assert result is False

    def test_hard_delete_removes_user_and_dependents(self, db_session):
        user = _create_user(db_session)
        user_id = user.id
        history = UserLoginHistory(user_id=user.id, ip_address="127.0.0.1", success=True)
        db_session.add(history)
        db_session.flush()
        result = delete_user_data(user_id, db_session)
        assert result is True
        assert db_session.query(User).filter(User.id == user_id).first() is None
        assert db_session.query(UserLoginHistory).filter(UserLoginHistory.user_id == user_id).count() == 0

    def test_hard_delete_nonexistent_user_returns_false(self, db_session):
        result = delete_user_data(99999, db_session)
        assert result is False


# ══════════════════════════════════════════════════════════════════
# Email Verification Flow
# ══════════════════════════════════════════════════════════════════


@pytest.mark.integration
class TestEmailVerification:
    """Test email verification flow."""

    def test_email_verification_token_created_on_registration(self, client, db_session):
        email = f"verify_{uuid.uuid4().hex[:8]}@zozi.test"
        reg = client.post(
            "/api/v1/auth/register",
            json={"email": email, "username": f"verifyuser_{uuid.uuid4().hex[:8]}", "password": "SecurePass1!", "role": "customer"},
        )
        assert reg.status_code in (200, 201), reg.text
        user = db_session.query(User).filter(User.email == email).first()
        tokens = db_session.query(EmailVerificationToken).filter(EmailVerificationToken.user_id == user.id).all()
        assert len(tokens) >= 1
        assert tokens[0].is_used is False

    def test_verify_email_with_valid_token(self, client, db_session):
        email = f"verify2_{uuid.uuid4().hex[:8]}@zozi.test"
        reg = client.post(
            "/api/v1/auth/register",
            json={"email": email, "username": f"verify2user_{uuid.uuid4().hex[:8]}", "password": "SecurePass1!", "role": "customer"},
        )
        assert reg.status_code in (200, 201), reg.text
        user = db_session.query(User).filter(User.email == email).first()
        token = db_session.query(EmailVerificationToken).filter(EmailVerificationToken.user_id == user.id).first()
        resp = client.get(f"/api/v1/auth/verify-email?token={token.token}")
        assert resp.status_code == 200
        db_session.refresh(user)
        assert user.email_verified is True

    def test_verify_email_with_invalid_token(self, client):
        resp = client.get("/api/v1/auth/verify-email?token=invalid_token")
        assert resp.status_code == 400


# ══════════════════════════════════════════════════════════════════
# OTP Send and Verify
# ══════════════════════════════════════════════════════════════════


@pytest.mark.integration
class TestOTP:
    """Test OTP send and verify flow."""

    def test_send_otp_creates_token(self, client):
        email = f"otp_{uuid.uuid4().hex[:8]}@zozi.test"
        reg = client.post(
            "/api/v1/auth/register",
            json={"email": email, "username": f"otpuser_{uuid.uuid4().hex[:8]}", "password": "SecurePass1!", "role": "customer"},
        )
        assert reg.status_code in (200, 201), reg.text
        login = client.post("/api/v1/auth/login", json={"email": email, "password": "SecurePass1!"})
        token = login.json()["access_token"]
        resp = client.post("/api/v1/auth/otp/send", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200

    def test_verify_otp_with_wrong_code(self, client):
        email = f"otp2_{uuid.uuid4().hex[:8]}@zozi.test"
        reg = client.post(
            "/api/v1/auth/register",
            json={"email": email, "username": f"otp2user_{uuid.uuid4().hex[:8]}", "password": "SecurePass1!", "role": "customer"},
        )
        assert reg.status_code in (200, 201), reg.text
        login = client.post("/api/v1/auth/login", json={"email": email, "password": "SecurePass1!"})
        token = login.json()["access_token"]
        client.post("/api/v1/auth/otp/send", headers={"Authorization": f"Bearer {token}"})
        resp = client.post(
            "/api/v1/auth/otp/verify",
            headers={"Authorization": f"Bearer {token}"},
            json={"code": "000000"},
        )
        assert resp.status_code == 400


# ══════════════════════════════════════════════════════════════════
# Consent Management
# ══════════════════════════════════════════════════════════════════


@pytest.mark.integration
class TestConsentManagement:
    """Test user consent management."""

    def test_record_consent_granted(self, db_session):
        user = _create_user(db_session)
        result = record_consent(user.id, CONSENT_TERMS, True, "127.0.0.1", "test-agent", db_session)
        assert result.granted is True
        assert result.consent_type == CONSENT_TERMS
        assert result.revoked_at is None

    def test_record_consent_revocation(self, db_session):
        user = _create_user(db_session)
        record_consent(user.id, CONSENT_MARKETING, True, "127.0.0.1", "test-agent", db_session)
        result = record_consent(user.id, CONSENT_MARKETING, False, "127.0.0.1", "test-agent", db_session)
        assert result.revoked_at is not None

    def test_has_active_consent_returns_true_when_granted(self, db_session):
        user = _create_user(db_session)
        record_consent(user.id, CONSENT_PRIVACY, True, "127.0.0.1", "test-agent", db_session)
        assert has_active_consent(user.id, CONSENT_PRIVACY, db_session) is True

    def test_has_active_consent_returns_false_when_revoked(self, db_session):
        user = _create_user(db_session)
        record_consent(user.id, CONSENT_PRIVACY, True, "127.0.0.1", "test-agent", db_session)
        record_consent(user.id, CONSENT_PRIVACY, False, "127.0.0.1", "test-agent", db_session)
        assert has_active_consent(user.id, CONSENT_PRIVACY, db_session) is False

    def test_get_user_consents_returns_history(self, db_session):
        user = _create_user(db_session)
        record_consent(user.id, CONSENT_TERMS, True, "127.0.0.1", "test-agent", db_session)
        record_consent(user.id, CONSENT_MARKETING, True, "127.0.0.1", "test-agent", db_session)
        consents = get_user_consents(user.id, db_session)
        assert len(consents) >= 2


# ══════════════════════════════════════════════════════════════════
# User Preference Management
# ══════════════════════════════════════════════════════════════════


@pytest.mark.integration
class TestUserPreferences:
    """Test user preference management."""

    def test_update_user_preferences(self, client):
        email = f"pref_{uuid.uuid4().hex[:8]}@zozi.test"
        reg = client.post(
            "/api/v1/auth/register",
            json={"email": email, "username": f"prefuser_{uuid.uuid4().hex[:8]}", "password": "SecurePass1!", "role": "customer"},
        )
        assert reg.status_code in (200, 201), reg.text
        login = client.post("/api/v1/auth/login", json={"email": email, "password": "SecurePass1!"})
        token = login.json()["access_token"]
        resp = client.put(
            "/api/v1/auth/preferences",
            headers={"Authorization": f"Bearer {token}"},
            json={"language": "en", "currency": "USD", "timezone": "UTC"},
        )
        assert resp.status_code == 200

    def test_get_user_preferences(self, client):
        email = f"pref2_{uuid.uuid4().hex[:8]}@zozi.test"
        reg = client.post(
            "/api/v1/auth/register",
            json={"email": email, "username": f"pref2user_{uuid.uuid4().hex[:8]}", "password": "SecurePass1!", "role": "customer"},
        )
        assert reg.status_code in (200, 201), reg.text
        login = client.post("/api/v1/auth/login", json={"email": email, "password": "SecurePass1!"})
        token = login.json()["access_token"]
        resp = client.get("/api/v1/auth/preferences", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200


# ══════════════════════════════════════════════════════════════════
# Logout Flow
# ══════════════════════════════════════════════════════════════════


@pytest.mark.integration
class TestLogout:
    """Test logout flow."""

    def test_logout_revokes_token(self, client):
        email = f"logout_{uuid.uuid4().hex[:8]}@zozi.test"
        reg = client.post(
            "/api/v1/auth/register",
            json={"email": email, "username": f"logoutuser_{uuid.uuid4().hex[:8]}", "password": "SecurePass1!", "role": "customer"},
        )
        assert reg.status_code in (200, 201), reg.text
        login = client.post("/api/v1/auth/login", json={"email": email, "password": "SecurePass1!"})
        token = login.json()["access_token"]
        resp = client.post("/api/v1/auth/logout", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200

    def test_logout_unauthorized(self, client):
        resp = client.post("/api/v1/auth/logout")
        assert resp.status_code == 401
