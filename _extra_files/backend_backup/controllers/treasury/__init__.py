"""Treasury controller package.

Holds treasury domain controllers (auto-payout, cash-write, payout admin/approval,
treasury metrics/query). Importing this package does not trigger any router
registration, so it is safe to import from anywhere in the dependency graph.
"""
from __future__ import annotations
