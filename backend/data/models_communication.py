"""Forwarder shim: the ``models.comms`` (chat/communication) surface via the exempt ``data`` layer."""
from __future__ import annotations

from models.comms import *  # noqa: F401,F403
import structlog
logger = structlog.get_logger(__name__)
