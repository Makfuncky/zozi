#!/usr/bin/env python3
"""
ZOZI Backend — Architecture Audit Section Laws 201-325
Detection logic for config, testing, deployment, performance, data, API,
git, documentation, scalability, security hardening, resilience, and operations.

Uses ASTAnalyzer, ImportGraph, and pre-indexed file lists from
full_system_audit.py. Each finding is recorded via f(lid, cat, sev, file, line, desc, fix).
"""

from __future__ import annotations

import ast
import re
from collections import defaultdict
from pathlib import Path


# ══════════════════════════════════════════════════════════════
# LOCAL HELPERS
# ══════════════════════════════════════════════════════════════

def _parse_ast(content: str):
    """Parse Python source into AST, returning None on failure."""
    try:
        return ast.parse(content)
    except Exception:
        return None


def _get_functions(tree):
    """Extract all function definitions from an AST."""
    if not tree:
        return []
    return [n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]


def _get_classes(tree):
    """Extract all class definitions from an AST."""
    if not tree:
        return []
    return [n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]


def _has_docstring(func_node):
    """Check if a function has a docstring."""
    return (
        func_node.body
        and isinstance(func_node.body[0], ast.Expr)
        and isinstance(func_node.body[0].value, (ast.Constant, ast.Str))
    )


def _grep_all(files, pattern, flags=re.IGNORECASE):
    """Search all files for a regex pattern, return list of (path, line_no, line)."""
    results = []
    for p in files:
        content = read(p)
        if not content:
            continue
        for i, line in enumerate(content.split("\n"), 1):
            if re.search(pattern, line, flags):
                results.append((p, i, line.strip()))
    return results


def _any_file_contains(files, pattern, flags=re.IGNORECASE):
    """Check if any file matches a pattern."""
    for p in files:
        content = read(p)
        if content and re.search(pattern, content, flags):
            return True
    return False


def _any_file_contains_kw(files, keywords):
    """Check if any file contains all keywords."""
    for p in files:
        content = read(p)
        if not content:
            continue
        content_lower = content.lower()
        if all(kw.lower() in content_lower for kw in keywords):
            return True
    return False


def _count_files_with_pattern(files, pattern, flags=re.IGNORECASE):
    """Count files matching a pattern."""
    count = 0
    for p in files:
        content = read(p)
        if content and re.search(pattern, content, flags):
            count += 1
    return count


# ══════════════════════════════════════════════════════════════
# SECTION: Config (Laws 201-206)
# ══════════════════════════════════════════════════════════════

def _check_config():
    """Laws 201-206: Configuration management."""
    project_root = ROOT.parent

    # ── Law 201: Env hierarchy ──────────────────────────────────
    env_example_root = project_root / ".env.example"
    env_root = project_root / ".env"
    env_backend_example = ROOT / ".env.example"
    env_frontend = project_root / "frontend" / "web_app" / ".env.local"
    env_frontend_example = project_root / "frontend" / "web_app" / ".env.example"

    if not env_example_root.exists() and not env_backend_example.exists():
        f(201, "config", "high", ".env.example", 0,
          "No .env.example found at project root or backend/",
          "Create .env.example with all required vars. Hierarchy: .env.example -> .env -> backend/.env -> frontend/.env.local")

    if env_root.exists() and env_example_root.exists():
        example_content = read(env_example_root)
        root_content = read(env_root)
        example_vars = set(re.findall(r'^([A-Z_]+)=', example_content, re.MULTILINE))
        root_vars = set(re.findall(r'^([A-Z_]+)=', root_content, re.MULTILINE))
        missing_in_root = example_vars - root_vars
        if missing_in_root:
            f(201, "config", "medium", ".env", 0,
              f"Root .env missing vars from .env.example: {', '.join(sorted(missing_in_root)[:5])}",
              "Ensure .env includes all variables from .env.example")

    if not env_frontend.exists() and not env_frontend_example.exists():
        f(201, "config", "medium", "frontend/web_app/.env.local", 0,
          "No .env.local or .env.example found in frontend/web_app/",
          "Create frontend/web_app/.env.local with NEXT_PUBLIC_* vars")

    # ── Law 202: Required vars ──────────────────────────────────
    required_vars = ["SECRET_KEY", "DATABASE_URL", "REDIS_URL"]
    config_file = ROOT / "infrastructure" / "utils" / "config.py"

    if config_file.exists():
        config_content = read(config_file)
        for var in required_vars:
            if var not in config_content:
                f(202, "config", "high", rel(config_file), 0,
                  f"Required env var {var} not referenced in config",
                  f"Add {var} to Settings class with os.getenv('{var}')")
    else:
        f(202, "config", "critical", "infrastructure/utils/config.py", 0,
          "Config file not found — required vars cannot be verified",
          "Create infrastructure/utils/config.py with SECRET_KEY, DATABASE_URL, REDIS_URL")

    if env_example_root.exists():
        example_content = read(env_example_root)
        for var in required_vars:
            if var not in example_content:
                f(202, "config", "high", ".env.example", 0,
                  f"Required var {var} missing from .env.example",
                  f"Add {var}=<value> to .env.example")

    # ── Law 203: Typed flags — no raw os.getenv outside config ───
    config_dir = ROOT / "infrastructure" / "utils"
    config_file_names = {str(p) for p in config_dir.glob("*.py")} if config_dir.exists() else set()

    for p in ALL_PY:
        if str(p) in config_file_names or "config.py" in str(p):
            continue
        content = read(p)
        if not content:
            continue
        lines = content.split("\n")
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            if re.search(r'os\.getenv\s*\(', stripped):
                if not re.search(r'os\.getenv\s*\(\s*["\'][A-Z_]+["\']', stripped):
                    continue
                f(203, "config", "medium", rel(p), i,
                  f"Raw os.getenv() outside config layer: {stripped.strip()}",
                  "Move env access to infrastructure/utils/config.py Settings class")

    # ── Law 204: Secrets manager ────────────────────────────────
    has_secrets_manager = False
    secrets_keywords = [
        "aws_secretsmanager", "boto3.client('secretsmanager')",
        'boto3.client("secretsmanager")', "hashicorp.vault", "hvac",
        "SecretsManager", "vault_client",
    ]
    for p in ALL_PY:
        content = read(p)
        if not content:
            continue
        if any(kw in content for kw in secrets_keywords):
            has_secrets_manager = True
            break

    if not has_secrets_manager:
        f(204, "config", "high", "infrastructure/utils/config.py", 0,
          "No secrets manager (AWS Secrets Manager / HashiCorp Vault) integration found",
          "Add secrets manager for production. Example:\n"
          "  import boto3\n"
          "  client = boto3.client('secretsmanager')\n"
          "  secret = client.get_secret_value(SecretId='zozi/production')")

    # ── Law 205: APP_ENV detection ──────────────────────────────
    app_env_found = False
    for p in ALL_PY:
        content = read(p)
        if not content:
            continue
        if "APP_ENV" in content or "app_env" in content:
            app_env_found = True
            break

    if not app_env_found:
        f(205, "config", "high", "infrastructure/utils/config.py", 0,
          "APP_ENV detection not found in any Python file",
          "Add APP_ENV env var with values: development, test, staging, production")

    # ── Law 206: CORS allowlist ─────────────────────────────────
    cors_config_found = False
    for p in ALL_PY:
        content = read(p)
        if not content:
            continue
        if "CORS_ORIGINS" in content or "cors_origins" in content:
            cors_config_found = True
            if "*" in content and "production" in content.lower():
                lines = content.split("\n")
                for i, line in enumerate(lines, 1):
                    if "*" in line and ("cors" in line.lower() or "CORS" in line):
                        f(206, "config", "critical", rel(p), i,
                          f"Wildcard CORS origin found: {line.strip()}",
                          "Replace wildcard with explicit comma-separated origins")
            break

    if not cors_config_found:
        f(206, "config", "high", "infrastructure/utils/config.py", 0,
          "CORS configuration not found",
          "Add CORS_ORIGINS env var with comma-separated allowed origins")


# ══════════════════════════════════════════════════════════════
# SECTION: Testing (Laws 207-214)
# ══════════════════════════════════════════════════════════════

