"""WebSocket authentication security tests (Law 41).

Verifies:
- WS handlers validate JWT ``type == 'access'``
- Refresh tokens are rejected as WS auth
- Blacklisted jti tokens are rejected
- Per-user connection limits are enforced (when the manager exposes the
  helper; otherwise the contract is checked structurally)
"""

from __future__ import annotations

import asyncio
import importlib
import time
import uuid

import jwt
import jwt as pyjwt
import pytest
from fastapi import HTTPException, WebSocketDisconnect


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
        import infrastructure.valkey.client as valkey_mod
        import infrastructure.security.auth as auth_mod
        original_valkey_client = valkey_mod.valkey_client
        valkey_mod.valkey_client = lambda: None
        try:
            jti = uuid.uuid4().hex
            token = _make_access_token("user-2", jti=jti)
            blacklist_token(jti, ttl_seconds=60)
            with pytest.raises(HTTPException) as exc:
                decode_token(token, expected_type="access")
            assert exc.value.status_code == 401
        finally:
            valkey_mod.valkey_client = original_valkey_client
            try:
                auth_mod._memory_blacklist.pop(f"bl:{jti}", None)
            except Exception:
                pass

    def test_access_token_passes_decode(self):
        """A valid access token decodes successfully."""
        import infrastructure.valkey.client as valkey_mod
        import infrastructure.security.auth as auth_mod
        original_valkey_client = valkey_mod.valkey_client
        valkey_mod.valkey_client = lambda: None
        try:
            from infrastructure.utils.auth import decode_token
            token = _make_access_token("user-3")
            payload = decode_token(token, expected_type="access")
            assert payload["type"] == "access"
            assert payload["sub"] == "user-3"
            assert payload.get("jti")
        finally:
            valkey_mod.valkey_client = original_valkey_client


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


class _FakeWebSocket:
    """ASGI WebSocket double that records accept/close instead of doing I/O.

    ``hold`` keeps the socket inside the receive loop so the manager state can
    be inspected while the connection is live.
    """

    def __init__(self, script=None, *, hold=False, peer=("203.0.113.7", 51000),
                 headers=None):
        self.client = type("_Peer", (), {"host": peer[0], "port": peer[1]})()
        self.headers = dict(headers or {})
        self.query_params = {}
        self.accepted = False
        self.closed_with = None
        self.sent = []
        self._script = list(script or [])
        self._hold = hold
        self._disconnected = False

    async def accept(self):
        self.accepted = True

    async def close(self, code=1000, reason=""):
        self.closed_with = (code, reason)

    async def receive_text(self):
        if self._script:
            return self._script.pop(0)
        if not self._hold and not self._disconnected:
            self._disconnected = True
            raise WebSocketDisconnect(code=1000)
        await asyncio.Event().wait()

    async def send_text(self, text):
        self.sent.append(text)


@pytest.fixture
def settings():
    from infrastructure.utils.config import settings as _settings

    return _settings


@pytest.fixture
def ws_env(monkeypatch):
    """Isolate the handler: no Valkey, and a clean connection manager."""
    import infrastructure.security.auth as auth_mod
    import infrastructure.valkey.client as valkey_mod
    from infrastructure.messaging.ws_manager import manager

    monkeypatch.setattr(valkey_mod, "valkey_client", lambda: None)
    manager.active_connections.clear()
    manager.user_connections.clear()
    yield manager
    manager.active_connections.clear()
    manager.user_connections.clear()
    auth_mod._memory_blacklist.clear()


