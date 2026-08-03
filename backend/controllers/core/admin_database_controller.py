"""Admin database health and management controller."""
from __future__ import annotations

import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional, cast
from sqlalchemy import inspect
from sqlalchemy.engine.url import make_url
from sqlalchemy.orm import Session

from data.base import Base
from utils.auth import get_redis_health_status
from utils.backup import get_backup_manager
from utils.cache import cache_get_json, cache_set_json
from utils.config import settings
from services.core.db_health_service import check_database_health, get_table_row_count, get_alembic_version


def _database_health_snapshot(db: Session) -> tuple[bool, str]:
    return check_database_health(db)


def _safe_database_location() -> str:
    if settings.database_url == "sqlite:///:memory:":
        return ":memory:"
    if settings.database_url.startswith("sqlite:///"):
        return settings.database_url.removeprefix("sqlite:///")
    return "managed server"


def _table_row_count(db: Session, table_name: str) -> int | None:
    return get_table_row_count(db, table_name)


def _table_column_details(columns: list[dict[str, Any]], primary_key: list[str]) -> list[dict[str, Any]]:
    primary_key_set = {str(column) for column in primary_key}
    details: list[dict[str, Any]] = []
    for column in columns:
        column_name = column.get("name")
        if not column_name:
            continue
        details.append(
            {
                "name": str(column_name),
                "type": str(column.get("type")),
                "nullable": bool(column.get("nullable", True)),
                "default": None if column.get("default") is None else str(column.get("default")),
                "primary_key": str(column_name) in primary_key_set,
            }
        )
    return details


def _sqlite_service_snapshot(active_engine: str) -> dict[str, Any]:
    active = active_engine == "sqlite"
    location = _safe_database_location() if active else None
    exists: bool | None = None
    if active and location not in {None, ":memory:", "managed server"}:
        exists = Path(location).exists()
    return {
        "label": "SQLite",
        "status": "active" if active else "supported",
        "active": active,
        "configured": active,
        "role": "Primary relational database for local file-backed runtime when DATABASE_URL uses sqlite:///.",
        "detail": "This runtime is currently backed by a local SQLite database file." if active else "SQLite support is built in for local development, but this runtime is not pointed at SQLite.",
        "location": location,
        "exists": exists,
        "backup_format": ".sqlite",
        "backup_strategy": "sqlite online backup API",
        "handles": ["canonical relational data", "schema introspection", "local file backups"],
    }


def _postgres_service_snapshot(active_engine: str) -> dict[str, Any]:
    active = active_engine == "postgresql"
    configured = settings.database_url.startswith("postgresql")
    parsed_url = make_url(settings.database_url)
    toolchain_ready = bool(shutil.which("pg_dump") and shutil.which("pg_restore")) if (active or configured) else None
    return {
        "label": "PostgreSQL",
        "status": "active" if active else "configured" if configured else "supported",
        "active": active,
        "configured": configured,
        "role": "Server-grade relational database option for production and multi-instance deployments.",
        "detail": "This runtime is currently backed by PostgreSQL." if active else "PostgreSQL is supported as the primary relational database when DATABASE_URL uses postgresql://.",
        "host": parsed_url.host if (active or configured) else None,
        "database": parsed_url.database if (active or configured) else None,
        "driver": parsed_url.drivername if (active or configured) else None,
        "toolchain_ready": toolchain_ready,
        "backup_format": ".pgdump",
        "backup_strategy": "pg_dump -Fc",
        "handles": ["canonical relational data", "multi-instance production persistence", "compressed logical backups"],
    }


def _redis_service_snapshot() -> dict[str, Any]:
    redis_status = get_redis_health_status()
    configured = bool(redis_status.get("configured", False))
    available = bool(redis_status.get("available", False))
    backend = str(redis_status.get("backend", "memory_fallback"))
    return {
        "label": "Redis",
        "status": "ready" if available else "degraded" if configured else "not_configured",
        "active": available,
        "configured": configured,
        "available": available,
        "role": "Optional cache and shared ephemeral state store; it does not replace the primary relational database.",
        "detail": "Redis is connected and serving shared cache/state." if available else "Redis is not connected; the app falls back to in-memory state for cache-like behavior in this runtime." if configured else "Redis is not configured for this runtime.",
        "backend": backend,
        "fallback_mode": "memory" if configured and not available else None,
        "shared_state": bool(redis_status.get("shared_state", False)),
        "handles": ["token blacklist", "shared cache", "background job coordination"],
    }


