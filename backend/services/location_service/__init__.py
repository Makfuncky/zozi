"""Location service package.

Exposes geo-resolution helpers used by ``routers.public_location_api_management``. The router
imports ``from location_service.geo_resolver import resolve_ip_location,
reverse_geocode`` -- hence the subpackage layout.
"""
from __future__ import annotations
import structlog
logger = structlog.get_logger(__name__)
