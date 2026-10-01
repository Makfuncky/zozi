"""customers/recommendations sub-domain — personalized recommendation services."""
from __future__ import annotations

from domains.customers.services.recommendations.recommendation_service import (
    get_last_seen,
    get_may_you_like,
)

__all__ = [
    "get_last_seen",
    "get_may_you_like",
]
