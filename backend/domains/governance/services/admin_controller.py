"""Re-export aggregator for the fissioned controllers.admin.admin_controller API.
Thin composition surface so legacy router imports keep working during the
NEW_STRUCTURE migration. Each name resolves to its real domain/infra home.
"""
from __future__ import annotations

from domains.comms.services.shared.ticket.tickets_service import (
    list_tickets,
    reply_to_ticket,
)

from domains.comms.services.shared.ticket.tickets_write_service import (
    update_ticket_status,
)

from domains.governance.services.products.flat_admin_catalog_operations_service import (
    approve_product,
    reject_product,
)

from domains.governance.services.commerce.flat_admin_commerce_configuration_service import (
    create_coupon,
    list_coupons,
)

from domains.governance.services.treasury.flat_admin_treasury_status_service import (
    list_pending_payouts,
    verify_payout,
)

from domains.governance.services.analytics.flat_analytics_service import (
    get_analytics,
    get_analytics_timeseries,
    get_chatbot_analytics,
    get_customer_insights,
    get_top_products_analytics,
    get_user_growth_analytics,
)

from domains.governance.services.core.flat_bulk_ops_service import (
    bulk_archive_entities,
    bulk_category_change,
    bulk_restore_entities,
)

from domains.governance.services.settings.flat_database_service import (
    get_database_overview,
)

from domains.governance.services.permissions.flat_effective_permissions import (
    require_permission,
)

from domains.governance.services.settings.misc_service import (
    archive_entity,
    get_audit_log_page,
    get_available_audit_actions,
    hard_delete_entity,
    restore_entity,
)

from domains.governance.services.orders.flat_orders_service import (
    bulk_delete_orders_admin,
    bulk_update_order_status_admin,
    delete_order_admin,
    get_all_orders,
    refund_order,
    update_order_status,
    update_order_tracking,
)

from domains.governance.services.permissions.permissions_service import (
    get_hierarchy_permissions,
    get_staff_permission_catalog,
    update_role_permissions,
)

from domains.governance.services.products.flat_products_service import (
    bulk_delete_products_admin,
    bulk_product_moderation,
    delete_product_admin,
    get_all_products,
    get_pending_products,
    restore_product_admin,
    toggle_product_badge,
)

from domains.governance.services.commerce.flat_public_commerce_validation_service import (
    delete_coupon,
)

from domains.governance.services.suppliers.suppliers_service import (
    bulk_manage_suppliers,
    bulk_supplier_verification,
    get_all_suppliers,
    get_pending_suppliers,
    get_supplier_comparison,
    reject_supplier,
    verify_supplier,
)

from domains.governance.services.users.flat_users_service import (
    bulk_delete_users_admin,
    bulk_toggle_users_active,
    bulk_update_staff_accounts,
    bulk_update_users_role,
    create_staff_account,
    delete_bank_account_record,
    delete_staff_account,
    delete_user_admin,
    force_reset_password_admin,
    get_all_users,
    list_pending_bank_accounts,
    list_staff_accounts,
    toggle_user_active,
    update_staff_account,
    update_user_role,
    verify_bank_account,
)

from domains.orders.services.coupons_write_service import (
    update_coupon,
)

from infrastructure.security.country_access import (
    require_country_access,
)

from infrastructure.utils.dependencies import (
    get_current_user,
    require_admin,
)

# Best-effort aliases for names that no longer exist after the controllers
# fission. They resolve the import contract; refine semantics per-feature later.
get_current_admin = get_current_user
require_roles = require_admin
require_admin_2fa_enabled = require_admin
require_admin_2fa_verified = require_admin
from domains.comms.services.shared.ticket.tickets_write_service import get_ticket_with_details as get_ticket_detail
