#!/usr/bin/env python
import sys
import os
sys.path.insert(0, '.')
os.environ['SECRET_KEY'] = 'test-key'

from db.base import Base
import models

lines = [
    'from __future__ import annotations',
    '',
    'import logging',
    'from contextvars import ContextVar',
    'from typing import Any',
    '',
    'from sqlalchemy import event',
    'from sqlalchemy.engine import Engine',
    '',
    'rls_country_scope_ctx: ContextVar[frozenset[str] | None] = ContextVar("rls_country_scope", default=None)',
    'rls_is_restricted_ctx: ContextVar[bool] = ContextVar("rls_is_restricted", default=False)',
    '',
    'COUNTRY_AWARE_TABLES: dict[str, str] = {',
]

for table in Base.metadata.tables.values():
    if 'country_code' in {c.name for c in table.columns}:
        lines.append(f'    "{table.name}": "country_code",')

lines.append('}')
lines.append('')

content = '\n'.join(lines)
print(content)