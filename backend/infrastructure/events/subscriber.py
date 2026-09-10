"""Event subscriber stubs for jobs module."""
from __future__ import annotations

from typing import Callable


class EventSubscriber:
    """Minimal event subscriber stub."""

    def __init__(self, consumer_group: str, handlers: dict[str, Callable[[dict], None]]) -> None:
        self.consumer_group = consumer_group
        self.handlers = handlers

    def start(self) -> None:
        pass

    def stop(self) -> None:
        pass


def create_subscriber(
    consumer_group: str,
    handlers: dict[str, Callable[[dict], None]],
) -> EventSubscriber:
    """Create a minimal event subscriber."""
    return EventSubscriber(consumer_group=consumer_group, handlers=handlers)
