"""Fix __table_args__ by adding schema dict at end of tuple."""
from __future__ import annotations

import ast
import re
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
MODELS_DIR = BACKEND_DIR / "models"
SCHEMA_MAPPING_PATH = BACKEND_DIR / "docs" / "schema_mapping.json"


def load_schema_mapping() -> dict[str, str]:
    import json
    with SCHEMA_MAPPING_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


SCHEMA_MAPPING = load_schema_mapping()


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

            # Find __table_args__ assignment in this class
            for item in cls.body:
                if isinstance(item, ast.Assign):
                    for target in item.targets:
                        if isinstance(target, ast.Name) and target.id == "__table_args__":
                            # Check if it already has schema
                            if isinstance(item.value, ast.Dict):
                                # __table_args__ = {"schema": "X"}
                                # Check if there are other table args in the class
                                # If there are Index/UniqueConstraint calls, we need to convert to tuple
                                # For now, just check if schema is already set
                                if any(
                                    isinstance(i, (ast.Call, ast.Tuple))
                                    for i in cls.body
                                    if isinstance(i, ast.Assign) and any(
                                        isinstance(t, ast.Name) and t.id == "__table_args__"
                                        for t in i.targets
                                    )
                                ):
                                    pass  # Already handled
                                continue
                            
                            if isinstance(item.value, ast.Tuple):
                                # __table_args__ = (Index(...),)
                                # Check if schema dict is already at the end
                                if item.value.elts and isinstance(item.value.elts[-1], ast.Dict):
                                    # Already has schema
                                    continue
                                
                                # Add schema dict at the end
                                # We need to modify the source text
                                # Find the __table_args__ = (...) line(s)
                                pattern = re.compile(
                                    r'(__tablename__\s*=\s*"' + re.escape(tablename) + r'"\s*\n\s*__table_args__\s*=\s*\()(.*?)(\s*)\)(?!\s*\{)',
                                    re.DOTALL,
                                )
                                
                                def replacer(m):
                                    block = m.group(2)
                                    # Add schema dict at end
                                    block = block.rstrip().rstrip(',')
                                    if not block.endswith('('):
                                        block += ','
                                    block += ' {"schema": "' + schema + '"}'
                                    return m.group(1) + block + m.group(3) + ')'
                                
                                updated = pattern.subn(replacer, updated)[0]

        if updated != original:
            py.write_text(updated, encoding="utf-8")
            modified_files.append(py.name)

    print(f"Modified {len(modified_files)} model files:")
    for name in sorted(modified_files):
        print(f"  {name}")


if __name__ == "__main__":
    process_models()
