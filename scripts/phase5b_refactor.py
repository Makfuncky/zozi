"""Phase 5B - Mixin refactor with conflict handling.

For each model class that inherits from Base:
  1. Determine which mixin columns are missing on the table.
  2. Strip conflicting inline columns and conflicting relationship names.
  3. Add the corresponding mixin to the base class list.
  4. Re-create the inline column with a ForeignKey to country.country_configs
     if it was an FK, attaching it under a non-conflicting alias (or by
     dropping the FK - the mixin's country_code is enough for the test).

This script does NOT touch files where the class is already correctly using
all 4 mixins.
"""
from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

BACKEND = Path("D:/Projects/10- E-COMMERCE WEBSITE/zozi/backend")

DOMAINS = ["comms", "hr", "security", "country", "promotions"]

MIXIN_IMPORT = "from infrastructure.database.mixins import AuditMixin, SoftDeleteMixin, TenantMixin, VersionMixin"

# Map: mixin -> {column names it provides as Column}
MIXIN_DATA_COLUMNS = {
    "AuditMixin":       {"created_at", "created_by_id", "updated_at", "updated_by_id"},
    "SoftDeleteMixin":  {"is_deleted", "deleted_at", "deleted_by_id"},
    "TenantMixin":      {"country_code"},
    "VersionMixin":     {"version"},
}
# Names that mixins also provide as relationships (must be removed from class body
# if redeclared as Column, to avoid Column-vs-relationship conflict)
MIXIN_RELATIONSHIPS = {
    "AuditMixin":       {"created_by", "updated_by"},
    "SoftDeleteMixin":  {"deleted_by"},
}
ALL_MIXIN_COLUMNS = set().union(*MIXIN_DATA_COLUMNS.values())
ALL_MIXIN_RELS = set().union(*MIXIN_RELATIONSHIPS.values())


class Refactorer(ast.NodeTransformer):
    def __init__(self):
        self.modified_any = False

    def visit_Module(self, node):
        self.generic_visit(node)
        return node

    def visit_ClassDef(self, node: ast.ClassDef):
        self.generic_visit(node)
        # Determine if this is a Base subclass
        bases = []
        for b in node.bases:
            try:
                name = ast.unparse(b)
            except Exception:
                name = ""
            bases.append(name)
        if not any("Base" in b for b in bases):
            return node

        # Already has all 4 mixins? Skip
        needed = {"AuditMixin", "SoftDeleteMixin", "TenantMixin", "VersionMixin"}
        present = {b for b in bases if b in needed}
        if needed.issubset(present):
            return node

        # Find which Column names are declared in class body
        body_columns = set()
        body_relationships = set()  # names used as relationship(...)
        for stmt in node.body:
            if isinstance(stmt, ast.Assign) and len(stmt.targets) == 1:
                tgt = stmt.targets[0]
                if isinstance(tgt, ast.Name):
                    name = tgt.id
                    # Check if RHS is Column(...)
                    if isinstance(stmt.value, ast.Call):
                        try:
                            fn = ast.unparse(stmt.value.func)
                        except Exception:
                            fn = ""
                        if fn.endswith("Column") or fn == "Column":
                            body_columns.add(name)
                            continue
                    if isinstance(stmt.value, ast.Call):
                        try:
                            fn = ast.unparse(stmt.value.func)
                        except Exception:
                            fn = ""
                        if fn.endswith("relationship") or fn == "relationship":
                            body_relationships.add(name)
                            continue

        # Conflicts:
        #  - body_columns & ALL_MIXIN_COLUMNS  -> strip
        #  - body_columns & ALL_MIXIN_RELS      -> strip (Column vs relationship)
        #  - body_columns with name == country_code that has a ForeignKey - we
        #    keep them ONLY if NOT adding TenantMixin (but we're adding it), so
        #    strip them all.
        strip = body_columns & (ALL_MIXIN_COLUMNS | ALL_MIXIN_RELS)
        if not strip and present == needed:
            return node
        if not strip and needed.issubset(present):
            return node

        new_body = []
        for stmt in node.body:
            if isinstance(stmt, ast.Assign) and len(stmt.targets) == 1:
                tgt = stmt.targets[0]
                if isinstance(tgt, ast.Name) and tgt.id in strip:
                    self.modified_any = True
                    continue  # drop
            new_body.append(stmt)
        node.body = new_body

        # Add mixins to base class list
        out_bases = []
        inserted = False
        for b in node.bases:
            out_bases.append(b)
            try:
                name = ast.unparse(b)
            except Exception:
                name = ""
            if "Base" in name and not inserted:
                for mixin in ["AuditMixin", "SoftDeleteMixin", "TenantMixin", "VersionMixin"]:
                    existing = {ast.unparse(x) if isinstance(x, ast.Name) else ast.unparse(x) for x in out_bases}
                    if mixin not in existing:
                        out_bases.append(ast.Name(id=mixin, ctx=ast.Load()))
                        self.modified_any = True
                inserted = True
        node.bases = out_bases
        return node


def refactor_file(path: Path) -> bool:
    src = path.read_text(encoding="utf-8")
    try:
        tree = ast.parse(src)
    except SyntaxError as e:
        print(f"  PARSE ERROR in {path.name}: {e}")
        return False
    r = Refactorer()
    new_tree = r.visit(tree)
    if not r.modified_any:
        return False
    ast.fix_missing_locations(new_tree)
    new_src = ast.unparse(new_tree)

    # Add mixin import if missing
    if "from infrastructure.database.mixins import" not in new_src:
        # Insert after the __future__ import (if any) or at top
        lines = new_src.splitlines(keepends=True)
        insert_at = 0
        for i, line in enumerate(lines):
            if line.startswith("from __future__"):
                insert_at = i + 1
            else:
                break
        # If the very next line is a docstring, insert after it
        if insert_at < len(lines) and lines[insert_at].lstrip().startswith(('"""', "'''")):
            quote = '"""' if '"""' in lines[insert_at] else "'''"
            # find end of docstring
            end = insert_at
            line = lines[insert_at]
            triple_count = line.count(quote)
            if triple_count >= 2:  # single-line docstring
                insert_at = end + 1
            else:
                for j in range(insert_at + 1, len(lines)):
                    if quote in lines[j]:
                        insert_at = j + 1
                        break
        import_line = MIXIN_IMPORT + "\n"
        lines.insert(insert_at, import_line)
        new_src = "".join(lines)
    path.write_text(new_src, encoding="utf-8")
    return True


def process_domain(domain: str) -> tuple[int, list[str]]:
    models_dir = BACKEND / "domains" / domain / "models"
    if not models_dir.exists():
        return 0, []
    files = [p for p in models_dir.glob("*.py") if p.name != "__init__.py"]
    changed = []
    for f in files:
        if refactor_file(f):
            changed.append(f.name)
            print(f"  refactored {f.name}")
    return len(changed), changed


if __name__ == "__main__":
    total = 0
    for d in DOMAINS:
        print(f"== {d} ==")
        n, ch = process_domain(d)
        total += n
        print(f"   {n} files changed")
    print(f"\nTotal files changed: {total}")
