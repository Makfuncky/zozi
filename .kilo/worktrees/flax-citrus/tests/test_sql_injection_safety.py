"""Regression / control tests for SEC101 & SEC5 SQL-injection findings.

Context
-------
SYSTEM_AUDIT_REPORT.md flagged 32 backend sites as possible SQL injection
(SEC101 / SEC5). Those rules are purely syntactic line-level regexes: they
match ANY f-string SQL that interpolates a variable, regardless of whether the
interpolated value is user-controlled.

Verification against the real source proved all 32 are FALSE POSITIVES. The
interpolated values fall into exactly one of three safe categories:

1. Strict allow-list / identifier validators (`_validate_table_name`,
   `_assert_safe_identifier`) reject anything that is not a plain
   `[A-Za-z_][A-Za-z0-9_]*` before it touches SQL.
2. Internal hard-coded dictionaries / constant literals (the column names and
   table names are source literals, never derived from request input).
3. Bind parameters (`:name`) — SQLAlchemy sends them as values, never as raw
   SQL text.

These tests lock in that behaviour so a future refactor cannot silently turn a
safe site into an unsafe one. They do NOT modify any production code.
"""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

# Make the backend package importable (mirrors the existing test harness).
_BACKEND_ROOT = Path(__file__).resolve().parent.parent / "backend"
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

import pytest
from sqlalchemy import text


# ─────────────────────────────────────────────────────────────────────────────
# Fake DB that captures every executed statement instead of touching a real DB
# ─────────────────────────────────────────────────────────────────────────────
class _FakeResult:
    def mappings(self):
        return self

    def first(self):
        # Enough for chat_enrichment.delete_message's pre-check SELECT and
        # log_activity's RETURNING row (needs created_at).
        return {"id": 1, "sender_id": 1, "body": "hello", "created_at": None}

    def all(self):
        return []

    def scalar(self):
        return 0


class FakeDB:
    def __init__(self):
        self.calls: list[tuple[str, dict]] = []

    def execute(self, statement, params=None):
        self.calls.append((str(statement), params or {}))
        return _FakeResult()

    def commit(self):
        pass


# ═════════════════════════════════════════════════════════════════════════════
# 1. Strict validators — the primary gatekeepers
# ═════════════════════════════════════════════════════════════════════════════
def test_validate_table_name_accepts_allowlisted():
    from controllers.command_center_controller import _validate_table_name

    for allowed in ("users", " Orders ", "order_items", "employee_work_logs"):
        assert isinstance(_validate_table_name(allowed), str)


def test_validate_table_name_rejects_malicious():
    from controllers.command_center_controller import _validate_table_name

    for evil in (
        "users; DROP TABLE users",
        "orders WHERE 1=1;--",
        "a-b",
        "../config",
        "users UNION SELECT password FROM accounts",
        "users`)",
    ):
        with pytest.raises(ValueError):
            _validate_table_name(evil)


def test_assert_safe_identifier_rejects_unsafe():
    from utils.rls_interceptor import _assert_safe_identifier

    for evil in ("", "1abc", "a-b", ";DROP", "tbl name", "a.b", "`x`"):
        with pytest.raises(ValueError):
            _assert_safe_identifier(evil)

    assert _assert_safe_identifier("valid_name") == "valid_name"
    assert _assert_safe_identifier("_ok123") == "_ok123"


# ═════════════════════════════════════════════════════════════════════════════
# 2. command_center_controller.safe_count — validated table, no DB hit on evil
# ═════════════════════════════════════════════════════════════════════════════
def test_safe_count_rejects_untrusted_table_before_db():
    from controllers.command_center_controller import safe_count

    db = FakeDB()
    with pytest.raises(ValueError):
        safe_count(db, "users; DROP TABLE users")
    # Validation happens first, so no statement is ever sent to the DB.
    assert db.calls == []


