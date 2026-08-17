import os, re, collections

ROOT = r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend"

def walk_py(folder):
    out=[]
    d=os.path.join(ROOT,folder)
    if not os.path.isdir(d): return out
    for dp,_,fs in os.walk(d):
        for f in fs:
            if f.endswith(".py"):
                out.append(os.path.relpath(os.path.join(dp,f), ROOT))
    return out

for layer in ["services","controllers","routers"]:
    fs=walk_py(layer)
    print(f"{layer:12} raw .py files: {len(fs)}")

# suffix breakdown inside services
svc=walk_py("services")
suff=collections.Counter()
for f in svc:
    name=os.path.basename(f)[:-3].lower()
    toks=re.findall(r"[a-z0-9]+",name)
    suff[toks[-1] if toks else ""]+=1
print("\nservices/ trailing-token breakdown:")
for k,v in suff.most_common():
    print(f"  {k}v {v}")

# controllers: decorator vs shim
ctrl=walk_py("controllers")
have_dec=0; shim=0
for f in ctrl:
    try:
        txt=open(os.path.join(ROOT,f),encoding="utf-8",errors="ignore").read()
    except: continue
    if re.search(r"@(get|post|put|patch|delete)\b", txt): have_dec+=1
    else: shim+=1
print(f"\ncontrollers: {len(ctrl)} total | with route decorator: {have_dec} | shim/no-decorator: {shim}")

# routers: business logic
rtr=walk_py("routers")
biz=0; nobiz=0
for f in rtr:
    try:
        txt=open(os.path.join(ROOT,f),encoding="utf-8",errors="ignore").read()
    except: continue
    if re.search(r"\b(db|session|sql|insert|update|query|model|save|create|await)\b", txt): biz+=1
    else: nobiz+=1
print(f"routers: {len(rtr)} total | with business-logic keywords: {biz} | thin: {nobiz}")
