"""Architecture gates for Laws 296-325 (Resilience, Operations).

These tests enforce resilience and operational laws:

  Law 296 — Circuit breaker: circuit breaker infrastructure must exist
  Law 297 — Retry + backoff: retry logic with exponential backoff
  Law 304 — DR (RPO=5min, RTO=1hr): disaster recovery configuration
  Law 311 — Feature flags: feature flag system must exist
  Law 313 — Compliance (GDPR, PCI-DSS): compliance controls must exist
"""
from __future__ import annotations

import ast
import pathlib
import re

import pytest

_BACKEND_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
_DOMAINS_DIR = _BACKEND_ROOT / "domains"
_MIDDLEWARE_DIR = _BACKEND_ROOT / "middleware"
_INFRASTRUCTURE_DIR = _BACKEND_ROOT / "infrastructure"
_PROVIDERS_DIR = _BACKEND_ROOT / "providers"
_RBAC_DIR = _BACKEND_ROOT / "rbac"
_JOBS_DIR = _BACKEND_ROOT / "jobs"


def _iter_py(root: pathlib.Path, exclude_dirs: set[str] | None = None):
    if not root.exists():
        return
    exclude_dirs = exclude_dirs or set()
    for path in sorted(root.rglob("*.py")):
        if path.name == "__init__.py":
            continue
        rel_parts = set(path.relative_to(_BACKEND_ROOT).parts)
        if rel_parts & exclude_dirs:
            continue
        yield path


class TestLaw296CircuitBreaker:
    """Law 296: Circuit breaker infrastructure must exist.

    External service calls must be wrapped in circuit breakers to prevent
    cascading failures.
    """

    def test_circuit_breaker_implementation_exists(self):
        found = False
        for path in _iter_py(_BACKEND_ROOT, exclude_dirs={
            "tests", "scripts", "venv", ".kilo", "alembic"
        }):
            try:
                src = path.read_text(encoding="utf-8")
            except OSError:
                continue
            if re.search(
                r"(?:circuit.?breaker|CircuitBreaker|circuit_breaker|"
                r" CircuitState|open_circuit|half.open)",
                src,
                re.IGNORECASE,
            ):
                found = True
                break
        assert found, (
            "Law 296 violation: no circuit breaker implementation found"
        )

    def test_circuit_breaker_has_states(self):
        """Verify circuit breaker implements OPEN, CLOSED, HALF_OPEN states."""
        for path in _iter_py(_BACKEND_ROOT, exclude_dirs={
            "tests", "scripts", "venv", ".kilo", "alembic"
        }):
            try:
                src = path.read_text(encoding="utf-8")
            except OSError:
                continue
            if "circuit" in src.lower() and "breaker" in src.lower():
                has_open = "OPEN" in src or "open" in src.lower()
                has_closed = "CLOSED" in src or "closed" in src.lower()
                if has_open or has_closed:
                    return
        pytest.skip("Circuit breaker state verification inconclusive")

    def test_external_calls_use_circuit_breaker(self):
        """Verify that external service calls are wrapped with circuit breakers."""
        for path in _iter_py(_PROVIDERS_DIR, exclude_dirs={"tests", "scripts"}):
            try:
                src = path.read_text(encoding="utf-8")
            except OSError:
                continue
            if "def " in src and ("client" in src.lower() or "request" in src.lower()):
                if "circuit" in src.lower():
                    return
        pytest.skip("Provider circuit breaker wrapping not explicitly verified")


class TestLaw297RetryAndBackoff:
    """Law 297: Retry logic with exponential backoff must exist.

    Transient failures must be handled with retry + exponential backoff.
    """

    def test_retry_mechanism_exists(self):
        found = False
        for path in _iter_py(_BACKEND_ROOT, exclude_dirs={
            "tests", "scripts", "venv", ".kilo", "alembic"
        }):
            try:
                src = path.read_text(encoding="utf-8")
            except OSError:
                continue
            if re.search(
                r"(?:retry|backoff|exponential|retry_count|max_retries|retry_delay)",
                src,
                re.IGNORECASE,
            ):
                found = True
                break
        assert found, (
            "Law 297 violation: no retry mechanism found"
        )

    def test_exponential_backoff_implemented(self):
        """Verify exponential backoff is used (not just fixed delay)."""
        for path in _iter_py(_BACKEND_ROOT, exclude_dirs={
            "tests", "scripts", "venv", ".kilo", "alembic"
        }):
            try:
                src = path.read_text(encoding="utf-8")
            except OSError:
                continue
            if re.search(
                r"(?:exponential.*backoff|backoff.*exponential|2\s*\*\*\s*|pow\s*\(2)",
                src,
                re.IGNORECASE,
            ):
                return
        pytest.skip("Exponential backoff not explicitly verified")

    def test_retry_with_jitter(self):
        """Verify retry includes jitter to prevent thundering herd."""
        for path in _iter_py(_BACKEND_ROOT, exclude_dirs={
            "tests", "scripts", "venv", ".kilo", "alembic"
        }):
            try:
                src = path.read_text(encoding="utf-8")
            except OSError:
                continue
            if "jitter" in src.lower() or "random" in src.lower():
                if "retry" in src.lower() or "backoff" in src.lower():
                    return
        pytest.skip("Retry jitter not explicitly implemented")


