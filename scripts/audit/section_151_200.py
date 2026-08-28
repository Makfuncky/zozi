#!/usr/bin/env python3
"""
ZOZI Audit Section 151-200: Domain Laws (remaining), RBAC, Frontend, Web App, Mobile, Shared.

Each function checks a group of related laws using the global helpers
(f, read, rel, read_lines, parse_ast, etc.) defined in full_system_audit.py.
"""

import json
import re
from pathlib import Path

# ══════════════════════════════════════════════════════════════
# LAWS 150-160: DOMAIN LAWS (REMAINING)
# ══════════════════════════════════════════════════════════════

def check_section_domain_laws():
    """Laws 150-160: Domain Laws (remaining)."""

    # ── Law 151: Service patterns ──────────────────────────────
    # Services take primitives, own DB access and transactions.
    _check_service_patterns()

    # ── Law 152: Model patterns ────────────────────────────────
    # __tablename__ + __table_args__ = {schema: <domain>}.
    _check_model_patterns()

    # ── Law 153: Schema patterns ───────────────────────────────
    # Pydantic models for validation.
    _check_schema_patterns()

    # ── Law 154: Event patterns ────────────────────────────────
    # Named {domain}.{entity}.{action}. Minimal data.
    _check_event_patterns()

    # ── Law 155: Port patterns ─────────────────────────────────
    # Sanctioned cross-domain READ path.
    _check_port_patterns()

    # ── Law 156: Subscriber patterns ───────────────────────────
    # Handle events from other domains.
    _check_subscriber_patterns()

    # ── Law 157: Feature patterns ──────────────────────────────
    # FEATURES = {key: description}.
    _check_feature_patterns()

    # ── Law 158: Read model patterns ───────────────────────────
    # CQRS-lite projections.
    _check_read_model_patterns()

    # ── Law 159: Policy patterns ───────────────────────────────
    # Authorization policies.
    _check_policy_patterns()

    # ── Law 160: 15 domains fixed ──────────────────────────────
    # New domains require architecture review.
    _check_domain_count()


def _check_service_patterns():
    """Law 151: Services take primitives, own DB access and transactions."""
    for svc_file in SERVICES:
        content = read(svc_file)
        if not content:
            continue
        tree = parse_ast(svc_file)
        if not tree:
            continue

        classes = get_classes(tree)
        for cls in classes:
            cls_name = cls.name
            if not cls_name.endswith("Service"):
                continue
            # Check that service classes have session/DB parameter in __init__
            init_method = None
            for item in cls.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)) and item.name == "__init__":
                    init_method = item
                    break
            if init_method:
                args = [a.arg for a in init_method.args.args]
                has_db = any(a in args for a in ("db", "session", "db_session"))
                if not has_db and len(args) > 1:
                    # Service with args but no db session — flag
                    f(151, "domain", "medium", rel(svc_file), init_method.lineno,
                      f"Service '{cls_name}' __init__ lacks db/session parameter",
                      "Add 'db: Session' as first parameter to own DB access and transactions")


def _check_model_patterns():
    """Law 152: __tablename__ + __table_args__ = {schema: <domain>}."""
    for model_file in MODELS:
        content = read(model_file)
        if not content:
            continue
        tree = parse_ast(model_file)
        if not tree:
            continue

        classes = get_classes(tree)
        for cls in classes:
            has_tablename = False
            has_schema = False
            for item in cls.body:
                if isinstance(item, ast.Assign):
                    for target in item.targets:
                        if isinstance(target, ast.Name):
                            if target.id == "__tablename__":
                                has_tablename = True
                            elif target.id == "__table_args__":
                                # Check if schema is present in table args
                                if _node_contains_schema(item.value):
                                    has_schema = True
            if has_tablename and not has_schema:
                f(152, "domain", "high", rel(model_file), cls.lineno,
                  f"Model '{cls.name}' has __tablename__ but __table_args__ missing schema declaration",
                  'Add __table_args__ = ({"schema": "<domain>"},) to assign model to correct Postgres schema')


def _node_contains_schema(node):
    """Check if an AST node contains a schema dictionary entry."""
    try:
        source = ast.dump(node)
        return "schema" in source
    except:
        return False


def _check_schema_patterns():
    """Law 153: Pydantic models for validation."""
    schema_files = []
    for domain_name, files in DOMAINS.items():
        for p in files:
            if "/schemas/" in str(p):
                schema_files.append(p)

    if not schema_files:
        f(153, "domain", "medium", "domains/", 0,
          "No schema directories found in any domain",
          "Create schemas/ directories with Pydantic models for input validation in each domain")
        return

    # Check that schema files use Pydantic
    for schema_file in schema_files:
        content = read(schema_file)
        if not content:
            continue
        if "BaseModel" not in content and "pydantic" not in content.lower():
            f(153, "domain", "low", rel(schema_file), 1,
              f"Schema file does not appear to use Pydantic BaseModel",
              "Use pydantic.BaseModel for all schema definitions")


def _check_event_patterns():
    """Law 154: Events named {domain}.{entity}.{action}. Minimal data."""
    for domain_name, files in DOMAINS.items():
        for p in files:
            if p.name == "events.py":
                content = read(p)
                if not content:
                    continue
                tree = parse_ast(p)
                if not tree:
                    continue
                # Look for event class definitions or event name strings
                classes = get_classes(tree)
                for cls in classes:
                    if "Event" in cls.name or "event" in cls.name.lower():
                        # Check naming convention
                        if not re.match(r'^[A-Z][a-zA-Z]+Event$', cls.name):
                            f(154, "domain", "low", rel(p), cls.lineno,
                              f"Event class '{cls.name}' does not follow DomainEntityEvent naming",
                              "Name events as {Domain}{Entity}{Action}Event (e.g., CatalogProductCreatedEvent)")


def _check_port_patterns():
    """Law 155: Port functions are sanctioned cross-domain READ path."""
    for domain_name, files in DOMAINS.items():
        for p in files:
            if p.name == "ports.py":
                content = read(p)
                if not content:
                    continue
                tree = parse_ast(p)
                if not tree:
                    continue
                funcs = get_functions(tree)
                for func in funcs:
                    if func.name.startswith("_"):
                        continue
                    # Port functions should have type annotations
                    if func.returns is None and not func.name.startswith("_"):
                        f(155, "domain", "low", rel(p), func.lineno,
                          f"Port function '{func.name}' lacks return type annotation",
                          "Add return type annotations to all port functions for cross-domain clarity")


