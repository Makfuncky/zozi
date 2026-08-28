#!/usr/bin/env python3
"""
ZOZI Audit — Section Checkers for Laws 1-50.
Each function checks a category of architecture laws using the global helpers
(f, read, rel, read_lines, parse_ast, etc.) defined in full_system_audit.py.

Called by main() after index_files() has populated the global file lists.
"""

import re
import ast
from pathlib import Path

# ══════════════════════════════════════════════════════════════
# LAW CATEGORY 1: ARCHITECTURE (Laws 1-7)
# ══════════════════════════════════════════════════════════════

def check_section_12_1():
    """Laws 1-7: Architecture — dependency direction, thin routers, cross-domain, features, RLS, schema, allowlist."""
    _law_1_dependency_direction()
    _law_2_thin_routers()
    _law_3_cross_domain_events_ports()
    _law_4_features_single_sourced()
    _law_5_country_orthogonal()
    _law_6_schema_discipline()
    _law_7_allowlist_only_shrinks()


def _law_1_dependency_direction():
    """Law 1: Arrows point down only. modules → domains → infrastructure → kernel."""
    # Forbidden import patterns: (source_prefix, forbidden_import_prefix)
    forbidden = [
        # infrastructure importing from higher layers
        ("infrastructure", "domains."),
        ("infrastructure", "modules."),
        ("infrastructure", "rbac."),
        ("infrastructure", "providers."),
        # kernel importing from anything above it
        ("kernel", "domains."),
        ("kernel", "modules."),
        ("kernel", "rbac."),
        ("kernel", "providers."),
        ("kernel", "infrastructure."),
    ]

    for file_list, prefix in [(INFRA, "infrastructure"), (KERNEL, "kernel")]:
        for p in file_list:
            content = read(p)
            if not content:
                continue
            r = rel(p)
            for _, forbidden_prefix in forbidden:
                if r.startswith(prefix + "/") and has_import_from(content, forbidden_prefix):
                    # Find the specific line
                    for i, line in enumerate(content.split("\n"), 1):
                        if re.search(rf'from\s+{re.escape(forbidden_prefix)}', line) or \
                           re.search(rf'import\s+{re.escape(forbidden_prefix)}', line):
                            f(1, "Architecture", "critical", r, i,
                              f"Infrastructure/kernel file imports from '{forbidden_prefix}' — "
                              f"violates dependency direction (Law 1).",
                              f"Remove the import from '{forbidden_prefix}'. Use events/ports for cross-layer "
                              f"communication. Move shared logic to kernel/ or infrastructure/.")
                            break

    # Domains importing from modules
    for domain_name, files in DOMAINS.items():
        for p in files:
            content = read(p)
            if not content:
                continue
            r = rel(p)
            if has_import_from(content, "modules."):
                for i, line in enumerate(content.split("\n"), 1):
                    if re.search(r'from\s+modules\.', line):
                        f(1, "Architecture", "critical", r, i,
                          f"Domain '{domain_name}' imports from 'modules.' — domains must never "
                          f"import modules (Law 1).",
                          "Remove the module import. Domains are the 'what' layer; they must not "
                          "depend on the 'who' layer. Use dependency inversion if needed.")
                        break


def _law_2_thin_routers():
    """Law 2: Routers = auth + require_feature + ONE service call. No DB writes, no business logic."""
    db_patterns = [
        r'\.query\s*\(',
        r'\.execute\s*\(',
        r'\.add\s*\(',
        r'\.commit\s*\(',
        r'\.delete\s*\(',
        r'session\.',
        r'db\.session',
        r'AsyncSession',
    ]
    business_logic_patterns = [
        r'if\s+.*(?:calc|compute|total|price|discount|tax|fee)',
        r'(?:calc|compute|total|price|discount|tax|fee)\s*=',
        r'for\s+.*\s+in\s+.*\.query',
        r'while\s+.*(?:process|handle|retry)',
    ]

    for p in ROUTERS:
        content = read(p)
        if not content:
            continue
        r = rel(p)
        lines = content.split("\n")
        line_count = len(lines)

        # Check router length
        if line_count > 100:
            f(2, "Architecture", "medium", r, 0,
              f"Router has {line_count} lines (limit: 100). Likely contains business logic.",
              "Extract business logic into a domain service. Router should only: authenticate, "
              "check features, call one service, return response.")

        # Check for DB operations in routers
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped.startswith("#") or stripped.startswith('"""') or stripped.startswith("'''"):
                continue
            for pat in db_patterns:
                if re.search(pat, line):
                    f(2, "Architecture", "high", r, i,
                      f"Router contains DB operation pattern '{pat.strip()}' — routers must not "
                      f"access the database directly (Law 2).",
                      "Move DB operations to a domain service. Router should call service methods only.")
                    break

        # Check for business logic patterns
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            for pat in business_logic_patterns:
                if re.search(pat, line, re.IGNORECASE):
                    f(2, "Architecture", "medium", r, i,
                      f"Router contains business logic pattern — calculation or data processing "
                      f"belongs in services (Law 2).",
                      "Move business logic to domains/{domain}/services/. "
                      "Router should be a thin pass-through.")
                    break


def _law_3_cross_domain_events_ports():
    """Law 3: Cross-domain WRITES via events.py/subscribers.py. READS via ports.py only."""
    domain_names = set(DOMAINS.keys())

    for domain_name, files in DOMAINS.items():
        for p in files:
            # Skip ports.py and events.py themselves
            if p.name in ("ports.py", "events.py", "subscribers.py"):
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
                # Check for imports from other domains
                for other_domain in domain_names:
                    if other_domain == domain_name:
                        continue
                    # Match: from domains.<other>. or import domains.<other>.
                    if re.search(rf'from\s+domains\.{re.escape(other_domain)}\.', line) or \
                       re.search(rf'import\s+domains\.{re.escape(other_domain)}\.', line):
                        f(3, "Architecture", "high", r, i,
                          f"Domain '{domain_name}' directly imports from domain '{other_domain}' — "
                          f"cross-domain reads must use ports.py, writes must use events.py (Law 3).",
                          f"For reads: create a function in domains/{other_domain}/ports.py and call it. "
                          f"For writes: emit an event in events.py and handle it in subscribers.py.")
                        break


