"""Static-analysis script for K-08 ORM-vs-migration delta.

Scans:
  * backend/alembic/versions/*.py  – DDL operations declared in migrations
  * backend/domains/**/models/*.py – ORM table/column definitions

Produces:
  * delta_report.json
  * delta_table.md
"""
from __future__ import annotations

import ast
import json
import re
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# ── Paths ──────────────────────────────────────────────────────────────────
BACKEND = Path(__file__).resolve().parent.parent
VERSIONS_DIR = BACKEND / "alembic" / "versions"
DOMAINS_DIR = BACKEND / "domains"
REPORT_JSON = BACKEND / "alembic" / "k08_delta_report.json"
REPORT_MD = BACKEND / "alembic" / "k08_delta_table.md"


# ── Data model ─────────────────────────────────────────────────────────────
@dataclass
class ColumnSpec:
    name: str
    col_type: str
    nullable: bool = True
    default: Optional[str] = None
    server_default: Optional[str] = None
    is_primary_key: bool = False


@dataclass
class TableSpec:
    name: str
    schema: str
    columns: List[ColumnSpec] = field(default_factory=list)
    source: str = ""

    @property
    def fqn(self) -> str:
        return f"{self.schema}.{self.name}"


@dataclass
class DeltaRow:
    schema: str
    table: str
    column: str
    orm_present: bool
    migration_present: bool
    orm_type: str = ""
    migration_type: str = ""
    orm_nullable: Optional[bool] = None
    migration_nullable: Optional[bool] = None
    orm_default: Optional[str] = None
    migration_default: Optional[str] = None
    orm_server_default: Optional[str] = None
    migration_server_default: Optional[str] = None
    gap_kind: str = ""
    notes: str = ""


# ── ORM scanner ────────────────────────────────────────────────────────────
def scan_orm_models() -> Dict[str, TableSpec]:
    tables: Dict[str, TableSpec] = {}
    for py_file in DOMAINS_DIR.glob("*/models/*.py"):
        if py_file.name == "__init__.py":
            continue
        source = py_file.read_text(encoding="utf-8")
        try:
            tree = ast.parse(source)
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            for item in node.body:
                if not isinstance(item, ast.Assign):
                    continue
                if not any(isinstance(t, ast.Name) and t.id == "__tablename__" for t in item.targets):
                    continue
                if not isinstance(item.value, ast.Constant) or not isinstance(item.value.value, str):
                    continue
                table_name = item.value.value
                schema = "public"
                for decorator in node.decorator_list:
                    if isinstance(decorator, ast.Call) and getattr(decorator.func, 'id', None) == 'schema':
                        continue
                for subitem in node.body:
                    if isinstance(subitem, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "__table_args__" for t in subitem.targets):
                        schema = _extract_schema_from_table_args(subitem.value)
                table = TableSpec(name=table_name, schema=schema, source=str(py_file.relative_to(BACKEND)))
                tables[table.fqn] = table
                for col_node in node.body:
                    if isinstance(col_node, ast.Assign) and isinstance(col_node.targets[0], ast.Name):
                        col_name = col_node.targets[0].id
                        if col_name.startswith("_") or col_name in ("__tablename__", "__table_args__", "id"):
                            continue
                        spec = _parse_column(col_node)
                        if spec:
                            table.columns.append(spec)
                break
    return tables


def _extract_schema_from_table_args(node) -> str:
    try:
        if isinstance(node, ast.Tuple):
            for elt in node.elts:
                if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                    return elt.value
                if isinstance(elt, ast.Dict):
                    for k, v in zip(elt.keys, elt.values):
                        if isinstance(k, ast.Constant) and k.value == "schema":
                            if isinstance(v, ast.Constant) and isinstance(v.value, str):
                                return v.value
    except Exception:
        pass
    return "public"


