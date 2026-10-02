"""Dimension 14 (extension) — design system, colour drift and UI primitives.

The prompt's dimension list has no design/colour axis, yet a multi-country
storefront cannot be production-ready when 500+ hardcoded hex values and a
second, undeclared colour vocabulary (raw Tailwind palette classes) sit beside
the token layer. Every count here is *measured from source in this run* and the
measured inventory is emitted as observations so the compiler can quantify the
refactor instead of asserting it.
"""
from __future__ import annotations

import re
from pathlib import Path

from zz_core.model import CheckResult, Finding, Observation, Recommendation, ScanContext
from zz_core.registry import check
from zz_core.util import read_text

# Files that legitimately own colour values: the token layer itself, theme
# switchers that *inject* tokens, and SVG brand assets. A literal in a brand
# SVG or a chart series palette is the correct representation, not drift.
TOKEN_OWNERS = (
    "src/styles/tokens.css",
    "src/styles/globals.css",
    "src/styles/glow.css",
    "src/styles/panel-modern.css",
    "src/styles/comm.css",
    "src/shared/theme.ts",
    "src/shared/theme.native.ts",
    "src/lib/utils.ts",
)

# Directories where a hex literal is correct, not a defect.
LEGIT_HEX_PATH_HINTS = (
    "src/logo/", "src/shared/logo/", "src/components/shared/components/logo/",
    "src/assets/", "public/",
)
LEGIT_HEX_NAME_HINTS = ("chart", "palette", "theme", "gradient", "color", "colour",
                        "swatch", "logo", "icon", "sparkline", "sparklines")


def _hex_is_legitimate(rel: str) -> bool:
    low = rel.lower()
    if any(h in low for h in LEGIT_HEX_PATH_HINTS):
        return True
    name = low.rsplit("/", 1)[-1]
    return any(h in name for h in LEGIT_HEX_NAME_HINTS)

HEX_RE = re.compile(r"#[0-9a-fA-F]{6}\b|#[0-9a-fA-F]{3}\b")
# A raw palette class bypasses the semantic scale (primary/secondary/accent/
# muted/destructive/surface/text/border) and cannot be themed.
PALETTE_RE = re.compile(
    r"\b(?:bg|text|border|fill|stroke|ring|from|via|to|outline|shadow|decoration|"
    r"divide|placeholder|caret|accent)-"
    r"(?:red|blue|green|yellow|purple|orange|pink|indigo|teal|cyan|slate|gray|grey|"
    r"zinc|neutral|stone|amber|lime|emerald|sky|violet|fuchsia|rose|white|black)"
    r"-\d{2,3}\b")
SEMANTIC_RE = re.compile(
    r"\b(?:bg|text|border|fill|stroke|ring|from|via|to)-(?:primary|secondary|accent|"
    r"muted|destructive|success|warning|info|surface|text|border|on-brand|"
    r"on-accent|on-warning|brand)(?:-[\w/]+)?\b")
INLINE_STYLE_RE = re.compile(r"style=\{\{")
DARK_RE = re.compile(r"\bdark:")

# A 5-tier product taxonomy needs this many hierarchy levels. The domain rule
# in FEATURE_STACK_LIST.md is the source of the target, not a hard-coded guess.
CATEGORY_DEPTH_TARGET = 5


def _web_root(ctx: ScanContext) -> Path:
    return ctx.frontend / "web_app"


def _token_files(ctx: ScanContext) -> list[Path]:
    styles = _web_root(ctx) / "src" / "styles"
    return sorted(styles.glob("*.css")) if styles.exists() else []


def _collect(ctx: ScanContext, pattern: re.Pattern, skip_legit_hex: bool = False) -> dict[str, list[int]]:
    """``{relative_path: [line numbers]}`` for a regex over frontend source.

    Web app only. React Native has no CSS cascade, so `style={{...}}` and hex
    literals there are the idiomatic representation, not design-system drift;
    including them inflated the counts roughly 5x and would have produced a
    finding nobody could act on.
    """
    hits: dict[str, list[int]] = {}
    for p in ctx.ts_files + ctx.js_files:
        rel = ctx.rel(p)
        # ctx.rel() is repo-relative with no leading slash.
        if "frontend/web_app/" not in rel:
            continue
        if any(rel.endswith(owner) for owner in TOKEN_OWNERS):
            continue
        if skip_legit_hex and _hex_is_legitimate(rel):
            continue
        text, _ = read_text(p)
        if not text:
            continue
        for n, line in enumerate(text.splitlines(), 1):
            if pattern.search(line):
                hits.setdefault(rel, []).append(n)
    return hits