def _database_architecture_snapshot(active_engine: str) -> dict[str, Any]:
    return {
        "mode": "single_primary_relational_with_optional_cache",
        "primary_database_engine": active_engine,
        "summary": "SQLite or PostgreSQL is the single source of truth for business data at runtime, selected by DATABASE_URL. Redis only accelerates cache and shared ephemeral state.",
        "write_path": "All canonical reads and writes go to the active relational database engine.",
        "cache_path": "Redis supplements the relational database for cache, token blacklist, and shared runtime state when available.",
    }


def get_database_overview(db: Session) -> dict[str, Any]:
    cache_key = "admin:db:overview"
    cached = cache_get_json(cache_key)
    if isinstance(cached, dict):
        return cached
    bind = cast(Any, db.get_bind())
    inspector = inspect(bind)
    table_names = sorted(inspector.get_table_names())
    orm_table_names = set(Base.metadata.tables.keys())
    tables: list[dict[str, Any]] = []

    for table_name in table_names:
        columns = inspector.get_columns(table_name)
        primary_key = inspector.get_pk_constraint(table_name).get("constrained_columns") or []
        indexes = inspector.get_indexes(table_name)
        foreign_keys = inspector.get_foreign_keys(table_name)
        tables.append(
            {
                "name": table_name,
                "row_count": _table_row_count(db, table_name),
                "column_count": len(columns),
                "columns": [str(column.get("name")) for column in columns if column.get("name")],
                "column_details": _table_column_details(columns, [str(column) for column in primary_key]),
                "primary_key": [str(column) for column in primary_key],
                "indexes": [str(index.get("name")) for index in indexes if index.get("name")],
                "index_count": len(indexes),
                "foreign_keys": [
                    {
                        "constrained_columns": [str(column) for column in (foreign_key.get("constrained_columns") or [])],
                        "referred_table": str(foreign_key.get("referred_table")) if foreign_key.get("referred_table") else None,
                        "referred_columns": [str(column) for column in (foreign_key.get("referred_columns") or [])],
                    }
                    for foreign_key in foreign_keys
                ],
                "foreign_key_count": len(foreign_keys),
                "orm_managed": table_name in orm_table_names,
            }
        )

    healthy, db_health = _database_health_snapshot(db)
    alembic_version: str | None = None
    if "alembic_version" in table_names:
        try:
            alembic_version = get_alembic_version(db)
        except Exception:
            alembic_version = None

    backups = get_backup_manager().list_backups()
    latest_backup = backups[0] if backups else None
    missing_model_tables = sorted(orm_table_names.difference(table_names))
    managed_table_count = sum(1 for table in tables if bool(table.get("orm_managed")))
    inspected_at = datetime.now(timezone.utc).isoformat()
    active_engine = str(bind.dialect.name)

    payload = {
        "status": "healthy" if healthy else "unhealthy",
        "inspected_at": inspected_at,
        "refresh_interval_seconds": 20,
        "database": {
            "engine": bind.dialect.name,
            "driver": bind.dialect.driver,
            "location": _safe_database_location(),
            "connected": healthy,
            "health": db_health,
            "app_env": settings.app_env,
            "runtime_profile": settings.runtime_profile,
            "alembic_version": alembic_version,
            "backup_strategy": "sqlite online backup API" if active_engine == "sqlite" else "pg_dump -Fc" if active_engine == "postgresql" else "engine-specific",
        },
        "architecture": _database_architecture_snapshot(active_engine),
        "services": {
            "sqlite": _sqlite_service_snapshot(active_engine),
            "postgresql": _postgres_service_snapshot(active_engine),
            "redis": _redis_service_snapshot(),
        },
        "backup": {
            "enabled": settings.backup_enabled,
            "artifact_count": len(backups),
            "latest_filename": latest_backup.get("filename") if latest_backup else None,
            "latest_created_at": latest_backup.get("created_at") if latest_backup else None,
            "latest_verified": latest_backup.get("verified") if latest_backup else None,
            "latest_size_bytes": latest_backup.get("size_bytes") if latest_backup else None,
        },
        "totals": {
            "table_count": len(table_names),
            "orm_model_table_count": len(orm_table_names),
            "managed_table_count": managed_table_count,
            "extra_table_count": max(len(table_names) - managed_table_count, 0),
            "missing_model_table_count": len(missing_model_tables),
        },
        "tables_missing_from_database": missing_model_tables,
        "tables": tables,
    }
    cache_set_json(cache_key, payload, 30)
    return payload


