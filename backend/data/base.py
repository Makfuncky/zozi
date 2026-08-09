"""Forwarder shim exposing the SQLAlchemy ``Base``/metadata through the exempt
``data`` layer.

Routers and controllers may not import ``db.base`` directly (circuit rule);
they reach the declarative base via this ``data.base`` shim instead.
"""
from __future__ import annotations

from db.base import *  # noqa: F401,F403
import structlog
logger = structlog.get_logger(__name__)
