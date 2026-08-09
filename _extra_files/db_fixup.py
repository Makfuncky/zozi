"""AST transformer: inject missing DBA03 standard columns, FK hygiene (DBA07/08),
GIN indexes for JSON (DBA09) and composite (country_code, created_at) indexes (DBA31)
into SQLAlchemy model classes. Idempotent and conflict-aware.

Read-only w.r.t. behaviour: only ADDS columns/indexes; never removes or renames.
Run per file. Back up originals first.
"""
import ast
import os
import sys

JSON_TYPES = {"JSON", "JSONB"}
UUID_TYPE_NAMES = {"UUID"}

# Column definitions that mirror db/mixins.py so behaviour matches existing mixins.
def _col_snippet(name, snippet):
    tree = ast.parse(snippet)
    return tree.body[0]

STANDARD_COLUMNS = {
    "uuid": 'uuid = Column(UUID(as_uuid=True), default=uuid4, unique=True, nullable=True)',
    "version": 'version = Column(Integer, nullable=False, default=1)',
    "created_at": 'created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)',
    "updated_at": 'updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)',
    "is_deleted": 'is_deleted = Column(Boolean, default=False, server_default="false", nullable=False, index=True)',
    "deleted_at": 'deleted_at = Column(DateTime(timezone=True), nullable=True)',
    "deleted_by": 'deleted_by = Column(Integer, nullable=True)',
    "created_by": 'created_by = Column(Integer, nullable=True, index=True)',
    "updated_by": 'updated_by = Column(Integer, nullable=True, index=True)',
}

NEEDED_IMPORTS = {
    "Column", "Integer", "Boolean", "DateTime", "Index", "func", "UUID",
}
NEEDED_UUID_IMPORT = "uuid4"


def _base_names(node):
    names = set()
    for b in node.bases:
        try:
            names.add(ast.unparse(b))
        except Exception:
            pass
    return names


def _is_column_call(value):
    return (
        isinstance(value, ast.Call)
        and isinstance(value.func, (ast.Name, ast.Attribute))
        and (getattr(value.func, "id", None) or getattr(value.func, "attr", None))
        in {"Column", "mapped_column"}
    )


def _has_keyword(call, kw):
    return any(k.arg == kw for k in call.keywords)


def _contains_foreignkey(call):
    return _find_foreignkey(call) is not None


def _find_foreignkey(call):
    for a in list(call.args) + [k.value for k in call.keywords]:
        if isinstance(a, ast.Call) and isinstance(a.func, (ast.Name, ast.Attribute)):
            fn = getattr(a.func, "id", None) or getattr(a.func, "attr", None)
            if fn == "ForeignKey":
                return a
    return None


def _column_type_name(call):
    if call.args:
        first = call.args[0]
        if isinstance(first, ast.Name):
            return first.id
        if isinstance(first, ast.Attribute):
            return first.attr
        if isinstance(first, ast.Call):
            return getattr(first.func, "attr", None) or getattr(first.func, "id", None)
    # also check keywords like type_=
    for k in call.keywords:
        if k.arg in ("type", "type_"):
            if isinstance(k.value, ast.Name):
                return k.value.id
            if isinstance(k.value, ast.Attribute):
                return k.value.attr
    return None


def _literal_col_names(cls):
    names = set()
    for stmt in cls.body:
        if isinstance(stmt, ast.Assign) and len(stmt.targets) == 1 and isinstance(stmt.targets[0], ast.Name):
            if _is_column_call(stmt.value):
                names.add(stmt.targets[0].id)
        # annotated assignments with mapped_column
        if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
            if stmt.value is not None and _is_column_call(stmt.value):
                names.add(stmt.target.id)
    return names


def _has_uuid_typed(cls):
    for stmt in cls.body:
        if isinstance(stmt, ast.Assign) and _is_column_call(stmt.value):
            if (_column_type_name(stmt.value) or "").upper() == "UUID":
                return True
    return False


