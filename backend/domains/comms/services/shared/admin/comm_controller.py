"""controllers.comms.comm_controller controller.

Business logic is delegated to services.comms.comm_service (routers -> controllers -> services)."""

from domains.comms.services.shared.admin.comm_service import create_chat_thread
from domains.comms.services.shared.admin.comm_service import create_incident_room
from domains.comms.services.shared.admin.comm_service import create_video_room
from domains.comms.services.shared.admin.comm_service import get_command_center_metrics
from domains.comms.services.shared.admin.comm_service import send_masked_message

__all__ = [
    "create_chat_thread", "create_incident_room", "create_video_room", "get_command_center_metrics", "send_masked_message"
]