def _check_testing():
    """Laws 207-214: Testing infrastructure."""

    # ── Law 207: pytest framework ───────────────────────────────
    has_pytest = False
    has_pytest_asyncio = False

    req_files = list(ROOT.parent.glob("requirements*.txt")) + list(ROOT.glob("requirements*.txt"))
    for rf in req_files:
        content = read(rf)
        if "pytest" in content:
            has_pytest = True
        if "pytest-asyncio" in content:
            has_pytest_asyncio = True

    conftest = ROOT / "tests" / "conftest.py"
    if conftest.exists():
        has_pytest = True
        content = read(conftest)
        if "pytest_asyncio" in content or "@pytest.mark.asyncio" in content:
            has_pytest_asyncio = True

    if not has_pytest:
        f(207, "testing", "critical", "tests/conftest.py", 0,
          "pytest framework not detected",
          "Install pytest: pip install pytest pytest-asyncio")

    if not has_pytest_asyncio:
        f(207, "testing", "high", "tests/conftest.py", 0,
          "pytest-asyncio not detected — async tests will fail",
          "Install pytest-asyncio: pip install pytest-asyncio")

    # ── Law 208: Fixtures ───────────────────────────────────────
    required_fixtures = ["db_session", "client"]
    optional_fixtures = ["admin_client", "supplier_client", "customer_client"]

    if conftest.exists():
        content = read(conftest)
        for fixture in required_fixtures:
            if f"def {fixture}" not in content:
                f(208, "testing", "high", "tests/conftest.py", 0,
                  f"Required fixture '{fixture}' not found in conftest.py",
                  f"Add @{fixture} fixture in tests/conftest.py")

        found_optional = [fx for fx in optional_fixtures if f"def {fx}" in content]
        if len(found_optional) < len(optional_fixtures):
            missing = set(optional_fixtures) - set(found_optional)
            f(208, "testing", "medium", "tests/conftest.py", 0,
              f"Missing recommended fixtures: {', '.join(missing)}",
              f"Add {', '.join(missing)} fixtures for role-based testing")
    else:
        f(208, "testing", "critical", "tests/conftest.py", 0,
          "conftest.py not found — no test fixtures defined",
          "Create tests/conftest.py with db_session, client, admin_client, etc.")

    # ── Law 209: Demo users ─────────────────────────────────────
    demo_users = ["admin@zozi.com", "supplier@zozi.com", "customer@zozi.com"]
    seeding_found = False

    for p in ALL_PY:
        content = read(p)
        if not content:
            continue
        if any(user in content for user in demo_users):
            seeding_found = True
            for user in demo_users:
                if user not in content:
                    f(209, "testing", "medium", rel(p), 0,
                      f"Demo user {user} not found in seed data",
                      f"Add {user} to demo user seeding")

    if not seeding_found:
        f(209, "testing", "high", "tests/conftest.py", 0,
          "No demo user seeding found (admin@zozi.com, supplier@zozi.com, customer@zozi.com)",
          "Add demo user seeding in tests/conftest.py or infrastructure/database/seed.py")

    # ── Law 210: Test environment ───────────────────────────────
    test_env_configured = False
    if conftest.exists():
        content = read(conftest)
        if 'APP_ENV' in content and 'test' in content:
            test_env_configured = True
        if 'CSRF_DISABLED' in content:
            test_env_configured = True

    if not test_env_configured:
        f(210, "testing", "high", "tests/conftest.py", 0,
          "Test environment not properly configured (APP_ENV=test, CSRF/rate disabled)",
          "Add to conftest.py:\n"
          "  os.environ.setdefault('APP_ENV', 'test')\n"
          "  os.environ.setdefault('CSRF_DISABLED', 'true')")

    # ── Law 211: Frontend tests ─────────────────────────────────
    frontend_pkg = FRONTEND_ROOT / "web_app" / "package.json" if FRONTEND_ROOT.exists() else None
    if frontend_pkg and frontend_pkg.exists():
        pkg_content = read(frontend_pkg)
        has_jest = "jest" in pkg_content
        has_rtl = "@testing-library/react" in pkg_content
        has_playwright = "@playwright/test" in pkg_content

        if not has_jest:
            f(211, "testing", "high", "frontend/web_app/package.json", 0,
              "Jest not found in frontend devDependencies",
              "Install Jest: npm install --save-dev jest @testing-library/react @testing-library/jest-dom")

        if not has_rtl:
            f(211, "testing", "high", "frontend/web_app/package.json", 0,
              "React Testing Library not found",
              "Install RTL: npm install --save-dev @testing-library/react @testing-library/jest-dom")

        if not has_playwright:
            f(211, "testing", "medium", "frontend/web_app/package.json", 0,
              "Playwright not found for E2E testing",
              "Install Playwright: npm install --save-dev @playwright/test")
    else:
        f(211, "testing", "medium", "frontend/web_app/package.json", 0,
          "Frontend package.json not found — cannot verify test setup",
          "Ensure frontend/web_app/package.json has jest, @testing-library/react, @playwright/test")

    # ── Law 212: Architecture tests ─────────────────────────────
    arch_test_dir = ROOT / "tests" / "architecture"
    if arch_test_dir.exists():
        arch_files = list(arch_test_dir.glob("test_*.py"))
        has_import_laws = any("import_laws" in f.name for f in arch_files)
        has_feature_catalog = any("feature_catalog" in f.name for f in arch_files)

        if not has_import_laws:
            f(212, "testing", "high", "tests/architecture/", 0,
              "test_import_laws.py not found — architecture import laws not tested",
              "Create tests/architecture/test_import_laws.py")

        if not has_feature_catalog:
            f(212, "testing", "medium", "tests/architecture/", 0,
              "test_feature_catalog.py not found — feature catalog not tested",
              "Create tests/architecture/test_feature_catalog.py")
    else:
        f(212, "testing", "critical", "tests/architecture/", 0,
          "tests/architecture/ directory not found — architecture tests missing",
          "Create tests/architecture/ with test_import_laws.py and test_feature_catalog.py")

    # ── Law 213: Coverage ───────────────────────────────────────
    # Check for coverage configuration
    coverage_config = False
    coverage_files = [
        ROOT.parent / ".coveragerc",
        ROOT.parent / "pyproject.toml",
        ROOT / "pyproject.toml",
    ]
    for cf in coverage_files:
        if cf.exists():
            content = read(cf)
            if "coverage" in content:
                coverage_config = True
                break

    if not coverage_config:
        f(213, "testing", "medium", "pyproject.toml", 0,
          "No coverage configuration found — test coverage tracking required",
          "Add [tool.coverage.run] to pyproject.toml with source=backend, fail_under=80")

    # ── Law 214: Isolation ──────────────────────────────────────
    # Check for transaction rollback in conftest
    has_rollback = False
    if conftest.exists():
        content = read(conftest)
        if re.search(r'rollback|transaction.*rollback|nested.*transaction', content, re.IGNORECASE):
            has_rollback = True

    if not has_rollback:
        f(214, "testing", "high", "tests/conftest.py", 0,
          "No transaction rollback detected — tests must use transaction-rolled-back isolation",
          "Add fixture that wraps each test in a transaction and rolls back after:\n"
          "  @pytest.fixture\n"
          "  def db_session():\n"
          "    connection = engine.connect()\n"
          "    transaction = connection.begin()\n"
          "    session = Session(bind=connection)\n"
          "    yield session\n"
          "    session.close()\n"
          "    transaction.rollback()\n"
          "    connection.close()")


# ══════════════════════════════════════════════════════════════
# SECTION: Deployment (Laws 215-220)
# ══════════════════════════════════════════════════════════════

def _check_deployment():
    """Laws 215-220: Deployment infrastructure."""
    project_root = ROOT.parent

    # ── Law 215: Docker Compose ─────────────────────────────────
    compose_files = [
        project_root / "docker-compose.yml",
        project_root / "docker-compose.yaml",
    ]
    has_compose = any(cf.exists() for cf in compose_files)

    if not has_compose:
        f(215, "deployment", "high", "docker-compose.yml", 0,
          "No docker-compose.yml found — container orchestration required",
          "Create docker-compose.yml with services: backend, frontend, redis, postgres")

    # ── Law 216: Production targets ─────────────────────────────
    prod_compose = project_root / "docker-compose.prod.yml"
    has_prod_target = prod_compose.exists()

    if not has_prod_target:
        # Check for Dockerfile with production stage
        dockerfile = project_root / "Dockerfile"
        if dockerfile.exists():
            content = read(dockerfile)
            if "production" in content.lower() or "AS prod" in content or "AS production" in content:
                has_prod_target = True

    if not has_prod_target:
        f(216, "deployment", "high", "docker-compose.prod.yml", 0,
          "No production deployment target found",
          "Create docker-compose.prod.yml or multi-stage Dockerfile with production target")

    # ── Law 217: Migration on deploy ────────────────────────────
    deploy_scripts = [
        project_root / "scripts" / "deploy.sh",
        ROOT / "scripts" / "deploy.sh",
    ]
    has_migration_deploy = False
    for ds in deploy_scripts:
        if ds.exists():
            content = read(ds)
            if "alembic" in content and "upgrade" in content:
                has_migration_deploy = True
                break

    if not has_migration_deploy:
        f(217, "deployment", "high", "scripts/deploy.sh", 0,
          "No migration-on-deploy detected — alembic upgrade must run on deploy",
          "Add to deploy script:\n"
          "  alembic upgrade head\n"
          "Run migrations before starting the application server.")

    # ── Law 218: Health checks ──────────────────────────────────
    has_health_check = False
    for p in ALL_PY:
        content = read(p)
        if not content:
            continue
        if re.search(r'@app\.(get|post)\s*\(\s*["\']/?health', content):
            has_health_check = True
            break
        if "health_check" in content or "healthcheck" in content.lower():
            has_health_check = True
            break

    if not has_health_check:
        f(218, "deployment", "high", "modules/", 0,
          "No health check endpoint found — required for load balancer and k8s probes",
          "Add GET /health endpoint returning {\"status\": \"ok\", \"version\": \"...\"}")

    # ── Law 219: Rollback ───────────────────────────────────────
    has_rollback = False
    for ds in deploy_scripts:
        if ds.exists():
            content = read(ds)
            if re.search(r'rollback|rollback', content, re.IGNORECASE):
                has_rollback = True
                break

    if not has_rollback:
        f(219, "deployment", "medium", "scripts/deploy.sh", 0,
          "No rollback mechanism detected — deploy script must support rollback",
          "Add rollback command:\n"
          "  alembic downgrade -1\n"
          "Or implement blue-green deployment with instant rollback.")

    # ── Law 220: Env promotion ──────────────────────────────────
    env_promotion = False
    staging_files = list(project_root.glob("*staging*")) + list(ROOT.glob("*staging*"))
    if staging_files:
        env_promotion = True

    # Check for environment-specific configs
    env_configs = list(project_root.glob(".env.*"))
    if len(env_configs) >= 2:
        env_promotion = True

    if not env_promotion:
        f(220, "deployment", "medium", ".env.staging", 0,
          "No environment promotion pipeline detected — staging -> production required",
          "Create environment-specific configs:\n"
          "  .env.staging, .env.production\n"
          "Implement promotion: test -> staging -> production")


# ══════════════════════════════════════════════════════════════
# SECTION: Performance (Laws 221-226)
# ══════════════════════════════════════════════════════════════

def _check_performance():
    """Laws 221-226: Performance optimization."""

    # ── Law 221: Caching strategy ───────────────────────────────
    has_caching = False
    for p in ALL_PY:
        content = read(p)
        if not content:
            continue
        if re.search(r'cache|Cache|redis.*cache|@cache|cache_page', content):
            has_caching = True
            break

    if not has_caching:
        f(221, "performance", "high", "backend", 0,
          "No caching strategy detected — Redis caching required for performance",
          "Implement caching:\n"
          "  1. Use @cache decorator for expensive computations\n"
          "  2. Cache catalog queries in Redis with TTL\n"
          "  3. Use cache_page for static API responses")

    # ── Law 222: Keyset pagination ──────────────────────────────
    has_keyset = False
    has_offset = False
    for p in ALL_PY:
        content = read(p)
        if not content:
            continue
        if re.search(r'keyset|keyset_pagination|where.*id.*>.*limit', content, re.IGNORECASE):
            has_keyset = True
        if re.search(r'\.offset\s*\(', content):
            has_offset = True

    if has_offset and not has_keyset:
        f(222, "performance", "high", "backend", 0,
          "OFFSET pagination detected without keyset alternative — degrades at scale",
          "Replace OFFSET with keyset pagination:\n"
          "  query.where(Model.id > last_id).limit(20)")

    # ── Law 223: Connection pooling ─────────────────────────────
    has_pooling = False
    for p in ALL_PY:
        content = read(p)
        if not content:
            continue
        if re.search(r'pool_size|max_overflow|pool_recycle|pool_pre_ping|create_engine.*pool', content):
            has_pooling = True
            break

    if not has_pooling:
        f(223, "performance", "high", "infrastructure/database/", 0,
          "No connection pooling configuration detected — required for 100K+ users",
          "Configure SQLAlchemy connection pooling:\n"
          "  create_engine(url, pool_size=20, max_overflow=30, pool_recycle=3600, pool_pre_ping=True)")

    # ── Law 224: Query optimization ─────────────────────────────
    has_eager_load = False
    for p in ALL_PY:
        content = read(p)
        if not content:
            continue
        if re.search(r'joinedload|selectinload|subqueryload|lazy.*selectin', content):
            has_eager_load = True
            break

    if not has_eager_load:
        f(224, "performance", "high", "domains/", 0,
          "No eager loading detected — N+1 query risk for related data",
          "Add eager loading for relationships:\n"
          "  from sqlalchemy.orm import joinedload, selectinload\n"
          "  query.options(joinedload(Model.relation))")

    # ── Law 225: CDN ────────────────────────────────────────────
    has_cdn = False
    for p in FRONTEND_FILES if FRONTEND_FILES else []:
        content = read(p)
        if not content:
            continue
        if re.search(r'cdn|cloudfront|cloudflare|fastly', content, re.IGNORECASE):
            has_cdn = True
            break

    if not has_cdn:
        f(225, "performance", "medium", "frontend/", 0,
          "No CDN configuration detected — static assets must be served via CDN",
          "Configure CDN for static assets:\n"
          "  1. Set CDN domain in NEXT_PUBLIC_CDN_URL\n"
          "  2. Upload static files to S3/CloudFront\n"
          "  3. Set Cache-Control headers for immutable assets")

    # ── Law 226: Async processing ───────────────────────────────
    has_async_processing = False
    for p in ALL_PY:
        content = read(p)
        if not content:
            continue
        if re.search(r'celery|background_task|asyncio\.create_task|threading\.Thread|ProcessPoolExecutor', content):
            has_async_processing = True
            break

    if not has_async_processing:
        f(226, "performance", "high", "backend", 0,
          "No async processing detected — heavy tasks must be offloaded",
          "Implement async processing:\n"
          "  1. Use Celery for background tasks (email, image processing)\n"
          "  2. Use asyncio.create_task for fire-and-forget\n"
          "  3. Use ProcessPoolExecutor for CPU-bound work")


