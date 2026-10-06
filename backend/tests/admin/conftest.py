"""Fix DATABASE_URL and re-apply conftest patches for admin tests.

tests/conftest.py seeds DATABASE_URL_DIRECT but not DATABASE_URL, and a
domain-model import caches Settings() with database_url="".  Force a valid
sync DATABASE_URL and patch the cached settings object so that modules which
import database.py later can instantiate a working engine.

The parent conftest also tries to patch ``require_admin`` and the RBAC
permissions service for SQLite test compat, but those patches fail during
parent import because database.py aborts before the patched settings take
effect.  Re-apply them here after the settings fix.

Finally, override the ``engine`` fixture so that security tables with broken
FKs (e.g. ``role_permission_assignments.granted_by -> governance.users``)
are removed before ``create_all`` and then re-created manually without the
broken constraints.
"""
import os
import logging
from typing import Optional

try:
    import sentry_sdk

    sentry_sdk.flush = lambda *args, **kwargs: None
    print("ADMIN CONFTEST: sentry_sdk.flush monkeypatched", flush=True)
except Exception as _sentry_patch_exc:
    print("ADMIN CONFTEST: sentry_sdk patch failed:", _sentry_patch_exc, flush=True)

os.environ["SENTRY_DSN"] = ""
import pytest
from sqlalchemy import create_engine, text, Integer
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import Session
from sqlalchemy import text as sa_text

# Use the absolute path already set by the parent conftest so the DB file
# resolves the same way regardless of cwd.
_PARENT_DB_URL = os.environ.get("DATABASE_URL", "sqlite:///test.db")
os.environ.setdefault("DATABASE_URL", _PARENT_DB_URL)
os.environ.setdefault("VALKEY_URL", "valkey://localhost:6379")
import config as _config
if getattr(_config, "settings", None) is not None:
    _config.settings.database_url = os.environ["DATABASE_URL"]
    _config.settings.valkey_url = "valkey://localhost:6379"

# Re-apply require_admin patch (parent conftest import of security_dependencies
# triggered database.py before DATABASE_URL was available).
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
except Exception as _admin_patch_exc:
    logging.getLogger(__name__).warning("admin conftest: require_admin patch failed: %s", _admin_patch_exc)

# Re-apply RBAC model imports (parent conftest import of rbac.models
# triggered database.py before DATABASE_URL was available).
try:
    import rbac.models
    from rbac.models.permission_entities import PermissionCategory, Permission
except Exception as _rbac_pkg_exc:
    logging.getLogger(__name__).warning("admin conftest: skipping RBAC model pkg %s: %s", "rbac", _rbac_pkg_exc)
try:
    from rbac.models.permission_entities import PermissionCategory
except Exception as _rbac_submod_exc:
    logging.getLogger(__name__).warning("admin conftest: skipping RBAC model module %s: %s", "permission_entities", _rbac_submod_exc)

# Re-apply permissions_service patch (parent conftest import of
# rbac.services.permissions_service triggered database.py before
# DATABASE_URL was available).
try:
    from rbac.services import permissions_service as _ps
    from typing import Any, Iterable, Optional

    _orig_list_categories = _ps.list_categories
    def _patched_list_categories(db: Session, country_code: Optional[str] = None) -> list[dict]:
        params: dict[str, Any] = {}
        where = "WHERE is_deleted = FALSE"
        if country_code:
            where += " AND country_code = :cc"
            params["cc"] = country_code.upper()
        rows = db.execute(
            sa_text(
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
            sa_text(
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
            sa_text(
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
    logging.getLogger(__name__).warning("admin conftest: permissions_service patch failed: %s", _ps_patch_exc)

# Override the session-scoped engine fixture for admin tests so that
# security tables with broken FKs (e.g. granted_by -> governance.users)
# are removed before create_all and then re-created manually without the
# broken constraints.
@pytest.fixture(scope="session")
def engine(db_file: str):
    import tests.conftest as _parent_conftest
    from infrastructure.database.base import Base

    eng = create_engine(
        f"sqlite:///{db_file}",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        execution_options={"schema_translate_map": _parent_conftest.SCHEMA_TRANSLATE_MAP},
    )

    # Remove security tables whose FKs reference missing governance.users
    for _tbl in ("role_permission_assignments", "user_permission_overrides", "permission_audit_log"):
        _full = f"security.{_tbl}"
        if _full in Base.metadata.tables:
            Base.metadata.remove(Base.metadata.tables[_full])

    Base.metadata.create_all(bind=eng)
    _parent_conftest._create_gap_tables(eng)

    # Re-create the removed security tables without broken FKs
    with eng.connect() as conn:
        conn.execute(text("PRAGMA foreign_keys = OFF"))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS role_permission_assignments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                uuid TEXT,
                version INTEGER NOT NULL DEFAULT 1,
                is_deleted BOOLEAN DEFAULT FALSE,
                deleted_at TIMESTAMP,
                deleted_by INTEGER,
                created_by INTEGER,
                updated_by INTEGER,
                role_name TEXT NOT NULL,
                permission_id INTEGER NOT NULL REFERENCES permissions(id),
                country_code TEXT REFERENCES country_configs(code),
                is_granted BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS user_permission_overrides (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                uuid TEXT,
                version INTEGER NOT NULL DEFAULT 1,
                is_deleted BOOLEAN DEFAULT FALSE,
                deleted_at TIMESTAMP,
                deleted_by INTEGER,
                created_by INTEGER,
                updated_by INTEGER,
                user_id INTEGER NOT NULL REFERENCES users(id),
                permission_id INTEGER NOT NULL REFERENCES permissions(id),
                country_code TEXT REFERENCES country_configs(code),
                is_granted BOOLEAN DEFAULT TRUE,
                expires_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS permission_audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                uuid TEXT,
                actor_id INTEGER NOT NULL REFERENCES users(id),
                action TEXT NOT NULL,
                target_user_id INTEGER REFERENCES users(id),
                target_role TEXT,
                permission_id INTEGER REFERENCES permissions(id),
                country_code TEXT,
                details TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        conn.execute(text("PRAGMA foreign_keys = ON"))
        conn.commit()

    _parent_conftest._legacy_engine = eng
    try:
        yield eng
    finally:
        _parent_conftest._legacy_engine = None
        eng.dispose()


try:
    import sentry_sdk

    sentry_sdk.flush = lambda *args, **kwargs: None
except Exception:
    pass
