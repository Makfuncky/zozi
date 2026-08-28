# -*- coding: utf-8 -*-
"""
ZOZI Audit — Laws 101-200: Wiring, Technology, Provider, Module, Infrastructure,
Domain, RBAC, Frontend, Web App, Mobile, Shared.

Uses the ASTAnalyzer class and pre-indexed file lists from full_system_audit.py.
All checks record findings via f(lid, cat, sev, file, line, desc, fix).
"""

import ast
import re
import json
from pathlib import Path


# ══════════════════════════════════════════════════════════════
# LAWS 101-106: WIRING
# ══════════════════════════════════════════════════════════════

def _check_kernel_isolation():
    """Law 101: kernel/ doesn't import from domains/modules/rbac/providers/jobs/middleware."""
    forbidden = ["domains.", "modules.", "rbac.", "providers.", "jobs.", "middleware."]
    for p in KERNEL:
        tree, content = ASTAnalyzer.parse(p)
        if not tree:
            continue
        imports = ASTAnalyzer.get_imports(tree)
        for imp in imports['from']:
            for prefix in forbidden:
                if imp['module'].startswith(prefix):
                    f(101, "wiring", "critical", rel(p), imp['lineno'],
                      f"kernel/ imports from forbidden layer: '{imp['module']}'",
                      f"Remove 'from {imp['module']} import ...'. kernel/ must not import from domains/modules/rbac/providers/jobs/middleware.")
        for imp in imports['import']:
            for name in imp['names']:
                for prefix in forbidden:
                    if name.startswith(prefix):
                        f(101, "wiring", "critical", rel(p), imp['lineno'],
                          f"kernel/ imports from forbidden layer: '{name}'",
                          f"Remove 'import {name}'. kernel/ must not import from domains/modules/rbac/providers/jobs/middleware.")


def _check_infrastructure_isolation():
    """Law 102: infrastructure/ doesn't import from domains/modules/rbac/providers."""
    forbidden = ["domains.", "modules.", "rbac.", "providers."]
    for p in INFRA:
        tree, content = ASTAnalyzer.parse(p)
        if not tree:
            continue
        imports = ASTAnalyzer.get_imports(tree)
        for imp in imports['from']:
            for prefix in forbidden:
                if imp['module'].startswith(prefix):
                    f(102, "wiring", "critical", rel(p), imp['lineno'],
                      f"infrastructure/ imports from upper layer: '{imp['module']}'",
                      f"Remove 'from {imp['module']} import ...'. infrastructure/ must not import from domains/modules/rbac/providers.")
        for imp in imports['import']:
            for name in imp['names']:
                for prefix in forbidden:
                    if name.startswith(prefix):
                        f(102, "wiring", "critical", rel(p), imp['lineno'],
                          f"infrastructure/ imports from upper layer: '{name}'",
                          f"Remove 'import {name}'. infrastructure/ must not import from domains/modules/rbac/providers.")


def _check_job_wiring():
    """Law 103: Jobs import from domains/ + infrastructure/ only."""
    forbidden = ["modules.", "rbac.", "middleware."]
    for p in JOBS:
        tree, content = ASTAnalyzer.parse(p)
        if not tree:
            continue
        imports = ASTAnalyzer.get_imports(tree)
        for imp in imports['from']:
            for prefix in forbidden:
                if imp['module'].startswith(prefix):
                    f(103, "wiring", "high", rel(p), imp['lineno'],
                      f"jobs/ imports from forbidden layer: '{imp['module']}'",
                      f"Remove 'from {imp['module']} import ...'. Jobs may only import from domains/ and infrastructure/.")
        for imp in imports['import']:
            for name in imp['names']:
                for prefix in forbidden:
                    if name.startswith(prefix):
                        f(103, "wiring", "high", rel(p), imp['lineno'],
                          f"jobs/ imports from forbidden layer: '{name}'",
                          f"Remove 'import {name}'. Jobs may only import from domains/ and infrastructure/.")


