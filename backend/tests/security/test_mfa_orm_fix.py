"""Minimal MFA ORM fix verification.

Tests that the MFA model uses EncryptedString and the service functions
are wired to MfaFactor instead of unmapped User attributes.
"""
from __future__ import annotations

import os
import sys

os.environ["FIELD_ENCRYPTION_SALT"] = "a" * 64
os.environ["FIELD_ENCRYPTION_KEY"] = "x" * 64
os.environ["APP_ENV"] = "test"
os.environ["CSRF_DISABLED"] = "true"
os.environ["SECRET_KEY"] = "test-secret-key-for-pytest-only-do-not-use-in-production"

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from infrastructure.security.encryption import EncryptedString


def test_mfa_factor_secret_uses_encrypted_string():
    from domains.accounts.models.mfa_factor import MfaFactor
    secret_col = MfaFactor.__table__.c.secret
    assert isinstance(secret_col.type, EncryptedString), (
        f"Expected EncryptedString, got {type(secret_col.type).__name__}"
    )


def test_user_does_not_have_unmapped_totp_columns():
    from domains.accounts.models.user import User
    assert not hasattr(User, "totp_enabled"), "User must not have totp_enabled"
    assert not hasattr(User, "totp_secret"), "User must not have totp_secret"
    assert not hasattr(User, "totp_recovery_codes"), "User must not have totp_recovery_codes"


def test_auth_service_uses_mfa_factor_not_user_attributes():
    import inspect
    from domains.accounts.services.auth import auth_service

    source = inspect.getsource(auth_service)

    # After the fix, auth_service should not reference unmapped User TOTP attributes
    assert "user.totp_enabled" not in source, "auth_service must not read user.totp_enabled"
    assert "user.totp_secret" not in source, "auth_service must not read user.totp_secret"
    assert "setattr(user, \"totp_enabled\"" not in source, "auth_service must not setattr totp_enabled"
    assert "setattr(user, \"totp_secret\"" not in source, "auth_service must not setattr totp_secret"
    assert "setattr(user, \"totp_recovery_codes\"" not in source, "auth_service must not setattr totp_recovery_codes"
