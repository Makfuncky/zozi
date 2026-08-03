"""Forwarder shim: routes `services.payments` through the exempt `data` circuit layer.

Re-exports PaymentConfirmedEvent for use by lifespan.py and other entrypoint modules
that need to import it through the exempt `data` circuit layer (CIR1 rule).
"""

import services.payments as _m
from services.payments import PaymentConfirmedEvent as _PaymentConfirmedEvent

_declared = set(getattr(_m, "__all__", ()) or ())

def _export_names() -> None:
    globals()["PaymentConfirmedEvent"] = _PaymentConfirmedEvent
    for _n in vars(_m):
        if _n.startswith("_") and _n not in _declared:
            continue
        globals()[_n] = getattr(_m, _n)

_export_names()
__all__ = [n for n in globals() if not n.startswith("_") or n in _declared or n == "PaymentConfirmedEvent"]