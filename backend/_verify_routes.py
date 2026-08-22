import main
from fastapi.routing import APIRoute
seen = {}
dups = []
total = 0
for rt in main.app.routes:
    if isinstance(rt, APIRoute):
        total += 1
        key = (frozenset(rt.methods), rt.path)
        if key in seen: dups.append(key)
        else: seen[key] = 1
print("APIRoute count:", total)
print("unique (method,path):", len(seen))
print("DUPLICATE (method,path) keys:", len(dups))
for d in dups[:30]:
    print("   DUP:", " ".join(sorted(d[0])), d[1])
