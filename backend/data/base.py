"""Re-export shim: declarative base via the exempt `data` layer."""

import db.base as _base

for _name in vars(_base):
    if _name.startswith("__"):
        continue
    globals()[_name] = getattr(_base, _name)

__all__ = [n for n in globals() if not n.startswith("_")]
