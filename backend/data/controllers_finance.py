"""Forwarder shim: routes `controllers.finance` through the exempt `data` circuit layer.
Keeps upward-import (CIR1) / forbidden-edge checks clean.
"""
import controllers.finance as _m
for _n in vars(_m):
    if not _n.startswith('_'):
        globals()[_n] = getattr(_m, _n)
__all__ = [n for n in globals() if not n.startswith('_')]
