import json, collections, re
rows = json.load(open("_extra_files/findings.json",encoding="utf-8"))
def norm(l): return l.replace("\\","/").split(":")[0]
S = {"\U0001f534":"RED","\U0001f7e1":"ADV","\U0001f7e2":"INFO"}
for r in rows: r["s"] = S.get(r["sev"], r["sev"])
p = re.compile(r"(catalog|product|categor|inventory|search|filter|moderation)", re.I)
sel = [r for r in rows if p.search(norm(r["loc"])) and norm(r["loc"]).startswith("backend")]
print("CATALOG:", len(sel), "RED:", sum(1 for r in sel if r["s"]=="RED"))
c = collections.Counter((r["s"], r["code"]) for r in sel)
for (sev,code),n in sorted(c.items(), key=lambda x:(x[0]!="RED",-x[1])): print(f"{n:5d} {sev} {code}")
print("\n== FILES ==")
for k,v in collections.Counter(norm(r["loc"]) for r in sel).most_common(50): print(f"{v:4d}  {k}")
