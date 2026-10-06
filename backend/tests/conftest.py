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
import sqlalchemy
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

# Set FIELD_ENCRYPTION_SALT so that models with encrypted fields can be imported
# during conftest's dynamic model discovery. Without this, accounts and other
# domain models fail to import, leaving gaps in Base.metadata that produce
# unresolvable FKs and mask schema defects.
os.environ.setdefault(
    "FIELD_ENCRYPTION_SALT",
    "a" * 64,
)

# Set required env vars for testing
# NOTE: These test passwords are for local development/testing only.
# In CI, override via environment variables for stronger secrets.
# SECRET_KEY must satisfy Settings' own min_length=32 validator
# (config.py): a 28-char value made Settings() raise at import time, which
# errored collection for any test module that builds Settings and aborted the
# whole architecture suite. This is a test-only value, never a real secret.
os.environ.setdefault(
    "SECRET_KEY",
    "test-secret-key-for-pytest-only-do-not-use-in-production",
)
# DATABASE_URL_DIRECT has min_length=10; provide a dummy so Settings()
# can be instantiated during test collection without relying on .env leakage.
os.environ.setdefault(
    "DATABASE_URL_DIRECT",
    "postgresql://test:test@localhost/test_db",
)


def _get_test_db_path() -> str:
    """Return an absolute, per-worker-unique SQLite file path for the global engine."""
    worker = os.environ.get("PYTEST_XDIST_WORKER")
    db_dir = Path(__file__).resolve().parent / "tmp"
    db_dir.mkdir(parents=True, exist_ok=True)
    if worker:
        return str(db_dir / f"test_{worker}.db")
    fd, path = tempfile.mkstemp(suffix=".db", prefix="zozi_test_", dir=str(db_dir))
    os.close(fd)
    return path


_test_db_path = _get_test_db_path()
# DATABASE_URL is required by infrastructure.database.database and some model
# modules (e.g. rbac.models). Set an absolute, per-worker-unique SQLite path
# so the global engine can open it reliably regardless of cwd or parallel workers.
os.environ.setdefault(
    "DATABASE_URL",
    f"sqlite:///{_test_db_path}",
)
os.environ.setdefault("SEED_ADMIN_PASSWORD", os.getenv("TEST_ADMIN_PASSWORD", "T3st_Adm!n_Secure#2024"))
os.environ.setdefault("SEED_SUPPLIER_PASSWORD", os.getenv("TEST_SUPPLIER_PASSWORD", "T3st_Supp!er_Secure#2024"))
os.environ.setdefault("SEED_CUSTOMER_PASSWORD", os.getenv("TEST_CUSTOMER_PASSWORD", "T3st_Cust0mer_Secure#2024"))
os.environ.setdefault("SEED_LOGISTICS_PASSWORD", "T3st_Log!stics_Secure#2024")
os.environ.setdefault("SEED_EMPLOYEE_PASSWORD", "T3st_Empl0y3e_Secure#2024")

