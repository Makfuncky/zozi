from __future__ import annotations

import logging
import os
import time
from contextlib import asynccontextmanager
from typing import Generator, AsyncGenerator

from sqlalchemy import create_engine, event, text
from sqlalchemy.pool import QueuePool, StaticPool
from sqlalchemy.orm import sessionmaker, Session

try:
    from sqlalchemy.ext.asyncio import (
        AsyncSession,
        async_sessionmaker,
        create_async_engine,
    )
    _HAS_ASYNC_SA = True
except ImportError:  # pragma: no cover - async support is optional
    AsyncSession = None  # type: ignore[assignment]
    async_sessionmaker = None  # type: ignore[assignment]
    create_async_engine = None  # type: ignore[assignment]
    _HAS_ASYNC_SA = False

from infrastructure.utils.config import settings, BASE_DIR
from infrastructure.database.base import Base

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

search_path = None
if _IS_POSTGRES:
    search_path = os.getenv("DB_SEARCH_PATH", "public,analytics,audit,commerce,configuration,country,customer,finance,hr,logistics,media,security,supplier")

_SCHEMA_TRANSLATE_MAP = None
if _IS_SQLITE:
    _SCHEMA_TRANSLATE_MAP = {
        "core": None,
        "commerce": None,
        "supplier": None,
        "customer": None,
        "logistics": None,
        "finance": None,
        "treasury": None,
        "hr": None,
        "country": None,
        "media": None,
        "ai": None,
        "communication": None,
        "audit": None,
        "security": None,
        "analytics": None,
        "configuration": None,
    }

_engine_kwargs = {
    "connect_args": connect_args,
    "poolclass": poolclass,
    "echo": getattr(settings, "debug", False),
    **_pool_kwargs,
}
if _SCHEMA_TRANSLATE_MAP is not None:
    _engine_kwargs["execution_options"] = {"schema_translate_map": _SCHEMA_TRANSLATE_MAP}

engine = create_engine(DATABASE_URL, **_engine_kwargs)

if _IS_SQLITE:
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


# --- Async engine (optional, for high-concurrency FastAPI endpoints) ---
# Created lazily so a project without `asyncpg` installed can still use the
# fully synchronous stack above. Use `get_async_db()` from async route
# handlers to share the same connection-pool budget as the sync engine.
_async_engine = None
_AsyncSessionLocal = None


def _build_async_database_url(sync_url: str) -> str | None:
    if not sync_url:
        return None
    if sync_url.startswith("postgresql+asyncpg://"):
        return sync_url
    if sync_url.startswith("postgresql://") or sync_url.startswith("postgres://"):
        return sync_url.replace("postgresql://", "postgresql+asyncpg://", 1).replace(
            "postgres://", "postgresql+asyncpg://", 1
        )
    if sync_url.startswith("sqlite+aiosqlite://"):
        return sync_url
    if sync_url.startswith("sqlite://"):
        return sync_url.replace("sqlite:///", "sqlite+aiosqlite:///", 1).replace(
            "sqlite://", "sqlite+aiosqlite://", 1
        )
    return None


def _get_async_engine():
    global _async_engine, _AsyncSessionLocal
    if not _HAS_ASYNC_SA:
        raise RuntimeError(
            "SQLAlchemy async support is not available. "
            "Install 'asyncpg' (PostgreSQL) and/or 'aiosqlite' to enable get_async_db()."
        )
    if _async_engine is not None:
        return _async_engine

    async_url = _build_async_database_url(DATABASE_URL)
    if async_url is None:
        raise RuntimeError(
            f"Cannot derive an async database URL from DATABASE_URL='{DATABASE_URL}'."
        )

    async_connect_args: dict = {}
    if async_url.startswith("sqlite"):
        async_connect_args["check_same_thread"] = False
    elif async_url.startswith("postgresql+asyncpg"):
        ssl_mode = os.getenv("DB_SSL_MODE", "prefer")
        if ssl_mode and ssl_mode != "disable":
            async_connect_args["ssl"] = ssl_mode

    async_pool_kwargs: dict = {}
    if not async_url.startswith("sqlite"):
        async_pool_kwargs = {
            "pool_size": settings.db_pool_size,
            "max_overflow": settings.db_max_overflow,
            "pool_recycle": settings.db_pool_recycle,
            "pool_pre_ping": True,
            "pool_timeout": settings.db_connect_timeout,
        }

    _async_engine = create_async_engine(
        async_url,
        connect_args=async_connect_args,
        echo=getattr(settings, "debug", False),
        **async_pool_kwargs,
    )
    _AsyncSessionLocal = async_sessionmaker(
        bind=_async_engine,
        expire_on_commit=False,
        class_=AsyncSession,
    )
    return _async_engine


