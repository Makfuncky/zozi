"""Add composite indexes for audit_logs and command_center_views

Revision ID: 2026_09_03_0002
Revises: 2026_09_03_0001
Create Date: 2026-09-03

Indexes added (Law 45/53): entity_time, country_time, status_time, ip, resource, command_center_user_default.
Separated from column migration (0001) per Law 26 (one logical change per migration).
Downgrade drops indexes (safe, recreatable).
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "2026_09_03_0002"
down_revision: Union[str, None] = "2026_09_03_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if "audit_logs" in inspector.get_table_names(schema="audit"):
        indexes_to_create = [
            ("ix_audit_logs_entity_time", ["entity_type", "entity_id", "created_at"]),
            ("ix_audit_logs_country_time", ["country_code", "created_at"]),
            ("ix_audit_logs_status_time", ["status", "created_at"]),
            ("ix_audit_logs_ip", ["ip_address"]),
            ("ix_audit_logs_resource", ["resource_type", "resource_id"]),
        ]
        for idx_name, columns in indexes_to_create:
            op.create_index(
                idx_name,
                "audit_logs",
                columns,
                schema="audit",
                if_not_exists=True,
            )

    if "command_center_views" in inspector.get_table_names(schema="audit"):
        op.create_index(
            "ix_command_center_user_default",
            "command_center_views",
            ["user_id", "is_default"],
            schema="audit",
            if_not_exists=True,
        )


def downgrade() -> None:
    indexes_to_drop_audit = [
        "ix_audit_logs_resource",
        "ix_audit_logs_ip",
        "ix_audit_logs_status_time",
        "ix_audit_logs_country_time",
        "ix_audit_logs_entity_time",
    ]
    for idx_name in indexes_to_drop_audit:
        op.drop_index(idx_name, table_name="audit_logs", schema="audit", if_exists=True)

    op.drop_index(
        "ix_command_center_user_default",
        table_name="command_center_views",
        schema="audit",
        if_exists=True,
    )
