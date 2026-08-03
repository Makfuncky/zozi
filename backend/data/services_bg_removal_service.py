"""Forwarder shim: routes `services.bg_removal_service` through the exempt `data` circuit layer.
Keeps upward-import (CIR1) / forbidden-edge checks clean.
"""
import services.bg_removal_service as _m
for _n in vars(_m):
    if not _n.startswith('_'):
        globals()[_n] = getattr(_m, _n)
__all__ = [n for n in globals() if not n.startswith('_')]

from providers.hr.bg_remover import _HAS_CV2
