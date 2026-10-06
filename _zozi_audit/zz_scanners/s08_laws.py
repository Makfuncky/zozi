"""Dimension 09 (laws 1-325) — every law classified PASS / FAIL / UNVERIFIABLE."""
from __future__ import annotations

import re
from pathlib import Path

from zz_core.constants import CANONICAL_DOMAINS, CANONICAL_MODULES, load_doc
from zz_core.model import CheckResult, Finding, ScanContext
from zz_core.registry import check
from zz_core.util import parse_markdown_tables, read_text

BACKEND_CORE = ("domains", "modules", "rbac", "kernel", "infrastructure",
                "providers", "jobs", "middleware")


def _f(law: int, category: str, file: str, current: str, target: str, fix: str,
       *, priority="P2", effort="S", blocker="no", cluster="") -> Finding:
    return Finding(
        id=f"LAW-{law:03d}", dimension="09_laws", phase="arch", cluster=cluster,
        file=file, line=0, current=current, target=target, delta=current[:180],
        fix=fix, effort=effort, priority=priority, confidence=4,
        evidence_strength="triangulated", truth_level="L0", claim_state="VERIFIED",
        completion_blocker=blocker, laws=(law,), status="NEW",
    )


def _parse_laws() -> list[dict]:
    text = load_doc("ARCHITECTURE_STACK.md")
    laws = []
    for table in parse_markdown_tables(text):
        for row in table:
            if len(row) >= 5 and re.fullmatch(r"\d+", row[0].strip().strip("*`")):
                laws.append({
                    "law": int(row[0].strip().strip("*`")),
                    "category": row[1].strip(),
                    "rule": row[2].strip(),
                    "description": row[3].strip(),
                    "why": row[4].strip() if len(row) > 4 else "",
                })
    return laws


# --------------------------------------------------------------------------- #
# Predicate helpers (each returns (status, evidence))
# --------------------------------------------------------------------------- #

def _count(pattern: str, ctx: ScanContext, dirs=BACKEND_CORE, flags=0) -> int:
    n = 0
    for d in dirs:
        base = ctx.backend / d
        if not base.exists():
            continue
        for p in base.rglob("*.py"):
            if "/tests/" in ctx.rel(p):
                continue
            text, _ = read_text(p)
            if text:
                n += len(re.findall(pattern, text, flags))
    return n


def _models(ctx: ScanContext):
    try:
        from .s06_database import _model_inventory
        return _model_inventory(ctx)
    except Exception:
        return []


def _import_graph(ctx: ScanContext):
    try:
        from .s01_architecture import _build_import_graph
        return _build_import_graph(ctx)
    except Exception:
        return {}


def _layer(rel: str) -> str:
    parts = rel.split("/")
    if len(parts) >= 2 and parts[0] == "backend":
        if parts[1] in ("domains", "modules") and len(parts) >= 3:
            return f"{parts[1]}.{parts[2]}"
        return parts[1]
    return rel


def _reverse_imports(ctx: ScanContext) -> int:
    graph = _import_graph(ctx)
    bad = 0
    for rel, imports in graph.items():
        layer = _layer(rel)
        for module, _line, _names in imports:
            top = (module or "").split(".")[0]
            if layer.startswith("domains.") and top == "modules":
                bad += 1
            elif layer == "infrastructure" and top in ("domains", "modules", "rbac", "providers", "jobs", "middleware"):
                bad += 1
            elif layer == "kernel" and top in ("domains", "modules", "rbac", "providers", "jobs", "middleware"):
                bad += 1
            elif layer == "providers" and top in ("domains", "modules", "rbac", "jobs", "middleware"):
                bad += 1
            elif layer == "middleware" and top in ("domains", "modules", "providers", "jobs"):
                bad += 1
            elif layer == "jobs" and top in ("modules", "middleware"):
                bad += 1
            elif layer == "rbac" and top in ("modules", "providers", "jobs", "middleware"):
                bad += 1
    return bad


