"""move governance-owned tables into the ``governance`` schema (GOV-SCHEMA G1)

30 tables that are owned by the governance domain but declared under
forbidden or unsanctioned schemas are moved into the canonical ``governance``
schema (one Postgres schema per domain, ARCHITECTURE_DIAGRAM.md Sec. 9, Law 6).

Source schemas:
- ``comms`` (7): tables that were in ``communication`` and got renamed to
  ``comms`` by the preceding migration; these are governance-owned
  (push_notification_tokens, ticket_replies, meeting_recordings, incident_*,
  war_room_templates).
- ``security`` (16): fraud/incident tables owned by governance.
- ``configuration`` (3): system_alerts, system_settings, email_provider_configs.
- ``core`` (2, forbidden schema): api_keys, role_permission_settings.
- ``analytics`` (2): processed_webhook_events, normalized_webhook_events
  (ANL-SCHEMA-1: these are payment-webhook idempotency tables, semantically
  governance, not analytics).

PostgreSQL moves each table (with its indexes, constraints, owned sequences
and cross-references) atomically via ``ALTER TABLE ... SET SCHEMA`` -- no data
is rewritten. The statements are guarded with ``IF EXISTS`` so the migration
is idempotent and safe to re-run on a DB that was already upgraded.

On SQLite (dev) the ORM + ``create_all`` already produce the correctly-named
tables under the declared schema, so this migration is a no-op there.

Revision ID: 20260822_governance_schema_consolidation
Revises: 20260822_communication_to_comms_schema
Create Date: 2026-08-22
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260822_governance_schema_consolidation"
down_revision: Union[str, None] = "20260822_communication_to_comms_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# (table_name, source_schema) -- all target ``governance``
_MOVES = [
    # comms (was communication, renamed by preceding migration)
    ("push_notification_tokens", "comms"),
    ("ticket_replies", "comms"),
    ("meeting_recordings", "comms"),
    ("incident_action_items", "comms"),
    ("incident_threads", "comms"),
    ("incident_war_rooms", "comms"),
    ("war_room_templates", "comms"),
    # security (unsanctioned)
    ("credit_card_bins", "security"),
    ("device_fingerprints", "security"),
    ("dlp_violations", "security"),
    ("fraud_alerts", "security"),
    ("fraud_blacklist", "security"),
    ("fraud_case_assignments", "security"),
    ("fraud_cases", "security"),
    ("fraud_events", "security"),
    ("fraud_rules", "security"),
    ("fraud_scoring_logs", "security"),
    ("fraud_velocity_counters", "security"),
    ("ip_account_linkages", "security"),
    ("ip_reputations", "security"),
    ("manual_review_queue", "security"),
    ("meeting_action_items", "security"),
    ("meeting_transcripts", "security"),
    # configuration (unsanctioned)
    ("email_provider_configs", "configuration"),
    ("system_alerts", "configuration"),
    ("system_settings", "configuration"),
    # core (forbidden schema)
    ("api_keys", "core"),
    ("role_permission_settings", "core"),
    # analytics (ANL-SCHEMA-1: payment-webhook idempotency)
    ("processed_webhook_events", "analytics"),
    ("normalized_webhook_events", "analytics"),
]


def _exec(sql: str) -> None:
    op.execute(sa.text(sql))


def upgrade() -> None:
    if op.get_context().dialect.name != "postgresql":
        return

    _exec("CREATE SCHEMA IF NOT EXISTS governance")

    for table, source_schema in _MOVES:
        _exec(
            "ALTER TABLE IF EXISTS {s}.{t} SET SCHEMA governance".format(
                s=source_schema, t=table
            )
        )


def downgrade() -> None:
    if op.get_context().dialect.name != "postgresql":
        return

    for table, source_schema in _MOVES:
        _exec(
            "ALTER TABLE IF EXISTS governance.{t} SET SCHEMA {s}".format(
                s=source_schema, t=table
            )
        )
