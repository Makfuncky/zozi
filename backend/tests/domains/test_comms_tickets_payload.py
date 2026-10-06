"""Contract tests for ``build_ticket_payload`` (FILE 173 / BOOT2-005).

``modules/admin/routers/tickets.py`` imports ``build_ticket_payload`` from
``domains.comms.services.tickets.tickets_service`` at module level and calls it
from four endpoints (get / reply / status). When the symbol was missing the
ImportError killed the whole admin tickets router, which
``modules/admin/routers/__init__.py`` only logged as
``Skipping router tickets: ...`` before continuing to boot. All four endpoints
then answered 404 in production while ``/health`` stayed green.

These tests pin the response contract the four frozen call sites depend on, so
the router and the service cannot drift apart again:

* shape - the exact keys and JSON types the sibling ``admin_list_tickets``
  dict literal returns, plus the ``messages`` list,
* invariant - an absent or empty message collection must serialize, not raise,
* error path - ``ticket=None`` is a programming error at every call site (each
  raises 404 first), so the serializer raises ``ValueError`` instead of
  fabricating an all-null payload that would 200 with empty data,
* eager relationships (Law 45) - the ``messages=None`` fallback reads an
  already-loaded collection out of the instance ``__dict__`` and never
  triggers a lazy SELECT.
"""
from __future__ import annotations

import datetime as dt

import pytest

from domains.comms.models.communication import TicketMessage
from domains.comms.services.tickets.tickets_service import build_ticket_payload
from domains.governance.ports import SupportTicket

REQUIRED_KEYS = {
    "id",
    "user_id",
    "subject",
    "message",
    "status",
    "priority",
    "created_at",
    "updated_at",
    "messages",
}

MESSAGE_KEYS = {"id", "sender_id", "message", "is_admin", "created_at"}


def _ticket(**overrides) -> SupportTicket:
    """Build a detached SupportTicket instance - no session, no DB write."""
    values = {
        "id": 7,
        "user_id": 42,
        "subject": "Order not delivered",
        "status": "open",
        "priority": "high",
    }
    values.update(overrides)
    return SupportTicket(**values)


def _msg(**overrides) -> TicketMessage:
    values = {
        "id": 11,
        "ticket_id": 7,
        "sender_id": 42,
        "message": "Where is my order?",
        "is_admin": False,
    }
    values.update(overrides)
    return TicketMessage(**values)


# ---------------------------------------------------------------- shape


def test_build_ticket_payload_shape() -> None:
    """All required keys are present with JSON-safe types (Law 89)."""
    payload = build_ticket_payload(None, _ticket(), [_msg()])

    assert REQUIRED_KEYS.issubset(payload.keys()), (
        f"missing keys: {sorted(REQUIRED_KEYS - payload.keys())}"
    )
    assert payload["id"] == 7
    assert payload["user_id"] == 42
    assert payload["subject"] == "Order not delivered"
    assert payload["message"] == "Where is my order?"
    assert payload["status"] == "open"
    assert payload["priority"] == "high"

    # Never hand a raw datetime back to FastAPI. A detached instance has not
    # been through the DB server_default yet, so None is the correct output
    # here - same as the sibling `admin_list_tickets`. Populated datetimes are
    # covered by test_build_ticket_payload_serializes_datetimes_as_iso.
    assert payload["created_at"] is None or isinstance(payload["created_at"], str)
    assert payload["updated_at"] is None or isinstance(payload["updated_at"], str)

    assert isinstance(payload["messages"], list)
    assert len(payload["messages"]) == 1
    entry = payload["messages"][0]
    assert MESSAGE_KEYS.issubset(entry.keys())
    assert entry["id"] == 11
    assert entry["sender_id"] == 42
    assert entry["message"] == "Where is my order?"
    assert entry["is_admin"] is False
    assert entry["created_at"] is None or isinstance(entry["created_at"], str)

    # Nothing datetime-shaped survives anywhere in the payload.
    def _no_datetimes(node) -> bool:
        if isinstance(node, dict):
            return all(_no_datetimes(v) for v in node.values())
        if isinstance(node, list):
            return all(_no_datetimes(v) for v in node)
        return not isinstance(node, dt.datetime)

    assert _no_datetimes(payload), "payload leaked a raw datetime object"