def _check_middleware_wiring():
    """Law 104: Middleware imports from infrastructure/ + rbac/ only."""
    forbidden = ["domains.", "modules.", "providers.", "jobs."]
    for p in MIDDLEWARE_FILES:
        tree, content = ASTAnalyzer.parse(p)
        if not tree:
            continue
        imports = ASTAnalyzer.get_imports(tree)
        for imp in imports['from']:
            for prefix in forbidden:
                if imp['module'].startswith(prefix):
                    f(104, "wiring", "high", rel(p), imp['lineno'],
                      f"middleware/ imports from forbidden layer: '{imp['module']}'",
                      f"Remove 'from {imp['module']} import ...'. Middleware may only import from infrastructure/ and rbac/.")
        for imp in imports['import']:
            for name in imp['names']:
                for prefix in forbidden:
                    if name.startswith(prefix):
                        f(104, "wiring", "high", rel(p), imp['lineno'],
                          f"middleware/ imports from forbidden layer: '{name}'",
                          f"Remove 'import {name}'. Middleware may only import from infrastructure/ and rbac/.")


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
# LAWS 107-122: TECHNOLOGY
# ══════════════════════════════════════════════════════════════

def _check_postgresql_in_prod():
    """Law 107: Production uses PostgreSQL 15."""
    for env_path in [ROOT / ".env.prod", ROOT / ".env"]:
        if not env_path.exists():
            continue
        content = read(env_path)
        if "DATABASE_URL" in content:
            if "postgresql" not in content.lower() and "postgres" not in content.lower():
                f(107, "technology", "high", rel(env_path), 0,
                  "DATABASE_URL does not use PostgreSQL in production config",
                  "Set DATABASE_URL to postgresql://... for production. PostgreSQL 15 is required.")
            return
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
    for p in safe_rglob(app_dir, "*.tsx"):
        content = read(p)
        if not content:
            continue
        if '"use client"' in content and ("fetch(" in content or "axios" in content):
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
        if "upload" in content.lower() and "websocket" in content.lower():
            tree, _ = ASTAnalyzer.parse(p)
            if tree:
                funcs = ASTAnalyzer.get_functions(tree)
                for func in funcs:
                    if "upload" in func.name.lower():
                        f(114, "technology", "medium", rel(p), func.lineno,
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
    required_gateways = {"stripe": False, "tap": False, "paypal": False, "paytabs": False, "thawani": False}
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
# LAWS 123-131: PROVIDER LAWS
# ══════════════════════════════════════════════════════════════

def _check_single_sdk_per_provider():
    """Law 123: Each provider wraps exactly one external SDK."""
    provider_dirs = [d for d in (ROOT / "providers").iterdir() if d.is_dir() and d.name != "__pycache__"]
    for d in provider_dirs:
        sdk_imports = set()
        for p in d.glob("*.py"):
            if p.name.startswith("_"):
                continue
            tree, _ = ASTAnalyzer.parse(p)
            if not tree:
                continue
            imports = ASTAnalyzer.get_imports(tree)
            for imp in imports['from']:
                mod = imp['module']
                if not mod.startswith(".") and not mod.startswith("infrastructure") and not mod.startswith("providers"):
                    sdk_imports.add(mod.split(".")[0])
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
            if content and re.search(r"HAS_\w+\s*=\s*(True|False)", content):
                has_flag_found = True
                break
        if not has_flag_found:
            f(124, "provider", "medium", f"providers/{d.name}/", 0,
              f"Provider {d.name}/ missing HAS_<SDK> boolean flag",
              f"Add HAS_{d.name.upper()}_SDK = True/False in providers/{d.name}/__init__.py to indicate SDK availability.")


def _check_degrade_gracefully():
    """Law 125: When HAS_<SDK> = False, return defaults."""
    for p in PROVIDERS:
        if p.name.startswith("_") or p.name == "__init__.py":
            continue
        content = read(p)
        if not content or "HAS_" not in content:
            continue
        tree, _ = ASTAnalyzer.parse(p)
        if not tree:
            continue
        funcs = ASTAnalyzer.get_functions(tree)
        for func in funcs:
            func_source = ast.dump(func)
            if "HAS_" in func_source:
                if "return " not in func_source or ("None" not in func_source and "[]" not in func_source and "{}" not in func_source):
                    f(125, "provider", "medium", rel(p), func.lineno,
                      f"Function '{func.name}' references HAS_ flag but may not return defaults on failure",
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
                tree, _ = ASTAnalyzer.parse(p)
                if tree:
                    funcs = ASTAnalyzer.get_functions(tree)
                    for func in funcs:
                        if keyword in func.name.lower():
                            f(126, "provider", "high", rel(p), func.lineno,
                              f"Provider contains business logic: function '{func.name}'",
                              f"Move '{func.name}' to the appropriate domain service. Providers must only wrap SDKs.")
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
    required = {"timeout": "timeout" in content, "api_key": "api_key" in content or "apikey" in content, "endpoint": "endpoint" in content or "url" in content}
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
            if content and "health_check" in content:
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
        tree, _ = ASTAnalyzer.parse(p)
        if not tree:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.ExceptHandler):
                if node.type:
                    handler_src = ast.dump(node)
                    if "raise" in handler_src:
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
# LAWS 132-139: MODULE LAWS
# ══════════════════════════════════════════════════════════════

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
            if not (mod_dir / sub).exists():
                f(132, "module", "medium", f"modules/{mod_name}/", 0,
                  f"Module {mod_name}/ missing {sub}/ subdirectory",
                  f"Create modules/{mod_name}/{sub}/ for {sub} organization.")


def _check_per_module_auth():
    """Law 133: Each module has its own auth dependency."""
    for mod_name in ["admin", "customer", "employee", "logistics", "supplier"]:
        auth_dir = ROOT / "modules" / mod_name / "auth"
        if not auth_dir.exists():
            f(133, "module", "medium", f"modules/{mod_name}/", 0,
              f"Module {mod_name}/ missing auth/ dependency",
              f"Create modules/{mod_name}/auth/dependencies.py with module-specific auth dependency.")
            continue
        if not (auth_dir / "dependencies.py").exists():
            f(133, "module", "medium", f"modules/{mod_name}/auth/", 0,
              f"Module {mod_name}/ missing auth/dependencies.py",
              f"Create modules/{mod_name}/auth/dependencies.py with get_current_active_{mod_name} dependency.")


def _check_router_file_naming():
    """Law 134: modules/{module}/routers/{domain}.py."""
    expected_domains = {
        "accounts", "analytics", "audit", "catalog", "comms", "country",
        "customers", "finance", "governance", "hr", "logistics", "orders",
        "payments", "promotions", "security", "suppliers"
    }
    for p in ROUTERS:
        r = rel(p)
        parts = r.split("/")
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
    for mod_name in ["admin", "customer", "employee", "logistics", "supplier"]:
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
            if p.stem not in content:
                f(135, "module", "medium", f"modules/{mod_name}/routers/__init__.py", 0,
                  f"Router '{p.stem}' not imported in __init__.py",
                  f"Add 'from .{p.stem} import router as {p.stem}_router' to __init__.py.")


def _check_public_vs_protected():
    """Law 136: public_routers vs routers separation."""
    for mod_name in ["admin", "customer", "employee", "logistics", "supplier"]:
        public_dir = ROOT / "modules" / mod_name / "public_routers"
        routers_dir = ROOT / "modules" / mod_name / "routers"
        if not public_dir.exists() and routers_dir.exists():
            f(136, "module", "low", f"modules/{mod_name}/", 0,
              f"Module {mod_name}/ missing public_routers/ for public endpoints",
              f"Consider creating modules/{mod_name}/public_routers/ for unauthenticated endpoints.")


def _check_serializers_location():
    """Law 137: Response serializers in modules/{module}/serializers/."""
    for mod_name in ["admin", "customer", "employee", "logistics", "supplier"]:
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
          f"Remove extra modules or update the expected list.")


