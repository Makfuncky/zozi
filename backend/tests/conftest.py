"""Shared pytest fixtures for the Zozi backend test-suite.

Every ``db_session`` is wrapped in a **transaction-level rollback** -- the
fixture opens a connection, begins a transaction, and yields a session whose
``commit()`` flushes rather than persists. At teardown the outer transaction
is rolled back, so tests never leak data to one another.  No more
country-code workarounds, no more stale rows between tests.

Gap tables (``onboarding_pipelines``, ``offboarding_cases``, etc.) are created
at session-scope inside the ``engine`` fixture (after ORM ``create_all()``)
because DDL auto-commits in SQLite and would break per-test transaction
isolation.

Usage in a test module::

    from fastapi.testclient import TestClient

    def test_health(client: TestClient):
        resp = client.get("/health")
        assert resp.status_code == 200

These fixtures intentionally avoid importing ``main`` at collection time (the
app eagerly loads every router); ``app`` / ``client`` import lazily so that
``pytest --co`` stays fast and resilient to unrelated router failures.
"""
from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Iterator

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session

# Ensure the backend package root is importable regardless of cwd.
_BACKEND_ROOT = Path(__file__).resolve().parent.parent
if str(_BACKEND_ROOT) not in os.sys.path:
    os.sys.path.insert(0, str(_BACKEND_ROOT))

# Disable rate limiting in tests by setting APP_ENV=test before the app loads.
os.environ.setdefault("APP_ENV", "test")

# Disable CSRF protection in tests
os.environ.setdefault("CSRF_DISABLED", "true")

# Set required env vars for testing
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-pytest-only")
os.environ.setdefault("SEED_ADMIN_PASSWORD", "admin123")

from db.base import Base  # noqa: E402

import models  # noqa: E402


def _patch_fk_schemas():
    """Patch unqualified FK references to include schema prefixes.

    Many model files use ForeignKey("users.id") where the actual table is
    registered as "core.users" because User.__table_args__ sets schema="core".
    This patch rewrites every ForeignKey target to match the metadata table key
    so that configure_mappers() / create_all() can resolve the reference.
    """
    metadata = models.Base.metadata

    table_schemas: dict[str, str | None] = {}
    for t in metadata.tables.values():
        key = t.key
        if "." in key:
            schema, name_part = key.split(".", 1)
            table_schemas[name_part] = schema
        else:
            table_schemas[t.name] = None

    for table in metadata.tables.values():
        for col in table.columns:
            for fk in col.foreign_keys:
                target = fk._colspec
                if isinstance(target, str):
                    parts = target.split(".")
                    if len(parts) == 2:
                        tbl_name, col_name = parts
                        if tbl_name in table_schemas:
                            schema = table_schemas[tbl_name]
                            if schema:
                                fk._colspec = f"{schema}.{tbl_name}.{col_name}"
                                if hasattr(fk, '_column_tokens'):
                                    del fk._column_tokens
                    elif len(parts) == 3:
                        schema, tbl_name, col_name = parts
                        if tbl_name in table_schemas:
                            expected_schema = table_schemas[tbl_name]
                            if expected_schema and expected_schema != schema:
                                fk._colspec = f"{expected_schema}.{tbl_name}.{col_name}"
                                if hasattr(fk, '_column_tokens'):
                                    del fk._column_tokens

_patch_fk_schemas()

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
    "trading": None,
}

_legacy_engine = None

def _get_legacy_engine():
    global _legacy_engine
    if _legacy_engine is None:
        _legacy_engine = create_engine("sqlite://", echo=False, execution_options={"schema_translate_map": _SCHEMA_TRANSLATE_MAP})
        _legacy_engine.execution_options(isolation_level="AUTOCOMMIT")
        models.Base.metadata.create_all(bind=_legacy_engine)
    return _legacy_engine


@pytest.fixture(scope="session")
def engine(db_file: str):
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
        "trading": None,
    }
    eng = create_engine(
        f"sqlite:///{db_file}",
        connect_args={"check_same_thread": False},
        poolclass=__import__("sqlalchemy.pool", fromlist=["StaticPool"]).StaticPool,
        execution_options={"schema_translate_map": _SCHEMA_TRANSLATE_MAP},
    )
    global _legacy_engine
    _legacy_engine = eng
    models.Base.metadata.create_all(bind=eng)
    _create_gap_tables(eng)
    try:
        yield eng
    finally:
        _legacy_engine = None
        eng.dispose()

