#!/usr/bin/env python3
"""Function inventory generator for the `_zozi_audit/` suite.

The audit is a program, not a document. Its behaviour is the sum of ~700
functions spread over `zz_core/`, `zz_scanners/`, `zz_integrations/`, the three
entry points and `tests/`. Nothing in the suite listed them, so "what does the
audit actually do" could only be answered by reading 25 files.

This module derives the inventory from the **AST of the running code** (never
from a hand-maintained list, which is how PLAN.md v2 drifted to "checks 82 vs
actual 92"). For every function it records:

    module · lineno · qualname · signature · decorator (@check name/dimension)
    · first docstring line · line span

CLI:

    python _zozi_audit/zz_core/inventory.py            # -> _zozi_audit/PLAN_FUNCTIONS.md
    python _zozi_audit/zz_core/inventory.py --json     # -> stdout, machine readable
    python _zozi_audit/zz_core/inventory.py --check    # reconcile counts, exit 1 on drift

`--check` is the point of the file: it turns "the plan says 92 checks" into a
fact that can fail. Exit status is the contract, so it is safe to call from CI.
"""
from __future__ import annotations

import argparse
import ast
import json
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
SUITE = HERE.parent

# Modules in reading order: entry points, then the layers bottom-up.
MODULE_ORDER = [
    "zozi_audit.py",
    "zozi_verify.py",
    "zozi_compile.py",
    "zz_core/model.py",
    "zz_core/constants.py",
    "zz_core/util.py",
    "zz_core/tools.py",
    "zz_core/registry.py",
    "zz_core/probe.py",
    "zz_core/measurements.py",
    "zz_core/probes.py",
    "zz_core/report.py",
    "zz_core/logs.py",
    "zz_integrations/http_probe.py",
    "zz_integrations/browser_probe.py",
    "zz_integrations/db_probe.py",
    "zz_integrations/load_probe.py",
    "zz_integrations/ollama_probe.py",
    "zz_scanners/preflight.py",
    "zz_scanners/s01_architecture.py",
    "zz_scanners/s02_technology.py",
    "zz_scanners/s03_logic.py",
    "zz_scanners/s04_operations.py",
    "zz_scanners/s05_wiring.py",
    "zz_scanners/s06_database.py",
    "zz_scanners/s07_providers.py",
    "zz_scanners/s08_laws.py",
    "zz_scanners/s09_environment.py",
    "zz_scanners/s10_tests.py",
    "zz_scanners/s11_frontend.py",
    "zz_scanners/s12_features.py",
    "zz_scanners/s13_security.py",
    "zz_scanners/s14_performance.py",
    "zz_scanners/s15_crosscut.py",
    "zz_scanners/s16_design.py",
    "zz_scanners/s17_interactions.py",
    "zz_scanners/s18_feature_matrix.py",
    "zz_scanners/s19_workflow.py",
    "zz_scanners/s20_db_advisor.py",
    "zz_scanners/s21_http_layer.py",
    "zz_scanners/s22_frontend_contracts.py",
    "zz_scanners/s23_law_coverage.py",
    "zz_scanners/s24_declared_laws.py",
    "tests/fixtures.py",
    "tests/run_tests.py",
]

# One-line description per layer, used as a section header in the plan file.
LAYER_BLURB = {
    "zozi_audit.py": "SCAN — walks the tree, runs every @check on a bounded pool, attaches probes, renders the single report.",
    "zozi_verify.py": "ADJUDICATE — re-derives each claim independently; refutation-only instruments may never CONFIRM.",
    "zozi_compile.py": "PLAN — turns only surviving claims into an ordered, gated remediation plan.",
    "zz_core/": "ENGINE — model, registry, probes, measurements, tools, util, report, logs.",
    "zz_integrations/": "RUNTIME EVIDENCE — optional live probes (http/browser/db/load/ollama); absence is recorded, never invented.",
    "zz_scanners/": "DETECTORS — one module per dimension group; each @check is an independent sub-agent.",
    "tests/": "REGRESSION GATE — polarity fixtures + a runner that fails when a detector inverts.",
}


@dataclass
class FunctionRow:
    module: str
    qualname: str
    lineno: int
    end_lineno: int
    args: str
    returns: str
    decorators: list[str] = field(default_factory=list)
    check_name: str = ""
    check_dimension: str = ""
    doc: str = ""
    is_check: bool = False
    kind: str = "function"  # function | method | class | nested

    @property
    def line_span(self) -> int:
        return max(1, self.end_lineno - self.lineno + 1)


