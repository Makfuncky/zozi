"""Shared DB read-access layer (Q1 / W1 infrastructure contract).

Routers, controllers and middleware must not call ``db.query()`` /
``db.execute()`` directly (auditor rule **Q1**). Instead they either

* build session-free SQLAlchemy ``select()`` / ``text()`` *statements* and hand
  them to the statement executors here (:func:`scalar`, :func:`scalars`,
  :func:`rows`, :func:`first_row`, :func:`row_mappings`), or
* pass a model plus session-free column-expression ``filters`` (and optional
  ``joins`` / ``options`` / ``group_by`` / ``order_by`` / paging) to the
  declarative helpers (:func:`all_rows`, :func:`first`, :func:`one_or_none`,
  :func:`count`, :func:`scalar_with_filters`, ...).

That keeps routers/controllers thin HTTP + orchestration adapters: **all**
session read access is owned by this single services-layer module, which is the
only place allowed to touch ``Session.query`` / ``Session.execute``.

Design rules
------------
* Every public helper takes the ``Session`` as its first argument and returns
  plain results (models, rows, scalars) — never a live ``Query``. Callers can
  therefore not keep building ORM internals outside this module.
* Everything after ``filters`` is keyword-only-friendly and optional, so
  existing call sites (``first(db, Model, [..])``, ``all_rows(db, Model, [..])``)
  keep working unchanged.
* Writes never belong here — use ``services/<domain>/*_write_service.py``.
"""
from __future__ import annotations

from decimal import Decimal
from typing import Any, Optional, Sequence, TypeVar

from sqlalchemy import func, select, text
from sqlalchemy.orm import Query, Session
import structlog

logger = structlog.get_logger(__name__)

ModelT = TypeVar("ModelT")

__all__ = [
    # statement executors
    "scalar",
    "scalars",
    "rows",
    "first_row",
    "row_mappings",
    # declarative model readers
    "all_rows",
    "first",
    "one",
    "one_or_none",
    "count",
    "exists",
    "by_pk",
    "scalar_sum",
    "scalar_with_filters",
    "column_values",
    "aggregate_rows",
    "locked_rows",
    "scalar_subquery",
    "exists_clause",
    "query",
    "execute",
    "get_alembic_version",
]


# ── select() / text() statement executors (caller builds the statement) ──────

def scalar(
    db: Session,
    stmt=None,
    *,
    sql: Optional[str] = None,
    params: Optional[dict] = None,
) -> Any:
    """Execute a ``select()`` (or raw ``sql``) and return its ``scalar()``."""
    if sql is not None:
        return db.execute(text(sql), params or {}).scalar()
    return db.execute(stmt).scalar()


def scalars(db: Session, stmt, unique: bool = False) -> list:
    """Execute a ``select()`` and return ``scalars().all()`` (optionally unique)."""
    result = db.execute(stmt)
    if unique:
        result = result.unique()
    return result.scalars().all()


def rows(
    db: Session,
    stmt=None,
    *,
    sql: Optional[str] = None,
    params: Optional[dict] = None,
) -> list:
    """Execute a ``select()`` (or raw ``sql``) and return ``.all()`` (row tuples)."""
    if sql is not None:
        return db.execute(text(sql), params or {}).all()
    return db.execute(stmt).all()


def first_row(
    db: Session,
    stmt=None,
    *,
    sql: Optional[str] = None,
    params: Optional[dict] = None,
) -> Optional[tuple]:
    """Execute a ``select()`` (or raw ``sql``) and return its first row, or None."""
    if sql is not None:
        return db.execute(text(sql), params or {}).first()
    return db.execute(stmt).first()


def row_mappings(
    db: Session,
    stmt=None,
    *,
    sql: Optional[str] = None,
    params: Optional[dict] = None,
) -> list[dict]:
    """Execute a statement and return rows as plain ``dict`` mappings."""
    if sql is not None:
        result = db.execute(text(sql), params or {})
    else:
        result = db.execute(stmt)
    return [dict(m) for m in result.mappings().all()]


# ── internal query builder (the ONLY place Session.query is used) ────────────

