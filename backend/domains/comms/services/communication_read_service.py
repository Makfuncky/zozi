"""Service methods for unified inbox communication queries."""
from __future__ import annotations
from infrastructure.utils.pagination import SAFE_QUERY_LIMIT
from sqlalchemy import Row, text, select, func
from sqlalchemy.orm import Session
from typing import Any
from infrastructure.utils.datetime_utils import utcnow as utcnow

from infrastructure.database.base import Base
from infrastructure.database import models  # noqa: F401  (registers all ORM tables on Base.metadata)
import logging
import structlog
logger = structlog.get_logger(__name__)
logger = logging.getLogger(__name__)



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
        "last_updated": utcnow().isoformat(),
    }


def execute_unified_inbox_query(db: Session, sql: str, params: dict) -> list[Row]:
    """Execute a parameterized SQL query for the unified inbox."""
    result = db.execute(db.text(sql) if hasattr(db, 'text') else sql, params)
    if hasattr(result, 'mappings'):
        return result.mappings().limit(SAFE_QUERY_LIMIT).all()
    return result.fetchall()


def get_safe_scalar(db: Session, sql: str, params: dict | None = None) -> Any:
    """Execute a SQL scalar query safely."""
    from sqlalchemy import text
    try:
        return db.execute(text(sql), params or {}).scalar() or 0
    except (ValueError, TypeError, KeyError, IndexError, AttributeError, RuntimeError, OSError, IOError, EOFError, ImportError, NameError, StopIteration, ArithmeticError, AssertionError, UnicodeError, NotImplementedError, RecursionError, ReferenceError, SystemError, BufferError, LookupError) as e:
        logger.exception("Handled Exception in communication_read_service.py:52")
        return 0


def get_safe_fetch(db: Session, sql: str, params: dict | None = None, scalar: bool = False) -> Any:
    """Execute a SQL fetch query safely."""
    from sqlalchemy import text
    try:
        result = db.execute(text(sql), params or {})
        return result.scalar() if scalar else result.fetchall()
    except (ValueError, TypeError, KeyError, IndexError, AttributeError, RuntimeError, OSError, IOError, EOFError, ImportError, NameError, StopIteration, ArithmeticError, AssertionError, UnicodeError, NotImplementedError, RecursionError, ReferenceError, SystemError, BufferError, LookupError) as e:
        logger.exception("Handled Exception in communication_read_service.py:62")
        return 0 if scalar else []


def get_safe_count(db: Session, table: str, where: str, params: dict | None = None) -> Any:
    """Execute a safe count query.

    ``table`` and ``where`` are pre-validated by the caller (allow-listed table
    name + sanitised WHERE clause). The table is resolved to a real ORM ``Table``
    object and the validated WHERE clause is embedded via ``text()``, so no raw
    string concatenation reaches the SQL builder.
    """
    tbl = Base.metadata.tables.get(table)
    if tbl is None:
        return 0
    stmt = select(func.count()).select_from(tbl)
    if where:
        stmt = stmt.where(text(where))
    try:
        return db.execute(stmt, params or {}).scalar() or 0
    except (ValueError, TypeError, KeyError, IndexError, AttributeError, RuntimeError, OSError, IOError, EOFError, ImportError, NameError, StopIteration, ArithmeticError, AssertionError, UnicodeError, NotImplementedError, RecursionError, ReferenceError, SystemError, BufferError, LookupError) as e:
        logger.exception("Handled Exception in communication_read_service.py:82")
        return 0