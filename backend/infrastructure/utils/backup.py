"""Backwards-compatible re-export shim.

``get_backup_manager`` now lives in ``infrastructure.storage.backup`` (per the
platform storage layout). This module keeps legacy import sites working.
"""
from __future__ import annotations

from infrastructure.storage.backup import (  # noqa: F401
    BackupManager,
    get_backup_manager,
)

__all__ = ["BackupManager", "get_backup_manager"]