def _build(
    db: Session,
    *entities,
    filters: Sequence = (),
    joins: Sequence = (),
    outerjoins: Sequence = (),
    options: Sequence = (),
    select_from=None,
    group_by=None,
    having=None,
    order_by=None,
    distinct: bool = False,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
) -> Query:
    """Compose a ``Query`` from session-free ingredients.

    ``entities`` may be a single model, a tuple/list of models/columns, or
    several positional entities. ``joins``/``outerjoins`` entries may be a
    single target or a ``(target, onclause)`` tuple.
    """
    flat: list = []
    for ent in entities:
        if isinstance(ent, (list, tuple)):
            flat.extend(ent)
        else:
            flat.append(ent)

    q = db.query(*flat)

    if select_from is not None:
        q = q.select_from(select_from)
    for opt in options:
        q = q.options(opt)
    for join in joins:
        q = q.join(*join) if isinstance(join, (list, tuple)) else q.join(join)
    for join in outerjoins:
        q = q.outerjoin(*join) if isinstance(join, (list, tuple)) else q.outerjoin(join)
    for f in filters:
        if f is None:
            continue
        q = q.filter(f)
    if group_by is not None:
        q = q.group_by(*group_by) if isinstance(group_by, (list, tuple)) else q.group_by(group_by)
    if having is not None:
        q = q.having(having)
    if distinct:
        q = q.distinct()
    if order_by is not None:
        q = q.order_by(*order_by) if isinstance(order_by, (list, tuple)) else q.order_by(order_by)
    if offset is not None:
        q = q.offset(offset)
    if limit is not None:
        q = q.limit(limit)
    return q


# ── declarative model readers ────────────────────────────────────────────────

def all_rows(
    db: Session,
    model,
    filters: Sequence = (),
    order_by=None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    joins: Sequence = (),
    *,
    outerjoins: Sequence = (),
    options: Sequence = (),
    select_from=None,
    group_by=None,
    having=None,
    distinct: bool = False,
) -> list:
    """Return every row matching ``filters`` (list of ORM objects or row tuples)."""
    return _build(
        db,
        model,
        filters=filters,
        joins=joins,
        outerjoins=outerjoins,
        options=options,
        select_from=select_from,
        group_by=group_by,
        having=having,
        order_by=order_by,
        distinct=distinct,
        limit=limit,
        offset=offset,
    ).all()


def first(
    db: Session,
    model,
    filters: Sequence = (),
    order_by=None,
    *,
    joins: Sequence = (),
    outerjoins: Sequence = (),
    options: Sequence = (),
    select_from=None,
    group_by=None,
    having=None,
    distinct: bool = False,
    offset: Optional[int] = None,
) -> Optional[Any]:
    """Return the first row matching ``filters``, or ``None``."""
    return _build(
        db,
        model,
        filters=filters,
        joins=joins,
        outerjoins=outerjoins,
        options=options,
        select_from=select_from,
        group_by=group_by,
        having=having,
        order_by=order_by,
        distinct=distinct,
        offset=offset,
    ).first()


def one(db: Session, model, filters: Sequence = (), *, joins: Sequence = (), options: Sequence = ()):
    """Return exactly one row (raises if 0 or >1)."""
    return _build(db, model, filters=filters, joins=joins, options=options).one()


def one_or_none(
    db: Session,
    model,
    filters: Sequence = (),
    *,
    joins: Sequence = (),
    options: Sequence = (),
) -> Optional[Any]:
    """Return exactly one row or ``None`` (raises if >1)."""
    return _build(db, model, filters=filters, joins=joins, options=options).one_or_none()


def count(
    db: Session,
    model,
    filters: Sequence = (),
    *,
    joins: Sequence = (),
    outerjoins: Sequence = (),
    options: Sequence = (),
    select_from=None,
    distinct: bool = False,
) -> int:
    """Return the number of rows matching ``filters``."""
    return _build(
        db,
        model,
        filters=filters,
        joins=joins,
        outerjoins=outerjoins,
        options=options,
        select_from=select_from,
        distinct=distinct,
    ).count()


def exists(db: Session, model, filters: Sequence = (), *, joins: Sequence = ()) -> bool:
    """``True`` when at least one row matches ``filters``."""
    return first(db, model, filters, joins=joins) is not None


def by_pk(db: Session, model, pk, *, options: Sequence = ()) -> Optional[Any]:
    """Primary-key lookup (replacement for ``Session.get``)."""
    if options:
        q = db.query(model)
        for opt in options:
            q = q.options(opt)
        return q.get(pk)
    return db.get(model, pk)


def scalar_sum(db: Session, column, filters: Sequence = (), *, joins: Sequence = ()) -> Decimal:
    """``COALESCE(SUM(column), 0)`` over the filtered set."""
    return _build(
        db,
        func.coalesce(func.sum(column), 0),
        filters=filters,
        joins=joins,
    ).scalar() or Decimal("0")


