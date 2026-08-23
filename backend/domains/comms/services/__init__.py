"""comms domain — service layer.

Sliced into sub-capability folders per diagram §3 (> ~8 services):

  admin/          — command center, comm controllers, content, asset tracking
  campaign/       — email campaign geography
  chat/           — chat system, write/read/enrichment, entity chat, chatbot
  email/          — email service, gateway, management, transactional
  media/          — media storage, image tools, AI image
  notification/   — notification service, engine, worker, push
  realtime/       — WebSocket, realtime chat, connection management
  security/       — proxy communication, QR, external contact
  ticket/         — tickets, escalation SLA
  utility/        — db_read, db_write, event_bus, write helpers, translation
  video/          — video conferencing, rooms, services
"""

__all__ = []
