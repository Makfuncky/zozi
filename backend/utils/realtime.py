from __future__ import annotations

import asyncio
import json
import logging
import threading
from collections import defaultdict
from typing import Any

from fastapi import WebSocket
from sqlalchemy import and_, event, inspect as sa_inspect
from sqlalchemy.orm import Session as OrmSession

from models import AuditLog, Notification, Payout, Product, SupplierDispute, SupportTicket, SupplierProfile, TicketReply, User, InternalEmail
from utils.config import settings


_REALTIME_EVENTS_KEY = "_zozi_realtime_events"
_REALTIME_STAFF_CACHE_KEY = "_zozi_realtime_staff_cache"
_USER_REALTIME_CHANNEL = "zozi:realtime:user"
_LOGISTICS_REALTIME_CHANNEL = "zozi:realtime:logistics"
_ADMIN_ALERT_ROLE_MAP: dict[str, frozenset[str]] = {
    "audit.read": frozenset({"admin", "sub_admin", "moderator", "support"}),
    "moderation.products": frozenset({"admin", "sub_admin", "moderator"}),
    "moderation.suppliers": frozenset({"admin", "sub_admin", "moderator"}),
    "payouts.verify": frozenset({"admin", "sub_admin"}),
    "tickets.manage": frozenset({"admin", "sub_admin", "moderator", "support"}),
}

logger = logging.getLogger(__name__)


def _create_realtime_redis_client():
    if not settings.redis_url.strip():
        return None
    try:
        import redis as _redis

        return _redis.from_url(
            settings.redis_url,
            socket_connect_timeout=1,
            socket_timeout=1,
            health_check_interval=15,
            decode_responses=True,
        )
    except Exception:
        return None


class _RedisRealtimeBridge:
    def __init__(self, channel: str, dispatcher) -> None:
        self._channel = channel
        self._dispatcher = dispatcher
        self._loop: asyncio.AbstractEventLoop | None = None
        self._publisher_client = None
        self._listener_thread: threading.Thread | None = None
        self._stop_event = threading.Event()

    def bind_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        self._loop = loop
        self._ensure_listener()

    def shutdown(self) -> None:
        self._stop_event.set()
        if self._listener_thread and self._listener_thread.is_alive():
            self._listener_thread.join(timeout=2)
        self._listener_thread = None
        self._publisher_client = None

    def publish(self, message: dict[str, Any]) -> bool:
        client = self._publisher_client
        if client is None:
            client = _create_realtime_redis_client()
            if client is None:
                return False
            self._publisher_client = client
            self._ensure_listener()
        try:
            client.publish(self._channel, json.dumps(message, default=str))
            return True
        except Exception:
            self._publisher_client = None
            return False

    def _ensure_listener(self) -> None:
        if self._loop is None:
            return
        if self._listener_thread and self._listener_thread.is_alive():
            return
        self._stop_event.clear()
        self._listener_thread = threading.Thread(
            target=self._listen_forever,
            daemon=True,
            name=f"realtime-{self._channel.rsplit(':', 1)[-1]}",
        )
        self._listener_thread.start()

    def _listen_forever(self) -> None:
        while not self._stop_event.is_set():
            client = _create_realtime_redis_client()
            if client is None:
                self._stop_event.wait(5)
                continue

            pubsub = client.pubsub(ignore_subscribe_messages=True)
            try:
                pubsub.subscribe(self._channel)
                while not self._stop_event.is_set():
                    message = pubsub.get_message(timeout=1.0)
                    if not message or message.get("type") != "message":
                        continue
                    data = message.get("data")
                    if not isinstance(data, str):
                        continue
                    payload = json.loads(data)
                    if self._loop is None or self._loop.is_closed():
                        continue
                    asyncio.run_coroutine_threadsafe(self._dispatcher(payload), self._loop)
            except Exception:
                logger.debug("Realtime Redis listener disconnected for %s", self._channel, exc_info=True)
            finally:
                try:
                    pubsub.close()
                except Exception:
                    pass
                try:
                    client.close()
                except Exception:
                    pass

            if not self._stop_event.is_set():
                self._stop_event.wait(1)


