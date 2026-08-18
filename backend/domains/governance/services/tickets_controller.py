"""Migration re-export shim for the old controller module `tickets_controller`.
Symbols resolve to their real domain/infra homes.
"""
from __future__ import annotations

from modules.admin.routers.admin import reply_ticket

# Unresolved during migration: list_tickets_route, ticket_detail, update_ticket_status_route
