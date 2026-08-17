"""Country domain — AXIS 3 feature atoms (permission catalog seed).

Single-sourced here; aggregated by ``rbac/catalog.py``. The strings below are the
canonical permission atoms for the country domain. CI must fail on any
``require_feature("country.*")`` literal that is not present in this map.

Seeded from ``rbac/effective_permissions.py`` (country.configure, country.staff.assign,
country.reports.view, country.*) and expanded with atoms implied by the country
service surface (tax, communications, versioning, payouts, localization, cross-border).
"""

from __future__ import annotations

FEATURES: dict[str, dict] = {
    "country.configure": {
        "label": "Configure Country",
        "risk": "high",
        "actions": ["read", "write", "approve"],
        "description": "Manage country config: identity, tax, logistics, commissions, payments, legal, regions, suppliers, payouts.",
    },
    "country.staff.assign": {
        "label": "Assign Country Staff",
        "risk": "high",
        "actions": ["read", "assign", "unassign"],
        "description": "Assign/unassign users to a country with a country-scoped role (maker-checker required).",
    },
    "country.reports.view": {
        "label": "View Country Reports",
        "risk": "medium",
        "actions": ["read"],
        "description": "Read country-scoped analytics and operational reports.",
    },
    "country.tax.manage": {
        "label": "Manage Country Tax",
        "risk": "high",
        "actions": ["read", "write", "preview"],
        "description": "Draft and publish country tax rates and category tax rates.",
    },
    "country.communications.send": {
        "label": "Send Country Communication",
        "risk": "medium",
        "actions": ["read", "send"],
        "description": "List and send internal country communications; mark read.",
    },
    "country.versioning.approve": {
        "label": "Approve Country Version",
        "risk": "high",
        "actions": ["read", "approve", "publish", "rollback"],
        "description": "Approve/publish/rollback country config version drafts.",
    },
    "country.payouts.manage": {
        "label": "Manage Country Payout Rules",
        "risk": "high",
        "actions": ["read", "create", "delete"],
        "description": "Manage country payout rule categories and products.",
    },
    "country.localization.manage": {
        "label": "Manage Country Localization",
        "risk": "low",
        "actions": ["read", "write"],
        "description": "Manage numeral system, RTL layout, address format, holidays, delivery zones.",
    },
    "country.cross_border.view": {
        "label": "View Cross-Border Sessions",
        "risk": "low",
        "actions": ["read"],
        "description": "View cross-country customer sessions and conversion tracking.",
    },
}


def all_features() -> list[str]:
    return sorted(FEATURES.keys())


def is_known(feature: str) -> bool:
    if feature in FEATURES:
        return True
    # Support wildcard form, e.g. "country.*"
    if feature.endswith(".*"):
        prefix = feature[:-1]
        return any(f.startswith(prefix) for f in FEATURES)
    return False
