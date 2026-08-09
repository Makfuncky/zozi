"""Mirrors DBA02 detection from scripts/system_trackers/system_architecture_audit.py
(lines ~10297-10317) to verify create_all dev-gating without running the full audit.
Read-only verification script (does not modify the audit script)."""
from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
BACKEND = REPO / "backend"
IGNORE_DIRS = {
    ".git", "node_modules", ".venv", "venv", "__pycache__", ".mypy_cache",
    ".pytest_cache", ".ruff_cache", ".tox", "htmlcov", ".next", ".expo",
    ".kotlin", "gradle", "android", "ios", ".idea", ".vscode", "test-results",
    ".playwright-artifacts-0", "playwright-out", "static-tmp", ".web-build-test",
    "artifacts", "uploads", ".turbo", "dist", "build", "coverage",
    "playwright-report", "test-output", "tmp", ".hypothesis", ".kilo",
    ".kilocode", "worktrees", ".repo", "e2e", "__tests__", "__mocks__",
    ".storybook", ".web", "web-dist",
}

create_re = re.compile(r"Base\.metadata\.create_all|metadata\.create_all\(")
gate_re = re.compile(r"APP_ENV|development|is_development|settings\.ENV|getenv\(['\"]APP_ENV|config\.ENV", re.I)

red, yellow = [], []
for f in BACKEND.rglob("*.py"):
    if any(part in IGNORE_DIRS for part in f.parts):
        continue
    text = f.read_text(encoding="utf-8", errors="ignore")
    if not text:
        continue
    for i, line in enumerate(text.splitlines(), 1):
        if create_re.search(line):
            if gate_re.search(text):
                yellow.append(f"{f.relative_to(REPO)}:{i}")
            else:
                red.append(f"{f.relative_to(REPO)}:{i}")
            break

print(f"DBA02 RED   (not dev-gated): {len(red)}")
for r in red:
    print("  RED  ", r)
print(f"DBA02 YELLOW (appears gated): {len(yellow)}")
for y in yellow:
    print("  YEL  ", y)
print("RESULT:", "PASS - zero RED" if not red else "FAIL - RED remains")
