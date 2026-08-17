"""Treasury service package.

Holds treasury domain services (query, cash-write, auto-payout) so that raw
SQL and write operations live in the service layer rather than in routers.
"""
from __future__ import annotations
import structlog
logger = structlog.get_logger(__name__)
