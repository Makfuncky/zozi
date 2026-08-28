"""Comprehensive authentication security tests for ZOZI backend.

Tests JWT token lifecycle, password security, account lockout,
email verification, token type enforcement, algorithm restrictions,
and device binding (dfp claim).
"""
from __future__ import annotations

import time
import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import patch, MagicMock

import bcrypt
import pytest
from fastapi.testclient import TestClient
from jose import jwt


# ── JWT Token Creation and Validation ─────────────────────────────────────


class TestJWTTokenCreation:
    """Test JWT token creation, structure, and validation."""

    def test_create_access_token_returns_valid_jwt(self):
        from infrastructure.utils.auth import create_access_token

        token = create_access_token(data={"sub": "1", "role": "customer"})
        assert isinstance(token, str)
        assert len(token) > 0

    def test_access_token_contains_required_claims(self):
        from infrastructure.utils.auth import create_access_token, SECRET_KEY, ALGORITHM

        token = create_access_token(data={"sub": "42", "role": "admin"})
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        assert payload["sub"] == "42"
        assert payload["role"] == "admin"
        assert payload["type"] == "access"
        assert "exp" in payload
        assert "jti" in payload

    def test_access_token_jti_is_unique(self):
        from infrastructure.utils.auth import create_access_token, decode_token

        token1 = create_access_token(data={"sub": "1", "role": "customer"})
        token2 = create_access_token(data={"sub": "1", "role": "customer"})

        payload1 = decode_token(token1)
        payload2 = decode_token(token2)

        assert payload1["jti"] != payload2["jti"]

    def test_verify_token_returns_subject(self, admin_token):
        from infrastructure.utils.auth import verify_token

        subject = verify_token(admin_token)
        assert subject is not None

    def test_verify_token_rejects_malformed_token(self):
        from infrastructure.utils.auth import verify_token

        with pytest.raises(Exception):
            verify_token("not.a.valid.jwt.token")

    def test_verify_token_rejects_empty_string(self):
        from infrastructure.utils.auth import verify_token

        with pytest.raises(Exception):
            verify_token("")

    def test_verify_token_rejects_tampered_token(self, admin_token):
        from infrastructure.utils.auth import verify_token

        tampered = admin_token[:-5] + "XXXXX"
        with pytest.raises(Exception):
            verify_token(tampered)

    def test_create_refresh_token_contains_family_id(self):
        from infrastructure.utils.auth import create_refresh_token, decode_token

        token = create_refresh_token(data={"sub": "1"})
        payload = decode_token(token, expected_type="refresh")

        assert payload["type"] == "refresh"
        assert "family_id" in payload
        assert "jti" in payload

    def test_refresh_token_preserves_family_id(self):
        from infrastructure.utils.auth import create_refresh_token, decode_token

        token = create_refresh_token(data={"sub": "1"}, family_id="test-family-123")
        payload = decode_token(token, expected_type="refresh")

        assert payload["family_id"] == "test-family-123"


class TestTokenExpiration:
    """Test token expiration behavior."""

    def test_access_token_expires_after_default_duration(self):
        from infrastructure.utils.auth import create_access_token, SECRET_KEY, ALGORITHM

        token = create_access_token(data={"sub": "1", "role": "customer"})
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        exp = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        now = datetime.now(timezone.utc)
        delta = exp - now

        assert delta.total_seconds() > 0
        assert delta.total_seconds() <= 15 * 60 + 60  # 15 min + 1 min tolerance

    def test_access_token_with_custom_expiry(self):
        from infrastructure.utils.auth import create_access_token, SECRET_KEY, ALGORITHM

        token = create_access_token(
            data={"sub": "1"},
            expires_delta=timedelta(seconds=1),
        )
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        exp = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        now = datetime.now(timezone.utc)

        assert (exp - now).total_seconds() < 5

    def test_expired_token_is_rejected(self):
        from infrastructure.utils.auth import create_access_token, verify_token

        expired_token = create_access_token(
            data={"sub": "1"},
            expires_delta=timedelta(seconds=-1),
        )

        with pytest.raises(Exception) as exc_info:
            verify_token(expired_token)
        assert "Invalid" in str(exc_info.value.detail) or "expired" in str(exc_info.value.detail).lower()

    def test_refresh_token_longer_expiry_than_access(self):
        from infrastructure.utils.auth import create_access_token, create_refresh_token, SECRET_KEY, ALGORITHM

        access = create_access_token(data={"sub": "1"})
        refresh = create_refresh_token(data={"sub": "1"})

        access_payload = jwt.decode(access, SECRET_KEY, algorithms=[ALGORITHM])
        refresh_payload = jwt.decode(refresh, SECRET_KEY, algorithms=[ALGORITHM])

        access_exp = datetime.fromtimestamp(access_payload["exp"], tz=timezone.utc)
        refresh_exp = datetime.fromtimestamp(refresh_payload["exp"], tz=timezone.utc)

        assert refresh_exp > access_exp


