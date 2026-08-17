"""Routers for the employee module (re-homed from flat backend/routers/)."""
import importlib

routers = []
public_routers = []

_module_names = [
    "accounting",
    "cash_management",
    "chat",
    "chat_api",
    "chat_enrichment",
    "chatbot",
    "comm",
    "comms_chat",
    "comms_unified",
    "comms_video",
    "email",
    "email_controller",
    "email_enrichment",
    "employees",
    "entity_chat",
    "entity_communication",
    "ess",
    "expense_controller",
    "expenses",
    "finance",
    "finance_automation",
    "finance_erp",
    "finance_package",
    "hierarchy",
    "hr",
    "hr_dashboard",
    "internal_channels",
    "internal_comms_channels",
    "invoices",
    "jobs",
    "lms",
    "messaging",
    "notifications",
    "okr",
    "payroll",
    "performance",
    "proxy_communication",
    "push_notifications",
    "risk",
    "shift_handover",
    "succession",
    "tickets",
    "trading",
    "travel",
    "treasury",
    "treasury_api",
    "video",
    "video_controller",
    "ws_chat",
]

for _n in _module_names:
    try:
        _m = importlib.import_module(f"modules.employee.routers.{_n}")
    except Exception as _e:  # noqa: BLE001
        import logging as _logging
        _logging.getLogger(__name__).error("Skipping router %s: %s", _n, _e)
        continue
    _r = getattr(_m, "router", None)
    if _r is not None:
        routers.append(_r)
    _pr = getattr(_m, "public_router", None)
    if _pr is not None:
        public_routers.append(_pr)
