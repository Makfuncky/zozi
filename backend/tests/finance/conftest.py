"""Finance test-suite conftest: set required env vars before any service import."""
from __future__ import annotations

import os
import sys

# finance services import ``providers`` -> ``infrastructure.utils.config`` at
# module load time; config validates ``database_url_direct`` (min 10 chars).
# Override any .env values so collection succeeds without a real Postgres.
# Use the absolute path already set by the parent conftest so the DB file
# resolves the same way regardless of cwd.
_PARENT_DB_URL = os.environ.get("DATABASE_URL", "sqlite:///test.db")
os.environ["DATABASE_URL"] = _PARENT_DB_URL
os.environ["DATABASE_URL_DIRECT"] = os.environ.get("DATABASE_URL_DIRECT", _PARENT_DB_URL)
os.environ["APP_ENV"] = "test"
# Field encryption requires a stable salt in non-production environments.
os.environ.setdefault("FIELD_ENCRYPTION_SALT", "a" * 64)
print(f"DEBUG conftest: DATABASE_URL={os.environ.get('DATABASE_URL')!r}")
print(f"DEBUG conftest: DATABASE_URL_DIRECT={os.environ.get('DATABASE_URL_DIRECT')!r}")
print(f"DEBUG conftest: FIELD_ENCRYPTION_SALT={os.environ.get('FIELD_ENCRYPTION_SALT')!r}")

# The parent conftest (backend/tests/conftest.py) may import modules that
# instantiate ``settings`` before we set DATABASE_URL.  Force the cached
# settings object to pick up the SQLite URLs we just configured.
for _mod_name in ("config", "infrastructure.utils.config"):
    _mod = sys.modules.get(_mod_name)
    if _mod is not None and hasattr(_mod, "settings"):
        try:
            _mod.settings.database_url = _PARENT_DB_URL
            _mod.settings.database_url_direct = os.environ.get("DATABASE_URL_DIRECT", _PARENT_DB_URL)
        except Exception:
            pass

# ``payment_engine`` imports ``stripe`` from ``providers.payments.stripe_sdk``
# and unconditionally sets ``stripe.api_key`` at module load time.  The
# provider shim sets ``stripe = None`` when the SDK is absent, so we inject a
# lightweight stub here so collection succeeds without the real SDK.
class _FakeStripe:
    api_key = ""


try:
    import providers.payments.stripe_sdk as _stripe_sdk
    _stripe_sdk.stripe = _FakeStripe()  # type: ignore[attr-defined]
    _stripe_sdk.HAS_STRIPE = True  # type: ignore[attr-defined]
except Exception:
    pass