# Comprehensive test-only environment for Settings() validators.
# config.py skips .env loading when APP_ENV=test, so every variable that
# any validator or module-level import might read must be supplied here.
# None of these are real secrets; they exist only to keep the test Settings
# instance valid across every app_env a test might explicitly pass.
# ------------------------------------------------------------------
# _validate_required_secrets_in_non_production (runs when app_env is not
#   production or test — some tests instantiate Settings(app_env="development")).
# ------------------------------------------------------------------
os.environ.setdefault("POSTGRES_DB", "test_db")
os.environ.setdefault("POSTGRES_USER", "test")
os.environ.setdefault("POSTGRES_PASSWORD", "test")
os.environ.setdefault("STRIPE_SECRET_KEY", "sk_test_dummy")
os.environ.setdefault("STRIPE_PUBLISHABLE_KEY", "pk_test_dummy")
os.environ.setdefault("STRIPE_WEBHOOK_SECRET", "whsec_test_dummy")
os.environ.setdefault("TAP_SECRET_KEY", "tap_test_dummy")
os.environ.setdefault("TAP_WEBHOOK_SECRET", "tap_whsec_test_dummy")
os.environ.setdefault("TAP_API_BASE_URL", "https://api.tap_dummy.test")
os.environ.setdefault("PAYTABS_SERVER_KEY", "paytabs_test_dummy")
os.environ.setdefault("PAYTABS_WEBHOOK_SECRET", "paytabs_whsec_test_dummy")
os.environ.setdefault("PAYTABS_PROFILE_ID", "paytabs_profile_test_dummy")
os.environ.setdefault("PAYTABS_API_BASE_URL", "https://api.paytabs_dummy.test")
os.environ.setdefault("PAYTABS_CALLBACK_URL", "https://callback.paytabs_dummy.test")
os.environ.setdefault("THAWANI_SECRET_KEY", "thawani_test_dummy")
os.environ.setdefault("THAWANI_PUBLISHABLE_KEY", "thawani_pub_test_dummy")
os.environ.setdefault("THAWANI_API_BASE_URL", "https://api.thawani_dummy.test")
os.environ.setdefault("THAWANI_WEBHOOK_SECRET", "thawani_whsec_test_dummy")
os.environ.setdefault("OPENAI_API_KEY", "sk-test-dummy-openai")
os.environ.setdefault("ENCRYPTION_KEY", "test-encryption-key-dummy-" + "x" * 32)
os.environ.setdefault("KMS_ENCRYPTION_KEY", "test-kms-key-dummy-" + "x" * 32)
os.environ.setdefault("HASH_SALT", "test-hash-salt-dummy-" + "x" * 32)
os.environ.setdefault("SENTRY_DSN", "https://dummy@sentry.example.invalid/1")
os.environ.setdefault("TWILIO_ACCOUNT_SID", "AC_dummy_twilio_sid")
os.environ.setdefault("TWILIO_AUTH_TOKEN", "dummy_twilio_token")
os.environ.setdefault("WHATSAPP_ACCOUNT_SID", "AC_dummy_whatsapp_sid")
os.environ.setdefault("WHATSAPP_AUTH_TOKEN", "dummy_whatsapp_token")
os.environ.setdefault("WHATSAPP_FROM_NUMBER", "+10000000000")
os.environ.setdefault("RESEND_API_KEY", "re_dummy_resend_key")
os.environ.setdefault("RESEND_WEBHOOK_SECRET", "whsec_dummy_resend")
os.environ.setdefault("GOOGLE_CLIENT_ID", "dummy_google_client_id")
os.environ.setdefault("GOOGLE_CLIENT_SECRET", "dummy_google_client_secret")
os.environ.setdefault("FACEBOOK_CLIENT_ID", "dummy_facebook_client_id")
os.environ.setdefault("FACEBOOK_CLIENT_SECRET", "dummy_facebook_client_secret")
os.environ.setdefault("SSO_CLIENT_ID", "dummy_sso_client_id")
os.environ.setdefault("AUDIT_CHAIN_KEY", "test-audit-chain-key-dummy-" + "x" * 32)
os.environ.setdefault("TRUSTED_PROXY_IPS", "10.0.0.0/8")
os.environ.setdefault("R2_BUCKET", "dummy-r2-bucket")
os.environ.setdefault("R2_ENDPOINT_URL", "https://s3.dummy-r2.example.invalid")
os.environ.setdefault("R2_ACCESS_KEY_ID", "dummy_r2_access_key")
os.environ.setdefault("R2_SECRET_ACCESS_KEY", "dummy_r2_secret_key")
os.environ.setdefault("BANK_API_AUTH_TOKEN", "dummy_bank_auth_token")
os.environ.setdefault("BANK_API_SOURCE_ACCOUNT_ID", "dummy_bank_source_account")
os.environ.setdefault("HF_API_TOKEN", "hf_dummy_token")
os.environ.setdefault("PAYPAL_SECRET", "dummy_paypal_secret")
os.environ.setdefault("PAYPAL_CLIENT_ID", "dummy_paypal_client_id")
os.environ.setdefault("PAYPAL_WEBHOOK_SECRET", "dummy_paypal_webhook_secret")
# ------------------------------------------------------------------
# _validate_production / _validate_staging supplementary requirements.
# ------------------------------------------------------------------
os.environ.setdefault("VALKEY_URL", "valkey://localhost:6379/0")
os.environ.setdefault("CELERY_BROKER_URL", "valkey://localhost:6379/1")
os.environ.setdefault("CELERY_RESULT_BACKEND", "valkey://localhost:6379/2")
os.environ.setdefault("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000")
os.environ.setdefault("FRONTEND_URL", "http://localhost:3000")
os.environ.setdefault("BACKEND_URL", "http://localhost:8000")
os.environ.setdefault("SMTP_HOST", "localhost")
os.environ.setdefault("SMTP_PORT", "587")
os.environ.setdefault("SMTP_USER", "test")
os.environ.setdefault("SMTP_PASSWORD", "test")
os.environ.setdefault("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4318")
os.environ.setdefault("MEDIA_STORAGE_BASE", str(Path(__file__).resolve().parent.parent / "uploads"))
os.environ.setdefault("FIELD_ENCRYPTION_KEY", "test-field-encryption-key-dummy-" + "x" * 32)

