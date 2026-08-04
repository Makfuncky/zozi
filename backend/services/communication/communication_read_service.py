"""Service methods for unified inbox communication queries."""
from sqlalchemy import Row, text
from sqlalchemy.orm import Session
from typing import Any
from utils.datetime_utils import utcnow as _utcnow


def get_command_center_metrics(db: Session) -> dict:
    """Get real-time command center metrics.

    Uses the safe scalar helpers so a missing/renamed table degrades to 0
    instead of raising a 500 during the metrics scrape.
    """
    return {
        "active_employees": get_safe_scalar(
            db, "SELECT COUNT(*) FROM employees WHERE employment_status = 'active'"
        ),
        "today_attendance": get_safe_scalar(
            db, "SELECT COUNT(*) FROM employee_attendance WHERE date = CURRENT_DATE"
        ),
        "active_meeting_rooms": get_safe_scalar(
            db, "SELECT COUNT(*) FROM video_rooms WHERE created_at >= CURRENT_DATE"
        ),
        "active_chat_threads": get_safe_scalar(
            db, "SELECT COUNT(*) FROM entity_chat_threads"
        ),
        "last_updated": _utcnow().isoformat(),
    }


def execute_unified_inbox_query(db: Session, sql: str, params: dict) -> list[Row]:
    """Execute a parameterized SQL query for the unified inbox."""
    result = db.execute(db.text(sql) if hasattr(db, 'text') else sql, params)
    if hasattr(result, 'mappings'):
        return result.mappings().all()
    return result.fetchall()


def get_safe_scalar(db: Session, sql: str, params: dict | None = None) -> Any:
    """Execute a SQL scalar query safely."""
    from sqlalchemy import text
    try:
        return db.execute(text(sql), params or {}).scalar() or 0
    except Exception:
        return 0


def get_safe_fetch(db: Session, sql: str, params: dict | None = None, scalar: bool = False) -> Any:
    """Execute a SQL fetch query safely."""
    from sqlalchemy import text
    try:
        result = db.execute(text(sql), params or {})
        return result.scalar() if scalar else result.fetchall()
    except Exception:
        return 0 if scalar else []


def get_safe_count(db: Session, table: str, where: str, params: dict | None = None) -> Any:
    """Execute a safe count query."""
    from sqlalchemy import text
    query = text("SELECT COUNT(*) FROM " + table + " WHERE " + where)
    if params:
        query = query.bindparams(**params)
    try:
        return db.execute(query).scalar() or 0
    except Exception:
        return 0
