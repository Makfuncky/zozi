"""Transitional re-export (spec target is kernel/money.py).

Kept so legacy `from kernel.currency import ...` references keep resolving while
domain services are migrated to `from kernel.money import ...`.
"""
from kernel.money import *  # noqa: F401,F403
