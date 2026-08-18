"""media_add_audit_softdelete_mixins_and_rename_ai_result

Revision ID: 20260806_0002
Revises: 20260806_0001
Create Date: 2026-08-06

Brings the media-domain ORM models in line with the mandatory column contract
(DBA03) and the JSON-column naming convention (DBA11):

  - media.media_assets           gains AuditMixin + SoftDeleteMixin columns
  - media.media_upload_sessions  gains AuditMixin + SoftDeleteMixin columns
  - ai.upload_jobs               gains TenantMixin + AuditMixin + SoftDeleteMixin
                                   columns (it previously had none of them)
  - ai.upload_jobs.ai_result     renamed to ai_result_json (DBA11)

Idempotent and skipped on SQLite: the dev/test database is recreated from the
ORM metadata via the build step in ``alembic/env.py``, so the model
changes alone drive the SQLite schema.
"""
from __future__ import annotations
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

from alembic.migration_helpers import safe_add_column, safe_create_index, safe_drop_index, safe_drop_column


revision: str = "20260806_0002"
down_revision: Union[str, None] = "20260806_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _media_assets_columns() -> list:
    return [
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("created_by", sa.Integer(), nullable=True, index=True),
        sa.Column("updated_by", sa.Integer(), nullable=True, index=True),
        sa.Column("deleted_by", sa.Integer(), nullable=True),
        sa.Column("delete_reason", sa.Text(), nullable=True),
    ]


def _media_upload_sessions_columns() -> list:
    return [
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_by", sa.Integer(), nullable=True, index=True),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.false(), index=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_by", sa.Integer(), nullable=True),
        sa.Column("delete_reason", sa.Text(), nullable=True),
    ]


def _upload_jobs_columns() -> list:
    return [
        sa.Column("uuid", sa.String(36), nullable=True, unique=True, index=True),
        sa.Column("country_code", sa.String(3), nullable=False, server_default="OMR", index=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true(), index=True),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_by", sa.Integer(), nullable=True, index=True),
        sa.Column("updated_by", sa.Integer(), nullable=True, index=True),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.false(), index=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_by", sa.Integer(), nullable=True),
        sa.Column("delete_reason", sa.Text(), nullable=True),
    ]


def upgrade() -> None:
    conn = op.get_bind()
    if conn.dialect.name == "sqlite":
        return

    for col in _media_assets_columns():
        safe_add_column(op, "media_assets", col, schema="media")
    for col in _media_upload_sessions_columns():
        safe_add_column(op, "media_upload_sessions", col, schema="media")

    for col in _upload_jobs_columns():
        safe_add_column(op, "upload_jobs", col, schema="ai")

    # DBA11: rename the JSON result column.
    conn.execute(
        text('ALTER TABLE IF EXISTS ai.upload_jobs RENAME COLUMN ai_result TO ai_result_json')
    )
    safe_drop_index(op, "ix_upload_jobs_ai_result_gin", "upload_jobs", schema="ai")
    safe_create_index(
        op, "ix_upload_jobs_ai_result_json_gin", "upload_jobs",
        ["ai_result_json"], schema="ai", postgresql_using="gin",
    )


def downgrade() -> None:
    conn = op.get_bind()
    if conn.dialect.name == "sqlite":
        return

    safe_drop_index(op, "ix_upload_jobs_ai_result_json_gin", "upload_jobs", schema="ai")
    safe_create_index(
        op, "ix_upload_jobs_ai_result_gin", "upload_jobs",
        ["ai_result"], schema="ai", postgresql_using="gin",
    )
    conn.execute(
        text('ALTER TABLE IF EXISTS ai.upload_jobs RENAME COLUMN ai_result_json TO ai_result')
    )

    for col in reversed(_upload_jobs_columns()):
        safe_drop_column(op, "upload_jobs", col.name, schema="ai")
    for col in reversed(_media_upload_sessions_columns()):
        safe_drop_column(op, "media_upload_sessions", col.name, schema="media")
    for col in reversed(_media_assets_columns()):
        safe_drop_column(op, "media_assets", col.name, schema="media")
