"""Country-staff assignment adapter for the middleware layer.

TODO: The ``CountryStaffAssignment`` model lives in
``domains/country/models`` and must not be imported from the middleware
layer (Law 1). The real reader will be relocated to
``infrastructure.security.country_staff`` so the middleware circuit can
call back into it without crossing layers. Until then, this adapter
returns an empty list which means RLS-middleware will treat every
non-admin user as "unassigned" and deny access.
"""
from __future__ import annotations

import logging
from typing import List

logger = logging.getLogger(__name__)


def get_user_country_codes(user_id: int) -> List[str]:
    """Return the active country codes assigned to ``user_id``.

    No-op until the reader is relocated out of ``domains/``.
    """
    logger.debug(
        "get_user_country_codes no-op for user_id=%s — adapter pending infrastructure relocation",
        user_id,
    )
    return []
