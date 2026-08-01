"""
Database dependency facade.

Controllers and routers should import session/db helpers from this module
instead of reaching directly into ``db.database`` (DG layer-contract
violation: controllers must not depend on db.database directly).

Everything here is re-exported from the canonical ``db.database`` module.
"""
from __future__ import annotations

from db.database import (
    SessionLocal,
    check_connection_health,
    close_db_session,
    create_tables,
    dispose_engine,
    engine,
    get_db,
    get_db_context,
    get_db_session,
    get_db_sync,
    get_pool_metrics,
    get_service_session,
    reset_tables,
)

__all__ = [
    "SessionLocal",
    "check_connection_health",
    "close_db_session",
    "create_tables",
    "dispose_engine",
    "engine",
    "get_db",
    "get_db_context",
    "get_db_session",
    "get_db_sync",
    "get_pool_metrics",
    "get_service_session",
    "reset_tables",
]
