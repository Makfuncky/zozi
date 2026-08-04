"""Tests for circuit breaker with async support."""
import asyncio
import time
import pytest

from utils.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerRegistry,
    CircuitBreakerError,
    circuit_break,
    circuit_break_with_config,
    get_breaker,
    CircuitState,
)


def _success_func():
    return "ok"


def _failing_func():
    raise ValueError("failure")


async def _async_success_func():
    await asyncio.sleep(0.01)
    return "async-ok"


async def _async_failing_func():
    await asyncio.sleep(0.01)
    raise ValueError("async-failure")


class TestCircuitBreaker:
    def test_initial_state_closed(self):
        cb = CircuitBreaker(name="test")
        assert cb.get_stats().state == CircuitState.CLOSED

    def test_successful_call(self):
        cb = CircuitBreaker(name="test")
        result = cb.call(_success_func)
        assert result == "ok"
        stats = cb.get_stats()
        assert stats.success_count == 1
        assert stats.failure_count == 0

    def test_failure_opens_circuit(self):
        cb = CircuitBreaker(name="test-fail-open", failure_threshold=2)
        with pytest.raises(ValueError):
            cb.call(_failing_func)
        assert cb.get_stats().state == CircuitState.CLOSED  # only 1 failure

        with pytest.raises(ValueError):
            cb.call(_failing_func)
        assert cb.get_stats().state == CircuitState.OPEN

    def test_open_circuit_raises_error(self):
        cb = CircuitBreaker(name="test-open", failure_threshold=1)
        with pytest.raises(ValueError):
            cb.call(_failing_func)
        assert cb.get_stats().state == CircuitState.OPEN

        with pytest.raises(CircuitBreakerError):
            cb.call(_success_func)

    def test_half_open_on_timeout(self):
        cb = CircuitBreaker(
            name="test-half-open",
            failure_threshold=1,
            recovery_timeout=0.1,
        )
        with pytest.raises(ValueError):
            cb.call(_failing_func)
        assert cb.get_stats().state == CircuitState.OPEN

        time.sleep(0.15)
        result = cb.call(lambda: "recovered")
        assert result == "recovered"
        assert cb.get_stats().state == CircuitState.CLOSED

    def test_reset(self):
        cb = CircuitBreaker(name="test-reset", failure_threshold=1)
        with pytest.raises(ValueError):
            cb.call(_failing_func)
        assert cb.get_stats().state == CircuitState.OPEN

        cb.reset()
        stats = cb.get_stats()
        assert stats.state == CircuitState.CLOSED
        assert stats.failure_count == 0
        assert stats.success_count == 0

    def test_get_stats_returns_copy(self):
        cb = CircuitBreaker(name="test-stats-copy")
        cb.call(_success_func)
        stats = cb.get_stats()
        assert stats.success_count == 1
        stats.success_count = 999
        assert cb.get_stats().success_count == 1  # original unchanged


class TestAsyncCircuitBreaker:
    @pytest.mark.asyncio
    async def test_async_successful_call(self):
        cb = CircuitBreaker(name="async-test")
        result = await cb.call_async(_async_success_func)
        assert result == "async-ok"
        stats = cb.get_stats()
        assert stats.success_count == 1

    @pytest.mark.asyncio
    async def test_async_failure_opens_circuit(self):
        cb = CircuitBreaker(name="async-fail", failure_threshold=1)
        with pytest.raises(ValueError):
            await cb.call_async(_async_failing_func)
        assert cb.get_stats().state == CircuitState.OPEN

    @pytest.mark.asyncio
    async def test_async_open_circuit_raises_error(self):
        cb = CircuitBreaker(name="async-open", failure_threshold=1)
        with pytest.raises(ValueError):
            await cb.call_async(_async_failing_func)

        with pytest.raises(CircuitBreakerError):
            await cb.call_async(_async_success_func)


class TestCircuitBreakDecorator:
    def test_sync_decorator(self):
        @circuit_break(failure_threshold=3, recovery_timeout=60)
        def my_func():
            return "decorated"

        result = my_func()
        assert result == "decorated"

    def test_async_decorator(self):
        @circuit_break(failure_threshold=3, recovery_timeout=60)
        async def my_async_func():
            return "async-decorated"

        result = asyncio.run(my_async_func())
        assert result == "async-decorated"

    def test_decorator_auto_detects_async(self):
        @circuit_break()
        async def sample_async():
            return "ok"

        coro = sample_async()
        assert asyncio.iscoroutine(coro)
        result = asyncio.run(coro)
        assert result == "ok"


class TestCircuitBreakerRegistry:
    def test_get_breaker_creates_new(self):
        cb = get_breaker("registry-test")
        assert cb.name == "registry-test"
        assert cb.get_stats().state == CircuitState.CLOSED

    def test_get_breaker_reuses_existing(self):
        cb1 = get_breaker("registry-reuse")
        cb2 = get_breaker("registry-reuse")
        assert cb1 is cb2

    def test_get_all_stats(self):
        registry = CircuitBreakerRegistry()
        registry.get_breaker("stats-a")
        registry.get_breaker("stats-b")
        all_stats = registry.get_all_stats()
        assert "stats-a" in all_stats
        assert "stats-b" in all_stats

    def test_reset_all(self):
        registry = CircuitBreakerRegistry()
        registry.get_breaker("reset-a")
        registry.get_breaker("reset-b")
        registry.reset_all()
        for name, stats in registry.get_all_stats().items():
            assert stats.state == CircuitState.CLOSED

    def test_remove_breaker(self):
        registry = CircuitBreakerRegistry()
        registry.get_breaker("remove-test")
        assert registry.remove_breaker("remove-test") is True
        assert registry.remove_breaker("nonexistent") is False


class TestCircuitBreakWithConfig:
    def test_with_config_dict(self):
        config = {
            "name": "config-test",
            "failure_threshold": 2,
            "recovery_timeout": 30.0,
        }

        @circuit_break_with_config(config)
        def configured_func():
            return "configured"

        result = configured_func()
        assert result == "configured"

    def test_circuit_breaker_error_message(self):
        cb = CircuitBreaker(name="err-test", failure_threshold=1)
        with pytest.raises(ValueError):
            cb.call(_failing_func)

        try:
            cb.call(_success_func)
        except CircuitBreakerError as e:
            assert "err-test" in str(e)
            assert "OPEN" in str(e)
