"""
Section Laws 1-50 — Architecture, Structure, and Security Audit Checks.

Implements detection logic for the first 50 laws of the ZOZI backend audit system.
Each law check uses ASTAnalyzer for code analysis and the pre-indexed file lists
(ALL_PY, DOMAINS, MODELS, etc.) provided by the main audit engine.

Laws covered:
  1, 3, 4, 5, 7, 8, 9, 10, 12, 13, 17, 20, 21, 23, 24, 25, 26,
  30, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44
"""

from pathlib import Path
from collections import defaultdict

# ══════════════════════════════════════════════════════════════
# CONSTANTS
# ══════════════════════════════════════════════════════════════

EXPECTED_DOMAINS = {
    "accounts", "analytics", "audit", "catalog", "comms",
    "country", "customers", "finance", "governance", "hr",
    "logistics", "orders", "payments", "promotions", "security", "suppliers",
}

EXPECTED_MODULES = {"admin", "customer", "employee", "logistics", "supplier"}

FORBIDDEN_SCHEMAS = {"core", "platform", "identity"}

INFRA_FORBIDDEN_IMPORTS = {"domains", "modules", "rbac", "providers"}

KERNEL_FORBIDDEN_IMPORTS = {"domains", "modules", "rbac", "providers", "infrastructure"}

# ══════════════════════════════════════════════════════════════
# LAW 1: Arrows point down only (modules → domains → infrastructure)
# ══════════════════════════════════════════════════════════════

def check_law_1_arrows_point_down():
    """Infrastructure and kernel must not import from higher layers."""
    # Check infrastructure/ files
    for p in INFRA:
        tree, _ = ASTAnalyzer.parse(p)
        if not tree:
            continue
        r = rel(p)
        imports = ASTAnalyzer.get_imports(tree)
        for imp in imports['from']:
            module = imp['module']
            for forbidden in INFRA_FORBIDDEN_IMPORTS:
                if module.startswith(forbidden):
                    f(1, "Architecture", "critical", r, imp['lineno'],
                      f"infrastructure/ imports from '{module}' — arrows must point down only (Law 1).",
                      f"Remove this import. infrastructure/ must not import from domains/, modules/, rbac/, or providers/.")
                    break

    # Check kernel/ files
    for p in KERNEL:
        tree, _ = ASTAnalyzer.parse(p)
        if not tree:
            continue
        r = rel(p)
        imports = ASTAnalyzer.get_imports(tree)
        for imp in imports['from']:
            module = imp['module']
            for forbidden in KERNEL_FORBIDDEN_IMPORTS:
                if module.startswith(forbidden):
                    f(1, "Architecture", "critical", r, imp['lineno'],
                      f"kernel/ imports from '{module}' — kernel must be pure with zero upward imports (Law 1).",
                      f"Remove this import. kernel/ must not import from domains/, modules/, rbac/, providers/, or infrastructure/.")
                    break

    # Check domains/ importing from modules/
    for domain_name, files in DOMAINS.items():
        for p in files:
            tree, _ = ASTAnalyzer.parse(p)
            if not tree:
                continue
            r = rel(p)
            imports = ASTAnalyzer.get_imports(tree)
            for imp in imports['from']:
                module = imp['module']
                if module.startswith("modules."):
                    f(1, "Architecture", "critical", r, imp['lineno'],
                      f"domains/{domain_name}/ imports from '{module}' — domains must never import from modules (Law 1).",
                      f"Remove this import. Domain-to-module imports violate the dependency arrow direction.")
                    break


# ══════════════════════════════════════════════════════════════
# LAW 3: Cross-domain writes via events, reads via ports
# ══════════════════════════════════════════════════════════════

def check_law_3_cross_domain_events_ports():
    """Domains must not import from other domains except via ports.py."""
    for domain_name, files in DOMAINS.items():
        for p in files:
            tree, _ = ASTAnalyzer.parse(p)
            if not tree:
                continue
            r = rel(p)
            # Skip ports.py and events.py — these are the allowed cross-domain interfaces
            if r.endswith("/ports.py") or r.endswith("/events.py") or r.endswith("/subscribers.py"):
                continue
            imports = ASTAnalyzer.get_imports(tree)
            for imp in imports['from']:
                module = imp['module']
                if module.startswith("domains."):
                    parts = module.split(".")
                    if len(parts) >= 2 and parts[1] != domain_name:
                        other_domain = parts[1]
                        if other_domain in EXPECTED_DOMAINS:
                            f(3, "Architecture", "high", r, imp['lineno'],
                              f"domains/{domain_name}/ imports from domains/{other_domain}/ — cross-domain reads must go via ports.py (Law 3).",
                              f"Move this import to domains/{domain_name}/ports.py and expose a read function. Direct cross-domain imports are forbidden.")
                            break


