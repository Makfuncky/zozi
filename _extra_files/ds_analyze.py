"""DS (design-system) analyzer — replicates scripts/system_trackers/system_architecture_audit.py
SECTION 50-54 logic exactly, but reports per-file detail so fixes can be targeted.

READ-ONLY. Writes nothing except stdout / optional JSON in _extra_files.
"""
from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

DEFAULT_IGNORE_DIRS = {
    ".git", "node_modules", ".venv", "venv", "__pycache__", ".mypy_cache", ".pytest_cache",
    ".ruff_cache", ".tox", "htmlcov", ".next", ".expo", ".kotlin", "gradle", "android", "ios",
    ".idea", ".vscode", "test-results", ".playwright-artifacts-0", "playwright-out",
    "static-tmp", ".web-build-test", "artifacts", "uploads", ".turbo", "dist", "build",
    "coverage", "playwright-report", "test-output", "tmp", ".hypothesis", ".kilo", ".kilocode",
    "worktrees", ".repo", "e2e", "__tests__", "__mocks__", ".storybook", ".web", "web-dist",
}

DS_SOURCE_EXT = {".ts", ".tsx", ".js", ".jsx", ".cjs", ".mjs"}
DS_CSS_EXT = {".css", ".scss"}
DS_MAX_READ_BYTES = 2_000_000

DS_PALETTE_FILE_RE = re.compile(r"(^|[/\\])(colors|tokens|theme|palette)\.(ts|tsx|js|jsx)$", re.I)
DS_CONFIG_FILE_RE = re.compile(
    r"(tailwind|postcss|metro|babel|next|eslint|jest|playwright|sentry)\.config\.", re.I)

DS_HEX_RE = re.compile(r"#(?:[0-9a-fA-F]{8}|[0-9a-fA-F]{6}|[0-9a-fA-F]{3,4})\b")
DS_RGB_RE = re.compile(r"rgba?\(\s*[\d.]+[,\s]+[\d.]+[,\s]+[\d.]+(?:[,\s]+[\d.]+)?\s*\)", re.I)
DS_HSL_RE = re.compile(r"hsla?\(\s*[\d.]+[^\)]*\)", re.I)
DS_TW_COLOR_RE = re.compile(r"([\w$-]+)\s*:\s*['\"](#[0-9a-fA-F]{3,8})['\"]")
DS_CSS_VAR_RE = re.compile(r"(--[\w-]+)\s*:\s*(#[0-9a-fA-F]{3,8}|rgba?\([^\)]+\)|hsla?\([^\)]+\))", re.I)

DS_STYLE_OBJ_RE = re.compile(r"style\s*=\s*\{\{")
DS_STYLE_TAG_RE = re.compile(r"<style[\s>/]", re.I)
DS_IMPORTANT_RE = re.compile(r"!\s*important", re.I)
DS_ZINDEX_RE = re.compile(r"z-index\s*:\s*(\d+)", re.I)
DS_ARB_RE = re.compile(
    r"(?<![\w-])(bg|text|border|from|to|via|ring|decoration|placeholder|fill|stroke|outline|divide"
    r"|w|h|size|p|px|py|pt|pb|pl|pr|m|mx|my|mt|mb|ml|mr|gap|rounded|z|shadow"
    r"|top|left|right|bottom|inset|leading|tracking|space-x|space-y|min-w|max-w|min-h|max-h|basis)"
    r"-\[([^\]]+)\]")
DS_ARB_COLOR_PREFIXES = {"bg", "text", "border", "from", "to", "via", "ring",
                         "decoration", "placeholder", "fill", "stroke", "outline", "divide"}