def _law_4_features_single_sourced():
    """Law 4: Permission atoms in domains/*/features.py. Aggregated by rbac/catalog.py."""
    for domain_name, files in DOMAINS.items():
        has_features = any(p.name == "features.py" for p in files)
        if not has_features:
            f(4, "Architecture", "medium", f"domains/{domain_name}", 0,
              f"Domain '{domain_name}' is missing features.py — permission atoms must be "
              f"single-sourced per domain (Law 4).",
              f"Create domains/{domain_name}/features.py with permission atom constants. "
              f"Register them in rbac/catalog.py.")


def _law_5_country_orthogonal():
    """Law 5: RLS session context + country_staff_assignments."""
    # Check main.py for instrument_rls() call
    main_files = list(ROOT.glob("main.py")) + list(ROOT.glob("app.py"))
    main_files += list(ROOT.glob("orchestrator.py"))

    rls_instrumented = False
    for mf in main_files:
        if mf.exists():
            content = read(mf)
            if "instrument_rls" in content:
                rls_instrumented = True
                break

    if not rls_instrumented:
        f(5, "Architecture", "high", "backend/main.py", 0,
          "instrument_rls() is not called in main.py — RLS session context must be established "
          "at application startup (Law 5).",
          "Call instrument_rls() in main.py startup. Ensure RLS middleware is active.")

    # Check for RLS middleware
    rls_middleware_exists = False
    for p in MIDDLEWARE_FILES:
        content = read(p)
        if content and "rls" in content.lower():
            rls_middleware_exists = True
            break

    if not rls_middleware_exists:
        f(5, "Architecture", "high", "backend/middleware", 0,
          "No RLS middleware found — country-based row-level security requires middleware (Law 5).",
          "Create middleware/rls_middleware.py that sets RLS session context per request.")


def _law_6_schema_discipline():
    """Law 6: Every table in domain Postgres schema. Alembic is only schema source."""
    # Check for OFFSET in raw SQL (schema discipline violation indicator)
    for p in ALL_PY:
        content = read(p)
        if not content:
            continue
        r = rel(p)
        # Skip migration files
        if "alembic" in r or "migration" in r.lower():
            continue
        lines = content.split("\n")
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            if re.search(r'\bOFFSET\s+\d+', line, re.IGNORECASE) and \
               re.search(r'\b(SELECT|SQL|query|execute)', line, re.IGNORECASE):
                f(6, "Architecture", "low", r, i,
                  "Raw SQL with OFFSET detected — schema discipline requires using domain "
                  "schemas and Alembic for schema changes (Law 6).",
                  "Use SQLAlchemy ORM with domain-specific schemas. Schema changes go through Alembic only.")
                break


def _law_7_allowlist_only_shrinks():
    """Law 7: DOMAIN_ALLOWLIST.yaml tracks temporary cross-domain imports."""
    allowlist_path = ROOT / "DOMAIN_ALLOWLIST.yaml"
    if not allowlist_path.exists():
        f(7, "Architecture", "medium", "backend/DOMAIN_ALLOWLIST.yaml", 0,
          "DOMAIN_ALLOWLIST.yaml does not exist — temporary cross-domain imports must be "
          "tracked in an allowlist that only shrinks (Law 7).",
          "Create backend/DOMAIN_ALLOWLIST.yaml listing all temporary cross-domain imports. "
          "CI must verify the list only shrinks over time.")


# ══════════════════════════════════════════════════════════════
# LAW CATEGORY 2: STRUCTURE (Laws 8-13)
# ══════════════════════════════════════════════════════════════

def check_section_12_2():
    """Laws 8-13: Structure — router layout, tools in providers, kernel purity, provider SDKs, domain/module counts."""
    _law_8_router_structure()
    _law_9_tools_in_providers()
    _law_10_kernel_is_pure()
    _law_11_providers_wrap_sdks()
    _law_12_fifteen_domains()
    _law_13_five_modules()


def _law_8_router_structure():
    """Law 8: modules/{m}/routers/{d}.py — one file per domain per module."""
    expected_modules = {"admin", "customer", "employee", "logistics", "supplier"}
    expected_domains = [
        "accounts", "analytics", "audit", "catalog", "comms", "country",
        "customers", "finance", "governance", "hr", "logistics", "orders",
        "payments", "promotions", "security", "suppliers"
    ]

    for module_name in expected_modules:
        module_router_dir = ROOT / "modules" / module_name / "routers"
        if not module_router_dir.exists():
            f(8, "Structure", "medium", f"modules/{module_name}/routers", 0,
              f"Module '{module_name}' has no routers/ directory — each module should have "
              f"routers for multiple domains (Law 8).",
              f"Create modules/{module_name}/routers/ with one file per domain: "
              f"modules/{module_name}/routers/{{domain}}.py")
            continue

        # Check that routers exist for multiple domains
        router_files = [f for f in module_router_dir.glob("*.py") if f.name != "__init__.py"]
        if len(router_files) < 2:
            f(8, "Structure", "low", f"modules/{module_name}/routers", 0,
              f"Module '{module_name}' has fewer than 2 router files — expected routers for "
              f"multiple domains (Law 8).",
              f"Add router files for each domain the module serves: "
              f"modules/{module_name}/routers/{{domain}}.py")


def _law_9_tools_in_providers():
    """Law 9: All tools code in providers/ai, providers/image. domains/media should not exist."""
    media_domain = ROOT / "domains" / "media"
    if media_domain.exists():
        f(9, "Structure", "high", "domains/media", 0,
          "domains/media exists — media/AI tools must be in providers/, not domains/ (Law 9).",
          "Move all code from domains/media to providers/image or providers/ai. "
          "domains/media should not exist.")


