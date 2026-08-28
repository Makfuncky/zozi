"""governance domain — AXIS 3 feature atoms (permission catalog seed).

Single-sourced here; aggregated by ``rbac/catalog.py``. The strings below are the
canonical permission atoms for the governance domain. CI must fail on any
``require_feature("governance.*")`` literal that is not present in this map.
"""

from __future__ import annotations

FEATURES: dict[str, dict] = {
    # -- Permission & Role management -------------------------------------------
    "governance.permission.create": {
        "label": "Create Permission",
        "risk": "critical",
        "actions": ["read", "write"],
        "description": "Create a new permission atom and assign it to a category.",
    },
    "governance.permission.read": {
        "label": "View Permissions",
        "risk": "medium",
        "actions": ["read"],
        "description": "View permission catalog, categories, and role assignments.",
    },
    "governance.permission.update": {
        "label": "Update Permission",
        "risk": "critical",
        "actions": ["read", "write"],
        "description": "Update permission metadata and role-permission mappings.",
    },
    "governance.permission.delete": {
        "label": "Delete Permission",
        "risk": "critical",
        "actions": ["read", "write", "delete"],
        "description": "Remove a permission atom from the catalog.",
    },
    "governance.role.assign": {
        "label": "Assign Role",
        "risk": "critical",
        "actions": ["read", "write", "approve"],
        "description": "Assign or change a user's role and staff permissions.",
    },
    "governance.role.permissions.update": {
        "label": "Update Role Permissions",
        "risk": "critical",
        "actions": ["read", "write"],
        "description": "Modify the permission set assigned to a role.",
    },
    # -- User management ---------------------------------------------------------
    "governance.user.create": {
        "label": "Create User",
        "risk": "high",
        "actions": ["read", "write"],
        "description": "Register a new user account and assign an initial role.",
    },
    "governance.user.read": {
        "label": "View User",
        "risk": "medium",
        "actions": ["read"],
        "description": "View user account details, profile, and activity.",
    },
    "governance.user.update": {
        "label": "Update User",
        "risk": "high",
        "actions": ["read", "write"],
        "description": "Update user account fields, role, and active status.",
    },
    "governance.user.delete": {
        "label": "Delete User",
        "risk": "high",
        "actions": ["read", "write", "delete"],
        "description": "Soft-delete or hard-delete a user account.",
    },
    "governance.user.toggle_active": {
        "label": "Toggle User Active",
        "risk": "high",
        "actions": ["read", "write"],
        "description": "Activate or deactivate a user account.",
    },
    "governance.user.bulk_manage": {
        "label": "Bulk Manage Users",
        "risk": "critical",
        "actions": ["read", "write", "delete"],
        "description": "Perform bulk operations on multiple user accounts.",
    },
    "governance.user.force_reset_password": {
        "label": "Force Password Reset",
        "risk": "high",
        "actions": ["read", "write"],
        "description": "Forcefully reset a user's password.",
    },
    # -- Staff management --------------------------------------------------------
    "governance.staff.create": {
        "label": "Create Staff Account",
        "risk": "high",
        "actions": ["read", "write"],
        "description": "Create a new staff account with role assignments.",
    },
    "governance.staff.update": {
        "label": "Update Staff Account",
        "risk": "high",
        "actions": ["read", "write"],
        "description": "Update staff account details and permissions.",
    },
    "governance.staff.delete": {
        "label": "Delete Staff Account",
        "risk": "high",
        "actions": ["read", "write", "delete"],
        "description": "Remove a staff account from the system.",
    },
    "governance.staff.bulk_update": {
        "label": "Bulk Update Staff",
        "risk": "critical",
        "actions": ["read", "write"],
        "description": "Update multiple staff accounts in bulk.",
    },
    # -- Supplier management -----------------------------------------------------
    "governance.supplier.verify": {
        "label": "Verify Supplier",
        "risk": "high",
        "actions": ["read", "write", "approve"],
        "description": "Verify a supplier account and grant marketplace access.",
    },
    "governance.supplier.reject": {
        "label": "Reject Supplier",
        "risk": "high",
        "actions": ["read", "write"],
        "description": "Reject a supplier's verification request.",
    },
    "governance.supplier.manage": {
        "label": "Manage Suppliers",
        "risk": "high",
        "actions": ["read", "write", "approve"],
        "description": "Manage supplier accounts, status, and trading permissions.",
    },
    "governance.supplier.bulk_verify": {
        "label": "Bulk Verify Suppliers",
        "risk": "critical",
        "actions": ["read", "write", "approve"],
        "description": "Verify or reject multiple suppliers in bulk.",
    },
    # -- Order management --------------------------------------------------------
    "governance.order.status_update": {
        "label": "Update Order Status",
        "risk": "medium",
        "actions": ["read", "write"],
        "description": "Change the status of an existing order.",
    },
    "governance.order.refund": {
        "label": "Refund Order",
        "risk": "high",
        "actions": ["read", "write"],
        "description": "Issue a refund for an order.",
    },
    "governance.order.delete": {
        "label": "Delete Order",
        "risk": "high",
        "actions": ["read", "write", "delete"],
        "description": "Remove an order from the system.",
    },
    "governance.order.bulk_status_update": {
        "label": "Bulk Update Orders",
        "risk": "high",
        "actions": ["read", "write"],
        "description": "Update status or refund multiple orders in bulk.",
    },
    "governance.order.tracking_update": {
        "label": "Update Tracking",
        "risk": "low",
        "actions": ["read", "write"],
        "description": "Update shipment tracking information for an order.",
    },
    # -- Product management ------------------------------------------------------
    "governance.product.approve": {
        "label": "Approve Product",
        "risk": "medium",
        "actions": ["read", "write", "approve"],
        "description": "Approve a product for marketplace listing.",
    },
    "governance.product.reject": {
        "label": "Reject Product",
        "risk": "medium",
        "actions": ["read", "write"],
        "description": "Reject a product listing request.",
    },
    "governance.product.delete": {
        "label": "Delete Product",
        "risk": "high",
        "actions": ["read", "write", "delete"],
        "description": "Remove a product from the marketplace.",
    },
    "governance.product.restore": {
        "label": "Restore Product",
        "risk": "medium",
        "actions": ["read", "write"],
        "description": "Restore a previously deleted product.",
    },
    "governance.product.bulk_moderation": {
        "label": "Bulk Moderate Products",
        "risk": "high",
        "actions": ["read", "write", "approve"],
        "description": "Approve or reject multiple products in bulk.",
    },
    "governance.product.toggle_badge": {
        "label": "Toggle Product Badge",
        "risk": "low",
        "actions": ["read", "write"],
        "description": "Toggle featured or verification badges on a product.",
    },
    # -- Treasury & Payouts ------------------------------------------------------
    "governance.treasury.read": {
        "label": "View Treasury",
        "risk": "medium",
        "actions": ["read"],
        "description": "View treasury reports and financial summaries.",
    },
    "governance.treasury.verify_payout": {
        "label": "Verify Payout",
        "risk": "high",
        "actions": ["read", "write", "approve"],
        "description": "Verify and approve a pending payout.",
    },
    "governance.treasury.record_remittance": {
        "label": "Record Remittance",
        "risk": "medium",
        "actions": ["read", "write"],
        "description": "Record a COD remittance or settlement.",
    },
    # -- Fraud & Security ---------------------------------------------------------
    "governance.fraud.read": {
        "label": "View Fraud Events",
        "risk": "medium",
        "actions": ["read"],
        "description": "View fraud detection events and risk scores.",
    },
    "governance.fraud.manage": {
        "label": "Manage Fraud Cases",
        "risk": "high",
        "actions": ["read", "write", "approve"],
        "description": "Manage fraud cases, whitelist, and blacklist entries.",
    },
    "governance.security.incident.read": {
        "label": "View Security Incidents",
        "risk": "medium",
        "actions": ["read"],
        "description": "View security incidents and war-room entries.",
    },
    "governance.security.incident.manage": {
        "label": "Manage Security Incidents",
        "risk": "high",
        "actions": ["read", "write"],
        "description": "Create, update, and resolve security incidents.",
    },
    "governance.risk.read": {
        "label": "View Risk Scores",
        "risk": "medium",
        "actions": ["read"],
        "description": "View risk scores and threat intelligence data.",
    },
    "governance.risk.manage": {
        "label": "Manage Risk",
        "risk": "high",
        "actions": ["read", "write"],
        "description": "Manage risk thresholds and automated response rules.",
    },
    # -- Audit & Compliance ------------------------------------------------------
    "governance.audit.read": {
        "label": "View Audit Trail",
        "risk": "medium",
        "actions": ["read"],
        "description": "View admin activity logs and audit trails.",
    },
    "governance.compliance.read": {
        "label": "View Compliance",
        "risk": "medium",
        "actions": ["read"],
        "description": "View compliance status and data residency information.",
    },
    "governance.retention.manage": {
        "label": "Manage Data Retention",
        "risk": "high",
        "actions": ["read", "write", "delete"],
        "description": "Configure and execute data retention policies.",
    },
    # -- Analytics & Reporting ---------------------------------------------------
    "governance.analytics.read": {
        "label": "View Analytics",
        "risk": "low",
        "actions": ["read"],
        "description": "View governance dashboards and analytics reports.",
    },
    "governance.export.read": {
        "label": "Export Data",
        "risk": "medium",
        "actions": ["read"],
        "description": "Export governance data and reports.",
    },
    # -- Geography & Country -----------------------------------------------------
    "governance.geography.read": {
        "label": "View Geography Config",
        "risk": "low",
        "actions": ["read"],
        "description": "View country and geographic configuration.",
    },
    "governance.geography.manage": {
        "label": "Manage Geography",
        "risk": "high",
        "actions": ["read", "write"],
        "description": "Manage country settings, zones, and restrictions.",
    },
    # -- System & Database -------------------------------------------------------
    "governance.system.health": {
        "label": "View System Health",
        "risk": "low",
        "actions": ["read"],
        "description": "View database health and system status.",
    },
    "governance.database.manage": {
        "label": "Manage Database",
        "risk": "critical",
        "actions": ["read", "write"],
        "description": "Perform database maintenance and management operations.",
    },
    # -- Legacy role/permission/policy atoms (from services/features.py) -------
    "governance.roles.read": {
        "label": "View Roles",
        "risk": "low",
        "actions": ["read"],
        "description": "View governance roles and their permission assignments.",
    },
    "governance.roles.manage": {
        "label": "Manage Roles",
        "risk": "high",
        "actions": ["read", "create", "update", "delete"],
        "description": "Create, update, and delete governance roles and assign permissions.",
    },
    "governance.permissions.read": {
        "label": "View Permissions",
        "risk": "low",
        "actions": ["read"],
        "description": "View the permission catalog and feature registry.",
    },
    "governance.permissions.assign": {
        "label": "Assign Permissions",
        "risk": "high",
        "actions": ["read", "create", "update"],
        "description": "Assign and revoke permissions to roles and users.",
    },
    "governance.policies.read": {
        "label": "View Policies",
        "risk": "low",
        "actions": ["read"],
        "description": "View governance policies, terms, and acceptable use agreements.",
    },
    "governance.policies.manage": {
        "label": "Manage Policies",
        "risk": "medium",
        "actions": ["read", "create", "update", "delete"],
        "description": "Create and manage governance policies and compliance frameworks.",
    },
    "governance.user.ban": {
        "label": "Ban/Suspend Users",
        "risk": "high",
        "actions": ["read", "update"],
        "description": "Ban or suspend user accounts for policy violations.",
    },
    "governance.moderation": {
        "label": "Content Moderation",
        "risk": "medium",
        "actions": ["read", "update", "delete"],
        "description": "Moderate user-generated content and enforce community guidelines.",
    },
    "governance.referral.read": {
        "label": "View Referrals",
        "risk": "low",
        "actions": ["read"],
        "description": "View referral program data and referral history.",
    },
    "governance.access.read": {
        "label": "View Access Records",
        "risk": "medium",
        "actions": ["read"],
        "description": "View access control records and permission audit trails.",
    },
    "governance.dispute.read": {
        "label": "View Disputes",
        "risk": "medium",
        "actions": ["read"],
        "description": "View governance disputes and resolution records.",
    },
}


def all_features() -> list[str]:
    return sorted(FEATURES.keys())


def is_known(feature: str) -> bool:
    if feature in FEATURES:
        return True
    # Support wildcard form, e.g. "governance.*"
    if feature.endswith(".*"):
        prefix = feature[:-1]
        return any(f.startswith(prefix) for f in FEATURES)
    return False
