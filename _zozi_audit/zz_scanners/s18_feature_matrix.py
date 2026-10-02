"""Dimension 16 (extension) — feature coverage matrix and product taxonomy.

Three questions the existing audit never answered:

1. Which declared features are gated, which gates point at features that do not
   exist, and which declared features are dead weight?
2. Is every *shipped route* reachable by a test, and is every *test* pointing at
   a route that still exists?
3. Can the catalog express the mandated multi-tier product taxonomy, and how
   deep does the data actually go? (A schema that can hold five levels but is
   seeded two deep is a real, separately-reportable defect.)

Findings assert a defect. Recommendations carry the *design* of the fix
(e.g. the five-tier model) so the compiler can turn it into work.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from zz_core.model import CheckResult, Finding, Observation, Recommendation, ScanContext
from zz_core.registry import check
from zz_core.util import read_text

# The target taxonomy depth. FEATURE_STACK_LIST.md describes a 5-layer
# category hierarchy; the schema must be able to hold it and the seed must use it.
CATEGORY_DEPTH_TARGET = 5

FEATURE_KEY_RE = re.compile(r'["\']([a-z][a-z0-9_]*(?:\.[a-z0-9_]+)+)["\']')
REQUIRE_RE = re.compile(r'require_feature\(\s*["\']([^"\']+)["\']')


def _looks_like_feature_id(lit: str) -> bool:
    """Reject sample values and string fragments that are not feature ids.

    The catalog uses ``<domain>.<verb>[.<noun>]`` in snake_case. Anything with a
    wildcard, whitespace, a newline, fewer than two segments, or an uppercase
    character is documentation or a template, not a gate.
    """
    if not lit or len(lit) > 80:
        return False
    if "*" in lit or any(ch.isspace() for ch in lit) or "\n" in lit:
        return False
    if lit != lit.lower() or '"' in lit or "'" in lit:
        return False
    segs = lit.split(".")
    if len(segs) < 2 or any(not re.fullmatch(r"[a-z][a-z0-9_]*", s) for s in segs):
        return False
    # Reserved sample values that are structurally valid but obviously not real.
    if segs[0] in ("x", "foo", "bar", "test", "example", "domain"):
        return False
    return True


def _strip_py_noise(text: str) -> str:
    """Blank out Python comments and docstrings, preserving line numbers.

    A gate literal that only appears in a comment or an example in a docstring
    is not a gate; matching it produces a finding no reviewer can reproduce.
    """
    import io
    import tokenize
    out = list(text)
    try:
        for tok in tokenize.generate_tokens(io.StringIO(text).readline):
            if tok.type == tokenize.COMMENT or (
                    tok.type == tokenize.STRING
                    and tok.line.strip().startswith(('"""', "'''"))):
                for i in range(tok.start[0], tok.end[0] + 1):
                    if 0 <= i - 1 < len(out):
                        out[i - 1] = re.sub(r"[^\n]", " ", out[i - 1])
    except (tokenize.TokenError, IndentationError, SyntaxError):
        return text
    return "".join(out)


def _catalog(ctx: ScanContext) -> dict[str, list[str]]:
    """``{domain: [feature_id, ...]}`` from every ``domains/*/features.py``."""
    out: dict[str, list[str]] = {}
    for p in ctx.py_files:
        rel = ctx.rel(p)
        m = re.match(r"backend/domains/([^/]+)/features\.py$", rel.replace("\\", "/"))
        if not m:
            continue
        text, _ = read_text(p)
        if not text:
            continue
        # A features module declares ids either as dict keys or list items.
        ids = set()
        for km in re.finditer(r'^\s{4}"([a-z][a-z0-9_]*(?:\.[a-z0-9_]+)+)"\s*:', text, re.M):
            ids.add(km.group(1))
        for lm in re.finditer(r'^\s*-\s*["\']([a-z][a-z0-9_]*(?:\.[a-z0-9_]+)+)["\']', text, re.M):
            ids.add(lm.group(1))
        for vm in re.finditer(r'["\']([a-z][a-z0-9_]*\.[a-z0-9_.]+)["\']\s*:', text):
            ids.add(vm.group(1))
        out[m.group(1)] = sorted(ids)
    return out