def _check_subscriber_patterns():
    """Law 156: Subscribers handle events from other domains."""
    for domain_name, files in DOMAINS.items():
        for p in files:
            if p.name == "subscribers.py":
                content = read(p)
                if not content:
                    continue
                tree = parse_ast(p)
                if not tree:
                    continue
                funcs = get_functions(tree)
                for func in funcs:
                    if func.name.startswith("_"):
                        continue
                    # Subscriber functions should accept event parameter
                    args = [a.arg for a in func.args.args]
                    if "event" not in args and "message" not in args:
                        f(156, "domain", "low", rel(p), func.lineno,
                          f"Subscriber '{func.name}' does not accept event/message parameter",
                          "Subscriber functions should accept an event or message parameter")


def _check_feature_patterns():
    """Law 157: FEATURES = {key: description} dict format."""
    for domain_name, files in DOMAINS.items():
        for p in files:
            if p.name == "features.py":
                content = read(p)
                if not content:
                    continue
                tree = parse_ast(p)
                if not tree:
                    continue
                # Check for FEATURES assignment
                for node in ast.walk(tree):
                    if isinstance(node, ast.Assign):
                        for target in node.targets:
                            if isinstance(target, ast.Name) and target.id == "FEATURES":
                                if not isinstance(node.value, ast.Dict):
                                    f(157, "domain", "high", rel(p), node.lineno,
                                      f"FEATURES is not a dictionary",
                                      "Define FEATURES as a dict: FEATURES = {'feature.key': 'Description'}")
                                else:
                                    # Check key format: should be dotted
                                    for key in node.value.keys:
                                        if isinstance(key, ast.Constant) and isinstance(key.value, str):
                                            if "." not in key.value:
                                                f(157, "domain", "medium", rel(p), node.lineno,
                                                  f"Feature key '{key.value}' missing dotted namespace",
                                                  "Use dotted format: '{domain}.{entity}.{action}' (e.g., 'catalog.product.create')")


def _check_read_model_patterns():
    """Law 158: Read model patterns — CQRS-lite projections."""
    for domain_name, files in DOMAINS.items():
        for p in files:
            if "/read_models/" in str(p) and p.suffix == ".py":
                content = read(p)
                if not content:
                    continue
                tree = parse_ast(p)
                if not tree:
                    continue
                classes = get_classes(tree)
                for cls in classes:
                    # Read models should be simple data classes or Pydantic
                    has_pydantic = "BaseModel" in content
                    if not has_pydantic and len(cls.body) > 10:
                        f(158, "domain", "low", rel(p), cls.lineno,
                          f"Read model '{cls.name}' is complex — read models should be simple projections",
                          "Keep read models simple: flat fields, no business logic, no DB writes")


def _check_policy_patterns():
    """Law 159: Authorization policies."""
    for domain_name, files in DOMAINS.items():
        for p in files:
            if "/policies/" in str(p) and p.suffix == ".py":
                content = read(p)
                if not content:
                    continue
                tree = parse_ast(p)
                if not tree:
                    continue
                funcs = get_functions(tree)
                for func in funcs:
                    if func.name.startswith("_"):
                        continue
                    # Policy functions should return bool
                    if func.returns is None:
                        f(159, "domain", "low", rel(p), func.lineno,
                          f"Policy function '{func.name}' lacks return type annotation",
                          "Policy functions should return bool and have type annotations")


def _check_domain_count():
    """Law 160: 15 domains fixed — new domains require architecture review."""
    expected_domains = {
        "accounts", "analytics", "audit", "catalog", "comms", "country",
        "customers", "finance", "governance", "hr", "logistics", "orders",
        "payments", "promotions", "security", "suppliers"
    }
    actual_domains = set(DOMAINS.keys())
    unexpected = actual_domains - expected_domains
    missing = expected_domains - actual_domains

    if unexpected:
        for domain in sorted(unexpected):
            f(160, "domain", "high", f"domains/{domain}/", 0,
              f"Unexpected domain '{domain}' — new domains require architecture review",
              "Submit architecture review before adding new domains")
    if missing:
        for domain in sorted(missing):
            f(160, "domain", "low", f"domains/{domain}/", 0,
              f"Expected domain '{domain}' not found",
              f"Verify domain '{domain}' exists or update expected domain list")


# ══════════════════════════════════════════════════════════════
# LAWS 161-167: RBAC
# ══════════════════════════════════════════════════════════════

def check_section_rbac():
    """Laws 161-167: RBAC."""

    # ── Law 161: Catalog single source ─────────────────────────
    _check_rbac_catalog()

    # ── Law 162: Role definitions ──────────────────────────────
    _check_rbac_roles()

    # ── Law 163: Resolution ────────────────────────────────────
    _check_rbac_resolution()

    # ── Law 164: Dependencies ──────────────────────────────────
    _check_rbac_dependencies()

    # ── Law 165: Service ───────────────────────────────────────
    _check_rbac_service()

    # ── Law 166: Permission models ─────────────────────────────
    _check_rbac_models()

    # ── Law 167: Frontend permissions ──────────────────────────
    _check_frontend_permissions()


def _check_rbac_catalog():
    """Law 161: Catalog aggregates all features.py via package scan."""
    catalog_files = [p for p in RBAC if p.name == "catalog.py"]
    if not catalog_files:
        f(161, "rbac", "critical", "rbac/catalog.py", 0,
          "rbac/catalog.py not found — feature catalog is single source of truth",
          "Create rbac/catalog.py that aggregates FEATURES from all domains/*/features.py via pkgutil")
        return

    content = read(catalog_files[0])
    if not content:
        return

    # Check for package scan pattern
    if "pkgutil" not in content and "iter_modules" not in content:
        f(161, "rbac", "high", rel(catalog_files[0]), 1,
          "Catalog does not use pkgutil.iter_modules to scan domains",
          "Use pkgutil.iter_modules(domains.__path__) to discover and aggregate all FEATURES dicts")

    # Check for FEATURE_CATALOG
    if "FEATURE_CATALOG" not in content:
        f(161, "rbac", "high", rel(catalog_files[0]), 1,
          "Catalog missing FEATURE_CATALOG dict",
          "Define FEATURE_CATALOG: dict = {} and populate via package scan")


