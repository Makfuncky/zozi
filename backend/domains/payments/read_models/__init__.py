"""payments domain — analytics projections (CQRS-lite read models).

These are pure-data DTOs populated by the payments services and consumed by
admin dashboards and reporting endpoints. They do NOT touch the DB directly;
service-layer functions build them.

Per Law 3, cross-domain reads happen via ``ports.py``; these projections are
the data shape consumed by the admin module routers.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal


@dataclass(frozen=True)
class DailyRevenueProjection:
    """Aggregated revenue for a single (date, country, provider) bucket."""
    bucket_date: date
    country_code: str
    provider: str
    gross_amount: Decimal
    net_amount: Decimal
    refund_amount: Decimal
    transaction_count: int
    refund_count: int


@dataclass(frozen=True)
class GatewayHealthProjection:
    """Live health snapshot for a single payment-gateway connection."""
    provider: str
    country_code: str
    is_active: bool
    last_test_status: str  # "ok" | "failed" | "untested"
    last_tested_at: datetime | None
    success_rate_24h: float
    p95_latency_ms_24h: float


@dataclass(frozen=True)
class PaymentMethodShareProjection:
    """Distribution of payment methods used in the last N days."""
    country_code: str
    window_days: int
    shares: dict[str, float]  # {"card": 0.62, "wallet": 0.27, "bank_account": 0.11}


@dataclass(frozen=True)
class ChargebackSummaryProjection:
    country_code: str
    open_count: int
    won_count: int
    lost_count: int
    total_disputed_amount: Decimal
    total_won_amount: Decimal
    total_lost_amount: Decimal


@dataclass(frozen=True)
class RefundBreakdownProjection:
    country_code: str
    window_days: int
    by_reason: dict[str, int] = field(default_factory=dict)
    by_provider: dict[str, int] = field(default_factory=dict)
    total_amount: Decimal = Decimal("0")


__all__ = [
    "DailyRevenueProjection",
    "GatewayHealthProjection",
    "PaymentMethodShareProjection",
    "ChargebackSummaryProjection",
    "RefundBreakdownProjection",
]