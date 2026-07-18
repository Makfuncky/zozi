import sys
sys.path.insert(0, r"F:\Projects\10- E-COMMERCE WEBSITE\zozi\backend")
import importlib, os

# Collect all imports from db.schemas in router files
import re

router_dir = r"F:\Projects\10- E-COMMERCE WEBSITE\zozi\backend\routers"
schemas_imported = set()
for fname in sorted(os.listdir(router_dir)):
    if not fname.endswith(".py") or fname == "__init__.py":
        continue
    fpath = os.path.join(router_dir, fname)
    with open(fpath, encoding="utf-8") as f:
        content = f.read()
    # Find all "from db.schemas import ..." lines at top level
    for m in re.finditer(r"from db\.schemas import (.*)", content, re.MULTILINE):
        for name in m.group(1).split(","):
            name = name.strip()
            if name and name != "\\":
                # Handle "from db.schemas import ( ... )" with line continuations
                schemas_imported.add(name.split(" as ")[0].strip())

# Now check which exist
import db.schemas as s
all_schemas = set(n for n in dir(s) if not n.startswith("_"))

missing = schemas_imported - all_schemas
unknown = schemas_imported - missing  # actually imported

print(f"Routers import {len(schemas_imported)} unique names from db.schemas")
print(f"All {len(unknown)} of them exist in db.schemas (names confirmed)")
if missing:
    print(f"WARNING: {len(missing)} names in router imports NOT found in db.schemas:")
    for n in sorted(missing):
        print(f"  MISSING: {n}")
else:
    print("No missing schema names found.")