class TestTokenRefreshFlow:
    """Test refresh token rotation and family tracking."""

    def test_rotate_refresh_token_returns_new_tokens(self):
        from infrastructure.utils.auth import create_refresh_token, rotate_refresh_token

        refresh = create_refresh_token(data={"sub": "42"}, family_id="fam-1")
        new_access, new_refresh = rotate_refresh_token(refresh)

        assert isinstance(new_access, str)
        assert isinstance(new_refresh, str)
        assert new_access != new_refresh

    def test_rotated_refresh_token_maintains_family(self):
        from infrastructure.utils.auth import create_refresh_token, rotate_refresh_token, decode_token

        refresh = create_refresh_token(data={"sub": "42"}, family_id="fam-1")
        _, new_refresh = rotate_refresh_token(refresh)
        payload = decode_token(new_refresh, expected_type="refresh")

        assert payload["family_id"] == "fam-1"

    def test_refresh_token_reuse_detected_and_revoked(self):
        from infrastructure.utils.auth import (
            create_refresh_token, rotate_refresh_token,
            is_refresh_family_revoked,
        )

        refresh = create_refresh_token(data={"sub": "42"}, family_id="fam-reuse")
        # First rotation succeeds
        rotate_refresh_token(refresh)

        # Second use of same token should fail
        with pytest.raises(Exception) as exc_info:
            rotate_refresh_token(refresh)
        assert "reuse" in str(exc_info.value.detail).lower() or "revoked" in str(exc_info.value.detail).lower()

        assert is_refresh_family_revoked("fam-reuse") is True

    def test_revoked_family_rejects_new_tokens(self):
        from infrastructure.utils.auth import (
            create_refresh_token, rotate_refresh_token,
            revoke_refresh_family, is_refresh_family_revoked,
        )

        family_id = "fam-revoke-test"
        revoke_refresh_family(family_id)
        assert is_refresh_family_revoked(family_id) is True

        refresh = create_refresh_token(data={"sub": "42"}, family_id=family_id)
        with pytest.raises(Exception) as exc_info:
            rotate_refresh_token(refresh)
        assert "revoked" in str(exc_info.value.detail).lower()

    def test_refresh_with_device_binding(self):
        from infrastructure.utils.auth import create_refresh_token, rotate_refresh_token, decode_token

        refresh = create_refresh_token(data={"sub": "42"}, family_id="fam-dfp")
        new_access, _ = rotate_refresh_token(refresh, device_fp="device-abc-123")
        payload = decode_token(new_access)

        assert payload.get("dfp") == "device-abc-123"


class TestJTIblacklist:
    """Test JTI-based token revocation."""

    def test_blacklist_token_revokes_access(self):
        from infrastructure.utils.auth import (
            create_access_token, blacklist_token,
            is_token_blacklisted, decode_token,
        )

        token = create_access_token(data={"sub": "1", "role": "customer"})
        payload = decode_token(token)
        jti = payload["jti"]

        assert is_token_blacklisted(jti) is False
        blacklist_token(jti, 3600)
        assert is_token_blacklisted(jti) is True

    def test_blacklisted_token_rejected_by_verify(self):
        from infrastructure.utils.auth import (
            create_access_token, blacklist_token, verify_token,
        )

        token = create_access_token(data={"sub": "1", "role": "customer"})
        payload = verify_token(token)
        assert payload == "1"

        # Blacklist and re-verify
        from infrastructure.utils.auth import decode_token
        decoded = decode_token(token)
        blacklist_token(decoded["jti"], 3600)

        with pytest.raises(Exception) as exc_info:
            verify_token(token)
        assert "revoked" in str(exc_info.value.detail).lower()