def _law_10_kernel_is_pure():
    """Law 10: kernel/ contains ONLY pure business primitives. No imports from domains/modules/rbac/providers/infrastructure."""
    forbidden_prefixes = ["domains.", "modules.", "rbac.", "providers.", "infrastructure."]

    for p in KERNEL:
        content = read(p)
        if not content:
            continue
        r = rel(p)
        lines = content.split("\n")
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            for prefix in forbidden_prefixes:
                if re.search(rf'from\s+{re.escape(prefix)}', line) or \
                   re.search(rf'import\s+{re.escape(prefix)}', line):
                    f(10, "Structure", "critical", r, i,
                      f"Kernel file imports from '{prefix}' — kernel must contain only pure "
                      f"business primitives (Law 10).",
                      f"Remove the import. kernel/ must be self-contained with no dependencies on "
                      f"domains, modules, rbac, providers, or infrastructure.")
                    break


def _law_11_providers_wrap_sdks():
    """Law 11: A provider wraps exactly one external SDK. No business logic, no domain imports."""
    for p in PROVIDERS:
        content = read(p)
        if not content:
            continue
        r = rel(p)
        lines = content.split("\n")

        # Check for domain imports
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            if has_import_from(content, "domains."):
                for j, l in enumerate(lines, 1):
                    if re.search(r'from\s+domains\.', l):
                        f(11, "Structure", "critical", r, j,
                          "Provider imports from domains/ — providers must only wrap external SDKs "
                          "and must not import domain code (Law 11).",
                          "Remove domain imports. Providers are pure SDK wrappers. "
                          "Business logic belongs in domains/*/services/.")
                        break
                break

        # Check for business logic patterns (calculations, conditionals on domain data)
        has_business_logic = False
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            if re.search(r'(?:if\s+.*(?:status|type|role|permission|amount|price|discount))', line):
                has_business_logic = True
                f(11, "Structure", "medium", r, i,
                  "Provider contains business logic pattern — providers must only wrap SDKs (Law 11).",
                  "Move business logic to a domain service. Provider should only expose SDK methods.")
                break


def _law_12_fifteen_domains():
    """Law 12: Fixed set of 15 domains."""
    expected_domains = {
        "accounts", "analytics", "audit", "catalog", "comms", "country",
        "customers", "finance", "governance", "hr", "logistics", "orders",
        "promotions", "security", "suppliers"
    }
    actual_domains = set(DOMAINS.keys())

    missing = expected_domains - actual_domains
    extra = actual_domains - expected_domains

    if missing:
        f(12, "Structure", "high", "backend/domains", 0,
          f"Missing expected domains: {', '.join(sorted(missing))} — Law 12 requires "
          f"exactly 15 domains: {', '.join(sorted(expected_domains))}.",
          f"Create the missing domain directories under domains/.")
    if extra:
        f(12, "Structure", "low", "backend/domains", 0,
          f"Unexpected extra domains: {', '.join(sorted(extra))} — expected exactly 15 domains "
          f"per Law 12.",
          f"Review whether these domains should be merged into existing ones or if Law 12 "
          f"domain list needs updating.")


def _law_13_five_modules():
    """Law 13: Fixed set of 5 modules."""
    expected_modules = {"admin", "customer", "employee", "logistics", "supplier"}

    # Discover modules from filesystem
    modules_dir = ROOT / "modules"
    actual_modules = set()
    if modules_dir.exists():
        actual_modules = {d.name for d in modules_dir.iterdir() if d.is_dir() and not d.name.startswith("_")}

    missing = expected_modules - actual_modules
    extra = actual_modules - expected_modules

    if missing:
        f(13, "Structure", "high", "backend/modules", 0,
          f"Missing expected modules: {', '.join(sorted(missing))} — Law 13 requires "
          f"exactly 5 modules: {', '.join(sorted(expected_modules))}.",
          f"Create the missing module directories under modules/.")
    if extra:
        f(13, "Structure", "low", "backend/modules", 0,
          f"Unexpected extra modules: {', '.join(sorted(extra))} — expected exactly 5 modules "
          f"per Law 13.",
          f"Review whether these modules should be merged or if the law list needs updating.")


# ══════════════════════════════════════════════════════════════
# LAW CATEGORY 3: FILE PLACEMENT (Laws 14-18)
# ══════════════════════════════════════════════════════════════

def check_section_12_3():
    """Laws 14-18: File placement — business logic, API endpoints, SDK wrappers, cross-domain channels, forbidden folders."""
    _law_14_business_logic_in_domains()
    _law_15_api_endpoints_in_modules()
    _law_16_sdk_wrappers_in_providers()
    _law_17_cross_domain_channels()
    _law_18_root_forbidden_folders()


def _law_14_business_logic_in_domains():
    """Law 14: All business logic in domain services."""
    root_services = ROOT / "services"
    if root_services.exists() and root_services.is_dir():
        py_files = safe_rglob(root_services, "*.py")
        if py_files:
            f(14, "File Placement", "high", "backend/services", 0,
              f"Root-level services/ directory exists with {len(py_files)} Python files — "
              f"all business logic must be in domains/*/services/ (Law 14).",
              "Move business logic from backend/services/ to the appropriate domains/{domain}/services/.")


def _law_15_api_endpoints_in_modules():
    """Law 15: Every HTTP endpoint in module router."""
    root_routers = ROOT / "routers"
    if root_routers.exists() and root_routers.is_dir():
        py_files = safe_rglob(root_routers, "*.py")
        if py_files:
            f(15, "File Placement", "high", "backend/routers", 0,
              f"Root-level routers/ directory exists with {len(py_files)} Python files — "
              f"all API endpoints must be in modules/*/routers/ (Law 15).",
              "Move routers from backend/routers/ to modules/{module}/routers/{domain}.py.")