def _check_rbac_roles():
    """Law 162: Role definitions — (module, role) to feature sets."""
    roles_files = [p for p in RBAC if p.name == "roles.py"]
    if not roles_files:
        f(162, "rbac", "critical", "rbac/roles.py", 0,
          "rbac/roles.py not found — role definitions missing",
          "Create rbac/roles.py with ROLE_FEATURES mapping (module, role) -> feature set")
        return

    content = read(roles_files[0])
    if not content:
        return

    if "ROLE_FEATURES" not in content:
        f(162, "rbac", "high", rel(roles_files[0]), 1,
          "rbac/roles.py missing ROLE_FEATURES definition",
          "Define ROLE_FEATURES: Dict[Tuple[str, str], Set[str]] mapping (module, role) to feature sets")


def _check_rbac_resolution():
    """Law 163: Resolution — actor x role x country to effective set. Redis-cached."""
    resolution_files = [p for p in RBAC if p.name == "resolution.py"]
    if not resolution_files:
        f(163, "rbac", "critical", "rbac/resolution.py", 0,
          "rbac/resolution.py not found — feature resolution missing",
          "Create rbac/resolution.py with effective_features() function")
        return

    content = read(resolution_files[0])
    if not content:
        return

    if "effective_features" not in content:
        f(163, "rbac", "high", rel(resolution_files[0]), 1,
          "resolution.py missing effective_features() function",
          "Define effective_features(role_features, db_grants, overrides, catalog) -> Set[str]")

    if "expand_wildcards" not in content:
        f(163, "rbac", "medium", rel(resolution_files[0]), 1,
          "resolution.py missing expand_wildcards() helper",
          "Define expand_wildcards(features, catalog) to expand '*' and 'prefix.*' patterns")


def _check_rbac_dependencies():
    """Law 164: require_feature() and require_module() gates."""
    dep_files = [p for p in RBAC if p.name == "dependencies.py"]
    if not dep_files:
        f(164, "rbac", "critical", "rbac/dependencies.py", 0,
          "rbac/dependencies.py not found — FastAPI gates missing",
          "Create rbac/dependencies.py with require_feature() and require_module() dependency factories")
        return

    content = read(dep_files[0])
    if not content:
        return

    if "require_feature" not in content:
        f(164, "rbac", "high", rel(dep_files[0]), 1,
          "dependencies.py missing require_feature() function",
          "Define require_feature(feature: str) -> FastAPI dependency that checks user's effective features")

    if "require_module" not in content:
        f(164, "rbac", "medium", rel(dep_files[0]), 1,
          "dependencies.py missing require_module() function",
          "Define require_module(module: str) -> FastAPI dependency for module-level gating")


def _check_rbac_service():
    """Law 165: Grant/revoke, delegation, maker-checker."""
    service_files = [p for p in RBAC if p.name == "service.py"]
    if not service_files:
        f(165, "rbac", "critical", "rbac/service.py", 0,
          "rbac/service.py not found — RBAC admin operations missing",
          "Create rbac/service.py with RBACService for grant/revoke operations")
        return

    content = read(service_files[0])
    if not content:
        return

    if "grant" not in content:
        f(165, "rbac", "high", rel(service_files[0]), 1,
          "service.py missing grant() method",
          "Implement grant(role, feature, granted_by, country_code) for feature assignment")

    if "revoke" not in content:
        f(165, "rbac", "high", rel(service_files[0]), 1,
          "service.py missing revoke() method",
          "Implement revoke(role, feature, revoked_by, country_code) for feature removal")


def _check_rbac_models():
    """Law 166: Permission models — categories, permissions, assignments, overrides."""
    models_files = [p for p in RBAC if p.name == "models.py"]
    if not models_files:
        # Check for models/ subdirectory
        models_dir = [p for p in RBAC if p.name.startswith("models")]
        if not models_dir:
            f(166, "rbac", "high", "rbac/models.py", 0,
              "rbac/models.py not found — permission persistence models missing",
              "Create rbac/models.py (or models/ package) with Permission, RolePermissionAssignment, PermissionAuditLog")
        return

    content = read(models_files[0])
    if not content:
        return

    required_models = ["Permission", "RolePermissionAssignment"]
    for model_name in required_models:
        if model_name not in content:
            f(166, "rbac", "medium", rel(models_files[0]), 1,
              f"rbac/models.py missing {model_name} model",
              f"Define {model_name} SQLAlchemy model for RBAC persistence")


def _check_frontend_permissions():
    """Law 167: permissions.ts GENERATED from /rbac/catalog."""
    if not FRONTEND_ROOT.exists():
        return

    # Look for permissions.ts in shared or web_app
    permissions_files = [
        FRONTEND_ROOT / "shared" / "src" / "permissions.ts",
        FRONTEND_ROOT / "web_app" / "src" / "permissions.ts",
    ]

    found = False
    for p in permissions_files:
        if p.exists():
            found = True
            content = read(p)
            if content:
                # Check for generation marker
                if "generated" not in content.lower() and "auto-generated" not in content.lower():
                    f(167, "frontend", "medium", str(p.relative_to(FRONTEND_ROOT)), 1,
                      "permissions.ts does not contain generation marker",
                      "Add comment: '// AUTO-GENERATED from GET /rbac/catalog — do not edit manually'")
            break

    if not found:
        f(167, "frontend", "high", "shared/src/permissions.ts", 0,
          "permissions.ts not found — frontend permissions must be generated from backend /rbac/catalog",
          "Generate permissions.ts from GET /rbac/catalog endpoint output")


# ══════════════════════════════════════════════════════════════
# LAWS 168-177: FRONTEND
# ══════════════════════════════════════════════════════════════

def check_section_frontend():
    """Laws 168-177: Frontend."""

    # ── Law 168: Monorepo ──────────────────────────────────────
    _check_frontend_monorepo()

    # ── Law 169: Next.js version ───────────────────────────────
    _check_nextjs_version()

    # ── Law 170: TypeScript strict ─────────────────────────────
    _check_typescript_strict()

    # ── Law 171: State management ──────────────────────────────
    _check_state_management()

    # ── Law 172: Data fetching ─────────────────────────────────
    _check_data_fetching()

    # ── Law 173: API proxy ─────────────────────────────────────
    _check_api_proxy()

    # ── Law 174: Styling ───────────────────────────────────────
    _check_styling()

    # ── Law 175: Forms ─────────────────────────────────────────
    _check_forms()

    # ── Law 176: Error handling ────────────────────────────────
    _check_error_handling()

    # ── Law 177: Route groups ──────────────────────────────────
    _check_route_groups()


