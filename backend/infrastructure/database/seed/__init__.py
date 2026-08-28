"""Split seed package — originally seed.py."""
from __future__ import annotations

from ._common import seed_data, _ensure_demo_user, _seed_password  # noqa: F401

__all__ = ["seed_data", "_ensure_demo_user", "_seed_password"]
