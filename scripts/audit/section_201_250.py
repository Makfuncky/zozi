"""
ZOZI Audit — Laws 201-250: Config, Testing, Deployment, Performance, Data, API, Git, Docs.

Each function uses the global helpers (f, read, rel, read_lines, parse_ast, etc.)
and the pre-indexed file lists (ALL_PY, DOMAINS, MODELS, ROUTERS, PROVIDERS,
SERVICES, MIDDLEWARE_FILES, INFRA, JOBS, TESTS, KERNEL, RBAC, SCRIPTS).
"""
import re
from pathlib import Path

# ══════════════════════════════════════════════════════════════
# SECTION: Config (Laws 201-266)
# ══════════════════════════════════════════════════════════════


def check_section_config_2():
    """Laws 201-206: Configuration management."""

    # ── Law 201: Env hierarchy ──────────────────────────────────
    # .env.example → .env → backend/.env → frontend/.env.local
    project_root = ROOT.parent
    env_example_root = project_root / ".env.example"
    env_root = project_root / ".env"
    env_backend = ROOT / ".env"
    env_backend_example = ROOT / ".env.example"
    env_frontend = project_root / "frontend" / "web_app" / ".env.local"
    env_frontend_example = project_root / "frontend" / "web_app" / ".env.example"

    if not env_example_root.exists() and not env_backend_example.exists():
        f(201, "config", "high", ".env.example",
          0, "No .env.example found at project root or backend/",
          "Create .env.example with all required vars. Hierarchy: .env.example → .env → backend/.env → frontend/.env.local")

    if env_root.exists() and env_example_root.exists():
        example_content = read(env_example_root)
        root_content = read(env_root)
        example_vars = set(re.findall(r'^([A-Z_]+)=', example_content, re.MULTILINE))
        root_vars = set(re.findall(r'^([A-Z_]+)=', root_content, re.MULTILINE))
        missing_in_root = example_vars - root_vars
        if missing_in_root:
            f(201, "config", "medium", ".env", 0,
              f"Root .env missing vars present in .env.example: {', '.join(sorted(missing_in_root)[:5])}",
              "Ensure .env includes all variables from .env.example")

    if not env_frontend.exists() and not env_frontend_example.exists():
        f(201, "config", "medium", "frontend/web_app/.env.local",
          0, "No .env.local or .env.example found in frontend/web_app/",
          "Create frontend/web_app/.env.local with NEXT_PUBLIC_* vars")

    # ── Law 202: Required vars ──────────────────────────────────
    required_vars = ["SECRET_KEY", "DATABASE_URL", "REDIS_URL"]
    config_file = ROOT / "infrastructure" / "utils" / "config.py"

    if config_file.exists():
        config_content = read(config_file)
        for var in required_vars:
            # Check that the var is referenced in config
            if var not in config_content and var.upper() not in config_content:
                f(202, "config", "high", rel(config_file), 0,
                  f"Required env var {var} not referenced in config",
                  f"Add {var} to Settings class with os.getenv('{var}')")
    else:
        f(202, "config", "critical", "infrastructure/utils/config.py",
          0, "Config file not found — required vars cannot be verified",
          "Create infrastructure/utils/config.py with SECRET_KEY, DATABASE_URL, REDIS_URL")

    # Also check .env.example has required vars
    if env_example_root.exists():
        example_content = read(env_example_root)
        for var in required_vars:
            if var not in example_content:
                f(202, "config", "high", ".env.example", 0,
                  f"Required var {var} missing from .env.example",
                  f"Add {var}=<value> to .env.example")

    # ── Law 203: Typed flags — pydantic-settings, no raw os.getenv ──
    # The project uses a custom Settings class, not pydantic-settings.
    # Check for raw os.getenv() outside of config files.
    config_files = list((ROOT / "infrastructure" / "utils").glob("*.py")) if (ROOT / "infrastructure" / "utils").exists() else []
    config_file_names = {str(p) for p in config_files}

    for p in ALL_PY:
        if str(p) in config_file_names:
            continue
        if "config.py" in str(p):
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
                # Allow if it's just reading a feature flag or simple value
                if not re.search(r'os\.getenv\s*\(\s*["\'][A-Z_]+["\']', stripped):
                    continue
                f(203, "config", "medium", rel(p), i,
                  f"Raw os.getenv() found outside config layer: {stripped.strip()}",
                  "Move env access to infrastructure/utils/config.py Settings class")

    # ── Law 204: Secrets manager ────────────────────────────────
    has_secrets_manager = False
    for p in ALL_PY:
        content = read(p)
        if not content:
            continue
        if any(kw in content for kw in ["aws_secretsmanager", "boto3.client('secretsmanager')",
                                          "boto3.client(\"secretsmanager\")", "hashicorp.vault",
                                          "hvac", "SecretsManager", "vault_client"]):
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
            # Check for wildcard in production config
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


