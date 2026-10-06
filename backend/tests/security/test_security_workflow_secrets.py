"""
Regression test for FILE-103: security.yml must not contain hardcoded secrets.

Verifies that .github/workflows/security.yml does not hardcode SECRET_KEY
or any other sensitive value as a plaintext literal in the env block.

Law 32: No hardcoded secrets — JWT keys, API keys, passwords from env vars
or secrets manager only.
"""
import re
import pathlib

import pytest

# Resolve to project root: this file is at backend/tests/security/
# Parent traversal: .../security/ -> .../tests/ -> .../backend/ -> project root
PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[3]
SECRETS_FILE = PROJECT_ROOT / ".github" / "workflows" / "security.yml"


def test_security_yml_no_hardcoded_secret_key():
    """SECRET_KEY in security.yml must use ${{ secrets.* }}, not a literal."""
    if not SECRETS_FILE.is_file():
        pytest.skip("security.yml not found")
    content = SECRETS_FILE.read_text(encoding="utf-8")
    lines = content.splitlines()

    secret_key_lines = [
        (i + 1, line)
        for i, line in enumerate(lines)
        if re.match(r"\s*SECRET_KEY:", line, re.IGNORECASE)
    ]

    assert secret_key_lines, "SECRET_KEY env var not found in security.yml"
    for lineno, line in secret_key_lines:
        assert "${{ secrets." in line, (
            f"Line {lineno}: SECRET_KEY is hardcoded, "
            f"must reference a GitHub Actions secret: {line!r}"
        )


def test_security_yml_no_other_hardcoded_secrets():
    """Other well-known secret env vars in security.yml must use ${{ secrets.* }}."""
    if not SECRETS_FILE.is_file():
        pytest.skip("security.yml not found")
    content = SECRETS_FILE.read_text(encoding="utf-8")
    lines = content.splitlines()

    known_secret_vars = {
        "SECRET_KEY",
        "DATABASE_URL",
        "DATABASE_URL_DIRECT",
        "STRIPE_SECRET_KEY",
        "STRIPE_WEBHOOK_SECRET",
        "SMTP_PASSWORD",
        "RESEND_API_KEY",
        "FIELD_ENCRYPTION_KEY",
        "AUDIT_CHAIN_KEY",
    }

    violations = []
    for i, line in enumerate(lines, start=1):
        stripped = line.strip()
        for var in known_secret_vars:
            if re.match(rf"^{var}:", stripped, re.IGNORECASE):
                val = stripped.split(":", 1)[1].strip()
                if val and not val.startswith("${{") and not val.startswith("sqlite"):
                    violations.append(
                        f"Line {i}: {var} = {val!r} "
                        f"(should use ${{{{ secrets.* }}}} )"
                    )

    assert violations == [], (
        f"Hardcoded secrets found in security.yml: {violations}"
    )
