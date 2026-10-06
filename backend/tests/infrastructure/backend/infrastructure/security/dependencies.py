"""Coverage for FILE-265 SEC-007: ``verify_captcha`` must fail closed in production.

Contract: ``_audit/resolver/contracts/FILE-265-dependencies-batch.md``.

Finding: ``verify_captcha()`` returned immediately when ``TURNSTILE_SECRET_KEY`` was
not configured, skipping CAPTCHA verification entirely in every environment.

These tests pin the corrected behaviour only:
- production + no secret key  -> HTTPException 500 (fails closed)
- production + blank secret key -> HTTPException 500
- non-production + no secret key -> unchanged skip (dev/test workflow preserved)
- production + secret key but no token -> HTTPException 400 (unchanged)
- public signature and return annotation of ``verify_captcha`` are unchanged
"""
from __future__ import annotations

import inspect
import os
import sys

import pytest

_BACKEND_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..")
)
if _BACKEND_ROOT not in sys.path:
    sys.path.insert(0, _BACKEND_ROOT)

os.environ.setdefault("APP_ENV", "test")

from fastapi import HTTPException, status  # noqa: E402

from infrastructure.security import dependencies as shim  # noqa: E402


class _FakeRequest:
    """Minimal stand-in for the Request argument; captcha raises before network IO."""

    def __init__(self) -> None:
        self.headers = {"content-type": "application/json"}
        self._body = b"{}"
        self.client = None


def test_production_without_secret_key_fails_closed(monkeypatch):
    """Adversarial input: production deploy with TURNSTILE_SECRET_KEY unset.

    Before the fix this returned ``None`` and silently disabled bot protection.
    """
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.delenv("TURNSTILE_SECRET_KEY", raising=False)

    with pytest.raises(HTTPException) as excinfo:
        shim.verify_captcha(_FakeRequest())

    assert excinfo.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


def test_production_with_blank_secret_key_fails_closed(monkeypatch):
    """A whitespace-only key is still an unconfigured key."""
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("TURNSTILE_SECRET_KEY", "   ")

    with pytest.raises(HTTPException) as excinfo:
        shim.verify_captcha(_FakeRequest())

    assert excinfo.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


def test_production_with_key_but_no_token_still_returns_400(monkeypatch):
    """Existing fail-closed token check is unchanged."""
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("TURNSTILE_SECRET_KEY", "test-turnstile-secret")

    with pytest.raises(HTTPException) as excinfo:
        shim.verify_captcha(_FakeRequest())

    assert excinfo.value.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.parametrize("app_env", ["development", "test", ""])
def test_non_production_without_secret_key_still_skips(monkeypatch, app_env):
    """Development and test workflows keep skipping when the key is unset."""
    monkeypatch.setenv("APP_ENV", app_env)
    monkeypatch.delenv("TURNSTILE_SECRET_KEY", raising=False)

    assert shim.verify_captcha(_FakeRequest()) is None


def test_verify_captcha_public_signature_unchanged():
    """Other modules import this; the signature and return type are frozen."""
    signature = inspect.signature(shim.verify_captcha)

    assert list(signature.parameters) == ["request"]
    assert signature.return_annotation in (None, "None")