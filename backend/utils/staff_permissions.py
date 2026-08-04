from typing import Iterable


STAFF_PERMISSION_GROUPS: tuple[dict[str, object], ...] = (
    {
        "key": "governance",
        "label": "Governance",
        "permissions": (
            "analytics.view",
            "audit.read",
            "hierarchy.view",
        ),
    },
    {
        "key": "users",
        "label": "Users & Staff",
        "permissions": (
            "users.read",
            "users.role.update",
            "users.toggle_active",
            "users.delete",
            "users.reset_password",
            "staff.view",
            "staff.create",
            "staff.manage",
            "staff.delete",
        ),
    },
    {
        "key": "commerce",
        "label": "Commerce Operations",
        "permissions": (
            "orders.manage",
            "products.manage",
            "moderation.suppliers",
            "moderation.products",
            "tickets.manage",
            "coupons.manage",
            "payouts.verify",
        ),
    },
    {
        "key": "countries",
        "label": "Country Management",
        "permissions": (
            "countries.configure",
            "countries.payouts",
            "countries.commissions",
            "countries.promotions",
            "countries.finance",
            "countries.banners",
            "countries.email",
        ),
    },
)


DEFAULT_ROLE_PERMISSION_MAP: dict[str, set[str]] = {
    "admin": {
        "analytics.view",
        "audit.read",
        "hierarchy.view",
        "users.read",
        "users.role.update",
        "users.toggle_active",
        "users.delete",
        "users.reset_password",
        "staff.view",
        "staff.create",
        "staff.manage",
        "staff.delete",
        "orders.manage",
        "products.manage",
        "moderation.suppliers",
        "moderation.products",
        "coupons.manage",
        "tickets.manage",
        "payouts.verify",
        "countries.configure",
        "countries.payouts",
        "countries.commissions",
        "countries.promotions",
        "countries.finance",
        "countries.banners",
        "countries.email",
    },
    "sub_admin": {
        "analytics.view",
        "audit.read",
        "hierarchy.view",
        "users.read",
        "users.toggle_active",
        "staff.view",
        "orders.manage",
        "products.manage",
        "moderation.suppliers",
        "moderation.products",
        "coupons.manage",
        "tickets.manage",
        "payouts.verify",
        "countries.configure",
        "countries.payouts",
        "countries.commissions",
        "countries.promotions",
        "countries.finance",
        "countries.banners",
        "countries.email",
    },
    "moderator": {
        "analytics.view",
        "audit.read",
        "hierarchy.view",
        "staff.view",
        "products.manage",
        "moderation.suppliers",
        "moderation.products",
        "tickets.manage",
    },
    "support": {
        "analytics.view",
        "audit.read",
        "hierarchy.view",
        "staff.view",
        "orders.manage",
        "tickets.manage",
    },
    "country_head": {
        "analytics.view",
        "audit.read",
        "staff.view",
        "orders.manage",
        "products.manage",
        "moderation.suppliers",
        "moderation.products",
        "tickets.manage",
        "coupons.manage",
        "payouts.verify",
        "countries.configure",
        "countries.payouts",
        "countries.commissions",
        "countries.promotions",
        "countries.finance",
    },
    "country_manager": {
        "analytics.view",
        "audit.read",
        "staff.view",
        "orders.manage",
        "products.manage",
        "moderation.suppliers",
        "moderation.products",
        "tickets.manage",
        "coupons.manage",
        "countries.promotions",
        "countries.finance",
        "countries.banners",
        "countries.email",
    },
}


KNOWN_ROLE_PERMISSIONS = frozenset(
    permission
    for group in STAFF_PERMISSION_GROUPS
    for permission in group["permissions"]
)


def sanitize_staff_permissions(permissions: Iterable[str] | None) -> list[str]:
    if permissions is None:
        return []

    normalized: list[str] = []
    seen: set[str] = set()
    for permission in permissions:
        candidate = str(permission).strip()
        if not candidate or candidate not in KNOWN_ROLE_PERMISSIONS or candidate in seen:
            continue
        seen.add(candidate)
        normalized.append(candidate)
    return normalized


def default_permissions_for_role(role: str | None) -> list[str]:
    if role is None:
        return []
    return sorted(DEFAULT_ROLE_PERMISSION_MAP.get(role, set()))