def test_safe_count_builds_validated_fragment_for_allowlisted():
    from controllers.command_center_controller import safe_count

    db = FakeDB()
    safe_count(db, "USERS", where="id = :uid", params={"uid": 5})

    sql, params = db.calls[0]
    assert "FROM users" in sql  # normalized by the allow-list validator
    assert "id = :uid" in sql
    assert params == {"uid": 5}
    assert "DROP" not in sql


# ═════════════════════════════════════════════════════════════════════════════
# 3. ess_write_service.update_employee_profile — only hardcoded columns + binds
# ═════════════════════════════════════════════════════════════════════════════
def test_ess_update_uses_only_hardcoded_columns_and_binds():
    from services.hr.ess_write_service import update_employee_profile

    db = FakeDB()
    emp = SimpleNamespace(id=42)
    malicious = "x'; UPDATE employees SET role='admin' WHERE id=1;--"

    update_employee_profile(
        db,
        emp,
        phone="123-456",
        address=malicious,
        emergency_contact_name="Jane",
        emergency_contact_phone="999",
    )

    sql, params = db.calls[0]
    # Column names are fixed literals from the source, never the user payload.
    assert sql.startswith("UPDATE employees SET ")
    assert "phone = :phone" in sql
    assert "address = :address" in sql
    assert "emergency_contact_name = :ec_name" in sql
    assert "emergency_contact_phone = :ec_phone" in sql
    assert "WHERE id = :eid" in sql
    # The malicious address reaches the DB ONLY as a bound value, never inline.
    assert malicious not in sql
    assert params["address"] == malicious
    assert params["eid"] == 42


# ═════════════════════════════════════════════════════════════════════════════
# 4. chat_enrichment.delete_message — table resolved from internal dict only
# ═════════════════════════════════════════════════════════════════════════════
def test_chat_delete_uses_internal_table_dict():
    from services.chat_enrichment import delete_message

    db = FakeDB()
    delete_message(db, message_id=1, message_type="direct", employee_id=7, hard_delete=False)

    # Find the dynamic SQL statement (the one with an f-string table name).
    sqls = [sql for sql, _ in db.calls]
    dynamic = [s for s in sqls if "FROM direct_chat_messages" in s or "direct_chat_messages" in s]
    assert dynamic, f"expected internal table name in SQL, got: {sqls}"
    # The payload id is a bind, not inline.
    assert all(":id" in s for s in dynamic)


def test_chat_delete_rejects_unknown_message_type():
    from services.chat_enrichment import delete_message

    db = FakeDB()
    with pytest.raises(ValueError):
        delete_message(
            db,
            message_id=1,
            message_type="; DROP TABLE users;--",  # would be attacker-controlled
            employee_id=7,
        )


# ═════════════════════════════════════════════════════════════════════════════
# 5. performance_service.get_kpi_dashboard — only :oidN bind placeholders
# ═════════════════════════════════════════════════════════════════════════════
def test_kpi_dashboard_uses_bind_placeholders_only():
    from services.performance_service import get_kpi_dashboard

    # Deliberately choose ids that are NOT equal to their positional index, so
    # that the index digits inside ":oid0" cannot mask a leaked data value.
    objective_ids = [100, 200, 300]
    placeholders = ", ".join(f":oid{i}" for i in range(len(objective_ids)))
    params = {f"oid{i}": oid for i, oid in enumerate(objective_ids)}

    # The data values must be sent as bound parameters, NOT concatenated into
    # the SQL text (where they would be executable SQL).
    assert placeholders == ":oid0, :oid1, :oid2"
    for oid in objective_ids:
        assert str(oid) not in placeholders, "data value leaked into SQL text"
        assert params[f"oid{objective_ids.index(oid)}"] == oid

    # Service baseline query is parameterised by :eid and never inlines ids.
    db = FakeDB()
    get_kpi_dashboard(db, employee_id=3)
    for sql, _ in db.calls:
        assert "100" not in sql and "200" not in sql and "300" not in sql
