from __future__ import annotations

import argparse
import contextlib
import importlib
import importlib.util
import os
from pathlib import Path
import socket
import subprocess
import sys
import time
from typing import Iterator
from urllib.error import URLError
from urllib.request import urlopen


REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = REPO_ROOT / "backend"
WEB_ROOT = REPO_ROOT / "frontend" / "web_app"
MOBILE_ROOT = REPO_ROOT / "frontend" / "mobile_app"
DEFAULT_PYTHON = REPO_ROOT / ".venv" / "Scripts" / "python.exe"
PYTHON_BIN = str(DEFAULT_PYTHON if DEFAULT_PYTHON.exists() else Path(sys.executable))
NPM_BIN = "npm.cmd" if os.name == "nt" else "npm"
NPX_BIN = "npx.cmd" if os.name == "nt" else "npx"

if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

DEMO_ACCOUNTS = (
    ("admin", "admin@zozi.com", "admin123"),
    ("supplier", "supplier@zozi.com", "supplier123"),
    ("customer", "customer@zozi.com", "customer123"),
    ("logistics_partner", "logistics@zozi.com", "logistics123"),
)


def base_env() -> dict[str, str]:
    env = os.environ.copy()
    env.setdefault("BACKUP_ENABLED", "false")
    env.setdefault("PYTHONUNBUFFERED", "1")
    return env


def print_section(title: str) -> None:
    print(f"\n=== {title} ===")


def run_command(
    label: str,
    command: list[str],
    cwd: Path,
    retries: int = 0,
    retry_on_output_substrings: tuple[str, ...] = (),
) -> None:
    print(f"[{label}] {' '.join(command)}")
    max_attempts = retries + 1

    for attempt in range(1, max_attempts + 1):
        started = time.perf_counter()
        completed = subprocess.run(
            command,
            cwd=cwd,
            env=base_env(),
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            check=False,
        )
        duration = time.perf_counter() - started

        if completed.stdout:
            print(completed.stdout.rstrip())
        if completed.stderr:
            print(completed.stderr.rstrip())

        if completed.returncode == 0:
            print(f"[ok] {label} ({duration:.1f}s)")
            return

        combined_output = f"{completed.stdout}\n{completed.stderr}".lower()
        should_retry = (
            attempt < max_attempts
            and bool(retry_on_output_substrings)
            and any(token.lower() in combined_output for token in retry_on_output_substrings)
        )

        if should_retry:
            print(
                f"[warn] {label} attempt {attempt}/{max_attempts} failed with a transient signature; retrying..."
            )
            time.sleep(2)
            continue

        raise RuntimeError(f"{label} failed with exit code {completed.returncode} after {duration:.1f}s")


def ensure_demo_accounts() -> None:
    print_section("Database Repair")
    migrations = importlib.import_module("utils.migrations")
    seed_module = importlib.import_module("db.seed")

    try:
        migrations.upgrade_database_to_head()
        print("Database migrations applied to the active database.")
    except Exception as exc:
        print(f"[warn] Alembic upgrade skipped: {exc}")
        sync_result = migrations.sync_sqlite_schema_with_models()
        print(
            "SQLite schema synced from ORM metadata: "
            f"tables_created={sync_result.get('tables_created', 0)} "
            f"columns_added={sync_result.get('columns_added', 0)}"
        )
        sync_errors = sync_result.get("errors") or []
        if sync_errors:
            for error in sync_errors:
                print(f"[warn] schema sync: {error}")
    seed_module.seed_data()
    print("Demo accounts and catalog ensured in the active database.")


def verify_demo_logins() -> None:
    print_section("Backend Auth")
    sys.path.insert(0, str(BACKEND_ROOT))

    module_spec = importlib.util.spec_from_file_location("zozi_backend_main", BACKEND_ROOT / "main.py")
    if module_spec is None or module_spec.loader is None:
        raise RuntimeError("Unable to load backend main module for health verification")

    main = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(main)

    from fastapi.testclient import TestClient

    with TestClient(main.app) as client:
        health = client.get("/health")
        if health.status_code != 200:
            raise RuntimeError(f"/health returned {health.status_code}: {health.text}")
        print(f"health: {health.status_code} {health.text}")

        for role, username, password in DEMO_ACCOUNTS:
            response = client.post(
                "/auth/login",
                data={"username": username, "password": password},
                headers={"content-type": "application/x-www-form-urlencoded"},
            )
            if response.status_code != 200:
                raise RuntimeError(f"{role} login failed: {response.status_code} {response.text}")
            print(f"login:{role}=ok")