def _check_route_prefixes():
    """Law 139: Route prefixes — /admin/*, /customer/*, etc."""
    orchestrator = ROOT / "middleware" / "orchestrator.py"
    if not orchestrator.exists():
        return
    content = read(orchestrator)
    for mod_name in ["admin", "customer", "employee", "logistics", "supplier"]:
        if f"/{mod_name}" not in content and f'"{mod_name}"' not in content:
            f(139, "module", "low", "middleware/orchestrator.py", 0,
              f"Module {mod_name} may not have route prefix /{mod_name}/* configured",
              f"Ensure router for {mod_name} is included with prefix '/{mod_name}' in orchestrator.py.")


# ══════════════════════════════════════════════════════════════
# LAWS 140-149: INFRASTRUCTURE LAWS
# ══════════════════════════════════════════════════════════════

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
    required_files = {"base.py": "DeclarativeBase definition", "session.py": "get_db / get_read_db dependencies", "transaction.py": "Transaction management"}
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
    for fname, desc in {"client.py": "Redis client singleton", "cache.py": "Cache abstraction layer"}.items():
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
    for fname, desc in {"ws_manager.py": "WebSocket connection manager", "realtime.py": "Realtime event dispatch"}.items():
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
        if "Session(" in content and "get_db" not in content:
            tree, _ = ASTAnalyzer.parse(p)
            if tree:
                for node in ast.walk(tree):
                    if isinstance(node, ast.Call):
                        seg = ASTAnalyzer.get_source_segment(content, node)
                        if seg and "Session(" in seg and "get_db" not in seg:
                            f(149, "infrastructure", "medium", rel(p), node.lineno,
                              "Manual Session() creation detected — should use Depends(get_db)",
                              "Replace manual Session() with FastAPI Depends(get_db) for proper session lifecycle.")


