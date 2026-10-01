"""Tests proving LAW-EXTRACT-018 fix for storage.py.

S3Storage.__init__ must read R2/S3 configuration exclusively through the
typed pydantic-settings object (``settings.r2_*``). Raw ``os.getenv()``
calls in the constructor are forbidden by TECHNOLOGY_STACK.md Law 84.
"""
from __future__ import annotations

import ast
import os
from pathlib import Path

import pytest


# ---------------------------------------------------------------------------
# Path to the source file under test.
# ---------------------------------------------------------------------------
# tests/infrastructure/storage/test_storage.py  →  go up 4 levels to repo root.
TESTS_DIR = Path(__file__).resolve().parent
REPO_ROOT = TESTS_DIR.parent.parent.parent.parent
STORAGE_PY = REPO_ROOT / "backend" / "infrastructure" / "storage" / "storage.py"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_class_init_source(class_name: str) -> str:
    """Return the source of ClassName.__init__ from storage.py."""
    src = STORAGE_PY.read_text(encoding="utf-8")
    tree = ast.parse(src)
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            for item in node.body:
                if isinstance(item, ast.FunctionDef) and item.name == "__init__":
                    return ast.get_source_segment(src, item) or ""
    return ""


def _s3storage_init_source() -> str:
    return _get_class_init_source("S3Storage")


# ---------------------------------------------------------------------------
# Law 84 / LAW-EXTRACT-018: no raw os.getenv() in S3Storage.__init__
# ---------------------------------------------------------------------------


class TestNoRawGetenvInS3StorageInit:
    """S3Storage.__init__ must not call os.getenv()."""

    def test_no_os_getenv_in_init(self):
        init_src = _s3storage_init_source()
        assert "os.getenv" not in init_src, (
            "S3Storage.__init__ must not use os.getenv(); "
            "use settings.r2_* references only"
        )

    def test_no_getenv_any_form_in_init(self):
        """Neither os.getenv nor bare getenv must appear in __init__."""
        init_src = _s3storage_init_source()
        assert "getenv" not in init_src, (
            "Found getenv reference inside S3Storage.__init__"
        )


# ---------------------------------------------------------------------------
# Settings-only config resolution
# ---------------------------------------------------------------------------


class TestS3StorageUsesSettingsOnly:
    """S3Storage must resolve bucket/region/endpoint from settings.r2_*."""

    def test_bucket_from_settings(self):
        init_src = _s3storage_init_source()
        assert "settings.r2_bucket" in init_src

    def test_region_from_settings(self):
        init_src = _s3storage_init_source()
        assert "settings.r2_region" in init_src

    def test_endpoint_from_settings(self):
        init_src = _s3storage_init_source()
        assert "settings.r2_endpoint_url" in init_src

    def test_cdn_base_from_settings(self):
        init_src = _s3storage_init_source()
        assert "settings.r2_cdn_base" in init_src

    def test_access_key_from_settings(self):
        init_src = _s3storage_init_source()
        assert "settings.r2_access_key_id" in init_src

    def test_secret_key_from_settings(self):
        init_src = _s3storage_init_source()
        assert "settings.r2_secret_access_key" in init_src

    def test_presign_ttl_from_settings(self):
        init_src = _s3storage_init_source()
        assert "settings.r2_presign_ttl_seconds" in init_src


# ---------------------------------------------------------------------------
# Runtime behaviour: S3Storage attribute values come from kwargs
# ---------------------------------------------------------------------------


class TestS3StorageKwargsDriveAttributes:
    """When kwargs are given directly, S3Storage uses them unchanged."""

    def test_explicit_kwargs_set_attributes(self):
        """Direct kwargs must still be stored on the instance."""
        # We test via AST because importing S3Storage pulls in config.Settings
        # which requires SECRET_KEY at import time. The structural test above
        # already proves the settings-only source; here we verify the AST
        # preserves the 'bucket or settings.r2_bucket' pattern.
        init_src = _s3storage_init_source()
        assert "bucket or settings.r2_bucket" in init_src
        assert "region or settings.r2_region" in init_src
        assert "endpoint_url or settings.r2_endpoint_url" in init_src
        assert "access_key or settings.r2_access_key_id" in init_src
        assert "secret_key or settings.r2_secret_access_key" in init_src

    def test_cdn_base_strips_trailing_slash_in_ast(self):
        """cdn_base assignment must call .rstrip('/')."""
        init_src = _s3storage_init_source()
        assert ".rstrip" in init_src and '"/"' in init_src

    def test_no_s3_fallback_env_vars_in_init(self):
        """S3_* env-var fallbacks must not appear in __init__."""
        init_src = _s3storage_init_source()
        for s3_var in (
            "S3_BUCKET",
            "S3_REGION",
            "S3_ENDPOINT_URL",
            "S3_CDN_BASE",
            "S3_ACCESS_KEY_ID",
            "S3_SECRET_ACCESS_KEY",
            "S3_PRESIGN_TTL_SECONDS",
        ):
            assert s3_var not in init_src, (
                f"S3 fallback env var {s3_var} must not appear in "
                "S3Storage.__init__"
            )

    def test_no_getattr_settings_fallback_in_init(self):
        """getattr(settings, ...) fallback pattern must not appear in __init__."""
        init_src = _s3storage_init_source()
        assert "getattr(settings" not in init_src, (
            "getattr(settings, ...) fallback pattern must not appear in "
            "S3Storage.__init__; use settings.r2_* directly"
        )