# ══════════════════════════════════════════════════════════════
# LAW 4: Features single-sourced in domains/*/features.py
# ══════════════════════════════════════════════════════════════

def check_law_4_features_single_sourced():
    """Each domain must have a features.py file."""
    for domain_name, files in DOMAINS.items():
        has_features = any(rel(p).endswith("/features.py") for p in files)
        if not has_features:
            f(4, "Structure", "medium", f"domains/{domain_name}/", 0,
              f"Domain '{domain_name}' missing features.py — features must be single-sourced per domain (Law 4).",
              f"Create domains/{domain_name}/features.py with feature flag definitions for this domain.")


# ══════════════════════════════════════════════════════════════
# LAW 5: Country is the orthogonal scope axis
# ══════════════════════════════════════════════════════════════

def check_law_5_country_orthogonal():
    """Check RLS instrumentation, middleware, and country_staff_assignments model."""
    # Check main.py for instrument_rls() call
    main_path = ROOT / "main.py"
    if main_path.exists():
        content = read(main_path)
        if "instrument_rls" not in content:
            f(5, "Architecture", "critical", "backend/main.py", 0,
              "main.py does not call instrument_rls() — RLS is not instrumented (Law 5).",
              "Add instrument_rls(engine) after engine creation to enable row-level security.")
        if "install_rls_policies" not in content:
            f(5, "Architecture", "high", "backend/main.py", 0,
              "main.py does not call install_rls_policies() — RLS policies not installed (Law 5).",
              "Add install_rls_policies(engine) to install Postgres RLS policies.")

    # Check for RLS middleware
    rls_middleware_found = False
    for p in MIDDLEWARE_FILES:
        if "rls" in p.name.lower():
            rls_middleware_found = True
            break
    if not rls_middleware_found:
        f(5, "Architecture", "high", "middleware/", 0,
          "No RLS middleware found — country scoping requires middleware enforcement (Law 5).",
          "Create middleware/rls_middleware.py that sets RLS scope based on authenticated user's country.")

    # Check for country_staff_assignments model
    country_staff_found = False
    for p in MODELS:
        content = read(p)
        if "country_staff_assignments" in content:
            country_staff_found = True
            break
    if not country_staff_found:
        f(5, "Architecture", "medium", "domains/country/", 0,
          "country_staff_assignments model not found — required for country-based staff scoping (Law 5).",
          "Create country_staff_assignments table in domains/country/models/ to track staff-to-country assignments.")


# ══════════════════════════════════════════════════════════════
# LAW 7: Allowlist only shrinks
# ══════════════════════════════════════════════════════════════

def check_law_7_allowlist_only_shrinks():
    """Check if DOMAIN_ALLOWLIST.yaml exists at ROOT."""
    allowlist_path = ROOT / "DOMAIN_ALLOWLIST.yaml"
    if not allowlist_path.exists():
        f(7, "Structure", "medium", "backend/", 0,
          "DOMAIN_ALLOWlist.yaml not found — temporary cross-domain imports must be tracked (Law 7).",
          "Create backend/DOMAIN_ALLOWLIST.yaml listing all temporary cross-domain imports. This file may only shrink over time.")


# ══════════════════════════════════════════════════════════════
# LAW 8: Router structure — modules/{m}/routers/{d}.py
# ══════════════════════════════════════════════════════════════

def check_law_8_router_structure():
    """Each module's routers/ directory should have files for multiple domains."""
    modules_path = ROOT / "modules"
    if not modules_path.exists():
        return

    for module_name in EXPECTED_MODULES:
        routers_dir = modules_path / module_name / "routers"
        if not routers_dir.exists():
            f(8, "Structure", "high", f"modules/{module_name}/", 0,
              f"Module '{module_name}' missing routers/ directory (Law 8).",
              f"Create modules/{module_name}/routers/ with one router file per domain.")
            continue

        router_files = [p for p in routers_dir.glob("*.py") if p.name != "__init__.py"]
        domain_count = len(router_files)
        if domain_count < 5:
            f(8, "Structure", "medium", f"modules/{module_name}/routers/", 0,
              f"Module '{module_name}' has only {domain_count} router files — expected ~15 (one per domain) (Law 8).",
              f"Add router files for all domains in modules/{module_name}/routers/.")


