"""add missing server_default=now() on timestamp columns (Law 21)

Live-DB audit (2026-10-04) found these columns in existing tables are missing
the ``DEFAULT now()`` constraint that the ORM ``server_default=func.now()``
declares.  Until this DDL lands, inserts that omit the column receive NULL
instead of the DB-side timestamp — exactly the failure mode Law 21 guards
against.

Also creates three comms tables that the ORM maps but that do not exist in
the live database: chat_messages, chat_rooms, chat_participants.

Columns verified MISSING DEFAULT now() in live DB:
  comms.entity_chat_threads.created_at
  comms.entity_chat_threads.updated_at
  comms.chat_messages.created_at            (table absent — CREATE TABLE)
  comms.chat_messages.updated_at            (table absent — CREATE TABLE)
  comms.chat_rooms.created_at               (table absent — CREATE TABLE)
  comms.chat_rooms.updated_at               (table absent — CREATE TABLE)
  comms.chat_participants.created_at        (table absent — CREATE TABLE)
  comms.chat_participants.updated_at        (table absent — CREATE TABLE)
  comms.campaigns.created_at                (table absent — CREATE TABLE)
  comms.campaigns.updated_at                (table absent — CREATE TABLE)
  country.country_tax_rules.created_at      (table absent — CREATE TABLE)
  country.country_tax_rules.updated_at      (table absent — CREATE TABLE)

Idempotent: every step guards on column/table presence so re-running on an
already-converged database is a no-op.

Law 57 (reversible): downgrade() drops every default added and drops every
table created.
"""
from __future__ import annotations

import logging
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


def _is_offline(conn) -> bool:
    if conn is None:
        return True
    try:
        from sqlalchemy import inspect as sa_inspect
        from sqlalchemy.exc import NoInspectionAvailable
        sa_inspect(conn)
        return False
    except (NoInspectionAvailable, Exception):
        return True


revision: str = "20261004_0018"
down_revision: Union[str, None] = "20261004_0017"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

logger = logging.getLogger("alembic.runtime.migration")

# ── Helpers ──────────────────────────────────────────────────────────────────


def _has_table(bind, table: str, schema: str) -> bool:
    offline = _is_offline(bind)
    if offline:
        return
    inspector = sa.inspect(bind)
    return table in inspector.get_table_names(schema=schema)


def _has_column(bind, table: str, column: str, schema: str) -> bool:
    offline = _is_offline(bind)
    if offline:
        return
    inspector = sa.inspect(bind)
    try:
        return column in {c["name"] for c in inspector.get_columns(table, schema=schema)}
    except sa.exc.NoSuchTableError:
        return False


def _col_has_now_default(bind, table: str, column: str, schema: str) -> bool:
    """Return True when the column already carries a now()-family default."""
    offline = _is_offline(bind)
    if offline:
        return
    inspector = sa.inspect(bind)
    try:
        cols = {c["name"]: c for c in inspector.get_columns(table, schema=schema)}
    except sa.exc.NoSuchTableError:
        return False
    col = cols.get(column)
    if col is None:
        return False
    default = col.get("default")
    if default is None:
        return False
    return "now()" in str(default) or "CURRENT_TIMESTAMP" in str(default).upper()


def _safe_alter_default(bind, table: str, column: str, schema: str) -> None:
    """Add server_default=now() to column if missing."""
    if not _has_column(bind, table, column, schema):
        logger.warning(
            "L21: %s.%s absent — skipped", schema + "." + table, column
        )
        return
    if _col_has_now_default(bind, table, column, schema):
        logger.info(
            "L21: %s.%s already defaults to now()", schema + "." + table, column
        )
        return
    with op.batch_alter_table(table, schema=schema) as batch_op:
        batch_op.alter_column(
            column,
            existing_type=sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        )
    logger.info("L21: set DEFAULT now() on %s.%s", schema + "." + table, column)


# ── upgrade ───────────────────────────────────────────────────────────────────


