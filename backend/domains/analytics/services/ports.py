"""Analytics domain — sanctioned cross-domain READ surface (ports).

Per ARCHITECTURE_DIAGRAM.md Law 3, cross-domain reads may ONLY happen through a
publishing domain's ports.py. Other domains import these functions instead of
importing domains.analytics.models or domains.analytics.services directly.

These are pure read helpers: no writes, no business decisions, no permission
checks (callers remain responsible for feature gating via rbac).
"""

from __future__ import annotations

from typing import Optional

from sqlalchemy import select

from .events import AnalyticsEvent  # noqa: F401 — re-export for type hints

# Model imports (lazy to avoid circular imports at module load)
def _get_models():
    from domains.analytics.models.analytics_schema_models import (
        ExecutiveNews,
        FinancialReport,
        PredictiveSimulation,
    )
    return ExecutiveNews, FinancialReport, PredictiveSimulation


def read_executive_news(db, country_code: Optional[str] = None, limit: int = 50) -> list:
    """Return recent published executive news, optionally scoped to a country."""
    ExecutiveNews, _, _ = _get_models()
    stmt = select(ExecutiveNews).where(ExecutiveNews.is_deleted == False)  # noqa: E712
    if country_code is not None:
        stmt = stmt.where(ExecutiveNews.country_code == country_code)
    stmt = stmt.order_by(ExecutiveNews.created_at.desc()).limit(limit)
    return db.execute(stmt).scalars().all()


def read_predictive_simulations(db, country_code: Optional[str] = None, limit: int = 50) -> list:
    """Return recent predictive simulations, optionally scoped to a country."""
    _, _, PredictiveSimulation = _get_models()
    stmt = select(PredictiveSimulation).where(PredictiveSimulation.is_deleted == False)  # noqa: E712
    if country_code is not None:
        stmt = stmt.where(PredictiveSimulation.country_code == country_code)
    stmt = stmt.order_by(PredictiveSimulation.created_at.desc()).limit(limit)
    return db.execute(stmt).scalars().all()


def get_financial_report_by_id(db, id_: int):
    """Return FinancialReport by primary key (or None)."""
    _, FinancialReport, _ = _get_models()
    return db.get(FinancialReport, id_)


def list_financial_reports(db, limit: int = 100) -> list:
    """Return up to ``limit`` FinancialReport rows, most-recent first."""
    _, FinancialReport, _ = _get_models()
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
]