def _law_16_sdk_wrappers_in_providers():
    """Law 16: Every third-party integration under providers/."""
    root_utils = ROOT / "utils"
    if root_utils.exists() and root_utils.is_dir():
        # Check for SDK-related code in root utils
        for p in safe_rglob(root_utils, "*.py"):
            content = read(p)
            if not content:
                continue
            r = rel(p)
            # Check for SDK patterns
            if re.search(r'(?:boto3|stripe|requests|openai|anthropic|sendgrid|twilio)', content):
                f(16, "File Placement", "medium", r, 0,
                  f"Root utils file contains SDK integration code — all third-party integrations "
                  f"must be under providers/ (Law 16).",
                  f"Move SDK wrapper code from {r} to providers/{category}/.")


def _law_17_cross_domain_channels():
    """Law 17: events.py and ports.py are the ONLY cross-domain channels."""
    for domain_name, files in DOMAINS.items():
        has_events = any(p.name == "events.py" for p in files)
        has_ports = any(p.name == "ports.py" for p in files)

        if not has_events and not has_ports:
            f(17, "File Placement", "medium", f"domains/{domain_name}", 0,
              f"Domain '{domain_name}' is missing both events.py and ports.py — cross-domain "
              f"communication requires these channels (Law 17).",
              f"Create domains/{domain_name}/events.py (for writes) and/or "
              f"domains/{domain_name}/ports.py (for reads).")
        elif not has_ports:
            f(17, "File Placement", "low", f"domains/{domain_name}", 0,
              f"Domain '{domain_name}' is missing ports.py — cross-domain reads should go "
              f"through ports.py (Law 17).",
              f"Create domains/{domain_name}/ports.py with read functions for other domains to call.")


def _law_18_root_forbidden_folders():
    """Law 18: utils/, routers/, controllers/, services/, models/, db/ FORBIDDEN at root."""
    forbidden = ["utils", "routers", "controllers", "services", "models", "db"]

    for folder_name in forbidden:
        folder_path = ROOT / folder_name
        if folder_path.exists() and folder_path.is_dir():
            py_files = safe_rglob(folder_path, "*.py")
            if py_files:
                f(18, "File Placement", "high", f"backend/{folder_name}", 0,
                  f"Forbidden root folder '{folder_name}/' exists with {len(py_files)} Python files — "
                  f"this folder must not exist at backend/ root (Law 18).",
                  f"Move contents of backend/{folder_name}/ to the appropriate location: "
                  f"utils → infrastructure/utils/ or kernel/; "
                  f"routers → modules/*/routers/; "
                  f"controllers → modules/*/routers/; "
                  f"services → domains/*/services/; "
                  f"models → domains/*/models/; "
                  f"db → infrastructure/database/.")


# ══════════════════════════════════════════════════════════════
# LAW CATEGORY 4: CODE QUALITY (Laws 19-24)
# ══════════════════════════════════════════════════════════════

def check_section_12_4():
    """Laws 19-24: Code quality — money types, country_code, timestamps, FK ondelete, audit columns, forbidden schemas."""
    _law_19_no_float_for_money()
    _law_20_country_code_string2()
    _law_21_timestamps_server_default()
    _law_22_fk_have_ondelete()
    _law_23_audit_columns()
    _law_24_no_forbidden_schemas()


def _law_19_no_float_for_money():
    """Law 19: Monetary values MUST use Decimal/Numeric. No Column(Float) for money."""
    money_keywords = ["price", "amount", "cost", "fee", "balance", "total", "subtotal",
                      "discount", "tax", "credit", "debit", "payment", "refund", "salary",
                      "wage", "revenue", "profit", "margin", "commission", "rate"]
    exclude_keywords = ["latitude", "longitude", "lat", "lon", "lng", "accuracy",
                        "rating", "score", "weight", "height", "width", "depth"]

    for p in MODELS:
        content = read(p)
        if not content:
            continue
        r = rel(p)
        lines = content.split("\n")

        for i, line in enumerate(lines, 1):
            if "Column(" in line and "Float" in line:
                # Check if it's a money-related column
                line_lower = line.lower()
                is_money = any(kw in line_lower for kw in money_keywords)
                is_excluded = any(kw in line_lower for kw in exclude_keywords)

                if is_money and not is_excluded:
                    f(19, "Code Quality", "high", r, i,
                      f"Column uses Float for monetary value — must use Decimal or Numeric (Law 19).",
                      "Replace Column(Float) with Column(Numeric(12, 2)) for monetary values. "
                      "Float causes rounding errors in financial calculations.")


def _law_20_country_code_string2():
    """Law 20: country_code = String(2) ISO 3166-1 alpha-2."""
    for p in MODELS:
        content = read(p)
        if not content:
            continue
        r = rel(p)
        lines = content.split("\n")

        for i, line in enumerate(lines, 1):
            if "country_code" in line.lower() and "Column" in line:
                # Check for correct type
                if not re.search(r'String\s*\(\s*2\s*\)', line):
                    # Also check for Integer or other wrong types
                    if re.search(r'(Integer|Text|VARCHAR|CHAR\s*\(\s*(?!2\)))', line):
                        f(20, "Code Quality", "medium", r, i,
                          f"country_code column does not use String(2) — must be String(2) "
                          f"for ISO 3166-1 alpha-2 (Law 20).",
                          "Change to Column(String(2)) for country_code.")


def _law_21_timestamps_server_default():
    """Law 21: created_at/updated_at use server_default=func.now()."""
    for p in MODELS:
        content = read(p)
        if not content:
            continue
        r = rel(p)
        lines = content.split("\n")

        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if re.search(r'(created_at|updated_at)\s*=\s*Column', stripped):
                # Check for server_default
                # Look at current and next few lines for server_default
                context = "\n".join(lines[max(0, i-1):min(len(lines), i+3)])
                if "server_default" not in context and "default" not in context:
                    f(21, "Code Quality", "medium", r, i,
                      f"Timestamp column missing server_default — created_at/updated_at must use "
                      f"server_default=func.now() (Law 21).",
                      "Add server_default=func.now() to the Column definition.")


