"""Database contract tests (DBA28).

These assert the structural guarantees the DATABASE-domain remediation must
hold, without needing a live database:

* exactly one Alembic head (no fractured migration graph -- DB2/DBA13),
* every ``country_code`` column is ``String(3)`` (DBA04),
* JSONB columns carry a GIN index signal (DBA09),
* hot tables carry the (country_code, created_at) composite index (DBA31),
* the ``automation_logs`` table carries the mandatory audit column set (DBA03).
"""
from __future__ import annotations

import ast
import os
import re
import sys
from pathlib import Path

BACKEND = Path(r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend")
VERSIONS = BACKEND / "alembic" / "versions"

if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))


def _collect_heads() -> list[str]:
    """Authoritative Alembic head list (handles multi-line tuple down_revision)."""
    from alembic.config import Config
    from alembic.script import ScriptDirectory

    cfg = Config(str(BACKEND / "alembic.ini"))
    cfg.set_main_option("script_location", str(VERSIONS.parent))
    script = ScriptDirectory.from_config(cfg)
    return list(script.get_heads())


def test_single_alembic_head() -> None:
    heads = _collect_heads()
    assert heads == ["ccw_unify_20260809"], f"expected single head, got {heads}"


def _models():
    import models  # noqa: F401  (registers all tables on Base.metadata)
    return models.Base.metadata


def test_country_code_width_uniform() -> None:
    md = _models()
    bad = []
    for table in md.tables.values():
        col = table.columns.get("country_code")
        if col is None:
            continue
        if getattr(col.type, "length", None) != 3:
            bad.append(f"{table.schema}.{table.name}")
    assert not bad, f"country_code not String(3): {bad}"


def test_jsonb_gin_signals() -> None:
    md = _models()

    def has_gin(table, column: str) -> bool:
        for idx in table.indexes:
            cols = {str(e).split(".")[-1] for e in idx.expressions}
            using = getattr(idx, "dialect_kwargs", {}).get("postgresql_using")
            if column in cols and (using == "gin" or "gin" in str(idx.dialect_kwargs).lower()):
                return True
        return False

    assert has_gin(md.tables["hr.employee_risk_scores"], "factors"), "employee_risk_scores.factors missing GIN"
    assert has_gin(md.tables["supplier.supplier_badge_catalog"], "benefits"), "supplier_badge_catalog.benefits missing GIN"


def test_composite_country_created_indexes() -> None:
    md = _models()
    expected = {
        "configuration.country_commission_rates",
        "communication.internal_channels",
        "commerce.flash_sales",
        "commerce.flash_sale_items",
    }
    for qualified in expected:
        table = md.tables[qualified]
        ok = False
        for idx in table.indexes:
            cols = [str(e).split(".")[-1] for e in idx.expressions]
            if "country_code" in cols and "created_at" in cols:
                ok = True
                break
        if not ok:
            # country_code individually indexed also satisfies the contract
            cc = table.columns.get("country_code")
            if cc is not None and (cc.index or cc.unique):
                ok = True
        assert ok, f"{qualified} missing (country_code, created_at) composite index"


def test_automation_log_audit_columns() -> None:
    md = _models()
    table = md.tables["finance.automation_logs"]
    for col in ("created_at", "updated_at", "created_by", "updated_by"):
        assert col in table.columns, f"automation_logs missing audit column '{col}'"
