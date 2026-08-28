# -*- coding: utf-8 -*-
"""
ZOZI Audit — Laws 97-160: Wiring, Technology, Provider, Module, Infrastructure, Domain.

Each check function uses the globally indexed file lists and helpers defined in
full_system_audit.py (f, read, rel, read_lines, parse_ast, get_classes,
get_functions, has_import_from, has_import, ROOT, FRONTEND_ROOT).

This module is loaded by full_system_audit.py which calls each function after
indexing. All functions mutate the global ``findings`` list via ``f()``.
"""

# ══════════════════════════════════════════════════════════════
# SECTION 1: WIRING (Laws 97-106)
# ══════════════════════════════════════════════════════════════

def check_section_wiring():
    """Laws 97-106: Wiring — inter-layer import constraints."""
    _check_kernel_isolation()          # Law 101
    _check_infrastructure_isolation()   # Law 102
    _check_job_wiring()                 # Law 103
    _check_middleware_wiring()          # Law 104
    _check_shared_package_wiring()      # Law 105
    _check_frontend_backend_wiring()    # Law 106


def _check_kernel_isolation():
    """Law 101: kernel/ doesn't import from domains/modules/rbac/providers/jobs/middleware."""
    forbidden_prefixes = [
        "domains.", "modules.", "rbac.", "providers.", "jobs.", "middleware."
    ]
    for p in KERNEL:
        content = read(p)
        if not content:
            continue
        tree = parse_ast(p)
        if not tree:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                for prefix in forbidden_prefixes:
                    if node.module.startswith(prefix):
                        f(101, "wiring", "critical", rel(p), node.lineno,
                          f"kernel/ file imports from forbidden layer: '{node.module}'",
                          f"Remove 'from {node.module} import ...'. kernel/ must not import from domains/modules/rbac/providers/jobs/middleware.")
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    for prefix in forbidden_prefixes:
                        if alias.name.startswith(prefix):
                            f(101, "wiring", "critical", rel(p), node.lineno,
                              f"kernel/ file imports from forbidden layer: '{alias.name}'",
                              f"Remove 'import {alias.name}'. kernel/ must not import from domains/modules/rbac/providers/jobs/middleware.")


def _check_infrastructure_isolation():
    """Law 102: infrastructure/ doesn't import from domains/modules/rbac/providers."""
    forbidden_prefixes = ["domains.", "modules.", "rbac.", "providers."]
    for p in INFRA:
        content = read(p)
        if not content:
            continue
        tree = parse_ast(p)
        if not tree:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                for prefix in forbidden_prefixes:
                    if node.module.startswith(prefix):
                        f(102, "wiring", "critical", rel(p), node.lineno,
                          f"infrastructure/ file imports from upper layer: '{node.module}'",
                          f"Remove 'from {node.module} import ...'. infrastructure/ must not import from domains/modules/rbac/providers.")
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    for prefix in forbidden_prefixes:
                        if alias.name.startswith(prefix):
                            f(102, "wiring", "critical", rel(p), node.lineno,
                              f"infrastructure/ file imports from upper layer: '{alias.name}'",
                              f"Remove 'import {alias.name}'. infrastructure/ must not import from domains/modules/rbac/providers.")


def _check_job_wiring():
    """Law 103: Jobs import from domains/ + infrastructure/ only."""
    forbidden_prefixes = ["modules.", "rbac.", "middleware."]
    for p in JOBS:
        content = read(p)
        if not content:
            continue
        tree = parse_ast(p)
        if not tree:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                for prefix in forbidden_prefixes:
                    if node.module.startswith(prefix):
                        f(103, "wiring", "high", rel(p), node.lineno,
                          f"jobs/ file imports from forbidden layer: '{node.module}'",
                          f"Remove 'from {node.module} import ...'. Jobs may only import from domains/ and infrastructure/.")
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    for prefix in forbidden_prefixes:
                        if alias.name.startswith(prefix):
                            f(103, "wiring", "high", rel(p), node.lineno,
                              f"jobs/ file imports from forbidden layer: '{alias.name}'",
                              f"Remove 'import {alias.name}'. Jobs may only import from domains/ and infrastructure/.")


def _check_middleware_wiring():
    """Law 104: Middleware imports from infrastructure/ + rbac/ only."""
    forbidden_prefixes = ["domains.", "modules.", "providers.", "jobs."]
    for p in MIDDLEWARE_FILES:
        content = read(p)
        if not content:
            continue
        tree = parse_ast(p)
        if not tree:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                for prefix in forbidden_prefixes:
                    if node.module.startswith(prefix):
                        f(104, "wiring", "high", rel(p), node.lineno,
                          f"middleware/ file imports from forbidden layer: '{node.module}'",
                          f"Remove 'from {node.module} import ...'. Middleware may only import from infrastructure/ and rbac/.")
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    for prefix in forbidden_prefixes:
                        if alias.name.startswith(prefix):
                            f(104, "wiring", "high", rel(p), node.lineno,
                              f"middleware/ file imports from forbidden layer: '{alias.name}'",
                              f"Remove 'import {alias.name}'. Middleware may only import from infrastructure/ and rbac/.")


def _check_shared_package_wiring():
    """Law 105: @zozi/shared doesn't import from web_app or mobile_app."""
    for p in SHARED_FILES:
        content = read(p)
        if not content:
            continue
        if "from web_app" in content or "import web_app" in content:
            f(105, "wiring", "medium", rel(p, FRONTEND_ROOT), 0,
              "shared/ package imports from web_app",
              "Remove web_app import. @zozi/shared must be application-agnostic.")
        if "from mobile_app" in content or "import mobile_app" in content:
            f(105, "wiring", "medium", rel(p, FRONTEND_ROOT), 0,
              "shared/ package imports from mobile_app",
              "Remove mobile_app import. @zozi/shared must be application-agnostic.")


def _check_frontend_backend_wiring():
    """Law 106: Frontend communicates via API proxy only — no backend imports."""
    backend_markers = [
        "from backend.", "import backend.",
        "from domains.", "import domains.",
        "from infrastructure.", "import infrastructure.",
        "from modules.", "import modules.",
        "from providers.", "import providers.",
    ]
    for p in FRONTEND_FILES:
        content = read(p)
        if not content:
            continue
        for marker in backend_markers:
            if marker in content:
                f(106, "wiring", "high", rel(p, FRONTEND_ROOT), 0,
                  f"Frontend file imports backend code via '{marker.strip()}'",
                  "Frontend must communicate with backend only through the API proxy (/api/*). Remove direct backend imports.")
                break