def _law_22_fk_have_ondelete():
    """Law 22: Every ForeignKey declares explicit ondelete."""
    for p in MODELS:
        content = read(p)
        if not content:
            continue
        r = rel(p)
        lines = content.split("\n")

        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if "ForeignKey" in stripped:
                # Check for ondelete in the same line or next few lines
                context = "\n".join(lines[max(0, i-1):min(len(lines), i+3)])
                if "ondelete" not in context:
                    f(22, "Code Quality", "high", r, i,
                      f"ForeignKey missing ondelete clause — every FK must declare explicit "
                      f"ondelete behavior (Law 22).",
                      "Add ondelete='CASCADE', ondelete='SET NULL', or ondelete='RESTRICT' "
                      "to the ForeignKey definition.")


def _law_23_audit_columns():
    """Law 23: Every model has created_at, updated_at, country_code, is_deleted."""
    required_columns = ["created_at", "updated_at", "country_code", "is_deleted"]

    for p in MODELS:
        content = read(p)
        if not content:
            continue
        r = rel(p)

        # Get class names to report which model is missing columns
        tree = parse_ast(p)
        classes = get_classes(tree) if tree else []

        for cls in classes:
            cls_source = get_source_segment(content, cls)
            if not cls_source:
                continue

            cls_name = cls.name
            # Skip base classes and mixins
            if cls_name.startswith("_") or cls_name in ("Base", "DeclarativeBase"):
                continue

            missing = []
            for col in required_columns:
                if col not in cls_source:
                    missing.append(col)

            if missing:
                f(23, "Code Quality", "medium", r, cls.lineno,
                  f"Model '{cls_name}' is missing audit columns: {', '.join(missing)} — "
                  f"every model must have created_at, updated_at, country_code, is_deleted (Law 23).",
                  f"Add the missing columns to model '{cls_name}': "
                  f"created_at=Column(DateTime, server_default=func.now()), "
                  f"updated_at=Column(DateTime, server_default=func.now(), onupdate=func.now()), "
                  f"country_code=Column(String(2)), is_deleted=Column(Boolean, default=False).")


def _law_24_no_forbidden_schemas():
    """Law 24: core, platform, identity FORBIDDEN as schema names."""
    forbidden_schemas = ["core", "platform", "identity"]

    for p in MODELS:
        content = read(p)
        if not content:
            continue
        r = rel(p)
        lines = content.split("\n")

        for i, line in enumerate(lines, 1):
            for schema in forbidden_schemas:
                if re.search(rf'''__tablename__.*schema\s*=\s*['"]{schema}['"]''', line) or \
                   re.search(rf'''__table_args__.*['"]schema['"]\s*:\s*['"]{schema}['"]''', line) or \
                   re.search(rf'''schema\s*=\s*['"]{schema}['"]''', line):
                    f(24, "Code Quality", "high", r, i,
                      f"Forbidden schema name '{schema}' — core, platform, and identity are "
                      f"reserved schema names (Law 24).",
                      f"Use a domain-specific schema name instead of '{schema}'. "
                      f"Each domain should use its own schema.")


# ══════════════════════════════════════════════════════════════
# LAW CATEGORY 5: MIGRATION (Laws 25-29)
# ══════════════════════════════════════════════════════════════

def check_section_migration():
    """Laws 25-29: Migration — file shifting, backward-compat, temp scripts, stubs, registry."""
    _law_25_shift_files_first()
    _law_26_backward_compat_shims()
    _law_27_delete_temp_scripts()
    _law_28_auto_stubs_not_architecture()
    _law_29_registry_not_architecture()


def _law_25_shift_files_first():
    """Law 25: All files to correct domains before reorganization."""
    # Look for _auto_stubs files that indicate incomplete migration
    for p in ALL_PY:
        if "_auto_stubs" in p.name:
            r = rel(p)
            f(25, "Migration", "medium", r, 0,
              f"File '{p.name}' is migration scaffolding — files should be fully shifted to "
              f"correct domains before reorganization (Law 25).",
              f"Complete the migration: move contents of '{r}' to the correct domain service "
              f"and delete the stub file.")


def _law_26_backward_compat_shims():
    """Law 26: Temporary re-exports for relocated files."""
    for p in INFRA:
        if "utils" in rel(p):
            content = read(p)
            if not content:
                continue
            r = rel(p)
            lines = content.split("\n")

            for i, line in enumerate(lines, 1):
                # Detect re-export patterns: from .X import Y or from ..X import Y
                if re.match(r'^\s*from\s+\.+\S+\s+import\s+\w+', line) and i <= 10:
                    # Check if it's a shim (file only has imports)
                    non_empty = [l for l in lines if l.strip() and not l.strip().startswith("#")]
                    if len(non_empty) <= 5:
                        f(26, "Migration", "low", r, i,
                          f"Backward-compat shim detected — temporary re-exports should be "
                          f"removed after migration (Law 26).",
                          f"Remove the re-export shim at '{r}'. Update all imports to point "
                          f"to the new location.")


def _law_27_delete_temp_scripts():
    """Law 27: Root-level fix_*.py, debug_*.py should be removed."""
    for p in ROOT.glob("*.py"):
        if p.name.startswith("fix_") or p.name.startswith("debug_"):
            r = rel(p)
            f(27, "Migration", "low", r, 0,
              f"Temporary script '{p.name}' at backend/ root — fix/debug scripts should be "
              f"removed after use (Law 27).",
              f"Delete '{r}' or move it to scripts/ if it's a permanent utility.")


