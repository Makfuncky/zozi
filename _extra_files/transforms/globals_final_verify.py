import re, pathlib, sys, collections
try:
    import tinycss2
    HAVE = True
except Exception as e:
    HAVE = False
    print("tinycss2 unavailable:", e, file=sys.stderr)

g = pathlib.Path("frontend/web_app/src/styles/globals.css").read_text(encoding="utf-8")
t = pathlib.Path("frontend/web_app/src/styles/tokens.css").read_text(encoding="utf-8")

print("=== LIVE globals.css ===")
print("bytes:", len(g.encode("utf-8")), "| lines:", g.count(chr(10)) + 1)
print("braces {:", g.count("{"), "}:", g.count("}"))
if HAVE:
    errs = [r.message for r in tinycss2.parse_stylesheet(g, skip_whitespace=True) if r.type == "error"]
    print("tinycss2 parse errors:", len(errs))
    for e in errs[:8]:
        print("   ", e)

# tokens defined in tokens.css
defined = set(re.findall(r"(--[\w-]+)\s*:", t))
print("tokens.css token count:", len(defined))

# every var(--x) referenced in globals.css must be defined in tokens.css
refs = collections.Counter(re.findall(r"var\((--[\w-]+)", g))
missing = [v for v in refs if v not in defined]
print("distinct var() refs in globals.css:", len(refs))
print("MISSING token defs:", missing if missing else "NONE")

# px + color residual counts
PX_RE = re.compile(r"(?<![\w.])(\d+(?:\.\d+)?)px\b")
print("px literals remaining:", len(PX_RE.findall(g)))

# off-palette reclassification (reuse reconstructed palette)
ROOT = pathlib.Path("frontend")
DS_RGB_RE = re.compile(r"rgba?\(\s*[\d.]+[,\s]+[\d.]+[,\s]+[\d.]+(?:[,\s]+[\d.]+)?\s*\)", re.I)
DS_HEX_RE = re.compile(r"#(?:[0-9a-fA-F]{8}|[0-9a-fA-F]{6}|[0-9a-fA-F]{3,4})\b")
DS_TW = re.compile(r"([\w\$-]+)\s*:\s*['\"](#[0-9a-fA-F]{3,8})['\"]")
DS_CSSVAR = re.compile(r"(--[\w-]+)\s*:\s*(#[0-9a-fA-F]{3,8}|rgba?\([^\)]+\)|hsla?\([^\)]+\))", re.I)
DS_PAL = re.compile(r"(^|[/\\])(colors|tokens|theme|palette)\.(ts|tsx|js|jsx)$", re.I)
IGNORE = {"node_modules", ".next", "dist", "build", ".git", ".turbo", "coverage"}
vi = {}
def walk(d):
    for e in d.iterdir():
        if e.is_dir():
            if e.name in IGNORE:
                continue
            yield from walk(e)
        else:
            yield e
for f in walk(ROOT):
    nm = f.name
    if nm.startswith("tailwind.config"):
        for m in DS_TW.finditer(f.read_text(encoding="utf-8", errors="ignore")):
            vi.setdefault(m.group(2).lower(), m.group(1))
    elif f.suffix.lower() in (".css", ".scss"):
        for m in DS_CSSVAR.finditer(f.read_text(encoding="utf-8", errors="ignore")):
            vi.setdefault(m.group(2).lower(), m.group(1))
    elif DS_PAL.search(str(f)):
        for m in DS_TW.finditer(f.read_text(encoding="utf-8", errors="ignore")):
            vi.setdefault(m.group(2).lower(), m.group(1))
def h2rgb(h):
    h = h.strip().lstrip("#").lower()
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    elif len(h) == 4:
        h = "".join(c * 2 for c in h[:3])
    elif len(h) == 8:
        h = h[:6]
    if len(h) != 6:
        return None
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))
pal = [h2rgb(h) for h in vi if h2rgb(h)]
def cds(a, b):
    rm = (a[0] + b[0]) / 2
    dr, dg, db = a[0] - b[0], a[1] - b[1], a[2] - b[2]
    return ((2 + rm / 256) * dr * dr + 4 * dg * dg + (2 + (255 - rm) / 256) * db * db) ** 0.5
def classify(lit):
    lit = lit.strip().lower()
    rgb = h2rgb(lit) if lit.startswith("#") else None
    if rgb is None:
        return "off"
    if lit in vi:
        return "token"
    return "near-token" if min((cds(rgb, p) for p in pal), default=9999) <= 10.0 else "off"
off = 0
for rx in (DS_HEX_RE, DS_RGB_RE):
    for m in rx.finditer(g):
        if classify(m.group(0)) == "off":
            off += 1
print("off-palette literals remaining:", off)
print("FINAL OK" if (not HAVE or len([r for r in tinycss2.parse_stylesheet(g, skip_whitespace=True) if r.type=='error'])==0) and not missing else "CHECK")
