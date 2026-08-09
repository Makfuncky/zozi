import os
roots = ["scripts","backend","."]
hits=[]
for root in roots:
    for dp,_,fns in os.walk(root):
        if ".git" in dp or "__pycache__" in dp: continue
        for fn in fns:
            if fn.endswith((".py",".json",".md",".yaml",".yml",".txt",".cfg",".toml")):
                p=os.path.join(dp,fn)
                try:
                    for i,line in enumerate(open(p,encoding="utf-8",errors="ignore"),1):
                        if "AuditMixin" in line or "DBA03" in line or "mandatory column" in line.lower():
                            hits.append((p,i,line.strip()[:120]))
                except Exception: pass
for h in hits[:40]:
    print(h)
print("TOTAL:", len(hits))
