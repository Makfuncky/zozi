"""Finance domain — commission geography services.

Moved from domains/governance/services/finance/ (wrong location).
Provides commission rate and badge tier management for finance domain.
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from domains.finance.ports import create_badge_tier
from domains.finance.ports import create_category_rate
from domains.finance.ports import list_badge_tiers
from domains.finance.ports import list_category_rates
from domains.finance.ports import update_badge_tier
from domains.finance.ports import update_category_rate


def list_rates(db: Session, country_code: str, page: int, page_size: int):
    """List commission category rates for a country."""
    return list_category_rates(db, country_code, page, page_size)


def create_rate(db: Session, country_code: str, payload):
    """Create a commission category rate."""
    return create_category_rate(db, payload, country_code)


def update_rate(db: Session, rate_id: int, country_code: str, payload):
    """Update a commission category rate."""
    return update_category_rate(db, rate_id, country_code, payload)


def list_badge_tiers_service(db: Session, country_code: str, page: int, page_size: int):
    """List commission badge tiers for a country."""
    return list_badge_tiers(db, country_code, page, page_size)


def create_badge_tier_service(db: Session, country_code: str, payload):
    """Create a commission badge tier."""
    return create_badge_tier(db, payload, country_code)


def update_badge_tier_service(db: Session, tier_id: int, country_code: str, payload):
    """Update a commission badge tier."""
    return update_badge_tier(db, tier_id, country_code, payload)


