import os
os.environ['APP_ENV'] = 'test'
os.environ['SECRET_KEY'] = 'test-secret-key-for-pytest-only'

from data.base import Base
import data.models

metadata = Base.metadata

# Build table_name -> schema mapping
table_schemas = {}
for t in metadata.tables.values():
    key = t.key
    if '.' in key:
        schema, name_part = key.split('.', 1)
        table_schemas[name_part] = schema
    else:
        table_schemas[t.name] = None

print("Table schemas:")
for name, schema in sorted(table_schemas.items()):
    if schema:
        print(f"  {name} -> {schema}")

# Patch FK references
patched = 0
for table in metadata.tables.values():
    for col in table.columns:
        for fk in col.foreign_keys:
            target = fk._colspec
            if isinstance(target, str) and '.' in target:
                parts = target.split('.')
                if len(parts) == 2:  # unqualified: "table.column"
                    tbl = parts[0]
                    if tbl in table_schemas:
                        schema = table_schemas[tbl]
                        if schema:
                            new_target = f"{schema}.{target}"
                            fk._colspec = new_target
                            fk._column_tokens = None
                            patched += 1

print(f"\nPatched {patched} FK references")

# Now try configure_mappers
from sqlalchemy.orm import configure_mappers
try:
    configure_mappers()
    print("configure_mappers succeeded")
except Exception as e:
    print(f"FAILED: {type(e).__name__}: {e}")
