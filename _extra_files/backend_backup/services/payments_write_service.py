"""Generated re-export shim.

This module was missing after a refactor that relocated handlers into
subpackage service modules. It re-exports the symbols from their
canonical locations so legacy imports (e.g. `from services.payments_write_service import ...`)
keep resolving. Prefer importing from the canonical module directly
in new code.
"""
from __future__ import annotations

from services.comms.tickets_write_service import create_notification

from services.write_help import commit_only

# The following symbols were referenced but have NO definition
# anywhere in the codebase. They are stubbed to fail loudly at
# call time rather than break import of this module.
def _missing_symbol(name):
    def _f(*_a, **_k):
        raise NotImplementedError(
            f"'{mod}.{name}' is not implemented (refactor gap)")
    return _f

add_notification = _missing_symbol('add_notification')
add_processed_webhook_event = _missing_symbol('add_processed_webhook_event')
create_or_update_gateway_connection = _missing_symbol('create_or_update_gateway_connection')
create_payment = _missing_symbol('create_payment')
create_payment_provider_config = _missing_symbol('create_payment_provider_config')
flush_model = _missing_symbol('flush_model')
update_gateway_connection = _missing_symbol('update_gateway_connection')
update_payment = _missing_symbol('update_payment')
update_payment_provider_config = _missing_symbol('update_payment_provider_config')
update_payment_provider_config_no_refresh = _missing_symbol('update_payment_provider_config_no_refresh')

