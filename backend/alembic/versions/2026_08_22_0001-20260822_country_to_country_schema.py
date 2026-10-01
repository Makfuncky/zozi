"""move country-domain tables from the catch-all ``configuration`` schema into ``country``

The 16 ``country_*`` tables that accumulated in the catch-all ``configuration``
schema are moved into their correct bounded-context schema, ``country`` — one
Postgres schema per domain (ARCHITECTURE_DIAGRAM.md §9, Law 6).

PostgreSQL moves each table (with its indexes, constraints, owned sequences and
cross-references) atomically via ``ALTER TABLE ... SET SCHEMA`` -- no data is
rewritten. The statements are guarded with ``IF EXISTS`` so the migration is
idempotent and safe to re-run on a DB that was already upgraded (or built from
scratch, since the earlier migrations still create these tables under
``configuration`` first).

On SQLite (dev) the ORM + ``create_all`` already produce the correctly-named
tables under the declared schema, so this migration is a no-op there.

Revision ID: 20260822_country_to_country_schema
Revises: 20260821_user_referral_to_customer
Create Date: 2026-08-22
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260822_country_to_country_schema"
down_revision: Union[str, None] = "20260821_user_referral_to_customer"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# tables currently living in ``configuration`` that belong to ``country``
_MOVES = [
    ("country_feature_flags", "country"),
    ("country_staff_assignments", "country"),
    ("cross_country_customer_sessions", "country"),
    ("oman_delivery_zones", "country"),
    ("country_config_versions", "country"),
    ("country_commission_rates", "country"),
    ("country_localization", "country"),
    ("country_payment_aliases", "country"),
    ("country_legal_contracts", "country"),
    ("country_category_tax_rates", "country"),
    ("country_holiday_calendars", "country"),
    ("country_gateway_configs", "country"),
    ("country_communication_threads", "country"),
    ("country_commission_rate_history", "country"),
    ("country_logistics_zones", "country"),
    ("country_payout_rules", "country"),
]


def _exec(sql: str) -> None:
    op.execute(sa.text(sql))


def upgrade() -> None:
    if op.get_context().dialect.name != "postgresql":
        return

    _exec("CREATE SCHEMA IF NOT EXISTS country")

    for table, schema in _MOVES:
        # Idempotent: a fresh DB (or an already-upgraded one) may not have the
        # table under ``configuration`` anymore, in which case this is a no-op.
        _exec(
            "ALTER TABLE IF EXISTS configuration.{t} SET SCHEMA {s}".format(
                t=table, s=schema
            )
        )


def downgrade() -> None:
    if op.get_context().dialect.name != "postgresql":
        return

    _exec("CREATE SCHEMA IF NOT EXISTS configuration")
    for table, schema in _MOVES:
        _exec(
            "ALTER TABLE IF EXISTS {s}.{t} SET SCHEMA configuration".format(
                s=schema, t=table
            )
        )
