#!/usr/bin/env python3
"""
design_audit.py — ZOZI Design System Governance Auditor (frontend).

Purpose:
  Read-only design-system auditor for the ZOZI frontend
  (web_app · mobile_app · shared).

It detects, FILE BY FILE:
  1.  Hardcoded CSS: inline style={{...}} objects, <style> tags in components,
      CSS-in-JS mixing, !important, raw px values, magic z-index.
  2.  Color theme drift: raw hex/rgb/hsl literals, off-palette colors,
      near-duplicate color clusters (#1A1A1A vs #191919 vs #1a1a2a),
      web-vs-mobile palette mismatches.
  3.  Typography: hardcoded font sizes / families / weights.
  4.  Spacing & shape: hardcoded dimensions, inconsistent border-radius,
      inconsistent shadows.
  5.  Tailwind discipline: arbitrary values that bypass tokens
      (bg-[#ff0000], w-[123px], z-[9999], rounded-[7px]).
  6.  Motion: inconsistent transition/animation durations.
  7.  Breakpoints: media queries not matching the Tailwind screen scale.
  8.  Accessibility-adjacent: low-contrast fg/bg pairs in the same style block.
  9.  Token system health: palette discovery (tailwind.config + CSS variables +
      shared token files), token coverage %, unused tokens.
 10.  Per-file DESIGN DEBT SCORE + top-offender ranking.

Design:
  * READ-ONLY. Does NOT import application code. Pure static analysis.
  * Self-contained: no YAML required.
  * Palette sources (tailwind.config.*, colors.ts, theme.ts, *.css variables)
    are scanned for tokens but exempt from violations.

Severity:
  [RED] VIOLATION   design-system breakage (style tags, !important, z>=1000,
                    no token source, unreadable contrast)
  [YEL] ADVISORY    drift / inconsistency / token bypass
  [GRN] INFO        palette inventory / coverage / healthy signal

Output:
  * stdout scorecard + hotlist + top offenders + color drift clusters
  * <repo>/DESIGN_AUDIT_REPORT.md  (gitignore it)
  * optional --json / --trend-file

Usage:
  python scripts/design_audit.py --no-fail
  python scripts/design_audit.py --ci
  python scripts/design_audit.py --json out/governance/design_audit.json
  python scripts/design_audit.py --trend-file .governance/design_trend.json --update-trend

Exit:
  1 if RED findings exist, unless --no-fail is passed.
"""

from __future__ import annotations

import argparse
import datetime
import json
import re
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

# ============================================================================
# 1. CONSTANTS
# ============================================================================

RED, YEL, GRN = "VIOLATION", "ADVISORY", "INFO"

SEV_ICON = {RED: "🔴", YEL: "🟡", GRN: "🟢"}

IGNORE_DIRS = {
    ".git", "node_modules", ".venv", "venv", "__pycache__", ".mypy_cache",
    ".pytest_cache", ".ruff_cache", ".tox", "htmlcov", ".next", ".expo",
    ".kotlin", "gradle", "android", "ios", ".idea", ".vscode",
    "test-results", ".playwright-artifacts-0", "playwright-out",
    "playwright-report", "static-tmp", ".web-build-test", "artifacts",
    "uploads", ".turbo", "dist", "build", "coverage", "test-output", "tmp",
    "e2e", "__tests__", ".web", "web-dist",
}

SOURCE_EXT = {".ts", ".tsx", ".js", ".jsx", ".cjs", ".mjs"}
CSS_EXT = {".css", ".scss"}
MAX_READ_BYTES = 2_000_000

# Files that DEFINE the palette — scanned for tokens, exempt from violations.
PALETTE_FILE_RE = re.compile(r"(^|[/\\])(colors|tokens|theme|palette)\.(ts|tsx|js|jsx)$", re.I)
CONFIG_FILE_RE = re.compile(
    r"(tailwind|postcss|metro|babel|next|eslint|jest|playwright|sentry)\.config\.", re.I
)

# --- color literal extraction ------------------------------------------------
HEX_RE = re.compile(r"#(?:[0-9a-fA-F]{8}|[0-9a-fA-F]{6}|[0-9a-fA-F]{3,4})\b")
RGB_RE = re.compile(r"rgba?\(\s*[\d.]+[,\s]+[\d.]+[,\s]+[\d.]+(?:[,\s]+[\d.]+)?\s*\)", re.I)
HSL_RE = re.compile(r"hsla?\(\s*[\d.]+[^\)]*\)", re.I)

TAILWIND_COLOR_RE = re.compile(r"([\w$-]+)\s*:\s*['\"](#[0-9a-fA-F]{3,8})['\"]")
CSS_VAR_RE = re.compile(
    r"(--[\w-]+)\s*:\s*(#[0-9a-fA-F]{3,8}|rgba?\([^\)]+\)|hsla?\([^\)]+\))", re.I
)

# --- hardcoded CSS signals ---------------------------------------------------
STYLE_OBJ_RE = re.compile(r"style\s*=\s*\{\{")
STYLE_ARR_RE = re.compile(r"style\s*=\s*\{\[[^\]]{0,200}?\{")   # RN: style={[s.x, {...}]}
STYLE_TAG_RE = re.compile(r"<style[\s>/]", re.I)
IMPORTANT_RE = re.compile(r"!\s*important", re.I)
STYLE_PROP_RE = re.compile(r"([A-Za-z]\w*)\s*:\s*(?:'([^']*)'|\"([^\"]*)\"|([\d.]+))")
ZINDEX_CSS_RE = re.compile(r"z-index\s*:\s*(\d+)", re.I)
SHADOW_CSS_RE = re.compile(r"(?:box-shadow|text-shadow)\s*:\s*([^;}{]+)", re.I)
RADIUS_CSS_RE = re.compile(r"border-radius\s*:\s*([^;}{]+)", re.I)
FONTSIZE_CSS_RE = re.compile(r"font-size\s*:\s*([^;}{]+)", re.I)
FONTFAM_CSS_RE = re.compile(r"font-family\s*:\s*([^;}{]+)", re.I)
MQ_RE = re.compile(r"@media[^{]*\(\s*(?:min|max)-width\s*:\s*(\d+)px", re.I)
MS_RE = re.compile(r"(?<![\w.])(\d+(?:\.\d+)?)ms\b")
PX_RE = re.compile(r"(?<![\w.])(\d+(?:\.\d+)?)px\b")
CSS_IN_JS_RE = re.compile(r"from\s+['\"](?:styled-components|@emotion/styled|@emotion/react)['\"]")
APPLY_RE = re.compile(r"@apply\b")

# Tailwind arbitrary values: the token-bypass vector.
ARB_RE = re.compile(
    r"(?<![\w-])"
    r"(bg|text|border|from|to|via|ring|decoration|placeholder|fill|stroke|outline|divide"
    r"|w|h|size|p|px|py|pt|pb|pl|pr|m|mx|my|mt|mb|ml|mr|gap|rounded|z|shadow"
    r"|top|left|right|bottom|inset|leading|tracking|space-x|space-y|min-w|max-w|min-h|max-h|basis)"
    r"-\[([^\]]+)\]"
)
ARB_COLOR_PREFIXES = {
    "bg", "text", "border", "from", "to", "via", "ring", "decoration",
    "placeholder", "fill", "stroke", "outline", "divide",
}

