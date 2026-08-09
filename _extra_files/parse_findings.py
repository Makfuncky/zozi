import re, collections, json
p = "SYSTEM_AUDIT_REPORT.md"
lines = open(p, encoding="utf-8").read().splitlines()
sec = lines[3456:8513]
rows = []
cur = None
pat = re.compile(r"^- (\S+) \*\*([A-Z0-9]+)\*\* `([^`]*)` — (.*)$")
for ln in sec:
    m = re.match(r"^### (.+?) \((\d+) findings\)", ln)
    if m:
        cur = m.group(1); continue
    m2 = pat.match(ln)
    if m2:
        sev, code, loc, msg = m2.groups()
        rows.append({"domain":cur,"sev":sev,"code":code,"loc":loc,"msg":msg})
print("rows", len(rows))
json.dump(rows, open("_extra_files/findings.json","w",encoding="utf-8"), indent=0)
# group by top-level module path
def mod(loc):
    l = loc.replace("\\","/")
    parts = l.split(":")[0].split("/")
    return "/".join(parts[:3])
c = collections.Counter()
red = collections.Counter()
for r in rows:
    k = mod(r["loc"])
    c[k]+=1
    if "🔴" in r["sev"]: red[k]+=1
print("\n== TOP MODULES BY RED ==")
for k,v in red.most_common(30): print(f"{v:5d} red / {c[k]:5d} tot  {k}")
