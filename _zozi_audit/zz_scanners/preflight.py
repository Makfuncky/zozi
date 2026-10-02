"""Phase 0 (boot smoke test) + Phase 0.5 (pre-flight checks).

These run before all other checks because later checks consume their tool
results. Every failure is also emitted as a completion-blocker finding in
dimension 27 so the main report leads with it.
"""
from __future__ import annotations

import re
import socket
from pathlib import Path
from urllib.parse import urlparse

from zz_core import tools
from zz_core.model import CheckResult, Finding, Observation, ScanContext
from zz_core.util import parse_package_json, parse_requirements, read_text


def _blocker(ctx: ScanContext, key: str, current: str, target: str, fix: str,
             verify: str, effort: str = "S", confidence: int = 5,
             evidence: str = "", snippet: str = "") -> Finding:
    return Finding(
        id=f"BLOCK-{key}",
        dimension="27_project_completion_blockers",
        phase="boot" if key.startswith("boot") else "infra",
        cluster="CLUSTER-boot-preflight",
        file=evidence.split(":")[0] if evidence else "backend/",
        line=int(evidence.split(":")[1]) if evidence.count(":") == 1 and evidence.split(":")[1].isdigit() else 0,
        current=current, target=target,
        delta=current[:160],
        fix=fix, effort=effort, priority="P0", confidence=confidence,
        evidence_strength="triangulated", truth_level="L1",
        claim_state="VERIFIED" if confidence >= 4 else "INFERRED",
        sibling="", verify=verify, test="", rollback="git revert <commit>",
        blast_radius="boot, CI, deployment", completion_blocker="yes",
        laws=(81,), snippet=snippet, origin="tool",
    )


# --------------------------------------------------------------------------- #
# Individual checks
# --------------------------------------------------------------------------- #

def _terminal_error(stderr: str) -> tuple[str, str]:
    """Return ``(project_file:line, exception_line)`` from a Python traceback.

    A boot failure is only actionable when the report names the file and line
    that raised, not the last line of a truncated stderr buffer.
    """
    text = stderr or ""
    file_line, exc = "", ""
    for raw in text.splitlines():
        line = raw.strip()
        m = re.match(r'^File "([^"]+)", line (\d+), in ', line)
        if m and "site-packages" not in m.group(1) and "<" not in m.group(1):
            file_line = f"{m.group(1)}:{m.group(2)}"
        if re.match(r"^(ImportError|ModuleNotFoundError|AttributeError|"
                    r"NameError|SyntaxError|ValueError|TypeError|RuntimeError|"
                    r"AssertionError|OSError|KeyError|PydanticUserError|"
                    r"ValidationError|SystemExit)\b", line):
            exc = line
    if not exc:
        lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
        exc = lines[-1][:240] if lines else "no exception line captured"
    return file_line, exc


def _rel(ctx: ScanContext, abspath_line: str) -> str:
    """``C:/repo/backend/x.py:12`` -> ``backend/x.py:12`` (repo-relative)."""
    if not abspath_line:
        return ""
    path, _, line = abspath_line.rpartition(":")
    try:
        rel = Path(path).resolve().relative_to(ctx.root.resolve())
    except Exception:
        return abspath_line
    return f"{rel.as_posix()}:{line}" if line else rel.as_posix()


