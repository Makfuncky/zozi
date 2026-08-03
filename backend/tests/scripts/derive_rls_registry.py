#!/usr/bin/env python
"""Regenerate COUNTRY_AWARE_TABLES from ORM models and live database.

This script should be run to regenerate rls_interceptor.py when models change.
"""
from __future__ import annotations
import os
import sys
from pathlib import Path

_project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_project_root))

os.environ.setdefault("SECRET_KEY", "test-key-for-script")

from data.base import Base
import data.models

def derive_country_aware_tables() -> dict[str, str]:
    result: dict[str, str] = {}
    
    for key, table in Base.metadata.tables.items():
        col_names = [c.name for c in table.columns]
        
        if "country_code" in col_names:
            result[table.name] = "country_code"
    
    return result


def main() -> None:
    tables = derive_country_aware_tables()
    
    lines = ['COUNTRY_AWARE_TABLES: dict[str, str] = {']
    
    for name in sorted(tables.keys()):
        col = tables[name]
        lines.append(f'    "{name}": "{col}",')
    
    lines.append("}")
    
    print("\n".join(lines))
    print(f"\n# Total: {len(tables)} tables")


if __name__ == "__main__":
    main()