def _parse_column(node: ast.Assign) -> Optional[ColumnSpec]:
    try:
        if not isinstance(node.value, ast.Call):
            return None
        func = node.value.func
        if isinstance(func, ast.Name) and func.id == "Column":
            pass
        elif isinstance(func, ast.Attribute) and func.attr == "Column":
            pass
        else:
            return None
    except Exception:
        return None
    col_name = node.targets[0].id if isinstance(node.targets[0], ast.Name) else None
    if not col_name:
        return None
    col_type = "unknown"
    nullable = True
    default = None
    server_default = None
    is_pk = False
    for kw in node.value.keywords:
        if kw.arg == "primary_key" and isinstance(kw.value, ast.Constant) and kw.value.value is True:
            is_pk = True
        if kw.arg == "nullable" and isinstance(kw.value, ast.Constant):
            nullable = kw.value.value
        if kw.arg == "default" and isinstance(kw.value, ast.Constant):
            default = repr(kw.value.value)
        if kw.arg == "server_default":
            if isinstance(kw.value, ast.Constant):
                server_default = repr(kw.value.value)
            elif isinstance(kw.value, ast.Call):
                func_name = ""
                if isinstance(kw.value.func, ast.Attribute):
                    func_name = kw.value.func.attr
                elif isinstance(kw.value.func, ast.Name):
                    func_name = kw.value.func.id
                if "now" in func_name.lower():
                    server_default = "func.now()"
    args = node.value.args
    if args:
        type_node = args[0]
        if isinstance(type_node, ast.Name):
            col_type = type_node.id
        elif isinstance(type_node, ast.Call):
            if isinstance(type_node.func, ast.Name):
                col_type = type_node.func.id
            elif isinstance(type_node.func, ast.Attribute):
                col_type = type_node.func.attr
            if col_type == "String" and type_node.args:
                try:
                    length = ast.literal_eval(type_node.args[0])
                    col_type = f"String({length})"
                except Exception:
                    pass
    return ColumnSpec(
        name=col_name,
        col_type=col_type,
        nullable=nullable,
        default=default,
        server_default=server_default,
        is_primary_key=is_pk,
    )


# ── Migration scanner ──────────────────────────────────────────────────────
def scan_migrations() -> Dict[str, TableSpec]:
    tables: Dict[str, TableSpec] = {}
    for py_file in sorted(VERSIONS_DIR.glob("*.py")):
        if py_file.name == "__init__.py":
            continue
        source = py_file.read_text(encoding="utf-8")
        try:
            tree = ast.parse(source)
        except SyntaxError:
            continue
        # Find upgrade() function
        upgrade_func = None
        for node in tree.body:
            if isinstance(node, ast.FunctionDef) and node.name == "upgrade":
                upgrade_func = node
                break
        if not upgrade_func:
            continue
        # Walk upgrade() looking for op.create_table / op.add_column / op.alter_column
        for stmt in ast.walk(upgrade_func):
            if not isinstance(stmt, ast.Expr):
                continue
            if not isinstance(stmt.value, ast.Call):
                continue
            func = stmt.value.func
            if not isinstance(func, ast.Attribute):
                continue
            method = func.attr
            if method == "create_table":
                tbl = _parse_create_table(stmt.value, py_file.name)
                if tbl:
                    tables[tbl.fqn] = tbl
            elif method == "add_column":
                col, schema = _parse_add_column(stmt.value)
                if col and schema:
                    fqn = f"{schema}.{_infer_table_from_add_column(stmt.value)}"
                    if fqn not in tables:
                        tables[fqn] = TableSpec(name=_infer_table_from_add_column(stmt.value), schema=schema, source=py_file.name)
                    tables[fqn].columns.append(col)
            elif method == "alter_column":
                alter = _parse_alter_column(stmt.value)
                if alter:
                    schema = alter.get("schema", "public")
                    tbl_name = alter.get("table", "")
                    fqn = f"{schema}.{tbl_name}"
                    if fqn not in tables:
                        tables[fqn] = TableSpec(name=tbl_name, schema=schema, source=py_file.name)
                    existing = {c.name: c for c in tables[fqn].columns}
                    if alter["column"] in existing:
                        c = existing[alter["column"]]
                        if alter.get("new_type"):
                            c.col_type = alter["new_type"]
                        if alter.get("nullable") is not None:
                            c.nullable = alter["nullable"]
                        if alter.get("server_default"):
                            c.server_default = alter["server_default"]
                    else:
                        tables[fqn].columns.append(ColumnSpec(
                            name=alter["column"],
                            col_type=alter.get("new_type", "unknown"),
                            nullable=alter.get("nullable", True),
                            server_default=alter.get("server_default"),
                        ))
    return tables


