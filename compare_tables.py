import re, os, glob

# Extract table names from models
model_files = glob.glob('backend/domains/*/models/*.py')
model_tables = {}

for mf in sorted(model_files):
    with open(mf, 'r', encoding='utf-8') as f:
        content = f.read()
    tables = re.findall(r"__tablename__ = ['\"]([^'\"]+)['\"]", content)
    for t in tables:
        model_tables[t] = mf

# Extract table names from migrations
migrations = glob.glob('backend/alembic/versions/*.py')
migration_tables = set()

for mig in sorted(migrations):
    with open(mig, 'r', encoding='utf-8') as f:
        content = f.read()
    for m in re.finditer(r"create_table\(['\"](\w+)['\"\],]", content):
        migration_tables.add(m.group(1))
    for m in re.finditer(r"add_column\(['\"](\w+)['\"\],]", content):
        migration_tables.add(m.group(1))

# Find models not in migrations
model_only = set(model_tables.keys()) - migration_tables
migration_only = migration_tables - set(model_tables.keys())

print("=== MODELS WITHOUT MIGRATIONS ===")
for t in sorted(model_only):
    print(f"  {t}  <- {model_tables[t]}")

print(f"\nTotal model tables: {len(model_tables)}")
print(f"Total migration tables: {len(migration_tables)}")
print(f"Models missing migrations: {len(model_only)}")
print(f"Migrations for non-existent models: {len(migration_only)}")