def check_boot(ctx: ScanContext) -> tuple[dict, CheckResult]:
    res = CheckResult(check="preflight_boot", dimension="27_project_completion_blockers")
    if ctx.options.get("no_tools"):
        row = {"check": "Boot smoke test", "status": "SKIPPED", "evidence": "--no-tools"}
        return row, res
    if ctx.fast:
        row = {"check": "Boot smoke test", "status": "SKIPPED",
               "evidence": "fast mode (run without --fast to import the app)"}
        return row, res
    out = tools.boot_smoke(ctx)
    if out.exit_code == 0:
        routes = (out.stdout_tail or "").strip().splitlines()[-1] if out.stdout_tail else "?"
        status = "PASS"
        evidence = f"`{out.cmd}` -> {routes} routes ({out.duration_s}s)"
        skipped = re.findall(r"Skipping router ([a-z_]+)", (out.stderr_tail or "") + (out.stdout_tail or ""))
        if skipped:
            status = "PARTIAL"
            evidence += f"; skipped routers: {', '.join(sorted(set(skipped)))}"
            res.findings.append(_blocker(
                ctx, "boot-routers",
                f"Routers fail to register at boot: {', '.join(sorted(set(skipped)))}",
                "All module routers mount successfully (Law 135)",
                "Fix the failing import so every router registers",
                "cd backend && python -c \"from main import app; print(len(app.routes))\"",
                evidence="backend/main.py:1",
            ))
        return {"check": "Boot smoke test", "status": status, "evidence": evidence}, res

    # The application does not import. Name the exact line that raised.
    adapted = ctx.tools.get("boot:backend-cwd")
    source = adapted or out
    where, exc = _terminal_error((source.stderr_tail or "") + "\n" + (out.stderr_tail or ""))
    rel = _rel(ctx, where)
    is_packaging = bool(re.match(r"ModuleNotFoundError: No module named '(infrastructure|"
                                 r"domains|modules|rbac|kernel|providers|jobs|middleware)'", exc))
    if is_packaging:
        fix = ("Make `backend/` importable from the repo root (add `backend/__init__.py`) "
               "or standardize on the documented `cd backend` boot command")
        current = f"repo-root boot cannot resolve backend packages — {exc}"
        target = "`python -c \"from backend.main import app\"` works from the repo root"
    else:
        fix = f"Fix the failing import at {rel or 'the reported frame'}"
        current = f"application fails to import — {exc} (raised at {rel or where or 'unknown'})"
        target = "`from main import app` succeeds and every router registers (Law 81)"
    res.findings.append(_blocker(
        ctx, "boot-import", current, target, fix,
        "cd backend && python -c \"from main import app; print(len(app.routes))\"",
        evidence=rel or "backend/main.py:1", snippet=exc,
    ))
    return {"check": "Boot smoke test", "status": "FAIL",
            "evidence": f"`{source.name}` failed (exit={source.exit_code}) at "
                        f"{rel or 'unknown'}: {exc}"}, res


def check_env(ctx: ScanContext) -> tuple[dict, CheckResult]:
    res = CheckResult(check="preflight_env", dimension="11_environmental")
    cfg = ctx.backend / "config.py"
    env_example = ctx.root / ".env.example"
    text, _ = read_text(cfg)
    env_text, _ = read_text(env_example)
    required = ("SECRET_KEY", "DATABASE_URL", "FIELD_ENCRYPTION_KEY", "AUDIT_CHAIN_KEY")
    declared = set(re.findall(r"\b([A-Z][A-Z0-9_]{2,})\b", env_text or ""))
    missing = [r for r in required if r not in declared]
    # does config even expose DATABASE_URL as typed field?
    typed_names = set(re.findall(r"^\s{4}([a-z_][a-z0-9_]*)\s*:", text or "", re.MULTILINE))
    attr_mismatch = "DATABASE_URL" in (env_text or "") and "DATABASE_URL" not in text
    if attr_mismatch and "database_url" not in text:
        res.findings.append(_blocker(
            ctx, "env-database-url",
            "`DATABASE_URL` env var is documented but config.py exposes no matching typed field",
            "Typed settings must resolve every documented env var (Law 84)",
            "Add the typed field or document the lowercase mapping",
            "python -c \"from backend.config import settings; print(settings.database_url)\"",
            evidence="backend/config.py:1",
        ))
    if missing:
        res.findings.append(_blocker(
            ctx, "env-required-missing",
            f"Required-in-production env vars missing from .env.example: {', '.join(missing)}",
            "Every required var is documented in .env.example (Law 202)",
            "Add the missing vars to .env.example with empty defaults",
            "grep -E 'SECRET_KEY|DATABASE_URL|FIELD_ENCRYPTION_KEY|AUDIT_CHAIN_KEY' .env.example",
        ))
    status = "PASS" if not missing and not attr_mismatch else "FAIL"
    evidence = f".env.example declared={len(declared)}; typed settings fields={len(typed_names)}"
    if missing:
        evidence += f"; missing={','.join(missing)}"
    return {"check": "Required env vars", "status": status, "evidence": evidence}, res


DEFAULT_PORTS = {
    "postgresql": 5432, "postgresql+asyncpg": 5432, "postgres": 5432,
    "valkey": 6379, "valkeys": 6379, "redis": 6379, "rediss": 6379,
    "amqp": 5672, "amqps": 5671,
}