def _law_28_auto_stubs_not_architecture():
    """Law 28: _auto_stubs.py are migration scaffolding, not architecture."""
    for domain_name, files in DOMAINS.items():
        for p in files:
            if "_auto_stubs" in p.name:
                r = rel(p)
                f(28, "Migration", "medium", r, 0,
                  f"_auto_stubs file in domain '{domain_name}' — these are migration scaffolding "
                  f"and should not be part of the architecture (Law 28).",
                  f"Replace '{r}' with proper domain service code or delete if no longer needed.")


def _law_29_registry_not_architecture():
    """Law 29: Service Registry was removed — registry.py, auto_wire.py should not exist."""
    registry_patterns = ["registry.py", "auto_wire.py", "service_registry.py"]

    for p in ALL_PY:
        if any(pat in p.name for pat in registry_patterns):
            r = rel(p)
            f(29, "Migration", "medium", r, 0,
              f"Service Registry file '{p.name}' found — the Service Registry was removed "
              f"from the architecture (Law 29).",
              f"Delete '{r}'. Service discovery is now handled by direct imports and "
              f"dependency injection.")


# ══════════════════════════════════════════════════════════════
# LAW CATEGORY 6: PROVIDER (Laws 30-31)
# ══════════════════════════════════════════════════════════════

def check_section_provider():
    """Laws 30-31: Provider — graceful degradation, no domain imports."""
    _law_30_graceful_degradation()
    _law_31_no_domain_imports()


def _law_30_graceful_degradation():
    """Law 30: Domains handle missing SDKs via HAS_<SDK> flags."""
    for p in PROVIDERS:
        content = read(p)
        if not content:
            continue
        r = rel(p)

        # Skip __init__.py and test files
        if p.name == "__init__.py" or "test" in p.name:
            continue

        # Check for HAS_ flag pattern
        has_flag = re.search(r'HAS_\w+\s*=\s*(?:True|False)', content)
        if not has_flag:
            # Check if the file imports any external SDK
            sdk_imports = re.findall(r'(?:import|from)\s+(\w+)', content)
            external_sdks = [s for s in sdk_imports if s not in (
                "os", "sys", "json", "re", "typing", "abc", "logging", "pathlib",
                "datetime", "collections", "functools", "contextlib", "asyncio",
                "hashlib", "base64", "io", "enum", "dataclasses", "warnings",
                "types", "urllib", "http", "math", "decimal", "uuid", "string",
                "textwrap", "itertools", "copy", "pprint", "time", "inspect"
            )]

            if external_sdks:
                f(30, "Provider", "medium", r, 0,
                  f"Provider missing HAS_<SDK> flag — domains must gracefully degrade when "
                  f"SDKs are unavailable (Law 30).",
                  f"Add 'HAS_<SDK> = True/False' flag at the top of '{r}'. "
                  f"Wrap SDK imports in try/except and set the flag accordingly.")


def _law_31_no_domain_imports():
    """Law 31: Providers MUST NOT import from domains."""
    for p in PROVIDERS:
        content = read(p)
        if not content:
            continue
        r = rel(p)
        lines = content.split("\n")

        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            if re.search(r'from\s+domains\.', line) or re.search(r'import\s+domains\.', line):
                f(31, "Provider", "critical", r, i,
                  f"Provider imports from domains/ — providers must only wrap external SDKs "
                  f"and must not depend on domain code (Law 31).",
                  f"Remove the domain import from '{r}'. If the provider needs domain data, "
                  f"pass it as function arguments instead of importing domain models.")


# ══════════════════════════════════════════════════════════════
# LAW CATEGORY 7: SECURITY (Laws 32-44)
# ══════════════════════════════════════════════════════════════

def check_section_security():
    """Laws 32-44: Security — secrets, JWT, SQL injection, CSRF, headers, rate limit, passwords, auth, CORS, WebSocket, validation, logging, deps."""
    _law_32_no_hardcoded_secrets()
    _law_33_token_type_verification()
    _law_34_parameterized_sql()
    _law_35_csrf_active()
    _law_36_security_headers()
    _law_37_rate_limit_fails_closed()
    _law_38_password_handling()
    _law_39_no_duplicate_auth()
    _law_40_cors_origin_validation()
    _law_41_websocket_auth()
    _law_42_input_validation()
    _law_43_security_event_logging()
    _law_44_dependency_scanning()


def _law_32_no_hardcoded_secrets():
    """Law 32: JWT keys, API keys from env vars only. No hardcoded secrets."""
    secret_patterns = [
        (r'(?:sk_live|sk_test)_[a-zA-Z0-9]{10,}', "Stripe secret key"),
        (r'(?:pk_live|pk_test)_[a-zA-Z0-9]{10,}', "Stripe public key"),
        (r'(?:password|passwd|pwd)\s*=\s*["\'][^"\']{4,}["\']', "hardcoded password"),
        (r'(?:secret|secret_key|api_key)\s*=\s*["\'][^"\']{8,}["\']', "hardcoded secret"),
        (r'(?:AWS_ACCESS_KEY_ID|AWS_SECRET_ACCESS_KEY)\s*=\s*["\'][^"\']+["\']', "AWS credentials"),
        (r'JWT_SECRET\s*=\s*["\'][^"\']{4,}["\']', "JWT secret"),
        (r'ALGORITHM\s*=\s*["\']HS256["\'].*?SECRET\s*=\s*["\'][^"\']{4,}["\']', "JWT config"),
    ]

    # Exclude test files and .env files
    for p in ALL_PY:
        r = rel(p)
        if "test" in r.lower() or "conftest" in r or "fixture" in r.lower():
            continue
        if "settings" in r.lower() or "config" in r.lower():
            # Settings files may have defaults — only flag non-default patterns
            pass

        content = read(p)
        if not content:
            continue
        lines = content.split("\n")

        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            for pattern, desc in secret_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    # Skip if it's clearly using os.environ or os.getenv
                    if "os.environ" in line or "os.getenv" in line or "config." in line:
                        continue
                    f(32, "Security", "critical", r, i,
                      f"Potential hardcoded {desc} detected — secrets must come from env vars (Law 32).",
                      f"Move the secret to an environment variable. Use os.environ.get('SECRET_NAME') "
                      f"or a settings module that reads from env.")
                    break


