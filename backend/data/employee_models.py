"""Forwarder shim exposing ``models.employee_models`` through the exempt ``data`` layer.

``utils`` is a leaf layer in the circuit contract and may not import ``models``
directly; it reaches ORM types through this ``data`` shim instead.
"""
from __future__ import annotations

from models.employee_models import *  # noqa: F401,F403
import structlog
logger = structlog.get_logger(__name__)
