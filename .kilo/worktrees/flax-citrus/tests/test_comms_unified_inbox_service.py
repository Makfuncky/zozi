"""Tests for the W1 refactor of routers/comms_unified.py.

Verifies DB access moved into services/comms/unified_inbox_service.py and
that the router is a thin orchestration layer. No real DB required.
"""
from __future__ import annotations

import datetime

import pytest

import services.comms.unified_inbox_service as svc
from routers import comms_unified as router_mod


def _dt(iso="2026-08-08T00:00:00"):
    return datetime.datetime.fromisoformat(iso)


class _FakeResult:
    def __init__(self, rows):
        self._rows = rows

    def mappings(self):
        return self

    def all(self):
        return self._rows


class _FakeDB:
    def __init__(self, rows):
        self.rows = rows
        self.captured = {}

    def execute(self, sql, params):
        self.captured["sql"] = str(sql)
        self.captured["params"] = params
        return _FakeResult(self.rows)


def test_get_unified_inbox_builds_query_and_shape():
    db = _FakeDB(
        rows=[{
            "id": "dm_1", "local_id": 1, "transport": "chat", "title": "Bob",
            "preview": "hi", "unread": 1, "updated_at": _dt(),
            "channel_type": "direct", "participants": 0,
            "peer_avatar": None, "folder": None,
        }]
    )
    out = svc.get_unified_inbox(
        db, user_id=42, lens="unread", transport="chat", limit=20, cursor=None
    )

    assert out["items"][0]["id"] == "dm_1"
    assert out["items"][0]["channelType"] == "direct"
    assert "UNION" in db.captured["sql"]
    assert "unread > 0" in db.captured["sql"]
    assert db.captured["params"]["user_id"] == 42
    assert db.captured["params"]["limit"] == 21  # limit + 1 for has_more
    assert out["hasMore"] is False
    assert out["nextCursor"] is None


def test_get_unified_inbox_cursor_decodes():
    db = _FakeDB(rows=[])
    import base64

    cursor = base64.urlsafe_b64encode("2026-01-01T00:00:00::5".encode()).decode()
    svc.get_unified_inbox(db, user_id=1, cursor=cursor, limit=10)
    assert db.captured["params"]["cursor_ts"] == "2026-01-01T00:00:00"
    assert db.captured["params"]["cursor_id"] == 5


def test_reset_unified_inbox_delegates_to_seed_and_audit(monkeypatch):
    seed_calls = []
    monkeypatch.setattr("jobs.seed_all.seed_comms", lambda: seed_calls.append(1))

    audit_calls = []
    monkeypatch.setattr(svc, "audit_log", lambda db, **kw: audit_calls.append(kw))

    out = svc.reset_unified_inbox(
        object(), user_id=7, username="admin", user_role="admin", ip_address="1.2.3.4"
    )

    assert out["status"] == "ok"
    assert seed_calls == [1]
    assert len(audit_calls) == 1
    assert audit_calls[0]["details"]["status"] == "success"
    assert audit_calls[0]["actor_id"] == 7
    assert audit_calls[0]["action"] == "inbox_reset"
    assert audit_calls[0]["entity"] == "comms"
    assert audit_calls[0]["entity_key"] == "unified_inbox"


def test_reset_unified_inbox_logs_failure_and_reraises(monkeypatch):
    monkeypatch.setattr("jobs.seed_all.seed_comms", lambda: (_ for _ in ()).throw(RuntimeError("boom")))

    audit_calls = []
    monkeypatch.setattr(svc, "audit_log", lambda db, **kw: audit_calls.append(kw))

    with pytest.raises(RuntimeError):
        svc.reset_unified_inbox(
            object(), user_id=7, username="a", user_role="admin", ip_address="x"
        )

    assert audit_calls and audit_calls[0]["details"]["status"] == "failure"
    assert "boom" in audit_calls[0]["details"]["error"]


def test_router_reset_delegates_to_service(monkeypatch):
    captured = {}

    def _fake_reset(db, **kw):
        captured.update(kw)
        return {"status": "ok", "message": "seeded"}

    monkeypatch.setattr(router_mod, "_reset_unified_inbox", _fake_reset)

    class _User:
        id = 7
        username = "admin"
        email = "a@b.c"
        role = "admin"

    class _Request:
        pass

    result = router_mod.reset_unified_inbox(request=_Request(), current_user=_User(), db=object())

    assert result == {"status": "ok", "message": "seeded"}
    assert captured["user_id"] == 7
    assert captured["username"] == "admin"


def test_router_inbox_delegates_to_service(monkeypatch):
    captured = {}

    def _fake_get(db, **kw):
        captured.update(kw)
        return {"items": [], "nextCursor": None, "hasMore": False}

    monkeypatch.setattr(router_mod, "_get_unified_inbox", _fake_get)

    class _User:
        id = 99

    result = router_mod.unified_inbox(
        lens="all", cursor=None, limit=50, transport=None, db=object(), current_user=_User()
    )

    assert result["items"] == []
    assert captured["user_id"] == 99
    assert captured["limit"] == 50
