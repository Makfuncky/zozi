"""baseline sync: materialise every ORM table explicitly.

Contract artifact for DBA13 (ORM tables must appear as literal
``op.create_table`` operations in the migration chain) and for production
readiness (the full schema must be explicitly reproducible from migrations,
not only via the dev-only runtime schema-materialisation path.

Guarded per table so the migration is idempotent on every environment:
* SQLite (dev / tests): no-op.
* PostgreSQL: a table is created only if it does not already exist
  (the baseline migration materialises the schema at runtime on fresh
  databases, so the checks below are no-ops there too).
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect
from sqlalchemy.dialects import postgresql

import infrastructure.utils.encryption  # noqa: F401
revision = "20260806_0003"
down_revision = "20260806_0002"
branch_labels = None
depends_on = None


def _has_table(name: str, schema: str | None = None) -> bool:
    return name in set(inspect(op.get_bind()).get_table_names(schema=schema))


def upgrade() -> None:
    if op.get_bind().dialect.name == "sqlite":
        return

    if not _has_table('account_balances', 'finance'):
        op.create_table('account_balances',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('account_id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=True),
            sa.Column('balance', sa.Numeric(precision=16, scale=4), nullable=True),
            sa.Column('currency', sa.String(length=3), nullable=True),
            sa.Column('last_entry_id', sa.Integer(), nullable=True),
            sa.Column('last_entry_at', sa.DateTime(), nullable=True),
            sa.Column('last_updated', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='finance',
    )

    if not _has_table('account_groups', 'finance'):
        op.create_table('account_groups',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('code', sa.String(length=10), nullable=False, unique=True),
            sa.Column('name', sa.String(length=100), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('account_type', sa.String(length=30), nullable=False),
            sa.Column('normal_side', sa.String(length=10), nullable=False),
            sa.Column('display_order', sa.Integer(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='finance',
    )

    if not _has_table('accounts', 'finance'):
        op.create_table('accounts',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('group_id', sa.Integer(), nullable=True),
            sa.Column('code', sa.String(length=20), nullable=False, unique=True),
            sa.Column('name', sa.String(length=200), nullable=False),
            sa.Column('normal_side', sa.String(length=10), nullable=False),
            sa.Column('currency', sa.String(length=3), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='finance',
    )

    if not _has_table('accruals', 'finance'):
        op.create_table('accruals',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('accrual_type', sa.String(length=20), nullable=False),
            sa.Column('description', sa.String(length=500), nullable=True),
            sa.Column('amount', sa.Numeric(precision=14, scale=2), nullable=False),
            sa.Column('expense_account_code', sa.String(length=20), nullable=False),
            sa.Column('accrual_account_code', sa.String(length=20), nullable=False),
            sa.Column('accrual_date', sa.DateTime(), nullable=False),
            sa.Column('reversal_date', sa.DateTime(), nullable=True),
            sa.Column('status', sa.String(length=20), nullable=True),
            sa.Column('journal_entry_id', sa.Integer(), nullable=True),
            sa.Column('reversal_entry_id', sa.Integer(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='finance',
    )

    if not _has_table('activity_logs', 'hr'):
        op.create_table('activity_logs',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('action', sa.String(length=120), nullable=True),
            sa.Column('entity_type', sa.String(length=60), nullable=True),
            sa.Column('entity_id', sa.Integer(), nullable=True),
            sa.Column('metadata_json', sa.JSON(), nullable=True),
            sa.Column('ip_address', sa.String(length=45), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='hr',
    )

    if not _has_table('addresses', 'customer'):
        op.create_table('addresses',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('label', sa.String(), nullable=True),
            sa.Column('full_name', sa.String(), nullable=False),
            sa.Column('phone', sa.String(), nullable=True),
            sa.Column('address_line1', sa.String(), nullable=False),
            sa.Column('address_line2', sa.String(), nullable=True),
            sa.Column('city', sa.String(), nullable=False),
            sa.Column('state', sa.String(), nullable=True),
            sa.Column('postal_code', sa.String(), nullable=True),
            sa.Column('country', sa.String(), nullable=True),
            sa.Column('is_default', sa.Boolean(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='customer',
    )

    if not _has_table('admin_activity_logs', 'audit'):
        op.create_table('admin_activity_logs',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('admin_id', sa.Integer(), nullable=False),
            sa.Column('action', sa.String(), nullable=False),
            sa.Column('details', sa.JSON(), nullable=True),
            sa.Column('ip_address', sa.String(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='audit',
    )

    if not _has_table('admin_analytics_snapshots', 'audit'):
        op.create_table('admin_analytics_snapshots',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('snapshot_key', sa.String(length=120), nullable=False),
            sa.Column('snapshot_group', sa.String(length=80), nullable=False),
            sa.Column('period', sa.String(length=40), nullable=True),
            sa.Column('payload_json', sa.Text(), nullable=False),
            sa.Column('computed_at', sa.DateTime(), nullable=False),
            sa.Column('expires_at', sa.DateTime(), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
            sa.Column('created_by', sa.Integer(), nullable=True),
            sa.Column('updated_by', sa.Integer(), nullable=True),
            sa.Column('is_deleted', sa.Boolean(), nullable=False),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='audit',
    )

    if not _has_table('admin_change_audit_logs', 'audit'):
        op.create_table('admin_change_audit_logs',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('admin_id', sa.Integer(), nullable=False),
            sa.Column('action', sa.String(), nullable=False),
            sa.Column('entity', sa.String(), nullable=False),
            sa.Column('entity_key', sa.String(), nullable=True),
            sa.Column('before_json', sa.Text(), nullable=True),
            sa.Column('after_json', sa.Text(), nullable=True),
            sa.Column('notes', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='audit',
    )

    if not _has_table('ai_audit_log', 'ai'):
        op.create_table('ai_audit_log',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('job_id', sa.Integer(), nullable=True),
            sa.Column('operation', sa.String(length=50), nullable=False),
            sa.Column('model_name', sa.String(length=100), nullable=False),
            sa.Column('input_tokens', sa.Integer(), nullable=True),
            sa.Column('output_tokens', sa.Integer(), nullable=True),
            sa.Column('cost', sa.Numeric(precision=12, scale=6), nullable=True),
            sa.Column('status', sa.String(length=20), nullable=False),
            sa.Column('error_message', sa.Text(), nullable=True),
            sa.Column('initiated_by', sa.Integer(), nullable=True),
            sa.Column('completed_at', sa.DateTime(), nullable=True),
            sa.Column('request_json', sa.Text(), nullable=True),
            sa.Column('response_json', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='ai',
    )

    if not _has_table('ai_embeddings', 'ai'):
        op.create_table('ai_embeddings',
                    sa.Column('id', sa.String(length=36), primary_key=True, nullable=False),
            sa.Column('source_type', sa.String(length=50), nullable=False),
            sa.Column('source_id', sa.String(length=100), nullable=False),
            sa.Column('model_name', sa.String(length=100), nullable=False),
            sa.Column('vector', sa.Text(), nullable=False),
            sa.Column('content_hash', sa.String(length=64), nullable=False, unique=True),
            sa.Column('created_at', sa.DateTime(), nullable=False), schema='ai',
    )

    if not _has_table('ai_generation_logs', 'ai'):
        op.create_table('ai_generation_logs',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('job_id', sa.Integer(), nullable=False),
            sa.Column('field', sa.String(length=40), nullable=False),
            sa.Column('model_used', sa.String(length=100), nullable=True),
            sa.Column('prompt_hash', sa.String(length=64), nullable=True),
            sa.Column('tokens_used', sa.Numeric(precision=12, scale=2), nullable=True),
            sa.Column('cost', sa.Numeric(precision=12, scale=6), nullable=True),
            sa.Column('confidence', sa.Numeric(precision=5, scale=4), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='ai',
    )

    if not _has_table('ai_requests', 'ai'):
        op.create_table('ai_requests',
                    sa.Column('id', sa.String(length=36), primary_key=True, nullable=False),
            sa.Column('provider', sa.String(length=50), nullable=False),
            sa.Column('model', sa.String(length=100), nullable=False),
            sa.Column('prompt', sa.Text(), nullable=False),
            sa.Column('metadata', sa.JSON(), nullable=True),
            sa.Column('user_id', sa.Integer(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='ai',
    )

    if not _has_table('ai_results', 'ai'):
        op.create_table('ai_results',
                    sa.Column('id', sa.String(length=36), primary_key=True, nullable=False),
            sa.Column('request_id', sa.String(length=36), nullable=False),
            sa.Column('response', sa.Text(), nullable=True),
            sa.Column('tokens_used', sa.Integer(), nullable=True),
            sa.Column('cost_cents', sa.Integer(), nullable=True),
            sa.Column('latency_ms', sa.Integer(), nullable=True),
            sa.Column('success', sa.Boolean(), nullable=False),
            sa.Column('error_message', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='ai',
    )

    if not _has_table('ai_staging_images', 'ai'):
        op.create_table('ai_staging_images',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('job_id', sa.Integer(), nullable=False),
            sa.Column('staging_product_id', sa.Integer(), nullable=True),
            sa.Column('staging_variant_id', sa.Integer(), nullable=True),
            sa.Column('source_image_url', sa.String(), nullable=False),
            sa.Column('processed_image_url', sa.String(), nullable=True),
            sa.Column('operation', sa.String(length=50), nullable=False),
            sa.Column('model_used', sa.String(length=100), nullable=True),
            sa.Column('prompt', sa.Text(), nullable=True),
            sa.Column('confidence_score', sa.Numeric(precision=5, scale=4), nullable=True),
            sa.Column('requires_human_review', sa.Boolean(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='ai',
    )

    if not _has_table('ai_staging_products', 'ai'):
        op.create_table('ai_staging_products',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('job_id', sa.Integer(), nullable=False),
            sa.Column('product_id', sa.Integer(), nullable=True),
            sa.Column('name', sa.String(), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('price', sa.Numeric(precision=10, scale=2), nullable=True),
            sa.Column('stock', sa.Integer(), nullable=True),
            sa.Column('category', sa.String(), nullable=True),
            sa.Column('subcategory', sa.String(), nullable=True),
            sa.Column('color', sa.String(), nullable=True),
            sa.Column('brand', sa.String(), nullable=True),
            sa.Column('tags', sa.JSON(), nullable=True),
            sa.Column('sizes', sa.JSON(), nullable=True),
            sa.Column('materials', sa.JSON(), nullable=True),
            sa.Column('image_url', sa.String(), nullable=True),
            sa.Column('additional_media', sa.JSON(), nullable=True),
            sa.Column('ai_description', sa.Text(), nullable=True),
            sa.Column('variant_axes', sa.JSON(), nullable=True),
            sa.Column('attributes', sa.JSON(), nullable=True),
            sa.Column('confidence_score', sa.Numeric(precision=5, scale=4), nullable=True),
            sa.Column('requires_human_review', sa.Boolean(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='ai',
    )

    if not _has_table('ai_staging_variants', 'ai'):
        op.create_table('ai_staging_variants',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('job_id', sa.Integer(), nullable=False),
            sa.Column('staging_product_id', sa.Integer(), nullable=False),
            sa.Column('variant_key', sa.String(length=64), nullable=True),
            sa.Column('size', sa.String(), nullable=True),
            sa.Column('color', sa.String(), nullable=True),
            sa.Column('material', sa.String(), nullable=True),
            sa.Column('pattern', sa.String(), nullable=True),
            sa.Column('gender', sa.String(), nullable=True),
            sa.Column('sku', sa.String(), nullable=True),
            sa.Column('barcode', sa.String(), nullable=True),
            sa.Column('product_code', sa.String(), nullable=True),
            sa.Column('price', sa.Numeric(precision=10, scale=2), nullable=True),
            sa.Column('stock', sa.Integer(), nullable=True),
            sa.Column('media_url', sa.String(), nullable=True),
            sa.Column('attributes_json', sa.Text(), nullable=True),
            sa.Column('requires_human_review', sa.Boolean(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='ai',
    )

    if not _has_table('ai_upload_jobs', 'ai'):
        op.create_table('ai_upload_jobs',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('supplier_id', sa.Integer(), nullable=False),
            sa.Column('status', sa.String(length=20), nullable=False),
            sa.Column('model_used', sa.String(length=100), nullable=True),
            sa.Column('prompt_hash', sa.String(length=64), nullable=True),
            sa.Column('tokens_used', sa.Numeric(precision=12, scale=2), nullable=True),
            sa.Column('source_media_json', sa.Text(), nullable=True),
            sa.Column('created_product_id', sa.Integer(), nullable=True),
            sa.Column('error_log', sa.Text(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='ai',
    )

    if not _has_table('alert_escalation_rules', 'security'):
        op.create_table('alert_escalation_rules',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('alert_type', sa.String(length=50), nullable=False),
            sa.Column('severity', sa.String(length=20), nullable=True),
            sa.Column('threshold_value', sa.Numeric(precision=15, scale=2), nullable=True),
            sa.Column('current_tier', sa.Integer(), nullable=True), schema='security',
    )

    if not _has_table('alumni_network', 'hr'):
        op.create_table('alumni_network',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('employee_id', sa.Integer(), nullable=False, unique=True),
            sa.Column('status', sa.String(length=20), nullable=True),
            sa.Column('granted_at', sa.DateTime(), nullable=True),
            sa.Column('eligibility_expires_at', sa.DateTime(), nullable=True),
            sa.Column('notes', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='hr',
    )

    if not _has_table('announcements', 'communication'):
        op.create_table('announcements',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('title', sa.String(), nullable=False),
            sa.Column('content', sa.Text(), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=True),
            sa.Column('starts_at', sa.DateTime(), nullable=True),
            sa.Column('ends_at', sa.DateTime(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True), schema='communication',
    )

    if not _has_table('ap_bills', 'finance'):
        op.create_table('ap_bills',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('vendor_id', sa.Integer(), nullable=False),
            sa.Column('bill_number', sa.String(length=80), nullable=True),
            sa.Column('bill_date', sa.DateTime(), nullable=False),
            sa.Column('due_date', sa.DateTime(), nullable=True),
            sa.Column('account_code', sa.String(length=20), nullable=False),
            sa.Column('amount', sa.Numeric(precision=14, scale=2), nullable=False),
            sa.Column('tax_amount', sa.Numeric(precision=14, scale=2), nullable=True),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('status', sa.String(length=20), nullable=True),
            sa.Column('linked_journal_entry_id', sa.Integer(), nullable=True),
            sa.Column('paid_journal_entry_id', sa.Integer(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='finance',
    )

    if not _has_table('ap_ledger_entries', 'finance'):
        op.create_table('ap_ledger_entries',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('supplier_id', sa.Integer(), nullable=False),
            sa.Column('order_id', sa.Integer(), nullable=True),
            sa.Column('invoice_id', sa.Integer(), nullable=True),
            sa.Column('settlement_id', sa.Integer(), nullable=True),
            sa.Column('reference_type', sa.String(length=50), nullable=True),
            sa.Column('reference_id', sa.Integer(), nullable=True),
            sa.Column('entry_type', sa.String(length=20), nullable=False),
            sa.Column('amount', sa.Numeric(precision=12, scale=2), nullable=False),
            sa.Column('balance_after', sa.Numeric(precision=12, scale=2), nullable=True),
            sa.Column('currency', sa.String(length=3), nullable=True),
            sa.Column('status', sa.String(length=20), nullable=True),
            sa.Column('due_date', sa.DateTime(), nullable=True),
            sa.Column('paid_at', sa.DateTime(), nullable=True),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('created_by', sa.Integer(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('deleted_at', sa.DateTime(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='finance',
    )

    if not _has_table('api_keys', 'security'):
        op.create_table('api_keys',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('name', sa.String(), nullable=False),
            sa.Column('key_hash', sa.String(), nullable=False),
            sa.Column('permissions', sa.JSON(), nullable=True),
            sa.Column('created_by', sa.Integer(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='security',
    )

    if not _has_table('approval_requests', 'hr'):
        op.create_table('approval_requests',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('assignee_id', sa.Integer(), nullable=False),
            sa.Column('requester_id', sa.Integer(), nullable=True),
            sa.Column('approval_type', sa.String(length=60), nullable=True),
            sa.Column('status', sa.String(length=20), nullable=True),
            sa.Column('reason', sa.Text(), nullable=True),
            sa.Column('decision_note', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='hr',
    )

    if not _has_table('ar_invoices', 'finance'):
        op.create_table('ar_invoices',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('customer_id', sa.Integer(), nullable=False),
            sa.Column('invoice_number', sa.String(length=80), nullable=True),
            sa.Column('invoice_date', sa.DateTime(), nullable=False),
            sa.Column('due_date', sa.DateTime(), nullable=True),
            sa.Column('account_code', sa.String(length=20), nullable=True),
            sa.Column('amount', sa.Numeric(precision=14, scale=2), nullable=False),
            sa.Column('tax_amount', sa.Numeric(precision=14, scale=2), nullable=True),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('status', sa.String(length=20), nullable=True),
            sa.Column('linked_journal_entry_id', sa.Integer(), nullable=True),
            sa.Column('paid_journal_entry_id', sa.Integer(), nullable=True),
            sa.Column('reference_order_id', sa.Integer(), nullable=True),
            sa.Column('vat_amount', sa.Numeric(precision=14, scale=2), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='finance',
    )

    if not _has_table('ar_ledger_entries', 'finance'):
        op.create_table('ar_ledger_entries',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('customer_id', sa.Integer(), nullable=False),
            sa.Column('order_id', sa.Integer(), nullable=True),
            sa.Column('invoice_id', sa.Integer(), nullable=True),
            sa.Column('reference_type', sa.String(length=50), nullable=True),
            sa.Column('reference_id', sa.Integer(), nullable=True),
            sa.Column('entry_type', sa.String(length=20), nullable=False),
            sa.Column('amount', sa.Numeric(precision=12, scale=2), nullable=False),
            sa.Column('balance_after', sa.Numeric(precision=12, scale=2), nullable=True),
            sa.Column('currency', sa.String(length=3), nullable=True),
            sa.Column('status', sa.String(length=20), nullable=True),
            sa.Column('due_date', sa.DateTime(), nullable=True),
            sa.Column('settled_at', sa.DateTime(), nullable=True),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('created_by', sa.Integer(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('deleted_at', sa.DateTime(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='finance',
    )

    if not _has_table('audit_logs', 'audit'):
        op.create_table('audit_logs',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('action', sa.String(), nullable=False),
            sa.Column('entity_type', sa.String(), nullable=False),
            sa.Column('entity_id', sa.Integer(), nullable=True),
            sa.Column('user_id', sa.Integer(), nullable=True),
            sa.Column('username', sa.String(), nullable=True),
            sa.Column('user_role', sa.String(), nullable=True),
            sa.Column('details', sa.JSON(), nullable=True),
            sa.Column('ip_address', sa.String(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True), schema='audit',
    )

    if not _has_table('automation_logs', 'finance'):
        op.create_table('automation_logs',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('rule_id', sa.Integer(), nullable=False),
            sa.Column('status', sa.String(length=20), nullable=True),
            sa.Column('detail', sa.JSON(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='finance',
    )

    if not _has_table('automation_rules', 'finance'):
        op.create_table('automation_rules',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('name', sa.String(length=120), nullable=False),
            sa.Column('trigger_type', sa.String(length=40), nullable=True),
            sa.Column('config', sa.JSON(), nullable=True),
            sa.Column('is_active', sa.Boolean(), nullable=True),
            sa.Column('created_by', sa.Integer(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='finance',
    )

    if not _has_table('badge_billing_records', 'commerce'):
        op.create_table('badge_billing_records',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=True),
            sa.Column('supplier_id', sa.Integer(), nullable=True),
            sa.Column('billing_reference', sa.String(), nullable=True, unique=True),
            sa.Column('badge_level', sa.String(length=50), nullable=True),
            sa.Column('charge_type', sa.String(), nullable=True),
            sa.Column('charge_source', sa.String(), nullable=True),
            sa.Column('amount', sa.Numeric(precision=12, scale=2), nullable=False),
            sa.Column('currency', sa.String(length=3), nullable=True),
            sa.Column('status', sa.String(), nullable=True),
            sa.Column('reference_id', sa.String(), nullable=True),
            sa.Column('period_start_at', sa.DateTime(), nullable=True),
            sa.Column('period_end_at', sa.DateTime(), nullable=True),
            sa.Column('due_at', sa.DateTime(), nullable=True),
            sa.Column('billed_at', sa.DateTime(), nullable=True),
            sa.Column('paid_at', sa.DateTime(), nullable=True),
            sa.Column('payment_method', sa.String(), nullable=True),
            sa.Column('notes', sa.Text(), nullable=True),
            sa.Column('created_by', sa.Integer(), nullable=True),
            sa.Column('bank_transaction_id', sa.Integer(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='commerce',
    )

    if not _has_table('badge_tiers', 'commerce'):
        op.create_table('badge_tiers',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('name', sa.String(), nullable=False),
            sa.Column('min_points', sa.Integer(), nullable=False),
            sa.Column('benefits_json', sa.JSON(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='commerce',
    )

    if not _has_table('badge_transactions', 'commerce'):
        op.create_table('badge_transactions',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('amount', sa.Numeric(precision=12, scale=2), nullable=False),
            sa.Column('transaction_type', sa.String(), nullable=False),
            sa.Column('reference_id', sa.String(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='commerce',
    )

    if not _has_table('bank_accounts', 'finance'):
        op.create_table('bank_accounts',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('bank_name', sa.String(length=160), nullable=False),
            sa.Column('account_name', sa.String(length=200), nullable=True),
            sa.Column('account_number', sa.String(length=60), nullable=True),
            sa.Column('iban', sa.String(length=60), nullable=True),
            sa.Column('swift_bic', sa.String(length=20), nullable=True),
            sa.Column('currency', sa.String(length=3), nullable=True),
            sa.Column('gl_account_code', sa.String(length=20), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='finance',
    )

    if not _has_table('bank_mapping_rules', 'finance'):
        op.create_table('bank_mapping_rules',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('match_pattern', sa.String(length=300), nullable=False),
            sa.Column('description_contains', sa.String(length=300), nullable=True),
            sa.Column('account_code', sa.String(length=20), nullable=False),
            sa.Column('normal_side', sa.String(length=10), nullable=False),
            sa.Column('category', sa.String(length=40), nullable=True),
            sa.Column('priority', sa.Integer(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='finance',
    )

    if not _has_table('bank_reconciliations', 'finance'):
        op.create_table('bank_reconciliations',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('statement_line_id', sa.Integer(), nullable=False),
            sa.Column('journal_entry_id', sa.Integer(), nullable=True),
            sa.Column('matched_amount', sa.Numeric(precision=14, scale=2), nullable=True),
            sa.Column('status', sa.String(length=20), nullable=True),
            sa.Column('note', sa.Text(), nullable=True),
            sa.Column('matched_by', sa.Integer(), nullable=True),
            sa.Column('matched_at', sa.DateTime(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='finance',
    )

    if not _has_table('bank_statement_imports', 'finance'):
        op.create_table('bank_statement_imports',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('bank_name', sa.String(length=120), nullable=True),
            sa.Column('file_name', sa.String(length=255), nullable=True),
            sa.Column('statement_period_start', sa.DateTime(), nullable=True),
            sa.Column('statement_period_end', sa.DateTime(), nullable=True),
            sa.Column('currency', sa.String(length=3), nullable=True),
            sa.Column('total_lines', sa.Integer(), nullable=True),
            sa.Column('matched_lines', sa.Integer(), nullable=True),
            sa.Column('unmatched_lines', sa.Integer(), nullable=True),
            sa.Column('status', sa.String(length=20), nullable=True),
            sa.Column('imported_by', sa.Integer(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='finance',
    )

    if not _has_table('bank_statement_lines', 'finance'):
        op.create_table('bank_statement_lines',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('import_id', sa.Integer(), nullable=False),
            sa.Column('txn_date', sa.DateTime(), nullable=True),
            sa.Column('description', sa.String(length=500), nullable=True),
            sa.Column('reference', sa.String(length=120), nullable=True),
            sa.Column('amount', sa.Numeric(precision=14, scale=2), nullable=False),
            sa.Column('mapped_account_code', sa.String(length=20), nullable=True),
            sa.Column('mapped_side', sa.String(length=10), nullable=True),
            sa.Column('mapping_rule_id', sa.Integer(), nullable=True),
            sa.Column('status', sa.String(length=20), nullable=True),
            sa.Column('posted_journal_entry_id', sa.Integer(), nullable=True),
            sa.Column('reconciled_transaction_id', sa.Integer(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='finance',
    )

    if not _has_table('bank_transactions', 'finance'):
        op.create_table('bank_transactions',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('transaction_ref', sa.String(), nullable=True),
            sa.Column('source', sa.String(), nullable=True),
            sa.Column('transaction_type', sa.String(), nullable=False),
            sa.Column('category', sa.String(), nullable=True),
            sa.Column('amount', sa.Numeric(precision=12, scale=2), nullable=False),
            sa.Column('currency', sa.String(length=3), nullable=True),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('linked_order_id', sa.Integer(), nullable=True),
            sa.Column('linked_supplier_id', sa.Integer(), nullable=True),
            sa.Column('linked_logistics_id', sa.Integer(), nullable=True),
            sa.Column('linked_payout_id', sa.Integer(), nullable=True),
            sa.Column('linked_refund_id', sa.Integer(), nullable=True),
            sa.Column('reconciled', sa.Boolean(), nullable=True),
            sa.Column('reconciled_by', sa.Integer(), nullable=True),
            sa.Column('reconciled_at', sa.DateTime(), nullable=True),
            sa.Column('transaction_date', sa.DateTime(), nullable=True),
            sa.Column('status', sa.String(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('flag_reason', sa.Text(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='finance',
    )

    if not _has_table('banners', 'commerce'):
        op.create_table('banners',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('title', sa.String(), nullable=False),
            sa.Column('subtitle', sa.String(), nullable=True),
            sa.Column('image_url', sa.String(), nullable=True),
            sa.Column('link', sa.String(), nullable=True),
            sa.Column('banner_type', sa.String(), nullable=True),
            sa.Column('deleted_at', sa.DateTime(), nullable=True),
            sa.Column('deleted_by_id', sa.Integer(), nullable=True),
            sa.Column('sort_order', sa.Integer(), nullable=True),
            sa.Column('bg_color', sa.String(), nullable=True),
            sa.Column('text_color', sa.String(), nullable=True),
            sa.Column('subtitle_color', sa.String(), nullable=True),
            sa.Column('btn_bg_color', sa.String(), nullable=True),
            sa.Column('btn_text_color', sa.String(), nullable=True),
            sa.Column('badge_text', sa.String(), nullable=True),
            sa.Column('badge_color', sa.String(), nullable=True),
            sa.Column('effect', sa.String(), nullable=True),
            sa.Column('video_url', sa.String(), nullable=True),
            sa.Column('cta_label', sa.String(), nullable=True),
            sa.Column('cta_url', sa.String(), nullable=True),
            sa.Column('starts_at', sa.DateTime(), nullable=True),
            sa.Column('ends_at', sa.DateTime(), nullable=True),
            sa.Column('created_by', sa.Integer(), nullable=True),
            sa.Column('layout_json', sa.Text(), nullable=True),
            sa.Column('country_code', sa.String(length=3), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='commerce',
    )

    if not _has_table('budgets', 'finance'):
        op.create_table('budgets',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('account_code', sa.String(length=20), nullable=False),
            sa.Column('fiscal_period_id', sa.Integer(), nullable=False),
            sa.Column('amount', sa.Numeric(precision=16, scale=4), nullable=False),
            sa.Column('currency', sa.String(length=3), nullable=True),
            sa.Column('created_by', sa.Integer(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='finance',
    )

    if not _has_table('campaign_recipients', 'communication'):
        op.create_table('campaign_recipients',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('campaign_id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('email', sa.String(), nullable=False),
            sa.Column('status', sa.String(), nullable=True),
            sa.Column('sent_at', sa.DateTime(), nullable=True),
            sa.Column('delivered_at', sa.DateTime(), nullable=True),
            sa.Column('opened_at', sa.DateTime(), nullable=True),
            sa.Column('clicked_at', sa.DateTime(), nullable=True),
            sa.Column('bounced_at', sa.DateTime(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True), schema='communication',
    )

    if not _has_table('cart_items', 'commerce'):
        op.create_table('cart_items',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('product_id', sa.Integer(), nullable=False),
            sa.Column('quantity', sa.Integer(), nullable=True),
            sa.Column('selected_size', sa.String(length=50), nullable=False),
            sa.Column('selected_color', sa.String(length=50), nullable=False),
            sa.Column('variant_id', sa.Integer(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='commerce',
    )

    if not _has_table('carts', 'commerce'):
        op.create_table('carts',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='commerce',
    )

    if not _has_table('cash_accounts', 'treasury'):
        op.create_table('cash_accounts',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('name', sa.String(), nullable=False),
            sa.Column('account_type', sa.String(), nullable=False),
            sa.Column('currency', sa.String(length=3), nullable=True),
            sa.Column('balance', sa.Numeric(precision=12, scale=2), nullable=True),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='treasury',
    )

    if not _has_table('cash_flow_forecasts', 'treasury'):
        op.create_table('cash_flow_forecasts',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('forecast_date', sa.DateTime(), nullable=False),
            sa.Column('period_start_at', sa.DateTime(), nullable=False),
            sa.Column('period_end_at', sa.DateTime(), nullable=False),
            sa.Column('net_cash_flow', sa.Numeric(precision=12, scale=2), nullable=True),
            sa.Column('opening_balance', sa.Numeric(precision=12, scale=2), nullable=True),
            sa.Column('closing_balance', sa.Numeric(precision=12, scale=2), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='treasury',
    )

    if not _has_table('cash_position_snapshots', 'treasury'):
        op.create_table('cash_position_snapshots',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('snapshot_time', sa.DateTime(), nullable=False),
            sa.Column('account_id', sa.Integer(), nullable=False),
            sa.Column('balance', sa.Numeric(precision=12, scale=2), nullable=True),
            sa.Column('currency', sa.String(length=3), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='treasury',
    )

    if not _has_table('cash_transactions', 'treasury'):
        op.create_table('cash_transactions',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('account_id', sa.Integer(), nullable=False),
            sa.Column('transaction_type', sa.String(), nullable=False),
            sa.Column('amount', sa.Numeric(precision=12, scale=2), nullable=False),
            sa.Column('balance_after', sa.Numeric(precision=12, scale=2), nullable=True),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('reference', sa.String(), nullable=True),
            sa.Column('category', sa.String(), nullable=True),
            sa.Column('performed_by', sa.Integer(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='treasury',
    )

    if not _has_table('categories', 'commerce'):
        op.create_table('categories',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('name', sa.String(), nullable=False),
            sa.Column('slug', sa.String(), nullable=True, unique=True),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('parent_id', sa.Integer(), nullable=True),
            sa.Column('icon', sa.String(), nullable=True),
            sa.Column('image_url', sa.String(), nullable=True),
            sa.Column('sort_order', sa.Integer(), nullable=True),
            sa.Column('commission_rate', sa.Numeric(precision=5, scale=4), nullable=True),
            sa.Column('meta_title', sa.String(), nullable=True),
            sa.Column('meta_description', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.Column('path', sa.String(length=255), nullable=True),
            sa.Column('lft', sa.Integer(), nullable=False),
            sa.Column('rgt', sa.Integer(), nullable=False),
            sa.Column('depth', sa.Integer(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='commerce',
    )

    if not _has_table('chat_attachments', 'communication'):
        op.create_table('chat_attachments',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('message_id', sa.Integer(), nullable=False),
            sa.Column('message_type', sa.String(length=20), nullable=False),
            sa.Column('attachment_type', sa.String(length=20), nullable=False),
            sa.Column('file_url', sa.String(length=500), nullable=False),
            sa.Column('file_name', sa.String(length=200), nullable=False),
            sa.Column('file_size_bytes', sa.Integer(), nullable=False),
            sa.Column('mime_type', sa.String(length=100), nullable=False),
            sa.Column('thumbnail_url', sa.String(length=500), nullable=True),
            sa.Column('duration_seconds', sa.Integer(), nullable=True),
            sa.Column('waveform_json', sa.Text(), nullable=True),
            sa.Column('is_processed', sa.Boolean(), nullable=True), schema='communication',
    )

    if not _has_table('chat_read_receipts', 'communication'):
        op.create_table('chat_read_receipts',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('message_id', sa.Integer(), nullable=False),
            sa.Column('message_type', sa.String(length=20), nullable=False),
            sa.Column('employee_id', sa.Integer(), nullable=False),
            sa.Column('read_at', sa.DateTime(), nullable=True), schema='communication',
    )

    if not _has_table('chatbot_query_events', 'audit'):
        op.create_table('chatbot_query_events',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=True),
            sa.Column('session_id', sa.String(length=64), nullable=False),
            sa.Column('event_type', sa.String(length=30), nullable=False, server_default=sa.text('query')),
            sa.Column('message', sa.Text(), nullable=True),
            sa.Column('normalized_query', sa.String(length=500), nullable=True),
            sa.Column('intent', sa.String(length=100), nullable=True),
            sa.Column('filters_json', sa.Text(), nullable=True),
            sa.Column('result_count', sa.Integer(), nullable=False, server_default=sa.text('0')),
            sa.Column('product_ids_json', sa.Text(), nullable=True),
            sa.Column('clicked_product_id', sa.Integer(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='audit',
    )

    if not _has_table('city_distance_matrix', 'logistics'):
        op.create_table('city_distance_matrix',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('origin_country_code', sa.String(length=3), nullable=False),
            sa.Column('origin_city_name', sa.String(), nullable=False),
            sa.Column('destination_country_code', sa.String(length=3), nullable=False),
            sa.Column('destination_city_name', sa.String(), nullable=False),
            sa.Column('distance_km', sa.Numeric(precision=10, scale=2), nullable=True),
            sa.Column('notes', sa.Text(), nullable=True),
            sa.Column('created_by', sa.Integer(), nullable=True),
            sa.Column('updated_by', sa.Integer(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True), schema='logistics',
    )

    if not _has_table('coi_reports', 'hr'):
        op.create_table('coi_reports',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('employee_id', sa.Integer(), nullable=False),
            sa.Column('related_person_name', sa.String(length=160), nullable=False),
            sa.Column('relation_type', sa.String(length=30), nullable=False),
            sa.Column('is_internal', sa.Boolean(), nullable=True),
            sa.Column('internal_employee_id', sa.Integer(), nullable=True),
            sa.Column('risk_level', sa.String(length=20), nullable=True),
            sa.Column('is_approved', sa.Boolean(), nullable=True),
            sa.Column('approved_by', sa.Integer(), nullable=True),
            sa.Column('approved_at', sa.DateTime(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='hr',
    )

    if not _has_table('command_center_views', 'audit'):
        op.create_table('command_center_views',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('view_name', sa.String(length=100), nullable=False),
            sa.Column('config', sa.JSON(), nullable=True),
            sa.Column('is_default', sa.Boolean(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True), schema='audit',
    )

    if not _has_table('commission_agreements', 'commerce'):
        op.create_table('commission_agreements',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('supplier_id', sa.Integer(), nullable=False),
            sa.Column('rate', sa.Numeric(precision=5, scale=4), nullable=False),
            sa.Column('set_by_admin_id', sa.Integer(), nullable=True),
            sa.Column('effective_to', sa.DateTime(), nullable=True),
            sa.Column('note', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='commerce',
    )

    if not _has_table('commission_badge_tiers', 'commerce'):
        op.create_table('commission_badge_tiers',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('name', sa.String(length=100), nullable=False),
            sa.Column('badge_level', sa.String(length=50), nullable=False, unique=True),
            sa.Column('commission_rate', sa.Numeric(precision=5, scale=4), nullable=False),
            sa.Column('setup_fee', sa.Numeric(precision=12, scale=2), nullable=True),
            sa.Column('recurring_fee', sa.Numeric(precision=12, scale=2), nullable=True),
            sa.Column('recurring_interval', sa.String(length=20), nullable=True),
            sa.Column('benefits_json', sa.Text(), nullable=True),
            sa.Column('min_fulfilled_orders', sa.Integer(), nullable=True),
            sa.Column('min_monthly_revenue', sa.Numeric(precision=15, scale=2), nullable=True),
            sa.Column('sort_order', sa.Integer(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='commerce',
    )

    if not _has_table('commission_category_rates', 'commerce'):
        op.create_table('commission_category_rates',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('category_id', sa.Integer(), nullable=True),
            sa.Column('category_slug', sa.String(length=100), nullable=True),
            sa.Column('category_display_name', sa.String(length=100), nullable=True),
            sa.Column('country_code', sa.String(length=3), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='commerce',
    )

    if not _has_table('commission_global_configs', 'commerce'):
        op.create_table('commission_global_configs',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('default_rate', sa.Numeric(precision=5, scale=4), nullable=True),
            sa.Column('low_value_threshold', sa.Numeric(precision=10, scale=2), nullable=True),
            sa.Column('fixed_cap_amount', sa.Numeric(precision=10, scale=2), nullable=True),
            sa.Column('is_fixed_cap_enabled', sa.Boolean(), nullable=True),
            sa.Column('is_margin_protection_enabled', sa.Boolean(), nullable=True),
            sa.Column('margin_threshold', sa.Numeric(precision=5, scale=4), nullable=True),
            sa.Column('updated_by', sa.Integer(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='commerce',
    )

    if not _has_table('commission_ledger_entries', 'commerce'):
        op.create_table('commission_ledger_entries',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('supplier_id', sa.Integer(), nullable=False),
            sa.Column('order_id', sa.Integer(), nullable=True),
            sa.Column('order_item_id', sa.Integer(), nullable=True),
            sa.Column('product_id', sa.Integer(), nullable=True),
            sa.Column('category_slug', sa.String(length=100), nullable=True),
            sa.Column('badge_level', sa.String(length=20), nullable=True),
            sa.Column('global_default_rate', sa.Numeric(precision=5, scale=4), nullable=True),
            sa.Column('category_rate', sa.Numeric(precision=5, scale=4), nullable=True),
            sa.Column('badge_rate', sa.Numeric(precision=5, scale=4), nullable=True),
            sa.Column('override_rate', sa.Numeric(precision=5, scale=4), nullable=True),
            sa.Column('applied_rate', sa.Numeric(precision=5, scale=4), nullable=True),
            sa.Column('calculation_method', sa.String(length=20), nullable=True),
            sa.Column('order_value', sa.Numeric(precision=12, scale=2), nullable=True),
            sa.Column('commission_pct', sa.Numeric(precision=12, scale=2), nullable=True),
            sa.Column('cap_applied', sa.Boolean(), nullable=True),
            sa.Column('commission_amount', sa.Numeric(precision=12, scale=2), nullable=True),
            sa.Column('low_value_threshold_used', sa.Boolean(), nullable=True),
            sa.Column('fixed_cap_used', sa.Boolean(), nullable=True),
            sa.Column('override_flag', sa.Boolean(), nullable=True),
            sa.Column('is_adjusted', sa.Boolean(), nullable=True),
            sa.Column('currency', sa.String(length=3), nullable=True),
            sa.Column('amount', sa.Numeric(precision=12, scale=2), nullable=True),
            sa.Column('adjusted_by', sa.Integer(), nullable=True),
            sa.Column('status', sa.String(), nullable=True),
            sa.Column('credited_at', sa.DateTime(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='commerce',
    )

    if not _has_table('commission_rules', 'commerce'):
        op.create_table('commission_rules',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('rule_name', sa.String(length=255), nullable=False),
            sa.Column('rule_type', sa.String(length=50), nullable=False),
            sa.Column('tier', sa.String(length=20), nullable=True),
            sa.Column('rate_percent', sa.Numeric(precision=5, scale=2), nullable=False),
            sa.Column('created_by', sa.Integer(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='commerce',
    )

    if not _has_table('communication_audit_trail', 'communication'):
        op.create_table('communication_audit_trail',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('entity_type', sa.String(length=50), nullable=False),
            sa.Column('entity_id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=True),
            sa.Column('action', sa.String(length=50), nullable=False),
            sa.Column('channel', sa.String(length=50), nullable=False),
            sa.Column('content_preview', sa.Text(), nullable=True),
            sa.Column('metadata_json', sa.JSON(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True), schema='communication',
    )

    if not _has_table('cost_centers', 'finance'):
        op.create_table('cost_centers',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('code', sa.String(length=30), nullable=False),
            sa.Column('name', sa.String(length=160), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='finance',
    )

    if not _has_table('country_basics', 'country'):
        op.create_table('country_basics',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('code', sa.String(length=3), nullable=False, unique=True),
            sa.Column('name', sa.String(), nullable=False),
            sa.Column('currency', sa.String(length=3), nullable=True),
            sa.Column('currency_symbol', sa.String(length=10), nullable=True),
            sa.Column('phone_code', sa.String(length=10), nullable=True),
            sa.Column('language', sa.String(length=10), nullable=True),
            sa.Column('timezone', sa.String(length=60), nullable=True),
            sa.Column('date_format', sa.String(length=20), nullable=True),
            sa.Column('status', sa.String(length=20), nullable=True),
            sa.Column('is_active', sa.Boolean(), nullable=True),
            sa.Column('is_deleted', sa.Boolean(), nullable=True),
            sa.Column('is_default', sa.Boolean(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.Column('created_by', sa.Integer(), nullable=True),
            sa.Column('updated_by', sa.Integer(), nullable=True),
            sa.Column('official_name', sa.String(length=200), nullable=True),
            sa.Column('alpha3', sa.String(length=3), nullable=True),
            sa.Column('flag_url', sa.String(length=500), nullable=True),
            sa.Column('currency_name', sa.String(length=50), nullable=True),
            sa.Column('exchange_rate_to_usd', sa.Numeric(precision=12, scale=6), nullable=True),
            sa.Column('capital', sa.String(length=100), nullable=True),
            sa.Column('region', sa.String(length=60), nullable=True),
            sa.Column('subregion', sa.String(length=60), nullable=True),
            sa.Column('population', sa.Integer(), nullable=True),
            sa.Column('internet_penetration_pct', sa.Numeric(precision=5, scale=2), nullable=True),
            sa.Column('gdp_per_capita_usd', sa.Numeric(precision=12, scale=2), nullable=True),
            sa.Column('urbanization_pct', sa.Numeric(precision=5, scale=2), nullable=True),
            sa.Column('mobile_subs_per_100', sa.Numeric(precision=5, scale=2), nullable=True),
            sa.Column('public_holidays_json', sa.Text(), nullable=True),
            sa.Column('macro_indicators_json', sa.Text(), nullable=True), schema='country',
    )

    if not _has_table('country_category_tax_rates', 'configuration'):
        op.create_table('country_category_tax_rates',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('category_id', sa.Integer(), nullable=False),
            sa.Column('tax_rate', sa.Numeric(precision=5, scale=4), nullable=True),
            sa.Column('tax_name', sa.String(length=50), nullable=True),
            sa.Column('category_slug', sa.String(length=100), nullable=True),
            sa.Column('rate', sa.Numeric(precision=5, scale=4), nullable=True),
            sa.Column('is_exempt', sa.Boolean(), nullable=True),
            sa.Column('is_reduced', sa.Boolean(), nullable=True),
            sa.Column('notes', sa.Text(), nullable=True),
            sa.Column('source', sa.String(length=50), nullable=True),
            sa.Column('is_active', sa.Boolean(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True), schema='configuration',
    )

    if not _has_table('country_cities', 'country'):
        op.create_table('country_cities',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('name', sa.String(length=200), nullable=False),
            sa.Column('name_local', sa.String(length=200), nullable=True),
            sa.Column('population', sa.Integer(), nullable=True),
            sa.Column('is_capital', sa.Boolean(), nullable=True),
            sa.Column('latitude', sa.Numeric(precision=10, scale=7), nullable=True),
            sa.Column('longitude', sa.Numeric(precision=10, scale=7), nullable=True),
            sa.Column('postal_code_prefix', sa.String(length=20), nullable=True),
            sa.Column('status', sa.String(length=20), nullable=True),
            sa.Column('is_active', sa.Boolean(), nullable=True),
            sa.Column('region', sa.String(length=100), nullable=True),
            sa.Column('sort_order', sa.Integer(), nullable=True),
            sa.Column('source', sa.String(length=50), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True), schema='country',
    )

    if not _has_table('country_commission_rate_history', 'configuration'):
        op.create_table('country_commission_rate_history',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('category_id', sa.Integer(), nullable=True),
            sa.Column('supplier_tier', sa.String(length=20), nullable=False),
            sa.Column('rate_percent', sa.Numeric(precision=5, scale=4), nullable=False),
            sa.Column('effective_from', sa.DateTime(), nullable=False),
            sa.Column('effective_to', sa.DateTime(), nullable=True),
            sa.Column('changed_by', sa.Integer(), nullable=True),
            sa.Column('change_reason', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True), schema='configuration',
    )

    if not _has_table('country_commission_rates', 'configuration'):
        op.create_table('country_commission_rates',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('supplier_tier', sa.String(length=20), nullable=False),
            sa.Column('name', sa.String(length=50), nullable=False),
            sa.Column('rate_percent', sa.Numeric(precision=5, scale=2), nullable=False),
            sa.Column('fixed_fee', sa.Numeric(precision=10, scale=2), nullable=True),
            sa.Column('effective_from', sa.DateTime(), nullable=True),
            sa.Column('effective_to', sa.DateTime(), nullable=True), schema='configuration',
    )

    if not _has_table('country_communication_threads', 'configuration'):
        op.create_table('country_communication_threads',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('entity_type', sa.String(length=50), nullable=False),
            sa.Column('entity_id', sa.Integer(), nullable=False),
            sa.Column('participants', sa.Text(), nullable=True),
            sa.Column('is_active', sa.Boolean(), nullable=True),
            sa.Column('last_message_at', sa.DateTime(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True), schema='configuration',
    )

    if not _has_table('country_communications', 'country'):
        op.create_table('country_communications',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('from_user_id', sa.Integer(), nullable=True),
            sa.Column('to_user_id', sa.Integer(), nullable=True),
            sa.Column('subject', sa.String(length=200), nullable=False),
            sa.Column('body', sa.Text(), nullable=False),
            sa.Column('priority', sa.String(length=20), nullable=True),
            sa.Column('category', sa.String(length=50), nullable=True),
            sa.Column('status', sa.String(length=20), nullable=True),
            sa.Column('related_entity_type', sa.String(length=50), nullable=True),
            sa.Column('related_entity_id', sa.Integer(), nullable=True),
            sa.Column('read_at', sa.DateTime(), nullable=True),
            sa.Column('attachments_json', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True), schema='country',
    )

    if not _has_table('country_config_versions', 'configuration'):
        op.create_table('country_config_versions',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('config_type', sa.String(length=50), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False),
            sa.Column('payload_json', sa.Text(), nullable=False),
            sa.Column('status', sa.String(length=20), nullable=True),
            sa.Column('draft_by', sa.Integer(), nullable=True),
            sa.Column('approved_by', sa.Integer(), nullable=True),
            sa.Column('published_at', sa.DateTime(), nullable=True),
            sa.Column('effective_from', sa.DateTime(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True), schema='configuration',
    )

    if not _has_table('country_configs', 'country'):
        op.create_table('country_configs',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('basics_id', sa.Integer(), nullable=True),
            sa.Column('code', sa.String(length=3), nullable=False, unique=True),
            sa.Column('name', sa.String(), nullable=False),
            sa.Column('currency', sa.String(length=3), nullable=True),
            sa.Column('currency_symbol', sa.String(length=10), nullable=True),
            sa.Column('phone_code', sa.String(length=10), nullable=True),
            sa.Column('language', sa.String(length=10), nullable=True),
            sa.Column('timezone', sa.String(length=60), nullable=True),
            sa.Column('date_format', sa.String(length=20), nullable=True),
            sa.Column('status', sa.String(length=20), nullable=True),
            sa.Column('is_active', sa.Boolean(), nullable=True),
            sa.Column('is_deleted', sa.Boolean(), nullable=True),
            sa.Column('is_default', sa.Boolean(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.Column('official_name', sa.String(length=200), nullable=True),
            sa.Column('alpha3', sa.String(length=3), nullable=True),
            sa.Column('flag_url', sa.String(length=500), nullable=True),
            sa.Column('currency_name', sa.String(length=50), nullable=True),
            sa.Column('exchange_rate_to_usd', sa.Numeric(precision=12, scale=6), nullable=True),
            sa.Column('capital', sa.String(length=100), nullable=True),
            sa.Column('region', sa.String(length=60), nullable=True),
            sa.Column('subregion', sa.String(length=60), nullable=True),
            sa.Column('population', sa.Integer(), nullable=True),
            sa.Column('internet_penetration_pct', sa.Numeric(precision=5, scale=2), nullable=True),
            sa.Column('gdp_per_capita_usd', sa.Numeric(precision=12, scale=2), nullable=True),
            sa.Column('urbanization_pct', sa.Numeric(precision=5, scale=2), nullable=True),
            sa.Column('mobile_subs_per_100', sa.Numeric(precision=5, scale=2), nullable=True),
            sa.Column('public_holidays_json', sa.Text(), nullable=True),
            sa.Column('macro_indicators_json', sa.Text(), nullable=True),
            sa.Column('tax_type', sa.String(length=20), nullable=True),
            sa.Column('tax_rate', sa.Numeric(precision=5, scale=4), nullable=True),
            sa.Column('tax_name', sa.String(length=50), nullable=True),
            sa.Column('tax_inclusive', sa.Boolean(), nullable=True),
            sa.Column('tax_exempt_categories_json', sa.Text(), nullable=True),
            sa.Column('tax_reduced_rates_json', sa.Text(), nullable=True),
            sa.Column('logistics_model', sa.String(length=30), nullable=True),
            sa.Column('default_vehicle_type', sa.String(length=30), nullable=True),
            sa.Column('base_rate', sa.Numeric(precision=10, scale=2), nullable=True),
            sa.Column('per_km_rate', sa.Numeric(precision=10, scale=2), nullable=True),
            sa.Column('minimum_charge', sa.Numeric(precision=10, scale=2), nullable=True),
            sa.Column('weight_surcharge_rate', sa.Numeric(precision=5, scale=4), nullable=True),
            sa.Column('weight_surcharge_threshold_kg', sa.Numeric(precision=10, scale=2), nullable=True),
            sa.Column('payment_methods_json', sa.Text(), nullable=True),
            sa.Column('payment_gateways_json', sa.Text(), nullable=True),
            sa.Column('logistics_providers_json', sa.Text(), nullable=True),
            sa.Column('legal_rules_json', sa.Text(), nullable=True),
            sa.Column('product_restrictions_json', sa.Text(), nullable=True),
            sa.Column('address_format_json', sa.Text(), nullable=True),
            sa.Column('regions_json', sa.Text(), nullable=True),
            sa.Column('supplier_requirements_json', sa.Text(), nullable=True),
            sa.Column('payout_settings_json', sa.Text(), nullable=True),
            sa.Column('commission_tiers_json', sa.Text(), nullable=True),
            sa.Column('suggested_gateway_rankings_json', sa.Text(), nullable=True),
            sa.Column('suggested_commission_ranges_json', sa.Text(), nullable=True),
            sa.Column('consumer_behavior_profile_json', sa.Text(), nullable=True),
            sa.Column('economic_tier', sa.String(length=20), nullable=True),
            sa.Column('fraud_risk_tier', sa.String(length=10), nullable=True),
            sa.Column('suggested_logistics_model', sa.String(length=30), nullable=True),
            sa.Column('data_residency_tier', sa.String(length=20), nullable=True),
            sa.Column('data_residency_encrypted', sa.Text(), nullable=True),
            sa.Column('confidence_score', sa.Numeric(precision=5, scale=4), nullable=True),
            sa.Column('audit_trail_json', sa.Text(), nullable=True),
            sa.Column('cod_enabled', sa.Boolean(), nullable=True),
            sa.Column('cod_max_amount', sa.Numeric(precision=12, scale=2), nullable=True),
            sa.Column('cod_verification_required', sa.Boolean(), nullable=True),
            sa.Column('cod_remittance_days', sa.Integer(), nullable=True),
            sa.Column('settlement_hold_days', sa.Integer(), nullable=True),
            sa.Column('minimum_payout_amount', sa.Numeric(precision=12, scale=2), nullable=True),
            sa.Column('payout_currency', sa.String(length=10), nullable=True),
            sa.Column('supplier_kyc_tier', sa.String(length=20), nullable=True),
            sa.Column('supplier_onboarding_fee', sa.Numeric(precision=12, scale=2), nullable=True),
            sa.Column('supplier_monthly_fee', sa.Numeric(precision=12, scale=2), nullable=True),
            sa.Column('supplier_rating_threshold', sa.Numeric(precision=5, scale=2), nullable=True),
            sa.Column('legal_entity_required', sa.Boolean(), nullable=True),
            sa.Column('consumer_protection_days', sa.Integer(), nullable=True),
            sa.Column('data_privacy_framework', sa.String(length=20), nullable=True),
            sa.Column('max_package_weight_kg', sa.Numeric(precision=8, scale=2), nullable=True),
            sa.Column('max_package_dimensions_cm', sa.String(length=200), nullable=True),
            sa.Column('signature_required_threshold', sa.Numeric(precision=10, scale=2), nullable=True),
            sa.Column('measurement_system', sa.String(length=10), nullable=True),
            sa.Column('working_days_json', sa.Text(), nullable=True),
            sa.Column('supported_languages_json', sa.Text(), nullable=True),
            sa.Column('payout_methods_json', sa.Text(), nullable=True),
            sa.Column('logistics_zones_json', sa.Text(), nullable=True),
            sa.Column('country_code', sa.String(length=3), nullable=True, unique=True), schema='country',
    )

    if not _has_table('country_economics', 'country'):
        op.create_table('country_economics',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('uuid', sa.String(length=36), nullable=True, unique=True),
            sa.Column('version', sa.Integer(), nullable=False, server_default=sa.text('1')),
            sa.Column('country_code', sa.String(length=3), nullable=False, unique=True),
            sa.Column('is_active', sa.Boolean(), nullable=True),
            sa.Column('is_deleted', sa.Boolean(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.Column('created_by', sa.Integer(), nullable=True),
            sa.Column('updated_by', sa.Integer(), nullable=True),
            sa.Column('economic_tier', sa.String(length=20), nullable=True),
            sa.Column('fraud_risk_tier', sa.String(length=10), nullable=True),
            sa.Column('suggested_logistics_model', sa.String(length=30), nullable=True),
            sa.Column('data_residency_tier', sa.String(length=20), nullable=True),
            sa.Column('data_residency_encrypted', sa.Text(), nullable=True),
            sa.Column('confidence_score', sa.Numeric(precision=5, scale=4), nullable=True),
            sa.Column('audit_trail_json', sa.Text(), nullable=True),
            sa.Column('cod_enabled', sa.String(length=1), nullable=True),
            sa.Column('cod_max_amount', sa.Numeric(precision=12, scale=2), nullable=True),
            sa.Column('cod_verification_required', sa.String(length=1), nullable=True),
            sa.Column('cod_remittance_days', sa.Integer(), nullable=True),
            sa.Column('settlement_hold_days', sa.Integer(), nullable=True),
            sa.Column('minimum_payout_amount', sa.Numeric(precision=12, scale=2), nullable=True),
            sa.Column('payout_currency', sa.String(length=3), nullable=True),
            sa.Column('supplier_kyc_tier', sa.String(length=20), nullable=True),
            sa.Column('supplier_onboarding_fee', sa.Numeric(precision=12, scale=2), nullable=True),
            sa.Column('supplier_monthly_fee', sa.Numeric(precision=12, scale=2), nullable=True),
            sa.Column('supplier_rating_threshold', sa.Numeric(precision=5, scale=2), nullable=True),
            sa.Column('legal_entity_required', sa.String(length=1), nullable=True),
            sa.Column('consumer_protection_days', sa.Integer(), nullable=True),
            sa.Column('data_privacy_framework', sa.String(length=20), nullable=True),
            sa.Column('max_package_weight_kg', sa.Numeric(precision=8, scale=2), nullable=True),
            sa.Column('max_package_dimensions_cm', sa.String(length=200), nullable=True),
            sa.Column('signature_required_threshold', sa.Numeric(precision=10, scale=2), nullable=True),
            sa.Column('measurement_system', sa.String(length=10), nullable=True),
            sa.Column('working_days_json', sa.Text(), nullable=True),
            sa.Column('supported_languages_json', sa.Text(), nullable=True),
            sa.Column('payout_methods_json', sa.Text(), nullable=True),
            sa.Column('logistics_zones_json', sa.Text(), nullable=True), schema='country',
    )

    if not _has_table('country_feature_flags', 'configuration'):
        op.create_table('country_feature_flags',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('feature_key', sa.String(length=100), nullable=False),
            sa.Column('feature_name', sa.String(length=200), nullable=True),
            sa.Column('is_enabled', sa.Boolean(), nullable=True),
            sa.Column('config', sa.Text(), nullable=True),
            sa.Column('rollout_audience', sa.String(length=100), nullable=True),
            sa.Column('notes', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True), schema='configuration',
    )

    if not _has_table('country_gateway_configs', 'configuration'):
        op.create_table('country_gateway_configs',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('gateway_id', sa.String(length=50), nullable=False),
            sa.Column('gateway_name', sa.String(length=100), nullable=False),
            sa.Column('is_enabled', sa.Boolean(), nullable=True),
            sa.Column('priority', sa.Integer(), nullable=True),
            sa.Column('credentials', sa.Text(), nullable=True),
            sa.Column('environment', sa.String(length=20), nullable=True),
            sa.Column('settings', sa.Text(), nullable=True),
            sa.Column('last_tested_at', sa.DateTime(), nullable=True),
            sa.Column('last_test_result', sa.String(length=20), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True), schema='configuration',
    )

    if not _has_table('country_gateway_credentials', 'country'):
        op.create_table('country_gateway_credentials',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('gateway_name', sa.String(length=100), nullable=False),
            sa.Column('environment', sa.String(length=20), nullable=True),
            sa.Column('credentials', sa.JSON(), nullable=True),
            sa.Column('is_active', sa.Boolean(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True), schema='country',
    )

    if not _has_table('country_holiday_calendars', 'configuration'):
        op.create_table('country_holiday_calendars',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('holiday_date', sa.DateTime(), nullable=False),
            sa.Column('name', sa.String(length=200), nullable=False),
            sa.Column('local_name', sa.String(length=200), nullable=True),
            sa.Column('is_observed', sa.Boolean(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True), schema='configuration',
    )

    if not _has_table('country_legal', 'country'):
        op.create_table('country_legal',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('uuid', sa.String(length=36), nullable=True, unique=True),
            sa.Column('version', sa.Integer(), nullable=False, server_default=sa.text('1')),
            sa.Column('country_code', sa.String(length=3), nullable=False, unique=True),
            sa.Column('is_active', sa.Boolean(), nullable=True),
            sa.Column('is_deleted', sa.Boolean(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.Column('created_by', sa.Integer(), nullable=True),
            sa.Column('updated_by', sa.Integer(), nullable=True),
            sa.Column('legal_entity_required', sa.String(length=1), nullable=True),
            sa.Column('consumer_protection_days', sa.Integer(), nullable=True),
            sa.Column('data_privacy_framework', sa.String(length=20), nullable=True),
            sa.Column('gdpr_compliant', sa.Boolean(), nullable=True),
            sa.Column('local_data_residency', sa.Boolean(), nullable=True),
            sa.Column('compliance_score', sa.Numeric(precision=5, scale=4), nullable=True),
            sa.Column('legal_risk_tier', sa.String(length=10), nullable=True),
            sa.Column('contract_templates_json', sa.Text(), nullable=True),
            sa.Column('regulatory_bodies_json', sa.Text(), nullable=True), schema='country',
    )

    if not _has_table('country_legal_contracts', 'configuration'):
        op.create_table('country_legal_contracts',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('contract_type', sa.String(length=50), nullable=False),
            sa.Column('version', sa.String(length=20), nullable=True),
            sa.Column('content_html', sa.Text(), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True), schema='configuration',
    )

    if not _has_table('country_localization', 'configuration'):
        op.create_table('country_localization',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False, unique=True),
            sa.Column('default_numeral_system', sa.String(length=20), nullable=True),
            sa.Column('hijri_calendar_enabled', sa.Boolean(), nullable=True),
            sa.Column('rtl_layout_enabled', sa.Boolean(), nullable=True),
            sa.Column('address_format', sa.String(length=200), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True), schema='configuration',
    )

    if not _has_table('country_logistics_zones', 'configuration'):
        op.create_table('country_logistics_zones',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('zone_code', sa.String(length=50), nullable=False),
            sa.Column('zone_name', sa.String(length=200), nullable=False),
            sa.Column('zone_type', sa.String(length=20), nullable=True),
            sa.Column('cities', sa.Text(), nullable=True),
            sa.Column('pricing_config', sa.Text(), nullable=True),
            sa.Column('is_active', sa.Boolean(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True), schema='configuration',
    )

    if not _has_table('country_map_configs', 'hr'):
        op.create_table('country_map_configs',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('api_key_ref', sa.String(length=100), nullable=True),
            sa.Column('country_code', sa.String(length=3), nullable=True),
            sa.Column('default_zoom', sa.Integer(), nullable=True),
            sa.Column('is_show_regions', sa.Boolean(), nullable=True),
            sa.Column('is_show_cities', sa.Boolean(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='hr',
    )

    if not _has_table('country_payment_aliases', 'configuration'):
        op.create_table('country_payment_aliases',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('alias_type', sa.String(length=50), nullable=False),
            sa.Column('alias_value', sa.String(length=200), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True), schema='configuration',
    )

    if not _has_table('country_payout_rules', 'configuration'):
        op.create_table('country_payout_rules',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('supplier_tier', sa.String(length=20), nullable=True),
            sa.Column('min_amount', sa.Numeric(precision=15, scale=3), nullable=True),
            sa.Column('max_amount', sa.Numeric(precision=15, scale=3), nullable=True),
            sa.Column('fixed_fee', sa.Numeric(precision=15, scale=3), nullable=True),
            sa.Column('percent_fee', sa.Numeric(precision=5, scale=4), nullable=True),
            sa.Column('settlement_days', sa.Integer(), nullable=True),
            sa.Column('is_active', sa.Boolean(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True), schema='configuration',
    )

    if not _has_table('country_staff_assignments', 'configuration'):
        op.create_table('country_staff_assignments',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('role_in_country', sa.String(length=40), nullable=False, server_default=sa.text('country_manager')),
            sa.Column('is_active', sa.Boolean(), nullable=True),
            sa.Column('assigned_by', sa.Integer(), nullable=True),
            sa.Column('notes', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True), schema='configuration',
    )

    if not _has_table('country_tax', 'country'):
        op.create_table('country_tax',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('uuid', sa.String(length=36), nullable=False, unique=True),
            sa.Column('country_code', sa.String(length=3), nullable=False, unique=True),
            sa.Column('is_active', sa.Boolean(), nullable=True),
            sa.Column('is_deleted', sa.Boolean(), nullable=True),
            sa.Column('version', sa.Integer(), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.Column('created_by', sa.Integer(), nullable=True),
            sa.Column('updated_by', sa.Integer(), nullable=True),
            sa.Column('tax_type', sa.String(length=20), nullable=True),
            sa.Column('tax_rate', sa.Numeric(precision=5, scale=4), nullable=True),
            sa.Column('tax_name', sa.String(length=50), nullable=True),
            sa.Column('tax_inclusive', sa.Boolean(), nullable=True),
            sa.Column('tax_exempt_categories_json', sa.Text(), nullable=True),
            sa.Column('tax_reduced_rates_json', sa.Text(), nullable=True), schema='country',
    )

    op.execute('DROP TABLE IF EXISTS "commerce"."coupon_usages"')
    if not _has_table('coupon_usage', 'commerce'):
        op.create_table('coupon_usage',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('coupon_id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('order_id', sa.Integer(), nullable=True),
            sa.Column('country_code', sa.String(length=10), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True), schema='commerce',
        )

    if not _has_table('coupons', 'commerce'):
        op.create_table('coupons',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('code', sa.String(), nullable=False, unique=True),
            sa.Column('title', sa.String(), nullable=True),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('discount_type', sa.String(), nullable=True),
            sa.Column('discount_value', sa.Numeric(precision=5, scale=2), nullable=True),
            sa.Column('minimum_order', sa.Numeric(precision=10, scale=2), nullable=True),
            sa.Column('maximum_discount', sa.Numeric(precision=10, scale=2), nullable=True),
            sa.Column('min_order_amount', sa.Numeric(precision=10, scale=2), nullable=True),
            sa.Column('valid_from', sa.DateTime(), nullable=True),
            sa.Column('valid_until', sa.DateTime(), nullable=True),
            sa.Column('usage_limit', sa.Integer(), nullable=True),
            sa.Column('usage_count', sa.Integer(), nullable=True),
            sa.Column('starts_at', sa.DateTime(), nullable=True),
            sa.Column('expires_at', sa.DateTime(), nullable=True),
            sa.Column('allow_product_coupons', sa.Boolean(), nullable=True),
            sa.Column('allow_category_coupons', sa.Boolean(), nullable=True),
            sa.Column('allow_global_coupons', sa.Boolean(), nullable=True),
            sa.Column('deleted_at', sa.DateTime(), nullable=True),
            sa.Column('deleted_by_id', sa.Integer(), nullable=True),
            sa.Column('country_code', sa.String(length=3), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='commerce',
    )

    if not _has_table('credit_card_bins', 'security'):
        op.create_table('credit_card_bins',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('bin', sa.String(length=10), nullable=False, unique=True),
            sa.Column('brand', sa.String(length=50), nullable=True),
            sa.Column('bank', sa.String(length=100), nullable=True),
            sa.Column('country', sa.String(length=10), nullable=True),
            sa.Column('is_blacklisted', sa.Boolean(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True), schema='security',
    )

    if not _has_table('cross_country_customer_sessions', 'configuration'):
        op.create_table('cross_country_customer_sessions',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('source_country_code', sa.String(length=3), nullable=False),
            sa.Column('target_country_code', sa.String(length=3), nullable=False),
            sa.Column('session_data', sa.Text(), nullable=True),
            sa.Column('conversion', sa.Boolean(), nullable=True),
            sa.Column('order_id', sa.Integer(), nullable=True),
            sa.Column('ip_address', sa.String(length=45), nullable=True),
            sa.Column('user_agent', sa.String(length=500), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True), schema='configuration',
    )

    if not _has_table('customers', 'finance'):
        op.create_table('customers',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('name', sa.String(length=200), nullable=False),
            sa.Column('tax_id', sa.String(length=60), nullable=True),
            sa.Column('contact_email', sa.String(length=160), nullable=True),
            sa.Column('currency', sa.String(length=3), nullable=True),
            sa.Column('payment_terms_days', sa.Integer(), nullable=True),
            sa.Column('credit_limit', sa.Numeric(precision=14, scale=2), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='finance',
    )

    if not _has_table('customs_entries', 'logistics'):
        op.create_table('customs_entries',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('shipment_id', sa.Integer(), nullable=False),
            sa.Column('customs_declaration_number', sa.String(length=50), nullable=True),
            sa.Column('customs_broker', sa.String(length=100), nullable=True),
            sa.Column('entry_date', sa.DateTime(), nullable=True),
            sa.Column('duty_rate_applied', sa.Numeric(precision=8, scale=4), nullable=True),
            sa.Column('duty_amount', sa.Numeric(precision=18, scale=2), nullable=True),
            sa.Column('vat_on_duty', sa.Numeric(precision=18, scale=2), nullable=True),
            sa.Column('penalties', sa.Numeric(precision=18, scale=2), nullable=True),
            sa.Column('total_customs_cost', sa.Numeric(precision=18, scale=2), nullable=True),
            sa.Column('status', sa.String(length=20), nullable=True),
            sa.Column('notes', sa.Text(), nullable=True),
            sa.Column('created_by', sa.Integer(), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
            sa.Column('updated_by', sa.Integer(), nullable=True),
            sa.Column('version', sa.Integer(), nullable=False, server_default=sa.text('1')),
            sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default=sa.text('false')),
            sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('deleted_by', sa.Integer(), nullable=True),
            sa.Column('delete_reason', sa.Text(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False), schema='logistics',
    )

    if not _has_table('data_residency_records', 'hr'):
        op.create_table('data_residency_records',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('data_type', sa.String(length=50), nullable=False),
            sa.Column('storage_location', sa.String(length=100), nullable=True),
            sa.Column('is_cross_border_allowed', sa.Boolean(), nullable=True),
            sa.Column('compliance_status', sa.String(length=30), nullable=True),
            sa.Column('country_code', sa.String(length=3), nullable=True),
            sa.Column('last_audit_at', sa.DateTime(), nullable=True),
            sa.Column('next_audit_at', sa.DateTime(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='hr',
    )

    if not _has_table('device_fingerprints', 'security'):
        op.create_table('device_fingerprints',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=True),
            sa.Column('fingerprint_hash', sa.String(), nullable=False),
            sa.Column('user_agent', sa.String(), nullable=True),
            sa.Column('ip_addresses', sa.Text(), nullable=True),
            sa.Column('is_trusted', sa.Boolean(), nullable=True),
            sa.Column('is_blocked', sa.Boolean(), nullable=True),
            sa.Column('risk_score', sa.Integer(), nullable=True),
            sa.Column('headless_attempts', sa.Integer(), nullable=True),
            sa.Column('account_count', sa.Integer(), nullable=True),
            sa.Column('first_seen_at', sa.DateTime(), nullable=True),
            sa.Column('last_seen_at', sa.DateTime(), nullable=True), schema='security',
    )

    if not _has_table('direct_chat_messages', 'communication'):
        op.create_table('direct_chat_messages',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('room_id', sa.Integer(), nullable=False),
            sa.Column('sender_id', sa.Integer(), nullable=False),
            sa.Column('message', sa.Text(), nullable=False),
            sa.Column('message_type', sa.String(length=20), nullable=True),
            sa.Column('read_at', sa.DateTime(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True), schema='communication',
    )

    if not _has_table('direct_chat_rooms', 'customer'):
        op.create_table('direct_chat_rooms',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('chat_id', sa.String(length=64), nullable=False, unique=True),
            sa.Column('participant_one', sa.Integer(), nullable=False),
            sa.Column('participant_two', sa.Integer(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='customer',
    )

    if not _has_table('disciplinary_cases', 'hr'):
        op.create_table('disciplinary_cases',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('employee_id', sa.Integer(), nullable=False),
            sa.Column('employee_name', sa.String(length=200), nullable=True),
            sa.Column('stage', sa.String(length=30), nullable=False),
            sa.Column('description', sa.Text(), nullable=False),
            sa.Column('issued_at', sa.DateTime(), nullable=True),
            sa.Column('status', sa.String(length=20), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='hr',
    )

    if not _has_table('dlp_violations', 'security'):
        op.create_table('dlp_violations',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('violation_type', sa.String(length=50), nullable=False),
            sa.Column('severity', sa.String(length=20), nullable=True),
            sa.Column('sender_id', sa.Integer(), nullable=True),
            sa.Column('recipient_email', sa.String(length=255), nullable=True),
            sa.Column('detected_content', sa.Text(), nullable=True),
            sa.Column('action_taken', sa.String(length=50), nullable=True),
            sa.Column('status', sa.String(length=20), nullable=True),
            sa.Column('reviewed_by', sa.Integer(), nullable=True),
            sa.Column('reviewed_at', sa.DateTime(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True), schema='security',
    )

    if not _has_table('document_verifications', 'security'):
        op.create_table('document_verifications',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('pipeline_id', sa.Integer(), nullable=False),
            sa.Column('document_type', sa.String(), nullable=False),
            sa.Column('document_data', sa.JSON(), nullable=True),
            sa.Column('status', sa.String(), nullable=True),
            sa.Column('verified_at', sa.DateTime(), nullable=True),
            sa.Column('verifier_id', sa.Integer(), nullable=True), schema='security',
    )

    if not _has_table('dynamic_qr_sessions', 'hr'):
        op.create_table('dynamic_qr_sessions',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('employee_id', sa.Integer(), nullable=False),
            sa.Column('qr_token', sa.String(length=255), nullable=False, unique=True),
            sa.Column('expires_at', sa.DateTime(), nullable=False),
            sa.Column('used_at', sa.DateTime(), nullable=True),
            sa.Column('ip_address', sa.String(length=45), nullable=True),
            sa.Column('user_agent', sa.String(length=500), nullable=True),
            sa.Column('device_fingerprint', sa.String(length=255), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='hr',
    )

    if not _has_table('email_campaign_logs', 'communication'):
        op.create_table('email_campaign_logs',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('campaign_id', sa.Integer(), nullable=False),
            sa.Column('recipient_email', sa.String(), nullable=False),
            sa.Column('status', sa.String(), nullable=True),
            sa.Column('sent_at', sa.DateTime(), nullable=True),
            sa.Column('delivered_at', sa.DateTime(), nullable=True),
            sa.Column('opened_at', sa.DateTime(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True), schema='communication',
    )

    if not _has_table('email_campaigns', 'communication'):
        op.create_table('email_campaigns',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('name', sa.String(), nullable=False),
            sa.Column('subject', sa.String(), nullable=False),
            sa.Column('status', sa.String(), nullable=True),
            sa.Column('send_at', sa.DateTime(), nullable=True),
            sa.Column('created_by', sa.Integer(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.Column('from_name', sa.String(length=200), nullable=True),
            sa.Column('target_audience', sa.Text(), nullable=True),
            sa.Column('scheduled_at', sa.DateTime(), nullable=True),
            sa.Column('sent_at', sa.DateTime(), nullable=True),
            sa.Column('sent_count', sa.Integer(), nullable=True),
            sa.Column('open_count', sa.Integer(), nullable=True),
            sa.Column('click_count', sa.Integer(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='communication',
    )

    if not _has_table('email_delivery_events', 'communication'):
        op.create_table('email_delivery_events',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('event_type', sa.String(), nullable=False),
            sa.Column('recipient_email', sa.String(), nullable=False),
            sa.Column('subject', sa.String(), nullable=True),
            sa.Column('status', sa.String(), nullable=True),
            sa.Column('details', sa.JSON(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True), schema='communication',
    )

    if not _has_table('email_folders', 'communication'):
        op.create_table('email_folders',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('employee_id', sa.Integer(), nullable=False),
            sa.Column('name', sa.String(length=50), nullable=False),
            sa.Column('folder_type', sa.String(length=20), nullable=True),
            sa.Column('sort_order', sa.Integer(), nullable=True),
            sa.Column('is_system', sa.Boolean(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True), schema='communication',
    )

    if not _has_table('email_provider_configs', 'configuration'):
        op.create_table('email_provider_configs',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('provider', sa.String(), nullable=True),
            sa.Column('updated_by', sa.Integer(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.Column('email_from_default', sa.String(), nullable=True),
            sa.Column('email_from_promotional', sa.String(), nullable=True),
            sa.Column('email_from_transactional', sa.String(), nullable=True),
            sa.Column('email_from_notification', sa.String(), nullable=True),
            sa.Column('email_from_alert', sa.String(), nullable=True),
            sa.Column('email_from_verification', sa.String(), nullable=True),
            sa.Column('email_from_login_verification', sa.String(), nullable=True),
            sa.Column('email_from_password_reset', sa.String(), nullable=True),
            sa.Column('resend_api_key', sa.String(), nullable=True),
            sa.Column('resend_webhook_secret', sa.String(), nullable=True),
            sa.Column('smtp_host', sa.String(), nullable=True),
            sa.Column('smtp_port', sa.Integer(), nullable=True),
            sa.Column('smtp_username', sa.String(), nullable=True),
            sa.Column('smtp_password', sa.String(), nullable=True),
            sa.Column('is_smtp_use_tls', sa.Boolean(), nullable=True),
            sa.Column('is_smtp_use_ssl', sa.Boolean(), nullable=True),
            sa.Column('smtp_timeout_seconds', sa.Integer(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='configuration',
    )

    if not _has_table('email_runtime_config', 'configuration'):
        op.create_table('email_runtime_config',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('provider', sa.String(length=50), nullable=True),
            sa.Column('resend_api_key', sa.String(), nullable=True),
            sa.Column('resend_webhook_secret', sa.String(), nullable=True),
            sa.Column('smtp_host', sa.String(), nullable=True),
            sa.Column('smtp_port', sa.Integer(), nullable=True),
            sa.Column('smtp_username', sa.String(), nullable=True),
            sa.Column('smtp_password', sa.String(), nullable=True),
            sa.Column('is_smtp_use_tls', sa.Boolean(), nullable=True),
            sa.Column('is_smtp_use_ssl', sa.Boolean(), nullable=True),
            sa.Column('smtp_timeout_seconds', sa.Integer(), nullable=True),
            sa.Column('email_from_default', sa.String(), nullable=True),
            sa.Column('email_from_promotional', sa.String(), nullable=True),
            sa.Column('email_from_transactional', sa.String(), nullable=True),
            sa.Column('email_from_notification', sa.String(), nullable=True),
            sa.Column('email_from_alert', sa.String(), nullable=True),
            sa.Column('email_from_verification', sa.String(), nullable=True),
            sa.Column('email_from_login_verification', sa.String(), nullable=True),
            sa.Column('email_from_password_reset', sa.String(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True), schema='configuration',
    )

    if not _has_table('email_suppressions', 'communication'):
        op.create_table('email_suppressions',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('email', sa.String(), nullable=False),
            sa.Column('reason', sa.String(), nullable=False),
            sa.Column('source', sa.String(), nullable=False),
            sa.Column('provider', sa.String(), nullable=True),
            sa.Column('status', sa.String(), nullable=True),
            sa.Column('notes', sa.Text(), nullable=True),
            sa.Column('suppressed_at', sa.DateTime(), nullable=True),
            sa.Column('last_event_at', sa.DateTime(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True), schema='communication',
    )

    if not _has_table('email_templates', 'communication'):
        op.create_table('email_templates',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('name', sa.String(length=200), nullable=False, unique=True),
            sa.Column('subject', sa.String(length=500), nullable=False),
            sa.Column('content', sa.Text(), nullable=True),
            sa.Column('template_type', sa.String(length=50), nullable=True),
            sa.Column('is_active', sa.Boolean(), nullable=True),
            sa.Column('created_by', sa.Integer(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True), schema='communication',
    )

    if not _has_table('email_verification_tokens', 'security'):
        op.create_table('email_verification_tokens',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=True),
            sa.Column('token', sa.String(), nullable=True, unique=True),
            sa.Column('expires_at', sa.DateTime(), nullable=False),
            sa.Column('used', sa.Boolean(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='security',
    )

    if not _has_table('employee_addresses', 'hr'):
        op.create_table('employee_addresses',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('employee_id', sa.Integer(), nullable=False),
            sa.Column('address_type', sa.String(length=30), nullable=False),
            sa.Column('street', sa.String(length=200), nullable=False),
            sa.Column('city', sa.String(length=100), nullable=False),
            sa.Column('state', sa.String(length=100), nullable=True),
            sa.Column('postal_code', sa.String(length=20), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('country_code', sa.String(length=3), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='hr',
    )

    if not _has_table('employee_assets', 'hr'):
        op.create_table('employee_assets',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('employee_id', sa.Integer(), nullable=False),
            sa.Column('asset_type', sa.String(length=50), nullable=False),
            sa.Column('asset_id', sa.String(length=100), nullable=False),
            sa.Column('serial_no', sa.String(length=100), nullable=True),
            sa.Column('assigned_at', sa.DateTime(), nullable=True),
            sa.Column('returned_at', sa.DateTime(), nullable=True),
            sa.Column('status', sa.String(length=20), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='hr',
    )

    if not _has_table('employee_attendance', 'hr'):
        op.create_table('employee_attendance',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('employee_id', sa.Integer(), nullable=False),
            sa.Column('date', sa.Date(), nullable=False),
            sa.Column('scan_in_time', sa.DateTime(), nullable=True),
            sa.Column('scan_out_time', sa.DateTime(), nullable=True),
            sa.Column('scan_type', sa.String(length=20), nullable=True),
            sa.Column('location_lat', sa.Float(), nullable=True),
            sa.Column('location_long', sa.Float(), nullable=True),
            sa.Column('device_fingerprint', sa.String(length=255), nullable=True),
            sa.Column('is_anomaly', sa.Boolean(), nullable=True),
            sa.Column('status', sa.String(length=20), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='hr',
    )

    if not _has_table('employee_biometrics', 'hr'):
        op.create_table('employee_biometrics',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('employee_id', sa.Integer(), nullable=False, unique=True),
            sa.Column('fingerprint_hash', sa.String(length=255), nullable=True),
            sa.Column('face_encoding', sa.Text(), nullable=True),
            sa.Column('biometric_type', sa.String(length=20), nullable=True),
            sa.Column('enrolled_at', sa.DateTime(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='hr',
    )

    if not _has_table('employee_certifications', 'hr'):
        op.create_table('employee_certifications',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('employee_id', sa.Integer(), nullable=False),
            sa.Column('cert_type', sa.String(length=100), nullable=False),
            sa.Column('cert_name', sa.String(length=200), nullable=False),
            sa.Column('issued_date', sa.Date(), nullable=True),
            sa.Column('expiry_date', sa.Date(), nullable=True),
            sa.Column('is_valid', sa.Boolean(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='hr',
    )

    if not _has_table('employee_communication_threads', 'communication'):
        op.create_table('employee_communication_threads',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('entity_id', sa.Integer(), nullable=False),
            sa.Column('entity_type', sa.String(length=50), nullable=False),
            sa.Column('participants', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('country_code', sa.String(length=3), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='communication',
    )

    if not _has_table('employee_dependents', 'hr'):
        op.create_table('employee_dependents',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('employee_id', sa.Integer(), nullable=False),
            sa.Column('name', sa.String(length=160), nullable=False),
            sa.Column('relation', sa.String(length=50), nullable=False),
            sa.Column('dob', sa.Date(), nullable=True),
            sa.Column('is_insured', sa.Boolean(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='hr',
    )

    if not _has_table('employee_documents', 'hr'):
        op.create_table('employee_documents',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('employee_id', sa.Integer(), nullable=False),
            sa.Column('doc_type', sa.String(length=50), nullable=False),
            sa.Column('file_url', sa.String(length=500), nullable=False),
            sa.Column('expiry_date', sa.Date(), nullable=True),
            sa.Column('verified_by', sa.Integer(), nullable=True),
            sa.Column('verified_at', sa.DateTime(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='hr',
    )

    if not _has_table('employee_expenses', 'hr'):
        op.create_table('employee_expenses',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('employee_id', sa.Integer(), nullable=False),
            sa.Column('expense_type', sa.String(length=50), nullable=False),
            sa.Column('amount', sa.Numeric(precision=12, scale=2), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('status', sa.String(length=20), nullable=True),
            sa.Column('approved_by', sa.Integer(), nullable=True),
            sa.Column('approved_at', sa.DateTime(), nullable=True),
            sa.Column('receipt_url', sa.String(length=500), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='hr',
    )

    if not _has_table('employee_leave_ledgers', 'hr'):
        op.create_table('employee_leave_ledgers',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('employee_id', sa.Integer(), nullable=False),
            sa.Column('leave_type', sa.String(length=50), nullable=False),
            sa.Column('year', sa.Integer(), nullable=False),
            sa.Column('allocated_days', sa.Integer(), nullable=True),
            sa.Column('used_days', sa.Integer(), nullable=True),
            sa.Column('carried_forward', sa.Integer(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='hr',
    )

    if not _has_table('employee_leave_requests', 'hr'):
        op.create_table('employee_leave_requests',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('employee_id', sa.Integer(), nullable=False),
            sa.Column('leave_type', sa.String(length=50), nullable=False),
            sa.Column('start_date', sa.Date(), nullable=False),
            sa.Column('end_date', sa.Date(), nullable=False),
            sa.Column('days_requested', sa.Integer(), nullable=False),
            sa.Column('status', sa.String(length=20), nullable=True),
            sa.Column('approved_by', sa.Integer(), nullable=True),
            sa.Column('approved_at', sa.DateTime(), nullable=True),
            sa.Column('rejection_reason', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='hr',
    )

    if not _has_table('employee_relations', 'hr'):
        op.create_table('employee_relations',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('employee_id', sa.Integer(), nullable=False),
            sa.Column('related_person_name', sa.String(length=160), nullable=False),
            sa.Column('relation_type', sa.String(length=30), nullable=False),
            sa.Column('is_internal_employee', sa.Boolean(), nullable=True),
            sa.Column('internal_employee_id', sa.Integer(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='hr',
    )

    if not _has_table('employee_roles', 'hr'):
        op.create_table('employee_roles',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('role_name', sa.String(length=100), nullable=True, unique=True),
            sa.Column('permissions', sa.JSON(), nullable=True),
            sa.Column('authority_level', sa.Integer(), nullable=True),
            sa.Column('can_approve_leave', sa.Boolean(), nullable=True),
            sa.Column('can_approve_expense', sa.Boolean(), nullable=True),
            sa.Column('can_manage_users', sa.Boolean(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='hr',
    )

    if not _has_table('employee_shift_rosters', 'hr'):
        op.create_table('employee_shift_rosters',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('employee_id', sa.Integer(), nullable=False),
            sa.Column('shift_date', sa.Date(), nullable=False),
            sa.Column('start_time', sa.Time(), nullable=False),
            sa.Column('end_time', sa.Time(), nullable=False),
            sa.Column('shift_type', sa.String(length=30), nullable=True),
            sa.Column('status', sa.String(length=20), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='hr',
    )

    if not _has_table('employee_trainings', 'hr'):
        op.create_table('employee_trainings',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('employee_id', sa.Integer(), nullable=False),
            sa.Column('module_id', sa.String(length=100), nullable=False),
            sa.Column('assigned_at', sa.DateTime(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')),
            sa.Column('completed_at', sa.DateTime(), nullable=True),
            sa.Column('score', sa.Numeric(precision=5, scale=2), nullable=True),
            sa.Column('status', sa.String(length=20), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='hr',
    )

    if not _has_table('employee_travel_requests', 'hr'):
        op.create_table('employee_travel_requests',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('employee_id', sa.Integer(), nullable=False),
            sa.Column('destination_country', sa.String(length=10), nullable=False),
            sa.Column('start_date', sa.Date(), nullable=False),
            sa.Column('end_date', sa.Date(), nullable=False),
            sa.Column('purpose', sa.String(length=200), nullable=True),
            sa.Column('status', sa.String(length=20), nullable=True),
            sa.Column('approved_by', sa.Integer(), nullable=True),
            sa.Column('approved_at', sa.DateTime(), nullable=True),
            sa.Column('per_diem_json', sa.JSON(), nullable=True),
            sa.Column('total_cost', sa.Numeric(precision=12, scale=2), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='hr',
    )

    if not _has_table('employee_work_logs', 'hr'):
        op.create_table('employee_work_logs',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('employee_id', sa.Integer(), nullable=False),
            sa.Column('date', sa.Date(), nullable=False),
            sa.Column('hours_worked', sa.Numeric(precision=5, scale=2), nullable=True),
            sa.Column('task_description', sa.Text(), nullable=True),
            sa.Column('location_lat', sa.Float(), nullable=True),
            sa.Column('location_long', sa.Float(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='hr',
    )

    if not _has_table('employees', 'hr'):
        op.create_table('employees',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=True, unique=True),
            sa.Column('employee_code', sa.String(length=20), nullable=False, unique=True),
            sa.Column('office_id', sa.Integer(), nullable=True),
            sa.Column('department', sa.String(length=100), nullable=True),
            sa.Column('position', sa.String(length=100), nullable=True),
            sa.Column('employment_type', sa.String(length=30), nullable=True),
            sa.Column('employment_status', sa.String(length=30), nullable=True),
            sa.Column('salary', sa.Numeric(precision=12, scale=2), nullable=True),
            sa.Column('currency', sa.String(length=3), nullable=True),
            sa.Column('termination_date', sa.Date(), nullable=True),
            sa.Column('hire_date', sa.DateTime(), nullable=True),
            sa.Column('is_verified', sa.Boolean(), nullable=True),
            sa.Column('gender', sa.String(length=20), nullable=True),
            sa.Column('years_of_experience', sa.Integer(), nullable=True),
            sa.Column('performance_score', sa.Integer(), nullable=True),
            sa.Column('education_level', sa.String(length=50), nullable=True),
            sa.Column('notes', sa.Text(), nullable=True),
            sa.Column('reporting_manager_id', sa.Integer(), nullable=True),
            sa.Column('hiring_manager_id', sa.Integer(), nullable=True),
            sa.Column('authority_level', sa.Integer(), nullable=True),
            sa.Column('org_unit_id', sa.Integer(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.Column('country_code', sa.String(length=3), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='hr',
    )

    if not _has_table('entity_chat_messages', 'communication'):
        op.create_table('entity_chat_messages',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('thread_id', sa.Integer(), nullable=False),
            sa.Column('sender_id', sa.Integer(), nullable=False),
            sa.Column('message', sa.Text(), nullable=False),
            sa.Column('message_type', sa.String(length=20), nullable=True),
            sa.Column('read_at', sa.DateTime(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True), schema='communication',
    )

    if not _has_table('entity_chat_threads', 'customer'):
        op.create_table('entity_chat_threads',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('entity_type', sa.String(), nullable=False),
            sa.Column('entity_id', sa.Integer(), nullable=False),
            sa.Column('title', sa.String(length=200), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True), schema='customer',
    )

    if not _has_table('erp_transactions', 'finance'):
        op.create_table('erp_transactions',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('type', sa.String(length=40), nullable=False),
            sa.Column('reference', sa.String(length=120), nullable=True),
            sa.Column('amount', sa.Numeric(precision=18, scale=2), nullable=True),
            sa.Column('status', sa.String(length=20), nullable=True),
            sa.Column('date', sa.DateTime(), nullable=True),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='finance',
    )

    if not _has_table('escalation_sla_logs', 'customer'):
        op.create_table('escalation_sla_logs',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('message_id', sa.Integer(), nullable=False),
            sa.Column('message_type', sa.String(length=30), nullable=False),
            sa.Column('original_recipient_id', sa.Integer(), nullable=True),
            sa.Column('escalated_to_user_id', sa.Integer(), nullable=True),
            sa.Column('escalated_to_role', sa.String(length=40), nullable=True),
            sa.Column('priority', sa.String(length=20), nullable=False),
            sa.Column('elapsed_minutes', sa.Integer(), nullable=True),
            sa.Column('status', sa.String(length=20), nullable=True),
            sa.Column('escalated_at', sa.DateTime(), nullable=True),
            sa.Column('acknowledged_at', sa.DateTime(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True), schema='customer',
    )

    if not _has_table('escalation_sla_rules', 'communication'):
        op.create_table('escalation_sla_rules',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('escalate_after_minutes', sa.Integer(), nullable=False),
            sa.Column('escalate_to_role', sa.String(length=40), nullable=False),
            sa.Column('notify_via', sa.String(length=100), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='communication',
    )

    if not _has_table('event_dead_letter', 'configuration'):
        op.create_table('event_dead_letter',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('uuid', sa.String(length=36), nullable=False, unique=True),
            sa.Column('event_id', sa.Integer(), nullable=False),
            sa.Column('payload_json', sa.Text(), nullable=False),
            sa.Column('failed_at', sa.DateTime(), nullable=False),
            sa.Column('reason', sa.String(length=255), nullable=True),
            sa.Column('resolved_by', sa.Integer(), nullable=True),
            sa.Column('country_code', sa.String(length=3), nullable=True),
            sa.Column('version', sa.Integer(), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
            sa.Column('is_deleted', sa.Boolean(), nullable=False),
            sa.Column('deleted_at', sa.DateTime(), nullable=True),
            sa.Column('delete_reason', sa.Text(), nullable=True),
            sa.Column('deleted_by_id', sa.Integer(), nullable=True),
            sa.Column('created_by_id', sa.Integer(), nullable=True),
            sa.Column('updated_by_id', sa.Integer(), nullable=True), schema='configuration',
    )

    if not _has_table('event_retry_queue', 'configuration'):
        op.create_table('event_retry_queue',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('uuid', sa.String(length=36), nullable=False, unique=True),
            sa.Column('event_id', sa.Integer(), nullable=False),
            sa.Column('attempt', sa.Integer(), nullable=False),
            sa.Column('next_attempt_at', sa.DateTime(), nullable=False),
            sa.Column('last_error', sa.Text(), nullable=True),
            sa.Column('country_code', sa.String(length=3), nullable=True),
            sa.Column('version', sa.Integer(), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
            sa.Column('is_deleted', sa.Boolean(), nullable=False),
            sa.Column('deleted_at', sa.DateTime(), nullable=True),
            sa.Column('delete_reason', sa.Text(), nullable=True),
            sa.Column('deleted_by_id', sa.Integer(), nullable=True),
            sa.Column('created_by_id', sa.Integer(), nullable=True),
            sa.Column('updated_by_id', sa.Integer(), nullable=True), schema='configuration',
    )

    if not _has_table('executive_news', 'analytics'):
        op.create_table('executive_news',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('title', sa.String(length=200), nullable=False),
            sa.Column('summary', sa.Text(), nullable=True),
            sa.Column('content', sa.Text(), nullable=True),
            sa.Column('url', sa.String(length=500), nullable=True),
            sa.Column('category', sa.String(length=50), nullable=True),
            sa.Column('priority', sa.String(length=20), nullable=True),
            sa.Column('ai_sentiment', sa.String(length=20), nullable=True),
            sa.Column('published_at', sa.DateTime(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='analytics',
    )

    if not _has_table('external_contact_masking', 'communication'):
        op.create_table('external_contact_masking',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('external_contact_type', sa.String(length=50), nullable=False),
            sa.Column('external_contact_id', sa.Integer(), nullable=False),
            sa.Column('masked_phone', sa.String(length=20), nullable=True),
            sa.Column('masked_email', sa.String(length=255), nullable=True), schema='communication',
    )

    if not _has_table('faqs', 'communication'):
        op.create_table('faqs',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('question', sa.Text(), nullable=False),
            sa.Column('answer', sa.Text(), nullable=False),
            sa.Column('category', sa.String(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='communication',
    )

    if not _has_table('feature_flags', 'configuration'):
        op.create_table('feature_flags',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('flag_key', sa.String(length=100), nullable=False, unique=True),
            sa.Column('flag_name', sa.String(length=255), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('disabled_for', sa.JSON(), nullable=True),
            sa.Column('rollout_percentage', sa.Integer(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='configuration',
    )

    if not _has_table('finance_audit_logs', 'finance'):
        op.create_table('finance_audit_logs',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('action', sa.String(length=60), nullable=False),
            sa.Column('actor_id', sa.Integer(), nullable=True),
            sa.Column('actor_role', sa.String(length=40), nullable=True),
            sa.Column('entity_type', sa.String(length=40), nullable=True),
            sa.Column('entity_id', sa.Integer(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='finance',
    )

    if not _has_table('finance_automation_logs', 'finance'):
        op.create_table('finance_automation_logs',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('kind', sa.String(length=40), nullable=False),
            sa.Column('records_processed', sa.Integer(), nullable=True),
            sa.Column('records_changed', sa.Integer(), nullable=True),
            sa.Column('detail', sa.JSON(), nullable=True),
            sa.Column('run_by', sa.Integer(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='finance',
    )

    if not _has_table('finance_bank_accounts', 'treasury'):
        op.create_table('finance_bank_accounts',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('account_name', sa.String(), nullable=True),
            sa.Column('account_number', sa.String(), nullable=False),
            sa.Column('bank_name', sa.String(), nullable=False),
            sa.Column('account_label', sa.String(), nullable=True),
            sa.Column('branch_name', sa.String(), nullable=True),
            sa.Column('iban', sa.String(), nullable=True),
            sa.Column('swift_code', sa.String(), nullable=True),
            sa.Column('routing_number', sa.String(), nullable=True),
            sa.Column('currency', sa.String(length=3), nullable=True),
            sa.Column('support_email', sa.String(), nullable=True),
            sa.Column('support_phone', sa.String(), nullable=True),
            sa.Column('remittance_reference_prefix', sa.String(), nullable=True),
            sa.Column('instructions', sa.Text(), nullable=True),
            sa.Column('created_by', sa.Integer(), nullable=True),
            sa.Column('updated_by', sa.Integer(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='treasury',
    )

    if not _has_table('finance_dashboard_metrics', 'finance'):
        op.create_table('finance_dashboard_metrics',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('metric_key', sa.String(length=100), nullable=False),
            sa.Column('metric_value', sa.Numeric(precision=18, scale=4), nullable=True),
            sa.Column('metric_label', sa.String(length=255), nullable=True),
            sa.Column('category', sa.String(length=50), nullable=True),
            sa.Column('computed_at', sa.DateTime(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='finance',
    )

    if not _has_table('finance_reports', 'finance'):
        op.create_table('finance_reports',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('report_type', sa.String(length=100), nullable=False),
            sa.Column('period_start', sa.DateTime(), nullable=False),
            sa.Column('period_end', sa.DateTime(), nullable=False),
            sa.Column('generated_at', sa.DateTime(), nullable=True),
            sa.Column('generated_by', sa.Integer(), nullable=True),
            sa.Column('status', sa.String(length=50), nullable=True),
            sa.Column('payload_json', sa.Text(), nullable=True),
            sa.Column('file_url', sa.String(length=500), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='finance',
    )

    if not _has_table('financial_reports', 'analytics'):
        op.create_table('financial_reports',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('report_type', sa.String(), nullable=False),
            sa.Column('period_start_at', sa.DateTime(), nullable=False),
            sa.Column('period_end_at', sa.DateTime(), nullable=False),
            sa.Column('generated_at', sa.DateTime(), nullable=True),
            sa.Column('is_deleted', sa.Boolean(), nullable=True),
            sa.Column('deleted_at', sa.DateTime(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='analytics',
    )

    if not _has_table('fiscal_periods', 'finance'):
        op.create_table('fiscal_periods',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('period_year', sa.Integer(), nullable=False),
            sa.Column('period_month', sa.Integer(), nullable=False),
            sa.Column('period_start_at', sa.DateTime(), nullable=False),
            sa.Column('period_end_at', sa.DateTime(), nullable=False),
            sa.Column('status', sa.String(length=20), nullable=True),
            sa.Column('is_locked', sa.Boolean(), nullable=True),
            sa.Column('closed_at', sa.DateTime(), nullable=True),
            sa.Column('closed_by', sa.Integer(), nullable=True),
            sa.Column('notes', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='finance',
    )

    if not _has_table('fixed_assets', 'finance'):
        op.create_table('fixed_assets',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('name', sa.String(length=200), nullable=False),
            sa.Column('asset_code', sa.String(length=40), nullable=True),
            sa.Column('category', sa.String(length=40), nullable=True),
            sa.Column('purchase_date', sa.DateTime(), nullable=False),
            sa.Column('purchase_cost', sa.Numeric(precision=14, scale=2), nullable=False),
            sa.Column('salvage_value', sa.Numeric(precision=14, scale=2), nullable=True),
            sa.Column('useful_life_months', sa.Integer(), nullable=False),
            sa.Column('accumulated_depreciation', sa.Numeric(precision=14, scale=2), nullable=True),
            sa.Column('last_depreciated_date', sa.DateTime(), nullable=True),
            sa.Column('asset_account_code', sa.String(length=20), nullable=True),
            sa.Column('depreciation_account_code', sa.String(length=20), nullable=True),
            sa.Column('accumulated_depr_account_code', sa.String(length=20), nullable=True),
            sa.Column('status', sa.String(length=20), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='finance',
    )

    if not _has_table('flash_sale_items', 'commerce'):
        op.create_table('flash_sale_items',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('flash_sale_id', sa.Integer(), nullable=False),
            sa.Column('product_id', sa.Integer(), nullable=False),
            sa.Column('original_price', sa.Numeric(precision=10, scale=2), nullable=False),
            sa.Column('discounted_price', sa.Numeric(precision=10, scale=2), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=True),
            sa.Column('quantity_limit', sa.Integer(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='commerce',
    )

    if not _has_table('flash_sales', 'commerce'):
        op.create_table('flash_sales',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('title', sa.String(), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('starts_at', sa.DateTime(), nullable=False),
            sa.Column('ends_at', sa.DateTime(), nullable=False),
            sa.Column('discount_pct', sa.Numeric(precision=5, scale=2), nullable=True),
            sa.Column('deleted_at', sa.DateTime(), nullable=True),
            sa.Column('deleted_by_id', sa.Integer(), nullable=True),
            sa.Column('product_ids', sa.JSON(), nullable=True),
            sa.Column('country_code', sa.String(length=3), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='commerce',
    )

    if not _has_table('fraud_alerts', 'security'):
        op.create_table('fraud_alerts',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('alert_type', sa.String(length=50), nullable=False),
            sa.Column('entity_type', sa.String(length=50), nullable=False),
            sa.Column('entity_id', sa.Integer(), nullable=False),
            sa.Column('fraud_score', sa.Numeric(precision=5, scale=2), nullable=False),
            sa.Column('triggered_rules', sa.Text(), nullable=True),
            sa.Column('priority', sa.String(length=20), nullable=True),
            sa.Column('details', sa.Text(), nullable=True),
            sa.Column('is_resolved', sa.Boolean(), nullable=True),
            sa.Column('resolved_at', sa.DateTime(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='security',
    )

    if not _has_table('fraud_blacklist', 'security'):
        op.create_table('fraud_blacklist',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('identifier_type', sa.String(), nullable=False),
            sa.Column('identifier_value', sa.String(), nullable=False),
            sa.Column('identifier_value_hash', sa.String(), nullable=True),
            sa.Column('reason', sa.String(), nullable=True),
            sa.Column('is_active', sa.Boolean(), nullable=True),
            sa.Column('status', sa.String(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('expires_at', sa.DateTime(), nullable=True), schema='security',
    )

    if not _has_table('fraud_case_assignments', 'security'):
        op.create_table('fraud_case_assignments',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('case_id', sa.Integer(), nullable=False),
            sa.Column('assigned_to', sa.Integer(), nullable=False),
            sa.Column('assigned_by', sa.Integer(), nullable=True),
            sa.Column('role_at_assignment', sa.String(length=50), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True), schema='security',
    )

    if not _has_table('fraud_cases', 'security'):
        op.create_table('fraud_cases',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('case_number', sa.String(length=50), nullable=False, unique=True),
            sa.Column('title', sa.String(length=200), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('fraud_score', sa.Integer(), nullable=False),
            sa.Column('priority', sa.String(length=20), nullable=True),
            sa.Column('status', sa.String(length=20), nullable=True),
            sa.Column('entity_type', sa.String(length=50), nullable=True),
            sa.Column('entity_id', sa.Integer(), nullable=True),
            sa.Column('assigned_to', sa.Integer(), nullable=True),
            sa.Column('created_by', sa.Integer(), nullable=True),
            sa.Column('resolved_at', sa.DateTime(), nullable=True),
            sa.Column('resolution_notes', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='security',
    )

    if not _has_table('fraud_events', 'security'):
        op.create_table('fraud_events',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=True),
            sa.Column('order_id', sa.Integer(), nullable=True),
            sa.Column('event_type', sa.String(length=50), nullable=False),
            sa.Column('ip_address', sa.String(length=45), nullable=True),
            sa.Column('device_hash', sa.String(length=64), nullable=True),
            sa.Column('session_id', sa.String(length=128), nullable=True),
            sa.Column('fraud_score', sa.Numeric(precision=5, scale=2), nullable=False),
            sa.Column('triggered_rules', sa.Text(), nullable=True),
            sa.Column('details', sa.JSON(), nullable=True),
            sa.Column('is_flagged', sa.Boolean(), nullable=True),
            sa.Column('status', sa.String(length=20), nullable=True),
            sa.Column('reviewed_by', sa.Integer(), nullable=True),
            sa.Column('reviewed_at', sa.DateTime(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='security',
    )

    if not _has_table('fraud_rules', 'security'):
        op.create_table('fraud_rules',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('rule_key', sa.String(length=100), nullable=False, unique=True),
            sa.Column('name', sa.String(length=200), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('weight', sa.Integer(), nullable=True),
            sa.Column('condition_json', sa.Text(), nullable=True),
            sa.Column('action', sa.String(length=50), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='security',
    )

    if not _has_table('fraud_scoring_logs', 'security'):
        op.create_table('fraud_scoring_logs',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('event_type', sa.String(length=50), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=True),
            sa.Column('order_id', sa.Integer(), nullable=True),
            sa.Column('ip_address', sa.String(length=45), nullable=True),
            sa.Column('device_hash', sa.String(length=64), nullable=True),
            sa.Column('session_id', sa.String(length=128), nullable=True),
            sa.Column('raw_score', sa.Integer(), nullable=False),
            sa.Column('triggered_rules', sa.JSON(), nullable=True),
            sa.Column('metadata_json', sa.JSON(), nullable=True),
            sa.Column('action_taken', sa.String(length=50), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='security',
    )

    if not _has_table('fraud_velocity_counters', 'security'):
        op.create_table('fraud_velocity_counters',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('key', sa.String(length=255), nullable=False),
            sa.Column('count', sa.Integer(), nullable=True),
            sa.Column('window_start', sa.DateTime(), nullable=True),
            sa.Column('window_end', sa.DateTime(), nullable=False),
            sa.Column('entity_type', sa.String(length=50), nullable=True),
            sa.Column('entity_id', sa.Integer(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True), schema='security',
    )

    if not _has_table('gateway_settlement_schedules', 'treasury'):
        op.create_table('gateway_settlement_schedules',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('gateway_id', sa.Integer(), nullable=False),
            sa.Column('settlement_date', sa.DateTime(), nullable=False),
            sa.Column('amount', sa.Numeric(precision=12, scale=2), nullable=False),
            sa.Column('currency', sa.String(length=3), nullable=True),
            sa.Column('status', sa.String(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='treasury',
    )

    if not _has_table('geo_fence_logs', 'hr'):
        op.create_table('geo_fence_logs',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('employee_id', sa.Integer(), nullable=False),
            sa.Column('latitude', sa.Float(), nullable=False),
            sa.Column('longitude', sa.Float(), nullable=False),
            sa.Column('accuracy_meters', sa.Integer(), nullable=True),
            sa.Column('scanned_at', sa.DateTime(), nullable=True),
            sa.Column('is_within_fence', sa.Boolean(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='hr',
    )

    if not _has_table('goods_receipt_lines', 'trading'):
        op.create_table('goods_receipt_lines',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('grn_id', sa.Integer(), nullable=False),
            sa.Column('po_line_id', sa.Integer(), nullable=True),
            sa.Column('product_id', sa.Integer(), nullable=True),
            sa.Column('product_name', sa.String(length=255), nullable=True),
            sa.Column('sku', sa.String(length=100), nullable=True),
            sa.Column('quantity_received', sa.Numeric(precision=14, scale=4), nullable=True),
            sa.Column('quantity_accepted', sa.Numeric(precision=14, scale=4), nullable=True),
            sa.Column('quantity_rejected', sa.Numeric(precision=14, scale=4), nullable=True),
            sa.Column('rejection_reason', sa.String(length=255), nullable=True),
            sa.Column('lot_number', sa.String(length=100), nullable=True),
            sa.Column('expiry_date', sa.DateTime(), nullable=True),
            sa.Column('unit_cost', sa.Numeric(precision=14, scale=4), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='trading',
    )

    if not _has_table('goods_receipt_notes', 'trading'):
        op.create_table('goods_receipt_notes',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('grn_number', sa.String(length=80), nullable=True, unique=True),
            sa.Column('po_id', sa.Integer(), nullable=False),
            sa.Column('supplier_id', sa.Integer(), nullable=True),
            sa.Column('receipt_date', sa.DateTime(), nullable=False),
            sa.Column('warehouse_id', sa.Integer(), nullable=True),
            sa.Column('status', sa.String(length=50), nullable=True),
            sa.Column('notes', sa.Text(), nullable=True),
            sa.Column('received_by', sa.Integer(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='trading',
    )

    if not _has_table('group_chat_members', 'customer'):
        op.create_table('group_chat_members',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('room_id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('role', sa.String(length=20), nullable=True),
            sa.Column('joined_at', sa.DateTime(), nullable=True), schema='customer',
    )

    if not _has_table('group_chat_messages', 'communication'):
        op.create_table('group_chat_messages',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('room_id', sa.Integer(), nullable=False),
            sa.Column('sender_id', sa.Integer(), nullable=False),
            sa.Column('message', sa.Text(), nullable=False),
            sa.Column('message_type', sa.String(length=20), nullable=True),
            sa.Column('read_at', sa.DateTime(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True), schema='communication',
    )

    if not _has_table('group_chat_rooms', 'communication'):
        op.create_table('group_chat_rooms',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('chat_id', sa.String(length=64), nullable=False, unique=True),
            sa.Column('name', sa.String(length=200), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='communication',
    )

    if not _has_table('help_categories', 'communication'):
        op.create_table('help_categories',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('name', sa.String(), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True), schema='communication',
    )

    if not _has_table('import_cost_templates', 'logistics'):
        op.create_table('import_cost_templates',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('name', sa.String(length=100), nullable=False),
            sa.Column('default_duty_rate', sa.Numeric(precision=8, scale=4), nullable=True),
            sa.Column('default_freight_percent', sa.Numeric(precision=8, scale=4), nullable=True),
            sa.Column('default_insurance_percent', sa.Numeric(precision=8, scale=4), nullable=True),
            sa.Column('default_port_charges_percent', sa.Numeric(precision=8, scale=4), nullable=True),
            sa.Column('default_bank_charges_percent', sa.Numeric(precision=8, scale=4), nullable=True),
            sa.Column('allocation_method', sa.String(length=20), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
            sa.Column('created_by', sa.Integer(), nullable=True),
            sa.Column('updated_by', sa.Integer(), nullable=True),
            sa.Column('version', sa.Integer(), nullable=False, server_default=sa.text('1')),
            sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default=sa.text('false')),
            sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('deleted_by', sa.Integer(), nullable=True),
            sa.Column('delete_reason', sa.Text(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False), schema='logistics',
    )

    if not _has_table('import_shipment_lines', 'logistics'):
        op.create_table('import_shipment_lines',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('shipment_id', sa.Integer(), nullable=False),
            sa.Column('po_line_id', sa.Integer(), nullable=True),
            sa.Column('product_id', sa.Integer(), nullable=True),
            sa.Column('product_name', sa.String(length=255), nullable=True),
            sa.Column('sku', sa.String(length=100), nullable=True),
            sa.Column('hs_code', sa.String(length=50), nullable=True),
            sa.Column('quantity', sa.Numeric(precision=18, scale=4), nullable=False),
            sa.Column('unit_cost_fx', sa.Numeric(precision=18, scale=6), nullable=True),
            sa.Column('unit_cost_local', sa.Numeric(precision=18, scale=6), nullable=True),
            sa.Column('line_total_fx', sa.Numeric(precision=18, scale=6), nullable=True),
            sa.Column('weight_kg', sa.Numeric(precision=12, scale=4), nullable=True),
            sa.Column('volume_cbm', sa.Numeric(precision=12, scale=4), nullable=True),
            sa.Column('allocated_insurance', sa.Numeric(precision=18, scale=2), nullable=True),
            sa.Column('allocated_port', sa.Numeric(precision=18, scale=2), nullable=True),
            sa.Column('allocated_other', sa.Numeric(precision=18, scale=2), nullable=True),
            sa.Column('duty_amount', sa.Numeric(precision=18, scale=2), nullable=True),
            sa.Column('landed_unit_cost', sa.Numeric(precision=18, scale=6), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
            sa.Column('created_by', sa.Integer(), nullable=True),
            sa.Column('updated_by', sa.Integer(), nullable=True),
            sa.Column('version', sa.Integer(), nullable=False, server_default=sa.text('1')),
            sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default=sa.text('false')),
            sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('deleted_by', sa.Integer(), nullable=True),
            sa.Column('delete_reason', sa.Text(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False), schema='logistics',
    )

    if not _has_table('import_shipments', 'logistics'):
        op.create_table('import_shipments',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('shipment_ref', sa.String(length=30), nullable=False, unique=True),
            sa.Column('po_id', sa.Integer(), nullable=True),
            sa.Column('supplier_id', sa.Integer(), nullable=True),
            sa.Column('supplier_name', sa.String(length=200), nullable=True),
            sa.Column('origin_country', sa.String(length=100), nullable=True),
            sa.Column('port_of_loading', sa.String(length=100), nullable=True),
            sa.Column('port_of_discharge', sa.String(length=100), nullable=True),
            sa.Column('vessel_name', sa.String(length=100), nullable=True),
            sa.Column('bill_of_lading', sa.String(length=100), nullable=True),
            sa.Column('container_number', sa.String(length=50), nullable=True),
            sa.Column('shipment_date', sa.DateTime(), nullable=True),
            sa.Column('estimated_arrival_at', sa.DateTime(), nullable=True),
            sa.Column('actual_arrival_at', sa.DateTime(), nullable=True),
            sa.Column('currency', sa.String(length=10), nullable=True),
            sa.Column('exchange_rate', sa.Numeric(precision=18, scale=6), nullable=True),
            sa.Column('warehouse_id', sa.Integer(), nullable=True),
            sa.Column('created_by', sa.Integer(), nullable=True),
            sa.Column('status', sa.String(length=20), nullable=True),
            sa.Column('product_cost_total', sa.Numeric(precision=18, scale=2), nullable=True),
            sa.Column('freight_cost', sa.Numeric(precision=18, scale=2), nullable=True),
            sa.Column('insurance_cost', sa.Numeric(precision=18, scale=2), nullable=True),
            sa.Column('port_charges', sa.Numeric(precision=18, scale=2), nullable=True),
            sa.Column('inland_freight', sa.Numeric(precision=18, scale=2), nullable=True),
            sa.Column('bank_charges', sa.Numeric(precision=18, scale=2), nullable=True),
            sa.Column('other_costs', sa.Numeric(precision=18, scale=2), nullable=True),
            sa.Column('duty_cost', sa.Numeric(precision=18, scale=2), nullable=True),
            sa.Column('total_landed_cost', sa.Numeric(precision=18, scale=2), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
            sa.Column('updated_by', sa.Integer(), nullable=True),
            sa.Column('version', sa.Integer(), nullable=False, server_default=sa.text('1')),
            sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default=sa.text('false')),
            sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('deleted_by', sa.Integer(), nullable=True),
            sa.Column('delete_reason', sa.Text(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False), schema='logistics',
    )

    if not _has_table('inbox_events', 'configuration'):
        op.create_table('inbox_events',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('uuid', sa.String(length=36), nullable=False, unique=True),
            sa.Column('idempotency_key', sa.String(length=64), nullable=False, unique=True),
            sa.Column('event_type', sa.String(length=100), nullable=False),
            sa.Column('status', sa.String(length=20), nullable=False),
            sa.Column('processed_at', sa.DateTime(), nullable=True),
            sa.Column('country_code', sa.String(length=3), nullable=True),
            sa.Column('version', sa.Integer(), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
            sa.Column('is_deleted', sa.Boolean(), nullable=False),
            sa.Column('deleted_at', sa.DateTime(), nullable=True),
            sa.Column('delete_reason', sa.Text(), nullable=True),
            sa.Column('deleted_by_id', sa.Integer(), nullable=True),
            sa.Column('created_by_id', sa.Integer(), nullable=True),
            sa.Column('updated_by_id', sa.Integer(), nullable=True), schema='configuration',
    )

    if not _has_table('incident_action_items', 'communication'):
        op.create_table('incident_action_items',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('war_room_id', sa.Integer(), nullable=False),
            sa.Column('assignee_id', sa.Integer(), nullable=True),
            sa.Column('title', sa.String(length=200), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('status', sa.String(), nullable=True),
            sa.Column('priority', sa.String(), nullable=True),
            sa.Column('due_date', sa.DateTime(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('completed_at', sa.DateTime(), nullable=True), schema='communication',
    )

    if not _has_table('incident_threads', 'communication'):
        op.create_table('incident_threads',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('war_room_id', sa.Integer(), nullable=False),
            sa.Column('participant_id', sa.Integer(), nullable=False),
            sa.Column('message', sa.Text(), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=True), schema='communication',
    )

    if not _has_table('incident_war_rooms', 'communication'):
        op.create_table('incident_war_rooms',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('incident_id', sa.String(), nullable=False, unique=True),
            sa.Column('title', sa.String(length=200), nullable=False),
            sa.Column('severity', sa.String(), nullable=True),
            sa.Column('status', sa.String(), nullable=True),
            sa.Column('created_by', sa.Integer(), nullable=False),
            sa.Column('started_at', sa.DateTime(), nullable=True),
            sa.Column('resolved_at', sa.DateTime(), nullable=True),
            sa.Column('closed_at', sa.DateTime(), nullable=True),
            sa.Column('context_data', sa.JSON(), nullable=True), schema='communication',
    )

    if not _has_table('internal_channel_members', 'communication'):
        op.create_table('internal_channel_members',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('channel_id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('role', sa.String(length=20), nullable=True),
            sa.Column('joined_at', sa.DateTime(), nullable=True), schema='communication',
    )

    if not _has_table('internal_channels', 'communication'):
        op.create_table('internal_channels',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('entity_type', sa.String(length=50), nullable=False),
            sa.Column('entity_id', sa.Integer(), nullable=False),
            sa.Column('name', sa.String(length=200), nullable=False),
            sa.Column('channel_id', sa.String(length=64), nullable=True, unique=True),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('is_public', sa.Boolean(), nullable=True),
            sa.Column('created_by', sa.Integer(), nullable=True),
            sa.Column('country_code', sa.String(length=3), nullable=True),
            sa.Column('allowed_roles', sa.JSON(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='communication',
    )

    if not _has_table('internal_emails', 'communication'):
        op.create_table('internal_emails',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('sender_id', sa.Integer(), nullable=False),
            sa.Column('subject', sa.String(length=200), nullable=False),
            sa.Column('body_html', sa.Text(), nullable=True),
            sa.Column('body_text', sa.Text(), nullable=True),
            sa.Column('recipients', sa.Text(), nullable=True),
            sa.Column('thread_id', sa.String(length=64), nullable=True),
            sa.Column('is_external', sa.Boolean(), nullable=True),
            sa.Column('external_message_id', sa.String(length=200), nullable=True),
            sa.Column('in_reply_to', sa.Integer(), nullable=True),
            sa.Column('folder_id', sa.Integer(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='communication',
    )

    if not _has_table('internal_messages', 'communication'):
        op.create_table('internal_messages',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('channel_id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('message', sa.Text(), nullable=False),
            sa.Column('message_type', sa.String(length=20), nullable=True),
            sa.Column('is_masked', sa.Boolean(), nullable=True),
            sa.Column('read_at', sa.DateTime(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True), schema='communication',
    )

    if not _has_table('internal_notices', 'communication'):
        op.create_table('internal_notices',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('title', sa.String(length=200), nullable=False),
            sa.Column('content', sa.Text(), nullable=False),
            sa.Column('priority', sa.String(length=20), nullable=True),
            sa.Column('valid_to', sa.DateTime(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True), schema='communication',
    )

    if not _has_table('invoice_items', 'finance'):
        op.create_table('invoice_items',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('invoice_id', sa.Integer(), nullable=False),
            sa.Column('product_id', sa.Integer(), nullable=True),
            sa.Column('description', sa.String(), nullable=False),
            sa.Column('quantity', sa.Integer(), nullable=True),
            sa.Column('unit_price', sa.Numeric(precision=10, scale=2), nullable=False),
            sa.Column('discount_amount', sa.Numeric(precision=10, scale=2), nullable=True),
            sa.Column('tax_rate', sa.Numeric(precision=5, scale=2), nullable=True),
            sa.Column('line_total', sa.Numeric(precision=10, scale=2), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='finance',
    )

    if not _has_table('invoices', 'finance'):
        op.create_table('invoices',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('order_id', sa.Integer(), nullable=False),
            sa.Column('shipment_id', sa.Integer(), nullable=True),
            sa.Column('supplier_id', sa.Integer(), nullable=True),
            sa.Column('invoice_number', sa.String(), nullable=True, unique=True),
            sa.Column('invoice_type', sa.String(), nullable=True),
            sa.Column('subtotal', sa.Numeric(precision=12, scale=2), nullable=True),
            sa.Column('tax_amount', sa.Numeric(precision=12, scale=2), nullable=True),
            sa.Column('shipping_amount', sa.Numeric(precision=12, scale=2), nullable=True),
            sa.Column('discount_amount', sa.Numeric(precision=12, scale=2), nullable=True),
            sa.Column('total_amount', sa.Numeric(precision=12, scale=2), nullable=True),
            sa.Column('currency', sa.String(length=3), nullable=True),
            sa.Column('status', sa.String(), nullable=True),
            sa.Column('issued_at', sa.DateTime(), nullable=True),
            sa.Column('due_at', sa.DateTime(), nullable=True),
            sa.Column('picked_at', sa.DateTime(), nullable=True),
            sa.Column('dispatched_at', sa.DateTime(), nullable=True),
            sa.Column('delivered_at', sa.DateTime(), nullable=True),
            sa.Column('paid_at', sa.DateTime(), nullable=True),
            sa.Column('notes', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.Column('deleted_at', sa.DateTime(), nullable=True),
            sa.Column('deleted_by', sa.Integer(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='finance',
    )

    if not _has_table('ip_account_linkages', 'security'):
        op.create_table('ip_account_linkages',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('ip_address', sa.String(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('device_fingerprint', sa.String(), nullable=True),
            sa.Column('session_id', sa.String(), nullable=True),
            sa.Column('interaction_count', sa.Integer(), nullable=True),
            sa.Column('is_suspicious', sa.Boolean(), nullable=True),
            sa.Column('last_seen', sa.DateTime(), nullable=True), schema='security',
    )

    if not _has_table('ip_reputations', 'security'):
        op.create_table('ip_reputations',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('ip_address', sa.String(), nullable=False),
            sa.Column('reputation_score', sa.Numeric(precision=5, scale=2), nullable=True),
            sa.Column('is_blocked', sa.Boolean(), nullable=True),
            sa.Column('is_proxy', sa.Boolean(), nullable=True),
            sa.Column('is_tor', sa.Boolean(), nullable=True),
            sa.Column('is_vpn', sa.Boolean(), nullable=True),
            sa.Column('is_hosting', sa.Boolean(), nullable=True),
            sa.Column('asn', sa.String(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='security',
    )

    if not _has_table('journal_entries', 'finance'):
        op.create_table('journal_entries',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('entry_date', sa.DateTime(), nullable=False),
            sa.Column('reference_number', sa.String(length=50), nullable=False, unique=True),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('source', sa.String(length=50), nullable=True),
            sa.Column('reconciled', sa.Boolean(), nullable=True),
            sa.Column('created_by', sa.Integer(), nullable=True),
            sa.Column('reference_type', sa.String(length=50), nullable=True),
            sa.Column('reference_id', sa.Integer(), nullable=True),
            sa.Column('period_id', sa.Integer(), nullable=True),
            sa.Column('reversal_of_id', sa.Integer(), nullable=True),
            sa.Column('is_deleted', sa.Boolean(), nullable=True),
            sa.Column('deleted_at', sa.DateTime(), nullable=True),
            sa.Column('deleted_by', sa.Integer(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='finance',
    )

    if not _has_table('journal_entry_lines', 'finance'):
        op.create_table('journal_entry_lines',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('entry_id', sa.Integer(), nullable=False),
            sa.Column('account_id', sa.Integer(), nullable=False),
            sa.Column('cost_center_id', sa.Integer(), nullable=True),
            sa.Column('amount', sa.Numeric(precision=12, scale=2), nullable=False),
            sa.Column('side', sa.String(length=10), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('entity_type', sa.String(length=50), nullable=True),
            sa.Column('entity_id', sa.Integer(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='finance',
    )

    if not _has_table('kpi_conversion', 'analytics'):
        op.create_table('kpi_conversion',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('kpi_date', sa.Date(), nullable=False),
            sa.Column('sessions', sa.Integer(), nullable=False),
            sa.Column('unique_visitors', sa.Integer(), nullable=False),
            sa.Column('add_to_cart_rate', sa.Numeric(precision=5, scale=4), nullable=False),
            sa.Column('checkout_conversion_rate', sa.Numeric(precision=5, scale=4), nullable=False),
            sa.Column('cart_abandonment_rate', sa.Numeric(precision=5, scale=4), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
            sa.Column('created_by', sa.Integer(), nullable=True),
            sa.Column('updated_by', sa.Integer(), nullable=True),
            sa.Column('is_deleted', sa.Boolean(), nullable=False),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='analytics',
    )

    if not _has_table('kpi_country', 'analytics'):
        op.create_table('kpi_country',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('kpi_date', sa.Date(), nullable=False),
            sa.Column('gmv', sa.Numeric(precision=14, scale=2), nullable=False),
            sa.Column('revenue', sa.Numeric(precision=14, scale=2), nullable=False),
            sa.Column('orders_count', sa.Integer(), nullable=False),
            sa.Column('active_users', sa.Integer(), nullable=False),
            sa.Column('conversion_rate', sa.Numeric(precision=5, scale=4), nullable=False),
            sa.Column('avg_order_value', sa.Numeric(precision=14, scale=2), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
            sa.Column('created_by', sa.Integer(), nullable=True),
            sa.Column('updated_by', sa.Integer(), nullable=True),
            sa.Column('is_deleted', sa.Boolean(), nullable=False),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='analytics',
    )

    if not _has_table('kpi_customer', 'analytics'):
        op.create_table('kpi_customer',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('kpi_date', sa.Date(), nullable=False),
            sa.Column('new_customers', sa.Integer(), nullable=False),
            sa.Column('active_customers', sa.Integer(), nullable=False),
            sa.Column('total_customers', sa.Integer(), nullable=False),
            sa.Column('repeat_customers', sa.Integer(), nullable=False),
            sa.Column('churned_customers', sa.Integer(), nullable=False),
            sa.Column('customer_lifetime_value', sa.Numeric(precision=14, scale=2), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
            sa.Column('created_by', sa.Integer(), nullable=True),
            sa.Column('updated_by', sa.Integer(), nullable=True),
            sa.Column('is_deleted', sa.Boolean(), nullable=False),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='analytics',
    )

    if not _has_table('kpi_orders', 'analytics'):
        op.create_table('kpi_orders',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('kpi_date', sa.Date(), nullable=False),
            sa.Column('total_orders', sa.Integer(), nullable=False),
            sa.Column('completed_orders', sa.Integer(), nullable=False),
            sa.Column('cancelled_orders', sa.Integer(), nullable=False),
            sa.Column('returned_orders', sa.Integer(), nullable=False),
            sa.Column('avg_order_value', sa.Numeric(precision=14, scale=2), nullable=False),
            sa.Column('on_time_delivery_rate', sa.Numeric(precision=5, scale=4), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
            sa.Column('created_by', sa.Integer(), nullable=True),
            sa.Column('updated_by', sa.Integer(), nullable=True),
            sa.Column('is_deleted', sa.Boolean(), nullable=False),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='analytics',
    )

    if not _has_table('kpi_retention', 'analytics'):
        op.create_table('kpi_retention',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('cohort_month', sa.String(length=7), nullable=False),
            sa.Column('retained_customers', sa.Integer(), nullable=False),
            sa.Column('retention_rate_1m', sa.Numeric(precision=5, scale=4), nullable=False),
            sa.Column('retention_rate_3m', sa.Numeric(precision=5, scale=4), nullable=False),
            sa.Column('retention_rate_6m', sa.Numeric(precision=5, scale=4), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
            sa.Column('created_by', sa.Integer(), nullable=True),
            sa.Column('updated_by', sa.Integer(), nullable=True),
            sa.Column('is_deleted', sa.Boolean(), nullable=False),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='analytics',
    )

    if not _has_table('kpi_revenue', 'analytics'):
        op.create_table('kpi_revenue',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('kpi_date', sa.Date(), nullable=False),
            sa.Column('gross_revenue', sa.Numeric(precision=14, scale=2), nullable=False),
            sa.Column('net_revenue', sa.Numeric(precision=14, scale=2), nullable=False),
            sa.Column('refunds', sa.Numeric(precision=14, scale=2), nullable=False),
            sa.Column('chargebacks', sa.Numeric(precision=14, scale=2), nullable=False),
            sa.Column('platform_commission', sa.Numeric(precision=14, scale=2), nullable=False),
            sa.Column('logistics_revenue', sa.Numeric(precision=14, scale=2), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
            sa.Column('created_by', sa.Integer(), nullable=True),
            sa.Column('updated_by', sa.Integer(), nullable=True),
            sa.Column('is_deleted', sa.Boolean(), nullable=False),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='analytics',
    )

    if not _has_table('kpi_supplier', 'analytics'):
        op.create_table('kpi_supplier',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('kpi_date', sa.Date(), nullable=False),
            sa.Column('new_suppliers', sa.Integer(), nullable=False),
            sa.Column('active_suppliers', sa.Integer(), nullable=False),
            sa.Column('total_suppliers', sa.Integer(), nullable=False),
            sa.Column('avg_products_per_supplier', sa.Numeric(precision=10, scale=2), nullable=False),
            sa.Column('fulfillment_rate', sa.Numeric(precision=5, scale=4), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
            sa.Column('created_by', sa.Integer(), nullable=True),
            sa.Column('updated_by', sa.Integer(), nullable=True),
            sa.Column('is_deleted', sa.Boolean(), nullable=False),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='analytics',
    )

    if not _has_table('kyc_verifications', 'security'):
        op.create_table('kyc_verifications',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('status', sa.String(), nullable=True),
            sa.Column('provider', sa.String(), nullable=True),
            sa.Column('verification_data', sa.JSON(), nullable=True),
            sa.Column('document_types', sa.JSON(), nullable=True),
            sa.Column('submitted_at', sa.DateTime(), nullable=True),
            sa.Column('reviewed_at', sa.DateTime(), nullable=True),
            sa.Column('reviewer_id', sa.Integer(), nullable=True), schema='security',
    )

    if not _has_table('landed_cost_allocations', 'logistics'):
        op.create_table('landed_cost_allocations',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('shipment_id', sa.Integer(), nullable=False),
            sa.Column('cost_type', sa.String(length=30), nullable=False),
            sa.Column('description', sa.String(length=255), nullable=True),
            sa.Column('total_amount', sa.Numeric(precision=18, scale=2), nullable=False),
            sa.Column('allocation_method', sa.String(length=20), nullable=True),
            sa.Column('currency', sa.String(length=10), nullable=True),
            sa.Column('exchange_rate', sa.Numeric(precision=18, scale=6), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('created_by', sa.Integer(), nullable=True),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
            sa.Column('updated_by', sa.Integer(), nullable=True),
            sa.Column('version', sa.Integer(), nullable=False, server_default=sa.text('1')),
            sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default=sa.text('false')),
            sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('deleted_by', sa.Integer(), nullable=True),
            sa.Column('delete_reason', sa.Text(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False), schema='logistics',
    )

    if not _has_table('legal_contract_templates', 'hr'):
        op.create_table('legal_contract_templates',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('template_type', sa.String(length=50), nullable=False),
            sa.Column('config_version', sa.String(length=20), nullable=True),
            sa.Column('country_code', sa.String(length=3), nullable=True),
            sa.Column('content', sa.Text(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='hr',
    )

    if not _has_table('logistics_category_pricing_rules', 'logistics'):
        op.create_table('logistics_category_pricing_rules',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('partner_id', sa.Integer(), nullable=False),
            sa.Column('service_area_id', sa.Integer(), nullable=True),
            sa.Column('category_name', sa.String(), nullable=False),
            sa.Column('flat_fee_override', sa.Numeric(precision=10, scale=2), nullable=True),
            sa.Column('special_handling_fee', sa.Numeric(precision=10, scale=2), nullable=True),
            sa.Column('currency', sa.String(length=3), nullable=True),
            sa.Column('approval_status', sa.String(), nullable=True),
            sa.Column('review_note', sa.String(), nullable=True),
            sa.Column('reviewed_by', sa.Integer(), nullable=True),
            sa.Column('reviewed_at', sa.DateTime(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='logistics',
    )

    if not _has_table('logistics_cod_remittance_receipts', 'logistics'):
        op.create_table('logistics_cod_remittance_receipts',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('partner_id', sa.Integer(), nullable=True),
            sa.Column('shipment_id', sa.Integer(), nullable=True),
            sa.Column('settlement_id', sa.Integer(), nullable=True),
            sa.Column('amount', sa.Numeric(precision=12, scale=2), nullable=False),
            sa.Column('bank_reference', sa.String(), nullable=True),
            sa.Column('receipt_file_url', sa.String(), nullable=True),
            sa.Column('notes', sa.Text(), nullable=True),
            sa.Column('review_note', sa.Text(), nullable=True),
            sa.Column('reviewed_by', sa.Integer(), nullable=True),
            sa.Column('status', sa.String(), nullable=True),
            sa.Column('currency', sa.String(length=3), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='logistics',
    )

    if not _has_table('logistics_fraud_indicators', 'logistics'):
        op.create_table('logistics_fraud_indicators',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('partner_id', sa.Integer(), nullable=False),
            sa.Column('indicator_type', sa.String(length=50), nullable=False),
            sa.Column('value', sa.String(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='logistics',
    )

    if not _has_table('logistics_partner_bank_accounts', 'logistics'):
        op.create_table('logistics_partner_bank_accounts',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('partner_id', sa.Integer(), nullable=False),
            sa.Column('account_number', sa.String(), nullable=True),
            sa.Column('bank_name', sa.String(), nullable=False),
            sa.Column('beneficiary_name', sa.String(), nullable=True),
            sa.Column('branch_name', sa.String(), nullable=True),
            sa.Column('iban', sa.String(), nullable=True),
            sa.Column('swift_code', sa.String(), nullable=True),
            sa.Column('routing_number', sa.String(), nullable=True),
            sa.Column('currency', sa.String(length=3), nullable=True),
            sa.Column('bank_country', sa.String(length=3), nullable=True),
            sa.Column('verification_status', sa.String(), nullable=True),
            sa.Column('verification_note', sa.Text(), nullable=True),
            sa.Column('provider', sa.String(), nullable=True),
            sa.Column('provider_recipient_id', sa.String(), nullable=True),
            sa.Column('provider_status', sa.String(), nullable=True),
            sa.Column('provider_last_synced_at', sa.DateTime(), nullable=True),
            sa.Column('verified_at', sa.DateTime(), nullable=True),
            sa.Column('verified_by', sa.Integer(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='logistics',
    )

    if not _has_table('logistics_partner_documents', 'logistics'):
        op.create_table('logistics_partner_documents',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('partner_id', sa.Integer(), nullable=False),
            sa.Column('doc_type', sa.String(), nullable=False),
            sa.Column('file_url', sa.String(), nullable=False),
            sa.Column('reviewed_by', sa.Integer(), nullable=True),
            sa.Column('is_verified', sa.Boolean(), nullable=True),
            sa.Column('verified_at', sa.DateTime(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='logistics',
    )

    if not _has_table('logistics_partner_kyc_requirements', 'country'):
        op.create_table('logistics_partner_kyc_requirements',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False, unique=True),
            sa.Column('min_experience_months', sa.Integer(), nullable=True),
            sa.Column('required_documents', sa.Text(), nullable=True),
            sa.Column('insurance_required', sa.Boolean(), nullable=True),
            sa.Column('insurance_min_coverage', sa.Numeric(precision=15, scale=2), nullable=True),
            sa.Column('vehicle_requirements', sa.Text(), nullable=True),
            sa.Column('background_check_required', sa.Boolean(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True), schema='country',
    )

    if not _has_table('logistics_partner_locations', 'hr'):
        op.create_table('logistics_partner_locations',
                    sa.Column('country_code', sa.String(length=3), nullable=True),
            sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('partner_id', sa.Integer(), nullable=False),
            sa.Column('latitude', sa.Float(), nullable=True),
            sa.Column('longitude', sa.Float(), nullable=True),
            sa.Column('address', sa.Text(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='hr',
    )

    if not _has_table('logistics_partner_payouts', 'logistics'):
        op.create_table('logistics_partner_payouts',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('partner_id', sa.Integer(), nullable=False),
            sa.Column('amount', sa.Numeric(precision=12, scale=2), nullable=False),
            sa.Column('currency', sa.String(length=3), nullable=True),
            sa.Column('period_start_at', sa.DateTime(), nullable=True),
            sa.Column('period_end_at', sa.DateTime(), nullable=True),
            sa.Column('status', sa.String(), nullable=True),
            sa.Column('reference_id', sa.String(), nullable=True),
            sa.Column('processed_at', sa.DateTime(), nullable=True),
            sa.Column('country_code', sa.String(length=3), nullable=True),
            sa.Column('method', sa.String(), nullable=True),
            sa.Column('notes', sa.Text(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='logistics',
    )

    if not _has_table('logistics_partner_profiles', 'logistics'):
        op.create_table('logistics_partner_profiles',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('partner_id', sa.Integer(), nullable=False, unique=True),
            sa.Column('tax_id', sa.String(), nullable=True),
            sa.Column('registration_number', sa.String(), nullable=True),
            sa.Column('business_type', sa.String(), nullable=True),
            sa.Column('years_in_business', sa.Integer(), nullable=True),
            sa.Column('insurance_provider', sa.String(), nullable=True),
            sa.Column('insurance_policy_number', sa.String(), nullable=True),
            sa.Column('insurance_expiry_at', sa.DateTime(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='logistics',
    )

    if not _has_table('logistics_partner_service_areas', 'logistics'):
        op.create_table('logistics_partner_service_areas',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('partner_id', sa.Integer(), nullable=False),
            sa.Column('origin_city', sa.String(), nullable=False),
            sa.Column('city_name', sa.String(), nullable=False),
            sa.Column('country_name', sa.String(), nullable=True),
            sa.Column('zone_label', sa.String(), nullable=True),
            sa.Column('charge_amount', sa.Numeric(precision=10, scale=2), nullable=True),
            sa.Column('minimum_charge', sa.Numeric(precision=10, scale=2), nullable=True),
            sa.Column('per_kg_rate', sa.Numeric(precision=10, scale=2), nullable=True),
            sa.Column('pickup_charge', sa.Numeric(precision=10, scale=2), nullable=True),
            sa.Column('dropoff_charge', sa.Numeric(precision=10, scale=2), nullable=True),
            sa.Column('per_km_rate', sa.Numeric(precision=10, scale=2), nullable=True),
            sa.Column('currency', sa.String(length=3), nullable=True),
            sa.Column('delivery_days_min', sa.Integer(), nullable=True),
            sa.Column('delivery_days_max', sa.Integer(), nullable=True),
            sa.Column('approval_status', sa.String(), nullable=True),
            sa.Column('is_active', sa.Boolean(), nullable=True),
            sa.Column('country_code', sa.String(length=3), nullable=True),
            sa.Column('review_note', sa.String(), nullable=True),
            sa.Column('reviewed_by', sa.Integer(), nullable=True),
            sa.Column('reviewed_at', sa.DateTime(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='logistics',
    )

    if not _has_table('logistics_partners', 'logistics'):
        op.create_table('logistics_partners',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=True),
            sa.Column('name', sa.String(), nullable=False),
            sa.Column('code', sa.String(), nullable=False, unique=True),
            sa.Column('contact_name', sa.String(), nullable=True),
            sa.Column('contact_email', sa.String(), nullable=True),
            sa.Column('contact_phone', sa.String(), nullable=True),
            sa.Column('website', sa.String(), nullable=True),
            sa.Column('coverage_regions_json', sa.JSON(), nullable=True),
            sa.Column('service_types_json', sa.JSON(), nullable=True),
            sa.Column('status', sa.String(), nullable=True),
            sa.Column('verification_status', sa.String(), nullable=True),
            sa.Column('verification_note', sa.String(), nullable=True),
            sa.Column('verified_by', sa.Integer(), nullable=True),
            sa.Column('verified_at', sa.DateTime(), nullable=True),
            sa.Column('business_type', sa.String(), nullable=True),
            sa.Column('region', sa.String(), nullable=True),
            sa.Column('city', sa.String(), nullable=True),
            sa.Column('address', sa.Text(), nullable=True),
            sa.Column('postal_code', sa.String(), nullable=True),
            sa.Column('tax_id', sa.String(), nullable=True),
            sa.Column('bio', sa.Text(), nullable=True),
            sa.Column('about_us', sa.Text(), nullable=True),
            sa.Column('logo_url', sa.String(), nullable=True),
            sa.Column('banner_url', sa.String(), nullable=True),
            sa.Column('latitude', sa.Numeric(precision=10, scale=7), nullable=True),
            sa.Column('longitude', sa.Numeric(precision=10, scale=7), nullable=True),
            sa.Column('social_links_json', sa.JSON(), nullable=True),
            sa.Column('notes', sa.Text(), nullable=True),
            sa.Column('is_terms_accepted', sa.Boolean(), nullable=True),
            sa.Column('terms_version', sa.String(), nullable=True),
            sa.Column('terms_accepted_at', sa.DateTime(), nullable=True),
            sa.Column('country_code', sa.String(length=3), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='logistics',
    )

    if not _has_table('logistics_pricing_profiles', 'logistics'):
        op.create_table('logistics_pricing_profiles',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('partner_id', sa.Integer(), nullable=False),
            sa.Column('service_area_id', sa.Integer(), nullable=False),
            sa.Column('profile_name', sa.String(), nullable=False),
            sa.Column('base_in_city_fee', sa.Numeric(precision=10, scale=2), nullable=True),
            sa.Column('per_kg_rate', sa.Numeric(precision=10, scale=2), nullable=True),
            sa.Column('minimum_charge', sa.Numeric(precision=10, scale=2), nullable=True),
            sa.Column('maximum_charge', sa.Numeric(precision=10, scale=2), nullable=True),
            sa.Column('fuel_multiplier', sa.Numeric(precision=5, scale=4), nullable=True),
            sa.Column('base_inter_city_fee', sa.Numeric(precision=10, scale=2), nullable=True),
            sa.Column('per_km_rate', sa.Numeric(precision=10, scale=2), nullable=True),
            sa.Column('bulk_discount_threshold_kg', sa.Numeric(precision=10, scale=2), nullable=True),
            sa.Column('bulk_discount_percent', sa.Numeric(precision=5, scale=4), nullable=True),
            sa.Column('currency', sa.String(length=3), nullable=True),
            sa.Column('approval_status', sa.String(), nullable=True),
            sa.Column('review_note', sa.String(), nullable=True),
            sa.Column('reviewed_by', sa.Integer(), nullable=True),
            sa.Column('reviewed_at', sa.DateTime(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='logistics',
    )

    if not _has_table('logistics_pricing_rules', 'logistics'):
        op.create_table('logistics_pricing_rules',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('zone_id', sa.Integer(), nullable=False),
            sa.Column('vehicle_type', sa.String(length=50), nullable=False),
            sa.Column('distance_band_start', sa.Numeric(precision=10, scale=2), nullable=True),
            sa.Column('distance_band_end', sa.Numeric(precision=10, scale=2), nullable=True),
            sa.Column('weight_band_start', sa.Numeric(precision=10, scale=2), nullable=True),
            sa.Column('weight_band_end', sa.Numeric(precision=10, scale=2), nullable=True),
            sa.Column('base_rate', sa.Numeric(precision=14, scale=4), nullable=False),
            sa.Column('per_km_rate', sa.Numeric(precision=14, scale=4), nullable=True),
            sa.Column('per_kg_rate', sa.Numeric(precision=14, scale=4), nullable=True),
            sa.Column('fuel_surcharge_percent', sa.Numeric(precision=5, scale=2), nullable=True),
            sa.Column('currency', sa.String(length=3), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True), schema='logistics',
    )

    if not _has_table('logistics_rates', 'logistics'):
        op.create_table('logistics_rates',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('zone_id', sa.Integer(), nullable=False),
            sa.Column('carrier_id', sa.Integer(), nullable=True),
            sa.Column('service_level', sa.String(length=50), nullable=True),
            sa.Column('rate', sa.Numeric(precision=14, scale=4), nullable=False),
            sa.Column('currency', sa.String(length=3), nullable=True),
            sa.Column('estimated_days_min', sa.Integer(), nullable=True),
            sa.Column('estimated_days_max', sa.Integer(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='logistics',
    )

    if not _has_table('logistics_settlements', 'logistics'):
        op.create_table('logistics_settlements',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('partner_id', sa.Integer(), nullable=False),
            sa.Column('order_id', sa.Integer(), nullable=True),
            sa.Column('ledger_id', sa.Integer(), nullable=True),
            sa.Column('shipment_id', sa.Integer(), nullable=True),
            sa.Column('amount', sa.Numeric(precision=12, scale=2), nullable=True),
            sa.Column('pickup_charge', sa.Numeric(precision=12, scale=2), nullable=True),
            sa.Column('dropoff_charge', sa.Numeric(precision=12, scale=2), nullable=True),
            sa.Column('total_delivery_fee', sa.Numeric(precision=12, scale=2), nullable=True),
            sa.Column('cod_collected', sa.Numeric(precision=12, scale=2), nullable=True),
            sa.Column('cod_remitted', sa.Numeric(precision=12, scale=2), nullable=True),
            sa.Column('cod_retained', sa.Numeric(precision=12, scale=2), nullable=True),
            sa.Column('cod_remittance_status', sa.String(), nullable=True),
            sa.Column('eligible_at', sa.DateTime(), nullable=True),
            sa.Column('status', sa.String(), nullable=True),
            sa.Column('currency', sa.String(length=3), nullable=True),
            sa.Column('payout_id', sa.Integer(), nullable=True),
            sa.Column('bank_transaction_id', sa.Integer(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='logistics',
    )

    if not _has_table('logistics_vehicle_rules', 'logistics'):
        op.create_table('logistics_vehicle_rules',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('partner_id', sa.Integer(), nullable=False),
            sa.Column('service_area_id', sa.Integer(), nullable=False),
            sa.Column('vehicle_type', sa.String(), nullable=False),
            sa.Column('max_weight_kg', sa.Numeric(precision=10, scale=2), nullable=True),
            sa.Column('cost_multiplier', sa.Numeric(precision=5, scale=4), nullable=True),
            sa.Column('priority_rank', sa.Integer(), nullable=True),
            sa.Column('route_scope', sa.String(), nullable=True),
            sa.Column('max_volume_cm3', sa.Numeric(precision=12, scale=2), nullable=True),
            sa.Column('approval_status', sa.String(), nullable=True),
            sa.Column('review_note', sa.String(), nullable=True),
            sa.Column('reviewed_by', sa.Integer(), nullable=True),
            sa.Column('reviewed_at', sa.DateTime(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='logistics',
    )

    if not _has_table('logistics_zones', 'logistics'):
        op.create_table('logistics_zones',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('zone_name', sa.String(length=255), nullable=False),
            sa.Column('zone_code', sa.String(length=50), nullable=False, unique=True),
            sa.Column('country_codes', sa.JSON(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True), schema='logistics',
    )

    if not _has_table('manual_review_queue', 'security'):
        op.create_table('manual_review_queue',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('entity_type', sa.String(length=50), nullable=False),
            sa.Column('entity_id', sa.Integer(), nullable=False),
            sa.Column('fraud_score', sa.Integer(), nullable=False),
            sa.Column('triggered_rules', sa.Text(), nullable=True),
            sa.Column('reason', sa.String(), nullable=False),
            sa.Column('priority', sa.String(), nullable=True),
            sa.Column('assigned_to', sa.Integer(), nullable=True),
            sa.Column('admin_notes', sa.Text(), nullable=True),
            sa.Column('status', sa.String(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True), schema='security',
    )

    if not _has_table('masked_messages', 'communication'):
        op.create_table('masked_messages',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('sender_id', sa.Integer(), nullable=False),
            sa.Column('recipient_ref', sa.String(length=200), nullable=False),
            sa.Column('message_hash', sa.Integer(), nullable=False),
            sa.Column('content', sa.Text(), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='communication',
    )

    if not _has_table('media_assets', 'media'):
        op.create_table('media_assets',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('product_id', sa.Integer(), nullable=True),
            sa.Column('supplier_id', sa.Integer(), nullable=True),
            sa.Column('entity_type', sa.String(length=20), nullable=False),
            sa.Column('entity_id', sa.Integer(), nullable=True),
            sa.Column('variant', sa.String(length=20), nullable=False),
            sa.Column('file_path', sa.String(length=500), nullable=False),
            sa.Column('file_url', sa.String(length=500), nullable=False),
            sa.Column('file_size_bytes', sa.Integer(), nullable=False),
            sa.Column('mime_type', sa.String(length=100), nullable=False),
            sa.Column('width', sa.Integer(), nullable=True),
            sa.Column('height', sa.Integer(), nullable=True),
            sa.Column('is_primary', sa.Boolean(), nullable=True),
            sa.Column('alt_text', sa.String(length=255), nullable=True),
            sa.Column('caption', sa.Text(), nullable=True),
            sa.Column('uploaded_by', sa.Integer(), nullable=True),
            sa.Column('uploaded_at', sa.DateTime(), nullable=True),
            sa.Column('is_deleted', sa.Boolean(), nullable=True),
            sa.Column('deleted_at', sa.DateTime(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
            sa.Column('created_by', sa.Integer(), nullable=True),
            sa.Column('updated_by', sa.Integer(), nullable=True),
            sa.Column('deleted_by', sa.Integer(), nullable=True),
            sa.Column('delete_reason', sa.Text(), nullable=True), schema='media',
    )

    if not _has_table('media_upload_sessions', 'media'):
        op.create_table('media_upload_sessions',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('session_id', sa.String(length=64), nullable=False, unique=True),
            sa.Column('entity_id', sa.Integer(), nullable=True),
            sa.Column('filename', sa.String(length=255), nullable=False),
            sa.Column('file_size', sa.Integer(), nullable=False),
            sa.Column('mime_type', sa.String(length=100), nullable=False),
            sa.Column('chunk_size', sa.Integer(), nullable=True),
            sa.Column('total_chunks', sa.Integer(), nullable=False),
            sa.Column('uploaded_chunks', sa.Integer(), nullable=True),
            sa.Column('status', sa.String(length=20), nullable=True),
            sa.Column('error_message', sa.Text(), nullable=True),
            sa.Column('created_by', sa.Integer(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('completed_at', sa.DateTime(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
            sa.Column('updated_by', sa.Integer(), nullable=True),
            sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default=sa.text('false')),
            sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('deleted_by', sa.Integer(), nullable=True),
            sa.Column('delete_reason', sa.Text(), nullable=True), schema='media',
    )

    if not _has_table('meeting_action_items', 'security'):
        op.create_table('meeting_action_items',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('meeting_id', sa.Integer(), nullable=False),
            sa.Column('entity_type', sa.String(length=50), nullable=True),
            sa.Column('entity_id', sa.Integer(), nullable=True),
            sa.Column('action', sa.String(), nullable=False),
            sa.Column('metadata_json', sa.JSON(), nullable=True),
            sa.Column('status', sa.String(length=20), nullable=True),
            sa.Column('assigned_to', sa.Integer(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('due_date', sa.DateTime(), nullable=True), schema='security',
    )

    if not _has_table('meeting_recordings', 'communication'):
        op.create_table('meeting_recordings',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('room_id', sa.String(length=64), nullable=False),
            sa.Column('started_by', sa.Integer(), nullable=False),
            sa.Column('recording_url', sa.String(length=500), nullable=True),
            sa.Column('duration_seconds', sa.Integer(), nullable=True),
            sa.Column('status', sa.String(length=20), nullable=True),
            sa.Column('started_at', sa.DateTime(), nullable=True),
            sa.Column('ended_at', sa.DateTime(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True), schema='communication',
    )

    if not _has_table('meeting_transcripts', 'security'):
        op.create_table('meeting_transcripts',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('room_id', sa.String(length=64), nullable=False),
            sa.Column('language', sa.String(length=10), nullable=True),
            sa.Column('segments', sa.JSON(), nullable=True),
            sa.Column('action_items', sa.JSON(), nullable=True),
            sa.Column('summary', sa.Text(), nullable=True),
            sa.Column('word_count', sa.Integer(), nullable=True),
            sa.Column('duration_seconds', sa.Integer(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True), schema='security',
    )

    if not _has_table('messages', 'country'):
        op.create_table('messages',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=True),
            sa.Column('from_user_id', sa.Integer(), nullable=False),
            sa.Column('to_user_id', sa.Integer(), nullable=False),
            sa.Column('subject', sa.String(length=200), nullable=False),
            sa.Column('body', sa.Text(), nullable=True),
            sa.Column('entity_type', sa.String(length=50), nullable=True),
            sa.Column('entity_id', sa.Integer(), nullable=True),
            sa.Column('priority', sa.String(length=20), nullable=True),
            sa.Column('category', sa.String(length=50), nullable=True),
            sa.Column('status', sa.String(length=20), nullable=True),
            sa.Column('read_at', sa.DateTime(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True), schema='country',
    )

    if not _has_table('mv_cash_position', 'analytics'):
        op.create_table('mv_cash_position',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('snapshot_date', sa.Date(), nullable=False),
            sa.Column('currency', sa.String(length=3), nullable=False),
            sa.Column('total_cash', sa.Numeric(precision=14, scale=2), nullable=False),
            sa.Column('cash_in_banks', sa.Numeric(precision=14, scale=2), nullable=False),
            sa.Column('cash_in_transit', sa.Numeric(precision=14, scale=2), nullable=False),
            sa.Column('pending_payouts', sa.Numeric(precision=14, scale=2), nullable=False),
            sa.Column('pending_settlements', sa.Numeric(precision=14, scale=2), nullable=False),
            sa.Column('net_cash_position', sa.Numeric(precision=14, scale=2), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
            sa.Column('created_by', sa.Integer(), nullable=True),
            sa.Column('updated_by', sa.Integer(), nullable=True),
            sa.Column('is_deleted', sa.Boolean(), nullable=False),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='analytics',
    )

    if not _has_table('mv_daily_sales', 'analytics'):
        op.create_table('mv_daily_sales',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('snapshot_date', sa.Date(), nullable=False),
            sa.Column('currency', sa.String(length=3), nullable=False),
            sa.Column('total_orders', sa.Integer(), nullable=False),
            sa.Column('total_revenue', sa.Numeric(precision=14, scale=2), nullable=False),
            sa.Column('total_gross_sales', sa.Numeric(precision=14, scale=2), nullable=False),
            sa.Column('total_net_sales', sa.Numeric(precision=14, scale=2), nullable=False),
            sa.Column('total_refunds', sa.Numeric(precision=14, scale=2), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
            sa.Column('created_by', sa.Integer(), nullable=True),
            sa.Column('updated_by', sa.Integer(), nullable=True),
            sa.Column('is_deleted', sa.Boolean(), nullable=False),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='analytics',
    )

    if not _has_table('mv_facet_counts', 'analytics'):
        op.create_table('mv_facet_counts',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('snapshot_date', sa.Date(), nullable=False),
            sa.Column('facet_type', sa.String(length=50), nullable=False),
            sa.Column('facet_value', sa.String(length=200), nullable=False),
            sa.Column('item_count', sa.Integer(), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
            sa.Column('created_by', sa.Integer(), nullable=True),
            sa.Column('updated_by', sa.Integer(), nullable=True),
            sa.Column('is_deleted', sa.Boolean(), nullable=False),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='analytics',
    )

    if not _has_table('mv_monthly_sales', 'analytics'):
        op.create_table('mv_monthly_sales',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('period_month', sa.Integer(), nullable=False),
            sa.Column('period_year', sa.Integer(), nullable=False),
            sa.Column('currency', sa.String(length=3), nullable=False),
            sa.Column('total_orders', sa.Integer(), nullable=False),
            sa.Column('total_revenue', sa.Numeric(precision=14, scale=2), nullable=False),
            sa.Column('total_gross_sales', sa.Numeric(precision=14, scale=2), nullable=False),
            sa.Column('total_net_sales', sa.Numeric(precision=14, scale=2), nullable=False),
            sa.Column('total_refunds', sa.Numeric(precision=14, scale=2), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
            sa.Column('created_by', sa.Integer(), nullable=True),
            sa.Column('updated_by', sa.Integer(), nullable=True),
            sa.Column('is_deleted', sa.Boolean(), nullable=False),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='analytics',
    )

    if not _has_table('news_articles', 'customer'):
        op.create_table('news_articles',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('source_id', sa.Integer(), nullable=True),
            sa.Column('external_id', sa.String(length=255), nullable=True),
            sa.Column('content_hash', sa.String(length=64), nullable=True),
            sa.Column('title', sa.String(length=300), nullable=False),
            sa.Column('summary', sa.Text(), nullable=True),
            sa.Column('content', sa.Text(), nullable=True),
            sa.Column('url', sa.String(length=500), nullable=True),
            sa.Column('image_url', sa.String(length=500), nullable=True),
            sa.Column('published_at', sa.DateTime(), nullable=True),
            sa.Column('ai_tags', sa.JSON(), nullable=True),
            sa.Column('is_published', sa.Boolean(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='customer',
    )

    if not _has_table('news_sources', 'communication'):
        op.create_table('news_sources',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('name', sa.String(length=100), nullable=False),
            sa.Column('url', sa.String(length=500), nullable=False),
            sa.Column('source_type', sa.String(length=20), nullable=True),
            sa.Column('api_key_required', sa.Boolean(), nullable=True),
            sa.Column('category', sa.String(length=50), nullable=True), schema='communication',
    )

    if not _has_table('newsletter_subscribers', 'communication'):
        op.create_table('newsletter_subscribers',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('email', sa.String(), nullable=False, unique=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True), schema='communication',
    )

    if not _has_table('normalized_webhook_events', 'analytics'):
        op.create_table('normalized_webhook_events',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('provider_code', sa.String(), nullable=False),
            sa.Column('gateway_event_id', sa.String(), nullable=False),
            sa.Column('event_type', sa.String(), nullable=False),
            sa.Column('status', sa.String(), nullable=False),
            sa.Column('environment', sa.String(), nullable=True),
            sa.Column('processed_at', sa.DateTime(), nullable=True),
            sa.Column('zozi_order_id', sa.Integer(), nullable=True),
            sa.Column('gateway_transaction_id', sa.String(), nullable=True),
            sa.Column('gateway_customer_id', sa.String(), nullable=True),
            sa.Column('gross_amount', sa.Numeric(precision=12, scale=2), nullable=True),
            sa.Column('currency', sa.String(length=3), nullable=True),
            sa.Column('gateway_fee', sa.Numeric(precision=12, scale=2), nullable=True),
            sa.Column('net_settlement', sa.Numeric(precision=12, scale=2), nullable=True),
            sa.Column('fraud_score', sa.Numeric(precision=5, scale=2), nullable=True),
            sa.Column('three_ds_status', sa.String(), nullable=True),
            sa.Column('avs_result', sa.String(), nullable=True),
            sa.Column('raw_payload', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='analytics',
    )

    if not _has_table('notifications', 'communication'):
        op.create_table('notifications',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('type', sa.String(), nullable=True),
            sa.Column('title', sa.String(), nullable=False),
            sa.Column('message', sa.Text(), nullable=False),
            sa.Column('channel', sa.String(), nullable=True),
            sa.Column('priority', sa.String(), nullable=True),
            sa.Column('is_read', sa.Boolean(), nullable=True),
            sa.Column('read_at', sa.DateTime(), nullable=True),
            sa.Column('link', sa.String(), nullable=True),
            sa.Column('template', sa.String(), nullable=True),
            sa.Column('variables', sa.JSON(), nullable=True),
            sa.Column('scheduled_at', sa.DateTime(), nullable=True),
            sa.Column('status', sa.String(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='communication',
    )

    if not _has_table('ocr_results', 'media'):
        op.create_table('ocr_results',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('document_verification_id', sa.Integer(), nullable=False, unique=True),
            sa.Column('extracted_text', sa.Text(), nullable=True),
            sa.Column('confidence_score', sa.String(), nullable=True),
            sa.Column('fields', sa.JSON(), nullable=True),
            sa.Column('processed_at', sa.DateTime(), nullable=True), schema='media',
    )

    if not _has_table('offboarding_cases', 'hr'):
        op.create_table('offboarding_cases',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('employee_id', sa.Integer(), nullable=False),
            sa.Column('employee_name', sa.String(length=200), nullable=True),
            sa.Column('reason', sa.String(length=50), nullable=False),
            sa.Column('status', sa.String(length=20), nullable=True),
            sa.Column('initiated_at', sa.DateTime(), nullable=True),
            sa.Column('completed_at', sa.DateTime(), nullable=True),
            sa.Column('notes', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='hr',
    )

    if not _has_table('offices', 'hr'):
        op.create_table('offices',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('name', sa.String(length=200), nullable=False),
            sa.Column('city', sa.String(length=200), nullable=True),
            sa.Column('latitude', sa.Float(), nullable=True),
            sa.Column('longitude', sa.Float(), nullable=True),
            sa.Column('geo_fence_radius_meters', sa.Integer(), nullable=True),
            sa.Column('address', sa.Text(), nullable=True),
            sa.Column('phone', sa.String(length=50), nullable=True),
            sa.Column('email', sa.String(length=200), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='hr',
    )

    if not _has_table('oman_delivery_zones', 'configuration'):
        op.create_table('oman_delivery_zones',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('zone_code', sa.String(length=20), nullable=False, unique=True),
            sa.Column('zone_name', sa.String(length=100), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('car_rate', sa.Numeric(precision=10, scale=2), nullable=True),
            sa.Column('van_rate', sa.Numeric(precision=10, scale=2), nullable=True),
            sa.Column('truck_rate', sa.Numeric(precision=10, scale=2), nullable=True),
            sa.Column('weight_surcharge_rate', sa.Numeric(precision=5, scale=4), nullable=True),
            sa.Column('weight_surcharge_threshold_kg', sa.Numeric(precision=10, scale=2), nullable=True),
            sa.Column('cities_json', sa.Text(), nullable=True),
            sa.Column('sort_order', sa.Integer(), nullable=True),
            sa.Column('is_active', sa.Boolean(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True), schema='configuration',
    )

    if not _has_table('onboarding_pipelines', 'hr'):
        op.create_table('onboarding_pipelines',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('pipeline_type', sa.String(), nullable=False),
            sa.Column('status', sa.String(), nullable=True),
            sa.Column('current_step', sa.Integer(), nullable=True),
            sa.Column('steps_data', sa.JSON(), nullable=True),
            sa.Column('started_at', sa.DateTime(), nullable=True),
            sa.Column('completed_at', sa.DateTime(), nullable=True), schema='hr',
    )

    if not _has_table('onboarding_steps', 'hr'):
        op.create_table('onboarding_steps',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('pipeline_id', sa.Integer(), nullable=False),
            sa.Column('step_name', sa.String(), nullable=False),
            sa.Column('status', sa.String(), nullable=True),
            sa.Column('data', sa.JSON(), nullable=True),
            sa.Column('started_at', sa.DateTime(), nullable=True),
            sa.Column('completed_at', sa.DateTime(), nullable=True), schema='hr',
    )

    if not _has_table('order_items', 'commerce'):
        op.create_table('order_items',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('order_id', sa.Integer(), nullable=False),
            sa.Column('product_id', sa.Integer(), nullable=False),
            sa.Column('variant_id', sa.Integer(), nullable=True),
            sa.Column('supplier_id', sa.Integer(), nullable=True),
            sa.Column('quantity', sa.Integer(), nullable=True),
            sa.Column('unit_price', sa.Numeric(precision=10, scale=2), nullable=True),
            sa.Column('price', sa.Numeric(precision=10, scale=2), nullable=True),
            sa.Column('total_price', sa.Numeric(precision=10, scale=2), nullable=True),
            sa.Column('product_name', sa.String(), nullable=True),
            sa.Column('product_image', sa.String(), nullable=True),
            sa.Column('selected_size', sa.String(), nullable=True),
            sa.Column('selected_color', sa.String(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='commerce',
    )

    if not _has_table('order_logistics_allocations', 'commerce'):
        op.create_table('order_logistics_allocations',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('order_id', sa.Integer(), nullable=False),
            sa.Column('supplier_id', sa.Integer(), nullable=False),
            sa.Column('shipment_id', sa.Integer(), nullable=True),
            sa.Column('partner_id', sa.Integer(), nullable=True),
            sa.Column('service_area_id', sa.Integer(), nullable=True),
            sa.Column('allocation_source', sa.String(), nullable=True),
            sa.Column('partner_name_snapshot', sa.String(), nullable=True),
            sa.Column('partner_code_snapshot', sa.String(), nullable=True),
            sa.Column('service_area_label_snapshot', sa.String(), nullable=True),
            sa.Column('destination_country', sa.String(), nullable=True),
            sa.Column('destination_city', sa.String(), nullable=True),
            sa.Column('shipping_amount', sa.Numeric(precision=10, scale=2), nullable=True),
            sa.Column('pickup_charge', sa.Numeric(precision=10, scale=2), nullable=True),
            sa.Column('dropoff_charge', sa.Numeric(precision=10, scale=2), nullable=True),
            sa.Column('accepted_vehicle_rule_id', sa.Integer(), nullable=True),
            sa.Column('accepted_vehicle_type', sa.String(), nullable=True),
            sa.Column('accepted_vehicle_multiplier', sa.Numeric(precision=5, scale=4), nullable=True),
            sa.Column('accepted_shipping_amount', sa.Numeric(precision=10, scale=2), nullable=True),
            sa.Column('accepted_pickup_charge', sa.Numeric(precision=10, scale=2), nullable=True),
            sa.Column('accepted_dropoff_charge', sa.Numeric(precision=10, scale=2), nullable=True),
            sa.Column('estimated_delivery_min', sa.Integer(), nullable=True),
            sa.Column('estimated_delivery_max', sa.Integer(), nullable=True),
            sa.Column('currency', sa.String(), nullable=True),
            sa.Column('pricing_breakdown_json', sa.Text(), nullable=True),
            sa.Column('accepted_pricing_breakdown_json', sa.Text(), nullable=True),
            sa.Column('country_code', sa.String(length=3), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='commerce',
    )

    if not _has_table('order_notifications', 'commerce'):
        op.create_table('order_notifications',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('order_id', sa.Integer(), nullable=False),
            sa.Column('notification_type', sa.String(length=50), nullable=False),
            sa.Column('is_read', sa.Boolean(), nullable=True),
            sa.Column('metadata_json', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True), schema='commerce',
    )

    if not _has_table('orders', 'commerce'):
        op.create_table('orders',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('order_number', sa.String(), nullable=True, unique=True),
            sa.Column('customer_id', sa.Integer(), nullable=True),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('status', sa.String(), nullable=True),
            sa.Column('status_label', sa.String(length=50), nullable=True),
            sa.Column('payment_status', sa.String(), nullable=True),
            sa.Column('payment_method', sa.String(), nullable=True),
            sa.Column('payment_provider', sa.String(), nullable=True),
            sa.Column('payment_intent_id', sa.String(), nullable=True),
            sa.Column('subtotal', sa.Numeric(precision=10, scale=2), nullable=True),
            sa.Column('subtotal_amount', sa.Numeric(precision=10, scale=2), nullable=True),
            sa.Column('shipping_fee', sa.Numeric(precision=10, scale=2), nullable=True),
            sa.Column('shipping_amount', sa.Numeric(precision=10, scale=2), nullable=True),
            sa.Column('tax_amount', sa.Numeric(precision=10, scale=2), nullable=True),
            sa.Column('vat_amount', sa.Numeric(precision=10, scale=2), nullable=True),
            sa.Column('discount_amount', sa.Numeric(precision=10, scale=2), nullable=True),
            sa.Column('total', sa.Numeric(precision=10, scale=2), nullable=True),
            sa.Column('total_amount', sa.Numeric(precision=10, scale=2), nullable=True),
            sa.Column('coupon_code', sa.String(), nullable=True),
            sa.Column('fraud_score', sa.Numeric(precision=5, scale=2), nullable=True),
            sa.Column('fraud_action', sa.String(), nullable=True),
            sa.Column('currency', sa.String(), nullable=True),
            sa.Column('shipping_address', sa.Text(), nullable=True),
            sa.Column('shipping_city', sa.String(), nullable=True),
            sa.Column('shipping_country', sa.String(), nullable=True),
            sa.Column('shipping_postal_code', sa.String(), nullable=True),
            sa.Column('customer_phone', sa.String(), nullable=True),
            sa.Column('delivery_location', sa.String(), nullable=True),
            sa.Column('delivery_note', sa.String(), nullable=True),
            sa.Column('tracking_number', sa.String(), nullable=True, unique=True),
            sa.Column('selected_partner_id', sa.Integer(), nullable=True),
            sa.Column('selected_service_area_id', sa.Integer(), nullable=True),
            sa.Column('estimated_delivery_min', sa.Integer(), nullable=True),
            sa.Column('estimated_delivery_max', sa.Integer(), nullable=True),
            sa.Column('payment_gateway_code', sa.String(), nullable=True),
            sa.Column('payment_gateway_fee_amount', sa.Numeric(precision=10, scale=2), nullable=True),
            sa.Column('payment_customer_total_amount', sa.Numeric(precision=10, scale=2), nullable=True),
            sa.Column('payment_gateway_fee_passed_to_customer', sa.Numeric(precision=10, scale=2), nullable=True),
            sa.Column('paid_at', sa.DateTime(), nullable=True),
            sa.Column('invoice_id', sa.Integer(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.Column('is_deleted', sa.Boolean(), nullable=True),
            sa.Column('deleted_at', sa.DateTime(), nullable=True),
            sa.Column('country_code', sa.String(length=3), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='commerce',
    )

    if not _has_table('org_units', 'hr'):
        op.create_table('org_units',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('name', sa.String(length=200), nullable=False),
            sa.Column('parent_id', sa.Integer(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='hr',
    )

    if not _has_table('outbox_events', 'configuration'):
        op.create_table('outbox_events',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('uuid', sa.String(length=36), nullable=False, unique=True),
            sa.Column('event_type', sa.String(length=100), nullable=False),
            sa.Column('aggregate_type', sa.String(length=50), nullable=False),
            sa.Column('aggregate_id', sa.Integer(), nullable=False),
            sa.Column('payload_json', sa.Text(), nullable=False),
            sa.Column('status', sa.String(length=20), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=True),
            sa.Column('published_at', sa.DateTime(), nullable=True),
            sa.Column('version', sa.Integer(), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
            sa.Column('is_deleted', sa.Boolean(), nullable=False),
            sa.Column('deleted_at', sa.DateTime(), nullable=True),
            sa.Column('delete_reason', sa.Text(), nullable=True),
            sa.Column('deleted_by_id', sa.Integer(), nullable=True),
            sa.Column('created_by_id', sa.Integer(), nullable=True),
            sa.Column('updated_by_id', sa.Integer(), nullable=True), schema='configuration',
    )

    if not _has_table('parcel_location_trackers', 'hr'):
        op.create_table('parcel_location_trackers',
                    sa.Column('country_code', sa.String(length=3), nullable=True),
            sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('parcel_id', sa.Integer(), nullable=False),
            sa.Column('longitude', sa.Float(), nullable=True),
            sa.Column('location_name', sa.String(length=200), nullable=True),
            sa.Column('timestamp_at', sa.DateTime(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='hr',
    )

    if not _has_table('password_reset_tokens', 'security'):
        op.create_table('password_reset_tokens',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=True),
            sa.Column('token', sa.String(), nullable=True, unique=True),
            sa.Column('expires_at', sa.DateTime(), nullable=False),
            sa.Column('used', sa.Boolean(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='security',
    )

    if not _has_table('payment_gateway_connections', 'treasury'):
        op.create_table('payment_gateway_connections',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('provider_code', sa.String(length=100), nullable=False),
            sa.Column('gateway_name', sa.String(length=100), nullable=False),
            sa.Column('fee_config', sa.JSON(), nullable=True),
            sa.Column('supported_methods', sa.JSON(), nullable=True),
            sa.Column('last_sync_at', sa.DateTime(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.Column('provider_kind', sa.String(length=20), nullable=False),
            sa.Column('display_name', sa.String(length=120), nullable=False),
            sa.Column('is_enabled', sa.Boolean(), nullable=True),
            sa.Column('supports_customer_checkout', sa.Boolean(), nullable=True),
            sa.Column('supports_payouts', sa.Boolean(), nullable=True),
            sa.Column('mode', sa.String(length=20), nullable=False),
            sa.Column('public_key', sa.String(length=500), nullable=True),
            sa.Column('secret_key', sa.String(length=1000), nullable=True),
            sa.Column('webhook_secret', sa.String(length=1000), nullable=True),
            sa.Column('merchant_id', sa.String(length=255), nullable=True),
            sa.Column('api_base_url', sa.String(length=500), nullable=True),
            sa.Column('webhook_url', sa.String(length=500), nullable=True),
            sa.Column('test_url', sa.String(length=500), nullable=True),
            sa.Column('settlement_cycle', sa.String(length=50), nullable=True),
            sa.Column('supported_currencies_json', sa.Text(), nullable=True),
            sa.Column('extra_config_json', sa.Text(), nullable=True),
            sa.Column('notes', sa.Text(), nullable=True),
            sa.Column('fee_percent', sa.Numeric(precision=8, scale=4), nullable=False),
            sa.Column('fixed_fee_amount', sa.Numeric(precision=12, scale=2), nullable=False),
            sa.Column('payout_fee_percent', sa.Numeric(precision=8, scale=4), nullable=False),
            sa.Column('payout_fixed_fee_amount', sa.Numeric(precision=12, scale=2), nullable=False),
            sa.Column('pass_fee_to_customer', sa.Boolean(), nullable=True),
            sa.Column('test_status', sa.String(length=20), nullable=False),
            sa.Column('test_message', sa.String(length=500), nullable=True),
            sa.Column('last_tested_at', sa.DateTime(), nullable=True),
            sa.Column('updated_by', sa.Integer(), nullable=True),
            sa.Column('adapter_supported', sa.Boolean(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='treasury',
    )

    op.execute('DROP TABLE IF EXISTS "hr"."payment_orchestrator_syncs"')
    if not _has_table('payment_orchestrator_sync', 'hr'):
        op.create_table('payment_orchestrator_sync',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('country_code', sa.String(length=10), nullable=False),
            sa.Column('gateway_id', sa.String(length=60), nullable=False),
            sa.Column('gateway_name', sa.String(length=100), nullable=True),
            sa.Column('environment', sa.String(length=20), nullable=True),
            sa.Column('is_active', sa.Boolean(), nullable=True),
            sa.Column('fee_percent', sa.Numeric(precision=8, scale=4), nullable=True),
            sa.Column('fee_fixed', sa.Numeric(precision=12, scale=2), nullable=True),
            sa.Column('supported_payment_methods', sa.Text(), nullable=True),
            sa.Column('last_sync_at', sa.DateTime(), nullable=True),
            sa.Column('status', sa.String(length=20), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True), schema='hr',
        )
        op.create_index('ix_pos_status', 'payment_orchestrator_sync', ['status'], schema='hr')
        op.create_unique_constraint('uq_pos_country_gateway', 'payment_orchestrator_sync', ['country_code', 'gateway_id'], schema='hr')

    if not _has_table('payment_provider_configs', 'treasury'):
        op.create_table('payment_provider_configs',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('provider_name', sa.String(), nullable=False),
            sa.Column('config', sa.JSON(), nullable=True),
            sa.Column('is_active', sa.Boolean(), nullable=True),
            sa.Column('updated_by', sa.Integer(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.Column('country_code', sa.String(length=3), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='treasury',
    )

    if not _has_table('payment_reconciliation_runs', 'treasury'):
        op.create_table('payment_reconciliation_runs',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('run_date', sa.DateTime(), nullable=False),
            sa.Column('total_amount', sa.Numeric(precision=15, scale=2), nullable=True),
            sa.Column('reconciled_count', sa.Integer(), nullable=True),
            sa.Column('unmatched_count', sa.Integer(), nullable=True),
            sa.Column('processed_count', sa.Integer(), nullable=True),
            sa.Column('stale_pending_orders', sa.Integer(), nullable=True),
            sa.Column('recent_webhook_count', sa.Integer(), nullable=True),
            sa.Column('result_json', sa.Text(), nullable=True),
            sa.Column('started_at', sa.DateTime(), nullable=True),
            sa.Column('completed_at', sa.DateTime(), nullable=True),
            sa.Column('status', sa.String(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='treasury',
    )

    if not _has_table('payments', 'finance'):
        op.create_table('payments',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('order_id', sa.Integer(), nullable=False),
            sa.Column('amount', sa.Numeric(precision=10, scale=2), nullable=False),
            sa.Column('payment_method', sa.String(), nullable=False),
            sa.Column('provider', sa.String(), nullable=True),
            sa.Column('status', sa.String(), nullable=True),
            sa.Column('intent_id', sa.String(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('layout_json', sa.Text(), nullable=True),
            sa.Column('country_code', sa.String(length=3), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='finance',
    )

    if not _has_table('payout_batch_items', 'treasury'):
        op.create_table('payout_batch_items',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('batch_id', sa.Integer(), nullable=False),
            sa.Column('entity_type', sa.String(length=20), nullable=False),
            sa.Column('entity_id', sa.Integer(), nullable=False),
            sa.Column('amount', sa.Numeric(precision=16, scale=4), nullable=False),
            sa.Column('currency', sa.String(length=3), nullable=True),
            sa.Column('reference', sa.String(length=100), nullable=True),
            sa.Column('status', sa.String(length=20), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='treasury',
    )

    if not _has_table('payout_batches', 'treasury'):
        op.create_table('payout_batches',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('batch_number', sa.String(length=50), nullable=False, unique=True),
            sa.Column('total_amount', sa.Numeric(precision=16, scale=4), nullable=True),
            sa.Column('item_count', sa.Integer(), nullable=True),
            sa.Column('status', sa.String(length=20), nullable=True),
            sa.Column('created_by', sa.Integer(), nullable=False),
            sa.Column('approved_by', sa.Integer(), nullable=True),
            sa.Column('dispatched_at', sa.DateTime(), nullable=True),
            sa.Column('settled_at', sa.DateTime(), nullable=True),
            sa.Column('notes', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='treasury',
    )

    if not _has_table('payout_rule_categories', 'country'):
        op.create_table('payout_rule_categories',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('category_slug', sa.String(), nullable=False),
            sa.Column('payout_rate', sa.Numeric(precision=5, scale=4), nullable=False),
            sa.Column('min_amount', sa.Numeric(precision=12, scale=2), nullable=True),
            sa.Column('max_amount', sa.Numeric(precision=12, scale=2), nullable=True),
            sa.Column('is_active', sa.Boolean(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True), schema='country',
    )

    if not _has_table('payout_rule_products', 'country'):
        op.create_table('payout_rule_products',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('product_id', sa.Integer(), nullable=False),
            sa.Column('payout_rate', sa.Numeric(precision=5, scale=4), nullable=False),
            sa.Column('min_amount', sa.Numeric(precision=12, scale=2), nullable=True),
            sa.Column('max_amount', sa.Numeric(precision=12, scale=2), nullable=True),
            sa.Column('is_active', sa.Boolean(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True), schema='country',
    )

    if not _has_table('payout_rules', 'treasury'):
        op.create_table('payout_rules',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('min_amount', sa.Numeric(precision=12, scale=2), nullable=True),
            sa.Column('max_amount', sa.Numeric(precision=12, scale=2), nullable=True),
            sa.Column('fixed_fee', sa.Numeric(precision=12, scale=2), nullable=True),
            sa.Column('percent_fee', sa.Numeric(precision=5, scale=4), nullable=True),
            sa.Column('is_active', sa.Boolean(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True), schema='treasury',
    )

    if not _has_table('payouts', 'treasury'):
        op.create_table('payouts',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('batch_number', sa.String(length=50), nullable=True),
            sa.Column('order_id', sa.Integer(), nullable=True),
            sa.Column('supplier_id', sa.Integer(), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=True),
            sa.Column('amount', sa.Numeric(precision=12, scale=2), nullable=False),
            sa.Column('currency', sa.String(length=3), nullable=True),
            sa.Column('method', sa.String(), nullable=False),
            sa.Column('status', sa.String(), nullable=True),
            sa.Column('reference_id', sa.String(), nullable=True),
            sa.Column('reference', sa.String(), nullable=True),
            sa.Column('provider', sa.String(), nullable=True),
            sa.Column('provider_recipient_id', sa.String(), nullable=True),
            sa.Column('provider_transfer_id', sa.String(), nullable=True),
            sa.Column('provider_status', sa.String(), nullable=True),
            sa.Column('notes', sa.Text(), nullable=True),
            sa.Column('processed_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='treasury',
    )

    if not _has_table('payroll_records', 'finance'):
        op.create_table('payroll_records',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('employee_id', sa.Integer(), nullable=True),
            sa.Column('period', sa.String(length=20), nullable=True),
            sa.Column('net_pay', sa.Numeric(precision=18, scale=2), nullable=True),
            sa.Column('gross_pay', sa.Numeric(precision=18, scale=2), nullable=True),
            sa.Column('status', sa.String(length=20), nullable=True),
            sa.Column('processed_at', sa.DateTime(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='finance',
    )

    if not _has_table('pending_journal_entries', 'finance'):
        op.create_table('pending_journal_entries',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('lines_json', sa.Text(), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('source', sa.String(length=50), nullable=True),
            sa.Column('amount_threshold_triggered', sa.Boolean(), nullable=True),
            sa.Column('status', sa.String(length=20), nullable=True),
            sa.Column('created_by', sa.Integer(), nullable=False),
            sa.Column('approved_by', sa.Integer(), nullable=True),
            sa.Column('rejected_by', sa.Integer(), nullable=True),
            sa.Column('rejection_reason', sa.Text(), nullable=True),
            sa.Column('approved_at', sa.DateTime(), nullable=True),
            sa.Column('journal_entry_id', sa.Integer(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='finance',
    )

    if not _has_table('permission_audit_log', 'security'):
        op.create_table('permission_audit_log',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('actor_id', sa.Integer(), nullable=False),
            sa.Column('action', sa.String(length=50), nullable=False),
            sa.Column('target_user_id', sa.Integer(), nullable=True),
            sa.Column('target_role', sa.String(length=80), nullable=True),
            sa.Column('permission_id', sa.Integer(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='security',
    )

    if not _has_table('permission_categories', 'security'):
        op.create_table('permission_categories',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('name', sa.String(length=100), nullable=False, unique=True),
            sa.Column('slug', sa.String(length=100), nullable=False, unique=True),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('icon', sa.String(length=50), nullable=True),
            sa.Column('sort_order', sa.Integer(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='security',
    )

    if not _has_table('permissions', 'security'):
        op.create_table('permissions',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('category_id', sa.Integer(), nullable=False),
            sa.Column('name', sa.String(length=150), nullable=False),
            sa.Column('slug', sa.String(length=150), nullable=False, unique=True),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('scope', sa.String(length=20), nullable=False, server_default=sa.text('global')),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='security',
    )

    if not _has_table('physical_id_cards', 'hr'):
        op.create_table('physical_id_cards',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('employee_id', sa.Integer(), nullable=False, unique=True),
            sa.Column('card_number', sa.String(length=50), nullable=False, unique=True),
            sa.Column('issued_at', sa.DateTime(), nullable=True),
            sa.Column('expires_at', sa.DateTime(), nullable=True),
            sa.Column('is_revoked', sa.Boolean(), nullable=True),
            sa.Column('revoked_at', sa.DateTime(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='hr',
    )

    if not _has_table('predictive_simulations', 'ai'):
        op.create_table('predictive_simulations',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('simulation_type', sa.String(length=50), nullable=False),
            sa.Column('parameters_json', sa.Text(), nullable=False),
            sa.Column('result_json', sa.Text(), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=True), schema='ai',
    )

    if not _has_table('processed_webhook_events', 'analytics'):
        op.create_table('processed_webhook_events',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('processor', sa.String(), nullable=False),
            sa.Column('event_id', sa.String(), nullable=False),
            sa.Column('payload_hash', sa.String(), nullable=False),
            sa.Column('processed_at', sa.DateTime(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='analytics',
    )

    if not _has_table('product_commission_overrides', 'commerce'):
        op.create_table('product_commission_overrides',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('product_id', sa.Integer(), nullable=False),
            sa.Column('supplier_id', sa.Integer(), nullable=False),
            sa.Column('rate_percent', sa.Numeric(precision=5, scale=2), nullable=False),
            sa.Column('set_by_admin_id', sa.Integer(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='commerce',
    )

    if not _has_table('product_filter_metadata', 'commerce'):
        op.create_table('product_filter_metadata',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('category_id', sa.Integer(), nullable=True),
            sa.Column('filter_name', sa.String(length=100), nullable=False),
            sa.Column('filter_type', sa.String(length=50), nullable=False),
            sa.Column('display_order', sa.Integer(), nullable=False, server_default=sa.text('0')),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='commerce',
    )

    if not _has_table('product_filter_options', 'commerce'):
        op.create_table('product_filter_options',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('filter_metadata_id', sa.Integer(), nullable=False),
            sa.Column('option_value', sa.String(length=255), nullable=False),
            sa.Column('option_display_name', sa.String(length=255), nullable=False),
            sa.Column('product_count', sa.Integer(), nullable=False, server_default=sa.text('0')),
            sa.Column('sort_order', sa.Integer(), nullable=False, server_default=sa.text('0')),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='commerce',
    )

    if not _has_table('product_images', 'commerce'):
        op.create_table('product_images',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('product_id', sa.Integer(), nullable=False),
            sa.Column('image_url', sa.String(length=500), nullable=False),
            sa.Column('alt_text', sa.String(length=255), nullable=True),
            sa.Column('sort_order', sa.Integer(), nullable=True),
            sa.Column('is_primary', sa.Boolean(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True), schema='commerce',
    )

    if not _has_table('product_variants', 'commerce'):
        op.create_table('product_variants',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('product_id', sa.Integer(), nullable=False),
            sa.Column('sku', sa.String(), nullable=True, unique=True),
            sa.Column('title', sa.String(), nullable=True),
            sa.Column('size', sa.String(), nullable=True),
            sa.Column('color', sa.String(), nullable=True),
            sa.Column('material', sa.String(), nullable=True),
            sa.Column('pattern', sa.String(), nullable=True),
            sa.Column('gender', sa.String(), nullable=True),
            sa.Column('barcode', sa.String(), nullable=True, unique=True),
            sa.Column('product_code', sa.String(), nullable=True),
            sa.Column('price', sa.Numeric(precision=10, scale=2), nullable=True),
            sa.Column('stock', sa.Integer(), nullable=True),
            sa.Column('media_url', sa.String(), nullable=True),
            sa.Column('attributes_json', postgresql.JSONB(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.Column('variant_key', sa.String(length=64), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='commerce',
    )

    if not _has_table('product_verifications', 'commerce'):
        op.create_table('product_verifications',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('product_id', sa.Integer(), nullable=False),
            sa.Column('status', sa.String(), nullable=True),
            sa.Column('verified_by', sa.Integer(), nullable=True),
            sa.Column('shipment_id', sa.Integer(), nullable=True),
            sa.Column('verification_type', sa.String(), nullable=True),
            sa.Column('result', sa.String(), nullable=True),
            sa.Column('expected_specs', sa.Text(), nullable=True),
            sa.Column('actual_specs', sa.Text(), nullable=True),
            sa.Column('discrepancies', sa.Text(), nullable=True),
            sa.Column('scan_code', sa.String(), nullable=True),
            sa.Column('image_urls', sa.Text(), nullable=True),
            sa.Column('notes', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('order_id', sa.Integer(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='commerce',
    )

    if not _has_table('product_videos', 'media'):
        op.create_table('product_videos',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('product_id', sa.Integer(), nullable=False),
            sa.Column('video_url', sa.String(length=500), nullable=False),
            sa.Column('thumbnail_url', sa.String(length=500), nullable=True),
            sa.Column('duration_seconds', sa.Integer(), nullable=True),
            sa.Column('video_type', sa.String(length=50), nullable=True),
            sa.Column('title', sa.String(length=255), nullable=True),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('views_count', sa.Integer(), nullable=True),
            sa.Column('is_featured', sa.Boolean(), nullable=True),
            sa.Column('upload_status', sa.String(length=50), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='media',
    )

    if not _has_table('products', 'commerce'):
        op.create_table('products',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('name', sa.String(), nullable=False),
            sa.Column('slug', sa.String(), nullable=True, unique=True),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('short_description', sa.Text(), nullable=True),
            sa.Column('ai_description', sa.Text(), nullable=True),
            sa.Column('sku', sa.String(), nullable=True, unique=True),
            sa.Column('barcode', sa.String(), nullable=True, unique=True),
            sa.Column('price', sa.Numeric(precision=10, scale=2), nullable=False),
            sa.Column('compare_price', sa.Numeric(precision=10, scale=2), nullable=True),
            sa.Column('cost_price', sa.Numeric(precision=10, scale=2), nullable=True),
            sa.Column('stock', sa.Integer(), nullable=True),
            sa.Column('low_stock_threshold', sa.Integer(), nullable=True),
            sa.Column('weight', sa.Numeric(precision=10, scale=2), nullable=True),
            sa.Column('dimensions', sa.String(), nullable=True),
            sa.Column('materials', postgresql.JSONB(), nullable=True),
            sa.Column('image_url', sa.String(), nullable=True),
            sa.Column('images', postgresql.JSONB(), nullable=True),
            sa.Column('category', sa.String(), nullable=True),
            sa.Column('category_id', sa.Integer(), nullable=True),
            sa.Column('country_code', sa.String(length=3), nullable=True),
            sa.Column('tags', postgresql.JSONB(), nullable=True),
            sa.Column('attributes', postgresql.JSONB(), nullable=True),
            sa.Column('supplier_id', sa.Integer(), nullable=True),
            sa.Column('is_digital', sa.Boolean(), nullable=True),
            sa.Column('is_verified', sa.Boolean(), nullable=True),
            sa.Column('moderation_status', sa.String(), nullable=True),
            sa.Column('brand', sa.String(), nullable=True),
            sa.Column('color', sa.String(), nullable=True),
            sa.Column('sizes', sa.JSON(), nullable=True),
            sa.Column('rating', sa.Numeric(precision=3, scale=2), nullable=True),
            sa.Column('sales_count', sa.Integer(), nullable=True),
            sa.Column('meta_title', sa.String(), nullable=True),
            sa.Column('meta_description', sa.Text(), nullable=True),
            sa.Column('is_approved', sa.Boolean(), nullable=True),
            sa.Column('is_deleted', sa.Boolean(), nullable=True),
            sa.Column('is_featured', sa.Boolean(), nullable=True),
            sa.Column('discount_starts_at', sa.DateTime(), nullable=True),
            sa.Column('discount_ends_at', sa.DateTime(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.Column('filter_attributes', postgresql.JSONB(), nullable=True),
            sa.Column('search_vector', sa.Text(), nullable=True),
            sa.Column('video_count', sa.Integer(), nullable=True),
            sa.Column('variant_axes', postgresql.JSONB(), nullable=True),
            sa.Column('bg_preset', sa.String(), nullable=True),
            sa.Column('visibility_regions', sa.Text(), nullable=True),
            sa.Column('slug_hash', sa.String(length=32), nullable=True, unique=True),
            sa.Column('subcategory', sa.String(), nullable=True),
            sa.Column('return_window_days', sa.Integer(), nullable=True),
            sa.Column('is_new', sa.Boolean(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='commerce',
    )

    if not _has_table('promotion_engine_configs', 'commerce'):
        op.create_table('promotion_engine_configs',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('is_engine_enabled', sa.Boolean(), nullable=True),
            sa.Column('allow_product_coupons', sa.Boolean(), nullable=True),
            sa.Column('allow_category_coupons', sa.Boolean(), nullable=True),
            sa.Column('allow_order_tier_discounts', sa.Boolean(), nullable=True),
            sa.Column('allow_referral_rewards', sa.Boolean(), nullable=True),
            sa.Column('allow_supplier_promotions', sa.Boolean(), nullable=True),
            sa.Column('allow_global_coupons', sa.Boolean(), nullable=True),
            sa.Column('stacking_mode', sa.String(), nullable=True),
            sa.Column('max_combined_discount_percent', sa.Numeric(precision=5, scale=2), nullable=True),
            sa.Column('max_combined_discount_amount', sa.Numeric(precision=12, scale=3), nullable=True),
            sa.Column('is_show_savings_line_item', sa.Boolean(), nullable=True),
            sa.Column('is_tier_discount_visible', sa.Boolean(), nullable=True),
            sa.Column('points_per_omr', sa.Integer(), nullable=True),
            sa.Column('referral_referrer_points', sa.Integer(), nullable=True),
            sa.Column('referral_referee_points', sa.Integer(), nullable=True),
            sa.Column('points_expiry_months', sa.Integer(), nullable=True),
            sa.Column('referral_monthly_cap', sa.Integer(), nullable=True),
            sa.Column('referral_verification_delay_days', sa.Integer(), nullable=True),
            sa.Column('min_points_redeem', sa.Integer(), nullable=True),
            sa.Column('allow_partial_points_redemption', sa.Boolean(), nullable=True),
            sa.Column('updated_by', sa.Integer(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('country_code', sa.String(length=3), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='commerce',
    )

    if not _has_table('promotion_ledger_entries', 'commerce'):
        op.create_table('promotion_ledger_entries',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('promotion_id', sa.Integer(), nullable=True),
            sa.Column('user_id', sa.Integer(), nullable=True),
            sa.Column('amount', sa.Numeric(precision=12, scale=2), nullable=False),
            sa.Column('entry_type', sa.String(), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='commerce',
    )

    if not _has_table('promotion_order_tiers', 'commerce'):
        op.create_table('promotion_order_tiers',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('promotion_id', sa.Integer(), nullable=True),
            sa.Column('tier_name', sa.String(), nullable=True),
            sa.Column('min_order_amount', sa.Numeric(precision=10, scale=2), nullable=False),
            sa.Column('max_order_amount', sa.Numeric(precision=10, scale=2), nullable=True),
            sa.Column('discount_type', sa.String(), nullable=False),
            sa.Column('discount_amount', sa.Numeric(precision=10, scale=2), nullable=True),
            sa.Column('discount_value', sa.Numeric(precision=10, scale=2), nullable=True),
            sa.Column('is_stacking_allowed', sa.Boolean(), nullable=True),
            sa.Column('sort_order', sa.Integer(), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=True),
            sa.Column('country_code', sa.String(length=3), nullable=True),
            sa.Column('updated_by', sa.Integer(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='commerce',
    )

    if not _has_table('proxy_call_logs', 'communication'):
        op.create_table('proxy_call_logs',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('channel_id', sa.Integer(), nullable=False),
            sa.Column('caller_id', sa.Integer(), nullable=False),
            sa.Column('callee_id', sa.Integer(), nullable=False),
            sa.Column('direction', sa.String(), nullable=False),
            sa.Column('duration_seconds', sa.Integer(), nullable=True),
            sa.Column('call_recording_url', sa.String(), nullable=True),
            sa.Column('is_recorded', sa.Boolean(), nullable=True),
            sa.Column('started_at', sa.DateTime(), nullable=True),
            sa.Column('ended_at', sa.DateTime(), nullable=True), schema='communication',
    )

    if not _has_table('proxy_channels', 'communication'):
        op.create_table('proxy_channels',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('entity_type', sa.String(), nullable=False),
            sa.Column('entity_id', sa.Integer(), nullable=False),
            sa.Column('proxy_phone', sa.String(), nullable=False, unique=True),
            sa.Column('proxy_email', sa.String(), nullable=False, unique=True),
            sa.Column('participants', sa.JSON(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True), schema='communication',
    )

    if not _has_table('proxy_messages', 'communication'):
        op.create_table('proxy_messages',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('session_id', sa.Integer(), nullable=False),
            sa.Column('sender_id', sa.Integer(), nullable=False),
            sa.Column('recipient_id', sa.Integer(), nullable=False),
            sa.Column('message_type', sa.String(), nullable=True),
            sa.Column('content', sa.Text(), nullable=False),
            sa.Column('is_masked', sa.Boolean(), nullable=True),
            sa.Column('read_at', sa.DateTime(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True), schema='communication',
    )

    if not _has_table('proxy_sessions', 'communication'):
        op.create_table('proxy_sessions',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('channel_id', sa.Integer(), nullable=False),
            sa.Column('participant_one_id', sa.Integer(), nullable=False),
            sa.Column('participant_two_id', sa.Integer(), nullable=False),
            sa.Column('started_at', sa.DateTime(), nullable=True),
            sa.Column('ended_at', sa.DateTime(), nullable=True),
            sa.Column('is_encrypted', sa.Boolean(), nullable=True),
            sa.Column('session_metadata', sa.JSON(), nullable=True), schema='communication',
    )

    if not _has_table('purchase_order_lines', 'trading'):
        op.create_table('purchase_order_lines',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('po_id', sa.Integer(), nullable=False),
            sa.Column('product_id', sa.Integer(), nullable=True),
            sa.Column('product_name', sa.String(length=255), nullable=True),
            sa.Column('sku', sa.String(length=100), nullable=True),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('quantity_ordered', sa.Numeric(precision=14, scale=4), nullable=False),
            sa.Column('quantity_received', sa.Numeric(precision=14, scale=4), nullable=True),
            sa.Column('unit_price', sa.Numeric(precision=14, scale=4), nullable=False),
            sa.Column('discount_percent', sa.Numeric(precision=5, scale=2), nullable=True),
            sa.Column('discount_amount', sa.Numeric(precision=14, scale=2), nullable=True),
            sa.Column('tax_rate', sa.Numeric(precision=5, scale=2), nullable=True),
            sa.Column('tax_amount', sa.Numeric(precision=14, scale=2), nullable=True),
            sa.Column('line_total', sa.Numeric(precision=14, scale=2), nullable=True),
            sa.Column('weight', sa.Numeric(precision=10, scale=3), nullable=True),
            sa.Column('volume', sa.Numeric(precision=10, scale=3), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='trading',
    )

    if not _has_table('purchase_orders', 'trading'):
        op.create_table('purchase_orders',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('po_number', sa.String(length=80), nullable=True, unique=True),
            sa.Column('supplier_id', sa.Integer(), nullable=False),
            sa.Column('vendor_id', sa.Integer(), nullable=True),
            sa.Column('supplier_name', sa.String(length=255), nullable=True),
            sa.Column('order_date', sa.DateTime(), nullable=False),
            sa.Column('expected_delivery_date', sa.DateTime(), nullable=True),
            sa.Column('delivery_date', sa.DateTime(), nullable=True),
            sa.Column('warehouse_id', sa.Integer(), nullable=True),
            sa.Column('currency', sa.String(length=3), nullable=True),
            sa.Column('subtotal', sa.Numeric(precision=14, scale=2), nullable=True),
            sa.Column('discount_total', sa.Numeric(precision=14, scale=2), nullable=True),
            sa.Column('tax_total', sa.Numeric(precision=14, scale=2), nullable=True),
            sa.Column('grand_total', sa.Numeric(precision=14, scale=2), nullable=True),
            sa.Column('total_amount', sa.Numeric(precision=14, scale=2), nullable=True),
            sa.Column('notes', sa.Text(), nullable=True),
            sa.Column('terms', sa.Text(), nullable=True),
            sa.Column('shipping_address', sa.Text(), nullable=True),
            sa.Column('status', sa.String(length=50), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('country_code', sa.String(length=3), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='trading',
    )

    if not _has_table('push_notification_tokens', 'communication'):
        op.create_table('push_notification_tokens',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('token', sa.String(), nullable=False),
            sa.Column('device_type', sa.String(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='communication',
    )

    if not _has_table('recurring_templates', 'finance'):
        op.create_table('recurring_templates',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('name', sa.String(length=200), nullable=False),
            sa.Column('frequency', sa.String(length=20), nullable=True),
            sa.Column('next_run_date', sa.DateTime(), nullable=True),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('lines', sa.JSON(), nullable=False),
            sa.Column('currency', sa.String(length=3), nullable=True),
            sa.Column('created_by', sa.Integer(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='finance',
    )

    if not _has_table('referral_point_events', 'customer'):
        op.create_table('referral_point_events',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('event_type', sa.String(length=40), nullable=False),
            sa.Column('points', sa.Integer(), nullable=False),
            sa.Column('referred_user_id', sa.Integer(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='customer',
    )

    if not _has_table('referrals', 'customer'):
        op.create_table('referrals',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('referrer_id', sa.Integer(), nullable=False),
            sa.Column('referred_id', sa.Integer(), nullable=False, unique=True),
            sa.Column('referral_code', sa.String(length=40), nullable=True),
            sa.Column('status', sa.String(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='customer',
    )

    if not _has_table('refund_ledger', 'finance'):
        op.create_table('refund_ledger',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('order_id', sa.Integer(), nullable=False),
            sa.Column('return_request_id', sa.Integer(), nullable=True),
            sa.Column('ledger_id', sa.Integer(), nullable=True),
            sa.Column('bank_transaction_id', sa.Integer(), nullable=True),
            sa.Column('reason', sa.Text(), nullable=True),
            sa.Column('refund_reason', sa.Text(), nullable=True),
            sa.Column('refund_method', sa.String(), nullable=True),
            sa.Column('customer_refund_amount', sa.Numeric(precision=12, scale=2), nullable=True),
            sa.Column('supplier_reversal', sa.Numeric(precision=12, scale=2), nullable=True),
            sa.Column('logistics_reversal', sa.Numeric(precision=12, scale=2), nullable=True),
            sa.Column('delivery_fee_reversal', sa.Numeric(precision=12, scale=2), nullable=True),
            sa.Column('commission_reversal', sa.Numeric(precision=12, scale=2), nullable=True),
            sa.Column('vat_adjustment', sa.Numeric(precision=12, scale=2), nullable=True),
            sa.Column('vat_reversal', sa.Numeric(precision=12, scale=2), nullable=True),
            sa.Column('performed_by', sa.Integer(), nullable=True),
            sa.Column('processed_at', sa.DateTime(), nullable=True),
            sa.Column('currency', sa.String(length=3), nullable=True),
            sa.Column('status', sa.String(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('deleted_at', sa.DateTime(), nullable=True),
            sa.Column('deleted_by', sa.Integer(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='finance',
    )

    if not _has_table('retention_job_runs', 'audit'):
        op.create_table('retention_job_runs',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('job_type', sa.String(length=50), nullable=True),
            sa.Column('target_table', sa.String(length=100), nullable=True),
            sa.Column('target_name', sa.String(length=100), nullable=True),
            sa.Column('cutoff_days', sa.Integer(), nullable=True),
            sa.Column('records_deleted', sa.Integer(), nullable=True),
            sa.Column('archived_count', sa.Integer(), nullable=True),
            sa.Column('deleted_count', sa.Integer(), nullable=True),
            sa.Column('artifact_path', sa.String(), nullable=True),
            sa.Column('result_json', sa.Text(), nullable=True),
            sa.Column('started_at', sa.DateTime(), nullable=True),
            sa.Column('completed_at', sa.DateTime(), nullable=True),
            sa.Column('status', sa.String(length=20), nullable=True),
            sa.Column('error_message', sa.Text(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='audit',
    )

    if not _has_table('return_abuse_patterns', 'commerce'):
        op.create_table('return_abuse_patterns',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('abuse_type', sa.String(length=50), nullable=False),
            sa.Column('occurrence_count', sa.Integer(), nullable=True),
            sa.Column('first_occurrence', sa.DateTime(), nullable=True),
            sa.Column('last_occurrence', sa.DateTime(), nullable=True),
            sa.Column('is_blocked', sa.Boolean(), nullable=True), schema='commerce',
    )

    if not _has_table('return_requests', 'commerce'):
        op.create_table('return_requests',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('order_id', sa.Integer(), nullable=False),
            sa.Column('order_item_id', sa.Integer(), nullable=True),
            sa.Column('customer_id', sa.Integer(), nullable=True),
            sa.Column('intent', sa.String(), nullable=True),
            sa.Column('reason', sa.String(), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('details', sa.Text(), nullable=True),
            sa.Column('supplier_review_state', sa.Text(), nullable=True),
            sa.Column('images', sa.Text(), nullable=True),
            sa.Column('status', sa.String(), nullable=True),
            sa.Column('refund_amount', sa.Numeric(precision=10, scale=2), nullable=True),
            sa.Column('items', sa.Text(), nullable=True),
            sa.Column('return_window_days', sa.Integer(), nullable=True),
            sa.Column('delivered_at', sa.DateTime(), nullable=True),
            sa.Column('return_deadline_at', sa.DateTime(), nullable=True),
            sa.Column('resolution_notes', sa.Text(), nullable=True),
            sa.Column('country_code', sa.String(length=3), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='commerce',
    )

    if not _has_table('reviews', 'commerce'):
        op.create_table('reviews',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('product_id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('rating', sa.Integer(), nullable=False),
            sa.Column('title', sa.String(), nullable=True),
            sa.Column('comment', sa.Text(), nullable=True),
            sa.Column('image_url', sa.String(), nullable=True),
            sa.Column('is_approved', sa.Boolean(), nullable=True),
            sa.Column('is_deleted', sa.Boolean(), nullable=True),
            sa.Column('is_verified_purchase', sa.Boolean(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='commerce',
    )

    if not _has_table('revoked_tokens', 'security'):
        op.create_table('revoked_tokens',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('jti', sa.String(length=64), nullable=False, unique=True),
            sa.Column('user_id', sa.Integer(), nullable=True),
            sa.Column('expires_at', sa.DateTime(), nullable=False),
            sa.Column('revoked_at', sa.DateTime(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='security',
    )

    if not _has_table('role_permission_assignments', 'security'):
        op.create_table('role_permission_assignments',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('role_name', sa.String(length=80), nullable=False),
            sa.Column('permission_id', sa.Integer(), nullable=False),
            sa.Column('is_granted', sa.Boolean(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='security',
    )

    if not _has_table('role_permission_settings', 'security'):
        op.create_table('role_permission_settings',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('role', sa.String(), nullable=False),
            sa.Column('permissions_json', sa.JSON(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='security',
    )

    if not _has_table('sales_order_lines', 'trading'):
        op.create_table('sales_order_lines',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('so_id', sa.Integer(), nullable=False),
            sa.Column('product_id', sa.Integer(), nullable=True),
            sa.Column('product_name', sa.String(length=255), nullable=True),
            sa.Column('sku', sa.String(length=100), nullable=True),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('quantity_ordered', sa.Numeric(precision=14, scale=4), nullable=False),
            sa.Column('quantity_dispatched', sa.Numeric(precision=14, scale=4), nullable=True),
            sa.Column('unit_price', sa.Numeric(precision=14, scale=4), nullable=False),
            sa.Column('discount_percent', sa.Numeric(precision=5, scale=2), nullable=True),
            sa.Column('discount_amount', sa.Numeric(precision=14, scale=2), nullable=True),
            sa.Column('tax_rate', sa.Numeric(precision=5, scale=2), nullable=True),
            sa.Column('tax_amount', sa.Numeric(precision=14, scale=2), nullable=True),
            sa.Column('line_total', sa.Numeric(precision=14, scale=2), nullable=True),
            sa.Column('weight', sa.Numeric(precision=10, scale=3), nullable=True),
            sa.Column('volume', sa.Numeric(precision=10, scale=3), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='trading',
    )

    if not _has_table('sales_orders', 'trading'):
        op.create_table('sales_orders',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('so_number', sa.String(length=80), nullable=True, unique=True),
            sa.Column('customer_id', sa.Integer(), nullable=False),
            sa.Column('customer_name', sa.String(length=255), nullable=True),
            sa.Column('customer_po_number', sa.String(length=100), nullable=True),
            sa.Column('order_date', sa.DateTime(), nullable=False),
            sa.Column('expected_delivery_date', sa.DateTime(), nullable=True),
            sa.Column('delivery_date', sa.DateTime(), nullable=True),
            sa.Column('warehouse_id', sa.Integer(), nullable=True),
            sa.Column('currency', sa.String(length=3), nullable=True),
            sa.Column('subtotal', sa.Numeric(precision=14, scale=2), nullable=True),
            sa.Column('discount_total', sa.Numeric(precision=14, scale=2), nullable=True),
            sa.Column('tax_total', sa.Numeric(precision=14, scale=2), nullable=True),
            sa.Column('grand_total', sa.Numeric(precision=14, scale=2), nullable=True),
            sa.Column('shipping_address', sa.Text(), nullable=True),
            sa.Column('billing_address', sa.Text(), nullable=True),
            sa.Column('notes', sa.Text(), nullable=True),
            sa.Column('terms', sa.Text(), nullable=True),
            sa.Column('status', sa.String(length=50), nullable=True),
            sa.Column('country_code', sa.String(length=3), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='trading',
    )

    if not _has_table('scanned_expenses', 'finance'):
        op.create_table('scanned_expenses',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('employee_id', sa.Integer(), nullable=True),
            sa.Column('vendor_name', sa.String(length=200), nullable=True),
            sa.Column('invoice_number', sa.String(length=100), nullable=True),
            sa.Column('expense_date', sa.DateTime(), nullable=True),
            sa.Column('amount', sa.Numeric(precision=14, scale=2), nullable=False),
            sa.Column('currency', sa.String(length=3), nullable=True),
            sa.Column('tax_amount', sa.Numeric(precision=14, scale=2), nullable=True),
            sa.Column('category', sa.String(length=50), nullable=True),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('expense_account_code', sa.String(length=20), nullable=True),
            sa.Column('image_url', sa.String(length=500), nullable=True),
            sa.Column('ocr_raw_text', sa.Text(), nullable=True),
            sa.Column('ocr_confidence', sa.Numeric(precision=5, scale=2), nullable=True),
            sa.Column('status', sa.String(length=20), nullable=True),
            sa.Column('posted_journal_entry_id', sa.Integer(), nullable=True),
            sa.Column('reviewed_by', sa.Integer(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='finance',
    )

    if not _has_table('shift_handover_logs', 'hr'):
        op.create_table('shift_handover_logs',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('shift_end_at', sa.DateTime(), nullable=True),
            sa.Column('notes', sa.Text(), nullable=True),
            sa.Column('handover_to_user_id', sa.Integer(), nullable=True),
            sa.Column('handover_notes', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('country_code', sa.String(length=3), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='hr',
    )

    if not _has_table('shift_handover_sessions', 'customer'):
        op.create_table('shift_handover_sessions',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('outgoing_employee_id', sa.Integer(), nullable=False),
            sa.Column('incoming_employee_id', sa.Integer(), nullable=True),
            sa.Column('shift_date', sa.DateTime(), nullable=False),
            sa.Column('notes', sa.Text(), nullable=True),
            sa.Column('status', sa.String(length=20), nullable=True),
            sa.Column('acknowledged_at', sa.DateTime(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='customer',
    )

    if not _has_table('shift_handover_tasks', 'hr'):
        op.create_table('shift_handover_tasks',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('session_id', sa.Integer(), nullable=False),
            sa.Column('description', sa.Text(), nullable=False),
            sa.Column('priority', sa.String(length=20), nullable=True),
            sa.Column('status', sa.String(length=20), nullable=True),
            sa.Column('assigned_to', sa.Integer(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True), schema='hr',
    )

    if not _has_table('shipment_confirmations', 'logistics'):
        op.create_table('shipment_confirmations',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('shipment_id', sa.Integer(), nullable=False),
            sa.Column('order_id', sa.Integer(), nullable=True),
            sa.Column('supplier_id', sa.Integer(), nullable=True),
            sa.Column('requester_user_id', sa.Integer(), nullable=True),
            sa.Column('requester_role', sa.String(), nullable=True),
            sa.Column('target_user_id', sa.Integer(), nullable=True),
            sa.Column('target_role', sa.String(), nullable=True),
            sa.Column('confirmation_type', sa.String(), nullable=True),
            sa.Column('status', sa.String(), nullable=True),
            sa.Column('requested_status', sa.String(), nullable=True),
            sa.Column('requested_event_type', sa.String(), nullable=True),
            sa.Column('current_hub', sa.String(), nullable=True),
            sa.Column('notes', sa.Text(), nullable=True),
            sa.Column('confirmation_code', sa.String(), nullable=True),
            sa.Column('confirmed_at', sa.DateTime(), nullable=True),
            sa.Column('responded_at', sa.DateTime(), nullable=True),
            sa.Column('tracking_number', sa.String(), nullable=True),
            sa.Column('delivery_signature_name', sa.String(), nullable=True),
            sa.Column('delivery_signature_data_url', sa.String(), nullable=True),
            sa.Column('delivery_signature_captured_at', sa.DateTime(), nullable=True),
            sa.Column('response_notes', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='logistics',
    )

    if not _has_table('shipment_events', 'logistics'):
        op.create_table('shipment_events',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('shipment_id', sa.Integer(), nullable=False),
            sa.Column('order_id', sa.Integer(), nullable=False),
            sa.Column('supplier_id', sa.Integer(), nullable=False),
            sa.Column('actor_user_id', sa.Integer(), nullable=True),
            sa.Column('actor_role', sa.String(), nullable=True),
            sa.Column('event_type', sa.String(), nullable=False),
            sa.Column('status_after', sa.String(), nullable=True),
            sa.Column('distribution_channel', sa.String(), nullable=True),
            sa.Column('location', sa.String(), nullable=True),
            sa.Column('latitude', sa.Numeric(precision=10, scale=8), nullable=True),
            sa.Column('longitude', sa.Numeric(precision=11, scale=8), nullable=True),
            sa.Column('scan_code', sa.String(), nullable=True),
            sa.Column('notes', sa.String(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='logistics',
    )

    if not _has_table('shipments', 'logistics'):
        op.create_table('shipments',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('order_id', sa.Integer(), nullable=False),
            sa.Column('supplier_id', sa.Integer(), nullable=False),
            sa.Column('assigned_partner_id', sa.Integer(), nullable=True),
            sa.Column('carrier_id', sa.Integer(), nullable=True),
            sa.Column('tracking_number', sa.String(), nullable=True, unique=True),
            sa.Column('carrier_name', sa.String(), nullable=True),
            sa.Column('status', sa.String(), nullable=True),
            sa.Column('distribution_channel', sa.String(), nullable=True),
            sa.Column('current_hub', sa.String(), nullable=True),
            sa.Column('scan_code', sa.String(), nullable=True),
            sa.Column('package_count', sa.Integer(), nullable=True),
            sa.Column('package_weight_kg', sa.Numeric(precision=5, scale=2), nullable=True),
            sa.Column('package_dimensions', sa.String(), nullable=True),
            sa.Column('packaged_at', sa.DateTime(), nullable=True),
            sa.Column('packaged_by_user_id', sa.Integer(), nullable=True),
            sa.Column('packaged_notes', sa.String(), nullable=True),
            sa.Column('packaging_notes', sa.String(), nullable=True),
            sa.Column('shipped_at', sa.DateTime(), nullable=True),
            sa.Column('estimated_delivery_at', sa.DateTime(), nullable=True),
            sa.Column('actual_delivery_at', sa.DateTime(), nullable=True),
            sa.Column('delivery_signature_name', sa.String(), nullable=True),
            sa.Column('delivery_signature_data_url', sa.String(), nullable=True),
            sa.Column('delivery_signature_captured_at', sa.DateTime(), nullable=True),
            sa.Column('notes', sa.Text(), nullable=True),
            sa.Column('accepted_vehicle_type', sa.String(), nullable=True),
            sa.Column('accepted_vehicle_multiplier', sa.Numeric(precision=5, scale=4), nullable=True),
            sa.Column('accepted_vehicle_selected_at', sa.DateTime(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='logistics',
    )

    if not _has_table('shipping_carriers', 'logistics'):
        op.create_table('shipping_carriers',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('supplier_id', sa.Integer(), nullable=True),
            sa.Column('name', sa.String(), nullable=False),
            sa.Column('code', sa.String(), nullable=False, unique=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='logistics',
    )

    if not _has_table('shipping_rules', 'logistics'):
        op.create_table('shipping_rules',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('method', sa.String(), nullable=False),
            sa.Column('base_rate', sa.Numeric(precision=10, scale=2), nullable=False),
            sa.Column('per_kg_rate', sa.Numeric(precision=10, scale=2), nullable=True),
            sa.Column('is_active', sa.Boolean(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True), schema='logistics',
    )

    if not _has_table('shipping_zones', 'logistics'):
        op.create_table('shipping_zones',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('supplier_id', sa.Integer(), nullable=True),
            sa.Column('name', sa.String(), nullable=False),
            sa.Column('countries', sa.JSON(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='logistics',
    )

    if not _has_table('shop_warehouse_locations', 'hr'):
        op.create_table('shop_warehouse_locations',
                    sa.Column('country_code', sa.String(length=3), nullable=True),
            sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('warehouse_code', sa.String(length=30), nullable=False),
            sa.Column('latitude', sa.Float(), nullable=True),
            sa.Column('longitude', sa.Float(), nullable=True),
            sa.Column('address', sa.Text(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='hr',
    )

    if not _has_table('stock_movements', 'logistics'):
        op.create_table('stock_movements',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('product_id', sa.Integer(), nullable=False),
            sa.Column('warehouse_id', sa.Integer(), nullable=True),
            sa.Column('movement_type', sa.String(length=50), nullable=False),
            sa.Column('reference_type', sa.String(length=50), nullable=True),
            sa.Column('reference_id', sa.Integer(), nullable=True),
            sa.Column('quantity_change', sa.Numeric(precision=14, scale=4), nullable=False),
            sa.Column('quantity_after', sa.Numeric(precision=14, scale=4), nullable=False),
            sa.Column('unit_cost', sa.Numeric(precision=14, scale=4), nullable=True),
            sa.Column('total_cost', sa.Numeric(precision=14, scale=4), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='logistics',
    )

    if not _has_table('supplier_bank_accounts', 'supplier'):
        op.create_table('supplier_bank_accounts',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('supplier_id', sa.Integer(), nullable=False),
            sa.Column('account_number', sa.String(), nullable=True),
            sa.Column('bank_name', sa.String(), nullable=False),
            sa.Column('beneficiary_name', sa.String(), nullable=True),
            sa.Column('branch_name', sa.String(), nullable=True),
            sa.Column('iban', sa.String(), nullable=True),
            sa.Column('swift_code', sa.String(), nullable=True),
            sa.Column('routing_number', sa.String(), nullable=True),
            sa.Column('currency', sa.String(length=3), nullable=True),
            sa.Column('bank_country', sa.String(length=3), nullable=True),
            sa.Column('verification_status', sa.String(), nullable=True),
            sa.Column('verification_note', sa.Text(), nullable=True),
            sa.Column('provider', sa.String(), nullable=True),
            sa.Column('provider_recipient_id', sa.String(), nullable=True),
            sa.Column('provider_status', sa.String(), nullable=True),
            sa.Column('provider_last_synced_at', sa.DateTime(), nullable=True),
            sa.Column('verified_at', sa.DateTime(), nullable=True),
            sa.Column('verified_by', sa.Integer(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='supplier',
    )

    if not _has_table('supplier_country_commissions', 'supplier'):
        op.create_table('supplier_country_commissions',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('supplier_id', sa.Integer(), nullable=False),
            sa.Column('category_slug', sa.String(length=100), nullable=True),
            sa.Column('notes', sa.Text(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='supplier',
    )

    if not _has_table('supplier_disputes', 'supplier'):
        op.create_table('supplier_disputes',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('supplier_id', sa.Integer(), nullable=False),
            sa.Column('order_id', sa.Integer(), nullable=True),
            sa.Column('dispute_type', sa.String(length=40), nullable=True),
            sa.Column('priority', sa.String(length=20), nullable=True),
            sa.Column('title', sa.String(length=200), nullable=True),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('return_request_id', sa.Integer(), nullable=True),
            sa.Column('verification_id', sa.Integer(), nullable=True),
            sa.Column('invoice_id', sa.Integer(), nullable=True),
            sa.Column('related_order_id', sa.Integer(), nullable=True),
            sa.Column('evidence_urls_json', sa.JSON(), nullable=True),
            sa.Column('metadata_json', sa.JSON(), nullable=True),
            sa.Column('supplier_notes', sa.Text(), nullable=True),
            sa.Column('admin_notes', sa.Text(), nullable=True),
            sa.Column('created_by', sa.Integer(), nullable=True),
            sa.Column('reason', sa.Text(), nullable=True),
            sa.Column('status', sa.String(), nullable=True),
            sa.Column('resolved_by', sa.Integer(), nullable=True),
            sa.Column('resolved_at', sa.DateTime(), nullable=True),
            sa.Column('resolution_notes', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='supplier',
    )

    if not _has_table('supplier_documents', 'supplier'):
        op.create_table('supplier_documents',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('supplier_id', sa.Integer(), nullable=False),
            sa.Column('doc_type', sa.String(), nullable=False),
            sa.Column('document_name', sa.String(), nullable=True),
            sa.Column('file_url', sa.String(), nullable=False),
            sa.Column('status', sa.String(), nullable=True),
            sa.Column('expires_at', sa.DateTime(), nullable=True),
            sa.Column('review_note', sa.Text(), nullable=True),
            sa.Column('reviewed_by', sa.Integer(), nullable=True),
            sa.Column('reviewed_at', sa.DateTime(), nullable=True),
            sa.Column('verified_by', sa.Integer(), nullable=True),
            sa.Column('is_verified', sa.Boolean(), nullable=True),
            sa.Column('verified_at', sa.DateTime(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True), schema='supplier',
    )

    if not _has_table('supplier_fraud_indicators', 'supplier'):
        op.create_table('supplier_fraud_indicators',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('supplier_id', sa.Integer(), nullable=False),
            sa.Column('indicator_type', sa.String(length=50), nullable=False),
            sa.Column('value', sa.String(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='supplier',
    )

    if not _has_table('supplier_kyc_requirements', 'country'):
        op.create_table('supplier_kyc_requirements',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False, unique=True),
            sa.Column('kyc_tier_required', sa.String(length=20), nullable=False),
            sa.Column('document_types_required', sa.Text(), nullable=True),
            sa.Column('verification_wait_days', sa.Integer(), nullable=True),
            sa.Column('auto_approve_threshold', sa.Numeric(precision=5, scale=2), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True), schema='country',
    )

    if not _has_table('supplier_notification_preferences', 'supplier'):
        op.create_table('supplier_notification_preferences',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('supplier_id', sa.Integer(), nullable=False),
            sa.Column('notify_new_order', sa.Boolean(), nullable=True),
            sa.Column('notify_low_stock', sa.Boolean(), nullable=True),
            sa.Column('notify_payout_processed', sa.Boolean(), nullable=True),
            sa.Column('notify_doc_expiry', sa.Boolean(), nullable=True),
            sa.Column('notify_return_updates', sa.Boolean(), nullable=True),
            sa.Column('notify_dispute_updates', sa.Boolean(), nullable=True),
            sa.Column('in_app_enabled', sa.Boolean(), nullable=True),
            sa.Column('email_enabled', sa.Boolean(), nullable=True),
            sa.Column('push_enabled', sa.Boolean(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='supplier',
    )

    op.execute('DROP TABLE IF EXISTS "hr"."supplier_onboarding_syncs"')
    if not _has_table('supplier_onboarding_sync', 'hr'):
        op.create_table('supplier_onboarding_sync',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('country_code', sa.String(length=10), nullable=False),
            sa.Column('supplier_id', sa.Integer(), nullable=False),
            sa.Column('kyc_status', sa.String(length=30), nullable=True),
            sa.Column('kyc_documents', sa.Text(), nullable=True),
            sa.Column('onboarding_fee_paid', sa.Boolean(), nullable=True),
            sa.Column('monthly_fee_status', sa.String(length=20), nullable=True),
            sa.Column('status', sa.String(length=20), nullable=True),
            sa.Column('notes', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True), schema='hr',
        )
        op.create_index('ix_sos_status', 'supplier_onboarding_sync', ['status'], schema='hr')
        op.create_unique_constraint('uq_sos_country_supplier', 'supplier_onboarding_sync', ['country_code', 'supplier_id'], schema='hr')

    if not _has_table('supplier_profiles', 'supplier'):
        op.create_table('supplier_profiles',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('business_name', sa.String(), nullable=False),
            sa.Column('slug', sa.String(), nullable=True, unique=True),
            sa.Column('business_type', sa.String(), nullable=True),
            sa.Column('website', sa.String(), nullable=True),
            sa.Column('address', sa.Text(), nullable=True),
            sa.Column('city', sa.String(), nullable=True),
            sa.Column('region', sa.String(), nullable=True),
            sa.Column('is_terms_accepted', sa.Boolean(), nullable=True),
            sa.Column('terms_version', sa.String(), nullable=True),
            sa.Column('verification_status', sa.String(), nullable=True),
            sa.Column('verified_at', sa.DateTime(), nullable=True),
            sa.Column('is_deleted', sa.Boolean(), nullable=True),
            sa.Column('deleted_at', sa.DateTime(), nullable=True),
            sa.Column('deleted_by_id', sa.Integer(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.Column('bio', sa.Text(), nullable=True),
            sa.Column('about_us', sa.Text(), nullable=True),
            sa.Column('postal_code', sa.String(), nullable=True),
            sa.Column('tax_id', sa.String(), nullable=True),
            sa.Column('logo_url', sa.String(), nullable=True),
            sa.Column('banner_url', sa.String(), nullable=True),
            sa.Column('video_url', sa.String(), nullable=True),
            sa.Column('certifications', sa.JSON(), nullable=True),
            sa.Column('social_links_json', sa.JSON(), nullable=True),
            sa.Column('established_year', sa.Integer(), nullable=True),
            sa.Column('operating_regions', sa.JSON(), nullable=True),
            sa.Column('verified_documents', sa.JSON(), nullable=True),
            sa.Column('document_expires_at', sa.DateTime(), nullable=True),
            sa.Column('terms_accepted_at', sa.DateTime(), nullable=True),
            sa.Column('badge_level', sa.String(), nullable=True),
            sa.Column('credibility_score', sa.Integer(), nullable=True),
            sa.Column('badge_granted_at', sa.DateTime(), nullable=True),
            sa.Column('country_code', sa.String(length=3), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='supplier',
    )

    if not _has_table('supplier_settlements', 'finance'):
        op.create_table('supplier_settlements',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('supplier_id', sa.Integer(), nullable=False),
            sa.Column('order_id', sa.Integer(), nullable=True),
            sa.Column('ledger_id', sa.Integer(), nullable=True),
            sa.Column('payout_id', sa.Integer(), nullable=True),
            sa.Column('shipment_id', sa.Integer(), nullable=True),
            sa.Column('gross_amount', sa.Numeric(precision=12, scale=2), nullable=False),
            sa.Column('commission_amount', sa.Numeric(precision=12, scale=2), nullable=True),
            sa.Column('commission_deducted', sa.Numeric(precision=12, scale=2), nullable=True),
            sa.Column('commission_rate', sa.Numeric(precision=5, scale=4), nullable=True),
            sa.Column('vat_on_commission', sa.Numeric(precision=12, scale=2), nullable=True),
            sa.Column('net_amount', sa.Numeric(precision=12, scale=2), nullable=False),
            sa.Column('status', sa.String(), nullable=True),
            sa.Column('settled_at', sa.DateTime(), nullable=True),
            sa.Column('eligible_at', sa.DateTime(), nullable=True),
            sa.Column('bank_transaction_id', sa.Integer(), nullable=True),
            sa.Column('currency', sa.String(length=3), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.Column('deleted_at', sa.DateTime(), nullable=True),
            sa.Column('deleted_by', sa.Integer(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='finance',
    )

    if not _has_table('support_ticket_replies', 'communication'):
        op.create_table('support_ticket_replies',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('ticket_id', sa.Integer(), nullable=False),
            sa.Column('sender_id', sa.Integer(), nullable=False),
            sa.Column('message', sa.Text(), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='communication',
    )

    if not _has_table('support_tickets', 'communication'):
        op.create_table('support_tickets',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('subject', sa.String(), nullable=False),
            sa.Column('priority', sa.String(), nullable=True),
            sa.Column('status', sa.String(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='communication',
    )

    if not _has_table('system_alerts', 'configuration'):
        op.create_table('system_alerts',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('alert_type', sa.String(), nullable=False),
            sa.Column('severity', sa.String(), nullable=True),
            sa.Column('title', sa.String(), nullable=False),
            sa.Column('message', sa.Text(), nullable=False),
            sa.Column('is_acknowledged', sa.Boolean(), nullable=True),
            sa.Column('acknowledged_by', sa.Integer(), nullable=True),
            sa.Column('acknowledged_at', sa.DateTime(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='configuration',
    )

    if not _has_table('system_health_events', 'customer'):
        op.create_table('system_health_events',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('service', sa.String(length=100), nullable=True),
            sa.Column('metric_name', sa.String(length=100), nullable=False),
            sa.Column('metric_value', sa.Numeric(precision=12, scale=4), nullable=False),
            sa.Column('severity', sa.String(length=20), nullable=True),
            sa.Column('message', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True), schema='customer',
    )

    if not _has_table('system_settings', 'configuration'):
        op.create_table('system_settings',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('key', sa.String(), nullable=False, unique=True),
            sa.Column('value', sa.Text(), nullable=True),
            sa.Column('value_type', sa.String(), nullable=True),
            sa.Column('description', sa.String(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='configuration',
    )

    if not _has_table('tax_rules', 'country'):
        op.create_table('tax_rules',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('tax_name', sa.String(length=100), nullable=False),
            sa.Column('tax_rate', sa.Numeric(precision=5, scale=4), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True), schema='country',
    )

    if not _has_table('ticket_attachments', 'communication'):
        op.create_table('ticket_attachments',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('ticket_reply_id', sa.Integer(), nullable=True),
            sa.Column('ticket_id', sa.Integer(), nullable=True),
            sa.Column('file_url', sa.String(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='communication',
    )

    if not _has_table('ticket_messages', 'communication'):
        op.create_table('ticket_messages',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('ticket_id', sa.Integer(), nullable=False),
            sa.Column('sender_id', sa.Integer(), nullable=False),
            sa.Column('message', sa.Text(), nullable=False),
            sa.Column('is_admin', sa.Boolean(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='communication',
    )

    if not _has_table('ticket_replies', 'communication'):
        op.create_table('ticket_replies',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('ticket_id', sa.Integer(), nullable=False),
            sa.Column('sender_id', sa.Integer(), nullable=False),
            sa.Column('message', sa.Text(), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='communication',
    )

    if not _has_table('trade_deal_items', 'finance'):
        op.create_table('trade_deal_items',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('deal_id', sa.Integer(), nullable=False),
            sa.Column('asset_code', sa.String(length=50), nullable=False),
            sa.Column('quantity', sa.Numeric(precision=14, scale=4), nullable=False),
            sa.Column('unit_price', sa.Numeric(precision=14, scale=4), nullable=False),
            sa.Column('total_value', sa.Numeric(precision=14, scale=2), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='finance',
    )

    if not _has_table('trade_deals', 'finance'):
        op.create_table('trade_deals',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('deal_number', sa.String(length=80), nullable=True, unique=True),
            sa.Column('counterparty_id', sa.Integer(), nullable=False),
            sa.Column('counterparty_legal_name', sa.String(length=255), nullable=True),
            sa.Column('status', sa.String(length=50), nullable=True),
            sa.Column('deal_date', sa.DateTime(), nullable=False),
            sa.Column('settlement_date', sa.DateTime(), nullable=True),
            sa.Column('buy_currency', sa.String(length=3), nullable=True),
            sa.Column('sell_currency', sa.String(length=3), nullable=True),
            sa.Column('buy_amount', sa.Numeric(precision=14, scale=2), nullable=True),
            sa.Column('sell_amount', sa.Numeric(precision=14, scale=2), nullable=True),
            sa.Column('rate', sa.Numeric(precision=14, scale=6), nullable=True),
            sa.Column('total_value', sa.Numeric(precision=14, scale=2), nullable=True),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('country_code', sa.String(length=3), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='finance',
    )

    if not _has_table('trade_settlements', 'finance'):
        op.create_table('trade_settlements',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('deal_id', sa.Integer(), nullable=False),
            sa.Column('settlement_date', sa.DateTime(), nullable=False),
            sa.Column('amount', sa.Numeric(precision=14, scale=2), nullable=False),
            sa.Column('currency', sa.String(length=3), nullable=True),
            sa.Column('status', sa.String(length=50), nullable=True),
            sa.Column('reference_number', sa.String(length=100), nullable=True),
            sa.Column('payment_method', sa.String(length=50), nullable=True),
            sa.Column('notes', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='finance',
    )

    if not _has_table('trading_configs', 'finance'):
        op.create_table('trading_configs',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('config_key', sa.String(length=100), nullable=False),
            sa.Column('config_value', sa.Text(), nullable=True),
            sa.Column('value_type', sa.String(length=20), nullable=True),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='finance',
    )

    if not _has_table('training_modules', 'hr'):
        op.create_table('training_modules',
                    sa.Column('module_id', sa.String(length=100), primary_key=True, nullable=False),
            sa.Column('title', sa.String(length=200), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('required_for_role', sa.String(length=100), nullable=True),
            sa.Column('duration_minutes', sa.Integer(), nullable=True),
            sa.Column('is_active', sa.Boolean(), nullable=True),
            sa.Column('permission_key', sa.String(length=100), nullable=True),
            sa.Column('permission_description', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True), schema='hr',
    )

    if not _has_table('transaction_ledgers', 'finance'):
        op.create_table('transaction_ledgers',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=True),
            sa.Column('supplier_id', sa.Integer(), nullable=True),
            sa.Column('logistics_partner_id', sa.Integer(), nullable=True),
            sa.Column('order_id', sa.Integer(), nullable=True),
            sa.Column('order_item_id', sa.Integer(), nullable=True),
            sa.Column('shipment_id', sa.Integer(), nullable=True),
            sa.Column('payment_method', sa.String(length=20), nullable=True),
            sa.Column('product_subtotal', sa.Numeric(precision=12, scale=2), nullable=True),
            sa.Column('discount_amount', sa.Numeric(precision=12, scale=2), nullable=True),
            sa.Column('delivery_pickup_charge', sa.Numeric(precision=12, scale=2), nullable=True),
            sa.Column('delivery_dropoff_charge', sa.Numeric(precision=12, scale=2), nullable=True),
            sa.Column('delivery_total', sa.Numeric(precision=12, scale=2), nullable=True),
            sa.Column('vat_amount', sa.Numeric(precision=12, scale=2), nullable=True),
            sa.Column('zozi_commission_rate', sa.Numeric(precision=5, scale=4), nullable=True),
            sa.Column('zozi_commission', sa.Numeric(precision=12, scale=2), nullable=True),
            sa.Column('net_supplier_amount', sa.Numeric(precision=12, scale=2), nullable=True),
            sa.Column('net_logistics_amount', sa.Numeric(precision=12, scale=2), nullable=True),
            sa.Column('net_zozi_amount', sa.Numeric(precision=12, scale=2), nullable=True),
            sa.Column('cod_collected_amount', sa.Numeric(precision=12, scale=2), nullable=True),
            sa.Column('cod_remittance_due', sa.Numeric(precision=12, scale=2), nullable=True),
            sa.Column('settlement_status', sa.String(length=30), nullable=True),
            sa.Column('currency', sa.String(length=3), nullable=True),
            sa.Column('transaction_type', sa.String(), nullable=True),
            sa.Column('reference_id', sa.String(), nullable=True),
            sa.Column('balance_after', sa.Numeric(precision=12, scale=2), nullable=True),
            sa.Column('notes', sa.Text(), nullable=True),
            sa.Column('amount', sa.Numeric(precision=12, scale=2), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='finance',
    )

    if not _has_table('treasury_accounts', 'treasury'):
        op.create_table('treasury_accounts',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('slug', sa.String(), nullable=False, unique=True),
            sa.Column('name', sa.String(), nullable=False),
            sa.Column('account_type', sa.String(), nullable=False),
            sa.Column('currency', sa.String(length=3), nullable=True),
            sa.Column('gl_account_code', sa.String(), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('employee_id', sa.Integer(), nullable=True),
            sa.Column('balance', sa.Numeric(precision=12, scale=2), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='treasury',
    )

    if not _has_table('treasury_transactions', 'treasury'):
        op.create_table('treasury_transactions',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('from_account_id', sa.Integer(), nullable=True),
            sa.Column('to_account_id', sa.Integer(), nullable=True),
            sa.Column('account_id', sa.Integer(), nullable=True),
            sa.Column('transaction_type', sa.String(), nullable=False),
            sa.Column('amount', sa.Numeric(precision=12, scale=2), nullable=False),
            sa.Column('currency', sa.String(length=3), nullable=True),
            sa.Column('reference', sa.String(), nullable=True),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('posted_at', sa.DateTime(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='treasury',
    )

    if not _has_table('upload_jobs', 'ai'):
        op.create_table('upload_jobs',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('supplier_id', sa.Integer(), nullable=False),
            sa.Column('filename', sa.String(length=512), nullable=False),
            sa.Column('status', sa.String(length=32), nullable=False),
            sa.Column('progress', sa.Float(), nullable=False),
            sa.Column('strategy_winner', sa.String(length=64), nullable=True),
            sa.Column('strategy_score', sa.Float(), nullable=True),
            sa.Column('ai_result_json', sa.JSON(), nullable=True),
            sa.Column('product_id', sa.Integer(), nullable=True),
            sa.Column('error_message', sa.Text(), nullable=True),
            sa.Column('image_url', sa.String(length=1024), nullable=True),
            sa.Column('processed_image_url', sa.String(length=1024), nullable=True),
            sa.Column('started_at', sa.DateTime(), nullable=True),
            sa.Column('completed_at', sa.DateTime(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
            sa.Column('stt_duration_ms', sa.Float(), nullable=True),
            sa.Column('nlp_duration_ms', sa.Float(), nullable=True),
            sa.Column('bg_duration_ms', sa.Float(), nullable=True),
            sa.Column('ai_duration_ms', sa.Float(), nullable=True),
            sa.Column('total_duration_ms', sa.Float(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False),
            sa.Column('created_by', sa.Integer(), nullable=True),
            sa.Column('updated_by', sa.Integer(), nullable=True),
            sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default=sa.text('false')),
            sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('deleted_by', sa.Integer(), nullable=True),
            sa.Column('delete_reason', sa.Text(), nullable=True), schema='ai',
    )

    if not _has_table('user_browsing_history', 'security'):
        op.create_table('user_browsing_history',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('product_id', sa.Integer(), nullable=False),
            sa.Column('viewed_at', sa.DateTime(), nullable=True), schema='security',
    )

    if not _has_table('user_devices', 'security'):
        op.create_table('user_devices',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('device_id', sa.String(length=255), nullable=False),
            sa.Column('device_type', sa.String(length=50), nullable=True),
            sa.Column('last_seen_at', sa.DateTime(), nullable=True),
            sa.Column('is_current', sa.Boolean(), nullable=True),
            sa.Column('is_trusted', sa.Boolean(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='security',
    )

    if not _has_table('user_login_history', 'security'):
        op.create_table('user_login_history',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('ip_address', sa.String(), nullable=False),
            sa.Column('user_agent', sa.String(), nullable=True),
            sa.Column('timestamp', sa.DateTime(), nullable=True),
            sa.Column('success', sa.Boolean(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='security',
    )

    if not _has_table('user_permission_overrides', 'security'):
        op.create_table('user_permission_overrides',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('permission_id', sa.Integer(), nullable=False),
            sa.Column('granted_by', sa.Integer(), nullable=True),
            sa.Column('expires_at', sa.DateTime(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='security',
    )

    if not _has_table('user_sessions', 'security'):
        op.create_table('user_sessions',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('session_token', sa.String(length=255), nullable=False, unique=True),
            sa.Column('ip_address', sa.String(length=45), nullable=True),
            sa.Column('user_agent', sa.String(length=500), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='security',
    )

    if not _has_table('users', 'security'):
        op.create_table('users',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('email', sa.String(), nullable=True, unique=True),
            sa.Column('username', sa.String(), nullable=True, unique=True),
            sa.Column('full_name', sa.String(length=160), nullable=True),
            sa.Column('phone', sa.String(length=40), nullable=True),
            sa.Column('hashed_password', sa.String(), nullable=True),
            sa.Column('role', sa.String(), nullable=True),
            sa.Column('profile_image', sa.String(), nullable=True),
            sa.Column('preferred_language', sa.String(), nullable=True),
            sa.Column('preferred_currency', sa.String(length=10), nullable=True),
            sa.Column('preferred_country', sa.String(length=10), nullable=True),
            sa.Column('email_verified', sa.Boolean(), nullable=True),
            sa.Column('last_login', sa.DateTime(), nullable=True),
            sa.Column('is_verified', sa.Boolean(), nullable=True),
            sa.Column('staff_role_label', sa.String(length=120), nullable=True),
            sa.Column('staff_title', sa.String(length=120), nullable=True),
            sa.Column('staff_department', sa.String(length=120), nullable=True),
            sa.Column('staff_country_codes', sa.Text(), nullable=True),
            sa.Column('staff_permissions', sa.Text(), nullable=True),
            sa.Column('staff_area_of_operation', sa.Text(), nullable=True),
            sa.Column('staff_hire_date', sa.DateTime(), nullable=True),
            sa.Column('staff_experience_level', sa.String(length=50), nullable=True),
            sa.Column('staff_performance_summary', sa.Text(), nullable=True),
            sa.Column('staff_assigned_tasks', sa.JSON(), nullable=True),
            sa.Column('staff_assigned_projects', sa.JSON(), nullable=True),
            sa.Column('staff_notes', sa.Text(), nullable=True),
            sa.Column('is_deleted', sa.Boolean(), nullable=True),
            sa.Column('deleted_at', sa.DateTime(), nullable=True),
            sa.Column('referral_code', sa.String(), nullable=True, unique=True),
            sa.Column('referred_by_user_id', sa.Integer(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.Column('referral_points', sa.Integer(), nullable=True),
            sa.Column('sharing_points', sa.Integer(), nullable=True),
            sa.Column('totp_enabled', sa.Boolean(), nullable=True),
            sa.Column('totp_secret', sa.String(), nullable=True),
            sa.Column('last_seen_at', sa.DateTime(), nullable=True),
            sa.Column('is_current', sa.Boolean(), nullable=True),
            sa.Column('address_book', infrastructure.utils.encryption.EncryptedString(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='security',
    )

    if not _has_table('vat_remittances', 'finance'):
        op.create_table('vat_remittances',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('period_start_at', sa.DateTime(), nullable=False),
            sa.Column('period_end_at', sa.DateTime(), nullable=False),
            sa.Column('vat_collected_amount', sa.Numeric(precision=12, scale=2), nullable=True),
            sa.Column('vat_adjustment_amount', sa.Numeric(precision=12, scale=2), nullable=True),
            sa.Column('amount_due', sa.Numeric(precision=12, scale=2), nullable=True),
            sa.Column('amount', sa.Numeric(precision=12, scale=2), nullable=False),
            sa.Column('amount_remitted', sa.Numeric(precision=12, scale=2), nullable=True),
            sa.Column('currency', sa.String(length=3), nullable=True),
            sa.Column('bank_transaction_id', sa.Integer(), nullable=True),
            sa.Column('remitted_by', sa.Integer(), nullable=True),
            sa.Column('remitted_at', sa.DateTime(), nullable=True),
            sa.Column('notes', sa.Text(), nullable=True),
            sa.Column('status', sa.String(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='finance',
    )

    if not _has_table('vendors', 'finance'):
        op.create_table('vendors',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('name', sa.String(length=200), nullable=False),
            sa.Column('tax_id', sa.String(length=60), nullable=True),
            sa.Column('contact_email', sa.String(length=160), nullable=True),
            sa.Column('currency', sa.String(length=3), nullable=True),
            sa.Column('payment_terms_days', sa.Integer(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='finance',
    )

    if not _has_table('video_analytics', 'media'):
        op.create_table('video_analytics',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('video_id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=True),
            sa.Column('event_type', sa.String(length=50), nullable=False),
            sa.Column('watch_duration_seconds', sa.Integer(), nullable=True),
            sa.Column('device_type', sa.String(length=50), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='media',
    )

    if not _has_table('video_room_participants', 'customer'):
        op.create_table('video_room_participants',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('room_id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('role', sa.String(length=20), nullable=True),
            sa.Column('joined_at', sa.DateTime(), nullable=True),
            sa.Column('left_at', sa.DateTime(), nullable=True), schema='customer',
    )

    if not _has_table('video_room_recordings', 'media'):
        op.create_table('video_room_recordings',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('room_id', sa.Integer(), nullable=False),
            sa.Column('started_by', sa.Integer(), nullable=False),
            sa.Column('recording_url', sa.String(length=500), nullable=True),
            sa.Column('duration_seconds', sa.Integer(), nullable=True),
            sa.Column('status', sa.String(length=20), nullable=True),
            sa.Column('started_at', sa.DateTime(), nullable=True),
            sa.Column('ended_at', sa.DateTime(), nullable=True), schema='media',
    )

    if not _has_table('video_rooms', 'customer'):
        op.create_table('video_rooms',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('room_id', sa.String(length=64), nullable=False, unique=True),
            sa.Column('room_uuid', sa.String(length=32), nullable=True, unique=True),
            sa.Column('name', sa.String(length=200), nullable=False),
            sa.Column('is_boardroom', sa.Boolean(), nullable=True),
            sa.Column('status', sa.String(length=20), nullable=True),
            sa.Column('max_participants', sa.Integer(), nullable=True),
            sa.Column('recording_enabled', sa.Boolean(), nullable=True),
            sa.Column('watermark_enabled', sa.Boolean(), nullable=True),
            sa.Column('transcription_enabled', sa.Boolean(), nullable=True),
            sa.Column('started_at', sa.DateTime(), nullable=True),
            sa.Column('ended_at', sa.DateTime(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('created_by', sa.Integer(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='customer',
    )

    if not _has_table('war_room_templates', 'communication'):
        op.create_table('war_room_templates',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('name', sa.String(length=100), nullable=False),
            sa.Column('severity', sa.String(), nullable=False),
            sa.Column('auto_assign', sa.Boolean(), nullable=True),
            sa.Column('template_data', sa.JSON(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True), schema='communication',
    )

    if not _has_table('warehouses', 'logistics'):
        op.create_table('warehouses',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('name', sa.String(length=255), nullable=False),
            sa.Column('code', sa.String(length=50), nullable=False, unique=True),
            sa.Column('address', sa.Text(), nullable=True),
            sa.Column('city', sa.String(length=100), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.Column('country_code', sa.String(length=3), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='logistics',
    )

    if not _has_table('wishlist_items', 'customer'):
        op.create_table('wishlist_items',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('product_id', sa.Integer(), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='customer',
    )

    if not _has_table('wishlists', 'customer'):
        op.create_table('wishlists',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('product_id', sa.Integer(), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='customer',
    )

    if not _has_table('worm_audit', 'audit'):
        op.create_table('worm_audit',
                    sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('entity_type', sa.String(length=100), nullable=False),
            sa.Column('entity_id', sa.String(length=100), nullable=False),
            sa.Column('action', sa.String(length=50), nullable=False),
            sa.Column('actor_id', sa.Integer(), nullable=True),
            sa.Column('actor_type', sa.String(length=50), nullable=True),
            sa.Column('payload_json', sa.JSON(), nullable=True),
            sa.Column('signature', sa.String(length=255), nullable=True),
            sa.Column('is_valid', sa.Boolean(), nullable=True),
            sa.Column('previous_state_hash', sa.String(length=255), nullable=True),
            sa.Column('new_state_hash', sa.String(length=255), nullable=True),
            sa.Column('timestamp', sa.DateTime(), nullable=False),
            sa.Column('uuid', sa.String(length=36), nullable=False),
            sa.Column('country_code', sa.String(length=3), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False), schema='audit',
    )

def downgrade() -> None:
    if op.get_bind().dialect.name == "sqlite":
        return

    op.execute('DROP TABLE IF EXISTS "audit"."worm_audit"')
    op.execute('DROP TABLE IF EXISTS "customer"."wishlists"')
    op.execute('DROP TABLE IF EXISTS "customer"."wishlist_items"')
    op.execute('DROP TABLE IF EXISTS "logistics"."warehouses"')
    op.execute('DROP TABLE IF EXISTS "communication"."war_room_templates"')
    op.execute('DROP TABLE IF EXISTS "customer"."video_rooms"')
    op.execute('DROP TABLE IF EXISTS "media"."video_room_recordings"')
    op.execute('DROP TABLE IF EXISTS "customer"."video_room_participants"')
    op.execute('DROP TABLE IF EXISTS "media"."video_analytics"')
    op.execute('DROP TABLE IF EXISTS "finance"."vendors"')
    op.execute('DROP TABLE IF EXISTS "finance"."vat_remittances"')
    op.execute('DROP TABLE IF EXISTS "security"."users"')
    op.execute('DROP TABLE IF EXISTS "security"."user_sessions"')
    op.execute('DROP TABLE IF EXISTS "security"."user_permission_overrides"')
    op.execute('DROP TABLE IF EXISTS "security"."user_login_history"')
    op.execute('DROP TABLE IF EXISTS "security"."user_devices"')
    op.execute('DROP TABLE IF EXISTS "security"."user_browsing_history"')
    op.execute('DROP TABLE IF EXISTS "ai"."upload_jobs"')
    op.execute('DROP TABLE IF EXISTS "treasury"."treasury_transactions"')
    op.execute('DROP TABLE IF EXISTS "treasury"."treasury_accounts"')
    op.execute('DROP TABLE IF EXISTS "finance"."transaction_ledgers"')
    op.execute('DROP TABLE IF EXISTS "hr"."training_modules"')
    op.execute('DROP TABLE IF EXISTS "finance"."trading_configs"')
    op.execute('DROP TABLE IF EXISTS "finance"."trade_settlements"')
    op.execute('DROP TABLE IF EXISTS "finance"."trade_deals"')
    op.execute('DROP TABLE IF EXISTS "finance"."trade_deal_items"')
    op.execute('DROP TABLE IF EXISTS "communication"."ticket_replies"')
    op.execute('DROP TABLE IF EXISTS "communication"."ticket_messages"')
    op.execute('DROP TABLE IF EXISTS "communication"."ticket_attachments"')
    op.execute('DROP TABLE IF EXISTS "country"."tax_rules"')
    op.execute('DROP TABLE IF EXISTS "configuration"."system_settings"')
    op.execute('DROP TABLE IF EXISTS "customer"."system_health_events"')
    op.execute('DROP TABLE IF EXISTS "configuration"."system_alerts"')
    op.execute('DROP TABLE IF EXISTS "communication"."support_tickets"')
    op.execute('DROP TABLE IF EXISTS "communication"."support_ticket_replies"')
    op.execute('DROP TABLE IF EXISTS "finance"."supplier_settlements"')
    op.execute('DROP TABLE IF EXISTS "supplier"."supplier_profiles"')
    op.execute('DROP TABLE IF EXISTS "hr"."supplier_onboarding_sync"')
    op.execute('DROP TABLE IF EXISTS "supplier"."supplier_notification_preferences"')
    op.execute('DROP TABLE IF EXISTS "country"."supplier_kyc_requirements"')
    op.execute('DROP TABLE IF EXISTS "supplier"."supplier_fraud_indicators"')
    op.execute('DROP TABLE IF EXISTS "supplier"."supplier_documents"')
    op.execute('DROP TABLE IF EXISTS "supplier"."supplier_disputes"')
    op.execute('DROP TABLE IF EXISTS "supplier"."supplier_country_commissions"')
    op.execute('DROP TABLE IF EXISTS "supplier"."supplier_bank_accounts"')
    op.execute('DROP TABLE IF EXISTS "logistics"."stock_movements"')
    op.execute('DROP TABLE IF EXISTS "hr"."shop_warehouse_locations"')
    op.execute('DROP TABLE IF EXISTS "logistics"."shipping_zones"')
    op.execute('DROP TABLE IF EXISTS "logistics"."shipping_rules"')
    op.execute('DROP TABLE IF EXISTS "logistics"."shipping_carriers"')
    op.execute('DROP TABLE IF EXISTS "logistics"."shipments"')
    op.execute('DROP TABLE IF EXISTS "logistics"."shipment_events"')
    op.execute('DROP TABLE IF EXISTS "logistics"."shipment_confirmations"')
    op.execute('DROP TABLE IF EXISTS "hr"."shift_handover_tasks"')
    op.execute('DROP TABLE IF EXISTS "customer"."shift_handover_sessions"')
    op.execute('DROP TABLE IF EXISTS "hr"."shift_handover_logs"')
    op.execute('DROP TABLE IF EXISTS "finance"."scanned_expenses"')
    op.execute('DROP TABLE IF EXISTS "trading"."sales_orders"')
    op.execute('DROP TABLE IF EXISTS "trading"."sales_order_lines"')
    op.execute('DROP TABLE IF EXISTS "security"."role_permission_settings"')
    op.execute('DROP TABLE IF EXISTS "security"."role_permission_assignments"')
    op.execute('DROP TABLE IF EXISTS "security"."revoked_tokens"')
    op.execute('DROP TABLE IF EXISTS "commerce"."reviews"')
    op.execute('DROP TABLE IF EXISTS "commerce"."return_requests"')
    op.execute('DROP TABLE IF EXISTS "commerce"."return_abuse_patterns"')
    op.execute('DROP TABLE IF EXISTS "audit"."retention_job_runs"')
    op.execute('DROP TABLE IF EXISTS "finance"."refund_ledger"')
    op.execute('DROP TABLE IF EXISTS "customer"."referrals"')
    op.execute('DROP TABLE IF EXISTS "customer"."referral_point_events"')
    op.execute('DROP TABLE IF EXISTS "finance"."recurring_templates"')
    op.execute('DROP TABLE IF EXISTS "communication"."push_notification_tokens"')
    op.execute('DROP TABLE IF EXISTS "trading"."purchase_orders"')
    op.execute('DROP TABLE IF EXISTS "trading"."purchase_order_lines"')
    op.execute('DROP TABLE IF EXISTS "communication"."proxy_sessions"')
    op.execute('DROP TABLE IF EXISTS "communication"."proxy_messages"')
    op.execute('DROP TABLE IF EXISTS "communication"."proxy_channels"')
    op.execute('DROP TABLE IF EXISTS "communication"."proxy_call_logs"')
    op.execute('DROP TABLE IF EXISTS "commerce"."promotion_order_tiers"')
    op.execute('DROP TABLE IF EXISTS "commerce"."promotion_ledger_entries"')
    op.execute('DROP TABLE IF EXISTS "commerce"."promotion_engine_configs"')
    op.execute('DROP TABLE IF EXISTS "commerce"."products"')
    op.execute('DROP TABLE IF EXISTS "media"."product_videos"')
    op.execute('DROP TABLE IF EXISTS "commerce"."product_verifications"')
    op.execute('DROP TABLE IF EXISTS "commerce"."product_variants"')
    op.execute('DROP TABLE IF EXISTS "commerce"."product_images"')
    op.execute('DROP TABLE IF EXISTS "commerce"."product_filter_options"')
    op.execute('DROP TABLE IF EXISTS "commerce"."product_filter_metadata"')
    op.execute('DROP TABLE IF EXISTS "commerce"."product_commission_overrides"')
    op.execute('DROP TABLE IF EXISTS "analytics"."processed_webhook_events"')
    op.execute('DROP TABLE IF EXISTS "ai"."predictive_simulations"')
    op.execute('DROP TABLE IF EXISTS "hr"."physical_id_cards"')
    op.execute('DROP TABLE IF EXISTS "security"."permissions"')
    op.execute('DROP TABLE IF EXISTS "security"."permission_categories"')
    op.execute('DROP TABLE IF EXISTS "security"."permission_audit_log"')
    op.execute('DROP TABLE IF EXISTS "finance"."pending_journal_entries"')
    op.execute('DROP TABLE IF EXISTS "finance"."payroll_records"')
    op.execute('DROP TABLE IF EXISTS "treasury"."payouts"')
    op.execute('DROP TABLE IF EXISTS "treasury"."payout_rules"')
    op.execute('DROP TABLE IF EXISTS "country"."payout_rule_products"')
    op.execute('DROP TABLE IF EXISTS "country"."payout_rule_categories"')
    op.execute('DROP TABLE IF EXISTS "treasury"."payout_batches"')
    op.execute('DROP TABLE IF EXISTS "treasury"."payout_batch_items"')
    op.execute('DROP TABLE IF EXISTS "finance"."payments"')
    op.execute('DROP TABLE IF EXISTS "treasury"."payment_reconciliation_runs"')
    op.execute('DROP TABLE IF EXISTS "treasury"."payment_provider_configs"')
    op.execute('DROP TABLE IF EXISTS "hr"."payment_orchestrator_sync"')
    op.execute('DROP TABLE IF EXISTS "treasury"."payment_gateway_connections"')
    op.execute('DROP TABLE IF EXISTS "security"."password_reset_tokens"')
    op.execute('DROP TABLE IF EXISTS "hr"."parcel_location_trackers"')
    op.execute('DROP TABLE IF EXISTS "configuration"."outbox_events"')
    op.execute('DROP TABLE IF EXISTS "hr"."org_units"')
    op.execute('DROP TABLE IF EXISTS "commerce"."orders"')
    op.execute('DROP TABLE IF EXISTS "commerce"."order_notifications"')
    op.execute('DROP TABLE IF EXISTS "commerce"."order_logistics_allocations"')
    op.execute('DROP TABLE IF EXISTS "commerce"."order_items"')
    op.execute('DROP TABLE IF EXISTS "hr"."onboarding_steps"')
    op.execute('DROP TABLE IF EXISTS "hr"."onboarding_pipelines"')
    op.execute('DROP TABLE IF EXISTS "configuration"."oman_delivery_zones"')
    op.execute('DROP TABLE IF EXISTS "hr"."offices"')
    op.execute('DROP TABLE IF EXISTS "hr"."offboarding_cases"')
    op.execute('DROP TABLE IF EXISTS "media"."ocr_results"')
    op.execute('DROP TABLE IF EXISTS "communication"."notifications"')
    op.execute('DROP TABLE IF EXISTS "analytics"."normalized_webhook_events"')
    op.execute('DROP TABLE IF EXISTS "communication"."newsletter_subscribers"')
    op.execute('DROP TABLE IF EXISTS "communication"."news_sources"')
    op.execute('DROP TABLE IF EXISTS "customer"."news_articles"')
    op.execute('DROP TABLE IF EXISTS "analytics"."mv_monthly_sales"')
    op.execute('DROP TABLE IF EXISTS "analytics"."mv_facet_counts"')
    op.execute('DROP TABLE IF EXISTS "analytics"."mv_daily_sales"')
    op.execute('DROP TABLE IF EXISTS "analytics"."mv_cash_position"')
    op.execute('DROP TABLE IF EXISTS "country"."messages"')
    op.execute('DROP TABLE IF EXISTS "security"."meeting_transcripts"')
    op.execute('DROP TABLE IF EXISTS "communication"."meeting_recordings"')
    op.execute('DROP TABLE IF EXISTS "security"."meeting_action_items"')
    op.execute('DROP TABLE IF EXISTS "media"."media_upload_sessions"')
    op.execute('DROP TABLE IF EXISTS "media"."media_assets"')
    op.execute('DROP TABLE IF EXISTS "communication"."masked_messages"')
    op.execute('DROP TABLE IF EXISTS "security"."manual_review_queue"')
    op.execute('DROP TABLE IF EXISTS "logistics"."logistics_zones"')
    op.execute('DROP TABLE IF EXISTS "logistics"."logistics_vehicle_rules"')
    op.execute('DROP TABLE IF EXISTS "logistics"."logistics_settlements"')
    op.execute('DROP TABLE IF EXISTS "logistics"."logistics_rates"')
    op.execute('DROP TABLE IF EXISTS "logistics"."logistics_pricing_rules"')
    op.execute('DROP TABLE IF EXISTS "logistics"."logistics_pricing_profiles"')
    op.execute('DROP TABLE IF EXISTS "logistics"."logistics_partners"')
    op.execute('DROP TABLE IF EXISTS "logistics"."logistics_partner_service_areas"')
    op.execute('DROP TABLE IF EXISTS "logistics"."logistics_partner_profiles"')
    op.execute('DROP TABLE IF EXISTS "logistics"."logistics_partner_payouts"')
    op.execute('DROP TABLE IF EXISTS "hr"."logistics_partner_locations"')
    op.execute('DROP TABLE IF EXISTS "country"."logistics_partner_kyc_requirements"')
    op.execute('DROP TABLE IF EXISTS "logistics"."logistics_partner_documents"')
    op.execute('DROP TABLE IF EXISTS "logistics"."logistics_partner_bank_accounts"')
    op.execute('DROP TABLE IF EXISTS "logistics"."logistics_fraud_indicators"')
    op.execute('DROP TABLE IF EXISTS "logistics"."logistics_cod_remittance_receipts"')
    op.execute('DROP TABLE IF EXISTS "logistics"."logistics_category_pricing_rules"')
    op.execute('DROP TABLE IF EXISTS "hr"."legal_contract_templates"')
    op.execute('DROP TABLE IF EXISTS "logistics"."landed_cost_allocations"')
    op.execute('DROP TABLE IF EXISTS "security"."kyc_verifications"')
    op.execute('DROP TABLE IF EXISTS "analytics"."kpi_supplier"')
    op.execute('DROP TABLE IF EXISTS "analytics"."kpi_revenue"')
    op.execute('DROP TABLE IF EXISTS "analytics"."kpi_retention"')
    op.execute('DROP TABLE IF EXISTS "analytics"."kpi_orders"')
    op.execute('DROP TABLE IF EXISTS "analytics"."kpi_customer"')
    op.execute('DROP TABLE IF EXISTS "analytics"."kpi_country"')
    op.execute('DROP TABLE IF EXISTS "analytics"."kpi_conversion"')
    op.execute('DROP TABLE IF EXISTS "finance"."journal_entry_lines"')
    op.execute('DROP TABLE IF EXISTS "finance"."journal_entries"')
    op.execute('DROP TABLE IF EXISTS "security"."ip_reputations"')
    op.execute('DROP TABLE IF EXISTS "security"."ip_account_linkages"')
    op.execute('DROP TABLE IF EXISTS "finance"."invoices"')
    op.execute('DROP TABLE IF EXISTS "finance"."invoice_items"')
    op.execute('DROP TABLE IF EXISTS "communication"."internal_notices"')
    op.execute('DROP TABLE IF EXISTS "communication"."internal_messages"')
    op.execute('DROP TABLE IF EXISTS "communication"."internal_emails"')
    op.execute('DROP TABLE IF EXISTS "communication"."internal_channels"')
    op.execute('DROP TABLE IF EXISTS "communication"."internal_channel_members"')
    op.execute('DROP TABLE IF EXISTS "communication"."incident_war_rooms"')
    op.execute('DROP TABLE IF EXISTS "communication"."incident_threads"')
    op.execute('DROP TABLE IF EXISTS "communication"."incident_action_items"')
    op.execute('DROP TABLE IF EXISTS "configuration"."inbox_events"')
    op.execute('DROP TABLE IF EXISTS "logistics"."import_shipments"')
    op.execute('DROP TABLE IF EXISTS "logistics"."import_shipment_lines"')
    op.execute('DROP TABLE IF EXISTS "logistics"."import_cost_templates"')
    op.execute('DROP TABLE IF EXISTS "communication"."help_categories"')
    op.execute('DROP TABLE IF EXISTS "communication"."group_chat_rooms"')
    op.execute('DROP TABLE IF EXISTS "communication"."group_chat_messages"')
    op.execute('DROP TABLE IF EXISTS "customer"."group_chat_members"')
    op.execute('DROP TABLE IF EXISTS "trading"."goods_receipt_notes"')
    op.execute('DROP TABLE IF EXISTS "trading"."goods_receipt_lines"')
    op.execute('DROP TABLE IF EXISTS "hr"."geo_fence_logs"')
    op.execute('DROP TABLE IF EXISTS "treasury"."gateway_settlement_schedules"')
    op.execute('DROP TABLE IF EXISTS "security"."fraud_velocity_counters"')
    op.execute('DROP TABLE IF EXISTS "security"."fraud_scoring_logs"')
    op.execute('DROP TABLE IF EXISTS "security"."fraud_rules"')
    op.execute('DROP TABLE IF EXISTS "security"."fraud_events"')
    op.execute('DROP TABLE IF EXISTS "security"."fraud_cases"')
    op.execute('DROP TABLE IF EXISTS "security"."fraud_case_assignments"')
    op.execute('DROP TABLE IF EXISTS "security"."fraud_blacklist"')
    op.execute('DROP TABLE IF EXISTS "security"."fraud_alerts"')
    op.execute('DROP TABLE IF EXISTS "commerce"."flash_sales"')
    op.execute('DROP TABLE IF EXISTS "commerce"."flash_sale_items"')
    op.execute('DROP TABLE IF EXISTS "finance"."fixed_assets"')
    op.execute('DROP TABLE IF EXISTS "finance"."fiscal_periods"')
    op.execute('DROP TABLE IF EXISTS "analytics"."financial_reports"')
    op.execute('DROP TABLE IF EXISTS "finance"."finance_reports"')
    op.execute('DROP TABLE IF EXISTS "finance"."finance_dashboard_metrics"')
    op.execute('DROP TABLE IF EXISTS "treasury"."finance_bank_accounts"')
    op.execute('DROP TABLE IF EXISTS "finance"."finance_automation_logs"')
    op.execute('DROP TABLE IF EXISTS "finance"."finance_audit_logs"')
    op.execute('DROP TABLE IF EXISTS "configuration"."feature_flags"')
    op.execute('DROP TABLE IF EXISTS "communication"."faqs"')
    op.execute('DROP TABLE IF EXISTS "communication"."external_contact_masking"')
    op.execute('DROP TABLE IF EXISTS "analytics"."executive_news"')
    op.execute('DROP TABLE IF EXISTS "configuration"."event_retry_queue"')
    op.execute('DROP TABLE IF EXISTS "configuration"."event_dead_letter"')
    op.execute('DROP TABLE IF EXISTS "communication"."escalation_sla_rules"')
    op.execute('DROP TABLE IF EXISTS "customer"."escalation_sla_logs"')
    op.execute('DROP TABLE IF EXISTS "finance"."erp_transactions"')
    op.execute('DROP TABLE IF EXISTS "customer"."entity_chat_threads"')
    op.execute('DROP TABLE IF EXISTS "communication"."entity_chat_messages"')
    op.execute('DROP TABLE IF EXISTS "hr"."employees"')
    op.execute('DROP TABLE IF EXISTS "hr"."employee_work_logs"')
    op.execute('DROP TABLE IF EXISTS "hr"."employee_travel_requests"')
    op.execute('DROP TABLE IF EXISTS "hr"."employee_trainings"')
    op.execute('DROP TABLE IF EXISTS "hr"."employee_shift_rosters"')
    op.execute('DROP TABLE IF EXISTS "hr"."employee_roles"')
    op.execute('DROP TABLE IF EXISTS "hr"."employee_relations"')
    op.execute('DROP TABLE IF EXISTS "hr"."employee_leave_requests"')
    op.execute('DROP TABLE IF EXISTS "hr"."employee_leave_ledgers"')
    op.execute('DROP TABLE IF EXISTS "hr"."employee_expenses"')
    op.execute('DROP TABLE IF EXISTS "hr"."employee_documents"')
    op.execute('DROP TABLE IF EXISTS "hr"."employee_dependents"')
    op.execute('DROP TABLE IF EXISTS "communication"."employee_communication_threads"')
    op.execute('DROP TABLE IF EXISTS "hr"."employee_certifications"')
    op.execute('DROP TABLE IF EXISTS "hr"."employee_biometrics"')
    op.execute('DROP TABLE IF EXISTS "hr"."employee_attendance"')
    op.execute('DROP TABLE IF EXISTS "hr"."employee_assets"')
    op.execute('DROP TABLE IF EXISTS "hr"."employee_addresses"')
    op.execute('DROP TABLE IF EXISTS "security"."email_verification_tokens"')
    op.execute('DROP TABLE IF EXISTS "communication"."email_templates"')
    op.execute('DROP TABLE IF EXISTS "communication"."email_suppressions"')
    op.execute('DROP TABLE IF EXISTS "configuration"."email_runtime_config"')
    op.execute('DROP TABLE IF EXISTS "configuration"."email_provider_configs"')
    op.execute('DROP TABLE IF EXISTS "communication"."email_folders"')
    op.execute('DROP TABLE IF EXISTS "communication"."email_delivery_events"')
    op.execute('DROP TABLE IF EXISTS "communication"."email_campaigns"')
    op.execute('DROP TABLE IF EXISTS "communication"."email_campaign_logs"')
    op.execute('DROP TABLE IF EXISTS "hr"."dynamic_qr_sessions"')
    op.execute('DROP TABLE IF EXISTS "security"."document_verifications"')
    op.execute('DROP TABLE IF EXISTS "security"."dlp_violations"')
    op.execute('DROP TABLE IF EXISTS "hr"."disciplinary_cases"')
    op.execute('DROP TABLE IF EXISTS "customer"."direct_chat_rooms"')
    op.execute('DROP TABLE IF EXISTS "communication"."direct_chat_messages"')
    op.execute('DROP TABLE IF EXISTS "security"."device_fingerprints"')
    op.execute('DROP TABLE IF EXISTS "hr"."data_residency_records"')
    op.execute('DROP TABLE IF EXISTS "logistics"."customs_entries"')
    op.execute('DROP TABLE IF EXISTS "finance"."customers"')
    op.execute('DROP TABLE IF EXISTS "configuration"."cross_country_customer_sessions"')
    op.execute('DROP TABLE IF EXISTS "security"."credit_card_bins"')
    op.execute('DROP TABLE IF EXISTS "commerce"."coupons"')
    op.execute('DROP TABLE IF EXISTS "commerce"."coupon_usage"')
    op.execute('DROP TABLE IF EXISTS "country"."country_tax"')
    op.execute('DROP TABLE IF EXISTS "configuration"."country_staff_assignments"')
    op.execute('DROP TABLE IF EXISTS "configuration"."country_payout_rules"')
    op.execute('DROP TABLE IF EXISTS "configuration"."country_payment_aliases"')
    op.execute('DROP TABLE IF EXISTS "hr"."country_map_configs"')
    op.execute('DROP TABLE IF EXISTS "configuration"."country_logistics_zones"')
    op.execute('DROP TABLE IF EXISTS "configuration"."country_localization"')
    op.execute('DROP TABLE IF EXISTS "configuration"."country_legal_contracts"')
    op.execute('DROP TABLE IF EXISTS "country"."country_legal"')
    op.execute('DROP TABLE IF EXISTS "configuration"."country_holiday_calendars"')
    op.execute('DROP TABLE IF EXISTS "country"."country_gateway_credentials"')
    op.execute('DROP TABLE IF EXISTS "configuration"."country_gateway_configs"')
    op.execute('DROP TABLE IF EXISTS "configuration"."country_feature_flags"')
    op.execute('DROP TABLE IF EXISTS "country"."country_economics"')
    op.execute('DROP TABLE IF EXISTS "country"."country_configs"')
    op.execute('DROP TABLE IF EXISTS "configuration"."country_config_versions"')
    op.execute('DROP TABLE IF EXISTS "country"."country_communications"')
    op.execute('DROP TABLE IF EXISTS "configuration"."country_communication_threads"')
    op.execute('DROP TABLE IF EXISTS "configuration"."country_commission_rates"')
    op.execute('DROP TABLE IF EXISTS "configuration"."country_commission_rate_history"')
    op.execute('DROP TABLE IF EXISTS "country"."country_cities"')
    op.execute('DROP TABLE IF EXISTS "configuration"."country_category_tax_rates"')
    op.execute('DROP TABLE IF EXISTS "country"."country_basics"')
    op.execute('DROP TABLE IF EXISTS "finance"."cost_centers"')
    op.execute('DROP TABLE IF EXISTS "communication"."communication_audit_trail"')
    op.execute('DROP TABLE IF EXISTS "commerce"."commission_rules"')
    op.execute('DROP TABLE IF EXISTS "commerce"."commission_ledger_entries"')
    op.execute('DROP TABLE IF EXISTS "commerce"."commission_global_configs"')
    op.execute('DROP TABLE IF EXISTS "commerce"."commission_category_rates"')
    op.execute('DROP TABLE IF EXISTS "commerce"."commission_badge_tiers"')
    op.execute('DROP TABLE IF EXISTS "commerce"."commission_agreements"')
    op.execute('DROP TABLE IF EXISTS "audit"."command_center_views"')
    op.execute('DROP TABLE IF EXISTS "hr"."coi_reports"')
    op.execute('DROP TABLE IF EXISTS "logistics"."city_distance_matrix"')
    op.execute('DROP TABLE IF EXISTS "audit"."chatbot_query_events"')
    op.execute('DROP TABLE IF EXISTS "communication"."chat_read_receipts"')
    op.execute('DROP TABLE IF EXISTS "communication"."chat_attachments"')
    op.execute('DROP TABLE IF EXISTS "commerce"."categories"')
    op.execute('DROP TABLE IF EXISTS "treasury"."cash_transactions"')
    op.execute('DROP TABLE IF EXISTS "treasury"."cash_position_snapshots"')
    op.execute('DROP TABLE IF EXISTS "treasury"."cash_flow_forecasts"')
    op.execute('DROP TABLE IF EXISTS "treasury"."cash_accounts"')
    op.execute('DROP TABLE IF EXISTS "commerce"."carts"')
    op.execute('DROP TABLE IF EXISTS "commerce"."cart_items"')
    op.execute('DROP TABLE IF EXISTS "communication"."campaign_recipients"')
    op.execute('DROP TABLE IF EXISTS "finance"."budgets"')
    op.execute('DROP TABLE IF EXISTS "commerce"."banners"')
    op.execute('DROP TABLE IF EXISTS "finance"."bank_transactions"')
    op.execute('DROP TABLE IF EXISTS "finance"."bank_statement_lines"')
    op.execute('DROP TABLE IF EXISTS "finance"."bank_statement_imports"')
    op.execute('DROP TABLE IF EXISTS "finance"."bank_reconciliations"')
    op.execute('DROP TABLE IF EXISTS "finance"."bank_mapping_rules"')
    op.execute('DROP TABLE IF EXISTS "finance"."bank_accounts"')
    op.execute('DROP TABLE IF EXISTS "commerce"."badge_transactions"')
    op.execute('DROP TABLE IF EXISTS "commerce"."badge_tiers"')
    op.execute('DROP TABLE IF EXISTS "commerce"."badge_billing_records"')
    op.execute('DROP TABLE IF EXISTS "finance"."automation_rules"')
    op.execute('DROP TABLE IF EXISTS "finance"."automation_logs"')
    op.execute('DROP TABLE IF EXISTS "audit"."audit_logs"')
    op.execute('DROP TABLE IF EXISTS "finance"."ar_ledger_entries"')
    op.execute('DROP TABLE IF EXISTS "finance"."ar_invoices"')
    op.execute('DROP TABLE IF EXISTS "hr"."approval_requests"')
    op.execute('DROP TABLE IF EXISTS "security"."api_keys"')
    op.execute('DROP TABLE IF EXISTS "finance"."ap_ledger_entries"')
    op.execute('DROP TABLE IF EXISTS "finance"."ap_bills"')
    op.execute('DROP TABLE IF EXISTS "communication"."announcements"')
    op.execute('DROP TABLE IF EXISTS "hr"."alumni_network"')
    op.execute('DROP TABLE IF EXISTS "security"."alert_escalation_rules"')
    op.execute('DROP TABLE IF EXISTS "ai"."ai_upload_jobs"')
    op.execute('DROP TABLE IF EXISTS "ai"."ai_staging_variants"')
    op.execute('DROP TABLE IF EXISTS "ai"."ai_staging_products"')
    op.execute('DROP TABLE IF EXISTS "ai"."ai_staging_images"')
    op.execute('DROP TABLE IF EXISTS "ai"."ai_results"')
    op.execute('DROP TABLE IF EXISTS "ai"."ai_requests"')
    op.execute('DROP TABLE IF EXISTS "ai"."ai_generation_logs"')
    op.execute('DROP TABLE IF EXISTS "ai"."ai_embeddings"')
    op.execute('DROP TABLE IF EXISTS "ai"."ai_audit_log"')
    op.execute('DROP TABLE IF EXISTS "audit"."admin_change_audit_logs"')
    op.execute('DROP TABLE IF EXISTS "audit"."admin_analytics_snapshots"')
    op.execute('DROP TABLE IF EXISTS "audit"."admin_activity_logs"')
    op.execute('DROP TABLE IF EXISTS "customer"."addresses"')
    op.execute('DROP TABLE IF EXISTS "hr"."activity_logs"')
    op.execute('DROP TABLE IF EXISTS "finance"."accruals"')
    op.execute('DROP TABLE IF EXISTS "finance"."accounts"')
    op.execute('DROP TABLE IF EXISTS "finance"."account_groups"')
    op.execute('DROP TABLE IF EXISTS "finance"."account_balances"')

