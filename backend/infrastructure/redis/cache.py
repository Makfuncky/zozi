"""infrastructure.redis.cache — alias of the canonical cache helpers.

The cache implementation lives in infrastructure.utils.cache; some modules import
the infrastructure.redis.cache path, so both surfaces are kept valid.
"""
from infrastructure.utils.cache import *  # noqa: F401,F403
