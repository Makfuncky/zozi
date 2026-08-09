import os, re, sys
from pathlib import Path

BACKEND = Path(r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend")
sys.path.insert(0, str(BACKEND))
os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("SECRET_KEY", "test-secret")
os.environ.setdefault("SEED_ADMIN_PASSWORD", "admin123")

from db.base import Base  # noqa: E402
import models  # noqa: E402  (imports employee_models among others)

_FK_RE = re.compile(r"foreign\(\s*(\w+)\.(\w+)\s*\)\s*==\s*(\w+)\.(\w+)")

def _qualify_foreign_keys(metadata):
    for table in metadata.tables.values():
        for fk in list(table.foreign_keys):
            colspec = fk._colspec
            if not isinstance(colspec, str):
                continue
            parts = colspec.split(".")
            if len(parts) != 2:
                continue
            tname, cname = parts
            target = next((t for t in metadata.tables.values() if t.name == tname), None)
            if target is None or not target.schema:
                continue
            fk._colspec = "%s.%s.%s" % (target.schema, tname, cname)
            fk.__dict__.pop("_column_tokens", None)
            fk._unresolvable = False

def _ensure_relationship_foreign_keys(metadata):
    from sqlalchemy import ForeignKey
    for mapper in list(Base.registry.mappers):
        for _name, prop in mapper._props.items():
            init_args = getattr(prop, "_init_args", None)
            if init_args is None:
                continue
            pj_arg = getattr(init_args, "primaryjoin", None)
            pj = getattr(pj_arg, "argument", None) if pj_arg is not None else None
            if not isinstance(pj, str):
                continue
            for _m in _FK_RE.finditer(pj):
                child_cls, child_col, parent_cls, parent_col = _m.groups()
                child_table = next((t for t in metadata.tables.values() if t.name == _table_name_for_class(metadata, child_cls)), None)
                parent_table = next((t for t in metadata.tables.values() if t.name == _table_name_for_class(metadata, parent_cls)), None)
                if child_table is None or parent_table is None:
                    continue
                col = child_table.c.get(child_col)
                if col is None or col.foreign_keys:
                    continue
                col.append_foreign_key(ForeignKey("%s.%s.%s" % (parent_table.schema, parent_table.name, parent_col)))

def _table_name_for_class(metadata, class_name):
    for mapper in Base.registry.mappers:
        if mapper.class_.__name__ == class_name and mapper.local_table is not None:
            return mapper.local_table.name
    return None

_qualify_foreign_keys(Base.metadata)
_ensure_relationship_foreign_keys(Base.metadata)

from sqlalchemy import create_engine
_SCHEMA_MAP = {s: None for s in ["core","commerce","supplier","customer","logistics","finance","treasury","hr","country","media","ai","communication","audit","security","analytics","configuration"]}
eng = create_engine("sqlite://", execution_options={"schema_translate_map": _SCHEMA_MAP})
Base.metadata.create_all(bind=eng)

import models.employee_models as em
missing = []
for name in em.__all__:
    cls = getattr(em, name, None)
    if cls is None or not hasattr(cls, "__table__"):
        continue
    if getattr(cls, "__module__", None) != "models.employee_models":
        continue
    cols = set(c.name for c in cls.__table__.columns)
    for req in ("uuid", "version", "is_deleted", "created_by", "updated_by"):
        if req not in cols:
            missing.append(f"{name}.{req}")
    if "created_at" not in cols or "updated_at" not in cols:
        missing.append(f"{name}.timestamps")
print("create_all OK")
print("employee_models classes checked:", len([n for n in em.__all__ if hasattr(getattr(em,n,None),'__table__')]))
if missing:
    raise SystemExit("MISSING: " + ", ".join(missing))
print("ALL DBA03 columns present on every employee model")