# ══════════════════════════════════════════════════════════════
# LAWS 150-160: DOMAIN LAWS
# ══════════════════════════════════════════════════════════════

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


def _check_service_patterns():
    """Law 151: Services take primitives, own DB access and transactions."""
    for svc_file in SERVICES:
        content = read(svc_file)
        if not content:
            continue
        tree, _ = ASTAnalyzer.parse(svc_file)
        if not tree:
            continue
        classes = ASTAnalyzer.get_classes(tree)
        for cls in classes:
            if not cls.name.endswith("Service"):
                continue
            init_method = None
            for item in cls.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)) and item.name == "__init__":
                    init_method = item
                    break
            if init_method:
                args = [a.arg for a in init_method.args.args]
                has_db = any(a in args for a in ("db", "session", "db_session"))
                if not has_db and len(args) > 1:
                    f(151, "domain", "medium", rel(svc_file), init_method.lineno,
                      f"Service '{cls.name}' __init__ lacks db/session parameter",
                      "Add 'db: Session' as first parameter to own DB access and transactions")


def _check_model_patterns():
    """Law 152: __tablename__ + __table_args__ = {schema: <domain>}."""
    for model_file in MODELS:
        content = read(model_file)
        if not content:
            continue
        tree, _ = ASTAnalyzer.parse(model_file)
        if not tree:
            continue
        classes = ASTAnalyzer.get_classes(tree)
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
                                val_dump = ast.dump(item.value)
                                if "schema" in val_dump:
                                    has_schema = True
            if has_tablename and not has_schema:
                f(152, "domain", "high", rel(model_file), cls.lineno,
                  f"Model '{cls.name}' has __tablename__ but __table_args__ missing schema declaration",
                  'Add __table_args__ = ({"schema": "<domain>"},) to assign model to correct Postgres schema')


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
    for schema_file in schema_files:
        content = read(schema_file)
        if not content:
            continue
        if "BaseModel" not in content and "pydantic" not in content.lower():
            f(153, "domain", "low", rel(schema_file), 1,
              "Schema file does not appear to use Pydantic BaseModel",
              "Use pydantic.BaseModel for all schema definitions")