DS_TW_SCREENS = {320, 375, 425, 640, 768, 820, 1024, 1280, 1440, 1536, 1920, 2560}
DS_NAMED_COLORS = {
    "white": "#ffffff", "black": "#000000", "red": "#ff0000", "green": "#008000",
    "blue": "#0000ff", "gray": "#808080", "grey": "#808080", "orange": "#ffa500",
    "purple": "#800080", "yellow": "#ffff00", "pink": "#ffc0cb", "teal": "#008080",
    "cyan": "#00ffff", "transparent": None, "inherit": None, "currentcolor": None,
}
DS_COLOR_PROPS = {"color", "backgroundColor", "borderColor", "tintColor", "background", "fill", "stroke"}
DS_SPACING_PROPS = {
    "padding", "paddingTop", "paddingBottom", "paddingLeft", "paddingRight",
    "paddingHorizontal", "paddingVertical", "margin", "marginTop", "marginBottom",
    "marginLeft", "marginRight", "marginHorizontal", "marginVertical",
    "width", "height", "top", "left", "right", "bottom", "gap", "rowGap",
    "columnGap", "borderWidth", "borderRadius", "fontSize", "lineHeight",
    "minWidth", "maxWidth", "minHeight", "maxHeight", "flexBasis",
}
DS_STYLE_PROP_RE = re.compile(r"([A-Za-z]\w*)\s*:\s*(?:'([^']*)'|\"([^\"]*)\"|([\d.]+))")
DS_SHADOW_CSS_RE = re.compile(r"(?:box-shadow|text-shadow)\s*:\s*([^;}{]+)", re.I)
DS_RADIUS_CSS_RE = re.compile(r"border-radius\s*:\s*([^;}{]+)", re.I)
DS_FONTSIZE_CSS_RE = re.compile(r"font-size\s*:\s*([^;}{]+)", re.I)
DS_FONTFAM_CSS_RE = re.compile(r"font-family\s*:\s*([^;}{]+)", re.I)
DS_MQ_RE = re.compile(r"@media[^{]*\(\s*(?:min|max)-width\s*:\s*(\d+)px", re.I)
DS_MS_RE = re.compile(r"(?<![\w.])(\d+(?:\.\d+)?)ms\b")
DS_PX_RE = re.compile(r"(?<![\w.])(\d+(?:\.\d+)?)px\b")
DS_APPLY_RE = re.compile(r"@apply\b")

DS_NEAR_DUP_THRESHOLD = 14.0
DS_NEAR_TOKEN_THRESHOLD = 10.0


def ds_hex_to_rgb(h: str):
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


def ds_to_hex(rgb) -> str:
    return "#%02x%02x%02x" % tuple(int(c) for c in rgb)


def ds_hsl_to_rgb(h: float, s: float, l: float):
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


def ds_parse_color(lit: str):
    lit = lit.strip().lower()
    if lit.startswith("#"):
        return ds_hex_to_rgb(lit)
    m = re.match(r"rgba?\(\s*([\d.]+)[,\s]+([\d.]+)[,\s]+([\d.]+)", lit)
    if m:
        try:
            return tuple(min(255, int(float(m.group(i)))) for i in (1, 2, 3))
        except ValueError:
            return None
    m = re.match(r"hsla?\(\s*([\d.]+)[,\s]+([\d.]+)[,\s]+([\d.]+)", lit)
    if m:
        try:
            return ds_hsl_to_rgb(float(m.group(1)), float(m.group(2)), float(m.group(3)))
        except ValueError:
            return None
    if lit in DS_NAMED_COLORS:
        v = DS_NAMED_COLORS[lit]
        return ds_hex_to_rgb(v) if v else None
    return None


def ds_color_distance(a, b) -> float:
    rmean = (a[0] + b[0]) / 2.0
    dr, dg, db = a[0] - b[0], a[1] - b[1], a[2] - b[2]
    return ((2 + rmean / 256.0) * dr * dr + 4 * dg * dg + (2 + (255 - rmean) / 256.0) * db * db) ** 0.5


def ds_chan(c: float) -> float:
    c /= 255.0
    return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4


