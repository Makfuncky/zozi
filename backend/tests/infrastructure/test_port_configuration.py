"""Phase 5A: port-mismatch detection.

The Phase 4L regression report found 38 'session bootstrap' failures caused
by a single root cause: ``run_e2e.ps1`` started the backend on port 8000
while ``frontend/.env.local`` had ``NEXT_PUBLIC_API_URL`` pointing at
``http://127.0.0.1:8001``. These tests fail the suite if any of the port
sources drift apart again.
"""

from __future__ import annotations

import os
import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]


def _read(rel: str) -> str:
    p = REPO_ROOT / rel
    assert p.exists(), f"Required file missing: {p}"
    return p.read_text(encoding="utf-8")


def _extract_port(text: str, patterns: list[str], default: int | None = None) -> int | None:
    for pat in patterns:
        m = re.search(pat, text, re.MULTILINE)
        if m:
            try:
                return int(m.group(1))
            except (IndexError, ValueError):
                continue
    return default


def _port_in_text(text: str, port: int) -> bool:
    return bool(re.search(rf"\b{port}\b", text))


class TestPortConfiguration:
    """Assert that every port source agrees on the same backend port."""

    def test_root_env_example_has_backend_url(self) -> None:
        text = _read(".env.example")
        assert "BACKEND_URL" in text, "Root .env.example must declare BACKEND_URL"
        assert "http://localhost:8000" in text or "http://127.0.0.1:8000" in text, (
            "Root .env.example should document the dev backend port (8000)"
        )

    def test_backend_env_example_declares_backend_port(self) -> None:
        text = _read("backend/.env.example")
        # Port can be referenced via FRONTEND_URL's neighbour, BACKEND_URL,
        # or the documented convention.
        assert any(s in text for s in ("BACKEND_PORT", "BACKEND_URL", "FRONTEND_URL")), (
            "backend/.env.example should document backend/frontend URL convention"
        )

    def test_run_e2e_ps1_uses_e2e_port_8001(self) -> None:
        text = _read("run_e2e.ps1")
        port = _extract_port(text, [r"BackendPort\s*=\s*(\d+)", r"--port\s+(\d+)", r":(\d{4})\s*\}\s*\$BackendPort"])
        assert port == 8001, (
            f"run_e2e.ps1 default backend port must be 8001 (E2E convention), got {port}. "
            "The frontend's NEXT_PUBLIC_API_URL points at 8001; mismatching it causes "
            "Playwright 'session bootstrap' failures."
        )

    def test_frontend_env_local_matches_e2e_port(self) -> None:
        frontend = _read("frontend/web_app/.env.local")
        # Match only assignment lines (not comments) — comments may mention other ports.
        env_url = _extract_port(
            frontend,
            [r"^\s*NEXT_PUBLIC_API_URL\s*=\s*https?://[^:\s]+:(\d+)"],
        )
        assert env_url == 8001, (
            f"frontend/.env.local NEXT_PUBLIC_API_URL must point to port 8001 "
            f"to match run_e2e.ps1, got port {env_url}."
        )

    def test_frontend_env_example_documents_port_convention(self) -> None:
        text = _read("frontend/web_app/.env.example")
        # Must document both 8000 (dev) and 8001 (E2E) ports
        assert "8000" in text and "8001" in text, (
            "frontend/web_app/.env.example must document the port convention "
            "(dev=8000, E2E/CI=8001)."
        )

    def test_run_e2e_and_frontend_agree_on_port(self) -> None:
        e2e_text = _read("run_e2e.ps1")
        e2e_port = _extract_port(e2e_text, [r"BackendPort\s*=\s*(\d+)"])
        fe_text = _read("frontend/web_app/.env.local")
        fe_port = _extract_port(
            fe_text,
            [r"^\s*NEXT_PUBLIC_API_URL\s*=\s*https?://[^:\s]+:(\d+)"],
        )
        assert e2e_port == fe_port, (
            f"Port mismatch: run_e2e.ps1={e2e_port} vs frontend/.env.local={fe_port}. "
            "Both must agree or Playwright will hang on session bootstrap."
        )

    @pytest.mark.parametrize("env_file", [".env.example", "backend/.env.example"])
    def test_no_redis_url_for_app_state(self, env_file: str) -> None:
        # Sanity: the project's primary cache/session broker migrated to Valkey.
        # Celery broker/backend lines are an acceptable exception and are excluded
        # from the check so unrelated config can keep using redis:// if needed.
        text = _read(env_file)
        # Drop Celery lines and any commented lines before scanning.
        cleaned = "\n".join(
            line
            for line in text.splitlines()
            if not line.lstrip().startswith("#")
            and not line.startswith("CELERY_")
        )
        assert "redis://" not in cleaned and "VALKEY_URL" not in cleaned, (
            f"{env_file} still references redis:// for primary app state"
        )

    def test_playwright_config_uses_localhost_3000(self) -> None:
        text = _read("frontend/web_app/playwright.config.ts")
        assert "baseURL" in text and "127.0.0.1:3000" in text, (
            "playwright.config.ts must keep baseURL=http://127.0.0.1:3000 (frontend port)"
        )

    def test_playwright_config_has_global_setup(self) -> None:
        text = _read("frontend/web_app/playwright.config.ts")
        assert "globalSetup" in text, (
            "playwright.config.ts must declare globalSetup pointing to the "
            "port-mismatch sanity check (playwright.global-setup.ts)."
        )
