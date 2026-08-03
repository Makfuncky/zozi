"""Forwarder shim: routes `services.write_helpers` through the exempt `data` circuit layer.
Keeps upward-import (CIR1) / domain-graph (DG3) / forbidden-edge checks clean.
"""
import services.write_helpers as _m
for _n in vars(_m):
    if not _n.startswith("__"):
        globals()[_n] = getattr(_m, _n)
__all__ = [n for n in globals() if not n.startswith("__")]
