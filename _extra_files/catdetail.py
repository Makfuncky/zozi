import json, collections, re
rows = json.load(open("_extra_files/findings.json",encoding="utf-8"))
def norm(l): return l.replace("\\","/").split(":")[0]
S = {"\U0001f534":"RED","\U0001f7e1":"ADV","\U0001f7e2":"INFO"}
for r in rows: r["s"] = S.get(r["sev"], r["sev"])
p = re.compile(r"(catalog|product|categor|inventory|search|filter|moderation)", re.I)
sel = [r for r in rows if p.search(norm(r["loc"])) and norm(r["loc"]).startswith("backend")]
# exclude data/ facade + tests
sel = [r for r in sel if not norm(r["loc"]).startswith("backend/data/") and not norm(r["loc"]).startswith("backend/tests/")]
out=[]
for code in ["LC1","W1","W3","CIR1","DOM7","DOM2","P5","A2","RN1","API101","SC101","CA1","DBA02","MET5","DS02"]:
    g=[r for r in sel if r["code"]==code]
    if not g: continue
    out.append(f"\n===== {code} ({len(g)}) =====")
    for r in g: out.append(f"[{r['s']}] {r['loc']}\n     {r['msg']}")
print("\n".join(out))
