"""Tests for EventPublisher (WIR-006, WIR-028).

Verifies:
   1. EventPublisher emits a DeprecationWarning on instantiation (WIR-028).
   2. EventPublisher.publish delegates to event_bus: listener failures are
      retried (max 5 attempts, 1-2-4-8s backoff) and routed to DLQ.
   3. EventPublisher.publish writes event payload to Valkey Stream for
      durability (WIR-028 outbox pattern).
"""
from __future__ import annotations

import logging
import os
import sys
import warnings
from unittest.mock import MagicMock, patch

import pytest

# Ensure backend root is importable
_BACKEND_ROOT = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")
if _BACKEND_ROOT not in sys.path:
    sys.path.insert(0, _BACKEND_ROOT)

os.environ["APP_ENV"] = "test"
os.environ["SECRET_KEY"] = (
    "test-secret-key-for-pytest-only-please-ignore-this-is-not-a-real-secret-1234567890"
)

from infrastructure.observability.logging_config import setup_structlog  # noqa: E402

setup_structlog(log_level=logging.DEBUG)


class TestEventPublisher:
    """EventPublisher retry, DLQ, deprecation, and Valkey durability."""

    def test_publish_emits_deprecation_warning(self):
        from infrastructure.messaging.events.event_publisher import EventPublisher

        with pytest.warns(DeprecationWarning, match="EventPublisher is deprecated"):
            EventPublisher()

    def test_publish_retries_on_listener_failure_then_dlq(self):
        from infrastructure.messaging.events.event_publisher import EventPublisher

        calls = {"count": 0}

        def failing_listener(payload):
            calls["count"] += 1
            raise RuntimeError("listener boom")

        mock_client = MagicMock()
        mock_client.rpush.return_value = 1
        mock_client.xadd.return_value = "stream-id"

        with (
            pytest.warns(DeprecationWarning),
            patch(
                "infrastructure.valkey.client.valkey_client",
                return_value=mock_client,
            ),
        ):
            publisher = EventPublisher()
            # register_listener normalises class-type keys to string keys
            # in the canonical bus; use a string key directly for the test.
            publisher.register_listener("test-event", failing_listener)
            publisher.publish("test-event")

        assert calls["count"] == 5
        mock_client.rpush.assert_called_once()
        dlq_payload = mock_client.rpush.call_args[0][1]
        assert "listener boom" in dlq_payload
        assert "test-event" in dlq_payload
        mock_client.xadd.assert_called_once()
        stream_name = mock_client.xadd.call_args[0][0]
        assert "event_stream" in stream_name

    def test_publish_writes_to_valkey_stream(self):
        from infrastructure.messaging.events.event_publisher import EventPublisher

        received = []

        def good_listener(payload):
            received.append(payload)

        mock_client = MagicMock()
        mock_client.rpush.return_value = 1
        mock_client.xadd.return_value = "stream-id"

        with (
            pytest.warns(DeprecationWarning),
            patch(
                "infrastructure.valkey.client.valkey_client",
                return_value=mock_client,
            ),
        ):
            publisher = EventPublisher()
            publisher.register_listener("hello", good_listener)
            publisher.publish("hello")

        assert received == [{"value": "hello"}]
        mock_client.xadd.assert_called_once()
        stream_name = mock_client.xadd.call_args[0][0]
        assert "event_stream" in stream_name
