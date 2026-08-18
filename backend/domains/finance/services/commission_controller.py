"""controllers.finance.commission_controller controller.

Business logic is delegated to services.finance.commission_service (routers -> controllers -> services)."""

from domains.finance.services.commission_service import _build_list_page_payload
from domains.finance.services.commission_service import _category_to_slug
from domains.finance.services.commission_service import _float_or_none
from domains.finance.services.commission_service import _require_admin
from domains.finance.services.commission_service import _serialize_agreement
from domains.finance.services.commission_service import _serialize_badge_tier
from domains.finance.services.commission_service import _serialize_category_rate
from domains.finance.services.commission_service import _serialize_global_config
from domains.finance.services.commission_service import _serialize_ledger_entry
from domains.finance.services.commission_service import _serialize_override
from domains.finance.services.commission_service import _supplier_rate_snapshot
from domains.finance.services.commission_service import create_ledger_adjustment
from domains.finance.services.commission_service import delete_product_commission_override
from domains.finance.services.commission_service import delete_supplier_commission_override
from domains.finance.services.commission_service import get_effective_rate
from domains.finance.services.commission_service import get_global_config
from domains.finance.services.commission_service import get_product_commission_override
from domains.finance.services.commission_service import get_supplier_commission
from domains.finance.services.commission_service import get_supplier_policy_snapshot
from domains.finance.services.commission_service import list_all_supplier_commissions
from domains.finance.services.commission_service import list_badge_tiers
from domains.finance.services.commission_service import list_category_rates
from domains.finance.services.commission_service import list_ledger_entries
from domains.finance.services.commission_service import list_product_commission_overrides
from domains.finance.services.commission_service import preview_commission
from domains.finance.services.commission_service import set_product_commission_override
from domains.finance.services.commission_service import set_supplier_commission
from domains.finance.services.commission_service import update_badge_tier
from domains.finance.services.commission_service import update_category_rate
from domains.finance.services.commission_service import update_global_config

__all__ = [
    "_build_list_page_payload", "_category_to_slug", "_float_or_none", "_require_admin", "_serialize_agreement", "_serialize_badge_tier",
    "_serialize_category_rate", "_serialize_global_config", "_serialize_ledger_entry", "_serialize_override", "_supplier_rate_snapshot", "create_ledger_adjustment",
    "delete_product_commission_override", "delete_supplier_commission_override", "get_effective_rate", "get_global_config", "get_product_commission_override", "get_supplier_commission",
    "get_supplier_policy_snapshot", "list_all_supplier_commissions", "list_badge_tiers", "list_category_rates", "list_ledger_entries", "list_product_commission_overrides",
    "preview_commission", "set_product_commission_override", "set_supplier_commission", "update_badge_tier", "update_category_rate", "update_global_config"
]
