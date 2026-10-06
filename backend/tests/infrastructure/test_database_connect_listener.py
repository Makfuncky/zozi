"""Regression guards for the PostgreSQL ``connect`` search_path listener.

FILE 178 / DBBOOT-001, DBBOOT-002, DBBOOT-003.

DBBOOT-001: ``_apply_search_path`` handed a SQLAlchemy ``text()`` clause to a raw
DBAPI cursor. That raised ``TypeError: Boolean value of this clause is not
defined`` (sqlalchemy/sql/elements.py:762) on *every* connection checkout against
PostgreSQL, so staging/production could not open a connection at all.

DBBOOT-002: because the listener had never executed, the per-domain
``search_path`` had never actually been applied on PostgreSQL.

DBBOOT-003: nothing in the suite exercised the listener, so the failure was
invisible (the whole suite runs on SQLite, which skips the branch).

Law 34: ``text()`` is executed by an Engine/Connection and is never handed to a
raw DBAPI cursor. These tests assert that invariant both statically (AST) and
dynamically (a recording fake cursor), and they assert that every
environment-supplied ``DB_SEARCH_PATH`` element is validated as a plain
identifier before it can reach DDL.

The one test that needs a real server is marked ``postgres`` (declared in
``backend/pyproject.toml``) and reads its DSN from the environment.
"""
from __future__ import annotations

import ast
import inspect
import logging
import os
import re
from pathlib import Path

import pytest
from sqlalchemy import create_engine, event, text
from sqlalchemy.engine.interfaces import Dialect
from sqlalchemy.sql.elements import ClauseElement

from infrastructure.database import database as dbmod


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #
_DATABASE_PY = Path(inspect.getsourcefile(dbmod))  # type: ignore[arg-type]


class _RecordingCursor:
    """A raw DBAPI cursor stand-in that records exactly what reached it."""

    def __init__(self, sink: list) -> None:
        self._sink = sink
        self.closed = False

    def execute(self, statement, parameters=None):  # noqa: ANN001, ANN201
        # A real psycopg2 cursor would blow up here on a SQLAlchemy clause; the
        # original bug is reproduced if `bool(statement)` is evaluated.
        if isinstance(statement, ClauseElement):
            raise TypeError(
                "A SQLAlchemy clause was handed to a raw DBAPI cursor "
                "(Law 34 violation, DBBOOT-001)"
            )
        if not isinstance(statement, str):
            raise TypeError(f"raw cursor received {type(statement)!r}, expected str")
        bool(statement)  # the exact operation that raised TypeError pre-fix
        self._sink.append((statement, parameters))

    def close(self) -> None:
        self.closed = True


class _RecordingConnection:
    def __init__(self) -> None:
        self.executed: list[tuple] = []
        self.cursors: list[_RecordingCursor] = []

    def cursor(self) -> _RecordingCursor:
        cursor = _RecordingCursor(self.executed)
        self.cursors.append(cursor)
        return cursor


def _use_search_path(monkeypatch: pytest.MonkeyPatch, raw: str) -> list[str]:
    """Point the module globals at a validated search path and return the schemas."""
    schemas = dbmod.validate_search_path(raw)
    monkeypatch.setattr(dbmod, "search_path_schemas", schemas, raising=False)
    monkeypatch.setattr(
        dbmod,
        "search_path_value",
        ", ".join(dbmod._quote_ident(schema) for schema in schemas),
        raising=False,
    )
    return schemas


def _apply_to_recorder(monkeypatch: pytest.MonkeyPatch, raw: str) -> _RecordingConnection:
    schemas = _use_search_path(monkeypatch, raw)
    conn = _RecordingConnection()
    if schemas:
        dbmod._apply_search_path(conn, None)
    return conn