def _check_frontend_monorepo():
    """Law 168: Monorepo — web_app/, mobile_app/, shared/."""
    if not FRONTEND_ROOT.exists():
        f(168, "frontend", "critical", "frontend/", 0,
          "frontend/ directory not found",
          "Create frontend/ with web_app/, mobile_app/, and shared/ packages")
        return

    required_dirs = ["web_app", "mobile_app", "shared"]
    for d in required_dirs:
        if not (FRONTEND_ROOT / d).exists():
            f(168, "frontend", "high", f"frontend/{d}/", 0,
              f"frontend/{d}/ directory missing",
              f"Create frontend/{d}/ as part of the frontend monorepo")


def _check_nextjs_version():
    """Law 169: Next.js 16.3.1+ with App Router."""
    if not FRONTEND_ROOT.exists():
        return

    package_json = FRONTEND_ROOT / "web_app" / "package.json"
    if not package_json.exists():
        f(169, "frontend", "high", "frontend/web_app/package.json", 0,
          "package.json not found in web_app",
          "Create package.json with next: 16.3.1+ dependency")
        return

    content = read(package_json)
    if not content:
        return

    match = re.search(r'"next":\s*"([^"]+)"', content)
    if match:
        version = match.group(1)
        # Parse major.minor
        parts = version.replace("^", "").replace("~", "").split(".")
        if len(parts) >= 2:
            try:
                major = int(parts[0])
                minor = int(parts[1])
                if major < 16 or (major == 16 and minor < 3):
                    f(169, "frontend", "high", "frontend/web_app/package.json", 0,
                      f"Next.js version {version} is below required 16.3.1",
                          "Upgrade to Next.js 16.3.1+ for App Router support")
            except ValueError:
                pass

    # Check for App Router (app/ directory)
    app_dir = FRONTEND_ROOT / "web_app" / "src" / "app"
    if not app_dir.exists():
        f(169, "frontend", "high", "frontend/web_app/src/app/", 0,
          "App Router directory (src/app/) not found",
          "Use App Router with src/app/ directory structure")


def _check_typescript_strict():
    """Law 170: TypeScript strict mode."""
    if not FRONTEND_ROOT.exists():
        return

    tsconfig = FRONTEND_ROOT / "web_app" / "tsconfig.json"
    if not tsconfig.exists():
        f(170, "frontend", "high", "frontend/web_app/tsconfig.json", 0,
          "tsconfig.json not found",
          "Create tsconfig.json with strict: true")
        return

    content = read(tsconfig)
    if not content:
        return

    try:
        config = json.loads(content)
        compiler_options = config.get("compilerOptions", {})
        if not compiler_options.get("strict", False):
            f(170, "frontend", "high", "frontend/web_app/tsconfig.json", 0,
              "TypeScript strict mode is not enabled",
              'Set "strict": true in tsconfig.json compilerOptions')
    except json.JSONDecodeError:
        f(170, "frontend", "medium", "frontend/web_app/tsconfig.json", 0,
          "tsconfig.json is not valid JSON",
          "Fix JSON syntax errors in tsconfig.json")


def _check_state_management():
    """Law 171: Zustand (global), React (local), Query/SWR (server)."""
    if not FRONTEND_ROOT.exists():
        return

    package_json = FRONTEND_ROOT / "web_app" / "package.json"
    if not package_json.exists():
        return

    content = read(package_json)
    if not content:
        return

    # Check for Zustand
    if "zustand" not in content:
        f(171, "frontend", "medium", "frontend/web_app/package.json", 0,
          "Zustand not found in dependencies — required for global state management",
          'Add "zustand" to dependencies for global state management')

    # Check for React Query or SWR
    has_query = "react-query" in content or "@tanstack/react-query" in content
    has_swr = "swr" in content
    if not has_query and not has_swr:
        f(171, "frontend", "medium", "frontend/web_app/package.json", 0,
          "No server-state library found (react-query or swr required)",
          "Add @tanstack/react-query or swr for server state management")


def _check_data_fetching():
    """Law 172: Server Components fetch directly."""
    if not FRONTEND_ROOT.exists():
        return

    app_dir = FRONTEND_ROOT / "web_app" / "src" / "app"
    if not app_dir.exists():
        return

    # Check for client components making API calls that should be server-side
    for p in safe_rglob(app_dir, "*.tsx"):
        content = read(p)
        if not content:
            continue
        # If it's a client component with fetch calls, flag
        if '"use client"' in content and "fetch(" in content:
            # Check if it's fetching from internal API
            if "/api/" in content:
                f(172, "frontend", "low", str(p.relative_to(FRONTEND_ROOT)), 1,
                  "Client component fetches internal API — consider using Server Component",
                  "Server Components should fetch data directly; avoid client-side API calls for initial data")


def _check_api_proxy():
    """Law 173: Next.js rewrites /api/*, /admin/*, etc."""
    if not FRONTEND_ROOT.exists():
        return

    next_config = FRONTEND_ROOT / "web_app" / "next.config.ts"
    if not next_config.exists():
        next_config = FRONTEND_ROOT / "web_app" / "next.config.js"

    if not next_config.exists():
        f(173, "frontend", "high", "frontend/web_app/next.config.ts", 0,
          "next.config.ts not found — API proxy rewrites missing",
          "Create next.config.ts with rewrites() for /api/*, /admin/*, /auth/*, /hr/*, /uploads/*")
        return

    content = read(next_config)
    if not content:
        return

    required_sources = ["/api/", "/admin/", "/auth/"]
    for source in required_sources:
        if source not in content:
            f(173, "frontend", "medium", str(next_config.relative_to(FRONTEND_ROOT)), 0,
              f"Missing rewrite for {source} in next.config",
              f"Add rewrite rule: {{ source: '{source}:path*', destination: ... }}")


