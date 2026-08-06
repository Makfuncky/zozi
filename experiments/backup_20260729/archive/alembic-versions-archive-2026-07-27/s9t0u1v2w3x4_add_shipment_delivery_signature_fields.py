"""add shipment delivery signature fields

Revision ID: s9t0u1v2w3x4
Revises: r7s8t9u0v1w2
Create Date: 2026-03-29 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision = 's9t0u1v2w3x4'
down_revision = "r7s8t9u0v1w2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    columns = {column["name"] for column in inspector.get_columns("shipments")}

    if "delivery_signature_name" not in columns:
        op.add_column("shipments", sa.Column("delivery_signature_name", sa.String(length=200), nullable=True))
    if "delivery_signature_data_url" not in columns:
        op.add_column("shipments", sa.Column("delivery_signature_data_url", sa.Text(), nullable=True))
    if "delivery_signature_captured_at" not in columns:
        op.add_column("shipments", sa.Column("delivery_signature_captured_at", sa.DateTime(), nullable=True))


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    columns = {column["name"] for column in inspector.get_columns("shipments")}

    if "delivery_signature_captured_at" in columns:
        op.drop_column("shipments", "delivery_signature_captured_at")
    if "delivery_signature_data_url" in columns:
        op.drop_column("shipments", "delivery_signature_data_url")
    if "delivery_signature_name" in columns:
        op.drop_column("shipments", "delivery_signature_name")