def check_section_testing_2():
    """Laws 207-214: Testing infrastructure."""

    # ── Law 207: pytest framework ───────────────────────────────
    has_pytest = False
    has_pytest_asyncio = False

    # Check requirements/pyproject for pytest
    req_files = list(ROOT.parent.glob("requirements*.txt")) + list(ROOT.glob("requirements*.txt"))
    for rf in req_files:
        content = read(rf)
        if "pytest" in content:
            has_pytest = True
        if "pytest-asyncio" in content:
            has_pytest_asyncio = True

    # Check conftest.py for pytest usage
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
        if 'CSRF_DISABLED' in content or 'rate_limit' in content.lower():
            # Check for disabling in test
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
            f(212, "testing", "high", "tests/architecture/", 0,
              "test_feature_catalog.py not found — feature catalog not tested",
              "Create tests/architecture/test_feature_catalog.py")
    else:
        f(212, "testing", "high", "tests/architecture/", 0,
          "tests/architecture/ directory not found",
          "Create tests/architecture/ with test_import_laws.py and test_feature_catalog.py")

    # ── Law 213: Coverage ───────────────────────────────────────
    # Check for per-domain smoke tests
    domains_dir = ROOT / "tests" / "domains"
    if domains_dir.exists():
        domain_test_files = list(domains_dir.glob("test_*.py"))
        tested_domains = {f.name.replace("test_", "").replace(".py", "") for f in domain_test_files}
        all_domains = set(DOMAINS.keys())
        untested = all_domains - tested_domains
        if untested:
            f(213, "testing", "medium", "tests/domains/", 0,
              f"Domains without smoke tests: {', '.join(sorted(untested)[:5])}",
              f"Add test_<domain>.py for each domain in tests/domains/")
    else:
        f(213, "testing", "medium", "tests/domains/", 0,
          "tests/domains/ directory not found — no per-domain smoke tests",
          "Create tests/domains/ with test_<domain>.py for each domain")

    # ── Law 214: Isolation ──────────────────────────────────────
    if conftest.exists():
        content = read(conftest)
        has_rollback = "rollback" in content.lower()
        has_transaction = "transaction" in content.lower()
        has_noleak = "leak" in content.lower() or "isolation" in content.lower()

        if not (has_rollback and has_transaction):
            f(214, "testing", "high", "tests/conftest.py", 0,
              "Test isolation via transaction rollback not clearly implemented",
              "Implement transaction-rollback isolation:\n"
              "  connection = engine.connect()\n"
              "  transaction = connection.begin()\n"
              "  # yield session\n"
              "  transaction.rollback()\n"
              "  connection.close()")
    else:
        f(214, "testing", "critical", "tests/conftest.py", 0,
          "conftest.py not found — test isolation cannot be verified",
          "Create tests/conftest.py with transaction-rollback isolation")


# ══════════════════════════════════════════════════════════════
# SECTION: Deployment (Laws 215-220)
# ══════════════════════════════════════════════════════════════