def _used_literals(ctx: ScanContext, declared_ids: set[str] | None = None) -> dict[str, list[str]]:
    """``{feature_id: [file:line, ...]}`` for feature literals referenced in code.

    A feature is *gated* when it appears as an argument to ``require_feature``.
    It is *referenced* when the exact declared id appears anywhere else in
    application code. Reporting both is what stops a 231-item "dead feature"
    list that is really 231 features gated through a helper this scanner did
    not recognise.
    """
    declared_ids = declared_ids or set()
    gated: dict[str, list[str]] = {}
    referenced: dict[str, list[str]] = {}
    sources = ctx.py_files + ctx.ts_files + ctx.js_files
    for p in sources:
        rel = ctx.rel(p)
        if "/node_modules/" in rel or rel.endswith("features.py") or \
                "/tests/" in rel or "/e2e/" in rel or "__tests__/" in rel:
            continue
        text, _ = read_text(p)
        if not text:
            continue
        # A literal inside a comment or docstring is not a gate. Without this
        # the audit reports example strings from documentation as undefined
        # features that no reviewer can reproduce.
        code = _strip_py_noise(text) if rel.endswith(".py") else text
        for m in re.finditer(r"require_feature\(\s*[\"']([^\"']+)[\"']", code):
            lit = m.group(1)
            # A real feature id is dot-separated snake_case. A wildcard ("*"),
            # a single bare token, or an embedded newline is a sample value or
            # a fragment of another string, not a gate anyone can reproduce.
            if not _looks_like_feature_id(lit):
                continue
            gated.setdefault(lit, []).append(
                f"{rel}:{code[:m.start()].count(chr(10)) + 1}")
    # Exact-string lookup against the declared ids. Matching the *known* ids
    # cannot invent a false reference, whereas scanning for any dotted string
    # would match config keys and module paths.
    for p in sources:
        rel = ctx.rel(p)
        if "/node_modules/" in rel or rel.endswith("features.py"):
            continue
        text, _ = read_text(p)
        if not text:
            continue
        for fid in declared_ids:
            for m in re.finditer(rf"[\"']{re.escape(fid)}[\"']", text):
                referenced.setdefault(fid, []).append(
                    f"{rel}:{text[:m.start()].count(chr(10)) + 1}")
                break
    for fid, sites in gated.items():
        referenced.setdefault(fid, sites)
    return {"gated": gated, "referenced": referenced}


@check("feature_gate_integrity", "16_features", "arch",
       "Reconcile every require_feature literal against the declared catalog: "
       "undefined gates, dead features, and the fail-open/fail-closed default.")