# ══════════════════════════════════════════════════════════════
# SECTION: Data (Laws 227-232)
# ══════════════════════════════════════════════════════════════

def _check_data():
    """Laws 227-232: Data management."""

    # ── Law 227: RLS enforcement ────────────────────────────────
    has_rls = False
    for p in ALL_PY:
        content = read(p)
        if not content:
            continue
        if re.search(r'row.level.security|rls|row_level_security|SET\s+app\.tenant', content, re.IGNORECASE):
            has_rls = True
            break

    if not has_rls:
        f(227, "data", "critical", "infrastructure/database/", 0,
          "No Row-Level Security enforcement detected — multi-tenant data isolation required",
          "Implement RLS:\n"
          "  1. Enable RLS on multi-tenant tables\n"
          "  2. SET app.tenant_id per request\n"
          "  3. CREATE POLICY for tenant isolation")

    # ── Law 228: Soft delete ────────────────────────────────────
    has_soft_delete = False
    for p in MODELS:
        content = read(p)
        if not content:
            continue
        if re.search(r'deleted_at|is_deleted|soft_delete|removed_at', content):
            has_soft_delete = True
            break

    if not has_soft_delete:
        f(228, "data", "high", "domains/", 0,
          "No soft delete pattern detected — data must be recoverable",
          "Add soft delete columns:\n"
          "  deleted_at = Column(DateTime, nullable=True)\n"
          "  is_deleted = Column(Boolean, default=False)\n"
          "Filter: query.filter(Model.is_deleted == False)")

    # ── Law 229: Audit columns ──────────────────────────────────
    has_audit_cols = False
    for p in MODELS:
        content = read(p)
        if not content:
            continue
        if re.search(r'created_at|updated_at|created_by|updated_by', content):
            has_audit_cols = True
            break

    if not has_audit_cols:
        f(229, "data", "high", "domains/", 0,
          "No audit columns detected — all tables need created_at/updated_at/created_by/updated_by",
          "Add audit columns to all models:\n"
          "  created_at = Column(DateTime, server_default=func.now())\n"
          "  updated_at = Column(DateTime, onupdate=func.now())\n"
          "  created_by = Column(ForeignKey('users.id'))\n"
          "  updated_by = Column(ForeignKey('users.id'))")

    # ── Law 230: Audit trail ────────────────────────────────────
    has_audit_trail = False
    for p in ALL_PY:
        content = read(p)
        if not content:
            continue
        if re.search(r'audit_log|audit_trail|AuditLog|audit_event', content):
            has_audit_trail = True
            break

    if not has_audit_trail:
        f(230, "data", "high", "domains/audit/", 0,
          "No audit trail system detected — all data changes must be logged",
          "Implement audit trail:\n"
          "  1. Create AuditLog model with action, entity, old_value, new_value\n"
          "  2. Log all CREATE/UPDATE/DELETE operations\n"
          "  3. Include actor, timestamp, IP address")

    # ── Law 231: Data residency ──────────────────────────────────
    has_data_residency = False
    for p in ALL_PY:
        content = read(p)
        if not content:
            continue
        if re.search(r'data.residency|data_residency|region.*restrict|country.*data|gdpr', content, re.IGNORECASE):
            has_data_residency = True
            break

    if not has_data_residency:
        f(231, "data", "medium", "backend", 0,
          "No data residency controls detected — GCC data must stay in-region",
          "Implement data residency:\n"
          "  1. Tag data with country/region\n"
          "  2. Restrict cross-region replication\n"
          "  3. Enforce data sovereignty per country")

    # ── Law 232: Backup & recovery ──────────────────────────────
    has_backup = False
    for p in ALL_PY:
        content = read(p)
        if not content:
            continue
        if re.search(r'backup|snapshot|pg_dump|WAL.*archive|point.*time.*recovery', content, re.IGNORECASE):
            has_backup = True
            break

    # Check for backup scripts
    backup_scripts = list((ROOT.parent / "scripts").glob("*backup*")) if (ROOT.parent / "scripts").exists() else []
    if backup_scripts:
        has_backup = True

    if not has_backup:
        f(232, "data", "high", "scripts/", 0,
          "No backup & recovery mechanism detected — daily backups required",
          "Implement backup strategy:\n"
          "  1. Daily pg_dump with 30-day retention\n"
          "  2. WAL archiving for point-in-time recovery\n"
          "  3. Test recovery monthly\n"
          "  4. Store backups in separate region")


# ══════════════════════════════════════════════════════════════
# SECTION: API (Laws 233-239)
# ══════════════════════════════════════════════════════════════

def _check_api():
    """Laws 233-239: API design standards."""

    # ── Law 233: REST conventions ───────────────────────────────
    has_rest_violations = False
    for p in ROUTERS:
        content = read(p)
        if not content:
            continue
        # Check for non-RESTful patterns (verbs in URLs instead of nouns)
        if re.search(r'@app\.(get|post|put|delete|patch)\s*\(\s*["\'].*?/create_', content):
            f(233, "api", "medium", rel(p), 0,
              "Non-RESTful URL pattern: verb in URL path",
              "Use nouns for resources: POST /orders instead of POST /create_order")
            has_rest_violations = True
        if re.search(r'@app\.(get|post|put|delete|patch)\s*\(\s*["\'].*?/do_', content):
            f(233, "api", "medium", rel(p), 0,
              "Non-RESTful URL pattern: action in URL path",
              "Use HTTP methods for actions: DELETE /orders/{id} instead of GET /do_delete_order")
            has_rest_violations = True

    # ── Law 234: Versioning ─────────────────────────────────────
    has_versioning = False
    for p in ROUTERS:
        content = read(p)
        if not content:
            continue
        if re.search(r'v1|v2|/api/v', content):
            has_versioning = True
            break

    if not has_versioning:
        f(234, "api", "high", "modules/", 0,
          "No API versioning detected — breaking changes must be versioned",
          "Add version prefix to API routes:\n"
          "  /api/v1/orders, /api/v2/orders\n"
          "Use APIRouter(prefix='/api/v1')")

    # ── Law 235: JSON format ────────────────────────────────────
    has_json_response = False
    for p in ROUTERS:
        content = read(p)
        if not content:
            continue
        if re.search(r'JSONResponse|response_model|jsonable_encoder', content):
            has_json_response = True
            break

    if not has_json_response:
        f(235, "api", "medium", "modules/", 0,
          "No explicit JSON response format — APIs must return JSON",
          "Use response_model or JSONResponse for all endpoints")

    # ── Law 236: RFC 7807 errors ────────────────────────────────
    has_rfc7807 = False
    for p in ALL_PY:
        content = read(p)
        if not content:
            continue
        if re.search(r'type.*uri|title.*error|detail.*error|RFC.?7807|ProblemDetail', content):
            has_rfc7807 = True
            break

    if not has_rfc7807:
        f(236, "api", "high", "backend", 0,
          "No RFC 7807 Problem Details format — errors must follow standard",
          "Implement RFC 7807:\n"
          "  {\n"
          "    \"type\": \"https://api.zozi.com/errors/insufficient-funds\",\n"
          "    \"title\": \"Insufficient Funds\",\n"
          "    \"status\": 402,\n"
          "    \"detail\": \"Account balance is too low\"\n"
          "  }")

    # ── Law 237: Pagination format ──────────────────────────────
    has_pagination = False
    for p in ALL_PY:
        content = read(p)
        if not content:
            continue
        if re.search(r'page.*size|limit.*offset|total.*count|has_next|has_prev|next_cursor', content):
            has_pagination = True
            break

    if not has_pagination:
        f(237, "api", "high", "domains/", 0,
          "No pagination format detected — list endpoints must paginate",
          "Implement pagination:\n"
          "  Response: {items: [], total: 100, page: 1, size: 20, has_next: true}\n"
          "  Query params: ?page=1&size=20")

    # ── Law 238: Filtering/sorting ──────────────────────────────
    has_filtering = False
    for p in ALL_PY:
        content = read(p)
        if not content:
            continue
        if re.search(r'filter.*param|sort.*by|order.*by.*param|__sort|__filter', content):
            has_filtering = True
            break

    if not has_filtering:
        f(238, "api", "medium", "domains/", 0,
          "No filtering/sorting support — list endpoints must support query params",
          "Add filtering and sorting:\n"
          "  ?status=active&sort=-created_at&category=electronics\n"
          "Parse query params and apply to SQLAlchemy query")

    # ── Law 239: Idempotency ────────────────────────────────────
    has_idempotency = False
    for p in ALL_PY:
        content = read(p)
        if not content:
            continue
        if re.search(r'idempoten|Idempotency-Key|idempotency_key', content):
            has_idempotency = True
            break

    if not has_idempotency:
        f(239, "api", "high", "modules/", 0,
          "No idempotency support — POST/PATCH must handle duplicate requests",
          "Implement idempotency:\n"
          "  1. Accept Idempotency-Key header\n"
          "  2. Store key+response in Redis with TTL\n"
          "  3. Return cached response for duplicate keys")


# ══════════════════════════════════════════════════════════════
# SECTION: Git (Laws 240-244)
# ══════════════════════════════════════════════════════════════

def _check_git():
    """Laws 240-244: Git workflow standards."""
    project_root = ROOT.parent

    # ── Law 240: Branching ──────────────────────────────────────
    git_dir = project_root / ".git"
    if git_dir.exists():
        # Check for branch protection (via git config or CI)
        ci_dir = project_root / ".github" / "workflows"
        has_branch_protection = False
        if ci_dir.exists():
            for p in ci_dir.glob("*.yml"):
                content = read(p)
                if re.search(r'branch.*protect|main.*protect|require.*review', content, re.IGNORECASE):
                    has_branch_protection = True
                    break

        if not has_branch_protection:
            f(240, "git", "medium", ".github/workflows/", 0,
              "No branch protection detected — main branch must be protected",
              "Add branch protection:\n"
              "  1. Require PR review before merge\n"
              "  2. Require CI pass\n"
              "  3. No direct pushes to main")

    # ── Law 241: Conventional commits ───────────────────────────
    commit_template = project_root / ".gitmessage"
    has_conventional = commit_template.exists()

    # Check CI for commit linting
    ci_dir = project_root / ".github" / "workflows"
    if ci_dir.exists():
        for p in ci_dir.glob("*.yml"):
            content = read(p)
            if re.search(r'commitlint|conventional.*commit|commit.*lint', content, re.IGNORECASE):
                has_conventional = True
                break

    if not has_conventional:
        f(241, "git", "low", ".gitmessage", 0,
          "No conventional commits enforcement — commits must follow format",
          "Add commitlint:\n"
          "  feat: add payment gateway\n"
          "  fix: resolve order total calculation\n"
          "  docs: update API documentation")

    # ── Law 242: PR process ─────────────────────────────────────
    pr_template = project_root / ".github" / "PULL_REQUEST_TEMPLATE.md"
    pr_dir = project_root / ".github" / "PULL_REQUEST_TEMPLATE"

    if not pr_template.exists() and not pr_dir.exists():
        f(242, "git", "medium", ".github/", 0,
          "No PR template found",
          "Create .github/PULL_REQUEST_TEMPLATE.md with review checklist")

    # ── Law 243: Hooks ──────────────────────────────────────────
    hooks_dir = project_root / ".githooks"
    pre_commit_hook = hooks_dir / "pre-commit" if hooks_dir.exists() else None
    pre_push_hook = hooks_dir / "pre-push" if hooks_dir.exists() else None

    if not hooks_dir.exists():
        precommit_config = project_root / ".pre-commit-config.yaml"
        if not precommit_config.exists():
            f(243, "git", "medium", ".githooks/", 0,
              "No git hooks configured (pre-commit: ruff, pre-push: architecture tests)",
              "Add .pre-commit-config.yaml with ruff linter and architecture test hooks")
    else:
        if pre_commit_hook and pre_commit_hook.exists():
            content = read(pre_commit_hook)
            if "ruff" not in content:
                f(243, "git", "medium", ".githooks/pre-commit", 0,
                  "Pre-commit hook does not run ruff",
                  "Add 'ruff check .' to pre-commit hook")
        else:
            f(243, "git", "medium", ".githooks/pre-commit", 0,
              "Pre-commit hook not found",
              "Create .githooks/pre-commit with 'ruff check .'")

        if pre_push_hook and pre_push_hook.exists():
            content = read(pre_push_hook)
            if "architecture" not in content and "import_laws" not in content:
                f(243, "git", "medium", ".githooks/pre-push", 0,
                  "Pre-push hook does not run architecture tests",
                  "Add 'python -m pytest tests/architecture/' to pre-push hook")

    # ── Law 244: Worktrees ──────────────────────────────────────
    agent_manager = project_root / ".kilo" / "agent-manager.json"
    if not agent_manager.exists():
        f(244, "git", "low", ".kilo/agent-manager.json", 0,
          "No Agent Manager worktree configuration found",
          "Agent Manager uses worktrees for parallel development sessions")