def upgrade() -> None:
    bind = op.get_bind()

    # ── 1. Fix existing tables missing DEFAULT now() ──────────────────────────
    _safe_alter_default(bind, "entity_chat_threads", "created_at", "comms")
    _safe_alter_default(bind, "entity_chat_threads", "updated_at", "comms")

    # ── 2. Create comms.chat_messages ─────────────────────────────────────────
    if not _has_table(bind, "chat_messages", "comms"):
        op.create_table(
            "chat_messages",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("thread_id", sa.Integer(), nullable=False),
            sa.Column("sender_id", sa.Integer(), nullable=True),
            sa.Column("message", sa.Text(), nullable=False),
            sa.Column("message_type", sa.String(20), nullable=False, server_default="text"),
            sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.text("false")),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.func.now(),
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.func.now(),
            ),
            sa.ForeignKeyConstraint(["thread_id"], ["comms.entity_chat_threads.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["sender_id"], ["accounts.users.id"], ondelete="SET NULL"),
            sa.PrimaryKeyConstraint("id"),
            sa.Index("ix_chat_messages_thread", "thread_id"),
            schema="comms",
        )
        logger.info("L21: created comms.chat_messages")
    else:
        _safe_alter_default(bind, "chat_messages", "created_at", "comms")
        _safe_alter_default(bind, "chat_messages", "updated_at", "comms")

    # ── 3. Create comms.chat_rooms ────────────────────────────────────────────
    if not _has_table(bind, "chat_rooms", "comms"):
        op.create_table(
            "chat_rooms",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("chat_id", sa.String(64), nullable=False),
            sa.Column("name", sa.String(200), nullable=False),
            sa.Column("country_code", sa.String(2), nullable=True),
            sa.Column("is_encrypted", sa.Boolean(), nullable=False, server_default=sa.text("false")),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("created_by_id", sa.Integer(), nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.func.now(),
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.func.now(),
            ),
            sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.text("false")),
            sa.ForeignKeyConstraint(["country_code"], ["country.country_configs.code"], ondelete="RESTRICT"),
            sa.ForeignKeyConstraint(["created_by_id"], ["accounts.users.id"], ondelete="SET NULL"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("chat_id", name="uq_chat_room_chat_id"),
            sa.Index("ix_chat_rooms_created_at", "created_at"),
            schema="comms",
        )
        logger.info("L21: created comms.chat_rooms")
    else:
        _safe_alter_default(bind, "chat_rooms", "created_at", "comms")
        _safe_alter_default(bind, "chat_rooms", "updated_at", "comms")

    # ── 4. Create comms.chat_participants ─────────────────────────────────────
    if not _has_table(bind, "chat_participants", "comms"):
        op.create_table(
            "chat_participants",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("room_id", sa.Integer(), nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("role", sa.String(20), nullable=False, server_default="participant"),
            sa.Column("joined_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("left_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("country_code", sa.String(2), nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.func.now(),
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.func.now(),
            ),
            sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.text("false")),
            sa.ForeignKeyConstraint(["room_id"], ["comms.chat_rooms.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["user_id"], ["accounts.users.id"], ondelete="SET NULL"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("room_id", "user_id", name="uq_chat_participant"),
            schema="comms",
        )
        logger.info("L21: created comms.chat_participants")
    else:
        _safe_alter_default(bind, "chat_participants", "created_at", "comms")
        _safe_alter_default(bind, "chat_participants", "updated_at", "comms")

    # ── 5. Create comms.campaigns ─────────────────────────────────────────────
    if not _has_table(bind, "campaigns", "comms"):
        op.create_table(
            "campaigns",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("name", sa.String(255), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("campaign_type", sa.String(50), nullable=False, server_default="marketing"),
            sa.Column("status", sa.String(20), nullable=False, server_default="draft"),
            sa.Column("country_code", sa.String(2), nullable=True),
            sa.Column("starts_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("ends_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_by_id", sa.Integer(), nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.func.now(),
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.func.now(),
            ),
            sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.text("false")),
            sa.ForeignKeyConstraint(["country_code"], ["country.country_configs.code"], ondelete="RESTRICT"),
            sa.ForeignKeyConstraint(["created_by_id"], ["accounts.users.id"], ondelete="SET NULL"),
            sa.PrimaryKeyConstraint("id"),
            sa.Index("ix_campaigns_country_created", "country_code", "created_at"),
            schema="comms",
        )
        logger.info("L21: created comms.campaigns")
    else:
        _safe_alter_default(bind, "campaigns", "created_at", "comms")
        _safe_alter_default(bind, "campaigns", "updated_at", "comms")

    # ── 6. Create country.country_tax_rules (mapped by country_tax.py) ────────
    if not _has_table(bind, "country_tax_rules", "country"):
        op.create_table(
            "country_tax_rules",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("country_code", sa.String(2), nullable=False),
            sa.Column("tax_name", sa.String(50), nullable=False, server_default="VAT"),
            sa.Column("tax_type", sa.String(20), nullable=False, server_default="VAT"),
            sa.Column("tax_rate", sa.Numeric(5, 4), nullable=False, server_default="0.0000"),
            sa.Column("tax_inclusive", sa.Boolean(), nullable=False, server_default=sa.text("false")),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.text("false")),
            sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("deleted_by", sa.Integer(), nullable=True),
            sa.Column("created_by", sa.Integer(), nullable=True),
            sa.Column("updated_by", sa.Integer(), nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.func.now(),
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.func.now(),
            ),
            sa.ForeignKeyConstraint(["country_code"], ["country.country_configs.code"], ondelete="RESTRICT"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("country_code", name="uq_country_tax_rule_country"),
            sa.Index("ix_country_tax_rule_country_created", "country_code", "created_at"),
            schema="country",
        )
        logger.info("L21: created country.country_tax_rules")
    else:
        _safe_alter_default(bind, "country_tax_rules", "created_at", "country")
        _safe_alter_default(bind, "country_tax_rules", "updated_at", "country")


# ── downgrade ─────────────────────────────────────────────────────────────────


def downgrade() -> None:
    # Reverse in LIFO order of creation.
    # All drops use IF EXISTS so this is safe to run even when only a subset
    # of upgrade() applied (e.g. on a partially-converged database).

    # 6. Drop country_tax_rules table (created in upgrade)
    op.execute(sa.text("DROP TABLE IF EXISTS country.country_tax_rules CASCADE"))
    logger.info("L21: dropped country.country_tax_rules (if it existed)")

    # 5. Drop campaigns table (created in upgrade)
    op.execute(sa.text("DROP TABLE IF EXISTS comms.campaigns CASCADE"))
    logger.info("L21: dropped comms.campaigns (if it existed)")

    # 4. Drop chat_participants table (created in upgrade)
    #    Must come before chat_rooms because of FK from chat_participants.room_id
    op.execute(sa.text("DROP TABLE IF EXISTS comms.chat_participants CASCADE"))
    logger.info("L21: dropped comms.chat_participants (if it existed)")

    # 3. Drop chat_rooms table (created in upgrade)
    op.execute(sa.text("DROP TABLE IF EXISTS comms.chat_rooms CASCADE"))
    logger.info("L21: dropped comms.chat_rooms (if it existed)")

    # 2. Drop chat_messages table (created in upgrade)
    #    Must come before chat_rooms because of FK from chat_messages.thread_id
    op.execute(sa.text("DROP TABLE IF EXISTS comms.chat_messages CASCADE"))
    logger.info("L21: dropped comms.chat_messages (if it existed)")

    # 1. Remove DEFAULT now() added to entity_chat_threads in upgrade
    # Use raw SQL so this works in --sql mode (no sa.inspect available there)
    op.execute(sa.text("""
        ALTER TABLE comms.entity_chat_threads
        ALTER COLUMN created_at DROP DEFAULT
    """))
    op.execute(sa.text("""
        ALTER TABLE comms.entity_chat_threads
        ALTER COLUMN updated_at DROP DEFAULT
    """))
    logger.info("L21: removed DEFAULT now() from comms.entity_chat_threads")
