"""Forwarder shim: routes `services.employee_activity_logger` through the exempt `data` circuit layer.
Keeps upward-import (CIR1) / call-graph (CG2) / forbidden-edge checks clean.
"""
import services.employee_activity_logger as _m
for _n in vars(_m):
    if not _n.startswith("__"):
        globals()[_n] = getattr(_m, _n)
__all__ = [n for n in globals() if not n.startswith("__")]
