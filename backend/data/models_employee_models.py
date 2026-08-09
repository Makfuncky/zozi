"""Forwarder shim: the ``models.employee_models`` surface via the exempt ``data`` layer."""
from __future__ import annotations

from models.employee_models import *  # noqa: F401,F403
import structlog
logger = structlog.get_logger(__name__)
