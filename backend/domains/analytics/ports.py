
"""analytics domain - AXIS 4 sanctioned cross-domain READ ports (Law 1/4).

Read-only access to analytics intelligence for other domains. These functions
NEVER import a sibling domain's services (no domain edge); they accept a caller
supplied ``db`` session and run scoped SELECTs against the analytics/ai schemas.

The caller owns the session/transaction. For write intents, publish an event
instead (see ``events.py``).
"""

from __future__ import annotations

from typing import Optional

from sqlalchemy import select

from .models.analytics_schema_models import (
    ExecutiveNews,
    FinancialReport,
    PredictiveSimulation,
)


def read_executive_news(db, country_code: Optional[str] = None, limit: int = 50) -> list:
    """Return recent published executive news, optionally scoped to a country."""
    stmt = select(ExecutiveNews).where(ExecutiveNews.is_deleted == False)  # noqa: E712
    if country_code is not None:
        stmt = stmt.where(ExecutiveNews.country_code == country_code)
    stmt = stmt.order_by(ExecutiveNews.created_at.desc()).limit(limit)
    return db.execute(stmt).scalars().all()


def read_predictive_simulations(db, country_code: Optional[str] = None, limit: int = 50) -> list:
    """Return recent predictive simulations, optionally scoped to a country."""
    stmt = select(PredictiveSimulation).where(PredictiveSimulation.is_deleted == False)  # noqa: E712
    if country_code is not None:
        stmt = stmt.where(PredictiveSimulation.country_code == country_code)
    stmt = stmt.order_by(PredictiveSimulation.created_at.desc()).limit(limit)
    return db.execute(stmt).scalars().all()


def get_financial_report_by_id(db, id_: int):
    """Return FinancialReport by primary key (or None)."""
    return db.get(FinancialReport, id_)


def list_financial_reports(db, limit: int = 100) -> list:
    """Return up to ``limit`` FinancialReport rows, most-recent first."""
    stmt = (
        select(FinancialReport)
        .where(FinancialReport.is_deleted == False)  # noqa: E712
        .order_by(FinancialReport.generated_at.desc())
        .limit(limit)
    )
    return db.execute(stmt).scalars().all()


__all__ = [
    "read_executive_news",
    "read_predictive_simulations",
    "get_financial_report_by_id",
    "list_financial_reports",
    "ExecutiveNews",
    "FinancialReport",
    "PredictiveSimulation",
]