# ══════════════════════════════════════════════════════════════
# SECTION 2: TECHNOLOGY (Laws 107-122)
# ══════════════════════════════════════════════════════════════

def check_section_technology():
    """Laws 107-122: Technology stack compliance."""
    _check_postgresql_in_prod()         # Law 107
    _check_sqlite_in_dev()              # Law 108
    _check_redis_usage()                # Law 109
    _check_redis_failure_handling()     # Law 110
    _check_nextjs_app_router()          # Law 111
    _check_react_server_components()    # Law 112
    _check_expo_router()                # Law 113
    _check_websocket_for_realtime()     # Law 114
    _check_celery_for_jobs()            # Law 115
    _check_email_via_smtp()             # Law 116
    _check_sms_via_twilio()             # Law 117
    _check_payment_gateways()           # Law 118
    _check_ai_ml_backends()             # Law 119
    _check_s3_storage()                 # Law 120
    _check_image_processing()            # Law 121
    _check_leaflet_maps()               # Law 122


def _check_postgresql_in_prod():
    """Law 107: Production uses PostgreSQL 15."""
    env_prod = ROOT / ".env.prod"
    env_file = ROOT / ".env"
    for env_path in [env_prod, env_file]:
        if not env_path.exists():
            continue
        content = read(env_path)
        if "DATABASE_URL" in content:
            if "postgresql" not in content.lower() and "postgres" not in content.lower():
                f(107, "technology", "high", rel(env_path), 0,
                  "DATABASE_URL does not use PostgreSQL in production config",
                  "Set DATABASE_URL to postgresql://... for production. PostgreSQL 15 is required.")
            break
    else:
        # Check infrastructure config for DB engine
        db_config = ROOT / "infrastructure" / "config.py"
        if db_config.exists():
            content = read(db_config)
            if "postgresql" not in content.lower() and "postgres" not in content.lower():
                if "DATABASE_URL" in content or "DB_URL" in content:
                    f(107, "technology", "medium", rel(db_config), 0,
                      "No PostgreSQL configuration found in infrastructure/config.py",
                      "Configure DATABASE_URL with postgresql://... for production.")


def _check_sqlite_in_dev():
    """Law 108: SQLite for zero-config startup."""
    env_example = ROOT / ".env.example"
    if env_example.exists():
        content = read(env_example)
        if "sqlite" not in content.lower() and "DATABASE_URL" in content:
            f(108, "technology", "low", rel(env_example), 0,
              ".env.example does not default to SQLite for development",
              "Set DATABASE_URL=sqlite+aiosqlite:///./zozi_dev.db as the default for zero-config dev startup.")


def _check_redis_usage():
    """Law 109: Redis for sessions, catalog cache, rate limiting, blacklist, pub/sub."""
    redis_files = [p for p in INFRA if "redis" in rel(p).lower()]
    if not redis_files:
        f(109, "technology", "high", "infrastructure/", 0,
          "No Redis infrastructure module found",
          "Create infrastructure/redis/ with client.py and cache.py for session/cache/rate-limit support.")
        return
    combined = "\n".join(read(p) for p in redis_files)
    required = {
        "session": "session" in combined.lower(),
        "cache": "cache" in combined.lower(),
        "rate_limit": "rate" in combined.lower() and "limit" in combined.lower(),
        "blacklist": "blacklist" in combined.lower() or "blocklist" in combined.lower(),
        "pubsub": "pubsub" in combined.lower() or "publish" in combined.lower(),
    }
    missing = [k for k, v in required.items() if not v]
    if missing:
        f(109, "technology", "medium", "infrastructure/redis/", 0,
          f"Redis infrastructure missing features: {', '.join(missing)}",
          f"Implement Redis-backed {', '.join(missing)} in infrastructure/redis/.")


def _check_redis_failure_handling():
    """Law 110: Sessions→DB fallback, caching pass-through, rate limit fails closed."""
    redis_files = [p for p in INFRA if "redis" in rel(p).lower()]
    combined = "\n".join(read(p) for p in redis_files)
    if not combined:
        return
    has_fallback = "fallback" in combined.lower() or "except" in combined.lower()
    has_circuit = "circuit" in combined.lower() or "CircuitBreaker" in combined
    if not has_fallback and not has_circuit:
        f(110, "technology", "medium", "infrastructure/redis/", 0,
          "Redis infrastructure lacks failure handling (fallback/circuit-breaker)",
          "Add try/except with DB fallback for sessions, pass-through for caching, and fail-closed for rate limits.")


def _check_nextjs_app_router():
    """Law 111: Web uses Next.js App Router."""
    next_config = FRONTEND_ROOT / "web_app" / "next.config.ts"
    if not next_config.exists():
        next_config = FRONTEND_ROOT / "web_app" / "next.config.js"
    if not next_config.exists():
        f(111, "technology", "medium", "web_app/", 0,
          "No next.config found — cannot verify App Router usage",
          "Ensure web_app uses Next.js App Router (app/ directory).")
        return
    app_dir = FRONTEND_ROOT / "web_app" / "src" / "app"
    if not app_dir.exists():
        f(111, "technology", "high", "web_app/src/", 0,
          "No app/ directory found — Next.js App Router not in use",
          "Migrate to App Router: create web_app/src/app/ with layout.tsx and page.tsx files.")


def _check_react_server_components():
    """Law 112: Data-fetching = Server Components."""
    app_dir = FRONTEND_ROOT / "web_app" / "src" / "app"
    if not app_dir.exists():
        return
    client_components = []
    for p in safe_rglob(app_dir, "*.tsx"):
        content = read(p)
        if content and '"use client"' in content:
            # Check if it does data fetching (has fetch/getServerSideProps-like patterns)
            if "fetch(" in content or "axios" in content:
                client_components.append(p)
    for p in client_components:
        f(112, "technology", "low", rel(p, FRONTEND_ROOT), 0,
          "Client component performs data fetching — should be a Server Component",
          "Move data fetching to Server Components. Remove 'use client' directive for data-fetching pages.")


def _check_expo_router():
    """Law 113: Mobile uses Expo Router."""
    mobile_app = FRONTEND_ROOT / "mobile_app"
    if not mobile_app.exists():
        return
    app_json = mobile_app / "app.json"
    if app_json.exists():
        content = read(app_json)
        if "expo-router" not in content:
            f(113, "technology", "medium", "mobile_app/app.json", 0,
              "expo-router not configured in app.json",
              "Add expo-router plugin to app.json and use file-based routing with app/ directory.")
    app_dir = mobile_app / "app"
    if not app_dir.exists():
        f(113, "technology", "medium", "mobile_app/", 0,
          "No app/ directory found — Expo Router not in use",
          "Create mobile_app/app/ with _layout.tsx and route files for Expo Router.")