class LogisticsRealtimeHub:
    def __init__(self) -> None:
        self._loop: asyncio.AbstractEventLoop | None = None
        self._partner_connections: dict[int, set[WebSocket]] = defaultdict(set)
        self._order_connections: dict[int, set[WebSocket]] = defaultdict(set)
        self._bridge = _RedisRealtimeBridge(_LOGISTICS_REALTIME_CHANNEL, self._dispatch_remote_message)

    def bind_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        self._loop = loop
        self._bridge.bind_loop(loop)

    def shutdown(self) -> None:
        self._bridge.shutdown()
        self._loop = None

    async def connect_partner(self, websocket: WebSocket, partner_id: int) -> None:
        await websocket.accept()
        self._partner_connections[partner_id].add(websocket)

    async def connect_order(self, websocket: WebSocket, order_id: int) -> None:
        await websocket.accept()
        self._order_connections[order_id].add(websocket)

    async def disconnect(self, websocket: WebSocket) -> None:
        for pool in (self._partner_connections, self._order_connections):
            for key in list(pool.keys()):
                pool[key].discard(websocket)
                if not pool[key]:
                    pool.pop(key, None)

    async def _broadcast(self, sockets: set[WebSocket], payload: dict[str, Any]) -> None:
        stale: list[WebSocket] = []
        for socket in list(sockets):
            try:
                await socket.send_json(payload)
            except Exception:
                stale.append(socket)
        for socket in stale:
            sockets.discard(socket)

    async def broadcast_partner(self, partner_id: int, payload: dict[str, Any]) -> None:
        sockets = self._partner_connections.get(partner_id)
        if sockets:
            await self._broadcast(sockets, payload)

    async def broadcast_all_partners(self, payload: dict[str, Any]) -> None:
        for sockets in list(self._partner_connections.values()):
            if sockets:
                await self._broadcast(sockets, payload)

    async def broadcast_order(self, order_id: int, payload: dict[str, Any]) -> None:
        sockets = self._order_connections.get(order_id)
        if sockets:
            await self._broadcast(sockets, payload)

    async def _dispatch_remote_message(self, message: dict[str, Any]) -> None:
        payload = message.get("payload")
        if not isinstance(payload, dict):
            return
        if message.get("broadcast_all_partners"):
            await self.broadcast_all_partners(payload)
        partner_id = message.get("partner_id")
        if isinstance(partner_id, int):
            await self.broadcast_partner(partner_id, payload)
        order_id = message.get("order_id")
        if isinstance(order_id, int):
            await self.broadcast_order(order_id, payload)

    def publish(
        self,
        *,
        partner_id: int | None = None,
        order_id: int | None = None,
        payload: dict[str, Any],
        broadcast_all_partners: bool = False,
    ) -> None:
        if self._loop is None or self._loop.is_closed():
            return
        message = {
            "partner_id": partner_id,
            "order_id": order_id,
            "payload": payload,
            "broadcast_all_partners": broadcast_all_partners,
        }
        if self._bridge.publish(message):
            return
        asyncio.run_coroutine_threadsafe(self._dispatch_remote_message(message), self._loop)


logistics_realtime_hub = LogisticsRealtimeHub()


class UserRealtimeHub:
    def __init__(self) -> None:
        self._loop: asyncio.AbstractEventLoop | None = None
        self._user_connections: dict[str, set[WebSocket]] = defaultdict(set)
        self._bridge = _RedisRealtimeBridge(_USER_REALTIME_CHANNEL, self._dispatch_remote_message)

    def bind_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        self._loop = loop
        self._bridge.bind_loop(loop)

    def shutdown(self) -> None:
        self._bridge.shutdown()
        self._loop = None

    async def connect_user(self, websocket: WebSocket, user_id: object) -> None:
        await websocket.accept()
        key = _user_connection_key(user_id)
        if key is None:
            return
        self._user_connections[key].add(websocket)

    async def disconnect(self, websocket: WebSocket) -> None:
        for user_id in list(self._user_connections.keys()):
            self._user_connections[user_id].discard(websocket)
            if not self._user_connections[user_id]:
                self._user_connections.pop(user_id, None)

    async def broadcast_user(self, user_id: object, payload: dict[str, Any]) -> None:
        key = _user_connection_key(user_id)
        if key is None:
            return
        sockets = self._user_connections.get(key)
        if not sockets:
            return
        stale: list[WebSocket] = []
        for socket in list(sockets):
            try:
                await socket.send_json(payload)
            except Exception:
                stale.append(socket)
        for socket in stale:
            sockets.discard(socket)

    async def _dispatch_remote_message(self, message: dict[str, Any]) -> None:
        user_id = message.get("user_id")
        payload = message.get("payload")
        if _user_connection_key(user_id) is None or not isinstance(payload, dict):
            return
        await self.broadcast_user(user_id, payload)

    def publish(self, user_id: object, payload: dict[str, Any]) -> None:
        if self._loop is None or self._loop.is_closed():
            return
        message = {"user_id": user_id, "payload": payload}
        if self._bridge.publish(message):
            return
        asyncio.run_coroutine_threadsafe(self._dispatch_remote_message(message), self._loop)


