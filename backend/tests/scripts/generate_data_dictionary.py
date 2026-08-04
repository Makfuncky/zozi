"""Generate database data dictionary from ORM models.

DB24 requirement: Machine-generated data dictionary for database documentation.
Outputs schema.json with table/column metadata for all ORM models.
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

_BACKEND_ROOT = Path(__file__).resolve().parent.parent
if str(_BACKEND_ROOT) not in os.sys.path:
    os.sys.path.insert(0, str(_BACKEND_ROOT))

os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("SECRET_KEY", "ci-non-production-key-for-data-dict")


def _get_column_type_info(column) -> dict[str, Any]:
    """Extract column type information."""
    info = {
        "type": str(column.type),
        "nullable": column.nullable,
        "primary_key": column.primary_key,
        "foreign_key": None,
        "unique": column.unique,
        "index": False,
        "default": None,
    }

    if column.foreign_keys:
        fk = list(column.foreign_keys)[0]
        try:
            info["foreign_key"] = f"{column.table.name}.{column.name} -> {fk.column.table.name}.{fk.column.name}"
        except Exception:
            info["foreign_key"] = str(fk)

    if column.default is not None:
        info["default"] = str(column.default)

    return info


def generate_data_dictionary() -> dict[str, Any]:
    """Generate a data dictionary from ORM metadata."""
    from data.base import Base
    import data.models  # noqa: F401

    result: dict[str, Any] = {
        "generated_at": datetime.utcnow().isoformat(),
        "total_tables": 0,
        "schemas": {},
    }

    for key, table in Base.metadata.tables.items():
        if "." in key:
            schema, table_name = key.split(".", 1)
        else:
            schema = "public"
            table_name = key

        if schema not in result["schemas"]:
            result["schemas"][schema] = {
                "tables": {},
                "table_count": 0,
            }

        columns = []
        for col in table.columns:
            col_info = _get_column_type_info(col)
            col_info["name"] = col.name
            col_info["comment"] = col.comment or ""
            columns.append(col_info)

        result["schemas"][schema]["tables"][table_name] = {
            "columns": columns,
            "primary_key": [c.name for c in table.primary_key.columns],
            "foreign_keys": [
                {
                    "column": fk.parent.name,
                    "target": fk.target_fullname,
                    "ondelete": fk.ondelete,
                }
                for fk in table.foreign_keys
            ],
            "indexes": [],
        }

        result["schemas"][schema]["table_count"] += 1
        result["total_tables"] += 1

    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Generate database data dictionary from ORM models"
    )
    parser.add_argument(
        "-o", "--output",
        default=None,
        help="Output file path (default: stdout)",
    )
    parser.add_argument(
        "--format",
        choices=["json", "markdown", "mermaid"],
        default="json",
        help="Output format (default: json)",
    )
    args = parser.parse_args(argv)

    result = generate_data_dictionary()

    if args.format == "markdown":
        output = _format_markdown(result)
    elif args.format == "mermaid":
        output = _generate_mermaid_erd(result)
    else:
        output = json.dumps(result, indent=2)

    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")
        print(f"Data dictionary written to {args.output}", file=sys.stderr)
    else:
        print(output)

    return 0


def _format_markdown(data: dict[str, Any]) -> str:
    """Format data dictionary as Markdown."""
    lines = [
        "# ZOZI Database Data Dictionary",
        "",
        f"**Generated:** {data['generated_at']}",
        f"**Total Tables:** {data['total_tables']}",
        "",
    ]

    for schema, schema_data in data["schemas"].items():
        lines.append(f"## Schema: {schema}")
        lines.append("")
        lines.append(f"Tables: {schema_data['table_count']}")
        lines.append("")

        for table_name, table_data in schema_data["tables"].items():
            lines.append(f"### {table_name}")
            lines.append("")

            if table_data["primary_key"]:
                lines.append(f"**Primary Key:** {', '.join(table_data['primary_key'])}")
                lines.append("")

            if table_data["foreign_keys"]:
                lines.append("**Foreign Keys:**")
                for fk in table_data["foreign_keys"]:
                    lines.append(f"- `{fk['column']}` → `{fk['target']}`")
                lines.append("")

            lines.append("| Column | Type | Nullable | PK | FK | Unique |")
            lines.append("|--------|------|----------|-----|-----|--------|")

            for col in table_data["columns"]:
                lines.append(
                    f"| `{col['name']}` | `{col['type']}` | "
                    f"{'Yes' if col['nullable'] else 'No'} | "
                    f"{'Yes' if col['primary_key'] else 'No'} | "
                    f"{'Yes' if col['foreign_key'] else 'No'} | "
                    f"{'Yes' if col['unique'] else 'No'} |"
                )

            lines.append("")

    return "\n".join(lines)


def _generate_mermaid_erd(data: dict[str, Any]) -> str:
    """Generate Mermaid ERD output for DB37 compliance."""
    lines = [
        "```mermaid",
        "erDiagram",
        "",
    ]

    for schema, schema_data in data["schemas"].items():
        for table_name, table_data in schema_data["tables"].items():
            lines.append(f"    {table_name} {{")
            pk_cols = table_data.get("primary_key", [])
            for col in table_data["columns"]:
                col_name = col["name"]
                is_pk = col_name in pk_cols
                col_type = col["type"].split("(")[0]
                if is_pk:
                    lines.append(f"        {col_name} {col_type} PK")
                elif col["primary_key"]:
                    lines.append(f"        {col_name} {col_type}")
            lines.append("    }")
            lines.append("")

            for fk in table_data.get("foreign_keys", []):
                target = str(fk["target"]).split(".")[-1]
                lines.append(f"    {table_name} }}--|--{{ {target} : {fk['column']}")

    lines.append("```")
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())