def _tcp_probe(url: str, default_host: str = "localhost") -> tuple[bool, str]:
    try:
        parsed = urlparse(url)
        host = parsed.hostname or default_host
        port = parsed.port or DEFAULT_PORTS.get((parsed.scheme or "").lower(), 0)
        if not port:
            return False, "no-port-and-unknown-scheme"
        with socket.create_connection((host, port), timeout=2.5):
            return True, f"{host}:{port} reachable"
    except Exception as exc:
        return False, f"{type(exc).__name__}"


def _is_placeholder(url: str) -> bool:
    """True when the DSN is an unresolved template (${VAR}, {var}, <...>)."""
    return any(tok in url for tok in ("${", "%(", "<", "{env", "{VAR", "example.com"))


def _resolve_dsn(ctx: ScanContext, env_name: str, settings_field: str) -> tuple[str, str]:
    """Resolve a DSN without ever echoing credentials.

    Order: the canonical repo-root ``.env`` (memory: one canonical ``.env``),
    then the declared default in ``backend/config.py``. Returns ``(dsn, source)``
    or ``("", "")`` when the value is not statically resolvable — in which case
    the caller must report UNVERIFIABLE rather than guessing.
    """
    env_text, _ = read_text(ctx.root / ".env")
    if env_text:
        for line in env_text.splitlines():
            line = line.strip()
            if line.startswith("#") or not line.startswith(env_name + "="):
                continue
            value = line.split("=", 1)[1].strip().strip("'\"")
            if value:
                return value, f".env:{env_name}"
    settings, _ = read_text(ctx.backend / "config.py")
    m = re.search(rf"^\s*{settings_field}\s*:\s*[^=\n]*=\s*Field\(\s*default\s*=\s*[\"']([^\"']+)[\"']",
                  settings or "", re.MULTILINE)
    if m and m.group(1):
        return m.group(1), f"backend/config.py:{settings_field} default"
    return "", ""


def _safe_endpoint(url: str) -> str:
    """``scheme://host:port/db`` with any credentials removed."""
    parsed = urlparse(url)
    host = parsed.hostname or "?"
    port = parsed.port or DEFAULT_PORTS.get((parsed.scheme or "").lower(), "?")
    db = (parsed.path or "").lstrip("/") or "?"
    return f"{parsed.scheme or '?'}://{host}:{port}/{db}"


def check_db(ctx: ScanContext) -> tuple[dict, CheckResult]:
    res = CheckResult(check="preflight_db", dimension="06_database")
    url, source = _resolve_dsn(ctx, "DATABASE_URL", "database_url")
    if not url:
        return {"check": "Database connectivity", "status": "UNVERIFIABLE",
                "evidence": "DATABASE_URL not statically resolvable (no .env entry, "
                            "no config.py default) — set it in the environment"}, res
    if url.startswith("sqlite"):
        return {"check": "Database connectivity", "status": "ADAPTED",
                "evidence": f"sqlite DSN detected ({_safe_endpoint(url)}) via {source}"}, res
    if _is_placeholder(url):
        return {"check": "Database connectivity", "status": "UNVERIFIABLE",
                "evidence": f"DATABASE_URL is a template ({_safe_endpoint(url)}) via {source}; "
                            "the real value comes from the runtime environment"}, res
    ok, why = _tcp_probe(url)
    status = "PASS" if ok else "FAIL"
    if not ok:
        res.findings.append(_blocker(
            ctx, "db-unreachable",
            f"DATABASE_URL endpoint not reachable ({_safe_endpoint(url)} via {source}: {why})",
            "DATABASE_URL must be reachable for the app to boot and migrations to run",
            "Start the database (docker compose up db) or point DATABASE_URL at a live branch",
            "cd backend && python -c \"import asyncio,asyncpg; asyncio.run(asyncpg.connect('postgresql+asyncpg://...'))\"",
            effort="S",
        ))
    return {"check": "Database connectivity", "status": status,
            "evidence": f"{_safe_endpoint(url)} — {why} (source: {source})"}, res