def ds_rel_luminance(rgb) -> float:
    return 0.2126 * ds_chan(rgb[0]) + 0.7152 * ds_chan(rgb[1]) + 0.0722 * ds_chan(rgb[2])


def ds_contrast_ratio(a, b) -> float:
    la, lb = ds_rel_luminance(a), ds_rel_luminance(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def ds_cluster_colors(hexes, threshold: float = DS_NEAR_DUP_THRESHOLD):
    rgb_map = {h: ds_hex_to_rgb(h) for h in hexes}
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
            if ds_color_distance(rgb_map[h], rgb_map[o]) <= threshold:
                cl.append(o)
                used.add(o)
        clusters.append(cl)
    return clusters


@dataclass
class P:
    path: str = ""
    workspace: str = ""
    kind: str = "component"
    colors: dict = field(default_factory=lambda: defaultdict(int))
    off_palette: dict = field(default_factory=lambda: defaultdict(int))
    inline_style_blocks: int = 0
    style_tag: int = 0
    important: int = 0
    arb_color: dict = field(default_factory=lambda: defaultdict(int))
    arb_size: int = 0
    px_values: int = 0
    zmagic: list = field(default_factory=list)
    shadows: set = field(default_factory=set)
    radii: set = field(default_factory=set)
    font_sizes: set = field(default_factory=set)
    font_families: set = field(default_factory=set)
    durations: set = field(default_factory=set)
    breakpoints_off: set = field(default_factory=set)
    contrast_pairs: list = field(default_factory=list)
    css_in_js: int = 0


def walk(root: Path):
    import os
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in DEFAULT_IGNORE_DIRS]
        for fn in filenames:
            yield Path(dirpath) / fn


