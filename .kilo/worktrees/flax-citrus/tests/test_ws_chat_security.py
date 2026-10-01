"""Regression tests for WebSocket chat authorization (VULN-001/002).

Security review findings this suite locks in:

- VULN-001  WebSocket chat IDOR -- an authenticated user could join ANY chat
            room (DM / group / entity thread) without being a member and
            (a) receive the live message stream, (b) inject messages, and
            (c) mark other users' messages read.
- VULN-002  Unauthenticated presence endpoints -- ``/ws/room/{id}/online`` and
            ``/ws/user/{id}/status`` exposed online/offline state to anyone.

Fix contract:
- ``websocket_chat`` closes with code 4003 (not a room member) / 4004 (room
  not found) BEFORE accepting the connection when the caller is not a member.
- DM rooms: caller must be ``participant_one`` / ``participant_two``.
- Group rooms: caller must have a ``GroupChatMember`` row.
- Entity threads: no membership model exists, so access is staff-only.
- Presence endpoints require a valid JWT (401) and enforce membership / staff
  rules (403).
"""
from __future__ import annotations

import pytest
from starlette.websockets import WebSocketDisconnect


@pytest.fixture
def chat_rooms(db_session):
    """Seed one room of each type + return the demo user ids involved.

    DM  -> between admin and supplier (customer is NOT a member)
    Group -> member list contains only admin (customer is NOT a member)
    Entity thread -> staff-only room (no membership model)
    """
    from data.models_core import (
        DirectChatRoom,
        GroupChatRoom,
        EntityChatThread,
    )
    from data.models_communication import GroupChatMember
    from models import User as UserModel

    def _user_id(email: str) -> int:
        user = db_session.query(UserModel).filter(UserModel.email == email).first()
        assert user is not None, f"demo user {email} missing"
        return int(user.id)

    admin_id = _user_id("admin@zozi.com")
    supplier_id = _user_id("supplier@zozi.com")

    dm = DirectChatRoom(
        chat_id="dm_security_test",
        participant_one=admin_id,
        participant_two=supplier_id,
    )
    db_session.add(dm)
    db_session.flush()

    group = GroupChatRoom(chat_id="group_security_test", name="Security Test")
    db_session.add(group)
    db_session.flush()
    db_session.add(GroupChatMember(room_id=group.id, user_id=admin_id, role="member"))

    thread = EntityChatThread(entity_type="support_ticket", entity_id=1, title="Sec")
    db_session.add(thread)
    db_session.flush()
    db_session.commit()

    return {
        "admin_id": admin_id,
        "supplier_id": supplier_id,
        "dm": dm.chat_id,
        "group": group.chat_id,
        "thread_id": int(thread.id),
    }


# ════════════════════════════════════════════════════════════════════
#  VULN-001  WebSocket chat membership enforcement
# ════════════════════════════════════════════════════════════════════

def _ws_url(room_id) -> str:
    return f"/api/v1/ws-chat/ws/chat/{room_id}"


def _assert_ws_rejected(client, url: str) -> None:
    """The server must close the socket (4003/4004) before accepting."""
    with pytest.raises(WebSocketDisconnect) as exc_info:
        with client.websocket_connect(url) as ws:
            ws.receive_json()
    assert exc_info.value.code in (4003, 4004)


def test_ws_chat_rejects_non_member_dm(
    client, db_session, chat_rooms, customer_token, monkeypatch
):
    """Customer (not a participant) must not join the admin<->supplier DM."""
    from routers import api_comms_realtime as realtime

    # WS handler opens its own session via get_db_session(); point it at the
    # test session so seeded rooms are visible.
    monkeypatch.setattr(realtime, "get_db_session", lambda: db_session)
    url = f"{_ws_url(chat_rooms['dm'])}?token={customer_token}"
    _assert_ws_rejected(client, url)


def test_ws_chat_rejects_non_member_group(
    client, db_session, chat_rooms, customer_token, monkeypatch
):
    """Customer (no GroupChatMember row) must not join the group room."""
    from routers import api_comms_realtime as realtime

    monkeypatch.setattr(realtime, "get_db_session", lambda: db_session)
    url = f"{_ws_url(chat_rooms['group'])}?token={customer_token}"
    _assert_ws_rejected(client, url)