# ══════════════════════════════════════════════════════════════
# SECTION: Documentation (Laws 245-250)
# ══════════════════════════════════════════════════════════════

def _check_docs():
    """Laws 245-250: Documentation standards."""
    project_root = ROOT.parent

    # ── Law 245: Architecture docs ──────────────────────────────
    arch_doc = project_root / "ARCHITECTURE_DIAGRAM.md"
    if arch_doc.exists():
        content = read(arch_doc)
        if len(content.strip()) < 100:
            f(245, "docs", "high", "ARCHITECTURE_DIAGRAM.md", 0,
              "ARCHITECTURE_DIAGRAM.md is nearly empty — should be authoritative",
              "Document the three-axis architecture: modules -> domains -> infrastructure")
    else:
        f(245, "docs", "critical", "ARCHITECTURE_DIAGRAM.md", 0,
          "ARCHITECTURE_DIAGRAM.md not found — architecture is not documented",
          "Create ARCHITECTURE_DIAGRAM.md documenting the full system architecture")

    # ── Law 246: Agent docs ─────────────────────────────────────
    agents_doc = project_root / "AGENTS.md"
    if agents_doc.exists():
        content = read(agents_doc)
        required_sections = ["Stack", "Commands", "Architecture"]
        for section in required_sections:
            if section.lower() not in content.lower():
                f(246, "docs", "medium", "AGENTS.md", 0,
                  f"AGENTS.md missing section: {section}",
                  f"Add '{section}' section to AGENTS.md")
    else:
        f(246, "docs", "high", "AGENTS.md", 0,
          "AGENTS.md not found — agent quick reference missing",
          "Create AGENTS.md with stack, commands, and architecture overview")

    # ── Law 247: API docs ───────────────────────────────────────
    api_docs_found = False
    for p in ALL_PY:
        content = read(p)
        if not content:
            continue
        if "FastAPI(" in content:
            api_docs_found = True
            break

    if not api_docs_found:
        f(247, "docs", "high", "main.py", 0,
          "FastAPI app not found — auto-generated API docs unavailable",
          "Ensure FastAPI() is instantiated for auto-generated /docs and /redoc")

    # ── Law 248: Runbooks ───────────────────────────────────────
    runbooks_dir = project_root / "docs" / "runbooks"
    if not runbooks_dir.exists():
        f(248, "docs", "medium", "docs/runbooks/", 0,
          "docs/runbooks/ directory not found",
          "Create docs/runbooks/ with operational runbooks for common incidents")
    else:
        runbook_files = list(runbooks_dir.glob("*.md"))
        if not runbook_files:
            f(248, "docs", "medium", "docs/runbooks/", 0,
              "docs/runbooks/ is empty — no operational runbooks",
              "Add runbooks: deployment.md, rollback.md, incident-response.md")

    # ── Law 249: Code comments ──────────────────────────────────
    docstring_count = 0
    total_functions = 0
    for p in SERVICES:
        content = read(p)
        if not content:
            continue
        tree = _parse_ast(content)
        if not tree:
            continue
        funcs = _get_functions(tree)
        total_functions += len(funcs)
        for func in funcs:
            if _has_docstring(func):
                docstring_count += 1

    if total_functions > 0:
        docstring_ratio = docstring_count / total_functions
        if docstring_ratio < 0.5:
            f(249, "docs", "low", "domains/", 0,
              f"Only {docstring_ratio:.0%} of service functions have docstrings",
              "Add docstrings to all public service functions")

    # ── Law 250: Changelog ──────────────────────────────────────
    changelog = project_root / "CHANGELOG.md"
    if not changelog.exists():
        f(250, "docs", "low", "CHANGELOG.md", 0,
          "CHANGELOG.md not found",
          "Create CHANGELOG.md following Keep a Changelog format")
    else:
        content = read(changelog)
        if len(content.strip()) < 50:
            f(250, "docs", "low", "CHANGELOG.md", 0,
              "CHANGELOG.md is nearly empty",
              "Document version history in CHANGELOG.md")


# ══════════════════════════════════════════════════════════════
# SECTION: Scalability (Laws 251-270)
# ══════════════════════════════════════════════════════════════

