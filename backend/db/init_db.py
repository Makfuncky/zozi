from __future__ import annotations

import argparse
from pathlib import Path
import sys


sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker
from db.database import Base, engine
from db.seed import seed_data
from utils.config import settings

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def _reset_sqlite_database() -> bool:
    url = make_url(settings.database_url)
    if url.drivername != "sqlite" or not url.database:
        return False

    db_path = Path(url.database)
    if db_path.exists():
        db_path.unlink()
    return True


def _create_tables() -> None:
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully.")


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
            print("Reset local SQLite database file.")
        else:
            print("--reset skipped: configured database is not SQLite.")

    _create_tables()

    if args.seed:
        seed_data(SessionLocal)
        print("Database seed completed successfully.")


if __name__ == "__main__":
    main()