def _check_websocket_for_realtime():
    """Law 114: WebSocket only for real-time features."""
    ws_files = [p for p in ALL_PY if "websocket" in rel(p).lower() or "ws_" in rel(p).lower() or "realtime" in rel(p).lower()]
    if not ws_files:
        f(114, "technology", "low", "infrastructure/", 0,
          "No WebSocket infrastructure found for real-time features",
          "Implement WebSocket support in infrastructure/messaging/ws_manager.py for real-time updates.")
    for p in ws_files:
        content = read(p)
        if not content:
            continue
        # Check if WebSocket is used for non-realtime purposes (file uploads, etc.)
        if "upload" in content.lower() and "websocket" in content.lower():
            tree = parse_ast(p)
            if tree:
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef) and "upload" in node.name.lower():
                        f(114, "technology", "medium", rel(p), node.lineno,
                          "WebSocket used for file upload — should use HTTP for non-real-time operations",
                          "Use HTTP endpoints for file uploads. Reserve WebSocket for real-time features only.")


def _check_celery_for_jobs():
    """Law 115: CPU-bound jobs use Celery."""
    celery_app = ROOT / "jobs" / "celery_app.py"
    if not celery_app.exists():
        f(115, "technology", "high", "jobs/", 0,
          "No celery_app.py found — CPU-bound jobs lack task queue",
          "Create jobs/celery_app.py with Celery configuration for CPU-bound task execution.")
        return
    content = read(celery_app)
    if "Celery" not in content:
        f(115, "technology", "high", "jobs/celery_app.py", 0,
          "celery_app.py does not instantiate Celery",
          "Instantiate Celery app: app = Celery('zozi', broker='redis://localhost:6379/0')")


def _check_email_via_smtp():
    """Law 116: Transactional email via providers/comms/email.py."""
    email_provider = ROOT / "providers" / "comms" / "email.py"
    if not email_provider.exists():
        f(116, "technology", "medium", "providers/comms/", 0,
          "No email.py provider found",
          "Create providers/comms/email.py wrapping SMTP (smtplib) for transactional email.")
        return
    content = read(email_provider)
    if "smtplib" not in content and "smtp" not in content.lower():
        f(116, "technology", "low", "providers/comms/email.py", 0,
          "Email provider does not use smtplib",
          "Use smtplib or aiosmtplib for SMTP-based email delivery in providers/comms/email.py.")


def _check_sms_via_twilio():
    """Law 117: SMS and WhatsApp via Twilio."""
    twilio_file = ROOT / "providers" / "comms" / "twilio.py"
    if not twilio_file.exists():
        f(117, "technology", "medium", "providers/comms/", 0,
          "No twilio.py provider found for SMS/WhatsApp",
          "Create providers/comms/twilio.py wrapping the Twilio SDK for SMS and WhatsApp messaging.")
        return
    content = read(twilio_file)
    if "twilio" not in content.lower():
        f(117, "technology", "low", "providers/comms/twilio.py", 0,
          "Twilio provider does not import twilio SDK",
          "Import and wrap the Twilio Client: from twilio.rest import Client")


def _check_payment_gateways():
    """Law 118: Stripe, Tap, PayPal, PayTabs, Thawani."""
    payments_dir = ROOT / "providers" / "payments"
    if not payments_dir.exists():
        f(118, "technology", "high", "providers/", 0,
          "No payments/ provider directory found",
          "Create providers/payments/ with stripe_sdk.py, tap.py, paypal.py, paytabs.py, thawani.py.")
        return
    required_gateways = {
        "stripe": False,
        "tap": False,
        "paypal": False,
        "paytabs": False,
        "thawani": False,
    }
    for p in payments_dir.glob("*.py"):
        content = read(p).lower()
        for gateway in required_gateways:
            if gateway in content:
                required_gateways[gateway] = True
    missing = [k for k, v in required_gateways.items() if not v]
    if missing:
        f(118, "technology", "medium", "providers/payments/", 0,
          f"Missing payment gateway providers: {', '.join(missing)}",
          f"Implement {', '.join(missing)} wrappers in providers/payments/.")


def _check_ai_ml_backends():
    """Law 119: Ollama, OpenAI, HuggingFace via providers/ai/."""
    ai_dir = ROOT / "providers" / "ai"
    if not ai_dir.exists():
        f(119, "technology", "medium", "providers/", 0,
          "No ai/ provider directory found",
          "Create providers/ai/ with openai_client.py, huggingface.py, and ollama integration.")
        return
    combined = "\n".join(read(p).lower() for p in ai_dir.glob("*.py"))
    required = {
        "openai": "openai" in combined,
        "huggingface": "huggingface" in combined or "transformers" in combined,
        "ollama": "ollama" in combined,
    }
    missing = [k for k, v in required.items() if not v]
    if missing:
        f(119, "technology", "low", "providers/ai/", 0,
          f"Missing AI/ML backends: {', '.join(missing)}",
          f"Add {', '.join(missing)} integration in providers/ai/.")


def _check_s3_storage():
    """Law 120: S3 (prod) or local (dev). Media blobs never in PostgreSQL."""
    storage_dir = ROOT / "providers" / "storage"
    if not storage_dir.exists():
        f(120, "technology", "high", "providers/", 0,
          "No storage/ provider directory found",
          "Create providers/storage/ with s3_client.py for S3-backed media storage.")
        return
    combined = "\n".join(read(p).lower() for p in storage_dir.glob("*.py"))
    has_s3 = "s3" in combined or "boto3" in combined
    has_local = "local" in combined
    if not has_s3:
        f(120, "technology", "medium", "providers/storage/", 0,
          "No S3 integration found in storage provider",
          "Add S3 client (boto3) for production media storage in providers/storage/s3_client.py.")
    if not has_local:
        f(120, "technology", "low", "providers/storage/", 0,
          "No local storage fallback found",
          "Add local filesystem storage for development in providers/storage/.")


