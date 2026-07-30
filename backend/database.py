"""Compatibility shim for ``database -> db.database`` imports.

New code should import directly from ``db.database``.
This module is kept for backward compatibility with existing imports.
"""
from __future__ import annotations

import db.database as _real

DATABASE_URL = _real.DATABASE_URL
engine = _real.engine
SessionLocal = _real.SessionLocal
Base = _real.Base
get_db = _real.get_db
get_db_session = _real.get_db_session
get_service_session = _real.get_service_session
get_db_context = _real.get_db_context
get_db_sync = _real.get_db_sync
check_connection_health = _real.check_connection_health
get_pool_metrics = _real.get_pool_metrics
dispose_engine = _real.dispose_engine
create_tables = _real.create_tables
reset_tables = _real.reset_tables
close_db_session = _real.close_db_session
