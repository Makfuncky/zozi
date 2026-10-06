"""Tests for the governance command-center query service (SEC-004).

The service used to accept a raw WHERE *fragment* and concatenate it into
``"SELECT COUNT(*) FROM " + table + " WHERE " + where``. The character allowlist
plus ``_BLOCKED_KEYWORDS`` denylist guarding that fragment omitted ``or`` and
``pg_sleep``, so ``1=1 or pg_sleep(5)=1`` passed every check. These tests pin the
Law 34 fix: fragments are refused outright and values travel as bound parameters.

The governance twin has 19 live ``safe_count`` call sites inside
``get_comprehensive_dashboard``; ``test_existing_call_sites_still_work``
reproduces every one of them so a future signature change cannot silently break
the admin dashboard's counters.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import Column, MetaData, Table
from sqlalchemy.types import NullType

from domains.governance.services.command_center.command_center_service import (
    ALLOWED_TABLES,
    Predicate,
    _validate_table_name,
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
        self.calls.append((" ".join(str(statement).split()), dict(params or {})))
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


@pytest.mark.parametrize(
    "payload",
    [
        "1=1 or benchmark(10000000,sha1(1))",
        "id=1 or benchmark(10000000,sha1(1))",
        "1=1 UNION SELECT version()",
        "country_code = 'OM' HAVING 1=1",
        "1=1; DROP TABLE orders",
        "created_at >= now() LIMIT 1 OFFSET 0",
        "version() = 1",
    ],
)
def test_rejects_additional_attack_shapes(payload):
    """Every shape the old denylist let through is refused at the boundary."""
    db = RecordingSession()
    with pytest.raises(ValueError):
        safe_count(db, "orders", payload)
    assert db.calls == []


# --- positive path ------------------------------------------------------------

def test_parameterised_predicate_accepted():
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

    assert "SELECT count(*)" in sql
    assert "FROM orders" in sql
    # Values must be bound, never interpolated.
    assert ":wq_0" in sql and ":wq_1" in sql
    assert "'pending'" not in sql
    assert "'US'" not in sql
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
    assert len(ALLOWED_TABLES) == 20
    for table in sorted(ALLOWED_TABLES):
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


def test_no_predicate_counts_every_row():
    """`where=None` replaces the old `where="1=1"` default."""
    db = RecordingSession()
    safe_count(db, "orders")
    sql, params = _only_call(db)
    assert "SELECT count(*)" in sql and "FROM orders" in sql
    assert params == {}


def test_accepts_core_boolean_expression():
    """A SQLAlchemy Core expression is also a supported `where`."""
    users = Table("users", MetaData(), Column("is_active", NullType))
    db = RecordingSession()
    safe_count(db, "users", users.c.is_active.is_(True))

    sql, _ = _only_call(db)
    assert "is_active IS true" in sql


# --- identifiers are validated, not pattern-matched against a denylist --------

@pytest.mark.parametrize(
    "predicate",
    [
        Predicate("status = 1 or pg_sleep(5)=1", "eq", "x"),
        Predicate("status); drop table orders --", "eq", "x"),
        Predicate("", "eq", "x"),
        Predicate("orders.status", "eq", "x"),
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
        Predicate("status", "or", "x"),
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
    assert "IN (:wq_0_0, :wq_0_1)" in sql
    assert "customer" not in sql
    assert params == {"wq_0_0": "customer", "wq_0_1": "supplier"}


def test_between_values_are_bound():
    db = RecordingSession()
    safe_count(db, "orders", [Predicate("total_amount", "between", (10, 500))])

    sql, params = _only_call(db)
    assert "BETWEEN :wq_0_lo AND :wq_0_hi" in sql
    assert params == {"wq_0_lo": 10, "wq_0_hi": 500}


def test_bare_predicate_is_accepted_as_a_single_term():
    db = RecordingSession()
    safe_count(db, "users", Predicate("role", "eq", "customer"))
    sql, params = _only_call(db)
    assert "role = :wq_0" in sql
    assert params == {"wq_0": "customer"}


# --- contract 4: all 19 existing call sites still work ----------------------
#
# Each tuple below mirrors one `safe_count(...)` call inside
# get_comprehensive_dashboard. Table names, column names, operators and value
# types are copied from the migrated source so this test fails if a migration
# is reverted, mis-typed, or silently dropped.

_NOW = datetime(2026, 10, 2, 12, 0, tzinfo=timezone.utc)
_TODAY = _NOW.replace(hour=0, minute=0, second=0, microsecond=0)
_CC = "OM"
_ONE_HOUR_AGO = _NOW - timedelta(hours=1)

EXISTING_CALL_SITES = [
    # (label, table, predicates)
    ("today_orders", "orders", [
        Predicate("created_at", "ge", _TODAY),
        Predicate("country_code", "eq", _CC),
    ]),
    ("failed_deliveries", "orders", [
        Predicate("status", "eq", "failed"),
        Predicate("created_at", "ge", _TODAY),
        Predicate("country_code", "eq", _CC),
    ]),
    ("employees_working", "employees", [
        Predicate("employment_status", "eq", "active"),
        Predicate("country_code", "eq", _CC),
    ]),
    ("system_issues", "system_health_events", [
        Predicate("severity", "in", ["error", "critical"]),
        Predicate("created_at", "ge", _ONE_HOUR_AGO),
    ]),
    ("active_disputes", "system_alerts", [
        Predicate("alert_type", "eq", "dispute"),
        Predicate("is_acknowledged", "eq", 0),
        Predicate("country_code", "eq", _CC),
    ]),
    ("return_requests", "return_requests", [
        Predicate("status", "eq", "pending"),
        Predicate("country_code", "eq", _CC),
    ]),
    ("users.customers", "users", [
        Predicate("role", "eq", "customer"),
        Predicate("is_active", "eq", True),
        Predicate("country_code", "eq", _CC),
    ]),
    ("users.suppliers", "users", [
        Predicate("role", "eq", "supplier"),
        Predicate("is_active", "eq", True),
        Predicate("country_code", "eq", _CC),
    ]),
    ("users.logistics_companies", "logistics_partners", [
        Predicate("type", "eq", "company"),
        Predicate("status", "eq", "active"),
    ]),
    ("users.logistics_individuals", "logistics_partners", [
        Predicate("type", "eq", "individual"),
        Predicate("status", "eq", "active"),
    ]),
    ("active_suppliers", "users", [
        Predicate("role", "eq", "supplier"),
        Predicate("is_active", "eq", True),
        Predicate("country_code", "eq", _CC),
    ]),
    ("supplier_issues", "supplier_profiles", [
        Predicate("verification_status", "eq", "rejected"),
    ]),
    ("total_products", "products", [
        Predicate("is_active", "eq", True),
        Predicate("country_code", "eq", _CC),
    ]),
    ("stuck_orders", "orders", [
        Predicate("status", "eq", "processing"),
        Predicate("updated_at", "lt", _ONE_HOUR_AGO),
        Predicate("country_code", "eq", _CC),
    ]),
    ("pending_kyc", "supplier_kyc_requirements", [
        Predicate("status", "eq", "pending"),
    ]),
    ("product_moderation", "products", [
        Predicate("is_active", "eq", False),
        Predicate("country_code", "eq", _CC),
    ]),
    ("open_tickets", "support_tickets", [
        Predicate("status", "eq", "open"),
    ]),
    ("active_logistics", "logistics_partners", [
        Predicate("status", "eq", "active"),
    ]),
    ("logistics_issues_count", "logistics_partners", [
        Predicate("status", "eq", "active"),
        Predicate("verification_status", "eq", "rejected"),
    ]),
]


def test_existing_call_sites_still_work():
    """All 19 migrated call sites render bound SQL and return a count."""
    assert len(EXISTING_CALL_SITES) == 19

    for label, table, predicates in EXISTING_CALL_SITES:
        # No call site may reach for a table outside the allowlist.
        assert _validate_table_name(table) == table, f"{label}: {table} not allowlisted"

        db = RecordingSession()
        result = safe_count(db, table, predicates)
        sql, params = _only_call(db)

        assert result == 7, f"{label}: safe_count must return the scalar count"
        assert "SELECT count(*)" in sql, f"{label}: not a COUNT(*)"
        assert f"FROM {table}" in sql, f"{label}: wrong table"
        # Every caller value must be bound, never interpolated into the SQL.
        assert f"'{_CC}'" not in sql, f"{label}: country_code was interpolated"
        for predicate in predicates:
            if isinstance(predicate.value, str) and predicate.value:
                assert f"'{predicate.value}'" not in sql, (
                    f"{label}: value {predicate.value!r} was interpolated"
                )
        assert len(params) == sum(
            2 if isinstance(p.value, (list, tuple)) and len(p.value) else 1
            for p in predicates
        ), f"{label}: unexpected bound parameter count"


# --- frozen behaviour of the sanctioned primitive (contract 3) ----------------

def test_safe_fetch_keeps_text_execution_path():
    db = RecordingSession()
    safe_fetch(db, "SELECT COUNT(*) FROM users WHERE id = :id", {"id": 5}, scalar=True)
    sql, params = _only_call(db)
    assert sql == "SELECT COUNT(*) FROM users WHERE id = :id"
    assert params == {"id": 5}


def test_safe_fetch_degrades_to_zero_on_db_error():
    """Governance's safe_fetch swallows DB errors so the dashboard still renders.

    That graceful degradation is contract 3, and it is also why the eight
    call sites naming a non-existent column keep reading 0 instead of failing
    loudly. See 04b_new_findings.txt NF-2/NF-3/NF-4.
    """
    db = RecordingSession(exc=RuntimeError("relation does not exist"))
    assert safe_fetch(db, "SELECT 1", scalar=True) == 0
    assert safe_fetch(db, "SELECT 1") == []