def _check_image_processing():
    """Law 121: Pillow, rembg, OpenCV."""
    image_dir = ROOT / "providers" / "image"
    if not image_dir.exists():
        f(121, "technology", "low", "providers/", 0,
          "No image/ provider directory found",
          "Create providers/image/ with Pillow, rembg, and OpenCV wrappers.")
        return
    combined = "\n".join(read(p).lower() for p in safe_rglob(image_dir, "*.py"))
    required = {
        "pillow": "pillow" in combined or "pil" in combined,
        "rembg": "rembg" in combined,
        "opencv": "opencv" in combined or "cv2" in combined,
    }
    missing = [k for k, v in required.items() if not v]
    if missing:
        f(121, "technology", "low", "providers/image/", 0,
          f"Missing image processing libraries: {', '.join(missing)}",
          f"Add {', '.join(missing)} wrappers in providers/image/.")


def _check_leaflet_maps():
    """Law 122: Leaflet + react-leaflet."""
    web_app_dir = FRONTEND_ROOT / "web_app"
    if not web_app_dir.exists():
        return
    package_json = web_app_dir / "package.json"
    if package_json.exists():
        content = read(package_json)
        if "leaflet" not in content.lower():
            f(122, "technology", "low", "web_app/package.json", 0,
              "Leaflet not found in web_app dependencies",
              "Add 'leaflet' and 'react-leaflet' to web_app/package.json for map functionality.")


# ══════════════════════════════════════════════════════════════
# SECTION 3: PROVIDER LAWS (Laws 123-131)
# ══════════════════════════════════════════════════════════════

def check_section_provider_laws():
    """Laws 123-131: Provider implementation standards."""
    _check_single_sdk_per_provider()    # Law 123
    _check_has_flags()                  # Law 124
    _check_degrade_gracefully()         # Law 125
    _check_no_business_logic()          # Law 126
    _check_config_in_providers()        # Law 127
    _check_async_workers_for_cpu()      # Law 128
    _check_health_checks()              # Law 129
    _check_error_mapping()              # Law 130
    _check_mock_in_tests()              # Law 131


def _check_single_sdk_per_provider():
    """Law 123: Each provider wraps exactly one external SDK."""
    provider_dirs = [d for d in (ROOT / "providers").iterdir() if d.is_dir() and d.name != "__pycache__"]
    for d in provider_dirs:
        sdk_imports = set()
        for p in d.glob("*.py"):
            if p.name.startswith("_"):
                continue
            content = read(p)
            if not content:
                continue
            tree = parse_ast(p)
            if not tree:
                continue
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom) and node.module:
                    # Track external SDK imports (not relative, not infrastructure)
                    if not node.module.startswith(".") and not node.module.startswith("infrastructure"):
                        if not node.module.startswith("providers"):
                            sdk_imports.add(node.module.split(".")[0])
        if len(sdk_imports) > 1:
            f(123, "provider", "medium", f"providers/{d.name}/", 0,
              f"Provider wraps multiple SDKs: {', '.join(sorted(sdk_imports))}",
              f"Split providers/{d.name}/ into separate directories, one per external SDK.")


def _check_has_flags():
    """Law 124: Every provider exposes HAS_<SDK> boolean flags."""
    provider_dirs = [d for d in (ROOT / "providers").iterdir() if d.is_dir() and d.name != "__pycache__"]
    for d in provider_dirs:
        has_flag_found = False
        for p in d.glob("*.py"):
            content = read(p)
            if not content:
                continue
            if re.search(r"HAS_\w+\s*=\s*(True|False)", content):
                has_flag_found = True
                break
        if not has_flag_found:
            f(124, "provider", "medium", f"providers/{d.name}/", 0,
              f"Provider {d.name}/ missing HAS_<SDK> boolean flag",
              f"Add HAS_{d.name.upper()}_SDK = True/False in providers/{d.name}/__init__.py to indicate SDK availability.")


def _check_degrade_gracefully():
    """Law 125: When HAS_<SDK> = False, return defaults."""
    provider_files = [p for p in PROVIDERS if p.name != "__init__.py" and not p.name.startswith("_")]
    for p in provider_files:
        content = read(p)
        if not content:
            continue
        if "HAS_" not in content:
            continue
        tree = parse_ast(p)
        if not tree:
            continue
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                func_src = get_source_segment(content, node)
                if func_src and "HAS_" in func_src:
                    # Check if there's a default return when HAS_ is False
                    if "return" in func_src and ("None" in func_src or "[]" in func_src or "{}" in func_src or "default" in func_src.lower()):
                        pass  # Has graceful degradation
                    else:
                        f(125, "provider", "medium", rel(p), node.lineno,
                          f"Function '{node.name}' references HAS_ flag but may not return defaults on failure",
                          "When HAS_<SDK> is False, return safe defaults (None, [], {}) instead of raising.")


def _check_no_business_logic():
    """Law 126: Providers contain ONLY SDK wrapping."""
    business_keywords = [
        "order", "payment", "invoice", "customer", "product", "cart",
        "discount", "tax", "shipping", "refund", "commission", "payout"
    ]
    for p in PROVIDERS:
        if p.name.startswith("_") or p.name == "__init__.py":
            continue
        content = read(p)
        if not content:
            continue
        content_lower = content.lower()
        for keyword in business_keywords:
            if keyword in content_lower:
                tree = parse_ast(p)
                if tree:
                    for node in ast.walk(tree):
                        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                            if keyword in node.name.lower():
                                f(126, "provider", "high", rel(p), node.lineno,
                                  f"Provider contains business logic: function '{node.name}'",
                                  f"Move '{node.name}' to the appropriate domain service. Providers must only wrap SDKs.")
                                break
                    break


def _check_config_in_providers():
    """Law 127: API keys, endpoints, timeouts in providers/config.py."""
    config_file = ROOT / "providers" / "config.py"
    if not config_file.exists():
        f(127, "provider", "medium", "providers/", 0,
          "No providers/config.py found",
          "Create providers/config.py to centralize API keys, endpoints, and timeouts for all providers.")
        return
    content = read(config_file).lower()
    required = {
        "timeout": "timeout" in content,
        "api_key": "api_key" in content or "apikey" in content,
        "endpoint": "endpoint" in content or "url" in content,
    }
    missing = [k for k, v in required.items() if not v]
    if missing:
        f(127, "provider", "low", "providers/config.py", 0,
          f"providers/config.py missing config keys: {', '.join(missing)}",
          f"Add {', '.join(missing)} configuration to providers/config.py.")


def _check_async_workers_for_cpu():
    """Law 128: CPU-bound provider work via providers/async_workers."""
    async_workers = ROOT / "providers" / "async_workers.py"
    if not async_workers.exists():
        f(128, "provider", "medium", "providers/", 0,
          "No providers/async_workers.py found",
          "Create providers/async_workers.py for CPU-bound provider work (image processing, ML inference).")


