"""OpenCV (cv2) access point for the provider layer.

The OpenCV SDK is an external integration. Service-layer code must not import
cv2 directly; it should reach it through this provider module so that all
third-party image SDK usage is centralized behind the provider boundary.
"""

from __future__ import annotations

HAS_CV2 = False
HAS_GUIDED_FILTER = False
cv2 = None
ximgproc = None

try:
    import cv2 as _cv2
    from cv2 import ximgproc as _ximgproc  # noqa: F401  (guided filter submodule)

    cv2 = _cv2
    ximgproc = _ximgproc
    HAS_CV2 = True
    HAS_GUIDED_FILTER = True
except Exception:  # pragma: no cover - optional heavy SDK
    pass

__all__ = ["cv2", "ximgproc", "HAS_CV2", "HAS_GUIDED_FILTER"]