# ══════════════════════════════════════════════════════════════
# LAW 9: Tools in providers (not domains/media)
# ══════════════════════════════════════════════════════════════

def check_law_9_tools_in_providers():
    """domains/media should not exist — media code belongs in providers/."""
    media_path = ROOT / "domains" / "media"
    if media_path.exists() and media_path.is_dir():
        py_files = list(media_path.rglob("*.py"))
        if py_files:
            f(9, "File Placement", "high", "domains/media/", 0,
              f"domains/media/ exists with {len(py_files)} Python files — media code belongs in providers/media/ (Law 9).",
              "Move all files from domains/media/ to providers/media/. Delete domains/media/ after migration.")


# ══════════════════════════════════════════════════════════════
# LAW 10: Kernel is pure
# ══════════════════════════════════════════════════════════════

def check_law_10_kernel_pure():
    """Kernel must not import from domains, modules, rbac, providers, or infrastructure."""
    for p in KERNEL:
        tree, _ = ASTAnalyzer.parse(p)
        if not tree:
            continue
        r = rel(p)
        imports = ASTAnalyzer.get_imports(tree)
        for imp in imports['from']:
            module = imp['module']
            for forbidden in KERNEL_FORBIDDEN_IMPORTS:
                if module.startswith(forbidden):
                    f(10, "Architecture", "critical", r, imp['lineno'],
                      f"kernel/ imports from '{module}' — kernel must be pure business primitives with zero external imports (Law 10).",
                      f"Remove this import. kernel/ must only contain pure primitives: money, currency, numbering, country, period.")
                    break


# ══════════════════════════════════════════════════════════════
# LAW 12: 15 domains
# ══════════════════════════════════════════════════════════════

def check_law_12_fifteen_domains():
    """Check DOMAINS has exactly 15 entries with correct names."""
    actual_domains = set(DOMAINS.keys())
    # Filter out parked/internal
    actual_domains = {d for d in actual_domains if not d.startswith("_")}

    missing = EXPECTED_DOMAINS - actual_domains
    extra = actual_domains - EXPECTED_DOMAINS

    if missing:
        f(12, "Structure", "high", "domains/", 0,
          f"Missing domains: {', '.join(sorted(missing))} — system requires exactly 15 domains (Law 12).",
          f"Create the missing domain directories with proper structure (models/, services/, ports.py, events.py).")
    if extra:
        f(12, "Structure", "medium", "domains/", 0,
          f"Unexpected domains: {', '.join(sorted(extra))} — not in expected 15 domains (Law 12).",
          f"Review whether these domains should be merged into existing ones or added to the expected list.")


# ══════════════════════════════════════════════════════════════
# LAW 13: 5 modules
# ══════════════════════════════════════════════════════════════

def check_law_13_five_modules():
    """Check modules/ directory has exactly 5 entries with correct names."""
    modules_path = ROOT / "modules"
    if not modules_path.exists():
        f(13, "Structure", "critical", "modules/", 0,
          "modules/ directory does not exist — system requires exactly 5 modules (Law 13).",
          "Create modules/ directory with admin, customer, employee, logistics, supplier subdirectories.")
        return

    actual_modules = {d.name for d in modules_path.iterdir() if d.is_dir() and not d.name.startswith("_")}
    missing = EXPECTED_MODULES - actual_modules
    extra = actual_modules - EXPECTED_MODULES

    if missing:
        f(13, "Structure", "high", "modules/", 0,
          f"Missing modules: {', '.join(sorted(missing))} — system requires exactly 5 modules (Law 13).",
          f"Create the missing module directories with proper structure (routers/, serializers/).")
    if extra:
        f(13, "Structure", "medium", "modules/", 0,
          f"Unexpected modules: {', '.join(sorted(extra))} — not in expected 5 modules (Law 13).",
          f"Review whether these modules should be merged into existing ones.")


# ══════════════════════════════════════════════════════════════
# LAW 17: Cross-domain → events/ports only
# ══════════════════════════════════════════════════════════════

def check_law_17_cross_domain_events_ports_files():
    """Each domain must have events.py and ports.py files."""
    for domain_name, files in DOMAINS.items():
        has_events = any(rel(p).endswith("/events.py") for p in files)
        has_ports = any(rel(p).endswith("/ports.py") for p in files)

        if not has_events:
            f(17, "Structure", "medium", f"domains/{domain_name}/", 0,
              f"Domain '{domain_name}' missing events.py — cross-domain writes require events (Law 17).",
              f"Create domains/{domain_name}/events.py defining domain events for cross-domain communication.")
        if not has_ports:
            f(17, "Structure", "medium", f"domains/{domain_name}/", 0,
              f"Domain '{domain_name}' missing ports.py — cross-domain reads require ports (Law 17).",
              f"Create domains/{domain_name}/ports.py exposing read functions for other domains.")