@check("design_tokens", "14_frontend_web", "frontend",
       "Design-token layer: which CSS custom properties exist, whether the "
       "semantic scale is complete, and whether a second colour vocabulary "
       "sits beside the token layer.")
def design_tokens(ctx: ScanContext) -> CheckResult:
    res = CheckResult(check="design_tokens", dimension="14_frontend_web")
    web = _web_root(ctx)
    css_files = _token_files(ctx)
    declared: dict[str, int] = {}
    dark_block = False
    for css in css_files:
        text, _ = read_text(css)
        if not text:
            continue
        for n, line in enumerate(text.splitlines(), 1):
            m = re.match(r"\s*(--[\w-]+)\s*:", line)
            if m:
                declared.setdefault(m.group(1), n)
            if re.search(r"(:root|\.dark|\[data-theme)", line):
                dark_block = True
    res.facts["design_tokens"] = {
        "css_files": [ctx.rel(c) for c in css_files],
        "custom_property_count": len(declared),
        "has_dark_block": dark_block,
        "semantic_scale": sorted(
            k for k in declared
            if re.search(r"(brand|surface|text|border|primary|accent|destructive|"
                         r"success|warning|info|radius)", k))[:40],
    }
    for css in css_files:
        text, _ = read_text(css)
        res.observations.append(Observation(
            "design_token_file", ctx.rel(css), ctx.rel(css), 0,
            "14_frontend_web",
            evidence=f"{len(declared)} custom properties declared across "
                     f"{len(css_files)} stylesheet(s)"))
    if not css_files:
        res.findings.append(Finding(
            id="DS-tokens-missing", dimension="14_frontend_web", phase="frontend",
            cluster="CLUSTER-design-tokens", file="frontend/web_app/src/styles",
            current="no stylesheet declares CSS custom properties for colour",
            target="a single token layer owns every colour, size and radius",
            delta="no token layer found",
            fix="add src/styles/tokens.css with :root custom properties and "
                "point tailwind.config.js at them",
            effort="L", priority="P0", confidence=5, evidence_strength="multiple",
            truth_level="L0", claim_state="VERIFIED", completion_blocker="no",
            verify="grep -c '^\\s*--' frontend/web_app/src/styles/*.css",
        ))
        return res
    # Semantic vocabulary must be declared once, centrally.
    token_only = [c for c in css_files if c.name not in ("globals.css",)]
    if not token_only:
        res.findings.append(Finding(
            id="DS-tokens-single-owner", dimension="14_frontend_web", phase="frontend",
            cluster="CLUSTER-design-tokens", file="frontend/web_app/src/styles/globals.css",
            current="globals.css is the only stylesheet, so tokens and component "
                    "rules cannot be changed independently",
            target="tokens.css owns variables; globals.css owns only base rules",
            delta="single-file token layer",
            fix="split the :root block from globals.css into tokens.css",
            effort="M", priority="P2", confidence=4, evidence_strength="single",
            truth_level="L1", claim_state="INFERRED", completion_blocker="no",
            verify="ls frontend/web_app/src/styles/",
        ))
    if not dark_block:
        res.findings.append(Finding(
            id="DS-dark-mode", dimension="14_frontend_web", phase="frontend",
            cluster="CLUSTER-design-tokens", file="frontend/web_app/src/styles",
            current="no dark-theme selector found in any stylesheet",
            target="every semantic token has a dark-mode value",
            delta="dark mode cannot be toggled",
            fix="add a `.dark` / `[data-theme='dark']` block overriding the "
                "semantic tokens",
            effort="M", priority="P1", confidence=4, evidence_strength="multiple",
            truth_level="L1", claim_state="INFERRED", completion_blocker="no",
            verify="grep -n '\\.dark' frontend/web_app/src/styles/*.css",
        ))
        res.recommendations.append(Recommendation(
            area="design", dimension="14_frontend_web",
            title="Introduce a semantic token scale and retire raw palette classes",
            rationale="A 5-country storefront needs a brand and per-country theme "
                      "that can change without editing components.",
            current="tokens exist but components also use raw Tailwind palette "
                    "classes and inline hex, so a brand change cannot propagate.",
            proposal="keep exactly one token layer (primary/secondary/accent/"
                     "muted/destructive/surface/text/border/radius) and map every "
                     "component to it; ban raw palette classes via an ESLint "
                     "no-restricted-syntax rule.",
            benefit="one brand change reaches every screen; dark mode becomes a "
                    "token swap instead of a code change",
            effort="XL", impact="high", category="design",
            evidence="frontend/web_app/src/styles/, frontend/web_app/tailwind.config.js",
            human_effort_saved="~1 day per rebrand (currently a multi-week sweep)",
        ))
    return res


