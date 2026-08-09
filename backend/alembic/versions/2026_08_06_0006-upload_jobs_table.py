"""upload_jobs_table

Revision ID: 20260806_0006
Revises: 20260806_0005
Create Date: 2026-08-06

Creates the ``upload_jobs`` table backing ``models.UploadJob``. Skipped on
SQLite: the dev/test schema is rebuilt from the ORM metadata via the build
step in ``alembic/env.py``, so the model alone drives the SQLite schema.
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20260806_0006"
down_revision: Union[str, None] = "20260806_0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    if conn.dialect.name == "sqlite":
        return
    op.create_table(
        "upload_jobs",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("uuid", sa.UUID(as_uuid=True), unique=True, nullable=True),
        sa.Column("version", sa.Integer(), nullable=False, server_default=sa.text("1")),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.false(), index=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_by", sa.Integer(), nullable=True),
        sa.Column("created_by", sa.Integer(), nullable=True, index=True),
        sa.Column("updated_by", sa.Integer(), nullable=True, index=True),
        sa.Column("filename", sa.String(255), nullable=False),
        sa.Column("stored_path", sa.String(1024), nullable=True),
        sa.Column("content_type", sa.String(128), nullable=True),
        sa.Column("file_size", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending", index=True),
        sa.Column("progress", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("error_log", sa.Text(), nullable=True),
        sa.Column("country_code", sa.String(10), nullable=True, index=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.Index("ix_upload_jobs_country_created", "country_code", "created_at"),
    )


def downgrade() -> None:
    conn = op.get_bind()
    if conn.dialect.name == "sqlite":
        return
    op.drop_table("upload_jobs")
