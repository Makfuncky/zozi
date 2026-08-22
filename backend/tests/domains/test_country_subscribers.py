"""Tests for country domain event subscribers (Law 3, canonical event_bus).

Verifies the guarded cross-domain invalidation dispatch and that the four country
listeners are wired onto the sanctioned string-keyed event_bus, without importing
the full app or any other domain (keeps the test fast and decoupled).
"""
from __future__ import annotations

from infrastructure.messaging.events import event_bus

from domains.country import subscribers
from domains.country.events import (
    EVENT_COUNTRY_CONFIG_DRAFT_CREATED,
    EVENT_COUNTRY_CONFIG_PUBLISHED,
    EVENT_COUNTRY_STAFF_ASSIGNED,
    EVENT_COUNTRY_TAX_RATE_CHANGED,
)


def _reset_registry():
    subscribers._cache_invalidators.clear()


def test_register_dedupes():
    _reset_registry()
    calls = []

    def fn(code):
        calls.append(code)

    subscribers.register_country_cache_invalidator(fn)
    subscribers.register_country_cache_invalidator(fn)
    assert len(subscribers._cache_invalidators) == 1


def test_config_published_dispatches_to_invalidator():
    _reset_registry()
    calls = []
    subscribers.register_country_cache_invalidator(lambda c: calls.append(c))
    subscribers._on_config_published({"country_code": "US", "version": 3, "published_by": 1})
    assert calls == ["US"]


def test_all_handlers_dispatch_and_are_resilient():
    _reset_registry()
    calls = []

    def bad(code):
        raise RuntimeError("downstream boom")

    subscribers.register_country_cache_invalidator(bad)
    subscribers.register_country_cache_invalidator(lambda c: calls.append(c))

    # None of these may raise, even though `bad` always raises.
    subscribers._on_config_published({"country_code": "FR"})
    subscribers._on_config_draft_created({"country_code": "FR"})
    subscribers._on_tax_changed({"country_code": "FR", "tax_rate": 0.2})
    subscribers._on_staff_assigned({"country_code": "FR", "user_id": 5, "role_in_country": "manager"})
    assert calls == ["FR", "FR", "FR", "FR"]


def test_register_subscribers_wires_all_four_listeners():
    expected = {
        EVENT_COUNTRY_CONFIG_PUBLISHED: subscribers._on_config_published,
        EVENT_COUNTRY_CONFIG_DRAFT_CREATED: subscribers._on_config_draft_created,
        EVENT_COUNTRY_STAFF_ASSIGNED: subscribers._on_staff_assigned,
        EVENT_COUNTRY_TAX_RATE_CHANGED: subscribers._on_tax_changed,
    }
    for evt, handler in expected.items():
        assert evt in event_bus._subscribers, f"{evt} not wired on bus"
        assert handler in event_bus._subscribers[evt], f"{evt} handler missing"
