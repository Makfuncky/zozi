import time
from typing import Any

import structlog
from sqlalchemy import event
from sqlalchemy.engine import Connection, Engine
from sqlalchemy.orm import Session

from utils.logging_config import db_query_time_ctx
from utils.metrics import db_query_duration_seconds


def _before_cursor_execute(
    conn: Connection,
    cursor: Any,
    statement: str,
    parameters: Any,
    context: Any | None,
    executemany: bool,
) -> None:
    conn.info.setdefault("query_start_time", []).append(time.monotonic())


def _after_cursor_execute(
    conn: Connection,
    cursor: Any,
    statement: str,
    parameters: Any,
    context: Any | None,
    executemany: bool,
) -> None:
    start_times = conn.info.get("query_start_time", [])
    if start_times:
        start_time = start_times.pop()
        duration = time.monotonic() - start_time
        duration_ms = round(duration * 1000, 2)

        cumulative = db_query_time_ctx.get(0.0)
        db_query_time_ctx.set(cumulative + duration_ms)

        query_type = statement.strip().split()[0].lower() if statement.strip() else "unknown"
        db_query_duration_seconds.labels(query_type=query_type).observe(duration)

        log = structlog.get_logger("zozi.db")
        log.debug(
            "db_query",
            query_type=query_type,
            duration_ms=duration_ms,
            statement_length=len(statement),
        )


def instrument_database_engine(engine: Engine) -> None:
    event.listen(engine, "before_cursor_execute", _before_cursor_execute)
    event.listen(engine, "after_cursor_execute", _after_cursor_execute)

    log = structlog.get_logger("zozi.db")
    log.info("Database query instrumentation enabled")


def get_db_pool_metrics(db: Session) -> dict[str, Any]:
    engine = db.get_bind()
    pool = engine.pool
    return {
        "size": pool.size(),
        "checkedin": pool.checkedin(),
        "overflow": pool.overflow(),
        "checkedout": pool.checkedout(),
    }