def check_section_deployment():
    """Laws 215-220: Deployment configuration."""

    project_root = ROOT.parent

    # ── Law 215: Docker Compose ─────────────────────────────────
    docker_compose = project_root / "docker-compose.yml"
    if docker_compose.exists():
        content = read(docker_compose)
        required_services = ["db", "redis", "backend", "frontend"]
        for svc in required_services:
            if f"  {svc}:" not in content and f"{svc}:" not in content:
                f(215, "deployment", "high", "docker-compose.yml", 0,
                  f"Required service '{svc}' not found in docker-compose.yml",
                  f"Add {svc} service to docker-compose.yml")

        # Check for Celery workers
        if "celery" not in content.lower():
            f(215, "deployment", "medium", "docker-compose.yml", 0,
              "No Celery workers defined in docker-compose.yml",
              "Add celery-worker and celery-beat services for async processing")
    else:
        f(215, "deployment", "critical", "docker-compose.yml", 0,
          "docker-compose.yml not found",
          "Create docker-compose.yml with db, redis, backend, frontend, celery-worker services")

    # ── Law 216: Production targets ─────────────────────────────
    # Check for deployment configuration files
    deploy_configs = list(project_root.glob("railway.toml")) + \
                     list(project_root.glob("railway.json")) + \
                     list(project_root.glob("vercel.json")) + \
                     list(project_root.glob(".railway")) + \
                     list((project_root / "backend").glob("railway.toml")) + \
                     list((project_root / "backend").glob("Dockerfile"))

    has_backend_deploy = any("railway" in str(p).lower() or "Dockerfile" in str(p) for p in deploy_configs)
    has_frontend_deploy = any("vercel" in str(p).lower() for p in deploy_configs)

    if not has_backend_deploy:
        f(216, "deployment", "medium", "backend/Dockerfile", 0,
          "No Railway deployment config found for backend",
          "Add railway.toml or configure Railway deployment for backend")

    if not has_frontend_deploy:
        f(216, "deployment", "medium", "frontend/web_app/vercel.json", 0,
          "No Vercel deployment config found for frontend",
          "Add vercel.json or configure Vercel deployment for frontend")

    # ── Law 217: Migration on deploy ────────────────────────────
    deploy_scripts = list(project_root.glob("scripts/deploy*")) + \
                     list(project_root.glob("scripts/*.sh")) + \
                     list((project_root / "backend" / "scripts").glob("*.sh")) if (project_root / "backend" / "scripts").exists() else []

    migration_in_deploy = False
    for script in deploy_scripts:
        content = read(script)
        if "alembic" in content and "upgrade" in content:
            migration_in_deploy = True
            break

    # Also check Dockerfile for migration command
    for df in [project_root / "backend" / "Dockerfile", project_root / "Dockerfile"]:
        if df.exists():
            content = read(df)
            if "alembic" in content and "upgrade" in content:
                migration_in_deploy = True
                break

    if not migration_in_deploy:
        f(217, "deployment", "high", "scripts/deploy.sh", 0,
          "No alembic upgrade head in deploy scripts",
          "Add 'alembic upgrade head' to deploy script or Dockerfile CMD")

    # ── Law 218: Health checks ──────────────────────────────────
    health_endpoints = []
    for p in ALL_PY:
        content = read(p)
        if not content:
            continue
        if re.search(r'@(?:app|router)\.(?:get|post)\s*\(\s*["\']/?health', content):
            health_endpoints.append(p)

    if not health_endpoints:
        f(218, "deployment", "high", "modules/", 0,
          "No /health endpoint found",
          "Add health endpoints:\n"
          "  @app.get('/health')\n"
          "  @app.get('/health/deps')\n"
          "  @app.get('/health/ready')")

    # ── Law 219: Rollback ───────────────────────────────────────
    rollback_found = False
    for p in ALL_PY:
        content = read(p)
        if not content:
            continue
        if "rollback" in content.lower() and ("deploy" in content.lower() or "migration" in content.lower()):
            rollback_found = True
            break

    # Check for down migration support
    alembic_dir = ROOT / "alembic" / "versions"
    if alembic_dir.exists():
        down_migrations = 0
        for mig in alembic_dir.glob("*.py"):
            content = read(mig)
            if "def downgrade" in content and "pass" not in content.split("def downgrade")[1].split("\n")[1] if "def downgrade" in content else True:
                down_migrations += 1
        if down_migrations == 0 and len(list(alembic_dir.glob("*.py"))) > 0:
            f(219, "deployment", "high", "alembic/versions/", 0,
              "No downgrade() functions found in migrations — rollback not supported",
              "Implement downgrade() in all Alembic migrations")

    if not rollback_found and not alembic_dir.exists():
        f(219, "deployment", "medium", "scripts/deploy.sh", 0,
          "No rollback mechanism found in deploy scripts",
          "Add rollback support: alembic downgrade -1, or blue-green deployment")

    # ── Law 220: Env promotion ──────────────────────────────────
    env_promotion = False
    for p in ALL_PY:
        content = read(p)
        if not content:
            continue
        envs = re.findall(r'(development|staging|production|test)', content.lower())
        if len(set(envs)) >= 3:
            env_promotion = True
            break

    if not env_promotion:
        f(220, "deployment", "medium", "infrastructure/utils/config.py", 0,
          "Environment promotion chain (dev → staging → prod) not clearly defined",
          "Define APP_ENV values: development, test, staging, production with promotion gates")


