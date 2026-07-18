"""add_command_center_models

Revision ID: b2c3d4e5f6g7
Revises: a1b2c3d4e5f6
Create Date: 2026-06-24 21:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b2c3d4e5f6g7"
down_revision: Union[str, Sequence[str], None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "system_health_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("event_type", sa.String(50), nullable=False),
        sa.Column("country_code", sa.String(10), nullable=True),
        sa.Column("metric_name", sa.String(100), nullable=False),
        sa.Column("metric_value", sa.Float(), nullable=True),
        sa.Column("threshold_value", sa.Float(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="ok"),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("metadata_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_health_event_type_created", "system_health_events", ["event_type", "created_at"])
    op.create_index("ix_health_event_status_created", "system_health_events", ["status", "created_at"])
    op.create_index("ix_health_event_country_created", "system_health_events", ["country_code", "created_at"])

    op.create_table(
        "search_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("country_code", sa.String(10), nullable=True),
        sa.Column("search_query", sa.String(500), nullable=False),
        sa.Column("results_count", sa.Integer(), nullable=True),
        sa.Column("zero_result", sa.Boolean(), nullable=True, server_default="false"),
        sa.Column("session_id", sa.String(64), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_search_user_created", "search_logs", ["user_id", "created_at"])
    op.create_index("ix_search_query_created", "search_logs", ["search_query", "created_at"])
    op.create_index("ix_search_country_created", "search_logs", ["country_code", "created_at"])
    op.create_index("ix_search_zero_result", "search_logs", ["zero_result"])

    op.create_table(
        "user_sessions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("country_code", sa.String(10), nullable=True),
        sa.Column("session_id", sa.String(64), nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=False),
        sa.Column("ended_at", sa.DateTime(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("device_type", sa.String(20), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("referrer", sa.String(500), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_user_session_user_active", "user_sessions", ["user_id", "is_active"])
    op.create_index("ix_user_session_country_active", "user_sessions", ["country_code", "is_active"])
    op.create_index("ix_user_session_started", "user_sessions", ["started_at"])
    op.create_index("ix_user_session_id", "user_sessions", ["session_id"], unique=True)

    op.create_table(
        "news_sources",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("url", sa.String(500), nullable=False),
        sa.Column("source_type", sa.String(20), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("refresh_minutes", sa.Integer(), nullable=False, server_default="15"),
        sa.Column("last_fetched_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_news_source_active", "news_sources", ["is_active"])
    op.create_index("ix_news_source_type", "news_sources", ["source_type"])

    op.create_table(
        "news_articles",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("source_id", sa.Integer(), nullable=False),
        sa.Column("external_id", sa.String(255), nullable=True),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("url", sa.String(500), nullable=False),
        sa.Column("image_url", sa.String(500), nullable=True),
        sa.Column("published_at", sa.DateTime(), nullable=True),
        sa.Column("country_code", sa.String(10), nullable=True),
        sa.Column("tags", sa.Text(), nullable=True),
        sa.Column("sentiment", sa.String(20), nullable=True),
        sa.Column("relevance_score", sa.Float(), nullable=True, server_default="0.0"),
        sa.Column("is_read", sa.Boolean(), nullable=True, server_default="false"),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["source_id"], ["news_sources.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_news_article_source_created", "news_articles", ["source_id", "published_at"])
    op.create_index("ix_news_article_country_created", "news_articles", ["country_code", "published_at"])
    op.create_index("ix_news_article_tags_created", "news_articles", ["tags", "published_at"])

    op.create_table(
        "system_alerts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("alert_type", sa.String(50), nullable=False),
        sa.Column("country_code", sa.String(10), nullable=True),
        sa.Column("severity", sa.String(20), nullable=False, server_default="medium"),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("related_entity_type", sa.String(50), nullable=True),
        sa.Column("related_entity_id", sa.Integer(), nullable=True),
        sa.Column("assigned_to", sa.Integer(), nullable=True),
        sa.Column("acknowledged_by", sa.Integer(), nullable=True),
        sa.Column("acknowledged_at", sa.DateTime(), nullable=True),
        sa.Column("resolved_by", sa.Integer(), nullable=True),
        sa.Column("resolved_at", sa.DateTime(), nullable=True),
        sa.Column("resolution_notes", sa.Text(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="open"),
        sa.Column("escalation_level", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["assigned_to"], ["users.id"]),
        sa.ForeignKeyConstraint(["acknowledged_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["resolved_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_alert_status_created", "system_alerts", ["status", "created_at"])
    op.create_index("ix_alert_severity_created", "system_alerts", ["severity", "created_at"])
    op.create_index("ix_alert_country_created", "system_alerts", ["country_code", "created_at"])

    op.create_table(
        "command_center_views",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("layout_config", sa.Text(), nullable=True),
        sa.Column("favorite_metrics", sa.Text(), nullable=True),
        sa.Column("hidden_zones", sa.Text(), nullable=True),
        sa.Column("notification_preferences", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "employees",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("country_code", sa.String(10), nullable=True),
        sa.Column("employee_id", sa.String(50), nullable=True),
        sa.Column("position", sa.String(120), nullable=True),
        sa.Column("department", sa.String(120), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("hire_date", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_employees_user_active", "employees", ["user_id", "is_active"])
    op.create_index("ix_employees_country_active", "employees", ["country_code", "is_active"])
    op.create_index("ix_employees_status", "employees", ["status"])

    op.add_column("logistics_partners", sa.Column("type", sa.String(20), nullable=False, server_default="company"))
    op.create_index("ix_logistics_partners_type", "logistics_partners", ["type"])


def downgrade() -> None:
    op.drop_index("ix_logistics_partners_type", table_name="logistics_partners")
    op.drop_column("logistics_partners", "type")
    op.drop_table("employees")
    op.drop_table("command_center_views")
    op.drop_table("system_alerts")
    op.drop_index("ix_news_article_tags_created", table_name="news_articles")
    op.drop_index("ix_news_article_country_created", table_name="news_articles")
    op.drop_index("ix_news_article_source_created", table_name="news_articles")
    op.drop_table("news_articles")
    op.drop_index("ix_news_source_type", table_name="news_sources")
    op.drop_index("ix_news_source_active", table_name="news_sources")
    op.drop_table("news_sources")
    op.drop_index("ix_user_session_started", table_name="user_sessions")
    op.drop_index("ix_user_session_country_active", table_name="user_sessions")
    op.drop_index("ix_user_session_user_active", table_name="user_sessions")
    op.drop_index("ix_user_session_id", table_name="user_sessions")
    op.drop_table("user_sessions")
    op.drop_index("ix_search_zero_result", table_name="search_logs")
    op.drop_index("ix_search_country_created", table_name="search_logs")
    op.drop_index("ix_search_query_created", table_name="search_logs")
    op.drop_index("ix_search_user_created", table_name="search_logs")
    op.drop_table("search_logs")
    op.drop_index("ix_health_event_country_created", table_name="system_health_events")
    op.drop_index("ix_health_event_status_created", table_name="system_health_events")
    op.drop_index("ix_health_event_type_created", table_name="system_health_events")
    op.drop_table("system_health_events")