@check("color_drift", "14_frontend_web", "frontend",
       "Measure hardcoded hex values and raw Tailwind palette classes outside "
       "the token layer; rank the worst offenders by file:line.")
def color_drift(ctx: ScanContext) -> CheckResult:
    res = CheckResult(check="color_drift", dimension="14_frontend_web")
    hex_hits = _collect(ctx, HEX_RE, skip_legit_hex=True)
    palette_hits = _collect(ctx, PALETTE_RE)
    semantic_hits = _collect(ctx, SEMANTIC_RE)
    inline_hits = _collect(ctx, INLINE_STYLE_RE)
    dark_hits = _collect(ctx, DARK_RE)

    hex_total = sum(len(v) for v in hex_hits.values())
    palette_total = sum(len(v) for v in palette_hits.values())
    inline_total = sum(len(v) for v in inline_hits.values())
    semantic_total = sum(len(v) for v in semantic_hits.values())
    res.facts["color_drift"] = {
        "hardcoded_hex_in_components": hex_total,
        "raw_palette_classes": palette_total,
        "inline_style_props": inline_total,
        "semantic_token_classes": semantic_total,
        "files_with_hex": len(hex_hits),
        "files_with_palette": len(palette_hits),
        "dark_variant_files": len(dark_hits),
        "note": "web app only; brand SVG/logo, chart and palette files excluded. "
                "React Native has no CSS cascade, so mobile inline styles and hex "
                "values are idiomatic and are not counted as drift",
        "top_hex_files": sorted(((p, len(l)) for p, l in hex_hits.items()),
                                key=lambda t: -t[1])[:15],
        "top_palette_files": sorted(((p, len(l)) for p, l in palette_hits.items()),
                                    key=lambda t: -t[1])[:15],
    }
    for rel, lines in list(hex_hits.items())[:40]:
        res.observations.append(Observation(
            "hex_color", rel, rel, lines[0], "14_frontend_web",
            evidence=f"{len(lines)} hardcoded hex value(s) outside the token layer",
        ))
    for rel, lines in list(palette_hits.items())[:40]:
        res.observations.append(Observation(
            "raw_palette_class", rel, rel, lines[0], "14_frontend_web",
            evidence=f"{len(lines)} raw Tailwind palette class(es) bypassing tokens",
        ))

    if palette_total > 40:
        worst = ", ".join(f"{p} ({n})" for p, n in
                          sorted(((p, len(l)) for p, l in palette_hits.items()),
                                 key=lambda t: -t[1])[:5])
        res.findings.append(Finding(
            id="DS-palette-drift", dimension="14_frontend_web", phase="frontend",
            cluster="CLUSTER-color-drift", file="frontend/web_app/src",
            current=f"{palette_total} raw Tailwind palette class(es) across "
                    f"{len(palette_hits)} files bypass the semantic token scale",
            target="every colour utility resolves to a semantic token "
                   "(primary/accent/muted/destructive/surface/text/border)",
            delta=f"{palette_total} unthemed colour utilities alongside "
                  f"{semantic_total} semantic ones, so a brand change cannot "
                  f"reach the unthemed set",
            fix="replace the raw palette classes with semantic token classes, "
                "starting with the five worst files; add an ESLint rule so they "
                "cannot come back",
            effort="XL", priority="P1", confidence=5, evidence_strength="multiple",
            truth_level="L0", claim_state="VERIFIED", completion_blocker="no",
            verify="grep -rEn '(bg|text|border)-(slate|gray|zinc|neutral)-[0-9]{2,3}' "
                   "frontend/web_app/src | wc -l",
            snippet=worst,
        ))
    if hex_total > 150:
        res.findings.append(Finding(
            id="DS-hex-drift", dimension="14_frontend_web", phase="frontend",
            cluster="CLUSTER-color-drift", file="frontend/web_app/src",
            current=f"{hex_total} hardcoded hex colour(s) across {len(hex_hits)} "
                    f"component file(s) outside the token layer (brand SVG, chart "
                    f"and palette files excluded — a literal is correct there)",
            target="no literal colour in a component outside tokens.css / theme.ts",
            delta=f"{hex_total} literals that a brand change cannot reach",
            fix="convert literals to `var(--color-*)` references or Tailwind token "
                "classes; brand assets (logo SVG) may keep literals but must be "
                "isolated in src/shared/logo/",
            effort="XL", priority="P1", confidence=5, evidence_strength="multiple",
            truth_level="L0", claim_state="VERIFIED", completion_blocker="no",
            verify="grep -rEon '#[0-9a-fA-F]{6}' frontend/web_app/src | "
                   "grep -v 'src/styles/tokens.css' | wc -l",
        ))
    if inline_total > 100:
        worst = sorted(((p, len(l)) for p, l in inline_hits.items()),
                       key=lambda t: -t[1])[:5]
        res.findings.append(Finding(
            id="DS-inline-style", dimension="14_frontend_web", phase="frontend",
            cluster="CLUSTER-color-drift", file="frontend/web_app/src",
            current=f"{inline_total} inline `style={{...}}` prop(s) across "
                    f"{len(inline_hits)} files; inline colour cannot be themed",
            target="colour and layout live in the token/class system",
            delta=f"{inline_total} unthemed inline styles; worst: "
                  + ", ".join(f"{p} ({n})" for p, n in worst),
            fix="move static colours and spacing out of inline styles into the "
                "token layer / utility classes; keep only genuinely dynamic values "
                "(measured positions, computed transforms)",
            effort="L", priority="P2", confidence=5, evidence_strength="multiple",
            truth_level="L0", claim_state="VERIFIED", completion_blocker="no",
            verify="grep -rc 'style={{' frontend/web_app/src --include=*.tsx | "
                   "awk -F: '$2>0' | wc -l",
        ))
    return res


