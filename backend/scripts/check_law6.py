"""Check remaining Law 6 violations."""
from __future__ import annotations
import re
import pathlib

DOMAINS_DIR = pathlib.Path(r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend\domains")

print("=== Missing schema (within 500 chars) ===")
schema_offenders = []
for path in sorted(DOMAINS_DIR.rglob("models/*.py")):
    if path.name == "__init__.py":
        continue
    if "read_models" in str(path):
        continue
    source = path.read_text(encoding="utf-8")
    if "__tablename__" not in source:
        continue
    for m in re.finditer(r'__tablename__\s*=\s*["\']([^"\']+)["\']', source):
        table_name = m.group(1)
        if table_name == "alembic_version":
            continue
        schema_match = re.search(r"""['"]schema['"]:\s*['"]([^'"]+)['"]""", source[m.start():m.start()+500])
        if not schema_match:
            schema_offenders.append(f"{path.name}: {table_name}")

for o in sorted(set(schema_offenders)):
    print(f"  {o}")
print(f"  Total: {len(set(schema_offenders))}")

print("\n=== FK columns without _id suffix ===")
fk_offenders = []
for path in sorted(DOMAINS_DIR.rglob("models/*.py")):
    if path.name == "__init__.py":
        continue
    if "read_models" in str(path):
        continue
    source = path.read_text(encoding="utf-8")
    if "ForeignKey" not in source:
        continue
    for m in re.finditer(r'(\w+)\s*=\s*Column\([^)]*ForeignKey', source):
        col = m.group(1)
        if col == "id":
            continue
        if not col.endswith("_id"):
            fk_offenders.append((path.name, col))

for name, col in sorted(set(fk_offenders)):
    print(f"  {name}: {col}")
print(f"  Total: {len(set(fk_offenders))}")
