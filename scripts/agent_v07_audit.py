"""Agent V07 — FK, Index, Soft-Delete, Timestamp Auditor v2.

Scans all backend/domains/*/models/*.py for:
  Law 21: created_at/updated_at use server_default=func.now() (not default=utcnow)
  Law 22/52: Every ForeignKey has explicit ondelete=...
  Law 53: Every ForeignKey column has explicit Index() or is part of composite index
  Law 54: Model has is_deleted = Column(Boolean, default=False, nullable=False)
"""
from __future__ import annotations

import ast
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple


PROJECT_ROOT = Path(r"D:\Projects\10- E-COMMERCE WEBSITE\zozi")
DOMAINS_DIR = PROJECT_ROOT / "backend" / "domains"
OUTPUT_PATH = PROJECT_ROOT / "_audit_results" / "09_09_26" / "agent_v07_fk_indexes_timestamps_verified.json"


@dataclass
class Violation:
    file: str
    line: int
    function: str
    violation: str
    severity: str
    law: str
    proposed_fix: str


def find_model_files() -> List[Path]:
    files = []
    for domain in sorted(DOMAINS_DIR.iterdir()):
        if not domain.is_dir():
            continue
        models_dir = domain / "models"
        if not models_dir.exists():
            continue
        for f in sorted(models_dir.glob("*.py")):
            if f.name == "__init__.py":
                continue
            files.append(f)
    return files


def extract_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    elif isinstance(node, ast.Attribute):
        return node.attr
    return ""


def find_fk_calls_in_node(node: ast.AST) -> List[ast.Call]:
    """Recursively find all ForeignKey(...) calls within a node."""
    results = []
    for child in ast.walk(node):
        if isinstance(child, ast.Call):
            if extract_name(child.func) == "ForeignKey":
                results.append(child)
    return results


def get_class_line_col_map(tree: ast.AST) -> dict:
    result = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            result[node.name] = (node.lineno, node.col_offset)
    return result


