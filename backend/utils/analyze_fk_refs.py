import os
import re
import json

cross_schema_fks = []
models_dir = 'models'

# Pattern to match ForeignKey definitions
fk_pattern = re.compile(r'ForeignKey\s*\(\s*["\']([^"\']+)["\']')

# Get all FK references from models
fk_refs = set()

for filename in os.listdir(models_dir):
    if not filename.endswith('.py'):
        continue
    
    filepath = os.path.join(models_dir, filename)
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Find all ForeignKey references
    for match in fk_pattern.finditer(content):
        fk_ref = match.group(1)
        if '.' in fk_ref:
            fk_refs.add(fk_ref)

# Categorize the FKs
categories = {
    'users_id': [],  # core.users.id referenced across schemas
    'geolocation': [],  # country.* references
    'products': [],  # commerce.products.id referenced
    'orders': [],  # commerce.orders/order_items referenced
    'logistics': [],  # logistics.* references
    'finance': [],  # finance.* references
    'supplier': [],  # supplier.* references
    'auth_permissions': [],  # core.users permissions, admin tables
    'other': []
}

for fk_ref in sorted(fk_refs):
    schema_table = fk_ref.split('.')[0]
    
    if 'users.id' in fk_ref:
        categories['users_id'].append(fk_ref)
    elif 'country_configs.code' in fk_ref or 'country_' in fk_ref:
        categories['geolocation'].append(fk_ref)
    elif 'products.id' in fk_ref or 'product_variants.id' in fk_ref:
        categories['products'].append(fk_ref)
    elif 'orders.id' in fk_ref or 'order_items.id' in fk_ref:
        categories['orders'].append(fk_ref)
    elif 'logistics_' in fk_ref:
        categories['logistics'].append(fk_ref)
    elif 'finance.' in fk_ref or 'treasury.' in fk_ref:
        categories['finance'].append(fk_ref)
    elif 'supplier_' in fk_ref:
        categories['supplier'].append(fk_ref)
    elif 'core.users' in fk_ref or 'permission' in fk_ref or 'admin_' in fk_ref:
        categories['auth_permissions'].append(fk_ref)
    else:
        categories['other'].append(fk_ref)

total = sum(len(v) for v in categories.values())
print(f'Total unique cross-schema FK targets: {total}')
print()

for cat, items in categories.items():
    print(f'{cat}: {len(items)} FKs')
    for item in items[:5]:
        print(f'  - {item}')
    if len(items) > 5:
        print(f'  ... and {len(items)-5} more')
    print()

# Save to file
with open('cross_schema_fk_analysis.json', 'w') as f:
    json.dump({
        'total_count': total,
        'categories': {k: v for k, v in categories.items()},
    }, f, indent=2)

print('Analysis saved to cross_schema_fk_analysis.json')