def _check_scalability():
    """Laws 251-270: Scalability patterns."""

    # ── Law 251: Horizontal scaling ──────────────────────────────
    has_redis_sessions = False
    for p in ALL_PY:
        content = read(p)
        if not content:
            continue
        if re.search(r'redis|Redis', content) and re.search(r'session|Session', content):
            has_redis_sessions = True
            break

    for p in MIDDLEWARE_FILES:
        content = read(p)
        if re.search(r'session|Session', content) and re.search(r'redis|Redis', content):
            has_redis_sessions = True
            break

    config_paths = [ROOT / "core" / "config.py", ROOT / "config.py", ROOT / "settings.py"]
    for cp in config_paths:
        if cp.exists():
            content = read(cp)
            if re.search(r'SESSION.*REDIS|REDIS.*SESSION', content, re.IGNORECASE):
                has_redis_sessions = True
                break

    if not has_redis_sessions:
        f(251, "Scalability", "high", "backend", 0,
          "No Redis-based session storage detected — horizontal scaling requires stateless replicas with shared session storage in Redis (Law 251).",
          "Configure Redis-backed sessions:\n"
          "  SESSION_BACKEND='redis'\n"
          "  REDIS_SESSION_URL=redis://localhost:6379/1")

    # ── Law 252: Auto-scaling ───────────────────────────────────
    deploy_paths = [
        ROOT.parent / "docker-compose.yml",
        ROOT.parent / "docker-compose.prod.yml",
        ROOT.parent / "k8s" / "deployment.yml",
        ROOT.parent / "k8s" / "hpa.yml",
    ]
    has_autoscaling = False
    for dp in deploy_paths:
        if dp.exists():
            content = read(dp)
            if re.search(r'hpa|autoscal|scale.*cpu|HorizontalPodAutoscaler', content, re.IGNORECASE):
                has_autoscaling = True
                break

    if not has_autoscaling:
        f(252, "Scalability", "medium", "backend", 0,
          "No auto-scaling configuration detected — system must scale based on CPU > 70% with min 2, max 20 replicas (Law 252).",
          "Add Kubernetes HPA:\n"
          "  minReplicas: 2\n"
          "  maxReplicas: 20\n"
          "  averageUtilization: 70")

    # ── Law 253: Partitioning ───────────────────────────────────
    has_partitioning = False
    for p in MODELS:
        content = read(p)
        if re.search(r'partition|Partition|PARTITION', content):
            has_partitioning = True
            break

    alembic_dir = ROOT / "alembic" / "versions"
    if alembic_dir.exists() and not has_partitioning:
        for p in alembic_dir.glob("*.py"):
            content = read(p)
            if re.search(r'partition|Partition|PARTITION', content):
                has_partitioning = True
                break

    if not has_partitioning:
        f(253, "Scalability", "medium", "backend", 0,
          "No table partitioning detected — large tables must use range partitioning by created_at (Law 253).",
          "Implement PostgreSQL range partitioning:\n"
          "  CREATE TABLE orders (...) PARTITION BY RANGE (created_at);")

    # ── Law 254: CQRS ───────────────────────────────────────────
    has_commands = False
    has_events = False
    has_read_models = False

    for p in SERVICES:
        content = read(p)
        name = p.name.lower()
        if 'command' in name or 'handler' in name:
            has_commands = True
        if 'event' in name or 'subscriber' in name:
            has_events = True
        if 'read' in name or 'query' in name:
            has_read_models = True

    for p in ALL_PY:
        content = read(p)
        if re.search(r'class\s+\w+Command|CommandHandler', content):
            has_commands = True
        if re.search(r'class\s+\w+Event|EventHandler|EventSubscriber', content):
            has_events = True

    if not (has_commands and has_events):
        f(254, "Scalability", "medium", "backend", 0,
          "CQRS pattern not fully implemented — commands must write, events must update read models (Law 254).",
          "Implement CQRS:\n"
          "  1. Command handlers in domains/{d}/commands/\n"
          "  2. Event handlers in domains/{d}/events/\n"
          "  3. Read models in domains/{d}/read_models/")

    # ── Law 255: Write-behind cache ─────────────────────────────
    has_write_behind = False
    for p in ALL_PY:
        content = read(p)
        if re.search(r'write.behind|write_behind|buffer.*flush', content, re.IGNORECASE):
            has_write_behind = True
            break
        if re.search(r'redis.*queue|queue.*redis', content, re.IGNORECASE) and re.search(r'flush|persist', content, re.IGNORECASE):
            has_write_behind = True
            break

    if not has_write_behind:
        f(255, "Scalability", "low", "backend", 0,
          "No write-behind cache pattern detected — buffer writes in Redis and flush async (Law 255).",
          "Implement write-behind caching:\n"
          "  1. Write to Redis list/queue immediately\n"
          "  2. Background worker flushes to DB in batches")

    # ── Law 256: Tenant quotas ──────────────────────────────────
    has_quotas = False
    for p in ALL_PY:
        content = read(p)
        if re.search(r'quota|limit.*country|country.*limit', content, re.IGNORECASE):
            has_quotas = True
            break
        if re.search(r'429|Too Many Requests|rate.limit', content):
            has_quotas = True
            break

    for p in MIDDLEWARE_FILES:
        content = read(p)
        if re.search(r'quota|rate.*limit|limit.*request', content, re.IGNORECASE):
            has_quotas = True
            break

    if not has_quotas:
        f(256, "Scalability", "high", "backend", 0,
          "No tenant quota enforcement detected — per-country limits with 429 response required (Law 256).",
          "Implement tenant quotas:\n"
          "  1. Add quota middleware checking per-country limits\n"
          "  2. Store quotas in Redis with TTL\n"
          "  3. Return HTTP 429 when quota exceeded")

    # ── Law 257: Full-text search ───────────────────────────────
    has_search = False
    for p in ALL_PY:
        content = read(p)
        if re.search(r'elasticsearch|opensearch|Elasticsearch|OpenSearch', content):
            has_search = True
            break

    for p in PROVIDERS:
        content = read(p)
        if re.search(r'search|elastic|opensearch', content, re.IGNORECASE):
            has_search = True
            break

    if not has_search:
        f(257, "Scalability", "medium", "backend", 0,
          "No full-text search engine detected — catalog search must use Elasticsearch or OpenSearch (Law 257).",
          "Add search provider:\n"
          "  1. Create providers/search/ with Elasticsearch client\n"
          "  2. Index catalog products on create/update\n"
          "  3. Route search queries to ES/OpenSearch")

    # ── Law 258: Image pipeline ─────────────────────────────────
    has_image_pipeline = False
    for p in ALL_PY:
        content = read(p)
        if re.search(r'webp|WebP|resize|thumbnail|pillow|PIL', content, re.IGNORECASE):
            has_image_pipeline = True
            break
        if re.search(r'exif|metadata.*strip|strip.*metadata', content, re.IGNORECASE):
            has_image_pipeline = True
            break

    if not has_image_pipeline:
        f(258, "Scalability", "medium", "backend", 0,
          "No image pipeline detected — images must be resized async, converted to WebP, and have metadata stripped (Law 258).",
          "Implement image pipeline:\n"
          "  1. Use Pillow for resize\n"
          "  2. Convert to WebP format\n"
          "  3. Strip EXIF metadata\n"
          "  4. Process via Celery task asynchronously")

    # ── Law 259: API caching ────────────────────────────────────
    has_api_caching = False
    for p in ALL_PY:
        content = read(p)
        if re.search(r'ETag|Last-Modified|Cache-Control|cache_control|etag', content):
            has_api_caching = True
            break

    if not has_api_caching:
        f(259, "Scalability", "high", "backend", 0,
          "No API caching headers detected — ETag, Last-Modified, Cache-Control required (Law 259).",
          "Add caching headers:\n"
          "  Cache-Control: public, max-age=3600\n"
          "  ETag: \"v1-abc123\"\n"
          "  Last-Modified: Wed, 21 Oct 2024 07:28:00 GMT")

    # ── Law 260: PgBouncer ──────────────────────────────────────
    has_pgbouncer = False
    for p in ALL_PY:
        content = read(p)
        if re.search(r'pgbouncer|pg_bouncer|transaction.*pool', content, re.IGNORECASE):
            has_pgbouncer = True
            break

    # Check docker-compose for PgBouncer
    compose_path = ROOT.parent / "docker-compose.yml"
    if compose_path.exists():
        content = read(compose_path)
        if "pgbouncer" in content.lower():
            has_pgbouncer = True

    if not has_pgbouncer:
        f(260, "Scalability", "high", "backend", 0,
          "No PgBouncer detected — connection pooling middleware required for 100K+ users (Law 260).",
          "Add PgBouncer:\n"
          "  1. Add pgbouncer service to docker-compose\n"
          "  2. Set pool_mode = transaction\n"
          "  3. Point DATABASE_URL to PgBouncer port")

    # ── Law 261: Read replicas ──────────────────────────────────
    has_read_replicas = False
    for p in ALL_PY:
        content = read(p)
        if re.search(r'read_replicas|read_replica|replica.*bind|bind.*replica|READ_REPLICA', content, re.IGNORECASE):
            has_read_replicas = True
            break

    if not has_read_replicas:
        f(261, "Scalability", "medium", "backend", 0,
          "No read replicas detected — read-heavy queries must use replicas (Law 261).",
          "Configure read replicas:\n"
          "  1. Set up PostgreSQL streaming replication\n"
          "  2. Route read queries to replica\n"
          "  3. Route write queries to primary")

    # ── Law 262: Archiving ──────────────────────────────────────
    has_archiving = False
    for p in ALL_PY:
        content = read(p)
        if re.search(r'archive|archive.*table|cold.*storage|move.*archive', content, re.IGNORECASE):
            has_archiving = True
            break

    if not has_archiving:
        f(262, "Scalability", "low", "backend", 0,
          "No data archiving detected — old data must be moved to cold storage (Law 262).",
          "Implement archiving:\n"
          "  1. Create archive tables for old data\n"
          "  2. Move data older than 1 year\n"
          "  3. Store in cheaper storage (S3 Glacier)")

    # ── Law 263: Write buffering ────────────────────────────────
    has_write_buffer = False
    for p in ALL_PY:
        content = read(p)
        if re.search(r'write.*buffer|buffer.*write|batch.*insert|bulk.*insert', content, re.IGNORECASE):
            has_write_buffer = True
            break

    if not has_write_buffer:
        f(263, "Scalability", "low", "backend", 0,
          "No write buffering detected — batch writes for high-throughput (Law 263).",
          "Implement write buffering:\n"
          "  1. Buffer writes in memory/Redis\n"
          "  2. Flush in batches (100ms or 1000 rows)\n"
          "  3. Use bulk_insert_mappings for efficiency")

    # ── Law 264: Static assets ──────────────────────────────────
    has_static_config = False
    for p in FRONTEND_FILES if FRONTEND_FILES else []:
        content = read(p)
        if re.search(r'static|asset|immutable|cache.*static', content, re.IGNORECASE):
            has_static_config = True
            break

    if not has_static_config:
        f(264, "Scalability", "medium", "frontend/", 0,
          "No static asset optimization detected — immutable caching required (Law 264).",
          "Optimize static assets:\n"
          "  1. Use hashed filenames (main.abc123.js)\n"
          "  2. Set Cache-Control: immutable, max-age=31536000\n"
          "  3. Serve from CDN")

    # ── Law 265: DB monitoring ──────────────────────────────────
    has_db_monitoring = False
    for p in ALL_PY:
        content = read(p)
        if re.search(r'slow.*query|query.*time|pg_stat|explain.*analyze|db.*monitor', content, re.IGNORECASE):
            has_db_monitoring = True
            break

    if not has_db_monitoring:
        f(265, "Scalability", "high", "backend", 0,
          "No database monitoring detected — slow query tracking required (Law 265).",
          "Implement DB monitoring:\n"
          "  1. Log queries > 100ms\n"
          "  2. Use pg_stat_statements\n"
          "  3. Set up Grafana dashboard for DB metrics")

    # ── Law 266: Synthetic monitoring ───────────────────────────
    has_synthetic = False
    for p in ALL_PY:
        content = read(p)
        if re.search(r'synthetic|heartbeat|uptime|ping.*monitor|check.*endpoint', content, re.IGNORECASE):
            has_synthetic = True
            break

    if not has_synthetic:
        f(266, "Scalability", "medium", "backend", 0,
          "No synthetic monitoring detected — endpoint health checks required (Law 266).",
          "Implement synthetic monitoring:\n"
          "  1. Ping critical endpoints every 60s\n"
          "  2. Alert on failure\n"
          "  3. Monitor from multiple regions")

    # ── Law 267: Endpoint limits ────────────────────────────────
    has_endpoint_limits = False
    for p in MIDDLEWARE_FILES:
        content = read(p)
        if re.search(r'max.*request|rate.*limit|throttl|endpoint.*limit', content, re.IGNORECASE):
            has_endpoint_limits = True
            break

    if not has_endpoint_limits:
        f(267, "Scalability", "high", "middleware/", 0,
          "No endpoint rate limits detected — per-endpoint throttling required (Law 267).",
          "Implement endpoint limits:\n"
          "  1. Rate limit per endpoint per user\n"
          "  2. Use sliding window algorithm\n"
          "  3. Return 429 with Retry-After header")

    # ── Law 268: Load shedding ──────────────────────────────────
    has_load_shedding = False
    for p in ALL_PY:
        content = read(p)
        if re.search(r'load.*shed|shedding|backpressure|reject.*overload|overload.*protect', content, re.IGNORECASE):
            has_load_shedding = True
            break

    if not has_load_shedding:
        f(268, "Scalability", "medium", "backend", 0,
          "No load shedding detected — reject requests under extreme load (Law 268).",
          "Implement load shedding:\n"
          "  1. Monitor request queue depth\n"
          "  2. Return 503 when overloaded\n"
          "  3. Prioritize critical endpoints")

    # ── Law 269: Cost optimization ──────────────────────────────
    has_cost_opt = False
    for p in ALL_PY:
        content = read(p)
        if re.search(r'cost.*optim|spot.*instance|reserved.*instance|right.*size', content, re.IGNORECASE):
            has_cost_opt = True
            break

    if not has_cost_opt:
        f(269, "Scalability", "low", "backend", 0,
          "No cost optimization detected — spot instances and right-sizing required (Law 269).",
          "Implement cost optimization:\n"
          "  1. Use spot instances for batch workloads\n"
          "  2. Right-size instances based on usage\n"
          "  3. Use reserved instances for baseline")

    # ── Law 270: Chaos engineering ──────────────────────────────
    has_chaos = False
    for p in ALL_PY:
        content = read(p)
        if re.search(r'chaos|fault.*inject|latency.*inject|kill.*instance|net.*partition', content, re.IGNORECASE):
            has_chaos = True
            break

    if not has_chaos:
        f(270, "Scalability", "low", "backend", 0,
          "No chaos engineering detected — fault injection testing required (Law 270).",
          "Implement chaos engineering:\n"
          "  1. Randomly kill instances in staging\n"
          "  2. Inject network latency\n"
          "  3. Test circuit breaker behavior")


# ══════════════════════════════════════════════════════════════
# SECTION: Security Hardening (Laws 271-295)
# ══════════════════════════════════════════════════════════════

