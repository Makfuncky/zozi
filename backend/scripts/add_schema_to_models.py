"""Add schema declarations to all model files based on schema_mapping.json.

This is the *canonical* schema normalizer. It is intentionally idempotent:
every pass strips any existing ``{"schema": ...}`` dicts from a class's
``__table_args__`` and then writes exactly one correct schema dict, so running
it repeatedly (e.g. from a harness) never produces duplicate or misplaced
schema entries -- which previously raised
``'dict' object has no attribute '_set_parent_with_dispatch'`` in SQLAlchemy.
"""
import json
import re
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent
models_dir = backend_dir / "models"
docs_dir = backend_dir / "var" / "artifacts"

with open(docs_dir / "schema_mapping.json") as f:
    table_to_schema = json.load(f)

DEFAULT_SCHEMA = "public"


def get_schema_for_table(table_name: str) -> str:
    return table_to_schema.get(table_name, DEFAULT_SCHEMA)


def _strip_schema_dicts(inner: str) -> str:
    """Remove every {"schema": ...} dict (and an adjacent comma) and tidy."""
    # Consume a schema dict plus an optional following comma.
    inner = re.sub(
        r'\{\s*["\']schema["\']\s*:\s*["\'][^"\']*["\']\s*\}\s*,?', "", inner
    )
    # Also catch a schema dict that was preceded by a comma (e.g. "(, {...}").
    inner = re.sub(
        r',\s*\{\s*["\']schema["\']\s*:\s*["\'][^"\']*["\']\s*\}', "", inner
    )
    inner = re.sub(r"\(\s*,", "(", inner)
    inner = re.sub(r",\s*\)", ")", inner)
    inner = re.sub(r"\[\s*,", "[", inner)
    inner = re.sub(r",\s*\]", "]", inner)
    inner = re.sub(r",\s*,", ",", inner)
    inner = inner.strip()
    inner = re.sub(r"^,", "", inner)
    inner = re.sub(r",$", "", inner)
    return inner.strip()


def _balanced_span(text: str, open_ch: str, close_ch: str, start: int) -> tuple[int, int]:
    """Return (content_start, content_end) of the balanced group at `start`."""
    assert text[start] == open_ch
    depth = 0
    i = start
    n = len(text)
    while i < n:
        ch = text[i]
        if ch == open_ch:
            depth += 1
        elif ch == close_ch:
            depth -= 1
            if depth == 0:
                return start + 1, i
        i += 1
    raise ValueError("unbalanced group")


def _normalize_class(part: str) -> str:
    tm = re.search(r'__tablename__\s*=\s*["\']([^"\']+)["\']', part)
    if not tm:
        return part
    table_name = tm.group(1)
    schema = get_schema_for_table(table_name)

    tam = re.search(r"__table_args__\s*=\s*", part)
    if not tam:
        # No __table_args__ yet: insert one right after the __tablename__ line.
        tn_end = tm.end()
        insert_at = part.find("\n", tn_end) + 1
        new_line = f'    __table_args__ = {{"schema": "{schema}"}}\n'
        return part[:insert_at] + new_line + part[insert_at:]

    after = tam.end()
    first = part[after]
    if first == "{":
        # Dict form: replace entirely with a single schema dict.
        c_start, c_end = _balanced_span(part, "{", "}", after)
        new_value = f'{{"schema": "{schema}"}}'
        return part[:c_start - 1] + new_value + part[c_end + 1:]
    if first in "([":
        close_ch = ")" if first == "(" else "]"
        c_start, c_end = _balanced_span(part, first, close_ch, after)
        inner = part[c_start:c_end]
        inner = _strip_schema_dicts(inner)
        if inner == "":
            new_inner = f'{{"schema": "{schema}"}}'
        else:
            # SQLAlchemy 2.x requires the schema dict to be the LAST element
            # of a tuple/list __table_args__.
            new_inner = f"{inner}, {{'schema': '{schema}'}}"
        return part[:c_start] + new_inner + part[c_end:]
    # Unknown shape: leave untouched.
    return part


def update_model_file(file_path: Path) -> int:
    content = file_path.read_text()
    original = content

    parts = re.split(r"(?m)^(?=class\s)", content)
    new_parts = []
    for part in parts:
        if part.lstrip().startswith("class "):
            new_parts.append(_normalize_class(part))
        else:
            new_parts.append(part)
    content = "".join(new_parts)

    if content != original:
        file_path.write_text(content)
        return 1
    return 0


if __name__ == "__main__":
    changed = 0
    for model_file in sorted(models_dir.glob("*.py")):
        if model_file.name in ("__init__.py", "mixins.py"):
            continue
        changed += update_model_file(model_file)
    print(f"Normalized schema across model files (changed={changed}).")
