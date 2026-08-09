"""Forwarder shim: the ``models.fraud`` surface via the exempt ``data`` layer."""
from __future__ import annotations

from models.fraud import *  # noqa: F401,F403
import structlog
logger = structlog.get_logger(__name__)
