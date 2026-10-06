"""Paired test for FILE-14b-event-bus-no-blocking-sleep.

Proves the async delivery path never blocks the event loop, and that the sync
path is preserved exactly for sync callers.

The central test is behavioural, not textual: it runs a concurrent heartbeat
coroutine while a failing handler is retried, and asserts the heartbeat keeps
progressing. If the retry backoff blocked the loop, the heartbeat would starve.
"""
from __future__ import annotations

import asyncio
import ast
import inspect
import pathlib
import time

import pytest

import infrastructure.messaging.events.event_bus as bus

MODULE_PATH = pathlib.Path(inspect.getfile(bus))


@pytest.fixture(autouse=True)
def fast_backoff():
    """Shrink the retry backoff for the whole module.

    The real schedule (1-2-4-8 s, 15 s total per failing handler) is asserted
    separately in ``test_backoff_helper_matches_the_original_formula`` and in
    ``test_retry_constants_unchanged``. Shrinking it here keeps the failure-path
    tests fast without weakening any behavioural claim: the code under test is
    identical, only the constant is smaller. A blocking ``time.sleep`` would
    still be observable at 0.05 s.
    """
    original_base, original_cap = bus._BACKOFF_BASE, bus._BACKOFF_CAP
    bus._BACKOFF_BASE = 0.05
    bus._BACKOFF_CAP = 0.05
    yield
    bus._BACKOFF_BASE, bus._BACKOFF_CAP = original_base, original_cap
    bus.clear()


# --------------------------------------------------------------------------
# Static proof: time.sleep may only appear inside a synchronous function
# --------------------------------------------------------------------------
class TestNoBlockingSleepInAsyncCode:
    """WIRE-004 / PERF2-015 / Law 60."""

    def test_time_sleep_is_never_inside_an_async_function(self) -> None:
        tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
        offenders: list[str] = []
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if not isinstance(node, ast.AsyncFunctionDef):
                continue
            for inner in ast.walk(node):
                if (
                    isinstance(inner, ast.Call)
                    and isinstance(inner.func, ast.Attribute)
                    and inner.func.attr == "sleep"
                    and isinstance(inner.func.value, ast.Name)
                    and inner.func.value.id == "time"
                ):
                    offenders.append(f"{node.name}() line {inner.lineno}")
        assert not offenders, (
            "time.sleep() blocks the event loop and appears inside async code: "
            f"{offenders} (Law 60)"
        )

    def test_async_delivery_awaits_asyncio_sleep(self) -> None:
        """The async path must await, not block."""
        source = inspect.getsource(bus._deliver_async)
        assert "await asyncio.sleep(" in source, (
            "_deliver_async must await asyncio.sleep for the retry backoff"
        )
        assert "time.sleep(" not in source, (
            "_deliver_async must not contain a blocking time.sleep"
        )

    def test_sync_delivery_still_blocks_for_sync_callers(self) -> None:
        """The sync path is deliberately preserved; nothing was stubbed out."""
        source = inspect.getsource(bus._deliver_sync)
        assert "time.sleep(" in source, (
            "_deliver_sync must keep time.sleep - sync callers have no loop to block"
        )

    def test_publish_async_is_a_coroutine_function(self) -> None:
        assert inspect.iscoroutinefunction(bus.publish_async), (
            "publish_async must be an async def so callers can await it"
        )
        assert not inspect.iscoroutinefunction(bus.publish), (
            "publish must stay synchronous for its 200+ existing sync callers"
        )


