"""
Batch B — DS11 shadow normalization for globals.css.

Maps every `box-shadow`/`text-shadow` declaration onto exactly FOUR canonical
tokens so the audit's distinct-shadow count drops to <=4:
  --zozi-elevation-sm / -md / -lg   (ambient elevation, bucketed by size)
  --zozi-ring                       (focus-ring outlines: `0 0 0 Npx`)

The 2 redundant `box-shadow: none` resets are removed (they are the default and
only add a 5th distinct value). This script NEVER deletes globals.css; it writes
an incremental backup and emits a candidate for review.
"""
import os
import re
import shutil
import sys
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(ROOT, "frontend", "web_app", "src", "styles", "globals.css")
BACKUP_DIR = os.path.join(ROOT, "_extra_files", "backups")
CANDIDATE = os.path.join(ROOT, "_extra_files", "transforms", "globals_shadow_candidate.css")

SHADOW_DECL_RE = re.compile(r"((?:box-shadow|text-shadow)\s*:\s*)([^;}{\n]+)", re.I)
RING_RE = re.compile(r"(?:^|[\s,(])0\s+0\s+0\s+\d+px")
RING_INSET_RE = re.compile(r"inset\s+0\s+0\s+0\s+\d+px")
PX_LEN_RE = re.compile(r"(-?\d+(?:\.\d+)?)px")
TOKEN_RE = re.compile(r"^var\(--zozi-(elevation|ring)")


def shadow_token_for(value):
    v = value.strip()
    if v == "none":
        return None  # signal removal
    if TOKEN_RE.match(v):
        return v
    # Focus ring: outset or inset `0 0 0 Npx`
    if RING_RE.search(v) or RING_INSET_RE.search(v):
        return "var(--zozi-ring)"
    # Bucket ambient elevation by the largest px length in the declaration.
    lens = [abs(float(x)) for x in PX_LEN_RE.findall(v)]
    mx = max(lens) if lens else 0
    if mx <= 4:
        return "var(--zozi-elevation-sm)"
    if mx <= 14:
        return "var(--zozi-elevation-md)"
    return "var(--zozi-elevation-lg)"


def transform(text):
    removed = [0]

    def repl(m):
        prefix = m.group(1)
        raw = m.group(2).strip()
        important = ""
        if raw.endswith("!important"):
            important = " !important"
            raw = raw[: -len("!important")].strip()
        tok = shadow_token_for(raw)
        if tok is None:
            removed[0] += 1
            return ""  # remove the whole `box-shadow: none;` declaration
        return prefix + tok + important

    return SHADOW_DECL_RE.sub(repl, text), removed[0]


def main():
    if not os.path.isfile(SRC):
        print("ERROR: globals.css not found")
        sys.exit(2)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    bak = os.path.join(BACKUP_DIR, f"globals_shadow_pre_{ts}.css")
    shutil.copy2(SRC, bak)
    print("Backup written:", bak)

    with open(SRC, "r", encoding="utf-8") as f:
        original = f.read()

    candidate, removed = transform(original)
    if len(candidate) < 0.5 * len(original):
        print("ERROR: candidate suspiciously small; aborting (original untouched).")
        sys.exit(3)

    os.makedirs(os.path.dirname(CANDIDATE), exist_ok=True)
    with open(CANDIDATE, "w", encoding="utf-8") as f:
        f.write(candidate)
    print("Candidate written:", CANDIDATE, "| removed 'none' decls:", removed)

    vals = set()
    for m in SHADOW_DECL_RE.finditer(candidate):
        vals.add(re.sub(r"\s+", " ", m.group(2).strip()))
    print("Distinct shadow values in candidate:", len(vals))
    for v in sorted(vals):
        print("   ", v)


if __name__ == "__main__":
    main()
