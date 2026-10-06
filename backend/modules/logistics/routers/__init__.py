"""Routers for the logistics module — domain routers."""
from infrastructure.utils.router_loader import load_router_submodules

routers = []
public_routers = []

_module_names = [
    "accounts",
    "analytics",
    "audit",
    "catalog",
    "comms",
    "country",
    "customers",
    "finance",
    "governance",
    "hr",
    "logistics",
    "orders",
    "promotions",
    "security",
    "suppliers",
]

# Routed through load_router_submodules so a submodule whose import raises is
# recorded with a full traceback and surfaced via boot_summary() /
# get_failed_imports(), instead of vanishing behind a single log line while the
# app booted healthy and its routes 404'd.
load_router_submodules(
    "modules.logistics.routers", _module_names, routers, public_routers
)