def test_build_ticket_payload_serializes_datetimes_as_iso() -> None:
    """Datetimes become ISO-8601 strings, matching admin_list_tickets."""
    created = dt.datetime(2026, 10, 5, 12, 30, 0, tzinfo=dt.timezone.utc)
    ticket = _ticket()
    ticket.created_at = created
    ticket.updated_at = created + dt.timedelta(hours=2)

    payload = build_ticket_payload(None, ticket, [])

    assert payload["created_at"] == created.isoformat()
    assert payload["updated_at"] == (created + dt.timedelta(hours=2)).isoformat()


def test_build_ticket_payload_first_message_convenience_field() -> None:
    """`message` mirrors the first row of `messages`, like admin_list_tickets."""
    msgs = [_msg(id=1, message="first"), _msg(id=2, message="second")]
    payload = build_ticket_payload(None, _ticket(), msgs)

    assert payload["message"] == "first"
    assert [m["id"] for m in payload["messages"]] == [1, 2]


# ------------------------------------------------------------ invariant


def test_build_ticket_payload_handles_empty_messages() -> None:
    """Empty list and missing collection both serialize without raising."""
    for messages in ([], None):
        payload = build_ticket_payload(None, _ticket(), messages)
        assert payload["messages"] == []
        assert payload["message"] == ""
        assert payload["id"] == 7


def test_build_ticket_payload_null_timestamps_stay_none() -> None:
    """created_at / updated_at are None before the DB server default lands."""
    payload = build_ticket_payload(None, _ticket(), [_msg()])

    assert payload["created_at"] is None
    assert payload["updated_at"] is None
    assert payload["messages"][0]["created_at"] is None


def test_build_ticket_payload_coerces_is_admin() -> None:
    """`is_admin` is always a real bool, never None or a string."""
    payload = build_ticket_payload(
        None, _ticket(), [_msg(is_admin=None), _msg(is_admin=True)]
    )

    assert [m["is_admin"] for m in payload["messages"]] == [False, True]


# ------------------------------------------------------------ error path


def test_build_ticket_payload_none_ticket_raises() -> None:
    """ticket=None is a caller bug; raise instead of fabricating a payload.

    Every one of the four call sites resolves the ticket first and raises 404
    if it is missing, so None can only mean the serializer was called wrong. A
    silent all-null dict would turn a 404 into a 200 with empty data.
    """
    with pytest.raises(ValueError, match="requires a SupportTicket"):
        build_ticket_payload(None, None, [])


# ------------------------------------------------------------ Law 45


def test_build_ticket_payload_none_messages_uses_eager_collection() -> None:
    """The None fallback reads the ALREADY-LOADED collection, no lazy load.

    ``get_ticket_with_details`` and ``get_ticket_by_id`` both
    ``selectinload(SupportTicket.messages)``, so the collection is present in
    the instance ``__dict__``. The serializer must use it without emitting a
    query - that is why it reads ``__dict__`` directly instead of going through
    ``ticket.messages``.
    """
    ticket = _ticket()
    msgs = [_msg(id=1, message="eager")]
    # Populate the instance state the way selectinload does.
    object.__setattr__(ticket, "messages", msgs)

    payload = build_ticket_payload(None, ticket, None)

    assert [m["id"] for m in payload["messages"]] == [1]
    assert payload["message"] == "eager"


def test_build_ticket_payload_unloaded_messages_does_not_trigger_load() -> None:
    """An unloaded relationship yields [] instead of a lazy SELECT.

    A bare (never-selectinloaded) instance has no ``messages`` key in
    ``__dict__``. Accessing ``ticket.messages`` on it would emit SQL, so the
    serializer must not.
    """
    ticket = _ticket()
    ticket.__dict__.pop("messages", None)

    payload = build_ticket_payload(None, ticket, None)

    assert payload["messages"] == []
    assert payload["message"] == ""


# ------------------------------------------ router/service cannot drift


def test_admin_tickets_router_imports_the_payload_builder() -> None:
    """The frozen consumer must import the symbol it calls (BOOT2-005)."""
    from domains.comms.services.tickets import tickets_service

    assert callable(tickets_service.build_ticket_payload)

    import importlib

    router = importlib.import_module("modules.admin.routers.tickets")
    paths = [getattr(r, "path", None) for r in router.router.routes]
    for expected in (
        "/admin/tickets",
        "/admin/tickets/{ticket_id}",
        "/admin/tickets/{ticket_id}/reply",
        "/admin/tickets/{ticket_id}/status",
    ):
        assert expected in paths, f"admin tickets router lost endpoint {expected}"
