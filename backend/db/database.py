from __future__ import annotations

import logging
import os
import time
from contextlib import asynccontextmanager
from typing import Generator, AsyncGenerator

from sqlalchemy import create_engine, event, text
from sqlalchemy.pool import QueuePool, StaticPool
from sqlalchemy.orm import sessionmaker, Session

from utils.config import settings, BASE_DIR
from db.base import Base

logger = logging.getLogger(__name__)

DATABASE_URL = str(settings.database_url)
if not DATABASE_URL:
    raise ValueError("DATABASE_URL must be configured in settings or environment")

if DATABASE_URL.startswith("sqlite"):
    if os.getenv("APP_ENV", "development").lower() == "production":
        raise ValueError(
            "SQLite is not allowed in production. "
            "Set DATABASE_URL to a PostgreSQL connection string. "
            "Example: postgresql://user:pass@host:5432/dbname"
        )
    db_path = DATABASE_URL.replace("sqlite:///", "")
    if not os.path.isabs(db_path):
        db_path = str(BASE_DIR / db_path)
    if ":" in db_path and not db_path.startswith("\\\\"):
        pass
    DATABASE_URL = f"sqlite:///{db_path}"

_IS_SQLITE = DATABASE_URL.startswith("sqlite")
_IS_POSTGRES = DATABASE_URL.startswith("postgresql") or DATABASE_URL.startswith("postgres")

if _IS_SQLITE:
    connect_args = {"check_same_thread": False}
    poolclass = StaticPool
    _pool_kwargs = {}
elif _IS_POSTGRES:
    connect_args = {}
    ssl_mode = os.getenv("DB_SSL_MODE", "prefer")
    if ssl_mode and ssl_mode != "disable":
        connect_args["sslmode"] = ssl_mode
    if os.getenv("DB_SSL_CERT"):
        connect_args["sslcert"] = os.getenv("DB_SSL_CERT")
    if os.getenv("DB_SSL_KEY"):
        connect_args["sslkey"] = os.getenv("DB_SSL_KEY")
    if os.getenv("DB_SSL_ROOT_CERT"):
        connect_args["sslrootcert"] = os.getenv("DB_SSL_ROOT_CERT")
    poolclass = QueuePool
    _pool_kwargs = {
        "pool_size": settings.db_pool_size,
        "max_overflow": settings.db_max_overflow,
        "pool_recycle": settings.db_pool_recycle,
        "pool_pre_ping": True,
        "pool_timeout": settings.db_connect_timeout,
    }
else:
    connect_args = {}
    poolclass = QueuePool
    _pool_kwargs = {
        "pool_size": settings.db_pool_size,
        "max_overflow": settings.db_max_overflow,
        "pool_recycle": settings.db_pool_recycle,
        "pool_pre_ping": True,
        "pool_timeout": settings.db_connect_timeout,
    }

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    poolclass=poolclass,
    echo=getattr(settings, "debug", False),
    **_pool_kwargs,
)

if _IS_SQLITE:
    # Performance + concurrency tuning applied to every connection. SQLite in
    # the default DELETE/ROLLBACK journal mode serializes writers and raises
    # "database is locked" under concurrent FastAPI threadpool traffic. WAL lets
    # readers proceed while a writer is active; busy_timeout makes contending
    # transactions wait instead of erroring; a larger page cache + mmap cut
    # physical IO on the RLS-heavy read path.
    @event.listens_for(engine, "connect")
    def _sqlite_perf_pragmas(dbapi_conn, _record):
        cur = dbapi_conn.cursor()
        try:
            cur.execute("PRAGMA journal_mode=WAL")
            cur.execute("PRAGMA synchronous=NORMAL")
            cur.execute("PRAGMA busy_timeout=5000")
            cur.execute("PRAGMA cache_size=-32000")  # 32 MB page cache
            cur.execute("PRAGMA temp_store=MEMORY")
            cur.execute("PRAGMA mmap_size=67108864")  # 64 MB memory-mapped IO
        finally:
            cur.close()

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False,
)

def close_db_session(db: Session) -> None:
    """Close a session obtained from get_db_session."""
    db.close()


async def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a database session with proper cleanup."""
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def get_db_session() -> Session:
    """Get a database session for non-FastAPI usage."""
    return SessionLocal()


def get_service_session(timeout_seconds: int = 30):
    """Session wrapper for background services with guaranteed cleanup."""
    from contextlib import contextmanager
    
    @contextmanager
    def _session():
        start_time = time.time()
        db = SessionLocal()
        try:
            yield db
            elapsed = time.time() - start_time
            if elapsed > timeout_seconds:
                logger.warning(
                    f"Service session took {elapsed:.2f}s, exceeding timeout of {timeout_seconds}s"
                )
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()
    return _session()


def get_db_context():
    """Context manager for non-FastAPI usage (e.g., controllers, background tasks)."""
    from contextlib import contextmanager
    
    @contextmanager
    def _session():
        db = SessionLocal()
        try:
            yield db
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()
    return _session()


def get_db_sync():
    """Synchronous session context manager for background tasks."""
    from contextlib import contextmanager
    
    @contextmanager
    def _session():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()
    return _session()


def check_connection_health() -> bool:
    """Check database connectivity."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False


def get_pool_metrics() -> dict:
    """Get connection pool metrics."""
    pool = engine.pool
    try:
        return {
            "size": pool.size() if hasattr(pool, "size") else 1,
            "checkedin": pool.checkedin() if hasattr(pool, "checkedin") else 1,
            "checkedout": pool.checkedout() if hasattr(pool, "checkedout") else 0,
            "overflow": pool.overflow() if hasattr(pool, "overflow") else 0,
        }
    except AttributeError:
        return {
            "size": 1,
            "checkedin": 1,
            "checkedout": 0,
            "overflow": 0,
            "note": "StaticPool used (SQLite development mode)",
        }


def dispose_engine() -> None:
    """Dispose the engine and release all connections."""
    engine.dispose()
    logger.info("Database engine disposed")


def _guard_dev_only(operation: str) -> None:
    """Refuse destructive schema helpers outside of safe (dev/SQLite) environments.

    ``create_tables`` / ``reset_tables`` use ``Base.metadata`` which can mask
    real migration drift and, on Postgres, can drop production data. They are
    only permitted on SQLite (development/test).
    """
    if _IS_POSTGRES:
        raise RuntimeError(
            f"{operation} is disabled on PostgreSQL. Use a reviewed Alembic "
            f"migration instead of Base.metadata.create_all/drop_all."
        )
    if str(getattr(settings, "app_env", "development")).lower() == "production":
        raise RuntimeError(
            f"{operation} is disabled in production. Use a reviewed Alembic migration."
        )


def create_tables() -> None:
    """Create all database tables (development/SQLite only)."""
    _guard_dev_only("create_tables")
    Base.metadata.create_all(bind=engine)
    logger.info("Tables created")


def reset_tables() -> None:
    """Drop and recreate all tables (development/SQLite only — destructive)."""
    _guard_dev_only("reset_tables")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    logger.info("Tables reset")
