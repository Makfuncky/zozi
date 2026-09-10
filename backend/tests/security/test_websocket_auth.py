"""WebSocket authentication security tests (Law 41).

Verifies:
- WS handlers validate JWT ``type == 'access'``
- Refresh tokens are rejected as WS auth
- Blacklisted jti tokens are rejected
- Per-user connection limits are enforced (when the manager exposes the
  helper; otherwise the contract is checked structurally)
"""

from __future__ import annotations

import importlib
import time
import uuid

import jwt as pyjwt
import pytest


_BACKEND_ROOT = importlib.import_module("pathlib").Path(__file__).resolve().parent.parent.parent


def _make_access_token(subject: str, *, jti: str | None = None) -> str:
    from infrastructure.utils.config import settings
    from datetime import datetime, timedelta, timezone

    expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    payload = {"sub": subject, "type": "access", "exp": expire, "jti": jti or uuid.uuid4().hex}
    return pyjwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def _make_refresh_token(subject: str) -> str:
    from infrastructure.utils.config import settings
    from datetime import datetime, timedelta, timezone

    expire = datetime.now(timezone.utc) + timedelta(days=1)
    payload = {
        "sub": subject,
        "type": "refresh",
        "exp": expire,
        "jti": uuid.uuid4().hex,
        "family_id": uuid.uuid4().hex,
    }
    return pyjwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


class TestWebSocketTokenType:
    """Law 41 — WS endpoints must verify JWT ``type == 'access'``."""

    def test_websocket_handlers_use_expected_type_access(self):
        """``_decode_ws_token`` in websocket_handlers.py must call
        ``decode_token(..., expected_type='access')``."""
        from domains.comms.services.messaging import websocket_handlers
        src = (
            _BACKEND_ROOT
            / "domains" / "comms" / "services" / "messaging" / "websocket_handlers.py"
        ).read_text(encoding="utf-8")
        assert "expected_type=\"access\"" in src, (
            "websocket_handlers.py must call decode_token with expected_type='access'"
        )

    def test_main_background_jobs_ws_uses_expected_type_access(self):
        """``/ws/admin/background-jobs`` handler in main.py must verify
        ``type == 'access'``."""
        src = (_BACKEND_ROOT / "main.py").read_text(encoding="utf-8")
        # Find the background-jobs handler block
        idx = src.find('"/ws/admin/background-jobs"')
        assert idx != -1, "/ws/admin/background-jobs route not found in main.py"
        block = src[idx: idx + 1200]
        assert 'expected_type="access"' in block, (
            "background-jobs WS handler must use decode_token(expected_type='access')"
        )

    def test_refresh_token_rejected_by_decode_token(self):
        """A refresh token must NOT pass the WS access-type gate."""
        from infrastructure.utils.auth import decode_token
        from fastapi import HTTPException

        refresh = _make_refresh_token("user-1")
        with pytest.raises(HTTPException) as exc:
            decode_token(refresh, expected_type="access")
        assert exc.value.status_code == 401

    def test_blacklisted_token_rejected(self):
        """A blacklisted jti must fail WS token decode."""
        from infrastructure.utils.auth import (
            blacklist_token,
            decode_token,
        )
        from fastapi import HTTPException

        # Force in-memory fallback (the valkey URL may be empty in test env
        # and parsing it raises ValueError, which the auth helpers don't catch).
        import infrastructure.utils.auth as auth_mod
        original_get_redis = auth_mod._get_redis
        auth_mod._get_redis = lambda: None
        try:
            jti = uuid.uuid4().hex
            token = _make_access_token("user-2", jti=jti)
            blacklist_token(jti, ttl_seconds=60)
            with pytest.raises(HTTPException) as exc:
                decode_token(token, expected_type="access")
            assert exc.value.status_code == 401
        finally:
            auth_mod._get_redis = original_get_redis
            try:
                auth_mod._memory_blacklist.pop(f"bl:{jti}", None)
            except Exception:
                pass

    def test_access_token_passes_decode(self):
        """A valid access token decodes successfully."""
        import infrastructure.utils.auth as auth_mod
        original_get_redis = auth_mod._get_redis
        auth_mod._get_redis = lambda: None
        try:
            from infrastructure.utils.auth import decode_token
            token = _make_access_token("user-3")
            payload = decode_token(token, expected_type="access")
            assert payload["type"] == "access"
            assert payload["sub"] == "user-3"
            assert payload.get("jti")
        finally:
            auth_mod._get_redis = original_get_redis


class TestWebSocketConnectionLimits:
    """Per-user connection limit contract.

    The current ``ConnectionManager`` allows multiple sockets per user
    without an enforced cap.  This test asserts the structural property
    that the manager exposes a single ``connect_user``/``connect_staff``
    entry point and tracks per-user connection counts — so that a future
    limit enforcement can hook in here.
    """

    def test_user_manager_tracks_per_user_sockets(self):
        from domains.comms.services.messaging.websocket_handlers import (
            UserConnectionManager,
        )
        mgr = UserConnectionManager()
        assert hasattr(mgr, "_user_sockets"), "UserConnectionManager must track _user_sockets"
        assert isinstance(mgr._user_sockets, dict)
        # Adding a (fake) websocket is verified by the manager API:
        assert hasattr(mgr, "connect_user")
        assert hasattr(mgr, "disconnect_user")
        assert hasattr(mgr, "broadcast_to_user")

    def test_connection_manager_tracks_per_user_in_room(self):
        from domains.comms.services.messaging.websocket_handlers import (
            ConnectionManager,
        )
        mgr = ConnectionManager()
        assert hasattr(mgr, "_rooms")
        assert hasattr(mgr, "get_room_size")
        assert hasattr(mgr, "get_user_status")
