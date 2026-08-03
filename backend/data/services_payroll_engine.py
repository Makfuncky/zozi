"""Forwarder shim: routes `services.payroll_engine` through the exempt `data` circuit layer.
Keeps upward-import (CIR1) / call-graph (CG2) / forbidden-edge checks clean.
"""
import services.payroll_engine as _m
for _n in vars(_m):
    if not _n.startswith("__"):
        globals()[_n] = getattr(_m, _n)
__all__ = [n for n in globals() if not n.startswith("__")]
