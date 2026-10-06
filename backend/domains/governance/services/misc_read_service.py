"""Read helpers shared across domains.

These were imported by name from ``domains.governance.ports`` but were never
implemented anywhere, so the importing call sites raised ImportError:

  domains/country/services/core/country_service.py:949  get_country_commissions
  domains/country/services/core/country_service.py:1481 get_users_by_ids
"""
from __future__ import annotations

from typing import Iterable, List

from sqlalchemy import select
from sqlalchemy.orm import Session


def get_country_commissions(db: Session, country_code: str) -> List[object]:
    """Active supplier commission rows for one country."""
    from domains.governance.models.admin import SupplierCountryCommission

    stmt = select(SupplierCountryCommission).where(
        SupplierCountryCommission.country_code == (country_code or "").upper(),
        SupplierCountryCommission.is_deleted.is_(False),
    )
    return list(db.execute(stmt).scalars().all())


def get_users_by_ids(db: Session, user_ids: Iterable[int]) -> List[object]:
    """Bulk user lookup, preserving no particular order."""
    from domains.accounts.models.user import User

    ids = [int(i) for i in (user_ids or []) if i is not None]
    if not ids:
        return []
    return list(db.execute(select(User).where(User.id.in_(ids))).scalars().all())


__all__ = ["get_country_commissions", "get_users_by_ids"]