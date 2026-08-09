"""Compatibility facade: re-exports db.schemas under the data.schemas name.

The recover/work reorg rewrote many modules to import from ``data.schemas``,
but that submodule was never created; the canonical module is ``db.schemas``.
This shim keeps the reorg import paths working without editing ~100 files.
"""
from db.schemas import *  # noqa: F401,F403
