"""governance domain — CQRS-lite read-model projections.

Flattened, read-optimised views of governance data for dashboards and
cross-domain queries. These are the sanctioned read surface for governance
data consumed by other domains via ports.py.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class AdminActivityProjection:
    """Flattened view of an admin activity log entry."""
    id: int
    admin_id: int
    admin_username: str
    action: str
    resource_type: Optional[str] = None
    resource_id: Optional[int] = None
    details: Optional[str] = None
    created_at: Optional[str] = None


@dataclass
class PermissionProjection:
    """Flattened view of a permission atom."""
    id: int
    name: str
    slug: str
    category: Optional[str] = None
    scope: str = "global"
    is_active: bool = True


@dataclass
class RolePermissionProjection:
    """View of a role's effective permissions."""
    role: str
    permissions: list[str] = field(default_factory=list)
    country_code: Optional[str] = None


@dataclass
class UserPermissionProjection:
    """View of a user's effective permission set."""
    user_id: int
    role: str
    permissions: list[str] = field(default_factory=list)
    country_code: Optional[str] = None


@dataclass
class FraudEventProjection:
    """Flattened view of a fraud detection event."""
    id: int
    event_type: str
    risk_score: float
    status: str
    user_id: Optional[int] = None
    description: Optional[str] = None
    created_at: Optional[str] = None


@dataclass
class FraudCaseProjection:
    """Flattened view of a fraud case."""
    id: int
    case_type: str
    status: str
    severity: str
    assigned_to: Optional[int] = None
    created_at: Optional[str] = None


@dataclass
class IncidentProjection:
    """Flattened view of a security incident."""
    id: int
    title: str
    severity: str
    status: str
    action_items_count: int = 0
    created_at: Optional[str] = None


@dataclass
class SupplierDisputeProjection:
    """Flattened view of a supplier dispute."""
    id: int
    supplier_id: int
    order_id: Optional[int] = None
    status: str = "open"
    amount: Optional[float] = None
    created_at: Optional[str] = None


@dataclass
class TreasuryPipelineProjection:
    """View of a single order in the treasury settlement pipeline."""
    order_id: int
    order_status: str
    order_total: float
    supplier_id: Optional[int] = None
    payment_method: Optional[str] = None
    payment_status: Optional[str] = None
    supplier_settlement_status: Optional[str] = None
    supplier_payout_status: Optional[str] = None
    commission: Optional[dict] = None
    stage: Optional[str] = None


@dataclass
class AnalyticsSnapshotProjection:
    """Flattened view of an analytics snapshot."""
    id: int
    metric: str
    value: Optional[float] = None
    dimensions: Optional[dict] = None
    country_code: Optional[str] = None
    created_at: Optional[str] = None


@dataclass
class RetentionJobProjection:
    """View of a data retention job run."""
    id: int
    job_type: str
    status: str
    records_processed: int = 0
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