def check_valkey(ctx: ScanContext) -> tuple[dict, CheckResult]:
    res = CheckResult(check="preflight_valkey", dimension="04_operational")
    url, source = _resolve_dsn(ctx, "VALKEY_URL", "valkey_url")
    if not url:
        return {"check": "Valkey connectivity", "status": "UNVERIFIABLE",
                "evidence": "VALKEY_URL not statically resolvable — set it in the "
                            "environment"}, res
    if _is_placeholder(url):
        return {"check": "Valkey connectivity", "status": "UNVERIFIABLE",
                "evidence": f"VALKEY_URL is a template ({_safe_endpoint(url)}) via {source}"}, res
    ok, why = _tcp_probe(url, "localhost")
    status = "PASS" if ok else "FAIL"
    if not ok:
        res.findings.append(_blocker(
            ctx, "valkey-unreachable",
            f"Valkey unreachable ({_safe_endpoint(url)} via {source}: {why}) — cache, "
            "sessions, rate limiting and the event bus degrade",
            "Valkey 9.0.6+ reachable in every environment that runs the API",
            "Start Valkey (docker compose up valkey) and verify RATE_LIMIT_ENABLED fails closed",
            "cd backend && python -c \"import valkey; print(valkey.Valkey.from_url('valkey://host:6379').ping())\"",
            effort="S",
        ))
    scheme = urlparse(url).scheme
    note = ""
    if not scheme.startswith("valkey"):
        note = f"; scheme={scheme or '?'} (canonical is valkey://)"
    return {"check": "Valkey connectivity", "status": status,
            "evidence": f"{_safe_endpoint(url)} — {why}{note} (source: {source})"}, res


def check_test_collection(ctx: ScanContext) -> tuple[dict, CheckResult]:
    res = CheckResult(check="preflight_tests", dimension="12_tests")
    if ctx.fast or ctx.options.get("no_tools"):
        return {"check": "Test collection", "status": "SKIPPED", "evidence": "fast mode"}, res
    out = tools.run_pytest_collect(ctx)
    tail = (out.full_stdout or "") + "\n" + (out.stderr_tail or "")
    errors = re.findall(r"^ERROR\s+(\S+)", tail, re.MULTILINE)
    # pytest -q ends with e.g. "4482 tests collected, 19 errors in 54.51s"
    summary = re.findall(
        r"(\d+)\s+(?:tests?\s+)?collected(?:,\s*(\d+)\s+errors?)?(?:\s+in\s+([\d.]+)s)?", tail)
    n = "0"
    n_err = len(set(errors))
    if summary:
        n, err_s, _dur = summary[-1]
        n_err = int(err_s) if err_s else n_err
    else:
        n2 = re.findall(r"(\d+)\s+tests? collected", tail)
        n = n2[-1] if n2 else "0"
    err_lines = [ln.strip() for ln in tail.splitlines() if ln.startswith("ERROR")][:20]
    if out.exit_code == 0:
        return {"check": "Test collection", "status": "PASS",
                "evidence": f"{n} tests collected in {out.duration_s}s"}, res
    res.findings.append(_blocker(
        ctx, "test-collection",
        f"pytest --collect-only exits {out.exit_code}: {n_err} collection error(s) "
        f"for {n} collected test(s). Broken modules: "
        + (", ".join(err_lines[:10]) if err_lines else "see Appendix A tool ledger"),
        "All tests collect without error (Law 71)",
        "Fix the broken imports reported by pytest --collect-only",
        "cd backend && pytest --collect-only -q", effort="L",
        evidence="backend/tests",
    ))
    return {"check": "Test collection", "status": "FAIL",
            "evidence": f"exit={out.exit_code}; {n} collected; "
                        f"{n_err} collection error(s): "
                        f"{', '.join(err_lines[:4])}"}, res


