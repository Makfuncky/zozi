from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Optional, Union

from sqlalchemy import (
    Column,
    ColumnElement,
    MetaData,
    Table,
    bindparam,
    func,
    select,
    text,
)
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from sqlalchemy.types import NullType
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


_BLOCKED_KEYWORDS = frozenset({
    "union", "select", "insert", "update", "delete", "drop", "create",
    "alter", "truncate", "grant", "revoke", "exec", "execute", "xp_",
})
_KEYWORD_PATTERN = re.compile(
    r'\b(?:' + '|'.join(re.escape(k) for k in _BLOCKED_KEYWORDS) + r')\b',
    re.IGNORECASE,
)


_COLUMN_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

_COMPARISON_OPERATORS = {
    "eq": lambda col, bp: col == bp,
    "ne": lambda col, bp: col != bp,
    "lt": lambda col, bp: col < bp,
    "le": lambda col, bp: col <= bp,
    "gt": lambda col, bp: col > bp,
    "ge": lambda col, bp: col >= bp,
    "like": lambda col, bp: col.like(bp),
    "ilike": lambda col, bp: col.ilike(bp),
}

_PREDICATE_OPERATORS = frozenset(
    set(_COMPARISON_OPERATORS) | {"in", "not_in", "between", "is_null", "not_null"}
)


@dataclass(frozen=True)
class Predicate:
    """One structured WHERE term for :func:`safe_count`.

    ``column`` is a bare identifier, ``operator`` is a name drawn from
    ``_PREDICATE_OPERATORS``, and ``value`` is carried to the database as a bound
    parameter. The caller never supplies SQL text.
    """
    column: str
    operator: str
    value: Any = None


def _validate_where_clause(where: Any) -> Union[None, ColumnElement, list[Predicate]]:
    """Validate and normalise the ``where`` argument of :func:`safe_count`.

    A raw SQL fragment is refused outright. A WHERE fragment cannot be
    parameterised, and no character allowlist plus keyword denylist can make one
    safe: that pairing is exactly what let ``1=1 or pg_sleep(5)=1`` through to
    the database. Callers now pass either a SQLAlchemy Core/ORM boolean
    expression or a sequence of :class:`Predicate` terms, so every value reaches
    the database as a bound parameter.
    """
    if where is None:
        return None
    if isinstance(where, str):
        logger.warning(
            "command_center_query_service.safe_count refused a raw WHERE fragment "
            "(possible SQL injection attempt): %.120s",
            where,
        )
        raise ValueError(
            "Raw WHERE fragments are not accepted by safe_count; pass a SQLAlchemy "
            "boolean expression or Predicate terms so every value stays bound"
        )
    if isinstance(where, ColumnElement):
        return where
    if isinstance(where, Predicate):
        return [where]
    if isinstance(where, (list, tuple)) and all(isinstance(t, Predicate) for t in where):
        return list(where)
    logger.warning(
        "command_center_query_service.safe_count refused a WHERE argument of type %s",
        type(where).__name__,
    )
    raise ValueError(
        "where must be None, a SQLAlchemy boolean expression, or Predicate term(s)"
    )


def _normalize_predicate(predicate: Predicate) -> tuple[str, str]:
    """Validate a predicate's identifiers before any SQL object is built."""
    column_name = str(predicate.column).strip()
    if not _COLUMN_PATTERN.match(column_name):
        raise ValueError(
            f"Predicate column {predicate.column!r} is not a valid column identifier"
        )
    op_name = str(predicate.operator).strip().lower()
    if op_name not in _PREDICATE_OPERATORS:
        raise ValueError(f"Predicate operator {predicate.operator!r} is not allowed")
    return column_name, op_name


def _render_predicate(
    table_obj: Table, column_name: str, op_name: str, value: Any, index: int
) -> Any:
    """Render one already-validated :class:`Predicate` into a bound expression."""
    column = table_obj.c[column_name]

    if op_name == "is_null":
        return column.is_(None)
    if op_name == "not_null":
        return column.is_not(None)
    if op_name in ("in", "not_in"):
        if not isinstance(value, (list, tuple, set, frozenset)):
            raise ValueError(f"Operator {op_name!r} requires a list or tuple of values")
        ordered = list(value)
        if not ordered:
            raise ValueError(f"Operator {op_name!r} requires at least one value")
        # One bind parameter per element, so the statement round-trips through
        # text() without SQLAlchemy's expanding post-compile placeholders.
        bound = [
            bindparam(f"wq_{index}_{position}", item)
            for position, item in enumerate(ordered)
        ]
        return column.in_(bound) if op_name == "in" else column.not_in(bound)
    if op_name == "between":
        if not isinstance(value, (list, tuple)) or len(value) != 2:
            raise ValueError("Operator 'between' requires exactly two values")
        return column.between(
            bindparam(f"wq_{index}_lo", value[0]),
            bindparam(f"wq_{index}_hi", value[1]),
        )
    return _COMPARISON_OPERATORS[op_name](column, bindparam(f"wq_{index}", value))


def safe_fetch(db: Session, sql: str, params: dict | None = None, scalar: bool = False) -> Any:
    try:
        result = db.execute(text(sql), params or {})
        return result.scalar() if scalar else result.fetchall()
    except SQLAlchemyError:
        logger.exception("Database error in safe_fetch")
        raise


def safe_count(
    db: Session,
    table: str,
    where: Optional[Union[ColumnElement, Predicate, list[Predicate]]] = None,
    params: dict | None = None,
) -> Any:
    """Count rows in an allowlisted table under a bound-parameter predicate.

    ``where`` is either ``None``, a SQLAlchemy Core/ORM boolean expression, or a
    :class:`Predicate` (or list of them). The statement is assembled from
    SQLAlchemy Core constructs, so identifiers come from the table allowlist and
    every value is a bind parameter - no fragment is ever interpolated.
    """
    validated_table = _validate_table_name(table)
    validated_where = _validate_where_clause(where)

    if isinstance(validated_where, ColumnElement):
        # The caller owns the Table object its expression references, so the FROM
        # clause is inferred from that expression rather than forced here. The
        # table argument is still checked against the allowlist above.
        statement = select(func.count()).where(validated_where)
    else:
        predicates = validated_where or []
        # Validate every identifier before building any SQL object, so a bad
        # column or operator surfaces as ValueError at the boundary.
        normalized = [_normalize_predicate(p) for p in predicates]
        column_names = sorted({column_name for column_name, _ in normalized})
        table_obj = Table(
            validated_table,
            MetaData(),
            *(Column(name, NullType) for name in column_names),
        )
        statement = select(func.count()).select_from(table_obj)
        for index, predicate in enumerate(predicates):
            column_name, op_name = normalized[index]
            statement = statement.where(
                _render_predicate(
                    table_obj, column_name, op_name, predicate.value, index
                )
            )

    compiled = statement.compile()
    bound_params = compiled.params or {}
    return safe_fetch(db, compiled.string, {**(params or {}), **bound_params}, scalar=True)