def _check_security_hardening():
    """Laws 271-295: Advanced security hardening."""

    # ── Law 271: AI-agent security ───────────────────────────────
    has_ai_security = False
    for p in ALL_PY:
        content = read(p)
        if re.search(r'agent.*security|ai.*agent.*restrict|prompt.*inject|agent.*sandbox', content, re.IGNORECASE):
            has_ai_security = True
            break

    if not has_ai_security:
        f(271, "Security", "high", "backend", 0,
          "No AI-agent security detected — agent sandboxing and prompt injection protection required (Law 271).",
          "Implement AI-agent security:\n"
          "  1. Sandbox agent execution\n"
          "  2. Detect prompt injection attempts\n"
          "  3. Limit agent file system access")

    # ── Law 272: Data exfiltration ───────────────────────────────
    has_exfil_protection = False
    for p in ALL_PY:
        content = read(p)
        if re.search(r'exfil|data.*loss.*prevent|DLP|egress.*filter', content, re.IGNORECASE):
            has_exfil_protection = True
            break

    if not has_exfil_protection:
        f(272, "Security", "high", "backend", 0,
          "No data exfiltration protection detected — DLP controls required (Law 272).",
          "Implement data exfiltration protection:\n"
          "  1. Monitor outbound data volume\n"
          "  2. Block suspicious egress patterns\n"
          "  3. Alert on bulk data access")

    # ── Law 273: Model poisoning ────────────────────────────────
    has_model_poisoning = False
    for p in ALL_PY:
        content = read(p)
        if re.search(r'model.*poison|poison.*detect|training.*data.*valid|model.*integrity', content, re.IGNORECASE):
            has_model_poisoning = True
            break

    if not has_model_poisoning:
        f(273, "Security", "medium", "backend", 0,
          "No model poisoning detection — ML model integrity checks required (Law 273).",
          "Implement model poisoning detection:\n"
          "  1. Validate training data integrity\n"
          "  2. Monitor model performance drift\n"
          "  3. Sign model artifacts")

    # ── Law 274: Adversarial detection ──────────────────────────
    has_adversarial = False
    for p in ALL_PY:
        content = read(p)
        if re.search(r'adversarial|adversarial.*detect|input.*anomal|perturbation.*detect', content, re.IGNORECASE):
            has_adversarial = True
            break

    if not has_adversarial:
        f(274, "Security", "medium", "backend", 0,
          "No adversarial detection — input anomaly detection required (Law 274).",
          "Implement adversarial detection:\n"
          "  1. Monitor input patterns for anomalies\n"
          "  2. Rate limit suspicious inputs\n"
          "  3. Alert on adversarial patterns")

    # ── Law 275: Encryption at rest ─────────────────────────────
    has_encryption_rest = False
    for p in ALL_PY:
        content = read(p)
        if re.search(r'encrypt.*rest|aes.*256|transparent.*data.*encrypt|TDE', content, re.IGNORECASE):
            has_encryption_rest = True
            break

    if not has_encryption_rest:
        f(275, "Security", "critical", "backend", 0,
          "No encryption at rest detected — database encryption required (Law 275).",
          "Implement encryption at rest:\n"
          "  1. Enable PostgreSQL TDE\n"
          "  2. Encrypt S3 buckets\n"
          "  3. Use AES-256 for sensitive fields")

    # ── Law 276: Encryption in transit ──────────────────────────
    has_encryption_transit = False
    for p in ALL_PY:
        content = read(p)
        if re.search(r'tls|ssl|https|encrypt.*transit|certificate', content, re.IGNORECASE):
            has_encryption_transit = True
            break

    if not has_encryption_transit:
        f(276, "Security", "critical", "backend", 0,
          "No encryption in transit detected — TLS/SSL required (Law 276).",
          "Implement encryption in transit:\n"
          "  1. Enforce HTTPS for all endpoints\n"
          "  2. Use TLS 1.3 for database connections\n"
          "  3. Enable HSTS header")

    # ── Law 277: Key rotation ───────────────────────────────────
    has_key_rotation = False
    for p in ALL_PY:
        content = read(p)
        if re.search(r'key.*rotation|rotate.*key|rotation.*period|key.*expir', content, re.IGNORECASE):
            has_key_rotation = True
            break

    if not has_key_rotation:
        f(277, "Security", "high", "backend", 0,
          "No key rotation detected — periodic key rotation required (Law 277).",
          "Implement key rotation:\n"
          "  1. Rotate JWT signing keys every 90 days\n"
          "  2. Rotate API keys annually\n"
          "  3. Automate rotation with KMS")

    # ── Law 278: WORM audit ─────────────────────────────────────
    has_worm = False
    for p in ALL_PY:
        content = read(p)
        if re.search(r'worm|write.*once|immutable.*audit|append.*only.*audit', content, re.IGNORECASE):
            has_worm = True
            break

    if not has_worm:
        f(278, "Security", "high", "backend", 0,
          "No WORM audit storage detected — write-once audit logs required (Law 278).",
          "Implement WORM audit:\n"
          "  1. Store audit logs in append-only storage\n"
          "  2. Use S3 Object Lock\n"
          "  3. Prevent audit log modification")

    # ── Law 279: Session binding ────────────────────────────────
    has_session_binding = False
    for p in ALL_PY:
        content = read(p)
        if re.search(r'session.*bind|bind.*session|device.*fingerprint|session.*fingerprint', content, re.IGNORECASE):
            has_session_binding = True
            break

    if not has_session_binding:
        f(279, "Security", "high", "backend", 0,
          "No session binding detected — sessions must be bound to device/IP (Law 279).",
          "Implement session binding:\n"
          "  1. Bind session to device fingerprint\n"
          "  2. Invalidate on IP change\n"
          "  3. Alert on session hijacking attempts")

    # ── Law 280: Brute force DB level ───────────────────────────
    has_brute_force_db = False
    for p in ALL_PY:
        content = read(p)
        if re.search(r'brute.*force|failed.*login.*count|account.*lock|login.*attempt', content, re.IGNORECASE):
            has_brute_force_db = True
            break

    if not has_brute_force_db:
        f(280, "Security", "high", "backend", 0,
          "No brute force protection detected — account lockout required (Law 280).",
          "Implement brute force protection:\n"
          "  1. Lock account after 5 failed attempts\n"
          "  2. Exponential backoff\n"
          "  3. Alert on brute force patterns")

    # ── Law 281: Bot detection ──────────────────────────────────
    has_bot_detection = False
    for p in ALL_PY:
        content = read(p)
        if re.search(r'bot.*detect|captcha|recaptcha|hcaptcha|bot.*protect', content, re.IGNORECASE):
            has_bot_detection = True
            break

    if not has_bot_detection:
        f(281, "Security", "high", "backend", 0,
          "No bot detection detected — CAPTCHA/bot protection required (Law 281).",
          "Implement bot detection:\n"
          "  1. Add CAPTCHA to login/register\n"
          "  2. Use rate limiting per IP\n"
          "  3. Detect automated patterns")

    # ── Law 282: PII masking ────────────────────────────────────
    has_pii_masking = False
    for p in ALL_PY:
        content = read(p)
        if re.search(r'pii.*mask|mask.*pii|personally.*identif|data.*mask|sensitive.*mask', content, re.IGNORECASE):
            has_pii_masking = True
            break

    if not has_pii_masking:
        f(282, "Security", "high", "backend", 0,
          "No PII masking detected — sensitive data must be masked in logs/responses (Law 282).",
          "Implement PII masking:\n"
          "  1. Mask email: j***@example.com\n"
          "  2. Mask phone: +966-***-**12\n"
          "  3. Mask credit card: ****-****-****-1234")

    # ── Law 283: MFA ────────────────────────────────────────────
    has_mfa = False
    for p in ALL_PY:
        content = read(p)
        if re.search(r'mfa|multi.*factor|totp|2fa|two.*factor|authenticator', content, re.IGNORECASE):
            has_mfa = True
            break

    if not has_mfa:
        f(283, "Security", "critical", "backend", 0,
          "No multi-factor authentication detected — MFA required for sensitive operations (Law 283).",
          "Implement MFA:\n"
          "  1. Add TOTP support\n"
          "  2. Require MFA for admin operations\n"
          "  3. Support backup codes")

    # ── Law 284: Zero-trust ─────────────────────────────────────
    has_zero_trust = False
    for p in ALL_PY:
        content = read(p)
        if re.search(r'zero.*trust|zero_trust|never.*trust|always.*verify|mTLS', content, re.IGNORECASE):
            has_zero_trust = True
            break

    if not has_zero_trust:
        f(284, "Security", "high", "backend", 0,
          "No zero-trust architecture detected — always verify, never trust (Law 284).",
          "Implement zero-trust:\n"
          "  1. Verify every request\n"
          "  2. Use mTLS for service-to-service\n"
          "  3. Implement least-privilege access")

    # ── Law 285: CSP ────────────────────────────────────────────
    has_csp = False
    for p in ALL_PY:
        content = read(p)
        if re.search(r'content.*security.*policy|CSP|content_security_policy', content, re.IGNORECASE):
            has_csp = True
            break

    if not has_csp:
        f(285, "Security", "high", "backend", 0,
          "No Content Security Policy detected — CSP headers required (Law 285).",
          "Implement CSP:\n"
          "  Content-Security-Policy: default-src 'self'; script-src 'self'")

    # ── Law 286: SRI ────────────────────────────────────────────
    has_sri = False
    for p in FRONTEND_FILES if FRONTEND_FILES else []:
        content = read(p)
        if re.search(r'integrity|SRI|subresource.*integrity', content, re.IGNORECASE):
            has_sri = True
            break

    if not has_sri:
        f(286, "Security", "medium", "frontend/", 0,
          "No Subresource Integrity detected — SRI required for external scripts (Law 286).",
          "Implement SRI:\n"
          "  <script src=\"...\" integrity=\"sha384-...\" crossorigin=\"anonymous\">")

    # ── Law 287: All security headers ───────────────────────────
    has_security_headers = False
    for p in ALL_PY:
        content = read(p)
        if re.search(r'X-Frame-Options|X-Content-Type|Strict-Transport|Referrer-Policy|Permissions-Policy', content):
            has_security_headers = True
            break

    if not has_security_headers:
        f(287, "Security", "high", "backend", 0,
          "Missing security headers — all security headers required (Law 287).",
          "Add security headers:\n"
          "  X-Frame-Options: DENY\n"
          "  X-Content-Type-Options: nosniff\n"
          "  Strict-Transport-Security: max-age=31536000\n"
          "  Referrer-Policy: strict-origin-when-cross-origin")

    # ── Law 288: Disclosure process ─────────────────────────────
    has_disclosure = False
    project_root = ROOT.parent
    security_md = project_root / "SECURITY.md"
    if security_md.exists():
        content = read(security_md)
        if re.search(r'disclosure|responsible.*disclosure|security.*report|vulnerability.*report', content, re.IGNORECASE):
            has_disclosure = True

    if not has_disclosure:
        f(288, "Security", "medium", "SECURITY.md", 0,
          "No vulnerability disclosure process detected — SECURITY.md required (Law 288).",
          "Create SECURITY.md with:\n"
          "  1. How to report vulnerabilities\n"
          "  2. Response time commitments\n"
          "  3. Bug bounty program (if applicable)")

    # ── Law 289: Pen testing ────────────────────────────────────
    has_pentest = False
    for p in ALL_PY:
        content = read(p)
        if re.search(r'penetration.*test|pentest|security.*audit|vulnerability.*scan', content, re.IGNORECASE):
            has_pentest = True
            break

    if not has_pentest:
        f(289, "Security", "medium", "backend", 0,
          "No penetration testing detected — annual pen testing required (Law 289).",
          "Schedule penetration testing:\n"
          "  1. Annual third-party pen test\n"
          "  2. Quarterly automated scans\n"
          "  3. Remediate findings within 30 days")

    # ── Law 290: Dependency pinning ─────────────────────────────
    has_pinned_deps = False
    req_files = list(ROOT.parent.glob("requirements*.txt")) + list(ROOT.glob("requirements*.txt"))
    for rf in req_files:
        content = read(rf)
        if re.search(r'==\d+\.\d+', content):
            has_pinned_deps = True
            break

    if not has_pinned_deps:
        f(290, "Security", "high", "requirements.txt", 0,
          "Dependencies not pinned — exact versions required for reproducibility (Law 290).",
          "Pin all dependencies:\n"
          "  fastapi==0.115.0\n"
          "  sqlalchemy==2.0.23\n"
          "Use pip-compile or poetry lock")

    # ── Law 291: SBOM ───────────────────────────────────────────
    has_sbom = False
    sbom_files = list(project_root.glob("*sbom*")) + list(project_root.glob("*SBOM*"))
    if sbom_files:
        has_sbom = True

    for p in ALL_PY:
        content = read(p)
        if re.search(r'sbom|software.*bill.*material|cyclonedx|spdx', content, re.IGNORECASE):
            has_sbom = True
            break

    if not has_sbom:
        f(291, "Security", "medium", "backend", 0,
          "No SBOM detected — Software Bill of Materials required (Law 291).",
          "Generate SBOM:\n"
          "  1. Use cyclonedx-py or pip-sbom\n"
          "  2. Generate on each release\n"
          "  3. Track all transitive dependencies")

    # ── Law 292: License compliance ─────────────────────────────
    has_license_check = False
    for p in ALL_PY:
        content = read(p)
        if re.search(r'license.*compliance|license.*check|license.*scan|osi.*approv', content, re.IGNORECASE):
            has_license_check = True
            break

    if not has_license_check:
        f(292, "Security", "low", "backend", 0,
          "No license compliance checking detected — dependency license audit required (Law 292).",
          "Implement license compliance:\n"
          "  1. Use pip-licenses or licensecheck\n"
          "  2. Block GPL in proprietary code\n"
          "  3. Generate license report")

    # ── Law 293: Incident automation ────────────────────────────
    has_incident_auto = False
    for p in ALL_PY:
        content = read(p)
        if re.search(r'incident.*auto|auto.*incident|incident.*response.*auto|runbook.*auto', content, re.IGNORECASE):
            has_incident_auto = True
            break

    if not has_incident_auto:
        f(293, "Security", "medium", "backend", 0,
          "No incident automation detected — automated incident response required (Law 293).",
          "Implement incident automation:\n"
          "  1. Auto-create incidents from alerts\n"
          "  2. Auto-assign based on service ownership\n"
          "  3. Auto-remediate known issues")

    # ── Law 294: Security training ──────────────────────────────
    has_security_training = False
    for p in ALL_PY:
        content = read(p)
        if re.search(r'security.*training|secure.*coding|security.*aware|phishing.*train', content, re.IGNORECASE):
            has_security_training = True
            break

    if not has_security_training:
        f(294, "Security", "low", "backend", 0,
          "No security training detected — annual security training required (Law 294).",
          "Implement security training:\n"
          "  1. Annual secure coding training\n"
          "  2. Phishing simulation\n"
          "  3. Security champion program")

    # ── Law 295: Supply chain ───────────────────────────────────
    has_supply_chain = False
    for p in ALL_PY:
        content = read(p)
        if re.search(r'supply.*chain|dependency.*verify|checksum.*verify|sigstore|cosign', content, re.IGNORECASE):
            has_supply_chain = True
            break

    if not has_supply_chain:
        f(295, "Security", "medium", "backend", 0,
          "No supply chain security detected — dependency verification required (Law 295).",
          "Implement supply chain security:\n"
          "  1. Verify package checksums\n"
          "  2. Use sigstore/cosign for signing\n"
          "  3. Scan dependencies for known vulnerabilities")


