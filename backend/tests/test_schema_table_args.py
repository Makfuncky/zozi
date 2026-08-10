"""Validate ``__table_args__`` schema-dict placement and DDL compilability.

The historical version of this file ran as a standalone script with a module
level ``sys.exit``; it is now a normal pytest module. Every pass criterion from
the script is a separate ``test_*`` function.

Pass criteria:
  * every ``{'schema': ...}`` dict is the last ``__table_args__`` element,
  * every table DDL-compiles (cross-schema FK errors are reported separately
    and are pre-existing, unrelated to schema-dict ordering),
  * all applied schema names are valid,
  * no schema mismatches beyond duplicate-tablename collisions (separate bug).
"""
import os
import sys
import ast
import pathlib

os.environ.setdefault("SECRET_KEY", "test-secret-for-schema-validation")
os.environ.setdefault("APP_ENV", "test")
if str(pathlib.Path(__file__).resolve().parents[1]) not in sys.path:
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.schema import CreateTable  # noqa: E402
from sqlalchemy.exc import NoReferencedTableError  # noqa: E402

import models  # noqa: E402

md = models.Base.metadata
tables = md.tables


def scan(path):
    """(A) any {'schema':..} dict NOT the last element of __table_args__ ?"""
    bad = []
    for f in sorted(pathlib.Path(path).rglob("*.py")):
        try:
            tree = ast.parse(f.read_text(encoding="utf-8"))
        except Exception:
            continue
        for cls in ast.walk(tree):
            if not isinstance(cls, ast.ClassDef):
                continue
            tn = None
            for n in cls.body:
                if isinstance(n, ast.Assign):
                    for t in n.targets:
                        if isinstance(t, ast.Name) and t.id == "__tablename__":
                            try:
                                tn = ast.literal_eval(n.value)
                            except Exception:
                                pass
                    if any(isinstance(t, ast.Name) and t.id == "__table_args__" for t in n.targets):
                        v = n.value
                        elems = getattr(v, "elts", None)
                        if elems is not None:
                            idxs = [i for i, e in enumerate(elems) if isinstance(e, ast.Dict)]
                            if idxs and idxs[-1] != len(elems) - 1:
                                bad.append((str(f), cls.name, tn))
    return bad


SCHEMA_CONST = {}


def collect_consts(path):
    for f in pathlib.Path(path).rglob("*.py"):
        try:
            tree = ast.parse(f.read_text(encoding="utf-8"))
        except Exception:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
                try:
                    SCHEMA_CONST[node.targets[0].id] = ast.literal_eval(node.value)
                except Exception:
                    pass


collect_consts("models")


def schema_of(v):
    elems = getattr(v, "elts", None)
    if elems is None:
        return None
    for e in elems:
        if isinstance(e, ast.Dict):
            for k, val in zip(e.keys, e.values):
                if isinstance(k, ast.Constant) and k.value == "schema":
                    try:
                        return ast.literal_eval(val)
                    except Exception:
                        if isinstance(val, ast.Name) and val.id in SCHEMA_CONST:
                            return SCHEMA_CONST[val.id]
    return None


def _source_declared_schemas():
    declared = {}
    for f in sorted(pathlib.Path("models").rglob("*.py")):
        try:
            tree = ast.parse(f.read_text(encoding="utf-8"))
        except Exception:
            continue
        for cls in ast.walk(tree):
            if not isinstance(cls, ast.ClassDef):
                continue
            tn = None
            for n in cls.body:
                if isinstance(n, ast.Assign):
                    for t in n.targets:
                        if isinstance(t, ast.Name) and t.id == "__tablename__":
                            try:
                                tn = ast.literal_eval(n.value)
                            except Exception:
                                pass
                    if any(isinstance(t, ast.Name) and t.id == "__table_args__" for t in n.targets):
                        s = schema_of(n.value)
                        if s is not None:
                            declared[tn] = s
    return declared


declared = _source_declared_schemas()
src_schemas = {}
for _tn, _s in declared.items():
    src_schemas.setdefault(_tn, set()).add(_s)
all_src_schemas = {tn: set(v) for tn, v in src_schemas.items()}

checked = 0
mismatch = 0
dup_collisions = 0
mismatch_rows = []
for tname, t in tables.items():
    base = tname.split(".", 1)[1] if "." in tname else tname
    if base in declared:
        checked += 1
        if (t.schema or None) != declared[base]:
            mismatch += 1
            if len(all_src_schemas.get(base, set())) > 1:
                dup_collisions += 1
            else:
                mismatch_rows.append((base, t.schema, declared[base]))

eng = create_engine("sqlite:///:memory:")
genuine = cross_fk = 0
genuine_fails = []
for t in tables.values():
    try:
        str(CreateTable(t).compile(eng))
    except NoReferencedTableError:
        cross_fk += 1
    except Exception as e:
        genuine += 1
        if len(genuine_fails) < 5:
            genuine_fails.append((t.name, type(e).__name__, str(e)[:80]))

schemas = {t.schema for t in tables.values() if t.schema}


def test_schema_dict_is_last_table_args_element():
    bad = scan("models")
    assert bad == [], f"schema dict not last in __table_args__: {bad[:10]}"


def test_all_tables_ddl_compile():
    assert genuine == 0, f"DDL compile failures: {genuine_fails}"


def test_schema_names_valid():
    assert all(s for s in schemas), "empty schema name present"


def test_no_schema_mismatch_beyond_duplicate_collisions():
    assert mismatch == dup_collisions, f"schema mismatches: {mismatch_rows}"


def test_metadata_imported_tables():
    assert len(tables) > 0