def _law_33_token_type_verification():
    """Law 33: JWT decoders verify type claim."""
    for p in ALL_PY:
        content = read(p)
        if not content:
            continue
        r = rel(p)

        # Look for JWT decode without type verification
        if "jwt.decode" in content or "decode_jwt" in content or "verify_token" in content:
            lines = content.split("\n")
            for i, line in enumerate(lines, 1):
                if "jwt.decode" in line or "decode_jwt" in line:
                    # Check surrounding context for type verification
                    context_start = max(0, i - 5)
                    context_end = min(len(lines), i + 10)
                    context = "\n".join(lines[context_start:context_end])

                    if "type" not in context.lower() and "token_type" not in context.lower():
                        f(33, "Security", "high", r, i,
                          f"JWT decode without type claim verification — decoders must verify "
                          f"the 'type' claim to prevent token substitution (Law 33).",
                          f"Add type claim verification after decoding: "
                          f"assert decoded.get('type') == 'access' or 'refresh'.")


def _law_34_parameterized_sql():
    """Law 34: No f-string interpolation in SQL."""
    sql_keywords = ["SELECT", "INSERT", "UPDATE", "DELETE", "DROP", "CREATE", "ALTER", "WHERE"]

    for p in ALL_PY:
        content = read(p)
        if not content:
            continue
        r = rel(p)
        lines = content.split("\n")

        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            # Check for f-strings containing SQL
            if re.search(rf'f["\']', line):
                for kw in sql_keywords:
                    if kw in line.upper():
                        f(34, "Security", "critical", r, i,
                          f"SQL query uses f-string interpolation — must use parameterized queries "
                          f"to prevent SQL injection (Law 34).",
                          f"Replace f-string SQL with parameterized queries: "
                          f"session.execute(text('SELECT * FROM t WHERE id = :id'), {{'id': value}}).")
                        break


def _law_35_csrf_active():
    """Law 35: CSRF middleware active in all environments."""
    csrf_found = False
    csrf_disabled = False

    for p in ALL_PY:
        content = read(p)
        if not content:
            continue
        r = rel(p)

        if "csrf" in content.lower():
            csrf_found = True
            lines = content.split("\n")
            for i, line in enumerate(lines, 1):
                # Check for CSRF disabled
                if re.search(r'(?:csrf_enabled|CSRF_ENABLED|csrf_protect)\s*=\s*False', line) or \
                   re.search(r'(?:disable|skip|bypass).*csrf', line, re.IGNORECASE):
                    csrf_disabled = True
                    f(35, "Security", "high", r, i,
                      f"CSRF middleware is disabled — CSRF protection must be active in all "
                      f"environments (Law 35).",
                      f"Enable CSRF middleware. If disabled for API routes, use token-based "
                      f"auth instead but keep CSRF for browser-based endpoints.")

    if not csrf_found:
        f(35, "Security", "high", "backend/middleware", 0,
          "No CSRF middleware found — CSRF protection must be active (Law 35).",
          "Add CSRF middleware to the application stack. Use fastapi-csrf or similar.")


def _law_36_security_headers():
    """Law 36: CSP, HSTS, X-Frame-Options security headers."""
    required_headers = ["Content-Security-Policy", "Strict-Transport-Security", "X-Frame-Options"]
    found_headers = set()

    for p in MIDDLEWARE_FILES:
        content = read(p)
        if not content:
            continue
        for header in required_headers:
            if header.lower() in content.lower():
                found_headers.add(header)

    missing = set(required_headers) - found_headers
    if missing:
        f(36, "Security", "medium", "backend/middleware", 0,
          f"Missing security headers: {', '.join(missing)} — CSP, HSTS, and X-Frame-Options "
          f"must be set (Law 36).",
          f"Add security headers middleware that sets: "
          f"Content-Security-Policy, Strict-Transport-Security, X-Frame-Options.")


def _law_37_rate_limit_fails_closed():
    """Law 37: Redis unreachable = deny requests (fail closed)."""
    for p in ALL_PY:
        content = read(p)
        if not content:
            continue
        r = rel(p)

        if "rate_limit" in content.lower() or "ratelimit" in content.lower():
            lines = content.split("\n")
            for i, line in enumerate(lines, 1):
                # Check for fail-open patterns
                if re.search(r'(?:except|catch).*(?:redis|connection|timeout)', line, re.IGNORECASE):
                    context_start = max(0, i - 2)
                    context_end = min(len(lines), i + 5)
                    context = "\n".join(lines[context_start:context_end])
                    if re.search(r'(?:pass|continue|allow|return\s+None)', context, re.IGNORECASE):
                        f(37, "Security", "high", r, i,
                          f"Rate limiter may fail open on Redis error — must fail closed (deny "
                          f"requests) when rate limiter is unreachable (Law 37).",
                          f"Change the exception handler to deny requests instead of allowing them. "
                          f"On Redis error, return 429 Too Many Requests.")


def _law_38_password_handling():
    """Law 38: Passwords >72 bytes rejected, never truncated."""
    for p in ALL_PY:
        content = read(p)
        if not content:
            continue
        r = rel(p)
        lines = content.split("\n")

        for i, line in enumerate(lines, 1):
            # Check for password truncation patterns
            if re.search(r'password\s*\[:\s*(\d+)\]', line) or \
               re.search(r'(?:trunc|slice).*password', line, re.IGNORECASE):
                f(38, "Security", "high", r, i,
                  f"Password truncation detected — passwords >72 bytes must be rejected, "
                  f"never truncated (Law 38).",
                  f"Remove truncation. Validate password length and reject if >72 bytes. "
                  f"Use: if len(password) > 72: raise ValueError('Password too long').")