def _parse_create_table(call_node: ast.Call, source_file: str) -> Optional[TableSpec]:
    table_name = None
    schema = "public"
    columns: List[ColumnSpec] = []
    for kw in call_node.keywords:
        if kw.arg == "schema" and isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, str):
            schema = kw.value.value
    for arg in call_node.args:
        if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
            table_name = arg.value
            break
        if isinstance(arg, ast.Str):  # pragma: no cover - py<3.8 compat
            table_name = arg.s
            break
    if not table_name:
        return None
    for kw in call_node.keywords:
        if kw.arg != "column":
            continue
        col_nodes = kw.value.elts if isinstance(kw.value, ast.Tuple) else [kw.value]
        for col_node in col_nodes:
            spec = _parse_column_def(col_node)
            if spec:
                columns.append(spec)
    return TableSpec(name=table_name, schema=schema, columns=columns, source=source_file)


def _parse_column_def(node) -> Optional[ColumnSpec]:
    if not isinstance(node, ast.Call):
        return None
    func = node.func
    if not (isinstance(func, ast.Name) and func.id == "Column"):
        return None
    col_name = None
    for arg in node.args:
        if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
            col_name = arg.value
            break
    if not col_name:
        return None
    col_type = "unknown"
    nullable = True
    default = None
    server_default = None
    is_pk = False
    if len(node.args) > 1:
        type_node = node.args[1]
        if isinstance(type_node, ast.Name):
            col_type = type_node.id
        elif isinstance(type_node, ast.Call):
            if isinstance(type_node.func, ast.Name):
                col_type = type_node.func.id
            elif isinstance(type_node.func, ast.Attribute):
                col_type = type_node.func.attr
            if col_type == "String" and type_node.args:
                try:
                    length = ast.literal_eval(type_node.args[0])
                    col_type = f"String({length})"
                except Exception:
                    pass
    for kw in node.keywords:
        if kw.arg == "primary_key" and isinstance(kw.value, ast.Constant) and kw.value.value is True:
            is_pk = True
        if kw.arg == "nullable" and isinstance(kw.value, ast.Constant):
            nullable = kw.value.value
        if kw.arg == "default" and isinstance(kw.value, ast.Constant):
            default = repr(kw.value.value)
        if kw.arg == "server_default":
            if isinstance(kw.value, ast.Constant):
                server_default = repr(kw.value.value)
            elif isinstance(kw.value, ast.Call):
                if isinstance(kw.value.func, ast.Attribute):
                    if kw.value.func.attr == "now":
                        server_default = "func.now()"
    return ColumnSpec(
        name=col_name,
        col_type=col_type,
        nullable=nullable,
        default=default,
        server_default=server_default,
        is_primary_key=is_pk,
    )


def _parse_add_column(call_node: ast.Call) -> Tuple[Optional[ColumnSpec], Optional[str]]:
    table_name = None
    schema = "public"
    col: Optional[ColumnSpec] = None
    for kw in call_node.keywords:
        if kw.arg == "schema" and isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, str):
            schema = kw.value.value
        if kw.arg == "name" and isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, str):
            table_name = kw.value.value
    for arg in call_node.args:
        if isinstance(arg, ast.Call) and isinstance(arg.func, ast.Name) and arg.func.id == "Column":
            col = _parse_column_def(arg)
    return col, schema if table_name else None