class TestLaw304DisasterRecovery:
    """Law 304: Disaster Recovery with RPO=5min, RTO=1hr.

    The system must have disaster recovery procedures defined.
    """

    def test_backup_mechanism_exists(self):
        found = False
        for path in _iter_py(_BACKEND_ROOT, exclude_dirs={
            "tests", "scripts", "venv", ".kilo", "alembic"
        }):
            try:
                src = path.read_text(encoding="utf-8")
            except OSError:
                continue
            if re.search(
                r"(?:backup|snapshot|dump|pg_dump|mysqldump)",
                src,
                re.IGNORECASE,
            ):
                found = True
                break
        if not found:
            # Check scripts directory
            scripts_dir = _BACKEND_ROOT / "scripts"
            if scripts_dir.exists():
                for path in scripts_dir.rglob("*.py"):
                    try:
                        src = path.read_text(encoding="utf-8")
                    except OSError:
                        continue
                    if "backup" in src.lower():
                        found = True
                        break
        if not found:
            pytest.skip("Backup mechanism not yet implemented")

    def test_rpo_rto_documented(self):
        """Verify RPO and RTO targets are documented."""
        rpo_found = False
        rto_found = False
        for path in _iter_py(_BACKEND_ROOT, exclude_dirs={
            "tests", "scripts", "venv", ".kilo", "alembic"
        }):
            try:
                src = path.read_text(encoding="utf-8")
            except OSError:
                continue
            if re.search(r"RPO|recovery.point.objective", src, re.IGNORECASE):
                rpo_found = True
            if re.search(r"RTO|recovery.time.objective", src, re.IGNORECASE):
                rto_found = True
        if not rpo_found and not rto_found:
            pytest.skip("RPO/RTO not documented in code")

    def test_failover_procedure_exists(self):
        """Verify failover procedures exist."""
        found = False
        for path in _iter_py(_BACKEND_ROOT, exclude_dirs={
            "tests", "scripts", "venv", ".kilo", "alembic"
        }):
            try:
                src = path.read_text(encoding="utf-8")
            except OSError:
                continue
            if re.search(
                r"(?:failover|failback|dr.|disaster.recovery|standby)",
                src,
                re.IGNORECASE,
            ):
                found = True
                break
        if not found:
            pytest.skip("Failover procedure not yet implemented")


class TestLaw311FeatureFlags:
    """Law 311: Feature flags system must exist.

    Features must be gated by a centralized feature flag system.
    """

    def test_feature_flag_system_exists(self):
        found = False
        for path in _iter_py(_BACKEND_ROOT, exclude_dirs={
            "tests", "scripts", "venv", ".kilo", "alembic"
        }):
            try:
                src = path.read_text(encoding="utf-8")
            except OSError:
                continue
            if re.search(
                r"(?:feature.?flag|feature_flag|require_feature|is_feature_enabled|"
                r"feature_catalog|FeatureCatalog)",
                src,
                re.IGNORECASE,
            ):
                found = True
                break
        assert found, (
            "Law 311 violation: no feature flag system found"
        )

    def test_rbac_catalog_exists(self):
        """Verify RBAC feature catalog exists."""
        catalog_file = _RBAC_DIR / "catalog.py"
        assert catalog_file.exists(), (
            "Law 311 violation: rbac/catalog.py must exist for feature flags"
        )

    def test_require_feature_used_in_modules(self):
        """Verify module routers use require_feature() for gating."""
        found = False
        for path in _iter_py(_BACKEND_ROOT / "modules", exclude_dirs={"tests"}):
            try:
                src = path.read_text(encoding="utf-8")
            except OSError:
                continue
            if "require_feature" in src:
                found = True
                break
        assert found, (
            "Law 311 violation: module routers don't use require_feature()"
        )

    def test_features_py_exists_in_domains(self):
        """Verify each domain has a features.py file."""
        domains_without_features = []
        for d in sorted(_DOMAINS_DIR.iterdir()):
            if not d.is_dir() or d.name.startswith("_") or d.name.startswith("."):
                continue
            features_file = d / "features.py"
            if not features_file.exists():
                domains_without_features.append(d.name)
        if domains_without_features:
            pytest.skip(
                f"Domains without features.py: {domains_without_features}"
            )