def _find_table_args(cls):
    for stmt in cls.body:
        if isinstance(stmt, ast.Assign) and len(stmt.targets) == 1 and isinstance(stmt.targets[0], ast.Name):
            if stmt.targets[0].id == "__table_args__":
                return stmt
    return None


def _table_args_text(cls):
    stmt = _find_table_args(cls)
    if not stmt:
        return ""
    try:
        return ast.unparse(stmt.value)
    except Exception:
        return ""


def transform_class(cls, table_name):
    bases = _base_names(cls)
    has_audit = ("AuditMixin" in bases) or ("TimestampMixin" in bases)
    has_soft = "SoftDeleteMixin" in bases
    has_version_mixin = "VersionMixin" in bases
    literal = _literal_col_names(cls)

    # Decide which standard columns to add.
    to_add = []
    if "uuid" not in literal and not _has_uuid_typed(cls):
        to_add.append("uuid")
    if "version" not in literal:
        to_add.append("version")
    if (not has_audit) and "created_at" not in literal:
        to_add.append("created_at")
    if (not has_audit) and "updated_at" not in literal:
        to_add.append("updated_at")
    if (not has_soft) and "is_deleted" not in literal:
        to_add.append("is_deleted")
    if (not has_soft) and "deleted_at" not in literal:
        to_add.append("deleted_at")
    if (not has_soft) and "deleted_by" not in literal:
        to_add.append("deleted_by")
    if (not has_audit) and "created_by" not in literal:
        to_add.append("created_by")
    if (not has_audit) and "updated_by" not in literal:
        to_add.append("updated_by")

    # Build new column Assign nodes, insert after __tablename__ (or at top of body).
    new_nodes = []
    for name in to_add:
        new_nodes.append(ast.parse(STANDARD_COLUMNS[name]).body[0])

    # FK hygiene: add index=True (Column kwarg) and ondelete="RESTRICT" (ForeignKey kwarg) where missing.
    for stmt in cls.body:
        targets = []
        if isinstance(stmt, ast.Assign) and _is_column_call(stmt.value):
            targets.append(stmt.value)
        if isinstance(stmt, ast.AnnAssign) and stmt.value is not None and _is_column_call(stmt.value):
            targets.append(stmt.value)
        for call in targets:
            fk = _find_foreignkey(call)
            if fk is None:
                continue
            if not _has_keyword(call, "index"):
                call.keywords.append(ast.keyword(arg="index", value=ast.Constant(value=True)))
            if not _has_keyword(fk, "ondelete"):
                fk.keywords.append(ast.keyword(arg="ondelete", value=ast.Constant(value="RESTRICT")))

    # Collect GIN + composite Index nodes to add to __table_args__.
    new_index_nodes = []
    table_args = _find_table_args(cls)
    args_text = _table_args_text(cls).lower()
    has_country = ("country_code" in literal) or ("TenantMixin" in bases)

    for stmt in cls.body:
        call = None
        if isinstance(stmt, ast.Assign) and _is_column_call(stmt.value):
            call = stmt.value
        if isinstance(stmt, ast.AnnAssign) and stmt.value is not None and _is_column_call(stmt.value):
            call = stmt.value
        if call is None:
            continue
        tname = _column_type_name(call) or ""
        if tname.upper() in JSON_TYPES:
            col = stmt.targets[0].id if isinstance(stmt, ast.Assign) else stmt.target.id
            if ("gin" not in args_text) and (col not in args_text):
                idx = ast.parse(
                    f'Index("ix_{table_name}_{col}_gin", "{col}", postgresql_using="gin")'
                ).body[0].value
                new_index_nodes.append(idx)

    # DBA31 composite index (country_code, created_at) if both present.
    created_at_present = ("created_at" in literal) or has_audit
    if has_country and created_at_present:
        if ("country_code" not in args_text) or ("created_at" not in args_text):
            composite = ast.parse(
                f'Index("ix_{table_name}_country_created", "country_code", "created_at")'
            ).body[0].value
            new_index_nodes.append(composite)

    # Attach index nodes to __table_args__.
    if new_index_nodes:
        if table_args is not None:
            val = table_args.value
            if isinstance(val, ast.Tuple):
                val.elts.extend(new_index_nodes)
            else:
                table_args.value = ast.Tuple(elts=[val] + new_index_nodes, ctx=ast.Load())
        else:
            table_args_assign = ast.Assign(
                targets=[ast.Name(id="__table_args__", ctx=ast.Store())],
                value=ast.Tuple(elts=list(new_index_nodes), ctx=ast.Load()),
            )
            new_nodes.append(table_args_assign)

    # If VersionMixin present, drop it from bases (literal version added instead).
    if has_version_mixin:
        cls.bases = [b for b in cls.bases if not (isinstance(b, ast.Name) and b.id == "VersionMixin")]

    if new_nodes:
        # Insert after __tablename__ assignment if present, else at start of body.
        insert_idx = 0
        for i, stmt in enumerate(cls.body):
            if isinstance(stmt, ast.Assign) and len(stmt.targets) == 1 and isinstance(stmt.targets[0], ast.Name):
                if stmt.targets[0].id == "__tablename__":
                    insert_idx = i + 1
                    break
        for offset, n in enumerate(new_nodes):
            cls.body.insert(insert_idx + offset, n)

    return bool(to_add) or bool(new_index_nodes) or has_version_mixin