TAILWIND_SCREENS = {320, 375, 425, 640, 768, 820, 1024, 1280, 1440, 1536, 1920, 2560}

NAMED_COLORS = {
    "white": "#ffffff", "black": "#000000", "red": "#ff0000", "green": "#008000",
    "blue": "#0000ff", "gray": "#808080", "grey": "#808080", "orange": "#ffa500",
    "purple": "#800080", "yellow": "#ffff00", "pink": "#ffc0cb", "teal": "#008080",
    "cyan": "#00ffff", "magenta": "#ff00ff", "brown": "#a52a2a", "silver": "#c0c0c0",
    "gold": "#ffd700", "navy": "#000080", "maroon": "#800000", "olive": "#808000",
    "lime": "#00ff00", "aqua": "#00ffff", "fuchsia": "#ff00ff", "indigo": "#4b0082",
    "violet": "#ee82ee", "coral": "#ff7f50", "salmon": "#fa8072", "khaki": "#f0e68c",
    "plum": "#dda0dd", "turquoise": "#40e0d0", "tomato": "#ff6347",
    "crimson": "#dc143c", "lavender": "#e6e6fa", "beige": "#f5f5dc",
    "ivory": "#fffff0", "tan": "#d2b48c", "chocolate": "#d2691e",
    "darkblue": "#00008b", "darkgreen": "#006400", "darkred": "#8b0000",
    "lightgray": "#d3d3d3", "lightgrey": "#d3d3d3", "darkgray": "#a9a9a9",
    "darkgrey": "#a9a9a9", "lightblue": "#add8e6", "whitesmoke": "#f5f5f5",
    "aliceblue": "#f0f8ff", "transparent": None, "inherit": None, "currentcolor": None,
}

COLOR_PROPS = {
    "color", "backgroundColor", "borderColor", "borderTopColor", "borderBottomColor",
    "borderLeftColor", "borderRightColor", "tintColor", "background", "fill", "stroke",
}
SPACING_PROPS = {
    "padding", "paddingTop", "paddingBottom", "paddingLeft", "paddingRight",
    "paddingHorizontal", "paddingVertical", "margin", "marginTop", "marginBottom",
    "marginLeft", "marginRight", "marginHorizontal", "marginVertical",
    "width", "height", "top", "left", "right", "bottom", "gap", "rowGap",
    "columnGap", "borderWidth", "borderRadius", "fontSize", "lineHeight",
    "minWidth", "maxWidth", "minHeight", "maxHeight", "flexBasis",
}

NEAR_DUPLICATE_THRESHOLD = 14.0   # redmean color distance
NEAR_TOKEN_THRESHOLD = 10.0

RULE_MEANING = {
    "DS01": "hardcoded CSS: inline style={{...}} object in component",
    "DS02": "hardcoded CSS: <style> tag inside a component file",
    "DS03": "raw/off-palette color literal (bypasses design tokens)",
    "DS04": "color theme drift: near-duplicate colors used as if different",
    "DS05": "Tailwind arbitrary value bypassing tokens (bg-[#...], w-[123px]...)",
    "DS06": "!important usage (specificity war)",
    "DS07": "hardcoded typography (font size / family literal)",
    "DS08": "hardcoded spacing/dimension (raw px)",
    "DS09": "inconsistent border-radius values",
    "DS10": "magic z-index (>=1000)",
    "DS11": "inconsistent box-shadow values",
    "DS12": "design token source missing or weak",
    "DS13": "cross-workspace palette mismatch (web vs mobile differ)",
    "DS14": "mixed styling systems (CSS-in-JS alongside Tailwind)",
    "DS15": "low-contrast foreground/background pair",
    "DS16": "inconsistent motion durations (transition/animation)",
    "DS17": "unused design tokens",
    "DS18": "media-query breakpoint outside the screen scale",
    "DSI1": "palette / token inventory",
    "DSI2": "token coverage",
    "DSI3": "design debt ranking",
    "DST1": "design audit trend delta",
}

HOTLIST_RULES = {
    "DS02", "DS03", "DS04", "DS05", "DS06", "DS10", "DS12", "DS13", "DS15",
}

# ============================================================================
# 2. DATA MODEL
# ============================================================================


@dataclass
class Finding:
    sev: str
    code: str
    domain: str
    path: str
    message: str
    intended: str = ""
    line: int | None = None

    def loc(self) -> str:
        return f"{self.path}:{self.line}" if self.line else self.path


@dataclass
class Report:
    findings: list[Finding] = field(default_factory=list)
    counters: dict[str, int] = field(default_factory=lambda: defaultdict(int))

    def add(self, sev, code, domain, path, message, intended="", line=None) -> None:
        self.findings.append(Finding(sev, code, domain, path, message, intended, line))
        self.counters[code] += 1


@dataclass
class FileDesignProfile:
    path: str
    workspace: str
    kind: str                      # "component" | "css"
    colors: dict = field(default_factory=lambda: defaultdict(int))   # hex -> count
    off_palette: dict = field(default_factory=lambda: defaultdict(int))
    inline_style_blocks: int = 0
    style_tag: int = 0
    important: int = 0
    arb_color: dict = field(default_factory=lambda: defaultdict(int))
    arb_size: int = 0
    arb_z: list = field(default_factory=list)
    arb_radius: list = field(default_factory=list)
    px_values: int = 0
    zmagic: list = field(default_factory=list)
    shadows: set = field(default_factory=set)
    radii: set = field(default_factory=set)
    font_sizes: set = field(default_factory=set)
    font_families: set = field(default_factory=set)
    durations: set = field(default_factory=set)
    breakpoints_off: set = field(default_factory=set)
    contrast_pairs: list = field(default_factory=list)   # (ratio, fg, bg, line)
    css_in_js: int = 0
    apply_count: int = 0
    score: int = 0

    def issue_tags(self) -> str:
        tags = []
        if self.inline_style_blocks:
            tags.append(f"inline×{self.inline_style_blocks}")
        if self.style_tag:
            tags.append("style-tag")
        if self.off_palette:
            tags.append(f"off-color×{sum(self.off_palette.values())}")
        if self.arb_color:
            tags.append(f"tw-arb-color×{sum(self.arb_color.values())}")
        if self.arb_size:
            tags.append(f"tw-arb-size×{self.arb_size}")
        if self.important:
            tags.append(f"!important×{self.important}")
        if self.zmagic or self.arb_z:
            tags.append("z-magic")
        if self.px_values:
            tags.append(f"px×{self.px_values}")
        if self.contrast_pairs:
            tags.append(f"contrast×{len(self.contrast_pairs)}")
        if self.css_in_js:
            tags.append("css-in-js")
        return ", ".join(tags) if tags else "clean"


# ============================================================================
# 3. COLOR MATH
# ============================================================================


def hex_to_rgb(h: str):
    h = h.strip().lstrip("#").lower()
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    elif len(h) == 4:
        h = "".join(c * 2 for c in h[:3])
    elif len(h) == 8:
        h = h[:6]
    if len(h) != 6:
        return None
    try:
        return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))
    except ValueError:
        return None


def to_hex(rgb) -> str:
    return "#%02x%02x%02x" % tuple(int(c) for c in rgb)


