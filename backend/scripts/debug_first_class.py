import re
import json
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
SCHEMA_MAPPING_PATH = BACKEND_DIR / "docs" / "schema_mapping.json"
with SCHEMA_MAPPING_PATH.open("r", encoding="utf-8") as f:
    SCHEMA_MAPPING = json.load(f)

text = Path("D:/Projects/10- E-COMMERCE WEBSITE/zozi/backend/models/admin.py").read_text(encoding="utf-8")

m = re.search(r'class\s+\w+\(Base\):\s*\n\s*__tablename__\s*=\s*"([^"]+)"', text)
if m:
    print("First match:", m.group(1))
    print("match end:", m.end())
    remaining = text[m.end():]
    print("remaining first 200 chars:", repr(remaining[:200]))
    
    next_class = re.search(r'\nclass\s+\w+\(', remaining)
    print("next_class found:", next_class is not None)
    if next_class:
        print("next_class start:", next_class.start())
        print("next_class match:", repr(next_class.group(0)[:40]))
        class_end = next_class.start()
    else:
        class_end = len(remaining)
    
    class_body = remaining[:class_end]
    print("class_body first 200 chars:", repr(class_body[:200]))
    print("has __table_args__:", "__table_args__" in class_body)