def _check_event_patterns():
    """Law 154: Events named {domain}.{entity}.{action}. Minimal data."""
    for domain_name, files in DOMAINS.items():
        for p in files:
            if p.name == "events.py":
                content = read(p)
                if not content:
                    continue
                tree, _ = ASTAnalyzer.parse(p)
                if not tree:
                    continue
                classes = ASTAnalyzer.get_classes(tree)
                for cls in classes:
                    if "Event" in cls.name or "event" in cls.name.lower():
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
                tree, _ = ASTAnalyzer.parse(p)
                if not tree:
                    continue
                funcs = ASTAnalyzer.get_functions(tree)
                for func in funcs:
                    if func.name.startswith("_"):
                        continue
                    if func.returns is None:
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
                tree, _ = ASTAnalyzer.parse(p)
                if not tree:
                    continue
                funcs = ASTAnalyzer.get_functions(tree)
                for func in funcs:
                    if func.name.startswith("_"):
                        continue
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
                tree, _ = ASTAnalyzer.parse(p)
                if not tree:
                    continue
                for node in ast.walk(tree):
                    if isinstance(node, ast.Assign):
                        for target in node.targets:
                            if isinstance(target, ast.Name) and target.id == "FEATURES":
                                if not isinstance(node.value, ast.Dict):
                                    f(157, "domain", "high", rel(p), node.lineno,
                                      "FEATURES is not a dictionary",
                                      "Define FEATURES as a dict: FEATURES = {'feature.key': 'Description'}")
                                else:
                                    for key in node.value.keys:
                                        if isinstance(key, ast.Constant) and isinstance(key.value, str):
                                            if "." not in key.value:
                                                f(157, "domain", "medium", rel(p), node.lineno,
                                                  f"Feature key '{key.value}' missing dotted namespace",
                                                  "Use dotted format: '{domain}.{entity}.{action}'")


def _check_read_model_patterns():
    """Law 158: Read model patterns — CQRS-lite projections."""
    for domain_name, files in DOMAINS.items():
        for p in files:
            if "/read_models/" in str(p) and p.suffix == ".py":
                content = read(p)
                if not content:
                    continue
                tree, _ = ASTAnalyzer.parse(p)
                if not tree:
                    continue
                classes = ASTAnalyzer.get_classes(tree)
                for cls in classes:
                    if "BaseModel" not in content and len(cls.body) > 10:
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
                tree, _ = ASTAnalyzer.parse(p)
                if not tree:
                    continue
                funcs = ASTAnalyzer.get_functions(tree)
                for func in funcs:
                    if func.name.startswith("_"):
                        continue
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
    for domain in sorted(unexpected):
        f(160, "domain", "high", f"domains/{domain}/", 0,
          f"Unexpected domain '{domain}' — new domains require architecture review",
          "Submit architecture review before adding new domains")
    for domain in sorted(missing):
        f(160, "domain", "low", f"domains/{domain}/", 0,
          f"Expected domain '{domain}' not found",
          f"Verify domain '{domain}' exists or update expected domain list")


# ══════════════════════════════════════════════════════════════
# LAWS 161-167: RBAC
# ══════════════════════════════════════════════════════════════

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
    if "pkgutil" not in content and "iter_modules" not in content:
        f(161, "rbac", "high", rel(catalog_files[0]), 1,
          "Catalog does not use pkgutil.iter_modules to scan domains",
          "Use pkgutil.iter_modules(domains.__path__) to discover and aggregate all FEATURES dicts")
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
        f(166, "rbac", "high", "rbac/models.py", 0,
          "rbac/models.py not found — permission persistence models missing",
          "Create rbac/models.py with Permission, RolePermissionAssignment, PermissionAuditLog")
        return
    content = read(models_files[0])
    if not content:
        return
    for model_name in ["Permission", "RolePermissionAssignment"]:
        if model_name not in content:
            f(166, "rbac", "medium", rel(models_files[0]), 1,
              f"rbac/models.py missing {model_name} model",
              f"Define {model_name} SQLAlchemy model for RBAC persistence")


def _check_frontend_permissions():
    """Law 167: permissions.ts GENERATED from /rbac/catalog."""
    if not FRONTEND_ROOT.exists():
        return
    permissions_files = [
        FRONTEND_ROOT / "shared" / "src" / "permissions.ts",
        FRONTEND_ROOT / "web_app" / "src" / "permissions.ts",
    ]
    found = False
    for p in permissions_files:
        if p.exists():
            found = True
            content = read(p)
            if content and "generated" not in content.lower() and "auto-generated" not in content.lower():
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

