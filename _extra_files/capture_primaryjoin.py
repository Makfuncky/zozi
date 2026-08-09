"""Restore cross-schema FKs in-memory (no file change), let SQLAlchemy infer
each cross-schema relationship's primaryjoin, serialize to a string, and emit
an edit plan. Handles forward + backref-reverse uniformly.
"""
from __future__ import annotations

import io, os, sys, json, inspect as pyinspect
sys.path.insert(0, os.path.join(os.getcwd(), "backend"))
import main  # noqa
from db.base import Base
from sqlalchemy import ForeignKey, inspect as sa_inspect

plan = json.load(io.open("_extra_files/dba06_plan.json", encoding="utf-8"))

reg = {}
for mapper in Base.registry.mappers:
    cls = mapper.class_
    t = mapper.local_table
    if t is not None:
        reg[cls.__name__] = (t.schema or None, t.name)

def find_table(schema, name):
    for t in Base.metadata.tables.values():
        if t.name == name and (t.schema or None) == (schema or None):
            return t
    return None

restored = 0
for e in plan:
    lcls = e["local_class"]; rcls = e["remote_class"]
    lschema, ltable = reg[lcls]
    target = e["fk_target"]  # e.g. core.users.id or users.id
    lcol = e["local_col"]
    t = find_table(lschema, ltable)
    if t is None:
        print("NO TABLE", lcls, ltable)
        continue
    col = t.c[lcol]
    if col.foreign_keys:
        continue
    fk = ForeignKey(target)
    col.foreign_keys.add(fk)
    restored += 1
print("restored FKs in-memory:", restored)

from sqlalchemy.orm import configure_mappers
configure_mappers()
print("CONFIGURED OK with restored FKs")

colmap = {}
for mapper in Base.registry.mappers:
    cls = mapper.class_
    for c in mapper.columns:
        colmap[id(c)] = (cls.__name__, c.name)

def ser(clause):
    from sqlalchemy.sql.elements import BinaryExpression
    from sqlalchemy.sql.operators import and_
    if isinstance(clause, BinaryExpression):
        op = clause.operator
        l = ser(clause.left); r = ser(clause.right)
        if op is and_:
            return f"and_({l}, {r})"
        return f"{l} == {r}"
    key = id(clause)
    if key in colmap:
        return f"{colmap[key][0]}.{colmap[key][1]}"
    try:
        return clause.name
    except Exception:
        return str(clause)

edits = []
for mapper in Base.registry.mappers:
    cls = mapper.class_
    t = mapper.local_table
    if t is None:
        continue
    Psch = t.schema or None
    for rel in mapper.relationships:
        ct = rel.mapper.local_table
        if ct is None:
            continue
        Csch = ct.schema or None
        if (Psch or None) == (Csch or None):
            continue
        pj = rel.primaryjoin
        pj_str = ser(pj)
        fks = [ser(fc) for fc in rel.foreign_keys]
        edits.append({
            "file": pyinspect.getsourcefile(cls),
            "cls": cls.__name__, "rel": rel.key,
            "pj": pj_str, "fks": fks,
        })

print(f"cross-schema relationship edits: {len(edits)}")
for e in edits[:25]:
    print(" ", e["cls"], e["rel"], "->", e["pj"], "| fks:", e["fks"])
json.dump(edits, io.open("_extra_files/rel_primaryjoin.json", "w", encoding="utf-8"), indent=2)
print("written rel_primaryjoin.json")