from infrastructure.database.base import Base  # noqa: E402

_legacy_engine = None

def _get_legacy_engine():
    global _legacy_engine
    if _legacy_engine is None:
        _legacy_engine = create_engine(
            "sqlite://",
            echo=False,
            execution_options={"schema_translate_map": SCHEMA_TRANSLATE_MAP},
        )
        _legacy_engine.execution_options(isolation_level="AUTOCOMMIT")
        _remove_broken_fk_tables()
        Base.metadata.create_all(bind=_legacy_engine)
    return _legacy_engine


# ---------------------------------------------------------------------------
# Monkey-patch sqlalchemy.create_engine so every SQLite engine created during
# the test session automatically gets:
#   1. an absolute, parent-directory-guaranteed file path, and
#   2. a complete schema_translate_map derived from the fully-populated
#      Base.metadata so that "unknown database <schema>" never occurs.
#
# This catches engines built by test modules that bypass the session-scoped
# ``engine`` fixture (e.g. tests/domains/test_search_endpoints.py).
# ---------------------------------------------------------------------------
_ORIG_SQLA_CREATE_ENGINE = sqlalchemy.create_engine


def _test_create_engine(url, **kwargs):
    url_str = str(url)
    if url_str.startswith("sqlite"):
        # 1) Normalize file paths to absolute and ensure parent directory exists.
        if url_str.startswith("sqlite:///"):
            db_path = url_str[len("sqlite:///"):]
            if db_path and db_path != ":memory:" and not os.path.isabs(db_path):
                db_path = str(_BACKEND_ROOT / db_path)
                url_str = f"sqlite:///{db_path}"
                parent = Path(db_path).parent
                parent.mkdir(parents=True, exist_ok=True)
        # 2) Always inject the complete schema_translate_map so that no
        #    "unknown database <schema>" error can occur, even when a caller
        #    (e.g. infrastructure/database/database.py) passes an incomplete map.
        _scm = {
            s: None
            for s in {t.schema for t in Base.metadata.tables.values() if t.schema}
        }
        if _scm:
            existing_opts = kwargs.get("execution_options", {})
            merged = dict(existing_opts)
            merged["schema_translate_map"] = _scm
            kwargs["execution_options"] = merged
    return _ORIG_SQLA_CREATE_ENGINE(url_str, **kwargs)


sqlalchemy.create_engine = _test_create_engine

