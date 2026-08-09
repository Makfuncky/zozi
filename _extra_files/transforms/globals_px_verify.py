import re, pathlib, difflib, sys
try:
    import tinycss2
    HAVE = True
except Exception as e:
    HAVE = False
    print("tinycss2 unavailable:", e, file=sys.stderr)

cand = pathlib.Path("_extra_files/transforms/globals_px_candidate.css").read_text(encoding="utf-8")
orig = pathlib.Path("frontend/web_app/src/styles/globals.css").read_text(encoding="utf-8")

print("braces orig {:", orig.count("{"), "}:", orig.count("}"),
      "| cand {:", cand.count("{"), "}:", cand.count("}"))

if HAVE:
    errs = [r.message for r in tinycss2.parse_stylesheet(cand, skip_whitespace=True) if r.type == "error"]
    print("tinycss2 parse errors:", len(errs))
    for e in errs[:8]:
        print("   ", e)

PX_RE = re.compile(r"(?<![\w.])(\d+(?:\.\d+)?)px\b")
print("px literals orig:", len(PX_RE.findall(orig)), "| cand:", len(PX_RE.findall(cand)))

sm = difflib.SequenceMatcher(None, orig.splitlines(), cand.splitlines())
nonpx = 0
for tag, i1, i2, j1, j2 in sm.get_opcodes():
    if tag == "equal":
        continue
    for ln in cand.splitlines()[j1:j2]:
        if not re.search(r"var\(--zozi-space-|px\b", ln):
            nonpx += 1
            print("   NON-PX CHANGED:", ln[:120])
print("non-px changed lines:", nonpx)
print("OK" if (not HAVE or len([r for r in tinycss2.parse_stylesheet(cand, skip_whitespace=True) if r.type=='error'])==0) else "PARSE-FAIL")