def _TestSession():
    return sessionmaker(bind=_get_legacy_engine(), autoflush=False, autocommit=False)()


# Ensure all model modules are imported so that Base.metadata knows about every table
# before create_all() runs. Import order matters for foreign-key tables.
import models  # noqa: E402
import models.user  # noqa: E402
import models.upload_job  # noqa: E402
import models.products  # noqa: E402
import models.orders  # noqa: E402
import models.payments  # noqa: E402
import models.suppliers  # noqa: E402
import models.logistics  # noqa: E402
import models.countries  # noqa: E402
import models.finance  # noqa: E402
import models.admin  # noqa: E402
import models.commission  # noqa: E402
import models.permissions  # noqa: E402
import models.mixins  # noqa: E402
import models.media_models  # noqa: E402


# ══════════════════════════════════════════════════════════════════
#  Rollback Session  --  intercept db.commit() so the outer
#  connection transaction can roll back everything at the end.
# ══════════════════════════════════════════════════════════════════

class _RollbackSession(Session):
    """Session whose ``commit()`` flushes within the current transaction
    rather than persisting to the database.  The outer
    ``connection.begin()`` transaction is rolled back at the end of every
    test, so no data ever leaks between tests."""

    def commit(self) -> None:
        # Services legitimately call db.commit() and expect flushed
        # data to be visible to subsequent queries *in the same test*.
        # Flushing satisfies that requirement without ending the outer
        # transaction that our fixture will roll back.
        self.flush()


# ══════════════════════════════════════════════════════════════════
#  Gap-table DDL  --  tables that the Alembic migration creates but
#  that have no (or incomplete) ORM models.  Created once at session
#  scope because DDL auto-commits in SQLite.
# ══════════════════════════════════════════════════════════════════

_GAP_DDL: dict[str, str] = {
    "onboarding_pipelines": """
        CREATE TABLE IF NOT EXISTS onboarding_pipelines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER NOT NULL UNIQUE REFERENCES employees(id) ON DELETE CASCADE,
            country_code TEXT REFERENCES country_configs(code),
            current_step TEXT,
            total_steps INTEGER DEFAULT 0,
            completed_steps INTEGER DEFAULT 0,
            status TEXT DEFAULT 'pending',
            started_at TIMESTAMP,
            due_date TIMESTAMP,
            completed_at TIMESTAMP,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """,
    "onboarding_steps": """
        CREATE TABLE IF NOT EXISTS onboarding_steps (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pipeline_id INTEGER NOT NULL REFERENCES onboarding_pipelines(id) ON DELETE CASCADE,
            employee_id INTEGER REFERENCES employees(id) ON DELETE CASCADE,
            step_name TEXT NOT NULL,
            label TEXT,
            description TEXT,
            sla_hours INTEGER DEFAULT 24,
            step_order INTEGER DEFAULT 0,
            status TEXT DEFAULT 'pending',
            completed_at TIMESTAMP,
            completed_by INTEGER REFERENCES users(id),
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """,
    "offboarding_cases": """
        CREATE TABLE IF NOT EXISTS offboarding_cases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
            country_code TEXT REFERENCES country_configs(code),
            reason TEXT,
            status TEXT DEFAULT 'in_progress',
            total_steps INTEGER DEFAULT 6,
            completed_steps INTEGER DEFAULT 0,
            current_step TEXT,
            initiated_by INTEGER NOT NULL REFERENCES users(id),
            initiated_at TIMESTAMP,
            notice_period_days INTEGER DEFAULT 30,
            proposed_exit_date TIMESTAMP,
            completed_at TIMESTAMP,
            cancellation_reason TEXT,
            cancelled_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """,
    "employee_activity_logs": """
        CREATE TABLE IF NOT EXISTS employee_activity_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            actor_employee_id INTEGER REFERENCES employees(id) ON DELETE SET NULL,
            target_employee_id INTEGER REFERENCES employees(id) ON DELETE SET NULL,
            action TEXT NOT NULL,
            entity_type TEXT,
            entity_id INTEGER,
            metadata_json TEXT,
            country_code TEXT REFERENCES country_configs(code),
            ip_address TEXT,
            device_fingerprint TEXT,
            session_id TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """,
    "employee_bank_accounts": """
        CREATE TABLE IF NOT EXISTS employee_bank_accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
            account_holder_name TEXT NOT NULL,
            bank_name TEXT NOT NULL,
            account_number_encrypted TEXT NOT NULL,
            iban TEXT,
            swift_code TEXT,
            currency TEXT DEFAULT 'OMR',
            is_primary INTEGER DEFAULT 0,
            is_verified INTEGER DEFAULT 0,
            verified_at TIMESTAMP,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """,
    "payout_batches": """
        CREATE TABLE IF NOT EXISTS payout_batches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            batch_number VARCHAR(50) NOT NULL,
            country_code VARCHAR(10),
            total_amount NUMERIC(16,4) NOT NULL,
            item_count INTEGER NOT NULL,
            status VARCHAR(20) DEFAULT 'pending_approval',
            created_by INTEGER REFERENCES users(id),
            approved_by INTEGER REFERENCES users(id),
            dispatched_at TIMESTAMP,
            settled_at TIMESTAMP,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """,
    "journal_entries": """
        CREATE TABLE IF NOT EXISTS journal_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entry_date TIMESTAMP NOT NULL,
            reference_number VARCHAR(50) NOT NULL UNIQUE,
            description TEXT,
            source VARCHAR(50),
            country_code VARCHAR(10),
            currency VARCHAR(3) DEFAULT 'OMR',
            is_reconciled BOOLEAN DEFAULT 0,
            created_by INTEGER,
            reference_type VARCHAR(50),
            reference_id INTEGER,
            period_id INTEGER,
            reversal_of_id INTEGER,
            is_deleted BOOLEAN DEFAULT 0,
            deleted_at TIMESTAMP,
            deleted_by INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """,
}