def _check_health_checks():
    """Law 129: All providers expose health_check()."""
    provider_dirs = [d for d in (ROOT / "providers").iterdir() if d.is_dir() and d.name != "__pycache__"]
    for d in provider_dirs:
        has_health = False
        for p in d.glob("*.py"):
            content = read(p)
            if not content:
                continue
            if "health_check" in content:
                has_health = True
                break
        if not has_health:
            f(129, "provider", "low", f"providers/{d.name}/", 0,
              f"Provider {d.name}/ missing health_check() method",
              f"Add async def health_check() -> bool to providers/{d.name}/ for liveness probes.")


def _check_error_mapping():
    """Law 130: SDK errors mapped to domain exceptions."""
    for p in PROVIDERS:
        if p.name.startswith("_") or p.name == "__init__.py":
            continue
        content = read(p)
        if not content:
            continue
        tree = parse_ast(p)
        if not tree:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.ExceptHandler):
                if node.type:
                    handler_src = get_source_segment(content, node)
                    if handler_src and "raise" in handler_src:
                        # Check if raising domain exception (not raw SDK error)
                        if not any(d in handler_src for d in ["DomainError", "ProviderError", "ServiceError", "BusinessError"]):
                            f(130, "provider", "medium", rel(p), node.lineno,
                              "SDK exception raised without mapping to domain exception",
                              "Map SDK errors to domain exceptions (e.g., ProviderError, DomainError) before raising.")


def _check_mock_in_tests():
    """Law 131: Provider tests mock the external SDK."""
    provider_tests = [p for p in TESTS if "provider" in rel(p).lower()]
    if not provider_tests:
        f(131, "provider", "low", "tests/", 0,
          "No provider-specific tests found",
          "Create tests/providers/ with tests that mock external SDKs (use unittest.mock.patch).")


# ══════════════════════════════════════════════════════════════
# SECTION 4: MODULE LAWS (Laws 132-139)
# ══════════════════════════════════════════════════════════════

def check_section_module_laws():
    """Laws 132-139: Module structure and organization."""
    _check_module_structure()           # Law 132
    _check_per_module_auth()            # Law 133
    _check_router_file_naming()         # Law 134
    _check_router_registration()        # Law 135
    _check_public_vs_protected()        # Law 136
    _check_serializers_location()       # Law 137
    _check_five_modules_fixed()         # Law 138
    _check_route_prefixes()             # Law 139


def _check_module_structure():
    """Law 132: modules/{name}/ with auth/, routers/, serializers/."""
    expected_modules = ["admin", "customer", "employee", "logistics", "supplier"]
    modules_root = ROOT / "modules"
    for mod_name in expected_modules:
        mod_dir = modules_root / mod_name
        if not mod_dir.exists():
            f(132, "module", "high", "modules/", 0,
              f"Module {mod_name}/ directory missing",
              f"Create modules/{mod_name}/ with auth/, routers/, serializers/ subdirectories.")
            continue
        for sub in ["auth", "routers", "serializers"]:
            sub_dir = mod_dir / sub
            if not sub_dir.exists():
                f(132, "module", "medium", f"modules/{mod_name}/", 0,
                  f"Module {mod_name}/ missing {sub}/ subdirectory",
                  f"Create modules/{mod_name}/{sub}/ for {sub} organization.")


def _check_per_module_auth():
    """Law 133: Each module has its own auth dependency."""
    expected_modules = ["admin", "customer", "employee", "logistics", "supplier"]
    for mod_name in expected_modules:
        auth_dir = ROOT / "modules" / mod_name / "auth"
        if not auth_dir.exists():
            f(133, "module", "medium", f"modules/{mod_name}/", 0,
              f"Module {mod_name}/ missing auth/ dependency",
              f"Create modules/{mod_name}/auth/dependencies.py with module-specific auth dependency.")
            continue
        deps_file = auth_dir / "dependencies.py"
        if not deps_file.exists():
            f(133, "module", "medium", f"modules/{mod_name}/auth/", 0,
              f"Module {mod_name}/ missing auth/dependencies.py",
              f"Create modules/{mod_name}/auth/dependencies.py with get_current_active_{mod_name} dependency.")


def _check_router_file_naming():
    """Law 134: modules/{module}/routers/{domain}.py."""
    expected_domains = [
        "accounts", "analytics", "audit", "catalog", "comms", "country",
        "customers", "finance", "governance", "hr", "logistics", "orders",
        "payments", "promotions", "security", "suppliers"
    ]
    for p in ROUTERS:
        r = rel(p)
        parts = r.split("/")
        # Expected: modules/{module}/routers/{domain}.py
        if len(parts) >= 4 and parts[0] == "modules" and parts[2] == "routers":
            domain_file = parts[3]
            if domain_file == "__init__.py":
                continue
            if domain_file.replace(".py", "") not in expected_domains:
                f(134, "module", "low", r, 0,
                  f"Router file '{domain_file}' doesn't match expected domain name",
                  f"Rename to match a domain (e.g., routers/catalog.py) or add domain to expected list.")


def _check_router_registration():
    """Law 135: All router files listed in routers/__init__.py."""
    expected_modules = ["admin", "customer", "employee", "logistics", "supplier"]
    for mod_name in expected_modules:
        init_file = ROOT / "modules" / mod_name / "routers" / "__init__.py"
        if not init_file.exists():
            f(135, "module", "medium", f"modules/{mod_name}/routers/", 0,
              f"Missing routers/__init__.py in module {mod_name}",
              f"Create modules/{mod_name}/routers/__init__.py that imports and exports all router files.")
            continue
        content = read(init_file)
        routers_dir = ROOT / "modules" / mod_name / "routers"
        for p in routers_dir.glob("*.py"):
            if p.name == "__init__.py":
                continue
            router_name = p.stem
            if router_name not in content:
                f(135, "module", "medium", f"modules/{mod_name}/routers/__init__.py", 0,
                  f"Router '{router_name}' not imported in __init__.py",
                  f"Add 'from .{router_name} import router as {router_name}_router' to __init__.py.")


def _check_public_vs_protected():
    """Law 136: public_routers vs routers separation."""
    expected_modules = ["admin", "customer", "employee", "logistics", "supplier"]
    for mod_name in expected_modules:
        public_dir = ROOT / "modules" / mod_name / "public_routers"
        routers_dir = ROOT / "modules" / mod_name / "routers"
        if not public_dir.exists() and routers_dir.exists():
            f(136, "module", "low", f"modules/{mod_name}/", 0,
              f"Module {mod_name}/ missing public_routers/ for public endpoints",
              f"Consider creating modules/{mod_name}/public_routers/ for unauthenticated endpoints.")


