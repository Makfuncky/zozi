"""Check schema coverage in model files."""
import re
from pathlib import Path

MODELS_DIR = Path("D:/Projects/10- E-COMMERCE WEBSITE/zozi/backend/models")
for f in sorted(MODELS_DIR.glob("*.py")):
    if f.name.startswith("_"):
        continue
    text = f.read_text(encoding="utf-8")
    has_schema = '"schema"' in text.lower() or "'schema'" in text.lower()
    has_table_args = "__table_args__" in text
    if has_table_args and not has_schema:
        print(f"{f.name}: has __table_args__ but NO schema")
    elif has_table_args and has_schema:
        count = text.lower().count('"schema"') + text.lower().count("'schema'")
        print(f"{f.name}: has schema ({count} occurrences)")