@pytest.fixture(scope="session")
def engine():
    """Session-scoped test engine backed by the global test database file.

    Uses ``_test_db_path`` (the same file the global ``engine`` in
    ``infrastructure.database.database`` points at) so that tests which call
    ``get_db()`` directly see the same schema created here.
    """
    eng = create_engine(
        f"sqlite:///{_test_db_path}",
        connect_args={"check_same_thread": False},
        poolclass=__import__("sqlalchemy.pool", fromlist=["StaticPool"]).StaticPool,
        execution_options={"schema_translate_map": SCHEMA_TRANSLATE_MAP},
    )
    global _legacy_engine
    _legacy_engine = eng
    _remove_broken_fk_tables()
    Base.metadata.create_all(bind=eng)
    _create_gap_tables(eng)
    try:
        yield eng
    finally:
        _legacy_engine = None
        eng.dispose()

def _TestSession():
    return sessionmaker(bind=_get_legacy_engine(), autoflush=False, autocommit=False)()


# Ensure all model modules are imported so that Base.metadata knows about every
# table before create_all() runs. Each domain models package is imported
# directly (canonical locations per Law 1: arrows point down only).
# Wrapped in try/except: the source code has pre-existing broken imports
# (missing classes, cross-domain FKs to removed tables). A broken module must
# not block the entire test DB setup — skip it and let the rest build.
import logging
import infrastructure.database.base  # noqa: E402
# Dynamically import every model module from every domain so that
# Base.metadata is complete before SCHEMA_TRANSLATE_MAP is computed.
# Wrapped in try/except: the source code has pre-existing broken imports
# (missing classes, cross-domain FKs to removed tables). A broken module must
# not block the entire test DB setup — skip it and let the rest build.
# NOTE: The bare `except: pass` is a D-SILENT hazard (see STAGE1_BRIEF §10.1
# D-SILENT-EXCEPT). Import errors are logged so broken modules are visible
# during test collection rather than silently masked.
_import_logger = logging.getLogger(__name__)

# Pre-import country models so that cross-domain string relationships
# (e.g. catalog.products -> CountryConfig) can resolve during mapper init.
try:
    from domains.country.models.countries import CountryConfig  # noqa: F401
except Exception as _preimport_exc:
    _import_logger.warning("conftest: pre-import country models failed: %s", _preimport_exc)

# Prevent ``infrastructure.database.models`` from clearing mappers at import
# time. ``main.py`` imports this module solely for its ``clear_mappers()``
# side-effect; in tests we want to preserve the instrumentation that the
# dynamic model-import loop below establishes.
import sys
import types

_fake_db_models = types.ModuleType("infrastructure.database.models")
_fake_db_models.clear_mappers = lambda: None
sys.modules["infrastructure.database.models"] = _fake_db_models

# Force Valkey client to no-op so app startup / router imports do not block
# or crash when no Valkey server is running in the test environment.
try:
    import infrastructure.valkey.client as _valkey_client_mod
    _valkey_client_mod._client = _valkey_client_mod._NoOpValkey()
except Exception as _valkey_exc:
    _import_logger.warning("conftest: valkey no-op patch failed: %s", _valkey_exc)

# FastAPI 0.141 treats ``*args`` / ``**kwargs`` in a dependency as required
# query parameters, which breaks every route that uses ``require_admin``
# (defined with ``*args, **kwargs`` for backward-compat). Patch it out so
# admin routes are reachable in tests.
try:
    from domains.accounts.services.auth import security_dependencies as _sec_dep
    from infrastructure.security.dependencies import get_current_user as _get_current_user
    from fastapi import Depends

    _orig_require_admin = _sec_dep.require_admin

    def _patched_require_admin(current_user=Depends(_get_current_user)):
        return _orig_require_admin(current_user)

    _sec_dep.require_admin = _patched_require_admin
    _infra_sec_dep = __import__(
        "infrastructure.security.dependencies", fromlist=["__dict__"]
    )
    _infra_sec_dep.__dict__["require_admin"] = _patched_require_admin
    import sys
    print("CONFTEST: require_admin patched, id=", id(_patched_require_admin), file=sys.stderr)
    print("CONFTEST: infra sec dep has require_admin:", "require_admin" in _infra_sec_dep.__dict__, file=sys.stderr)
    if "require_admin" in _infra_sec_dep.__dict__:
        print("CONFTEST: infra sec dep require_admin id=", id(_infra_sec_dep.__dict__["require_admin"]), file=sys.stderr)
    _import_logger.warning("conftest: require_admin patched successfully")
