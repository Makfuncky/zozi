"""In-process event bus for cross-domain decoupling.

Lives in the circuit-exempt ``data`` layer so first-party domains can publish
and subscribe to events without importing one another (bounded context). This
is the sanctioned mechanism for breaking dependency cycles: a domain publishes
an intent here instead of calling a sibling domain's service directly.

``data`` is an exempt layer in the architecture audit, so importing this module
never creates a domain dependency edge.

Event delivery contract
-----------------------
* ``publish()`` delivers synchronously with up to ``_MAX_RETRIES`` attempts per
  handler, using exponential backoff (base 1 s, cap 8 s).
* Permanently failed handler payloads are routed to the Valkey DLQ list
  (``DLQ_KEY``) so a periodic reconciler can alert or replay them.
* Every publish also appends to the Valkey Stream (``STREAM_KEY``) for the
  outbox pattern (WIR-028).
* The ``propagate`` flag still controls whether a handler failure bubbles up
  to the caller (used for governance *requested intents*).
"""
from __future__ import annotations

import dataclasses
import json
import logging
import time
from typing import Any, Callable, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Retry / DLQ constants
# ---------------------------------------------------------------------------

_MAX_RETRIES: int = 5
_BACKOFF_BASE: float = 1.0   # seconds; doubled per attempt (1, 2, 4, 8 …)
_BACKOFF_CAP: float = 8.0

# Valkey keys
DLQ_KEY: str = "event_dead_letter"
STREAM_KEY: str = "event_stream"

# ---------------------------------------------------------------------------
# Internal subscriber bookkeeping
# ---------------------------------------------------------------------------
# Each entry is a 3-tuple:
#   (handler: Callable, attempts: int, next_attempt_at: float)
_SubEntry = Tuple[Callable, int, float]

# String-keyed subscribers (existing mechanism).
_subscribers: Dict[str, List[_SubEntry]] = {}

# Class-type subscribers (EventPublisher-style; WIR-028 consolidation).
# Keys are ``"<class.__name__>"``; values are plain callables receiving the
# event object directly, mirroring the EventPublisher handler contract.
_CLASS_TYPE_SUFFIX = "_callbacks"
_event_callbacks: Dict[str, List[Callable]] = {}

# Canonical event-name constants
EVENT_ORDER_STATUS_CHANGED = "order.status_changed"
EVENT_ORDER_REFUNDED = "order.refunded"

# Canonical finance event name (mirrors domains.finance.events)
EVENT_FINANCE_BADGE_BILLING_PAID = "finance.badge_billing_paid"

# Canonical payment event names (mirrors payment_events.py)
EVENT_PAYMENT_CONFIRMED = "payments.confirmed"
EVENT_PAYMENT_FAILED = "payments.failed"
EVENT_PAYMENT_REFUNDED = "payments.refunded"


# ---------------------------------------------------------------------------
# Valkey accessor
# ---------------------------------------------------------------------------

def _get_valkey_client() -> Any:
    """Return the process-wide Valkey client, falling back to a NoOp shim.

    The Valkey singleton lives in ``infrastructure.valkey.client``; importing
    here would create a cross-module dependency, so we defer the import to
    runtime.
    """
    try:
        from infrastructure.valkey.client import valkey_client as _factory  # noqa: PLC0415
        return _factory()
    except Exception:  # noqa: BLE001 - Valkey may be unavailable in dev/test
        return None


def _normalize_key(event_key: Any) -> str:
    """Return the canonical string key for *event_key*.

    String keys are returned unchanged.  Class-type keys are converted to
    ``"<class.__name__>"`` so that ``subscribe(OrderCreated, handler)`` and
    ``subscribe("OrderCreated", handler)`` share the same registry entry.
    """
    if isinstance(event_key, str):
        return event_key
    return getattr(event_key, "__name__", repr(event_key))


def _event_to_payload(event: Any) -> dict:
    """Serialize an event object to a plain dict for stream/queue persistence.

    Uses ``dataclasses.asdict`` for dataclass events (handles nested dataclasses
    and ``Decimal`` values), falls back to ``.serialize()`` when available,
    then to ``vars()`` as a last resort.
    """
    if dataclasses.is_dataclass(event):
        try:
            return dataclasses.asdict(event)
        except Exception:  # noqa: BLE001
            pass
    if hasattr(event, "serialize") and callable(event.serialize):
        try:
            return event.serialize()
        except Exception:  # noqa: BLE001
            pass
    if hasattr(event, "__dict__"):
        return vars(event)
    return {"value": str(event)}


# ---------------------------------------------------------------------------
# DLQ + Stream persistence
# ---------------------------------------------------------------------------