def hsl_to_rgb(h: float, s: float, l: float):
    s /= 100.0
    l /= 100.0
    c = (1 - abs(2 * l - 1)) * s
    x = c * (1 - abs(((h / 60.0) % 2) - 1))
    m = l - c / 2
    if h < 60:
        r, g, b = c, x, 0
    elif h < 120:
        r, g, b = x, c, 0
    elif h < 180:
        r, g, b = 0, c, x
    elif h < 240:
        r, g, b = 0, x, c
    elif h < 300:
        r, g, b = x, 0, c
    else:
        r, g, b = c, 0, x
    return (int((r + m) * 255), int((g + m) * 255), int((b + m) * 255))


def parse_color_literal(lit: str):
    lit = lit.strip()
    low = lit.lower()
    if low.startswith("#"):
        return hex_to_rgb(low)
    m = re.match(r"rgba?\(\s*([\d.]+)[,\s]+([\d.]+)[,\s]+([\d.]+)", low)
    if m:
        try:
            return tuple(min(255, int(float(m.group(i)))) for i in (1, 2, 3))
        except ValueError:
            return None
    m = re.match(r"hsla?\(\s*([\d.]+)[,\s]+([\d.]+)[,\s]+([\d.]+)", low)
    if m:
        try:
            return hsl_to_rgb(float(m.group(1)), float(m.group(2)), float(m.group(3)))
        except ValueError:
            return None
    if low in NAMED_COLORS:
        v = NAMED_COLORS[low]
        return hex_to_rgb(v) if v else None
    return None


def color_distance(a, b) -> float:
    """Redmean approximation of perceptual distance (0..~765)."""
    rmean = (a[0] + b[0]) / 2.0
    dr, dg, db = a[0] - b[0], a[1] - b[1], a[2] - b[2]
    return (
        (2 + rmean / 256.0) * dr * dr
        + 4 * dg * dg
        + (2 + (255 - rmean) / 256.0) * db * db
    ) ** 0.5


def _chan(c: float) -> float:
    c /= 255.0
    return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4


def rel_luminance(rgb) -> float:
    return 0.2126 * _chan(rgb[0]) + 0.7152 * _chan(rgb[1]) + 0.0722 * _chan(rgb[2])


