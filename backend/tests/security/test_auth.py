"""Resolution tests for FILE-15 backend/infrastructure/security/auth.py."""
from __future__ import annotations

import os

os.environ.setdefault("SECRET_KEY", os.getenv("TEST_SECRET_KEY", "a" * 32))

import pytest


def test_blacklist_token_valkey_outage_production():
    os.environ["APP_ENV"] = "production"
    try:
        from infrastructure.security.auth import blacklist_token

        import infrastructure.valkey.client as valkey_mod
        import infrastructure.security.auth as auth_module

        original_valkey_client = valkey_mod.valkey_client

        def fake_valkey_client():
            return None

        valkey_mod.valkey_client = fake_valkey_client
        try:
            jti = "test-jti-outage"
            blacklist_token(jti, ttl_seconds=60)
            assert jti in auth_module._memory_blacklist
        finally:
            valkey_mod.valkey_client = original_valkey_client
            auth_module._memory_blacklist.pop(jti, None)
    finally:
        os.environ.pop("APP_ENV", None)


def test_access_token_includes_device_fingerprint():
    from infrastructure.security.auth import create_access_token, decode_token

    token = create_access_token(data={"sub": "user-1", "role": "customer"})
    payload = decode_token(token, expected_type="access")
    assert "dfp" in payload
    assert isinstance(payload["dfp"], str)
    assert len(payload["dfp"]) > 0


def test_access_token_explicit_device_fp_preserved():
    from infrastructure.security.auth import create_access_token, decode_token

    explicit_fp = "explicit-fingerprint-123"
    token = create_access_token(data={"sub": "user-1"}, device_fp=explicit_fp)
    payload = decode_token(token, expected_type="access")
    assert payload["dfp"] == explicit_fp


def test_access_token_device_fp_deterministic_for_same_sub():
    from infrastructure.security.auth import create_access_token, decode_token

    token1 = create_access_token(data={"sub": "user-1"})
    token2 = create_access_token(data={"sub": "user-1"})
    payload1 = decode_token(token1, expected_type="access")
    payload2 = decode_token(token2, expected_type="access")
    assert payload1["dfp"] == payload2["dfp"]


def test_access_token_device_fp_differs_by_sub():
    from infrastructure.security.auth import create_access_token, decode_token

    token1 = create_access_token(data={"sub": "user-1"})
    token2 = create_access_token(data={"sub": "user-2"})
    payload1 = decode_token(token1, expected_type="access")
    payload2 = decode_token(token2, expected_type="access")
    assert payload1["dfp"] != payload2["dfp"]
