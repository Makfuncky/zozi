"""add email AB test fields and GPS coords to shipment_events

Revision ID: g1h2i3j4k5l6
Revises: a3b4c5d6e7f8
Create Date: 2026-03-26
"""
from alembic import op
import sqlalchemy as sa

revision = "g1h2i3j4k5l6"
down_revision = "a3b4c5d6e7f8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # EmailCampaign — A/B subject-line testing columns
    with op.batch_alter_table("email_campaigns") as batch:
        batch.add_column(sa.Column("subject_b", sa.String(500), nullable=True))
        batch.add_column(sa.Column("ab_test_enabled", sa.Boolean(), server_default=sa.false(), nullable=False))
        batch.add_column(sa.Column("ab_winner_variant", sa.String(1), nullable=True))

    # ShipmentEvent — GPS coordinate columns for map widget
    with op.batch_alter_table("shipment_events") as batch:
        batch.add_column(sa.Column("latitude", sa.Float(), nullable=True))
        batch.add_column(sa.Column("longitude", sa.Float(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("email_campaigns") as batch:
        batch.drop_column("subject_b")
        batch.drop_column("ab_test_enabled")
        batch.drop_column("ab_winner_variant")

    with op.batch_alter_table("shipment_events") as batch:
        batch.drop_column("latitude")
        batch.drop_column("longitude")

