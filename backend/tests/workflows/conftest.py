"""Fix DATABASE_URL and stripe loading for workflow tests.

tests/conftest.py seeds DATABASE_URL_DIRECT but not DATABASE_URL, and a
domain-model import caches Settings() with database_url="".  Force a valid
sync DATABASE_URL and patch the cached settings object so that modules which
import database.py later can instantiate a working engine.

Also eagerly load the Stripe SDK because providers.payments.stripe_sdk uses
lazy loading and leaves stripe=None at module level. payment_engine.py tries
to set stripe.api_key at import time, which crashes customer finance/orders
router loading — a regression that turns customer endpoints into 404s.
"""
import os

# Use the absolute path already set by the parent conftest so the DB file
# resolves the same way regardless of cwd.
_PARENT_DB_URL = os.environ.get("DATABASE_URL")
if _PARENT_DB_URL:
    os.environ.setdefault("DATABASE_URL", _PARENT_DB_URL)
else:
    os.environ.setdefault("DATABASE_URL", "sqlite:///test.db")
os.environ.setdefault("VALKEY_URL", "valkey://localhost:6379")
import config as _config
if getattr(_config, "settings", None) is not None:
    _config.settings.database_url = os.environ["DATABASE_URL"]
    _config.settings.valkey_url = "valkey://localhost:6379"

import providers.payments.stripe_sdk as _stripe_sdk
_stripe_sdk._load_stripe()