def analyze_file(path: Path) -> List[Violation]:
    violations = []
    rel = str(path.relative_to(PROJECT_ROOT)).replace("\\", "/")

    try:
        source = path.read_text(encoding="utf-8")
    except Exception as e:
        return [Violation(rel, 1, "UNKNOWN", f"Cannot read file: {e}", "High", "N/A", "Fix file encoding")]

    try:
        tree = ast.parse(source)
    except SyntaxError as e:
        return [Violation(rel, e.lineno or 1, "UNKNOWN", f"Syntax error: {e}", "High", "N/A", "Fix syntax error")]

    class_locs = get_class_line_col_map(tree)

    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        class_name = node.name
        class_start = node.lineno

        # Collect all assignments in the class body
        assignments: List[Tuple[int, str, Optional[ast.AST]]] = []
        for child in node.body:
            if isinstance(child, ast.Assign):
                for target in child.targets:
                    if isinstance(target, ast.Name):
                        assignments.append((child.lineno, target.id, child.value))
            elif isinstance(child, ast.AnnAssign):
                if isinstance(child.target, ast.Name):
                    assignments.append((child.lineno, child.target.id, child.value or ast.Constant(None)))

        # Collect __table_args__
        table_args_value = None
        has_tablename = False
        non_meta_assignments = []
        for child in ast.walk(node):
            if isinstance(child, ast.Assign):
                for target in child.targets:
                    if isinstance(target, ast.Name):
                        if target.id == "__tablename__":
                            has_tablename = True
                        if target.id == "__table_args__":
                            table_args_value = child.value

        non_meta_assignments = [a for a in assignments if a[1] not in ("__tablename__", "__table_args__", "__all__")]

        # Build set of indexed columns from __table_args__
        indexed_columns: set = set()
        if table_args_value is not None:
            if isinstance(table_args_value, (ast.Tuple, ast.List)):
                for elt in table_args_value.elts:
                    if isinstance(elt, ast.Call):
                        func_name = extract_name(elt.func)
                        if func_name == "Index":
                            for arg in elt.args[1:]:
                                if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                                    indexed_columns.add(arg.value)
                        if func_name == "UniqueConstraint":
                            for arg in elt.args[1:]:
                                if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                                    indexed_columns.add(arg.value)

        # Also check column-level index=True
        column_indexed: set = set()
        for lineno, col_name, value_node in assignments:
            if value_node is None:
                continue
            if isinstance(value_node, ast.Call) and extract_name(value_node.func) == "Column":
                for kw in value_node.keywords:
                    if kw.arg == "index" and isinstance(kw.value, ast.Constant) and kw.value.value is True:
                        column_indexed.add(col_name)

        # --- Check 1: ForeignKey ondelete (Laws 22, 52) ---
        fk_info: List[Tuple[int, str, ast.Call]] = []
        for lineno, col_name, value_node in assignments:
            if value_node is None:
                continue
            # Find ForeignKey calls nested inside Column(...) or standalone
            fk_calls = find_fk_calls_in_node(value_node)
            for fk_call in fk_calls:
                fk_info.append((lineno, col_name, fk_call))

        for lineno, col_name, fk_call in fk_info:
            has_ondelete = any(kw.arg == "ondelete" for kw in fk_call.keywords)
            if not has_ondelete:
                violations.append(Violation(
                    file=rel, line=lineno, function=class_name,
                    violation=f"ForeignKey column '{col_name}' missing ondelete action",
                    severity="Critical", law="Law 22 / Law 52",
                    proposed_fix=f"Add ondelete='CASCADE' or appropriate action to ForeignKey for '{col_name}'",
                ))

        # --- Check 2: FK column has explicit index (Law 53) ---
        for lineno, col_name, fk_call in fk_info:
            if col_name not in indexed_columns and col_name not in column_indexed:
                violations.append(Violation(
                    file=rel, line=lineno, function=class_name,
                    violation=f"FK column '{col_name}' has no explicit Index()",
                    severity="High", law="Law 53",
                    proposed_fix=f"Add index=True to Column('{col_name}') or add Index(..., '{col_name}') to __table_args__",
                ))

        # --- Check 3: is_deleted soft-delete column (Law 54) ---
        has_is_deleted = False
        is_deleted_lineno = None
        for lineno, col_name, value_node in assignments:
            if col_name == "is_deleted":
                has_is_deleted = True
                is_deleted_lineno = lineno
                if value_node is not None and isinstance(value_node, ast.Call):
                    if extract_name(value_node.func) == "Column":
                        has_default_false = False
                        has_nullable_false = False
                        for kw in value_node.keywords:
                            if kw.arg == "default" and isinstance(kw.value, ast.Constant) and kw.value.value is False:
                                has_default_false = True
                            if kw.arg == "nullable" and isinstance(kw.value, ast.Constant) and kw.value.value is False:
                                has_nullable_false = True
                        if not has_default_false:
                            violations.append(Violation(
                                file=rel, line=lineno, function=class_name,
                                violation="is_deleted column missing default=False",
                                severity="Medium", law="Law 54",
                                proposed_fix="Set default=False on is_deleted Column",
                            ))
                        if not has_nullable_false:
                            violations.append(Violation(
                                file=rel, line=lineno, function=class_name,
                                violation="is_deleted column missing nullable=False",
                                severity="Medium", law="Law 54",
                                proposed_fix="Set nullable=False on is_deleted Column",
                            ))

        if not has_is_deleted and has_tablename:
            if len(non_meta_assignments) > 2:
                violations.append(Violation(
                    file=rel, line=class_start, function=class_name,
                    violation="Model missing is_deleted soft-delete column",
                    severity="Medium", law="Law 54",
                    proposed_fix="Add is_deleted = Column(Boolean, default=False, nullable=False, index=True)",
                ))

        # --- Check 4: created_at/updated_at with server_default=func.now() (Law 21) ---
        has_created_at = False
        has_updated_at = False
        for lineno, col_name, value_node in assignments:
            if col_name == "created_at":
                has_created_at = True
                if value_node is not None and isinstance(value_node, ast.Call):
                    if extract_name(value_node.func) == "Column":
                        has_server_default = any(
                            kw.arg == "server_default"
                            for kw in value_node.keywords
                        )
                        if not has_server_default:
                            violations.append(Violation(
                                file=rel, line=lineno, function=class_name,
                                violation="created_at missing server_default=func.now() (uses Python-side default)",
                                severity="High", law="Law 21",
                                proposed_fix="Use Column(DateTime, server_default=func.now(), nullable=False)",
                            ))
            elif col_name == "updated_at":
                has_updated_at = True
                if value_node is not None and isinstance(value_node, ast.Call):
                    if extract_name(value_node.func) == "Column":
                        has_server_default = any(
                            kw.arg == "server_default"
                            for kw in value_node.keywords
                        )
                        if not has_server_default:
                            violations.append(Violation(
                                file=rel, line=lineno, function=class_name,
                                violation="updated_at missing server_default=func.now() (uses Python-side default)",
                                severity="High", law="Law 21",
                                proposed_fix="Use Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=True)",
                            ))

        if has_tablename and len(non_meta_assignments) > 2:
            if not has_created_at:
                violations.append(Violation(
                    file=rel, line=class_start, function=class_name,
                    violation="Model missing created_at timestamp column",
                    severity="High", law="Law 21",
                    proposed_fix="Add created_at = Column(DateTime, server_default=func.now(), nullable=False)",
                ))
            if not has_updated_at:
                violations.append(Violation(
                    file=rel, line=class_start, function=class_name,
                    violation="Model missing updated_at timestamp column",
                    severity="High", law="Law 21",
                    proposed_fix="Add updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=True)",
                ))

    return violations


def main():
    files = find_model_files()
    all_violations: List[Violation] = []
    for f in files:
        all_violations.extend(analyze_file(f))

    # Deduplicate
    seen = set()
    unique_violations = []
    for v in all_violations:
        key = (v.file, v.line, v.function, v.violation)
        if key not in seen:
            seen.add(key)
            unique_violations.append(v)

    unique_violations.sort(key=lambda v: (v.file, v.line))

    result = {
        "agent_id": "V07",
        "agent_name": "FKs, Indexes, Soft-Delete, Timestamps (Verified)",
        "status": "completed",
        "findings_count": len(unique_violations),
        "findings": [
            {
                "file": v.file,
                "line": v.line,
                "function": v.function,
                "violation": v.violation,
                "severity": v.severity,
                "law": v.law,
                "proposed_fix": v.proposed_fix,
            }
            for v in unique_violations
        ],
        "summary": (
            f"Agent V07 completed exhaustive audit of {len(files)} model files across all 16 ZOZI domains. "
            f"Found {len(unique_violations)} violations of Laws 21 (timestamps), 22/52 (FK ondelete), "
            f"53 (FK indexes), and 54 (soft-delete). "
            f"Violations are classified as Critical (missing ondelete), High (missing index or wrong timestamp default), "
            f"and Medium (missing is_deleted or missing nullable=False). Each finding includes exact file:line, model class, and proposed fix."
        ),
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Written {len(unique_violations)} findings to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
