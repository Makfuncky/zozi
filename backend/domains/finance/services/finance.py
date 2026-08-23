"""Lazy re-export delegator for ``domains.finance.services``.

Importing a name from this module resolves to the matching submodule on demand.
With sub-domain folders (ledger/, treasury/, payouts/, ...), the delegator
first checks the root, then falls back to each sub-domain.
"""
from __future__ import annotations

import importlib
import sys

_PACKAGE = "domains.finance.services"
_SUBDOMAINS = [
    "ledger", "accounts", "treasury", "payouts", "tax",
    "reporting", "country", "commission", "shared",
]


def __getattr__(name: str):
    if name.startswith("__") and name.endswith("__"):
        raise AttributeError(name)
    # Try root-level first.
    try:
        module = importlib.import_module(f"{_PACKAGE}.{name}")
        setattr(sys.modules[__name__], name, module)
        return module
    except ModuleNotFoundError:
        pass
    # Fall back to sub-domain folders.
    for sub in _SUBDOMAINS:
        try:
            module = importlib.import_module(f"{_PACKAGE}.{sub}.{name}")
            setattr(sys.modules[__name__], name, module)
            return module
        except ModuleNotFoundError:
            continue
    raise AttributeError(f"module {_PACKAGE!r} has no attribute {name!r}")