def _decorator_source(node: ast.AST) -> str:
    try:
        return ast.unparse(node)
    except Exception:  # pragma: no cover - unparse is total on 3.13
        return "<decorator>"


def _check_args(dec_src: str) -> tuple[str, str]:
    """Extract (name, dimension) from a `@check("name", "01", ...)` decorator."""
    if not dec_src.startswith("check("):
        return "", ""
    inner = dec_src[len("check("):].rstrip(")")
    try:
        parts = next(ast.iter_child_nodes(ast.parse(f"f({inner})", mode="eval"))).args  # type: ignore[attr-defined]
    except Exception:
        return "", ""
    vals = []
    for p in parts:
        if isinstance(p, ast.Constant):
            vals.append(str(p.value))
        else:
            try:
                vals.append(ast.unparse(p))
            except Exception:
                vals.append("?")
    name = vals[0] if vals else ""
    dim = ""
    for v in vals[1:]:
        if v and (v[:2].isdigit() and " " not in v or v.startswith("dim")):
            dim = v
            break
    return name, dim


def _signature(fn: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
    a = fn.args
    parts: list[str] = []
    for arg in getattr(a, "posonlyargs", []) + a.args:
        parts.append(arg.arg)
    if a.vararg:
        parts.append("*" + a.vararg.arg)
    elif a.kwonlyargs:
        parts.append("*")
    for arg in a.kwonlyargs:
        parts.append(arg.arg)
    if a.kwarg:
        parts.append("**" + a.kwarg.arg)
    ret = ""
    if fn.returns is not None:
        try:
            ret = ast.unparse(fn.returns)
        except Exception:
            ret = "?"
    return f"({', '.join(parts)})" + (f" -> {ret}" if ret else "")


def _first_doc_line(node) -> str:
    doc = ast.get_docstring(node) or ""
    for line in doc.splitlines():
        line = line.strip()
        if line:
            return line[:180]
    return ""


def scan_module(path: Path, module_label: str) -> list[FunctionRow]:
    text = path.read_text(encoding="utf-8-sig")
    tree = ast.parse(text, filename=str(path))
    rows: list[FunctionRow] = []

    def visit(node: ast.AST, prefix: str, kind: str) -> None:
        for child in ast.iter_child_nodes(node):
            if isinstance(child, ast.ClassDef):
                rows.append(FunctionRow(
                    module=module_label, qualname=f"{prefix}{child.name}",
                    lineno=child.lineno, end_lineno=getattr(child, "end_lineno", child.lineno),
                    args="", returns="", kind="class", doc=_first_doc_line(child),
                ))
                visit(child, f"{prefix}{child.name}.", "method")
            elif isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                decs = [_decorator_source(d) for d in child.decorator_list]
                cname, cdim = "", ""
                for d in decs:
                    if d.startswith("check("):
                        cname, cdim = _check_args(d)
                        break
                pre = "async def " if isinstance(child, ast.AsyncFunctionDef) else "def "
                rows.append(FunctionRow(
                    module=module_label,
                    qualname=f"{prefix}{child.name}",
                    lineno=child.lineno,
                    end_lineno=getattr(child, "end_lineno", child.lineno),
                    args=_signature(child),
                    returns="",
                    decorators=decs,
                    check_name=cname,
                    check_dimension=cdim,
                    doc=_first_doc_line(child),
                    is_check=bool(cname),
                    kind="method" if kind == "method" else ("nested" if prefix else "function"),
                ))
                # nested defs are reported with their parent prefix
                visit(child, f"{prefix}{child.name}.<locals>.", kind)
            elif isinstance(child, (ast.If, ast.Try, ast.For, ast.While, ast.With)):
                visit(child, prefix, kind)

    visit(tree, "", "function")
    rows.sort(key=lambda r: (r.lineno, r.qualname))
    return rows


def scan_all() -> dict[str, list[FunctionRow]]:
    out: dict[str, list[FunctionRow]] = {}
    for label in MODULE_ORDER:
        path = SUITE / label
        if not path.exists():
            continue
        out[label] = scan_module(path, label)
    # Any module on disk that is not in MODULE_ORDER is drift, not silence.
    for path in sorted(SUITE.glob("zz_*/*.py")) + sorted(SUITE.glob("*.py")):
        if "__pycache__" in path.parts:
            continue
        rel = path.relative_to(SUITE).as_posix()
        if rel not in out and path.name != "__init__.py":
            out[rel] = scan_module(path, rel)
    return out


def collect_facts(scanned: dict[str, list[FunctionRow]]) -> dict:
    from zz_core import constants  # noqa: E402

    checks = [r for rows in scanned.values() for r in rows if r.is_check]
    per_module_checks: dict[str, int] = {}
    for r in checks:
        per_module_checks[r.module] = per_module_checks.get(r.module, 0) + 1
    dims = sorted({r.check_dimension for r in checks if r.check_dimension})

    preflight_checks = 0
    try:
        from zz_scanners import preflight  # noqa: E402
        preflight_checks = len(preflight.CHECKS)
    except Exception:
        pass

    # The registry exposes the live check list through `all_checks()`; there is no
    # module-level `CHECKS`. Reading a missing attribute inside a `try` would have
    # reported 0 and silently disabled the drift guard below — the exact failure
    # mode this suite forbids in its detectors, so the lookup is explicit.
    registered = 0
    try:
        from zz_core import registry  # noqa: E402
        registered = len(registry.all_checks())
    except Exception as exc:
        print(f"[inventory] registry introspection failed: {exc}", file=sys.stderr)
        registered = -1

    return {
        "modules": len(scanned),
        "functions": sum(len(v) for v in scanned.values()),
        "checks_decorated": len(checks),
        "checks_registered": registered,
        "preflight_checks": preflight_checks,
        "check_modules": per_module_checks,
        "dimensions": dims,
        "canonical_domains": len(getattr(constants, "DOMAINS", []) or []),
        "canonical_modules": len(getattr(constants, "MODULES", []) or []),
    }


def render_markdown(scanned: dict[str, list[FunctionRow]], facts: dict) -> str:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    out: list[str] = []
    out.append("# `_zozi_audit/` — Function Inventory & Audit Plan\n")
    out.append(
        "> Generated by `python _zozi_audit/zz_core/inventory.py`. Every row is read from the\n"
        "> AST of the file on disk, so this file cannot drift from the code; regenerate it\n"
        "> instead of editing it. `--check` reconciles the counts and exits non-zero on drift.\n"
    )
    out.append(f"**Generated:** {now} · **Functions:** {facts['functions']} · "
               f"**Modules:** {facts['modules']} · **@check detectors:** {facts['checks_decorated']} "
               f"(+{facts['preflight_checks']} pre-flight)\n")
    out.append("## 0 · How to read this file\n")
    out.append(
        "A function is a unit of behaviour. The `@check` rows are the audit's sub-agents: the\n"
        "registry runs them on a bounded pool of at most 10, in parallel, and a crash in one\n"
        "becomes a finding instead of aborting the sweep. Every other row is machinery that a\n"
        "check, a probe, the verifier or the compiler depends on; deleting one silently changes\n"
        "a verdict, which is why they are listed here.\n"
    )
    out.append("| Column | Meaning |")
    out.append("|---|---|")
    out.append("| Line | Definition line in the module |")
    out.append("| Signature | Parameters only (the AST's view, not the docstring's) |")
    out.append("| Kind | function · method · nested · class |")
    out.append("| Check | `@check` name + dimension, if this row is a detector |")
    out.append("| First doc line | The contract, as the author wrote it |")
    out.append("")

    out.append("## 1 · Reconciliation\n")
    out.append("| Fact | Value |")
    out.append("|---|---|")
    out.append(f"| Modules scanned | {facts['modules']} |")
    out.append(f"| Functions / methods / classes | {facts['functions']} |")
    out.append(f"| `@check`-decorated detectors | {facts['checks_decorated']} |")
    out.append(f"| Detectors visible in the registry | {facts['checks_registered']} |")
    out.append(f"| Pre-flight checks (not @check-decorated) | {facts['preflight_checks']} |")
    out.append(f"| Dimensions emitted | {len(facts['dimensions'])} |")
    out.append(f"| Canonical domains / modules known to constants | "
               f"{facts['canonical_domains']} / {facts['canonical_modules']} |")
    out.append("")
    out.append("Detector count per module:\n")
    out.append("| Module | Detectors |")
    out.append("|---|---|")
    for mod, n in sorted(facts["check_modules"].items()):
        out.append(f"| `{mod}` | {n} |")
    out.append("")

    out.append("## 2 · The pipeline in call order\n")
    out.append("```")
    out.append("zozi_audit.main")
    out.append("  ├─ resolve_root / build_context            # walk the tree, capture git revision")
    out.append("  ├─ tools.run / tools.probe_all             # subprocess ledger (ruff, tsc, pytest, alembic…)")
    out.append("  ├─ zz_scanners.preflight.run_preflight     # Phase 0 boot smoke + Phase 0.5 pre-flight")
    out.append("  ├─ registry.run_checks(workers<=10)        # every @check, bounded pool")
    out.append("  ├─ registry.group                          # findings / observations / recommendations / facts")
    out.append("  ├─ zz_core.probes.attach                   # bind a machine-checkable rule to each finding")
    out.append("  ├─ zz_integrations.*                       # optional live evidence (--browser/--llm/--db/--load)")
    out.append("  └─ zz_core.report.build_report             # -> zozi_forensic_audit.md + logs/*")
    out.append("zozi_verify.main   # reads logs/findings.jsonl -> logs/verdicts.jsonl")
    out.append("zozi_compile.main  # reads findings + verdicts -> logs/plan.json -> zozi_remediation_plan.md")
    out.append("```\n")

    for label in MODULE_ORDER:
        if label not in scanned:
            continue
        rows = scanned[label]
        blurb = LAYER_BLURB.get(label) or LAYER_BLURB.get(label.split("/")[0] + "/") or ""
        out.append(f"## `{label}` — {len(rows)} definitions\n")
        if blurb:
            out.append(f"*{blurb}*\n")
        out.append("| Line | Kind | Name | Signature | Check | First doc line |")
        out.append("|---|---|---|---|---|---|")
        for r in rows:
            name = r.qualname
            check = ""
            if r.is_check:
                check = f"`{r.check_name}`"
                if r.check_dimension:
                    check += f" · {r.check_dimension}"
            doc = r.doc.replace("|", "\\|")
            if len(doc) > 150:
                doc = doc[:147] + "…"
            out.append(
                f"| {r.lineno} | {r.kind} | `{name}` | `{r.args or '—'}` | {check or '—'} | {doc} |"
            )
        out.append("")

    out.append("## 3 · Change protocol\n")
    out.append(
        "1. Edit a detector or engine file.\n"
        "2. Regenerate this file (`python _zozi_audit/zz_core/inventory.py`).\n"
        "3. Run `--check`; a changed detector count without a changed file is drift.\n"
        "4. Run `python _zozi_audit/zozi_audit.py --self-test` before trusting any number.\n"
    )
    return "\n".join(out) + "\n"


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Inventory the audit suite's functions.")
    p.add_argument("--out", default=str(SUITE / "PLAN_FUNCTIONS.md"))
    p.add_argument("--json", action="store_true", help="print the inventory as JSON")
    p.add_argument("--check", action="store_true",
                   help="reconcile counts only; exit 1 when registry and AST disagree")
    args = p.parse_args(argv)

    # Running `python zz_core/inventory.py` puts the *script* directory on
    # sys.path[0], i.e. `zz_core/` itself — so a guard keyed on HERE never
    # fires and `import zz_core...` fails. Require the suite root explicitly.
    if str(SUITE) not in sys.path:
        sys.path.insert(0, str(SUITE))
    scanned = scan_all()
    facts = collect_facts(scanned)

    if args.json:
        payload = {
            "facts": facts,
            "modules": {k: [r.__dict__ for r in v] for k, v in scanned.items()},
        }
        print(json.dumps(payload, indent=2))
        return 0

    if args.check:
        problems = []
        if facts["checks_registered"] < 0:
            problems.append("registry unavailable — cannot reconcile the detector count")
        elif facts["checks_registered"] != facts["checks_decorated"]:
            problems.append(
                f"registry has {facts['checks_registered']} checks but AST shows "
                f"{facts['checks_decorated']} @check decorators")
        if not facts["checks_decorated"]:
            problems.append("no @check detectors found — scanners failed to parse or were removed")
        for mod in MODULE_ORDER:
            if mod.startswith("zz_scanners/s") and mod not in scanned:
                problems.append(f"scanner module missing: {mod}")
        if problems:
            for problem in problems:
                print(f"DRIFT: {problem}", file=sys.stderr)
            return 1
        print(f"OK: {facts['checks_decorated']} detectors, {facts['functions']} definitions, "
              f"{len(facts['dimensions'])} dimensions, {facts['modules']} modules")
        return 0

    text = render_markdown(scanned, facts)
    Path(args.out).write_text(text, encoding="utf-8")
    print(f"[inventory] wrote {args.out} — {facts['functions']} definitions, "
          f"{facts['checks_decorated']} detectors")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