def _listener_ast() -> ast.FunctionDef:
    tree = ast.parse(_DATABASE_PY.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "_apply_search_path":
            return node
    raise AssertionError("_apply_search_path not found in database.py")


# --------------------------------------------------------------------------- #
# DBBOOT-001 - Law 34 on the connect path
# --------------------------------------------------------------------------- #
class TestConnectListenerLaw34:
    def test_connect_listener_is_law34_compliant(self) -> None:
        """No raw DBAPI cursor may receive a SQLAlchemy clause (Law 34).

        Statically: inside `_apply_search_path`, every `execute(...)` call must
        pass a plain statement plus a bind-parameter object, and the statement
        must not be built from `text(...)`.
        """
        func = _listener_ast()
        execute_calls: list[ast.Call] = []
        text_calls: list[ast.Call] = []

        for node in ast.walk(func):
            if not isinstance(node, ast.Call):
                continue
            func_name = node.func.attr if isinstance(node.func, ast.Attribute) else getattr(node.func, "id", "")
            if func_name == "execute":
                execute_calls.append(node)
            if func_name == "text":
                text_calls.append(node)

        assert execute_calls, (
            "_apply_search_path no longer executes anything - the search path would "
            "silently stop being applied (DBBOOT-002 regression)"
        )
        for call in execute_calls:
            assert call.args, "cursor.execute() called without a statement"
            first_arg = call.args[0]
            assert not isinstance(first_arg, ast.Call) or getattr(
                getattr(first_arg.func, "attr", None) or getattr(first_arg.func, "id", None), "", ""
            ) != "text", (
                "Law 34 violation: a SQLAlchemy text() clause is passed to a raw DBAPI "
                "cursor.execute() (DBBOOT-001)"
            )
            assert len(call.args) >= 2, (
                "Law 34 violation: cursor.execute() must receive bind parameters, not an "
                "interpolated statement"
            )

        assert not text_calls, (
            "Law 34 violation: _apply_search_path builds a SQLAlchemy text() clause. A "
            "connect event fires before a SQLAlchemy Connection exists, so text() can "
            "never be executed here (DBBOOT-001)."
        )

    def test_raw_cursor_receives_a_string_and_bind_parameters(self, monkeypatch) -> None:
        """Dynamic guard: the original TypeError cannot come back unnoticed."""
        conn = _apply_to_recorder(monkeypatch, "public,accounts,catalog")

        assert len(conn.executed) == 1, f"expected exactly one statement, got {conn.executed!r}"
        statement, parameters = conn.executed[0]
        assert isinstance(statement, str)
        assert parameters is not None, "the search path must travel as a bind parameter"
        # The env-supplied value must never be concatenated into the SQL text.
        for schema in ("public", "accounts", "catalog"):
            assert schema not in statement, (
                f"schema {schema!r} was interpolated into the SQL text instead of bound"
            )
        assert conn.cursors[0].closed is True, "the cursor must be closed"

    def test_listener_binds_through_the_driver_paramstyle(self) -> None:
        """The placeholder is translated to the driver's own paramstyle."""
        expected_markers = {
            "qmark": "?",
            "numeric": ":1",
            "numeric_dollar": "$1",
            "format": "%s",
            "pyformat": "%(search_path)s",
            "named": ":search_path",
        }
        for paramstyle, marker in expected_markers.items():
            statement, parameters = dbmod._bind_search_path(
                "SELECT set_config('search_path', ?, false)", '"public", "catalog"', paramstyle
            )
            assert marker in statement, f"{paramstyle}: placeholder not translated ({statement})"
            if paramstyle != "qmark":
                assert "?" not in statement, f"{paramstyle}: qmark placeholder left behind"
            if isinstance(parameters, dict):
                assert parameters["search_path"] == '"public", "catalog"'
            else:
                assert tuple(parameters) == ('"public", "catalog"',)

    def test_unknown_paramstyle_is_refused_not_interpolated(self) -> None:
        with pytest.raises(RuntimeError, match="paramstyle"):
            dbmod._bind_search_path(
                "SELECT set_config('search_path', ?, false)", "public", "banana"
            )

    def test_listener_is_registered_on_postgres_engine(self) -> None:
        """The listener must be attached whenever a search path is configured."""
        if not dbmod._IS_POSTGRES:
            assert dbmod.search_path is None
            return
        assert dbmod.search_path_schemas, "no schema validated out of DB_SEARCH_PATH"
        assert event.contains(dbmod.engine, "connect", dbmod._apply_search_path), (
            "_apply_search_path is not registered on the engine - search_path would "
            "never be applied (DBBOOT-002 regression)"
        )


# --------------------------------------------------------------------------- #
# Security - DB_SEARCH_PATH is env-supplied and must be validated (Law 34, Law 75)
# --------------------------------------------------------------------------- #
class TestSearchPathValidation:
    def test_db_search_path_elements_are_validated(self) -> None:
        valid = ["public", "accounts", "catalog", "_private", "Schema2", "a_1"]
        assert dbmod.validate_search_path(",".join(valid)) == valid

    @pytest.mark.parametrize(
        "hostile",
        [
            'public"',
            'public"; DROP TABLE users; --',
            "accounts; SELECT pg_sleep(10)",
            "public accounts",
            "1accounts",
            'pub"lic',
            "pub-lic",
            "public)",
            "public\nDROP TABLE users",
            "$user",
            "public;",
            'a"b"c',
            "%s",
            "public'",
        ],
    )
    def test_hostile_search_path_elements_are_rejected(self, hostile: str, caplog) -> None:
        with caplog.at_level(logging.WARNING, logger=dbmod.logger.name):
            schemas = dbmod.validate_search_path(hostile)
        assert schemas == [], f"hostile element survived validation: {hostile!r} -> {schemas!r}"
        assert any("DB_SEARCH_PATH" in rec.getMessage() for rec in caplog.records), (
            "Law 75 violation: a rejected DB_SEARCH_PATH element must be logged at WARNING"
        )
        assert any(rec.levelno >= logging.WARNING for rec in caplog.records)

    def test_hostile_elements_are_dropped_but_valid_ones_survive(self, caplog) -> None:
        raw = 'public,evil"; DROP TABLE users; --,catalog'
        with caplog.at_level(logging.WARNING, logger=dbmod.logger.name):
            schemas = dbmod.validate_search_path(raw)
        assert schemas == ["public", "catalog"]
        assert any(rec.levelno >= logging.WARNING for rec in caplog.records)

    def test_validated_value_is_quoted_and_never_raw_env_text(self, monkeypatch) -> None:
        raw = 'public,evil",catalog'
        _use_search_path(monkeypatch, raw)
        value = dbmod.search_path_value
        assert value == '"public", "catalog"'
        # No unbalanced quote can survive: every quote is doubled or paired.
        assert value.count('"') % 2 == 0
        assert "evil" not in value

    def test_empty_search_path_applies_nothing_and_says_so(self, monkeypatch, caplog) -> None:
        conn = _apply_to_recorder(monkeypatch, "")
        assert conn.executed == [], "an empty search path must not overwrite the server default"
        with caplog.at_level(logging.WARNING, logger=dbmod.logger.name):
            dbmod._apply_search_path(_RecordingConnection(), None)
        assert any(
            "no valid PostgreSQL schema identifiers" in rec.getMessage()
            for rec in caplog.records
        ), "Law 75 violation: a fully invalid DB_SEARCH_PATH must be logged at WARNING"

    def test_default_schema_list_is_preserved_verbatim(self) -> None:
        """Contract section 3: the default DB_SEARCH_PATH list and its order are frozen."""
        fragments = (
            '"public,accounts,analytics,audit,catalog,comms,country,customers,"',
            '"finance,governance,hr,logistics,media,orders,payments,promotions,"',
            '"security,suppliers"',
        )
        source = _DATABASE_PY.read_text(encoding="utf-8")
        for fragment in fragments:
            assert fragment in source, f"the default DB_SEARCH_PATH list was changed: {fragment}"
        expected = "".join(fragment.strip('"') for fragment in fragments)
        assert dbmod.validate_search_path(expected) == expected.split(",")


# --------------------------------------------------------------------------- #
# DBBOOT-003 - the listener must actually work against a real PostgreSQL server
# --------------------------------------------------------------------------- #
def _postgres_dsn() -> str | None:
    for name in ("TEST_POSTGRES_URL", "TEST_DATABASE_URL", "DATABASE_URL"):
        dsn = (os.environ.get(name) or "").strip()
        if dsn.startswith("postgres"):
            return dsn
    return None


@pytest.mark.postgres
def test_live_postgres_connection_applies_search_path(monkeypatch) -> None:
    """Open a real PostgreSQL connection and assert the search path is applied.

    Requires a reachable PostgreSQL server. Point `TEST_POSTGRES_URL` at one (CI
    uses the `postgres:18-alpine` service) to exercise this test.
    """
    dsn = _postgres_dsn()
    if dsn is None:
        pytest.skip(
            "no PostgreSQL DSN in TEST_POSTGRES_URL/TEST_DATABASE_URL/DATABASE_URL; "
            "run with a postgres server (marker: postgres) to exercise the live listener"
        )

    schemas = _use_search_path(monkeypatch, "public,accounts,catalog,orders")
    assert schemas == ["public", "accounts", "catalog", "orders"]

    engine = create_engine(dsn, poolclass=dbmod.QueuePool, pool_pre_ping=True)
    event.listen(engine, "connect", dbmod._apply_search_path)
    try:
        with engine.connect() as conn:
            applied = conn.execute(text("SHOW search_path")).scalar()
            resolved = conn.execute(text("SELECT current_schemas(false)")).scalar()
            unqualified = conn.execute(text("SELECT to_regclass('products')")).scalar()
        assert applied is not None
        for schema in schemas:
            assert schema in applied, f"{schema!r} missing from SHOW search_path: {applied!r}"
        assert "public" in (resolved or [])
        assert unqualified is not None, (
            "an unqualified table name must resolve through the configured search_path "
            "(DBBOOT-002 regression)"
        )
    finally:
        engine.dispose()