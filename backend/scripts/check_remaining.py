"""Check remaining files without schema."""
import json
import re
from pathlib import Path

BACKEND_DIR = Path("D:/Projects/10- E-COMMERCE WEBSITE/zozi/backend")
MODELS_DIR = BACKEND_DIR / "models"
SCHEMA_MAPPING_PATH = BACKEND_DIR / "docs" / "schema_mapping.json"

with SCHEMA_MAPPING_PATH.open("r", encoding="utf-8") as f:
    SCHEMA_MAPPING = json.load(f)

for py in sorted(MODELS_DIR.glob("*.py")):
    if py.name.startswith("_"):
        continue
    text = py.read_text(encoding="utf-8")
    for m in re.finditer(r"__table_args__\s*=\s*\(", text):
        start = m.start()
        preceding = text[:start]
        tablename_m = re.search(r'__tablename__\s*=\s*"([^"]+)"\s*$', preceding, re.MULTILINE)
        if not tablename_m:
            continue
        tablename = tablename_m.group(1)
        schema = SCHEMA_MAPPING.get(tablename)
        if not schema or schema == "public":
            continue
        depth = 1
        j = m.end()
        block = ""
        while j < len(text) and depth > 0:
            ch = text[j]
            if ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
            if depth > 0:
                block += ch
            j += 1
        if '"schema"' not in block.lower() and "'schema'" not in block.lower():
            print(f"{py.name}: {tablename} -> {schema}")
            break
