# AUTO-GENERATED controller delegator (routers -> controllers -> services).
"""Lazy re-export delegator for ``domains.media.services``.

Importing a name from this module (e.g.
``from domains.media.services.ai import automation_scheduler``) resolves to the
sibling module ``domains.media.services.<name>`` on demand. Resolving lazily
avoids the import cycles that a top-level re-export would create.
"""
import importlib

_PACKAGE = "domains.media.services"


def __getattr__(name: str):
    if name.startswith("__") and name.endswith("__"):
        raise AttributeError(name)
    module = importlib.import_module(f"{_PACKAGE}.{name}")
    return getattr(module, name)
