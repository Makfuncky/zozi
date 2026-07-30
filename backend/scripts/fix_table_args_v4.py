"""Add schema dict to __table_args__ tuples using parenthesis counting."""
import json
import re
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
MODELS_DIR = BACKEND_DIR / "models"
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


def fix_file(path: Path) -> bool:
    content = path.read_text(encoding="utf-8")
    new_content, changes = add_schema_to_table_args(content)
    if changes:
        path.write_text(new_content, encoding="utf-8")
    return changes > 0


def main():
    modified = []
    for py in sorted(MODELS_DIR.glob("*.py")):
        if py.name.startswith("_"):
            continue
        if fix_file(py):
            modified.append(py.name)

    print(f"Modified {len(modified)} files:")
    for name in sorted(modified):
        print(f"  {name}")


if __name__ == "__main__":
    main()