def check_tsc(ctx: ScanContext) -> tuple[dict, CheckResult]:
    res = CheckResult(check="preflight_tsc", dimension="14_frontend_web")
    if ctx.fast or ctx.options.get("no_tools"):
        return {"check": "Frontend type check", "status": "SKIPPED", "evidence": "fast mode"}, res
    out = tools.run_tsc(ctx)
    if getattr(out, "skipped_reason", ""):
        return {"check": "Frontend type check", "status": "UNVERIFIABLE",
                "evidence": out.skipped_reason}, res
    # Count on the untruncated output: stdout_tail elides the middle of a long
    # compile, which silently under-reports the error count.
    tail = (out.full_stdout or "") + "\n" + (out.stderr_tail or "")
    errs = re.findall(r"error TS\d+", tail)
    files = re.findall(r"^([^\s(]+\.(?:ts|tsx))\(", tail, re.MULTILINE)
    if out.exit_code == 0:
        return {"check": "Frontend type check", "status": "PASS",
                "evidence": f"tsc clean in {out.duration_s}s"}, res
    # A non-zero exit with zero parsed errors means the compiler never produced
    # output (killed, or the runner was hijacked by an install hook). Report
    # UNVERIFIABLE — never "FAIL: 0 errors", which reads as a clean run.
    if not errs:
        reason = getattr(out, "skipped_reason", "") or (
            f"tsc exited {out.exit_code} after {out.duration_s}s without emitting "
            f"compiler output (last line: "
            f"{(tail.strip().splitlines() or ['no output'])[-1][:120]})")
        return {"check": "Frontend type check", "status": "UNVERIFIABLE",
                "evidence": reason}, res
    worst = ", ".join(sorted(set(files))[:4])
    res.findings.append(_finding(ctx, "WEB-tsc", "14_frontend_web", "frontend",
                                 "frontend/web_app",
                                 f"{len(errs)} TypeScript error(s) across "
                                 f"{len(set(files))} file(s)",
                                 "tsc --noEmit passes with zero errors (Law 186)",
                                 "Fix the TypeScript errors reported by tsc; start "
                                 f"with {worst}",
                                 "cd frontend/web_app && node_modules/.bin/tsc --noEmit",
                                 effort="L", priority="P0", blocker="yes",
                                 origin="tool", snippet=worst))
    return {"check": "Frontend type check", "status": "FAIL",
            "evidence": f"{len(errs)} TS errors in {len(set(files))} file(s) "
                        f"({out.duration_s}s); first: {worst}"}, res


def _finding(ctx: ScanContext, fid: str, dimension: str, phase: str, file_hint: str,
             current: str, target: str, fix: str, verify: str, effort: str = "M",
             priority: str = "P1", blocker: str = "partial", origin: str = "static",
             snippet: str = ""):
    return Finding(
        id=fid, dimension=dimension, phase=phase, file=file_hint,
        current=current, target=target, delta=current[:160], fix=fix,
        effort=effort, priority=priority, confidence=4,
        evidence_strength="multiple", truth_level="L1", claim_state="VERIFIED",
        verify=verify, completion_blocker=blocker, origin=origin,
        snippet=snippet,
    )


def check_lint(ctx: ScanContext) -> tuple[dict, CheckResult]:
    res = CheckResult(check="preflight_lint", dimension="02_technological")
    if ctx.fast or ctx.options.get("no_tools"):
        return {"check": "Backend lint", "status": "SKIPPED", "evidence": "fast mode"}, res
    out = tools.run_ruff(ctx)
    if not out.available:
        return {"check": "Backend lint", "status": "SKIPPED",
                "evidence": out.skipped_reason or "ruff unavailable"}, res
    tail = (out.full_stdout or "") + "\n" + (out.stderr_tail or "")
    # ruff is invoked with --statistics, so the output is
    # "<count> <CODE> [fixable] description" — count those, do not look for
    # "file:line:col" (that would silently report 0 for a real violation set).
    stats: list[tuple[int, str]] = []
    for m in re.finditer(r"^(\d+)\s+([A-Z]+[0-9]+)\b", tail, re.MULTILINE):
        stats.append((int(m.group(1)), m.group(2)))
    count = sum(c for c, _ in stats)
    if not stats:
        count = len(re.findall(r"^[^:]+:\d+:\d+", tail, re.MULTILINE))
    top = ", ".join(f"{code}={c}" for c, code in
                    sorted(stats, key=lambda t: -t[0])[:6]) if stats else "no rule breakdown"
    if out.exit_code == 0:
        return {"check": "Backend lint", "status": "PASS",
                "evidence": f"ruff clean in {out.duration_s}s"}, res
    res.findings.append(_finding(ctx, "TECH-lint", "02_technological", "tech", "backend/",
                                 f"ruff reports {count} violation(s); top rules: {top}",
                                 "ruff passes in CI (TECHNOLOGY_STACK §11, Law 243)",
                                 "Run `ruff check . --fix`, then resolve the remaining rules",
                                 "cd backend && ruff check .", effort="L",
                                 priority="P0", blocker="yes", origin="tool"))
    return {"check": "Backend lint", "status": "FAIL",
            "evidence": f"{count} violation(s) in {out.duration_s}s; {top}"}, res


