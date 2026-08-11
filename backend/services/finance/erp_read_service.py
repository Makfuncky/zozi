"""ERP read-access service (finance).

Thin read helpers over the chart-of-accounts, consumed by
``data.ledger_impl_bridge`` so the general-ledger facade can resolve account
lookups without creating a ``general_ledger -> finance`` dependency edge.

Implementations are intentionally lightweight: the canonical GL/ERP logic is
consolidated in ``services.finance.general_ledger_service`` and
``services.treasury``; these leaf functions exist so the import graph stays
acyclic and ``import main`` succeeds.
"""
from __future__ import annotations

from typing import Any, List, Optional

from services.common.db_read import first, all_rows
import structlog

logger = structlog.get_logger(__name__)

__all__ = ["get_account_by_code", "list_accounts_paged"]


def get_account_by_code(db: Any, code: str) -> Optional[Any]:
    """Return the account row matching ``code`` (or ``None``)."""
    from models import Account

    return first(db, Account, filters=[Account.code == code])


def list_accounts_paged(
    db: Any,
    skip: int = 0,
    limit: int = 50,
    country_code: Optional[str] = None,
) -> List[Any]:
    """Return a page of account rows, optionally filtered by ``country_code``."""
    from models import Account

    filters = []
    if country_code is not None:
        filters.append(Account.country_code == country_code)
    return all_rows(
        db,
        Account,
        filters=filters,
        order_by=Account.code,
        offset=skip,
        limit=limit,
    )