def _create_gap_tables(engine) -> None:
    """Create gap tables that the Alembic migration provides but which
    have no ORM model (or whose ORM model has an incomplete column set).
    Called once inside the session-scoped ``engine`` fixture so DDL
    auto-commit doesn't interfere with per-test transaction isolation.

    Uses ``CREATE TABLE IF NOT EXISTS`` so it is idempotent across
    pytest sessions sharing the same file (unlikely, but safe).
    """
    with engine.connect() as conn:
        for table_name, ddl in _GAP_DDL.items():
            # Drop first so the richer migration DDL replaces the
            # ORM-created (limited-column) version if it exists.
            conn.execute(text(f"DROP TABLE IF EXISTS {table_name}"))
            conn.execute(text("PRAGMA foreign_keys = OFF"))
            conn.execute(text(ddl))
            conn.execute(text("PRAGMA foreign_keys = ON"))
        conn.commit()


# ══════════════════════════════════════════════════════════════════
#  Fixtures
# ══════════════════════════════════════════════════════════════════


@pytest.fixture(scope="session")
def db_file() -> Iterator[str]:
    """Create a throwaway SQLite file for the test session."""
    fd, path = tempfile.mkstemp(suffix=".db", prefix="zozi_test_")
    os.close(fd)
    yield path
    try:
        os.remove(path)
    except OSError:
        pass


@pytest.fixture
def db_session(engine) -> Iterator[Session]:
    """Yield a session wrapped in a transaction that is **always rolled
    back** when the test finishes.  The session uses ``_RollbackSession``
    so that ``db.commit()`` flushes within the ongoing transaction rather
    than ending it.  No data written during the test ever leaks to other
    tests.
    """
    connection = engine.connect()
    transaction = connection.begin()
    session = _RollbackSession(bind=connection, autoflush=False)
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture
def app(engine, _seed_default_accounts):
    """Build the FastAPI app with the DB dependency overridden to the test engine.

    Depends on ``_seed_default_accounts`` so demo users (admin, supplier, etc.)
    exist in the DB before any test that uses the TestClient runs.
    """
    from db.database import get_db as _real_get_db  # noqa: F401

    import main as _main  # noqa: F401  (ensures routers are importable)

    Session = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    def _override_get_db():
        db = Session()
        try:
            yield db
        finally:
            db.close()

    _main.app.dependency_overrides[_real_get_db] = _override_get_db
    yield _main.app
    _main.app.dependency_overrides.clear()


