"""Event subscriber that registers handlers with the canonical event bus."""
from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, Callable, Optional

try:
    import structlog
    logger = structlog.get_logger(__name__)
except ImportError:
    logger = logging.getLogger(__name__)


try:
    from infrastructure.valkey.client import valkey_client
except Exception:  # noqa: BLE001 - Valkey may be unavailable in dev/test
    valkey_client = None  # type: ignore[assignment]


class EventSubscriber:
    """Registers event handlers with the canonical Valkey Stream consumer."""

    def __init__(
        self,
        consumer_group: str,
        handlers: dict[str, Callable[[dict], None]],
        block_ms: int = 50,
        stream_key: str = "events:stream",
    ) -> None:
        self.consumer_group = consumer_group
        self.handlers = handlers
        self.block_ms = block_ms
        self.stream_key = stream_key
        self._started = False
        self._task: Optional[asyncio.Task] = None
        self._running = False

    def _dispatch(self, payload: dict) -> None:
        """Dispatch a payload to the matching handler."""
        event_type = payload.get("event_type") or payload.get("type")
        handler = self.handlers.get(event_type)
        if handler is None:
            return
        try:
            handler(payload)
        except Exception:  # noqa: BLE001 - handler failure must not break dispatch
            logger.exception("Handler failed for %s", event_type)

    async def _consume(self) -> None:
        client = valkey_client() if valkey_client is not None else None
        if client is None or not hasattr(client, "xgroup_create"):
            return
        consumer_name = f"{self.consumer_group}-consumer"
        while self._running:
            try:
                try:
                    client.xgroup_create(
                        self.stream_key,
                        self.consumer_group,
                        id="$",
                        mkstream=True,
                    )
                except Exception:  # noqa: BLE001 - group may already exist
                    pass
                result = client.xreadgroup(
                    self.consumer_group,
                    consumer_name,
                    {self.stream_key: ">"},
                    10,
                    self.block_ms,
                )
            except Exception:  # noqa: BLE001 - transient Valkey error
                await asyncio.sleep(0.1)
                continue
            if not result:
                await asyncio.sleep(0)
                continue
            for stream, messages in result:
                for msg_id, fields in messages:
                    if not isinstance(fields, dict):
                        continue
                    event_type = fields.get("event_type")
                    payload_str = fields.get("payload", "{}")
                    try:
                        payload = json.loads(payload_str)
                    except Exception:  # noqa: BLE001
                        payload = {"value": payload_str}
                    if event_type:
                        payload["event_type"] = event_type
                    self._dispatch(payload)
                    try:
                        client.xack(self.stream_key, self.consumer_group, msg_id)
                    except Exception:  # noqa: BLE001 - ack failure must be visible
                        logger.warning(
                            "XACK failed for %s group=%s msg=%s",
                            self.stream_key,
                            self.consumer_group,
                            msg_id,
                            exc_info=True,
                        )
            await asyncio.sleep(0)

    def start(self) -> None:
        if self._started:
            return
        self._running = True
        self._task = asyncio.get_event_loop().create_task(self._consume())
        self._started = True

    def stop(self) -> None:
        if not self._started:
            return
        self._running = False
        if self._task is not None:
            self._task.cancel()
            self._task = None
        self._started = False


def create_subscriber(
    consumer_group: str,
    handlers: dict[str, Callable[[dict], None]],
    block_ms: int = 50,
    stream_key: str = "events:stream",
) -> EventSubscriber:
    """Create an EventSubscriber wired to the canonical event bus."""
    return EventSubscriber(
        consumer_group=consumer_group,
        handlers=handlers,
        block_ms=block_ms,
        stream_key=stream_key,
    )
