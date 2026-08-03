"""Re-export logistics partner controller for backward compatibility."""
from controllers.logistics.logistics_partner_controller import *  # noqa: F401, F403

__all__ = [
    "get_partner",
    "get_partners",
    "create_partner",
    "update_partner",
    "delete_partner",
    "activate_partner",
    "deactivate_partner",
]