# ══════════════════════════════════════════════════════════════
# SECTION: Performance (Laws 221-226)
# ══════════════════════════════════════════════════════════════


def check_section_performance():
    """Laws 221-226: Performance optimization."""

    # ── Law 221: Caching strategy ───────────────────────────────
    redis_cache_found = False
    for p in ALL_PY:
        content = read(p)
        if not content:
            continue
        if "redis" in content.lower() and ("cache" in content.lower() or "ttl" in content.lower()):
            redis_cache_found = True
            break

    if not redis_cache_found:
        f(221, "performance", "high", "infrastructure/", 0,
          "No Redis caching with TTL pattern found",
          "Implement Redis caching:\n"
          "  redis.setex(f'cache:{key}', 3600, value)\n"
          "  # Event-driven invalidation on writes")

    # ── Law 222: Keyset pagination ──────────────────────────────
    offset_found = False
    keyset_found = False
    for p in ALL_PY:
        content = read(p)
        if not content:
            continue
        if re.search(r'\boffset\s*=', content, re.IGNORECASE) or re.search(r'\.offset\s*\(', content):
            offset_found = True
        if "cursor" in content.lower() or "keyset" in content.lower() or "cursor_paginate" in content:
            keyset_found = True

    if offset_found and not keyset_found:
        f(222, "performance", "high", "domains/", 0,
          "OFFSET-based pagination found — OFFSET is forbidden for large datasets",
          "Replace OFFSET with keyset pagination:\n"
          "  WHERE id > :cursor ORDER BY id LIMIT 50")

    # ── Law 223: Connection pooling ─────────────────────────────
    pool_config_found = False
    for p in ALL_PY:
        content = read(p)
        if not content:
            continue
        if "pool_size" in content and "max_overflow" in content:
            pool_config_found = True
            # Check values
            pool_match = re.search(r'pool_size\s*[=:]\s*(\d+)', content)
            overflow_match = re.search(r'max_overflow\s*[=:]\s*(\d+)', content)
            if pool_match and int(pool_match.group(1)) < 10:
                f(223, "performance", "high", rel(p), 0,
                  f"pool_size={pool_match.group(1)} is below minimum of 10",
                  "Set pool_size >= 10 for production workloads")
            if overflow_match and int(overflow_match.group(1)) < 20:
                f(223, "performance", "high", rel(p), 0,
                  f"max_overflow={overflow_match.group(1)} is below minimum of 20",
                  "Set max_overflow >= 20 for production workloads")

    if not pool_config_found:
        f(223, "performance", "high", "infrastructure/database/", 0,
          "Connection pooling not configured (pool_size >= 10, max_overflow >= 20)",
          "Configure SQLAlchemy engine with:\n"
          "  create_engine(url, pool_size=20, max_overflow=40, pool_recycle=1800)")

    # ── Law 224: Query optimization ─────────────────────────────
    # Check for N+1 patterns (loops with queries)
    for p in ALL_PY:
        content = read(p)
        if not content:
            continue
        tree = parse_ast(p)
        if not tree:
            continue
        # Look for loops that contain database queries
        for node in ast.walk(tree):
            if isinstance(node, (ast.For, ast.While)):
                # Check if loop body contains session.query or similar
                loop_source = get_source_segment(content, node)
                if loop_source and any(q in loop_source for q in ["session.query", ".query(", "db.query"]):
                    f(224, "performance", "medium", rel(p), node.lineno,
                      "Potential N+1 query pattern: database query inside loop",
                      "Use eager loading (selectinload, joinedload) or batch queries")

    # ── Law 225: CDN ────────────────────────────────────────────
    cdn_found = False
    for p in ALL_PY:
        content = read(p)
        if not content:
            continue
        if any(kw in content for kw in ["cdn", "CDN", "cloudfront", "cloudflare", "s3_cdn"]):
            cdn_found = True
            break

    if not cdn_found:
        f(225, "performance", "medium", "infrastructure/utils/config.py", 0,
          "No CDN configuration found for static assets/images",
          "Add CDN base URL config (e.g., S3_CDN_BASE) and serve static assets via CDN")

    # ── Law 226: Async processing ───────────────────────────────
    celery_found = False
    for p in ALL_PY:
        content = read(p)
        if not content:
            continue
        if "celery" in content.lower() or "delay(" in content or "apply_async" in content:
            celery_found = True
            break

    if not celery_found:
        f(226, "performance", "high", "jobs/", 0,
          "No Celery async task processing found",
          "Implement Celery for CPU-bound work:\n"
          "  @celery_app.task\n"
          "  def process_image(image_id):\n"
          "      ...")


