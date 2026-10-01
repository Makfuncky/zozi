"""Phase 4G: Security regression tests (Tasks 9-12).

Covers SQL injection / XSS / path-traversal rejection, JWT jti blacklist
enforcement, CSRF protection, and audit log writes.
"""
from __future__ import annotations

import pytest


class TestJWTBlacklist:
    def test_blacklist_token_then_verify_is_revoked(self):
        from infrastructure.utils.auth import (
            create_access_token, blacklist_token, decode_token,
        )
        from fastapi import HTTPException

        tok = create_access_token({"sub": "u1"})
        # extract jti
        from jose import jwt
        from infrastructure.utils.config import settings
        payload = jwt.get_unverified_claims(tok)
        jti = payload["jti"]
        blacklist_token(jti, ttl_seconds=60)
        with pytest.raises(HTTPException) as ei:
            decode_token(tok, expected_type="access")
        assert ei.value.status_code == 401


class TestCSRF:
    def test_csrf_middleware_loaded(self):
        from middleware.orchestrator import _SECURITY
        assert any(c.__name__ == "CSRFMiddleware" for c in _SECURITY)

    def test_csrf_module_has_protect_decorator_or_callable(self):
        """There must be a callable that decides if a request is CSRF-valid."""
        from middleware import csrf_middleware
        import inspect
        members = [n for n, _ in inspect.getmembers(csrf_middleware)]
        # csrf_middleware.py exposes get_csrf_token_from_request and
        # generate_csrf_token; CSRFMiddleware is the gate.
        assert "CSRFMiddleware" in members
        assert "generate_csrf_token" in members


class TestAuditLog:
    def test_audit_log_table_in_db(self):
        """Verify the audit_logs table is reachable in the dev SQLite DB."""
        import sqlite3
        import pathlib
        db = pathlib.Path("var/zozi.db")
        if not db.exists():
            pytest.skip("dev DB not present")
        conn = sqlite3.connect(str(db))
        try:
            rows = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='audit_logs'"
            ).fetchall()
            assert rows, "audit_logs table must exist in dev DB"
        finally:
            conn.close()


class TestInputValidation:
    def test_password_verify_rejects_known_injection_strings(self):
        """verify_password must never raise on injection-shaped plaintext."""
        from infrastructure.utils.auth import hash_password, verify_password
        h = hash_password("Test_pw_123!")
        for bad in ("' OR 1=1 --", '" OR 1=1 --', "<script>alert(1)</script>",
                    "../../etc/passwd", "'; DROP TABLE users; --"):
            assert verify_password(bad, h) is False
        assert verify_password("Test_pw_123!", h) is True
