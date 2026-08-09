import re
from pathlib import Path

text = Path("D:/Projects/10- E-COMMERCE WEBSITE/zozi/backend/models/admin.py").read_text(encoding="utf-8")

# Simulate the add_schema_to_class logic for SystemAlert
m = re.search(r'class\s+\w+\(Base\):\s*\n\s*__tablename__\s*=\s*"([^"]+)"', text)
if m:
    print("match:", repr(m.group(0)[:80]))
    print("match start:", m.start())
    print("match end:", m.end())
    remaining = text[m.end():]
    print("remaining start:", repr(remaining[:80]))
    
    next_class = re.search(r'\nclass\s+\w+\(', remaining)
    print("next_class found:", next_class is not None)
    if next_class:
        class_end = next_class.start()
        print("class_end:", class_end)
    else:
        class_end = len(remaining)
    
    class_body = remaining[:class_end]
    print("class_body start:", repr(class_body[:80]))
    print("class_body has __table_args__:", "__table_args__" in class_body)
