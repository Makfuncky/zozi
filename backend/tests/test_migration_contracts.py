"""Migration contract tests — Phase 1 CI gate.

Each test asserts the Alembic migration chain satisfies the contract required
for safe, reproducible deployments:

* Single, linear head (no divergent branches).
* Every revision that is *not* the baseline declares its ``down_revision`` so
  the chain is contiguous.
* Every revision defines an importable ``upgrade`` and ``downgrade``.
* The root baseline migration materialises the canonical ORM schema and is
  idempotent on a missing-table (fresh) database.
* A fresh database initialised via ``alembic upgrade head`` alone exposes
  every table the ORM defines (zero missing).
"""
from __future__ import annotations

import os
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config

BACKEND_ROOT = Path(__file__).resolve().parent.parent
VERSIONS_DIR = BACKEND_ROOT / "alembic" / "versions"


def _alembic_config(db_path: str) -> Config:
    cfg = Config(str(BACKEND_ROOT / "alembic.ini"))
    cfg.set_main_option("script_location", str(BACKEND_ROOT / "alembic"))
    cfg.set_main_option("sqlalchemy.url", f"sqlite:///{db_path}")
    return cfg


@pytest.fixture
def alembic_cfg(tmp_path):
    db_path = str(tmp_path / "contract.db")
    previous_url = os.environ.pop("DATABASE_URL", None)
    os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"
    cfg = _alembic_config(db_path)
    try:
        yield cfg
    finally:
        if previous_url is not None:
            os.environ["DATABASE_URL"] = previous_url
        else:
            os.environ.pop("DATABASE_URL", None)


def _revision_files() -> list[Path]:
    return sorted(p for p in VERSIONS_DIR.glob("*.py") if not p.name.startswith("_"))


_MIG_CACHE: dict[str, object] | None = None


def _revision_modules() -> dict[str, object]:
    global _MIG_CACHE
    if _MIG_CACHE is not None:
        return _MIG_CACHE
    _MIG_CACHE = {}
    for path in _revision_files():
        import importlib.util

        module_name = f"_migration_contract_{path.stem}"
        spec = importlib.util.spec_from_file_location(module_name, str(path))
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(module)
        _MIG_CACHE[module_name] = module
    return _MIG_CACHE


BASELINE_REV = "b81bfc888610"


def test_single_linear_migration_head(alembic_cfg):
    from alembic.script import ScriptDirectory

    heads = ScriptDirectory.from_config(alembic_cfg).get_heads()
    assert len(heads) == 1, f"Expected exactly 1 migration head, found {len(heads)}: {heads}"


def test_each_migration_has_upgrade_and_downgrade():
    modules = _revision_modules()
    assert modules, "No migration revision files discovered"
    missing: list[str] = []
    for name, module in modules.items():
        if not callable(getattr(module, "upgrade", None)):
            missing.append(f"{name}.upgrade")
        if not callable(getattr(module, "downgrade", None)):
            missing.append(f"{name}.downgrade")
    assert not missing, f"Migrations missing upgrade/downgrade: {missing}"


def test_chain_contiguity():
    modules = _revision_modules()
    revisions: dict[str, str | None] = {}
    for module in modules.values():
        rev = getattr(module, "revision", None)
        down = getattr(module, "down_revision", None)
        if rev is None:
            continue
        revisions[rev] = down

    baselines = [rev for rev, down in revisions.items() if down is None]
    assert len(baselines) == 1, f"Expected single baseline (down_revision=None), got {baselines}"

    referenced = {down for down in revisions.values() if down}
    dangling = referenced - set(revisions)
    assert not dangling, f"down_revision references unknown revision(s): {sorted(dangling)}"


def test_baseline_upgrade_is_idempotent_on_missing_tables(alembic_cfg):
    """The root baseline migration must not crash on a fresh/empty database
    where the tables it patches (internal_messages, org_units, sales_order_lines)
    do not yet exist. Guards make these no-ops instead of hard failures."""
    from sqlalchemy import inspect

    command.upgrade(alembic_cfg, BASELINE_REV)
    command.downgrade(alembic_cfg, "base")

    db_url = alembic_cfg.get_main_option("sqlalchemy.url")
    from sqlalchemy import create_engine

    engine = create_engine(db_url)
    tables = set(inspect(engine).get_table_names()) - {"alembic_version"}
    engine.dispose()
    assert tables == set(), f"Tables remained after baseline downgrade: {sorted(tables)}"


def test_fresh_db_upgrade_head_creates_all_orm_tables(alembic_cfg):
    """Full fresh-DB contract: the migration chain initialises every table the
    ORM defines (0 missing). Migration-only (gap) tables are expected and
    excluded from this assertion."""
    from db.base import Base
    import models  # noqa: F401
    from sqlalchemy import create_engine, inspect

    command.upgrade(alembic_cfg, "head")
    db_url = alembic_cfg.get_main_option("sqlalchemy.url")
    from utils.schema_compat import SCHEMA_TRANSLATE_MAP

    engine = create_engine(
        db_url,
        connect_args={"check_same_thread": False},
        execution_options={"schema_translate_map": SCHEMA_TRANSLATE_MAP},
    )
    inspector = inspect(engine)
    db_tables = {t.split(".")[-1] for t in inspector.get_table_names()}
    orm_tables = {t.split(".")[-1] for t in Base.metadata.tables}
    missing = orm_tables - db_tables
    engine.dispose()
    assert not missing, f"ORM tables missing from DB after upgrade head: {sorted(missing)}"
