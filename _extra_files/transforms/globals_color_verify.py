import re, collections, pathlib, difflib, sys
try:
    import tinycss2
    HAVE = True
except Exception as e:
    HAVE = False
    print("tinycss2 not available:", e, file=sys.stderr)

ROOT = pathlib.Path("frontend")
cand = pathlib.Path("_extra_files/transforms/globals_color_candidate.css").read_text(encoding="utf-8")
orig = pathlib.Path("frontend/web_app/src/styles/globals.css").read_text(encoding="utf-8")

print("braces orig {:", orig.count("{"), "}:", orig.count("}"),
      "| cand {:", cand.count("{"), "}:", cand.count("}"))

if HAVE:
    errors = []
    for rule in tinycss2.parse_stylesheet(cand, skip_whitespace=True):
        if rule.type == "error":
            errors.append(rule.message)
    print("tinycss2 parse errors in candidate:", len(errors))
    for e in errors[:8]:
        print("   ", e)

# --- diff scope: which lines changed, and are they color-only? ---
odel, cdel = orig.splitlines(), cand.splitlines()
sm = difflib.SequenceMatcher(None, odel, cdel)
changed_lines = 0
noncolor_changes = 0
for tag, i1, i2, j1, j2 in sm.get_opcodes():
    if tag == "equal":
        continue
    changed_lines += (j2 - j1) + (i2 - i1)
    for ln in cdel[j1:j2]:
        # a changed line is acceptable only if it now contains a token var or removed a literal
        if not re.search(r"var\(--zozi-ov-|var\(--zozi-pal-|rgba?\(|#[0-9a-fA-F]{3,8}", ln, re.I):
            noncolor_changes += 1
            print("   NON-COLOR CHANGED LINE:", ln[:120])
print("changed line slots:", changed_lines, "| non-color changed lines:", noncolor_changes)

# --- reclassify candidate for off-palette ---
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
        t = f.read_text(encoding="utf-8", errors="ignore")
        for m in DS_TW.finditer(t):
            vi.setdefault(m.group(2).lower(), m.group(1))
    elif f.suffix.lower() in (".css", ".scss"):
        t = f.read_text(encoding="utf-8", errors="ignore")
        for m in DS_CSSVAR.finditer(t):
            vi.setdefault(m.group(2).lower(), m.group(1))
    elif DS_PAL.search(str(f)):
        t = f.read_text(encoding="utf-8", errors="ignore")
        for m in DS_TW.finditer(t):
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
c_off = collections.Counter()
for rx in (DS_HEX_RE, DS_RGB_RE):
    for m in rx.finditer(cand):
        if classify(m.group(0)) == "off":
            c_off[m.group(0).lower()] += 1
print("CANDIDATE off-palette literals remaining:", sum(c_off.values()), "distinct:", len(c_off))
for k, n in c_off.most_common(20):
    print("   ", k, n)
print("OK" if (not HAVE or len([1 for r in tinycss2.parse_stylesheet(cand, skip_whitespace=True) if r.type=='error'])==0) else "PARSE-FAIL")
