"""Fix single-line __table_args__ that were missed by the main script."""
from __future__ import annotations

import ast
import json
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
MODELS_DIR = BACKEND_DIR / "models"
SCHEMA_MAPPING_PATH = BACKEND_DIR / "docs" / "schema_mapping.json"


def load_schema_mapping() -> dict[str, str]:
    with SCHEMA_MAPPING_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


SCHEMA_MAPPING = load_schema_mapping()


def fix_single_line_table_args(source: str, table_name: str, schema: str) -> str:
    if schema == "public":
        return source

    pattern = re.compile(
        r'(__tablename__\s*=\s*"'
        + re.escape(table_name)
        + r'"\s*\n\s*__table_args__\s*=\s*\()(.*?)(\s*)\)(?!\s*\{)',
        re.DOTALL,
    )

    def replacer(m: re.Match, s: str = schema) -> str:
        return m.group(1) + m.group(2) + ", {\"schema\": \"" + s + "\"}" + m.group(3) + ")"

    new_source, count = pattern.subn(replacer, source)
    return new_source


import re


def process_models() -> None:
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

            updated = fix_single_line_table_args(updated, tablename, schema)

        if updated != original:
            py.write_text(updated, encoding="utf-8")
            modified_files.append(py.name)

    print(f"Modified {len(modified_files)} model files:")
    for name in sorted(modified_files):
        print(f"  {name}")


if __name__ == "__main__":
    process_models()
