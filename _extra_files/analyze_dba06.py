"""DBA06 analysis: enumerate every cross-schema FK and the edits required.

Outputs a JSON plan consumed by the applier. Also prints anomaly categories
so we can review before mutating 269 constraints.
"""
from __future__ import annotations

import io, os, sys, json
sys.path.insert(0, os.path.join(os.getcwd(), "backend"))
import main  # noqa
from db.base import Base
from sqlalchemy import inspect as sa_inspect

# registry: (schema, table) -> class name
reg = {}
mapper_of = {}
for mapper in Base.registry.mappers:
    cls = mapper.class_
    t = mapper.local_table
    if t is not None:
        reg[(t.schema, t.name)] = cls.__name__
        mapper_of[cls.__name__] = mapper

def rname(schema, table):
    return reg.get((schema, table))

plan = []
inline = 0
table_level = 0
rel_missing = 0
rel_ambiguous = []
composite = []

for t in Base.metadata.tables.values():
    lschema = t.schema or None
    for fkc in t.foreign_key_constraints:
        elements = list(fkc.elements)
        # Determine if cross-schema
        targets = set()
        for fk in elements:
            rschema = fk.column.table.schema or None
            targets.add((rschema, fk.column.table.name))
        # A constraint is "cross-schema" if ANY element crosses schemas
        is_cross = False
        for fk in elements:
            rschema = fk.column.table.schema or None
            if (lschema or None) != (rschema or None):
                is_cross = True
        if not is_cross:
            continue
        # local class
        lcls = reg.get((lschema, t.name))
        if lcls is None:
            composite.append(("no-local-class", t.name))
            continue
        mapper = mapper_of[lcls]
        rels = mapper.relationships
        for fk in elements:
            rschema = fk.column.table.schema or None
            rtable = fk.column.table.name
            rcol = fk.column.name
            lcol = fk.parent.name
            rcls = rname(rschema, rtable)
            if rcls is None:
                composite.append(("no-remote-class", f"{rschema}.{rtable}"))
                continue
            # find matching relationship
            matches = []
            for rel in rels:
                if rel.mapper.class_.__name__ != rcls:
                    continue
                local_cols = {c.name for c in rel.local_columns}
                if lcol in local_cols:
                    matches.append(rel)
            if len(matches) == 0:
                rel_missing += 1
            elif len(matches) > 1:
                rel_ambiguous.append((lcls, lcol, rcls, [m.key for m in matches]))
            plan.append({
                "kind": "inline" if len(elements) == 1 else "composite",
                "file": None,  # filled by applier via getsourcefile
                "local_class": lcls,
                "local_col": lcol,
                "remote_class": rcls,
                "remote_col": rcol,
                "fk_target": f"{rschema}.{rtable}.{rcol}" if rschema else f"{rtable}.{rcol}",
                "rel_keys": [m.key for m in matches],
                "rel_count": len(matches),
            })
            inline += 1

print("inline cross-schema FK elements:", inline)
print("relationships with NO match (FK only, no rel):", rel_missing)
print("ambiguous rel matches:", len(rel_ambiguous))
for a in rel_ambiguous[:20]:
    print("   AMBIG:", a)
print("anomalies (no class):", len(composite), composite[:10])
print("TOTAL plan entries:", len(plan))

with io.open("_extra_files/dba06_plan.json", "w", encoding="utf-8") as f:
    json.dump(plan, f, indent=2)
print("plan written")
