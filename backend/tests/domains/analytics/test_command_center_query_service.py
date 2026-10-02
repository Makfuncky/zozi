"""Tests for the analytics command-center query service (SEC-004).

The service used to accept a raw WHERE *fragment* and interpolate it into
``f"SELECT COUNT(*) FROM {table} WHERE {where}"``. The character allowlist plus
``_BLOCKED_KEYWORDS`` denylist guarding that fragment omitted ``or`` and
``pg_sleep``, so ``1=1 or pg_sleep(5)=1`` passed every check and reached the
database. These tests pin the Law 34 fix: fragments are refused outright and
values travel as bound parameters.
"""
from __future__ import annotations

import pytest
from sqlalchemy import Column
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.types import NullType

from domains.analytics.services.aggregation.command_center_query_service import (
    Predicate,
    _ALLOWED_TABLES,
    _validate_where_clause,
    safe_count,
    safe_fetch,
)


class _Result:
    def scalar(self):
        return 7

    def fetchall(self):
        return []


class RecordingSession:
    """Captures the statement/params safe_fetch would hand to the driver."""

    def __init__(self, exc: Exception | None = None):
        self.calls: list[tuple[str, dict]] = []
        self._exc = exc

    def execute(self, statement, params=None):
        self.calls.append((str(statement), dict(params or {})))
        if self._exc is not None:
            raise self._exc
        return _Result()


def _only_call(db: RecordingSession) -> tuple[str, dict]:
    assert len(db.calls) == 1, f"expected exactly one statement, got {db.calls}"
    return db.calls[0]


# --- the two required denial tests (contract 10 / 20) -------------------------

def test_rejects_time_based_injection():
    """`1=1 or pg_sleep(5)=1` passed every pre-fix check. It must be refused."""
    with pytest.raises(ValueError):
        _validate_where_clause("1=1 or pg_sleep(5)=1")

    db = RecordingSession()
    with pytest.raises(ValueError):
        safe_count(db, "orders", "1=1 or pg_sleep(5)=1")
    assert db.calls == [], "no SQL may be emitted for a refused fragment"


def test_rejects_boolean_injection():
    """A tautology fragment must be refused rather than counted through."""
    with pytest.raises(ValueError):
        _validate_where_clause("1=1 or 1=1")

    db = RecordingSession()
    with pytest.raises(ValueError):
        safe_count(db, "users", "id = 1 or 1=1")
    assert db.calls == [], "no SQL may be emitted for a refused fragment"


# --- positive path ------------------------------------------------------------

def test_accepts_parameterised_predicate():
    """Structured predicates render to named bind parameters, not inline values."""
    db = RecordingSession()
    result = safe_count(
        db,
        "orders",
        [
            Predicate("status", "eq", "pending"),
            Predicate("country_code", "eq", "US"),
        ],
    )

    assert result == 7
    sql, params = _only_call(db)
    normalised = " ".join(sql.split())

    assert "SELECT count(*)" in normalised
    assert "FROM orders" in normalised
    # Values must be bound, never interpolated.
    assert ":wq_0" in normalised and ":wq_1" in normalised
    assert "'pending'" not in normalised
    assert "'US'" not in normalised
    assert params == {"wq_0": "pending", "wq_1": "US"}


def test_unknown_table_still_rejected():
    """The 20-name table allowlist keeps rejecting anything else."""
    db = RecordingSession()
    with pytest.raises(ValueError):
        safe_count(db, "users; DROP TABLE users")
    with pytest.raises(ValueError):
        safe_count(db, "information_schema.tables")
    assert db.calls == []

    # ...and every allowlisted name still renders (CHAIN-005).
    assert len(_ALLOWED_TABLES) == 20
    for table in sorted(_ALLOWED_TABLES):
        db = RecordingSession()
        safe_count(db, table)
        sql, _ = _only_call(db)
        assert table in sql


def test_table_name_is_normalised_before_use():
    db = RecordingSession()
    safe_count(db, "  USERS  ")
    sql, _ = _only_call(db)
    assert "users" in sql.lower()
    assert "USERS" not in sql


# --- identifiers are validated, not pattern-matched against a denylist --------

@pytest.mark.parametrize(
    "predicate",
    [
        Predicate("status = 1 or pg_sleep(5)=1", "eq", "x"),
        Predicate("status); drop table orders --", "eq", "x"),
        Predicate("", "eq", "x"),
    ],
)
def test_rejects_malformed_column_identifier(predicate):
    db = RecordingSession()
    with pytest.raises(ValueError):
        safe_count(db, "users", [predicate])
    assert db.calls == []


@pytest.mark.parametrize(
    "predicate",
    [
        Predicate("status", "union", "x"),
        Predicate("status", "eq; drop table orders", "x"),
        Predicate("status", "", "x"),
    ],
)
def test_rejects_unknown_operator(predicate):
    db = RecordingSession()
    with pytest.raises(ValueError):
        safe_count(db, "users", [predicate])
    assert db.calls == []


def test_rejects_non_predicate_where():
    db = RecordingSession()
    with pytest.raises(ValueError):
        safe_count(db, "users", ["status = 1"])
    with pytest.raises(ValueError):
        safe_count(db, "users", object())
    assert db.calls == []


# --- multi-value operators stay bound ----------------------------------------

def test_in_list_values_are_bound():
    db = RecordingSession()
    safe_count(db, "users", [Predicate("role", "in", ["customer", "supplier"])])

    sql, params = _only_call(db)
    normalised = " ".join(sql.split())
    assert "IN (:wq_0_0, :wq_0_1)" in normalised
    assert "customer" not in normalised
    assert params == {"wq_0_0": "customer", "wq_0_1": "supplier"}


def test_between_values_are_bound():
    db = RecordingSession()
    safe_count(db, "orders", [Predicate("total_amount", "between", (10, 500))])

    sql, params = _only_call(db)
    normalised = " ".join(sql.split())
    assert "BETWEEN :wq_0_lo AND :wq_0_hi" in normalised
    assert params == {"wq_0_lo": 10, "wq_0_hi": 500}


def test_accepts_core_boolean_expression():
    """A SQLAlchemy Core expression is also a supported `where`."""
    from sqlalchemy import MetaData, Table

    users = Table("users", MetaData(), Column("is_active", NullType))
    db = RecordingSession()
    safe_count(db, "users", users.c.is_active.is_(True))

    sql, _ = _only_call(db)
    assert "is_active IS true" in " ".join(sql.split())


# --- frozen behaviour of the sanctioned primitive (contract 3) ----------------

def test_safe_fetch_keeps_text_execution_path():
    db = RecordingSession()
    safe_fetch(db, "SELECT COUNT(*) FROM users WHERE id = :id", {"id": 5}, scalar=True)
    sql, params = _only_call(db)
    assert sql == "SELECT COUNT(*) FROM users WHERE id = :id"
    assert params == {"id": 5}


def test_safe_fetch_logs_and_reraises_on_db_error():
    db = RecordingSession(exc=SQLAlchemyError("boom"))
    with pytest.raises(SQLAlchemyError):
        safe_fetch(db, "SELECT 1", scalar=True)