def _check_styling():
    """Law 174: Tailwind CSS + CVA + tailwind-merge + clsx."""
    if not FRONTEND_ROOT.exists():
        return

    package_json = FRONTEND_ROOT / "web_app" / "package.json"
    if not package_json.exists():
        return

    content = read(package_json)
    if not content:
        return

    required_libs = {
        "tailwind-merge": "tailwind-merge for class merging",
        "clsx": "clsx for conditional classes",
        "class-variance-authority": "CVA for component variants",
    }

    for lib, description in required_libs.items():
        if lib not in content:
            f(174, "frontend", "medium", "frontend/web_app/package.json", 0,
              f"Missing {description}",
              f'Add "{lib}" to dependencies')

    # Check for PostCSS config
    postcss_config = FRONTEND_ROOT / "web_app" / "postcss.config.js"
    if not postcss_config.exists():
        f(174, "frontend", "high", "frontend/web_app/postcss.config.js", 0,
          "postcss.config.js not found — required for Tailwind CSS processing",
          "Create postcss.config.js with tailwindcss and autoprefixer plugins")


def _check_forms():
    """Law 175: React Hook Form + Zod."""
    if not FRONTEND_ROOT.exists():
        return

    package_json = FRONTEND_ROOT / "web_app" / "package.json"
    if not package_json.exists():
        return

    content = read(package_json)
    if not content:
        return

    if "react-hook-form" not in content:
        f(175, "frontend", "medium", "frontend/web_app/package.json", 0,
          "react-hook-form not found in dependencies",
          'Add "react-hook-form" for form management')

    if "zod" not in content:
        f(175, "frontend", "medium", "frontend/web_app/package.json", 0,
          "zod not found in dependencies",
          'Add "zod" for form validation schemas')


def _check_error_handling():
    """Law 176: API errors to toasts/boundaries."""
    if not FRONTEND_ROOT.exists():
        return

    # Check for error boundary components
    error_boundary = FRONTEND_ROOT / "web_app" / "src" / "components" / "ui" / "ErrorBoundary.tsx"
    if not error_boundary.exists():
        f(176, "frontend", "medium", "frontend/web_app/src/components/ui/ErrorBoundary.tsx", 0,
          "ErrorBoundary component not found",
          "Create ErrorBoundary.tsx for React error handling")

    # Check for global error handler
    global_error = FRONTEND_ROOT / "web_app" / "src" / "app" / "global-error.tsx"
    if not global_error.exists():
        f(176, "frontend", "low", "frontend/web_app/src/app/global-error.tsx", 0,
          "global-error.tsx not found — Next.js global error UI missing",
          "Create app/global-error.tsx for uncaught route errors")


def _check_route_groups():
    """Law 177: Route groups organized by actor."""
    if not FRONTEND_ROOT.exists():
        return

    app_dir = FRONTEND_ROOT / "web_app" / "src" / "app"
    if not app_dir.exists():
        return

    # Check for actor-based route groups (parenthesized directories)
    route_groups = []
    for p in app_dir.iterdir():
        if p.is_dir() and p.name.startswith("(") and p.name.endswith(")"):
            route_groups.append(p.name)

    expected_groups = {"(auth)", "(tabs)"}
    found_groups = set(route_groups)

    if not found_groups:
        f(177, "frontend", "low", "frontend/web_app/src/app/", 0,
          "No route groups found — organize routes by actor using (group) directories",
          "Create route groups like (auth)/, (tabs)/, (dashboard)/ for actor-based organization")


# ══════════════════════════════════════════════════════════════
# LAWS 178-186: WEB APP
# ══════════════════════════════════════════════════════════════

def check_section_web_app():
    """Laws 178-186: Web App."""

    # ── Law 178: Route structure ───────────────────────────────
    _check_route_structure()

    # ── Law 179: Component structure ───────────────────────────
    _check_component_structure()

    # ── Law 180: Hook patterns ─────────────────────────────────
    _check_hook_patterns()

    # ── Law 181: Lib patterns ──────────────────────────────────
    _check_lib_patterns()

    # ── Law 182: Service patterns ──────────────────────────────
    _check_web_services()

    # ── Law 183: Theme/styling ─────────────────────────────────
    _check_theme_styling()

    # ── Law 184: Types ─────────────────────────────────────────
    _check_web_types()

    # ── Law 185: Utils ─────────────────────────────────────────
    _check_web_utils()

    # ── Law 186: Build ─────────────────────────────────────────
    _check_web_build()


def _check_route_structure():
    """Law 178: page.tsx, layout.tsx, loading.tsx, error.tsx per route."""
    if not FRONTEND_ROOT.exists():
        return

    app_dir = FRONTEND_ROOT / "web_app" / "src" / "app"
    if not app_dir.exists():
        return

    # Find route directories (those containing page.tsx)
    route_dirs = set()
    for p in safe_rglob(app_dir, "page.tsx"):
        route_dirs.add(p.parent)

    for route_dir in route_dirs:
        rel_path = str(route_dir.relative_to(app_dir))
        # Check for layout.tsx
        if not (route_dir / "layout.tsx").exists():
            f(178, "web_app", "low", f"frontend/web_app/src/app/{rel_path}/layout.tsx", 0,
              f"Route '{rel_path}' missing layout.tsx",
              f"Create layout.tsx for consistent page structure in {rel_path}/")


def _check_component_structure():
    """Law 179: ui/ (design system), admin/, auth/, etc."""
    if not FRONTEND_ROOT.exists():
        return

    components_dir = FRONTEND_ROOT / "web_app" / "src" / "components"
    if not components_dir.exists():
        f(179, "web_app", "high", "frontend/web_app/src/components/", 0,
          "components/ directory not found",
          "Create src/components/ with ui/ (design system), admin/, auth/ subdirectories")
        return

    # Check for ui/ design system
    ui_dir = components_dir / "ui"
    if not ui_dir.exists():
        f(179, "web_app", "medium", "frontend/web_app/src/components/ui/", 0,
          "components/ui/ directory not found — design system components missing",
          "Create components/ui/ with design system primitives (Button, Input, Card, etc.)")


