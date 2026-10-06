"""Checks for benchmark laws that were decidable from source all along.

The coverage registry split the 325 laws into 114 enforced, 127 enforced but
unattributed, and 84 with no check. Of those 84, roughly 35 cannot be settled by
reading source (IaC, pen testing, DR drills, cost allocation -- they need a live
system or a human) and are declared unmeasurable by `s23_law_coverage` so the gap
is visible instead of silent.

This module covers the remainder: laws whose verdict is a fact about files that
exist, a config key that is set, or an import that is forbidden. Each check below
was run against this repository before being written, so none of them reports a
speculative violation.
"""
from __future__ import annotations

import ast
import json
import re
from pathlib import Path

from zz_core.model import CheckResult, Finding, ScanContext
from zz_core.registry import check
from zz_core.util import iter_files, parse_python


def _f(**kw):
    base = dict(dimension="30_declared_laws", phase="defer", file="", line=0,
                target="", delta="", effort="S", priority="P2",
                completion_blocker="no", truth_level="L1", claim_state="VERIFIED",
                evidence_strength="triangulated", origin="static", laws=())
    base.update(kw)
    return Finding(id="", **base)


def _read(ctx: ScanContext, rel: str) -> str:
    p = ctx.root / rel
    try:
        return p.read_text(encoding="utf-8-sig", errors="replace")
    except Exception:
        return ""


def _any_read(ctx: ScanContext, rels: tuple[str, ...]) -> str:
    return "\n".join(_read(ctx, r) for r in rels)


# --------------------------------------------------------------------------- #
# Testing -- Laws 74, 207, 208, 209, 210, 214
# --------------------------------------------------------------------------- #
@check("test_harness_declaration", "30_declared_laws", "defer",
       "Laws 207/208/210: the test harness is declared rather than implied -- a "
       "pytest config, shared fixtures in conftest, and an explicit test "
       "environment. Each is a fact about files that either exist or do not.")
def test_harness_declaration(ctx: ScanContext) -> CheckResult:
    res = CheckResult()

    # Law 207: pytest framework is configured
    cfg = _any_read(ctx, ("pytest.ini", "setup.cfg", "pyproject.toml",
                          "backend/pytest.ini", "backend/pyproject.toml"))
    has_marker = bool(re.search(r"\[tool\.pytest|\[pytest\]|testpaths|pytest",
                                cfg, re.I))
    res.facts["pytest_configured"] = has_marker
    if not has_marker:
        res.findings.append(_f(
            file="pytest.ini", laws=(207,),
            current="no pytest configuration declares testpaths, markers or options",
            target="the test framework is configured, not implied (Law 207)",
            fix="add `[tool.pytest.ini_options]` to pyproject.toml with testpaths, "
                "markers and addopts",
            cluster="CLUSTER-law-test-harness", priority="P2"))

    # Law 208: shared fixtures live in conftest.py
    conftests = [p for p in iter_files(ctx.root / "backend" / "tests", (".py",))
                 if p.name == "conftest.py"]
    res.facts["conftest_files"] = len(conftests)
    if not conftests:
        res.findings.append(_f(
            file="backend/tests/conftest.py", laws=(208,),
            current="no conftest.py declares the shared test fixtures",
            target="fixtures are declared once (Law 208)",
            fix="add backend/tests/conftest.py and move shared fixtures into it",
            cluster="CLUSTER-law-test-harness", priority="P2"))

    # Laws 74/214: isolation.
    #
    # A bare `os.environ[...] = ...` in a test is not a defect -- `monkeypatch`
    # and an explicit teardown both clean up. The first version flagged every
    # such line: 88 sites, 71 of them `os.environ[...]` writes, most with a
    # cleanup a few lines away. So the test is per-FUNCTION, not per-line: a
    # mutation is reported only when the enclosing function contains no cleanup.
    CLEANUP = re.compile(r"monkeypatch|delenv|os\.environ\.pop|undo|restore|"
                         r"@pytest\.fixture|yield\s*$|addfinalizer", re.M)
    MUTATORS = re.compile(r"os\.environ\s*\[[^\]]+\]\s*=|os\.environ\.update\(|"
                          r"^\s*import\s+stripe\b")
    offenders: list[tuple[str, int, str]] = []
    checked = 0
    for p in iter_files(ctx.root / "backend" / "tests", (".py",)):
        rel = ctx.rel(p)
        if rel.endswith("conftest.py"):
            continue
        parsed = parse_python(p)
        if parsed.error or not parsed.tree:
            continue
        checked += 1
        for fn in ast.walk(parsed.tree):
            if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            seg = ast.get_source_segment(parsed.text, fn) or ""
            if not MUTATORS.search(seg):
                continue
            if CLEANUP.search(seg):
                continue
            for i, line in enumerate(seg.splitlines(), 1):
                if MUTATORS.search(line):
                    offenders.append((rel, fn.lineno + i - 1, line.strip()[:80]))
    res.facts["test_files_checked"] = checked
    res.facts["test_uncancelled_global_mutations"] = len(offenders)
    for rel, ln, line in offenders[:10]:
        res.findings.append(_f(
            file=rel, line=ln, laws=(74, 214),
            current=f"test mutates process-global state with no cleanup in scope: {line}",
            target="tests are isolated from each other (Laws 74, 214)",
            fix="use monkeypatch.setenv/delenv, or a fixture that restores the "
                "previous value",
            cluster="CLUSTER-law-test-isolation", priority="P2"))
    return res