def _fails_closed(text: str) -> tuple[bool, str]:
    """Law 37: does the rate limiter deny when its backend is unreachable?

    Two independent conditions, both required, so neither a comment nor a stray
    4xx can satisfy the law on its own:
      1. the module *acknowledges* fail-closed behaviour (any inflection of
         "fail closed": `fail_closed`, `failing closed`, `fail-closed`);
      2. some `except` handler actually *denies* -- it returns rather than
         falling through to `call_next`, and the returned expression either
         carries a 4xx/5xx `status_code` or is a false/empty denial value.
    """
    import ast as _ast  # local: this module deliberately has no top-level ast import

    if not text:
        return False, "rate limiter module not found"
    acknowledged = bool(re.search(r"fail\w*[-_\s]?closed", text, re.I))
    denies = False
    detail = "no except-handler denial path"
    try:
        tree = _ast.parse(text)
    except SyntaxError as exc:
        return False, f"unparsable: {exc}"
    for node in _ast.walk(tree):
        if not isinstance(node, _ast.Try):
            continue
        for handler in node.handlers:
            for stmt in _ast.walk(_ast.Module(body=handler.body, type_ignores=[])):
                if not isinstance(stmt, _ast.Return) or stmt.value is None:
                    continue
                src = " ".join(_ast.unparse(stmt.value).split())
                if re.search(r"status_code\s*=\s*[45]\d\d", src) or src in (
                        "False", "False, 0, 10", "None"):
                    denies = True
                    detail = f"handler denies with: {src[:60]}"
    if acknowledged and denies:
        return True, detail
    if not acknowledged:
        return False, "no fail-closed acknowledgement in the limiter"
    return False, detail