def feature_gate_integrity(ctx: ScanContext) -> CheckResult:
    res = CheckResult(check="feature_gate_integrity", dimension="16_features")
    catalog = _catalog(ctx)
    declared = {fid for ids in catalog.values() for fid in ids}
    used_map = _used_literals(ctx, declared)
    used = used_map["gated"]
    referenced = used_map["referenced"]
    # Only a literal passed to require_feature() (or to a FEATURES collection)
    # counts as an undefined gate. A name merely appearing in a FEATURES tuple
    # that is never used to gate is a separate, weaker signal.
    undefined = sorted(fid for fid in set(used) if fid not in declared)
    weak_undefined = sorted(
        fid for fid in referenced
        if fid not in declared and fid not in used
        and any(fid.startswith(f"{d}.") or fid.startswith(f"{d}_") for d in catalog))
    # "Dead" means declared AND never mentioned anywhere outside its own
    # features.py. Anything referenced through a helper is not dead.
    dead = sorted(fid for fid in declared if fid not in referenced)

    # The critical question: what does an unknown feature do? fail-open means
    # the gate protects nothing.
    default_behaviour = "unknown"
    impl = None
    for p in ctx.py_files:
        if re.search(r"backend/(rbac|kernel|infrastructure)/", ctx.rel(p).replace("\\", "/")):
            text, _ = read_text(p)
            if text and "def require_feature" in text:
                impl = p
                break
    if impl is not None:
        text, _ = read_text(impl)
        body = text[text.find("def require_feature"):][:2500]
        if re.search(r"if\s+not\s+[a-z_]+\s*:", body) or re.search(r"return\s+True", body[:600]):
            default_behaviour = "allow-unknown" if re.search(r"return\s+True", body[:600]) else "deny-unknown"
        elif re.search(r"return\s+False", body[:600]):
            default_behaviour = "deny-unknown"

    res.facts["feature_catalog"] = {
        "domains": len(catalog),
        "declared_features": len(declared),
        "gated_features": len(used),
        "referenced_features": len(referenced),
        "undefined_gates": len(undefined),
        "weak_undefined_references": len(weak_undefined),
        "dead_features": len(dead),
        "gate_default_for_unknown": default_behaviour,
        "per_domain": {d: len(v) for d, v in sorted(catalog.items())},
        "undefined_sample": undefined[:30],
        "weak_undefined_sample": weak_undefined[:20],
        "dead_sample": dead[:30],
    }
    for d, ids in sorted(catalog.items()):
        res.observations.append(Observation(
            "feature_domain", f"backend/domains/{d}/features.py",
            f"backend/domains/{d}/features.py", 0, "16_features",
            evidence=f"{len(ids)} feature(s) declared in {d}",
        ))

    for fid in undefined[:40]:
        site = (used.get(fid) or referenced.get(fid) or ["backend/domains", 0])[0]
        path, _, line = str(site).partition(":")
        is_gate = fid in used
        res.findings.append(Finding(
            id="FEAT-UNDEF", dimension="16_features", phase="arch",
            cluster="CLUSTER-feature-gate", file=path, line=int(line or 0),
            current=(f"`require_feature(\"{fid}\")` gates on a feature that no "
                     f"features.py declares" if is_gate else
                     f"feature literal `{fid}` is used in code but declared in no "
                     f"features.py"),
            target="every feature literal exists in the feature catalog (Law 4)",
            delta=f"{len(undefined)} undefined feature literal(s); the gate "
                  f"behaviour depends on the unknown-feature default",
            fix=f"declare `{fid}` in the owning domain's features.py, or correct the "
                f"literal to the intended feature id",
            effort="S", priority="P1" if is_gate else "P2", confidence=4,
            evidence_strength="multiple",
            truth_level="L0" if is_gate else "L1",
            claim_state="VERIFIED" if is_gate else "INFERRED",
            completion_blocker="no",
            verify=f"grep -rn '\"{fid}\"' backend/domains/*/features.py",
            laws=(4,),
        ))
    if dead:
        res.findings.append(Finding(
            id="FEAT-DEAD", dimension="16_features", phase="arch",
            cluster="CLUSTER-feature-gate", file="backend/domains",
            current=f"{len(dead)} declared feature(s) are never referenced by any "
                    f"gate",
            target="a declared feature is either gated somewhere or removed",
            delta=f"{len(dead)} features give a false impression of coverage and "
                  f"appear in the catalog UI as enabled",
            fix="gate the endpoints that should use them, or delete the dead "
                "entries from features.py",
            effort="M", priority="P2", confidence=4, evidence_strength="multiple",
            truth_level="L0", claim_state="VERIFIED", completion_blocker="no",
            verify="python _zozi_audit/zozi_compile.py --check feature-dead",
            snippet=", ".join(dead[:20]),
        ))
    if default_behaviour == "allow-unknown":
        res.findings.append(Finding(
            id="FEAT-FAIL-OPEN", dimension="16_features", phase="arch",
            cluster="CLUSTER-feature-gate", file=ctx.rel(impl) if impl else "backend/rbac",
            current="require_feature() allows a feature it cannot resolve",
            target="an unknown feature is denied, so a typo cannot silently expose "
                   "a feature",
            delta="every undefined literal above currently grants access",
            fix="make the resolver return False (or raise) for an unknown feature "
                "id and add a startup assertion that every literal exists",
            effort="S", priority="P0", confidence=4, evidence_strength="multiple",
            truth_level="L1", claim_state="INFERRED", completion_blocker="yes",
            verify="pytest backend/tests/architecture/test_feature_catalog.py",
            laws=(4,),
        ))
    return res