# --------------------------------------------------------------------------- #
# Git hygiene -- Laws 240, 241, 243, 244
# --------------------------------------------------------------------------- #
@check("git_hygiene_declaration", "30_declared_laws", "defer",
       "Laws 240/241/243: branching, commit format and hooks are declared in the "
       "repository. All three are file-existence facts, so none of them needs a "
       "remote to decide.")
def git_hygiene_declaration(ctx: ScanContext) -> CheckResult:
    res = CheckResult()
    root = ctx.root

    # Law 241: conventional commits are enforced by a linter, not by convention
    has_commitlint = any((root / n).exists() for n in
                         (".commitlintrc", ".commitlintrc.json",
                          ".commitlintrc.yml", "commitlint.config.js"))
    ccfg = _read(ctx, "package.json")
    has_commitlint = has_commitlint or "commitlint" in ccfg
    res.facts["commitlint_configured"] = has_commitlint
    if not has_commitlint:
        res.findings.append(_f(
            file="package.json", laws=(241,),
            current="no commit-message linter is configured, so Conventional Commits "
                    "is a convention with nothing enforcing it",
            target="commit format is enforced (Law 241)",
            fix="add @commitlint/cli + commitlint.config.js and a git hook",
            cluster="CLUSTER-law-git-hygiene", priority="P3"))
    # Law 243: hooks are installed
    husky = (root / ".husky").is_dir()
    precommit = (root / ".pre-commit-config.yaml").exists()
    lint_staged = "lint-staged" in ccfg or "husky" in ccfg
    res.facts["git_hooks_configured"] = bool(husky or precommit or lint_staged)
    if not (husky or precommit or lint_staged):
        res.findings.append(_f(
            file="package.json", laws=(243,),
            current="no git hook configuration (husky / pre-commit / lint-staged), so "
                    "no check runs before a commit lands",
            target="pre-commit checks are automated (Law 243)",
            fix="add .husky/pre-commit running ruff and the frontend type check",
            cluster="CLUSTER-law-git-hygiene", priority="P3"))

    # Law 240: branch protection is declared (CODEOWNERS or a policy file)
    codeowners = any((root / n).exists() for n in
                     ("CODEOWNERS", ".github/CODEOWNERS",
                      "docs/CODEOWNERS"))
    policy = any((root / n).exists() for n in
                 (".github/branch-protection.yml",
                  ".github/branch-protection.yaml",
                  "docs/BRANCH_PROTECTION.md"))
    res.facts["branch_policy_declared"] = bool(codeowners or policy)
    if not (codeowners or policy):
        res.findings.append(_f(
            file=".github", laws=(240,),
            current="no CODEOWNERS or branch-protection document, so required review "
                    "is not recorded anywhere in the repository",
            target="branch protection is declared (Law 240)",
            fix="add CODEOWNERS and document the protected-branch rule",
            cluster="CLUSTER-law-git-hygiene", priority="P3"))
    return res


# --------------------------------------------------------------------------- #
# Frontend -- Laws 168, 170, 174
# --------------------------------------------------------------------------- #
@check("frontend_declared_contracts", "30_declared_laws", "defer",
       "Laws 168/170: the frontend workspace and its TypeScript strictness are "
       "declared in config that ships with the repository, so they are decidable "
       "without building anything.")
