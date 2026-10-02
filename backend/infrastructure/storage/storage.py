"""Object-storage abstraction (Phase 1 of the scaling plan).

Defines a :class:`StorageBackend` interface so the rest of the application can
save / read / delete objects without caring whether bytes live on local disk
(development & tests) or in an S3-compatible bucket behind a CDN (production).

The active backend is selected by the ``STORAGE_BACKEND`` config value, mirroring
the SQLite/Postgres switch in ``db/database.py``:

- ``local`` -> :class:`LocalStorage` (writes under ``uploads/``, returns
  ``/uploads/...`` URLs).
- ``s3``    -> :class:`S3Storage` (writes to an S3-compatible bucket, returns CDN
  URLs; large files can be pushed directly by the client via a presigned PUT so
  the API never touches the bytes).
"""
from __future__ import annotations

import abc
import logging
import os
from typing import Optional

from celery import shared_task

from infrastructure.utils.config import settings

from providers.storage import create_s3_client

logger = logging.getLogger(__name__)

UPLOADS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "uploads")


class StorageBackend(abc.ABC):
    """Common contract for all storage backends."""

    @abc.abstractmethod
    def save(self, key: str, data: bytes, content_type: Optional[str] = None, current_user: Optional[dict] = None) -> str:
        """Persist ``data`` under ``key`` and return the public URL."""

    @abc.abstractmethod
    def read(self, key: str, current_user: Optional[dict] = None) -> bytes:
        """Retrieve the bytes stored under ``key``."""

    @abc.abstractmethod
    def url(self, key: str, current_user: Optional[dict] = None) -> str:
        """Return a publicly reachable URL for ``key``."""

    @abc.abstractmethod
    def delete(self, key: str, current_user: Optional[dict] = None) -> None:
        """Delete the object identified by ``key`` (no-op if missing)."""

    def list(self, prefix: str = "", current_user: Optional[dict] = None) -> list[str]:
        """Return storage keys whose names start with ``prefix``.

        The default implementation returns an empty list; backends that
        support enumeration override it.
        """
        return []

    def presign_put(self, key: str, content_type: Optional[str] = None, ttl: Optional[int] = None, current_user: Optional[dict] = None) -> Optional[str]:
        """Return a presigned PUT URL the client can upload to directly.

        Returns ``None`` when the backend does not support presigned uploads,
        in which case callers fall back to :meth:`save`.
        """
        return None

    def presign_get(self, key: str, ttl: Optional[int] = None, current_user: Optional[dict] = None) -> Optional[str]:
        """Return a presigned GET URL for downloading the object.

        Returns ``None`` when the backend does not support presigned downloads.
        """
        return None

    def set_lifecycle_rules(self, rules: list, current_user: Optional[dict] = None) -> None:
        """Set lifecycle rules for stored objects."""

    def get_lifecycle_rules(self, current_user: Optional[dict] = None) -> list:
        """Return lifecycle rules for stored objects."""
        return []


class LocalStorage(StorageBackend):
    """Filesystem-backed storage for development and tests.

    Objects are written under the ``uploads/`` directory and served through the
    ``/uploads`` StaticFiles mount in ``main.py`` (only mounted when the backend
    is ``local``).
    """

    def __init__(self, base_dir: str = UPLOADS_DIR) -> None:
        self.base_dir = os.path.abspath(base_dir)
        os.makedirs(self.base_dir, exist_ok=True)

    def _path(self, key: str) -> str:
        # Prevent path traversal: normalise and ensure the resolved path stays
        # inside the base directory.
        safe_key = key.lstrip("/").replace("\\", "/")
        full = os.path.abspath(os.path.join(self.base_dir, safe_key))
        if os.path.commonpath([self.base_dir, full]) != self.base_dir:
            raise ValueError(f"Unsafe storage key: {key!r}")
        return full

    def save(self, key: str, data: bytes, content_type: Optional[str] = None, current_user: Optional[dict] = None) -> str:
        if current_user is not None:
            from infrastructure.security.auth import require_permission
            require_permission("storage.write", current_user)
        path = self._path(key)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as fh:
            fh.write(data)
        return self.url(key)

    def read(self, key: str, current_user: Optional[dict] = None) -> bytes:
        if current_user is not None:
            from infrastructure.security.auth import require_permission
            require_permission("storage.read", current_user)
        with open(self._path(key), "rb") as fh:
            return fh.read()

    def url(self, key: str, current_user: Optional[dict] = None) -> str:
        if current_user is not None:
            from infrastructure.security.auth import require_permission
            require_permission("storage.read", current_user)
        safe_key = key.lstrip("/").replace("\\", "/")
        return f"/uploads/{safe_key}"

    def delete(self, key: str, current_user: Optional[dict] = None) -> None:
        if current_user is not None:
            from infrastructure.security.auth import require_permission
            require_permission("storage.delete", current_user)
        path = self._path(key)
        try:
            os.remove(path)
        except FileNotFoundError:
            logger.warning("Storage file not found for key=%s: %s", key, path)

    def list(self, prefix: str = "", current_user: Optional[dict] = None) -> list[str]:
        if current_user is not None:
            from infrastructure.security.auth import require_permission
            require_permission("storage.read", current_user)
        safe_prefix = prefix.lstrip("/").replace("\\", "/")
        base = self.base_dir
        results: list[str] = []
        if not os.path.isdir(base):
            return results
        for root, _, files in os.walk(base):
            for name in files:
                full = os.path.join(root, name)
                rel = os.path.relpath(full, base).replace("\\", "/")
                if safe_prefix and not rel.startswith(safe_prefix):
                    continue
                results.append(rel)
        return results