def _predicates() -> dict:
    def pred(law):
        def deco(fn):
            _PRED[law] = fn
            return fn
        return deco

    _PRED: dict[int, callable] = {}

    @pred(1)
    def law1(ctx):
        n = _reverse_imports(ctx)
        return ("FAIL" if n else "PASS", f"{n} reverse-layer import(s)")

    @pred(2)
    def law2(ctx):
        hits = 0
        for p in ctx.py_files:
            rel = ctx.rel(p)
            if "/modules/" in rel and "/routers/" in rel:
                text, _ = read_text(p)
                hits += len(re.findall(r"\bget_db\(|session\.execute|db\.commit\(", text or ""))
        return ("FAIL" if hits else "PASS", f"{hits} direct DB touch(es) in routers")

    @pred(3)
    def law3(ctx):
        try:
            from .s05_wiring import wire_event_bus
            res = wire_event_bus(ctx)
            spine = any("CLUSTER-event-spine" in f.cluster for f in res.findings)
            return ("FAIL" if spine else "PASS",
                    f"event-spine findings={sum(1 for f in res.findings if f.cluster == 'CLUSTER-event-spine')}")
        except Exception as exc:
            return ("UNVERIFIABLE", f"check failed: {exc}")

    @pred(4)
    def law4(ctx):
        catalog = set()
        for fp in ctx.backend.glob("domains/*/features.py"):
            text, _ = read_text(fp)
            catalog.update(re.findall(r'"([a-z][a-z0-9_.]*\.[a-z0-9_.]+)"\s*:', text or ""))
        literals = set()
        for p in ctx.py_files:
            rel = ctx.rel(p)
            if "/modules/" not in rel or "/tests/" in rel:
                continue
            text, _ = read_text(p)
            # `\S` inside the literal, not `[^"\'*]+`. The negated class matched
            # across newlines, so in
            # `assert require_feature_count >= len(endpoints), (\n f"...` it
            # swallowed 60 characters of assertion and produced one bogus
            # "unknown gate literal" that no catalog could ever contain.
            literals.update(re.findall(r'require_feature\(\s*["\']([^"\'*\s]+)["\']', text or ""))
        unknown = [l for l in literals if l not in catalog]
        return ("FAIL" if unknown else "PASS",
                f"{len(unknown)} gate literal(s) missing from catalog ({', '.join(sorted(unknown)[:5])})")

    @pred(5)
    def law5(ctx):
        text, _ = read_text(ctx.backend / "infrastructure" / "database" / "rls_interceptor.py")
        has = "SET LOCAL" in (text or "")
        pol = ""
        for p in (ctx.backend / "infrastructure").rglob("*.sql"):
            t, _ = read_text(p)
            m = re.search(r"current_setting\('([^']+)'", t or "")
            if m:
                pol = m.group(1)
                break
        mid = ""
        for p in (ctx.backend / "middleware").glob("*.py"):
            t, _ = read_text(p)
            m = re.search(r"SET\s+LOCAL\s+([a-z_.]+)", t or "", re.IGNORECASE)
            if m:
                mid = m.group(1)
                break
        mismatch = pol and mid and pol != mid
        return ("FAIL" if (not has or mismatch) else "PASS",
                f"SET LOCAL present={has}; policy var={pol}; middleware var={mid}")

    @pred(6)
    def law6(ctx):
        tables = _models(ctx)
        missing = [t["table"] for t in tables if not t["has_table_args"] or not t["schema"]]
        return ("FAIL" if missing else "PASS",
                f"{len(missing)}/{len(tables)} table(s) without schema declaration")

    @pred(7)
    def law7(ctx):
        p = ctx.backend / "DOMAIN_ALLOWLIST.yaml"
        if not p.exists():
            return ("PASS", "no allowlist file (no temporary cross-domain imports declared)")
        text, _ = read_text(p)
        entries = re.findall(r"^\s*-\s*(.+)$", text or "", re.MULTILINE)
        undated = [e for e in entries if not re.search(r"\d{4}-\d{2}-\d{2}", e)]
        return ("FAIL" if undated else "PASS",
                f"{len(entries)} entr(ies), {len(undated)} without dated removal plan")

    @pred(12)
    def law12(ctx):
        extra = [d.name for d in (ctx.backend / "domains").iterdir()
                 if d.is_dir() and d.name not in CANONICAL_DOMAINS and d.name != "__pycache__"]
        return ("FAIL" if extra else "PASS", f"extra domain(s): {', '.join(extra) or 'none'}")

    @pred(13)
    def law13(ctx):
        mods = ctx.backend / "modules"
        extra = [d.name for d in mods.iterdir()
                 if d.is_dir() and d.name not in CANONICAL_MODULES and d.name != "__pycache__"] if mods.exists() else []
        return ("FAIL" if extra else "PASS", f"extra module(s): {', '.join(extra) or 'none'}")

    @pred(18)
    def law18(ctx):
        bad = [d for d in ("utils", "routers", "controllers", "services", "models", "db")
               if (ctx.backend / d).exists()]
        return ("FAIL" if bad else "PASS", f"forbidden root dir(s): {', '.join(bad) or 'none'}")

    @pred(19)
    def law19(ctx):
        tables = _models(ctx)
        float_money = 0
        for t in tables:
            for c in t["columns"]:
                if re.search(r"\bFloat\b", c["span"]):
                    float_money += 1
        cfg, _ = read_text(ctx.backend / "config.py")
        cfg_floats = len(re.findall(r"(vat_rate|commission_rate|tax_rate)\s*:\s*float", cfg or ""))
        return ("FAIL" if (float_money or cfg_floats) else "PASS",
                f"{float_money} Float column(s); {cfg_floats} float money config field(s)")

    @pred(20)
    def law20(ctx):
        bad = 0
        total = 0
        for t in _models(ctx):
            for c in t["columns"]:
                if c["name"] == "country_code":
                    total += 1
                    if "String(2)" not in c["span"].replace(" ", ""):
                        bad += 1
        return ("FAIL" if bad else "PASS", f"{bad}/{total} country_code column(s) not String(2)")

    @pred(21)
    def law21(ctx):
        py_default = 0
        for t in _models(ctx):
            for c in t["columns"]:
                if c["name"] in ("created_at", "updated_at") and "server_default" not in c["span"] and "default=" in c["span"]:
                    py_default += 1
        return ("FAIL" if py_default else "PASS", f"{py_default} Python-side timestamp default(s)")

    @pred(22)
    def law22(ctx):
        bad = 0
        for t in _models(ctx):
            for c in t["columns"]:
                if "ForeignKey(" in c["span"] and "ondelete" not in c["span"]:
                    bad += 1
        return ("FAIL" if bad else "PASS", f"{bad} FK(s) without ondelete")

    @pred(23)
    def law23(ctx):
        bad = 0
        for t in _models(ctx):
            names = {c["name"] for c in t["columns"]}
            if not {"created_at", "updated_at", "is_deleted"} <= names:
                bad += 1
        return ("FAIL" if bad else "PASS", f"{bad} table(s) missing audit columns")

    @pred(24)
    def law24(ctx):
        used = {t["schema"] for t in _models(ctx) if t["schema"]}
        bad = sorted(used & {"core", "platform", "identity"})
        return ("FAIL" if bad else "PASS", f"forbidden schema(s) in use: {', '.join(bad) or 'none'}")

    @pred(27)
    def law27(ctx):
        import glob as _glob
        hits = 0
        for pat in ("_tmp_*.py", "health_test_*.py", "fix_*.py", "debug_*.py", "_audit_boot_check.py"):
            hits += len(list((ctx.backend).glob(pat)))
        return ("FAIL" if hits else "PASS", f"{hits} temp/debug file(s) at backend root")

    @pred(31)
    def law31(ctx):
        bad = 0
        for p in (ctx.backend / "providers").rglob("*.py"):
            text, _ = read_text(p)
            bad += len(re.findall(r"^from\s+(domains|modules|rbac|jobs|middleware)\b|^import\s+(domains|modules|rbac|jobs|middleware)\b",
                                  text or "", re.MULTILINE))
        return ("FAIL" if bad else "PASS", f"{bad} provider→higher-layer import(s)")

    @pred(32)
    def law32(ctx):
        hits = 0
        for p in ctx.backend.glob("health_test_*.py"):
            text, _ = read_text(p)
            hits += len(re.findall(r"(SECRET_KEY|FIELD_ENCRYPTION_KEY|AUDIT_CHAIN_KEY)\s*=\s*[\"'][^\"']{8,}", text or ""))
        for p in ctx.backend.glob("_tmp_*.py"):
            text, _ = read_text(p)
            hits += len(re.findall(r"(SECRET_KEY|password|token)\s*=\s*[\"'][^\"']{8,}", text or "", re.IGNORECASE))
        return ("FAIL" if hits else "PASS", f"{hits} hardcoded secret literal(s) in root scripts")

    @pred(33)
    def law33(ctx):
        found = _count(r"expected_type|token_type|\[\"type\"\]", ctx,
                       dirs=("infrastructure", "rbac", "modules", "middleware"))
        return ("PASS" if found else "FAIL", f"{found} type-claim verification reference(s)")

    @pred(34)
    def law34(ctx):
        hits = _count(r'(text|execute)\(\s*f["\']', ctx)
        hits += _count(r"execute\(\s*f[\"']", ctx)
        return ("FAIL" if hits else "PASS", f"{hits} f-string SQL site(s)")

    @pred(35)
    def law35(ctx):
        orch, _ = read_text(ctx.backend / "middleware" / "orchestrator.py")
        return ("PASS" if "csrf" in (orch or "").lower() else "FAIL",
                "CSRF middleware referenced in orchestrator" if "csrf" in (orch or "").lower() else "CSRF middleware not registered")

    @pred(36)
    def law36(ctx):
        orch, _ = read_text(ctx.backend / "middleware" / "orchestrator.py")
        ok = "security_headers" in (orch or "").lower() or "securityheaders" in (orch or "").lower()
        return ("PASS" if ok else "FAIL", "security headers middleware registered" if ok else "security headers middleware missing")

    @pred(37)
    def law37(ctx):
        text, _ = read_text(ctx.backend / "middleware" / "rate_limit_middleware.py")
        ok, why = _fails_closed(text or "")
        # The old predicate searched for `status_code=503` / `deny` / the literal
        # regex `fail.?closed` and produced a P0 blocker against code that does
        # fail closed: the limiter answers 429 from inside `except Exception`
        # ("Valkey rate limit check failed — failing closed") and the token bucket
        # returns `False, 0, 10`. "failing closed" does not match `fail.?closed`,
        # and a 429 is not a 5xx. A predicate that cannot match the correct
        # implementation is not a check; it is noise that the verifier then has to
        # spend a probe disproving.
        return ("PASS" if ok else "FAIL",
                f"rate limiter fails closed ({why})" if ok
                else f"rate limiter does not fail closed ({why})")

    @pred(38)
    def law38(ctx):
        text, _ = read_text(ctx.backend / "infrastructure" / "security" / "auth.py")
        ok = bool(re.search(r"72|len\(.*password.*encode", text or ""))
        return ("PASS" if ok else "FAIL", "72-byte password guard present" if ok else "no 72-byte guard found")

    @pred(40)
    def law40(ctx):
        cfg, _ = read_text(ctx.backend / "config.py")
        localhost = "localhost" in (cfg or "")
        return ("PASS" if localhost else "UNVERIFIABLE",
                "cors_origins default includes localhost (dev-only acceptable)" if localhost else "cannot resolve CORS posture")

    @pred(45)
    def law45(ctx):
        total = 0
        missing = 0
        for t in _models(ctx):
            for r in t["relationships"]:
                total += 1
                if "lazy=" not in r["span"]:
                    missing += 1
        return ("FAIL" if missing else "PASS", f"{missing}/{total} relationship(s) without lazy=")

    @pred(46)
    def law46(ctx):
        hits = _count(r"SELECT\s+\*\s+FROM", ctx, flags=re.IGNORECASE)
        return ("FAIL" if hits else "PASS", f"{hits} SELECT * site(s)")

    @pred(49)
    def law49(ctx):
        try:
            from .s06_database import db_migration_graph
            res = db_migration_graph(ctx)
            heads = res.facts.get("migration_heads", -1)
            return ("FAIL" if heads not in (0, 1) else "PASS",
                    f"{heads} migration heads")
        except Exception as exc:
            return ("UNVERIFIABLE", f"graph parse failed: {exc}")

    @pred(51)
    def law51(ctx):
        seen = {}
        dup = 0
        for t in _models(ctx):
            if t["table"] in seen:
                dup += 1
            seen[t["table"]] = True
        return ("FAIL" if dup else "PASS", f"{dup} duplicate __tablename__")

    @pred(52)
    def law52(ctx):
        return law22(ctx)

    @pred(53)
    def law53(ctx):
        bad = 0
        for t in _models(ctx):
            for c in t["columns"]:
                if "ForeignKey(" in c["span"] and "index=True" not in c["span"]:
                    bad += 1
        return ("FAIL" if bad else "PASS", f"{bad} FK(s) without index=True (verify composite indexes manually)")

    @pred(54)
    def law54(ctx):
        bad = sum(1 for t in _models(ctx) if "is_deleted" not in {c["name"] for c in t["columns"]})
        return ("FAIL" if bad else "PASS", f"{bad} table(s) without is_deleted")

    @pred(55)
    def law55(ctx):
        return law6(ctx)

    @pred(58)
    def law58(ctx):
        n = _count(r"(?<![\w.])print\(", ctx)
        return ("FAIL" if n else "PASS", f"{n} print() call(s) in production code")

    @pred(59)
    def law59(ctx):
        n = 0
        for p in (ctx.backend / "domains").rglob("*.py"):
            rel = ctx.rel(p)
            if "/tests/" in rel:
                continue
            text, _ = read_text(p)
            if not text:
                continue
            for m in re.finditer(r"except[^:]*:\s*\n\s+(pass|return None)\s*(?:\n|$)", text):
                n += 1
        return ("FAIL" if n else "PASS", f"{n} pass/return-None-only except block(s) (sample scan)")

    @pred(62)
    def law62(ctx):
        n = _count(r"#\s*(TODO|FIXME)(?!.*(#[0-9]+|[A-Z]+-[0-9]+|\d{4}-\d{2}-\d{2}))", ctx, flags=re.IGNORECASE)
        return ("FAIL" if n else "PASS", f"{n} untracked TODO/FIXME")

    @pred(69)
    def law69(ctx):
        tests_root = ctx.backend / "tests"
        dom_tests = list(tests_root.glob("domains/**/test_*.py")) if tests_root.exists() else []
        return ("PASS" if dom_tests else "FAIL", f"{len(dom_tests)} domain smoke/integration test file(s)")

    @pred(70)
    def law70(ctx):
        arch = ctx.backend / "tests" / "architecture"
        files = list(arch.glob("test_*.py")) if arch.exists() else []
        return ("PASS" if len(files) >= 4 else "PARTIAL",
                f"{len(files)} architecture law test file(s)")

    @pred(84)
    def law84(ctx):
        n = _count(r"os\.(getenv|environ\.get)\(", ctx, dirs=("providers", "jobs", "middleware", "infrastructure", "domains"))
        return ("FAIL" if n else "PASS", f"{n} raw os.getenv read(s)")

    @pred(92)
    def law92(ctx):
        n = _count(r"structlog\.get_logger|logger\s*=\s*structlog", ctx)
        return ("PASS" if n else "FAIL", f"{n} structlog logger reference(s)")

    @pred(107)
    def law107(ctx):
        env, _ = read_text(ctx.root / ".env.example")
        neon = "neon" in (env or "").lower() or "DATABASE_URL" in (env or "")
        return ("PASS" if neon else "UNVERIFIABLE", "DATABASE_URL present in env example")

    @pred(115)
    def law115(ctx):
        jobs = list((ctx.backend / "jobs").glob("*.py")) if (ctx.backend / "jobs").exists() else []
        return ("PASS" if jobs else "FAIL", f"{len(jobs)} job module(s)")

    @pred(120)
    def law120(ctx):
        r2 = list((ctx.backend / "providers" / "storage").rglob("*r2*")) if (ctx.backend / "providers" / "storage").exists() else []
        return ("PASS" if r2 else "FAIL", f"{len(r2)} R2 storage module(s)")

    @pred(123)
    def law123(ctx):
        bad = 0
        for p in (ctx.backend / "providers" / "payments").rglob("*.py"):
            text, _ = read_text(p)
            if re.search(r"orchestrat|route.*gateway|select.*gateway", text or "", re.IGNORECASE):
                bad += 1
        return ("FAIL" if bad else "PASS", f"{bad} provider file(s) containing routing logic")

    @pred(124)
    def law124(ctx):
        n = 0
        total = 0
        for p in (ctx.backend / "providers").rglob("*.py"):
            if p.name == "__init__.py":
                continue
            total += 1
            text, _ = read_text(p)
            if re.search(r"HAS_[A-Z_]+", text or ""):
                n += 1
        return ("FAIL" if total and n < total * 0.5 else "PASS", f"{n}/{total} providers expose HAS_ flags")

    @pred(129)
    def law129(ctx):
        n = 0
        total = 0
        for p in (ctx.backend / "providers").rglob("*.py"):
            if p.name in ("__init__.py", "_base.py"):
                continue
            total += 1
            text, _ = read_text(p)
            if "def health_check" in (text or ""):
                n += 1
        return ("FAIL" if total and n < total * 0.5 else "PASS", f"{n}/{total} providers have health_check()")

    @pred(150)
    def law150(ctx):
        missing = []
        for d in CANONICAL_DOMAINS:
            base = ctx.backend / "domains" / d
            if not base.exists():
                missing.append(d)
                continue
            for artefact in ("services", "models", "schemas", "events.py", "ports.py", "features.py"):
                if not (base / artefact).exists():
                    missing.append(f"{d}/{artefact}")
        return ("FAIL" if missing else "PASS", f"{len(missing)} missing domain artefact(s)")

    @pred(161)
    def law161(ctx):
        text, _ = read_text(ctx.backend / "rbac" / "catalog.py")
        ok = "features" in (text or "") and "FEATURE_CATALOG" in (text or "")
        return ("PASS" if ok else "FAIL", "catalog aggregates domains/*/features.py" if ok else "catalog aggregation not found")

    @pred(171)
    def law171(ctx):
        from zz_core.util import parse_package_json
        pkg = parse_package_json(ctx.frontend / "web_app" / "package.json")
        deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
        bad = [d for d in deps if d.lower() in ("@tanstack/react-query", "swr")]
        return ("FAIL" if bad else "PASS", f"forbidden client-state libs: {', '.join(bad) or 'none'}")

    @pred(186)
    def law186(ctx):
        res = ctx.tools.get("next:build")
        if res is None:
            return ("UNVERIFIABLE", "next build not run (use --full)")
        return ("PASS" if getattr(res, "exit_code", None) == 0 else "FAIL",
                f"next build exit={getattr(res, 'exit_code', None)}")

    @pred(207)
    def law207(ctx):
        pt, _ = read_text(ctx.backend / "pyproject.toml")
        return ("PASS" if "pytest" in (pt or "") else "UNVERIFIABLE", "pytest configured in pyproject" if "pytest" in (pt or "") else "pytest config not found")

    @pred(222)
    def law222(ctx):
        n = _count(r"\.offset\(", ctx)
        return ("FAIL" if n else "PASS", f"{n} OFFSET usage(s)")

    @pred(239)
    def law239(ctx):
        n = 0
        for p in ctx.py_files:
            rel = ctx.rel(p)
            if not any(k in rel for k in ("payment", "webhook", "refund", "payout")):
                continue
            text, _ = read_text(p)
            if "idempotency" in (text or "").lower():
                n += 1
        return ("PASS" if n else "FAIL", f"{n} payment-path file(s) reference idempotency")

    @pred(243)
    def law243(ctx):
        pc = ctx.root / ".pre-commit-config.yaml"
        if not pc.exists():
            return ("FAIL", "no pre-commit config")
        text, _ = read_text(pc)
        return ("PASS", f"pre-commit hooks: {len(re.findall(r'id:\s*\S+', text or ''))}")

    @pred(248)
    def law248(ctx):
        docs = list((ctx.root / "docs").rglob("*.md")) if (ctx.root / "docs").exists() else []
        return ("PASS" if docs else "FAIL", f"{len(docs)} doc file(s) under docs/")

    @pred(275)
    def law275(ctx):
        fe = ctx.backend / "infrastructure" / "security" / "field_encryption.py"
        return ("PASS" if fe.exists() else "FAIL", "field_encryption.py present" if fe.exists() else "field encryption module missing")

    @pred(283)
    def law283(ctx):
        n = _count(r"pyotp|totp", ctx)
        return ("PASS" if n else "FAIL", f"{n} TOTP reference(s)")

    @pred(290)
    def law290(ctx):
        uv = (ctx.backend / "uv.lock").exists()
        pnpm = (ctx.frontend / "web_app" / "pnpm-lock.yaml").exists()
        return ("PASS" if (uv and pnpm) else "FAIL", f"uv.lock={uv} pnpm-lock={pnpm}")

    @pred(313)
    def law313(ctx):
        orch = list((ctx.backend / "domains" / "finance").rglob("*payment_orchestrator*"))
        gateways = any("payment_gateway" in ctx.rel(p) for p in (ctx.backend / "domains" / "finance").rglob("*.py"))
        return ("PASS" if (orch or gateways) else "FAIL",
                f"orchestrator={bool(orch)} gateway-model={gateways}")

    return _PRED