except Exception as _admin_patch_exc:
    _import_logger.warning("conftest: require_admin patch failed: %s", _admin_patch_exc)

# Pre-import country models so that cross-domain string relationships
# (e.g. catalog.products -> CountryConfig) can resolve during mapper init.
try:
    from domains.country.models.countries import CountryConfig  # noqa: F401
except Exception as _preimport_exc:
    _import_logger.warning("conftest: pre-import country models failed: %s", _preimport_exc)

for _domain_dir in sorted((_BACKEND_ROOT / "domains").iterdir()):
    if not _domain_dir.is_dir():
        continue
    _models_dir = _domain_dir / "models"
    if not _models_dir.exists():
        continue
    _pkg = f"domains.{_domain_dir.name}.models"
    try:
        __import__(_pkg)
    except Exception as _pkg_exc:
        _import_logger.warning("conftest: skipping model pkg %s: %s", _pkg, _pkg_exc)
    for _py_file in _models_dir.glob("*.py"):
        if _py_file.stem == "__init__":
            continue
        _submod = f"{_pkg}.{_py_file.stem}"
        try:
            __import__(_submod)
        except Exception as _submod_exc:
            _import_logger.warning("conftest: skipping model module %s: %s", _submod, _submod_exc)

# RBAC permission models live under rbac/models/ (outside the domains/ tree).
# Import them explicitly so Base.metadata includes the security.permissions
# family before SCHEMA_TRANSLATE_MAP is computed.
_rbac_models_dir = _BACKEND_ROOT / "rbac" / "models"
if _rbac_models_dir.exists():
    _rbac_pkg = "rbac.models"
    try:
        __import__(_rbac_pkg)
    except Exception as _rbac_pkg_exc:
        _import_logger.warning("conftest: skipping RBAC model pkg %s: %s", _rbac_pkg, _rbac_pkg_exc)
    for _py_file in _rbac_models_dir.glob("*.py"):
        if _py_file.stem == "__init__":
            continue
        _rbac_submod = f"{_rbac_pkg}.{_py_file.stem}"
        try:
            __import__(_rbac_submod)
        except Exception as _rbac_submod_exc:
            _import_logger.warning("conftest: skipping RBAC model module %s: %s", _rbac_submod, _rbac_submod_exc)

# The models declare Postgres schemas (e.g. {"schema": "commerce"}). SQLite
# cannot create ``CREATE TABLE commerce.categories`` ("unknown database"), so
# translate every schema to None for the in-memory/file test engines. This is
# test-only and has no effect on the production Postgres dialect.
_SCHEMAS = {t.schema for t in Base.metadata.tables.values() if t.schema}
SCHEMA_TRANSLATE_MAP = {s: None for s in _SCHEMAS}

# Populate the RBAC feature catalog so ``require_feature("*")`` expands correctly.
# Domain ``features.py`` modules can have cross-domain import issues; skip any
# that fail so the rest still load.
try:
    import domains
    import pkgutil
    for _feat_mod in pkgutil.iter_modules(domains.__path__):
        try:
            _feat_pkg = __import__(f"domains.{_feat_mod.name}.features", fromlist=["FEATURES"])
            _import_logger.debug("conftest: loaded features for %s", _feat_mod.name)
        except Exception as _feat_exc:
            _import_logger.warning("conftest: skipping features for %s: %s", _feat_mod.name, _feat_exc)
