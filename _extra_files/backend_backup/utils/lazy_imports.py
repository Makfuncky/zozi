from __future__ import annotations


class LazyNumpy:
    """Lazy proxy for numpy to avoid top-level import."""

    def __getattr__(self, name):
        import numpy as np
        return getattr(np, name)


class LazyPIL:
    """Lazy proxy for PIL.Image to avoid top-level import."""

    def __getattr__(self, name):
        from PIL import Image
        return getattr(Image, name)


np = LazyNumpy()
Image = LazyPIL()