def _route_to_dlq(event_type: str, payload: dict, error: str) -> None:
    """Append a failed event payload to the Valkey DLQ list.

    The DLQ entry is a JSON blob with the original event context plus the
    error that caused the failure, giving operators enough information to
    replay or investigate later.
    """
    client = _get_valkey_client()
    if client is None or not hasattr(client, "rpush"):
        logger.debug("DLQ write skipped: Valkey client unavailable")
        return
    try:
        entry = {
            "event_type": event_type,
            "payload": payload,
            "error": error,
        }
        client.rpush(DLQ_KEY, json.dumps(entry, default=str))
    except Exception:  # noqa: BLE001 - DLQ write must not mask the original failure
        logger.warning("DLQ write failed for %s", event_type, exc_info=True)


def _publish_to_stream(event_type: str, payload: dict) -> None:
    """Append event to the Valkey Stream for outbox durability (WIR-028).

    ``payload`` is always JSON-serialised into the ``payload`` stream field.  If
    the payload is a single-key dict whose value is a string (the convention
    used by the ``_shutdown`` sentinel), that value is also promoted to a
    top-level stream field so consumers can match on it without JSON parsing.
    """
    client = _get_valkey_client()
    if client is None or not hasattr(client, "xadd"):
        logger.debug("Stream write skipped: Valkey client unavailable")
        return
    try:
        payload_blob = json.dumps(payload, default=str)
        fields: dict = {"event_type": event_type, "payload": payload_blob}
        # Promote single-string payload values to top-level fields so that
        # stream consumers can match on them without JSON-deserialising.
        if (
            len(payload) == 1
            and isinstance(payload.get("shutdown"), str)
        ):
            fields["shutdown"] = payload["shutdown"]
        client.xadd(STREAM_KEY, fields)
    except Exception:  # noqa: BLE001 - stream write must not mask the original failure
        logger.warning("Stream write failed for %s", event_type, exc_info=True)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def subscribe(event_type: Any, handler: Callable) -> None:
    """Register *handler* to receive every published *event_type* payload.

    *event_type* may be a string key (e.g. ``"order.status_changed"``) or a
    class (e.g. ``OrderCreated``).  Class-type keys share one flat namespace
    keyed on ``<class.__name__>`` so that ``EventPublisher``-style
    ``register_listener(OrderCreated, handler)`` calls route to the same
    handlers as ``event_bus.subscribe(OrderCreated, handler)`` (WIR-028).
    """
    key = _normalize_key(event_type)
    if isinstance(event_type, type):
        _event_callbacks.setdefault(key, []).append(handler)
    else:
        _subscribers.setdefault(key, []).append((handler, 0, 0.0))


def unsubscribe(event_type: Any, handler: Callable) -> None:
    """Remove *handler* from *event_type* subscribers (WIR-035).

    Supports both string keys and class-type keys.
    """
    key = _normalize_key(event_type)
    if isinstance(event_type, str):
        entries = _subscribers.get(key, [])
        _subscribers[key] = [
            (h, a, t) for (h, a, t) in entries if h is not handler
        ]
    else:
        cbs = _event_callbacks.get(key, [])
        _event_callbacks[key] = [cb for cb in cbs if cb is not handler]


def clear() -> None:
    """Remove all registered subscribers across every event type (WIR-035)."""
    _subscribers.clear()
    _event_callbacks.clear()


