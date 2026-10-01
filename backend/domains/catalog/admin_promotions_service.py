"""Backwards-compatible facade for catalog admin promotion operations.

The canonical ``create_coupon`` implementation now lives in
``domains.catalog.services.promotions.promotions_service`` (per the catalog
domain boundary). This module keeps legacy import sites working.
"""
from __future__ import annotations

from domains.catalog.services.promotions.promotions_service import create_coupon

__all__ = ["create_coupon"]
