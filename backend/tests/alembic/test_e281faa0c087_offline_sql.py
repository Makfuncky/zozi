"""Paired pytest tests for e281faa0c087 offline-SQL fix.

Before the fix, ``_index_exists`` called ``conn.execute()`` then
``result.scalar()``; in Alembic offline mode ``execute()`` returns ``None``
so ``scalar()`` raised ``AttributeError``.  The fix adds an offline-mode
detector (``_is_offline_connection``) and guards every introspection call
so that offline mode emits DDL unconditionally.
"""
from __future__ import annotations

import importlib.util
import os
import sys
import types
from unittest.mock import MagicMock

import pytest
import sqlalchemy as sa
from sqlalchemy.engine.mock import MockConnection


# ---------------------------------------------------------------------------
# Helpers to load the migration module with a mocked alembic.op
# ---------------------------------------------------------------------------

_MIGRATION_PATH = os.path.join(
    os.path.dirname(__file__),
    "..", "..", "..", "backend", "alembic", "versions",
    "2026_07_29_10_17-e281faa0c087_add_orm_models_for_orphaned_employee_.py",
)
_MIGRATION_PATH = os.path.normpath(_MIGRATION_PATH)


def _load_migration(mock_op: MagicMock):
    """Load the migration module, injecting *mock_op* as ``alembic.op``."""
    mock_alembic_pkg = types.ModuleType("alembic")
    mock_alembic_pkg.op = mock_op
    mock_alembic_pkg.__path__ = []
    mock_alembic_pkg.__package__ = "alembic"
    sys.modules["alembic"] = mock_alembic_pkg

    _spec = importlib.util.spec_from_file_location("migration_e281faa0c087", _MIGRATION_PATH)
    _mod = importlib.util.module_from_spec(_spec)
    _mod.__dict__["op"] = mock_op
    _spec.loader.exec_module(_mod)
    return _mod


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def mock_op():
    """A mocked ``alembic.op`` whose ``get_bind`` returns a MockConnection."""
    engine = sa.create_engine("postgresql://")
    mock_conn = MockConnection(engine.dialect, lambda *a, **kw: None)

    mock_op = MagicMock()
    mock_op.get_bind.return_value = mock_conn

    _batch_ctx = MagicMock()
    _batch_ctx.__enter__ = MagicMock(return_value=_batch_ctx)
    _batch_ctx.__exit__ = MagicMock(return_value=False)
    _batch_ctx.create_index = MagicMock()
    _batch_ctx.create_foreign_key = MagicMock()
    mock_op.batch_alter_table.return_value = _batch_ctx

    return mock_op


@pytest.fixture()
def migration(mock_op):
    """The loaded migration module."""
    return _load_migration(mock_op)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestOfflineDetector:
    def test_mock_connection_is_offline(self, migration):
        assert migration._is_offline_connection(
            MockConnection(sa.create_engine("postgresql://").dialect, lambda *a, **kw: None)
        ) is True

    def test_real_sqlite_connection_is_not_offline(self, migration):
        engine = sa.create_engine("sqlite://")
        with engine.connect() as conn:
            assert migration._is_offline_connection(conn) is False


class TestIndexIntrospection:
    def test_existing_index_detected(self, migration):
        engine = sa.create_engine("sqlite://")
        with engine.connect() as conn:
            conn.execute(sa.text("CREATE TABLE t (id INTEGER PRIMARY KEY, name TEXT)"))
            conn.execute(sa.text("CREATE INDEX ix_name ON t (name)"))
            conn.commit()
            assert migration._index_exists(conn, "t", "ix_name") is True

    def test_missing_index_returns_false(self, migration):
        engine = sa.create_engine("sqlite://")
        with engine.connect() as conn:
            conn.execute(sa.text("CREATE TABLE t (id INTEGER PRIMARY KEY, name TEXT)"))
            conn.commit()
            assert migration._index_exists(conn, "t", "ix_missing") is False


class TestFkIntrospection:
    def test_existing_fk_detected(self, migration):
        engine = sa.create_engine("sqlite://")
        with engine.connect() as conn:
            conn.execute(sa.text("CREATE TABLE users (id INTEGER PRIMARY KEY)"))
            conn.execute(sa.text("""
                CREATE TABLE employee_audit_timeline (
                    id INTEGER PRIMARY KEY, actor_id INTEGER,
                    FOREIGN KEY(actor_id) REFERENCES users(id)
                )
            """))
            conn.commit()
            assert migration._fk_exists(
                conn, "employee_audit_timeline", "actor_id", "users", "id"
            ) is True

    def test_missing_fk_returns_false(self, migration):
        engine = sa.create_engine("sqlite://")
        with engine.connect() as conn:
            conn.execute(sa.text("CREATE TABLE users (id INTEGER PRIMARY KEY)"))
            conn.execute(sa.text("""
                CREATE TABLE employee_audit_timeline (
                    id INTEGER PRIMARY KEY, actor_id INTEGER
                )
            """))
            conn.commit()
            assert migration._fk_exists(
                conn, "employee_audit_timeline", "actor_id", "users", "id"
            ) is False


class TestOfflineGuard:
    def test_upgrade_does_not_raise_in_offline_mode(self, migration):
        """Regression: before the fix upgrade() crashed with
        AttributeError: 'NoneType' object has no attribute 'scalar'."""
        migration.upgrade()  # must not raise

    def test_four_batch_alter_table_calls_in_offline_mode(self, migration, mock_op):
        migration.upgrade()
        assert mock_op.batch_alter_table.call_count == 4