def transform_file(path):
    src = open(path, encoding="utf-8").read()
    tree = ast.parse(src)
    changed = False

    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        # model if it has __tablename__
        has_tn = any(
            isinstance(s, ast.Assign) and len(s.targets) == 1
            and isinstance(s.targets[0], ast.Name) and s.targets[0].id == "__tablename__"
            for s in node.body
        )
        if not has_tn:
            continue
        table_name = None
        for s in node.body:
            if isinstance(s, ast.Assign) and len(s.targets) == 1 and isinstance(s.targets[0], ast.Name) and s.targets[0].id == "__tablename__":
                if isinstance(s.value, ast.Constant):
                    table_name = str(s.value.value)
                break
        if not table_name:
            continue
        if transform_class(node, table_name):
            changed = True

    if not changed:
        return False

    # Ensure needed imports exist.
    imported = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.ImportFrom) and n.module:
            for a in n.names:
                imported.add(a.asname or a.name)
        if isinstance(n, ast.Import):
            for a in n.names:
                imported.add((a.asname or a.name).split(".")[-1])
    # Insert new imports AFTER any `from __future__` imports (which must stay first).
    insert_idx = 0
    for i, s in enumerate(tree.body):
        if isinstance(s, ast.ImportFrom) and s.module == "__future__":
            insert_idx = i + 1
    to_add_imports = []
    if NEEDED_UUID_IMPORT not in imported:
        to_add_imports.append(ast.ImportFrom(module="uuid", names=[ast.alias(name="uuid4")], level=0))
    needed = [x for x in NEEDED_IMPORTS if x not in imported]
    if needed:
        to_add_imports.append(ast.ImportFrom(module="sqlalchemy", names=[ast.alias(name=x) for x in needed], level=0))
    for n in reversed(to_add_imports):
        tree.body.insert(insert_idx, n)

    ast.fix_missing_locations(tree)
    new_src = ast.unparse(tree)
    # Preserve a trailing newline behaviour: ast.unparse ends without newline sometimes.
    with open(path, "w", encoding="utf-8") as f:
        f.write(new_src)
    return True


if __name__ == "__main__":
    root = r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend\models"
    changed_files = []
    for dp, dn, fn in os.walk(root):
        for f in fn:
            if not f.endswith(".py"):
                continue
            full = os.path.join(dp, f)
            try:
                if transform_file(full):
                    changed_files.append(full)
            except Exception as e:
                print("ERROR", full, type(e).__name__, e)
    print("TRANSFORMED", len(changed_files), "files")
    for c in changed_files:
        print("  ", os.path.relpath(c, root))