# ══════════════════════════════════════════════════════════════
# LAW 20: country_code = String(2)
# ══════════════════════════════════════════════════════════════

def check_law_20_country_code_type():
    """country_code columns must use String(2) type."""
    for p in MODELS:
        tree, content = ASTAnalyzer.parse(p)
        if not tree:
            continue
        r = rel(p)
        lines = content.split("\n")
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if "country_code" in stripped and "Column" in stripped:
                # Check for String(2) pattern
                if "String(2)" not in stripped and "String(2)" not in (lines[i] if i < len(lines) else ""):
                    # Check if it's a proper String(2) or something else
                    if "String" in stripped:
                        # Extract the String definition
                        if "String(2)" not in stripped:
                            f(20, "Schema", "medium", r, i,
                              f"country_code column does not use String(2) — must be exactly 2-char ISO code (Law 20).",
                              "Change to Column(String(2), ...) for ISO 3166-1 alpha-2 country codes.")
                    else:
                        f(20, "Schema", "high", r, i,
                          f"country_code column missing String(2) type annotation (Law 20).",
                          "Use Column(String(2), nullable=False, index=True) for country_code.")


# ══════════════════════════════════════════════════════════════
# LAW 21: Timestamps = server_default
# ══════════════════════════════════════════════════════════════

def check_law_21_timestamps_server_default():
    """created_at/updated_at columns must have server_default."""
    for p in MODELS:
        tree, content = ASTAnalyzer.parse(p)
        if not tree:
            continue
        r = rel(p)
        lines = content.split("\n")
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if ("created_at" in stripped or "updated_at" in stripped) and "Column" in stripped:
                if "server_default" not in stripped:
                    # Check next few lines for multi-line column def
                    context = "\n".join(lines[max(0, i-1):min(len(lines), i+3)])
                    if "server_default" not in context:
                        col_name = "created_at" if "created_at" in stripped else "updated_at"
                        f(21, "Schema", "medium", r, i,
                          f"{col_name} column missing server_default — timestamps must use server_default=func.now() (Law 21).",
                          f"Add server_default=func.now() to {col_name} column definition.")


# ══════════════════════════════════════════════════════════════
# LAW 23: Audit columns
# ══════════════════════════════════════════════════════════════

def check_law_23_audit_columns():
    """Each model should have created_at, updated_at, country_code, is_deleted."""
    for p in MODELS:
        tree, content = ASTAnalyzer.parse(p)
        if not tree:
            continue
        r = rel(p)
        # Skip __init__ files
        if r.endswith("__init__.py"):
            continue

        classes = ASTAnalyzer.get_classes(tree)
        for cls in classes:
            class_source = ast.get_source_segment(content, cls)
            if not class_source:
                continue
            # Skip base classes and mixins
            if cls.name in ("Base", "DeclarativeBase"):
                continue

            missing = []
            if "created_at" not in class_source:
                missing.append("created_at")
            if "updated_at" not in class_source:
                missing.append("updated_at")
            if "country_code" not in class_source:
                missing.append("country_code")
            if "is_deleted" not in class_source:
                missing.append("is_deleted")

            if missing and len(missing) < 4:
                f(23, "Schema", "low", r, cls.lineno,
                  f"Model '{cls.name}' missing audit columns: {', '.join(missing)} (Law 23).",
                  f"Add {', '.join(missing)} columns to model '{cls.name}' for full audit trail.")


# ══════════════════════════════════════════════════════════════
# LAW 24: No forbidden schemas
# ══════════════════════════════════════════════════════════════

def check_law_24_no_forbidden_schemas():
    """Check model files for forbidden schema values."""
    for p in MODELS:
        tree, content = ASTAnalyzer.parse(p)
        if not tree:
            continue
        r = rel(p)
        lines = content.split("\n")
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if "schema" in stripped and "=" in stripped:
                for schema in FORBIDDEN_SCHEMAS:
                    if f"'{schema}'" in stripped or f'"{schema}"' in stripped:
                        f(24, "Schema", "high", r, i,
                          f"Model uses forbidden schema='{schema}' — must use domain-specific schema (Law 24).",
                          f"Replace schema='{schema}' with schema='<domain_name>' matching the owning domain.")


# ══════════════════════════════════════════════════════════════
# LAW 25: Shift files first
# ══════════════════════════════════════════════════════════════