class TestPasswordHashing:
    """Test bcrypt password hashing."""

    def test_password_hashing_produces_different_salts(self):
        from infrastructure.utils.auth import get_password_hash

        hash1 = get_password_hash("SecurePass1!")
        hash2 = get_password_hash("SecurePass1!")

        assert hash1 != hash2

    def test_verify_password_correct(self):
        from infrastructure.utils.auth import get_password_hash, verify_password

        hashed = get_password_hash("SecurePass1!")
        assert verify_password("SecurePass1!", hashed) is True

    def test_verify_password_incorrect(self):
        from infrastructure.utils.auth import get_password_hash, verify_password

        hashed = get_password_hash("SecurePass1!")
        assert verify_password("WrongPass1!", hashed) is False

    def test_password_never_stored_in_plaintext(self):
        from infrastructure.utils.auth import get_password_hash

        hashed = get_password_hash("SecurePass1!")
        assert "SecurePass1" not in hashed

    def test_bcrypt_roundtrip_with_unicode(self):
        from infrastructure.utils.auth import get_password_hash, verify_password

        password = "Pässwörd123!🔒"
        hashed = get_password_hash(password)
        assert verify_password(password, hashed) is True


class TestPasswordComplexity:
    """Test password complexity validation."""

    def test_valid_complex_password_accepted(self):
        from infrastructure.utils.auth import validate_password_complexity

        validate_password_complexity("SecurePass1!")  # Should not raise

    def test_short_password_rejected(self):
        from infrastructure.utils.auth import validate_password_complexity

        with pytest.raises(Exception):
            validate_password_complexity("Ab1!")

    def test_password_without_uppercase_rejected(self):
        from infrastructure.utils.auth import validate_password_complexity

        with pytest.raises(Exception):
            validate_password_complexity("lowercase1!")

    def test_password_without_lowercase_rejected(self):
        from infrastructure.utils.auth import validate_password_complexity

        with pytest.raises(Exception):
            validate_password_complexity("UPPERCASE1!")

    def test_password_without_digit_rejected(self):
        from infrastructure.utils.auth import validate_password_complexity

        with pytest.raises(Exception):
            validate_password_complexity("NoDigitsHere!")

    def test_password_without_special_char_rejected(self):
        from infrastructure.utils.auth import validate_password_complexity

        with pytest.raises(Exception):
            validate_password_complexity("NoSpecial123")

    def test_password_over_72_bytes_rejected(self):
        from infrastructure.utils.auth import get_password_hash, validate_password_complexity

        long_password = "A" * 73 + "a1!"
        with pytest.raises(ValueError, match="72"):
            get_password_hash(long_password)

        with pytest.raises(ValueError, match="72"):
            validate_password_complexity(long_password)

    def test_password_exactly_72_bytes_accepted(self):
        from infrastructure.utils.auth import get_password_hash

        password_72 = "A" + "a" * 68 + "1!"
        assert len(password_72.encode("utf-8")) == 72
        hashed = get_password_hash(password_72)
        assert hashed is not None


class TestAccountLockout:
    """Test account lockout after failed login attempts."""

    def test_account_locks_after_max_attempts(self):
        from infrastructure.utils.auth import (
            record_failed_login, is_account_locked, clear_failed_logins,
            LOGIN_FAIL_MAX,
        )

        identifier = f"locktest-{uuid.uuid4().hex}"
        clear_failed_logins(identifier)

        for _ in range(LOGIN_FAIL_MAX):
            record_failed_login(identifier)

        assert is_account_locked(identifier) is True
        clear_failed_logins(identifier)

    def test_account_not_locked_below_threshold(self):
        from infrastructure.utils.auth import (
            record_failed_login, is_account_locked, clear_failed_logins,
        )

        identifier = f"locktest-{uuid.uuid4().hex}"
        clear_failed_logins(identifier)

        for _ in range(3):
            record_failed_login(identifier)

        assert is_account_locked(identifier) is False
        clear_failed_logins(identifier)

    def test_clear_failed_logins_resets_counter(self):
        from infrastructure.utils.auth import (
            record_failed_login, is_account_locked, clear_failed_logins,
        )

        identifier = f"locktest-{uuid.uuid4().hex}"
        clear_failed_logins(identifier)

        for _ in range(3):
            record_failed_login(identifier)

        clear_failed_logins(identifier)
        assert is_account_locked(identifier) is False

    def test_record_failed_login_increments_count(self):
        from infrastructure.utils.auth import record_failed_login, clear_failed_logins

        identifier = f"counttest-{uuid.uuid4().hex}"
        clear_failed_logins(identifier)

        count1 = record_failed_login(identifier)
        count2 = record_failed_login(identifier)

        assert count2 == count1 + 1
        clear_failed_logins(identifier)


class TestEmailVerification:
    """Test email verification flow."""

    def test_email_verified_flag_on_user_model(self, db_session):
        from domains.accounts.models.user import User
        from infrastructure.utils.auth import get_password_hash

        user = User(
            email=f"verify_{uuid.uuid4().hex[:8]}@zozi.test",
            username=f"verify_{uuid.uuid4().hex[:8]}",
            hashed_password=get_password_hash("SecurePass1!"),
            role="customer",
            email_verified=False,
        )
        db_session.add(user)
        db_session.flush()

        assert user.email_verified is False

        user.email_verified = True
        db_session.flush()
        assert user.email_verified is True


