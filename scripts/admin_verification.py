from __future__ import annotations

import argparse
import os
from pathlib import Path
import subprocess
import sys
import time


REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = REPO_ROOT / "backend"
WEB_ROOT = REPO_ROOT / "frontend" / "web_app"
MOBILE_ROOT = REPO_ROOT / "frontend" / "mobile_app"
DEFAULT_PYTHON = REPO_ROOT / ".venv" / "Scripts" / "python.exe"
PYTHON_BIN = str(DEFAULT_PYTHON if DEFAULT_PYTHON.exists() else Path(sys.executable))
NPM_BIN = "npm.cmd" if os.name == "nt" else "npm"
NPX_BIN = "npx.cmd" if os.name == "nt" else "npx"

BACKEND_TESTS = [
    "tests/test_admin_management.py",
    "tests/test_admin_hierarchy_payouts.py",
    "tests/test_admin_export.py",
    "tests/test_admin_cleanup.py",
    "tests/test_admin_analytics.py",
    "tests/test_admin_analytics_timeseries.py",
    "tests/test_banners.py",
    "tests/test_flash_sales.py",
    "tests/test_returns.py",
    "tests/test_coupons.py",
    "tests/test_invoices.py",
    "tests/test_product_verification.py",
    "tests/test_email_campaigns.py",
    "tests/test_email_ab.py",
    "tests/test_logistics_partner.py",
]

WEB_TESTS = [
    "src/__tests__/pages/products.test.tsx",
    "src/__tests__/pages/logisticsPartnerPages.test.tsx",
    "src/__tests__/pages/adminLogisticsPages.test.tsx",
    "src/__tests__/pages/adminManagementPages.test.tsx",
    "src/__tests__/pages/adminPaymentsPage.test.tsx",
    "src/__tests__/lib/adminPermissions.test.ts",
]

MOBILE_TESTS = [
    "lib/__tests__/adminGuardedScreens.test.tsx",
    "lib/__tests__/adminDashboardScreen.test.ts",
    "lib/__tests__/adminManagementUtils.test.ts",
    "lib/__tests__/adminListUtils.test.ts",
]


def base_env() -> dict[str, str]:
    env = os.environ.copy()
    env.setdefault("BACKUP_ENABLED", "false")
    env.setdefault("PYTHONUNBUFFERED", "1")
    return env


def print_section(title: str) -> None:
    print(f"\n=== {title} ===")


def run_command(label: str, command: list[str], cwd: Path) -> None:
    print(f"[{label}] {' '.join(command)}")
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

    if completed.returncode != 0:
        raise RuntimeError(f"{label} failed with exit code {completed.returncode} after {duration:.1f}s")

    print(f"[ok] {label} ({duration:.1f}s)")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the widened admin verification sweep across backend, web, mobile, and type-check stages.",
    )
    parser.add_argument("--skip-backend", action="store_true", help="Skip backend admin pytest suites.")
    parser.add_argument("--skip-web", action="store_true", help="Skip web admin Jest and TypeScript checks.")
    parser.add_argument("--skip-mobile", action="store_true", help="Skip mobile admin Jest and full TypeScript checks.")
    parser.add_argument("--skip-typecheck", action="store_true", help="Skip web/mobile TypeScript checks.")
    return parser.parse_args()


def run_backend() -> None:
    print_section("Backend Admin Regression")
    run_command(
        "backend admin pytest",
        [PYTHON_BIN, "-m", "pytest", *BACKEND_TESTS, "-q"],
        BACKEND_ROOT,
    )


def run_web(skip_typecheck: bool) -> None:
    print_section("Web Admin Regression")
    run_command(
        "web admin jest",
        [NPX_BIN, "jest", "--runInBand", "--runTestsByPath", *WEB_TESTS],
        WEB_ROOT,
    )
    if not skip_typecheck:
        run_command("web tsc", [NPX_BIN, "tsc", "--noEmit"], WEB_ROOT)


def run_mobile(skip_typecheck: bool) -> None:
    print_section("Mobile Admin Regression")
    run_command(
        "mobile admin jest",
        [NPM_BIN, "test", "--", "--runTestsByPath", *MOBILE_TESTS],
        MOBILE_ROOT,
    )
    if not skip_typecheck:
        run_command("mobile tsc", [NPX_BIN, "tsc", "--noEmit"], MOBILE_ROOT)


def main() -> int:
    args = parse_args()

    if not args.skip_backend:
        run_backend()

    if not args.skip_web:
        run_web(args.skip_typecheck)

    if not args.skip_mobile:
        run_mobile(args.skip_typecheck)

    print("\nAdmin verification sweep passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())