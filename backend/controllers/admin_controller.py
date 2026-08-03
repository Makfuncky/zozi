"""Backward-compatible re-exports from the admin subpackage.

DEPRECATED: The controllers.admin subpackage was reorganized into domain
folders (controllers/{domain}/admin_*_controller.py) to comply with the
architecture governance contract. Update imports to the new locations.

Routers that still import from controllers.admin_controller will
continue to work for backward compatibility.
"""
import logging

# Auth & security (controllers/security/)
from controllers.security.auth import (
    require_admin,
    require_admin_2fa_enabled,
    require_admin_2fa_verified,
    require_country_access,
    require_permission,
    require_roles,
    get_current_admin,
)
from controllers.security.auth_controller import get_current_user
from controllers.security.permissions import (
    get_hierarchy_permissions,
    update_role_permissions,
    load_role_permission_settings,
    get_staff_permission_catalog,
)

# Analytics (controllers/analytics/)
from controllers.analytics.admin_analytics_controller import (
    get_analytics,
    get_analytics_timeseries,
    get_top_products_analytics,
    get_user_growth_analytics,
    get_chatbot_analytics,
    get_customer_insights,
    ROLE_PERMISSION_MAP,
)
from controllers.supplier.admin_suppliers_controller import get_supplier_comparison

# Orders (controllers/orders/)
from controllers.orders.admin_orders_controller import (
    get_all_orders,
    delete_order_admin,
    update_order_status,
    refund_order,
    update_order_tracking,
    bulk_delete_orders_admin,
    bulk_update_order_status_admin,
)

# Catalog / Products (controllers/catalog/)
from controllers.catalog.products import (
    get_all_products,
    delete_product_admin,
    restore_product_admin,
    get_pending_products,
    approve_product,
    reject_product,
    toggle_product_badge,
    bulk_delete_products_admin,
    bulk_product_moderation,
)
from controllers.core.admin_bulk_ops_controller import (
    bulk_archive_entities,
    bulk_restore_entities,
    bulk_category_change,
)

# Suppliers (controllers/supplier/)
from controllers.supplier.admin_suppliers_controller import (
    get_all_suppliers,
    get_pending_suppliers,
    verify_supplier,
    reject_supplier,
    bulk_manage_suppliers,
    bulk_supplier_verification,
)

# Commerce / Coupons (controllers/commerce/)
from controllers.commerce.admin_coupons_controller import (
    list_coupons,
    create_coupon,
    update_coupon,
    delete_coupon,
)

# Communication / Tickets (controllers/communication/)
from controllers.communication.admin_tickets_controller import (
    list_tickets,
    get_ticket_detail,
    reply_to_ticket,
    update_ticket_status,
)

# Treasury / Payouts (controllers/treasury/)
from controllers.treasury.admin_payouts_controller import (
    list_pending_payouts,
    verify_payout,
)

# Core / Users & Operations (controllers/core/)
from controllers.core.admin_operations_controller import (
    archive_entity,
    restore_entity,
    hard_delete_entity,
    get_audit_log_page,
    get_available_audit_actions,
    soft_delete,
    restore,
    hard_delete,
)
from controllers.core.admin_users_controller import (
    get_all_users,
    update_user_role,
    toggle_user_active,
    delete_user_admin,
    bulk_delete_users_admin,
    bulk_toggle_users_active,
    bulk_update_users_role,
    force_reset_password_admin,
    create_staff_account,
    update_staff_account,
    bulk_update_staff_accounts,
    delete_staff_account,
    list_staff_accounts,
    delete_bank_account_record,
    verify_bank_account,
    list_pending_bank_accounts,
)
from controllers.core.admin_database_controller import get_database_overview

logger = logging.getLogger(__name__)

__all__ = [
    "require_admin",
    "require_admin_2fa_enabled",
    "require_admin_2fa_verified",
    "require_country_access",
    "require_permission",
    "require_roles",
    "get_current_admin",
    "get_current_user",
    "get_hierarchy_permissions",
    "update_role_permissions",
    "load_role_permission_settings",
    "get_staff_permission_catalog",
    "get_analytics",
    "get_analytics_timeseries",
    "get_top_products_analytics",
    "get_user_growth_analytics",
    "get_chatbot_analytics",
    "get_customer_insights",
    "get_supplier_comparison",
    "ROLE_PERMISSION_MAP",
    "get_all_orders",
    "delete_order_admin",
    "update_order_status",
    "refund_order",
    "update_order_tracking",
    "bulk_delete_orders_admin",
    "bulk_update_order_status_admin",
    "get_all_products",
    "delete_product_admin",
    "restore_product_admin",
    "get_pending_products",
    "approve_product",
    "reject_product",
    "toggle_product_badge",
    "bulk_delete_products_admin",
    "bulk_product_moderation",
    "bulk_archive_entities",
    "bulk_restore_entities",
    "bulk_category_change",
    "get_all_suppliers",
    "get_pending_suppliers",
    "verify_supplier",
    "reject_supplier",
    "bulk_manage_suppliers",
    "bulk_supplier_verification",
    "list_coupons",
    "create_coupon",
    "update_coupon",
    "delete_coupon",
    "list_tickets",
    "get_ticket_detail",
    "reply_to_ticket",
    "update_ticket_status",
    "list_pending_payouts",
    "verify_payout",
    "archive_entity",
    "restore_entity",
    "hard_delete_entity",
    "get_audit_log_page",
    "get_available_audit_actions",
    "soft_delete",
    "restore",
    "hard_delete",
    "get_all_users",
    "update_user_role",
    "toggle_user_active",
    "delete_user_admin",
    "bulk_delete_users_admin",
    "bulk_toggle_users_active",
    "bulk_update_users_role",
    "force_reset_password_admin",
    "create_staff_account",
    "update_staff_account",
    "bulk_update_staff_accounts",
    "delete_staff_account",
    "list_staff_accounts",
    "delete_bank_account_record",
    "verify_bank_account",
    "list_pending_bank_accounts",
    "get_database_overview",
]
