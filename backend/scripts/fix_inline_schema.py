"""Fix __table_args__ by moving inline schema dicts to end of tuple."""
from __future__ import annotations

import ast
import re
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
MODELS_DIR = BACKEND_DIR / "models"
SCHEMA_MAPPING_PATH = BACKEND_DIR / "docs" / "schema_mapping.json"


def load_schema_mapping() -> dict[str, str]:
    with SCHEMA_MAPPING_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


import json


SCHEMA_MAPPING = load_schema_mapping()


def fix_inline_schema_in_table_args(source: str, table_name: str, schema: str) -> str:
    if schema == "public":
        return source

    pattern = re.compile(
        r'(__tablename__\s*=\s*"'
        + re.escape(table_name)
        + r'"\s*\n\s*__table_args__\s*=\s*\()(.*?)(\s*)\)(?!\s*\{)',
        re.DOTALL,
    )

    def replacer(m: re.Match) -> str:
        block = m.group(2)
        # Remove inline {"schema": "..."} from inside Index/UniqueConstraint calls
        block = re.sub(r',\s*\{\s*"schema"\s*:\s*"' + re.escape(schema) + r'"\s*\}', '', block)
        # Add schema dict at end if not already present as separate dict
        if not re.search(r'\{\s*"schema"\s*:\s*"' + re.escape(schema) + r'"\s*\}', block):
            block = block.rstrip()
            if block and not block.endswith(','):
                block += ','
            block += ' {"schema": "' + schema + '"}'
        return m.group(1) + block + m.group(3) + ')'

    new_source, count = pattern.subn(replacer, source)
    return new_source


def fix_missing_schema_in_table_args(source: str, table_name: str, schema: str) -> str:
    if schema == "public":
        return source

    pattern = re.compile(
        r'(__tablename__\s*=\s*"'
        + re.escape(table_name)
        + r'"\s*\n\s*__table_args__\s*=\s*\()(.*?)(\s*)\)(?!\s*\{)',
        re.DOTALL,
    )

    def replacer(m: re.Match) -> str:
        block = m.group(2)
        # Add schema dict at end if not already present
        if 'schema' not in block.lower():
            block = block.rstrip()
            if block and not block.endswith(','):
                block += ','
            block += ' {"schema": "' + schema + '"}'
        return m.group(1) + block + m.group(3) + ')'

    new_source, count = pattern.subn(replacer, source)
    return new_source


def process_models():
    modified_files = []

    for py in sorted(MODELS_DIR.glob("*.py")):
        if py.name.startswith("_"):
            continue

        original = py.read_text(encoding="utf-8")

        try:
            tree = ast.parse(original)
        except SyntaxError as exc:
            print(f"[SKIP] {py.name}: {exc}")
            continue

        classes = [
            node for node in tree.body if isinstance(node, ast.ClassDef)
        ]

        updated = original
        for cls in classes:
            tablename = None
            for item in cls.body:
                if isinstance(item, ast.Assign):
                    for target in item.targets:
                        if isinstance(target, ast.Name) and target.id == "__tablename__":
                            if isinstance(item.value, ast.Constant) and isinstance(item.value.value, str):
                                tablename = item.value.value

            if not tablename:
                continue

            schema = SCHEMA_MAPPING.get(tablename)
            if not schema or schema == "public":
                continue

            updated = fix_inline_schema_in_table_args(updated, tablename, schema)

        if updated != original:
            py.write_text(updated, encoding="utf-8")
            modified_files.append(py.name)

    print(f"Modified {len(modified_files)} model files:")
    for name in sorted(modified_files):
        print(f"  {name}")


if __name__ == "__main__":
    process_models()
