"""Temporary script: audit CSRF exempt prefixes against current routes."""
from main import app

csrf_exempt_prefixes = [
    '/payments/webhook',
    '/payments/tap/webhook',
    '/email/webhooks/',
    '/auth/oauth/',
    '/auth/verify-email',
    '/auth/resend-verification/public',
    '/auth/login',
    '/auth/refresh',
    '/auth/logout',
    '/auth/register',
    '/auth/forgot-password',
    '/auth/reset-password',
    '/email/newsletter',
    '/email/unsubscribe',
    '/coupons/validate',
    '/translate',
    '/chatbot/',
]

print("=== Checking exempt prefix status ===")
for prefix in csrf_exempt_prefixes:
    found = any(
        getattr(route, "path", "").startswith(prefix)
        for route in app.routes
    )
    print(f"{'OK' if found else 'STALE'}: {prefix}")

print()
print("=== POST routes without auth dependency (potential CSRF gaps) ===")
for route in app.routes:
    p = getattr(route, "path", "")
    methods = getattr(route, "methods", set())
    if "POST" not in methods:
        continue
    deps = getattr(route, "dependencies", []) or []
    exempt = any(p.startswith(e) for e in csrf_exempt_prefixes)
    auth_required = any(
        hasattr(d, "dependency") and "get_current_user" in str(d.dependency)
        for d in deps
    )
    if not exempt and not auth_required:
        print(f"  NON-AUTH POST: {p}")

