"""add shipment confirmation requests

Revision ID: u1v2w3x4y5z6
Revises: t1u2v3w4x5y6
Create Date: 2026-03-30 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision = "u1v2w3x4y5z6"
down_revision = "t1u2v3w4x5y6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if inspector.has_table("shipment_confirmations"):
        return

    op.create_table(
        "shipment_confirmations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("shipment_id", sa.Integer(), nullable=False),
        sa.Column("order_id", sa.Integer(), nullable=False),
        sa.Column("supplier_id", sa.Integer(), nullable=False),
        sa.Column("requester_user_id", sa.Integer(), nullable=True),
        sa.Column("requester_role", sa.String(length=50), nullable=False, server_default="logistics_partner"),
        sa.Column("target_user_id", sa.Integer(), nullable=False),
        sa.Column("target_role", sa.String(length=50), nullable=False),
        sa.Column("confirmation_type", sa.String(length=30), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="pending"),
        sa.Column("requested_status", sa.String(length=50), nullable=False),
        sa.Column("requested_event_type", sa.String(length=80), nullable=False),
        sa.Column("current_hub", sa.Text(), nullable=True),
        sa.Column("tracking_number", sa.String(length=200), nullable=True),
        sa.Column("delivery_signature_name", sa.String(length=200), nullable=True),
        sa.Column("delivery_signature_data_url", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("response_notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("responded_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"]),
        sa.ForeignKeyConstraint(["requester_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["shipment_id"], ["shipments.id"]),
        sa.ForeignKeyConstraint(["supplier_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["target_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_shipment_confirmations_confirmation_type"), "shipment_confirmations", ["confirmation_type"], unique=False)
    op.create_index(op.f("ix_shipment_confirmations_created_at"), "shipment_confirmations", ["created_at"], unique=False)
    op.create_index(op.f("ix_shipment_confirmations_id"), "shipment_confirmations", ["id"], unique=False)
    op.create_index(op.f("ix_shipment_confirmations_order_id"), "shipment_confirmations", ["order_id"], unique=False)
    op.create_index(op.f("ix_shipment_confirmations_order_status"), "shipment_confirmations", ["order_id", "status"], unique=False)
    op.create_index(op.f("ix_shipment_confirmations_requested_status"), "shipment_confirmations", ["requested_status"], unique=False)
    op.create_index(op.f("ix_shipment_confirmations_shipment_created"), "shipment_confirmations", ["shipment_id", "created_at"], unique=False)
    op.create_index(op.f("ix_shipment_confirmations_shipment_id"), "shipment_confirmations", ["shipment_id"], unique=False)
    op.create_index(op.f("ix_shipment_confirmations_status"), "shipment_confirmations", ["status"], unique=False)
    op.create_index(op.f("ix_shipment_confirmations_supplier_id"), "shipment_confirmations", ["supplier_id"], unique=False)
    op.create_index(op.f("ix_shipment_confirmations_target_status"), "shipment_confirmations", ["target_user_id", "status"], unique=False)
    op.create_index(op.f("ix_shipment_confirmations_target_user_id"), "shipment_confirmations", ["target_user_id"], unique=False)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if not inspector.has_table("shipment_confirmations"):
        return

    op.drop_index(op.f("ix_shipment_confirmations_target_user_id"), table_name="shipment_confirmations")
    op.drop_index(op.f("ix_shipment_confirmations_target_status"), table_name="shipment_confirmations")
    op.drop_index(op.f("ix_shipment_confirmations_supplier_id"), table_name="shipment_confirmations")
    op.drop_index(op.f("ix_shipment_confirmations_status"), table_name="shipment_confirmations")
    op.drop_index(op.f("ix_shipment_confirmations_shipment_id"), table_name="shipment_confirmations")
    op.drop_index(op.f("ix_shipment_confirmations_shipment_created"), table_name="shipment_confirmations")
    op.drop_index(op.f("ix_shipment_confirmations_requested_status"), table_name="shipment_confirmations")
    op.drop_index(op.f("ix_shipment_confirmations_order_status"), table_name="shipment_confirmations")
    op.drop_index(op.f("ix_shipment_confirmations_order_id"), table_name="shipment_confirmations")
    op.drop_index(op.f("ix_shipment_confirmations_id"), table_name="shipment_confirmations")
    op.drop_index(op.f("ix_shipment_confirmations_created_at"), table_name="shipment_confirmations")
    op.drop_index(op.f("ix_shipment_confirmations_confirmation_type"), table_name="shipment_confirmations")
    op.drop_table("shipment_confirmations")