def publish(event_type: Any, payload: Any = None, propagate: bool = False) -> Any:
    """Deliver *payload* (or *event_type* when it is an event object) to all subscribers.

    Accepts two calling conventions:

    1. ``publish("string.key", payload_dict)`` — the original string-key API.
    2. ``publish(EventClass, event_instance)`` — class-type key (WIR-028
       consolidation); the instance is serialised to a dict before delivery
       to string-keyed handlers, and delivered as-is to class-type callbacks
       registered via ``subscribe(EventClass, handler)``.

    Each handler is invoked up to ``_MAX_RETRIES`` times with exponential
    backoff (1-2-4-8 s + jitter) between attempts.  After the final failed
    attempt the payload is routed to the Valkey DLQ (``DLQ_KEY``) and a
    WARNING is emitted so that ops can alert on DLQ backlog.

    The event is also appended to the Valkey Stream (``STREAM_KEY``) on every
    call to satisfy the outbox pattern (WIR-028).

    Returns the value produced by the last successful handler so a *requested*
    intent can hand the caller back the result of the delegated write
    (preserving the direct-call contract during the Law-3 migration).  With a
    single subscriber the handler's return value is passed through; with
    several, a list of results is returned; with none, ``None``.

    Parameters
    ----------
    event_type:
        Canonical event name (string) or event class (e.g. ``OrderCreated``).
    payload:
        Dict payload for string-keyed publish; event object for class-type
        publish.  Ignored when *event_type* is an event instance passed as
        the first positional argument (``publish(event_instance)``).
    propagate:
        When ``True`` a handler exception is re-raised after logging (used for
        governance *requested* intents that must surface failures to the
        caller).  The DLQ route still fires before the raise so the failure
        is never silently lost.
    """
    # Normalise: support both publish(str, dict) and publish(class, instance).
    if isinstance(event_type, str):
        str_key = event_type
        stream_payload = payload if isinstance(payload, dict) else {"value": str(payload)}
        event_obj = payload
    elif isinstance(event_type, type):
        # Class-type key (e.g. publish(OrderCreated, event_instance)).
        # For built-in types (str, int, ...) use __name__ as the string key
        # so that EventPublisher-style publish(str, "value") routes to
        # handlers registered under the corresponding string type key.
        if event_type in (str, int, float, bool, bytes, type(None)):
            str_key = event_type.__name__
            event_obj = payload
            stream_payload = {"value": str(event_obj)} if event_obj is not None else {}
        else:
            str_key = _normalize_key(event_type)
            event_obj = payload
            stream_payload = _event_to_payload(event_obj) if event_obj is not None else {}
    else:
        # Event instance passed as first positional arg (publish(event_instance)).
        str_key = _normalize_key(type(event_type))
        event_obj = event_type
        stream_payload = _event_to_payload(event_obj)

    # Persist to stream regardless of subscriber state (WIR-028).
    _publish_to_stream(str_key, stream_payload)

    # Collect string-keyed handlers (retry-capable).
    entries = list(_subscribers.get(str_key, []))
    # Collect class-type callbacks (no retry — delegates to string-key path).
    class_callbacks = list(_event_callbacks.get(str_key, []))

    if not entries and not class_callbacks:
        return None

    results: List[Any] = []
    last_exc: Optional[BaseException] = None

    for handler, attempts, _next_attempt in entries:
        handler_attempts = 0
        while True:
            try:
                result = handler(stream_payload)
                results.append(result)
                break
            except Exception as exc:  # noqa: BLE001
                handler_attempts += 1
                last_exc = exc
                if handler_attempts >= _MAX_RETRIES:
                    logger.warning(
                        "Handler %r for %s failed after %d attempts; routing to DLQ",
                        getattr(handler, "__name__", repr(handler)),
                        str_key,
                        handler_attempts,
                        exc_info=True,
                    )
                    _route_to_dlq(str_key, stream_payload, str(exc))
                    results.append(None)
                    break
                backoff = min(
                    _BACKOFF_BASE * (2 ** (handler_attempts - 1))
                    + (0.5 if handler_attempts > 1 else 0.0),
                    _BACKOFF_CAP,
                )
                logger.debug(
                    "Handler %r for %s attempt %d/%d failed; retrying in %.1fs",
                    getattr(handler, "__name__", repr(handler)),
                    str_key,
                    handler_attempts,
                    _MAX_RETRIES,
                    backoff,
                )
                time.sleep(backoff)

    # Class-type callbacks receive the raw event object (EventPublisher contract).
    for cb in class_callbacks:
        try:
            result = cb(event_obj)
            results.append(result)
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "Class-type callback %r for %s failed: %s",
                getattr(cb, "__name__", repr(cb)),
                str_key,
                exc,
                exc_info=True,
            )
            _route_to_dlq(str_key, _event_to_payload(event_obj), str(exc))
            results.append(None)
            last_exc = exc

    if last_exc is not None and propagate:
        raise last_exc

    if len(results) == 1:
        return results[0]
    if len(results) > 1:
        return results
    return None


def shutdown() -> None:
    """Persist in-flight subscriber state and clear the registry (WIR-035).

    Emits a sentinel ``shutdown=true`` message to the Valkey Stream so that
    any outbox consumer can detect process shutdown and pause consumption.
    Clears both string-keyed and class-type subscriber registries.
    """
    _publish_to_stream("_shutdown", {"shutdown": "true"})
    _subscribers.clear()
    _event_callbacks.clear()


# ---------------------------------------------------------------------------
# Convenience helpers (preserve existing callers)
# ---------------------------------------------------------------------------

def publish_order_status_changed(
    order_id: int,
    status: str,
    old_status: str | None = None,
) -> None:
    publish(
        EVENT_ORDER_STATUS_CHANGED,
        {"order_id": order_id, "status": status, "old_status": old_status},
    )


def publish_order_refunded(order_id: int, source: str = "admin") -> None:
    publish(EVENT_ORDER_REFUNDED, {"order_id": order_id, "source": source})
