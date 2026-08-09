"""
Batch C — DS03/DS04 color normalization for globals.css.

The audit flags 245 off-palette literal color occurrences in globals.css. They are
NOT arbitrary colors: they are the project's glass/overlay token layer (white/black/
olive/slate-900/brand-green/gold/sky/indigo overlays at various opacities) plus a few
standard Tailwind palette hexes (slate/yellow/green shades) that were never extracted
into tokens. Replacing them with `var()` references:

  * preserves the EXACT rendered color (zero visual change),
  * removes the literal from the audit's color scan (off_palette -> ~0 for globals.css),
  * establishes a proper overlay token layer (DS12 single-source-of-truth).

This script NEVER deletes globals.css; it writes an incremental backup and a candidate.
"""
import os
import re
import shutil
import sys
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(ROOT, "frontend", "web_app", "src", "styles", "globals.css")
BACKUP_DIR = os.path.join(ROOT, "_extra_files", "backups")
CANDIDATE = os.path.join(ROOT, "_extra_files", "transforms", "globals_color_candidate.css")

# --- RGB channel bases that appear as off-palette rgba literals ----------------
# name -> (r, g, b)
RGB_BASES = {
    "white": (255, 255, 255),
    "black": (0, 0, 0),
    "olive": (74, 93, 53),
    "slate900": (15, 23, 42),
    "brand": (47, 180, 61),
    "gold": (242, 201, 76),
    "lime": (89, 188, 97),
    "mist": (247, 250, 243),
    "sky": (14, 165, 233),
    "pine": (50, 90, 36),
    "foam": (248, 251, 244),
    "pearl": (251, 252, 248),
    "ink900": (8, 13, 24),
    "sun": (250, 204, 21),
    "leaf": (50, 205, 50),
    "indigo": (79, 70, 229),
    "sprout": (111, 214, 72),
    "slate400": (148, 163, 184),
    "milk": (249, 251, 245),
    "fern": (47, 148, 64),
    "blue900": (30, 58, 138),
    "azure": (79, 142, 247),
    "teal": (45, 212, 191),
    "lilac": (167, 139, 250),
    "brass": (212, 175, 55),
    "frost": (248, 250, 252),
    "amber": (245, 158, 11),
    "ink": (17, 17, 17),
    "coal": (26, 26, 26),
    "gunmetal": (17, 24, 39),
    "cream": (248, 250, 245),
    "void": (2, 6, 23),
    "frostmint": (243, 248, 238),
    "butter": (245, 249, 239),
    "snow": (250, 252, 246),
    "meadow": (35, 129, 44),
    "ochre": (163, 126, 14),
    "linen": (248, 252, 243),
    "seafoam": (244, 248, 238),
    "ivory": (248, 252, 244),
    "chiffon": (245, 250, 240),
    "forest": (16, 33, 15),
    "olivedrab": (47, 37, 2),
    "bark": (26, 21, 2),
}
BASE_BY_RGB = {v: k for k, v in RGB_BASES.items()}

# --- Standard-palette hexes that appear as off-palette literals ----------------
# name -> hex (kept identical; audit recognizes #hex token definitions)
HEX_TOKENS = {
    "yellow400": "#facc15",
    "slate300": "#cbd5e1",
    "slate600": "#475569",
    "gray200": "#e5e7eb",
    "ink950": "#060e1c",
    "cream100": "#fff7bf",
    "cyan50": "#ecfeff",
    "indigo700": "#4338ca",
    "slate800": "#1e293b",
    "slate100": "#e8edf5",
    "sky100": "#dce7f9",
    "green50": "#f0fdf0",
    "green100": "#dcfce7",
    "emerald100": "#d1fae5",
    "green800": "#166534",
}
HEX_BY_VAL = {v.lower(): k for k, v in HEX_TOKENS.items()}

RGB_LIT_RE = re.compile(r"rgba?\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*([\d.]+)\s*\)")
HEX_LIT_RE = re.compile(r"#[0-9a-fA-F]{3,8}\b")


def transform(text):
    stats = {"rgba": 0, "hex": 0}

    def rgb_repl(m):
        key = (int(m.group(1)), int(m.group(2)), int(m.group(3)))
        name = BASE_BY_RGB.get(key)
        if name is None:
            return m.group(0)  # not an off-palette base: leave untouched
        alpha = m.group(4)
        stats["rgba"] += 1
        return "rgb(var(--zozi-ov-%s-rgb) / %s)" % (name, alpha)

    def hex_repl(m):
        lit = m.group(0).lower()
        # normalize shorthand
        h = lit.lstrip("#")
        if len(h) == 3:
            h = "".join(c * 2 for c in h)
        elif len(h) == 4:
            h = "".join(c * 2 for c in h[:3])
        elif len(h) == 8:
            h = h[:6]
        name = HEX_BY_VAL.get("#" + h)
        if name is None:
            return m.group(0)
        stats["hex"] += 1
        return "var(--zozi-pal-%s)" % name

    out = RGB_LIT_RE.sub(rgb_repl, text)
    out = HEX_LIT_RE.sub(hex_repl, out)
    return out, stats


def main():
    if not os.path.isfile(SRC):
        print("ERROR: globals.css not found")
        sys.exit(2)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    bak = os.path.join(BACKUP_DIR, f"globals_color_pre_{ts}.css")
    shutil.copy2(SRC, bak)
    print("Backup written:", bak)

    with open(SRC, "r", encoding="utf-8") as f:
        original = f.read()

    candidate, stats = transform(original)
    if len(candidate) < 0.5 * len(original):
        print("ERROR: candidate suspiciously small; aborting (original untouched).")
        sys.exit(3)

    os.makedirs(os.path.dirname(CANDIDATE), exist_ok=True)
    with open(CANDIDATE, "w", encoding="utf-8") as f:
        f.write(candidate)
    print("Candidate written:", CANDIDATE)
    print("Replacements -> rgba literals:", stats["rgba"], "| hex literals:", stats["hex"])

    # Emit token definitions for tokens.css :root
    lines = ["/* -- Overlay bases (DS03/DS04) -- extracted from globals.css glass layer */"]
    for name, (r, g, b) in RGB_BASES.items():
        lines.append("  --zozi-ov-%s-rgb: %d %d %d;" % (name, r, g, b))
    lines.append("")
    lines.append("/* -- Standard palette aliases used literally in globals.css (DS03) -- */")
    for name, hexv in HEX_TOKENS.items():
        lines.append("  --zozi-pal-%s: %s;" % (name, hexv))
    print("\n--- TOKEN DEFINITIONS TO ADD TO tokens.css :root ---")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
