import os
import re
import subprocess

import pytest

REMOVED_SECRETS = [
    "440c_REDACTED_TEST_FIXTURE",
    "npg_REDACTED_TEST_FIXTURE",
    "cfat_REDACTED_TEST_FIXTURE",
    "cd76_REDACTED_TEST_FIXTURE",
]

EXCLUDED_PREFIXES = [
    "_audit/",
    "tests/",
    "backend/tests/",
    ".env.example",
    "backend/.env.example",
    "docker-compose",
    "monitoring/docker-compose",
    ".githooks/",
    ".github/",
    "frontend/mobile_app/web-dist/",
    "documents/",
    "backend/scripts/_debug/",
]

SECRET_PATTERNS = [
    re.compile(r"npg_[A-Za-z0-9]+"),
    re.compile(r"SECRET_KEY=\S+"),
    re.compile(r"POSTGRES_PASSWORD=\S+"),
    re.compile(r"CLOUDFLARE_API_TOKEN=\S+"),
    re.compile(r"FIELD_ENCRYPTION_KEY=\S+"),
    re.compile(r"password=['\"][^'\"]+['\"]"),
    re.compile(r"api_key=['\"][^'\"]+['\"]"),
    re.compile(r"api_token=['\"][^'\"]+['\"]"),
]


def _get_tracked_files() -> list[str]:
    result = subprocess.run(
        ["git", "ls-files"],
        capture_output=True,
        text=True,
        check=True,
    )
    return [line for line in result.stdout.splitlines() if line]


def _get_worktree_files() -> list[str]:
    tracked = _get_tracked_files()
    untracked = subprocess.run(
        ["git", "ls-files", "--others", "--exclude-standard"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.splitlines()
    return [f for f in tracked + untracked if f and os.path.isfile(f)]


def _is_excluded(file_path: str) -> bool:
    for prefix in EXCLUDED_PREFIXES:
        if file_path.startswith(prefix):
            return True
    return False


@pytest.mark.parametrize("file_path", [f for f in _get_worktree_files() if not _is_excluded(f)])
def test_no_secrets_in_worktree(file_path: str):
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    matched = []
    for pattern in SECRET_PATTERNS:
        matches = pattern.findall(content)
        if matches:
            matched.extend(matches)

    assert not matched, f"Potential secrets found in {file_path}: {matched}"


def test_removed_secrets_not_in_env():
    env_path = os.path.join(os.path.dirname(__file__), "..", "..", ".env")
    env_path = os.path.abspath(env_path)

    with open(env_path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    for secret in REMOVED_SECRETS:
        assert secret not in content, f"Removed secret '{secret}' found in .env"
