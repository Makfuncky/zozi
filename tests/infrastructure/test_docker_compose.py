import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
COMPOSE_PATH = REPO_ROOT / "docker-compose.prod.yml"


def test_compose_file_exists():
    assert COMPOSE_PATH.exists(), f"Missing {COMPOSE_PATH}"


def _read_compose() -> str:
    return COMPOSE_PATH.read_text(encoding="utf-8")


def _service_block(text: str, name: str) -> str:
    m = re.search(rf"\n  {re.escape(name)}:\n(.*?)(?=\n  [a-z_]+:|\Z)", text, re.DOTALL)
    assert m, f"{name} service block not found"
    return m.group(1)


def test_docker_compose_prod():
    text = _read_compose()
    assert "services:" in text
    assert "networks:" in text
    assert "volumes:" in text
    assert "zozi_net:" in text
    required_services = ["pgbouncer", "backend", "ml_worker", "celery-beat", "valkey"]
    for svc in required_services:
        assert re.search(rf"\n  {svc}:\n", text), f"{svc} service not defined"
    assert "db:" not in text, "Local db service must be removed per Neon canonical stack"
    assert "postgres_data:" not in text, "postgres_data volume must be removed with db service"


def test_all_services_have_logging():
    text = _read_compose()
    services_match = re.search(r"services:\n(.*?)(?=\nnetworks:|\nvolumes:|\Z)", text, re.DOTALL)
    assert services_match, "services section not found"
    services_text = services_match.group(1)
    service_names = re.findall(r"\n  ([a-z_]+):\n", services_text)
    for svc in service_names:
        block = _service_block(text, svc)
        assert "logging:" in block, f"{svc} missing logging configuration"
        assert 'driver: "json-file"' in block, f"{svc} logging missing json-file driver"
        assert "max-size:" in block, f"{svc} logging missing max-size"
        assert "max-file:" in block, f"{svc} logging missing max-file"


def test_valkey_version():
    text = _read_compose()
    valkey_block = _service_block(text, "valkey")
    assert "valkey:9" in valkey_block, "Valkey must be version 9.0+ per TECHNOLOGY_STACK.md"
    assert "valkey:8" not in valkey_block, "Valkey 8.x is forbidden"


def test_pgbouncer_uses_direct_url():
    text = _read_compose()
    pgbouncer_block = _service_block(text, "pgbouncer")
    assert "DATABASE_URL=${DATABASE_URL_DIRECT}" in pgbouncer_block, (
        "pgbouncer must use DATABASE_URL_DIRECT, not a local db reference"
    )
    assert "db:5432" not in pgbouncer_block, "pgbouncer must not reference local db service"


def test_valkey_has_resource_limits():
    text = _read_compose()
    valkey_block = _service_block(text, "valkey")
    assert "deploy:" in valkey_block, "valkey missing deploy section"
    assert "resources:" in valkey_block, "valkey missing resources"
    assert "limits:" in valkey_block, "valkey missing limits"
    assert "reservations:" in valkey_block, "valkey missing reservations"


def test_pgbouncer_has_resource_limits():
    text = _read_compose()
    pgbouncer_block = _service_block(text, "pgbouncer")
    assert "deploy:" in pgbouncer_block, "pgbouncer missing deploy section"
    assert "resources:" in pgbouncer_block, "pgbouncer missing resources"
    assert "limits:" in pgbouncer_block, "pgbouncer missing limits"
    assert "reservations:" in pgbouncer_block, "pgbouncer missing reservations"


def test_backend_healthcheck_uses_ready():
    text = _read_compose()
    backend_block = _service_block(text, "backend")
    assert "healthcheck:" in backend_block, "backend missing healthcheck"
    assert "health/ready" in backend_block, "backend healthcheck must use /health/ready"
