import re, os, glob

migrations = glob.glob('backend/alembic/versions/*.py')
tables_in_migrations = set()

for mig in sorted(migrations):
    with open(mig, 'r', encoding='utf-8') as f:
        content = f.read()
    # find create_table and add_column patterns
    for m in re.finditer(r"create_table\(['\"](\w+)['\"\],]", content):
        tables_in_migrations.add(m.group(1))
    for m in re.finditer(r"add_column\(['\"](\w+)['\"\],]", content):
        tables_in_migrations.add(m.group(1))

print('Tables found in migrations:')
for t in sorted(tables_in_migrations):
    print(t)
print(f'\nTotal: {len(tables_in_migrations)}')
