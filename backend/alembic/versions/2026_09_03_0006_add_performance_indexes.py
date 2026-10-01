"""Add performance indexes for scalability (Law 45: keyset + composite indexes).

Adds single-column indexes on ``country_code`` for hot tables that were
introduced in the Phase C / Law 5 column-add migration, plus composite
indexes aligned with the most common query patterns identified by the
audit:

* ``(country_code, id)`` for keyset pagination (Law 45: never OFFSET).
* ``(country_code, created_at)`` for time-bounded admin list queries.
* ``(country_code, status_code)`` / ``(country_code, status)`` for the
  status-filtered admin grids.

Indexes are created with ``IF NOT EXISTS`` so the migration is idempotent
against dev databases that were built via ``Base.metadata.create_all``.
SQLite is skipped because composite indexes on these tables are less
critical for dev and the column types differ.

Revision ID: 2026_09_03_0006
Revises: 2026_09_03_0005
Create Date: 2026-09-03
"""
import sqlalchemy as sa
from typing import Sequence, Union

from alembic import op
from sqlalchemy.sql import quoted_name as sql_identifier

revision: str = "2026_09_03_0006"
down_revision: Union[str, None] = "2026_09_03_0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Single-column country_code indexes for hot tables introduced in Phase C.
SINGLE_COUNTRY_INDEXES = [
    ("comms", "entity_chat_threads"),
    ("comms", "entity_chat_messages"),
    ("comms", "group_chat_members"),
    ("comms", "escalation_sla_logs"),
    ("comms", "video_room_participants"),
    ("comms", "video_room_recordings"),
    ("comms", "live_stream_viewers"),
    ("customer", "addresses"),
    ("customer", "wishlist_items"),
    ("customer", "review_helpful_votes"),
    ("customer", "customer_segments"),
    ("customer", "support_tickets"),
    ("finance", "currency_exchange_rates"),
    ("finance", "commission_rules"),
    ("finance", "tax_rules"),
    ("finance", "payouts"),
    ("finance", "refund_requests"),
    ("finance", "vendor_payments"),
    ("logistics", "shipments"),
    ("logistics", "delivery_zones"),
    ("logistics", "tracking_events"),
    ("logistics", "warehouse_inventory"),
    ("orders", "order_addresses"),
    ("orders", "order_payments"),
    ("promotions", "coupon_usages"),
    ("promotions", "promotion_targets"),
    ("promotions", "referral_codes"),
    ("suppliers", "supplier_metrics"),
    ("suppliers", "supplier_payout_methods"),
    ("suppliers", "supplier_documents"),
    ("country", "country_payment_gateways"),
    ("country", "country_tax_rates"),
    ("country", "country_city"),
    ("country", "country_logistics_partners"),
]


# Composite indexes for keyset pagination + common query patterns.
COMPOSITE_INDEXES = [
    # Keyset on (country_code, id) for hot admin lists.
    ("comms", "entity_chat_threads", "ix_chat_threads_country_id", ["country_code", "id"]),
    ("comms", "entity_chat_messages", "ix_chat_messages_country_id", ["country_code", "id"]),
    ("customer", "wishlist_items", "ix_wishlist_country_id", ["country_code", "id"]),
    ("orders", "order_addresses", "ix_order_addresses_country_id", ["country_code", "id"]),
    ("logistics", "shipments", "ix_shipments_country_id", ["country_code", "id"]),
    # Time-bounded admin list queries.
    ("customer", "support_tickets", "ix_support_tickets_country_created", ["country_code", "created_at"]),
    ("finance", "payouts", "ix_payouts_country_created", ["country_code", "created_at"]),
    ("logistics", "tracking_events", "ix_tracking_country_created", ["country_code", "created_at"]),
    # Status-filtered admin grids.
    ("finance", "payouts", "ix_payouts_country_status", ["country_code", "status"]),
    ("logistics", "shipments", "ix_shipments_country_status", ["country_code", "status"]),
    ("customer", "support_tickets", "ix_support_tickets_country_status", ["country_code", "status"]),
    ("suppliers", "supplier_documents", "ix_supplier_docs_country_status", ["country_code", "verification_status"]),
]


def upgrade() -> None:
    conn = op.get_bind()
    dialect = conn.dialect.name

    # Single-column country_code indexes (idempotent).
    for schema, table in SINGLE_COUNTRY_INDEXES:
        idx_name = f"ix_{schema}_{table}_country_code"
        if dialect == "postgresql":
            sch = sql_identifier(schema)
            tbl = sql_identifier(table)
            idx = sql_identifier(idx_name)
            op.execute(
                sa.text('CREATE INDEX IF NOT EXISTS :idx ON :sch.:tbl ("country_code")'),
                {"idx": idx, "sch": sch, "tbl": tbl},
            )
        elif dialect == "sqlite":
            continue
        else:
            sch = sql_identifier(schema)
            tbl = sql_identifier(table)
            idx = sql_identifier(idx_name)
            op.execute(
                sa.text('CREATE INDEX IF NOT EXISTS :idx ON :sch.:tbl ("country_code")'),
                {"idx": idx, "sch": sch, "tbl": tbl},
            )

    # Composite indexes (Postgres only — SQLite handles these via the ORM).
    for schema, table, idx_name, columns in COMPOSITE_INDEXES:
        if dialect == "sqlite":
            continue
        col_list = ", ".join(columns)
        sch = sql_identifier(schema)
        tbl = sql_identifier(table)
        idx = sql_identifier(idx_name)
        op.execute(
            sa.text('CREATE INDEX IF NOT EXISTS :idx ON :sch.:tbl (:cols)'),
            {"idx": idx, "sch": sch, "tbl": tbl, "cols": col_list},
        )


def downgrade() -> None:
    conn = op.get_bind()
    dialect = conn.dialect.name

    for schema, table, idx_name, _columns in reversed(COMPOSITE_INDEXES):
        if dialect == "sqlite":
            continue
        sch = sql_identifier(schema)
        idx = sql_identifier(idx_name)
        op.execute(
            sa.text('DROP INDEX IF EXISTS :sch.:idx'),
            {"sch": sch, "idx": idx},
        )

    for schema, table in reversed(SINGLE_COUNTRY_INDEXES):
        idx_name = f"ix_{schema}_{table}_country_code"
        if dialect == "sqlite":
            continue
        sch = sql_identifier(schema)
        idx = sql_identifier(idx_name)
        op.execute(
            sa.text('DROP INDEX IF EXISTS :sch.:idx'),
            {"sch": sch, "idx": idx},
        )