def _check_frontend_monorepo():
    """Law 168: Monorepo — web_app/, mobile_app/, shared/."""
    if not FRONTEND_ROOT.exists():
        f(168, "frontend", "critical", "frontend/", 0,
          "frontend/ directory not found",
          "Create frontend/ with web_app/, mobile_app/, and shared/ packages")
        return
    for d in ["web_app", "mobile_app", "shared"]:
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
        version = match.group(1).replace("^", "").replace("~", "").split(".")
        if len(version) >= 2:
            try:
                major, minor = int(version[0]), int(version[1])
                if major < 16 or (major == 16 and minor < 3):
                    f(169, "frontend", "high", "frontend/web_app/package.json", 0,
                      f"Next.js version {match.group(1)} is below required 16.3.1",
                      "Upgrade to Next.js 16.3.1+ for App Router support")
            except ValueError:
                pass
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
        if not config.get("compilerOptions", {}).get("strict", False):
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
    if "zustand" not in content:
        f(171, "frontend", "medium", "frontend/web_app/package.json", 0,
          "Zustand not found in dependencies — required for global state management",
          'Add "zustand" to dependencies for global state management')
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
    for p in safe_rglob(app_dir, "*.tsx"):
        content = read(p)
        if not content:
            continue
        if '"use client"' in content and "fetch(" in content and "/api/" in content:
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
    for source in ["/api/", "/admin/", "/auth/"]:
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
    for lib, desc in {
        "tailwind-merge": "tailwind-merge for class merging",
        "clsx": "clsx for conditional classes",
        "class-variance-authority": "CVA for component variants",
    }.items():
        if lib not in content:
            f(174, "frontend", "medium", "frontend/web_app/package.json", 0,
              f"Missing {desc}",
              f'Add "{lib}" to dependencies')
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
    error_boundary = FRONTEND_ROOT / "web_app" / "src" / "components" / "ui" / "ErrorBoundary.tsx"
    if not error_boundary.exists():
        f(176, "frontend", "medium", "frontend/web_app/src/components/ui/ErrorBoundary.tsx", 0,
          "ErrorBoundary component not found",
          "Create ErrorBoundary.tsx for React error handling")
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
    found_groups = [p.name for p in app_dir.iterdir() if p.is_dir() and p.name.startswith("(") and p.name.endswith(")")]
    if not found_groups:
        f(177, "frontend", "low", "frontend/web_app/src/app/", 0,
          "No route groups found — organize routes by actor using (group) directories",
          "Create route groups like (auth)/, (tabs)/, (dashboard)/ for actor-based organization")


# ══════════════════════════════════════════════════════════════
# LAWS 178-186: WEB APP
# ══════════════════════════════════════════════════════════════

def _check_route_structure():
    """Law 178: page.tsx, layout.tsx, loading.tsx, error.tsx per route."""
    if not FRONTEND_ROOT.exists():
        return
    app_dir = FRONTEND_ROOT / "web_app" / "src" / "app"
    if not app_dir.exists():
        return
    for p in safe_rglob(app_dir, "page.tsx"):
        route_dir = p.parent
        rel_path = str(route_dir.relative_to(app_dir))
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
    if not (components_dir / "ui").exists():
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
        if re.search(r'<[A-Z][a-zA-Z]*[\s/>]|<[a-z]+[\s/>]', content):
            f(180, "web_app", "medium", str(p.relative_to(FRONTEND_ROOT)), 1,
              f"Hook file '{p.name}' contains JSX — hooks should not return JSX",
              "Move JSX to components; hooks should return data/state only")
    for p in hooks_dir.glob("*.tsx"):
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
    api_files = list(lib_dir.glob("*.ts"))
    if not any("api" in f.name.lower() or "client" in f.name.lower() for f in api_files):
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
          "Create src/services/ for domain-specific frontend services")
        return
    if not list(services_dir.glob("*.ts")):
        f(182, "web_app", "low", "frontend/web_app/src/services/", 0,
          "No service files found in services/",
          "Add service files like localizationService.ts, crossBorderService.ts")


def _check_theme_styling():
    """Law 183: Design tokens, Tailwind config, global CSS."""
    if not FRONTEND_ROOT.exists():
        return
    tailwind_config = FRONTEND_ROOT / "web_app" / "tailwind.config.js"
    if not tailwind_config.exists():
        tailwind_config = FRONTEND_ROOT / "web_app" / "tailwind.config.ts"
    if not tailwind_config.exists():
        f(183, "web_app", "high", "frontend/web_app/tailwind.config.js", 0,
          "tailwind.config.js not found",
          "Create tailwind.config.js with design tokens and content paths")
    global_css = FRONTEND_ROOT / "web_app" / "src" / "app" / "globals.css"
    if not global_css.exists():
        alt_css = FRONTEND_ROOT / "web_app" / "src" / "styles" / "globals.css"
        if not alt_css.exists():
            f(183, "web_app", "medium", "frontend/web_app/src/app/globals.css", 0,
              "globals.css not found — global styles missing",
              "Create globals.css with Tailwind directives and CSS custom properties")


