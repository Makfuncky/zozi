import os
os.environ.setdefault("SECRET_KEY", "verify-fk-completeness-secret")

from sqlalchemy import create_engine, inspect
from sqlalchemy.schema import CreateTable
import models  # noqa: F401  (triggers model registration on Base.metadata)

META = models.Base.metadata

# Build table_name -> schema map (only schema'd tables matter)
name_schema = {}
for t in META.tables.values():
    if t.schema:
        name_schema[t.name] = t.schema
print(f"TOTAL TABLES: {len(META.tables)}  SCHEMA'D: {len(name_schema)}")

unqualified = []

def check_target(target):
    # target like 'schema.table.column' or 'table.column'
    parts = target.split(".")
    if len(parts) == 3:
        return  # already qualified
    if len(parts) == 2:
        tbl = parts[0]
        if tbl in name_schema:
            unqualified.append(target)

for table in META.tables.values():
    for col in table.columns:
        for fk in col.foreign_keys:
            check_target(fk.target_fullname)
    for constraint in table.constraints:
        from sqlalchemy import ForeignKeyConstraint
        if isinstance(constraint, ForeignKeyConstraint):
            for tgt in constraint.elements:
                check_target(tgt.target_fullname)

print(f"UNQUALIFIED SCHEMA'D FK TARGETS: {len(unqualified)}")
for u in sorted(set(unqualified)):
    print("  -", u)

# Definitive create_all regression test with schema stripping (SQLite has no schemas)
engine = create_engine("sqlite://")
conn = engine.connect()
try:
    META.create_all(engine.execution_options(schema_translate_map={s: None for s in set(name_schema.values())}))
    print("CREATE_ALL_OK (all FK targets resolved)")
except Exception as e:
    print("CREATE_ALL_FAIL:", type(e).__name__, str(e)[:300])
finally:
    conn.close()