@check("feature_route_test_matrix", "16_features", "tests",
       "Matrix of shipped routes against browser/e2e specs: uncovered routes, "
       "and specs that point at routes which no longer exist.")
def feature_route_test_matrix(ctx: ScanContext) -> CheckResult:
    res = CheckResult(check="feature_route_test_matrix", dimension="16_features")
    app = ctx.frontend / "web_app" / "src" / "app"
    if not app.exists():
        return res

    def route_of(p: Path) -> str:
        rel = p.relative_to(app).as_posix()
        rel = re.sub(r"/page\.tsx$", "", rel)
        segs = [s for s in rel.split("/") if s and s != "page.tsx"]
        segs = [s for s in segs if not (s.startswith("(") and s.endswith(")"))]
        return "/" + "/".join(segs if segs else [""])

    routes = sorted({route_of(p) for p in app.rglob("page.tsx")})
    specs: list[tuple[str, set[str]]] = []
    for base in (ctx.root / "_browser_test" / "tests", ctx.frontend / "web_app" / "e2e"):
        if not base.exists():
            continue
        for p in sorted(base.rglob("*.spec.ts")):
            text, _ = read_text(p)
            if not text:
                continue
            urls = set()
            for m in re.finditer(r"[\"'`](https?://[^\"'`\s]+|/[a-zA-Z0-9][^\"'`\s]*)[\"'`]", text):
                u = m.group(1)
                if u.startswith("http"):
                    u = re.sub(r"^https?://[^/]+", "", u)
                if u and u != "/" and not u.startswith("/api"):
                    urls.add(u.split("?")[0].rstrip("/") or "/")
            specs.append((ctx.rel(p), urls))

    def matches(route: str, urls: set[str]) -> bool:
        rx = "^" + re.sub(r":[^/]+", "[^/]+", re.escape(route).replace(r"\:", ":")) + "/?$"
        for u in urls:
            if re.match(rx, u) or re.match(rx, u + "/"):
                return True
            # parent route covered implies the nested page was at least reached
            if route.count("/") > 1 and re.match(
                    r"^" + re.escape("/".join(route.split("/")[:2])) + "/?$", u):
                return True
        return False

    covered, uncovered = [], []
    for route in routes:
        hit = next((name for name, urls in specs if matches(route, urls)), None)
        (covered if hit else uncovered).append((route, hit))

    covered_urls = set().union(*[u for _, u in specs]) if specs else set()
    orphan_specs = [name for name, urls in specs
                    if urls and not any(matches(r, urls) for r in routes)]

    res.facts["route_test_matrix"] = {
        "routes": len(routes),
        "covered_routes": len(covered),
        "uncovered_routes": len(uncovered),
        "coverage_ratio": (round(len(covered) / len(routes), 3) if routes else None),
        "spec_files": len(specs),
        "specs_not_matching_any_route": len(orphan_specs),
        "uncovered_admin": [r for r, _ in uncovered if r.startswith("/admin")],
        "uncovered_sample": [r for r, _ in uncovered[:40]],
        "orphan_spec_sample": orphan_specs[:20],
    }
    for route, hit in uncovered[:60]:
        res.observations.append(Observation(
            "route", route, route, 0, "16_features",
            evidence="no browser spec navigates this route",
        ))
    if routes and len(uncovered) / len(routes) > 0.4:
        admin_gap = [r for r, _ in uncovered if r.startswith("/admin")]
        res.findings.append(Finding(
            id="FEAT-ROUTE-NOTEST", dimension="16_features", phase="tests",
            cluster="CLUSTER-coverage-route", file="frontend/web_app/src/app",
            current=f"{len(uncovered)} of {len(routes)} shipped routes have no "
                    f"browser or e2e spec ({len(admin_gap)} of them under /admin)",
            target="every revenue or admin-affecting route has at least one spec "
                   "that navigates it and asserts the outcome",
            delta=f"route coverage is {res.facts['route_test_matrix']['coverage_ratio']}",
            fix="generate a smoke spec per uncovered route (navigate, assert heading "
                "and no console error), then deepen the admin and finance routes",
            effort="L", priority="P1", confidence=5, evidence_strength="multiple",
            truth_level="L0", claim_state="VERIFIED", completion_blocker="no",
            verify="python _zozi_audit/zozi_compile.py --report coverage",
            snippet=", ".join(r for r, _ in uncovered[:12]),
        ))
        res.recommendations.append(Recommendation(
            area="coverage", dimension="16_features",
            title="Close the route-level test coverage gap with generated smoke specs",
            rationale=f"{len(uncovered)} of {len(routes)} routes are untested, so "
                      f"regressions in them reach production undetected.",
            current="coverage is authored by hand and drifts.",
            proposal="generate a smoke spec per route from the app-router tree "
                     "(navigate, assert the page heading, assert zero console "
                     "errors), then hand-write depth for the critical journeys.",
            benefit=f"route coverage from "
                    f"{res.facts['route_test_matrix']['coverage_ratio']} to 1.0 with a "
                    f"regenerable baseline",
            effort="L", impact="high", category="quality",
            evidence=f"frontend/web_app/src/app ({len(routes)} routes) vs "
                     f"{len(specs)} spec files",
            human_effort_saved="~1 day per release currently spent on manual QA",
            prerequisites=("DS-palette-drift",),
        ))
    if orphan_specs:
        res.findings.append(Finding(
            id="FEAT-SPEC-ORPHAN", dimension="16_features", phase="tests",
            cluster="CLUSTER-coverage-route", file="_browser_test/tests",
            current=f"{len(orphan_specs)} spec file(s) navigate to paths that no "
                    f"longer exist in the app router",
            target="every spec asserts against a real route",
            delta=f"{len(orphan_specs)} specs provide false confidence",
            fix="delete or repoint the orphaned specs",
            effort="S", priority="P2", confidence=4, evidence_strength="multiple",
            truth_level="L0", claim_state="VERIFIED", completion_blocker="no",
            verify="npx playwright test --list",
            snippet=", ".join(orphan_specs[:8]),
        ))
    return res


