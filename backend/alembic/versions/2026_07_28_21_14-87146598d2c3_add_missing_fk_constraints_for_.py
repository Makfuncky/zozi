"""add_missing_fk_constraints_for_production

Revision ID: 87146598d2c3
Revises: e8efae30fc29
Create Date: 2026-07-28 21:14:18.350445+00:00

Adds the missing FK constraint for a table whose ORM model
defines a ForeignKey column but the database schema is missing
the enforceable constraint:

- email_delivery_events.campaign_recipient_id -> campaign_recipients.id

Uses Alembic batch_alter_table so the migration works on both SQLite
(dev) and PostgreSQL (production).  On SQLite the table is recreated;
on PostgreSQL a standard ALTER TABLE ADD CONSTRAINT is emitted.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '87146598d2c3'
down_revision: Union[str, None] = 'e8efae30fc29'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("email_delivery_events") as batch_op:
        batch_op.create_foreign_key(
            "fk_email_delivery_events_campaign_recipient_id",
            "campaign_recipients",
            ["campaign_recipient_id"],
            ["id"],
        )


def downgrade() -> None:
    with op.batch_alter_table("email_delivery_events") as batch_op:
        batch_op.drop_constraint(
            "fk_email_delivery_events_campaign_recipient_id", type_="foreignkey"
        )
