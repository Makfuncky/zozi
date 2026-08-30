"""CLI entry point: initialize the ZOZI database (create tables, optional seed).

Importing this module as library code is a no-op with respect to sys.path.
Previously the ``sys.path.insert`` ran at import time, which polluted the
path so a later ``import database`` resolved to this package's own empty
``__init__.py`` instead of ``backend/database.py``. Only script execution
mutates sys.path now, and only before the module-level imports that depend
on it.
"""
from __future__ import annotations

import argparse
import logging
from pathlib import Path
import sys

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    # Standalone execution: the backend root must be on sys.path so the
    # ``infrastructure`` package is importable when this file is invoked
    # directly rather than as ``python -m infrastructure.database.init_db``.
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker
from infrastructure.database.base import Base
from infrastructure.database.database import engine
from infrastructure.database.seed import seed_data
from infrastructure.utils.config import settings

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def _reset_sqlite_database() -> bool:
    url = make_url(settings.database_url)
    if url.drivername != "sqlite" or not url.database:
        return False

    db_path = Path(url.database)
    if db_path.exists():
        db_path.unlink()
    return True


def _import_all_models() -> None:
    import importlib
    import pkgutil
    import domains
    for _, modname, ispkg in pkgutil.walk_packages(domains.__path__, prefix='domains.'):
        if '.models.' in modname or modname.endswith('.models'):
            try:
                importlib.import_module(modname)
            except Exception as exc:
                logger.debug('Skip model import %s: %s', modname, exc)


def _create_tables() -> None:
    from infrastructure.database.base import Base as ModelsBase
    from infrastructure.database.database import _IS_SQLITE
    _import_all_models()
    if _IS_SQLITE:
        # SQLite doesn't support schemas - strip schema from all tables
        for table in ModelsBase.metadata.tables.values():
            table.schema = None
    ModelsBase.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Initialize the ZOZI database")
    parser.add_argument("--seed", action="store_true", help="Seed demo users and products")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Delete the local SQLite database before applying migrations",
    )
    args = parser.parse_args()

    if args.reset:
        if _reset_sqlite_database():
            logger.info("Reset local SQLite database file.")
        else:
            logger.info("--reset skipped: configured database is not SQLite.")

    _create_tables()

    if args.seed:
        seed_data(SessionLocal)
        logger.info("Database seed completed successfully.")


if __name__ == "__main__":
    main()