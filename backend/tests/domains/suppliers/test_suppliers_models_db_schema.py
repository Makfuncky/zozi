"""Database-tier regression guard for FILE 104 - findings TF-266 and TF-267.

The unit-tier guard (``test_suppliers_models_laws.py``) proved the ORM half of
both findings. This file proves the *schema* half, which is where the actual
defect was:

  - TF-266 (Law 23): ``suppliers.supplier_disputes`` had no ``updated_at``
    column even though ``SupplierDispute.updated_at`` is emitted in every
    ORM SELECT of the table.
  - TF-267 (Law 54): ``suppliers.supplier_disputes`` had no ``is_deleted``
    column even though ``SupplierDispute.is_deleted`` is emitted in every ORM
    SELECT of the table.

Fixed by ``alembic/versions/2026_10_03_0001_suppliers_supplier_disputes_audit_columns.py``.

Read-only: ``information_schema`` and ``pg_indexes`` only, no writes.

Connection resolution, in order: ``TEST_DATABASE_URL`` -> ``DATABASE_URL_DIRECT``
-> ``DATABASE_URL`` -> the repo-root ``.env``. A SQLite URL, a missing URL, or
an unreachable host causes an explicit ``pytest.skip`` with a reason - never a
silent pass - so "skipped" is distinguishable from "verified".
"""
from __future__ import annotations

import os
from pathlib import Path

import pytest
import sqlalchemy as sa

REPO_ROOT = Path(__file__).resolve().parents[4]
SCHEMA = "suppliers"
TABLE = "supplier_disputes"

TABLES_WITH_AUDIT_DEFAULTS = (
    "supplier_profiles",
    "supplier_documents",
    "supplier_notification_preferences",
    "supplier_badge_catalogs",
    "supplier_badges",
    "supplier_badge_billing_histories",
    "supplier_disputes",
)


def _resolve_sync_url() -> str:
    url = (
        os.getenv("TEST_DATABASE_URL")
        or os.getenv("DATABASE_URL_DIRECT")
        or os.getenv("DATABASE_URL")
    )
    if not url:
        env_file = REPO_ROOT / ".env"
        if env_file.exists():
            for raw in env_file.read_text(encoding="utf-8", errors="ignore").splitlines():
                line = raw.strip()
                if line.startswith("DATABASE_URL_DIRECT="):
                    url = line.split("=", 1)[1].strip()
                    break
                if line.startswith("DATABASE_URL=") and url is None:
                    url = line.split("=", 1)[1].strip()
    if not url:
        pytest.skip("no PostgreSQL URL available (TEST_DATABASE_URL / DATABASE_URL_DIRECT / DATABASE_URL / .env)")
    if url.startswith("postgresql+asyncpg://"):
        url = "postgresql://" + url.split("://", 1)[1]
    if not url.startswith("postgresql://"):
        pytest.skip(
            "database-tier guard needs PostgreSQL; SQLite dev databases are bootstrapped "
            "from ORM metadata and already carry the audited columns"
        )
    return url


@pytest.fixture(scope="module")
def pg():
    url = _resolve_sync_url()
    try:
        engine = sa.create_engine(url, connect_args={"connect_timeout": 8})
        with engine.connect() as conn:
            conn.execute(sa.text("select 1"))
    except Exception as exc:  # unreachable -> explicit skip, never a pass
        pytest.skip(f"database unreachable: {type(exc).__name__}: {exc}")
    yield engine
    engine.dispose()


@pytest.fixture(scope="module")
def db_columns(pg) -> dict[str, dict]:
    with pg.connect() as conn:
        rows = conn.execute(
            sa.text(
                "select column_name, data_type, is_nullable, column_default "
                "from information_schema.columns "
                "where table_schema = :s and table_name = :t "
                "order by ordinal_position"
            ),
            {"s": SCHEMA, "t": TABLE},
        ).fetchall()
    return {
        r[0]: {"data_type": r[1], "is_nullable": r[2], "column_default": r[3]}
        for r in rows
    }


class TestSupplierDisputesSchemaMatchesOrm:
    def test_table_exists(self, db_columns) -> None:
        assert db_columns, f"{SCHEMA}.{TABLE} not present in information_schema"

    def test_tf_266_updated_at_column_present(self, db_columns) -> None:
        """TF-266 - Law 23: updated_at must exist in the applied schema."""
        assert "updated_at" in db_columns, (
            f"TF-266: {SCHEMA}.{TABLE} has no updated_at column (Law 23); the ORM emits "
            f"it on every read. Migration 20261003_0001 adds it."
        )

    def test_tf_266_updated_at_has_now_default(self, db_columns) -> None:
        """TF-266 - Law 21: the applied default must be DB-side."""
        default = (db_columns["updated_at"]["column_default"] or "").lower()
        assert "now" in default or "current_timestamp" in default, (
            f"TF-266: {SCHEMA}.{TABLE}.updated_at has no now() default (Law 21); "
            f"got {db_columns['updated_at']['column_default']!r}"
        )

    def test_tf_267_is_deleted_column_present(self, db_columns) -> None:
        """TF-267 - Law 54: is_deleted must exist in the applied schema."""
        assert "is_deleted" in db_columns, (
            f"TF-267: {SCHEMA}.{TABLE} has no is_deleted column (Law 54); the ORM emits "
            f"it on every read. Migration 20261003_0001 adds it."
        )

    def test_tf_267_is_deleted_is_boolean_not_null_default_false(self, db_columns) -> None:
        """TF-267 - Law 54: boolean, NOT NULL, default false."""
        col = db_columns["is_deleted"]
        assert col["data_type"] == "boolean", f"TF-267: is_deleted is {col['data_type']!r}"
        assert col["is_nullable"] == "NO", "TF-267: is_deleted must be NOT NULL"
        assert (col["column_default"] or "").lower() in {"false", "false::boolean"}, (
            f"TF-267: is_deleted default is {col['column_default']!r}, expected false"
        )

    def test_tf_267_is_deleted_is_indexed(self, pg) -> None:
        """The ORM declares index=True; the applied schema must agree."""
        with pg.connect() as conn:
            n = conn.execute(
                sa.text(
                    "select count(*) from pg_indexes "
                    "where schemaname = :s and tablename = :t "
                    "and indexdef ilike '%is_deleted%'"
                ),
                {"s": SCHEMA, "t": TABLE},
            ).scalar()
        assert n and n > 0, f"TF-267: no index on {SCHEMA}.{TABLE}.is_deleted"


class TestSupplierTablesServerDefaultsMatchOrm:
    """Law 6 - Alembic is the source of truth, so the DB default and the ORM
    ``server_default`` must agree on every audited timestamp."""

    def test_created_at_and_updated_at_have_now_defaults(self, pg) -> None:
        with pg.connect() as conn:
            rows = conn.execute(
                sa.text(
                    "select table_name, column_name, column_default "
                    "from information_schema.columns "
                    "where table_schema = :s and column_name in ('created_at','updated_at')"
                ),
                {"s": SCHEMA},
            ).fetchall()
        seen = {(r[0], r[1]): r[2] for r in rows}
        offenders = [
            f"{SCHEMA}.{t}.{c}={seen.get((t, c))!r}"
            for t in TABLES_WITH_AUDIT_DEFAULTS
            for c in ("created_at", "updated_at")
            if not ("now" in (seen.get((t, c)) or "").lower()
                    or "current_timestamp" in (seen.get((t, c)) or "").lower())
        ]
        assert not offenders, f"Law 21: DB defaults missing now() on {offenders}"
