import os
import sys

BACKEND = r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend"
if BACKEND not in sys.path:
    sys.path.insert(0, BACKEND)

os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("SECRET_KEY", "smoke-secret")
os.environ.setdefault("CSRF_DISABLED", "true")

from db.base import Base  # noqa: E402
import models  # noqa: E402  (registers all tables)
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402
from tests.conftest import (  # noqa: E402
    _qualify_foreign_keys,
    _SCHEMA_TRANSLATE_MAP,
    _create_gap_tables,
)

_qualify_foreign_keys(Base.metadata)
eng = create_engine(
    "sqlite://",
    poolclass=StaticPool,
    execution_options={"schema_translate_map": _SCHEMA_TRANSLATE_MAP},
)
Base.metadata.create_all(bind=eng)
_create_gap_tables(eng)
print("CREATE_ALL OK -> tables:", len(Base.metadata.tables))
