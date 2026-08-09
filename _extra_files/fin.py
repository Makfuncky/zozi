import json, collections, re
rows = json.load(open("_extra_files/findings.json",encoding="utf-8"))
def norm(l): return l.replace("\\","/").split(":")[0]
S = {"\U0001f534":"RED","\U0001f7e1":"ADV","\U0001f7e2":"INFO"}
for r in rows: r["s"] = S.get(r["sev"], r["sev"])
fin_pat = re.compile(r"(finance|commission|accounting|billing|payout|treasury|payment|cash|settlement|reconcil|erp|ledger|invoice)", re.I)
sel = [r for r in rows if fin_pat.search(norm(r["loc"]))]
print("finance-ish findings:", len(sel), " RED:", sum(1 for r in sel if r["s"]=="RED"))
c = collections.Counter((r["s"], r["code"]) for r in sel)
for (sev,code),n in sorted(c.items(), key=lambda x:(x[0]!="RED",-x[1])):
    print(f"{n:5d} {sev} {code}")
print()
f = collections.Counter(norm(r["loc"]) for r in sel)
print("== TOP FILES ==")
for k,v in f.most_common(30): print(f"{v:5d}  {k}")