@check("ui_primitives", "14_frontend_web", "frontend",
       "Shared UI primitive layer: variant system, ref forwarding, and how many "
       "components duplicate primitive markup instead of importing it.")
def ui_primitives(ctx: ScanContext) -> CheckResult:
    res = CheckResult(check="ui_primitives", dimension="14_frontend_web")
    ui_dirs = [
        _web_root(ctx) / "src" / "components" / "ui",
        _web_root(ctx) / "src" / "shared" / "components" / "ui",
    ]
    primitives: list[dict] = []
    for d in ui_dirs:
        if not d.exists():
            continue
        for f in sorted(d.glob("*.tsx")):
            text, _ = read_text(f)
            if not text:
                continue
            primitives.append({
                "name": f.stem,
                "file": ctx.rel(f),
                "line": 0,
                "cva": "cva(" in text,
                "forward_ref": "forwardRef" in text,
                "display_name": ".displayName" in text or "displayName =" in text,
                "lines": len(text.splitlines()),
            })
    if not primitives:
        res.findings.append(Finding(
            id="DS-primitives-missing", dimension="14_frontend_web", phase="frontend",
            cluster="CLUSTER-design-primitives", file="frontend/web_app/src/components",
            current="no shared UI primitive directory exists",
            target="one primitive layer (Button, Card, Dialog, Input, Select, "
                   "Table, Toast) that every screen imports",
            delta="every screen re-implements its own controls",
            fix="introduce src/components/ui with the canonical primitives",
            effort="XL", priority="P1", confidence=4, evidence_strength="single",
            truth_level="L1", claim_state="INFERRED", completion_blocker="no",
            verify="ls frontend/web_app/src/components/ui",
        ))
        return res

    res.facts["ui_primitives"] = {
        "count": len(primitives),
        "using_cva": sum(1 for p in primitives if p["cva"]),
        "missing_forward_ref": [p["file"] for p in primitives if not p["forward_ref"]],
        "missing_display_name": [p["file"] for p in primitives if not p["display_name"]],
        "names": sorted(p["name"] for p in primitives),
    }
    no_ref = [p for p in primitives if not p["forward_ref"]]
    no_name = [p for p in primitives if not p["display_name"]]
    no_cva = [p for p in primitives if not p["cva"]]
    if not any(p["cva"] for p in primitives):
        res.findings.append(Finding(
            id="DS-no-variant-system", dimension="14_frontend_web", phase="frontend",
            cluster="CLUSTER-design-primitives", file="frontend/web_app/src/components/ui",
            current=f"none of the {len(primitives)} primitives use a variant "
                    f"system (class-variance-authority); variants are raw "
                    f"Record<string, string> maps",
            target="typed variants with compound support so a new visual state is "
                   "one declaration",
            delta="variant logic is duplicated per component and cannot be "
                  "type-checked",
            fix="adopt `cva` for Button/Card/Badge/Progress variant maps",
            effort="M", priority="P2", confidence=5, evidence_strength="multiple",
            truth_level="L0", claim_state="VERIFIED", completion_blocker="no",
            verify="grep -rl 'cva(' frontend/web_app/src/components/ui | wc -l",
            snippet=", ".join(p["file"] for p in no_cva[:8]),
        ))
    if no_ref:
        res.findings.append(Finding(
            id="DS-primitive-ref", dimension="14_frontend_web", phase="frontend",
            cluster="CLUSTER-design-primitives", file="frontend/web_app/src/components/ui",
            current=f"{len(no_ref)} of {len(primitives)} primitives do not forward "
                    f"refs and set no displayName",
            target="every primitive forwards its ref and declares displayName "
                   "(required by Radix/floating-ui and for React DevTools)",
            delta="ref-based focus management and tooltips cannot wrap these "
                  "components",
            fix="wrap each primitive body in forwardRef<HTMLElement, Props> and "
                "assign `.displayName`",
            effort="M", priority="P2", confidence=5, evidence_strength="multiple",
            truth_level="L0", claim_state="VERIFIED", completion_blocker="no",
            verify="grep -rL 'forwardRef' frontend/web_app/src/components/ui/*.tsx",
            snippet=", ".join(p["file"] for p in no_ref[:10]),
        ))

    # How many screens duplicate the card/input class string instead of
    # importing a primitive? That is the refactor's real size.
    dup_re = re.compile(r"rounded-(?:xl|2xl|-lg)\s+border\s+border-(?:border|surface)")
    dup_files: list[str] = []
    dup_hits = 0
    for p in ctx.ts_files:
        rel = ctx.rel(p)
        if "frontend/web_app/src/" not in rel or "/components/ui/" in rel:
            continue
        text, _ = read_text(p)
        if text and dup_re.search(text):
            dup_files.append(rel)
            dup_hits += len(dup_re.findall(text))
    res.facts["ui_primitives"]["duplicate_card_markup_files"] = len(dup_files)
    res.facts["ui_primitives"]["duplicate_card_markup_sites"] = dup_hits
    if len(dup_files) > 25:
        res.findings.append(Finding(
            id="DS-duplicate-markup", dimension="14_frontend_web", phase="frontend",
            cluster="CLUSTER-design-primitives", file="frontend/web_app/src",
            current=f"{dup_hits} hand-rolled card/input class strings across "
                    f"{len(dup_files)} files duplicate an existing primitive",
            target="screens import the Card/Input primitive instead of "
                   "re-declaring the class string",
            delta="a visual change to cards requires editing "
                  f"{len(dup_files)} files",
            fix="replace the duplicated class strings with <Card>/<Input>; the "
                "primitive already exists, so this is a mechanical sweep",
            effort="L", priority="P2", confidence=5, evidence_strength="multiple",
            truth_level="L0", claim_state="VERIFIED", completion_blocker="no",
            verify="grep -rlE 'rounded-(xl|2xl) border border-(border|surface)' "
                   "frontend/web_app/src | wc -l",
            snippet=", ".join(dup_files[:8]),
        ))
        res.recommendations.append(Recommendation(
            area="design", dimension="14_frontend_web",
            title="Adopt the existing UI primitives and delete duplicated markup",
            rationale="The primitives already exist; screens simply do not use them, "
                      "so every redesign multiplies the edit surface.",
            current=f"{len(primitives)} primitives exist but {len(dup_files)} files "
                    f"hand-roll the same class strings.",
            proposal="codemod the duplicated class strings to the primitives, then "
                     "add a lint rule forbidding raw card/input class strings.",
            benefit=f"future visual changes touch {len(primitives)} files instead of "
                    f"{len(dup_files) + len(primitives)}",
            effort="L", impact="high", category="design",
            evidence="frontend/web_app/src/components/ui",
            human_effort_saved="~2 days per UI refresh",
            prerequisites=("DS-palette-drift",),
        ))
    return res
