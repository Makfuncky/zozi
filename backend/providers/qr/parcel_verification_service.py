"""Parcel photo verification service.

Routers must not import ``providers.*`` directly (auditor rule **V6**); they
call this services-layer wrapper, which is the only place allowed to reach the
``providers.image.parcel_verification`` multi-engine provider (SSIM + feature
match + homography + vision AI).
"""
from __future__ import annotations

from typing import Any

from providers.image.parcel_verification import (
    verify_parcel_fast as _provider_verify_parcel_fast,
    verify_parcel_photo as _provider_verify_parcel_photo,
)

__all__ = ["verify_parcel_fast", "verify_parcel_photo"]


def verify_parcel_photo(
    *,
    image_bytes: bytes,
    item_descriptions: list[str],
    reference_image_bytes: bytes | None = None,
    run_ssim: bool = True,
    run_feature_match: bool = True,
    run_homography: bool = True,
    run_vision_ai: bool = True,
) -> dict[str, Any]:
    return _provider_verify_parcel_photo(
        image_bytes=image_bytes,
        item_descriptions=item_descriptions,
        reference_image_bytes=reference_image_bytes,
        run_ssim=run_ssim,
        run_feature_match=run_feature_match,
        run_homography=run_homography,
        run_vision_ai=run_vision_ai,
    )


def verify_parcel_fast(
    *,
    image_bytes: bytes,
    item_descriptions: list[str],
    reference_image_bytes: bytes | None = None,
) -> dict[str, Any]:
    return _provider_verify_parcel_fast(
        image_bytes=image_bytes,
        item_descriptions=item_descriptions,
        reference_image_bytes=reference_image_bytes,
    )
