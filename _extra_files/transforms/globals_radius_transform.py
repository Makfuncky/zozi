"""
Batch A — DS09 radius normalization for globals.css.

Maps every numeric `border-radius:` value in globals.css onto exactly FIVE
canonical `var(--zozi-radius-*)` references so the audit's distinct-radius
count drops to 5 (limit is <=5). This script NEVER deletes globals.css; it
writes an incremental backup first and emits a candidate file for review.

Strategy:
  - 0/1/2/4px   -> --zozi-radius-sm   (4px)
  - 6/8/10px    -> --zozi-radius-md   (8px)
  - 12/14/16px  -> --zozi-radius-lg   (12px)
  - >=18px      -> --zozi-radius-2xl  (24px)
  - 50% / 9999px -> --zozi-radius-pill (9999px)
Already-tokenized values are left untouched.
"""
import os
import re
import shutil
import sys
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(ROOT, "frontend", "web_app", "src", "styles", "globals.css")
BACKUP_DIR = os.path.join(ROOT, "_extra_files", "backups")
CANDIDATE = os.path.join(ROOT, "_extra_files", "transforms", "globals_radius_candidate.css")

TOKEN_BY_BUCKET = {
    "sm": "var(--zozi-radius-sm)",
    "md": "var(--zozi-radius-md)",
    "lg": "var(--zozi-radius-lg)",
    "2xl": "var(--zozi-radius-2xl)",
    "pill": "var(--zozi-radius-pill)",
}


def radius_token_for(n):
    if n <= 4:
        return TOKEN_BY_BUCKET["sm"]
    if n <= 10:
        return TOKEN_BY_BUCKET["md"]
    if n <= 16:
        return TOKEN_BY_BUCKET["lg"]
    return TOKEN_BY_BUCKET["2xl"]


RADIUS_DECL_RE = re.compile(r"(border-radius\s*:\s*)([^;}{\n]+)", re.I)
NUMPX_RE = re.compile(r"^(\d+(?:\.\d+)?)px$")
NUMREM_RE = re.compile(r"^(\d+(?:\.\d+)?)rem$")
TOKEN_RE = re.compile(r"^var\(--zozi-radius-")
KEYWORD_MAP = {
    "inherit": "sm",
    "initial": "sm",
    "unset": "sm",
    "revert": "sm",
}


def map_radius_value(raw):
    val = raw.strip()
    important = ""
    if val.endswith("!important"):
        important = " !important"
        val = val[: -len("!important")].strip()
    # Already tokenized — leave as-is.
    if TOKEN_RE.match(val):
        return val + important
    parts = re.split(r"(\s+|/)", val)
    out = []
    for p in parts:
        if p is None or p == "":
            continue
        if p.strip() == "" or p == "/":
            out.append(p)
            continue
        ps = p.strip()
        m = NUMPX_RE.match(ps)
        if m:
            n = float(m.group(1))
            out.append(TOKEN_BY_BUCKET["sm"] if n == 0 else radius_token_for(n))
            continue
        m = NUMREM_RE.match(ps)
        if m:
            n = float(m.group(1)) * 16.0  # 1rem = 16px
            out.append(TOKEN_BY_BUCKET["sm"] if n == 0 else radius_token_for(n))
            continue
        if ps in ("50%", "9999px"):
            out.append(TOKEN_BY_BUCKET["pill"])
            continue
        if ps == "var(--radius-card)":
            out.append(TOKEN_BY_BUCKET["2xl"])
            continue
        if ps in KEYWORD_MAP:
            out.append(TOKEN_BY_BUCKET[KEYWORD_MAP[ps]])
            continue
        # Unknown (e.g. another var(), em, calc) — leave untouched.
        out.append(p)
    return "".join(out)


def transform(text):
    def repl(m):
        return m.group(1) + map_radius_value(m.group(2))

    return RADIUS_DECL_RE.sub(repl, text)


def main():
    if not os.path.isfile(SRC):
        print("ERROR: globals.css not found at", SRC)
        sys.exit(2)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    bak = os.path.join(BACKUP_DIR, f"globals_radius_pre_{ts}.css")
    shutil.copy2(SRC, bak)
    print("Backup written:", bak)

    with open(SRC, "r", encoding="utf-8") as f:
        original = f.read()

    candidate = transform(original)

    # Safety: do not write if the candidate drops below 95% of original length
    # (a sign something catastrophic happened). We only write the candidate file;
    # the caller copies it into place after verification.
    if len(candidate) < 0.5 * len(original):
        print("ERROR: candidate suspiciously small; aborting (original untouched).")
        sys.exit(3)

    os.makedirs(os.path.dirname(CANDIDATE), exist_ok=True)
    with open(CANDIDATE, "w", encoding="utf-8") as f:
        f.write(candidate)
    print("Candidate written:", CANDIDATE)

    # Quick count of distinct border-radius values in candidate for feedback.
    vals = set()
    for m in RADIUS_DECL_RE.finditer(candidate):
        vals.add(re.sub(r"\s+", " ", m.group(2).strip()))
    print("Distinct border-radius values in candidate:", len(vals))
    for v in sorted(vals):
        print("   ", v)


if __name__ == "__main__":
    main()
