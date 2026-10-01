import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
COMPOSE_PATH = REPO_ROOT / "docker-compose.prod.yml"


def test_compose_file_exists():
    assert COMPOSE_PATH.exists(), f"Missing {COMPOSE_PATH}"


def _read_compose() -> str:
    return COMPOSE_PATH.read_text(encoding="utf-8")


def _service_block(text: str, name: str) -> str:
    m = re.search(rf"\n  {re.escape(name)}:\n(.*?)(?=\n  [a-z_]+:|\Z)", text, re.DOTALL)
    assert m, f"{name} service block not found"
    return m.group(1)


class TestStorageBackendR2:
    """ENV-11-005/ENV-11-006: S3 vars removed, R2 vars present."""

    def test_backend_storage_backend_is_r2(self):
        text = _read_compose()
        backend_block = _service_block(text, "backend")
        assert "STORAGE_BACKEND=r2" in backend_block
        assert "STORAGE_BACKEND=s3" not in backend_block

    def test_backend_s3_vars_removed(self):
        backend_block = _service_block(_read_compose(), "backend")
        for var in (
            "S3_BUCKET",
            "S3_REGION",
            "S3_ENDPOINT_URL",
            "S3_CDN_BASE",
            "S3_ACCESS_KEY_ID",
            "S3_SECRET_ACCESS_KEY",
        ):
            assert var not in backend_block, f"{var} should be removed from backend"

    def test_backend_r2_vars_present(self):
        backend_block = _service_block(_read_compose(), "backend")
        for var in (
            "R2_ACCOUNT_ID",
            "R2_ACCESS_KEY_ID",
            "R2_SECRET_ACCESS_KEY",
            "R2_BUCKET",
            "R2_ENDPOINT_URL",
        ):
            assert var in backend_block, f"{var} should be present in backend"

    def test_ml_worker_storage_backend_is_r2(self):
        text = _read_compose()
        ml_block = _service_block(text, "ml_worker")
        assert "STORAGE_BACKEND=r2" in ml_block

    def test_ml_worker_s3_vars_removed(self):
        ml_block = _service_block(_read_compose(), "ml_worker")
        for var in (
            "S3_BUCKET",
            "S3_ENDPOINT_URL",
            "S3_ACCESS_KEY_ID",
            "S3_SECRET_ACCESS_KEY",
        ):
            assert var not in ml_block, f"{var} should be removed from ml_worker"


class TestDbPoolSize:
    """ENV-11-008: DB pool size increased."""

    def test_db_pool_size_is_20(self):
        text = _read_compose()
        assert "DB_POOL_SIZE=20" in text
        assert "DB_POOL_SIZE=10" not in text

    def test_db_max_overflow_is_20(self):
        text = _read_compose()
        assert "DB_MAX_OVERFLOW=20" in text
        assert "DB_MAX_OVERFLOW=10" not in text


class TestMissingEnvVars:
    """ENV-11-009: required production env vars present in backend."""

    def test_required_env_vars_present(self):
        backend_block = _service_block(_read_compose(), "backend")
        required = [
            "FRONTEND_URL",
            "BACKEND_URL",
            "WEBHOOK_SECRET",
            "STRIPE_WEBHOOK_SECRET",
            "PAYTABS_WEBHOOK_SECRET",
            "PAYPAL_WEBHOOK_SECRET",
            "THAWANI_WEBHOOK_SECRET",
            "TAP_WEBHOOK_SECRET",
            "CORS_ORIGINS",
        ]
        for var in required:
            assert var in backend_block, f"{var} missing from backend env"


class TestNoLocalPostgres:
    """D2P-014: local postgres service removed; Neon is the canonical stack."""

    def test_no_local_db_service(self):
        text = _read_compose()
        assert not re.search(r"\n  db:\n", text), "local db service must not be defined (Neon canonical)"

    def test_no_postgres_image(self):
        text = _read_compose()
        assert "postgres:18-alpine" not in text, "no local postgres image in prod compose"


class TestPgbouncerDatabaseUrl:
    """D2P-014: pgbouncer upstream points at the managed (Neon) direct URL."""

    def test_pgbouncer_points_to_direct_url(self):
        pgbouncer_block = _service_block(_read_compose(), "pgbouncer")
        assert "DATABASE_URL=${DATABASE_URL_DIRECT}" in pgbouncer_block
        assert "@db:5432" not in pgbouncer_block


class TestBackendUpdateConfig:
    """DIM-13-013: backend deploy has update_config."""

    def test_backend_has_update_config(self):
        backend_block = _service_block(_read_compose(), "backend")
        assert "update_config:" in backend_block
        assert "parallelism: 1" in backend_block
        assert "delay: 10s" in backend_block
        assert "order: start-first" in backend_block


class TestFile179Resolutions:
    """FILE-179 open findings: OPS-001 celery-beat, TECH-029 valkey version."""

    def test_celery_beat_service_defined(self):
        text = _read_compose()
        assert re.search(r"\n  celery-beat:\n", text), "celery-beat service missing (OPS-001)"
        assert "celery -A jobs.celery_app beat" in text

    def test_valkey_image_is_v9(self):
        valkey_block = _service_block(_read_compose(), "valkey")
        assert re.search(r"image:\s*valkey:9", valkey_block), "valkey 9.0.6+ mandated (TECH-029)"

    def test_backend_healthcheck_uses_ready(self):
        backend_block = _service_block(_read_compose(), "backend")
        assert "/health/ready" in backend_block, "healthcheck must use /health/ready (OPS-009)"

    def test_no_redis_service(self):
        text = _read_compose()
        assert not re.search(r"\n  redis:\n", text), "redis service must not exist; use valkey"


class TestFile179LoggingAndResources:
    """FILE-179 OPS-006/OPS-007: logging on all services, resources on valkey/pgbouncer."""

    def test_all_services_have_logging(self):
        text = _read_compose()
        for service in ("backend", "ml_worker", "valkey", "celery-beat", "pgbouncer"):
            block = _service_block(text, service)
            assert 'driver: "json-file"' in block, f"{service} missing logging config"
            assert "max-size" in block, f"{service} missing log rotation"

    def test_valkey_has_deploy_resources(self):
        valkey_block = _service_block(_read_compose(), "valkey")
        assert "deploy:" in valkey_block
        assert "limits:" in valkey_block
        assert "reservations:" in valkey_block

    def test_pgbouncer_has_deploy_resources(self):
        pgbouncer_block = _service_block(_read_compose(), "pgbouncer")
        assert "deploy:" in pgbouncer_block
        assert "limits:" in pgbouncer_block
        assert "reservations:" in pgbouncer_block
