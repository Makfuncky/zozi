"""Definitive cross-schema (DBA06) FK scanner across the ENTIRE ORM.

A cross-schema FK is any FK constraint whose source table schema differs from
its target table schema (None/"public" vs a named schema both count as distinct).
Tables where both ends are schema-less are legitimate (same default schema).
"""
from __future__ import annotations

import io, os, sys
sys.path.insert(0, os.path.join(os.getcwd(), "backend"))

import main  # noqa: F401  (imports/models side effects)
from db.base import Base


def scan():
    violations = []
    for t in Base.metadata.tables.values():
        for fkc in t.foreign_key_constraints:
            for fk in fkc.elements:
                tgt = fk.column.table
                if (t.schema or None) != (tgt.schema or None):
                    violations.append(
                        (t.schema or "public", t.name,
                         tgt.schema or "public", tgt.name, fk.parent.name,
                         fk.column.name)
                    )
    return violations


v = scan()
if v:
    for row in v:
        print("CROSS-SCHEMA:", ".".join(row[:2]), "->", ".".join(row[2:4]),
              f"({row[4]}->{row[5]})")
    print(f"TOTAL CROSS-SCHEMA FKs: {len(v)}")
else:
    print("CLEAN: zero cross-schema foreign keys in the ORM.")
