"""Create employee HR and system tables

Revision ID: 20260728_0000
Revises: 20260727_0908
Create Date: 2026-07-28

Replaces raw SQL migration in db/migrations/new_tables.py.
All tables are now managed by Alembic with proper downgrade support.
"""
from alembic import op
import sqlalchemy as sa

revision = "20260728_0000"
down_revision = "20260727_0908"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "employee_active_tasks",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("employee_id", sa.Integer, sa.ForeignKey("employees.id", ondelete="CASCADE"), nullable=False),
        sa.Column("task_name", sa.String(200), nullable=False),
        sa.Column("task_type", sa.String(50), nullable=False),
        sa.Column("country_code", sa.String(10), nullable=True),
        sa.Column("permission_scope", sa.Text, nullable=True),
        sa.Column("start_time", sa.DateTime, nullable=True),
        sa.Column("end_time", sa.DateTime, nullable=True),
        sa.Column("status", sa.String(20), nullable=True, server_default="active"),
        sa.Column("created_at", sa.DateTime, nullable=True, server_default=sa.func.current_timestamp()),
    )
    op.create_index("idx_active_tasks_employee", "employee_active_tasks", ["employee_id"])

    op.create_table(
        "employee_risk_scores",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("employee_id", sa.Integer, sa.ForeignKey("employees.id", ondelete="CASCADE"), nullable=False),
        sa.Column("metric_name", sa.String(100), nullable=False),
        sa.Column("score", sa.Numeric(5, 2), nullable=False),
        sa.Column("recorded_at", sa.DateTime, nullable=True, server_default=sa.func.current_timestamp()),
        sa.UniqueConstraint("employee_id", "metric_name", name="uq_risk_scores_employee_metric"),
    )
    op.create_index("idx_risk_scores_employee", "employee_risk_scores", ["employee_id"])

    op.create_table(
        "employee_audit_timeline",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("employee_id", sa.Integer, sa.ForeignKey("employees.id", ondelete="CASCADE"), nullable=False),
        sa.Column("event_type", sa.String(100), nullable=False),
        sa.Column("event_data", sa.Text, nullable=True),
        sa.Column("actor_id", sa.Integer, sa.ForeignKey("users.id"), nullable=True),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("user_agent", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=True, server_default=sa.func.current_timestamp()),
    )
    op.create_index("idx_audit_timeline_employee", "employee_audit_timeline", ["employee_id"])
    op.create_index("idx_audit_timeline_created", "employee_audit_timeline", ["created_at"])

    op.create_table(
        "video_rooms",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("room_id", sa.String(100), unique=True, nullable=False),
        sa.Column("room_uuid", sa.String(50), unique=True, nullable=True),
        sa.Column("title", sa.String(200), nullable=True),
        sa.Column("created_by", sa.Integer, sa.ForeignKey("users.id"), nullable=True),
        sa.Column("max_participants", sa.Integer, nullable=True, server_default="100"),
        sa.Column("is_recording", sa.Boolean, nullable=True, server_default="0"),
        sa.Column("settings", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=True, server_default=sa.func.current_timestamp()),
    )
    op.create_index("ix_video_rooms_status", "video_rooms", ["status"])
    op.create_index("ix_video_rooms_created", "video_rooms", ["created_at"])

    op.create_table(
        "chat_threads",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("thread_id", sa.String(100), unique=True, nullable=False),
        sa.Column("entity_type", sa.String(50), nullable=True),
        sa.Column("entity_id", sa.Integer, nullable=True),
        sa.Column("title", sa.String(200), nullable=True),
        sa.Column("created_by", sa.Integer, sa.ForeignKey("users.id"), nullable=True),
        sa.Column("is_direct", sa.Boolean, nullable=True, server_default="0"),
        sa.Column("created_at", sa.DateTime, nullable=True, server_default=sa.func.current_timestamp()),
    )
    op.create_index("idx_chat_threads_entity", "chat_threads", ["entity_type", "entity_id"])

    op.create_table(
        "masked_messages",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("sender_id", sa.Integer, sa.ForeignKey("employees.id"), nullable=True),
        sa.Column("recipient_ref", sa.String(100), nullable=True),
        sa.Column("message_hash", sa.BigInteger, nullable=True),
        sa.Column("content", sa.Text, nullable=True),
        sa.Column("sent_at", sa.DateTime, nullable=True, server_default=sa.func.current_timestamp()),
    )

    op.create_table(
        "incident_rooms",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("room_id", sa.String(100), unique=True, nullable=False),
        sa.Column("severity", sa.String(20), nullable=True),
        sa.Column("title", sa.String(200), nullable=True),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=True, server_default=sa.func.current_timestamp()),
    )

    op.create_table(
        "training_modules",
        sa.Column("module_id", sa.String(100), primary_key=True),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("required_for_role", sa.String(100), nullable=True),
        sa.Column("duration_minutes", sa.Integer, nullable=True, server_default="30"),
        sa.Column("is_active", sa.Boolean, nullable=True, server_default="1"),
        sa.Column("permission_key", sa.String(100), nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=True, server_default=sa.func.current_timestamp()),
    )

    op.create_table(
        "employee_trainings",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("employee_id", sa.Integer, sa.ForeignKey("employees.id", ondelete="CASCADE"), nullable=False),
        sa.Column("module_id", sa.String(100), sa.ForeignKey("training_modules.module_id"), nullable=False),
        sa.Column("assigned_at", sa.DateTime, nullable=True, server_default=sa.func.current_timestamp()),
        sa.Column("completed_at", sa.DateTime, nullable=True),
        sa.Column("score", sa.Numeric(5, 2), nullable=True),
        sa.Column("status", sa.String(20), nullable=True, server_default="assigned"),
        sa.UniqueConstraint("employee_id", "module_id", name="uq_employee_training"),
    )

    op.create_table(
        "country_blackout_dates",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("country_code", sa.String(10), nullable=False),
        sa.Column("date", sa.Date, nullable=False),
        sa.Column("max_leave_percentage", sa.Numeric(5, 2), nullable=True, server_default="20.0"),
        sa.Column("reason", sa.String(200), nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=True, server_default=sa.func.current_timestamp()),
        sa.UniqueConstraint("country_code", "date", name="uq_blackout_date"),
    )

    op.create_table(
        "shift_rosters",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("employee_id", sa.Integer, sa.ForeignKey("employees.id", ondelete="CASCADE"), nullable=False),
        sa.Column("shift_date", sa.Date, nullable=False),
        sa.Column("start_time", sa.Time, nullable=False),
        sa.Column("end_time", sa.Time, nullable=False),
        sa.Column("shift_type", sa.String(30), nullable=True, server_default="scheduled"),
        sa.Column("status", sa.String(20), nullable=True, server_default="scheduled"),
        sa.Column("created_at", sa.DateTime, nullable=True, server_default=sa.func.current_timestamp()),
        sa.UniqueConstraint("employee_id", "shift_date", name="uq_shift_roster"),
    )
    op.create_index("idx_shift_roster_date", "shift_rosters", ["shift_date"])

    op.create_table(
        "treasury_ledger",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("account_id", sa.Integer, sa.ForeignKey("treasury_accounts.id"), nullable=True),
        sa.Column("entry_type", sa.String(20), nullable=False),
        sa.Column("amount", sa.Numeric(15, 2), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("reference_id", sa.String(100), nullable=True),
        sa.Column("entry_date", sa.DateTime, nullable=True, server_default=sa.func.current_timestamp()),
    )

    op.create_table(
        "treasury_accounts",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("employee_id", sa.Integer, sa.ForeignKey("employees.id"), nullable=True),
        sa.Column("account_name", sa.String(200), nullable=True),
        sa.Column("account_type", sa.String(50), nullable=True),
        sa.Column("balance", sa.Numeric(15, 2), nullable=True, server_default="0"),
        sa.Column("currency", sa.String(3), nullable=True, server_default="OMR"),
        sa.Column("is_locked", sa.Boolean, nullable=True, server_default="0"),
        sa.Column("locked_reason", sa.String(200), nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=True, server_default=sa.func.current_timestamp()),
    )


def downgrade():
    op.drop_table("treasury_accounts")
    op.drop_table("treasury_ledger")
    op.drop_table("shift_rosters")
    op.drop_table("country_blackout_dates")
    op.drop_table("employee_trainings")
    op.drop_table("training_modules")
    op.drop_table("incident_rooms")
    op.drop_table("masked_messages")
    op.drop_table("chat_threads")
    op.drop_table("video_rooms")
    op.drop_table("employee_audit_timeline")
    op.drop_table("employee_risk_scores")
    op.drop_table("employee_active_tasks")