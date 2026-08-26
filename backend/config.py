"""Application configuration (spec: backend/config.py).

Canonical settings / env / feature-gates entry point. Re-exports the existing
implementation in infrastructure.utils.config so behaviour is unchanged while
the new top-level module becomes the single import surface.
"""
from infrastructure.utils.config import *  # noqa: F401,F403
