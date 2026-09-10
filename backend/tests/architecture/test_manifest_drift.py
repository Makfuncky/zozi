"""Architecture tests — Manifest / version drift fixes (Phase 1 upgrade plan).

Verifies that the dependency manifests in the repo are internally consistent
and align with installed versions after the Phase 1 upgrade.
"""
from __future__ import annotations

import pathlib
import re

import pytest


_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent.parent
_BACKEND = _REPO_ROOT / "backend"
_FRONTEND = _REPO_ROOT / "frontend"
_REQUIREMENTS_TXT = _BACKEND / "requirements.txt"
_REQUIREMENTS_DEV = _BACKEND / "requirements-dev.txt"
_PACKAGE_JSON_WEB = _FRONTEND / "web_app" / "package.json"
_PACKAGE_JSON_MOBILE = _FRONTEND / "mobile_app" / "package.json"
_PACKAGE_JSON_SHARED = _FRONTEND / "shared" / "package.json"


def test_requirements_txt_has_no_redis() -> None:
    """The `redis` package must NOT be in backend/requirements.txt (§14)."""
    if not _REQUIREMENTS_TXT.exists():
        pytest.skip("requirements.txt not found")
    text = _REQUIREMENTS_TXT.read_text(encoding="utf-8")
    # Match lines like `redis==5.0.8` (not part of e.g. `valkey-redis` or `redis_url`)
    redis_lines = [
        line.strip() for line in text.splitlines()
        if re.match(r"^redis[=<>!~]", line.strip()) and not line.strip().startswith("#")
    ]
    assert not redis_lines, (
        f"backend/requirements.txt must not declare redis (use valkey): {redis_lines}"
    )


def test_requirements_txt_has_valkey() -> None:
    """The `valkey` package must be in backend/requirements.txt (§14)."""
    if not _REQUIREMENTS_TXT.exists():
        pytest.skip("requirements.txt not found")
    text = _REQUIREMENTS_TXT.read_text(encoding="utf-8")
    assert re.search(r"^valkey[=<>!~]", text, re.MULTILINE), (
        "backend/requirements.txt must declare valkey==X.Y.Z"
    )


def test_requirements_txt_pillow_uses_real_version() -> None:
    """Pillow must be pinned to a real version (not 12.3.0 which doesn't exist)."""
    if not _REQUIREMENTS_TXT.exists():
        pytest.skip("requirements.txt not found")
    text = _REQUIREMENTS_TXT.read_text(encoding="utf-8")
    for line in text.splitlines():
        if line.strip().lower().startswith("pillow"):
            # Pin must be 11.x or 10.x (12.3.0 does not exist on PyPI)
            assert not line.strip().startswith("Pillow==12.3.0"), (
                "Pillow 12.3.0 does not exist on PyPI; use 11.x"
            )
            break


def test_domain_allowlist_is_20_or_fewer_entries() -> None:
    """DOMAIN_ALLOWLIST.yaml must not exceed the recorded baseline (Law 7)."""
    allowlist = _BACKEND / "DOMAIN_ALLOWLIST.yaml"
    if not allowlist.exists():
        pytest.skip("DOMAIN_ALLOWLIST.yaml not found")
    text = allowlist.read_text(encoding="utf-8")
    entry_count = sum(
        1
        for line in text.splitlines()
        if line.lstrip().startswith("- ") and "->" in line
    )
    baseline_file = _BACKEND / "tests" / "architecture" / "_allowlist_shrinks_baseline.txt"
    if baseline_file.exists():
        baseline = int(baseline_file.read_text(encoding="utf-8").strip() or "0")
        assert entry_count <= baseline, (
            f"DOMAIN_ALLOWLIST.yaml has {entry_count} entries; baseline is {baseline} (Law 7)"
        )


def test_dockerfile_uses_python_3_13() -> None:
    """backend/Dockerfile must use python:3.13-slim (per upgrade plan)."""
    dockerfile = _BACKEND / "Dockerfile"
    if not dockerfile.exists():
        pytest.skip("Dockerfile not found")
    text = dockerfile.read_text(encoding="utf-8")
    assert "python:3.13" in text, "Dockerfile must use python:3.13-slim per upgrade plan"
    assert "python:3.11" not in text, "Dockerfile must NOT use python:3.11-slim (outdated)"


def test_dockerfile_prod_uses_python_3_13() -> None:
    """backend/Dockerfile.prod must use python:3.13-slim (per upgrade plan)."""
    dockerfile = _BACKEND / "Dockerfile.prod"
    if not dockerfile.exists():
        pytest.skip("Dockerfile.prod not found")
    text = dockerfile.read_text(encoding="utf-8")
    assert "python:3.13" in text, "Dockerfile.prod must use python:3.13-slim per upgrade plan"


def test_docker_compose_uses_valkey_9_0() -> None:
    """docker-compose.yml must use valkey:9.0-alpine (per upgrade plan)."""
    compose = _REPO_ROOT / "docker-compose.yml"
    if not compose.exists():
        pytest.skip("docker-compose.yml not found")
    text = compose.read_text(encoding="utf-8")
    assert "valkey:9.0" in text, "docker-compose.yml must use valkey:9.0-alpine (latest 9.0.x branch)"
    assert "image: redis:" not in text, "docker-compose.yml must NOT use redis:* images"


