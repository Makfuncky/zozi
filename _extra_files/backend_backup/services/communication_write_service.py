"""Generated re-export shim.

This module was missing after a refactor that relocated handlers into
subpackage service modules. It re-exports the symbols from their
canonical locations so legacy imports (e.g. `from services.communication_write_service import ...`)
keep resolving. Prefer importing from the canonical module directly
in new code.
"""
from __future__ import annotations

from services.comms.communication_write_service import (
    create_chat_thread,
    create_incident_room,
    create_video_room,
    send_masked_message,
)

