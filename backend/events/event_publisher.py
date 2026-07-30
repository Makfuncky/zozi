"""Event publisher for domain events.

This module provides a simple event publishing system that allows
listeners to register for domain events and be notified when those
events occur.
"""

import logging
from typing import Any, Callable, Dict, List, Type

logger = logging.getLogger(__name__)


class EventPublisher:
    """Simple event publisher for domain events."""

    def __init__(self) -> None:
        """Initialize the event publisher with empty listener registry."""
        self._listeners: Dict[Type, List[Callable]] = {}

    def register_listener(self, event_type: Type, listener: Callable) -> None:
        """Register a listener for a specific event type.

        Args:
            event_type: The event class to listen for
            listener: Callable that will be called when the event occurs
        """
        if event_type not in self._listeners:
            self._listeners[event_type] = []
        self._listeners[event_type].append(listener)
        logger.debug(
            "Registered listener for %s: %s",
            event_type.__name__,
            listener.__name__,
        )

    def publish(self, event: Any) -> None:
        """Publish an event to all registered listeners.

        Args:
            event: The event instance to publish
        """
        event_type = type(event)
        listeners = self._listeners.get(event_type, [])

        if not listeners:
            logger.debug("No listeners registered for %s", event_type.__name__)
            return

        logger.info(
            "Publishing %s event '%s' to %d listener(s)",
            event_type.__name__,
            getattr(event, "event_id", "unknown"),
            len(listeners),
        )

        # Notify all listeners
        for listener in listeners:
            try:
                listener(event)
            except Exception as e:
                logger.error(
                    "Error in listener %s for %s event '%s': %s",
                    listener.__name__,
                    event_type.__name__,
                    getattr(event, "event_id", "unknown"),
                    e,
                    exc_info=True,
                )

    def get_registered_event_types(self) -> List[str]:
        """Get all event types that have listeners registered."""
        return list(self._listeners.keys())