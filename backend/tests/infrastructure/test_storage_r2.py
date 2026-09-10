"""Tests for the R2 (S3-compatible) storage abstraction (Law 120).

These tests exercise the renamed ``R2Storage`` class and the
``generate_presigned_upload_url`` / ``generate_presigned_download_url``
module-level helpers, plus the bucket-name constants.

The boto3 client is mocked everywhere so no real network call is attempted.
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest


class TestBucketConstants:
    def test_four_canonical_buckets_present(self):
        from infrastructure.storage.storage import (
            R2_BUCKET_MEDIA,
            R2_BUCKET_SUPPLIER_UPLOADS,
            R2_BUCKET_EXPORTS,
            R2_BUCKET_ARCHIVES,
            R2_BUCKETS,
        )

        assert R2_BUCKET_MEDIA == "zozi-media"
        assert R2_BUCKET_SUPPLIER_UPLOADS == "zozi-supplier-uploads"
        assert R2_BUCKET_EXPORTS == "zozi-exports"
        assert R2_BUCKET_ARCHIVES == "zozi-archives"
        assert set(R2_BUCKETS) == {
            R2_BUCKET_MEDIA,
            R2_BUCKET_SUPPLIER_UPLOADS,
            R2_BUCKET_EXPORTS,
            R2_BUCKET_ARCHIVES,
        }


class TestR2ClassRename:
    def test_R2Storage_imports(self):
        from infrastructure.storage.storage import R2Storage

        assert R2Storage is not None

    def test_S3Storage_alias_to_R2Storage(self):
        from infrastructure.storage.storage import R2Storage, S3Storage

        assert S3Storage is R2Storage

    def test_create_r2_client_importable_from_package(self):
        from providers.storage import create_r2_client

        assert callable(create_r2_client)

    def test_create_s3_client_alias_to_create_r2_client(self):
        from providers.storage import create_r2_client, create_s3_client

        assert create_s3_client is create_r2_client


class TestR2ClientFactory:
    def test_create_r2_client_uses_boto3_s3(self):
        from providers.storage import r2_client as r2_mod
        from providers.storage.r2_client import create_r2_client

        # `create_r2_client` does `import boto3` inside the function. We mock
        # `__import__` for the boto3 module name to inject a fake boto3.
        fake_boto3 = MagicMock(name="boto3")
        fake_boto3.client.return_value = MagicMock(name="r2_client")
        real_import = __builtins__["__import__"] if isinstance(__builtins__, dict) else __builtins__.__import__

        def fake_import(name, *args, **kwargs):
            if name == "boto3":
                return fake_boto3
            return real_import(name, *args, **kwargs)

        if isinstance(__builtins__, dict):
            __builtins__["__import__"] = fake_import
        else:
            __builtins__.__import__ = fake_import
        try:
            result = create_r2_client(
                bucket="zozi-media",
                region="auto",
                endpoint_url="https://example.r2.cloudflarestorage.com",
                access_key="AKIA",
                secret_key="secret",
            )
        finally:
            if isinstance(__builtins__, dict):
                __builtins__["__import__"] = real_import
            else:
                __builtins__.__import__ = real_import

        assert result is fake_boto3.client.return_value
        fake_boto3.client.assert_called_once()
        call_kwargs = fake_boto3.client.call_args.kwargs
        assert call_kwargs["endpoint_url"] == "https://example.r2.cloudflarestorage.com"
        assert call_kwargs["aws_access_key_id"] == "AKIA"
        assert call_kwargs["aws_secret_access_key"] == "secret"


class TestPresignedUrls:
    def _storage_with_mock(self):
        from infrastructure.storage.storage import R2Storage

        storage = R2Storage(
            bucket="zozi-media",
            region="auto",
            endpoint_url="https://x.r2.cloudflarestorage.com",
            access_key="AK",
            secret_key="SK",
        )
        storage._client = MagicMock(name="boto3_client")
        return storage

    def test_presign_put_returns_url(self):
        storage = self._storage_with_mock()
        storage._client.generate_presigned_url.return_value = "https://signed/put"

        url = storage.presign_put("key/x.jpg", content_type="image/jpeg", ttl=60)

        assert url == "https://signed/put"
        args, kwargs = storage._client.generate_presigned_url.call_args
        assert args[0] == "put_object"
        assert kwargs["ExpiresIn"] == 60
        assert kwargs["Params"]["Bucket"] == "zozi-media"
        assert kwargs["Params"]["Key"] == "key/x.jpg"
        assert kwargs["Params"]["ContentType"] == "image/jpeg"

    def test_presign_get_returns_url(self):
        storage = self._storage_with_mock()
        storage._client.generate_presigned_url.return_value = "https://signed/get"

        url = storage.presign_get("key/x.jpg", ttl=120)

        assert url == "https://signed/get"
        args, kwargs = storage._client.generate_presigned_url.call_args
        assert args[0] == "get_object"
        assert kwargs["ExpiresIn"] == 120

    def test_presign_put_none_when_no_credentials(self):
        from infrastructure.storage.storage import R2Storage

        storage = R2Storage(bucket="zozi-media", access_key="", secret_key="")
        assert storage.presign_put("k") is None


class TestModuleLevelPresignedHelpers:
    @patch("infrastructure.storage.storage.create_r2_client")
    def test_generate_presigned_upload_url(self, mock_factory, monkeypatch):
        mock_client = MagicMock()
        mock_client.generate_presigned_url.return_value = "https://signed/upload"
        mock_factory.return_value = mock_client

        monkeypatch.setenv("R2_ACCESS_KEY_ID", "AK")
        monkeypatch.setenv("R2_SECRET_ACCESS_KEY", "SK")
        monkeypatch.setenv("R2_ENDPOINT_URL", "https://x.r2.cloudflarestorage.com")

        from infrastructure.storage.storage import generate_presigned_upload_url

        url = generate_presigned_upload_url(
            bucket="zozi-media", key="uploads/x.jpg", expires=300
        )

        assert url == "https://signed/upload"
        mock_factory.assert_called_once()
        args, kwargs = mock_client.generate_presigned_url.call_args
        assert args[0] == "put_object"
        assert kwargs["ExpiresIn"] == 300

    def test_generate_presigned_upload_url_none_without_credentials(self, monkeypatch):
        monkeypatch.delenv("R2_ACCESS_KEY_ID", raising=False)
        monkeypatch.delenv("R2_SECRET_ACCESS_KEY", raising=False)
        monkeypatch.delenv("AWS_ACCESS_KEY_ID", raising=False)
        monkeypatch.delenv("AWS_SECRET_ACCESS_KEY", raising=False)

        from infrastructure.storage.storage import generate_presigned_upload_url

        assert generate_presigned_upload_url("zozi-media", "k") is None


class TestStorageBackendSelection:
    def test_local_is_default(self, monkeypatch):
        from infrastructure.storage.storage import LocalStorage, get_storage

        monkeypatch.setenv("STORAGE_BACKEND", "local")
        assert isinstance(get_storage(), LocalStorage)

    def test_r2_backend_returns_R2Storage(self, monkeypatch):
        from infrastructure.storage.storage import R2Storage, get_storage

        monkeypatch.setenv("STORAGE_BACKEND", "r2")
        # Credentials intentionally empty so R2Storage doesn't try to construct
        # a real client — we just want the class selection.
        assert isinstance(get_storage(), R2Storage)

    def test_legacy_s3_backend_still_returns_R2Storage(self, monkeypatch):
        from infrastructure.storage.storage import R2Storage, get_storage

        monkeypatch.setenv("STORAGE_BACKEND", "s3")
        assert isinstance(get_storage(), R2Storage)


class TestBackupManagerR2Naming:
    def test_r2_client_method_exists(self):
        from infrastructure.storage.backup import BackupManager

        assert hasattr(BackupManager, "_r2_client")
        # Backward-compat alias intentionally NOT preserved (private method).

    def test_r2_attributes_present_on_instance(self):
        from infrastructure.storage.backup import BackupManager

        # Private attributes are assigned in __init__, so check an instance.
        b = BackupManager()
        for attr in (
            "_r2_bucket",
            "_r2_prefix",
            "_r2_region",
            "_r2_endpoint_url",
            "_r2_access_key_id",
            "_r2_secret_access_key",
        ):
            assert hasattr(b, attr), f"BackupManager instance missing {attr}"

    def test_no_legacy_s3_attributes(self):
        from infrastructure.storage.backup import BackupManager

        b = BackupManager()
        for attr in (
            "_s3_bucket",
            "_s3_prefix",
            "_s3_region",
            "_s3_endpoint_url",
            "_s3_access_key_id",
            "_s3_secret_access_key",
        ):
            assert not hasattr(b, attr), f"Legacy attribute still present: {attr}"