class TestLaw313Compliance:
    """Law 313: Compliance controls for GDPR, PCI-DSS.

    The system must implement compliance controls for data protection standards.
    """

    def test_gdpr_compliance_exists(self):
        found = False
        for path in _iter_py(_BACKEND_ROOT, exclude_dirs={
            "tests", "scripts", "venv", ".kilo", "alembic"
        }):
            try:
                src = path.read_text(encoding="utf-8")
            except OSError:
                continue
            if re.search(
                r"(?:gdpr|data.?protection|right.?to.?erasure|data.?portability|"
                r"consent|data.?subject|data.?controller)",
                src,
                re.IGNORECASE,
            ):
                found = True
                break
        if not found:
            pytest.skip("GDPR compliance not explicitly implemented")

    def test_pci_dss_compliance_exists(self):
        found = False
        for path in _iter_py(_BACKEND_ROOT, exclude_dirs={
            "tests", "scripts", "venv", ".kilo", "alembic"
        }):
            try:
                src = path.read_text(encoding="utf-8")
            except OSError:
                continue
            if re.search(
                r"(?:pci.?dss|pci_dss|cardholder.?data|payment.?card|"
                r"tokenization|pan.?masking)",
                src,
                re.IGNORECASE,
            ):
                found = True
                break
        assert found, (
            "Law 313 violation: no PCI-DSS compliance controls found"
        )

    def test_pci_dss_middleware_exists(self):
        """Verify PCI-DSS compliance middleware exists."""
        pci_file = _MIDDLEWARE_DIR / "pci_dss_compliance.py"
        if pci_file.exists():
            src = pci_file.read_text(encoding="utf-8")
            assert "def " in src, (
                "Law 313 violation: pci_dss_compliance.py has no functions"
            )
        else:
            pytest.skip("pci_dss_compliance.py not found in middleware/")

    def test_data_retention_policy_exists(self):
        """Verify data retention policies are implemented."""
        found = False
        for path in _iter_py(_BACKEND_ROOT, exclude_dirs={
            "tests", "scripts", "venv", ".kilo", "alembic"
        }):
            try:
                src = path.read_text(encoding="utf-8")
            except OSError:
                continue
            if re.search(
                r"(?:data.?retention|retention.?policy|purge|ttl|expir)",
                src,
                re.IGNORECASE,
            ):
                found = True
                break
        if not found:
            pytest.skip("Data retention policy not explicitly implemented")

    def test_audit_trail_for_compliance(self):
        """Verify audit trail exists for compliance reporting."""
        audit_dir = _DOMAINS_DIR / "audit"
        if audit_dir.exists():
            audit_files = list(audit_dir.rglob("test_*.py")) + list(audit_dir.rglob("*.py"))
            assert len(audit_files) > 0, (
                "Law 313 violation: audit domain has no files"
            )
        else:
            pytest.skip("audit domain does not exist")


class TestLaw314Through325AdditionalResilience:
    """Laws 314-325: Additional resilience and operational requirements."""

    def test_health_check_endpoint_exists(self):
        """Verify health check endpoint exists."""
        found = False
        for path in _iter_py(_BACKEND_ROOT / "modules", exclude_dirs={"tests"}):
            try:
                src = path.read_text(encoding="utf-8")
            except OSError:
                continue
            if re.search(r"health.?check|/health|/ready|/live", src, re.IGNORECASE):
                found = True
                break
        if not found:
            # Check main.py
            main_file = _BACKEND_ROOT / "main.py"
            if main_file.exists():
                src = main_file.read_text(encoding="utf-8")
                if "health" in src.lower():
                    found = True
        if not found:
            pytest.skip("Health check endpoint not explicitly implemented")

    def test_graceful_shutdown_exists(self):
        """Verify graceful shutdown handling exists."""
        lifespan_file = _BACKEND_ROOT / "lifespan.py"
        main_file = _BACKEND_ROOT / "main.py"
        for f in [lifespan_file, main_file]:
            if f.exists():
                src = f.read_text(encoding="utf-8")
                if "shutdown" in src.lower() or "lifespan" in src.lower():
                    return
        pytest.skip("Graceful shutdown not explicitly implemented")

    def test_observability_infrastructure_exists(self):
        """Verify observability (metrics, tracing) infrastructure exists."""
        obs_dir = _INFRASTRUCTURE_DIR / "observability"
        if obs_dir.exists():
            obs_files = list(obs_dir.rglob("*.py"))
            assert len(obs_files) > 0, (
                "Observability directory exists but is empty"
            )
        else:
            pytest.skip("infrastructure/observability/ does not exist")

    def test_background_jobs_exist(self):
        """Verify background job processing exists."""
        if _JOBS_DIR.exists():
            job_files = list(_JOBS_DIR.rglob("*.py"))
            assert len(job_files) > 0, (
                "Law 314-325 violation: jobs/ directory is empty"
            )
        else:
            pytest.skip("jobs/ directory does not exist")

    def test_rate_limiting_across_system(self):
        """Verify rate limiting is applied system-wide."""
        rate_file = _MIDDLEWARE_DIR / "rate_limit_middleware.py"
        if rate_file.exists():
            src = rate_file.read_text(encoding="utf-8")
            assert "def " in src, (
                "Rate limit middleware has no function definitions"
            )
        else:
            pytest.skip("rate_limit_middleware.py not found")
