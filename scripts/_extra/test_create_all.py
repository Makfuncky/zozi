"""Test script to verify create_all works in development only."""
from __future__ import annotations

import os
import sys

# Guard: Only allow create_all in development
app_env = os.getenv("APP_ENV", "development").lower()
if app_env == "production":
    print("ERROR: create_all is not allowed in production. Use alembic upgrade head instead.")
    sys.exit(1)

# Only SQLite is allowed for create_all
from db.database import _IS_SQLITE
if not _IS_SQLITE:
    print("ERROR: create_all is only allowed with SQLite. Use alembic for PostgreSQL.")
    sys.exit(1)

from db.base import Base
from db.database import engine

print(f'Engine dialect: {engine.dialect.name}')
print(f'Schema translate map: {"schema_translate_map" in engine._execution_options}')
Base.metadata.create_all(engine)
print('create_all: OK')
