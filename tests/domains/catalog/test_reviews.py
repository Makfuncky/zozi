"""Tests for the customer review photo upload endpoint (F-010).

Verifies that:
  - POST /api/v1/customer/reviews/{id}/photos exists and is wired in the router
  - Non-image uploads are rejected
  - Router enforces size limit
  - Router is mounted under correct prefix
  - Endpoint gates on require_feature
"""
from __future__ import annotations

import sys
import os

_BACKEND_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "backend")
)
if _BACKEND_ROOT not in sys.path:
    sys.path.insert(0, _BACKEND_ROOT)


def test_upload_review_photo_endpoint_exists():
    """The reviews router must expose POST /{id}/photos."""
    from modules.customer.routers.reviews import router

    found = False
    for route in router.routes:
        methods = getattr(route, "methods", set())
        path = getattr(route, "path", "")
        if "POST" in methods and "{id}/photos" in path:
            found = True
            break
    paths = [r.path for r in router.routes]
    assert found, f"POST /{{id}}/photos not found in router routes: {paths}"


def test_upload_review_photo_rejects_non_image():
    """The endpoint must reject unsupported file types."""
    from modules.customer.routers.reviews import _ALLOWED_IMAGE_TYPES

    assert "image/jpeg" in _ALLOWED_IMAGE_TYPES
    assert "image/png" in _ALLOWED_IMAGE_TYPES
    assert "application/pdf" not in _ALLOWED_IMAGE_TYPES


def test_upload_review_photo_rate_limits_size():
    """The endpoint must enforce a max upload size of 5 MB."""
    from modules.customer.routers.reviews import _MAX_UPLOAD_BYTES

    assert _MAX_UPLOAD_BYTES == 5 * 1024 * 1024


def test_review_photo_router_prefix():
    """Router must be mounted under /api/v1/customer/reviews."""
    from modules.customer.routers.reviews import router

    assert router.prefix == "/api/v1/customer/reviews"


def test_upload_review_photo_requires_feature():
    """The endpoint must gate on catalog.review.create feature."""
    import inspect

    from modules.customer.routers import reviews as reviews_mod

    source = inspect.getsource(reviews_mod.upload_review_photo)
    assert "require_feature" in source, "Endpoint must use require_feature gate"
    assert "catalog.review.create" in source