def contrast_ratio(a, b) -> float:
    la, lb = rel_luminance(a), rel_luminance(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def cluster_colors(hexes: list[str], threshold: float = NEAR_DUPLICATE_THRESHOLD):
    rgb_map = {h: hex_to_rgb(h) for h in hexes}
    clusters = []
    used = set()
    for h in hexes:
        if h in used or rgb_map[h] is None:
            continue
        cl = [h]
        used.add(h)
        for o in hexes:
            if o in used or rgb_map[o] is None:
                continue
            if color_distance(rgb_map[h], rgb_map[o]) <= threshold:
                cl.append(o)
                used.add(o)
        clusters.append(cl)
    return clusters


# ============================================================================
# 4. GENERIC HELPERS
# ============================================================================


def rel(p: Path, base: Path) -> str:
    try:
        return str(p.relative_to(base))
    except ValueError:
        return str(p)


def walk_dirs(root: Path, ignore_dirs: set):
    stack = [root]
    while stack:
        d = stack.pop()
        try:
            entries = list(d.iterdir())
        except (PermissionError, OSError):
            continue
        yield d, entries
        for e in entries:
            if e.is_dir() and e.name.lower() in ignore_dirs:
                continue
            if e.is_dir():
                stack.append(e)


def iter_frontend_files(frontend: Path, exts: set) -> Iterable[Path]:
    if not frontend.exists():
        return
    for d, entries in walk_dirs(frontend, IGNORE_DIRS):
        for e in entries:
            if e.is_file() and e.suffix.lower() in exts:
                try:
                    if e.stat().st_size <= MAX_READ_BYTES:
                        yield e
                except OSError:
                    pass


def read_text(p: Path) -> str | None:
    try:
        return p.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None


def workspace_of(f: Path, frontend: Path) -> str:
    try:
        parts = f.relative_to(frontend).parts
    except ValueError:
        return "frontend-root"
    if parts and parts[0] in ("web_app", "mobile_app", "shared"):
        return parts[0]
    return "frontend-root"


def is_palette_source(f: Path) -> bool:
    name = f.name
    if name.startswith("tailwind.config"):
        return True
    return bool(PALETTE_FILE_RE.search(str(f)))


def is_scan_exempt(f: Path) -> bool:
    if f.suffix.lower() == ".ts" and f.name.endswith(".d.ts"):
        return True
    if CONFIG_FILE_RE.search(f.name):
        return True
    if is_palette_source(f):
        return True
    if ".min." in f.name:
        return True
    return False


def _is_comment_line(line: str) -> bool:
    s = line.strip()
    return s.startswith("//") or s.startswith("*") or s.startswith("/*")


# ============================================================================
# 5. PALETTE DISCOVERY  (the "intended theme" — single source of truth)
# ============================================================================


def discover_palette(frontend: Path) -> dict:
    tokens: dict[str, str] = {}          # name -> hex
    value_index: dict[str, str] = {}     # hex  -> name
    sources: list[str] = []
    css_var_count = 0

    if not frontend.exists():
        return {"tokens": tokens, "value_index": value_index,
                "sources": sources, "css_var_count": css_var_count}

    for f in iter_frontend_files(frontend, SOURCE_EXT | CSS_EXT):
        text = read_text(f)
        if not text:
            continue

        name = f.name

        # Tailwind config colors
        if name.startswith("tailwind.config"):
            sources.append(rel(f, frontend.parent.parent))
            for m in TAILWIND_COLOR_RE.finditer(text):
                key, val = m.group(1), m.group(2)
                rgb = hex_to_rgb(val)
                if rgb is None:
                    continue
                hx = to_hex(rgb)
                tokens.setdefault(key, hx)
                value_index.setdefault(hx, key)

        # CSS custom properties
        elif f.suffix.lower() in CSS_EXT:
            for m in CSS_VAR_RE.finditer(text):
                var_name, raw = m.group(1), m.group(2)
                rgb = parse_color_literal(raw)
                if rgb is None:
                    continue
                hx = to_hex(rgb)
                tokens.setdefault(var_name, hx)
                value_index.setdefault(hx, var_name)
                css_var_count += 1

        # shared token/theme/palette files
        elif PALETTE_FILE_RE.search(str(f)):
            sources.append(rel(f, frontend.parent.parent))
            for m in TAILWIND_COLOR_RE.finditer(text):
                key, val = m.group(1), m.group(2)
                rgb = hex_to_rgb(val)
                if rgb is None:
                    continue
                hx = to_hex(rgb)
                tokens.setdefault(key, hx)
                value_index.setdefault(hx, key)

    return {"tokens": tokens, "value_index": value_index,
            "sources": sources, "css_var_count": css_var_count}


def make_classifier(palette: dict):
    """Return classify(hex_literal) -> 'token' | 'near-token' | 'off'."""
    value_index = palette["value_index"]
    pal_rgbs = []
    for hx in value_index:
        rgb = hex_to_rgb(hx)
        if rgb:
            pal_rgbs.append(rgb)

    cache: dict[str, str] = {}

    def classify(lit_hex: str) -> str:
        if lit_hex in cache:
            return cache[lit_hex]
        rgb = hex_to_rgb(lit_hex)
        if rgb is None:
            cache[lit_hex] = "off"
            return "off"
        if lit_hex in value_index:
            cache[lit_hex] = "token"
            return "token"
        best = 9999.0
        for pr in pal_rgbs:
            d = color_distance(rgb, pr)
            if d < best:
                best = d
            if best <= NEAR_TOKEN_THRESHOLD:
                break
        verdict = "near-token" if best <= NEAR_TOKEN_THRESHOLD else "off"
        cache[lit_hex] = verdict
        return verdict

    return classify


# ============================================================================
# 6. FILE SCANNERS
# ============================================================================


def extract_style_objects(text: str) -> list[tuple[int, str]]:
    """Best-effort extraction of style={{ ... }} object bodies."""
    out = []
    for m in STYLE_OBJ_RE.finditer(text):
        start = m.end() - 1          # position of the inner '{'
        depth = 0
        i = start
        while i < len(text):
            ch = text[i]
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    break
            i += 1
        out.append((m.start(), text[start + 1:i]))
    return out


def _add_color(profile: FileDesignProfile, raw: str, classify, line: int | None = None):
    rgb = parse_color_literal(raw)
    if rgb is None:
        return
    hx = to_hex(rgb)
    profile.colors[hx] += 1
    verdict = classify(hx)
    if verdict == "off":
        profile.off_palette[hx] += 1


def scan_component_file(f: Path, text: str, ws: str, repo: Path, classify) -> FileDesignProfile:
    p = FileDesignProfile(path=rel(f, repo), workspace=ws, kind="component")

    # ---- color literals across the file (hex / rgb / hsl) ----
    lines = text.splitlines()
    for rx in (HEX_RE, RGB_RE, HSL_RE):
        for m in rx.finditer(text):
            line_no = text.count("\n", 0, m.start()) + 1
            try:
                line = lines[line_no - 1]
            except IndexError:
                continue
            if _is_comment_line(line):
                continue
            _add_color(p, m.group(0), classify, line_no)

    # ---- inline style objects ----
    for _pos, body in extract_style_objects(text):
        p.inline_style_blocks += 1
        fg = None
        bg = None
        line_no = text.count("\n", 0, _pos) + 1

        for pm in STYLE_PROP_RE.finditer(body):
            prop = pm.group(1)
            val = pm.group(2) or pm.group(3) or pm.group(4) or ""
            if not val:
                continue

            if prop in COLOR_PROPS:
                _add_color(p, val, classify, line_no)
                rgb = parse_color_literal(val)
                if prop == "color":
                    fg = rgb
                elif prop in ("backgroundColor", "background"):
                    bg = rgb

            elif prop in SPACING_PROPS:
                if pm.group(4):               # bare number (React Native)
                    p.px_values += 1
                elif "px" in val:
                    p.px_values += 1

            if prop == "zIndex":
                try:
                    z = int(float(val))
                    if z >= 1000:
                        p.zmagic.append(z)
                except ValueError:
                    pass

            elif prop == "borderRadius":
                p.radii.add(val.strip())

            elif prop in ("boxShadow", "shadow"):
                p.shadows.add(re.sub(r"\s+", " ", val.strip()))

            elif prop == "fontSize":
                p.font_sizes.add(val.strip())

            elif prop == "fontFamily":
                p.font_families.add(val.strip().strip("'\""))

            elif prop in ("transition", "animation"):
                for dm in MS_RE.finditer(val):
                    p.durations.add(f"{dm.group(1)}ms")

        if fg and bg:
            ratio = contrast_ratio(fg, bg)
            if ratio < 3.2:
                p.contrast_pairs.append((round(ratio, 2), to_hex(fg), to_hex(bg), line_no))

    # RN inline overrides: style={[styles.x, {...}]}
    p.inline_style_blocks += len(STYLE_ARR_RE.findall(text))

    # ---- <style> tags ----
    p.style_tag = len(STYLE_TAG_RE.findall(text))

    # ---- CSS-in-JS mixing ----
    p.css_in_js = len(CSS_IN_JS_RE.findall(text))

    # ---- Tailwind arbitrary values ----
    for m in ARB_RE.finditer(text):
        prefix, val = m.group(1), m.group(2)
        line_no = text.count("\n", 0, m.start()) + 1
        try:
            if _is_comment_line(lines[line_no - 1]):
                continue
        except IndexError:
            pass

        is_color_val = val.startswith("#") or "rgb" in val.lower() or "hsl" in val.lower()

        if prefix in ARB_COLOR_PREFIXES and is_color_val:
            p.arb_color[val.lower()] += 1
            _add_color(p, val, classify, line_no)
        elif prefix == "z":
            p.arb_z.append(val)
            try:
                if int(val) >= 1000:
                    p.zmagic.append(int(val))
            except ValueError:
                pass
        elif prefix == "rounded":
            p.arb_radius.append(val)
            p.radii.add(val)
        elif prefix == "shadow":
            p.shadows.add(f"tw:{val}")
        else:
            if re.search(r"\d", val):
                p.arb_size += 1

    return p


def scan_css_file(f: Path, text: str, ws: str, repo: Path, classify) -> FileDesignProfile:
    p = FileDesignProfile(path=rel(f, repo), workspace=ws, kind="css")

    lines = text.splitlines()
    for rx in (HEX_RE, RGB_RE, HSL_RE):
        for m in rx.finditer(text):
            line_no = text.count("\n", 0, m.start()) + 1
            try:
                if _is_comment_line(lines[line_no - 1]):
                    continue
            except IndexError:
                pass
            _add_color(p, m.group(0), classify, line_no)

    p.important = len(IMPORTANT_RE.findall(text))
    p.px_values = len(PX_RE.findall(text))
    p.apply_count = len(APPLY_RE.findall(text))

    for m in ZINDEX_CSS_RE.finditer(text):
        z = int(m.group(1))
        if z >= 1000:
            p.zmagic.append(z)

    for m in SHADOW_CSS_RE.finditer(text):
        p.shadows.add(re.sub(r"\s+", " ", m.group(1).strip()))

    for m in RADIUS_CSS_RE.finditer(text):
        p.radii.add(re.sub(r"\s+", " ", m.group(1).strip()))

    for m in FONTSIZE_CSS_RE.finditer(text):
        p.font_sizes.add(m.group(1).strip())

    for m in FONTFAM_CSS_RE.finditer(text):
        p.font_families.add(m.group(1).strip())

    for m in MS_RE.finditer(text):
        p.durations.add(f"{m.group(1)}ms")

    for m in MQ_RE.finditer(text):
        bp = int(m.group(1))
        if bp not in TAILWIND_SCREENS:
            p.breakpoints_off.add(bp)

    return p


def compute_file_score(p: FileDesignProfile) -> int:
    s = 0
    s += p.inline_style_blocks * 3
    s += p.style_tag * 25
    s += p.important * 8
    s += sum(p.arb_color.values()) * 5
    s += p.arb_size * 1
    s += len(p.zmagic) * 20
    s += sum(p.off_palette.values()) * 4
    s += min(p.px_values, 60) * 1
    s += min(len(p.shadows), 10) * 2
    s += min(len(p.radii), 10) * 2
    s += min(len(p.font_sizes), 10) * 2
    s += min(len(p.durations), 10)
    s += len(p.breakpoints_off) * 3
    s += sum(1 for r, *_ in p.contrast_pairs if r < 2.0) * 20
    s += sum(1 for r, *_ in p.contrast_pairs if 2.0 <= r < 3.2) * 6
    s += p.css_in_js * 10
    return s


# ============================================================================
# 7. AGGREGATE CHECKS
# ============================================================================


def run_checks(repo: Path, rep: Report, profiles: list[FileDesignProfile],
               palette: dict, classify) -> dict:
    frontend = repo / "frontend"

    # ---- DS12: token source health ----
    token_count = len(palette["tokens"])
    if token_count == 0:
        rep.add(RED, "DS12", "design", rel(frontend, repo),
                "no design token source found (no tailwind theme colors, no CSS variables, no shared token file)",
                intended="create shared/src/tokens/colors.ts + tailwind.config theme.extend.colors; every color must come from a token")
    elif token_count < 5:
        rep.add(YEL, "DS12", "design", rel(frontend, repo),
                f"weak token source: only {token_count} color tokens discovered",
                intended="define the full brand palette (primary/secondary/neutral/semantic states) as tokens")

    # ---- global color aggregation ----
    literal_files: dict[str, set] = defaultdict(set)
    literal_usage: dict[str, int] = defaultdict(int)
    literal_ws: dict[str, set] = defaultdict(set)
    total_color_occurrences = 0
    on_palette_occurrences = 0

    for p in profiles:
        for hx, cnt in p.colors.items():
            literal_files[hx].add(p.path)
            literal_usage[hx] += cnt
            literal_ws[hx].add(p.workspace)
            total_color_occurrences += cnt
            if classify(hx) != "off":
                on_palette_occurrences += cnt

    coverage = (on_palette_occurrences / total_color_occurrences * 100) if total_color_occurrences else 100.0

    rep.add(GRN, "DSI2", "design", rel(frontend, repo),
            f"token coverage: {coverage:.1f}% of color occurrences match the palette "
            f"({on_palette_occurrences}/{total_color_occurrences}, {len(literal_usage)} distinct colors)")

    # ---- DS03: off-palette literals (worst offenders) ----
    off_literals = sorted(
        (hx for hx in literal_usage if classify(hx) == "off"),
        key=lambda hx: (-literal_usage[hx], hx),
    )
    for hx in off_literals[:30]:
        files = sorted(literal_files[hx])
        rep.add(YEL, "DS03", "design", files[0],
                f"off-palette color {hx} used {literal_usage[hx]}× in {len(files)} file(s): "
                + ", ".join(files[:4]) + (f" +{len(files) - 4} more" if len(files) > 4 else ""),
                intended="replace with the nearest design token, or add it to the palette with an ADR if it is a new brand color")

    # ---- DS04 / DS13: near-duplicate drift clusters ----
    distinct = sorted(literal_usage.keys())
    clusters = cluster_colors(distinct)
    drift_clusters = []
    for cl in clusters:
        if len(cl) < 2:
            continue
        total = sum(literal_usage[hx] for hx in cl)
        if total < 3:
            continue
        drift_clusters.append((cl, total))
    drift_clusters.sort(key=lambda x: -x[1])

    for cl, total in drift_clusters[:25]:
        ws_span = set()
        for hx in cl:
            ws_span |= literal_ws[hx]
        detail = " ≈ ".join(f"{hx} (×{literal_usage[hx]})" for hx in sorted(cl))
        cross = len(ws_span) > 1
        code = "DS13" if cross else "DS04"
        dom = "/".join(sorted(ws_span)) if cross else "design"
        sev = YEL
        intended = ("web and mobile disagree on this color — unify in shared tokens"
                    if cross else
                    "pick ONE token; these are visually the same color")
        rep.add(sev, code, dom, ", ".join(sorted(literal_files[cl[0]]))[:120],
                f"color drift ({total}× total): {detail}", intended=intended)

    # ---- DS01: inline style hotspots ----
    inline_files = sorted(
        (p for p in profiles if p.inline_style_blocks >= 3),
        key=lambda p: -p.inline_style_blocks,
    )
    for p in inline_files[:60]:
        rep.add(YEL, "DS01", p.workspace, p.path,
                f"{p.inline_style_blocks} inline style object(s) — hardcoded CSS inside the component",
                intended="move to Tailwind classes / StyleSheet.create / a shared component variant")

    # ---- DS02: <style> tags ----
    for p in (p for p in profiles if p.style_tag):
        rep.add(RED, "DS02", p.workspace, p.path,
                f"{p.style_tag} <style> tag(s) inside a component file",
                intended="delete; styles belong in the design system (Tailwind/global CSS), not in JSX")

    # ---- DS05: arbitrary Tailwind color values ----
    arb_files = sorted(
        (p for p in profiles if p.arb_color),
        key=lambda p: -sum(p.arb_color.values()),
    )
    for p in arb_files[:40]:
        worst = ", ".join(sorted(p.arb_color, key=lambda v: -p.arb_color[v])[:4])
        rep.add(YEL, "DS05", p.workspace, p.path,
                f"{sum(p.arb_color.values())} arbitrary Tailwind color value(s) bypass tokens: {worst}",
                intended="use palette classes (bg-primary, text-neutral-700...) instead of bg-[#...]")

    # ---- DS06: !important ----
    for p in sorted((p for p in profiles if p.important), key=lambda p: -p.important)[:20]:
        rep.add(RED, "DS06", p.workspace, p.path,
                f"!important used {p.important}× — specificity war",
                intended="fix selector specificity or component structure; never !important in a design system")

    # ---- DS07: typography ----
    all_font_sizes = set()
    fam_files: dict[str, set] = defaultdict(set)
    for p in profiles:
        all_font_sizes |= p.font_sizes
        for fam in p.font_families:
            fam_files[fam].add(p.path)
    if len(all_font_sizes) > 8:
        rep.add(YEL, "DS07", "design", rel(frontend, repo),
                f"{len(all_font_sizes)} distinct hardcoded font sizes: "
                + ", ".join(sorted(all_font_sizes)[:12]) + " ...",
                intended="collapse onto a type scale (text-xs/sm/base/lg/xl...); max ~8 steps")
    for fam, files in sorted(fam_files.items(), key=lambda kv: -len(kv[1]))[:8]:
        if len(fam_files) > 1:
            rep.add(YEL, "DS07", "design", sorted(files)[0],
                    f"font family literal '{fam}' hardcoded in {len(files)} file(s)",
                    intended="reference the font token from the theme; one brand family + one mono")

    # ---- DS08: px hotspots ----
    px_files = sorted((p for p in profiles if p.px_values >= 10), key=lambda p: -p.px_values)
    for p in px_files[:30]:
        rep.add(YEL, "DS08", p.workspace, p.path,
                f"{p.px_values} raw px value(s) — hardcoded spacing/sizing",
                intended="use the spacing scale (p-2/gap-4...) or RN spacing tokens")

    # ---- DS09: radius inconsistency ----
    all_radii = set()
    for p in profiles:
        all_radii |= p.radii
    if len(all_radii) > 5:
        rep.add(YEL, "DS09", "design", rel(frontend, repo),
                f"{len(all_radii)} distinct border-radius values: "
                + ", ".join(sorted(all_radii)[:10]),
                intended="standardize on 3-4 radii tokens (sm/md/lg/full)")

    # ---- DS10: magic z-index ----
    for p in sorted((p for p in profiles if p.zmagic), key=lambda p: -max(p.zmagic))[:15]:
        rep.add(RED, "DS10", p.workspace, p.path,
                f"magic z-index value(s): {', '.join(str(z) for z in sorted(set(p.zmagic))[:5])}",
                intended="use a z-index scale token (dropdown=100, modal=200, toast=300); never 9999+")

    # ---- DS11: shadow inconsistency ----
    all_shadows = set()
    for p in profiles:
        all_shadows |= p.shadows
    if len(all_shadows) > 4:
        rep.add(YEL, "DS11", "design", rel(frontend, repo),
                f"{len(all_shadows)} distinct shadow definitions — no elevation system",
                intended="define 3 elevation tokens (shadow-sm/md/lg) and reuse them")

    # ---- DS14: mixed styling systems ----
    for p in (p for p in profiles if p.css_in_js):
        rep.add(YEL, "DS14", p.workspace, p.path,
                "CSS-in-JS library imported alongside Tailwind — two styling systems",
                intended="pick ONE system (Tailwind); remove styled-components/emotion")

    # ---- DS15: low contrast ----
    reported = 0
    for p in profiles:
        for ratio, fg, bg, line_no in p.contrast_pairs:
            sev = RED if ratio < 2.0 else YEL
            rep.add(sev, "DS15", p.workspace, p.path,
                    f"low contrast {ratio}:1 — text {fg} on {bg}",
                    intended="WCAG minimum 4.5:1 for body text; fix the token pairing",
                    line=line_no)
            reported += 1
            if reported >= 25:
                break
        if reported >= 25:
            break

    # ---- DS16: motion inconsistency ----
    all_durations = set()
    for p in profiles:
        all_durations |= p.durations
    if len(all_durations) > 6:
        rep.add(YEL, "DS16", "design", rel(frontend, repo),
                f"{len(all_durations)} distinct animation durations: "
                + ", ".join(sorted(all_durations)[:10]),
                intended="standardize on 2-3 motion tokens (150ms/250ms/400ms)")

    # ---- DS18: rogue breakpoints ----
    all_bps = set()
    for p in profiles:
        all_bps |= p.breakpoints_off
    if all_bps:
        rep.add(YEL, "DS18", "design", rel(frontend, repo),
                f"media-query breakpoints outside the screen scale: "
                + ", ".join(f"{bp}px" for bp in sorted(all_bps)[:10]),
                intended="use the Tailwind screens (sm=640, md=768, lg=1024, xl=1280, 2xl=1536)")

    # ---- DS17: unused tokens ----
    if token_count:
        used_hexes = set(literal_usage.keys())
        all_text_hits = set()
        unused = []
        for name, hx in palette["tokens"].items():
            if hx in used_hexes:
                continue
            if len(name) >= 4 and any(name in (p.path or "") for p in profiles):
                continue
            unused.append(name)
        if unused:
            rep.add(YEL, "DS17", "design", ", ".join(palette["sources"][:2]) or "palette",
                    f"{len(unused)} palette token(s) never referenced: "
                    + ", ".join(sorted(unused)[:12]) + (" ..." if len(unused) > 12 else ""),
                    intended="remove dead tokens or use them; unused tokens rot the system")

    # ---- DSI1: palette inventory ----
    top_colors = sorted(literal_usage, key=lambda hx: -literal_usage[hx])[:10]
    inv = ", ".join(f"{hx}×{literal_usage[hx]}" for hx in top_colors)
    rep.add(GRN, "DSI1", "design", rel(frontend, repo),
            f"top colors in use: {inv}")

    return {
        "coverage": coverage,
        "total_color_occurrences": total_color_occurrences,
        "distinct_colors": len(literal_usage),
        "literal_usage": dict(literal_usage),
        "literal_files": {hx: sorted(fs) for hx, fs in literal_files.items()},
        "drift_clusters": [
            {"values": sorted(cl), "total": total} for cl, total in drift_clusters
        ],
        "classify": {hx: classify(hx) for hx in literal_usage},
    }


# ============================================================================
# 8. SCORE / SUMMARY / TREND
# ============================================================================


def compute_debt_score(rep: Report) -> int:
    red = sum(1 for f in rep.findings if f.sev == RED)
    yel = sum(1 for f in rep.findings if f.sev == YEL)
    by = rep.counters
    score = red * 100 + yel * 15
    score += by.get("DS01", 0) * 4
    score += by.get("DS02", 0) * 30
    score += by.get("DS03", 0) * 6
    score += by.get("DS04", 0) * 12
    score += by.get("DS05", 0) * 8
    score += by.get("DS06", 0) * 10
    score += by.get("DS07", 0) * 8
    score += by.get("DS08", 0) * 4
    score += by.get("DS09", 0) * 8
    score += by.get("DS10", 0) * 25
    score += by.get("DS11", 0) * 8
    score += by.get("DS12", 0) * 60
    score += by.get("DS13", 0) * 18
    score += by.get("DS14", 0) * 12
    score += by.get("DS15", 0) * 15
    score += by.get("DS16", 0) * 5
    score += by.get("DS17", 0) * 4
    score += by.get("DS18", 0) * 5
    return int(score)


def build_summary(repo, rep, profiles, palette, color_stats, debt_score) -> dict:
    n_red = sum(1 for f in rep.findings if f.sev == RED)
    n_yel = sum(1 for f in rep.findings if f.sev == YEL)
    n_grn = sum(1 for f in rep.findings if f.sev == GRN)

    ws_counts: dict[str, int] = defaultdict(int)
    for p in profiles:
        ws_counts[p.workspace] += 1

    offenders = sorted(profiles, key=lambda p: -p.score)

    return {
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "repo": str(repo),
        "red": n_red,
        "yellow": n_yel,
        "green": n_grn,
        "debt_score": debt_score,
        "by_code": dict(rep.counters),
        "files_scanned": len(profiles),
        "workspaces": dict(ws_counts),
        "palette_tokens": len(palette["tokens"]),
        "palette_sources": palette["sources"],
        "token_coverage_pct": round(color_stats["coverage"], 1),
        "distinct_colors": color_stats["distinct_colors"],
        "color_occurrences": color_stats["total_color_occurrences"],
        "top_offenders": [
            {"file": p.path, "workspace": p.workspace, "score": p.score,
             "issues": p.issue_tags()}
            for p in offenders[:25]
        ],
    }


def read_json(path: Path):
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else None
    except Exception:
        return None


def update_trend(path: Path, current: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(current, indent=2), encoding="utf-8")


def print_design_trend(rep: Report, current: dict, baseline: dict | None) -> None:
    if not baseline:
        print("\nNo design trend baseline found. Use --update-trend to create one.")
        return
    old_red = int(baseline.get("red", 0))
    new_red = int(current.get("red", 0))
    old_score = int(baseline.get("debt_score", 0))
    new_score = int(current.get("debt_score", 0))
    old_cov = float(baseline.get("token_coverage_pct", 0))
    new_cov = float(current.get("token_coverage_pct", 0))

    print("\n" + "=" * 78)
    print("  DESIGN TREND")
    print("=" * 78)
    print(f"  RED: {old_red} -> {new_red}    DEBT: {old_score} -> {new_score}")
    print(f"  TOKEN COVERAGE: {old_cov:.1f}% -> {new_cov:.1f}%")

    old_codes = baseline.get("by_code", {})
    new_codes = current.get("by_code", {})
    regs, imps = [], []
    for code in sorted(set(old_codes) | set(new_codes)):
        d = int(new_codes.get(code, 0)) - int(old_codes.get(code, 0))
        if d > 0:
            regs.append((code, d))
        elif d < 0:
            imps.append((code, d))
    if regs:
        print("\n  Regressions:  " + ", ".join(f"+{d} {c}" for c, d in regs))
    if imps:
        print("  Improvements: " + ", ".join(f"{d} {c}" for c, d in imps))

    rep.add(GRN, "DST1", "design", "trend",
            f"RED {old_red}->{new_red}, DEBT {old_score}->{new_score}, coverage {old_cov:.1f}%->{new_cov:.1f}%",
            intended="drive design debt down continuously")


# ============================================================================
# 9. RENDERING
# ============================================================================


def render_stdout(repo, rep, summary, profiles, color_stats) -> int:
    n_red, n_yel, n_grn = summary["red"], summary["yellow"], summary["green"]
    debt = summary["debt_score"]
    cov = summary["token_coverage_pct"]

    print("=" * 78)
    print("  ZOZI DESIGN SYSTEM GOVERNANCE AUDIT")
    print("  hardcoded CSS · color drift · typography · spacing · tokens · contrast")
    print("=" * 78)
    print(f"  repo: {repo}")
    print(f"  [RED] VIOLATIONS : {n_red}    [YEL] ADVISORIES : {n_yel}    [GRN] INFO : {n_grn}")
    print(f"  DESIGN DEBT SCORE: {debt}")
    print(f"  TOKEN COVERAGE   : {cov:.1f}%   ({summary['distinct_colors']} distinct colors, "
          f"{summary['palette_tokens']} palette tokens, {summary['files_scanned']} files)")
    print("  by rule: " + ", ".join(f"{k}={v}" for k, v in sorted(rep.counters.items())))

    # ---- design system checklist ----
    print("-" * 78)
    print("  DESIGN SYSTEM CHECKLIST")
    print("-" * 78)
    checks = [
        ("color token source exists", summary["palette_tokens"] > 0),
        ("token coverage >= 60%", cov >= 60.0),
        ("no <style> tags in components", rep.counters.get("DS02", 0) == 0),
        ("no !important", rep.counters.get("DS06", 0) == 0),
        ("no magic z-index", rep.counters.get("DS10", 0) == 0),
        ("no cross-workspace palette mismatch", rep.counters.get("DS13", 0) == 0),
        ("no unreadable contrast pairs", rep.counters.get("DS15", 0) == 0),
    ]
    for name, ok in checks:
        print(f"  {'✅' if ok else '❌'} {name}")

    # ---- hotlist ----
    hot = [f for f in rep.findings if f.code in HOTLIST_RULES or f.sev == RED]
    hot.sort(key=lambda f: (0 if f.sev == RED else 1, f.code, f.path))
    print("-" * 78)
    print(f"  DESIGN DAMAGE HOTLIST ({len(hot)} items)")
    print("-" * 78)
    for f in hot[:80]:
        print(f"  {SEV_ICON[f.sev]} {f.code:<5} [{f.domain:<12}] {f.loc()}")
        print(f"        {f.message}")
        if f.intended:
            print(f"        -> intended: {f.intended}")
    if len(hot) > 80:
        print(f"  ... +{len(hot) - 80} more (see report)")

    # ---- top offenders: the file-by-file ranking ----
    offenders = sorted(profiles, key=lambda p: -p.score)
    print("\n" + "=" * 78)
    print("  TOP DESIGN-DEBT FILES (file-by-file ranking)")
    print("=" * 78)
    max_score = offenders[0].score if offenders and offenders[0].score > 0 else 1
    for p in offenders[:20]:
        if p.score <= 0:
            break
        bar_len = int(p.score / max_score * 24)
        bar = "█" * max(bar_len, 1)
        print(f"  {p.score:>5}  {bar:<24} [{p.workspace:<11}] {p.path}")
        print(f"         {p.issue_tags()}")

    # ---- color drift clusters ----
    clusters = color_stats["drift_clusters"]
    if clusters:
        print("\n" + "=" * 78)
        print(f"  COLOR THEME DRIFT ({len(clusters)} near-duplicate cluster(s))")
        print("=" * 78)
        for c in clusters[:15]:
            vals = " ≈ ".join(f"{v} (×{color_stats['literal_usage'][v]})" for v in c["values"])
            verdict = "off-palette" if any(
                color_stats["classify"].get(v) == "off" for v in c["values"]
            ) else "near-token"
            print(f"  • {vals}   [{verdict}]")

    # ---- domain sections ----
    by_dom: dict[str, list] = defaultdict(list)
    for f in rep.findings:
        by_dom[f.domain].append(f)
    for dom in ["design", "web_app", "mobile_app", "shared", "frontend-root"]:
        items = by_dom.get(dom, [])
        if not items:
            continue
        print("\n" + "=" * 78)
        print(f"  DOMAIN: {dom.upper()} ({len(items)} finding(s))")
        print("=" * 78)
        for sev in (RED, YEL, GRN):
            for f in [x for x in items if x.sev == sev]:
                print(f"  {SEV_ICON[f.sev]} {f.code}  {f.loc()}")
                print(f"        {f.message}")
                if f.intended:
                    print(f"        -> {f.intended}")

    print("\n" + "=" * 78)
    return n_red


def render_markdown(repo, rep, out: Path, summary, profiles, color_stats) -> None:
    n_red, n_yel, n_grn = summary["red"], summary["yellow"], summary["green"]
    debt = summary["debt_score"]
    cov = summary["token_coverage_pct"]

    L = [
        "# ZOZI Design System Governance Audit Report (GENERATED — do not hand-edit)",
        "",
        f"**Repo:** `{repo}`  ",
        f"**Result:** 🔴 {n_red} · 🟡 {n_yel} · 🟢 {n_grn}  ",
        f"**Design Debt Score:** `{debt}`  ",
        f"**Token Coverage:** `{cov:.1f}%` "
        f"({summary['distinct_colors']} distinct colors / {summary['palette_tokens']} tokens / "
        f"{summary['files_scanned']} files)  ",
        "**Ephemeral. Add to `.gitignore`.**",
        "",
        "## Scorecard",
        "",
        "| Code | Count | Sev | Meaning |",
        "|---|---:|---|---|",
    ]
    for code in sorted(rep.counters):
        sev = next((f.sev for f in rep.findings if f.code == code), GRN)
        L.append(f"| {code} | {rep.counters[code]} | {SEV_ICON[sev]} {sev} | {RULE_MEANING.get(code, '')} |")

    # ---- per-file table (the file-by-file view) ----
    offenders = sorted(profiles, key=lambda p: -p.score)
    L += [
        "",
        "## File-by-File Design Debt",
        "",
        "| # | Score | Workspace | File | Colors | Off-palette | Inline styles | Issues |",
        "|---:|---:|---|---|---:|---:|---:|---|",
    ]
    for i, p in enumerate(offenders[:60], 1):
        if p.score <= 0 and i > 20:
            break
        L.append(
            f"| {i} | {p.score} | {p.workspace} | `{p.path}` "
            f"| {sum(p.colors.values())} | {sum(p.off_palette.values())} "
            f"| {p.inline_style_blocks} | {p.issue_tags()} |"
        )

    # ---- palette inventory ----
    usage = color_stats["literal_usage"]
    files_by_lit = color_stats["literal_files"]
    classify = color_stats["classify"]
    L += [
        "",
        "## Color Inventory (most used first)",
        "",
        "| Color | Hex | Usage | Files | Palette status |",
        "|---|---|---:|---:|---|",
    ]
    for hx in sorted(usage, key=lambda h: -usage[h])[:40]:
        status = classify.get(hx, "off")
        badge = {"token": "✅ token", "near-token": "🟡 near-token", "off": "🔴 OFF-PALETTE"}[status]
        L.append(f"| ![{hx}](https://via.placeholder.com/14/{hx[1:]}/{hx[1:]}) "
                 f"| `{hx}` | {usage[hx]} | {len(files_by_lit.get(hx, []))} | {badge} |")

    # ---- drift clusters ----
    clusters = color_stats["drift_clusters"]
    if clusters:
        L += ["", "## Color Theme Drift Clusters", "",
              "These colors are visually near-identical but written differently — ",
              "the classic symptom of theme drift.", ""]
        for c in clusters[:20]:
            vals = " ≈ ".join(f"`{v}` ×{usage[v]}" for v in c["values"])
            L.append(f"- {vals}")

    # ---- hotlist + domains ----
    hot = sorted([f for f in rep.findings if f.code in HOTLIST_RULES or f.sev == RED],
                 key=lambda f: (0 if f.sev == RED else 1, f.code))
    L += ["", "## Design Damage Hotlist", "",
          "| Sev | Rule | Domain | Location | Problem | Intended |",
          "|---|---|---|---|---|---|"]
    for f in hot:
        L.append(f"| {SEV_ICON[f.sev]} | {f.code} | {f.domain} | `{f.loc()}` "
                 f"| {f.message} | {f.intended or '-'} |")

    by_dom: dict[str, list] = defaultdict(list)
    for f in rep.findings:
        by_dom[f.domain].append(f)
    for dom in ["design", "web_app", "mobile_app", "shared", "frontend-root"]:
        items = by_dom.get(dom, [])
        if not items:
            continue
        L += ["", f"## Domain: {dom}", ""]
        for f in items:
            L.append(f"- {SEV_ICON[f.sev]} **{f.code}** `{f.loc()}` — {f.message}"
                     + (f" → *{f.intended}*" if f.intended else ""))

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(L) + "\n", encoding="utf-8")