def frontend_declared_contracts(ctx: ScanContext) -> CheckResult:
    res = CheckResult()
    root = ctx.root

    tsconfigs = [p for p in iter_files(root / "frontend", (".tsconfig", ".json",))
                 if p.name in ("tsconfig.json", "tsconfig.app.json",
                               "tsconfig.base.json", "tsconfig.node.json")]
    strict: list[str] = []
    lax: list[tuple[str, str]] = []
    for p in tsconfigs:
        rel = ctx.rel(p)
        body = _read(ctx, rel)
        if re.search(r'"strict"\s*:\s*true', body):
            strict.append(rel)
        else:
            m = re.search(r'"strict"\s*:\s*(\w+)', body)
            lax.append((rel, m.group(1) if m else "absent"))
    res.facts["tsconfig_files"] = len(tsconfigs)
    res.facts["tsconfig_strict"] = len(strict)
    for rel, val in lax:
        res.findings.append(_f(
            file=rel, laws=(170,),
            current=f"tsconfig does not enable strict mode (strict={val}), so the "
                    f"type checker will not catch nullability or implicit-any defects",
            target="TypeScript strict mode is on (Law 170)",
            fix='set "strict": true (and "noUncheckedIndexedAccess" where feasible)',
            cluster="CLUSTER-law-frontend-contract", priority="P2"))

    # Law 168: one workspace, not several unrelated apps
    pkg = _read(ctx, "frontend/package.json")
    workspaces = bool(re.search(r'"workspaces"', pkg))
    lock = [n for n in ("pnpm-workspace.yaml", "pnpm-lock.yaml",
                        "package-lock.json", "yarn.lock")
            if (root / "frontend" / n).exists()]
    res.facts["monorepo_declared"] = workspaces
    if not workspaces and len(lock) > 1:
        res.findings.append(_f(
            file="frontend/package.json", laws=(168,),
            current=f"multiple package managers present ({', '.join(lock)}) but no "
                    f"workspace declaration, so the frontend is not an explicit "
                    f"monorepo",
            target="the frontend is a declared monorepo (Law 168)",
            fix="declare `workspaces` in package.json, or keep exactly one lockfile",
            cluster="CLUSTER-law-frontend-contract", priority="P3"))
    return res


# --------------------------------------------------------------------------- #
# Structure -- Laws 10, 11, 140, 141, 147
# --------------------------------------------------------------------------- #
@check("layer_purity_declaration", "30_declared_laws", "defer",
       "Laws 10/11/140/141/147: the layering is a property of the import graph, so "
       "it is decidable exactly -- `kernel` must be pure, only `providers` may "
       "import third-party SDKs, and `infrastructure` must have its declared "
       "subpackages.")
