"""Split service package — originally users_admin_service.py."""
from __future__ import annotations

from .__header___p1_p1 import *  # noqa: F401,F403
from .__header___p1_p2 import *  # noqa: F401,F403
from .__header___p2_p1 import *  # noqa: F401,F403
from .__header___p2_p2 import *  # noqa: F401,F403
from .__header___p3 import *  # noqa: F401,F403
from .merged_from_user_read_service_py import *  # noqa: F401,F403
from .merged_from_user_write_ops_py import *  # noqa: F401,F403

__all__: list[str] = []
