"""Database health monitoring service."""

from typing import Any, cast
from sqlalchemy import text, func, select, Table, MetaData
from sqlalchemy.orm import Session


def check_database_health(db: Session) -> tuple[bool, str]:
    try:
        db.execute(text("SELECT 1"))
        return True, "ok"
    except Exception:
        return False, "connection_failed"


def get_table_row_count(db: Session, table_name: str) -> int | None:
    try:
        if not table_name or not table_name.replace("_", "").isalnum():
            return None
        metadata = MetaData()
        table = Table(table_name, metadata, autoload_with=db.get_bind())
        count_value = db.execute(select(func.count()).select_from(table)).scalar()
        return 0 if count_value is None else int(count_value)
    except Exception:
        return None


def get_alembic_version(db: Session) -> str | None:
    version_value = db.execute(text("SELECT version_num FROM alembic_version LIMIT 1")).scalar()
    return str(version_value) if version_value is not None else None
