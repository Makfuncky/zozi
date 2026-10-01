import asyncio
import inspect

import pytest

from infrastructure.observability.retry import RetryExhausted, with_retry


def test_defaults():
    sig = inspect.signature(with_retry)
    assert sig.parameters["max_attempts"].default == 5
    assert sig.parameters["base_delay"].default == 1.0


def test_sync_succeeds_on_first_try():
    call_count = 0

    @with_retry()
    def fn():
        nonlocal call_count
        call_count += 1
        return "ok"

    result = fn()
    assert result == "ok"
    assert call_count == 1


def test_sync_retries_then_succeeds():
    call_count = 0

    @with_retry()
    def fn():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise RuntimeError("fail")
        return "ok"

    result = fn()
    assert result == "ok"
    assert call_count == 3


def test_sync_exhausts_after_max_attempts():
    call_count = 0

    @with_retry()
    def fn():
        nonlocal call_count
        call_count += 1
        raise RuntimeError("always fail")

    with pytest.raises(RetryExhausted) as exc_info:
        fn()
    assert exc_info.value.attempts == 5
    assert call_count == 5


@pytest.mark.asyncio
async def test_async_retries_then_succeeds():
    call_count = 0

    @with_retry()
    async def fn():
        nonlocal call_count
        call_count += 1
        if call_count < 2:
            raise RuntimeError("fail")
        return "ok"

    result = await fn()
    assert result == "ok"
    assert call_count == 2


def test_custom_retryable_exceptions():
    call_count = 0

    @with_retry(retryable_exceptions=(ValueError,))
    def fn():
        nonlocal call_count
        call_count += 1
        raise TypeError("not retried")

    with pytest.raises(TypeError):
        fn()
    assert call_count == 1


def test_on_retry_callback():
    events = []

    @with_retry(on_retry=lambda exc, attempt: events.append((str(exc), attempt)))
    def fn():
        raise RuntimeError("boom")

    with pytest.raises(RetryExhausted):
        fn()
    assert len(events) == 4
    assert events[0][1] == 1
    assert events[-1][1] == 4
