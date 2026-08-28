"""Fix Law 6 schema discipline violations."""
from __future__ import annotations

import re
import pathlib

BACKEND_ROOT = pathlib.Path(__file__).resolve().parent.parent
DOMAINS_DIR = BACKEND_ROOT / "domains"

def get_domain(file_path):
    """Extract domain from file path relative to domains dir."""
    try:
        parts = file_path.relative_to(DOMAINS_DIR).parts
        return parts[0] if parts else None
    except ValueError:
        return None

def fix_schema_in_file(source, domain):
    """Add schema declaration to models missing it.

    Strategy: for each __tablename__ line, check if schema is declared
    within the next 500 chars. If not, add __table_args__ right after.
    """
    lines = source.split('\n')
    result = []
    i = 0

    while i < len(lines):
        line = lines[i]
        result.append(line)

        # Check if this line has __tablename__ assignment
        if re.search(r'__tablename__\s*=', line) and '=' in line:
            # Look ahead ~500 chars for schema declaration
            lookahead = '\n'.join(lines[i:i+25])
            has_schema = re.search(r"""['"]schema['"]\s*:\s*['"]""", lookahead)

            if not has_schema:
                # Get indentation of current line
                indent = len(line) - len(line.lstrip())
                indent_str = ' ' * indent
                result.append(f'{indent_str}__table_args__ = {{"schema": "{domain}"}}')

        i += 1

    return '\n'.join(result)


def fix_plural_tables(source):
    """Rename non-plural table names to plural."""
    # Map of non-plural -> plural table names
    plural_map = {
        'coupon_usage': 'coupon_usages',
        'communication_audit_trail': 'communication_audit_trails',
        'external_contact_masking': 'external_contact_maskings',
        'user_browsing_history': 'user_browsing_histories',
        'payment_orchestrator_sync': 'payment_orchestrator_syncs',
        'supplier_onboarding_sync': 'supplier_onboarding_syncs',
        'country_commission_rate_history': 'country_commission_rate_histories',
        'country_localization': 'country_localizations',
        'country_legal': 'country_legals',
        'country_tax': 'country_taxes',
        'alumni_network': 'alumni_networks',
        'employee_attendance': 'employee_attendances',
        'fraud_blacklist': 'fraud_blacklists',
        'manual_review_queue': 'manual_review_queues',
        'refund_ledger': 'refund_ledgers',
        'city_distance_matrix': 'city_distance_matrices',
        'email_runtime_config': 'email_runtime_configs',
        'product_filter_metadata': 'product_filter_metadatas',
        'supplier_badge_billing_history': 'supplier_badge_billing_histories',
        'supplier_badge_catalog': 'supplier_badge_catalogs',
        'user_login_history': 'user_login_histories',
    }

    for old, new in plural_map.items():
        source = re.sub(
            rf"(__tablename__\s*=\s*['\"]){re.escape(old)}(['\"])",
            rf"\g<1>{new}\2",
            source
        )

    return source


def fix_fk_columns(source):
    """Rename FK columns to use _id suffix."""
    # Map of column_name -> column_name_id
    fk_rename_map = {
        'created_by': 'created_by_id',
        'participant_one': 'participant_one_id',
        'participant_two': 'participant_two_id',
        'started_by': 'started_by_id',
        'adjusted_by': 'adjusted_by_id',
        'in_reply_to': 'in_reply_to_id',
        'received_by': 'received_by_id',
        'closed_by': 'closed_by_id',
        'deleted_by': 'deleted_by_id',
    }

    # Only rename columns that have ForeignKey
    # Pattern: col_name = Column(...ForeignKey
    for old_name, new_name in fk_rename_map.items():
        # Check if this column has a ForeignKey
        pattern = rf'({re.escape(old_name)}\s*=\s*Column\([^)]*ForeignKey)'
        if re.search(pattern, source):
            source = re.sub(
                rf'\b{re.escape(old_name)}\b',
                new_name,
                source
            )

    return source


def fix_timestamps(source):
    """Add updated_at to models missing it but having created_at."""
    if 'updated_at' in source:
        return source

    if 'created_at' not in source:
        return source

    # Add updated_at after created_at
    # Pattern: created_at = Column(...)})
    # We need to add updated_at right after created_at
    source = re.sub(
        r'(created_at\s*=\s*Column\([^)]+\))',
        r'\1\n    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=True)',
        source,
        count=1
    )

    return source


def main():
    model_files = []
    for path in sorted(DOMAINS_DIR.rglob("models/*.py")):
        if path.name == "__init__.py":
            continue
        if "read_models" in str(path):
            continue
        model_files.append(path)

    fixed_count = 0
    for path in model_files:
        domain = get_domain(path)
        if not domain:
            continue

        source = path.read_text(encoding="utf-8")
        if "__tablename__" not in source:
            continue

        new_source = source
        new_source = fix_schema_in_file(new_source, domain)
        new_source = fix_plural_tables(new_source)
        new_source = fix_fk_columns(new_source)
        new_source = fix_timestamps(new_source)

        if new_source != source:
            path.write_text(new_source, encoding="utf-8")
            fixed_count += 1
            print(f"  Fixed: {path.relative_to(BACKEND_ROOT)}")

    print(f"\nTotal files modified: {fixed_count}")


if __name__ == "__main__":
    main()
