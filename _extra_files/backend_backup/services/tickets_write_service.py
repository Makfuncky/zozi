"""Backward-compatible re-export shim for support-ticket write operations.

The canonical implementations live in `services.comms.tickets_write_service`.
Names are resolved lazily via module-level `__getattr__` so this shim never
contributes to an import-time cycle.
"""
from __future__ import annotations

import importlib
from typing import Any

_SRC = "services.comms.tickets_write_service"

_REEXPORTS: dict[str, tuple[str, str]] = {
    "admin_reply_to_ticket": (_SRC, "admin_reply_to_ticket"),
    "count_tickets": (_SRC, "count_tickets"),
    "create_notification": (_SRC, "create_notification"),
    "create_ticket_reply": (_SRC, "create_ticket_reply"),
    "create_ticket_with_message": (_SRC, "create_ticket_with_message"),
    "get_ticket_by_id": (_SRC, "get_ticket_by_id"),
    "get_ticket_messages": (_SRC, "get_ticket_messages"),
    "get_ticket_with_details": (_SRC, "get_ticket_with_details"),
    "get_tickets_query": (_SRC, "get_tickets_query"),
    "list_tickets": (_SRC, "list_tickets"),
    "update_ticket_status": (_SRC, "update_ticket_status"),
}


def __getattr__(name: str) -> Any:
    if name in _REEXPORTS:
        module_path, attr = _REEXPORTS[name]
        return getattr(importlib.import_module(module_path), attr)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
