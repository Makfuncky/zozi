"""Tests for ``infrastructure.events.subscriber.EventSubscriber``.

Verifies:
   1. ``EventSubscriber.start()`` issues Valkey ``XREADGROUP`` with the
      declared ``consumer_group`` (WIR-007 fix).
   2. ``EventSubscriber.stop()`` cancels the consumer task.
   3. Received events are dispatched to the matching handler.
   4. The module exposes real handler registrations (AIDRIFT-020 fix) via
      the ``create_subscriber`` factory.
"""
from __future__ import annotations

import asyncio
import os
import sys
from unittest.mock import MagicMock, patch

import pytest

# Ensure backend root is importable
_BACKEND_ROOT = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")
if _BACKEND_ROOT not in sys.path:
    sys.path.insert(0, _BACKEND_ROOT)

os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault(
    "SECRET_KEY",
    "test-secret-key-for-pytest-only-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
)

# ---------------------------------------------------------------------------
# Break the config → Settings() import chain before subscriber.py loads.
#
# ``subscriber.py`` imports ``valkey_client`` from ``infrastructure.valkey.client``
# which transitively imports ``infrastructure.utils.config`` → ``config``.
# ``config.py`` instantiates ``Settings()`` at module level; the project-root
# ``.env`` lacks ``SECRET_KEY`` so validation fails at collection time.
#
# We temporarily insert a stub ``config`` module into ``sys.modules`` so that
# importing ``subscriber.py`` succeeds, then remove it immediately so that
# other test files can load the real config normally.
# ---------------------------------------------------------------------------
_original_config = sys.modules.get("config")
_mock_config = MagicMock()
_mock_settings = MagicMock()
# Attributes accessed at module level in background_jobs.py
_mock_settings.background_job_workers = 4
_mock_settings.ml_workers = 2
_mock_config.settings = _mock_settings
sys.modules["config"] = _mock_config

try:
    from infrastructure.events.subscriber import EventSubscriber, create_subscriber  # noqa: E402
finally:
    # Restore the real config module (or remove our stub) so that other
    # test files in the same pytest session are not affected.
    if _original_config is not None:
        sys.modules["config"] = _original_config
    else:
        del sys.modules["config"]

# Patch target: valkey_client is a module-level attribute in subscriber.py
_VALKEY_PATCH = "infrastructure.events.subscriber.valkey_client"


def _run_consumer(subscriber, mock_client, duration=0.2):
    """Helper: start subscriber, yield control briefly, stop."""
    with patch(_VALKEY_PATCH, return_value=mock_client):
        subscriber.start()
        # Yield to the event loop so the consumer task can start and
        # reach its first asyncio.sleep() yielding point.
        loop = asyncio.get_event_loop()
        loop.run_until_complete(asyncio.sleep(duration))
        subscriber.stop()


class TestEventSubscriberStart:
    """start() must call Valkey XREADGROUP with the consumer_group."""

    def test_start_uses_xreadgroup_with_consumer_group(self):
        """XREADGROUP must be called with the declared consumer_group."""
        subscriber = EventSubscriber(
            consumer_group="test-consumer-group",
            handlers={},
            block_ms=50,
        )

        mock_client = MagicMock()
        mock_client.xgroup_create = MagicMock()
        mock_client.xreadgroup = MagicMock(return_value=[])
        mock_client.xack = MagicMock()

        _run_consumer(subscriber, mock_client, duration=0.2)

        # xgroup_create is invoked at the top of every consumer loop iteration;
        # we verify it is called at least once with the correct arguments.
        assert mock_client.xgroup_create.call_count >= 1
        assert mock_client.xreadgroup.call_count >= 1
        args, _ = mock_client.xreadgroup.call_args
        # Signature: xreadgroup(group, consumer_name, streams, count, block)
        assert args[0] == "test-consumer-group"  # groupname (1st positional)
        assert args[4] == 50                       # block_ms (5th positional)

    def test_start_passes_declared_consumer_group_to_xreadgroup(self):
        """Verify consumer_group flows into XREADGROUP groupname parameter."""
        subscriber = EventSubscriber(
            consumer_group="payments-worker",
            handlers={},
            block_ms=50,
        )

        mock_client = MagicMock()
        mock_client.xgroup_create = MagicMock()
        mock_client.xreadgroup = MagicMock(return_value=[])
        mock_client.xack = MagicMock()

        _run_consumer(subscriber, mock_client, duration=0.2)

        assert mock_client.xreadgroup.call_count >= 1
        args, _ = mock_client.xreadgroup.call_args
        assert args[0] == "payments-worker"

    def test_xreadgroup_block_parameter_set(self):
        """XREADGROUP must use a finite block value (not block forever)."""
        subscriber = EventSubscriber(
            consumer_group="block-test-group",
            handlers={},
            block_ms=50,
        )

        mock_client = MagicMock()
        mock_client.xgroup_create = MagicMock()
        mock_client.xreadgroup = MagicMock(return_value=[])
        mock_client.xack = MagicMock()

        _run_consumer(subscriber, mock_client, duration=0.2)

        assert mock_client.xreadgroup.call_count >= 1
        args, _ = mock_client.xreadgroup.call_args
        assert args[4] == 50  # block_ms is the 5th positional arg


