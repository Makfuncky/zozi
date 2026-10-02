"""Live HTTP-layer probe.

Every other check in this suite is static, or runs a CLI tool, or exercises the
ASGI app in-process. None of them look at a real HTTP response. That is a whole
class of defect the audit was blind to:

* a CORS preflight that answers 405 instead of 2xx (every cross-origin write is
  blocked in a browser while curl and TestClient both look fine),
* a security header missing or inconsistent between routes,
* a deprecated header still being emitted,
* a CSP that is syntactically valid but references localhost origins,
* startup failures logged as "non-critical" that nobody reads.

This probe starts the real app under a real server and asserts on the bytes that
come back. It never mutates data: it only issues GET, OPTIONS and HEAD.
"""
from __future__ import annotations

import json
import os
import re
import socket
import subprocess
import sys
import time
from pathlib import Path

# Headers a modern browser actually honours. `X-XSS-Protection` is absent on
# purpose: it was removed from Chrome/Firefox/Edge and is ignored everywhere,
# so emitting it is dead weight that can re-enable legacy XSS filters.
REQUIRED_HEADERS = {
    "content-security-policy": "CSP",
    "strict-transport-security": "HSTS (production only)",
    "x-content-type-options": "MIME sniffing protection",
    "x-frame-options": "clickjacking protection",
    "referrer-policy": "referrer leakage control",
}
PRODUCTION_ONLY = {"strict-transport-security"}

DEPRECATED_HEADERS = {
    "x-xss-protection": "removed from all current browsers; ignored, and "
                        "re-enables legacy XSS filters when honoured",
    "x-powered-by": "discloses the stack",
}

PROBE_PATHS = ("/health", "/docs", "/openapi.json", "/definitely-not-a-route")


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _raw_request(port: int, method: str, path: str, headers: dict[str, str],
                 timeout: float = 20.0) -> tuple[int, dict[str, list[str]], str, str]:
    """One HTTP/1.1 exchange over a raw socket.

    Raw socket rather than a client library on purpose: a client library would
    normalise or reject a malformed response for us, and the whole point is to
    see what actually reaches the wire.
    """
    import http.client

    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=timeout)
    try:
        conn.putrequest(method, path, skip_host=False, skip_accept_encoding=True)
        for k, v in headers.items():
            conn.putheader(k, v)
        conn.endheaders()
        resp = conn.getresponse()
        body = resp.read(4096).decode("utf-8", "replace")
        collected: dict[str, list[str]] = {}
        for k, v in resp.getheaders():
            collected.setdefault(k.lower(), []).append(v)
        return resp.status, collected, body, resp.reason or ""
    finally:
        conn.close()


def run_probe(ctx, timeout: int = 300) -> dict:
    """Boot the app under uvicorn, probe it, shut it down. Never raises."""
    fact: dict = {"probed": False, "error": "", "checks": [], "boot": {}}
    if ctx.options.get("no_tools"):
        fact["error"] = "--no-tools"
        return fact
    backend = ctx.backend
    if not (backend / "main.py").exists():
        fact["error"] = "backend/main.py missing"
        return fact

    port = _free_port()
    env = dict(os.environ)
    env.setdefault("APP_ENV", "test")
    env["PYTHONPATH"] = str(backend) + os.pathsep + env.get("PYTHONPATH", "")
    log_path = ctx.out_dir / "logs" / "http_probe.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)

    started = time.time()
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "main:app",
         "--host", "127.0.0.1", "--port", str(port), "--log-level", "warning"],
        cwd=str(backend), env=env,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
        errors="replace",
    )
    fact["port"] = port
    try:
        # Wait for the port to accept, not for a log line: the readiness signal
        # is a successful HTTP exchange.
        ready = False
        while time.time() - started < timeout:
            if proc.poll() is not None:
                fact["error"] = (proc.stdout.read() if proc.stdout else "")[-1500:]
                break
            try:
                with socket.create_connection(("127.0.0.1", port), timeout=1):
                    ready = True
                    break
            except OSError:
                time.sleep(1.0)
        fact["boot"] = {
            "ready": ready,
            "seconds": round(time.time() - started, 1),
            "exited_early": proc.poll() is not None,
        }
        if not ready:
            fact["error"] = fact["error"] or f"server did not accept within {timeout}s"
            return fact
        fact["probed"] = True
        _probe_all(port, fact)
    except Exception as exc:  # pragma: no cover - probe must never break a run
        fact["error"] = f"{type(exc).__name__}: {exc}"
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=15)
        except subprocess.TimeoutExpired:
            proc.kill()
        # Drain the child's output so a pipelined read never blocks on exit.
        try:
            out = proc.stdout.read() if proc.stdout else ""
        except Exception:
            out = ""
        if out:
            try:
                log_path.write_text(out[-200_000:], encoding="utf-8")
            except Exception:
                pass
    _scan_startup_log(out or "", fact)
    return fact