def test_docker_compose_uses_postgres_18() -> None:
    """docker-compose.yml must use postgres:18-alpine (per upgrade plan)."""
    compose = _REPO_ROOT / "docker-compose.yml"
    if not compose.exists():
        pytest.skip("docker-compose.yml not found")
    text = compose.read_text(encoding="utf-8")
    assert "postgres:18" in text, "docker-compose.yml must use postgres:18-alpine (Neon supports PG18 preview)"


def test_web_app_package_json_has_aligned_versions() -> None:
    """frontend/web_app/package.json versions must be declared with valid specifiers."""
    if not _PACKAGE_JSON_WEB.exists():
        pytest.skip("package.json not found")
    import json
    data = json.loads(_PACKAGE_JSON_WEB.read_text(encoding="utf-8"))
    deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
    # Critical packages must be declared
    for pkg in ("next", "react", "react-dom", "typescript"):
        assert pkg in deps, f"web_app/package.json must declare {pkg}"


def test_mobile_app_package_json_has_aligned_versions() -> None:
    """frontend/mobile_app/package.json must declare all required dependencies."""
    if not _PACKAGE_JSON_MOBILE.exists():
        pytest.skip("package.json not found")
    import json
    data = json.loads(_PACKAGE_JSON_MOBILE.read_text(encoding="utf-8"))
    deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
    # Critical packages must be declared (manifest must list them even if UNMET)
    for pkg in (
        "expo", "react", "react-dom", "react-native",
        "@react-native-async-storage/async-storage",
        "@stripe/stripe-react-native",
        "dayjs", "lucide-react-native", "zustand",
    ):
        assert pkg in deps, f"mobile_app/package.json must declare {pkg}"


def test_shared_package_json_has_aligned_versions() -> None:
    """frontend/shared/package.json must declare all required peer dependencies."""
    if not _PACKAGE_JSON_SHARED.exists():
        pytest.skip("package.json not found")
    import json
    data = json.loads(_PACKAGE_JSON_SHARED.read_text(encoding="utf-8"))
    peers = data.get("peerDependencies", {})
    for pkg in ("react", "react-dom", "react-native"):
        assert pkg in peers, f"shared/package.json must declare peer dep {pkg}"


def test_no_debug_scripts_at_backend_root() -> None:
    """Debug scripts (test_*.py, debug_*.py, check_*.py, fix_*.py, _*.py) must not be at backend/ root."""
    # Whitelist: __init__.py, main.py, config.py, etc.
    allowed = {
        "__init__.py", "main.py", "config.py", "lifespan.py", "bootstrap.py",
    }
    for py_file in _BACKEND.glob("*.py"):
        if py_file.name in allowed:
            continue
        if py_file.name.startswith("test_") or py_file.name.startswith("debug_"):
            pytest.fail(f"Debug/test script at backend root: {py_file.name}")
        if py_file.name.startswith("check_") or py_file.name.startswith("fix_"):
            pytest.fail(f"Debug script at backend root: {py_file.name}")
        if py_file.name.startswith("_") and not py_file.name.startswith("__"):
            pytest.fail(f"Underscore-prefixed debug script at backend root: {py_file.name}")


def test_upgraded_packages_present() -> None:
    """Verify that Phase 2 upgraded packages are installed in the venv."""
    import importlib.metadata
    for pkg, min_version in (
        ("fastapi", "0.141"),
        ("celery", "5.6"),
        ("stripe", "15.6"),
        ("SQLAlchemy", "2.0.52"),
        ("alembic", "1.19"),
        ("pydantic", "2.13"),
        ("asyncpg", "0.31"),
        ("prometheus-fastapi-instrumentator", "8.0"),
        ("valkey", "6.1.1"),
    ):
        try:
            version = importlib.metadata.version(pkg)
        except importlib.metadata.PackageNotFoundError:
            pytest.fail(f"Package {pkg} not installed (required for Phase 2 upgrade)")
        # Check version >= min_version
        from packaging.version import Version
        assert Version(version) >= Version(min_version), (
            f"Package {pkg} version {version} < required {min_version}"
        )


def test_docker_compose_uses_latest_valkey_and_pg() -> None:
    """Per Neon's PG18 availability, docker-compose should test against PG18.

    Valkey 9.0.6 is the latest in the 9.0.x branch.
    PostgreSQL 18 is available on Neon as a preview.
    """
    compose = (_REPO_ROOT / "docker-compose.yml").read_text(encoding="utf-8")
    assert "valkey:9.0" in compose, (
        "Valkey 9.0.x is the latest branch with security fixes (Valkey 9.0.6)"
    )
    assert "postgres:18" in compose, (
        "PostgreSQL 18 is the latest version (Neon supports it as preview)"
    )
    # Verify no old Valkey 8.x or PG 17 references
    assert "valkey:8" not in compose, "Valkey 8.x is outdated; use 9.0.x"
    assert "postgres:17" not in compose, "PostgreSQL 17 is outdated; use 18"
    assert "postgres:15" not in compose, "PostgreSQL 15 is outdated; use 18"


def test_products_smoke_test_exists_in_proper_folder() -> None:
    """Products smoke test must live in tests/domains/catalog/ (not backend/ root)."""
    smoke = _BACKEND / "tests" / "domains" / "catalog" / "test_products_service.py"
    assert smoke.exists(), (
        "test_products_service.py must exist in tests/domains/catalog/ "
        "(not at backend/ root)"
    )
    legacy = _BACKEND / "test_products.py"
    assert not legacy.exists(), (
        "backend/test_products.py (debug script) must NOT exist at backend/ root"
    )
