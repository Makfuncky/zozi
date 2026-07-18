"""Widen bounded encrypted columns to ciphertext-safe storage sizes.

Revision ID: h1j2k3l4m5n6
Revises: f1a2b3c4d5e6
Create Date: 2026-04-11 22:45:00.000000
"""

from __future__ import annotations

from contextlib import contextmanager

from alembic import op
import sqlalchemy as sa
import utils.encryption


# revision identifiers, used by Alembic.
revision = 'h1j2k3l4m5n6'
down_revision = "f1a2b3c4d5e6"
branch_labels = None
depends_on = None


_BOUNDED_ENCRYPTED_COLUMNS: tuple[tuple[str, str, int], ...] = (
    ("users", "phone", 100),
    ("addresses", "city", 120),
    ("addresses", "state", 120),
    ("addresses", "postal_code", 50),
    ("email_provider_configs", "resend_api_key", 500),
    ("email_provider_configs", "resend_webhook_secret", 500),
    ("email_provider_configs", "smtp_password", 500),
    ("finance_bank_accounts", "beneficiary_name", 255),
    ("finance_bank_accounts", "account_number", 120),
    ("finance_bank_accounts", "iban", 120),
    ("finance_bank_accounts", "swift_code", 120),
    ("finance_bank_accounts", "routing_number", 120),
    ("finance_bank_accounts", "support_email", 255),
    ("finance_bank_accounts", "support_phone", 80),
    ("logistics_partners", "contact_email", 255),
    ("logistics_partners", "contact_phone", 80),
    ("payment_gateway_connections", "secret_key", 1000),
    ("payment_gateway_connections", "webhook_secret", 1000),
    ("payouts", "reference", 255),
    ("supplier_bank_accounts", "beneficiary_name", 255),
    ("supplier_bank_accounts", "account_number", 120),
    ("supplier_bank_accounts", "iban", 120),
    ("supplier_bank_accounts", "swift_code", 120),
    ("supplier_bank_accounts", "routing_number", 120),
    ("supplier_profiles", "postal_code", 50),
    ("supplier_profiles", "phone_business", 60),
    ("supplier_profiles", "tax_id", 150),
    ("logistics_partner_bank_accounts", "beneficiary_name", 255),
    ("logistics_partner_bank_accounts", "account_number", 120),
    ("logistics_partner_bank_accounts", "iban", 120),
    ("logistics_partner_bank_accounts", "swift_code", 120),
    ("logistics_partner_bank_accounts", "routing_number", 120),
    ("logistics_partner_payouts", "reference", 255),
    ("orders", "customer_phone", 60),
    ("shipment_confirmations", "current_hub", 200),
    ("shipment_events", "location", 255),
)


def _column_lookup(inspector: sa.Inspector, table_name: str) -> dict[str, dict[str, object]]:
    if table_name not in inspector.get_table_names():
        return {}
    return {column["name"]: column for column in inspector.get_columns(table_name)}


@contextmanager
def _sqlite_foreign_keys_disabled(bind: sa.Connection):
    if bind.dialect.name != "sqlite":
        yield
        return

    previous = bool(bind.exec_driver_sql("PRAGMA foreign_keys").scalar())
    with op.get_context().autocommit_block():
        bind.exec_driver_sql("PRAGMA foreign_keys=OFF")

    try:
        yield
    finally:
        with op.get_context().autocommit_block():
            bind.exec_driver_sql(f"PRAGMA foreign_keys={'ON' if previous else 'OFF'}")


def _alter_column(table_name: str, column_name: str, plaintext_length: int, *, encrypt: bool) -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    column_info = _column_lookup(inspector, table_name).get(column_name)
    if column_info is None:
        return

    if bind.dialect.name == "sqlite":
        op.execute(sa.text(f"DROP TABLE IF EXISTS _alembic_tmp_{table_name}"))

    target_type: sa.types.TypeEngine
    if encrypt:
        target_type = utils.encryption.EncryptedString(length=plaintext_length)
    else:
        target_type = sa.String(length=plaintext_length)

    with _sqlite_foreign_keys_disabled(bind):
        with op.batch_alter_table(table_name, schema=None) as batch_op:
            batch_op.alter_column(
                column_name,
                existing_type=sa.String(length=plaintext_length),
                type_=target_type,
                existing_nullable=bool(column_info.get("nullable", True)),
            )


def upgrade() -> None:
    for table_name, column_name, plaintext_length in _BOUNDED_ENCRYPTED_COLUMNS:
        _alter_column(table_name, column_name, plaintext_length, encrypt=True)


def downgrade() -> None:
    for table_name, column_name, plaintext_length in reversed(_BOUNDED_ENCRYPTED_COLUMNS):
        _alter_column(table_name, column_name, plaintext_length, encrypt=False)