def check_law_25_shift_files_first():
    """Check for files in wrong locations that need migration."""
    # Check for root-level forbidden folders
    forbidden_root = ["utils", "routers", "controllers", "services", "db"]
    for folder in forbidden_root:
        folder_path = ROOT / folder
        if folder_path.exists() and folder_path.is_dir():
            py_files = list(folder_path.rglob("*.py"))
            if py_files:
                f(25, "Migration", "high", f"backend/{folder}/", 0,
                  f"Root-level folder '{folder}/' exists with {len(py_files)} files — must be migrated to proper location (Law 25).",
                  f"Move contents of backend/{folder}/ to the correct domain or infrastructure location.")


# ══════════════════════════════════════════════════════════════
# LAW 26: Backward-compat shims
# ══════════════════════════════════════════════════════════════

def check_law_26_backward_compat_shims():
    """Check for re-export patterns in infrastructure/utils/ that indicate shims."""
    utils_dir = ROOT / "infrastructure" / "utils"
    if not utils_dir.exists():
        return

    for p in utils_dir.glob("*.py"):
        if p.name == "__init__.py":
            continue
        tree, content = ASTAnalyzer.parse(p)
        if not tree:
            continue
        r = rel(p)
        imports = ASTAnalyzer.get_imports(tree)
        # Check for re-export patterns: importing and re-exporting from same module
        for imp in imports['from']:
            module = imp['module']
            for name in imp['names']:
                # If the file imports X and also has X in __all__ or just passes through
                if name in content and f"def {name}" not in content and f"class {name}" not in content:
                    # This is a re-export shim
                    f(26, "Migration", "low", r, imp['lineno'],
                      f"Potential backward-compat shim: re-exports '{name}' from '{module}' (Law 26).",
                      "Remove shim after all imports are updated to the canonical location.")
                    break


# ══════════════════════════════════════════════════════════════
# LAW 30: Graceful degradation
# ══════════════════════════════════════════════════════════════

def check_law_30_graceful_degradation():
    """Providers must have HAS_ flags and domains must check them."""
    # Check providers have HAS_ flags
    for p in PROVIDERS:
        if p.name == "__init__.py":
            continue
        content = read(p)
        if not content:
            continue
        r = rel(p)
        if "def " in content and "HAS_" not in content:
            f(30, "Provider", "medium", r, 1,
              f"Provider '{p.name}' missing HAS_<SDK> availability flag — domains need this for graceful degradation (Law 30).",
              "Add HAS_<SDK> = True/False flag. Domains check this before calling provider functions.")

    # Check domains check HAS_ flags before using providers
    for domain_name, files in DOMAINS.items():
        for p in files:
            if "/services/" not in rel(p):
                continue
            tree, content = ASTAnalyzer.parse(p)
            if not tree:
                continue
            r = rel(p)
            imports = ASTAnalyzer.get_imports(tree)
            uses_provider = False
            for imp in imports['from']:
                if imp['module'].startswith("providers."):
                    uses_provider = True
                    break
            if uses_provider and "HAS_" not in content:
                f(30, "Architecture", "medium", r, 1,
                  f"Domain service imports providers but doesn't check HAS_ flags — must degrade gracefully (Law 30).",
                  "Check HAS_<SDK> flag before calling provider functions. Provide fallback behavior when SDK unavailable.")
                break


# ══════════════════════════════════════════════════════════════
# LAW 32: No hardcoded secrets (additional checks beyond PatternMatcher)
# ══════════════════════════════════════════════════════════════

def check_law_32_no_hardcoded_secrets():
    """Additional checks for JWT secrets, API keys in config files."""
    # Check config files for hardcoded secrets
    config_files = list((ROOT / "infrastructure").glob("config*.py"))
    config_files.extend(ROOT.glob("*.env*"))

    for p in config_files:
        if p.name.endswith(".env.example") or p.name.endswith(".env.template"):
            continue
        content = read(p)
        if not content:
            continue
        r = rel(p)
        lines = content.split("\n")
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            # Check for hardcoded JWT secrets
            if re.search(r'(?:SECRET_KEY|JWT_SECRET|PASSWORD)\s*=\s*["\'][^"\']{8,}["\']', stripped):
                if "os.getenv" not in stripped and "os.environ" not in stripped and "settings." not in stripped:
                    f(32, "Security", "critical", r, i,
                      "Hardcoded secret in config file — must use environment variables (Law 32).",
                      "Move secret to environment variable: os.getenv('SECRET_KEY').")


# ══════════════════════════════════════════════════════════════
# LAW 33: Token type verification
# ══════════════════════════════════════════════════════════════