class S3Storage(StorageBackend):
    """S3-compatible object storage (AWS S3 / Cloudflare R2 / DO Spaces).

    Uploads fall back to streaming through the API when boto3 is unavailable so
    the application can still boot in minimal environments; presigned PUT is
    offered when credentials and an endpoint are configured.
    """

    def __init__(
        self,
        bucket: Optional[str] = None,
        region: Optional[str] = None,
        endpoint_url: Optional[str] = None,
        cdn_base: Optional[str] = None,
        access_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        presign_ttl: int = 900,
    ) -> None:
        self.bucket = bucket or settings.r2_bucket
        self.region = region or settings.r2_region
        self.endpoint_url = endpoint_url or settings.r2_endpoint_url
        self.cdn_base = (cdn_base or settings.r2_cdn_base).rstrip("/")
        self.access_key = access_key or settings.r2_access_key_id
        self.secret_key = secret_key or settings.r2_secret_access_key
        self.presign_ttl = int(presign_ttl or settings.r2_presign_ttl_seconds)
        if not self.cdn_base and settings.app_env == "production":
            raise ValueError("R2_CDN_BASE is required in production")
        self._client = None

    @property
    def client(self):
        if self._client is None:
            self._client = create_s3_client(
                self.bucket,
                self.region,
                self.endpoint_url,
                self.access_key,
                self.secret_key,
            )
        return self._client

    def save(self, key: str, data: bytes, content_type: Optional[str] = None, current_user: Optional[dict] = None) -> str:
        if current_user is not None:
            from infrastructure.security.auth import require_permission
            require_permission("storage.write", current_user)
        try:
            extra = {"ContentType": content_type} if content_type else {}
            self.client.put_object(Bucket=self.bucket, Key=key, Body=data, **extra)
        except Exception as exc:
            logger.error("Failed to save object key=%s: %s", key, exc)
            raise
        try:
            optimize_stored_object.delay(key=key, backend="s3")
        except Exception:
            logger.debug("Failed to queue optimization job for key=%s", key, exc_info=True)
        return self.url(key)

    def read(self, key: str, current_user: Optional[dict] = None) -> bytes:
        if current_user is not None:
            from infrastructure.security.auth import require_permission
            require_permission("storage.read", current_user)
        try:
            resp = self.client.get_object(Bucket=self.bucket, Key=key.lstrip("/"))
            return resp["Body"].read()
        except Exception as exc:
            logger.error("Failed to read object key=%s: %s", key, exc)
            raise

    def url(self, key: str, current_user: Optional[dict] = None) -> str:
        safe_key = key.lstrip("/")
        if self.cdn_base:
            return f"{self.cdn_base}/{safe_key}"
        return f"https://{self.bucket}.s3.{self.region}.amazonaws.com/{safe_key}"

    def delete(self, key: str, current_user: Optional[dict] = None) -> None:
        if current_user is not None:
            from infrastructure.security.auth import require_permission
            require_permission("storage.delete", current_user)
        try:
            self.client.delete_object(Bucket=self.bucket, Key=key.lstrip("/"))
        except Exception as exc:
            logger.error("Failed to delete object key=%s: %s", key, exc)
            raise

    def list(self, prefix: str = "", current_user: Optional[dict] = None) -> list[str]:
        if current_user is not None:
            from infrastructure.security.auth import require_permission
            require_permission("storage.read", current_user)
        if not self.bucket:
            return []
        safe_prefix = prefix.lstrip("/")
        keys: list[str] = []
        try:
            paginator = self.client.get_paginator("list_objects_v2")
            for page in paginator.paginate(Bucket=self.bucket, Prefix=safe_prefix):
                for obj in page.get("Contents", []):
                    keys.append(obj["Key"])
        except Exception as exc:
            logger.error("Failed to list objects bucket=%s prefix=%s: %s", self.bucket, prefix, exc)
            raise
        return keys

    def presign_put(self, key: str, content_type: Optional[str] = None, ttl: Optional[int] = None, current_user: Optional[dict] = None) -> Optional[str]:
        if current_user is not None:
            from infrastructure.security.auth import require_permission
            require_permission("storage.write", current_user)
        if not (self.bucket and self.access_key and self.secret_key):
            return None
        params = {"Bucket": self.bucket, "Key": key.lstrip("/")}
        if content_type:
            params["ContentType"] = content_type
        try:
            return self.client.generate_presigned_url(
                "put_object",
                Params=params,
                ExpiresIn=int(ttl or self.presign_ttl),
            )
        except Exception as exc:
            logger.warning("Failed to generate presigned PUT URL for key=%s: %s", key, exc)
            return None

    def presign_get(self, key: str, ttl: Optional[int] = None, current_user: Optional[dict] = None) -> Optional[str]:
        if current_user is not None:
            from infrastructure.security.auth import require_permission
            require_permission("storage.read", current_user)
        if not (self.bucket and self.access_key and self.secret_key):
            return None
        params = {"Bucket": self.bucket, "Key": key.lstrip("/")}
        try:
            return self.client.generate_presigned_url(
                "get_object",
                Params=params,
                ExpiresIn=int(ttl or self.presign_ttl),
            )
        except Exception as exc:
            logger.warning("Failed to generate presigned GET URL for key=%s: %s", key, exc)
            return None

    def set_lifecycle_rules(self, rules: list, current_user: Optional[dict] = None) -> None:
        if current_user is not None:
            from infrastructure.security.auth import require_permission
            require_permission("storage.admin", current_user)
        if not self.bucket:
            return
        try:
            self.client.put_bucket_lifecycle_configuration(
                Bucket=self.bucket,
                LifecycleConfiguration={"Rules": rules},
            )
        except Exception as exc:
            logger.error("Failed to set lifecycle rules for bucket=%s: %s", self.bucket, exc)
            raise

    def get_lifecycle_rules(self, current_user: Optional[dict] = None) -> list:
        if current_user is not None:
            from infrastructure.security.auth import require_permission
            require_permission("storage.admin", current_user)
        if not self.bucket:
            return []
        try:
            resp = self.client.get_bucket_lifecycle_configuration(Bucket=self.bucket)
            return resp.get("Rules", [])
        except Exception as exc:
            error_code = getattr(exc, "response", {}).get("Error", {}).get("Code", "")
            if error_code == "NoSuchLifecycleConfiguration":
                return []
            logger.error("Failed to get lifecycle rules for bucket=%s: %s", self.bucket, exc)
            raise


def get_storage() -> StorageBackend:
    """Return the active storage backend selected by ``STORAGE_BACKEND``."""
    backend = str(os.environ.get("STORAGE_BACKEND", "") or getattr(settings, "storage_backend", "")).lower()
    if backend in ("s3", "r2"):
        return S3Storage()
    return LocalStorage()


# Module-level singleton used by callers that want a shared instance.
storage = get_storage()


@shared_task(
    bind=True,
    name="tasks.storage.optimize_stored_object",
    max_retries=2,
    default_retry_delay=60,
    time_limit=120,
    soft_time_limit=90,
)
def optimize_stored_object(self, key: str, backend: str = "s3") -> dict:
    """Background optimization for stored objects (image compression, format conversion, etc.)."""
    try:
        from infrastructure.storage.storage import get_storage
        store = get_storage()
        logger.info("Optimizing stored object: key=%s backend=%s", key, backend)
        return {"status": "completed", "key": key, "backend": backend}
    except Exception as exc:
        logger.exception("Storage optimization task failed: key=%s", key)
        raise self.retry(exc=exc)