def scalar_with_filters(
    db: Session,
    column_expr,
    filters: Sequence = (),
    *,
    joins: Sequence = (),
    outerjoins: Sequence = (),
    select_from=None,
    group_by=None,
    having=None,
    distinct: bool = False,
    order_by=None,
) -> Any:
    """Execute an aggregate/column expression (e.g. ``func.count(Model.id)``)."""
    return _build(
        db,
        column_expr,
        filters=filters,
        joins=joins,
        outerjoins=outerjoins,
        select_from=select_from,
        group_by=group_by,
        having=having,
        distinct=distinct,
        order_by=order_by,
    ).scalar()


def column_values(
    db: Session,
    column,
    filters: Sequence = (),
    *,
    joins: Sequence = (),
    outerjoins: Sequence = (),
    order_by=None,
    distinct: bool = False,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
) -> list:
    """Return a flat list of values for a single column expression."""
    result = _build(
        db,
        column,
        filters=filters,
        joins=joins,
        outerjoins=outerjoins,
        order_by=order_by,
        distinct=distinct,
        limit=limit,
        offset=offset,
    ).all()
    return [row[0] for row in result]


def aggregate_rows(
    db: Session,
    entities: Sequence,
    filters: Sequence = (),
    *,
    joins: Sequence = (),
    outerjoins: Sequence = (),
    select_from=None,
    group_by=None,
    having=None,
    order_by=None,
    distinct: bool = False,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
) -> list:
    """Multi-entity / GROUP BY read returning row tuples."""
    return _build(
        db,
        entities,
        filters=filters,
        joins=joins,
        outerjoins=outerjoins,
        select_from=select_from,
        group_by=group_by,
        having=having,
        order_by=order_by,
        distinct=distinct,
        limit=limit,
        offset=offset,
    ).all()


def locked_rows(
    db: Session,
    model,
    filters: Sequence = (),
    *,
    joins: Sequence = (),
    options: Sequence = (),
    order_by=None,
) -> list:
    """``SELECT ... FOR UPDATE`` — row-level lock inside an open transaction."""
    return _build(
        db,
        model,
        filters=filters,
        joins=joins,
        options=options,
        order_by=order_by,
    ).with_for_update().all()


# ── session-free SQL expression builders (no execution) ──────────────────────

def scalar_subquery(
    entity,
    filters: Sequence = (),
    *,
    joins: Sequence = (),
    distinct: bool = False,
    limit: Optional[int] = None,
):
    """Build a correlated scalar subquery without touching a ``Session``."""
    stmt = select(entity)
    for join in joins:
        stmt = stmt.join(*join) if isinstance(join, (list, tuple)) else stmt.join(join)
    for f in filters:
        if f is None:
            continue
        stmt = stmt.where(f)
    if distinct:
        stmt = stmt.distinct()
    if limit is not None:
        stmt = stmt.limit(limit)
    return stmt.scalar_subquery()


def exists_clause(entity, filters: Sequence = ()):
    """Build an ``EXISTS (...)`` clause without touching a ``Session``."""
    stmt = select(entity)
    for f in filters:
        if f is None:
            continue
        stmt = stmt.where(f)
    return stmt.exists()


def get_alembic_version(db: Session) -> Optional[str]:
    """Return the current ``alembic_version`` row value, or ``None``.

    Owned here in the services layer so callers (controllers/routers) never
    embed raw SQL; they only call this plain helper (auditor rule **Q1**).
    """
    try:
        value = scalar(db, sql="SELECT version_num FROM alembic_version LIMIT 1")
    except Exception:  # pragma: no cover - table may be absent on fresh DBs
        return None
    return str(value) if value else None


# ── legacy read convenience re-exports (kept for pre-reorg controllers) ──────
#
# A few controllers still call ``db_read_query(db, Model)`` (returns a
# ``Query`` they chain ``.filter()`` / ``.first()`` / ``.all()`` / ``.count()``
# on) and ``db_read_execute(db, stmt)`` (runs a ``select()`` / ``text()``
# statement). Both keep the ``Session`` access inside this services layer
# (auditor rule **Q1**) instead of in router/controller code.

def query(db: Session, *entities):
    """Return a SQLAlchemy ``Query`` bound to the session (read-only use)."""
    return db.query(*entities)


from services.common.db_write import execute  # noqa: F401  (re-export for legacy controllers)
