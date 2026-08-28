"""Fix remaining Law 6 schema discipline violations (precise 500-char lookahead)."""
from __future__ import annotations

import re
import pathlib

BACKEND_ROOT = pathlib.Path(__file__).resolve().parent.parent
DOMAINS_DIR = BACKEND_ROOT / "domains"

def get_domain(file_path):
    """Extract domain from file path relative to domains dir."""
    try:
        parts = file_path.relative_to(DOMAINS_DIR).parts
        return parts[0] if parts else None
    except ValueError:
        return None

def fix_schema_in_file(source, domain):
    """Add schema declaration within 500 chars of __tablename__ if missing.

    Uses character-based lookahead to match the test's 500-char window.
    """
    # Find all __tablename__ positions
    result = source
    offset = 0

    for m in re.finditer(r'__tablename__\s*=\s*["\']([^"\']+)["\']', source):
        table_name = m.group(1)
        if table_name == "alembic_version":
            continue

        # Check if schema is declared within 500 chars
        window = source[m.start():m.start()+500]
        has_schema = re.search(r"""['"]schema['"]:\s*['"]""", window)

        if not has_schema:
            # Add __table_args__ right after __tablename__ line
            insert_pos = m.end()
            # Find end of line
            eol = source.find('\n', insert_pos)
            if eol == -1:
                eol = len(source)

            # Get indentation from the __tablename__ line
            line_start = source.rfind('\n', 0, m.start()) + 1
            indent = source[line_start:m.start()]
            indent = len(indent) - len(indent.lstrip())
            indent_str = ' ' * indent

            insertion = f'\n{indent_str}__table_args__ = {{"schema": "{domain}"}}'
            result = result[:eol + offset] + insertion + result[eol + offset:]
            offset += len(insertion)

    return result


def main():
    model_files = []
    for path in sorted(DOMAINS_DIR.rglob("models/*.py")):
        if path.name == "__init__.py":
            continue
        if "read_models" in str(path):
            continue
        model_files.append(path)

    fixed = 0
    for path in model_files:
        domain = get_domain(path)
        if not domain:
            continue

        source = path.read_text(encoding="utf-8")
        if "__tablename__" not in source:
            continue

        new_source = fix_schema_in_file(source, domain)

        if new_source != source:
            path.write_text(new_source, encoding="utf-8")
            fixed += 1
            print(f"  Fixed: {path.relative_to(BACKEND_ROOT)}")

    print(f"\nTotal files modified: {fixed}")


if __name__ == "__main__":
    main()