# ══════════════════════════════════════════════════════════════
# SECTION: Data (Laws 227-232)
# ══════════════════════════════════════════════════════════════


def check_section_data():
    """Laws 227-232: Data management."""

    # ── Law 227: RLS enforcement ────────────────────────────────
    rls_found = False
    for p in ALL_PY:
        content = read(p)
        if not content:
            continue
        if "set_rls_context" in content or "rls_context" in content or "country_code" in content:
            rls_found = True
            break

    if not rls_found:
        f(227, "data", "critical", "infrastructure/database/", 0,
          "No RLS (Row Level Security) enforcement found",
          "Implement set_rls_context() to set country_code per request:\n"
          "  def set_rls_context(session, country_code):\n"
          "      session.execute(text(f'SET app.country = :cc'), {'cc': country_code})")

    # ── Law 228: Soft delete ────────────────────────────────────
    soft_delete_found = False
    for p in MODELS:
        content = read(p)
        if not content:
            continue
        if "is_deleted" in content or "deleted_at" in content:
            soft_delete_found = True
            break

    if not soft_delete_found:
        f(228, "data", "high", "domains/", 0,
          "No soft delete pattern (is_deleted/deleted_at) found in models",
          "Add is_deleted = Column(Boolean, default=False) to models requiring soft delete")

    # ── Law 229: Audit columns ──────────────────────────────────
    audit_columns_found = False
    timestamp_mixin = False
    for p in ALL_PY:
        content = read(p)
        if not content:
            continue
        if "TimestampMixin" in content or "timestamp_mixin" in content:
            timestamp_mixin = True
        if "created_at" in content and "updated_at" in content:
            audit_columns_found = True

    if not audit_columns_found:
        f(229, "data", "high", "domains/", 0,
          "Audit columns (created_at/updated_at) not found in models",
          "Add TimestampMixin or created_at/updated_at columns to all domain models")

    if not timestamp_mixin:
        f(229, "data", "medium", "infrastructure/database/", 0,
          "No TimestampMixin class found for consistent audit columns",
          "Create TimestampMixin with created_at/updated_at Column(DateTime)")

    # ── Law 230: Audit trail ────────────────────────────────────
    audit_trail_found = False
    for p in ALL_PY:
        content = read(p)
        if not content:
            continue
        if "audit_log" in content.lower() or "audit_trail" in content.lower():
            audit_trail_found = True
            break

    if not audit_trail_found:
        f(230, "data", "high", "domains/audit/", 0,
          "No audit trail (WORM log) implementation found",
          "Implement audit trail with actor, action, entity, timestamp:\n"
          "  class AuditLog(Base):\n"
          "      actor_id, action, entity_type, entity_id, timestamp")

    # ── Law 231: Data residency ─────────────────────────────────
    residency_found = False
    for p in ALL_PY:
        content = read(p)
        if not content:
            continue
        if "country_code" in content and ("shard" in content.lower() or "residen" in content.lower()):
            residency_found = True
            break

    if not residency_found:
        f(231, "data", "medium", "infrastructure/database/", 0,
          "Data residency sharding by country_code not implemented",
          "Consider sharding by country_code for data residency compliance")

    # ── Law 232: Backup & recovery ──────────────────────────────
    backup_found = False
    for p in ALL_PY:
        content = read(p)
        if not content:
            continue
        if "backup" in content.lower():
            backup_found = True
            break

    if not backup_found:
        f(232, "data", "high", "infrastructure/", 0,
          "No backup & recovery mechanism found",
          "Implement daily backups with tested recovery:\n"
          "  - pg_dump for PostgreSQL\n"
          "  - Redis BGSAVE\n"
          "  - Test recovery monthly")


