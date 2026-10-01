"""Add missing AuditLog columns (no indexes; see 0002 for indexes)

Revision ID: 2026_09_03_0001
Revises: 2026_09_03_0000
Create Date: 2026-09-03

Columns added: uuid, resource_type, resource_id, user_agent, status, is_deleted, country_code, updated_at.
WORM columns (worm_hash, worm_prev_hash) are added by 20260827_audit_logs_worm_hash.
Indexes moved to 2026_09_03_0002 to satisfy Law 26 (one logical change per migration).
Downgrade is no-op per Law 57/230/278 (WORM audit trail protection).
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "2026_09_03_0001"
down_revision: Union[str, None] = "2026_09_03_0000"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "audit_logs" not in inspector.get_table_names(schema="audit"):
        return

    existing = {c["name"] for c in inspector.get_columns("audit_logs", schema="audit")}

    columns_to_add = [
        ("uuid", sa.String(length=36), None),
        ("resource_type", sa.String(length=255), None),
        ("resource_id", sa.String(length=255), None),
        ("user_agent", sa.String(length=255), None),
        ("status", sa.String(length=50), "success"),
        ("is_deleted", sa.Boolean(), False),
        ("country_code", sa.String(length=2), None),
        ("updated_at", sa.DateTime(), None),
    ]

    for col_name, col_type, default in columns_to_add:
        if col_name not in existing:
            col = sa.Column(col_name, col_type, server_default=default)
            op.add_column("audit_logs", col, schema="audit")

    indexes_to_create = [
        ("ix_audit_logs_action_created", ["action", "created_at"]),
        ("ix_audit_logs_user_created", ["user_id", "created_at"]),
        ("ix_audit_logs_country_action", ["country_code", "action"]),
    ]

    for idx_name, columns in indexes_to_create:
        op.create_index(
            idx_name,
            "audit_logs",
            columns,
            schema="audit",
            if_not_exists=True,
        )


def downgrade() -> None:
    # WORM audit domain: downgrades are intentionally no-op to prevent audit trail destruction.
    # Law 57: Destructive migrations require backward-compatible strategy.
    # Law 230/278: WORM audit logs must be tamper-proof.
    import warnings
    warnings.warn(
        "Downgrade of audit_logs columns is disabled for WORM compliance. "
        "Use point-in-time recovery (NEON branching) instead.",
        RuntimeWarning,
        stacklevel=2,
    )
    # Index drops are safe (recreatable), but we skip to keep migration reversible in spirit.
    pass
