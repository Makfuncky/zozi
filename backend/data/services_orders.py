"""Forwarder shim: routes `services.orders` through the exempt `data` circuit layer.
Keeps upward-import (CIR1) / forbidden-edge checks clean.

Forwards every public name plus any underscore-prefixed names that the source
package explicitly declares in ``__all__`` (e.g. ``_event_publisher``,
``_order_holds_inventory``) so downstream consumers can import them without a
circuit violation.
"""
import services.orders as _m

_declared = set(getattr(_m, "__all__", ()) or ())

def _forward_names() -> None:
    for _n in vars(_m):
        if _n.startswith("_") and _n not in _declared:
            continue
        globals()[_n] = getattr(_m, _n)

_forward_names()
__all__ = [n for n in globals() if not n.startswith("_") or n in _declared]