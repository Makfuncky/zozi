import os
import re
import json
from collections import defaultdict

fk_pattern = re.compile(r'ForeignKey\s*\(\s*["\']([^"\']+)["\']')

models_dir = 'models'
fk_refs = []

for filename in sorted(os.listdir(models_dir)):
    if not filename.endswith('.py'):
        continue
    
    filepath = os.path.join(models_dir, filename)
    with open(filepath, 'r') as f:
        lines = f.readlines()
    
    source_table = filename.replace('.py', '')
    if source_table == '__init__':
        continue
    
    for i, line in enumerate(lines):
        match = fk_pattern.search(line)
        if match:
            fk_ref = match.group(1)
            if '.' in fk_ref:
                col_match = re.match(r'\s*(\w+)\s*=', line.strip())
                if col_match:
                    col_name = col_match.group(1)
                    # Determine source schema from filename patterns
                    source_schema = None
                    for s in ['admin', 'ai', 'analytics', 'audit', 'communication', 'configuration', 
                             'core', 'country', 'customer', 'finance', 'hr', 'logistics', 
                             'media', 'security', 'supplier', 'trading', 'treasury']:
                        if s in filename:
                            source_schema = s
                            break
                    
                    if not source_schema and source_table in ['countries', 'employee_models', 'media_models']:
                        # Handle special cases
                        if 'countries' in source_table:
                            source_schema = 'country'
                        elif 'employee' in source_table:
                            source_schema = 'hr'
                        elif 'media' in source_table:
                            source_schema = 'media'
                    
                    target_schema = fk_ref.split('.')[0] if '.' in fk_ref else None
                    
                    is_cross_schema = source_schema and target_schema and source_schema != target_schema
                    
                    fk_refs.append({
                        'source_table': source_table,
                        'source_schema': source_schema,
                        'source_column': col_name,
                        'target': fk_ref,
                        'target_schema': target_schema,
                        'is_cross_schema': is_cross_schema,
                        'source_file': filename
                    })

# Total counts
total = len(fk_refs)
cross_schema_count = sum(1 for f in fk_refs if f['is_cross_schema'])

print(f'Total FK column references: {total}')
print(f'Cross-schema FK columns: {cross_schema_count}')
print()

# Analyze by source schema
by_source = defaultdict(list)
for ref in fk_refs:
    if ref['source_schema']:
        by_source[ref['source_schema']].append(ref)

print('FKs by source schema:')
for schema in sorted(by_source.keys()):
    print(f'  {schema}: {len(by_source[schema])}')
print()

# Analyze target schemas
by_target = defaultdict(list)
for ref in fk_refs:
    if ref['target_schema']:
        by_target[ref['target_schema']].append(ref)

print('FKs by target schema:')
for schema in sorted(by_target.keys()):
    print(f'  {schema}: {len(by_target[schema])}')
print()

# High-risk analysis: core.users.id is referenced 284 times
# This is a critical FK that many tables depend on
core_users_refs = [f for f in fk_refs if 'core.users' in f['target']]
print(f'core.users.id references: {len(core_users_refs)}')
print('  Most common source tables:')
source_counts = defaultdict(int)
for r in core_users_refs:
    source_counts[r['source_table']] += 1
for s, c in sorted(source_counts.items(), key=lambda x: -x[1])[:10]:
    print(f'    {s}: {c}')

# commerce.products.id references
products_refs = [f for f in fk_refs if 'commerce.products.id' in f['target']]
print(f'commerce.products.id references: {len(products_refs)}')

# commerce.orders.id references  
orders_refs = [f for f in fk_refs if 'commerce.orders.id' in f['target']]
print(f'commerce.orders.id references: {len(orders_refs)}')

# country.country_configs.code references (for country_code columns)
country_refs = [f for f in fk_refs if 'country.country_configs.code' in f['target'] or 'country.country_basics' in f['target']]
print(f'country.* references: {len(country_refs)}')

# Save to file
output = {
    'summary': {
        'total_fk_columns': total,
        'cross_schema_count': cross_schema_count
    },
    'by_source_schema': {k: len(v) for k, v in sorted(by_source.items())},
    'by_target_schema': {k: len(v) for k, v in sorted(by_target.items())},
    'high_risk': {
        'core_users_id': len(core_users_refs),
        'commerce_products_id': len(products_refs),
        'commerce_orders_id': len(orders_refs),
        'commerce_order_items_id': len([f for f in fk_refs if 'commerce.order_items.id' in f['target']]),
        'country_refs': len(country_refs)
    },
    'detail': fk_refs
}

with open('cross_schema_fk_analysis.json', 'w') as f:
    json.dump(output, f, indent=2, default=str)

print()
print('Analysis saved to cross_schema_fk_analysis.json')