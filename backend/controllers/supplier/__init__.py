"""Supplier controller subpackage.

Domain-organized modules for supplier portal operations.
This subpackage re-exports all functions from the monolithic
supplier_controller.py for backward compatibility, while also
providing domain-specific modules for new code.

Routers should import from here (controllers.supplier) instead of
controllers.supplier_controller for future-proof access.
"""
from controllers.supplier_controller import *  # noqa: F401, F403
