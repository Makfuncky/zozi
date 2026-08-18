"""infrastructure.config — alias of the canonical settings module.

Re-exports infrastructure.utils.config so ``from infrastructure.config import *``
resolves. NEW_STRUCTURE.md places config at backend root, but some modules import
the infrastructure.config path, so both surfaces are kept valid.
"""
from infrastructure.utils.config import *  # noqa: F401,F403
