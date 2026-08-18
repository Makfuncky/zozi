"""Session/engine access facade.

Routers, controllers and utils must obtain a SQLAlchemy session handle
from this facade instead of `db.database`, so the dependency-graph
layer contract (those layers may not depend on `db.database`) holds.
All symbols are re-exported unchanged from `db.database`.
"""
from __future__ import annotations

from db.database import (
    SessionLocal,
    check_connection_health,
    engine,
    get_db,
    get_db_context,
    get_db_session,
    get_service_session,
)
