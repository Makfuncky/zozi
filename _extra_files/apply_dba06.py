"""DBA06 applier (dry-run by default).

For each cross-schema FK:
  * remove `ForeignKey("schema.table.col")` from the Column line
  * if a relationship matches (local col -> remote class), add
    `primaryjoin="LocalClass.local_col == RemoteClass.remote_col"`
    and `foreign_keys=[local_col]` when absent.

Edits are line-based (ast node lineno) to preserve file formatting.
"""
from __future__ import annotations

import io, os, sys, re, argparse, ast, inspect as pyinspect
sys.path.insert(0, os.path.join(os.getcwd(), "backend"))
import main  # noqa
from db.base import Base

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

# Build entries grouped by file
entries_by_file = {}
for t in Base.metadata.tables.values():
    lschema = t.schema or None
    lcls = reg.get((lschema, t.name))
    if lcls is None:
        continue
    mapper = mapper_of[lcls]
    rels = {r.key: r for r in mapper.relationships}
    for fkc in t.foreign_key_constraints:
        for fk in fkc.elements:
            rschema = fk.column.table.schema or None
            if (lschema or None) == (rschema or None):
                continue
            rcls = rname(rschema, fk.column.table.name)
            if rcls is None:
                continue
            lcol = fk.parent.name
            rcol = fk.column.name
            target = f"{rschema}.{fk.column.table.name}.{rcol}" if rschema else f"{fk.column.table.name}.{rcol}"
            matched = [r.key for r in mapper.relationships
                       if r.mapper.class_.__name__ == rcls and lcol in {c.name for c in r.local_columns}]
            f = pyinspect.getsourcefile(mapper.class_)
            entries_by_file.setdefault(f, []).append({
                "cls": lcls, "lcol": lcol, "rcls": rcls, "rcol": rcol,
                "target": target, "rels": matched,
            })

def edit_column_line(line, target):
    pat = r'ForeignKey\(\s*[\'"]' + re.escape(target) + r'[\'"]\s*\)'
    if not re.search(pat, line):
        return None
    new = re.sub(pat, "", line)
    # tidy commas
    new = re.sub(r',\s*,', ',', new)
    new = re.sub(r'\(\s*,', '(', new)
    new = re.sub(r',\s*\)', ')', new)
    return new

def edit_rel_line(line, cls, lcol, rcls, rcol, rels):
    # find relationship( ... ) on this line (single line assumed)
    m = re.search(r'relationship\s*\(', line)
    if not m:
        return None
    if 'primaryjoin=' in line:
        return None  # already has primaryjoin
    pj = f'{cls}.{lcol} == {rcls}.{rcol}'
    # insert before final ')'
    idx = line.rfind(')')
    if idx == -1:
        return None
    foreign = "" if 'foreign_keys=' in line else f', foreign_keys=[{lcol}]'
    new = line[:idx] + f', primaryjoin="{pj}"' + foreign + line[idx:]
    return new

def process_file(f, entries, dry):
    with io.open(f, encoding="utf-8") as fh:
        lines = fh.readlines()
    src = "".join(lines)
    tree = ast.parse(src)
    # map class -> body assignments
    edits = 0
    skips = 0
    # build (class, attr) -> node and (class, relkey)->node
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        cname = node.name
        for item in node.body:
            if not isinstance(item, ast.Assign):
                continue
            if len(item.targets) != 1 or not isinstance(item.targets[0], ast.Name):
                continue
            attr = item.targets[0].id
            val = item.value
            if not isinstance(val, ast.Call):
                continue
            fname = getattr(val.func, "id", getattr(val.func, "attr", ""))
            # column removal
            if fname == "Column":
                for e in entries:
                    if e["cls"] == cname and e["lcol"] == attr:
                        if item.lineno != item.end_lineno:
                            skips += 1
                            continue
                        nl = edit_column_line(lines[item.lineno-1], e["target"])
                        if nl and nl != lines[item.lineno-1]:
                            if not dry:
                                lines[item.lineno-1] = nl
                            edits += 1
            # relationship primaryjoin
            if fname == "relationship":
                for e in entries:
                    if e["cls"] == cname and attr in e["rels"]:
                        if item.lineno != item.end_lineno:
                            skips += 1
                            continue
                        nl = edit_rel_line(lines[item.lineno-1], e["cls"], e["lcol"], e["rcls"], e["rcol"], e["rels"])
                        if nl and nl != lines[item.lineno-1]:
                            if not dry:
                                lines[item.lineno-1] = nl
                            edits += 1
    if not dry:
        with io.open(f, "w", encoding="utf-8") as fh:
            fh.write("".join(lines))
    return edits, skips

def main_():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    dry = not args.apply
    total_edits = 0
    total_skips = 0
    for f in sorted(entries_by_file):
        e, s = process_file(f, entries_by_file[f], dry)
        total_edits += e
        total_skips += s
        print(f"{'DRY' if dry else 'APPLY'} {e:4d} edits, {s:3d} skips  {f}")
    print(f"TOTAL edits={total_edits} skips={total_skips}")

if __name__ == "__main__":
    main_()
