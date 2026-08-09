"""Regenerate backend/utils/analyze_fks.py with main() guard (no import side effects)."""
from pathlib import Path

CONTENT = '''"""Cross-schema foreign-key analysis tool (CLI only).

Importing this module has NO side effects — all inspection and output is
deferred to :func:`main`, which runs only when executed directly:

    python -m utils.analyze_fks
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, '.')

from sqlalchemy import inspect  # noqa: E402

from data.db import engine  # noqa: E402


# High-risk tables
HIGH_RISK_TABLES = {
    'core.users', 'commerce.products', 'orders.orders',
    'orders.order_items', 'core.permissions', 'commerce.commission_rules'
}


def categorize(fk: dict) -> str:
    """Bucket a foreign key into an audit category based on its tables."""
    source = fk['source_table'].lower()
    target = fk['target_table'].lower()
    if 'users' in source or 'users' in target:
        return 'core_identity'
    if 'product' in source or 'product' in target:
        return 'product_hierarchy'
    if 'order' in source or 'order' in target:
        return 'order_flow'
    if 'country' in source or 'country' in target:
        return 'geolocation'
    if 'permission' in source or 'permission' in target:
        return 'authorization'
    return 'cross_ecosystem'


def collect_cross_schema_fks() -> list:
    """Return all foreign keys whose referred schema differs from the source."""
    inspector = inspect(engine)
    schemas = [
        s for s in inspector.get_schema_names()
        if not s.startswith('_') and s not in ('pg_catalog', 'information_schema')
    ]
    cross_schema_fks = []
    for schema in schemas:
        for table in inspector.get_table_names(schema=schema):
            for fk in inspector.get_foreign_keys(table, schema=schema):
                if fk.get('referred_schema') and fk['referred_schema'] != schema:
                    cross_schema_fks.append({
                        'source_table': f'{schema}.{table}',
                        'column': fk['constrained_columns'],
                        'target_table': f"{fk['referred_schema']}.{fk['referred_table']}",
                    })
    return cross_schema_fks


def main() -> None:
    """Run the analysis and write the JSON artifact to the out/ directory."""
    cross_schema_fks = collect_cross_schema_fks()
    print(f'Total cross-schema FKs: {len(cross_schema_fks)}')

    categories = {
        'authorization': [],
        'core_identity': [],
        'product_hierarchy': [],
        'order_flow': [],
        'geolocation': [],
        'cross_ecosystem': [],
    }
    for fk in cross_schema_fks:
        categories[categorize(fk)].append(fk)

    for cat, items in categories.items():
        print(f'{cat}: {len(items)} FKs')

    # Save to file (gitignored out/ dir so the artifact is not committed/flagged)
    out_dir = Path(__file__).resolve().parents[2] / 'out'
    out_dir.mkdir(parents=True, exist_ok=True)
    artifact = out_dir / 'cross_schema_fk_analysis.json'
    with open(artifact, 'w') as f:
        json.dump({
            'total_count': len(cross_schema_fks),
            'categories': categories,
            'high_risk_examples': [
                fk for fk in cross_schema_fks if fk['source_table'] in HIGH_RISK_TABLES
            ][:10],
        }, f, indent=2)

    print()
    print(f'Analysis saved to {artifact}')


if __name__ == '__main__':
    main()
'''

target = Path(r'D:/Projects/10- E-COMMERCE WEBSITE/zozi/backend/utils/analyze_fks.py')
target.write_text(CONTENT, encoding='utf-8')
print(f'Wrote {target} ({len(CONTENT.splitlines())} lines)')