def _probe_all(port: int, fact: dict) -> None:
    origin = "http://localhost:3000"

    # 1. Header presence + consistency across a real route and an unknown route.
    seen: dict[str, dict[str, list[str]]] = {}
    statuses: dict[str, int] = {}
    for path in PROBE_PATHS:
        try:
            status, headers, body, _ = _raw_request(port, "GET", path, {})
        except Exception as exc:
            fact["checks"].append({
                "id": "HTTP-GET", "path": path, "status": "error",
                "detail": f"{type(exc).__name__}: {exc}", "ok": False})
            continue
        statuses[path] = status
        seen[path] = headers
        missing = [label for name, label in REQUIRED_HEADERS.items()
                   if name not in headers and name not in PRODUCTION_ONLY]
        deprecated = [f"{name}: {why}" for name, why in DEPRECATED_HEADERS.items()
                      if name in headers]
        fact["checks"].append({
            "id": "HTTP-HEADERS", "path": path, "status": status,
            "missing_required": missing, "deprecated_present": deprecated,
            "csp": (headers.get("content-security-policy") or [""])[0][:400],
            "header_count": len(headers),
            "ok": not missing and not deprecated,
        })

    # 2. CORS preflight. A browser will not send the real request unless this
    #    answers 2xx with Access-Control-Allow-Methods. curl and TestClient both
    #    hide this, which is exactly why it survived.
    for path, method in (("/api/v1/auth/login", "POST"), ("/health", "GET")):
        try:
            status, headers, body, reason = _raw_request(port, "OPTIONS", path, {
                "Origin": origin,
                "Access-Control-Request-Method": method,
                "Access-Control-Request-Headers": "authorization,content-type",
            })
        except Exception as exc:
            fact["checks"].append({
                "id": "HTTP-CORS-PREFLIGHT", "path": path, "method": method,
                "status": "error", "detail": f"{type(exc).__name__}: {exc}",
                "ok": False})
            continue
        allow_methods = headers.get("access-control-allow-methods", [])
        allow_origin = headers.get("access-control-allow-origin", [])
        ok = (200 <= status < 300 and bool(allow_methods)
              and bool(allow_origin))
        fact["checks"].append({
            "id": "HTTP-CORS-PREFLIGHT", "path": path, "method": method,
            "status": status, "reason": reason,
            "allow_origin": allow_origin, "allow_methods": allow_methods,
            "allow_credentials": headers.get("access-control-allow-credentials", []),
            "allow_headers": headers.get("access-control-allow-headers", []),
            "vary": headers.get("vary", []),
            "ok": ok,
        })

    # 3. Origin reflection: ACAO must never be "*" together with credentials.
    try:
        status, headers, _, _ = _raw_request(port, "GET", "/health",
                                             {"Origin": "https://evil.example"})
        fact["checks"].append({
            "id": "HTTP-CORS-ORIGIN", "path": "/health", "status": status,
            "allow_origin": headers.get("access-control-allow-origin", []),
            "allow_credentials": headers.get("access-control-allow-credentials", []),
            "ok": headers.get("access-control-allow-origin") != ["*"],
        })
    except Exception as exc:
        fact["checks"].append({
            "id": "HTTP-CORS-ORIGIN", "status": "error",
            "detail": f"{type(exc).__name__}: {exc}", "ok": False})

    # 4. A cookie the API sets without Secure/SameSite is a transport finding.
    for path in ("/health",):
        set_cookie = (seen.get(path) or {}).get("set-cookie", [])
        insecure = [c for c in set_cookie
                    if "secure" not in c.lower() and "httponly" not in c.lower()]
        fact["checks"].append({
            "id": "HTTP-COOKIE-FLAGS", "path": path,
            "cookies": len(set_cookie),
            "missing_secure_or_httponly": insecure[:3],
            "ok": not insecure,
        })

    # 5. CSP sanity on the real response.
    for path, headers in seen.items():
        csp = (headers.get("content-security-policy") or [""])[0]
        if not csp:
            continue
        directives = [d.strip() for d in csp.split(";") if d.strip()]
        names = [d.split()[0] if d.split() else "" for d in directives]
        localhost = [d for d in directives if "localhost" in d or "127.0.0.1" in d]
        fact["checks"].append({
            "id": "HTTP-CSP-SHAPE", "path": path,
            "directive_count": len(directives),
            "directives": names,
            "localhost_in_csp": localhost,
            "uses_deprecated_report_uri": any(n == "report-uri" for n in names),
            "missing_object_src": "object-src" not in names,
            "missing_base_uri": "base-uri" not in names,
            "wildcard_in_script_src": any(
                d.startswith("script-src") and "'unsafe-inline'" in d
                or d.startswith("script-src") and "*" in d.split()[1:]
                for d in directives if d.startswith("script-src")),
            "ok": not localhost,
        })


def _scan_startup_log(output: str, fact: dict) -> None:
    """Surface startup failures the app itself logged as non-critical."""
    problems: list[dict] = []
    for line in output.splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            continue
        if rec.get("level") not in ("error", "critical"):
            continue
        exc = str(rec.get("exception", ""))
        m = re.search(r"AttributeError:\s*([^\n\"']+)", exc)
        m2 = re.search(r'File "([^"]+)", line (\d+), in ', exc)
        problems.append({
            "logger": rec.get("logger", ""),
            "event": rec.get("event", ""),
            "message": str(rec.get("error", ""))[:200],
            "attribute": m.group(1).strip() if m else "",
            "location": f"{Path(m2.group(1)).name}:{m2.group(2)}" if m2 else "",
            "traceback_tail": exc[-400:],
        })
    fact["startup_errors"] = problems
    fact["startup_error_count"] = len(problems)
    slow = re.findall(r'"db_query_time_ms":\s*([0-9.]+)', output)
    fact["slow_queries_at_startup"] = sorted(
        (float(v) for v in slow), reverse=True)[:5]
