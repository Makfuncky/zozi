"""Storage utility re-export.

Provides a thin re-export of the canonical storage backend instance from
``infrastructure.storage.storage`` so that domain services can import from
``infrastructure.utils.storage`` without reaching into the storage subsystem
directly.
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

__all__ = [
    "StorageBackend",
    "LocalStorage",
    "S3Storage",
    "get_storage",
    "storage",
    "UPLOADS_DIR",
]