def read_text(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return ""


def rel(p: Path) -> str:
    try:
        return str(p.relative_to(REPO))
    except ValueError:
        return str(p)


def discover_palette(frontend: Path):
    tokens: dict[str, str] = {}
    value_index: dict[str, str] = {}
    sources: list[str] = []
    for e in walk(frontend):
        if e.suffix.lower() not in DS_SOURCE_EXT | DS_CSS_EXT:
            continue
        text = read_text(e)
        if not text:
            continue
        name = e.name
        if name.startswith("tailwind.config"):
            sources.append(rel(e))
            for m in DS_TW_COLOR_RE.finditer(text):
                key, val = m.group(1), m.group(2)
                rgb = ds_hex_to_rgb(val)
                if rgb is None:
                    continue
                hx = ds_to_hex(rgb)
                tokens.setdefault(key, hx)
                value_index.setdefault(hx, key)
        elif e.suffix.lower() in DS_CSS_EXT:
            for m in DS_CSS_VAR_RE.finditer(text):
                var_name, raw = m.group(1), m.group(2)
                rgb = ds_parse_color(raw)
                if rgb is None:
                    continue
                hx = ds_to_hex(rgb)
                tokens.setdefault(var_name, hx)
                value_index.setdefault(hx, var_name)
        elif DS_PALETTE_FILE_RE.search(str(e)):
            sources.append(rel(e))
            for m in DS_TW_COLOR_RE.finditer(text):
                key, val = m.group(1), m.group(2)
                rgb = ds_hex_to_rgb(val)
                if rgb is None:
                    continue
                hx = ds_to_hex(rgb)
                tokens.setdefault(key, hx)
                value_index.setdefault(hx, key)
    return {"tokens": tokens, "value_index": value_index, "sources": sources}


def make_classifier(palette):
    value_index = palette["value_index"]
    pal_rgbs = []
    for hx in value_index:
        rgb = ds_hex_to_rgb(hx)
        if rgb:
            pal_rgbs.append(rgb)
    cache: dict[str, str] = {}

    def classify(lit_hex: str) -> str:
        if lit_hex in cache:
            return cache[lit_hex]
        rgb = ds_hex_to_rgb(lit_hex)
        if rgb is None:
            cache[lit_hex] = "off"
            return "off"
        if lit_hex in value_index:
            cache[lit_hex] = "token"
            return "token"
        best = 9999.0
        for pr in pal_rgbs:
            d = ds_color_distance(rgb, pr)
            if d < best:
                best = d
            if best <= DS_NEAR_TOKEN_THRESHOLD:
                break
        verdict = "near-token" if best <= DS_NEAR_TOKEN_THRESHOLD else "off"
        cache[lit_hex] = verdict
        return verdict

    return classify


def extract_style_objects(text: str):
    out = []
    for m in DS_STYLE_OBJ_RE.finditer(text):
        start = m.end() - 1
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


def scan(frontend: Path, classify):
    profiles = []
    for e in walk(frontend):
        if e.suffix.lower() not in DS_SOURCE_EXT | DS_CSS_EXT:
            continue
        if e.suffix.lower() == ".ts" and e.name.endswith(".d.ts"):
            continue
        if DS_CONFIG_FILE_RE.search(e.name):
            continue
        if DS_PALETTE_FILE_RE.search(str(e)):
            continue
        if ".min." in e.name:
            continue
        text = read_text(e)
        if not text:
            continue
        try:
            if e.stat().st_size > DS_MAX_READ_BYTES:
                continue
        except OSError:
            continue
        try:
            parts = e.relative_to(frontend).parts
            ws = parts[0] if parts and parts[0] in ("web_app", "mobile_app", "shared") else "frontend-root"
        except ValueError:
            ws = "frontend-root"

        p = P(path=rel(e), workspace=ws,
              kind="css" if e.suffix.lower() in DS_CSS_EXT else "component")
        lines = text.splitlines()

        for rx in (DS_HEX_RE, DS_RGB_RE, DS_HSL_RE):
            for m in rx.finditer(text):
                line_no = text.count("\n", 0, m.start()) + 1
                try:
                    line = lines[line_no - 1]
                    if line.strip().startswith("//") or line.strip().startswith("*"):
                        continue
                except IndexError:
                    pass
                rgb = ds_parse_color(m.group(0))
                if rgb is None:
                    continue
                hx = ds_to_hex(rgb)
                p.colors[hx] += 1
                if classify(hx) == "off":
                    p.off_palette[hx] += 1

        p.inline_style_blocks = len(DS_STYLE_OBJ_RE.findall(text))
        p.style_tag = len(DS_STYLE_TAG_RE.findall(text))
        p.important = len(DS_IMPORTANT_RE.findall(text))
        p.css_in_js = len(re.findall(
            r"from\s+['\"](?:styled-components|@emotion/styled|@emotion/react)['\"]", text))

        for _pos, body in extract_style_objects(text):
            line_no = text.count("\n", 0, _pos) + 1
            fg_rgb = None
            bg_rgb = None
            for pm in DS_STYLE_PROP_RE.finditer(body):
                prop = pm.group(1)
                val = pm.group(2) or pm.group(3) or pm.group(4) or ""
                if not val:
                    continue
                if prop in DS_COLOR_PROPS:
                    rgb_val = ds_parse_color(val)
                    if rgb_val:
                        hx = ds_to_hex(rgb_val)
                        p.colors[hx] += 1
                        if classify(hx) == "off":
                            p.off_palette[hx] += 1
                        if prop == "color":
                            fg_rgb = rgb_val
                        elif prop in ("backgroundColor", "background"):
                            bg_rgb = rgb_val
                elif prop in DS_SPACING_PROPS:
                    if pm.group(4) or "px" in val:
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
                    for dm in DS_MS_RE.finditer(val):
                        p.durations.add(f"{dm.group(1)}ms")
            if fg_rgb and bg_rgb:
                ratio = ds_contrast_ratio(fg_rgb, bg_rgb)
                if ratio < 3.2:
                    p.contrast_pairs.append((round(ratio, 2), ds_to_hex(fg_rgb), ds_to_hex(bg_rgb), line_no))

        for m in DS_ARB_RE.finditer(text):
            prefix, val = m.group(1), m.group(2)
            is_color_val = val.startswith("#") or "rgb" in val.lower() or "hsl" in val.lower()
            if prefix in DS_ARB_COLOR_PREFIXES and is_color_val:
                p.arb_color[val.lower()] += 1
            elif prefix == "z":
                try:
                    if int(val) >= 1000:
                        p.zmagic.append(int(val))
                except ValueError:
                    pass
            elif prefix == "rounded":
                p.radii.add(val)
            elif prefix == "shadow":
                p.shadows.add(f"tw:{val}")
            else:
                if re.search(r"\d", val):
                    p.arb_size += 1

        if p.kind == "css":
            for m in DS_ZINDEX_RE.finditer(text):
                z = int(m.group(1))
                if z >= 1000:
                    p.zmagic.append(z)
            for m in DS_SHADOW_CSS_RE.finditer(text):
                p.shadows.add(re.sub(r"\s+", " ", m.group(1).strip()))
            for m in DS_RADIUS_CSS_RE.finditer(text):
                p.radii.add(re.sub(r"\s+", " ", m.group(1).strip()))
            for m in DS_FONTSIZE_CSS_RE.finditer(text):
                p.font_sizes.add(m.group(1).strip())
            for m in DS_FONTFAM_CSS_RE.finditer(text):
                p.font_families.add(m.group(1).strip())
            for m in DS_MS_RE.finditer(text):
                p.durations.add(f"{m.group(1)}ms")
            for m in DS_MQ_RE.finditer(text):
                bp = int(m.group(1))
                if bp not in DS_TW_SCREENS:
                    p.breakpoints_off.add(bp)
            p.px_values += len(DS_PX_RE.findall(text))

        profiles.append(p)
    return profiles


def main():
    frontend = REPO / "frontend"
    palette = discover_palette(frontend)
    classify = make_classifier(palette)
    profiles = scan(frontend, classify)

    out = {}
    out["palette_token_count"] = len(palette["tokens"])
    out["palette_sources"] = palette["sources"]

    literal_usage = defaultdict(int)
    literal_files = defaultdict(set)
    for p in profiles:
        for hx, cnt in p.colors.items():
            literal_usage[hx] += cnt
            literal_files[hx].add(p.path)

    # DS01
    ds01 = sorted(((p.path, p.inline_style_blocks) for p in profiles if p.inline_style_blocks >= 3),
                  key=lambda t: -t[1])
    out["DS01_files_ge3"] = ds01
    out["DS01_count_reported"] = min(len(ds01), 60)

    # DS02
    out["DS02"] = [(p.path, p.style_tag) for p in profiles if p.style_tag]

    # DS03
    off = sorted((hx for hx in literal_usage if classify(hx) == "off"),
                 key=lambda hx: (-literal_usage[hx], hx))
    out["DS03_total_off_literals"] = len(off)
    out["DS03_reported"] = [
        {"hex": hx, "count": literal_usage[hx], "files": sorted(literal_files[hx])}
        for hx in off[:30]
    ]
    out["DS03_all"] = [{"hex": hx, "count": literal_usage[hx], "files": sorted(literal_files[hx])}
                       for hx in off]

    # DS04
    clusters = ds_cluster_colors(sorted(literal_usage.keys()))
    ds04 = []
    for cl in clusters:
        if len(cl) < 2:
            continue
        total = sum(literal_usage.get(hx, 0) for hx in cl)
        if total < 3:
            continue
        ds04.append({
            "total": total,
            "members": [{"hex": hx, "count": literal_usage.get(hx, 0),
                         "files": sorted(literal_files[hx])} for hx in sorted(cl)],
        })
    out["DS04"] = ds04

    # DS05 / DS06 / DS10 / DS14 (for regression watch)
    out["DS05"] = [(p.path, sum(p.arb_color.values()), sorted(p.arb_color)) for p in profiles if p.arb_color]
    out["DS06"] = [(p.path, p.important) for p in profiles if p.important]
    out["DS10"] = [(p.path, sorted(set(p.zmagic))) for p in profiles if p.zmagic]
    out["DS14"] = [p.path for p in profiles if p.css_in_js]

    # DS07
    fs = defaultdict(list)
    ff = defaultdict(list)
    for p in profiles:
        for v in p.font_sizes:
            fs[v].append(p.path)
        for v in p.font_families:
            ff[v].append(p.path)
    out["DS07_font_sizes"] = {k: sorted(set(v)) for k, v in sorted(fs.items())}
    out["DS07_font_families"] = {k: sorted(set(v)) for k, v in sorted(ff.items())}

    # DS08
    out["DS08_total_px"] = sum(p.px_values for p in profiles)
    out["DS08_by_file"] = sorted(((p.path, p.px_values) for p in profiles if p.px_values),
                                 key=lambda t: -t[1])

    # DS09
    radii = defaultdict(list)
    for p in profiles:
        for v in p.radii:
            radii[v].append(p.path)
    out["DS09_radii"] = {k: sorted(set(v)) for k, v in sorted(radii.items())}

    # DS11
    shadows = defaultdict(list)
    for p in profiles:
        for v in p.shadows:
            shadows[v].append(p.path)
    out["DS11_shadows"] = {k: sorted(set(v)) for k, v in sorted(shadows.items())}

    # DS15
    out["DS15"] = [(p.path, p.contrast_pairs) for p in profiles if p.contrast_pairs]

    # DS16
    durations = defaultdict(list)
    for p in profiles:
        for v in p.durations:
            durations[v].append(p.path)
    out["DS16_durations"] = {k: sorted(set(v)) for k, v in sorted(durations.items())}

    # DS17
    used_hexes = set(literal_usage.keys())
    out["DS17_unused_tokens"] = sorted(
        name for name, hx in palette["tokens"].items() if hx not in used_hexes)

    # DS18
    bps = set()
    for p in profiles:
        bps |= p.breakpoints_off
    out["DS18_breakpoints"] = sorted(bps)

    dest = REPO / "_extra_files" / "ds_report.json"
    dest.write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")

    print(f"palette tokens        : {out['palette_token_count']}")
    print(f"palette sources       : {out['palette_sources']}")
    print(f"DS01 files (>=3 inline): {len(ds01)}  (reported cap 60)")
    print(f"DS02 style tags        : {out['DS02']}")
    print(f"DS03 off-palette hexes : {len(off)}  (reported cap 30)")
    print(f"DS04 drift clusters    : {len(ds04)}")
    print(f"DS05 arb-color files   : {len(out['DS05'])}")
    print(f"DS06 !important files  : {len(out['DS06'])}")
    print(f"DS07 font sizes        : {len(fs)} (limit 8)")
    print(f"DS07 font families     : {len(ff)} (limit 2) -> {sorted(ff)}")
    print(f"DS08 total px          : {out['DS08_total_px']} (limit 100)")
    print(f"DS09 radii             : {len(radii)} (limit 5)")
    print(f"DS10 magic z files     : {len(out['DS10'])}")
    print(f"DS11 shadows           : {len(shadows)} (limit 4)")
    print(f"DS14 css-in-js         : {out['DS14']}")
    print(f"DS15 contrast files    : {len(out['DS15'])}")
    print(f"DS16 durations         : {len(durations)} (limit 6) -> {sorted(durations)}")
    print(f"DS17 unused tokens     : {len(out['DS17_unused_tokens'])}")
    print(f"DS18 breakpoints off   : {out['DS18_breakpoints']}")
    print(f"\nwrote {dest}")


if __name__ == "__main__":
    sys.exit(main())
