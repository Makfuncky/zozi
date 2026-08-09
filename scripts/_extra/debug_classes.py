import re
from pathlib import Path

text = Path("D:/Projects/10- E-COMMERCE WEBSITE/zozi/backend/models/admin.py").read_text(encoding="utf-8")

# Find all class matches
for m in re.finditer(r'class\s+\w+\(Base\):\s*\n\s*__tablename__\s*=\s*"([^"]+)"', text):
    tablename = m.group(1)
    remaining = text[m.end():]
    next_class = re.search(r'\nclass\s+\w+\(', remaining)
    class_end = next_class.start() if next_class else len(remaining)
    class_body = remaining[:class_end]
    has_table_args = "__table_args__" in class_body
    print(f"{tablename}: has __table_args__ = {has_table_args}, class_body starts with: {repr(class_body[:60])}")
