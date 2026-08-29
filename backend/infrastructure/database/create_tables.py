"""CLI entry point: apply pending Alembic migrations to the configured DB.

Importing this module as library code is a no-op with respect to sys.path.
Previously the ``sys.path.insert`` ran at import time, which polluted the
path so a later ``import database`` resolved to this package's own empty
``__init__.py`` instead of ``backend/database.py``. Only script execution
mutates sys.path now, and only before the module-level import that depends
on it.
"""
from __future__ import annotations

import logging
from pathlib import Path
import sys

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    # Standalone execution: the backend root must be on sys.path so the
    # ``infrastructure`` package is importable when this file is invoked
    # directly rather than as ``python -m infrastructure.database.create_tables``.
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from infrastructure.utils.migrations import upgrade_database_to_head


if __name__ == "__main__":
    upgrade_database_to_head()
    logger.info("Database migrations applied successfully.")