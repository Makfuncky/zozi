"""Broker re-exporting the cash-management controller surface.

The historical ``cash_management_controller`` module was consolidated into the
``CashManagementService`` class in ``cash_management_service``. This thin module
keeps the old import path alive (Law 3 sanctioned re-export) by exposing the
service methods as module-level callables that take ``db`` as their first
argument, matching how callers (e.g. the employee finance router) invoke them.
"""
from domains.finance.services.treasury.cash_management_service import *  # noqa: F401,F403
from domains.finance.services.treasury.cash_management_service import CashManagementService


def _make_wrapper(method_name: str):
    method = getattr(CashManagementService, method_name)

    def _wrapper(db, *args, **kwargs):
        return method(CashManagementService(db), *args, **kwargs)

    _wrapper.__name__ = method_name
    _wrapper.__doc__ = getattr(method, "__doc__", None)
    return _wrapper


for _name in dir(CashManagementService):
    if _name.startswith("_"):
        continue
    _attr = getattr(CashManagementService, _name)
    if callable(_attr) and _name not in globals():
        globals()[_name] = _make_wrapper(_name)
