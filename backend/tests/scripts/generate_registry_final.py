#!/usr/bin/env python
"""Generate COUNTRY_AWARE_TABLES from ORM models."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import os
os.environ.setdefault("SECRET_KEY", "test-key-for-script")

from data.base import Base
import data.models

def derive_tables() -> dict[str, str]:
    result: dict[str, str] = {}
    for table in Base.metadata.tables.values():
        cols = {c.name for c in table.columns}
        if "country_code" in cols:
            result[table.name] = "country_code"
    return result

tables = derive_tables()

print("COUNTRY_AWARE_TABLES: dict[str, str] = {")
for name in sorted(tables.keys()):
    print(f'    "{name}": "country_code",')
print("}")
print(f"\n# Total: {len(tables)} tables")