def check_law_33_token_type_verification():
    """JWT decode functions must verify 'type' claim."""
    auth_files = [p for p in ALL_PY if "auth" in rel(p).lower() or "token" in rel(p).lower() or "jwt" in rel(p).lower()]

    for p in auth_files:
        tree, content = ASTAnalyzer.parse(p)
        if not tree:
            continue
        r = rel(p)
        lines = content.split("\n")
        # Find jwt.decode calls
        for i, line in enumerate(lines, 1):
            if "jwt.decode" in line or "jwt.decode" in lines[i-1] if i > 1 else False:
                # Check surrounding context for type verification
                context_start = max(0, i - 3)
                context_end = min(len(lines), i + 10)
                context = "\n".join(lines[context_start:context_end])
                if 'type' not in context and 'payload.get' not in context:
                    f(33, "Security", "high", r, i,
                      "jwt.decode() call without type claim verification — must verify 'type' claim (Law 33).",
                      "Add type verification: if payload.get('type') != 'access': raise HTTPException(...).")


# ══════════════════════════════════════════════════════════════
# LAW 34: Parameterized SQL (AST-based f-string detection)
# ══════════════════════════════════════════════════════════════

def check_law_34_parameterized_sql():
    """AST-based detection of f-strings in SQL contexts."""
    for p in ALL_PY:
        if p.name == "__init__.py":
            continue
        tree, content = ASTAnalyzer.parse(p)
        if not tree:
            continue
        r = rel(p)
        # Look for f-strings containing SQL keywords
        for node in ast.walk(tree):
            if isinstance(node, ast.JoinedStr):  # f-string
                # Check if any part contains SQL keywords
                for value in node.values:
                    if isinstance(value, ast.Constant) and isinstance(value.value, str):
                        if re.search(r'\b(?:SELECT|INSERT|UPDATE|DELETE|WHERE|FROM|JOIN)\b', value.value, re.IGNORECASE):
                            f(34, "Security", "critical", r, node.lineno,
                              "SQL query built with f-string interpolation — SQL injection risk (Law 34).",
                              "Use parameterized queries with text() and bind parameters instead of f-strings.")
                            break


# ══════════════════════════════════════════════════════════════
# LAW 35: CSRF active
# ══════════════════════════════════════════════════════════════

def check_law_35_csrf_active():
    """Check middleware for CSRF enforcement."""
    csrf_found = False
    csrf_in_orchestrator = False

    for p in MIDDLEWARE_FILES:
        content = read(p)
        if "csrf" in content.lower():
            csrf_found = True
            break

    # Check if CSRF is registered in orchestrator
    orchestrator_path = ROOT / "middleware" / "orchestrator.py"
    if orchestrator_path.exists():
        content = read(orchestrator_path)
        if "CSRFMiddleware" in content or "csrf" in content.lower():
            csrf_in_orchestrator = True

    if not csrf_found:
        f(35, "Security", "high", "middleware/", 0,
          "No CSRF middleware found — CSRF protection required for state-changing endpoints (Law 35).",
          "Create middleware/csrf_middleware.py implementing double-submit cookie pattern.")
    elif not csrf_in_orchestrator:
        f(35, "Security", "high", "middleware/orchestrator.py", 0,
          "CSRF middleware exists but not registered in orchestrator — not active (Law 35).",
          "Add CSRFMiddleware to the middleware pipeline in orchestrator.py.")


# ══════════════════════════════════════════════════════════════
# LAW 36: Security headers
# ══════════════════════════════════════════════════════════════

def check_law_36_security_headers():
    """Check middleware for security headers (CSP, HSTS, etc.)."""
    headers_found = False
    required_headers = ["X-Content-Type-Options", "X-Frame-Options", "Strict-Transport-Security"]
    missing_headers = []

    for p in MIDDLEWARE_FILES:
        content = read(p)
        if "security" in p.name.lower() or "header" in p.name.lower():
            headers_found = True
            for header in required_headers:
                if header not in content:
                    missing_headers.append(header)

    if not headers_found:
        f(36, "Security", "high", "middleware/", 0,
          "No security headers middleware found — CSP, HSTS, X-Frame-Options required (Law 36).",
          "Create middleware/security_headers.py with CSP, HSTS, X-Frame-Options, X-Content-Type-Options headers.")
    elif missing_headers:
        f(36, "Security", "medium", "middleware/security_headers.py", 0,
          f"Security headers middleware missing: {', '.join(missing_headers)} (Law 36).",
          f"Add {', '.join(missing_headers)} to security headers middleware.")