def _set_email_verified(email: str) -> None:
    from models import User as _User

    sess = _TestSession()
    try:
        user = sess.query(_User).filter(_User.email == email).first()
        if user:
            user.email_verified = True
            if hasattr(user, "is_email_verified"):
                user.is_email_verified = True
            sess.commit()
    finally:
        sess.close()


# ── Module-level constant: demo user email/role map used by both
#    ``_seed_default_accounts`` and ``_auth_tokens`` so a new role
#    only requires one change.
_DEMO_USERS: list[tuple[str, str, str, str, str]] = [
    ("admin@zozi.com", "admin", "admin123", "admin", "admin"),
    ("supplier@zozi.com", "supplier", "supplier123", "supplier", "supplier"),
    ("customer@zozi.com", "customer", "customer123", "customer", "customer"),
]


@pytest.fixture(scope="session")
def _seed_default_accounts(engine):
    """Seed demo users and the countries they reference **once per session**.

    ``_ensure_demo_user`` in ``db/seed.py`` hard-codes ``country_code="AE"``
    on every user, and the ``users`` table has
    ``ForeignKey("country_configs.code")``.  We must create the country
    rows *before* users or the FK constraint will fail.

    ``autouse=True`` was removed — tests that need the demo accounts should
    declare ``_seed_default_accounts`` as a parameter or depend on ``client``
    (which transitively seeds).  This saves ~6s per test file by running the
    seeding only once per pytest session.
    """
    from db.seed import _ensure_demo_user
    from models import CountryConfig, User as _UserModel

    TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    session = TestingSession()
    try:
        # ── Step 1: ensure the countries that _ensure_demo_user references ──
        demo_countries = [
            {"code": "AE", "name": "United Arab Emirates", "currency": "AED",
             "currency_symbol": "د.إ", "phone_code": "+971"},
            {"code": "SA", "name": "Saudi Arabia", "currency": "SAR",
             "currency_symbol": "﷼", "phone_code": "+966"},
            {"code": "OM", "name": "Oman", "currency": "OMR",
             "currency_symbol": "﷼", "phone_code": "+968"},
        ]
        for c in demo_countries:
            existing = session.query(CountryConfig).filter(
                CountryConfig.code == c["code"]
            ).first()
            if not existing:
                session.add(CountryConfig(**c))
        session.flush()

        # ── Step 2a: seed WELCOME10 coupon for coupon validation tests ──
        from models import Coupon as _Coupon
        existing_coupon = session.query(_Coupon).filter(_Coupon.code == "WELCOME10").first()
        if not existing_coupon:
            session.add(_Coupon(
                code="WELCOME10",
                title="Welcome Discount",
                discount_type="percentage",
                discount_value=10,
                minimum_order=10,
                is_active=True,
            ))
        session.flush()

        # ── Step 2: seed demo user accounts ──
        for email, username, password, role, label in _DEMO_USERS:
            _ensure_demo_user(
                session,
                email=email,
                username=username,
                password=password,
                role=role,
                log_label=label,
            )
            # Ensure customer users are email-verified so tokens work
            # out of the box for every endpoint.
            if role == "customer":
                user_obj = session.query(_UserModel).filter(_UserModel.email == email).first()
                if user_obj:
                    user_obj.email_verified = True
            session.flush()
        session.commit()
    finally:
        session.close()
    yield
    # No explicit cleanup needed — the engine fixture uses a throwaway
    # temp SQLite file that the db_file fixture deletes at session end.


# ══════════════════════════════════════════════════════════════════
#  Session-scoped Auth Token Fixtures
#
#  Pre-create JWT access tokens for each demo role **once per
#  pytest session** so individual tests never pay the login
#  overhead.  The tokens are created from the demo users seeded
#  by ``_seed_default_accounts``.
# ══════════════════════════════════════════════════════════════════


