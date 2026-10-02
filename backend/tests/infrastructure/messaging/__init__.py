"""Tests for the FILE-112 event_bus fixes.

Verifies:
  1. WIR-005: handler invocation retries with exponential backoff (max 5,
     1-2-4-8s + jitter).
  2. WIR-023: permanently failed handler payloads are routed to the Valkey
     dead-letter queue (``event_dead_letter``).
  3. WIR-028: events are appended to Valkey Stream (``event_stream``).
  4. WIR-035: ``unsubscribe()``, ``clear()``, and graceful ``shutdown()``.
"""
from __future__ import annotations

import json
import os
import sys
import time

import pytest

# Ensure backend root is importable
_BACKEND_ROOT = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")
if _BACKEND_ROOT not in sys.path:
    sys.path.insert(0, _BACKEND_ROOT)

os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-pytest-only")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _reset_bus():
    """Return event_bus module to a clean state between tests.

    Clears both the in-memory subscriber registry and the Valkey DLQ + stream
    so that test assertions against ``DLQ_KEY`` / ``STREAM_KEY`` are never
    polluted by prior runs or previous pytest invocations sharing db=0.
    """
    import infrastructure.messaging.events.event_bus as bus
    bus.clear()
    bus._subscribers = {}
    try:
        client = bus._get_valkey_client()
        if client is not None:
            before_stream = client.xlen(bus.STREAM_KEY)
            before_dlq = client.llen(bus.DLQ_KEY)
            print(f"[_reset_bus test_event_bus] BEFORE: stream={before_stream}, dlq={before_dlq}")
            # delete removes the list/stream entirely; UNLINK is non-blocking but
            # may not exist on Valkey, so try delete first.
            if hasattr(client, "delete"):
                r1 = client.delete(bus.DLQ_KEY)
                r2 = client.delete(bus.STREAM_KEY)
                print(f"[_reset_bus test_event_bus] delete: DLQ={r1}, STREAM={r2}")
            elif hasattr(client, "unlink"):
                r1 = client.unlink(bus.DLQ_KEY)
                r2 = client.unlink(bus.STREAM_KEY)
                print(f"[_reset_bus test_event_bus] unlink: DLQ={r1}, STREAM={r2}")
            after_stream = client.xlen(bus.STREAM_KEY)
            after_dlq = client.llen(bus.DLQ_KEY)
            print(f"[_reset_bus test_event_bus] AFTER: stream={after_stream}, dlq={after_dlq}")
    except Exception as exc:  # noqa: BLE001 - cleanup must not fail tests
        print(f"[_reset_bus test_event_bus] exception: {exc!r}")
    return bus


def _make_handler(results: list, value=None, exc=None):
    """Return a handler that records its outcome."""
    def handler(payload):
        if exc is not None:
            raise exc
        results.append((payload, value))
        return value
    return handler


# ---------------------------------------------------------------------------
# WIR-005: retry with exponential backoff
# ---------------------------------------------------------------------------

class TestRetryBehavior:
    """WIR-005: publish() retries handlers with 1-2-4-8s backoff."""

    def test_handler_succeeds_on_first_attempt(self):
        import infrastructure.messaging.events.event_bus as bus
        bus = _reset_bus()
        results = []
        handler = _make_handler(results, value="ok")
        bus.subscribe("test.event", handler)
        result = bus.publish("test.event", {"id": 1})
        assert result == "ok"
        assert len(results) == 1

    def test_handler_is_retried_up_to_max_attempts(self):
        import infrastructure.messaging.events.event_bus as bus
        bus = _reset_bus()
        call_count = {"n": 0}

        def flaky_handler(payload):
            call_count["n"] += 1
            if call_count["n"] < 3:
                raise RuntimeError("transient")
            return "recovered"

        bus.subscribe("test.event", flaky_handler)
        start = time.monotonic()
        result = bus.publish("test.event", {"id": 2})
        elapsed = time.monotonic() - start
        assert call_count["n"] == 3
        assert result == "recovered"
        # attempt 1 fails -> sleep ~1s, attempt 2 fails -> sleep ~2s
        assert elapsed >= 2.5, f"expected >= 2.5s backoff, got {elapsed:.2f}s"

    def test_handler_fails_after_max_retries(self):
        import infrastructure.messaging.events.event_bus as bus
        bus = _reset_bus()
        call_count = {"n": 0}

        def always_failing(payload):
            call_count["n"] += 1
            raise RuntimeError("permanent")

        bus.subscribe("test.event", always_failing)
        start = time.monotonic()
        result = bus.publish("test.event", {"id": 3})
        elapsed = time.monotonic() - start
        assert call_count["n"] == 5  # _MAX_RETRIES
        assert result is None
        # 1+2+4 = 7s of backoff before the final (5th) attempt
        assert elapsed >= 6.0, f"expected >= 6.0s backoff, got {elapsed:.2f}s"