def _check_serializers_location():
    """Law 137: Response serializers in modules/{module}/serializers/."""
    expected_modules = ["admin", "customer", "employee", "logistics", "supplier"]
    for mod_name in expected_modules:
        serializers_dir = ROOT / "modules" / mod_name / "serializers"
        if not serializers_dir.exists():
            f(137, "module", "medium", f"modules/{mod_name}/", 0,
              f"Module {mod_name}/ missing serializers/ directory",
              f"Create modules/{mod_name}/serializers/ for response serialization logic.")


def _check_five_modules_fixed():
    """Law 138: 5 modules fixed — admin, customer, employee, logistics, supplier."""
    expected = {"admin", "customer", "employee", "logistics", "supplier"}
    modules_root = ROOT / "modules"
    if not modules_root.exists():
        f(138, "module", "high", "modules/", 0,
          "modules/ directory does not exist",
          "Create modules/ with admin, customer, employee, logistics, supplier subdirectories.")
        return
    actual = {d.name for d in modules_root.iterdir() if d.is_dir() and not d.name.startswith("_")}
    missing = expected - actual
    extra = actual - expected
    if missing:
        f(138, "module", "high", "modules/", 0,
          f"Missing modules: {', '.join(missing)}",
          f"Create modules/{', '.join(missing)}/ directories.")
    if extra:
        f(138, "module", "medium", "modules/", 0,
          f"Unexpected modules found: {', '.join(extra)}",
          f"Remove extra modules or update the expected list. Expected: {', '.join(expected)}.")


def _check_route_prefixes():
    """Law 139: Route prefixes — /admin/*, /customer/*, etc."""
    expected_modules = ["admin", "customer", "employee", "logistics", "supplier"]
    orchestrator = ROOT / "middleware" / "orchestrator.py"
    if not orchestrator.exists():
        return
    content = read(orchestrator)
    for mod_name in expected_modules:
        if f"/{mod_name}" not in content and f'"{mod_name}"' not in content:
            f(139, "module", "low", "middleware/orchestrator.py", 0,
              f"Module {mod_name} may not have route prefix /{mod_name}/* configured",
              f"Ensure router for {mod_name} is included with prefix '/{mod_name}' in orchestrator.py.")


# ══════════════════════════════════════════════════════════════
# SECTION 5: INFRASTRUCTURE LAWS (Laws 140-149)
# ══════════════════════════════════════════════════════════════

def check_section_infrastructure_laws():
    """Laws 140-149: Infrastructure subpackage standards."""
    _check_seven_subpackages()          # Law 140
    _check_database_infra()             # Law 141
    _check_redis_infra()                # Law 142
    _check_storage_infra()              # Law 143
    _check_messaging_infra()            # Law 144
    _check_observability_infra()        # Law 145
    _check_security_infra()             # Law 146
    _check_utils_infra()                # Law 147
    _check_canonical_base()             # Law 148
    _check_session_lifecycle()          # Law 149


def _check_seven_subpackages():
    """Law 140: 7 subpackages — database/, redis/, storage/, messaging/, observability/, security/, utils/."""
    expected = {"database", "redis", "storage", "messaging", "observability", "security", "utils"}
    infra_root = ROOT / "infrastructure"
    if not infra_root.exists():
        f(140, "infrastructure", "high", "infrastructure/", 0,
          "infrastructure/ directory does not exist",
          "Create infrastructure/ with database/, redis/, storage/, messaging/, observability/, security/, utils/.")
        return
    actual = {d.name for d in infra_root.iterdir() if d.is_dir() and not d.name.startswith("_")}
    missing = expected - actual
    if missing:
        f(140, "infrastructure", "medium", "infrastructure/", 0,
          f"Missing infrastructure subpackages: {', '.join(missing)}",
          f"Create infrastructure/{', '.join(missing)}/ directories.")


def _check_database_infra():
    """Law 141: Base, get_db/get_read_db, sessions, RLS, transactions."""
    db_dir = ROOT / "infrastructure" / "database"
    if not db_dir.exists():
        f(141, "infrastructure", "high", "infrastructure/", 0,
          "No database/ subpackage found",
          "Create infrastructure/database/ with base.py, session.py, transaction.py.")
        return
    required_files = {
        "base.py": "DeclarativeBase definition",
        "session.py": "get_db / get_read_db dependencies",
        "transaction.py": "Transaction management",
    }
    for fname, desc in required_files.items():
        if not (db_dir / fname).exists():
            f(141, "infrastructure", "medium", "infrastructure/database/", 0,
              f"Missing {fname} ({desc})",
              f"Create infrastructure/database/{fname} for {desc}.")


def _check_redis_infra():
    """Law 142: Client singleton, cache abstraction, blacklist, pub/sub."""
    redis_dir = ROOT / "infrastructure" / "redis"
    if not redis_dir.exists():
        f(142, "infrastructure", "medium", "infrastructure/", 0,
          "No redis/ subpackage found",
          "Create infrastructure/redis/ with client.py and cache.py.")
        return
    required = {
        "client.py": "Redis client singleton",
        "cache.py": "Cache abstraction layer",
    }
    for fname, desc in required.items():
        if not (redis_dir / fname).exists():
            f(142, "infrastructure", "low", "infrastructure/redis/", 0,
              f"Missing {fname} ({desc})",
              f"Create infrastructure/redis/{fname} for {desc}.")


def _check_storage_infra():
    """Law 143: Abstraction interface + backup utilities."""
    storage_dir = ROOT / "infrastructure" / "storage"
    if not storage_dir.exists():
        f(143, "infrastructure", "medium", "infrastructure/", 0,
          "No storage/ subpackage found",
          "Create infrastructure/storage/ with storage.py and backup.py.")
        return
    if not (storage_dir / "storage.py").exists():
        f(143, "infrastructure", "low", "infrastructure/storage/", 0,
          "Missing storage.py abstraction interface",
          "Create infrastructure/storage/storage.py with StorageBackend interface.")


def _check_messaging_infra():
    """Law 144: WS manager, realtime, email wrappers, event bus."""
    messaging_dir = ROOT / "infrastructure" / "messaging"
    if not messaging_dir.exists():
        f(144, "infrastructure", "medium", "infrastructure/", 0,
          "No messaging/ subpackage found",
          "Create infrastructure/messaging/ with ws_manager.py, realtime.py, email_service.py.")
        return
    required = {
        "ws_manager.py": "WebSocket connection manager",
        "realtime.py": "Realtime event dispatch",
    }
    for fname, desc in required.items():
        if not (messaging_dir / fname).exists():
            f(144, "infrastructure", "low", "infrastructure/messaging/", 0,
              f"Missing {fname} ({desc})",
              f"Create infrastructure/messaging/{fname} for {desc}.")


