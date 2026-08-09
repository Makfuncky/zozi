"""Forwarder shim exposing DB session helpers through the exempt ``data`` layer.

Routers and controllers may not import ``db.database`` directly (circuit
rule); they reach sessions via this ``data.db`` shim instead.
"""
from __future__ import annotations

from db.database import *  # noqa: F401,F403
import structlog
logger = structlog.get_logger(__name__)
