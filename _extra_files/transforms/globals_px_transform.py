"""
Batch D — DS08 raw-px normalization for globals.css.

Most small/medium px values in globals.css exactly match the Tailwind spacing
scale (4, 8, 12, 16, 20, 24, ... px). Routing them through --zozi-space-* tokens:

  * keeps the EXACT rendered size (px -> var with same px value),
  * removes the raw px literal from the audit scan (total_px drops),
  * builds a spacing token layer (DS12).

We NEVER touch:
  * @media breakpoint widths (e.g. min-width: 1024px),
  * calc()/clamp()/min()/max()/var()/url() expressions,
  * font-size / line-height (DS07 owns typography),
  * large one-off layout dimensions (> 64px) and non-scale values.

This script NEVER deletes globals.css; it writes a backup and a candidate.
"""
import os
import re
import shutil
import sys
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(ROOT, "frontend", "web_app", "src", "styles", "globals.css")
BACKUP_DIR = os.path.join(ROOT, "_extra_files", "backups")
CANDIDATE = os.path.join(ROOT, "_extra_files", "transforms", "globals_px_candidate.css")

# px value -> token name (Tailwind-aligned spacing scale, 1..64px)
PX_TO_TOKEN = {
    1: "px", 2: "050", 3: "075", 4: "1", 6: "150", 8: "2", 10: "250",
    12: "3", 14: "350", 16: "4", 18: "450", 20: "5", 22: "550", 24: "6",
    26: "650", 28: "7", 30: "750", 32: "8", 34: "850", 36: "9", 38: "950",
    40: "10", 44: "11", 48: "12", 52: "13", 56: "14", 60: "15", 64: "16",
}

# properties whose px we leave alone (typography + anything we don't own here)
EXCLUDE_PROPS = {
    "font-size", "line-height", "font", "font-weight", "font-family",
    "font-stretch", "font-variant", "letter-spacing",  # keep tracking as-is
    "z-index", "opacity", "flex", "flex-grow", "flex-shrink",
    "order", "zoom", "stroke-dasharray", "stroke-dashoffset",
}

DECL_RE = re.compile(r"([\w-]+)\s*:\s*([^;}{\n]+)")
PX_RE = re.compile(r"(?<![\w.])(\d+(?:\.\d+)?)px\b")
SKIP_LINE = re.compile(r"@media|calc\(|clamp\(|min\(|max\(|var\(|url\(")

stats = {"replaced": 0, "skipped_decl": 0}


def transform(text):
    out_lines = []
    for line in text.splitlines():
        if SKIP_LINE.search(line):
            out_lines.append(line)
            continue
        changed = False

        def decl_repl(m):
            prop = m.group(1).lower()
            val = m.group(2)
            if prop in EXCLUDE_PROPS:
                return m.group(0)
            important = ""
            v = val.strip()
            if v.endswith("!important"):
                important = " !important"
                v = v[: -len("!important")].strip()
            if re.search(r"calc\(|clamp\(|min\(|max\(|var\(|url\(|%|vw|vh|em|rem", v):
                return m.group(0)

            def px_repl(pm):
                n = float(pm.group(1))
                if n != int(n):
                    return pm.group(0)
                tok = PX_TO_TOKEN.get(int(n))
                if tok is None:
                    return pm.group(0)
                stats["replaced"] += 1
                return "var(--zozi-space-%s)" % tok

            newval = PX_RE.sub(px_repl, v)
            if newval != v:
                return "%s: %s%s" % (m.group(1), newval, important)
            return m.group(0)

        newline = DECL_RE.sub(decl_repl, line)
        out_lines.append(newline)
    return "\n".join(out_lines) + ("\n" if text.endswith("\n") else "")


def main():
    if not os.path.isfile(SRC):
        print("ERROR: globals.css not found")
        sys.exit(2)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    bak = os.path.join(BACKUP_DIR, f"globals_px_pre_{ts}.css")
    shutil.copy2(SRC, bak)
    print("Backup written:", bak)

    with open(SRC, "r", encoding="utf-8") as f:
        original = f.read()

    candidate = transform(original)
    if len(candidate) < 0.5 * len(original):
        print("ERROR: candidate suspiciously small; aborting.")
        sys.exit(3)

    os.makedirs(os.path.dirname(CANDIDATE), exist_ok=True)
    with open(CANDIDATE, "w", encoding="utf-8") as f:
        f.write(candidate)
    print("Candidate written:", CANDIDATE)
    print("px literals replaced:", stats["replaced"])

    lines = ["/* -- Spacing scale (DS08) -- Tailwind-aligned; px kept identical */"]
    for px, name in sorted(PX_TO_TOKEN.items()):
        lines.append("  --zozi-space-%s: %dpx;" % (name, px))
    print("\n--- TOKEN DEFINITIONS TO ADD TO tokens.css :root ---")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
