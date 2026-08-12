"""Backward-compatible re-exports from the admin subpackage.

Routers that still import from controllers.admin.admin_controller will
continue to work. All business logic lives in services/admin/*.py; these
thin aliases preserve the legacy call signatures (entity_type string +
user-context dict) the routers expect.
"""
from controllers.admin import *  # noqa: F401, F403

from services.admin.bulk_ops_service import (  # noqa: F401
    bulk_archive_entities,
    bulk_category_change,
    bulk_restore_entities,
)
from services.admin.misc_service import (  # noqa: F401
    archive_entity,
    hard_delete_entity,
    restore_entity,
)
from services.admin.orders_service import update_order_status  # noqa: F401
from services.admin.products_service import bulk_product_moderation  # noqa: F401
from services.admin.suppliers_service import get_all_suppliers  # noqa: F401
from services.admin.users_service import get_all_users  # noqa: F401
from services.admin.users_service import update_user_role  # noqa: F401

from services.admin.users_service import toggle_user_active

from services.admin.suppliers_service import verify_supplier
from services.admin.analytics_service import get_analytics
from services.admin.analytics_service import get_analytics_timeseries
from services.admin.users_service import list_staff_accounts
from services.admin.suppliers_service import get_pending_suppliers
from services.admin.orders_service import get_all_orders
from services.admin.coupons_service import list_coupons
from services.admin.users_service import bulk_update_users_role
from services.admin.products_service import approve_product
from services.admin.users_service import bulk_toggle_users_active
from services.admin.database_service import get_database_overview
from services.admin.misc_service import get_audit_log_page
from services.admin.misc_service import get_available_audit_actions
from services.admin.users_service import force_reset_password_admin
from services.admin.tickets_service import get_ticket_detail
from services.admin.products_service import toggle_product_badge
from services.admin.users_service import delete_bank_account_record
from services.admin.users_service import create_staff_account
from services.admin.tickets_service import reply_to_ticket
from services.admin.coupons_service import update_coupon
from services.admin.permissions_service import update_role_permissions
from services.admin.products_service import reject_product
from services.admin.coupons_service import create_coupon
from services.admin.orders_service import refund_order
from services.admin.products_service import get_pending_products
from services.admin.orders_service import update_order_tracking
from services.admin.users_service import delete_staff_account
from services.admin.suppliers_service import get_supplier_comparison
from services.admin.payouts_service import list_pending_payouts
from services.admin.analytics_service import get_top_products_analytics
from services.admin.orders_service import bulk_delete_orders_admin
from services.admin.orders_service import bulk_update_order_status_admin
from services.admin.tickets_service import list_tickets
from services.admin.products_service import restore_product_admin
from services.admin.users_service import delete_user_admin
from services.admin.suppliers_service import reject_supplier
from services.admin.users_service import list_pending_bank_accounts
from services.admin.payouts_service import verify_payout
from services.admin.orders_service import delete_order_admin
from services.admin.users_service import update_staff_account
from services.admin.analytics_service import get_customer_insights
from services.admin.products_service import bulk_delete_products_admin
from services.admin.analytics_service import get_chatbot_analytics
from services.admin.users_service import bulk_update_staff_accounts
from services.admin.coupons_service import delete_coupon
from services.admin.permissions_service import get_hierarchy_permissions
from services.admin.products_service import delete_product_admin
from services.admin.suppliers_service import bulk_manage_suppliers
from services.admin.suppliers_service import bulk_supplier_verification
from services.admin.permissions_service import get_staff_permission_catalog
from services.admin.users_service import bulk_delete_users_admin
from services.admin.products_service import get_all_products
from services.admin.analytics_service import get_user_growth_analytics
from services.admin.tickets_service import update_ticket_status
from services.admin.users_service import verify_bank_account
