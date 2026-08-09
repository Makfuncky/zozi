"""uuid_enumeration_prevention

Add UUID columns to Orders, Payouts, LogisticsPartnerPayouts, and Invoices
so that external-facing APIs can reference resources by UUID instead of
auto-increment integer IDs.  This prevents ID enumeration attacks.

Revision ID: n5o6p7q8r9s0
Revises: m0n1o2p3q4r5
Create Date: 2026-06-24 14:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "n5o6p7q8r9s0"
down_revision: Union[str, Sequence[str], None] = ("m0n1o2p3q4r5", "z2a3b4c5d6e7")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = set(inspector.get_table_names())

    # ── orders ──────────────────────────────────────────────────────────────────
    if "orders" in existing_tables:
        existing_cols = {c["name"] for c in inspector.get_columns("orders")}
        if "public_id" not in existing_cols:
            op.add_column("orders", sa.Column("public_id", sa.String(36), nullable=True))
        if "ix_orders_public_id" not in {ix["name"] for ix in inspector.get_indexes("orders")}:
            op.create_index("ix_orders_public_id", "orders", ["public_id"], unique=True)

    # ── payouts ─────────────────────────────────────────────────────────────────
    if "payouts" in existing_tables:
        existing_cols = {c["name"] for c in inspector.get_columns("payouts")}
        if "public_id" not in existing_cols:
            op.add_column("payouts", sa.Column("public_id", sa.String(36), nullable=True))
        if "ix_payouts_public_id" not in {ix["name"] for ix in inspector.get_indexes("payouts")}:
            op.create_index("ix_payouts_public_id", "payouts", ["public_id"], unique=True)

    # ── logistics_partner_payouts ───────────────────────────────────────────────
    if "logistics_partner_payouts" in existing_tables:
        existing_cols = {c["name"] for c in inspector.get_columns("logistics_partner_payouts")}
        if "public_id" not in existing_cols:
            op.add_column("logistics_partner_payouts", sa.Column("public_id", sa.String(36), nullable=True))
        if "ix_logistics_partner_payouts_public_id" not in {ix["name"] for ix in inspector.get_indexes("logistics_partner_payouts")}:
            op.create_index(
                "ix_logistics_partner_payouts_public_id",
                "logistics_partner_payouts",
                ["public_id"],
                unique=True,
            )

    # ── invoices ────────────────────────────────────────────────────────────────
    if "invoices" in existing_tables:
        existing_cols = {c["name"] for c in inspector.get_columns("invoices")}
        if "public_id" not in existing_cols:
            op.add_column("invoices", sa.Column("public_id", sa.String(36), nullable=True))
        if "ix_invoices_public_id" not in {ix["name"] for ix in inspector.get_indexes("invoices")}:
            op.create_index("ix_invoices_public_id", "invoices", ["public_id"], unique=True)

    # ── shipment_events (if it exists) ──────────────────────────────────────────
    if "shipment_events" in existing_tables:
        existing_cols = {c["name"] for c in inspector.get_columns("shipment_events")}
        if "public_id" not in existing_cols:
            op.add_column("shipment_events", sa.Column("public_id", sa.String(36), nullable=True))
        if "ix_shipment_events_public_id" not in {ix["name"] for ix in inspector.get_indexes("shipment_events")}:
            op.create_index(
                "ix_shipment_events_public_id",
                "shipment_events",
                ["public_id"],
                unique=True,
            )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    for table in ("orders", "payouts", "logistics_partner_payouts", "invoices", "shipment_events"):
        if table in set(inspector.get_table_names()):
            try:
                op.drop_constraint(f"ix_{table}_public_id", table, type_="index")
            except Exception:
                pass
            try:
                op.drop_column(table, "public_id")
            except Exception:
                pass

