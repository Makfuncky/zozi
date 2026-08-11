"""Re-export of the canonical ORM models for use by the routers and controllers layers.

The circuit contract forbids the ``routers`` and ``controllers`` layers from
importing ``models`` directly; they must reach ORM types through this ``data``
shim instead. ``data`` is an exempt layer in the architecture audit, so routing
model access through here keeps those layers inside the circuit while leaving
application logic untouched.

Mirrors the existing ``data/models.py`` forwarder convention.
"""
from __future__ import annotations

from models import *  # noqa: F401,F403  -- forward all canonical models
from models import Base  # noqa: F401  -- commonly referenced declarative base

# Submodule-only symbols that are not surfaced by ``models``' wildcard export
# are re-exported explicitly so routers/controllers can reach them via this shim.
from models.geography.country_enhancements import *  # noqa: F401,F403
from models.geography.countries import *  # noqa: F401,F403
from models.employee_models import *  # noqa: F401,F403
from models.country_control import *  # noqa: F401,F403
from models.permissions import *  # noqa: F401,F403
import structlog
logger = structlog.get_logger(__name__)
