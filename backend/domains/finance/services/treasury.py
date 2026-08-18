# AUTO-GENERATED controller delegator (routers -> controllers -> services).
"""Lazy re-export delegator for ``domains.finance.services``.

Importing a name from this module (e.g.
``from domains.finance.services.treasury import admin_reporting_service``) resolves
to the sibling module ``domains.finance.services.<name>`` on demand. Resolving
lazily avoids the import cycles that a top-level re-export would create.
"""
import importlib

_PACKAGE = "domains.finance.services"


def __getattr__(name: str):
    if name.startswith("__") and name.endswith("__"):
        raise AttributeError(name)
    module = importlib.import_module(f"{_PACKAGE}.{name}")
    return getattr(module, name)