async def get_async_db() -> AsyncGenerator["AsyncSession", None]:
    """FastAPI dependency that yields an async database session.

    Kept independent from the sync `engine`/`SessionLocal` so a single FastAPI
    process can mix sync and async handlers without sharing a connection pool.
    """
    if not _HAS_ASYNC_SA:
        raise RuntimeError(
            "Async database support requires SQLAlchemy 1.4+ with async drivers "
            "installed (asyncpg for PostgreSQL, aiosqlite for SQLite)."
        )
    factory = _AsyncSessionLocal or _get_async_engine() and _AsyncSessionLocal
    if factory is None:
        _get_async_engine()
        factory = _AsyncSessionLocal
    assert factory is not None
    session = factory()
    try:
        yield session
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


# --- Read replica ---
# Used for read-heavy endpoints (catalog browse, search, analytics) so the
# primary is not starved by writes. Falls back transparently to the primary
# when DATABASE_REPLICA_URL is not configured.
_replica_engine = None
_ReplicaSessionLocal = None


def _get_replica_engine():
    global _replica_engine, _ReplicaSessionLocal
    if _replica_engine is not None:
        return _replica_engine

    replica_url = str(getattr(settings, "database_replica_url", "") or "").strip()
    if not replica_url:
        replica_url = DATABASE_URL

    replica_connect_args: dict = {}
    replica_pool_kwargs: dict = {}
    if replica_url.startswith("sqlite"):
        replica_connect_args["check_same_thread"] = False
        replica_poolclass = StaticPool
    elif replica_url.startswith("postgresql") or replica_url.startswith("postgres"):
        replica_poolclass = QueuePool
        replica_connect_args = {}
        ssl_mode = os.getenv("DB_SSL_MODE", "prefer")
        if ssl_mode and ssl_mode != "disable":
            replica_connect_args["sslmode"] = ssl_mode
        if os.getenv("DB_SSL_CERT"):
            replica_connect_args["sslcert"] = os.getenv("DB_SSL_CERT")
        if os.getenv("DB_SSL_KEY"):
            replica_connect_args["sslkey"] = os.getenv("DB_SSL_KEY")
        if os.getenv("DB_SSL_ROOT_CERT"):
            replica_connect_args["sslrootcert"] = os.getenv("DB_SSL_ROOT_CERT")
        replica_pool_kwargs = {
            "pool_size": settings.db_pool_size,
            "max_overflow": settings.db_max_overflow,
            "pool_recycle": settings.db_pool_recycle,
            "pool_pre_ping": True,
            "pool_timeout": settings.db_connect_timeout,
        }
    else:
        replica_poolclass = QueuePool
        replica_pool_kwargs = {
            "pool_size": settings.db_pool_size,
            "max_overflow": settings.db_max_overflow,
            "pool_recycle": settings.db_pool_recycle,
            "pool_pre_ping": True,
            "pool_timeout": settings.db_connect_timeout,
        }

    replica_engine_kwargs: dict = {
        "connect_args": replica_connect_args,
        "poolclass": replica_poolclass,
        "echo": getattr(settings, "debug", False),
        **replica_pool_kwargs,
    }

    _replica_engine = create_engine(replica_url, **replica_engine_kwargs)
    _ReplicaSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=_replica_engine,
        expire_on_commit=False,
    )
    return _replica_engine


