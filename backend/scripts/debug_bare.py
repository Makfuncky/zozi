import re
import json
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
SCHEMA_MAPPING_PATH = BACKEND_DIR / "docs" / "schema_mapping.json"
with SCHEMA_MAPPING_PATH.open("r", encoding="utf-8") as f:
    SCHEMA_MAPPING = json.load(f)

text = Path("D:/Projects/10- E-COMMERCE WEBSITE/zozi/backend/models/admin.py").read_text(encoding="utf-8")

def add_schema_to_class(content):
    result = []
    i = 0
    n = len(content)
    changes = 0

    while i < n:
        m = re.search(r'class\s+\w+\(Base\):\s*\n\s*__tablename__\s*=\s*"([^"]+)"', content[i:])
        if not m:
            result.append(content[i:])
            break

        match_start = i + m.start()
        match_end = i + m.end()
        tablename = m.group(1)
        print(f"Found class: {tablename} at {match_start}-{match_end}")
        result.append(content[i:match_end])

        remaining = content[match_start + m.end():]
        next_class = re.search(r'\nclass\s+\w+\(', remaining)
        class_end = next_class.start() if next_class else len(remaining)
        class_body = remaining[:class_end]

        if "__table_args__" in class_body:
            print(f"  -> already has __table_args__, skipping")
            result.append(class_body)
            i = match_start + m.end() + class_end
            continue

        schema = SCHEMA_MAPPING.get(tablename)
        if not schema or schema == "public":
            print(f"  -> no schema mapping, skipping")
            result.append(class_body)
            i = match_start + m.end() + class_end
            continue

        indent = re.search(r'\n(\s*)', class_body)
        indent_str = indent.group(1) if indent else "    "
        print(f"  -> adding schema: {schema}, indent: {repr(indent_str)}")
        new_args = f"\n{indent_str}__table_args__ = ({{\"schema\": \"{schema}\"}},)"
        result.append(new_args + class_body)
        changes += 1
        i = match_start + m.end() + class_end

    return ''.join(result), changes

new_content, changes = add_schema_to_class(text)
print(f"\nTotal changes: {changes}")
print("First 500 chars of result:")
print(repr(new_content[:500]))
