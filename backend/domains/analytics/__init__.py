from infrastructure.database.base import Base  # noqa: F401
from . import subscribers  # noqa: F401  (AXIS 2: register analytics event subscribers)
__all__ = ["Base"]
