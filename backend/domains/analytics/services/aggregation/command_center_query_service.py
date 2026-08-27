from __future__ import annotations

from typing import Any, Optional

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
import logging
import structlog
logger = structlog.get_logger(__name__)
logger = logging.getLogger(__name__)


_ALLOWED_TABLES = {
    "orders", "order_items", "shipments", "users", "user_sessions",
    "employees", "system_health_events", "logistics_partners", "accounts",
    "account_balances", "products", "system_alerts", "fraud_alerts",
    "executive_news", "support_tickets", "return_requests", "search_logs",
    "supplier_profiles", "employee_work_logs", "supplier_kyc_requirements",
}


def _validate_table_name(table_name: str) -> str:
    normalized = table_name.strip().lower()
    if normalized not in _ALLOWED_TABLES:
        raise ValueError(f"Table '{table_name}' is not allowed in command center queries")
    return normalized


def _validate_where_clause(where: str) -> str:
    allowed_chars = set(
        "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_ =<>!()',:/.%+-*"
    )
    if not all(c in allowed_chars for c in where):
        raise ValueError("Unsafe characters in WHERE clause")
    return where


def safe_fetch(db: Session, sql: str, params: dict | None = None, scalar: bool = False) -> Any:
    try:
        result = db.execute(text(sql), params or {})
        return result.scalar() if scalar else result.fetchall()
    except SQLAlchemyError:
        logger.exception("Database error in safe_fetch")
        raise


def safe_count(db: Session, table: str, where: Optional[str] = None, params: dict | None = None) -> Any:
    validated_table = _validate_table_name(table)
    if where is None:
        sql = f"SELECT COUNT(*) FROM {validated_table}"
        return safe_fetch(db, sql, params, scalar=True)
    _validate_where_clause(where)
    sql = f"SELECT COUNT(*) FROM {validated_table} WHERE {where}"
    return safe_fetch(db, sql, params, scalar=True)