def check_migrations(ctx: ScanContext) -> tuple[dict, CheckResult]:
    res = CheckResult(check="preflight_migrations", dimension="10_migrations")
    if ctx.fast or ctx.options.get("no_tools"):
        return {"check": "Alembic heads", "status": "SKIPPED", "evidence": "fast mode"}, res
    out = tools.run_alembic(ctx)
    tail = (out.full_stdout or "") + "\n" + (out.stderr_tail or "")
    heads = re.findall(r"^([0-9a-zA-Z_]+)\s*\(head\)", tail, re.MULTILINE)
    lowered = tail.lower()
    if out.exit_code != 0 or "error" in lowered[:2000]:
        res.findings.append(_finding(ctx, "MIG-alembic-crash", "10_migrations", "db",
                                     "backend/alembic/",
                                     f"`alembic heads` fails: {tail.strip()[-200:]}",
                                     "Alembic CLI runs without import errors",
                                     "Fix the migration import chain so alembic can enumerate heads",
                                     "cd backend && alembic -c alembic/alembic.ini heads",
                                     effort="M", priority="P0", blocker="yes", origin="tool"))
        return {"check": "Alembic heads", "status": "FAIL",
                "evidence": tail.strip()[-200:]}, res
    n = len(heads)
    if n > 1:
        res.findings.append(_finding(ctx, "MIG-divergent-heads", "10_migrations", "db",
                                     "backend/alembic/versions/",
                                     f"{n} divergent heads: {', '.join(heads)}",
                                     "Exactly one linear head (Law 49)",
                                     "Merge all heads into one linear chain",
                                     "cd backend && alembic -c alembic/alembic.ini heads",
                                     effort="L", priority="P0", blocker="yes", origin="tool"))
    return {"check": "Alembic heads", "status": "FAIL" if n != 1 else "PASS",
            "evidence": f"{n} head(s): {', '.join(heads) or 'none'}"}, res


def check_lockfiles(ctx: ScanContext) -> tuple[dict, CheckResult]:
    res = CheckResult(check="preflight_lockfiles", dimension="02_technological")
    req = parse_requirements(ctx.backend / "requirements.txt")
    uv = ctx.backend / "uv.lock"
    uv_text, _ = read_text(uv)
    uv_entries = len(re.findall(r"^\[\[package\]\]", uv_text or "", re.MULTILINE))
    pkg = parse_package_json(ctx.frontend / "web_app" / "package.json")
    lock = ctx.frontend / "web_app" / "pnpm-lock.yaml"
    deps = len((pkg.get("dependencies") or {}))
    issues = []
    if not req:
        issues.append("requirements.txt unreadable/empty")
    if uv_entries < 10 and deps:
        issues.append(f"uv.lock has {uv_entries} package entries (not a usable lockfile)")
    if not lock.exists():
        issues.append("web pnpm-lock.yaml missing")
    status = "FAIL" if issues else "PASS"
    if issues:
        res.findings.append(_finding(ctx, "TECH-lockfiles", "02_technological", "tech",
                                     "backend/uv.lock",
                                     "; ".join(issues),
                                     "uv.lock and pnpm-lock.yaml are complete and in sync with manifests",
                                     "Populate uv.lock from pyproject.toml; keep pnpm-lock.yaml committed",
                                     "uv lock --check && pnpm install --frozen-lockfile",
                                     effort="M", priority="P0", blocker="yes"))
    return {"check": "Lockfile sync", "status": status,
            "evidence": f"requirements={len(req)} uv-lock-entries={uv_entries} "
                        f"web-deps={deps} pnpm-lock={'yes' if lock.exists() else 'no'}"}, res


