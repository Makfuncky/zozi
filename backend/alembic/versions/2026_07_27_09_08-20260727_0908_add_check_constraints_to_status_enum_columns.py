"""add_check_constraints_to_status_enum_columns

Revision ID: 20260727_0908
Revises: c0f3f1817791
Create Date: 2026-07-27 09:08:00.000000+00:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260727_0908"
down_revision: Union[str, None] = "c0f3f1817791"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("orders", schema=None) as batch_op:
        batch_op.create_check_constraint(
            "chk_order_status_valid",
            "status IN ('pending','processing','confirmed','shipped','delivered','cancelled','refunded')",
        )
        batch_op.create_check_constraint(
            "chk_order_payment_status_valid",
            "payment_status IN ('pending','completed','failed','refunded')",
        )
        batch_op.create_check_constraint(
            "chk_order_fraud_action_valid",
            "fraud_action IN ('allow','review','block')",
        )

    with op.batch_alter_table("return_requests", schema=None) as batch_op:
        batch_op.create_check_constraint(
            "chk_return_intent_valid",
            "intent IN ('return','exchange','refund')",
        )
        batch_op.create_check_constraint(
            "chk_return_status_valid",
            "status IN ('requested','approved','rejected','completed')",
        )

    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.create_check_constraint(
            "chk_user_role_valid",
            "role IN ('customer','supplier','admin','employee','logistics')",
        )

    with op.batch_alter_table("referrals", schema=None) as batch_op:
        batch_op.create_check_constraint(
            "chk_referral_status_valid",
            "status IN ('pending','completed','expired','cancelled')",
        )

    with op.batch_alter_table("logistics_partners", schema=None) as batch_op:
        batch_op.create_check_constraint(
            "chk_logistics_partner_status_valid",
            "status IN ('active','suspended','deactivated')",
        )

    with op.batch_alter_table("shipments", schema=None) as batch_op:
        batch_op.create_check_constraint(
            "chk_shipment_status_valid",
            "status IN ('pending','processing','shipped','delivered','returned','cancelled')",
        )

    with op.batch_alter_table("support_tickets", schema=None) as batch_op:
        batch_op.create_check_constraint(
            "chk_ticket_status_valid",
            "status IN ('open','in_progress','resolved','closed')",
        )

    with op.batch_alter_table("notifications", schema=None) as batch_op:
        batch_op.create_check_constraint(
            "chk_notification_status_valid",
            "status IN ('pending','delivered','read','failed')",
        )


def downgrade() -> None:
    with op.batch_alter_table("notifications", schema=None) as batch_op:
        batch_op.drop_constraint("chk_notification_status_valid", type_="check")

    with op.batch_alter_table("support_tickets", schema=None) as batch_op:
        batch_op.drop_constraint("chk_ticket_status_valid", type_="check")

    with op.batch_alter_table("shipments", schema=None) as batch_op:
        batch_op.drop_constraint("chk_shipment_status_valid", type_="check")

    with op.batch_alter_table("logistics_partners", schema=None) as batch_op:
        batch_op.drop_constraint("chk_logistics_partner_status_valid", type_="check")

    with op.batch_alter_table("referrals", schema=None) as batch_op:
        batch_op.drop_constraint("chk_referral_status_valid", type_="check")

    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.drop_constraint("chk_user_role_valid", type_="check")

    with op.batch_alter_table("return_requests", schema=None) as batch_op:
        batch_op.drop_constraint("chk_return_status_valid", type_="check")
        batch_op.drop_constraint("chk_return_intent_valid", type_="check")

    with op.batch_alter_table("orders", schema=None) as batch_op:
        batch_op.drop_constraint("chk_order_fraud_action_valid", type_="check")
        batch_op.drop_constraint("chk_order_payment_status_valid", type_="check")
        batch_op.drop_constraint("chk_order_status_valid", type_="check")
