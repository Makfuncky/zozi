"""Comprehensive check of all model files for schema coverage."""
import ast
import re
import json
from pathlib import Path

BACKEND_DIR = Path("D:/Projects/10- E-COMMERCE WEBSITE/zozi/backend")
SCHEMA_MAPPING_PATH = BACKEND_DIR / "docs" / "schema_mapping.json"

with SCHEMA_MAPPING_PATH.open("r", encoding="utf-8") as f:
    SCHEMA_MAPPING = json.load(f)

# Find all Python files that might contain SQLAlchemy models
model_dirs = [
    BACKEND_DIR / "models",
    BACKEND_DIR / "db",
]

total_models = 0
missing_schema = []
errors = []

for model_dir in model_dirs:
    if not model_dir.exists():
        continue
    for py in sorted(model_dir.glob("*.py")):
        if py.name.startswith("_"):
            continue
        try:
            text = py.read_text(encoding="utf-8")
            ast.parse(text)
        except SyntaxError as e:
            errors.append((str(py), e))
            continue

        # Find all classes with __tablename__
        for m in re.finditer(r'class\s+(\w+)\(Base\):\s*\n\s*__tablename__\s*=\s*"([^"]+)"', text):
            class_name = m.group(1)
            tablename = m.group(2)
            total_models += 1

            # Check if __table_args__ exists in this class
            remaining = text[m.end():]
            next_class = re.search(r'\nclass\s+\w+\(', remaining)
            class_end = next_class.start() if next_class else len(remaining)
            class_body = remaining[:class_end]

            has_table_args = "__table_args__" in class_body
            has_schema = has_table_args and ('"schema"' in class_body.lower() or "'schema'" in class_body.lower())

            schema = SCHEMA_MAPPING.get(tablename)
            needs_schema = schema and schema != "public"

            if needs_schema and not has_schema:
                missing_schema.append((str(py), class_name, tablename, schema))

print(f"Total models found: {total_models}")
print(f"Missing schema: {len(missing_schema)}")
if missing_schema:
    for py, cls, tn, sc in missing_schema:
        print(f"  {py}: {cls} ({tn}) -> {sc}")

if errors:
    print(f"\nSyntax errors: {len(errors)}")
    for py, e in errors:
        print(f"  {py}: {e}")
else:
    print("No syntax errors.")
