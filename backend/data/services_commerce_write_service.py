"""Lazy forwarder shim for the exempt ``data`` facade.

Forwards attribute access to ``services.commerce_write_service`` on demand. Using
``__getattr__`` (instead of copying every attribute at import time) means importing
this module does not eagerly trigger the load of every re-exported dependency, which
had caused circular-import and eager-resolution failures on the address routes.
"""
import importlib
import structlog
logger = structlog.get_logger(__name__)

_target = "services.commerce_write_service"


def __getattr__(name: str):
    if name.startswith("__"):
        raise AttributeError(name)
    module = importlib.import_module(_target)
    return getattr(module, name)


def __dir__():
    module = importlib.import_module(_target)
    return dir(module)