# ══════════════════════════════════════════════════════════════
# LAW 37: Rate limit fails closed
# ══════════════════════════════════════════════════════════════

def check_law_37_rate_limit_fails_closed():
    """Check rate limiter configuration for fail-closed behavior."""
    rate_limit_files = [p for p in ALL_PY if "rate" in rel(p).lower() and "limit" in rel(p).lower()]

    for p in rate_limit_files:
        content = read(p)
        if not content:
            continue
        r = rel(p)
        # Check for fail-open patterns (returning early on Redis failure)
        if "except" in content and ("return" in content or "pass" in content):
            if "fail" not in content.lower() or "closed" not in content.lower():
                f(37, "Security", "medium", r, 1,
                  "Rate limiter may fail open on Redis errors — must fail closed (Law 37).",
                  "On Redis failure, deny the request (fail closed) rather than allow it (fail open).")


# ══════════════════════════════════════════════════════════════
# LAW 38: Password handling
# ══════════════════════════════════════════════════════════════

def check_law_38_password_handling():
    """Check for password truncation patterns (bcrypt 72-byte limit)."""
    auth_files = [p for p in ALL_PY if "auth" in rel(p).lower() or "password" in rel(p).lower()]

    for p in auth_files:
        content = read(p)
        if not content:
            continue
        r = rel(p)
        # Check for bcrypt usage without length check
        if "bcrypt" in content or "hashpw" in content:
            if "len(password" not in content and "72" not in content:
                f(38, "Security", "medium", r, 1,
                  "Password hashing without length validation — bcrypt truncates at 72 bytes (Law 38).",
                  "Add password length check before hashing: if len(password) > 72: raise ValueError.")


# ══════════════════════════════════════════════════════════════
# LAW 39: No duplicate auth
# ══════════════════════════════════════════════════════════════

def check_law_39_no_duplicate_auth():
    """Check for duplicate auth implementations across modules."""
    auth_implementations = defaultdict(list)

    for p in ALL_PY:
        content = read(p)
        if not content:
            continue
        r = rel(p)
        # Look for auth function definitions
        if re.search(r'def\s+(?:get_current_user|verify_token|authenticate)', content):
            # Extract function name
            match = re.search(r'def\s+(get_current_user|verify_token|authenticate\w*)', content)
            if match:
                func_name = match.group(1)
                auth_implementations[func_name].append(r)

    for func_name, files in auth_implementations.items():
        if len(files) > 1:
            f(39, "Architecture", "high", files[0], 0,
              f"Duplicate auth implementation '{func_name}' found in {len(files)} files: {', '.join(files[:3])} (Law 39).",
              f"Consolidate '{func_name}' into a single canonical implementation in infrastructure/utils/auth.py.")


# ══════════════════════════════════════════════════════════════
# LAW 40: CORS origin validation
# ══════════════════════════════════════════════════════════════

def check_law_40_cors_origin_validation():
    """Check CORS middleware for origin validation."""
    cors_found = False
    origin_validation = False

    for p in ALL_PY:
        content = read(p)
        if not content:
            continue
        r = rel(p)
        if "CORSMiddleware" in content or "cors" in r.lower():
            cors_found = True
            # Check for origin validation (not allow_all_origins)
            if "allow_origins" in content and "*" not in content:
                origin_validation = True
            if "allow_all_origins" in content or "allow_origins=['*']" in content:
                f(40, "Security", "high", r, 1,
                  "CORS allows all origins — must validate against allowlist (Law 40).",
                  "Replace allow_all_origins=True with explicit allow_origins list from configuration.")

    if not cors_found:
        f(40, "Security", "medium", "middleware/", 0,
          "No CORS middleware found — origin validation required for API security (Law 40).",
          "Add CORSMiddleware with explicit allow_origins list from configuration.")


# ══════════════════════════════════════════════════════════════
# LAW 41: WebSocket auth
# ══════════════════════════════════════════════════════════════

def check_law_41_websocket_auth():
    """Check WebSocket endpoints for JWT verification."""
    ws_files = [p for p in ALL_PY if "websocket" in rel(p).lower() or "ws_" in p.name.lower()]

    for p in ws_files:
        content = read(p)
        if not content:
            continue
        r = rel(p)
        # Look for WebSocket endpoint handlers
        if "WebSocket" in content and "async def" in content:
            # Check for auth verification
            if "jwt" not in content.lower() and "token" not in content.lower() and "auth" not in content.lower():
                f(41, "Security", "high", r, 1,
                  "WebSocket endpoint without JWT verification — must authenticate connections (Law 41).",
                  "Add JWT verification in WebSocket connect handler before accepting connections.")


