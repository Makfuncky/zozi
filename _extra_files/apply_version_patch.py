import sys, os, re, io, inspect
sys.path.insert(0, os.path.join(os.getcwd(), "backend"))
import models
from sqlalchemy.orm import class_mapper

REQ = ["uuid","created_at","updated_at","is_deleted","deleted_at","version","created_by","updated_by"]

def all_subclasses(cls):
    out=set(); stack=list(cls.__subclasses__())
    while stack:
        c=stack.pop()
        if c in out: continue
        out.add(c); stack.extend(c.__subclasses__())
    return out

targets=[]
for c in all_subclasses(models.Base):
    try: class_mapper(c)
    except Exception: continue
    if not getattr(c,"__tablename__",None): continue
    cols=set(col.name for col in c.__table__.columns)
    missing=[x for x in REQ if x not in cols]
    if missing==["version"]:
        targets.append(c)

by_file={}
for c in targets:
    by_file.setdefault(inspect.getsourcefile(c),[]).append(c.__name__)

def last_import_idx(lines):
    idx=-1
    for i,l in enumerate(lines):
        if re.match(r"^(from |import )", l): idx=i
    return idx

changed_files=0
for fn, names in by_file.items():
    lines=io.open(fn,encoding="utf-8").read().split("\n")
    nameset=set(names)
    for i,l in enumerate(lines):
        m=re.match(r"^class\s+(\w+)\s*\(", l)
        if m and m.group(1) in nameset:
            name=m.group(1)
            # extract base group
            o=m.group(0)
            if "VersionMixin" in l: 
                continue
            # replace "(...)" right after class name
            newl=re.sub(r"(class\s+"+name+r"\s*\()([^)]*)(\))",
                        lambda mm: mm.group(1)+"VersionMixin, "+mm.group(2)+mm.group(3), l, count=1)
            lines[i]=newl
            nameset.discard(name)
    # add import if missing
    if not any("VersionMixin" in l and ("import" in l) for l in lines):
        j=last_import_idx(lines)
        if j>=0:
            lines.insert(j+1, "from db.mixins import VersionMixin")
        else:
            lines.insert(0, "from db.mixins import VersionMixin")
    io.open(fn,"w",encoding="utf-8").write("\n".join(lines))
    changed_files+=1

print("PATCHED FILES:", changed_files)
print("REMAINING UNMATCHED NAMES:", sum(len(v) for v in by_file.values()))
