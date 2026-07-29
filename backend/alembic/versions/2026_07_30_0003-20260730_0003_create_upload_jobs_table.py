"""create_upload_jobs_table

Revision ID: 20260730_0003
Revises: 20260730_0002
Create Date: 2026-07-30
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260730_0003"
down_revision: Union[str, None] = "20260730_0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    if conn.dialect.name == "sqlite":
        op.execute("CREATE TABLE IF NOT EXISTS upload_jobs (id INTEGER NOT NULL PRIMARY KEY, supplier_id INTEGER NOT NULL, filename VARCHAR(512) NOT NULL, status VARCHAR(32) NOT NULL, progress FLOAT NOT NULL, strategy_winner VARCHAR(64), strategy_score FLOAT, ai_result JSON, product_id INTEGER, error_message TEXT, image_url VARCHAR(1024), processed_image_url VARCHAR(1024), started_at DATETIME, completed_at DATETIME, created_at DATETIME NOT NULL, updated_at DATETIME NOT NULL, stt_duration_ms FLOAT, nlp_duration_ms FLOAT, bg_duration_ms FLOAT, ai_duration_ms FLOAT, total_duration_ms FLOAT, CONSTRAINT fk_upload_jobs_supplier_id FOREIGN KEY(supplier_id) REFERENCES users (id), CONSTRAINT fk_upload_jobs_product_id FOREIGN KEY(product_id) REFERENCES products (id))")
        op.execute("CREATE INDEX IF NOT EXISTS ix_upload_jobs_id ON upload_jobs (id)")
        op.execute("CREATE INDEX IF NOT EXISTS ix_upload_jobs_status ON upload_jobs (status)")
        op.execute("CREATE INDEX IF NOT EXISTS ix_upload_jobs_supplier_id ON upload_jobs (supplier_id)")
    else:
        op.create_table(
            "upload_jobs",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("supplier_id", sa.Integer(), nullable=False),
            sa.Column("filename", sa.String(length=512), nullable=False),
            sa.Column("status", sa.String(length=32), nullable=False),
            sa.Column("progress", sa.Float(), nullable=False),
            sa.Column("strategy_winner", sa.String(length=64), nullable=True),
            sa.Column("strategy_score", sa.Float(), nullable=True),
            sa.Column("ai_result", sa.JSON(), nullable=True),
            sa.Column("product_id", sa.Integer(), nullable=True),
            sa.Column("error_message", sa.Text(), nullable=True),
            sa.Column("image_url", sa.String(length=1024), nullable=True),
            sa.Column("processed_image_url", sa.String(length=1024), nullable=True),
            sa.Column("started_at", sa.DateTime(), nullable=True),
            sa.Column("completed_at", sa.DateTime(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.Column("stt_duration_ms", sa.Float(), nullable=True),
            sa.Column("nlp_duration_ms", sa.Float(), nullable=True),
            sa.Column("bg_duration_ms", sa.Float(), nullable=True),
            sa.Column("ai_duration_ms", sa.Float(), nullable=True),
            sa.Column("total_duration_ms", sa.Float(), nullable=True),
            sa.ForeignKeyConstraint(["product_id"], ["products.id"], name="fk_upload_jobs_product_id"),
            sa.ForeignKeyConstraint(["supplier_id"], ["users.id"], name="fk_upload_jobs_supplier_id"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_upload_jobs_id", "upload_jobs", ["id"], unique=False)
        op.create_index("ix_upload_jobs_status", "upload_jobs", ["status"], unique=False)
        op.create_index("ix_upload_jobs_supplier_id", "upload_jobs", ["supplier_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_upload_jobs_supplier_id", table_name="upload_jobs")
    op.drop_index("ix_upload_jobs_status", table_name="upload_jobs")
    op.drop_index("ix_upload_jobs_id", table_name="upload_jobs")
    op.drop_table("upload_jobs")