def _infer_table_from_add_column(call_node: ast.Call) -> str:
    for kw in call_node.keywords:
        if kw.arg == "name" and isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, str):
            return kw.value.value
    return "unknown"


def _parse_alter_column(call_node: ast.Call) -> Optional[Dict]:
    result = {"column": None, "table": None, "schema": "public", "new_type": None, "nullable": None, "server_default": None}
    for kw in call_node.keywords:
        if kw.arg == "column_name" and isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, str):
            result["column"] = kw.value.value
        if kw.arg == "table_name" and isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, str):
            result["table"] = kw.value.value
        if kw.arg == "schema" and isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, str):
            result["schema"] = kw.value.value
        if kw.arg == "type_" and isinstance(kw.value, ast.Call):
            func = kw.value.func
            if isinstance(func, ast.Name):
                result["new_type"] = func.id
            elif isinstance(func, ast.Attribute):
                result["new_type"] = func.attr
            if result["new_type"] == "String" and kw.value.args:
                try:
                    length = ast.literal_eval(kw.value.args[0])
                    result["new_type"] = f"String({length})"
                except Exception:
                    pass
        if kw.arg == "nullable" and isinstance(kw.value, ast.Constant):
            result["nullable"] = kw.value.value
        if kw.arg == "server_default":
            if isinstance(kw.value, ast.Constant):
                result["server_default"] = repr(kw.value.value)
            elif isinstance(kw.value, ast.Call):
                if isinstance(kw.value.func, ast.Attribute) and kw.value.func.attr == "now":
                    result["server_default"] = "func.now()"
    if result["column"]:
        return result
    return None


