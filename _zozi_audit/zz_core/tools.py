"""Subprocess tooling for the ZOZI audit.

Every external command is optional: failures are captured as ``ToolResult``
records and never abort the audit. Commands run with timeouts and truncated
output tails.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from urllib import request as urllib_request

from .model import ScanContext, ToolResult
from .util import read_text, truncate

DEFAULT_TIMEOUT = float(os.environ.get("ZOZI_AUDIT_TOOL_TIMEOUT", "180"))
BIG_TIMEOUT = float(os.environ.get("ZOZI_AUDIT_BIG_TIMEOUT", "600"))
#: Untruncated stdout kept for parsing. `stdout_tail` is a *display* buffer with
#: the middle elided; counting inside it under-reports every metric of a long
#: run (a 119-error tsc run reported 25). 24 MB is far above any realistic
#: compiler or pytest output and bounds memory during the sweep.
FULL_OUTPUT_CAP = int(os.environ.get("ZOZI_AUDIT_FULL_OUTPUT_CAP", 24 * 1024 * 1024))


def which(cmd: str) -> str:
    if os.name == "nt":
        for ext in ("", ".cmd", ".exe", ".bat", ".ps1"):
            found = shutil.which(cmd + ext)
            if found:
                return found
        return ""
    return shutil.which(cmd) or ""


def run(
    cmd,
    cwd: Path | None = None,
    timeout: float = DEFAULT_TIMEOUT,
    env: dict | None = None,
    name: str = "",
    shell: bool | None = None,
) -> ToolResult:
    """Run a command, capture everything, never raise."""
    if isinstance(cmd, str):
        shell = True if shell is None else shell
        pretty = cmd
    else:
        shell = False if shell is None else shell
        pretty = " ".join(str(c) for c in cmd)
    started = time.time()
    merged_env = dict(os.environ)
    merged_env.setdefault("PYTHONIOENCODING", "utf-8")
    merged_env.setdefault("CI", "1")
    if env:
        merged_env.update({k: str(v) for k, v in env.items()})
    try:
        proc = subprocess.run(
            cmd if not shell else pretty,
            cwd=str(cwd) if cwd else None,
            capture_output=True,
            text=True,
            errors="replace",
            timeout=timeout,
            shell=shell,
            env=merged_env,
        )
        return ToolResult(
            name=name or pretty[:80],
            cmd=pretty,
            exit_code=proc.returncode,
            duration_s=round(time.time() - started, 2),
            stdout_tail=truncate(proc.stdout or "", 6000),
            stderr_tail=truncate(proc.stderr or "", 3000),
            available=True,
            full_stdout=(proc.stdout or "")[:FULL_OUTPUT_CAP],
        )
    except subprocess.TimeoutExpired as exc:
        return ToolResult(
            name=name or pretty[:80],
            cmd=pretty,
            exit_code=None,
            duration_s=round(time.time() - started, 2),
            stdout_tail=truncate(getattr(exc, "stdout", "") or "", 3000),
            stderr_tail=f"TIMEOUT after {timeout}s",
            available=True,
            skipped_reason=f"timeout>{timeout}s",
            full_stdout=(getattr(exc, "stdout", "") or "")[:FULL_OUTPUT_CAP],
        )
    except FileNotFoundError:
        return ToolResult(
            name=name or pretty[:80], cmd=pretty, available=False,
            skipped_reason="executable-not-found",
        )
    except Exception as exc:  # pragma: no cover - defensive
        return ToolResult(
            name=name or pretty[:80], cmd=pretty, available=True,
            skipped_reason=f"{type(exc).__name__}: {exc}",
        )


def capture(ctx: ScanContext, name: str, cmd, cwd: Path | None = None,
            timeout: float = DEFAULT_TIMEOUT, **kw) -> ToolResult:
    """Run + register in ctx.tools so the report includes the ledger."""
    res = run(cmd, cwd=cwd, timeout=timeout, name=name, **kw)
    ctx.tools[name] = res
    return res


# --------------------------------------------------------------------------- #
# Probes
# --------------------------------------------------------------------------- #

def probe_all(ctx: ScanContext) -> dict:
    probes = {
        "python": [sys.executable, "--version"],
        "node": ["node", "--version"],
        "pnpm": ["pnpm", "--version"],
        "npm": ["npm", "--version"],
        "git": ["git", "--version"],
        "ruff": ["ruff", "--version"],
        "pytest": [sys.executable, "-m", "pytest", "--version"],
        "alembic": ["alembic", "--version"],
        "playwright": ["npx", "playwright", "--version"],
        "uv": ["uv", "--version"],
    }
    for name, cmd in probes.items():
        binary = cmd[0]
        if binary == sys.executable or which(binary):
            res = run(cmd, cwd=ctx.root, timeout=60, name=f"probe:{name}")
        else:
            res = ToolResult(name=f"probe:{name}", cmd=" ".join(cmd),
                             available=False, skipped_reason="not-installed")
        ctx.tools[f"probe:{name}"] = res
    # Ollama reachability (HTTP)
    url = ctx.options.get("ollama_url", "http://localhost:11434")
    ctx.tools["probe:ollama"] = _http_probe(f"{url.rstrip('/')}/api/tags", "ollama")
    return ctx.tools


def _http_probe(url: str, name: str, timeout: float = 3.0) -> ToolResult:
    started = time.time()
    try:
        with urllib_request.urlopen(url, timeout=timeout) as resp:
            body = resp.read(2000).decode("utf-8", errors="replace")
        return ToolResult(name=f"probe:{name}", cmd=url, exit_code=0,
                          duration_s=round(time.time() - started, 2),
                          stdout_tail=truncate(body, 500), available=True)
    except Exception as exc:
        return ToolResult(name=f"probe:{name}", cmd=url, available=False,
                          skipped_reason=f"unreachable: {type(exc).__name__}")


# --------------------------------------------------------------------------- #
# Boot / pre-flight commands
# --------------------------------------------------------------------------- #

def boot_smoke(ctx: ScanContext) -> ToolResult:
    """Try the canonical import from the repo root, then the adapted one."""
    root_cmd = [sys.executable, "-c",
                "from backend.main import app; print(len(app.routes))"]
    res = run(root_cmd, cwd=ctx.root, timeout=120, name="boot:root")
    if res.exit_code == 0:
        ctx.tools["boot:root"] = res
        return res
    ctx.tools["boot:root"] = res
    adapted = [sys.executable, "-c",
               "from main import app; print(len(app.routes))"]
    res2 = run(adapted, cwd=ctx.backend, timeout=180, name="boot:backend-cwd",
               env={"APP_ENV": ctx.options.get("app_env", "test")})
    ctx.tools["boot:backend-cwd"] = res2
    return res2 if res2.exit_code == 0 else res


def run_pytest_collect(ctx: ScanContext) -> ToolResult:
    res = run([sys.executable, "-m", "pytest", "--collect-only", "-q",
               "--no-header", "-p", "no:cacheprovider"],
              cwd=ctx.backend, timeout=BIG_TIMEOUT, name="pytest:collect")
    ctx.tools["pytest:collect"] = res
    return res


def run_pytest_architecture(ctx: ScanContext) -> ToolResult:
    arch = ctx.backend / "tests" / "architecture"
    if not arch.exists():
        res = ToolResult(name="pytest:architecture", available=False,
                         skipped_reason="tests/architecture missing")
        ctx.tools["pytest:architecture"] = res
        return res
    res = run([sys.executable, "-m", "pytest", str(arch), "-q", "--no-header",
               "-p", "no:cacheprovider", "--timeout=120"],
              cwd=ctx.backend, timeout=900, name="pytest:architecture")
    if res.exit_code == 4 and "unrecognized arguments: --timeout" in (
            (res.stderr_tail or "") + (res.stdout_tail or "")):
        # pytest-timeout is not installed in this environment; the flag, not the
        # test suite, caused the failure. Retry without it so the architecture
        # laws are actually exercised.
        res = run([sys.executable, "-m", "pytest", str(arch), "-q", "--no-header",
                   "-p", "no:cacheprovider"],
                  cwd=ctx.backend, timeout=900, name="pytest:architecture:no-timeout")
    if getattr(res, "skipped_reason", "").startswith("timeout"):
        # A timeout is a FAIL (the laws were not proven), never a silent SKIP.
        res.skipped_reason = ""
        res.exit_code = 124
        res.stderr_tail = ((res.stderr_tail or "") + "\nTIMEOUT: the architecture "
                           "law suite did not finish within 900s. Treat the laws "
                           "as UNVERIFIED.")[-3000:]
    ctx.tools["pytest:architecture"] = res
    return res


def run_ruff(ctx: ScanContext) -> ToolResult:
    exe = which("ruff")
    if not exe:
        res = ToolResult(name="ruff", available=False, skipped_reason="ruff not installed")
        ctx.tools["ruff"] = res
        return res
    res = run([exe, "check", ".", "--output-format=concise",
               "--exclude", "tests", "--statistics", "--quiet"],
              cwd=ctx.backend, timeout=BIG_TIMEOUT, name="ruff")
    ctx.tools["ruff"] = res
    return res


def run_tsc(ctx: ScanContext) -> ToolResult:
    web = ctx.frontend / "web_app"
    if not (web / "tsconfig.json").exists():
        res = ToolResult(name="tsc", available=False,
                         skipped_reason="web_app/tsconfig.json missing")
        ctx.tools["tsc"] = res
        return res
    # Prefer the local binary. `pnpm exec` runs this repo's supply-chain
    # preinstall hook first, which can resolve/install for minutes and then
    # produce no compiler output at all — the audit then reported
    # "0 TypeScript errors" next to a FAIL, which is worse than no report.
    local = web / "node_modules" / ".bin" / ("tsc.cmd" if os.name == "nt" else "tsc")
    if local.exists():
        res = run([str(local), "--noEmit"], cwd=web, timeout=BIG_TIMEOUT, name="tsc")
    else:
        res = run("pnpm exec tsc --noEmit", cwd=web, timeout=BIG_TIMEOUT, name="tsc")
    ctx.tools["tsc"] = res
    return res


def run_next_build(ctx: ScanContext) -> ToolResult:
    web = ctx.frontend / "web_app"
    if not (web / "package.json").exists():
        res = ToolResult(name="next:build", available=False,
                         skipped_reason="web_app/package.json missing")
        ctx.tools["next:build"] = res
        return res
    res = run("pnpm build", cwd=web, timeout=BIG_TIMEOUT * 2, name="next:build")
    ctx.tools["next:build"] = res
    return res


def run_alembic(ctx: ScanContext) -> ToolResult:
    ini = ctx.backend / "alembic" / "alembic.ini"
    if not ini.exists():
        res = ToolResult(name="alembic:heads", available=False,
                         skipped_reason="alembic/alembic.ini missing")
        ctx.tools["alembic:heads"] = res
        return res
    res = run(["alembic", "-c", str(ini), "heads"], cwd=ctx.backend,
              timeout=180, name="alembic:heads")
    ctx.tools["alembic:heads"] = res
    return res


def run_pnpm_frozen_check(ctx: ScanContext) -> ToolResult:
    web = ctx.frontend / "web_app"
    if not (web / "pnpm-lock.yaml").exists():
        res = ToolResult(name="pnpm:frozen", available=False,
                         skipped_reason="pnpm-lock.yaml missing")
        ctx.tools["pnpm:frozen"] = res
        return res
    res = run("pnpm install --frozen-lockfile --offline", cwd=web,
              timeout=BIG_TIMEOUT, name="pnpm:frozen")
    ctx.tools["pnpm:frozen"] = res
    return res


def run_pip_audit(ctx: ScanContext) -> ToolResult:
    exe = which("pip-audit")
    if not exe:
        res = ToolResult(name="pip-audit", available=False, skipped_reason="not installed")
        ctx.tools["pip-audit"] = res
        return res
    res = run([exe, "-r", str(ctx.backend / "requirements.txt"), "--format=json"],
              cwd=ctx.root, timeout=BIG_TIMEOUT, name="pip-audit")
    ctx.tools["pip-audit"] = res
    return res


def run_gitleaks(ctx: ScanContext) -> ToolResult:
    exe = which("gitleaks")
    if not exe:
        res = ToolResult(name="gitleaks", available=False, skipped_reason="not installed")
        ctx.tools["gitleaks"] = res
        return res
    res = run([exe, "detect", "--no-git", "--source", str(ctx.root),
               "--report-format", "json", "--redact", "--exit-code", "0"],
              cwd=ctx.root, timeout=BIG_TIMEOUT, name="gitleaks")
    ctx.tools["gitleaks"] = res
    return res


# --------------------------------------------------------------------------- #
# Ollama (local LLM)
# --------------------------------------------------------------------------- #

def ollama_chat(ctx: ScanContext, prompt: str, model: str | None = None,
                timeout: float = 120.0) -> tuple[bool, str]:
    """Blocking call to Ollama /api/chat. Returns (ok, text)."""
    base = ctx.options.get("ollama_url", "http://localhost:11434").rstrip("/")
    model = model or ctx.options.get("ollama_model", "phi3:mini")
    payload = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
        "options": {"temperature": 0.0, "num_predict": 600},
    }).encode("utf-8")
    req = urllib_request.Request(
        f"{base}/api/chat", data=payload,
        headers={"Content-Type": "application/json"}, method="POST",
    )
    try:
        with urllib_request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8", errors="replace"))
        return True, (data.get("message", {}) or {}).get("content", "")
    except Exception as exc:
        return False, f"ollama-unavailable: {type(exc).__name__}: {exc}"