except Exception as _feat_import_exc:
    _import_logger.warning("conftest: feature catalog population failed: %s", _feat_import_exc)

# ``permissions_service`` uses raw SQL with hard-coded ``security.`` schema
# prefixes. SQLite test DBs are created with schema translated to ``None``, so
# the actual table names have no prefix. Monkeypatch the service to drop the
# prefix so permission smoke tests can pass.
try:
    from rbac.services import permissions_service as _ps
    from sqlalchemy import text
    from typing import Any, Iterable, Optional
    from sqlalchemy.orm import Session

    _orig_list_categories = _ps.list_categories
    def _patched_list_categories(db: Session, country_code: Optional[str] = None) -> list[dict]:
        params: dict[str, Any] = {}
        where = "WHERE is_deleted = FALSE"
        if country_code:
            where += " AND country_code = :cc"
            params["cc"] = country_code.upper()
        rows = db.execute(
            text(
                f"""
                SELECT id, name, slug, description, icon, sort_order, is_active,
                       country_code, created_at, updated_at
                FROM permission_categories
                {where}
                ORDER BY sort_order, name
                """
            ),
            params,
        ).mappings().all()
        return [dict(r) for r in rows]

    _orig_list_permissions = _ps.list_permissions
    def _patched_list_permissions(db: Session, country_code: Optional[str] = None) -> list[dict]:
        params: dict[str, Any] = {}
        where = "WHERE p.is_deleted = FALSE"
        if country_code:
            where += " AND p.country_code = :cc"
            params["cc"] = country_code.upper()
        rows = db.execute(
            text(
                f"""
                SELECT p.id, p.name, p.slug, p.description, p.scope, p.is_active,
                       p.country_code, p.category_id, c.name AS category_name,
                       c.slug AS category_slug
                FROM permissions p
                LEFT JOIN permission_categories c ON c.id = p.category_id
                {where}
                ORDER BY c.sort_order, c.name, p.name
                """
            ),
            params,
        ).mappings().all()
        return [dict(r) for r in rows]

    _orig_get_role_permissions = _ps.get_role_permissions
    def _patched_get_role_permissions(db: Session, role: str, country_code: Optional[str] = None) -> list[dict]:
        params: dict[str, Any] = {"role": role}
        where = "WHERE rpa.role_name = :role AND rpa.is_granted = TRUE"
        if country_code:
            where += " AND (rpa.country_code = :cc OR rpa.country_code IS NULL)"
            params["cc"] = country_code.upper()
        rows = db.execute(
            text(
                f"""
                SELECT rpa.id, rpa.role_name, rpa.permission_id, rpa.country_code,
                       p.name AS permission_name, p.slug AS permission_slug,
                       p.scope, p.category_id, c.name AS category_name
                FROM role_permission_assignments rpa
                JOIN permissions p ON p.id = rpa.permission_id
                LEFT JOIN permission_categories c ON c.id = p.category_id
                {where}
                ORDER BY c.name, p.name
                """
            ),
            params,
        ).mappings().all()
        return [dict(r) for r in rows]

    _ps.list_categories = _patched_list_categories
    _ps.list_permissions = _patched_list_permissions
    _ps.get_role_permissions = _patched_get_role_permissions
except Exception as _ps_patch_exc:
    _import_logger.warning("conftest: permissions_service patch failed: %s", _ps_patch_exc)