# ── Delta computation ──────────────────────────────────────────────────────
def compute_delta(orm_tables: Dict[str, TableSpec], mig_tables: Dict[str, TableSpec]) -> List[DeltaRow]:
    rows: List[DeltaRow] = []
    all_fqns = set(orm_tables.keys()) | set(mig_tables.keys())

    # Heuristic: skip finance.accounts (chart of accounts) when comparing to accounts.* user tables
    # because they are different entities that happen to share a name.
    skip_mig_fqns = set()

    for fqn in sorted(all_fqns):
        if fqn in skip_mig_fqns:
            continue
        orm_tbl = orm_tables.get(fqn)
        mig_tbl = mig_tables.get(fqn)
        if not orm_tbl and mig_tbl:
            rows.append(DeltaRow(
                schema=mig_tbl.schema, table=mig_tbl.name, column="<entire table>",
                orm_present=False, migration_present=True, gap_kind="TABLE_IN_MIGRATION_ONLY",
                notes=f"Migration-only table (may be created by ORM create_all outside chain)"
            ))
            continue
        if orm_tbl and not mig_tbl:
            # Skip known ORM-only tables (created by create_all outside migration chain)
            if fqn in {
                "accounts.mfa_factors",
            }:
                continue
            rows.append(DeltaRow(
                schema=orm_tbl.schema, table=orm_tbl.name, column="<entire table>",
                orm_present=True, migration_present=False, gap_kind="TABLE_IN_ORM_ONLY",
                notes="ORM-only table (no create_table migration found)"
            ))
            continue
        if not orm_tbl or not mig_tbl:
            continue

        orm_cols = {c.name: c for c in orm_tbl.columns}
        mig_cols = {c.name: c for c in mig_tbl.columns}

        for col_name in sorted(set(orm_cols.keys()) | set(mig_cols.keys())):
            orm_col = orm_cols.get(col_name)
            mig_col = mig_cols.get(col_name)
            in_orm = col_name in orm_cols
            in_mig = col_name in mig_cols

            if in_orm and not in_mig:
                rows.append(DeltaRow(
                    schema=orm_tbl.schema, table=orm_tbl.name, column=col_name,
                    orm_present=True, migration_present=False,
                    orm_type=orm_col.col_type if orm_col else "",
                    orm_nullable=orm_col.nullable if orm_col else None,
                    orm_default=orm_col.default if orm_col else None,
                    orm_server_default=orm_col.server_default if orm_col else None,
                    gap_kind="MISSING_IN_MIGRATION",
                    notes=f"Column declared in ORM but not produced by any migration",
                ))
            elif not in_orm and in_mig:
                rows.append(DeltaRow(
                    schema=mig_tbl.schema, table=mig_tbl.name, column=col_name,
                    orm_present=False, migration_present=True,
                    migration_type=mig_col.col_type if mig_col else "",
                    migration_nullable=mig_col.nullable if mig_col else None,
                    migration_default=mig_col.default if mig_col else None,
                    migration_server_default=mig_col.server_default if mig_col else None,
                    gap_kind="MISSING_IN_ORM",
                    notes=f"Migration-only column not found in ORM",
                ))
            else:
                diffs = []
                if orm_col and mig_col:
                    if orm_col.col_type != mig_col.col_type:
                        diffs.append(f"type ORM={orm_col.col_type} vs MIG={mig_col.col_type}")
                    if orm_col.nullable != mig_col.nullable:
                        diffs.append(f"nullable ORM={orm_col.nullable} vs MIG={mig_col.nullable}")
                    if orm_col.server_default != mig_col.server_default:
                        diffs.append(f"server_default ORM={orm_col.server_default} vs MIG={mig_col.server_default}")
                if diffs:
                    rows.append(DeltaRow(
                        schema=orm_tbl.schema, table=orm_tbl.name, column=col_name,
                        orm_present=True, migration_present=True,
                        orm_type=orm_col.col_type if orm_col else "",
                        migration_type=mig_col.col_type if mig_col else "",
                        orm_nullable=orm_col.nullable if orm_col else None,
                        migration_nullable=mig_col.nullable if mig_col else None,
                        orm_server_default=orm_col.server_default if orm_col else None,
                        migration_server_default=mig_col.server_default if mig_col else None,
                        gap_kind="TYPE_OR_DEFAULT_MISMATCH",
                        notes="; ".join(diffs),
                    ))
    return rows


# ── Reports ────────────────────────────────────────────────────────────────
def write_reports(rows: List[DeltaRow]) -> None:
    REPORT_JSON.write_text(json.dumps([asdict(r) for r in rows], indent=2, default=str), encoding="utf-8")
    lines = [
        "# K-08 ORM vs Migration Delta Table",
        "",
        "| Schema | Table | Column | ORM | Migration | Gap Kind | Details |",
        "|--------|-------|--------|-----|-----------|----------|---------|",
    ]
    for r in rows:
        lines.append(
            f"| {r.schema} | {r.table} | {r.column} "
            f"| {'YES' if r.orm_present else 'NO'} "
            f"| {'YES' if r.migration_present else 'NO'} "
            f"| {r.gap_kind} "
            f"| {r.notes} |"
        )
    REPORT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {REPORT_JSON}")
    print(f"Wrote {REPORT_MD}")


def main() -> None:
    print("Scanning ORM models...")
    orm_tables = scan_orm_models()
    print(f"  Found {len(orm_tables)} ORM tables")

    print("Scanning migrations...")
    mig_tables = scan_migrations()
    print(f"  Found {len(mig_tables)} migration-tracked tables")

    print("Computing delta...")
    rows = compute_delta(orm_tables, mig_tables)
    gap_rows = [r for r in rows if r.gap_kind != ""]
    print(f"  Total delta rows: {len(rows)} (gaps: {len(gap_rows)})")

    write_reports(rows)
    for r in gap_rows:
        print(f"  GAP: {r.schema}.{r.table}.{r.column} -> {r.gap_kind}: {r.notes}")


if __name__ == "__main__":
    main()