def test_ws_chat_rejects_non_staff_entity_thread(
    client, db_session, chat_rooms, customer_token, monkeypatch
):
    """Entity threads have no membership model -> staff-only access."""
    from routers import api_comms_realtime as realtime

    monkeypatch.setattr(realtime, "get_db_session", lambda: db_session)
    url = f"{_ws_url(chat_rooms['thread_id'])}?token={customer_token}"
    _assert_ws_rejected(client, url)


def _assert_pong(client, url: str) -> None:
    """Connect, then drain broadcasts until the pong reply arrives.

    The server broadcasts ``user_joined`` to the room (including the newly
    connected socket) right after accepting, so the first frame is not
    necessarily the pong.
    """
    with client.websocket_connect(url) as ws:
        ws.send_json({"type": "ping"})
        for _ in range(20):
            reply = ws.receive_json()
            if reply.get("type") == "pong":
                return
        raise AssertionError("pong not received")


def test_ws_chat_accepts_dm_member(
    client, db_session, chat_rooms, admin_token, monkeypatch
):
    """Admin IS a DM participant -> connection succeeds and pings work."""
    from routers import api_comms_realtime as realtime

    monkeypatch.setattr(realtime, "get_db_session", lambda: db_session)
    _assert_pong(client, f"{_ws_url(chat_rooms['dm'])}?token={admin_token}")


def test_ws_chat_accepts_group_member(
    client, db_session, chat_rooms, admin_token, monkeypatch
):
    """Admin has a GroupChatMember row -> connection succeeds."""
    from routers import api_comms_realtime as realtime

    monkeypatch.setattr(realtime, "get_db_session", lambda: db_session)
    _assert_pong(client, f"{_ws_url(chat_rooms['group'])}?token={admin_token}")


def test_ws_chat_rejects_unknown_room(
    client, db_session, chat_rooms, admin_token, monkeypatch
):
    """A room id that matches no existing room is rejected (4004)."""
    from routers import api_comms_realtime as realtime

    monkeypatch.setattr(realtime, "get_db_session", lambda: db_session)
    url = f"{_ws_url('dm_does_not_exist')}?token={admin_token}"
    _assert_ws_rejected(client, url)


# ════════════════════════════════════════════════════════════════════
#  VULN-002  Presence endpoints must require auth + enforce rules
# ════════════════════════════════════════════════════════════════════

def test_online_users_requires_auth(client, chat_rooms):
    resp = client.get(f"/api/v1/ws-chat/ws/room/{chat_rooms['dm']}/online")
    assert resp.status_code == 401


def test_user_status_requires_auth(client, chat_rooms):
    resp = client.get(f"/api/v1/ws-chat/ws/user/{chat_rooms['admin_id']}/status")
    assert resp.status_code == 401


def test_online_users_forbidden_for_non_member(
    client, db_session, chat_rooms, customer_auth_headers
):
    """Authenticated customer who is not a member gets 403, not data."""
    resp = client.get(
        f"/api/v1/ws-chat/ws/room/{chat_rooms['dm']}/online",
        headers=customer_auth_headers,
    )
    assert resp.status_code == 403


def test_online_users_allowed_for_member(
    client, db_session, chat_rooms, admin_auth_headers
):
    """Authenticated admin (DM participant) may view room presence."""
    resp = client.get(
        f"/api/v1/ws-chat/ws/room/{chat_rooms['dm']}/online",
        headers=admin_auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["room_id"] == chat_rooms["dm"]


def test_user_status_self_allowed(
    client, db_session, chat_rooms, admin_auth_headers
):
    """A user may view their own presence status."""
    resp = client.get(
        f"/api/v1/ws-chat/ws/user/{chat_rooms['admin_id']}/status",
        headers=admin_auth_headers,
    )
    assert resp.status_code == 200


def test_user_status_other_user_forbidden_for_regular_user(
    client, db_session, chat_rooms, customer_auth_headers
):
    """A regular customer may NOT probe another user's presence."""
    resp = client.get(
        f"/api/v1/ws-chat/ws/user/{chat_rooms['admin_id']}/status",
        headers=customer_auth_headers,
    )
    assert resp.status_code == 403


def test_user_status_other_user_allowed_for_staff(
    client, db_session, chat_rooms, admin_auth_headers
):
    """Staff may view any user's presence."""
    resp = client.get(
        f"/api/v1/ws-chat/ws/user/{chat_rooms['supplier_id']}/status",
        headers=admin_auth_headers,
    )
    assert resp.status_code == 200