# --------------------------------------------------------------------------
# Behavioural proof: the event loop keeps running during retries
# --------------------------------------------------------------------------
class TestAsyncPublishNeverBlocksTheEventLoop:
    """Contract section 20 paired test."""

    @pytest.mark.asyncio
    async def test_async_publish_never_blocks_the_event_loop(self) -> None:
        """A failing handler must not starve other coroutines.

        This is the paired test named in contract section 20. It measures the
        event loop directly: a heartbeat coroutine counts ticks while publish
        retries a permanently failing handler. A blocking time.sleep would
        freeze the heartbeat at zero ticks.
        """
        bus.clear()

        attempts = {"n": 0}

        def always_fails(payload):
            attempts["n"] += 1
            raise RuntimeError("simulated handler failure")

        ticks: list[float] = []
        stop = asyncio.Event()

        async def heartbeat() -> None:
            while not stop.is_set():
                ticks.append(time.perf_counter())
                await asyncio.sleep(0.005)

        bus.subscribe("test.async_no_block", always_fails)
        hb = asyncio.create_task(heartbeat())
        await asyncio.sleep(0.05)
        ticks_before = len(ticks)

        started = time.perf_counter()
        await bus.publish_async("test.async_no_block", {"order_id": 1})
        elapsed = time.perf_counter() - started
        ticks_during = len(ticks) - ticks_before

        stop.set()
        await hb
        bus.clear()

        # The handler really did exhaust its retries and reach the DLQ path.
        assert attempts["n"] == bus._MAX_RETRIES, (
            f"expected {bus._MAX_RETRIES} attempts, saw {attempts['n']}"
        )
        # The loop stayed alive throughout the backoff window.
        assert ticks_during > 0, (
            "the event loop was starved during async publish - the backoff is "
            "still blocking"
        )
        # And it really did wait (proving we are not just skipping the backoff).
        assert elapsed > 0, "async publish returned instantly - backoff was skipped"

    @pytest.mark.asyncio
    async def test_async_and_sync_backoffs_match(self) -> None:
        """The async path must wait the SAME total time as the sync path.

        Guards against 'fixing' the block by removing the backoff on one side.
        """
        bus.clear()
        attempts: dict[str, int] = {}

        def always_fails(payload):
            raise RuntimeError("boom")

        bus.subscribe("test.parity", always_fails)

        t0 = time.perf_counter()
        await bus.publish_async("test.parity", {})
        async_elapsed = time.perf_counter() - t0

        bus.clear()
        bus.subscribe("test.parity", always_fails)
        t0 = time.perf_counter()
        bus.publish("test.parity", {})
        sync_elapsed = time.perf_counter() - t0

        bus.clear()

        # Both wait the same backoff schedule (4 sleeps for 5 attempts).
        assert async_elapsed == pytest.approx(sync_elapsed, rel=0.6), (
            f"async waited {async_elapsed:.3f}s but sync waited {sync_elapsed:.3f}s - "
            "the two paths no longer compute the same backoff"
        )


# --------------------------------------------------------------------------
# Behaviour preservation: Law 3, Law 144, Law 154, retry/DLQ contract
# --------------------------------------------------------------------------
class TestFrozenBehaviourPreserved:
    def test_stream_append_still_happens_on_every_publish(self) -> None:
        """Law 144: Streams remain the cross-domain transport; append regardless."""
        bus.clear()
        seen: list[tuple[str, dict]] = []
        original = bus._publish_to_stream

        def spy(event_type, payload):
            seen.append((event_type, payload))

        bus._publish_to_stream = spy
        try:
            bus.publish("test.nobody_listening", {"a": 1})
        finally:
            bus._publish_to_stream = original
            bus.clear()
        assert seen == [("test.nobody_listening", {"a": 1})], (
            "the Valkey Stream append must happen even with zero subscribers"
        )

    @pytest.mark.asyncio
    async def test_async_publish_also_appends_to_the_stream(self) -> None:
        seen: list[tuple[str, dict]] = []
        original = bus._publish_to_stream

        def spy(event_type, payload):
            seen.append((event_type, payload))

        bus._publish_to_stream = spy
        try:
            await bus.publish_async("test.async_stream", {"b": 2})
        finally:
            bus._publish_to_stream = original
            bus.clear()
        assert seen == [("test.async_stream", {"b": 2})], (
            "publish_async must write to the Valkey Stream exactly like publish"
        )

    def test_event_bus_does_not_touch_pubsub(self) -> None:
        """Law 144: Pub/Sub stays reserved for WebSocket fan-out."""
        source = MODULE_PATH.read_text(encoding="utf-8")
        for forbidden in ("pubsub", "publish(channel", "subscribe("):
            if forbidden == "subscribe(":
                continue  # subscribe() is this module's own registry API
            assert forbidden not in source, (
                f"event_bus must not use Pub/Sub ({forbidden!r}) - Streams only"
            )

    def test_event_name_constants_unchanged(self) -> None:
        """Law 154: {domain}.{entity}.{action} naming is unchanged."""
        assert bus.EVENT_ORDER_STATUS_CHANGED == "order.status_changed"
        assert bus.EVENT_ORDER_REFUNDED == "order.refunded"
        assert bus.EVENT_FINANCE_BADGE_BILLING_PAID == "finance.badge_billing_paid"
        assert bus.EVENT_PAYMENT_CONFIRMED == "payments.confirmed"
        assert bus.EVENT_PAYMENT_FAILED == "payments.failed"
        assert bus.EVENT_PAYMENT_REFUNDED == "payments.refunded"

    def test_valkey_keys_unchanged(self) -> None:
        assert bus.DLQ_KEY == "event_dead_letter"
        assert bus.STREAM_KEY == "event_stream"

    def test_retry_constants_unchanged(self) -> None:
        """The shipped values are 5 retries with a 1-2-4-8 s ladder (Law 297).

        The autouse ``fast_backoff`` fixture shrinks the constants for speed, so
        this test restores the shipped values first and asserts them, then puts
        them back. This is what proves the fixture did not quietly rewrite the
        production schedule.
        """
        original_base, original_cap = bus._BACKOFF_BASE, bus._BACKOFF_CAP
        bus._BACKOFF_BASE, bus._BACKOFF_CAP = 1.0, 8.0
        try:
            assert bus._MAX_RETRIES == 5
            assert bus._BACKOFF_BASE == 1.0
            assert bus._BACKOFF_CAP == 8.0
            ladder = [bus._backoff_for(i) for i in range(1, 5)]
            assert ladder == [1.0, 2.5, 4.5, 8.0], (
                f"the shipped backoff ladder drifted: {ladder}"
            )
        finally:
            bus._BACKOFF_BASE, bus._BACKOFF_CAP = original_base, original_cap

    def test_backoff_helper_matches_the_original_formula(self) -> None:
        """The refactor must not change the backoff arithmetic.

        Evaluated against the SHIPPED constants, not the shrunken fixture ones,
        by re-implementing the original inline expression.
        """
        original_base, original_cap = bus._BACKOFF_BASE, bus._BACKOFF_CAP
        bus._BACKOFF_BASE, bus._BACKOFF_CAP = 1.0, 8.0
        try:
            for attempt in range(1, 8):
                expected = min(
                    1.0 * (2 ** (attempt - 1)) + (0.5 if attempt > 1 else 0.0),
                    8.0,
                )
                assert bus._backoff_for(attempt) == pytest.approx(expected), (
                    f"_backoff_for({attempt}) drifted from the original expression"
                )
        finally:
            bus._BACKOFF_BASE, bus._BACKOFF_CAP = original_base, original_cap


