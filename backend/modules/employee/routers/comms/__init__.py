"""Split router package — originally comms.py."""

from comms.router import router  # noqa: F401
import comms.chat  # noqa: F401
import comms.chat_api  # noqa: F401
import comms.chat_enrichment  # noqa: F401
import comms.chatbot  # noqa: F401
import comms.comm  # noqa: F401
import comms.comms_chat  # noqa: F401
import comms.comms_unified  # noqa: F401
import comms.comms_video  # noqa: F401
import comms.email  # noqa: F401
import comms.email_controller  # noqa: F401
import comms.email_enrichment  # noqa: F401
import comms.entity_chat  # noqa: F401
import comms.entity_communication  # noqa: F401
import comms.internal_channels  # noqa: F401
import comms.internal_comms_channels  # noqa: F401
import comms.messaging  # noqa: F401
import comms.notifications  # noqa: F401
import comms.proxy_communication  # noqa: F401
import comms.push_notifications  # noqa: F401
import comms.tickets  # noqa: F401
import comms.video  # noqa: F401
import comms.video_controller  # noqa: F401
import comms.ws_chat  # noqa: F401

__all__ = ["router"]
