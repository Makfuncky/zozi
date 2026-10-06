"""Routers for the admin module — domain routers."""
from infrastructure.utils.router_loader import load_router_submodules

routers = []
public_routers = []

_module_names = [
    "accounts",
    "analytics",
    "audit",
    "catalog",
    "comms",
    "config_versions",
    "country",
    "customers",
    "disputes",
    "finance",
    "governance",
    "hr",
    "logistics",
    "orders",
    "permissions",
    "promotions",
    "security",
    "staff",
    "suppliers",
    "tickets",
]

# Routed through load_router_submodules so a submodule whose import raises is
# recorded with a full traceback and surfaced via boot_summary() /
# get_failed_imports(), instead of vanishing behind a single log line while the
# app booted healthy and its routes 404'd.
#
# This is how modules.admin.routers.tickets silently disappeared: it imported
# build_ticket_payload, which did not exist, and the whole /admin/tickets
# surface 404'd on an otherwise healthy-looking boot.
load_router_submodules(
    "modules.admin.routers", _module_names, routers, public_routers
)
