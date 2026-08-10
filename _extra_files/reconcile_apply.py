import os, re, shutil

BACKEND = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
MAIN = os.path.join(BACKEND, "main.py")
BAK = os.path.join(BACKEND, "main.py.reconcile_bak")

if not os.path.exists(BAK):
    shutil.copyfile(MAIN, BAK)

src = open(MAIN, encoding="utf-8").read()

# locate the router_names block
start = src.index("router_names = [")
end = src.index("]", start) + 1
block = src[start:end]

entries = re.findall(r'\("([^"]+)",\s*"([^"]+)"\)', block)

router_stems = {f[:-3] for f in os.listdir(os.path.join(BACKEND, "routers"))
                if f.endswith(".py") and f != "__init__.py"}
ctrl_stems = {f[:-3] for f in os.listdir(os.path.join(BACKEND, "controllers"))
              if f.endswith(".py") and f != "__init__.py"}

kept = [(n, p) for n, p in entries if (n in router_stems or n in ctrl_stems)]
removed = [(n, p) for n, p in entries if not (n in router_stems or n in ctrl_stems)]

new_block = "router_names = [\n"
for n, p in kept:
    new_block += f'        ("{n}", "{p}"),\n'
new_block += "    ]"

new_src = src[:start] + new_block + src[end:]

with open(MAIN, "w", encoding="utf-8") as f:
    f.write(new_src)

print(f"Entries before: {len(entries)}")
print(f"Kept           : {len(kept)}")
print(f"Removed        : {len(removed)}")
for n, p in removed:
    print(f"  - {n} {p}")