def _law_39_no_duplicate_auth():
    """Law 39: Auth logic in exactly one canonical location."""
    auth_files = []
    for p in ALL_PY:
        content = read(p)
        if not content:
            continue
        r = rel(p)
        # Look for auth-related files
        if "auth" in r.lower() and ("verify" in content.lower() or "authenticate" in content.lower()):
            if "test" not in r.lower():
                auth_files.append(r)

    # Check for auth logic outside canonical locations
    canonical_auth_paths = ["infrastructure/auth", "providers/auth", "middleware/auth"]
    non_canonical = [f for f in auth_files if not any(c in f for c in canonical_auth_paths)]

    if len(non_canonical) > 1:
        f(39, "Security", "medium", ", ".join(non_canonical[:3]), 0,
          f"Multiple auth implementations found: {', '.join(non_canonical[:3])} — auth logic "
          f"must be in exactly one canonical location (Law 39).",
          f"Consolidate auth logic into infrastructure/auth/ or providers/auth/. "
          f"Remove duplicate auth implementations.")


def _law_40_cors_origin_validation():
    """Law 40: Origin validated against allowlist. No allow-all."""
    for p in ALL_PY:
        content = read(p)
        if not content:
            continue
        r = rel(p)
        lines = content.split("\n")

        for i, line in enumerate(lines, 1):
            # Check for CORS allow-all patterns
            if re.search(r'allow_origins\s*=\s*\[\s*["\']\*["\']', line) or \
               re.search(r'allow_origins\s*=\s*["\']\*["\']', line) or \
               re.search(r'Access-Control-Allow-Origin\s*:\s*\*', line):
                f(40, "Security", "high", r, i,
                  f"CORS allows all origins — origin must be validated against an allowlist (Law 40).",
                  f"Replace allow_origins=['*'] with a specific list of allowed origins. "
                  f"Load from environment config.")


def _law_41_websocket_auth():
    """Law 41: WebSocket verifies JWT type claim."""
    for p in ALL_PY:
        content = read(p)
        if not content:
            continue
        r = rel(p)

        if "websocket" in content.lower() or "ws" in content.lower():
            # Check for WebSocket endpoints without JWT verification
            if "WebSocket" in content or "websocket" in content:
                if "jwt" not in content.lower() and "token" not in content.lower():
                    f(41, "Security", "high", r, 0,
                      f"WebSocket endpoint without JWT verification — WebSocket connections must "
                      f"verify JWT type claim (Law 41).",
                      f"Add JWT verification to WebSocket endpoints. Verify the 'type' claim "
                      f"is 'access' before accepting the connection.")


def _law_42_input_validation():
    """Law 42: All public endpoints use Pydantic schemas."""
    for p in ROUTERS:
        content = read(p)
        if not content:
            continue
        r = rel(p)
        lines = content.split("\n")

        for i, line in enumerate(lines, 1):
            # Look for endpoint definitions without Pydantic schemas
            if re.search(r'@(?:app|router)\.(?:get|post|put|delete|patch)\s*\(', line):
                # Check next few lines for body params without Pydantic
                context = "\n".join(lines[i:min(len(lines), i+5)])
                if "Body(" in context and "BaseModel" not in content:
                    # Check if the router file imports from schemas
                    if "from domains" not in content or "schemas" not in content:
                        f(42, "Security", "medium", r, i,
                          f"Endpoint may lack Pydantic schema validation — all public endpoints "
                          f"must use Pydantic schemas for input validation (Law 42).",
                          f"Define a Pydantic schema for the request body and use it as the "
                          f"parameter type.")


def _law_43_security_event_logging():
    """Law 43: Auth failures, 403s logged at WARNING+."""
    security_events = ["403", "401", "forbidden", "unauthorized", "auth_fail", "login_fail"]
    logged_events = set()

    for p in ALL_PY:
        content = read(p)
        if not content:
            continue
        r = rel(p)

        for event in security_events:
            if event in content.lower():
                # Check if it's being logged
                if "logger" in content or "logging" in content:
                    if re.search(r'logger\.(?:warning|error|critical).*{event}', content, re.IGNORECASE):
                        logged_events.add(event)

    missing_logging = set(security_events) - logged_events
    if missing_logging:
        f(43, "Security", "medium", "backend", 0,
          f"Security events may not be logged at WARNING+: {', '.join(missing_logging)} — "
          f"auth failures and 403s must be logged (Law 43).",
          f"Add logging.warning() calls for authentication failures, authorization denials, "
          f"and other security events.")


def _law_44_dependency_scanning():
    """Law 44: Deps scanned for CVEs in CI."""
    ci_files = []
    # Check common CI locations
    ci_paths = [
        ROOT.parent / ".github" / "workflows",
        ROOT.parent / ".gitlab-ci.yml",
        ROOT.parent / "Jenkinsfile",
        ROOT.parent / ".circleci" / "config.yml",
    ]

    for ci_path in ci_paths:
        if ci_path.exists():
            if ci_path.is_dir():
                ci_files.extend(ci_path.glob("*"))
            else:
                ci_files.append(ci_path)

    has_dep_scan = False
    for ci_file in ci_files:
        content = read(ci_file)
        if not content:
            continue
        if re.search(r'(?:safety|pip-audit|dependabot|snyk|trivy|grype|owasp)', content, re.IGNORECASE):
            has_dep_scan = True
            break

    if not has_dep_scan and ci_files:
        f(44, "Security", "medium", "backend", 0,
          f"No dependency vulnerability scanning found in CI — dependencies must be scanned "
          f"for CVEs in CI pipeline (Law 44).",
          f"Add a dependency scanning step to CI: 'pip-audit' or 'safety check' or "
          f"GitHub Dependabot alerts.")