def _check_observability_infra():
    """Law 145: OTEL, Prometheus, structlog, Sentry."""
    obs_dir = ROOT / "infrastructure" / "observability"
    if not obs_dir.exists():
        f(145, "infrastructure", "medium", "infrastructure/", 0,
          "No observability/ subpackage found",
          "Create infrastructure/observability/ with tracing.py, metrics.py, logging_config.py.")
        return
    combined = "\n".join(read(p).lower() for p in obs_dir.glob("*.py"))
    required = {
        "otel": "opentelemetry" in combined or "otel" in combined,
        "prometheus": "prometheus" in combined,
        "structlog": "structlog" in combined,
        "sentry": "sentry" in combined,
    }
    missing = [k for k, v in required.items() if not v]
    if missing:
        f(145, "infrastructure", "low", "infrastructure/observability/", 0,
          f"Missing observability integrations: {', '.join(missing)}",
          f"Add {', '.join(missing)} integration in infrastructure/observability/.")


def _check_security_infra():
    """Law 146: JWT, bcrypt, KMS encryption, rate limiting, CSRF."""
    sec_dir = ROOT / "infrastructure" / "security"
    if not sec_dir.exists():
        f(146, "infrastructure", "high", "infrastructure/", 0,
          "No security/ subpackage found",
          "Create infrastructure/security/ with encryption.py, csrf.py, rate_limiter.py.")
        return
    combined = "\n".join(read(p).lower() for p in sec_dir.glob("*.py"))
    required = {
        "jwt": "jwt" in combined or "jose" in combined,
        "bcrypt": "bcrypt" in combined or "passlib" in combined,
        "encryption": "encrypt" in combined or "kms" in combined,
        "rate_limit": "rate" in combined and "limit" in combined,
        "csrf": "csrf" in combined,
    }
    missing = [k for k, v in required.items() if not v]
    if missing:
        f(146, "infrastructure", "medium", "infrastructure/security/", 0,
          f"Missing security features: {', '.join(missing)}",
          f"Add {', '.join(missing)} implementation in infrastructure/security/.")


def _check_utils_infra():
    """Law 147: Pure technical helpers — pagination, datetime, config."""
    utils_dir = ROOT / "infrastructure" / "utils"
    if not utils_dir.exists():
        f(147, "infrastructure", "medium", "infrastructure/", 0,
          "No utils/ subpackage found",
          "Create infrastructure/utils/ with pagination.py, datetime_utils.py, config.py.")
        return
    combined = "\n".join(read(p).lower() for p in utils_dir.glob("*.py"))
    required = {
        "pagination": "pagination" in combined or "paginate" in combined,
        "datetime": "datetime" in combined or "timezone" in combined,
        "config": "config" in combined or "settings" in combined,
    }
    missing = [k for k, v in required.items() if not v]
    if missing:
        f(147, "infrastructure", "low", "infrastructure/utils/", 0,
          f"Missing utility modules: {', '.join(missing)}",
          f"Add {', '.join(missing)} helpers in infrastructure/utils/.")


def _check_canonical_base():
    """Law 148: infrastructure.database.base.Base is THE base."""
    base_file = ROOT / "infrastructure" / "database" / "base.py"
    if not base_file.exists():
        return
    content = read(base_file)
    if "DeclarativeBase" not in content:
        f(148, "infrastructure", "high", "infrastructure/database/base.py", 0,
          "base.py does not define DeclarativeBase",
          "Define: from sqlalchemy.orm import DeclarativeBase; class Base(DeclarativeBase): pass")
    # Check for duplicate Base classes elsewhere
    for p in ALL_PY:
        if p == base_file:
            continue
        r = rel(p)
        if "infrastructure/database/base" in r:
            continue
        p_content = read(p)
        if not p_content:
            continue
        if re.search(r'class\s+\w+Base\s*\(\s*DeclarativeBase\s*\)', p_content):
            f(148, "infrastructure", "high", r, 0,
              f"Duplicate DeclarativeBase subclass found in {r}",
              "Remove duplicate Base class. Use infrastructure.database.base.Base as the single source.")


def _check_session_lifecycle():
    """Law 149: Sessions via FastAPI Depends(get_db) only."""
    for p in ALL_PY:
        if p.name.startswith("_"):
            continue
        content = read(p)
        if not content:
            continue
        # Look for manual session creation patterns
        if "Session(" in content and "get_db" not in content:
            tree = parse_ast(p)
            if tree:
                for node in ast.walk(tree):
                    if isinstance(node, ast.Call):
                        call_src = get_source_segment(content, node)
                        if call_src and "Session(" in call_src and "get_db" not in call_src:
                            f(149, "infrastructure", "medium", rel(p), node.lineno,
                              "Manual Session() creation detected — should use Depends(get_db)",
                              "Replace manual Session() with FastAPI Depends(get_db) for proper session lifecycle.")


# ══════════════════════════════════════════════════════════════
# SECTION 6: DOMAIN LAWS (Laws 150-160)
# ══════════════════════════════════════════════════════════════

def check_section_domain_laws():
    """Laws 150-160: Domain structure and organization."""
    _check_domain_structure()            # Law 150
    _check_domain_events()              # Law 151
    _check_domain_subscribers()         # Law 152
    _check_domain_ports()               # Law 153
    _check_domain_features()            # Law 154
    _check_domain_read_models()         # Law 155
    _check_domain_policies()            # Law 156
    _check_domain_services()            # Law 157
    _check_domain_models()              # Law 158
    _check_domain_schemas()             # Law 159
    _check_domain_cross_imports()       # Law 160


def _check_domain_structure():
    """Law 150: services/, models/, schemas/, events.py, subscribers.py, ports.py, features.py, read_models/, policies/."""
    required_files = ["events.py", "subscribers.py", "ports.py", "features.py"]
    required_dirs = ["services", "models", "schemas", "read_models", "policies"]
    for domain_name, paths in DOMAINS.items():
        domain_root = ROOT / "domains" / domain_name
        if not domain_root.exists():
            continue
        for fname in required_files:
            if not (domain_root / fname).exists():
                f(150, "domain", "medium", f"domains/{domain_name}/", 0,
                  f"Domain {domain_name}/ missing {fname}",
                  f"Create domains/{domain_name}/{fname}.")
        for dname in required_dirs:
            if not (domain_root / dname).exists():
                f(150, "domain", "medium", f"domains/{domain_name}/", 0,
                  f"Domain {domain_name}/ missing {dname}/ directory",
                  f"Create domains/{domain_name}/{dname}/.")


