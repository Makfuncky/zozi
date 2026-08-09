"""Compatibility facade: re-exports db.database under the data.database name.

The recover/work reorg rewrote many modules to import from ``data.database``,
but that submodule was never created; the canonical module is ``db.database``.
This shim keeps the reorg import paths working without editing ~100 files.
"""
from db.database import *  # noqa: F401,F403
