"""List models without __table_args__."""
from pathlib import Path

MODELS_DIR = Path("D:/Projects/10- E-COMMERCE WEBSITE/zozi/backend/models")
for f in sorted(MODELS_DIR.glob("*.py")):
    if f.name.startswith("_"):
        continue
    text = f.read_text(encoding="utf-8")
    if "__table_args__" not in text:
        print(f.name)