# ══════════════════════════════════════════════════════════════
# LAW 42: Input validation
# ══════════════════════════════════════════════════════════════

def check_law_42_input_validation():
    """Check public endpoints for Pydantic schemas."""
    for p in ROUTERS:
        content = read(p)
        if not content:
            continue
        r = rel(p)
        lines = content.split("\n")
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            # Look for endpoint definitions
            if re.match(r'@(app|router)\.(post|put|patch)\(', stripped):
                # Check for Pydantic schema in the endpoint signature
                context = "\n".join(lines[i:min(len(lines), i+5)])
                if "BaseModel" not in context and "schema" not in context.lower() and "=" not in context:
                    f(42, "Security", "medium", r, i,
                      "State-changing endpoint missing Pydantic request schema — must validate input (Law 42).",
                      "Add Pydantic request schema as parameter: async def endpoint(data: RequestSchema).")


# ══════════════════════════════════════════════════════════════
# LAW 43: Security event logging
# ══════════════════════════════════════════════════════════════

def check_law_43_security_event_logging():
    """Check for logging of auth failures, 403s, rate limits."""
    security_events = {
        "auth_failure": ["401", "invalid_token", "authentication_failed"],
        "forbidden": ["403", "forbidden", "permission_denied"],
        "rate_limit": ["429", "rate_limit", "too_many_requests"],
    }

    for event_type, keywords in security_events.items():
        found = False
        for p in ALL_PY:
            content = read(p)
            if not content:
                continue
            if any(kw in content.lower() for kw in keywords):
                if "logger" in content or "logging" in content:
                    found = True
                    break

        if not found:
            f(43, "Security", "medium", "infrastructure/", 0,
              f"No logging found for {event_type} events — security events must be logged (Law 43).",
              f"Add logging for {event_type} events using structlog logger.")


# ══════════════════════════════════════════════════════════════
# LAW 44: Dependency scanning
# ══════════════════════════════════════════════════════════════

def check_law_44_dependency_scanning():
    """Check CI config for dependency scanning."""
    ci_dir = ROOT.parent / ".github" / "workflows"
    if not ci_dir.exists():
        f(44, "Security", "medium", ".github/workflows/", 0,
          "No CI workflows directory found — dependency scanning required in CI (Law 44).",
          "Create CI workflow with dependency scanning (e.g., safety, pip-audit, or dependabot).")
        return

    ci_files = list(ci_dir.glob("*.yml")) + list(ci_dir.glob("*.yaml"))
    has_dep_scan = False
    for ci_file in ci_files:
        content = read(ci_file)
        if any(tool in content.lower() for tool in ["safety", "pip-audit", "dependabot", "snyk", "trivy"]):
            has_dep_scan = True
            break

    if not has_dep_scan:
        f(44, "Security", "medium", ".github/workflows/", 0,
          "CI workflows missing dependency scanning step — required for vulnerability detection (Law 44).",
          "Add dependency scanning to CI: pip install safety && safety check, or use pip-audit.")


# ══════════════════════════════════════════════════════════════
# MASTER RUN FUNCTION
# ══════════════════════════════════════════════════════════════

def run_checks():
    """Run all law checks for laws 1-50."""
    check_law_1_arrows_point_down()
    check_law_3_cross_domain_events_ports()
    check_law_4_features_single_sourced()
    check_law_5_country_orthogonal()
    check_law_7_allowlist_only_shrinks()
    check_law_8_router_structure()
    check_law_9_tools_in_providers()
    check_law_10_kernel_pure()
    check_law_12_fifteen_domains()
    check_law_13_five_modules()
    check_law_17_cross_domain_events_ports_files()
    check_law_20_country_code_type()
    check_law_21_timestamps_server_default()
    check_law_23_audit_columns()
    check_law_24_no_forbidden_schemas()
    check_law_25_shift_files_first()
    check_law_26_backward_compat_shims()
    check_law_30_graceful_degradation()
    check_law_32_no_hardcoded_secrets()
    check_law_33_token_type_verification()
    check_law_34_parameterized_sql()
    check_law_35_csrf_active()
    check_law_36_security_headers()
    check_law_37_rate_limit_fails_closed()
    check_law_38_password_handling()
    check_law_39_no_duplicate_auth()
    check_law_40_cors_origin_validation()
    check_law_41_websocket_auth()
    check_law_42_input_validation()
    check_law_43_security_event_logging()
    check_law_44_dependency_scanning()