@pytest.fixture(scope="session")
def _auth_tokens(engine, _seed_default_accounts) -> dict[str, str]:
    """Build and cache a ``{role: jwt_token}`` dict for every demo user.

    Runs once per session, immediately after the demo accounts are seeded.
    The tokens are created by calling ``utils.auth.create_access_token``
    with a sufficiently long expiry so they stay valid for the whole test
    run.

    Tokens are created for the roles defined in ``_DEMO_USERS`` (the
    module-level constant shared with ``_seed_default_accounts``).

    Returns
    -------
    dict[str, str]
        Mapping of role → JWT string, e.g. ``{"admin": "eyJ...",
        "supplier": "eyJ...", "customer": "eyJ..."}``
    """
    from datetime import timedelta
    from models import User as _User
    from utils.auth import create_access_token as _create_token

    _Session = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    session = _Session()
    try:
        tokens: dict[str, str] = {}
        for email, _uname, _pwd, role, _label in _DEMO_USERS:
            user = session.query(_User).filter(_User.email == email).first()
            if user is None:
                raise RuntimeError(
                    f"Demo user '{email}' not found — ensure _seed_default_accounts "
                    f"runs before _auth_tokens"
                )
            # The `sub` must be the user ID as string — that's what
            # `verify_token` -> `_resolve_user_from_subject` expects.
            token = _create_token(
                data={"sub": str(user.id), "role": role},
                expires_delta=timedelta(hours=24),  # far future, no expiry during test
            )
            tokens[role] = token
        return tokens
    finally:
        session.close()


@pytest.fixture(scope="session")
def admin_token(_auth_tokens) -> str:
    """JWT access token for the admin demo user (admin@zozi.com)."""
    return _auth_tokens["admin"]


@pytest.fixture(scope="session")
def supplier_token(_auth_tokens) -> str:
    """JWT access token for the supplier demo user (supplier@zozi.com)."""
    return _auth_tokens["supplier"]


@pytest.fixture(scope="session")
def customer_token(_auth_tokens) -> str:
    """JWT access token for the customer demo user (customer@zozi.com)."""
    return _auth_tokens["customer"]


@pytest.fixture(scope="session")
def admin_auth_headers(admin_token) -> dict[str, str]:
    """``Authorization: Bearer <admin_jwt>`` header dict for API calls."""
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture(scope="session")
def supplier_auth_headers(supplier_token) -> dict[str, str]:
    """``Authorization: Bearer <supplier_jwt>`` header dict."""
    return {"Authorization": f"Bearer {supplier_token}"}


@pytest.fixture(scope="session")
def customer_auth_headers(customer_token) -> dict[str, str]:
    """``Authorization: Bearer <customer_jwt>`` header dict."""
    return {"Authorization": f"Bearer {customer_token}"}


# ── Authenticated TestClient ─────────────────────────────────────────────


@pytest.fixture
def client(app) -> Iterator["TestClient"]:  # type: ignore[name-defined]
    """A FastAPI TestClient wired to the test database."""
    from fastapi.testclient import TestClient

    with TestClient(app) as c:
        yield c


@pytest.fixture
def admin_client(app, admin_auth_headers) -> Iterator["TestClient"]:
    """TestClient with ``Authorization: Bearer <admin>`` pre-set on every
    request.  Uses default headers so you can call
    ``admin_client.get("/admin/some-route")`` without manually passing
    auth headers."""
    from fastapi.testclient import TestClient

    with TestClient(app, headers=admin_auth_headers) as c:
        yield c


@pytest.fixture
def supplier_client(app, supplier_auth_headers) -> Iterator["TestClient"]:
    """TestClient with ``Authorization: Bearer <supplier>`` pre-set."""
    from fastapi.testclient import TestClient

    with TestClient(app, headers=supplier_auth_headers) as c:
        yield c


@pytest.fixture
def customer_client(app, customer_auth_headers) -> Iterator["TestClient"]:
    """TestClient with ``Authorization: Bearer <customer>`` pre-set."""
    from fastapi.testclient import TestClient

    with TestClient(app, headers=customer_auth_headers) as c:
        yield c
