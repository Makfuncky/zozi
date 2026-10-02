"""Event subscriber that registers handlers with the canonical event bus."""
from __future__ import annotations

import logging
from typing import Any, Callable

try:
    import structlog
    logger = structlog.get_logger(__name__)
except ImportError:
    logger = logging.getLogger(__name__)


class EventSubscriber:
    """Registers event handlers with the canonical in-process event bus."""

    def __init__(self, consumer_group: str, handlers: dict[str, Callable[[dict], None]]) -> None:
        self.consumer_group = consumer_group
        self.handlers = handlers
        self._started = False

    def start(self) -> None:
        if self._started:
            return
        from infrastructure.messaging.events.event_bus import subscribe
        for event_type, handler in self.handlers.items():
            subscribe(event_type, handler)
            logger.info("Subscribed %s to %s", self.consumer_group, event_type)
        self._started = True

    def stop(self) -> None:
        if not self._started:
            return
        from infrastructure.messaging.events.event_bus import unsubscribe
        for event_type, handler in self.handlers.items():
            unsubscribe(event_type, handler)
            logger.info("Unsubscribed %s from %s", self.consumer_group, event_type)
        self._started = False


def create_subscriber(
    consumer_group: str,
    handlers: dict[str, Callable[[dict], None]],
) -> EventSubscriber:
    """Create an EventSubscriber wired to the canonical event bus."""
    return EventSubscriber(consumer_group=consumer_group, handlers=handlers)
