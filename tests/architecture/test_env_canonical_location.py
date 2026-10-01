import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_no_env_example_in_subdirectories():
    result = subprocess.run(
        ["git", "ls-files"],
        capture_output=True,
        text=True,
        check=True,
        cwd=REPO_ROOT,
    )
    tracked = [line for line in result.stdout.splitlines() if line]

    bad = [
        f
        for f in tracked
        if f.endswith(".env.example") and f != ".env.example"
    ]

    assert not bad, f".env.example found in subdirectories: {bad}"
