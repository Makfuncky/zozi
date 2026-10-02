"""Paired test for FILE 107 DLQ findings (WIR-024 / OBS-003).

Verifies that ``event_bus.publish()`` routes permanently failed handler
payloads to the Valkey DLQ list (``event_dead_letter``), closing the gap
where the migration created the table but no application code wrote to it.
"""
from __future__ import annotations

import json
import os
import sys

import pytest

# Ensure backend root is importable
_BACKEND_ROOT = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")
if _BACKEND_ROOT not in sys.path:
    sys.path.insert(0, _BACKEND_ROOT)

os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-pytest-only")


def _reset_bus():
    """Return event_bus module to a clean state between tests.

    Clears in-memory subscriber state AND the Valkey DLQ + stream so that
    assertions are not polluted by prior tests or prior pytest invocations.
    """
    import infrastructure.messaging.events.event_bus as bus
    bus.clear()
    bus._subscribers = {}
    try:
        client = bus._get_valkey_client()
        if client is not None:
            for key in (bus.DLQ_KEY, bus.STREAM_KEY):
                if hasattr(client, "delete"):
                    client.delete(key)
                elif hasattr(client, "unlink"):
                    client.unlink(key)
    except Exception:  # noqa: BLE001 - cleanup must not fail tests
        pass
    return bus


# ---------------------------------------------------------------------------
# test_dlq_write: the paired test from the worklist Resolution section
# ---------------------------------------------------------------------------

class TestDLQWrite:
    """WIR-023 / OBS-003: permanently failed events are written to event_dead_letter."""

    def test_dlq_write_on_permanent_failure(self):
        """After max retries, the event payload must appear in the Valkey DLQ."""
        import infrastructure.messaging.events.event_bus as bus
        bus = _reset_bus()
        client = bus._get_valkey_client()
        if client is None or not hasattr(client, "rpush"):
            pytest.skip("Valkey not available")

        # Ensure DLQ is empty before the test
        try:
            client.delete(bus.DLQ_KEY)
        except Exception:  # noqa: BLE001
            pass

        def always_failing(payload):
            raise RuntimeError("dlq-write-test")

        bus.subscribe("test.dlq.write", always_failing)
        result = bus.publish("test.dlq.write", {"id": 107, "action": "test_dlq_write"})
        assert result is None  # all handlers failed

        # Verify the DLQ entry was written
        raw_entries = client.lrange(bus.DLQ_KEY, -1, -1)
        assert len(raw_entries) >= 1, "Expected at least one DLQ entry"
        body = json.loads(raw_entries[0])
        assert body["event_type"] == "test.dlq.write"
        assert body["payload"] == {"id": 107, "action": "test_dlq_write"}
        assert "dlq-write-test" in body["error"]

        # Cleanup
        client.delete(bus.DLQ_KEY)

    def test_dlq_not_used_on_success(self):
        """Successful handlers must NOT produce a DLQ entry."""
        import infrastructure.messaging.events.event_bus as bus
        bus = _reset_bus()
        client = bus._get_valkey_client()
        if client is None or not hasattr(client, "rpush"):
            pytest.skip("Valkey not available")

        try:
            client.delete(bus.DLQ_KEY)
        except Exception:  # noqa: BLE001
            pass

        def good_handler(payload):
            return "ok"

        bus.subscribe("test.dlq.success", good_handler)
        result = bus.publish("test.dlq.success", {"id": 107})
        assert result == "ok"
        assert client.llen(bus.DLQ_KEY) == 0

        client.delete(bus.DLQ_KEY)

    def test_dlq_persists_all_failed_handlers(self):
        """With multiple failing handlers, each produces its own DLQ entry."""
        import infrastructure.messaging.events.event_bus as bus
        bus = _reset_bus()
        client = bus._get_valkey_client()
        if client is None or not hasattr(client, "rpush"):
            pytest.skip("Valkey not available")

        try:
            client.delete(bus.DLQ_KEY)
        except Exception:  # noqa: BLE001
            pass

        def fail_a(payload):
            raise RuntimeError("handler-a")

        def fail_b(payload):
            raise RuntimeError("handler-b")

        bus.subscribe("test.dlq.multi", fail_a)
        bus.subscribe("test.dlq.multi", fail_b)
        bus.publish("test.dlq.multi", {"id": 107})

        depth = int(client.llen(bus.DLQ_KEY) or 0)
        assert depth == 2, f"Expected 2 DLQ entries, got {depth}"

        entries = [json.loads(e) for e in client.lrange(bus.DLQ_KEY, 0, -1)]
        errors = {e["error"] for e in entries}
        assert "handler-a" in errors
        assert "handler-b" in errors

        client.delete(bus.DLQ_KEY)
