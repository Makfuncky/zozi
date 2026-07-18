"""add referral points system

Revision ID: w3x4y5z6a7b8
Revises: v2w3x4y5z6a7
Create Date: 2026-03-31 10:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "w3x4y5z6a7b8"
down_revision: Union[str, Sequence[str], None] = "v2w3x4y5z6a7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _is_sqlite() -> bool:
    bind = op.get_bind()
    return bind.dialect.name == "sqlite"


def _inspector() -> sa.Inspector:
    return sa.inspect(op.get_bind())


def _table_exists(table_name: str) -> bool:
    return table_name in _inspector().get_table_names()


def _column_names(table_name: str) -> set[str]:
    if not _table_exists(table_name):
        return set()
    return {str(column.get("name")) for column in _inspector().get_columns(table_name)}


def _index_names(table_name: str) -> set[str]:
    if not _table_exists(table_name):
        return set()
    return {str(index.get("name")) for index in _inspector().get_indexes(table_name)}


def _foreign_key_names(table_name: str) -> set[str]:
    if not _table_exists(table_name):
        return set()
    names: set[str] = set()
    for foreign_key in _inspector().get_foreign_keys(table_name):
        fk_name = foreign_key.get("name")
        if fk_name:
            names.add(str(fk_name))
    return names


def upgrade() -> None:
    user_columns = _column_names("users")

    if "referral_code" not in user_columns:
        op.add_column("users", sa.Column("referral_code", sa.String(length=24), nullable=True))
    if "referred_by_user_id" not in user_columns:
        op.add_column("users", sa.Column("referred_by_user_id", sa.Integer(), nullable=True))
    if "referral_points" not in user_columns:
        op.add_column("users", sa.Column("referral_points", sa.Integer(), nullable=True, server_default="0"))
    if "sharing_points" not in user_columns:
        op.add_column("users", sa.Column("sharing_points", sa.Integer(), nullable=True, server_default="0"))

    if not _is_sqlite() and "fk_users_referred_by_user_id_users" not in _foreign_key_names("users"):
        op.create_foreign_key(
            "fk_users_referred_by_user_id_users",
            "users",
            "users",
            ["referred_by_user_id"],
            ["id"],
        )

    user_indexes = _index_names("users")
    if "ix_users_referred_by_user_id" not in user_indexes:
        op.create_index("ix_users_referred_by_user_id", "users", ["referred_by_user_id"], unique=False)
    if "ix_users_referral_code" not in user_indexes:
        op.create_index("ix_users_referral_code", "users", ["referral_code"], unique=True)

    user_columns = _column_names("users")
    if not _is_sqlite():
        if "referral_points" in user_columns:
            op.alter_column("users", "referral_points", server_default=None)
        if "sharing_points" in user_columns:
            op.alter_column("users", "sharing_points", server_default=None)

    if not _table_exists("referral_point_events"):
        op.create_table(
            "referral_point_events",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("event_type", sa.String(length=40), nullable=False),
            sa.Column("points", sa.Integer(), nullable=False),
            sa.Column("channel", sa.String(length=40), nullable=True),
            sa.Column("referred_user_id", sa.Integer(), nullable=True),
            sa.Column("metadata_json", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(["referred_user_id"], ["users.id"]),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
            sa.PrimaryKeyConstraint("id"),
        )

    referral_event_indexes = _index_names("referral_point_events")
    if "ix_referral_point_events_user_id" not in referral_event_indexes:
        op.create_index("ix_referral_point_events_user_id", "referral_point_events", ["user_id"], unique=False)
    if "ix_referral_point_events_event_type" not in referral_event_indexes:
        op.create_index("ix_referral_point_events_event_type", "referral_point_events", ["event_type"], unique=False)
    if "ix_referral_point_events_created_at" not in referral_event_indexes:
        op.create_index("ix_referral_point_events_created_at", "referral_point_events", ["created_at"], unique=False)
    if "ix_referral_point_events_user_created" not in referral_event_indexes:
        op.create_index(
            "ix_referral_point_events_user_created",
            "referral_point_events",
            ["user_id", "created_at"],
            unique=False,
        )
    if "ix_referral_point_events_type_created" not in referral_event_indexes:
        op.create_index(
            "ix_referral_point_events_type_created",
            "referral_point_events",
            ["event_type", "created_at"],
            unique=False,
        )


def downgrade() -> None:
    referral_event_indexes = _index_names("referral_point_events")
    if "ix_referral_point_events_type_created" in referral_event_indexes:
        op.drop_index("ix_referral_point_events_type_created", table_name="referral_point_events")
    if "ix_referral_point_events_user_created" in referral_event_indexes:
        op.drop_index("ix_referral_point_events_user_created", table_name="referral_point_events")
    if "ix_referral_point_events_created_at" in referral_event_indexes:
        op.drop_index("ix_referral_point_events_created_at", table_name="referral_point_events")
    if "ix_referral_point_events_event_type" in referral_event_indexes:
        op.drop_index("ix_referral_point_events_event_type", table_name="referral_point_events")
    if "ix_referral_point_events_user_id" in referral_event_indexes:
        op.drop_index("ix_referral_point_events_user_id", table_name="referral_point_events")
    if _table_exists("referral_point_events"):
        op.drop_table("referral_point_events")

    user_indexes = _index_names("users")
    if "ix_users_referral_code" in user_indexes:
        op.drop_index("ix_users_referral_code", table_name="users")
    if "ix_users_referred_by_user_id" in user_indexes:
        op.drop_index("ix_users_referred_by_user_id", table_name="users")
    if not _is_sqlite() and "fk_users_referred_by_user_id_users" in _foreign_key_names("users"):
        op.drop_constraint("fk_users_referred_by_user_id_users", "users", type_="foreignkey")

    user_columns = _column_names("users")
    if "sharing_points" in user_columns:
        op.drop_column("users", "sharing_points")
    if "referral_points" in user_columns:
        op.drop_column("users", "referral_points")
    if "referred_by_user_id" in user_columns:
        op.drop_column("users", "referred_by_user_id")
    if "referral_code" in user_columns:
        op.drop_column("users", "referral_code")

