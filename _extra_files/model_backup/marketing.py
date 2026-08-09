"""Re-export of the canonical marketing models.

The ``models.comms`` package is the canonical home for these ORM classes.
This flat module now forwards to it so that ``models.FlashSale`` and
``models.comms.marketing.FlashSale`` resolve to the *same* class object,
eliminating the duplicate-table collision flagged by the architecture audit.
"""
from __future__ import annotations

from models.comms.marketing import *  # noqa: F401,F403
