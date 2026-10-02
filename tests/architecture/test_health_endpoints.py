"""Health endpoint accuracy tests.

Verifies that /health, /health/deps, and /health/ready report actual
dependency status rather than static or hardcoded values.
"""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[2]
_BACKEND_ROOT = _REPO_ROOT / "backend"


def _run_python_code(code: str) -> subprocess.CompletedProcess:
    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".py",
        delete=False,
        prefix="health_test_",
        dir=str(_BACKEND_ROOT),
    ) as f:
        f.write(
            "import sys\n"
            f"sys.path.insert(0, r'{_REPO_ROOT}')\n"
            "import os\n"
            "os.environ['APP_ENV'] = 'test'\n"
            "os.environ['SECRET_KEY'] = 'healthtest-secret-key-0123456789-0123456789-0123456789-0123456789'\n"
            "os.environ['FIELD_ENCRYPTION_KEY'] = 'healthtest-field-encryption-key-0123456789-0123456789-0123456789-0123456789'\n"
            "os.environ['AUDIT_CHAIN_KEY'] = 'healthtest-audit-chain-key-0123456789-0123456789-0123456789-0123456789'\n"
        )
        f.write(code)
        script_path = f.name
    try:
        return subprocess.run(
            [sys.executable, script_path],
            capture_output=True,
            text=True,
            cwd=str(_BACKEND_ROOT),
        )
    finally:
        os.unlink(script_path)


class TestHealthDepsReportsActualStatus:
    """OPS-004 / LAW-018 / OBS-013: /health/deps must report real status."""

    def test_health_deps_reports_actual_status(self):
        """Payments must not be hardcoded 'ok'; must reflect real provider state."""
        code = (
            "from fastapi.testclient import TestClient\n"
            "from backend.main import app\n"
            "client = TestClient(app)\n"
            "resp = client.get('/health/deps')\n"
            "assert resp.status_code == 200, resp.text\n"
            "data = resp.json()\n"
            "deps = data.get('dependencies', {})\n"
            "assert 'payments' in deps\n"
            "assert deps['payments']['status'] in ('ok', 'unavailable')\n"
            "assert 'database' in deps\n"
            "assert deps['database']['status'] in ('ok', 'failed')\n"
            "assert 'circuit_breakers' in deps\n"
            "assert isinstance(deps['circuit_breakers'], dict)\n"
        )
        result = _run_python_code(code)
        assert result.returncode == 0, (
            f"/health/deps actual status check failed:\n{result.stderr}"
        )

    def test_health_deps_contains_database(self):
        """LAW-018: /health/deps must include database connectivity."""
        code = (
            "from fastapi.testclient import TestClient\n"
            "from backend.main import app\n"
            "client = TestClient(app)\n"
            "resp = client.get('/health/deps')\n"
            "assert resp.status_code == 200, resp.text\n"
            "data = resp.json()\n"
            "deps = data.get('dependencies', {})\n"
            "assert 'database' in deps\n"
            "assert 'status' in deps['database']\n"
        )
        result = _run_python_code(code)
        assert result.returncode == 0, (
            f"/health/deps database check failed:\n{result.stderr}"
        )

    def test_health_deps_contains_circuit_breakers(self):
        """OBS-013: /health/deps must include circuit breaker state."""
        code = (
            "from fastapi.testclient import TestClient\n"
            "from backend.main import app\n"
            "client = TestClient(app)\n"
            "resp = client.get('/health/deps')\n"
            "assert resp.status_code == 200, resp.text\n"
            "data = resp.json()\n"
            "deps = data.get('dependencies', {})\n"
            "assert 'circuit_breakers' in deps\n"
            "assert isinstance(deps['circuit_breakers'], dict)\n"
        )
        result = _run_python_code(code)
        assert result.returncode == 0, (
            f"/health/deps circuit breaker check failed:\n{result.stderr}"
        )


class TestHealthReadyBlocksOnFailingDep:
    """OPS-003: /health/ready must fail closed when Valkey is unreachable."""

    def test_health_ready_blocks_on_failing_dep(self):
        """When Valkey is down, /health/ready must return 503."""
        code = (
            "from unittest.mock import patch\n"
            "from fastapi.testclient import TestClient\n"
            "from backend.main import app\n"
            "client = TestClient(app)\n"
            "with patch('infrastructure.valkey.client.get_valkey', return_value=None):\n"
            "    resp = client.get('/health/ready')\n"
            "    assert resp.status_code == 503, resp.text\n"
            "    data = resp.json()\n"
            "    assert data['ready'] is False\n"
            "    assert 'valkey' in data['blocking_dependencies']\n"
        )
        result = _run_python_code(code)
        assert result.returncode == 0, (
            f"/health/ready fail-closed check failed:\n{result.stderr}"
        )


class TestHealthEndpointAccuracy:
    """OPS-002: /health must report dependency status, not a static response."""

    def test_health_includes_dependencies(self):
        """OPS-002: /health must include dependency status in response."""
        code = (
            "from fastapi.testclient import TestClient\n"
            "from backend.main import app\n"
            "client = TestClient(app)\n"
            "resp = client.get('/health')\n"
            "assert resp.status_code == 200, resp.text\n"
            "data = resp.json()\n"
            "assert 'dependencies' in data\n"
            "deps = data['dependencies']\n"
            "assert 'database' in deps\n"
            "assert 'valkey' in deps\n"
            "assert deps['database']['status'] in ('ok', 'failed')\n"
            "assert deps['valkey']['status'] in ('ok', 'unavailable')\n"
        )
        result = _run_python_code(code)
        assert result.returncode == 0, (
            f"/health dependency check failed:\n{result.stderr}"
        )

    def test_health_status_reflects_dependencies(self):
        """OPS-002: /health status must degrade when dependencies fail."""
        code = (
            "from unittest.mock import patch\n"
            "from fastapi.testclient import TestClient\n"
            "from backend.main import app\n"
            "import infrastructure.database.database as db_mod\n"
            "client = TestClient(app)\n"
            "patches = [\n"
            "    patch.object(db_mod, 'check_connection_health', return_value=False),\n"
            "    patch('infrastructure.valkey.client.get_valkey_health_status', return_value={'available': False}),\n"
            "]\n"
            "for p in patches:\n"
            "    p.start()\n"
            "try:\n"
            "    resp = client.get('/health')\n"
            "    assert resp.status_code == 200, resp.text\n"
            "    data = resp.json()\n"
            "    assert data['status'] == 'degraded'\n"
            "    assert data['dependencies']['database']['status'] == 'failed'\n"
            "    assert data['dependencies']['valkey']['status'] == 'unavailable'\n"
            "finally:\n"
            "    for p in patches:\n"
            "        p.stop()\n"
        )
        result = _run_python_code(code)
        assert result.returncode == 0, (
            f"/health degraded status check failed:\n{result.stderr}"
        )
        result = _run_python_code(code)
        assert result.returncode == 0, (
            f"/health degraded status check failed:\n{result.stderr}"
        )