user_realtime_hub = UserRealtimeHub()


def _user_connection_key(user_id: object) -> str | None:
    if user_id is None:
        return None
    key = str(user_id).strip()
    if not key:
        return None
    return key


def _iso_timestamp(value: Any) -> str | None:
    if value is None:
        return None
    try:
        return value.isoformat()
    except AttributeError:
        return None


def _notification_payload(notification: Notification, event_type: str) -> dict[str, Any]:
    return {
        "type": event_type,
        "notification_id": notification.id,
        "notification_type": getattr(notification, "type", None),
        "title": getattr(notification, "title", None),
        "message": getattr(notification, "message", None),
        "link": getattr(notification, "link", None),
        "read": bool(getattr(notification, "read", False)),
        "created_at": _iso_timestamp(getattr(notification, "created_at", None)),
        "level": "info",
    }


def _ticket_link(ticket_id: int | None) -> str | None:
    if ticket_id is None:
        return None
    return f"/tickets/{ticket_id}"


def _ticket_reply_payload(reply: TicketReply) -> dict[str, Any]:
    is_admin = bool(getattr(reply, "is_admin", False))
    title = "Support replied" if is_admin else "New ticket reply"
    message = getattr(reply, "message", None) or "There is a new update on your support ticket."
    return {
        "type": "ticket.reply_created",
        "ticket_id": reply.ticket_id,
        "reply_id": reply.id,
        "is_admin": is_admin,
        "title": title,
        "message": message,
        "link": _ticket_link(reply.ticket_id),
        "level": "info",
    }


def _ticket_status_payload(ticket: SupportTicket) -> dict[str, Any]:
    status = getattr(ticket, "status", None)
    status_label = str(status).replace("_", " ").title() if status else "Updated"
    return {
        "type": "ticket.updated",
        "ticket_id": ticket.id,
        "status": status,
        "title": f"Ticket {status_label}",
        "message": f"Your support ticket is now {status_label.lower()}.",
        "link": _ticket_link(ticket.id),
        "level": "info",
    }


