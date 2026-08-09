"""Verify syntax of all model files."""
import ast
from pathlib import Path

MODELS_DIR = Path("D:/Projects/10- E-COMMERCE WEBSITE/zozi/backend/models")
errors = []
for f in sorted(MODELS_DIR.glob("*.py")):
    if f.name.startswith("_"):
        continue
    try:
        ast.parse(f.read_text(encoding="utf-8"))
    except SyntaxError as e:
        errors.append((f.name, e))

if errors:
    for name, e in errors:
        print(f"SYNTAX ERROR in {name}: {e}")
else:
    print("All model files have valid Python syntax.")