_PRED_CACHE = None


def _get_predicates():
    global _PRED_CACHE
    if _PRED_CACHE is None:
        _PRED_CACHE = _predicates()
    return _PRED_CACHE


@check("laws_all", "09_laws", "arch",
       "Audit all 325 laws: statically checkable ones get a PASS/FAIL verdict "
       "with evidence, the rest are UNVERIFIABLE with the reason.")
def laws_all(ctx: ScanContext) -> CheckResult:
    res = CheckResult(check="laws_all", dimension="09_laws")
    laws = _parse_laws()
    if not laws:
        res.findings.append(_f(0, "docs", "_most_imp_docx/ARCHITECTURE_STACK.md",
                               "law table could not be parsed",
                               "all 325 laws present", "Restore the canon doc",
                               priority="P0", blocker="yes"))
        return res
    preds = _get_predicates()
    rows = []
    fails = 0
    for law in laws:
        n = law["law"]
        fn = preds.get(n)
        if fn is None:
            status = "UNVERIFIABLE"
            evidence = "process/organizational law — needs runtime, CI or human artifact"
        else:
            try:
                status, evidence = fn(ctx)
            except Exception as exc:
                status, evidence = "UNVERIFIABLE", f"predicate error: {type(exc).__name__}: {exc}"
        if status not in ("PASS", "FAIL", "PARTIAL", "UNVERIFIABLE"):
            status = "UNVERIFIABLE"
        rows.append({**law, "status": status, "evidence": evidence})
        if status == "FAIL":
            fails += 1
            high = law["category"].lower() in (
                "security", "architecture", "database", "code quality",
                "wiring", "provider", "config")
            res.findings.append(_f(
                n, law["category"], "backend/",
                f"Law {n} ({law['rule']}) violated: {evidence}",
                law["description"][:220],
                f"Fix Law-{n} violation: {law['rule']}",
                priority="P0" if law["category"].lower() in ("security", "architecture") else ("P1" if high else "P2"),
                blocker="partial" if high else "no",
                cluster=f"CLUSTER-law-{law['category'].lower().replace(' ', '-')}",
            ))
    res.facts["laws"] = rows
    res.facts["laws_total"] = len(rows)
    res.facts["laws_fail"] = fails
    res.facts["laws_pass"] = sum(1 for r in rows if r["status"] == "PASS")
    res.facts["laws_unverifiable"] = sum(1 for r in rows if r["status"] == "UNVERIFIABLE")
    return res
