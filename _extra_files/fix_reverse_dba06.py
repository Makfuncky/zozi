"""Enumerate cross-schema relationships WITHOUT triggering configure_mappers,
derive the primaryjoin string, and apply it (reverse + any missed forward)."""
from __future__ import annotations

import io, os, sys, re, ast, inspect as pyinspect, json
sys.path.insert(0, os.path.join(os.getcwd(), "backend"))
import main  # noqa  (imports models; does NOT configure mappers)
from db.base import Base

reg = {}
mapper_of = {}
pk_of = {}
for mapper in Base.registry.mappers:
    cls = mapper.class_
    t = mapper.local_table
    if t is not None:
        reg[(t.schema, t.name)] = cls.__name__
        mapper_of[cls.__name__] = mapper
        pks = [c.name for c in mapper.primary_key]
        pk_of[cls.__name__] = pks[0] if pks else None

fkmap = {}
for t in Base.metadata.tables.values():
    lschema = t.schema or None
    for fkc in t.foreign_key_constraints:
        for fk in fkc.elements:
            rschema = fk.column.table.schema or None
            if (lschema or None) == (rschema or None):
                continue
            key = (lschema, t.name, rschema, fk.column.table.name)
            fkmap.setdefault(key, []).append((fk.parent.name, fk.column.name))


def candidate(Pcls, Psch, Ptbl, Ccls, CSch, Ctbl):
    cands = []
    kA = (Psch, Ptbl, CSch, Ctbl)
    if kA in fkmap:
        for fk_col, ref_col in fkmap[kA]:
            cands.append(f"{Pcls}.{fk_col} == {Ccls}.{ref_col}")
    kB = (CSch, Ctbl, Psch, Ptbl)
    if kB in fkmap:
        for fk_col, ref_col in fkmap[kB]:
            cands.append(f"{Pcls}.{ref_col} == {Ccls}.{fk_col}")
    return cands


problems = []
for mapper in Base.registry.mappers:
    cls = mapper.class_
    t = mapper.local_table
    if t is None:
        continue
    Psch, Ptbl, Pcls = t.schema or None, t.name, cls.__name__
    for key, prop in mapper._props.items():
        if not isinstance(prop, __import__("sqlalchemy").orm.RelationshipProperty):
            continue
        try:
            target = prop.mapper
        except Exception:
            continue
        ct = target.local_table
        if ct is None:
            continue
        CSch, Ctbl, Ccls = ct.schema or None, ct.name, target.class_.__name__
        if (Psch or None) == (CSch or None):
            continue
        cands = candidate(Pcls, Psch, Ptbl, Ccls, CSch, Ctbl)
        problems.append({
            "file": pyinspect.getsourcefile(cls),
            "cls": Pcls, "rel": key, "Ccls": Ccls,
            "cands": cands,
        })

manual = [p for p in problems if not p["cands"]]
multi = [p for p in problems if len(p["cands"]) > 1]
print(f"cross-schema relationships: {len(problems)}")
print(f"  NO candidate: {len(manual)}")
print(f"  MULTI candidate: {len(multi)}")
for p in manual[:40]:
    print("  NOCAND", p["cls"], p["rel"], "->", p["Ccls"])
for p in multi[:40]:
    print("  MULTI ", p["cls"], p["rel"], "->", p["Ccls"], "::", p["cands"])

with io.open("_extra_files/reverse_rel.json", "w", encoding="utf-8") as f:
    json.dump(problems, f, indent=2)
print("written")
