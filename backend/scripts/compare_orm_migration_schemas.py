import os
import re
import sys

os.environ.setdefault("SECRET_KEY", "test-key-for-phase-2")
os.environ.setdefault("FIELD_ENCRYPTION_KEY", "test-enc-key-32characters-long")
os.environ.setdefault("DATABASE_URL", "sqlite:///./test_compare.db")

sys.path.insert(0, ".")

from db.base import Base

orm_tables = {}
for k, v in Base.metadata.tables.items():
    if v.schema:
        orm_tables[k.split('.')[-1]] = v.schema

with open("alembic/versions/2026_07_30_0005-20260730_0005_bounded_context_schema_migration.py") as f:
    content = f.read()

match = re.search(r'TABLE_SCHEMA_MAP = \[(.*?)\]', content, re.DOTALL)
if match:
    pairs = re.findall(r'\("(\w+)", "(\w+)"\)', match.group(1))
    db_tables = dict(pairs)
else:
    db_tables = {}

orm_keys = set(orm_tables.keys())
db_keys = set(db_tables.keys())
missing_in_migration = orm_keys - db_keys
extra_in_migration = db_keys - orm_keys

print(f'ORM tables: {len(orm_tables)}')
print(f'Migration tables: {len(db_tables)}')
print(f'Missing from migration ({len(missing_in_migration)}): {sorted(missing_in_migration)}')
print(f'Extra in migration ({len(extra_in_migration)}): {sorted(extra_in_migration)}')

mismatches = []
for t in orm_keys & db_keys:
    if orm_tables[t] != db_tables[t]:
        mismatches.append((t, orm_tables[t], db_tables[t]))
if mismatches:
    print(f'Schema mismatches ({len(mismatches)}):')
    for m in mismatches:
        print(f'  {m[0]}: ORM={m[1]}, migration={m[2]}')
else:
    print('No schema mismatches on common tables.')

print(f'\nTotal match: {orm_keys == db_keys and len(mismatches) == 0}')
