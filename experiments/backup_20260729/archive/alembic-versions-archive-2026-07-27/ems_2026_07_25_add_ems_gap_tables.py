"""Add all EMS gap tables — bank accounts, OKR/KPI, performance reviews,
internal email, chat attachments/read receipts, activity ledger, onboarding,
offboarding, leave ledgers, disciplinary cases, and communication threads.

Revision ID: ems_gap_tables_20260725
Revises: 4481d6124799
Create Date: 2026-07-25
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
import json

# revision identifiers, used by Alembic.
revision = "ems_gap_tables_20260725"
down_revision = "4481d6124799"
branch_labels = None
depends_on = None


def _json():
    """Return JSON column type — JSON for SQLite, JSONB for Postgres."""
    return JSONB() if op.get_context().dialect.name == "postgresql" else sa.JSON()


def upgrade() -> None:
    # ──────────────────────────────────────────────────────────────
    # 0. Add performance_score column to employees table
    # ──────────────────────────────────────────────────────────────
    op.add_column(
        "employees",
        sa.Column("performance_score", sa.Numeric(3, 2), nullable=True, comment="Weighted average of 360° reviews, 0.00-5.00"),
    )

    # ──────────────────────────────────────────────────────────────
    # 1. Employee Bank Accounts (payroll disbursement target)
    # ──────────────────────────────────────────────────────────────
    op.create_table(
        "employee_bank_accounts",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("employee_id", sa.Integer(), sa.ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("account_holder_name", sa.String(200), nullable=False),
        sa.Column("bank_name", sa.String(200), nullable=False),
        sa.Column("branch_code", sa.String(50), nullable=True),
        sa.Column("account_number_encrypted", sa.String(500), nullable=False, comment="Encrypted IBAN/account number"),
        sa.Column("iban", sa.String(34), nullable=True),
        sa.Column("swift_code", sa.String(11), nullable=True),
        sa.Column("currency", sa.String(3), default="OMR"),
        sa.Column("is_primary", sa.Boolean(), default=False),
        sa.Column("is_verified", sa.Boolean(), default=False),
        sa.Column("verified_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("verified_at", sa.DateTime(), nullable=True),
        sa.Column("change_requested_at", sa.DateTime(), nullable=True, comment="Freeze period before changes take effect"),
        sa.Column("change_effective_at", sa.DateTime(), nullable=True),
        sa.Column("is_active", sa.Boolean(), default=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index("ix_emp_bank_employee_primary", "employee_bank_accounts", ["employee_id", "is_primary"])

    # ──────────────────────────────────────────────────────────────
    # 2. OKR Objectives (cascaded via hierarchy)
    # ──────────────────────────────────────────────────────────────
    op.create_table(
        "okr_objectives",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("parent_objective_id", sa.Integer(), sa.ForeignKey("okr_objectives.id"), nullable=True),
        sa.Column("org_unit_id", sa.Integer(), nullable=True, comment="FK to org_units.id — created by a separate migration"),
        sa.Column("employee_id", sa.Integer(), sa.ForeignKey("employees.id"), nullable=True),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("objective_type", sa.String(20), default="individual", comment="company | department | individual"),
        sa.Column("quarter", sa.String(10), nullable=False, comment="e.g. 2026-Q3"),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(20), default="draft", comment="draft | active | completed | cancelled"),
        sa.Column("progress_pct", sa.Integer(), default=0),
        sa.Column("confidence_level", sa.Integer(), nullable=True, comment="1-10 scale"),
        sa.Column("country_code", sa.String(10), sa.ForeignKey("country_configs.code"), nullable=True),
        sa.Column("created_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index("ix_okr_org_unit", "okr_objectives", ["org_unit_id"])
    op.create_index("ix_okr_employee", "okr_objectives", ["employee_id"])
    op.create_index("ix_okr_quarter", "okr_objectives", ["quarter", "year"])

    # ──────────────────────────────────────────────────────────────
    # 3. KPI Metrics (quantitative, auto-sourced where possible)
    # ──────────────────────────────────────────────────────────────
    op.create_table(
        "kpi_metrics",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("objective_id", sa.Integer(), sa.ForeignKey("okr_objectives.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("employee_id", sa.Integer(), sa.ForeignKey("employees.id"), nullable=False, index=True),
        sa.Column("metric_name", sa.String(200), nullable=False),
        sa.Column("metric_type", sa.String(30), default="number", comment="number | percentage | currency | boolean | rating"),
        sa.Column("target_value", sa.Numeric(12, 2), nullable=False),
        sa.Column("current_value", sa.Numeric(12, 2), default=0),
        sa.Column("weight_pct", sa.Integer(), default=100, comment="Contribution to objective progress"),
        sa.Column("data_source", sa.String(100), nullable=True, comment="auto-pulled from orders, tickets, sales, etc."),
        sa.Column("auto_source_query", sa.Text(), nullable=True, comment="SQL/snapshot query for auto-refresh"),
        sa.Column("last_auto_refreshed_at", sa.DateTime(), nullable=True),
        sa.Column("country_code", sa.String(10), sa.ForeignKey("country_configs.code"), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index("ix_kpi_objective", "kpi_metrics", ["objective_id", "employee_id"])

    # ──────────────────────────────────────────────────────────────
    # 4. Performance Reviews (360° — self, manager, peers, subordinates)
    # ──────────────────────────────────────────────────────────────
    op.create_table(
        "performance_reviews",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("employee_id", sa.Integer(), sa.ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("review_cycle", sa.String(30), nullable=False, comment="e.g. 2026-Q3, 2026-Annual"),
        sa.Column("review_type", sa.String(30), default="self", comment="self | manager | peer | subordinate | 360"),
        sa.Column("reviewer_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("overall_score", sa.Numeric(5, 2), nullable=True, comment="Weighted 0-5 scale"),
        sa.Column("rating", sa.String(20), nullable=True, comment="exceeds | meets | below | pip"),
        sa.Column("comments", sa.Text(), nullable=True),
        sa.Column("strengths", sa.Text(), nullable=True),
        sa.Column("areas_for_improvement", sa.Text(), nullable=True),
        sa.Column("goals_next_period", sa.Text(), nullable=True),
        sa.Column("status", sa.String(20), default="pending", comment="pending | submitted | acknowledged | closed"),
        sa.Column("submitted_at", sa.DateTime(), nullable=True),
        sa.Column("acknowledged_at", sa.DateTime(), nullable=True),
        sa.Column("country_code", sa.String(10), sa.ForeignKey("country_configs.code"), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index("ix_perf_review_cycle", "performance_reviews", ["employee_id", "review_cycle"])
    op.create_index("ix_perf_review_reviewer", "performance_reviews", ["reviewer_id"])

    # ──────────────────────────────────────────────────────────────
    # 5. Internal Email System
    # ──────────────────────────────────────────────────────────────
    op.create_table(
        "email_folders",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("employee_id", sa.Integer(), sa.ForeignKey("employees.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("folder_type", sa.String(20), default="custom", comment="inbox | sent | drafts | trash | custom"),
        sa.Column("icon", sa.String(50), nullable=True),
        sa.Column("sort_order", sa.Integer(), default=0),
        sa.Column("is_system", sa.Boolean(), default=False, comment="Cannot delete system folders"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_unique_constraint("uq_email_folder_employee_name", "email_folders", ["employee_id", "name"])

    op.create_table(
        "internal_emails",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("thread_id", sa.String(36), nullable=False, index=True, comment="UUID grouping related messages"),
        sa.Column("in_reply_to", sa.Integer(), sa.ForeignKey("internal_emails.id"), nullable=True),
        sa.Column("sender_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("recipients", sa.JSON(), nullable=False, comment="List of {user_id, email, type(to/cc/bcc)} objects"),
        sa.Column("subject", sa.String(500), nullable=False),
        sa.Column("body_html", sa.Text(), nullable=True),
        sa.Column("body_text", sa.Text(), nullable=True),
        sa.Column("attachments_json", sa.JSON(), nullable=True, comment="Array of {media_asset_id, filename, size, mime}"),
        sa.Column("folder_id", sa.Integer(), sa.ForeignKey("email_folders.id"), nullable=True),
        sa.Column("labels", sa.JSON(), nullable=True),
        sa.Column("is_read", sa.Boolean(), default=False),
        sa.Column("is_starred", sa.Boolean(), default=False),
        sa.Column("is_draft", sa.Boolean(), default=False),
        sa.Column("is_external", sa.Boolean(), default=False, comment="True = sent via SMTP relay"),
        sa.Column("external_message_id", sa.String(255), nullable=True, comment="SMTP Message-ID for external tracking"),
        sa.Column("read_at", sa.DateTime(), nullable=True),
        sa.Column("country_code", sa.String(10), sa.ForeignKey("country_configs.code"), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index("ix_email_thread", "internal_emails", ["thread_id", "created_at"])
    op.create_index("ix_email_sender", "internal_emails", ["sender_id", "created_at"])
    op.create_index("ix_email_folder", "internal_emails", ["folder_id", "is_read"])

    # ──────────────────────────────────────────────────────────────
    # 6. Chat Attachments (rich media — image, video, voice, doc)
    # ──────────────────────────────────────────────────────────────
    op.create_table(
        "chat_attachments",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("message_id", sa.Integer(), nullable=False, index=True, comment="FK to direct_chat_messages or group_chat_messages"),
        sa.Column("message_type", sa.String(30), nullable=False, comment="direct_chat | group_chat | channel"),
        sa.Column("media_asset_id", sa.Integer(), sa.ForeignKey("media_assets.id"), nullable=True),
        sa.Column("attachment_type", sa.String(20), nullable=False, comment="image | video | voice | document"),
        sa.Column("file_url", sa.String(500), nullable=False),
        sa.Column("file_name", sa.String(255), nullable=False),
        sa.Column("file_size_bytes", sa.Integer(), nullable=False),
        sa.Column("mime_type", sa.String(100), nullable=True),
        sa.Column("duration_seconds", sa.Integer(), nullable=True, comment="For voice/video notes"),
        sa.Column("waveform_json", sa.JSON(), nullable=True, comment="Voice note waveform visualization data"),
        sa.Column("thumbnail_url", sa.String(500), nullable=True),
        sa.Column("width", sa.Integer(), nullable=True),
        sa.Column("height", sa.Integer(), nullable=True),
        sa.Column("is_processed", sa.Boolean(), default=False, comment="Transcoding/optimization complete"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index("ix_chat_att_msg", "chat_attachments", ["message_id", "message_type"])
    op.create_index("ix_chat_att_type", "chat_attachments", ["attachment_type"])

    # ──────────────────────────────────────────────────────────────
    # 7. Chat Read Receipts
    # ──────────────────────────────────────────────────────────────
    op.create_table(
        "chat_read_receipts",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("message_id", sa.Integer(), nullable=False, index=True),
        sa.Column("message_type", sa.String(30), nullable=False, comment="direct_chat | group_chat | channel"),
        sa.Column("employee_id", sa.Integer(), sa.ForeignKey("employees.id", ondelete="CASCADE"), nullable=False),
        sa.Column("read_at", sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_unique_constraint("uq_chat_read_receipt", "chat_read_receipts", ["message_id", "message_type", "employee_id"])

    # ──────────────────────────────────────────────────────────────
    # 8. Employee Activity / Collaboration Ledger
    # ──────────────────────────────────────────────────────────────
    op.create_table(
        "employee_activity_logs",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("actor_employee_id", sa.Integer(), sa.ForeignKey("employees.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("target_employee_id", sa.Integer(), sa.ForeignKey("employees.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("action", sa.String(100), nullable=False, index=True, comment="e.g. login, attendance_scan, handover, mention, document_share, approval_given"),
        sa.Column("entity_type", sa.String(50), nullable=True, comment="e.g. leave_request, performance_review, chat_message, email"),
        sa.Column("entity_id", sa.Integer(), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=True, comment="Arbitrary event-specific payload"),
        sa.Column("country_code", sa.String(10), sa.ForeignKey("country_configs.code"), nullable=True),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("device_fingerprint", sa.String(255), nullable=True),
        sa.Column("session_id", sa.String(36), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), index=True),
    )
    op.create_index("ix_act_log_actor_time", "employee_activity_logs", ["actor_employee_id", "created_at"])
    op.create_index("ix_act_log_target", "employee_activity_logs", ["target_employee_id"])
    op.create_index("ix_act_log_action", "employee_activity_logs", ["action", "created_at"])
    op.create_index("ix_act_log_country", "employee_activity_logs", ["country_code", "created_at"])

    # ──────────────────────────────────────────────────────────────
    # 9. Employee Communication Threads (for cross-service linking)
    # ──────────────────────────────────────────────────────────────
    op.create_table(
        "employee_communication_threads",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("thread_type", sa.String(30), nullable=False, comment="email_thread | chat_thread | channel_thread | incident"),
        sa.Column("external_key", sa.String(100), nullable=True, comment="Reference key from source system"),
        sa.Column("participants", sa.JSON(), nullable=False, comment="List of employee_id / user_id objects"),
        sa.Column("subject", sa.String(300), nullable=True),
        sa.Column("message_count", sa.Integer(), default=0),
        sa.Column("last_message_at", sa.DateTime(), nullable=True),
        sa.Column("last_message_preview", sa.String(200), nullable=True),
        sa.Column("is_archived", sa.Boolean(), default=False),
        sa.Column("country_code", sa.String(10), sa.ForeignKey("country_configs.code"), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index("ix_comm_thread_type", "employee_communication_threads", ["thread_type", "last_message_at"])
    # Participants index — GIN for Postgres, standard index for SQLite
    dialect = op.get_context().dialect.name
    if dialect == "postgresql":
        op.create_index("ix_comm_thread_participants", "employee_communication_threads", ["participants"], postgresql_using="gin")
    else:
        op.create_index("ix_comm_thread_participants", "employee_communication_threads", ["participants"])

    # ──────────────────────────────────────────────────────────────
    # 10. Onboarding Pipeline
    # ──────────────────────────────────────────────────────────────
    op.create_table(
        "onboarding_pipelines",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("employee_id", sa.Integer(), sa.ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("country_code", sa.String(10), sa.ForeignKey("country_configs.code"), nullable=True),
        sa.Column("current_step", sa.String(50), nullable=True, comment="Alias of the step currently being worked on"),
        sa.Column("total_steps", sa.Integer(), default=0),
        sa.Column("completed_steps", sa.Integer(), default=0),
        sa.Column("status", sa.String(20), default="pending", comment="pending | in_progress | completed | cancelled"),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("due_date", sa.DateTime(), nullable=True, comment="Expected completion date based on SLA sum"),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    op.create_table(
        "onboarding_steps",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("pipeline_id", sa.Integer(), sa.ForeignKey("onboarding_pipelines.id", ondelete="CASCADE"), nullable=False),
        sa.Column("employee_id", sa.Integer(), sa.ForeignKey("employees.id", ondelete="CASCADE"), nullable=True),
        sa.Column("step_name", sa.String(50), nullable=False, comment="document_collection | biometric_enrollment | equipment_assignment | id_card | orientation | system_access | buddy_assignment"),
        sa.Column("label", sa.String(100), nullable=True, comment="Human-readable step name"),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("sla_hours", sa.Integer(), default=24, comment="Expected hours to complete this step"),
        sa.Column("step_order", sa.Integer(), default=0),
        sa.Column("status", sa.String(20), default="pending", comment="pending | in_progress | completed | skipped"),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("completed_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index("ix_onboard_step_pipeline", "onboarding_steps", ["pipeline_id", "step_order"])

    # ──────────────────────────────────────────────────────────────
    # 11. Offboarding Cases
    # ──────────────────────────────────────────────────────────────
    op.create_table(
        "offboarding_cases",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("employee_id", sa.Integer(), sa.ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("country_code", sa.String(10), sa.ForeignKey("country_configs.code"), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True, comment="Reason for offboarding"),
        sa.Column("status", sa.String(20), default="in_progress", comment="in_progress | completed | cancelled"),
        sa.Column("total_steps", sa.Integer(), default=6),
        sa.Column("completed_steps", sa.Integer(), default=0),
        sa.Column("current_step", sa.String(50), nullable=True, comment="Next step to complete"),
        sa.Column("initiated_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("initiated_at", sa.DateTime(), nullable=True),
        sa.Column("notice_period_days", sa.Integer(), default=30),
        sa.Column("proposed_exit_date", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("cancellation_reason", sa.Text(), nullable=True),
        sa.Column("cancelled_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # ──────────────────────────────────────────────────────────────
    # 12. Employee Leave Ledger (allocated / used / carried_forward)
    # ──────────────────────────────────────────────────────────────
    op.create_table(
        "employee_leave_ledgers",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("employee_id", sa.Integer(), sa.ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("leave_type", sa.String(50), nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("allocated_days", sa.Numeric(5, 1), default=0),
        sa.Column("used_days", sa.Numeric(5, 1), default=0),
        sa.Column("carried_forward_days", sa.Numeric(5, 1), default=0),
        sa.Column("pending_days", sa.Numeric(5, 1), default=0, comment="Approved but not yet taken"),
        sa.Column("country_code", sa.String(10), sa.ForeignKey("country_configs.code"), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_unique_constraint("uq_leave_ledger_emp_type_year", "employee_leave_ledgers", ["employee_id", "leave_type", "year"])

    # ──────────────────────────────────────────────────────────────
    # 13. Disciplinary Cases
    # ──────────────────────────────────────────────────────────────
    op.create_table(
        "disciplinary_cases",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("employee_id", sa.Integer(), sa.ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("case_type", sa.String(50), nullable=False, comment="attendance | misconduct | performance | policy_violation | harassment"),
        sa.Column("severity", sa.String(20), default="medium", comment="low | medium | high | critical"),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("evidence_json", sa.JSON(), nullable=True, comment="Array of {file_url, description, uploaded_by}"),
        sa.Column("status", sa.String(20), default="open", comment="open | under_investigation | warning_issued | suspended | closed | dismissed"),
        sa.Column("assigned_investigator", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("resolution", sa.Text(), nullable=True),
        sa.Column("resolution_date", sa.Date(), nullable=True),
        sa.Column("warning_level", sa.Integer(), nullable=True, comment="1=verbal, 2=written, 3=final"),
        sa.Column("suspension_start", sa.Date(), nullable=True),
        sa.Column("suspension_end", sa.Date(), nullable=True),
        sa.Column("country_code", sa.String(10), sa.ForeignKey("country_configs.code"), nullable=True),
        sa.Column("raised_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("approved_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index("ix_disc_case_status", "disciplinary_cases", ["status", "severity"])


def downgrade() -> None:
    """Remove all EMS gap tables in reverse dependency order."""
    tables = [
        "disciplinary_cases",
        "employee_leave_ledgers",
        "offboarding_cases",
        "onboarding_steps",
        "onboarding_pipelines",
        "employee_communication_threads",
        "employee_activity_logs",
        "chat_read_receipts",
        "chat_attachments",
        "internal_emails",
        "email_folders",
        "performance_reviews",
        "kpi_metrics",
        "okr_objectives",
        "employee_bank_accounts",
    ]
    for table in tables:
        op.drop_table(table)
