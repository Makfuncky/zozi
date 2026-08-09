"""Generate a data dictionary for the ZOZI database (DBA24).

Introspects the configured database (via DATABASE_URL) and emits a Markdown
data dictionary describing schemas, tables, columns, types, nullability,
defaults and indexes.

Usage:
    python backend/scripts/generate_data_dictionary.py [--out docs/data_dictionary.md]
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

# Ensure backend/ is importable when run as a script.
BACKEND_ROOT = Path(__file__).resolve().parent.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from sqlalchemy import create_engine, inspect


def _db_url() -> str:
    url = os.getenv("DATABASE_URL")
    if url:
        return url
    try:
        from utils.config import settings

        return str(settings.database_url)
    except Exception:
        return f"sqlite:///{BACKEND_ROOT / 'data' / 'app.db'}"


def _mermaid_erd(engine) -> list[str]:
    """Emit a Mermaid erDiagram block covering every schema/table/FK edge (DBA37)."""
    insp = inspect(engine)
    lines = ["## Entity-Relationship Diagram", "", "```mermaid", "erDiagram"]
    for schema in insp.get_schema_names():
        if schema in ("information_schema", "pg_catalog"):
            continue
        for table in sorted(insp.get_table_names(schema=schema)):
            safe = f"{schema}_{table}".replace("-", "_").replace(".", "_")
            pk = ""
            for col in insp.get_pk_constraint(table, schema=schema).get("constrained_columns", []) or []:
                pk = col
                break
            lines.append(f'    {safe} {{')
            lines.append(f'        {"int" if pk else "type"} {pk or "id"} PK')
            lines.append("    }")
    for schema in insp.get_schema_names():
        if schema in ("information_schema", "pg_catalog"):
            continue
        for table in sorted(insp.get_table_names(schema=schema)):
            left = f"{schema}_{table}".replace("-", "_").replace(".", "_")
            for fk in insp.get_foreign_keys(table, schema=schema):
                if not fk.get("referred_schema"):
                    continue
                right = (
                    f"{fk['referred_schema']}_{fk['referred_table']}"
                    .replace("-", "_").replace(".", "_")
                )
                cols = fk.get("constrained_columns") or []
                refs = fk.get("referred_columns") or []
                if not cols or not refs:
                    continue
                for c, r in zip(cols, refs):
                    lines.append(f'    {left} ||--o{{ {right} : "{c} -> {r}"')
    lines.append("```")
    return lines


def generate(out_path: Path) -> None:
    url = _db_url()
    engine = create_engine(url)
    insp = inspect(engine)

    lines = ["# ZOZI Data Dictionary", "", f"> Generated from `{url}`", ""]
    lines.extend(_mermaid_erd(engine))
    lines.append("")
    for schema in insp.get_schema_names():
        if schema in ("information_schema", "pg_catalog"):
            continue
        table_names = insp.get_table_names(schema=schema)
        if not table_names:
            continue
        lines.append(f"## Schema: `{schema}`")
        lines.append("")
        for table in sorted(table_names):
            lines.append(f"### `{table}`")
            lines.append("")
            lines.append("| Column | Type | Nullable | Default |")
            lines.append("|---|---|---|---|")
            for col in insp.get_columns(table, schema=schema):
                default = col.get("default")
                default = "" if default is None else str(default)
                lines.append(
                    f"| {col['name']} | {col['type']} | {col['nullable']} | {default} |"
                )
            indexes = insp.get_indexes(table, schema=schema)
            if indexes:
                lines.append("")
                lines.append(
                    "Indexes: "
                    + ", ".join(
                        f"`{ix['name']}`({','.join(ix['column_names'])})" for ix in indexes
                    )
                )
            lines.append("")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Data dictionary written to {out_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate ZOZI data dictionary")
    parser.add_argument(
        "--out",
        default=str(BACKEND_ROOT / "docs" / "data_dictionary.md"),
        help="Output markdown path",
    )
    args = parser.parse_args()
    generate(Path(args.out))


if __name__ == "__main__":
    main()