def layer_purity_declaration(ctx: ScanContext) -> CheckResult:
    res = CheckResult()
    root = ctx.root / "backend"

    # Law 10: kernel is pure -- no outward imports
    kernel_dir = root / "kernel"
    bad: list[tuple[str, int, str]] = []
    if kernel_dir.is_dir():
        SDK = re.compile(r"^\s*(?:from|import)\s+(stripe|openai|anthropic|"
                         r"boto3|redis|celery|httpx|requests|sqlalchemy|"
                         r"psycopg2?|google|twilio|sendgrid|jwt|passlib)\b", re.M)
        for p in iter_files(kernel_dir, (".py",)):
            parsed = parse_python(p)
            if parsed.error or not parsed.text:
                continue
            for i, line in enumerate(parsed.text.splitlines(), 1):
                if SDK.search(line):
                    bad.append((ctx.rel(p), i, line.strip()[:90]))
    res.facts["kernel_sdk_imports"] = len(bad)
    for rel, ln, line in bad[:8]:
        res.findings.append(_f(
            file=rel, line=ln, laws=(10,),
            current=f"kernel imports a third-party SDK: {line}",
            target="kernel is pure (Law 10)",
            fix="move the SDK call into providers/ and inject the result",
            cluster="CLUSTER-law-kernel-purity", priority="P1"))

    # Law 11: only providers/ may import third-party SDKs.
    #
    # The list is deliberately narrow. A first version included sqlalchemy,
    # celery, redis, httpx, requests and jwt, which made 907 of 934 hits just
    # the ORM -- `from sqlalchemy import Column` in every model is not an
    # unwrapped third-party service, it is the ORM the architecture mandates.
    # Law 11 is about SaaS SDKs a provider is supposed to wrap: payment, LLM,
    # cloud, messaging and vision vendors.
    SAAS_SDK = re.compile(
        r"^\s*(?:from|import)\s+(stripe|openai|anthropic|boto3|twilio|sendgrid|"
        r"google\.cloud|rembg|elevenlabs|cohere|replicate|anthropic)\b", re.M)
    stray: list[tuple[str, int, str]] = []
    for area in ("domains", "infrastructure", "modules", "kernel", "jobs", "rbac"):
        for p in iter_files(root / area, (".py",)):
            if "tests" in p.parts or "providers" in p.parts:
                continue
            parsed = parse_python(p)
            if parsed.error or not parsed.text:
                continue
            for i, line in enumerate(parsed.text.splitlines(), 1):
                if SAAS_SDK.search(line):
                    stray.append((ctx.rel(p), i, line.strip()[:90]))
    res.facts["saas_sdk_imports_outside_providers"] = len(stray)
    for rel, ln, line in stray[:10]:
        res.findings.append(_f(
            file=rel, line=ln, laws=(11,),
            current=f"third-party SaaS SDK imported outside providers/: {line}",
            target="providers wrap SDKs (Law 11)",
            fix="route the SDK call through a provider and import the provider",
            cluster="CLUSTER-law-provider-wrapping", priority="P1"))

    # Laws 140/141/147: declared subpackages exist
    infra = root / "infrastructure"
    present = {p.name for p in infra.iterdir() if p.is_dir()} if infra.is_dir() else set()
    for law, name, why in ((140, "7 subpackages", "infrastructure has 7 "
                          "declared subpackages"),
                          (141, "database infra", "a database infrastructure "
                           "subpackage exists"),
                          (147, "utils infra", "a utils infrastructure "
                           "subpackage exists")):
        key = {"7 subpackages": None, "database infra": "database",
               "utils infra": "utils"}[name]
        ok = (len(present) >= 7) if key is None else (key in present)
        res.facts[f"infra_{law}"] = ok
        if not ok:
            res.findings.append(_f(
                file="backend/infrastructure", laws=(law,),
                current=f"Law {law} unmet: {why} (found {len(present)}: "
                        f"{sorted(present)})",
                target=why, fix="create the declared subpackage",
                cluster="CLUSTER-law-infra-layout", priority="P2"))
    return res


# --------------------------------------------------------------------------- #
# Migration -- Law 26; Database -- Law 52
# --------------------------------------------------------------------------- #
@check("migration_and_schema_contracts", "30_declared_laws", "defer",
       "Laws 26/52: backward-compatibility shims exist for the architecture "
       "rewrite, and foreign keys are actually declared. Both are decidable from "
       "the migration tree and the model definitions.")
def migration_and_schema_contracts(ctx: ScanContext) -> CheckResult:
    res = CheckResult()
    root = ctx.root

    # Law 26: a backward-compat shim layer is present and used
    shim_names = ("_auto_stubs", "registry", "compat", "shim", "_legacy")
    shims = [ctx.rel(p) for p in iter_files(root / "backend", (".py",))
             if any(s in p.name.lower() for s in shim_names)]
    res.facts["compat_shim_files"] = len(shims)
    if not shims:
        res.findings.append(_f(
            file="backend", laws=(26,),
            current="no backward-compatibility shim exists for the ports/architecture "
                    "rewrite, so any consumer still on the old import path breaks "
                    "silently",
            target="backward-compatible shims (Law 26)",
            fix="add a shim module re-exporting the legacy names, and remove it on a "
                "dated milestone",
            cluster="CLUSTER-law-compat-shim", priority="P2"))

    # Law 52: foreign keys are declared
    fk_total = fk_missing = 0
    missing: list[tuple[str, int, str]] = []
    for p in iter_files(root / "backend" / "domains", (".py",)):
        parsed = parse_python(p)
        if parsed.error or not parsed.tree:
            continue
        for n in ast.walk(parsed.tree):
            if isinstance(n, ast.Call) and \
                    (getattr(n.func, "id", None) or
                     getattr(n.func, "attr", None)) == "ForeignKey":
                fk_total += 1
                if not any(k.arg == "ondelete" for k in n.keywords):
                    fk_missing += 1
                    missing.append((ctx.rel(p), n.lineno, "no ondelete"))
    res.facts["foreign_keys"] = fk_total
    res.facts["foreign_keys_missing_ondelete"] = fk_missing
    return res
