"""add_shipment_package_fields_and_return_intent

Revision ID: k2l3m4n5o6p7
Revises: j1k2l3m4n5o6
Create Date: 2026-03-27 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision: str = "k2l3m4n5o6p7"
down_revision: Union[str, Sequence[str], None] = "j1k2l3m4n5o6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    return_request_columns = {column["name"] for column in inspector.get_columns("return_requests")}
    shipment_columns = {column["name"] for column in inspector.get_columns("shipments")}
    shipment_foreign_keys = {foreign_key.get("name") for foreign_key in inspector.get_foreign_keys("shipments")}

    with op.batch_alter_table("return_requests", schema=None) as batch_op:
        if "intent" not in return_request_columns:
            batch_op.add_column(sa.Column("intent", sa.String(length=30), nullable=False, server_default="return"))

    with op.batch_alter_table("shipments", schema=None) as batch_op:
        if "package_count" not in shipment_columns:
            batch_op.add_column(sa.Column("package_count", sa.Integer(), nullable=True))
        if "package_weight_kg" not in shipment_columns:
            batch_op.add_column(sa.Column("package_weight_kg", sa.Float(), nullable=True))
        if "package_dimensions" not in shipment_columns:
            batch_op.add_column(sa.Column("package_dimensions", sa.String(length=120), nullable=True))
        if "packaged_at" not in shipment_columns:
            batch_op.add_column(sa.Column("packaged_at", sa.DateTime(), nullable=True))
        if "packaged_by_user_id" not in shipment_columns:
            batch_op.add_column(sa.Column("packaged_by_user_id", sa.Integer(), nullable=True))
        if "packaging_notes" not in shipment_columns:
            batch_op.add_column(sa.Column("packaging_notes", sa.Text(), nullable=True))
        if "fk_shipments_packaged_by_user_id_users" not in shipment_foreign_keys and "packaged_by_user_id" in {
            *shipment_columns,
            "packaged_by_user_id",
        }:
            batch_op.create_foreign_key(
                "fk_shipments_packaged_by_user_id_users",
                "users",
                ["packaged_by_user_id"],
                ["id"],
            )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    return_request_columns = {column["name"] for column in inspector.get_columns("return_requests")}
    shipment_columns = {column["name"] for column in inspector.get_columns("shipments")}
    shipment_foreign_keys = {foreign_key.get("name") for foreign_key in inspector.get_foreign_keys("shipments")}

    with op.batch_alter_table("shipments", schema=None) as batch_op:
        if "fk_shipments_packaged_by_user_id_users" in shipment_foreign_keys:
            batch_op.drop_constraint("fk_shipments_packaged_by_user_id_users", type_="foreignkey")
        if "packaging_notes" in shipment_columns:
            batch_op.drop_column("packaging_notes")
        if "packaged_by_user_id" in shipment_columns:
            batch_op.drop_column("packaged_by_user_id")
        if "packaged_at" in shipment_columns:
            batch_op.drop_column("packaged_at")
        if "package_dimensions" in shipment_columns:
            batch_op.drop_column("package_dimensions")
        if "package_weight_kg" in shipment_columns:
            batch_op.drop_column("package_weight_kg")
        if "package_count" in shipment_columns:
            batch_op.drop_column("package_count")

    with op.batch_alter_table("return_requests", schema=None) as batch_op:
        if "intent" in return_request_columns:
            batch_op.drop_column("intent")