# ---------------------------------------------------------------------------
# WIR-023: dead-letter queue on permanent failure
# ---------------------------------------------------------------------------

class TestDeadLetterQueue:
    """WIR-023: failed events are routed to event_dead_letter."""

    def test_dlq_receives_failed_event(self):
        import infrastructure.messaging.events.event_bus as bus
        bus = _reset_bus()
        client = bus._get_valkey_client()
        if client is None or not hasattr(client, "lpush"):
            pytest.skip("Valkey not available")

        def always_failing(payload):
            raise RuntimeError("dlq-test")

        bus.subscribe("test.event", always_failing)
        bus.publish("test.event", {"id": 10})

        entries = client.lrange(bus.DLQ_KEY, 0, -1)
        assert len(entries) >= 1
        body = json.loads(entries[0])
        assert body["event_type"] == "test.event"
        assert body["payload"] == {"id": 10}
        assert "dlq-test" in body["error"]
        client.delete(bus.DLQ_KEY)

    def test_dlq_not_used_on_success(self):
        import infrastructure.messaging.events.event_bus as bus
        bus = _reset_bus()
        client = bus._get_valkey_client()
        if client is None or not hasattr(client, "lpush"):
            pytest.skip("Valkey not available")

        def good_handler(payload):
            return "ok"

        bus.subscribe("test.event", good_handler)
        bus.publish("test.event", {"id": 11})
        assert client.llen(bus.DLQ_KEY) == 0


# ---------------------------------------------------------------------------
# WIR-028: Valkey Streams backing
# ---------------------------------------------------------------------------

class TestValkeyStreams:
    """WIR-028: events are appended to a Valkey Stream."""

    def test_publish_appends_to_stream(self):
        import infrastructure.messaging.events.event_bus as bus
        bus = _reset_bus()
        client = bus._get_valkey_client()
        if client is None or not hasattr(client, "xadd"):
            pytest.skip("Valkey not available")

        bus.publish("test.event", {"id": 20})
        # xlen should be >= 1
        length = client.xlen(bus.STREAM_KEY)
        assert length >= 1
        # Read back the entry
        entries = client.xread({bus.STREAM_KEY: "0-0"}, count=1)
        assert len(entries) == 1
        stream_name, msgs = entries[0]
        assert stream_name == bus.STREAM_KEY
        assert len(msgs) >= 1
        msg = msgs[0]
        assert msg["event_type"] == "test.event"
        payload = json.loads(msg["payload"])
        assert payload == {"id": 20}
        # cleanup
        client.xtrim(bus.STREAM_KEY, approximate=False, maxlen=0)

    def test_stream_key_is_constant(self):
        import infrastructure.messaging.events.event_bus as bus
        assert bus.STREAM_KEY == "event_stream"


# ---------------------------------------------------------------------------
# WIR-035: unsubscribe / clear / graceful shutdown
# ---------------------------------------------------------------------------

class TestGracefulShutdown:
    """WIR-035: unsubscribe, clear, and shutdown hooks."""

    def test_unsubscribe_removes_handler(self):
        import infrastructure.messaging.events.event_bus as bus
        bus = _reset_bus()
        results = []
        handler = _make_handler(results, value="v")
        bus.subscribe("test.event", handler)
        assert len(bus._subscribers["test.event"]) == 1
        bus.unsubscribe("test.event", handler)
        assert len(bus._subscribers.get("test.event", [])) == 0

    def test_clear_removes_all_subscribers(self):
        import infrastructure.messaging.events.event_bus as bus
        bus = _reset_bus()
        bus.subscribe("e1", lambda p: None)
        bus.subscribe("e2", lambda p: None)
        assert len(bus._subscribers) == 2
        bus.clear()
        assert len(bus._subscribers) == 0

    def test_shutdown_persists_to_stream_and_clears(self):
        import infrastructure.messaging.events.event_bus as bus
        bus = _reset_bus()
        client = bus._get_valkey_client()
        if client is None or not hasattr(client, "xadd"):
            pytest.skip("Valkey not available")

        bus.subscribe("test.event", lambda p: None)
        bus.shutdown()
        assert len(bus._subscribers) == 0
        entries = client.xread({bus.STREAM_KEY: "0-0"}, count=10)
        shutdown_msgs = []
        for _, msgs in entries:
            for msg in msgs:
                if msg.get("shutdown") == "true":
                    shutdown_msgs.append(msg)
        assert len(shutdown_msgs) >= 1
        client.xtrim(bus.STREAM_KEY, approximate=False, maxlen=0)