def _admin_alert_payload(alert_type: str, **extra: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {"type": alert_type, "level": "warning", **extra}

    if alert_type == "admin.alert.ticket":
        ticket_id = extra.get("ticket_id")
        status = extra.get("status")
        is_admin = bool(extra.get("is_admin", False))
        if extra.get("reply_id"):
            payload.update(
                {
                    "title": "Ticket updated",
                    "message": "A customer or staff reply was added to a support ticket." if not is_admin else "A staff reply was added to a support ticket.",
                }
            )
        else:
            payload.update(
                {
                    "title": "Support ticket needs attention",
                    "message": f"Ticket #{ticket_id} is {status}." if ticket_id and status else "A support ticket needs attention.",
                }
            )
        payload["link"] = "/admin/dashboard"
    elif alert_type == "admin.alert.product":
        payload.update(
            {
                "title": "Product review pending",
                "message": f"Product #{extra.get('product_id')} is awaiting moderation." if extra.get("product_id") else "A product is awaiting moderation.",
                "link": "/admin/product-verification",
            }
        )
    elif alert_type == "admin.alert.supplier":
        payload.update(
            {
                "title": "Supplier review pending",
                "message": f"Supplier #{extra.get('supplier_id')} is awaiting verification." if extra.get("supplier_id") else "A supplier verification request is awaiting review.",
                "link": "/admin/suppliers",
            }
        )
    elif alert_type == "admin.alert.payout":
        payload.update(
            {
                "title": "Payout review pending",
                "message": f"Payout #{extra.get('payout_id')} requires review." if extra.get("payout_id") else "A payout request requires review.",
                "link": "/admin/dashboard",
            }
        )
    elif alert_type == "admin.alert.audit":
        action = extra.get("action")
        payload.update(
            {
                "title": "New audit event",
                "message": f"Audit action recorded: {action}." if action else "A new audit event was recorded.",
                "link": "/admin/audit-logs",
            }
        )
    elif alert_type == "admin.alert.dispute":
        dispute_id = extra.get("dispute_id")
        status = extra.get("status")
        supplier_id = extra.get("supplier_id")
        payload.update(
            {
                "title": "Supplier dispute needs review",
                "message": (
                    f"Dispute #{dispute_id} from supplier #{supplier_id} is {status}."
                    if dispute_id and supplier_id and status
                    else "A supplier dispute was submitted and needs review."
                ),
                "link": "/admin/disputes",
            }
        )

    return payload


def _queue_user_event(session: OrmSession, user_id: object, payload: dict[str, Any]) -> None:
    key = _user_connection_key(user_id)
    if key is None:
        return
    queued = session.info.setdefault(_REALTIME_EVENTS_KEY, [])
    queued.append((key, payload))


def _queue_user_events(session: OrmSession, user_ids: list[object], payload: dict[str, Any]) -> None:
    for user_id in user_ids:
        _queue_user_event(session, user_id, payload)


def _staff_user_ids_for_permission(session: OrmSession, permission: str) -> list[object]:
    cache = session.info.setdefault(_REALTIME_STAFF_CACHE_KEY, {})
    if permission in cache:
        return cache[permission]

    roles = _ADMIN_ALERT_ROLE_MAP.get(permission, frozenset())
    if not roles:
        cache[permission] = []
        return []

    rows = (
        session.query(User.id)
        .filter(and_(User.role.in_(tuple(roles)), User.is_active == 1))
        .all()
    )
    user_ids = [user_id for (user_id,) in rows if _user_connection_key(user_id) is not None]
    cache[permission] = user_ids
    return user_ids


def _ticket_user_id(reply: TicketReply) -> object:
    ticket = reply.ticket
    if ticket is not None and getattr(ticket, "user_id", None) is not None:
        return getattr(ticket, "user_id")
    return None


@event.listens_for(OrmSession, "after_flush")
def _collect_realtime_events(session: OrmSession, flush_context) -> None:  # pragma: no cover - exercised via commit tests
    for obj in session.new:
        if isinstance(obj, Notification):
            _queue_user_event(
                session,
                getattr(obj, "user_id", None),
                _notification_payload(obj, "notification.created"),
            )
        elif isinstance(obj, SupportTicket):
            _queue_user_event(
                session,
                getattr(obj, "user_id", None),
                {
                    "type": "ticket.created",
                    "ticket_id": obj.id,
                    "status": getattr(obj, "status", None),
                    "title": "Ticket received",
                    "message": "Your support ticket has been created.",
                    "link": _ticket_link(obj.id),
                    "level": "info",
                },
            )
            _queue_user_events(
                session,
                _staff_user_ids_for_permission(session, "tickets.manage"),
                _admin_alert_payload(
                    "admin.alert.ticket",
                    ticket_id=obj.id,
                    status=getattr(obj, "status", None),
                ),
            )
        elif isinstance(obj, TicketReply):
            _queue_user_event(
                session,
                _ticket_user_id(obj),
                _ticket_reply_payload(obj),
            )
            _queue_user_events(
                session,
                _staff_user_ids_for_permission(session, "tickets.manage"),
                _admin_alert_payload(
                    "admin.alert.ticket",
                    ticket_id=obj.ticket_id,
                    reply_id=obj.id,
                    is_admin=bool(getattr(obj, "is_admin", False)),
                ),
            )
        elif isinstance(obj, Product) and bool(getattr(obj, "is_approved", True)) is False:
            _queue_user_events(
                session,
                _staff_user_ids_for_permission(session, "moderation.products"),
                _admin_alert_payload(
                    "admin.alert.product",
                    product_id=obj.id,
                    supplier_id=getattr(obj, "supplier_id", None),
                ),
            )
        elif isinstance(obj, Payout):
            _queue_user_events(
                session,
                _staff_user_ids_for_permission(session, "payouts.verify"),
                _admin_alert_payload(
                    "admin.alert.payout",
                    payout_id=obj.id,
                    status=getattr(obj, "status", None),
                ),
            )
        elif isinstance(obj, InternalEmail):
            # New internal email — notify all recipients so their
            # inbox badge and folder tree unread count update live.
            recipients = obj.recipients
            if isinstance(recipients, str):
                import json
                recipients = json.loads(recipients)
            if isinstance(recipients, list):
                for entry in recipients:
                    if isinstance(entry, dict):
                        uid = entry.get("user_id")
                        if uid is not None:
                            _queue_user_event(
                                session,
                                uid,
                                {
                                    "type": "email.received",
                                    "email_id": obj.id,
                                    "thread_id": obj.thread_id,
                                    "subject": obj.subject,
                                    "sender_id": obj.sender_id,
                                    "folder_id": obj.folder_id,
                                    "unread": True,
                                },
                            )
        elif isinstance(obj, SupplierProfile):
            verification_status = getattr(obj, "verification_status", None)
            if verification_status in {None, "pending", "under_review"}:
                _queue_user_events(
                    session,
                    _staff_user_ids_for_permission(session, "moderation.suppliers"),
                    _admin_alert_payload(
                        "admin.alert.supplier",
                        supplier_id=getattr(obj, "user_id", None),
                        status=verification_status,
                    ),
                )
        elif isinstance(obj, AuditLog):
            _queue_user_events(
                session,
                _staff_user_ids_for_permission(session, "audit.read"),
                _admin_alert_payload(
                    "admin.alert.audit",
                    audit_id=obj.id,
                    action=getattr(obj, "action", None),
                    status=getattr(obj, "status", None),
                ),
            )
        elif isinstance(obj, SupplierDispute):
            _queue_user_events(
                session,
                _staff_user_ids_for_permission(session, "moderation.suppliers"),
                _admin_alert_payload(
                    "admin.alert.dispute",
                    dispute_id=obj.id,
                    supplier_id=getattr(obj, "supplier_id", None),
                    status=getattr(obj, "status", None),
                ),
            )

    for obj in session.dirty:
        if isinstance(obj, Notification):
            state = sa_inspect(obj)
            if state.attrs.read.history.has_changes():
                _queue_user_event(
                    session,
                    getattr(obj, "user_id", None),
                    _notification_payload(obj, "notification.updated"),
                )
        elif isinstance(obj, SupportTicket):
            state = sa_inspect(obj)
            if state.attrs.status.history.has_changes():
                _queue_user_event(
                    session,
                    getattr(obj, "user_id", None),
                    _ticket_status_payload(obj),
                )
                _queue_user_events(
                    session,
                    _staff_user_ids_for_permission(session, "tickets.manage"),
                    _admin_alert_payload(
                        "admin.alert.ticket",
                        ticket_id=obj.id,
                        status=getattr(obj, "status", None),
                    ),
                )
        elif isinstance(obj, SupplierProfile):
            state = sa_inspect(obj)
            if state.attrs.verification_status.history.has_changes():
                verification_status = getattr(obj, "verification_status", None)
                if verification_status in {None, "pending", "under_review"}:
                    _queue_user_events(
                        session,
                        _staff_user_ids_for_permission(session, "moderation.suppliers"),
                        _admin_alert_payload(
                            "admin.alert.supplier",
                            supplier_id=getattr(obj, "user_id", None),
                            status=verification_status,
                        ),
                    )
        elif isinstance(obj, SupplierDispute):
            state = sa_inspect(obj)
            if state.attrs.status.history.has_changes():
                _queue_user_events(
                    session,
                    _staff_user_ids_for_permission(session, "moderation.suppliers"),
                    _admin_alert_payload(
                        "admin.alert.dispute",
                        dispute_id=obj.id,
                        supplier_id=getattr(obj, "supplier_id", None),
                        status=getattr(obj, "status", None),
                    ),
                )

    for obj in session.deleted:
        if isinstance(obj, Notification):
            _queue_user_event(
                session,
                getattr(obj, "user_id", None),
                _notification_payload(obj, "notification.deleted"),
            )


@event.listens_for(OrmSession, "after_commit")
def _publish_realtime_events(session: OrmSession) -> None:  # pragma: no cover - exercised via commit tests
    queued = session.info.pop(_REALTIME_EVENTS_KEY, [])
    session.info.pop(_REALTIME_STAFF_CACHE_KEY, None)
    seen: set[tuple[str, tuple[tuple[str, Any], ...]]] = set()
    for user_id, payload in queued:
        key = (str(user_id), tuple(sorted(payload.items())))
        if key in seen:
            continue
        seen.add(key)
        user_realtime_hub.publish(user_id, payload)


@event.listens_for(OrmSession, "after_rollback")
def _clear_realtime_events(session: OrmSession) -> None:  # pragma: no cover - rollback path
    session.info.pop(_REALTIME_EVENTS_KEY, None)
    session.info.pop(_REALTIME_STAFF_CACHE_KEY, None)

