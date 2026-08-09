"""DBA06 regression guard: the ORM must contain ZERO cross-schema foreign
keys. Every cross-schema reference is modelled via an ORM relationship with an
explicit ``primaryjoin`` (FK-owning column annotated ``foreign()``), never a
database-level cross-schema FK constraint.

Run with: pytest tests/test_dba06_rescue.py
"""
from __future__ import annotations

import pytest

pytest.importorskip("main")  # ensure the app package is importable

import main  # noqa: F401  (registers all models)
from db.base import Base


def _cross_schema_fks():
    bad = []
    for t in Base.metadata.tables.values():
        for fkc in t.foreign_key_constraints:
            for fk in fkc.elements:
                tgt = fk.column.table
                if (t.schema or None) != (tgt.schema or None):
                    bad.append(
                        (t.schema or "public", t.name,
                         tgt.schema or "public", tgt.name,
                         fk.parent.name, fk.column.name)
                    )
    return bad


def test_no_cross_schema_foreign_keys():
    bad = _cross_schema_fks()
    assert bad == [], (
        "DBA06 violation — cross-schema FK constraints found:\n"
        + "\n".join("  " + ".".join(str(x) for x in row) for row in bad)
    )
