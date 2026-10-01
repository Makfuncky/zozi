"""Shared fixtures for orders-domain tests."""
from __future__ import annotations

import os

# orders_service transitively imports the encryption stack, which requires
# FIELD_ENCRYPTION_SALT to be set at import time.
os.environ["FIELD_ENCRYPTION_SALT"] = "a" * 64
print("DEBUG: orders conftest loaded, FIELD_ENCRYPTION_SALT set to", os.environ.get("FIELD_ENCRYPTION_SALT", "NOT SET"))