def get_read_db() -> Generator[Session, None, None]:
    """FastAPI dependency yielding a session bound to the read replica.

    Falls back to the primary database when no replica is configured
    (`settings.database_replica_url` is empty).
    """
    if _ReplicaSessionLocal is None:
        _get_replica_engine()
    assert _ReplicaSessionLocal is not None
    db = _ReplicaSessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

def close_db_session(db: Session) -> None:
    """Close a session obtained from get_db_session."""
    db.close()


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a database session with proper cleanup.

    Implemented as a *synchronous* generator so it can be used both ways:
      * ``Depends(get_db)`` in route handlers (2412 call sites) — FastAPI drives
        the generator and runs teardown on request completion.
      * ``with get_db() as db:`` in non-request code (background tasks,
        middleware, websockets, health probes) — a plain context manager.

    It was previously an ``async def`` generator, which made ``with get_db()``
    raise ``AttributeError: __enter__``. That error was silently swallowed in
    ``middleware/country_context.py``, so the row-level-security country scope
    was never set, and surfaced as 500s in ``utils/entity_messaging.py``.
    """
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
    """Check database connectivity with connection validation."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            # Additional validation: check connection is alive and get server info
            if _IS_POSTGRES:
                result = conn.execute(text("SELECT current_database(), current_user, version()"))
                db_name, db_user, version = result.fetchone()
                logger.debug(f"DB Health: database={db_name}, user={db_user}, version={version[:50]}")
        return True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False


def validate_connection_pool() -> dict:
    """Validate connection pool health and return diagnostics."""
    pool = engine.pool
    try:
        # Force a connection validation
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            validation_ok = True
        pool_metrics = {
            "size": pool.size() if hasattr(pool, "size") else 1,
            "checkedin": pool.checkedin() if hasattr(pool, "checkedin") else 1,
            "checkedout": pool.checkedout() if hasattr(pool, "checkedout") else 0,
            "overflow": pool.overflow() if hasattr(pool, "overflow") else 0,
            "validation_ok": validation_ok,
            "pre_ping_enabled": _pool_kwargs.get("pool_pre_ping", False),
            "pool_recycle_seconds": _pool_kwargs.get("pool_recycle", 1800),
        }
        return pool_metrics
    except AttributeError:
        return {
            "size": 1,
            "checkedin": 1,
            "checkedout": 0,
            "overflow": 0,
            "note": "StaticPool used (SQLite development mode)",
        }
    except Exception as e:
        return {"error": str(e), "validation_ok": False}


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
    if _replica_engine is not None:
        _replica_engine.dispose()
    if _async_engine is not None:
        # async_engine.dispose is a coroutine; close synchronously best-effort.
        try:
            close_fn = getattr(_async_engine, "close", None)
            if close_fn is not None:
                result = close_fn()
                if hasattr(result, "__await__"):
                    # Running event loop is the caller's responsibility in
                    # startup/shutdown hooks; fall through to sync dispose.
                    pass
        except Exception:
            logger.debug("Async engine close() best-effort failed", exc_info=True)
        try:
            _async_engine.sync_engine.dispose()
        except Exception:
            logger.debug("Async engine sync_engine dispose failed", exc_info=True)
    logger.info("Database engines disposed")


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
    from infrastructure.database.base import Base as ModelsBase
    ModelsBase.metadata.create_all(bind=engine)
    logger.info("Tables created")


def reset_tables() -> None:
    """Drop and recreate all tables (development/SQLite only — destructive)."""
    _guard_dev_only("reset_tables")
    from infrastructure.database.base import Base as ModelsBase
    ModelsBase.metadata.drop_all(bind=engine)
    ModelsBase.metadata.create_all(bind=engine)
    logger.info("Tables reset")