def _check_hook_patterns():
    """Law 180: useXxx prefix. No JSX in hooks."""
    if not FRONTEND_ROOT.exists():
        return

    hooks_dir = FRONTEND_ROOT / "web_app" / "src" / "hooks"
    if not hooks_dir.exists():
        return

    for p in hooks_dir.glob("*.ts"):
        content = read(p)
        if not content:
            continue
        # Check for JSX in hooks (should not have JSX)
        if "<" in content and ">" in content:
            # Simple heuristic: check for JSX patterns
            if re.search(r'<[A-Z][a-zA-Z]*[\s/>]|<[a-z]+[\s/>]', content):
                f(180, "web_app", "medium", str(p.relative_to(FRONTEND_ROOT)), 1,
                  f"Hook file '{p.name}' contains JSX — hooks should not return JSX",
                  "Move JSX to components; hooks should return data/state only")

    for p in hooks_dir.glob("*.tsx"):
        # .tsx hooks are acceptable if they return JSX, but name should start with use
        if not p.stem.startswith("use"):
            f(180, "web_app", "low", str(p.relative_to(FRONTEND_ROOT)), 1,
              f"Hook file '{p.name}' does not start with 'use' prefix",
              "Rename to use<Name>.tsx to follow hook naming convention")


def _check_lib_patterns():
    """Law 181: api/ (client, auth, country, errors), rbac.ts."""
    if not FRONTEND_ROOT.exists():
        return

    lib_dir = FRONTEND_ROOT / "web_app" / "src" / "lib"
    if not lib_dir.exists():
        f(181, "web_app", "high", "frontend/web_app/src/lib/", 0,
          "lib/ directory not found",
          "Create src/lib/ with api/, rbac.ts, and utility modules")
        return

    # Check for api client
    api_files = list(lib_dir.glob("*.ts"))
    api_related = [f for f in api_files if "api" in f.name.lower() or "client" in f.name.lower()]
    if not api_related:
        f(181, "web_app", "medium", "frontend/web_app/src/lib/", 0,
          "No API client file found in lib/",
          "Create lib/api.ts or lib/client.ts for API communication")


def _check_web_services():
    """Law 182: localizationService, crossBorderService, etc."""
    if not FRONTEND_ROOT.exists():
        return

    services_dir = FRONTEND_ROOT / "web_app" / "src" / "services"
    if not services_dir.exists():
        f(182, "web_app", "low", "frontend/web_app/src/services/", 0,
          "services/ directory not found",
          "Create src/services/ for domain-specific frontend services (localizationService, crossBorderService)")
        return

    service_files = list(services_dir.glob("*.ts"))
    if not service_files:
        f(182, "web_app", "low", "frontend/web_app/src/services/", 0,
          "No service files found in services/",
          "Add service files like localizationService.ts, crossBorderService.ts")


def _check_theme_styling():
    """Law 183: Design tokens, Tailwind config, global CSS."""
    if not FRONTEND_ROOT.exists():
        return

    # Check for Tailwind config
    tailwind_config = FRONTEND_ROOT / "web_app" / "tailwind.config.js"
    if not tailwind_config.exists():
        tailwind_config = FRONTEND_ROOT / "web_app" / "tailwind.config.ts"

    if not tailwind_config.exists():
        f(183, "web_app", "high", "frontend/web_app/tailwind.config.js", 0,
          "tailwind.config.js not found",
          "Create tailwind.config.js with design tokens and content paths")

    # Check for global CSS
    global_css = FRONTEND_ROOT / "web_app" / "src" / "app" / "globals.css"
    if not global_css.exists():
        # Check alternative locations
        alt_css = FRONTEND_ROOT / "web_app" / "src" / "styles" / "globals.css"
        if not alt_css.exists():
            f(183, "web_app", "medium", "frontend/web_app/src/app/globals.css", 0,
              "globals.css not found — global styles missing",
              "Create globals.css with Tailwind directives and CSS custom properties")


def _check_web_types():
    """Law 184: Types from @zozi/shared + local definitions."""
    if not FRONTEND_ROOT.exists():
        return

    # Check for @zozi/shared imports
    src_dir = FRONTEND_ROOT / "web_app" / "src"
    if not src_dir.exists():
        return

    has_shared_import = False
    for p in safe_rglob(src_dir, "*.ts*"):
        content = read(p)
        if not content:
            continue
        if "@zozi/shared" in content:
            has_shared_import = True
            break

    if not has_shared_import:
        f(184, "web_app", "medium", "frontend/web_app/src/", 0,
          "No imports from @zozi/shared found",
          "Import shared types from @zozi/shared for cross-platform type consistency")


def _check_web_utils():
    """Law 185: Pure utility functions."""
    if not FRONTEND_ROOT.exists():
        return

    lib_dir = FRONTEND_ROOT / "web_app" / "src" / "lib"
    if not lib_dir.exists():
        return

    utils_file = lib_dir / "utils.ts"
    if not utils_file.exists():
        f(185, "web_app", "low", "frontend/web_app/src/lib/utils.ts", 0,
          "lib/utils.ts not found — pure utility functions missing",
          "Create lib/utils.ts for shared pure utility functions (formatting, validation helpers)")


def _check_web_build():
    """Law 186: next build passes with no errors."""
    if not FRONTEND_ROOT.exists():
        return

    # Check for build script in package.json
    package_json = FRONTEND_ROOT / "web_app" / "package.json"
    if not package_json.exists():
        return

    content = read(package_json)
    if not content:
        return

    if '"build"' not in content:
        f(186, "web_app", "high", "frontend/web_app/package.json", 0,
          "No build script found in package.json",
          'Add "build": "next build" script to package.json')


# ══════════════════════════════════════════════════════════════
# LAWS 187-194: MOBILE
# ══════════════════════════════════════════════════════════════

def check_section_mobile():
    """Laws 187-194: Mobile."""

    # ── Law 187: Expo SDK 51+ ──────────────────────────────────
    _check_expo_sdk()

    # ── Law 188: Route groups ──────────────────────────────────
    _check_mobile_routes()

    # ── Law 189: Components ────────────────────────────────────
    _check_mobile_components()

    # ── Law 190: Lib patterns ──────────────────────────────────
    _check_mobile_lib()

    # ── Law 191: Platform-specific ─────────────────────────────
    _check_platform_specific()

    # ── Law 192: State ─────────────────────────────────────────
    _check_mobile_state()

    # ── Law 193: Storage ───────────────────────────────────────
    _check_mobile_storage()

    # ── Law 194: Build ─────────────────────────────────────────
    _check_mobile_build()


