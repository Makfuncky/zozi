"""supply_chain_shipment_events

Revision ID: f7e8d9c0b1a2
Revises: c4d5e6f7a8b9
Create Date: 2026-03-24
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "f7e8d9c0b1a2"
down_revision: Union[str, Sequence[str], None] = "c4d5e6f7a8b9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = __import__("sqlalchemy").inspect(bind)
    existing_tables = inspector.get_table_names()
    shipment_cols = {c["name"] for c in inspector.get_columns("shipments")} if "shipments" in existing_tables else set()

    # Add columns to shipments (defensive)
    new_ship_cols = {
        "distribution_channel": sa.Column("distribution_channel", sa.String(length=100), nullable=True),
        "current_hub": sa.Column("current_hub", sa.String(length=200), nullable=True),
        "scan_code": sa.Column("scan_code", sa.String(length=120), nullable=True),
    }
    ship_to_add = {k: v for k, v in new_ship_cols.items() if k not in shipment_cols}
    if ship_to_add:
        with op.batch_alter_table("shipments", schema=None) as batch_op:
            for col in ship_to_add.values():
                batch_op.add_column(col)
            if "scan_code" in ship_to_add:
                batch_op.create_index(batch_op.f("ix_shipments_scan_code"), ["scan_code"], unique=False)

    if "shipment_events" not in existing_tables:
        op.create_table(
            "shipment_events",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("shipment_id", sa.Integer(), nullable=False),
            sa.Column("order_id", sa.Integer(), nullable=False),
            sa.Column("supplier_id", sa.Integer(), nullable=False),
            sa.Column("actor_user_id", sa.Integer(), nullable=True),
            sa.Column("actor_role", sa.String(length=50), nullable=False),
            sa.Column("event_type", sa.String(length=80), nullable=False),
            sa.Column("status_after", sa.String(length=50), nullable=True),
            sa.Column("distribution_channel", sa.String(length=100), nullable=True),
            sa.Column("location", sa.String(length=200), nullable=True),
            sa.Column("scan_code", sa.String(length=120), nullable=True),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"]),
            sa.ForeignKeyConstraint(["order_id"], ["orders.id"]),
            sa.ForeignKeyConstraint(["shipment_id"], ["shipments.id"]),
            sa.ForeignKeyConstraint(["supplier_id"], ["users.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(op.f("ix_shipment_events_id"), "shipment_events", ["id"], unique=False)
        op.create_index(op.f("ix_shipment_events_scan_code"), "shipment_events", ["scan_code"], unique=False)
        op.create_index(
            "ix_shipment_events_shipment_created",
            "shipment_events",
            ["shipment_id", "created_at"],
            unique=False,
        )
        op.create_index(
            "ix_shipment_events_order_created",
            "shipment_events",
            ["order_id", "created_at"],
            unique=False,
        )


def downgrade() -> None:
    op.drop_index("ix_shipment_events_order_created", table_name="shipment_events")
    op.drop_index("ix_shipment_events_shipment_created", table_name="shipment_events")
    op.drop_index(op.f("ix_shipment_events_scan_code"), table_name="shipment_events")
    op.drop_index(op.f("ix_shipment_events_id"), table_name="shipment_events")
    op.drop_table("shipment_events")

    with op.batch_alter_table("shipments", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_shipments_scan_code"))
        batch_op.drop_column("scan_code")
        batch_op.drop_column("current_hub")
        batch_op.drop_column("distribution_channel")

