"""add_logistics_acceptance_vehicle_overrides

Revision ID: c7d8e9f0a1b2
Revises: ab8d4b3ead2b
Create Date: 2026-04-10 22:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c7d8e9f0a1b2"
down_revision: Union[str, Sequence[str], None] = "ab8d4b3ead2b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _is_sqlite() -> bool:
    bind = op.get_bind()
    return bind.dialect.name == "sqlite"


def _set_sqlite_foreign_keys(enabled: bool) -> None:
    if _is_sqlite():
        op.execute(f"PRAGMA foreign_keys={'ON' if enabled else 'OFF'}")


def upgrade() -> None:
    _set_sqlite_foreign_keys(False)
    with op.batch_alter_table("shipments", schema=None) as batch_op:
        batch_op.add_column(sa.Column("accepted_vehicle_rule_id", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("accepted_vehicle_type", sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column("accepted_vehicle_multiplier", sa.Numeric(precision=8, scale=4), nullable=True))
        batch_op.add_column(sa.Column("accepted_vehicle_selected_at", sa.DateTime(), nullable=True))
        batch_op.create_foreign_key(
            "fk_shipments_accepted_vehicle_rule",
            "logistics_vehicle_rules",
            ["accepted_vehicle_rule_id"],
            ["id"],
        )

    with op.batch_alter_table("order_logistics_allocations", schema=None) as batch_op:
        batch_op.add_column(sa.Column("accepted_vehicle_rule_id", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("accepted_vehicle_type", sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column("accepted_vehicle_multiplier", sa.Numeric(precision=8, scale=4), nullable=True))
        batch_op.add_column(sa.Column("accepted_shipping_amount", sa.Numeric(precision=12, scale=2), nullable=True))
        batch_op.add_column(sa.Column("accepted_pickup_charge", sa.Numeric(precision=12, scale=2), nullable=True))
        batch_op.add_column(sa.Column("accepted_dropoff_charge", sa.Numeric(precision=12, scale=2), nullable=True))
        batch_op.add_column(sa.Column("accepted_pricing_breakdown_json", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("accepted_at", sa.DateTime(), nullable=True))
        batch_op.create_index(
            "ix_order_logistics_allocations_accepted_vehicle_rule_id",
            ["accepted_vehicle_rule_id"],
            unique=False,
        )
        batch_op.create_foreign_key(
            "fk_order_logistics_allocations_accepted_vehicle_rule",
            "logistics_vehicle_rules",
            ["accepted_vehicle_rule_id"],
            ["id"],
        )
    _set_sqlite_foreign_keys(True)


def downgrade() -> None:
    _set_sqlite_foreign_keys(False)
    with op.batch_alter_table("order_logistics_allocations", schema=None) as batch_op:
        batch_op.drop_constraint("fk_order_logistics_allocations_accepted_vehicle_rule", type_="foreignkey")
        batch_op.drop_index("ix_order_logistics_allocations_accepted_vehicle_rule_id")
        batch_op.drop_column("accepted_at")
        batch_op.drop_column("accepted_pricing_breakdown_json")
        batch_op.drop_column("accepted_dropoff_charge")
        batch_op.drop_column("accepted_pickup_charge")
        batch_op.drop_column("accepted_shipping_amount")
        batch_op.drop_column("accepted_vehicle_multiplier")
        batch_op.drop_column("accepted_vehicle_type")
        batch_op.drop_column("accepted_vehicle_rule_id")

    with op.batch_alter_table("shipments", schema=None) as batch_op:
        batch_op.drop_constraint("fk_shipments_accepted_vehicle_rule", type_="foreignkey")
        batch_op.drop_column("accepted_vehicle_selected_at")
        batch_op.drop_column("accepted_vehicle_multiplier")
        batch_op.drop_column("accepted_vehicle_type")
        batch_op.drop_column("accepted_vehicle_rule_id")
    _set_sqlite_foreign_keys(True)

