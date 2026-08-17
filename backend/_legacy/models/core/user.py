"""User-model surface of the ``models.core`` package.

Re-exports the canonical user models from the top-level ``models.user`` module
so ``from models.core.user import *`` (used by ``models._exports``) resolves.
"""
from __future__ import annotations

from models.user import *  # noqa: F401,F403