# ══════════════════════════════════════════════════════════════
# SECTION: Resilience (Laws 296-310)
# ══════════════════════════════════════════════════════════════

def _check_resilience():
    """Laws 296-310: Resilience patterns."""

    # ── Law 296: Circuit breaker ────────────────────────────────
    has_circuit_breaker = False
    for p in ALL_PY:
        content = read(p)
        if re.search(r'circuit.*breaker|circuit_breaker|CircuitBreaker|open.*circuit', content, re.IGNORECASE):
            has_circuit_breaker = True
            break

    if not has_circuit_breaker:
        f(296, "Resilience", "high", "backend", 0,
          "No circuit breaker detected — required for external service calls (Law 296).",
          "Implement circuit breaker:\n"
          "  1. Use pybreaker or tenacity\n"
          "  2. Open after 5 failures\n"
          "  3. Half-open after 30s timeout")

    # ── Law 297: Retry + backoff ────────────────────────────────
    has_retry = False
    for p in ALL_PY:
        content = read(p)
        if re.search(r'retry|backoff|exponential.*backoff|tenacity', content, re.IGNORECASE):
            has_retry = True
            break

    if not has_retry:
        f(297, "Resilience", "high", "backend", 0,
          "No retry with backoff detected — transient failures must be retried (Law 297).",
          "Implement retry with backoff:\n"
          "  1. Use tenacity or backoff library\n"
          "  2. Exponential backoff: 1s, 2s, 4s, 8s\n"
          "  3. Max 3 retries with jitter")

    # ── Law 298: Dead letter queue ──────────────────────────────
    has_dlq = False
    for p in ALL_PY:
        content = read(p)
        if re.search(r'dead.*letter|dead_letter|DLQ|failed.*queue|error.*queue', content, re.IGNORECASE):
            has_dlq = True
            break

    if not has_dlq:
        f(298, "Resilience", "medium", "backend", 0,
          "No dead letter queue detected — failed events must be queued for retry (Law 298).",
          "Implement dead letter queue:\n"
          "  1. Route failed events to DLQ\n"
          "  2. Retry DLQ items after delay\n"
          "  3. Alert after max retries")

    # ── Law 299: Feature health ─────────────────────────────────
    has_feature_health = False
    for p in ALL_PY:
        content = read(p)
        if re.search(r'feature.*health|health.*feature|feature.*status|feature.*degrad', content, re.IGNORECASE):
            has_feature_health = True
            break

    if not has_feature_health:
        f(299, "Resilience", "medium", "backend", 0,
          "No feature health monitoring detected — per-feature health checks required (Law 299).",
          "Implement feature health:\n"
          "  1. Track success rate per feature\n"
          "  2. Alert on degradation\n"
          "  3. Auto-disable unhealthy features")

    # ── Law 300: Per-feature fallback ───────────────────────────
    has_feature_fallback = False
    for p in ALL_PY:
        content = read(p)
        if re.search(r'feature.*fallback|fallback.*feature|degrade.*feature|feature.*degrad', content, re.IGNORECASE):
            has_feature_fallback = True
            break

    if not has_feature_fallback:
        f(300, "Resilience", "medium", "backend", 0,
          "No per-feature fallback detected — graceful degradation required (Law 300).",
          "Implement feature fallback:\n"
          "  1. Define fallback for each feature\n"
          "  2. Return cached/stale data on failure\n"
          "  3. Return partial results")

    # ── Law 301: Error budget ───────────────────────────────────
    has_error_budget = False
    for p in ALL_PY:
        content = read(p)
        if re.search(r'error.*budget|error_budget|SLO|SLA|availability.*target', content, re.IGNORECASE):
            has_error_budget = True
            break

    if not has_error_budget:
        f(301, "Resilience", "medium", "backend", 0,
          "No error budget tracking detected — SLO-based reliability required (Law 301).",
          "Implement error budget:\n"
          "  1. Define SLO: 99.9% availability\n"
          "  2. Track error budget consumption\n"
          "  3. Freeze releases when budget exhausted")

    # ── Law 302: On-call ────────────────────────────────────────
    has_oncall = False
    for p in ALL_PY:
        content = read(p)
        if re.search(r'on.*call|oncall|pagerduty|opsgenie|escalat', content, re.IGNORECASE):
            has_oncall = True
            break

    if not has_oncall:
        f(302, "Resilience", "medium", "backend", 0,
          "No on-call process detected — incident response requires on-call rotation (Law 302).",
          "Implement on-call:\n"
          "  1. Set up PagerDuty/Opsgenie\n"
          "  2. Define escalation policy\n"
          "  3. Weekly rotation")

    # ── Law 303: Runbooks ───────────────────────────────────────
    has_runbooks = False
    runbooks_dir = ROOT.parent / "docs" / "runbooks"
    if runbooks_dir.exists() and list(runbooks_dir.glob("*.md")):
        has_runbooks = True

    if not has_runbooks:
        f(303, "Resilience", "medium", "docs/runbooks/", 0,
          "No runbooks detected — operational runbooks required for incidents (Law 303).",
          "Create runbooks:\n"
          "  1. High CPU: scale up, check slow queries\n"
          "  2. DB down: failover to replica\n"
          "  3. Cache miss: warm cache")

    # ── Law 304: DR ─────────────────────────────────────────────
    has_dr = False
    for p in ALL_PY:
        content = read(p)
        if re.search(r'disaster.*recover|disaster_recovery|DR.*plan|failover.*plan|RTO|RPO', content, re.IGNORECASE):
            has_dr = True
            break

    if not has_dr:
        f(304, "Resilience", "high", "backend", 0,
          "No disaster recovery plan detected — DR required for business continuity (Law 304).",
          "Implement disaster recovery:\n"
          "  1. Define RTO (Recovery Time Objective)\n"
          "  2. Define RPO (Recovery Point Objective)\n"
          "  3. Test DR plan quarterly")

    # ── Law 305: DB failover ────────────────────────────────────
    has_db_failover = False
    for p in ALL_PY:
        content = read(p)
        if re.search(r'db.*failover|database.*failover|auto.*failover|patroni|repmgr', content, re.IGNORECASE):
            has_db_failover = True
            break

    if not has_db_failover:
        f(305, "Resilience", "high", "backend", 0,
          "No database failover detected — automatic failover required (Law 305).",
          "Implement DB failover:\n"
          "  1. Use Patroni or repmgr\n"
          "  2. Automatic failover < 30s\n"
          "  3. Test failover monthly")

    # ── Law 306: Multi-region ───────────────────────────────────
    has_multi_region = False
    for p in ALL_PY:
        content = read(p)
        if re.search(r'multi.*region|multi_region|region.*failover|cross.*region|active.*active', content, re.IGNORECASE):
            has_multi_region = True
            break

    if not has_multi_region:
        f(306, "Resilience", "medium", "backend", 0,
          "No multi-region deployment detected — multi-region required for DR (Law 306).",
          "Implement multi-region:\n"
          "  1. Deploy to 2+ regions\n"
          "  2. Use global load balancer\n"
          "  3. Replicate data across regions")

    # ── Law 307: Backup verify ──────────────────────────────────
    has_backup_verify = False
    for p in ALL_PY:
        content = read(p)
        if re.search(r'backup.*verify|verify.*backup|test.*restore|restore.*test', content, re.IGNORECASE):
            has_backup_verify = True
            break

    if not has_backup_verify:
        f(307, "Resilience", "high", "backend", 0,
          "No backup verification detected — backup restore testing required (Law 307).",
          "Implement backup verification:\n"
          "  1. Monthly restore test\n"
          "  2. Verify data integrity\n"
          "  3. Document restore procedure")

    # ── Law 308: Drift detection ────────────────────────────────
    has_drift = False
    for p in ALL_PY:
        content = read(p)
        if re.search(r'drift.*detect|detect.*drift|config.*drift|infrastructure.*drift', content, re.IGNORECASE):
            has_drift = True
            break

    if not has_drift:
        f(308, "Resilience", "low", "backend", 0,
          "No drift detection detected — infrastructure drift monitoring required (Law 308).",
          "Implement drift detection:\n"
          "  1. Compare actual vs desired state\n"
          "  2. Alert on configuration drift\n"
          "  3. Auto-remediate known drift")

    # ── Law 309: Dependency monitoring ──────────────────────────
    has_dep_monitor = False
    for p in ALL_PY:
        content = read(p)
        if re.search(r'dependabot|renovate|snyk.*monitor|dependency.*monitor', content, re.IGNORECASE):
            has_dep_monitor = True
            break

    if not has_dep_monitor:
        f(309, "Resilience", "low", "backend", 0,
          "No dependency monitoring detected — automated dependency updates required (Law 309).",
          "Implement dependency monitoring:\n"
          "  1. Enable Dependabot or Renovate\n"
          "  2. Auto-merge patch updates\n"
          "  3. Review minor/major updates weekly")

    # ── Law 310: Post-incident reviews ──────────────────────────
    has_postmortem = False
    for p in ALL_PY:
        content = read(p)
        if re.search(r'post.*mortem|postmortem|post.*incident|incident.*review|blameless', content, re.IGNORECASE):
            has_postmortem = True
            break

    if not has_postmortem:
        f(310, "Resilience", "medium", "backend", 0,
          "No post-incident review process detected — blameless postmortems required (Law 310).",
          "Implement post-incident reviews:\n"
          "  1. Conduct blameless postmortem for P1/P2\n"
          "  2. Document root cause and action items\n"
          "  3. Track action item completion")