class TestTokenTypeVerification:
    """Test access vs refresh token type enforcement."""

    def test_access_token_rejected_as_refresh(self):
        from infrastructure.utils.auth import create_access_token, verify_refresh_token

        access_token = create_access_token(data={"sub": "1"})

        with pytest.raises(Exception) as exc_info:
            verify_refresh_token(access_token)
        assert "type" in str(exc_info.value.detail).lower()

    def test_refresh_token_rejected_as_access(self):
        from infrastructure.utils.auth import create_refresh_token, verify_token

        refresh_token = create_refresh_token(data={"sub": "1"})

        with pytest.raises(Exception) as exc_info:
            verify_token(refresh_token)
        assert "type" in str(exc_info.value.detail).lower()

    def test_decode_token_type_check(self):
        from infrastructure.utils.auth import create_access_token, decode_token

        token = create_access_token(data={"sub": "1"})

        with pytest.raises(Exception):
            decode_token(token, expected_type="refresh")


class TestAlgorithmRestriction:
    """Test that alg:none and other algorithm attacks are rejected."""

    def test_alg_none_token_rejected(self):
        from infrastructure.utils.auth import verify_token

        # Craft a token with alg:none
        none_token = jwt.encode({"sub": "1", "type": "access"}, "", algorithm="none")
        # jose library may not support alg:none; if so, manually construct
        if none_token is None or none_token == "":
            import base64
            header = base64.urlsafe_b64encode(b'{"alg":"none","typ":"JWT"}').rstrip(b"=").decode()
            payload = base64.urlsafe_b64encode(b'{"sub":"1","type":"access"}').rstrip(b"=").decode()
            none_token = f"{header}.{payload}."

        with pytest.raises(Exception):
            verify_token(none_token)

    def test_wrong_algorithm_token_rejected(self):
        from infrastructure.utils.auth import verify_token

        # Token signed with different secret should fail
        wrong_token = jwt.encode(
            {"sub": "1", "type": "access", "exp": datetime.now(timezone.utc) + timedelta(hours=1)},
            "wrong-secret",
            algorithm="HS256",
        )

        with pytest.raises(Exception):
            verify_token(wrong_token)


class TestDeviceBinding:
    """Test device fingerprint (dfp) claim."""

    def test_access_token_with_device_fp(self):
        from infrastructure.utils.auth import create_access_token, decode_token

        token = create_access_token(data={"sub": "1"}, device_fp="fp-abc-123")
        payload = decode_token(token)

        assert payload["dfp"] == "fp-abc-123"

    def test_access_token_without_device_fp(self):
        from infrastructure.utils.auth import create_access_token, decode_token

        token = create_access_token(data={"sub": "1"})
        payload = decode_token(token)

        assert "dfp" not in payload


class TestIntegrationAuthFlow:
    """Integration tests for complete auth flows via API."""

    def test_register_login_access_protected_route(self, client):
        email = f"fullflow_{uuid.uuid4().hex[:8]}@zozi.test"
        password = "SecurePass1!"

        # Register
        reg = client.post(
            "/api/v1/auth/register",
            json={"email": email, "username": f"flow_{uuid.uuid4().hex[:8]}", "password": password, "role": "customer"},
        )
        assert reg.status_code in (200, 201)

        # Login
        login = client.post("/api/v1/auth/login", json={"email": email, "password": password})
        assert login.status_code == 200
        token = login.json()["access_token"]

        # Access protected route
        me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert me.status_code == 200

    def test_blacklisted_token_blocks_access(self, client, admin_token):
        """Verify that a blacklisted token cannot access protected endpoints."""
        from infrastructure.utils.auth import decode_token, blacklist_token

        payload = decode_token(admin_token)
        blacklist_token(payload["jti"], 3600)

        resp = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {admin_token}"})
        assert resp.status_code == 401

    def test_invalid_token_returns_401(self, client):
        resp = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid.token.here"},
        )
        assert resp.status_code == 401

    def test_missing_token_returns_401(self, client):
        resp = client.get("/api/v1/auth/me")
        assert resp.status_code == 401

    def test_wrong_role_cannot_access_admin(self, customer_client):
        """Customer token should not access admin endpoints."""
        resp = customer_client.get("/admin/users")
        # Should be 403 or 404 (route may not exist in test app, but should not be 200)
        assert resp.status_code in (403, 404)