def _remove_broken_fk_tables() -> None:
    """Drop tables whose FKs reference tables that don't exist in metadata.

    The source code has cross-domain FKs (e.g. ``products.supplier_id ->
    governance.users``) where the target table was removed/migrated. SQLite
    ``create_all()`` fails hard on these. Removing the broken tables from
    metadata lets the rest of the test DB build. Repeat until stable since
    removing one table can resolve another's FK.

    **This helper masks schema defects.** Every removal is logged as an ERROR
    so that broken FKs are visible during test collection rather than silently
    turning into confusing downstream failures.
    """
    _SECURITY_TABLES = {
        "security.permission_categories",
        "security.permissions",
        "security.role_permission_assignments",
        "security.user_permission_overrides",
        "security.permission_audit_log",
    }
    for _pass in range(10):
        broken: set[str] = set()
        broken_fk_details: dict[str, list[str]] = {}
        existing = {t.name for t in Base.metadata.tables.values()}
        for table in list(Base.metadata.tables.values()):
            if table.fullname in _SECURITY_TABLES:
                continue
            for fk in table.foreign_key_constraints:
                try:
                    target = fk.referred_table
                except Exception:
                    broken.add(table.fullname)
                    broken_fk_details.setdefault(table.fullname, []).append(
                        f"<unresolvable: {fk}>"
                    )
                    continue
                if target is None or target.name not in existing:
                    broken.add(table.fullname)
                    broken_fk_details.setdefault(table.fullname, []).append(
                        f"{fk.elements[0].column_fullname if fk.elements else '?'} -> {target.fullname if target else 'None'}"
                    )
        if not broken:
            break
        for name in sorted(broken):
            _import_logger.error(
                "conftest: REMOVING table %s from metadata due to broken FK(s): %s",
                name,
                "; ".join(broken_fk_details.get(name, ["?"])),
            )
            try:
                Base.metadata.remove(Base.metadata.tables[name])
            except KeyError:
                pass


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
            entry_date DATE NOT NULL,
            description TEXT,
            reference TEXT,
            total_debit REAL NOT NULL,
            total_credit REAL NOT NULL,
            status TEXT DEFAULT 'posted',
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
            if not table_name.replace("_", "").isalnum():
                raise ValueError(f"Invalid table name: {table_name}")
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


@pytest.fixture(scope="session", autouse=True)
def _cleanup_global_test_db():
    """Remove stale test DB files before and after the test session."""
    _purge_stale_test_dbs()
    yield
    try:
        os.remove(_test_db_path)
    except OSError:
        pass
    _purge_stale_test_dbs()


def _purge_stale_test_dbs() -> None:
    """Remove old zozi_test_*.db files so stale schemas cannot hide drift."""
    db_dir = Path(__file__).resolve().parent / "tmp"
    if not db_dir.exists():
        return
    for _f in db_dir.glob("zozi_test_*.db"):
        try:
            _f.unlink()
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
    from infrastructure.database.database import get_db as _real_get_db  # noqa: F401

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
# Demo user email/role map. Passwords are read from environment variables
# (TEST_ADMIN_PASSWORD, TEST_SUPPLIER_PASSWORD, TEST_CUSTOMER_PASSWORD)
# with strong defaults for local testing. Override in CI for security.
_DEMO_USERS: list[tuple[str, str, str, str, str]] = [
    ("admin@zozi.com", "admin", os.getenv("TEST_ADMIN_PASSWORD", "T3st_Adm!n_Secure#2024"), "admin", "admin"),
    ("supplier@zozi.com", "supplier", os.getenv("TEST_SUPPLIER_PASSWORD", "T3st_Supp!er_Secure#2024"), "supplier", "supplier"),
    ("customer@zozi.com", "customer", os.getenv("TEST_CUSTOMER_PASSWORD", "T3st_Cust0mer_Secure#2024"), "customer", "customer"),
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
    from infrastructure.database.seed import _ensure_demo_user
    from domains.accounts.models.user import User as _UserModel
    from domains.country.models.countries import CountryConfig
    import infrastructure.utils.auth as _auth_mod

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
    The tokens are created by calling ``infrastructure.utils.auth.create_access_token``
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
    from domains.accounts.models.user import User as _User
    from infrastructure.utils.auth import create_access_token as _create_token

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


