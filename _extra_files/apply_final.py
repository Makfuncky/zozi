"""Final DBA06 applier (dry-run default, --apply to write).

For every cross-schema FK (dba06_plan.json):
  * remove the `ForeignKey(...)` from the owning Column (robust; idempotent).
  * ensure the FORWARD relationship on the FK-owning class has a primaryjoin
    whose FK-owning column is annotated `foreign(...)`. If a primaryjoin
    already exists (hand-written or previously added) it is patched to wrap
    the FK column with foreign(); otherwise one is added using foreign().
  * ensure the REVERSE relationship (on the referenced class) is likewise
    patched/added. Backref-only reverses are not in source and inherit.

Source edits are line-based via ast node lineno; formatting preserved.
"""
from __future__ import annotations

import io, os, sys, re, ast, argparse, json, inspect as pyinspect
sys.path.insert(0, os.path.join(os.getcwd(), "backend"))
import main  # noqa
from db.base import Base

plan = json.load(io.open("_extra_files/dba06_plan.json", encoding="utf-8"))

ctab = {}
for mapper in Base.registry.mappers:
    t = mapper.local_table
    if t is not None:
        ctab[mapper.class_.__name__] = (t.schema or None, t.name)

def file_of(cls_name):
    for mapper in Base.registry.mappers:
        if mapper.class_.__name__ == cls_name:
            return pyinspect.getsourcefile(mapper.class_)
    return None

entries_by_file = {}
for e in plan:
    lf = file_of(e["local_class"]); rf = file_of(e["remote_class"])
    if lf:
        entries_by_file.setdefault(lf, []).append(e)
    if rf and rf != lf:
        entries_by_file.setdefault(rf, []).append(e)

def remove_fk_call(line, target):
    i = line.find("ForeignKey(")
    while i != -1:
        p = line.find("(", i); depth = 0; j = p
        while j < len(line):
            if line[j] == "(":
                depth += 1
            elif line[j] == ")":
                depth -= 1
                if depth == 0:
                    break
            j += 1
        seg = line[i:j+1]
        if target in seg:
            new = line[:i] + line[j+1:]
            new = re.sub(r",\s*,", ",", new)
            new = re.sub(r"\(\s*,", "(", new)
            new = re.sub(r",\s*\)", ")", new)
            return new
        i = line.find("ForeignKey(", i+1)
    return None

def rel_target_str(node):
    if not isinstance(node, ast.Call):
        return None
    if not node.args:
        return None
    a = node.args[0]
    if isinstance(a, ast.Constant) and isinstance(a.value, str):
        return a.value
    if isinstance(a, ast.Name):
        return a.id
    if isinstance(a, ast.Attribute):
        return a.attr
    return None

def find_rel_assignment(class_node, target_class, foreign_col=None):
    cands = []
    for item in class_node.body:
        if not isinstance(item, ast.Assign) or len(item.targets) != 1 or not isinstance(item.targets[0], ast.Name):
            continue
        val = item.value
        if not isinstance(val, ast.Call):
            continue
        fn = getattr(val.func, "id", getattr(val.func, "attr", ""))
        if fn != "relationship" or rel_target_str(val) != target_class:
            continue
        fk_cols = []
        for kw in val.keywords:
            if kw.arg == "foreign_keys":
                if isinstance(kw.value, ast.List):
                    fk_cols += [el.id for el in kw.value.elts if isinstance(el, ast.Name)]
                elif isinstance(kw.value, ast.Name):
                    fk_cols.append(kw.value.id)
        cands.append((item.targets[0].id, item, fk_cols))
    if not cands:
        return None
    if foreign_col is not None:
        for a, n, fc in cands:
            if foreign_col in fc:
                return (a, n)
    return (cands[0][0], cands[0][1])

def add_primaryjoin_pj(line, pj):
    if "primaryjoin=" in line:
        return None
    m = re.search(r"relationship\s*\(", line)
    if not m:
        return None
    idx = line.rfind(")")
    if idx == -1:
        return None
    return line[:idx] + f', primaryjoin="{pj}"' + line[idx:]

def strip_foreign_keys(line):
    return re.sub(r",\s*foreign_keys\s*=\s*\[[^\]]*\]", "", line)

