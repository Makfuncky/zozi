import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_no_hardcoded_secret_key_in_workflows():
    workflow_files = list((REPO_ROOT / ".github" / "workflows").glob("*.yml"))
    assert workflow_files, "No workflow files found"
    bad = []
    for wf in workflow_files:
        text = wf.read_text(encoding="utf-8")
        if "SECRET_KEY: e2e-test-secret" in text or 'SECRET_KEY: "e2e-test-secret"' in text:
            bad.append(str(wf))
    assert not bad, f"Hardcoded SECRET_KEY literals found in: {bad}"


def test_no_hardcoded_secret_key_in_conftest():
    conftest = REPO_ROOT / "backend" / "tests" / "conftest.py"
    assert conftest.exists(), "conftest.py missing"
    text = conftest.read_text(encoding="utf-8")
    assert "test-secret-key-for-pytest-only-32+" not in text, "Hardcoded SECRET_KEY fallback found in conftest.py"
