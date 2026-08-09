"""Add schema dict to models lacking __table_args__ entirely."""
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


def add_schema_to_class(content: str) -> str:
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
    new_content, changes = add_schema_to_class(content)
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