def _check_domain_events():
    """Law 151: events.py defines domain events."""
    for domain_name, paths in DOMAINS.items():
        events_file = ROOT / "domains" / domain_name / "events.py"
        if not events_file.exists():
            continue
        content = read(events_file)
        if not content.strip() or content.strip() == '"""\n"""' or content.strip() == "pass":
            f(151, "domain", "low", f"domains/{domain_name}/events.py", 0,
              f"Domain {domain_name}/events.py is empty",
              f"Define domain events in domains/{domain_name}/events.py (e.g., OrderCreated, PaymentProcessed).")


def _check_domain_subscribers():
    """Law 152: subscribers.py handles cross-domain events."""
    for domain_name, paths in DOMAINS.items():
        sub_file = ROOT / "domains" / domain_name / "subscribers.py"
        if not sub_file.exists():
            continue
        content = read(sub_file)
        if not content.strip() or content.strip() == '"""\n"""' or content.strip() == "pass":
            f(152, "domain", "low", f"domains/{domain_name}/subscribers.py", 0,
              f"Domain {domain_name}/subscribers.py is empty",
              f"Define event subscribers in domains/{domain_name}/subscribers.py for cross-domain events.")


def _check_domain_ports():
    """Law 153: ports.py defines cross-domain read interfaces."""
    for domain_name, paths in DOMAINS.items():
        ports_file = ROOT / "domains" / domain_name / "ports.py"
        if not ports_file.exists():
            continue
        content = read(ports_file)
        if not content.strip() or content.strip() == '"""\n"""' or content.strip() == "pass":
            f(153, "domain", "low", f"domains/{domain_name}/ports.py", 0,
              f"Domain {domain_name}/ports.py is empty",
              f"Define cross-domain read functions in domains/{domain_name}/ports.py (e.g., get_by_id helpers).")


def _check_domain_features():
    """Law 154: features.py defines feature atoms for RBAC."""
    for domain_name, paths in DOMAINS.items():
        features_file = ROOT / "domains" / domain_name / "features.py"
        if not features_file.exists():
            continue
        content = read(features_file)
        if not content.strip() or content.strip() == '"""\n"""' or content.strip() == "pass":
            f(154, "domain", "low", f"domains/{domain_name}/features.py", 0,
              f"Domain {domain_name}/features.py is empty",
              f"Define feature atoms in domains/{domain_name}/features.py for RBAC permission gating.")


def _check_domain_read_models():
    """Law 155: read_models/ for cross-domain read projections."""
    for domain_name, paths in DOMAINS.items():
        rm_dir = ROOT / "domains" / domain_name / "read_models"
        if not rm_dir.exists():
            continue
        init_file = rm_dir / "__init__.py"
        if init_file.exists():
            content = read(init_file)
            if not content.strip() or content.strip() == '"""\n"""':
                f(155, "domain", "low", f"domains/{domain_name}/read_models/", 0,
                  f"Domain {domain_name}/read_models/__init__.py is empty",
                  f"Define read model projections in domains/{domain_name}/read_models/ for cross-domain reads.")


def _check_domain_policies():
    """Law 156: policies/ for domain authorization policies."""
    for domain_name, paths in DOMAINS.items():
        pol_dir = ROOT / "domains" / domain_name / "policies"
        if not pol_dir.exists():
            continue
        init_file = pol_dir / "__init__.py"
        if init_file.exists():
            content = read(init_file)
            if not content.strip() or content.strip() == '"""\n"""':
                f(156, "domain", "low", f"domains/{domain_name}/policies/", 0,
                  f"Domain {domain_name}/policies/__init__.py is empty",
                  f"Define authorization policies in domains/{domain_name}/policies/.")


def _check_domain_services():
    """Law 157: services/ contains business logic."""
    for domain_name, paths in DOMAINS.items():
        svc_dir = ROOT / "domains" / domain_name / "services"
        if not svc_dir.exists():
            continue
        svc_files = [p for p in svc_dir.glob("*.py") if p.name != "__init__.py"]
        if not svc_files:
            f(157, "domain", "medium", f"domains/{domain_name}/services/", 0,
              f"Domain {domain_name}/services/ has no service files",
              f"Add service classes in domains/{domain_name}/services/ for business logic.")


def _check_domain_models():
    """Law 158: models/ contains SQLAlchemy models."""
    for domain_name, paths in DOMAINS.items():
        model_dir = ROOT / "domains" / domain_name / "models"
        if not model_dir.exists():
            continue
        model_files = [p for p in model_dir.glob("*.py") if p.name != "__init__.py"]
        if not model_files:
            f(158, "domain", "medium", f"domains/{domain_name}/models/", 0,
              f"Domain {domain_name}/models/ has no model files",
              f"Add SQLAlchemy model classes in domains/{domain_name}/models/.")


def _check_domain_schemas():
    """Law 159: schemas/ contains Pydantic schemas."""
    for domain_name, paths in DOMAINS.items():
        schema_dir = ROOT / "domains" / domain_name / "schemas"
        if not schema_dir.exists():
            continue
        schema_files = [p for p in schema_dir.glob("*.py") if p.name != "__init__.py"]
        if not schema_files:
            f(159, "domain", "medium", f"domains/{domain_name}/schemas/", 0,
              f"Domain {domain_name}/schemas/ has no schema files",
              f"Add Pydantic schemas in domains/{domain_name}/schemas/ for request/response validation.")


def _check_domain_cross_imports():
    """Law 160: Domains don't import from other domains directly."""
    for domain_name, paths in DOMAINS.items():
        for p in paths:
            content = read(p)
            if not content:
                continue
            tree = parse_ast(p)
            if not tree:
                continue
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom) and node.module:
                    if node.module.startswith("domains."):
                        imported_domain = node.module.split(".")[1] if len(node.module.split(".")) > 1 else ""
                        if imported_domain and imported_domain != domain_name:
                            f(160, "domain", "high", rel(p), node.lineno,
                              f"Domain {domain_name} directly imports from domain {imported_domain}: '{node.module}'",
                              f"Use ports.py for cross-domain reads. Move 'from {node.module} import ...' to domains/{domain_name}/ports.py.")


# ══════════════════════════════════════════════════════════════
# MODULE IMPORT HOOK
# ══════════════════════════════════════════════════════════════

# Import ast at module level for use in walk() calls
import ast
import re