# ============================================================================
# 10. MAIN
# ============================================================================


def _looks_like_repo_root(p: Path) -> bool:
    if not p.is_dir():
        return False
    if (p / "backend").is_dir() and (p / "frontend").is_dir():
        return True
    if (p / "frontend" / "web_app").is_dir():
        return True
    return False


def find_repo(explicit: str | None) -> Path:
    candidates: list[Path] = []
    if explicit:
        candidates.append(Path(explicit).resolve())
    script_dir = Path(__file__).resolve().parent
    if script_dir.name.lower() in {"scripts", "script"}:
        candidates.append(script_dir.parent)
    candidates.extend([script_dir, script_dir.parent, script_dir.parent.parent,
                       script_dir.parent.parent.parent, Path.cwd().resolve()])
    seen: list[Path] = []
    for cand in candidates:
        try:
            cand = cand.resolve()
        except Exception:
            continue
        if cand in seen:
            continue
        seen.append(cand)
        if _looks_like_repo_root(cand):
            return cand
    for start in (script_dir, Path.cwd()):
        for parent in [start, *start.parents]:
            parent = parent.resolve()
            if parent not in seen and _looks_like_repo_root(parent):
                return parent
    print("[FATAL] could not confirm the ZOZI repository root.\n"
          f"        looked in: {[str(c) for c in seen]}\n"
          "        Run from the repo root, or pass --root <repo>.", file=sys.stderr)
    sys.exit(2)