def _check_expo_sdk():
    """Law 187: Expo SDK 51+ with Expo Router."""
    if not FRONTEND_ROOT.exists():
        return

    package_json = FRONTEND_ROOT / "mobile_app" / "package.json"
    if not package_json.exists():
        f(187, "mobile", "critical", "frontend/mobile_app/package.json", 0,
          "mobile_app/package.json not found",
          "Create mobile_app/ with Expo SDK 51+ and Expo Router")
        return

    content = read(package_json)
    if not content:
        return

    # Check Expo version
    match = re.search(r'"expo":\s*"([^"]+)"', content)
    if match:
        version = match.group(1).replace("^", "").replace("~", "")
        parts = version.split(".")
        if len(parts) >= 2:
            try:
                major = int(parts[0])
                if major < 51:
                    f(187, "mobile", "high", "frontend/mobile_app/package.json", 0,
                      f"Expo SDK {version} is below required 51",
                      "Upgrade to Expo SDK 51+ for latest features and security")
            except ValueError:
                pass

    # Check for expo-router
    if "expo-router" not in content:
        f(187, "mobile", "high", "frontend/mobile_app/package.json", 0,
          "expo-router not found in dependencies",
          'Add "expo-router" for file-based routing')


def _check_mobile_routes():
    """Law 188: Route groups — (auth), (tabs), admin/, supplier/, etc."""
    if not FRONTEND_ROOT.exists():
        return

    app_dir = FRONTEND_ROOT / "mobile_app" / "app"
    if not app_dir.exists():
        f(188, "mobile", "high", "frontend/mobile_app/app/", 0,
          "mobile app/ directory not found — Expo Router routes missing",
          "Create app/ directory with route groups: (auth)/, (tabs)/, admin/, supplier/")
        return

    # Check for route groups
    has_auth_group = (app_dir / "(auth)").exists() or (app_dir / "(tabs)").exists()
    has_admin = (app_dir / "admin").exists()
    has_supplier = (app_dir / "supplier").exists()

    if not has_auth_group:
        f(188, "mobile", "medium", "frontend/mobile_app/app/(auth)/", 0,
          "No route groups (auth)/ or (tabs)/ found",
          "Create (auth)/ and (tabs)/ route groups for organized navigation")

    if not has_admin:
        f(188, "mobile", "low", "frontend/mobile_app/app/admin/", 0,
          "No admin/ route group found",
          "Create app/admin/ for admin-specific screens")


def _check_mobile_components():
    """Law 189: components/ui/ design system."""
    if not FRONTEND_ROOT.exists():
        return

    components_dir = FRONTEND_ROOT / "mobile_app" / "components"
    if not components_dir.exists():
        f(189, "mobile", "high", "frontend/mobile_app/components/", 0,
          "mobile components/ directory not found",
          "Create components/ with ui/ design system")
        return

    ui_dir = components_dir / "ui"
    if not ui_dir.exists():
        f(189, "mobile", "medium", "frontend/mobile_app/components/ui/", 0,
          "components/ui/ directory not found — design system missing",
          "Create components/ui/ with reusable design system components")


def _check_mobile_lib():
    """Law 190: api, stores, authPrompt, countryContext, etc."""
    if not FRONTEND_ROOT.exists():
        return

    lib_dir = FRONTEND_ROOT / "mobile_app" / "lib"
    if not lib_dir.exists():
        f(190, "mobile", "high", "frontend/mobile_app/lib/", 0,
          "mobile lib/ directory not found",
          "Create lib/ with api.ts, stores, authPrompt, countryContext")
        return

    # Check for API module
    api_file = lib_dir / "api.ts"
    if not api_file.exists():
        f(190, "mobile", "medium", "frontend/mobile_app/lib/api.ts", 0,
          "lib/api.ts not found — API client missing",
          "Create lib/api.ts for API communication")


def _check_platform_specific():
    """Law 191: .native.ts / .ts suffixes for platform-specific code."""
    if not FRONTEND_ROOT.exists():
        return

    mobile_dir = FRONTEND_ROOT / "mobile_app"
    if not mobile_dir.exists():
        return

    # Check for platform-specific files
    try:
        native_files = list(mobile_dir.rglob("*.native.ts")) + list(mobile_dir.rglob("*.native.tsx"))
        web_files = list(mobile_dir.rglob("*.web.ts")) + list(mobile_dir.rglob("*.web.tsx"))
    except (OSError, PermissionError):
        native_files = []
        web_files = []

    if not native_files and not web_files:
        f(191, "mobile", "low", "frontend/mobile_app/", 0,
          "No platform-specific files (.native.ts, .web.ts) found",
          "Use .native.ts/.native.tsx for native-only code and .web.ts/.web.tsx for web-specific code")


def _check_mobile_state():
    """Law 192: Zustand (same stores as web)."""
    if not FRONTEND_ROOT.exists():
        return

    package_json = FRONTEND_ROOT / "mobile_app" / "package.json"
    if not package_json.exists():
        return

    content = read(package_json)
    if not content:
        return

    if "zustand" not in content:
        f(192, "mobile", "high", "frontend/mobile_app/package.json", 0,
          "Zustand not found in mobile dependencies — required for state management",
          'Add "zustand" to dependencies for global state management (same stores as web)')


def _check_mobile_storage():
    """Law 193: expo-secure-storage for secrets."""
    if not FRONTEND_ROOT.exists():
        return

    package_json = FRONTEND_ROOT / "mobile_app" / "package.json"
    if not package_json.exists():
        return

    content = read(package_json)
    if not content:
        return

    if "expo-secure-store" not in content:
        f(193, "mobile", "high", "frontend/mobile_app/package.json", 0,
          "expo-secure-store not found — required for secure secret storage",
          'Add "expo-secure-store" to dependencies for storing tokens and secrets')


def _check_mobile_build():
    """Law 194: EAS Build. Expo Go for dev."""
    if not FRONTEND_ROOT.exists():
        return

    # Check for app.json/app.config.js
    app_json = FRONTEND_ROOT / "mobile_app" / "app.json"
    app_config = FRONTEND_ROOT / "mobile_app" / "app.config.js"

    if not app_json.exists() and not app_config.exists():
        f(194, "mobile", "high", "frontend/mobile_app/app.json", 0,
          "No app.json or app.config.js found — Expo configuration missing",
          "Create app.json with Expo configuration for EAS Build")
        return

    # Check for EAS config
    eas_json = FRONTEND_ROOT / "mobile_app" / "eas.json"
    if not eas_json.exists():
        f(194, "mobile", "low", "frontend/mobile_app/eas.json", 0,
          "eas.json not found — EAS Build configuration missing",
          "Create eas.json with build profiles for EAS Build")


