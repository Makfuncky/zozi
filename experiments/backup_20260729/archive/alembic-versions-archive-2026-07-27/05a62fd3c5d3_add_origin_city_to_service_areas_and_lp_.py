"""add_origin_city_to_service_areas_and_lp_document_table

Revision ID: 05a62fd3c5d3
Revises: f8a9b0c1d2e3
Create Date: 2026-04-05 21:08:16.301876

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '05a62fd3c5d3'
down_revision: Union[str, Sequence[str], None] = 'f8a9b0c1d2e3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add origin_city to logistics_partner_service_areas and create logistics_partner_documents table."""
    inspector = sa.inspect(op.get_bind())
    table_names = set(inspector.get_table_names())

    # Add origin_city column only if not already present (idempotent)
    existing_cols = {
        column["name"]
        for column in inspector.get_columns("logistics_partner_service_areas")
    } if "logistics_partner_service_areas" in table_names else set()
    if "logistics_partner_service_areas" in table_names and "origin_city" not in existing_cols:
        with op.batch_alter_table("logistics_partner_service_areas") as batch_op:
            batch_op.add_column(sa.Column("origin_city", sa.String(length=120), nullable=True))
            batch_op.create_index("ix_lp_service_areas_origin_city", ["origin_city"], unique=False)

    # Create logistics_partner_documents table only if not already present
    if "logistics_partner_documents" not in table_names:
        op.create_table(
            "logistics_partner_documents",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("partner_id", sa.Integer(), sa.ForeignKey("logistics_partners.id"), nullable=False),
            sa.Column("document_type", sa.String(length=80), nullable=False),
            sa.Column("document_name", sa.String(length=200), nullable=False),
            sa.Column("file_url", sa.String(length=500), nullable=False),
            sa.Column("status", sa.String(length=30), nullable=True),
            sa.Column("expires_at", sa.DateTime(), nullable=True),
            sa.Column("review_note", sa.Text(), nullable=True),
            sa.Column("reviewed_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
            sa.Column("reviewed_at", sa.DateTime(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.Column("updated_at", sa.DateTime(), nullable=True),
            sa.PrimaryKeyConstraint("id"),
        )
        with op.batch_alter_table("logistics_partner_documents") as batch_op:
            batch_op.create_index("ix_lp_docs_id", ["id"], unique=False)
            batch_op.create_index("ix_lp_docs_partner_id", ["partner_id"], unique=False)
            batch_op.create_index("ix_lp_docs_status", ["status"], unique=False)
            batch_op.create_index("ix_lp_docs_doc_type", ["document_type", "status"], unique=False)
            batch_op.create_index("ix_lp_docs_partner_status", ["partner_id", "status"], unique=False)


def downgrade() -> None:
    """Reverse the migration."""
    inspector = sa.inspect(op.get_bind())
    table_names = set(inspector.get_table_names())

    if "logistics_partner_documents" in table_names:
        op.drop_table("logistics_partner_documents")

    if "logistics_partner_service_areas" in table_names:
        service_area_columns = {column["name"] for column in inspector.get_columns("logistics_partner_service_areas")}
        service_area_indexes = {index["name"] for index in inspector.get_indexes("logistics_partner_service_areas")}
        with op.batch_alter_table("logistics_partner_service_areas") as batch_op:
            if "ix_lp_service_areas_origin_city" in service_area_indexes:
                batch_op.drop_index("ix_lp_service_areas_origin_city")
            if "origin_city" in service_area_columns:
                batch_op.drop_column("origin_city")