class TestWebSocketUserHandlerDenial:
    """Law 41 — drive the real ``websocket_user`` handler with a fake socket.

    These three cases are the paired test named in contract section 20 and the
    tests required by section 10.
    """

    @pytest.mark.asyncio
    async def test_websocket_rejects_missing_token(self, ws_env):
        """No ``?token=`` -> the socket is closed and NEVER accepted."""
        from modules.admin.routers.comms import websocket_user

        ws = _FakeWebSocket()
        await websocket_user(ws, token=None)

        assert ws.accepted is False, "an unauthenticated socket must never be accepted"
        assert ws.closed_with is not None
        assert ws.closed_with[0] == 4001
        assert ws_env.active_connections == {}, "no socket may be registered"

    @pytest.mark.asyncio
    async def test_websocket_rejects_refresh_token(self, ws_env):
        """A REFRESH token must be refused (Law 41 / Law 33 type claim)."""
        from modules.admin.routers.comms import websocket_user

        ws = _FakeWebSocket()
        await websocket_user(ws, token=_make_refresh_token("user-refresh"))

        assert ws.accepted is False, "a refresh token must not open the socket"
        assert ws.closed_with is not None
        assert ws.closed_with[0] == 4001
        assert ws_env.active_connections == {}, "no socket may be registered"

    @pytest.mark.asyncio
    async def test_refresh_denial_is_not_caused_by_expiry(self, ws_env, settings):
        """The refresh token must be refused because of its ``type`` claim,
        not because it happens to be unparseable or expired."""
        from infrastructure.utils.auth import decode_token
        from modules.admin.routers.comms import websocket_user

        refresh = _make_refresh_token("user-refresh-type")
        # The token is otherwise perfectly valid: only the type differs.
        assert jwt.decode(refresh, settings.secret_key, algorithms=[settings.algorithm])

        ws = _FakeWebSocket()
        await websocket_user(ws, token=refresh)
        assert ws.accepted is False
        assert ws.closed_with[0] == 4001

        with pytest.raises(HTTPException) as exc:
            decode_token(refresh, expected_type="access")
        assert exc.value.status_code == 401
        assert "expected access" in str(exc.value.detail)

    @pytest.mark.asyncio
    async def test_rejection_is_logged_at_warning_with_peer_and_request_id(
        self, ws_env, caplog
    ):
        """BOOT2-006 / Law 43 + Law 59: the denial path must log at WARNING+
        with peer info and a request_id, and must NOT log the token (Law 282).

        This is the case that fails against the DEBUG-level implementation.
        """
        import logging

        from modules.admin.routers.comms import websocket_user

        token = _make_refresh_token("user-logged")
        ws = _FakeWebSocket(peer=("198.51.100.4", 44444))

        caplog.set_level(logging.DEBUG, logger="modules.admin.routers.comms")
        await websocket_user(ws, token=token)

        records = [r for r in caplog.records if r.name == "modules.admin.routers.comms"]
        assert records, "Law 59: the rejection path must emit a log record"

        levels = {r.levelno for r in records}
        assert logging.WARNING in levels, (
            f"Law 43: a rejected credential is a security event and must be "
            f"logged at WARNING+; saw levels={sorted(levels)}"
        )

        # Peer + request_id must be attached (Law 43, Law 93).
        assert any("198.51.100.4" in str(r.msg) or
                   "198.51.100.4" in str(getattr(r, "peer", "")) for r in records), (
            "Law 43: the peer address must be present in the security log"
        )
        assert any(getattr(r, "request_id", "") for r in records), (
            "Law 93: a request_id must be attached to the security log"
        )

        # Law 282: the credential itself must never reach the log.
        blob = " ".join(
            f"{r.msg} {r.args} {r.__dict__}" for r in records
        )
        assert token not in blob, "Law 282: the JWT must never be logged"

    @pytest.mark.asyncio
    async def test_websocket_accepts_valid_access_token(self, ws_env):
        """A valid ACCESS token connects, echoes, and is cleaned up on exit."""
        from modules.admin.routers.comms import USER_ROOM, websocket_user

        ws = _FakeWebSocket(script=['{"ping":1}'])
        await websocket_user(ws, token=_make_access_token("user-ok"))

        assert ws.accepted is True, "a valid access token must still connect"
        assert ws.closed_with is None
        assert ws.sent == ['{"ping": 1}']

        # Contract section 3: the finally-cleanup must not leak the socket.
        room = f"{USER_ROOM}:user-ok"
        assert ws_env.active_connections.get(room, []) == [], (
            "the socket must be removed from the connection manager on exit"
        )
