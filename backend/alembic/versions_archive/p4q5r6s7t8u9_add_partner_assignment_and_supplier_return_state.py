"""add_partner_assignment_and_supplier_return_state

Revision ID: p4q5r6s7t8u9
Revises: n1o2p3q4r5s6
Create Date: 2026-03-28 11:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision: str = "p4q5r6s7t8u9"
down_revision: Union[str, Sequence[str], None] = "n1o2p3q4r5s6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    table_names = set(inspector.get_table_names())

    if "return_requests" in table_names:
        return_request_columns = {column["name"] for column in inspector.get_columns("return_requests")}
        if "supplier_review_state" not in return_request_columns:
            with op.batch_alter_table("return_requests", schema=None) as batch_op:
                batch_op.add_column(sa.Column("supplier_review_state", sa.Text(), nullable=True))

    if "shipments" not in table_names or "logistics_partners" not in table_names:
        return

    shipment_columns = {column["name"] for column in inspector.get_columns("shipments")}
    shipment_indexes = {index["name"] for index in inspector.get_indexes("shipments") if index.get("name")}
    shipment_foreign_keys = inspector.get_foreign_keys("shipments")
    shipment_fk_names = {foreign_key.get("name") for foreign_key in shipment_foreign_keys if foreign_key.get("name")}
    has_assigned_partner_fk = (
        "fk_shipments_assigned_partner_id_logistics_partners" in shipment_fk_names
        or any(
            foreign_key.get("referred_table") == "logistics_partners"
            and foreign_key.get("constrained_columns") == ["assigned_partner_id"]
            for foreign_key in shipment_foreign_keys
        )
    )

    needs_assigned_partner_column = "assigned_partner_id" not in shipment_columns
    needs_assigned_partner_index = "ix_shipments_assigned_partner_id" not in shipment_indexes
    needs_partner_status_index = "ix_shipments_partner_status" not in shipment_indexes

    if (
        needs_assigned_partner_column
        or needs_assigned_partner_index
        or needs_partner_status_index
        or not has_assigned_partner_fk
    ):
        with op.batch_alter_table("shipments", schema=None) as batch_op:
            if needs_assigned_partner_column:
                batch_op.add_column(sa.Column("assigned_partner_id", sa.Integer(), nullable=True))
            if needs_assigned_partner_index:
                batch_op.create_index("ix_shipments_assigned_partner_id", ["assigned_partner_id"], unique=False)
            if needs_partner_status_index:
                batch_op.create_index("ix_shipments_partner_status", ["assigned_partner_id", "status"], unique=False)
            if not has_assigned_partner_fk:
                batch_op.create_foreign_key(
                    "fk_shipments_assigned_partner_id_logistics_partners",
                    "logistics_partners",
                    ["assigned_partner_id"],
                    ["id"],
                )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    table_names = set(inspector.get_table_names())

    if "shipments" in table_names:
        shipment_columns = {column["name"] for column in inspector.get_columns("shipments")}
        shipment_indexes = {index["name"] for index in inspector.get_indexes("shipments") if index.get("name")}
        shipment_foreign_keys = inspector.get_foreign_keys("shipments")
        shipment_fk_names = {foreign_key.get("name") for foreign_key in shipment_foreign_keys if foreign_key.get("name")}

        if (
            "assigned_partner_id" in shipment_columns
            or "ix_shipments_assigned_partner_id" in shipment_indexes
            or "ix_shipments_partner_status" in shipment_indexes
            or "fk_shipments_assigned_partner_id_logistics_partners" in shipment_fk_names
        ):
            with op.batch_alter_table("shipments", schema=None) as batch_op:
                if "fk_shipments_assigned_partner_id_logistics_partners" in shipment_fk_names:
                    batch_op.drop_constraint("fk_shipments_assigned_partner_id_logistics_partners", type_="foreignkey")
                if "ix_shipments_partner_status" in shipment_indexes:
                    batch_op.drop_index("ix_shipments_partner_status")
                if "ix_shipments_assigned_partner_id" in shipment_indexes:
                    batch_op.drop_index("ix_shipments_assigned_partner_id")
                if "assigned_partner_id" in shipment_columns:
                    batch_op.drop_column("assigned_partner_id")

    if "return_requests" in table_names:
        return_request_columns = {column["name"] for column in inspector.get_columns("return_requests")}
        if "supplier_review_state" in return_request_columns:
            with op.batch_alter_table("return_requests", schema=None) as batch_op:
                batch_op.drop_column("supplier_review_state")