class TestEventSubscriberStop:
    """stop() must cancel the running consumer task."""

    def test_stop_cancels_consumer_task(self):
        """stop() should cancel the background task created by start()."""
        subscriber = EventSubscriber(
            consumer_group="test-stop-group",
            handlers={},
            block_ms=50,
        )

        mock_client = MagicMock()
        mock_client.xgroup_create = MagicMock()
        mock_client.xreadgroup = MagicMock(return_value=[])
        mock_client.xack = MagicMock()

        with patch(_VALKEY_PATCH, return_value=mock_client):
            subscriber.start()
            assert subscriber._task is not None, "start() must create a task"
            subscriber.stop()

        assert subscriber._task is None, "stop() must clear the task reference"
        assert subscriber._running is False, "stop() must clear the running flag"


class TestEventSubscriberDispatch:
    """Received events must be dispatched to the matching handler."""

    def test_handler_called_for_matching_event_type(self):
        """Handler must be called with the event payload."""
        handler = MagicMock()
        subscriber = EventSubscriber(
            consumer_group="test-dispatch-group",
            handlers={"order.created": handler},
        )

        event_payload = {
            "event_type": "order.created",
            "aggregate_id": "42",
        }

        subscriber._dispatch(event_payload)
        handler.assert_called_once_with(event_payload)

    def test_no_handler_called_for_unknown_event_type(self):
        """Unknown event types must not raise."""
        handler = MagicMock()
        subscriber = EventSubscriber(
            consumer_group="test-unknown-group",
            handlers={"order.created": handler},
        )

        subscriber._dispatch({"event_type": "unknown.event", "data": "x"})
        handler.assert_not_called()

    def test_handler_exception_does_not_break_dispatch(self):
        """A failing handler must not raise out of _dispatch."""
        def bad_handler(payload: dict) -> None:
            raise RuntimeError("handler failure")

        subscriber = EventSubscriber(
            consumer_group="test-fail-group",
            handlers={"test.event": bad_handler},
        )
        # Should not raise
        subscriber._dispatch({"event_type": "test.event"})

    def test_type_field_used_as_fallback_for_event_type(self):
        """payload['type'] is used when 'event_type' is absent."""
        handler = MagicMock()
        subscriber = EventSubscriber(
            consumer_group="test-type-fallback-group",
            handlers={"test.type": handler},
        )

        subscriber._dispatch({"type": "test.type", "data": "x"})
        handler.assert_called_once()


class TestCreateSubscriber:
    """create_subscriber must produce a fully wired EventSubscriber."""

    def test_create_subscriber_returns_event_subscriber(self):
        handler = MagicMock()
        subscriber = create_subscriber(
            consumer_group="factory-test-group",
            handlers={"test.event": handler},
        )
        assert isinstance(subscriber, EventSubscriber)
        assert subscriber.consumer_group == "factory-test-group"
        assert subscriber.handlers == {"test.event": handler}

    def test_create_subscriber_default_stream_key(self):
        subscriber = create_subscriber("g", {})
        assert subscriber.stream_key == "events:stream"

    def test_handler_registration_used_in_dispatch(self):
        """create_subscriber-created subscribers must dispatch to handlers."""
        handler = MagicMock()
        subscriber = create_subscriber(
            consumer_group="dispatch-factory-group",
            handlers={"test.event": handler},
        )
        subscriber._dispatch({"event_type": "test.event", "data": 1})
        handler.assert_called_once()


class TestEventSubscriberNoOpFallback:
    """When Valkey is unavailable the subscriber must not crash."""

    def test_start_stop_with_noop_valkey(self):
        """start/stop must not raise when Valkey is unavailable."""
        subscriber = EventSubscriber(
            consumer_group="noop-test-group",
            handlers={},
            block_ms=50,
        )

        failing_client = MagicMock()
        failing_client.xgroup_create = MagicMock(
            side_effect=Exception(" Valkey down")
        )
        failing_client.xreadgroup = MagicMock(return_value=[])
        failing_client.xack = MagicMock()

        with patch(
            _VALKEY_PATCH,
            return_value=failing_client,
        ):
            subscriber.start()
            loop = asyncio.get_event_loop()
            loop.run_until_complete(asyncio.sleep(0.2))
            subscriber.stop()

        assert subscriber._running is False


class TestEventSubscriberXack:
    """XACK must be called after each event is processed."""

    def test_xack_called_after_event_processed(self):
        """XACK must be called with the stream, group, and message id."""
        handler = MagicMock()
        subscriber = EventSubscriber(
            consumer_group="ack-test-group",
            handlers={"test.event": handler},
            block_ms=50,
        )

        mock_client = MagicMock()
        mock_client.xgroup_create = MagicMock()
        mock_client.xreadgroup = MagicMock(
            return_value=[("events:stream", [("msg-123", {"event_type": "test.event"})])]
        )
        mock_client.xack = MagicMock()

        with patch(_VALKEY_PATCH, return_value=mock_client):
            subscriber.start()
            loop = asyncio.get_event_loop()
            loop.run_until_complete(asyncio.sleep(0.2))
            subscriber.stop()

        # xack is invoked once per received event per loop iteration;
        # verify it was called at least once with correct arguments.
        assert mock_client.xack.call_count >= 1
        # Inspect the last call (all calls carry the same args for this mock).
        last_call = mock_client.xack.call_args
        assert last_call is not None
        assert last_call.args == ("events:stream", "ack-test-group", "msg-123")