def _check_web_types():
    """Law 184: Types from @zozi/shared + local definitions."""
    if not FRONTEND_ROOT.exists():
        return
    src_dir = FRONTEND_ROOT / "web_app" / "src"
    if not src_dir.exists():
        return
    has_shared_import = False
    for p in safe_rglob(src_dir, "*.ts*"):
        content = read(p)
        if content and "@zozi/shared" in content:
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
    if not (lib_dir / "utils.ts").exists():
        f(185, "web_app", "low", "frontend/web_app/src/lib/utils.ts", 0,
          "lib/utils.ts not found — pure utility functions missing",
          "Create lib/utils.ts for shared pure utility functions")


def _check_web_build():
    """Law 186: next build passes with no errors."""
    if not FRONTEND_ROOT.exists():
        return
    package_json = FRONTEND_ROOT / "web_app" / "package.json"
    if not package_json.exists():
        return
    content = read(package_json)
    if content and '"build"' not in content:
        f(186, "web_app", "high", "frontend/web_app/package.json", 0,
          "No build script found in package.json",
          'Add "build": "next build" script to package.json')


# ══════════════════════════════════════════════════════════════
# LAWS 187-194: MOBILE
# ══════════════════════════════════════════════════════════════

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
    match = re.search(r'"expo":\s*"([^"]+)"', content)
    if match:
        version = match.group(1).replace("^", "").replace("~", "").split(".")
        if len(version) >= 2:
            try:
                if int(version[0]) < 51:
                    f(187, "mobile", "high", "frontend/mobile_app/package.json", 0,
                      f"Expo SDK {match.group(1)} is below required 51",
                      "Upgrade to Expo SDK 51+ for latest features and security")
            except ValueError:
                pass
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
    has_auth_group = (app_dir / "(auth)").exists() or (app_dir / "(tabs)").exists()
    if not has_auth_group:
        f(188, "mobile", "medium", "frontend/mobile_app/app/(auth)/", 0,
          "No route groups (auth)/ or (tabs)/ found",
          "Create (auth)/ and (tabs)/ route groups for organized navigation")
    if not (app_dir / "admin").exists():
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
    if not (components_dir / "ui").exists():
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
    if not (lib_dir / "api.ts").exists():
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
    try:
        native_files = list(mobile_dir.rglob("*.native.ts")) + list(mobile_dir.rglob("*.native.tsx"))
        web_files = list(mobile_dir.rglob("*.web.ts")) + list(mobile_dir.rglob("*.web.tsx"))
    except (OSError, PermissionError):
        native_files, web_files = [], []
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
    if content and "zustand" not in content:
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
    if content and "expo-secure-store" not in content:
        f(193, "mobile", "high", "frontend/mobile_app/package.json", 0,
          "expo-secure-store not found — required for secure secret storage",
          'Add "expo-secure-store" to dependencies for storing tokens and secrets')


def _check_mobile_build():
    """Law 194: EAS Build. Expo Go for dev."""
    if not FRONTEND_ROOT.exists():
        return
    app_json = FRONTEND_ROOT / "mobile_app" / "app.json"
    app_config = FRONTEND_ROOT / "mobile_app" / "app.config.js"
    if not app_json.exists() and not app_config.exists():
        f(194, "mobile", "high", "frontend/mobile_app/app.json", 0,
          "No app.json or app.config.js found — Expo configuration missing",
          "Create app.json with Expo configuration for EAS Build")
        return
    eas_json = FRONTEND_ROOT / "mobile_app" / "eas.json"
    if not eas_json.exists():
        f(194, "mobile", "low", "frontend/mobile_app/eas.json", 0,
          "eas.json not found — EAS Build configuration missing",
          "Create eas.json with build profiles for EAS Build")