def check_architecture_tests(ctx: ScanContext) -> tuple[dict, CheckResult]:
    res = CheckResult(check="preflight_architecture_tests", dimension="12_tests")
    if ctx.fast or ctx.options.get("no_tools"):
        return {"check": "Architecture tests", "status": "SKIPPED", "evidence": "fast mode"}, res
    out = tools.run_pytest_architecture(ctx)
    if getattr(out, "skipped_reason", ""):
        return {"check": "Architecture tests", "status": "SKIPPED",
                "evidence": out.skipped_reason}, res
    # Untruncated: a failing architecture run emits megabytes of traceback and
    # the summary line plus the FAILED list sit in the elided middle.
    tail = ((out.full_stdout or "") + "\n" + (out.stderr_tail or "")).strip()
    # pytest's own summary line, not "the last line of the buffer": workers
    # that prompt (e.g. a stuck valkey client) emit a trailing message that
    # would otherwise be reported as the test result.
    m = re.search(r"^=+\s*(.*(?:passed|failed|error|no tests ran).*?)\s*=+$",
                  tail, re.MULTILINE)
    parsed_summary = m.group(1).strip() if m else ""
    failed = re.findall(r"^FAILED\s+([^\s:]+)::(\S+)", tail, re.MULTILINE)
    errored = re.findall(r"^ERROR\s+([^\s:]+)::(\S+)", tail, re.MULTILINE)
    # Name the individual law tests that failed. A single "50 failed" line hides
    # which laws are broken, which is the only actionable part.
    by_file: dict[str, int] = {}
    for path, _ in failed + errored:
        by_file[path] = by_file.get(path, 0) + 1
    res.facts["architecture_tests"] = {
        "summary": parsed_summary or "(no pytest summary — run did not finish)",
        "failed": len(failed),
        "errored": len(errored),
        "completed": bool(parsed_summary),
        "by_file": dict(sorted(by_file.items(), key=lambda kv: -kv[1])),
        "failing_tests": [f"{p}::{t}" for p, t in (failed + errored)[:60]],
    }
    for path, name in (failed + errored)[:25]:
        res.observations.append(Observation(
            "arch_law_test", f"{path}::{name}", f"backend/tests/{path}", 0,
            "12_tests", evidence=f"failing architecture-law test: {name}"))
    worst = ", ".join(f"{p.replace('tests/architecture/', '')}({n})"
                      for p, n in list(by_file.items())[:5])
    if out.exit_code == 0 and parsed_summary:
        return {"check": "Architecture tests", "status": "PASS",
                "evidence": f"{parsed_summary} ({out.duration_s}s)"}, res
    if not parsed_summary:
        # The run was killed (a worker hung on a socket and something broke the
        # process) so pytest never printed a summary. That is not a clean FAIL
        # and not a PASS: report what was observed and say the rest is unproven.
        res.findings.append(_finding(
            ctx, "TEST-arch-hang", "12_tests", "testing", "backend/tests/architecture",
            f"the architecture-law suite did not finish in {out.duration_s}s "
            f"(exit {out.exit_code}); {len(failed)} failure(s) and "
            f"{len(errored)} error(s) were observed before it stopped: {worst}",
            "tests/architecture/ runs to completion and reports a summary",
            "find the test that blocks (likely a socket or DB wait), then re-run; "
            "the remaining law tests are UNVERIFIED until it completes",
            "cd backend && python -m pytest tests/architecture -q --timeout=120",
            effort="L", priority="P0", blocker="yes", origin="tool",
            snippet="; ".join(f"{p}::{t}" for p, t in (failed + errored)[:8])))
        return {"check": "Architecture tests", "status": "INCOMPLETE",
                "evidence": f"no summary after {out.duration_s}s (exit {out.exit_code}); "
                            f"{len(failed)} failed, {len(errored)} errored so far; "
                            f"worst: {worst}"}, res
    res.findings.append(_finding(
        ctx, "TEST-arch-laws", "12_tests", "testing", "backend/tests/architecture",
        f"architecture (law) tests fail: {parsed_summary} — worst files: {worst}",
        "tests/architecture/ enforces the ARCHITECTURE_STACK laws and passes",
        "Fix the failing architecture test, or the law violation it exposes; "
        f"start with {worst.split(',')[0] if by_file else 'the first file'}",
        "cd backend && python -m pytest tests/architecture -q",
        effort="L", priority="P0", blocker="yes", origin="tool",
        snippet="; ".join(f"{p}::{t}" for p, t in (failed + errored)[:8])))
    return {"check": "Architecture tests", "status": "FAIL",
            "evidence": f"{parsed_summary} ({out.duration_s}s); worst: {worst}"}, res


CHECKS = [
    check_boot, check_env, check_db, check_valkey, check_test_collection,
    check_tsc, check_lint, check_migrations, check_lockfiles,
    check_architecture_tests,
]


def run_preflight(ctx: ScanContext) -> tuple[list[dict], list[CheckResult]]:
    rows: list[dict] = []
    results: list[CheckResult] = []
    for fn in CHECKS:
        try:
            row, res = fn(ctx)
        except Exception as exc:  # pragma: no cover
            row = {"check": fn.__name__, "status": "ERROR",
                   "evidence": f"{type(exc).__name__}: {exc}"}
            res = CheckResult(check=fn.__name__, dimension="27_project_completion_blockers")
            ctx.errors.append(f"preflight {fn.__name__}: {exc}")
        rows.append(row)
        results.append(res)
    return rows, results