def resolve_repo_output_path(repo: Path, value: str | None, default_name: str) -> Path:
    if not value:
        return repo / default_name
    p = Path(value)
    if p.is_absolute():
        return p.resolve()
    return (repo / p).resolve()


def main() -> int:
    ap = argparse.ArgumentParser(description="ZOZI read-only design system governance auditor.")
    ap.add_argument("--root", default=None, help="repo root")
    ap.add_argument("--out", default=None, help="markdown report path")
    ap.add_argument("--json", default=None, help="write JSON report")
    ap.add_argument("--no-write", action="store_true", help="do not write markdown report")
    ap.add_argument("--no-fail", action="store_true", help="always exit 0")
    ap.add_argument("--ci", action="store_true", help="CI mode")
    ap.add_argument("--trend-file", default=None, help="design trend JSON file")
    ap.add_argument("--update-trend", action="store_true", help="overwrite trend baseline")
    args = ap.parse_args()

    repo = find_repo(args.root)
    frontend = repo / "frontend"

    if args.ci:
        if not args.json:
            args.json = str(repo / "out" / "governance" / "design_audit.json")
        if not args.out and not args.no_write:
            args.out = str(repo / "out" / "governance" / "design_audit_report.md")
        if not args.trend_file:
            args.trend_file = str(repo / ".governance" / "design_trend.json")

    print(f"Scanning design system: {frontend}")

    rep = Report()
    palette = discover_palette(frontend)
    classify = make_classifier(palette)

    profiles: list[FileDesignProfile] = []
    for f in iter_frontend_files(frontend, SOURCE_EXT):
        if is_scan_exempt(f):
            continue
        text = read_text(f)
        if not text:
            continue
        ws = workspace_of(f, frontend)
        profiles.append(scan_component_file(f, text, ws, repo, classify))

    for f in iter_frontend_files(frontend, CSS_EXT):
        if is_scan_exempt(f):
            continue
        text = read_text(f)
        if not text:
            continue
        ws = workspace_of(f, frontend)
        profiles.append(scan_css_file(f, text, ws, repo, classify))

    for p in profiles:
        p.score = compute_file_score(p)

    color_stats = run_checks(repo, rep, profiles, palette, classify)

    debt_score = compute_debt_score(rep)
    summary = build_summary(repo, rep, profiles, palette, color_stats, debt_score)

    trend_path = Path(args.trend_file).resolve() if args.trend_file else None
    if trend_path:
        if args.update_trend:
            update_trend(trend_path, summary)
            print(f"\nDesign trend file updated: {trend_path}")
        else:
            print_design_trend(rep, summary, read_json(trend_path))

    n_red = render_stdout(repo, rep, summary, profiles, color_stats)

    if not args.no_write:
        out = resolve_repo_output_path(repo, args.out, "DESIGN_AUDIT_REPORT.md")
        render_markdown(repo, rep, out, summary, profiles, color_stats)
        print(f"\nReport written: {out}  (generated -> .gitignore it)")

    if args.json:
        jp = resolve_repo_output_path(repo, args.json, "design_audit.json")
        jp.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "summary": summary,
            "palette": {k: v for k, v in palette["tokens"].items()},
            "color_inventory": {
                hx: {"usage": color_stats["literal_usage"][hx],
                     "files": color_stats["literal_files"][hx],
                     "status": color_stats["classify"].get(hx, "off")}
                for hx in sorted(color_stats["literal_usage"],
                                 key=lambda h: -color_stats["literal_usage"][h])
            },
            "drift_clusters": color_stats["drift_clusters"],
            "findings": [
                {"sev": f.sev, "code": f.code, "domain": f.domain, "path": f.path,
                 "line": f.line, "message": f.message, "intended": f.intended}
                for f in rep.findings
            ],
        }
        jp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(f"JSON written: {jp}")

    return 1 if (n_red and not args.no_fail) else 0


if __name__ == "__main__":
    sys.exit(main())