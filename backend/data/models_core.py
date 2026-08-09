"""Forwarder shim: the ``models.core`` surface reached via the exempt ``data`` layer."""
from __future__ import annotations

from models.core import *  # noqa: F401,F403
import structlog
logger = structlog.get_logger(__name__)
