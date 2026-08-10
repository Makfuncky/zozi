import os, re

BACKEND = os.path.join(os.path.dirname(__file__), "..", "backend")
BACKEND = os.path.abspath(BACKEND)

src = open(os.path.join(BACKEND, "main.py"), encoding="utf-8").read()
m = re.search(r"router_names = \[(.*?)\n    \]", src, re.S)
entries = re.findall(r'\("([^"]+)",\s*"([^"]+)"\)', m.group(1))

router_stems = {f[:-3] for f in os.listdir(os.path.join(BACKEND, "routers"))
                if f.endswith(".py") and f != "__init__.py"}
ctrl_stems = {f[:-3] for f in os.listdir(os.path.join(BACKEND, "controllers"))
              if f.endswith(".py") and f != "__init__.py"}

dangling = []
existing = []
for name, prefix in entries:
    if name in router_stems or name in ctrl_stems:
        existing.append((name, prefix))
    else:
        dangling.append((name, prefix))

print("TOTAL names:", len(entries))
print("EXISTING   :", len(existing))
print("DANGLING   :", len(dangling))
print("--- DANGLING (no router or controller file) ---")
for n, p in dangling:
    print(f"{n:30s} {p}")

# duplicate names within the list
from collections import Counter
c = Counter(n for n, _ in entries)
dups = {k: v for k, v in c.items() if v > 1}
print("--- DUPLICATE names in list ---")
for k, v in dups.items():
    print(f"{k}: {v}")
