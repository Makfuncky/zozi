import re
from pathlib import Path

paths = [ln.strip() for ln in Path(r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\_extra_files\all_services.txt").read_text().splitlines()
         if ln.strip() and ln.strip().endswith(".py")]

BASE = {"service","services","controller","controllers","handler","handlers","helper","helpers",
        "util","utils","common","base","abstract","interface","impl","write","read","create",
        "update","delete","get","list","bulk","batch","query","router","routes","ops","operations",
        "operation","admin","public","core","api","unified","fallback","v1","v2","v3","new","old",
        "temp","job","jobs","legacy","sync","upload","uploads","download","mgr","svc","fn","func","function"}
ROLE = {"engine","manager","managers","worker","scheduler","scheduling","background","query","router"}

def norm(t):
    if t.endswith("ies") and len(t) > 4:
        return t[:-3] + "y"
    if t.endswith("s") and len(t) > 3:
        return t[:-1]
    return t

def count(stop):
    g = set()
    for p in paths:
        stem = Path(p).stem.lower()
        toks = [t for t in re.split(r"[_\-]", stem) if t and t not in stop]
        key = tuple(sorted(norm(t) for t in toks))
        if not key:
            key = (stem,)
        g.add(key)
    return len(g)

print("A) engine v9.3 stop (role tokens stripped):", count(BASE | ROLE))
print("B) surface-only stop (role tokens kept):    ", count(BASE))
print("C) raw files:                                ", len(paths))
