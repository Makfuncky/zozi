"""Backward-compat shim — canonical location is backend/config.py.

Re-exports every name defined by the canonical module so existing
``from infrastructure.utils.config import settings`` imports keep working
(Law 26 — temporary re-exports for relocated files).

No debug output here: this module is imported on every process boot, and
Law 58 forbids ``print()``/``traceback.print_stack()`` in production code.
"""
from config import *  # noqa: F401,F403