def port_open(host: str, port: int) -> bool:
    with contextlib.closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
        sock.settimeout(0.5)
        return sock.connect_ex((host, port)) == 0


def wait_for_http(url: str, timeout_seconds: int, process: subprocess.Popen[str] | None = None) -> None:
    deadline = time.time() + timeout_seconds
    last_error: str | None = None

    while time.time() < deadline:
      if process is not None and process.poll() is not None:
          raise RuntimeError("Backend process exited before it became healthy")
      try:
          with urlopen(url, timeout=2) as response:
              if 200 <= response.status < 500:
                  return
      except URLError as exc:
          last_error = str(exc)
      except OSError as exc:
          last_error = str(exc)
      time.sleep(1)

    raise RuntimeError(f"Timed out waiting for {url}: {last_error or 'no response'}")


@contextlib.contextmanager
def managed_backend_server() -> Iterator[None]:
    if port_open("127.0.0.1", 8000):
        print("Backend server already reachable at http://127.0.0.1:8000")
        yield
        return

    print("Starting backend server for Playwright checks...")
    process = subprocess.Popen(
        [PYTHON_BIN, "-m", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", "8000"],
        cwd=BACKEND_ROOT,
        env=base_env(),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        text=True,
    )
    try:
        wait_for_http("http://127.0.0.1:8000/health", 60, process=process)
        yield
    finally:
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a full-stack ZOZI health sweep across database, backend, web, mobile, and browser auth/fulfillment smoke checks.",
    )
    parser.add_argument("--skip-playwright", action="store_true", help="Skip browser e2e smoke checks.")
    parser.add_argument("--skip-web", action="store_true", help="Skip web unit and type checks.")
    parser.add_argument("--skip-mobile", action="store_true", help="Skip mobile unit and type checks.")
    parser.add_argument("--skip-backend-tests", action="store_true", help="Skip backend pytest sweep.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    ensure_demo_accounts()
    verify_demo_logins()

    if not args.skip_backend_tests:
        print_section("Backend Tests")
        run_command("backend pytest", [PYTHON_BIN, "-m", "pytest", "backend/tests", "-q"], REPO_ROOT)

    if not args.skip_web:
        print_section("Web Tests")
        run_command("web jest", [NPM_BIN, "test"], WEB_ROOT)
        run_command("web tsc", [NPX_BIN, "tsc", "--noEmit"], WEB_ROOT)

    if not args.skip_mobile:
        print_section("Mobile Tests")
        run_command("mobile jest", [NPM_BIN, "test"], MOBILE_ROOT)
        run_command("mobile tsc", [NPX_BIN, "tsc", "--noEmit"], MOBILE_ROOT)

    if not args.skip_playwright:
        print_section("Browser Smoke")
        with managed_backend_server():
            run_command(
                "playwright auth smoke",
                [
                    NPM_BIN,
                    "run",
                    "test:e2e",
                    "--",
                    "--workers=1",
                    "e2e/auth-role-login.spec.ts",
                ],
                WEB_ROOT,
                retries=1,
                retry_on_output_substrings=("err_aborted",),
            )
            run_command(
                "playwright admin data ops smoke",
                [
                    NPM_BIN,
                    "run",
                    "test:e2e",
                    "--",
                    "--workers=1",
                    "e2e/admin-data-ops.spec.ts",
                ],
                WEB_ROOT,
                retries=1,
                retry_on_output_substrings=("err_aborted",),
            )
            run_command(
                "playwright fulfillment smoke",
                [
                    NPM_BIN,
                    "run",
                    "test:e2e",
                    "--",
                    "--workers=1",
                    "e2e/fulfillment-role-flow.spec.ts",
                ],
                WEB_ROOT,
                retries=1,
                retry_on_output_substrings=("err_aborted",),
            )

    print("\nAll requested health checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())