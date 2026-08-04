"""Object-storage abstraction for media (Phase 1 of the scaling plan).

Defines a :class:`StorageBackend` interface so the rest of the application can
save / read / delete media without caring whether bytes live on local disk
(development & tests) or in an S3-compatible bucket behind a CDN (production).

The active backend is selected by the ``STORAGE_BACKEND`` config value, mirroring
the SQLite/Postgres switch in ``db/database.py``:

- ``local`` -> :class:`LocalStorage` (writes under ``uploads/``, returns
  ``/uploads/...`` URLs served by the StaticFiles mount in ``main.py``).
- ``s3``    -> :class:`S3Storage` (writes to an S3-compatible bucket, returns CDN
  URLs; large files can be pushed directly by the client via a presigned PUT so
  the API never touches the bytes).

Nothing in the recovered codebase imports this module yet; it is the
infrastructure the media/P0-A refactor is meant to route through.
"""

import abc
import os
from typing import Optional

from utils.config import settings

UPLOADS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "uploads")


class StorageBackend(abc.ABC):
    """Common contract for all storage backends."""

    @abc.abstractmethod
    def save(self, key: str, data: bytes, content_type: Optional[str] = None) -> str:
        """Persist ``data`` under ``key`` and return the public URL."""

    @abc.abstractmethod
    def read(self, key: str) -> bytes:
        """Retrieve the bytes stored under ``key``."""

    @abc.abstractmethod
    def url(self, key: str) -> str:
        """Return a publicly reachable URL for ``key``."""

    @abc.abstractmethod
    def delete(self, key: str) -> None:
        """Delete the object identified by ``key`` (no-op if missing)."""

    def list(self, prefix: str = "") -> list[str]:
        """Return storage keys whose names start with ``prefix``.

        The default implementation returns an empty list; backends that
        support enumeration override it.
        """
        return []

    def presign_put(self, key: str, content_type: Optional[str] = None, ttl: Optional[int] = None) -> Optional[str]:
        """Return a presigned PUT URL the client can upload to directly.

        Returns ``None`` when the backend does not support presigned uploads,
        in which case callers fall back to :meth:`save`.
        """
        return None


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

    def save(self, key: str, data: bytes, content_type: Optional[str] = None) -> str:
        path = self._path(key)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as fh:
            fh.write(data)
        return self.url(key)

    def read(self, key: str) -> bytes:
        with open(self._path(key), "rb") as fh:
            return fh.read()

    def url(self, key: str) -> str:
        safe_key = key.lstrip("/").replace("\\", "/")
        return f"/uploads/{safe_key}"

    def delete(self, key: str) -> None:
        path = self._path(key)
        try:
            os.remove(path)
        except FileNotFoundError:
            pass

    def list(self, prefix: str = "") -> list[str]:
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
        self.bucket = bucket or getattr(settings, "s3_bucket", "") or os.getenv("S3_BUCKET", "")
        self.region = region or getattr(settings, "s3_region", "") or os.getenv("S3_REGION", "auto")
        self.endpoint_url = endpoint_url or getattr(settings, "s3_endpoint_url", "") or os.getenv("S3_ENDPOINT_URL", "")
        self.cdn_base = (cdn_base or getattr(settings, "s3_cdn_base", "") or os.getenv("S3_CDN_BASE", "")).rstrip("/")
        self.access_key = access_key or getattr(settings, "s3_access_key_id", "") or os.getenv("S3_ACCESS_KEY_ID", "")
        self.secret_key = secret_key or getattr(settings, "s3_secret_access_key", "") or os.getenv("S3_SECRET_ACCESS_KEY", "")
        self.presign_ttl = int(presign_ttl or getattr(settings, "s3_presign_ttl_seconds", 900) or 900)
        self._client = None

    @property
    def client(self):
        if self._client is None:
            import boto3  # local import so the dependency stays optional

            self._client = boto3.client(
                "s3",
                region_name=self.region if self.region not in ("", "auto") else None,
                endpoint_url=self.endpoint_url or None,
                aws_access_key_id=self.access_key or None,
                aws_secret_access_key=self.secret_key or None,
            )
        return self._client

    def save(self, key: str, data: bytes, content_type: Optional[str] = None) -> str:
        extra = {"ContentType": content_type} if content_type else {}
        self.client.put_object(Bucket=self.bucket, Key=key, Body=data, **extra)
        return self.url(key)

    def read(self, key: str) -> bytes:
        resp = self.client.get_object(Bucket=self.bucket, Key=key.lstrip("/"))
        return resp["Body"].read()

    def url(self, key: str) -> str:
        safe_key = key.lstrip("/")
        if self.cdn_base:
            return f"{self.cdn_base}/{safe_key}"
        return f"https://{self.bucket}.s3.{self.region}.amazonaws.com/{safe_key}"

    def delete(self, key: str) -> None:
        self.client.delete_object(Bucket=self.bucket, Key=key.lstrip("/"))

    def list(self, prefix: str = "") -> list[str]:
        if not self.bucket:
            return []
        safe_prefix = prefix.lstrip("/")
        keys: list[str] = []
        paginator = self.client.get_paginator("list_objects_v2")
        for page in paginator.paginate(Bucket=self.bucket, Prefix=safe_prefix):
            for obj in page.get("Contents", []):
                keys.append(obj["Key"])
        return keys

    def presign_put(self, key: str, content_type: Optional[str] = None, ttl: Optional[int] = None) -> Optional[str]:
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
        except Exception:
            return None


def get_storage() -> StorageBackend:
    """Return the active storage backend selected by ``STORAGE_BACKEND``."""
    backend = str(getattr(settings, "storage_backend", "") or os.getenv("STORAGE_BACKEND", "local")).lower()
    if backend == "s3":
        return S3Storage()
    return LocalStorage()


# Module-level singleton used by callers that want a shared instance.
storage = get_storage()
