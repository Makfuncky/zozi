import os
root = "backend/models"
hits = []
for dp,_,fns in os.walk(root):
    for fn in fns:
        if not fn.endswith(".py"): continue
        p = os.path.join(dp,fn)
        for i,line in enumerate(open(p,encoding="utf-8"),1):
            if "version" in line and "Column" in line and ("=" in line.split("version")[1][:12]):
                hits.append((p,i,line.strip()))
for h in hits:
    print(h)
print("TOTAL:", len(hits))
