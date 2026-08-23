"""governance domain — read-model projections package."""
from .governance_read_models import (
    AdminActivityProjection,
    AnalyticsSnapshotProjection,
    FraudCaseProjection,
    FraudEventProjection,
    IncidentProjection,
    PermissionProjection,
    RetentionJobProjection,
    RolePermissionProjection,
    SupplierDisputeProjection,
    TreasuryPipelineProjection,
    UserPermissionProjection,
)

__all__ = [
    "AdminActivityProjection",
    "AnalyticsSnapshotProjection",
    "FraudCaseProjection",
    "FraudEventProjection",
    "IncidentProjection",
    "PermissionProjection",
    "RetentionJobProjection",
    "RolePermissionProjection",
    "SupplierDisputeProjection",
    "TreasuryPipelineProjection",
    "UserPermissionProjection",
]


# === Merged from accounts/__init__.py ===

# CQRS-lite read models for the `accounts` domain.
# Sanctioned cross-domain READ surface (ARCHITECTURE_DIAGRAM.md Sec.3).
# Populated incrementally as projections are extracted from write services.