# ══════════════════════════════════════════════════════════════
# SECTION: API (Laws 233-239)
# ══════════════════════════════════════════════════════════════


def check_section_api():
    """Laws 233-239: API design and conventions."""

    # ── Law 233: REST conventions ───────────────────────────────
    rest_violations = []
    for p in ROUTERS:
        content = read(p)
        if not content:
            continue
        # Check for non-RESTful patterns
        if re.search(r'@router\.(post|put|delete)\s*\(\s*["\'].*list', content):
            rest_violations.append((p, "POST/PUT/DELETE on list endpoint"))

    for p, violation in rest_violations:
        f(233, "api", "medium", rel(p), 0,
          f"REST convention violation: {violation}",
          "Use GET for list/detail, POST for create, PUT for update, DELETE for delete")

    # ── Law 234: Versioning ─────────────────────────────────────
    versioning_found = False
    for p in ROUTERS:
        content = read(p)
        if not content:
            continue
        if "/api/v1" in content or "/v1/" in content:
            versioning_found = True
            break

    # Also check main.py for version prefix
    main_py = ROOT / "main.py"
    if main_py.exists():
        content = read(main_py)
        if "/api/v1" in content or "/v1/" in content or "api_version" in content:
            versioning_found = True

    if not versioning_found:
        f(234, "api", "high", "modules/", 0,
          "API versioning not found — no /api/v1/ prefix",
          "Add URL prefix /api/v1/ to all router includes:\n"
          "  app.include_router(router, prefix='/api/v1/admin')")

    # ── Law 235: JSON format ────────────────────────────────────
    json_validation_found = False
    for p in ALL_PY:
        content = read(p)
        if not content:
            continue
        if "response_model" in content or "BaseModel" in content:
            json_validation_found = True
            break

    if not json_validation_found:
        f(235, "api", "high", "modules/", 0,
          "No Pydantic response_model validation found in routers",
          "Add response_model parameter to all endpoints for JSON validation")

    # ── Law 236: RFC 7807 errors ────────────────────────────────
    rfc7807_found = False
    for p in ALL_PY:
        content = read(p)
        if not content:
            continue
        if "problem" in content.lower() or "rfc7807" in content.lower() or "application/problem+json" in content:
            rfc7807_found = True
            break

    if not rfc7807_found:
        f(236, "api", "medium", "middleware/", 0,
          "RFC 7807 Problem Details error format not implemented",
          "Implement RFC 7807 error responses:\n"
          "  {\"type\": \"...\", \"title\": \"...\", \"status\": 400, \"detail\": \"...\"}")

    # ── Law 237: Pagination format ──────────────────────────────
    pagination_format_found = False
    for p in ALL_PY:
        content = read(p)
        if not content:
            continue
        if "next_cursor" in content or "has_more" in content:
            pagination_format_found = True
            break

    if not pagination_format_found:
        f(237, "api", "medium", "domains/", 0,
          "Standard pagination format (items + next_cursor + has_more) not found",
          "Return paginated responses as: {\"items\": [...], \"next_cursor\": \"...\", \"has_more\": true}")

    # ── Law 238: Filtering/sorting ──────────────────────────────
    filtering_found = False
    for p in ALL_PY:
        content = read(p)
        if not content:
            continue
        if "filter[" in content or "sort=" in content or "sort_by" in content:
            filtering_found = True
            break

    if not filtering_found:
        f(238, "api", "low", "modules/", 0,
          "No query parameter filtering/sorting pattern found",
          "Support filter[field]=value and sort=-created_at query parameters")

    # ── Law 239: Idempotency ────────────────────────────────────
    idempotency_found = False
    for p in ALL_PY:
        content = read(p)
        if not content:
            continue
        if "idempoten" in content.lower():
            idempotency_found = True
            break

    if not idempotency_found:
        f(239, "api", "medium", "middleware/", 0,
          "Idempotency-Key header support not found",
          "Add Idempotency-Key header handling for POST/PUT endpoints")


