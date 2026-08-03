import sys
import json
sys.path.insert(0, '.')
from sqlalchemy import inspect
from data.db import engine

inspector = inspect(engine)
schemas = [s for s in inspector.get_schema_names() if not s.startswith('_') and s not in ['pg_catalog', 'information_schema']]

cross_schema_fks = []
for schema in schemas:
    tables = inspector.get_table_names(schema=schema)
    for table in tables:
        fks = inspector.get_foreign_keys(table, schema=schema)
        for fk in fks:
            if fk.get('referred_schema') and fk['referred_schema'] != schema:
                cross_schema_fks.append({
                    'source_table': f'{schema}.{table}',
                    'column': fk['constrained_columns'],
                    'target_table': f"{fk['referred_schema']}.{fk['referred_table']}"
                })

print(f'Total cross-schema FKs: {len(cross_schema_fks)}')

# Categorize
categories = {
    'authorization': [],  # Users/roles/permissions across schemas
    'core_identity': [],  # User IDs referenced by many tables
    'product_hierarchy': [],  # Products/categories across schemas
    'order_flow': [],  # Orders/order_items across schemas
    'geolocation': [],  # Country/city references
    'cross_ecosystem': [],  # Other intentional cross-schema FKs
}

# High-risk tables
high_risk_tables = {
    'core.users', 'commerce.products', 'orders.orders', 
    'orders.order_items', 'core.permissions', 'commerce.commission_rules'
}

for fk in cross_schema_fks:
    source = fk['source_table']
    target = fk['target_table']
    
    if 'users' in source.lower() or 'users' in target.lower():
        categories['core_identity'].append(fk)
    elif 'product' in source.lower() or 'product' in target.lower():
        categories['product_hierarchy'].append(fk)
    elif 'order' in source.lower() or 'order' in target.lower():
        categories['order_flow'].append(fk)
    elif 'country' in source.lower() or 'country' in target.lower():
        categories['geolocation'].append(fk)
    elif 'permission' in source.lower() or 'permission' in target.lower():
        categories['authorization'].append(fk)
    else:
        categories['cross_ecosystem'].append(fk)

for cat, items in categories.items():
    print(f'{cat}: {len(items)} FKs')

# Save to file
with open('cross_schema_fk_analysis.json', 'w') as f:
    json.dump({
        'total_count': len(cross_schema_fks),
        'categories': categories,
        'high_risk_examples': [fk for fk in cross_schema_fks if fk['source_table'] in high_risk_tables][:10]
    }, f, indent=2)

print()
print('Analysis saved to cross_schema_fk_analysis.json')