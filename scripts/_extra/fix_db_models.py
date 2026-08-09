"""Add schema to db model files."""
import json
import re
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
DB_DIR = BACKEND_DIR / "db"
SCHEMA_MAPPING_PATH = BACKEND_DIR / "docs" / "schema_mapping.json"


def load_schema_mapping() -> dict[str, str]:
    with SCHEMA_MAPPING_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


SCHEMA_MAPPING = load_schema_mapping()


def add_schema_to_table_args(content: str) -> str:
    result = []
    i = 0
    n = len(content)
    changes = 0

    while i < n:
        m = re.search(r'__table_args__\s*=\s*\(', content[i:])
        if not m:
            result.append(content[i:])
            break

        match_start = i + m.start()
        match_end = i + m.end()
        result.append(content[i:match_end])

        depth = 1
        j = match_end
        while j < n and depth > 0:
            ch = content[j]
            if ch == '(':
                depth += 1
            elif ch == ')':
                depth -= 1
            j += 1

        if depth != 0:
            result.append(content[match_start:])
            break

        block = content[match_end : j - 1]

        preceding = content[:match_start]
        tablename_m = re.search(r'__tablename__\s*=\s*"([^"]+)"\s*$', preceding, re.MULTILINE)
        if not tablename_m:
            result.append(block + ')')
            i = j
            continue

        tablename = tablename_m.group(1)
        schema = SCHEMA_MAPPING.get(tablename)

        if not schema or schema == "public":
            result.append(block + ')')
            i = j
            continue

        if '"schema"' in block.lower() or "'schema'" in block.lower():
            result.append(block + ')')
            i = j
            continue

        stripped = block.rstrip()
        if stripped.endswith(','):
            new_block = stripped + ' {"schema": "' + schema + '"}'
        else:
            new_block = stripped + ', {"schema": "' + schema + '"}'

        result.append(new_block + ')')
        changes += 1
        i = j

    return ''.join(result), changes


def add_schema_to_bare_classes(content: str) -> str:
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
        result.append(content[i:match_end])

        remaining = content[match_end:]
        next_class = re.search(r'\nclass\s+\w+\(', remaining)
        class_end = next_class.start() if next_class else len(remaining)
        class_body = remaining[:class_end]

        if "__table_args__" in class_body:
            result.append(class_body)
            i = match_end + class_end
            continue

        schema = SCHEMA_MAPPING.get(tablename)
        if not schema or schema == "public":
            result.append(class_body)
            i = match_end + class_end
            continue

        indent = re.search(r'\n(\s*)', class_body)
        indent_str = indent.group(1) if indent else "    "
        new_args = f"\n{indent_str}__table_args__ = ({{\"schema\": \"{schema}\"}},)"
        result.append(new_args + class_body)
        changes += 1
        i = match_end + class_end

    return ''.join(result), changes


def fix_file(path: Path) -> bool:
    content = path.read_text(encoding="utf-8")
    new_content, c1 = add_schema_to_table_args(content)
    new_content, c2 = add_schema_to_bare_classes(new_content)
    if c1 + c2:
        path.write_text(new_content, encoding="utf-8")
    return (c1 + c2) > 0


def main():
    modified = []
    for py in sorted(DB_DIR.glob("*.py")):
        if py.name.startswith("_"):
            continue
        if fix_file(py):
            modified.append(py.name)

    print(f"Modified {len(modified)} files:")
    for name in sorted(modified):
        print(f"  {name}")


if __name__ == "__main__":
    main()