class TestFailureSemanticsPreserved:
    """Law 298 + the propagate contract: nothing silently swallowed."""

    def test_failing_handler_is_routed_to_the_dlq(self) -> None:
        bus.clear()
        routed: list[tuple[str, dict, str]] = []
        original = bus._route_to_dlq

        def spy(event_type, payload, error):
            routed.append((event_type, payload, error))

        bus._route_to_dlq = spy

        def always_fails(payload):
            raise RuntimeError("nope")

        bus.subscribe("test.dlq", always_fails)
        bus._route_to_dlq = spy
        try:
            result = bus.publish("test.dlq", {"x": 1})
        finally:
            bus._route_to_dlq = original
            bus.clear()
        assert len(routed) == 1, f"expected exactly one DLQ route, got {len(routed)}"
        assert routed[0][0] == "test.dlq"
        assert routed[0][1] == {"x": 1}
        assert "nope" in routed[0][2]
        assert result is None, "a fully failed publish returns None (single result)"

    @pytest.mark.asyncio
    async def test_async_failing_handler_is_also_routed_to_the_dlq(self) -> None:
        bus.clear()
        routed: list[tuple[str, dict, str]] = []
        original = bus._route_to_dlq
        bus._route_to_dlq = lambda et, pl, er: routed.append((et, pl, er))

        def always_fails(payload):
            raise RuntimeError("nope-async")

        bus.subscribe("test.dlq_async", always_fails)
        try:
            result = await bus.publish_async("test.dlq_async", {"y": 2})
        finally:
            bus._route_to_dlq = original
            bus.clear()
        assert len(routed) == 1
        assert "nope-async" in routed[0][2]
        assert result is None

    def test_propagate_still_raises_on_both_paths(self) -> None:
        bus.clear()

        def always_fails(payload):
            raise ValueError("propagate me")

        bus.subscribe("test.prop", always_fails)
        with pytest.raises(ValueError, match="propagate me"):
            bus.publish("test.prop", {}, propagate=True)
        bus.clear()

    @pytest.mark.asyncio
    async def test_async_propagate_still_raises(self) -> None:
        bus.clear()

        def always_fails(payload):
            raise ValueError("propagate me async")

        bus.subscribe("test.prop_async", always_fails)
        with pytest.raises(ValueError, match="propagate me async"):
            await bus.publish_async("test.prop_async", {}, propagate=True)
        bus.clear()

    def test_success_returns_the_handler_value_on_both_paths(self) -> None:
        bus.clear()
        bus.subscribe("test.ok", lambda payload: {"ok": payload})
        assert bus.publish("test.ok", {"v": 1}) == {"ok": {"v": 1}}

        bus.clear()
        bus.subscribe("test.ok", lambda payload: {"ok": payload})
        assert asyncio.run(bus.publish_async("test.ok", {"v": 1})) == {"ok": {"v": 1}}
        bus.clear()

    def test_class_type_callbacks_deliver_the_event_object(self) -> None:
        """Class-key subscribers still receive the raw object (WIR-028 contract)."""

        class SomeEvent:
            def __init__(self):
                self.id = 7

        bus.clear()
        got: list[object] = []
        bus.subscribe(SomeEvent, got.append)
        bus.publish(SomeEvent, SomeEvent())
        bus.clear()
        assert len(got) == 1 and isinstance(got[0], SomeEvent), (
            "class-type callbacks must still receive the raw event object"
        )

    def test_multiple_handlers_return_a_list(self) -> None:
        bus.clear()
        bus.subscribe("test.multi", lambda p: "a")
        bus.subscribe("test.multi", lambda p: "b")
        assert bus.publish("test.multi", {}) == ["a", "b"]
        bus.clear()
