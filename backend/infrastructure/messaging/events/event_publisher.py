"""Event publisher for domain events.

.. deprecated::
    ``EventPublisher`` is deprecated; use ``event_bus`` instead.  This class
    remains as a backwards-compatible adapter with retry + DLQ + Valkey Stream
    support so existing callers continue to work during the WIR-028 migration.
"""
from __future__ import annotations

import json
import logging
import time
import warnings
from typing import Any, Callable, Dict, List, Type

from infrastructure.observability.retry import RetryExhausted, with_retry

logger = logging.getLogger(__name__)

_DLQ_KEY = "event_dead_letter"
_STREAM_KEY = "event_stream"


def _get_valkey_client() -> Any:
    try:
        from infrastructure.valkey.client import valkey_client as _factory
        return _factory()
    except Exception:
        return None


def _route_to_dlq(event_type: str, payload: dict, error: str) -> None:
    client = _get_valkey_client()
    if client is None or not hasattr(client, "rpush"):
        logger.debug("DLQ write skipped: Valkey client unavailable")
        return
    try:
        entry = {"event_type": event_type, "payload": payload, "error": error}
        client.rpush(_DLQ_KEY, json.dumps(entry, default=str))
    except Exception:
        logger.warning("DLQ write failed for %s", event_type, exc_info=True)


def _publish_to_stream(event_type: str, payload: dict) -> None:
    client = _get_valkey_client()
    if client is None or not hasattr(client, "xadd"):
        logger.debug("Stream write skipped: Valkey client unavailable")
        return
    try:
        payload_blob = json.dumps(payload, default=str)
        fields = {"event_type": event_type, "payload": payload_blob}
        client.xadd(_STREAM_KEY, fields)
    except Exception:
        logger.warning("Stream write failed for %s", event_type, exc_info=True)


class EventPublisher:
    """Deprecated event publisher with retry + DLQ + Valkey Stream support."""

    def __init__(self) -> None:
        warnings.warn(
            "EventPublisher is deprecated; use event_bus instead",
            DeprecationWarning,
            stacklevel=2,
        )
        self._listeners: Dict[Type, List[Callable]] = {}

    def register_listener(self, event_type: Any, listener: Callable) -> None:
        key = event_type.__name__ if isinstance(event_type, type) else str(event_type)
        if key not in self._listeners:
            self._listeners[key] = []
        self._listeners[key].append(listener)
        logger.debug(
            "Registered listener for %s: %s",
            key,
            listener.__name__,
        )

    def publish(self, event: Any) -> None:
        if isinstance(event, str):
            key = event
            event_id = event
            listener_payload = {"value": event}
        elif isinstance(event, type):
            key = event.__name__
            event_id = "unknown"
            listener_payload = event
        else:
            key = type(event).__name__
            event_id = getattr(event, "event_id", "unknown")
            listener_payload = event

        listeners = self._listeners.get(key, [])

        if not listeners:
            logger.debug("No listeners registered for %s", key)
            return

        payload = {"event_id": event_id}
        _publish_to_stream(key, payload)

        for listener in listeners:
            try:
                wrapped = with_retry()(listener)
                wrapped(listener_payload)
            except RetryExhausted as e:
                _route_to_dlq(key, payload, str(e.last_exception))
                logger.error(
                    "Error in listener %s for %s event '%s': %s",
                    listener.__name__,
                    key,
                    event_id,
                    e.last_exception,
                    exc_info=True,
                )
            except Exception as e:
                logger.error(
                    "Error in listener %s for %s event '%s': %s",
                    listener.__name__,
                    key,
                    event_id,
                    e,
                    exc_info=True,
                )

    def get_registered_event_types(self) -> List[str]:
        return list(self._listeners.keys())
