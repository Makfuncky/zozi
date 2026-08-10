"""Regression tests for Tier-1 security hardening.

Covers the genuine security defects fixed in this remediation pass:
  * JWT revocation enforced on the raw ``decode_token`` path (auth bypass).
  * Vault no longer derives its key from the JWT signing secret.
  * KMS fails closed (raises) instead of silently storing plaintext.
  * location_service CORS never combines wildcard origin with credentials.
  * RLS scope resolution is fail-closed for staff (X-Country-Code cannot
    disable scoping).
  * RLS interceptor raises when restricted without a scope.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
from types import SimpleNamespace

_BACKEND_ROOT = Path(__file__).resolve().parent.parent / "backend"
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

import pytest
from fastapi import HTTPException

import utils.auth as auth
from utils.vault import VaultService, VaultError
from utils.kms_encryption import KMSEncryption, KMSEncryptionError
from utils.rls_interceptor import (
    set_rls_context,
    rls_before_execute,
    SecurityContextMissingError,
)
from middleware.country_context import _compute_rls_scope


# ─────────────────────────────────────────────────────────────────────────────
# 1. JWT revocation enforced on decode_token (auth bypass fix)
# ─────────────────────────────────────────────────────────────────────────────
def test_decode_token_rejects_blacklisted_jti():
    token = auth.create_access_token({"sub": "1", "role": "customer"})
    jti = auth.decode_token(token).get("jti")
    assert jti
    auth.blacklist_token(jti, ttl_seconds=60)
    with pytest.raises(HTTPException):
        auth.decode_token(token)


def test_decode_token_accepts_valid_token():
    token = auth.create_access_token({"sub": "7", "role": "admin"})
    payload = auth.decode_token(token)
    assert payload["sub"] == "7"
    assert payload["role"] == "admin"


def test_decode_token_rejects_garbage():
    with pytest.raises(HTTPException):
        auth.decode_token("not.a.jwt")


# ─────────────────────────────────────────────────────────────────────────────
# 2. Vault key isolation (no JWT secret_key fallback)
# ─────────────────────────────────────────────────────────────────────────────
def test_vault_roundtrip_with_explicit_key(monkeypatch):
    monkeypatch.delenv("ZOZI_VAULT_MASTER_KEY", raising=False)
    monkeypatch.setattr(auth.settings, "_resolve_field_encryption_key", lambda: "")
    # Explicit key works.
    v = VaultService(master_key="explicit-master-key")
    ct = v.encrypt("super-secret-value")
    assert ct != "super-secret-value"
    assert v.decrypt(ct) == "super-secret-value"


def test_vault_refuses_when_no_key_and_not_jwt_secret(monkeypatch):
    monkeypatch.delenv("ZOZI_VAULT_MASTER_KEY", raising=False)
    monkeypatch.setattr(auth.settings, "_resolve_field_encryption_key", lambda: "")
    # Even if SECRET_KEY is present, the vault must NOT fall back to it.
    assert auth.settings.secret_key
    with pytest.raises(VaultError):
        VaultService()


# ─────────────────────────────────────────────────────────────────────────────
# 3. KMS fail-closed (no silent plaintext)
# ─────────────────────────────────────────────────────────────────────────────
def test_kms_encrypt_decrypt_roundtrip(monkeypatch):
    monkeypatch.delenv("KMS_MASTER_KEY", raising=False)
    kms = KMSEncryption(master_key="kms-test-key")
    ct = kms.encrypt("national-id-123")
    assert ct != "national-id-123"
    assert kms.decrypt(ct) == "national-id-123"


def test_kms_raises_when_key_missing(monkeypatch):
    monkeypatch.delenv("KMS_MASTER_KEY", raising=False)
    kms = KMSEncryption()  # no env key
    with pytest.raises(KMSEncryptionError):
        kms.encrypt("sensitive")
    with pytest.raises(KMSEncryptionError):
        kms.decrypt("anything")


# ─────────────────────────────────────────────────────────────────────────────
# 4. location_service CORS: never wildcard + credentials
# ─────────────────────────────────────────────────────────────────────────────
def test_cors_default_is_explicit_allowlist():
    from services.location_service.main import _resolve_cors

    orig = os.environ.get("LOCATION_CORS_ORIGINS")
    os.environ["LOCATION_CORS_ORIGINS"] = "http://localhost:3000,http://127.0.0.1:3000"
    try:
        origins, allow_credentials = _resolve_cors()
        assert origins == ["http://localhost:3000", "http://127.0.0.1:3000"]
        assert allow_credentials is True
    finally:
        if orig is None:
            os.environ.pop("LOCATION_CORS_ORIGINS", None)
        else:
            os.environ["LOCATION_CORS_ORIGINS"] = orig


def test_cors_wildcard_disables_credentials():
    from services.location_service.main import _resolve_cors

    orig = os.environ.get("LOCATION_CORS_ORIGINS")
    os.environ["LOCATION_CORS_ORIGINS"] = "*"
    try:
        origins, allow_credentials = _resolve_cors()
        assert origins == ["*"]
        assert allow_credentials is False  # must never be True with "*"
    finally:
        if orig is None:
            os.environ.pop("LOCATION_CORS_ORIGINS", None)
        else:
            os.environ["LOCATION_CORS_ORIGINS"] = orig


# ─────────────────────────────────────────────────────────────────────────────
# 5. RLS scope resolution: staff cannot disable scoping (fail-closed)
# ─────────────────────────────────────────────────────────────────────────────
def test_staff_always_restricted_to_assigned():
    staff = SimpleNamespace(role="staff", staff_country_codes=["AE", "OM"])
    scope, restricted, effective = _compute_rls_scope("staff", {"AE", "OM"}, None)
    assert restricted is True
    assert scope == frozenset({"AE", "OM"})


def test_staff_spoofed_header_ignored():
    # Staff assigned only to AE tries to escalate to SA via X-Country-Code.
    scope, restricted, effective = _compute_rls_scope("staff", {"AE"}, "SA")
    assert restricted is True
    assert scope == frozenset({"AE"})  # spoofed SA ignored
    assert effective == "AE"


def test_staff_valid_header_narrows_scope():
    scope, restricted, effective = _compute_rls_scope("staff", {"AE", "OM"}, "OM")
    assert restricted is True
    assert scope == frozenset({"OM"})
    assert effective == "OM"


def test_admin_global_unrestricted():
    scope, restricted, effective = _compute_rls_scope("admin", None, "AE")
    assert restricted is False
    assert scope is None
    assert effective == "AE"  # advisory only


def test_customer_not_country_restricted():
    scope, restricted, effective = _compute_rls_scope("customer", None, "AE")
    assert restricted is False
    assert scope == frozenset({"AE"})


def test_invalid_country_code_rejected():
    # normalize_country_code returns "" for garbage; it must not become a scope.
    scope, restricted, effective = _compute_rls_scope("staff", {"AE"}, "not-a-real-country!!")
    assert restricted is True
    assert scope == frozenset({"AE"})  # falls back to assigned


# ─────────────────────────────────────────────────────────────────────────────
# 6. RLS interceptor fails closed when restricted without scope
# ─────────────────────────────────────────────────────────────────────────────
def test_rls_interceptor_raises_when_restricted_without_scope():
    from sqlalchemy import select, table

    set_rls_context(None, is_restricted=True)
    clause = select(table("orders"))
    with pytest.raises(SecurityContextMissingError):
        rls_before_execute(None, clause, (), {}, {})


def test_rls_interceptor_injects_filter_when_scoped():
    from sqlalchemy import select, table

    set_rls_context(frozenset({"AE"}), is_restricted=True)
    clause = select(table("orders"))
    # Should not raise; returns a clause (with injected WHERE).
    result = rls_before_execute(None, clause, (), {}, {})
    assert result is not None
