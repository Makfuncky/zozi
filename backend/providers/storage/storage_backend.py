"""Object-storage abstraction (Phase 1 of the scaling plan).

This module re-exports the canonical storage implementation from
``infrastructure.storage.storage`` to maintain backward compatibility.
"""
from __future__ import annotations

from infrastructure.storage.storage import (
    StorageBackend,
    LocalStorage,
    S3Storage,
    get_storage,
    storage,
    UPLOADS_DIR,
)

HAS_STORAGE_BACKEND = True

__all__ = [
    "StorageBackend",
    "LocalStorage",
    "S3Storage",
    "get_storage",
    "storage",
    "UPLOADS_DIR",
]