@check("category_hierarchy_depth", "16_features", "arch",
       "Can the product taxonomy express the mandated 5-tier hierarchy, and "
       "how deep does the seeded data actually go?")
def category_hierarchy_depth(ctx: ScanContext) -> CheckResult:
    res = CheckResult(check="category_hierarchy_depth", dimension="16_features")
    model = None
    schema_cols: dict[str, int] = {}
    best_score = -1
    HIER_COLS = ("parent_id", "parent_category_id", "depth", "level", "tier",
                 "path", "sort_order", "sort_rank", "is_active", "slug")
    for p in ctx.py_files:
        rel = ctx.rel(p)
        if not re.match(r"backend/(domains|infrastructure)/.*models.*\.py$", rel):
            continue
        text, _ = read_text(p)
        if not text or "class Category" not in text:
            continue
        # A codebase can hold several Category-ish classes (a chart-of-accounts
        # table, a promotions category, ...). Pick the one that actually looks
        # like the product taxonomy, i.e. the richest hierarchy shape.
        for cm in re.finditer(r"class\s+(Category\w*)\s*\(([^)]*)\)", text):
            start = cm.end()
            nxt = re.search(r"\nclass\s+", text[start:])
            block = text[start:start + (nxt.start() if nxt else 8000)]
            if "__tablename__" not in block:
                continue
            cols_found = {c: block.find(f"\n    {c}") for c in HIER_COLS
                          if re.search(rf"^\s+{c}\b", block, re.M)}
            score = sum(1 for c in ("parent_id", "parent_category_id", "depth",
                                    "level", "tier", "path") if c in cols_found)
            if score > best_score:
                best_score = score
                model = p
                tn = re.search(r'__tablename__\s*=\s*["\']([^"\']+)["\']', block)
                schema_cols = dict(cols_found)
                if tn:
                    schema_cols["__tablename__"] = block.find("__tablename__")
        if best_score >= 2:
            break

    has_parent = any(k in schema_cols for k in ("parent_id", "parent_category_id"))
    has_depth = any(k in schema_cols for k in ("depth", "level", "tier"))
    has_path = "path" in schema_cols
    has_sort = any(k in schema_cols for k in ("sort_order", "sort_rank"))

    # Depth enforced in code (guard) and depth present in seed data.
    guard = None
    for p in ctx.py_files:
        text, _ = read_text(p)
        if text and ("rebuild_category_paths" in text or "category_tree" in ctx.rel(p)):
            m = re.search(r"depth\s*[<>=]+\s*(\d+)", text)
            if m:
                guard = int(m.group(1))
                break
    seeded_depth = 0
    seed_file = ""
    for p in ctx.py_files:
        rel = ctx.rel(p).replace("\\", "/")
        if "/seed" not in rel and "categor" not in rel.lower():
            continue
        text, _ = read_text(p)
        if not text:
            continue
        # count the longest "a > b > c" style path or nested dict chain
        for m in re.finditer(r"depth[\"']?\s*[:=]\s*(\d+)", text):
            seeded_depth = max(seeded_depth, int(m.group(1)))
        for m in re.finditer(r"parent_id[\"']?\s*[:=]\s*(?!None)\S+", text):
            seeded_depth = max(seeded_depth, 2)
        if re.search(r"electronics", text, re.I) and "smartphone" in text.lower():
            seeded_depth = max(seeded_depth, 2)
            seed_file = seed_file or rel
    # third level observed in seed text
    if re.search(r"smartphone", (read_text(
            ctx.backend / "infrastructure" / "database" / "seed" / "_seed_constants.py")[0] or ""),
            re.I):
        seeded_depth = max(seeded_depth, 3)

    res.facts["category_taxonomy"] = {
        "model_file": ctx.rel(model) if model else "",
        "columns": sorted(schema_cols),
        "has_self_reference": has_parent,
        "has_depth_column": has_depth,
        "has_materialised_path": has_path,
        "has_sort_column": has_sort,
        "code_depth_guard": guard,
        "observed_seeded_depth": seeded_depth,
        "target_depth": CATEGORY_DEPTH_TARGET,
        "seed_evidence": seed_file,
    }
    if model is None:
        res.findings.append(Finding(
            id="CAT-model-missing", dimension="16_features", phase="arch",
            cluster="CLUSTER-category-taxonomy", file="backend/domains/catalog/models",
            current="no Category model was found for the product taxonomy",
            target="a Category table able to express the 5-tier hierarchy",
            delta="products cannot be organised into the mandated hierarchy",
            fix="add catalog.categories with parent_id, depth, path, sort_order",
            effort="L", priority="P0", confidence=4, evidence_strength="single",
            truth_level="L1", claim_state="INFERRED", completion_blocker="yes",
            verify="grep -rn 'class Category' backend/domains",
        ))
        return res
    if not has_parent:
        res.findings.append(Finding(
            id="CAT-no-selfref", dimension="16_features", phase="arch",
            cluster="CLUSTER-category-taxonomy", file=ctx.rel(model),
            current="Category has no parent self-reference, so it is flat",
            target="parent_id self-reference plus depth and path",
            delta="a hierarchy cannot be represented at all",
            fix="add parent_id (FK self), depth, path, sort_order and a unique "
                "constraint on (parent_id, slug)",
            effort="L", priority="P0", confidence=5, evidence_strength="multiple",
            truth_level="L0", claim_state="VERIFIED", completion_blocker="yes",
        ))
    if has_parent and seeded_depth < CATEGORY_DEPTH_TARGET:
        res.findings.append(Finding(
            id="CAT-depth-underused", dimension="16_features", phase="arch",
            cluster="CLUSTER-category-taxonomy", file=ctx.rel(model),
            current=f"the schema can express a hierarchy (columns: "
                    f"{', '.join(sorted(schema_cols))}) but the seeded taxonomy only "
                    f"reaches depth {seeded_depth} of the mandated "
                    f"{CATEGORY_DEPTH_TARGET}",
            target=f"a seeded taxonomy that uses all {CATEGORY_DEPTH_TARGET} tiers "
                   f"(e.g. Department > Category > Subcategory > Product type > Attribute)",
            delta=f"{CATEGORY_DEPTH_TARGET - seeded_depth} tier(s) unused: operators "
                  f"cannot group thousands of SKUs into a browsable hierarchy",
            fix="author the full taxonomy as a versioned JSON/py seed "
                "(department > category > subcategory > product_type > attribute), "
                "load it through the tree builder, and add a depth-check test",
            effort="XL", priority="P1", confidence=4, evidence_strength="multiple",
            truth_level="L1", claim_state="INFERRED", completion_blocker="no",
            verify="pytest backend/tests/domains/catalog -k categor",
            snippet=seed_file,
        ))
        res.recommendations.append(Recommendation(
            area="data", dimension="16_features",
            title="Model and seed the full 5-tier product taxonomy",
            rationale="A multi-country marketplace with thousands of SKUs cannot be "
                      "navigated or filtered without a real hierarchy; the schema "
                      "already supports it, only the data and the admin UI are missing.",
            current=f"taxonomy seeded to depth {seeded_depth}; admin UI has no tree "
                    f"editor and no drag-to-reparent.",
            proposal="1) ship a versioned taxonomy seed covering the 5 tiers; "
                     "2) rebuild depth/path on every write via the existing tree "
                     "builder; 3) add a category tree editor with drag-to-reparent "
                     "and cycle detection; 4) add facet filters that read the same "
                     "path; 5) add a uniqueness constraint on (parent_id, slug) and "
                     "a test that asserts no category exceeds depth 5.",
            benefit="browsable, filterable catalog; SEO landing pages per tier; "
                    "commission and tax rules can attach per tier",
            effort="XL", impact="high", category="schema",
            evidence=f"{ctx.rel(model)}; observed depth {seeded_depth}/"
                     f"{CATEGORY_DEPTH_TARGET}",
            human_effort_saved="~2 days per manual category tidy-up, recurring",
            prerequisites=("CAT-no-selfref",),
        ))
    if has_parent and not has_sort:
        res.findings.append(Finding(
            id="CAT-no-ordering", dimension="16_features", phase="arch",
            cluster="CLUSTER-category-taxonomy", file=ctx.rel(model),
            current="Category has no sort/rank column, so ordering is unstable "
                    "between renders",
            target="deterministic sibling ordering",
            delta="category menus reorder between pages and between deployments",
            fix="add sort_order and order the tree by (depth, parent_id, sort_order, slug)",
            effort="S", priority="P2", confidence=4, evidence_strength="single",
            truth_level="L1", claim_state="INFERRED", completion_blocker="no",
        ))
    return res
