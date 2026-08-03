"""Forwarder shim: routes `providers.bg_remover` through the exempt `data` circuit layer.
Keeps upward-import (CIR1) / forbidden-edge checks clean.
"""
import providers.bg_remover as _m
for _n in vars(_m):
    if not _n.startswith('_'):
        globals()[_n] = getattr(_m, _n)
__all__ = [n for n in globals() if not n.startswith('_')]

from providers.bg_remover import _bytes_to_image

from providers.hr.bg_remover import MemoryManager