# ══════════════════════════════════════════════════════════════
# SECTION: Git (Laws 240-244)
# ══════════════════════════════════════════════════════════════


def check_section_git():
    """Laws 240-244: Git workflow and hooks."""

    project_root = ROOT.parent

    # ── Law 240: Branching ──────────────────────────────────────
    git_dir = project_root / ".git"
    if git_dir.exists():
        # Check for branch naming patterns in CI/workflow files
        github_dir = project_root / ".github"
        if github_dir.exists():
            workflow_files = safe_rglob(github_dir, "*.yml") + safe_rglob(github_dir, "*.yaml")
            if not workflow_files:
                f(240, "git", "medium", ".github/", 0,
                  "No GitHub workflow files found — branch protection not enforced",
                  "Add .github/workflows/ci.yml with branch protection rules")
    else:
        f(240, "git", "low", ".git", 0,
          "No .git directory found — not a git repository",
          "Initialize git repository: git init")

    # ── Law 241: Conventional Commits ───────────────────────────
    commitlint_found = False
    for f_path in [project_root / ".commitlintrc", project_root / ".commitlintrc.json",
                   project_root / "commitlint.config.js", project_root / ".commitlintrc.yml"]:
        if f_path.exists():
            commitlint_found = True
            break

    # Check if there's a commit message validation in CI
    github_dir = project_root / ".github"
    if github_dir.exists():
        for wf in safe_rglob(github_dir, "*.yml"):
            content = read(wf)
            if "commit" in content.lower() and ("lint" in content.lower() or "conventional" in content.lower()):
                commitlint_found = True
                break

    if not commitlint_found:
        f(241, "git", "low", ".commitlintrc", 0,
          "No conventional commits enforcement found",
          "Add .commitlintrc.json to enforce type(scope): description format")

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
        # Check for .pre-commit-config.yaml
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
    # Check if .kilo/agent-manager.json exists (Agent Manager worktree config)
    agent_manager = project_root / ".kilo" / "agent-manager.json"
    if not agent_manager.exists():
        f(244, "git", "low", ".kilo/agent-manager.json", 0,
          "No Agent Manager worktree configuration found",
          "Agent Manager uses worktrees for parallel development sessions")


# ══════════════════════════════════════════════════════════════
# SECTION: Documentation (Laws 245-250)
# ══════════════════════════════════════════════════════════════


def check_section_docs():
    """Laws 245-250: Documentation standards."""

    project_root = ROOT.parent

    # ── Law 245: Architecture docs ──────────────────────────────
    arch_doc = project_root / "ARCHITECTURE_DIAGRAM.md"
    if arch_doc.exists():
        content = read(arch_doc)
        if len(content.strip()) < 100:
            f(245, "docs", "high", "ARCHITECTURE_DIAGRAM.md", 0,
              "ARCHITECTURE_DIAGRAM.md is nearly empty — should be authoritative",
              "Document the three-axis architecture: modules → domains → infrastructure")
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
    # FastAPI auto-generates at /docs and /redoc
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
    # Check for docstrings in service files
    docstring_count = 0
    total_functions = 0
    for p in SERVICES:
        content = read(p)
        if not content:
            continue
        tree = parse_ast(p)
        if not tree:
            continue
        funcs = get_functions(tree)
        total_functions += len(funcs)
        for func in funcs:
            if (func.body and isinstance(func.body[0], ast.Expr) and
                    isinstance(func.body[0].value, (ast.Constant, ast.Str))):
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
