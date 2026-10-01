import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
COMPOSE_PATH = REPO_ROOT / "monitoring" / "docker-compose.monitoring.yml"


def test_compose_file_exists():
    assert COMPOSE_PATH.exists(), f"Missing {COMPOSE_PATH}"


def _read_compose() -> str:
    return COMPOSE_PATH.read_text(encoding="utf-8")


def _service_block(text: str, name: str) -> str:
    m = re.search(rf"\n  {re.escape(name)}:\n(.*?)(?=\n  [a-z_]+:|\Z)", text, re.DOTALL)
    assert m, f"{name} service block not found"
    return m.group(1)


class TestFile181Resolutions:
    """FILE-181: ENV-006 sentry secrets required via ${VAR:?}, D2P-025 loki retention."""

    def test_sentry_secret_key_uses_required_reference(self):
        sentry_block = _service_block(_read_compose(), "sentry")
        assert "SENTRY_SECRET_KEY=${SENTRY_SECRET_KEY:?" in sentry_block
        assert "sentry-secret-key-change-in-production" not in sentry_block

    def test_sentry_db_password_uses_required_reference(self):
        sentry_block = _service_block(_read_compose(), "sentry")
        assert "SENTRY_DB_PASSWORD=${SENTRY_DB_PASSWORD:?" in sentry_block
        assert "sentry-password" not in sentry_block

    def test_loki_has_retention_config(self):
        loki_block = _service_block(_read_compose(), "loki")
        assert "LOKI_LOCAL_CONFIG" in loki_block
        assert "retention_period" in loki_block
