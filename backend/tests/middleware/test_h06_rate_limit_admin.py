"""H-06: admin endpoints missing from rate-limit table — paired tests."""
from __future__ import annotations

import sys
from pathlib import Path

_BACKEND_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

from middleware.rate_limit_middleware import PATH_LIMITS, LOADTEST_PATH_LIMITS


class TestAdminRateLimitCoverage:
    """Admin paths must appear in PATH_LIMITS and LOADTEST_PATH_LIMITS."""

    def test_admin_prefix_covered_in_path_limits(self):
        prefixes = [p for p, _, _ in PATH_LIMITS]
        assert any(p == "/admin/" or p.startswith("/admin/") for p in prefixes), (
            "No /admin/ prefix in PATH_LIMITS"
        )
        assert any(p == "/api/v1/admin/" or p.startswith("/api/v1/admin/") for p in prefixes), (
            "No /api/v1/admin/ prefix in PATH_LIMITS"
        )

    def test_admin_specific_paths_covered(self):
        admin_paths = [
            "/admin/disputes",
            "/admin/staff",
            "/admin/tickets",
            "/admin/users",
            "/admin/ghost-employees",
            "/api/v1/admin/accounts/users",
            "/api/v1/admin/security/events",
            "/api/v1/admin/security/blacklist",
            "/api/v1/admin/command-center/dashboard",
            "/api/v1/admin/{employee_id}/audit-timeline",
            "/api/v1/admin/governance/config/checkout",
        ]
        for path in admin_paths:
            matched = any(path.startswith(prefix) for prefix, _, _ in PATH_LIMITS)
            assert matched, f"{path} is not covered by any PATH_LIMITS prefix"

    def test_loadtest_admin_prefix_covered(self):
        prefixes = [p for p, _, _ in LOADTEST_PATH_LIMITS]
        assert any(p == "/admin/" or p.startswith("/admin/") for p in prefixes), (
            "No /admin/ prefix in LOADTEST_PATH_LIMITS"
        )
        assert any(p == "/api/v1/admin/" or p.startswith("/api/v1/admin/") for p in prefixes), (
            "No /api/v1/admin/ prefix in LOADTEST_PATH_LIMITS"
        )

    def test_admin_security_has_stricter_limit(self):
        admin_security_limits = [(r, w) for p, r, w in PATH_LIMITS if "/security" in p]
        assert len(admin_security_limits) > 0, "No security-related limit in PATH_LIMITS"
        for requests, window in admin_security_limits:
            assert requests <= 3, (
                f"Security limit {requests}/{window}s is not strict enough; "
                f"benchmark mandates <=3 for privileged security routes"
            )

    def test_admin_tier_enforced_at_middleware(self):
        """Import middleware and verify _get_path_tier returns limits for admin paths."""
        from middleware.rate_limit_middleware import RateLimitMiddleware

        mw = RateLimitMiddleware.__new__(RateLimitMiddleware)
        # Direct admin route
        max_r, window = mw._get_path_tier("/admin/disputes")
        assert max_r == 5 and window == 60, (
            f"Expected /admin/disputes tier 5/60, got {max_r}/{window}"
        )
        # Versioned admin route
        max_r, window = mw._get_path_tier("/api/v1/admin/security/events")
        assert max_r == 5 and window == 60, (
            f"Expected /api/v1/admin/security/events tier 5/60, got {max_r}/{window}"
        )
        # Admin backup (stricter)
        max_r, window = mw._get_path_tier("/admin/backup")
        assert max_r == 3 and window == 60, (
            f"Expected /admin/backup tier 3/60, got {max_r}/{window}"
        )
        # Admin security (stricter)
        max_r, window = mw._get_path_tier("/admin/security")
        assert max_r == 3 and window == 60, (
            f"Expected /admin/security tier 3/60, got {max_r}/{window}"
        )
        # Versioned admin security
        max_r, window = mw._get_path_tier("/api/v1/admin/security/blacklist")
        assert max_r == 5 and window == 60, (
            f"Expected /api/v1/admin/security/blacklist tier 5/60, got {max_r}/{window}"
        )

    def test_nested_admin_paths_covered(self):
        from middleware.rate_limit_middleware import RateLimitMiddleware

        mw = RateLimitMiddleware.__new__(RateLimitMiddleware)
        nested_paths = [
            "/admin/disputes/bulk",
            "/admin/staff/bulk",
            "/admin/tickets/123/reply",
            "/admin/users/456/reset-password",
            "/api/v1/admin/accounts/users/bulk/archive",
            "/api/v1/admin/accounts/users/789/role",
            "/api/v1/admin/command-center/alerts/abc/resolve",
        ]
        for path in nested_paths:
            max_r, window = mw._get_path_tier(path)
            assert max_r < 60 or window < 60, (
                f"Nested admin path {path} fell through to default limit"
            )

    def test_health_path_not_broken(self):
        from middleware.rate_limit_middleware import RateLimitMiddleware

        mw = RateLimitMiddleware.__new__(RateLimitMiddleware)
        # Health endpoints should still resolve a tier (default 60/60 if not explicitly listed)
        max_r, window = mw._get_path_tier("/health")
        assert max_r > 0 and window > 0, "Health path should still resolve a valid tier"

    def test_ordinary_user_traffic_not_broken(self):
        from middleware.rate_limit_middleware import RateLimitMiddleware

        mw = RateLimitMiddleware.__new__(RateLimitMiddleware)
        user_paths = ["/payments", "/cart", "/orders", "/products/US"]
        for path in user_paths:
            max_r, window = mw._get_path_tier(path)
            assert max_r > 0 and window > 0, f"User path {path} should still resolve a valid tier"
