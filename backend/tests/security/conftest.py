"""Fixtures for RBAC security tests under tests/security/."""
from __future__ import annotations

import os
import sys
import pytest
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql.schema import ForeignKeyConstraint

# tests/conftest.py seeds DATABASE_URL_DIRECT but not DATABASE_URL, and a
# domain-model import caches Settings() with database_url="".  Force a valid
# sync DATABASE_URL and patch the cached settings object so that modules which
# import database.py later can instantiate a working engine.
os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("VALKEY_URL", "valkey://localhost:6379")

# Encryption env vars must be set before config/Settings is imported, otherwise
# field_encryptor is created with empty values and remains None for the vault
# tests that exercise enc:: values.
os.environ.setdefault("FIELD_ENCRYPTION_KEY", "x" * 64)
os.environ.setdefault("FIELD_ENCRYPTION_SALT", "a" * 64)
os.environ.setdefault("ZOZI_VAULT_MASTER_KEY", "v" * 64)

import config as _config  # noqa: E402
if getattr(_config, "settings", None) is not None:
    _config.settings.database_url = "sqlite://"
    _config.settings.valkey_url = "valkey://localhost:6379"
    _config.settings.field_encryption_key = "x" * 64
    _config.settings.field_encryption_salt = "a" * 64

# tests/conftest.py may have left a broken rbac package in sys.modules after
# its Settings() import failure.  Clear it so the real models can be imported.
for _rbac_key in ("rbac", "rbac.models"):
    sys.modules.pop(_rbac_key, None)

# Re-import rbac.models now that DATABASE_URL and settings are patched.
import rbac.models  # noqa: E402

# The RBAC permission models carry FKs to tables that either do not exist
# (governance.users) or are created later by other domains.  Drop those FKs
# from the SQLAlchemy metadata so Base.metadata.create_all() can build the
# test schema without raising NoReferencedTableError.
from rbac.models.permission_entities import (  # noqa: E402
    PermissionAuditLog,
    RolePermissionAssignment,
    UserPermissionOverride,
)

_BROKEN_FK_TABLES = [
    RolePermissionAssignment.__table__,
    UserPermissionOverride.__table__,
    PermissionAuditLog.__table__,
]

for _tbl in _BROKEN_FK_TABLES:
    for _fk in list(_tbl.foreign_keys):
        _tbl.foreign_keys.remove(_fk)
    for _con in list(_tbl.constraints):
        if isinstance(_con, ForeignKeyConstraint):
            _tbl.constraints.remove(_con)

from tests.rbac.fixtures import seed_permission_categories


@pytest.fixture(scope="session", autouse=True)
def _seed_rbac_categories(engine):
    """Seed ``security.permission_categories`` so RBACService.grant() has a
    valid ``category_id=1`` target (hardcoded in ``rbac/service.py``)."""
    from infrastructure.database.base import Base
    from rbac.models.permission_entities import PermissionCategory

    Base.metadata.create_all(bind=engine, tables=[PermissionCategory.__table__], checkfirst=True)

    TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    session = TestingSession()
    try:
        seed_permission_categories(session)
        session.commit()
    finally:
        session.close()
    yield