# ══════════════════════════════════════════════════════════════
# SECTION: Operations (Laws 311-325)
# ══════════════════════════════════════════════════════════════

def _check_operations():
    """Laws 311-325: Operational excellence."""

    # ── Law 311: Feature flags ──────────────────────────────────
    has_feature_flags = False
    for p in ALL_PY:
        content = read(p)
        if re.search(r'feature.*flag|feature_flag|FeatureFlag|launchdarkly|flagsmith', content, re.IGNORECASE):
            has_feature_flags = True
            break

    if not has_feature_flags:
        f(311, "Operations", "high", "backend", 0,
          "No feature flags detected — gradual rollout requires feature flags (Law 311).",
          "Implement feature flags:\n"
          "  1. Use LaunchDarkly or Flagsmith\n"
          "  2. Gate new features behind flags\n"
          "  3. Enable gradual rollout (1% -> 10% -> 100%)")

    # ── Law 312: A/B testing ────────────────────────────────────
    has_ab_testing = False
    for p in ALL_PY:
        content = read(p)
        if re.search(r'a.b.*test|ab_test|experiment|variant.*test|split.*test', content, re.IGNORECASE):
            has_ab_testing = True
            break

    if not has_ab_testing:
        f(312, "Operations", "medium", "backend", 0,
          "No A/B testing detected — experimentation required for data-driven decisions (Law 312).",
          "Implement A/B testing:\n"
          "  1. Define experiment framework\n"
          "  2. Track conversion metrics\n"
          "  3. Statistical significance testing")

    # ── Law 313: Compliance ─────────────────────────────────────
    has_compliance = False
    for p in ALL_PY:
        content = read(p)
        if re.search(r'compliance|GDPR|CCPA|SOC.?2|ISO.?27001|PCI.?DSS', content, re.IGNORECASE):
            has_compliance = True
            break

    if not has_compliance:
        f(313, "Operations", "high", "backend", 0,
          "No compliance framework detected — regulatory compliance required (Law 313).",
          "Implement compliance:\n"
          "  1. GDPR: data deletion, consent management\n"
          "  2. PCI DSS: payment card security\n"
          "  3. SOC 2: security controls audit")

    # ── Law 314: IaC ────────────────────────────────────────────
    has_iac = False
    iac_files = list((ROOT.parent).glob("*.tf")) + list((ROOT.parent).glob("*.tfvars"))
    iac_files += list((ROOT.parent / "terraform").glob("*.tf")) if (ROOT.parent / "terraform").exists() else []
    if iac_files:
        has_iac = True

    for p in ALL_PY:
        content = read(p)
        if re.search(r'terraform|pulumi|cloudformation|ansible|infrastructure.*code', content, re.IGNORECASE):
            has_iac = True
            break

    if not has_iac:
        f(314, "Operations", "medium", "backend", 0,
          "No Infrastructure as Code detected — IaC required for reproducibility (Law 314).",
          "Implement IaC:\n"
          "  1. Use Terraform or Pulumi\n"
          "  2. Define all infrastructure in code\n"
          "  3. Version control infrastructure")

    # ── Law 315: Log aggregation ────────────────────────────────
    has_log_aggregation = False
    for p in ALL_PY:
        content = read(p)
        if re.search(r'elk|elasticsearch.*log|loki|splunk|datadog.*log|cloudwatch.*log|fluentd|filebeat', content, re.IGNORECASE):
            has_log_aggregation = True
            break

    if not has_log_aggregation:
        f(315, "Operations", "high", "backend", 0,
          "No log aggregation detected — centralized logging required (Law 315).",
          "Implement log aggregation:\n"
          "  1. Use ELK stack or Loki\n"
          "  2. Ship all service logs\n"
          "  3. Set retention policy (30 days hot, 1 year cold)")

    # ── Law 316: Dashboards ─────────────────────────────────────
    has_dashboards = False
    for p in ALL_PY:
        content = read(p)
        if re.search(r'grafana|dashboard|kibana|datadog.*dashboard|newrelic', content, re.IGNORECASE):
            has_dashboards = True
            break

    if not has_dashboards:
        f(316, "Operations", "medium", "backend", 0,
          "No monitoring dashboards detected — operational dashboards required (Law 316).",
          "Implement dashboards:\n"
          "  1. Create Grafana dashboards\n"
          "  2. Monitor key metrics: latency, errors, throughput\n"
          "  3. Set up team-specific views")

    # ── Law 317: Alerting tiers ─────────────────────────────────
    has_alerting = False
    for p in ALL_PY:
        content = read(p)
        if re.search(r'P1|P2|P3|severity.*critical|alert.*tier|page.*critical', content, re.IGNORECASE):
            has_alerting = True
            break

    if not has_alerting:
        f(317, "Operations", "medium", "backend", 0,
          "No alerting tiers detected — P1/P2/P3 classification required (Law 317).",
          "Implement alerting tiers:\n"
          "  P1: Service down -> page immediately\n"
          "  P2: Degraded -> page during business hours\n"
          "  P3: Warning -> ticket, next business day")

    # ── Law 318: Capacity planning ──────────────────────────────
    has_capacity = False
    docs_paths = [
        ROOT.parent / "docs" / "capacity",
        ROOT.parent / "docs" / "planning",
    ]
    for dp in docs_paths:
        if dp.exists():
            has_capacity = True
            break

    for p in ALL_PY:
        content = read(p)
        if re.search(r'capacity.*plan|growth.*project|resource.*forecast', content, re.IGNORECASE):
            has_capacity = True
            break

    if not has_capacity:
        f(318, "Operations", "low", "backend", 0,
          "No capacity planning detected — monthly capacity planning required (Law 318).",
          "Implement capacity planning:\n"
          "  1. Monthly resource utilization review\n"
          "  2. Project growth trends\n"
          "  3. Plan scaling actions")

    # ── Law 319: Release management ─────────────────────────────
    has_release_mgmt = False
    for p in ALL_PY:
        content = read(p)
        if re.search(r'canary|blue.*green|rolling.*deploy|deploy.*strategy', content, re.IGNORECASE):
            has_release_mgmt = True
            break

    if not has_release_mgmt:
        f(319, "Operations", "medium", "backend", 0,
          "No release management strategy detected — canary rollout required (Law 319).",
          "Implement release management:\n"
          "  1. Deploy to canary (5% traffic)\n"
          "  2. Monitor error rate and latency\n"
          "  3. Gradually increase to 100%")

    # ── Law 320: DevX ───────────────────────────────────────────
    has_devx = False
    setup_paths = [
        ROOT.parent / "Makefile",
        ROOT.parent / "docker-compose.yml",
        ROOT.parent / "CONTRIBUTING.md",
        ROOT.parent / "docs" / "setup.md",
    ]
    for sp in setup_paths:
        if sp.exists():
            has_devx = True
            break

    if not has_devx:
        f(320, "Operations", "low", "backend", 0,
          "No developer setup documentation detected — < 10min setup required (Law 320).",
          "Improve DevX:\n"
          "  1. Create one-command setup: 'make dev'\n"
          "  2. Use Docker Compose for dependencies\n"
          "  3. Document setup in CONTRIBUTING.md")

    # ── Law 321: Doc freshness ──────────────────────────────────
    has_doc_review = False
    docs_paths = [ROOT.parent / "docs"]
    for dp in docs_paths:
        if dp.exists():
            for p in safe_rglob(dp):
                if p.is_file():
                    content = read(p)
                    if re.search(r'review.*quarter|quarter.*review|doc.*fresh|last.*reviewed', content, re.IGNORECASE):
                        has_doc_review = True
                        break

    if not has_doc_review:
        f(321, "Operations", "low", "backend", 0,
          "No documentation review process detected — quarterly doc reviews required (Law 321).",
          "Implement doc reviews:\n"
          "  1. Add 'last_reviewed' date to docs\n"
          "  2. Schedule quarterly review\n"
          "  3. Track stale docs (> 90 days)")

    # ── Law 322: Cost allocation ────────────────────────────────
    has_cost_alloc = False
    for p in ALL_PY:
        content = read(p)
        if re.search(r'cost.*alloc|alloc.*cost|tag.*cost|cost.*center|team.*budget', content, re.IGNORECASE):
            has_cost_alloc = True
            break

    if not has_cost_alloc:
        f(322, "Operations", "low", "backend", 0,
          "No cost allocation detected — cost allocation by domain/team required (Law 322).",
          "Implement cost allocation:\n"
          "  1. Tag all resources with domain/team\n"
          "  2. Use cloud cost allocation tags\n"
          "  3. Generate monthly cost reports")

    # ── Law 323: Human access ───────────────────────────────────
    has_access_control = False
    for p in RBAC:
        content = read(p)
        if re.search(r'least.*privilege|offboarding|access.*revoke|deprovision', content, re.IGNORECASE):
            has_access_control = True
            break

    if not has_access_control:
        f(323, "Operations", "high", "backend", 0,
          "No access control process detected — least-privilege with 24h offboarding required (Law 323).",
          "Implement access control:\n"
          "  1. Define least-privilege roles in RBAC\n"
          "  2. Automate access provisioning/deprovisioning\n"
          "  3. Complete offboarding within 24h")

    # ── Law 324: Change management ──────────────────────────────
    has_change_mgmt = False
    ci_paths = [ROOT.parent / ".github" / "workflows"]
    for cp in ci_paths:
        if cp.exists():
            for p in safe_rglob(cp):
                if p.is_file():
                    content = read(p)
                    if re.search(r'require.*review|branch.*protect|PR.*required|pull_request', content, re.IGNORECASE):
                        has_change_mgmt = True
                        break

    if not has_change_mgmt:
        f(324, "Operations", "medium", "backend", 0,
          "No change management enforcement detected — all changes via PR + CI required (Law 324).",
          "Implement change management:\n"
          "  1. Require PR review before merge\n"
          "  2. Enforce CI pass before merge\n"
          "  3. Protect main branch")

    # ── Law 325: Sustainability ─────────────────────────────────
    has_sustainability = False
    for p in ALL_PY:
        content = read(p)
        if re.search(r'carbon|sustain|green.*computing|energy.*efficien|right.*size', content, re.IGNORECASE):
            has_sustainability = True
            break

    if not has_sustainability:
        f(325, "Operations", "low", "backend", 0,
          "No sustainability practices detected — right-sizing and carbon tracking required (Law 325).",
          "Implement sustainability:\n"
          "  1. Right-size instances based on actual usage\n"
          "  2. Track carbon footprint (cloud provider tools)\n"
          "  3. Use spot instances for batch workloads")


# ══════════════════════════════════════════════════════════════
# MAIN ENTRY POINT
# ══════════════════════════════════════════════════════════════

def run_checks():
    """Run all law checks for laws 201-325."""
    # Config (201-206)
    _check_config()

    # Testing (207-214)
    _check_testing()

    # Deployment (215-220)
    _check_deployment()

    # Performance (221-226)
    _check_performance()

    # Data (227-232)
    _check_data()

    # API (233-239)
    _check_api()

    # Git (240-244)
    _check_git()

    # Documentation (245-250)
    _check_docs()

    # Scalability (251-270)
    _check_scalability()

    # Security Hardening (271-295)
    _check_security_hardening()

    # Resilience (296-310)
    _check_resilience()

    # Operations (311-325)
    _check_operations()
