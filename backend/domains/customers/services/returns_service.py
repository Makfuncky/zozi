"""Customer-domain returns service (architecture realignment bridge).

The customer module router previously reached directly into
``domains.orders.services.returns_controller`` / ``returns_service``. Per
ARCHITECTURE_DIAGRAM.md the customer module must depend only on the customers
domain, so this module re-exports the return operations from the orders domain
service implementations. The orders domain retains ownership of the
``ReturnRequest`` model and its write orchestration; this is a sanctioned
cross-domain delegation surface (routers -> customers.services -> orders.services).
"""
from __future__ import annotations

from typing import Any


def bulk_update_return_requests(*args, **kwargs):
    from domains.orders.services.returns_controller_service import bulk_update_return_requests as _impl
    return _impl(*args, **kwargs)


def create_return_request(*args, **kwargs):
    from domains.orders.services.returns_controller_service import create_return_request as _impl
    return _impl(*args, **kwargs)


def get_return_request(*args, **kwargs):
    from domains.orders.services.returns_controller_service import get_return_request as _impl
    return _impl(*args, **kwargs)


def list_return_requests(*args, **kwargs):
    from domains.orders.services.returns_controller_service import list_return_requests as _impl
    return _impl(*args, **kwargs)


def update_return_request(*args, **kwargs):
    from domains.orders.services.returns_controller_service import update_return_request as _impl
    return _impl(*args, **kwargs)


def update_return_request_status(*args, **kwargs):
    from domains.orders.services.returns_service import update_return_request_status as _impl
    return _impl(*args, **kwargs)