def ensure_foreign(line, local_class, local_col):
    schema, table = ctab.get(local_class, (None, local_class))
    m = re.search(r'primaryjoin="([^"]*)"', line)
    if not m:
        return None
    inner = m.group(1)
    if "foreign(" in inner:
        return None
    alts = [re.escape(local_class) + r"\." + re.escape(local_col),
            (re.escape(schema) + r"\." + re.escape(table) + r"\." + re.escape(local_col)) if schema else None,
            re.escape(table) + r"\." + re.escape(local_col),
            r"(?<![\w.])" + re.escape(local_col) + r"(?![\w.])"]
    alts = [a for a in alts if a]
    ref = re.search("|".join(alts), inner)
    if not ref:
        return None
    new_inner = inner[:ref.start()] + "foreign(" + ref.group(0) + ")" + inner[ref.end():]
    return line[:m.start(1)] + new_inner + line[m.end(1):]

def process_file(f, entries, dry):
    with io.open(f, encoding="utf-8") as fh:
        lines = fh.readlines()
    tree = ast.parse("".join(lines))
    edits = skips = 0
    classes = {n.name: n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)}
    changes = []
    for cls_name, cnode in classes.items():
        for e in [x for x in entries if x["local_class"] == cls_name]:
            # column removal
            for item in cnode.body:
                if isinstance(item, ast.Assign) and isinstance(item.targets[0], ast.Name) and item.targets[0].id == e["local_col"]:
                    if item.lineno == item.end_lineno:
                        nl = remove_fk_call(lines[item.lineno-1], e["fk_target"])
                        if nl and nl != lines[item.lineno-1]:
                            changes.append((item.lineno, nl)); edits += 1
                    else:
                        skips += 1
            # forward relationship
            r = find_rel_assignment(cnode, e["remote_class"], e["local_col"])
            if r:
                attr, node = r
                if node.lineno == node.end_lineno:
                    line = lines[node.lineno-1]
                    if "primaryjoin=" in line:
                        nl = ensure_foreign(line, e["local_class"], e["local_col"])
                        if nl and nl != line:
                            nl = strip_foreign_keys(nl)
                            if nl != lines[node.lineno-1]:
                                changes.append((node.lineno, nl)); edits += 1
                    else:
                        pj = f'foreign({e["local_class"]}.{e["local_col"]}) == {e["remote_class"]}.{e["remote_col"]}'
                        nl = add_primaryjoin_pj(line, pj)
                        if nl and nl != line:
                            changes.append((node.lineno, nl)); edits += 1
                else:
                    skips += 1
        for e in [x for x in entries if x["remote_class"] == cls_name]:
            # reverse relationship
            r = find_rel_assignment(cnode, e["local_class"])
            if r:
                attr, node = r
                if node.lineno == node.end_lineno:
                    line = lines[node.lineno-1]
                    if "primaryjoin=" in line:
                        nl = ensure_foreign(line, e["local_class"], e["local_col"])
                        if nl and nl != line:
                            changes.append((node.lineno, nl)); edits += 1
                    else:
                        pj = f'{e["remote_class"]}.{e["remote_col"]} == foreign({e["local_class"]}.{e["local_col"]})'
                        nl = add_primaryjoin_pj(line, pj)
                        if nl and nl != line:
                            changes.append((node.lineno, nl)); edits += 1
                else:
                    skips += 1
    for ln, nl in changes:
        lines[ln-1] = nl
    if not dry and changes:
        with io.open(f, "w", encoding="utf-8") as fh:
            fh.write("".join(lines))
    return edits, skips, len(changes)

def main_():
    ap = argparse.ArgumentParser(); ap.add_argument("--apply", action="store_true")
    args = ap.parse_args(); dry = not args.apply
    te = ts = tc = 0
    for f in sorted(entries_by_file):
        e, s, c = process_file(f, entries_by_file[f], dry)
        te += e; ts += s; tc += c
        print(f"{'DRY' if dry else 'APPLY'} edits={e:4d} skips={s:3d} changed={c:4d}  {f}")
    print(f"TOTAL edits={te} skips={ts} changed={tc}")

if __name__ == "__main__":
    main_()