# ══════════════════════════════════════════════════════════════
# LAWS 195-200: SHARED
# ══════════════════════════════════════════════════════════════

def check_section_shared():
    """Laws 195-200: Shared."""

    # ── Law 195: Structure ─────────────────────────────────────
    _check_shared_structure()

    # ── Law 196: No app imports ────────────────────────────────
    _check_shared_no_app_imports()

    # ── Law 197: Permissions generated ─────────────────────────
    _check_shared_permissions_generated()

    # ── Law 198: Cross-platform types ──────────────────────────
    _check_shared_cross_platform_types()

    # ── Law 199: API core ──────────────────────────────────────
    _check_shared_api_core()

    # ── Law 200: Money formatting ──────────────────────────────
    _check_shared_money_formatting()


def _check_shared_structure():
    """Law 195: api-core, money, i18n, domain helpers, etc."""
    if not FRONTEND_ROOT.exists():
        return

    shared_src = FRONTEND_ROOT / "shared" / "src"
    if not shared_src.exists():
        f(195, "shared", "critical", "frontend/shared/src/", 0,
          "shared/src/ directory not found",
          "Create shared/src/ with api-core.ts, money.ts, i18n.ts, types.ts, helpers")
        return

    expected_files = ["api-core.ts", "money.ts", "types.ts", "i18n.ts"]
    for fname in expected_files:
        if not (shared_src / fname).exists():
            f(195, "shared", "medium", f"frontend/shared/src/{fname}", 0,
              f"shared/src/{fname} not found",
              f"Create shared/src/{fname} for cross-platform reuse")


def _check_shared_no_app_imports():
    """Law 196: MUST NOT import from web_app/ or mobile_app/."""
    if not FRONTEND_ROOT.exists():
        return

    shared_dir = FRONTEND_ROOT / "shared"
    if not shared_dir.exists():
        return

    for p in safe_rglob(shared_dir, "*.ts*"):
        content = read(p)
        if not content:
            continue
        # Check for imports from web_app or mobile_app
        if re.search(r'from\s+["\']\.\./.*web_app', content) or \
           re.search(r'from\s+["\']\.\./.*mobile_app', content) or \
           re.search(r'from\s+["\']@/web_app', content) or \
           re.search(r'from\s+["\']@/mobile_app', content):
            f(196, "shared", "critical", str(p.relative_to(FRONTEND_ROOT)), 1,
              f"Shared file imports from app-specific code — shared must be platform-agnostic",
              "Remove imports from web_app/ or mobile_app/; shared must only depend on other shared code")


def _check_shared_permissions_generated():
    """Law 197: permissions.ts GENERATED from backend."""
    if not FRONTEND_ROOT.exists():
        return

    shared_src = FRONTEND_ROOT / "shared" / "src"
    if not shared_src.exists():
        return

    permissions_file = shared_src / "permissions.ts"
    if not permissions_file.exists():
        f(197, "shared", "medium", "frontend/shared/src/permissions.ts", 0,
          "permissions.ts not found in shared package",
          "Create permissions.ts generated from backend /rbac/catalog endpoint")
        return

    content = read(permissions_file)
    if content and "generated" not in content.lower() and "auto" not in content.lower():
        f(197, "shared", "low", "frontend/shared/src/permissions.ts", 1,
          "permissions.ts missing generation marker",
          "Add comment indicating this file is auto-generated from backend /rbac/catalog")


def _check_shared_cross_platform_types():
    """Law 198: Platform-agnostic types."""
    if not FRONTEND_ROOT.exists():
        return

    shared_src = FRONTEND_ROOT / "shared" / "src"
    if not shared_src.exists():
        return

    types_file = shared_src / "types.ts"
    if not types_file.exists():
        f(198, "shared", "high", "frontend/shared/src/types.ts", 0,
          "types.ts not found — cross-platform type definitions missing",
          "Create types.ts with platform-agnostic type definitions")
        return

    content = read(types_file)
    if not content:
        return

    # Check for platform-specific imports
    if "react-native" in content.lower() and "Platform" not in content:
        f(198, "shared", "medium", "frontend/shared/src/types.ts", 1,
          "types.ts may contain platform-specific code — types should be platform-agnostic",
          "Use Platform.OS checks or .native.ts extensions for platform-specific types")


def _check_shared_api_core():
    """Law 199: apiFetch base client with auth, errors, retry."""
    if not FRONTEND_ROOT.exists():
        return

    shared_src = FRONTEND_ROOT / "shared" / "src"
    if not shared_src.exists():
        return

    api_core = shared_src / "api-core.ts"
    if not api_core.exists():
        f(199, "shared", "critical", "frontend/shared/src/api-core.ts", 0,
          "api-core.ts not found — base API client missing",
          "Create api-core.ts with ApiError class, auth handling, retry logic, and TokenAdapter interface")
        return

    content = read(api_core)
    if not content:
        return

    # Check for essential API core features
    if "ApiError" not in content:
        f(199, "shared", "high", "frontend/shared/src/api-core.ts", 1,
          "api-core.ts missing ApiError class",
          "Define ApiError class extending Error with status and body properties")

    if "TokenAdapter" not in content:
        f(199, "shared", "high", "frontend/shared/src/api-core.ts", 1,
          "api-core.ts missing TokenAdapter interface",
          "Define TokenAdapter interface for platform-specific token storage")


def _check_shared_money_formatting():
    """Law 200: Intl.NumberFormat with locale support."""
    if not FRONTEND_ROOT.exists():
        return

    shared_src = FRONTEND_ROOT / "shared" / "src"
    if not shared_src.exists():
        return

    money_file = shared_src / "money.ts"
    if not money_file.exists():
        f(200, "shared", "high", "frontend/shared/src/money.ts", 0,
          "money.ts not found — currency formatting missing",
          "Create money.ts with formatMoney() using Intl.NumberFormat with locale support")
        return

    content = read(money_file)
    if not content:
        return

    if "Intl.NumberFormat" not in content:
        f(200, "shared", "high", "frontend/shared/src/money.ts", 1,
          "money.ts does not use Intl.NumberFormat for currency formatting",
          "Use Intl.NumberFormat with style: 'currency' for locale-aware money formatting")

    if "formatMoney" not in content:
        f(200, "shared", "medium", "frontend/shared/src/money.ts", 1,
          "money.ts missing formatMoney function",
          "Define formatMoney(value, currency, locale) function for currency formatting")