# ══════════════════════════════════════════════════════════════
# LAWS 195-200: SHARED
# ══════════════════════════════════════════════════════════════

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
    for fname in ["api-core.ts", "money.ts", "types.ts", "i18n.ts"]:
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
        if re.search(r'from\s+["\']\.\./.*web_app', content) or \
           re.search(r'from\s+["\']\.\./.*mobile_app', content) or \
           re.search(r'from\s+["\']@/web_app', content) or \
           re.search(r'from\s+["\']@/mobile_app', content):
            f(196, "shared", "critical", str(p.relative_to(FRONTEND_ROOT)), 1,
              "Shared file imports from app-specific code — shared must be platform-agnostic",
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
    if content and "react-native" in content.lower() and "Platform" not in content:
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


# ══════════════════════════════════════════════════════════════
# MAIN ENTRY POINT
# ══════════════════════════════════════════════════════════════

def run_checks():
    """Run all law checks for laws 101-200."""
    # Wiring (101-106)
    _check_kernel_isolation()
    _check_infrastructure_isolation()
    _check_job_wiring()
    _check_middleware_wiring()
    _check_shared_package_wiring()
    _check_frontend_backend_wiring()

    # Technology (107-122)
    _check_postgresql_in_prod()
    _check_sqlite_in_dev()
    _check_redis_usage()
    _check_redis_failure_handling()
    _check_nextjs_app_router()
    _check_react_server_components()
    _check_expo_router()
    _check_websocket_for_realtime()
    _check_celery_for_jobs()
    _check_email_via_smtp()
    _check_sms_via_twilio()
    _check_payment_gateways()
    _check_ai_ml_backends()
    _check_s3_storage()
    _check_image_processing()
    _check_leaflet_maps()

    # Provider Laws (123-131)
    _check_single_sdk_per_provider()
    _check_has_flags()
    _check_degrade_gracefully()
    _check_no_business_logic()
    _check_config_in_providers()
    _check_async_workers_for_cpu()
    _check_health_checks()
    _check_error_mapping()
    _check_mock_in_tests()

    # Module Laws (132-139)
    _check_module_structure()
    _check_per_module_auth()
    _check_router_file_naming()
    _check_router_registration()
    _check_public_vs_protected()
    _check_serializers_location()
    _check_five_modules_fixed()
    _check_route_prefixes()

    # Infrastructure Laws (140-149)
    _check_seven_subpackages()
    _check_database_infra()
    _check_redis_infra()
    _check_storage_infra()
    _check_messaging_infra()
    _check_observability_infra()
    _check_security_infra()
    _check_utils_infra()
    _check_canonical_base()
    _check_session_lifecycle()

    # Domain Laws (150-160)
    _check_domain_structure()
    _check_service_patterns()
    _check_model_patterns()
    _check_schema_patterns()
    _check_event_patterns()
    _check_port_patterns()
    _check_subscriber_patterns()
    _check_feature_patterns()
    _check_read_model_patterns()
    _check_policy_patterns()
    _check_domain_count()

    # RBAC (161-167)
    _check_rbac_catalog()
    _check_rbac_roles()
    _check_rbac_resolution()
    _check_rbac_dependencies()
    _check_rbac_service()
    _check_rbac_models()
    _check_frontend_permissions()

    # Frontend (168-177)
    _check_frontend_monorepo()
    _check_nextjs_version()
    _check_typescript_strict()
    _check_state_management()
    _check_data_fetching()
    _check_api_proxy()
    _check_styling()
    _check_forms()
    _check_error_handling()
    _check_route_groups()

    # Web App (178-186)
    _check_route_structure()
    _check_component_structure()
    _check_hook_patterns()
    _check_lib_patterns()
    _check_web_services()
    _check_theme_styling()
    _check_web_types()
    _check_web_utils()
    _check_web_build()

    # Mobile (187-194)
    _check_expo_sdk()
    _check_mobile_routes()
    _check_mobile_components()
    _check_mobile_lib()
    _check_platform_specific()
    _check_mobile_state()
    _check_mobile_storage()
    _check_mobile_build()

    # Shared (195-200)
    _check_shared_structure()
    _check_shared_no_app_imports()
    _check_shared_permissions_generated()
    _check_shared_cross_platform_types()
    _check_shared_api_core()
    _check_shared_money_formatting()
