# ZOZI Feature Implementation Checker — Report

**Generated:** 2026-08-16 23:10:56
**Features checked:** 17
**Overall implementation:** 481/2329 items found (20.7%)

---

## Summary by Category

| Category | Found / Total | % |
|---|---|---|
| backend_files | 0 / 548 | ❌ 0.0% |
| database_files | 153 / 221 | 🟡 69.2% |
| model_files | 0 / 69 | ❌ 0.0% |
| frontend_web | 108 / 307 | ❌ 35.2% |
| frontend_mobile | 31 / 129 | ❌ 24.0% |
| tests | 0 / 288 | ❌ 0.0% |
| extra_files | 0 / 0 | ❌ 0.0% |
| api_routes | 0 / 511 | ❌ 0.0% |
| models | 189 / 256 | 🟡 73.8% |

---

## SYS_001 — Communication Workspace (Chat · Email · Video · Contacts · Files)

### Backend Files

**Missing (37):**

- ❌ `comms_chat.py                                                    → thin router for chat endpoints (direct/group/entity threads, messages, read receipts)`
- ❌ `comms_video.py                                                    → thin router for video conferencing endpoints (rooms, tokens, recording)`
- ❌ `email.py                                                          → thin router for internal email endpoints (send, templates, history, bulk, from-alias)`
- ❌ `internal_channels.py                                              → thin router for internal channels endpoints (CRUD channels, members, messages)`
- ❌ `proxy_communication.py                                            → thin router for proxy/external contact endpoints (masks, proxy channels, messages, call logs)`
- ❌ `audit.py                                                          → thin router for communication audit trail endpoints (get trail, export for eDiscovery)`
- ❌ `ediscovery.py                                                     → thin router for eDiscovery search endpoints (search communications, export)`
- ❌ `comms_unified.py                                                  → thin router for unified inbox aggregator endpoint (GET /comms/unified-inbox?lens=&cursor=&limit=)`
- ❌ `comms/comm_controller.py                                      → orchestrates chat routes, delegates to chat_system_service, no FastAPI imports`
- ❌ `core/admin_video_controller.py                               → orchestrates video routes, delegates to video_service, no FastAPI imports`
- ❌ `core/email_controller.py                                      → orchestrates email routes, delegates to email_gateway_service, no FastAPI imports`
- ❌ `core/internal_channels_controller.py                         → orchestrates internal channels routes, delegates to internal_communication_service, no FastAPI imports`
- ❌ `router_bridges/proxy_communication.py                        → orchestrates proxy routes, delegates to proxy_communication_service, no FastAPI imports`
- ❌ `comms/communication_audit_controller.py                      → orchestrates audit routes, delegates to communication_audit_service, no FastAPI imports`
- ❌ `admin/audit_controller.py                                    → orchestrates admin audit/eDiscovery routes, delegates to ediscovery_service, no FastAPI imports`
- ❌ `core/comms_unified_controller.py                             → orchestrates unified inbox route, merges multi-transport threads, delegates to unified_inbox_service, no FastAPI imports`
- ❌ `comms/chat_system_service.py                                    → owns DB writes for chat (direct/group/entity threads, messages, read receipts, reactions), business logic`
- ❌ `comms/chat_read_service.py                                      → read-model queries for chat history, pagination, presence caching`
- ❌ `comms/chat_write_service.py                                     → write-model commands for chat (send, edit, delete, react), outbox event publishing`
- ❌ `comms/entity_chat_service.py                                    → entity-linked B2B chat threads (order/supplier context), country-scoped`
- ❌ `comms/video_conferencing_service.py                             → owns DB writes for video rooms, participants, recordings, tokens, watermark, transcript, action items`
- ❌ `comms/video_room_service.py                                     → room lifecycle (create, end, status transitions), participant management`
- ❌ `comms/email_gateway_service.py                                  → owns DB writes for internal/external emails, folders, threads, DLP scanning, SMTP relay, bulk/alias send`
- ❌ `comms/internal_communication_service.py                         → owns DB writes for internal channels, members, messages, topic/pinned messages`
- ❌ `comms/external_contact_service.py                               → owns DB writes for proxy channels, sessions, messages, call logs, masking logic`
- ❌ `comms/communication_audit_service.py                            → owns DB writes for communication_audit_trails, append-only, legal-hold enforcement`
- ❌ `comms/unified_inbox_service.py                                  → cursor-paginated merge of DMs/channels/emails/videos/tickets, server-sort by urgency, WS delta patch`
- ❌ `audit/ediscovery_service.py                                     → eDiscovery queries, full-text search across communications, export for legal`
- ❌ `middleware/websocket_manager.py                                          → WebSocket manager for real-time chat, typing, presence, inbox patches (reuse existing, extend for comms)`
- ❌ `jobs/transcoding_worker.py                                               → background worker for video/voice transcoding, thumbnail generation (Celery/Redis queue)`
- ❌ `jobs/communication_retention.py                                          → background worker for retention purge, legal-hold checks, archive old communications`
- ❌ `events/event_publisher.py                                                → Redis pub/sub event publisher (reuse existing, extend for comms events)`
- ❌ `events/communication_events.py                                           → domain event schemas for chat/email/video/audit events (reuse/payment_events.py pattern)`
- ❌ `providers/comms/email_provider.py                                       → 3rd-party SMTP relay adapter (subclass BaseProvider), health_check, retry logic`
- ❌ `providers/comms/video_provider.py                                       → 3rd-party video/WebRTC adapter (subclass BaseProvider), health_check, token generation`
- ❌ `providers/comms/transcription_provider.py                               → Whisper transcription adapter (subclass BaseAIProvider), health_check, async processing`
- ❌ `providers/comms/media_storage_provider.py                               → R2/S3 media storage adapter (subclass BaseProvider), upload/download, presigned URLs`

### Database Files

**Present (9):**

- ✅ `base.py`
- ✅ `database.py`
- ✅ `session.py`
- ✅ `transaction.py`
- ✅ `schemas.py`
- ✅ `models.py`
- ✅ `create_tables.py`
- ✅ `init_db.py`
- ✅ `database_logging.py`

**Missing (4):**

- ❌ `security/`
- ❌ `setup/`
- ❌ `seeds/`
- ❌ `alembic/`

### Frontend Web

**Present (4):**

- ✅ `comms/CommShell.tsx`
- ✅ `comms/CommandPalette.tsx`
- ✅ `comms/StatusDock.tsx`
- ✅ `hooks/useUnifiedInbox.ts`

**Missing (20):**

- ❌ `web_app/comms/communication/page.tsx`
- ❌ `comms/Rail/RailGroup.tsx`
- ❌ `comms/Rail/RailRow.tsx`
- ❌ `comms/Rail/LensChips.tsx`
- ❌ `comms/Stage/ThreadHeader.tsx`
- ❌ `comms/Stage/ComposerDock.tsx`
- ❌ `comms/Stage/renderTransport.tsx`
- ❌ `comms/Stage/renderers/Chat.tsx`
- ❌ `comms/Stage/renderers/Email.tsx`
- ❌ `comms/Stage/renderers/Video.tsx`
- ❌ `comms/Stage/renderers/Contact.tsx`
- ❌ `comms/Stage/renderers/B2B.tsx`
- ❌ `comms/Stage/renderers/Incident.tsx`
- ❌ `comms/Context/ContextCard.tsx`
- ❌ `comms/Context/People360.tsx`
- ❌ `comms/Context/SharedFiles.tsx`
- ❌ `comms/Context/Tasks.tsx`
- ❌ `comms/Context/AiDlp.tsx`
- ❌ `comms/Context/Audit.tsx`
- ❌ `styles/comm.css`

### Frontend Mobile

**Missing (10):**

- ❌ `comms/communication/_layout.tsx`
- ❌ `comms/communication/index.tsx`
- ❌ `comms/communication/chat.tsx`
- ❌ `comms/communication/email.tsx`
- ❌ `comms/communication/video.tsx`
- ❌ `comms/communication/channels.tsx`
- ❌ `components/comms/ChatInterface.tsx`
- ❌ `components/comms/EmailClient.tsx`
- ❌ `components/comms/VideoMeeting.tsx`
- ❌ `components/comms/ChannelList.tsx`

### Tests

**Missing (7):**

- ❌ `tests/backend/_test_comms_communication.py`
- ❌ `tests/backend/_test_comms_unified_inbox.py`
- ❌ `tests/backend/_test_comms_audit_ediscovery.py`
- ❌ `tests/frontend/web_app/_test_comms_communication.test.tsx`
- ❌ `tests/frontend/web_app/_test_comms_unified_inbox.test.tsx`
- ❌ `tests/frontend/mobile_app/_test_comms_communication.test.tsx`
- ❌ `tests/playwright/_test_comms_e2e.spec.ts`

### API Routes

**Missing (33):**

- ❌ `POST /api/v1/chat/direct`
- ❌ `POST /api/v1/chat/group`
- ❌ `POST /api/v1/chat/message`
- ❌ `GET /api/v1/chat/history/{chat_id}`
- ❌ `GET /api/v1/chat/threads`
- ❌ `POST /api/v1/chat/threads`
- ❌ `GET /api/v1/chat/threads/{thread_id}/messages`
- ❌ `POST /api/v1/chat/threads/{thread_id}/messages`
- ❌ `POST /api/v1/chat/read`
- ❌ `POST /api/v1/video/rooms`
- ❌ `GET /api/v1/video/rooms`
- ❌ `POST /api/v1/video/rooms/{room_id}/tokens`
- ❌ `POST /api/v1/video/rooms/{room_id}/recording`
- ❌ `POST /api/v1/video/rooms/{room_id}/end`
- ❌ `GET /api/v1/video/rooms/{room_id}`
- ❌ `POST /api/v1/email/internal`
- ❌ `POST /api/v1/email/external`
- ❌ `GET /api/v1/email/templates`
- ❌ `POST /api/v1/email/track-open`
- ❌ `GET /api/v1/email/history/{user_id}`
- ❌ `POST /api/v1/email/bulk`
- ❌ `POST /api/v1/email/from-alias`
- ❌ `POST /api/v1/internal/channels`
- ❌ `GET /api/v1/internal/channels`
- ❌ `GET /api/v1/internal/channels/{channel_id}`
- ❌ `POST /api/v1/internal/channels/{channel_id}/members`
- ❌ `DELETE /api/v1/internal/channels/{channel_id}/members/{user_id}`
- ❌ `POST /api/v1/internal/channels/{channel_id}/messages`
- ❌ `GET /api/v1/internal/channels/{channel_id}/messages`
- ❌ `GET /api/v1/audit`
- ❌ `GET /api/v1/audit/export`
- ❌ `GET /api/v1/audit/search`
- ❌ `GET /comms/unified-inbox`

### DB Model Classes

**Present (25):**

- ✅ `DirectChatRoom`
- ✅ `DirectChatMessage`
- ✅ `GroupChatRoom`
- ✅ `GroupChatMember`
- ✅ `GroupChatMessage`
- ✅ `EntityChatThread`
- ✅ `EntityChatMessage`
- ✅ `ChatAttachment`
- ✅ `ChatReadReceipt`
- ✅ `VideoRoom`
- ✅ `VideoRoomParticipant`
- ✅ `VideoRoomRecording`
- ✅ `InternalChannel`
- ✅ `InternalChannelMember`
- ✅ `InternalMessage`
- ✅ `EmployeeCommunicationThread`
- ✅ `ExternalContactMasking`
- ✅ `CommunicationAuditTrail`
- ✅ `ProxyChannel`
- ✅ `ProxySession`
- ✅ `ProxyMessage`
- ✅ `ProxyCallLog`
- ✅ `Notification`
- ✅ `TicketMessage`
- ✅ `MediaAsset`

---

## SYS_002 — Order Tracker & Order Management

### Backend Files

**Missing (29):**

- ❌ `orders/customer_orders_router.py → thin router for customer order endpoints (create, preview, list, get, tracking, cancel)`
- ❌ `orders/admin_orders_router.py → thin router for admin order endpoints (list, status update, override, bulk actions)`
- ❌ `logistics/shipments_router.py → thin router for shipment endpoints (create, list, status transitions, events, GPS update, POD)`
- ❌ `orders/returns_router.py → thin router for return/refund endpoints (create, list, approve, reject, complete)`
- ❌ `orders/labels_router.py → thin router for label endpoints (generate, print, download)`
- ❌ `orders/orders_controller.py → orchestrates customer order routes, delegates to orders_service, no FastAPI imports`
- ❌ `orders/logistics_controller.py → orchestrates logistics/shipment routes, delegates to logistics_service, no FastAPI imports`
- ❌ `admin/admin_orders_status_controller.py → orchestrates admin order status routes, delegates to admin_orders_service, no FastAPI imports`
- ❌ `admin/returns_admin_controller.py → orchestrates admin return/refund routes, delegates to returns_service, no FastAPI imports`
- ❌ `orders/orders_service.py → owns DB writes for orders (create, preview, get, cancel), business logic`
- ❌ `orders/order_tracking_service.py → read-model queries for order tracking, timeline, history`
- ❌ `orders/orders_write_service.py → write-model commands for order lifecycle transitions, outbox event publishing`
- ❌ `orders/order_lifecycle_service.py → server-side state machine enforcement, config-driven transition validation`
- ❌ `logistics/logistics_service.py → owns DB writes for shipments (create, claim, status transitions, GPS, POD), business logic`
- ❌ `logistics/logistics_engine.py → logistics engine for routing, partner matching, claim board queries`
- ❌ `commerce/return_service.py → owns DB writes for return_requests, refunds, reverse shipments`
- ❌ `commerce/refund_service.py → refund posting, ledger reconciliation, variance alerting`
- ❌ `commerce/order_notification_service.py → outbox event fan-out to notifications, WS push, email/SMS/push`
- ❌ `orders/order_label_service.py → shipping label + packing slip PDF generation, print queue`
- ❌ `middleware/rls_middleware.py → RLS enforcement on order/shipment/return queries (cross-cutting)`
- ❌ `jobs/label_generation_worker.py → background worker for shipping label PDF generation, print queue (Celery/Redis)`
- ❌ `jobs/order_autocancel_worker.py → background worker for auto-cancel unpaid PENDING_PAYMENT after SLA`
- ❌ `jobs/reconciliation_worker.py → background worker for COD & Card reconciliation, nightly variance cron`
- ❌ `jobs/order_notification_task.py → background worker for notification fan-out, DLQ handling`
- ❌ `events/order_events.py → domain event schemas for order/shipment/return events`
- ❌ `events/order_status_pusher.py → WebSocket push for order status changes`
- ❌ `providers/media/shipping_label_provider.py → shipping label + packing slip PDF adapter (subclass BaseProvider)`
- ❌ `providers/media/media_storage_provider.py → R2/S3 media storage adapter for photos, signatures, labels`
- ❌ `providers/geography/location_service_provider.py → IP-geo + GPS sidecar adapter (subclass BaseProvider)`

### Database Files

**Present (9):**

- ✅ `base.py`
- ✅ `database.py`
- ✅ `session.py`
- ✅ `transaction.py`
- ✅ `schemas.py`
- ✅ `models.py`
- ✅ `create_tables.py`
- ✅ `init_db.py`
- ✅ `database_logging.py`

**Missing (4):**

- ❌ `security/`
- ❌ `setup/`
- ❌ `seeds/`
- ❌ `alembic/`

### Model Files

**Missing (4):**

- ❌ `orders.py → Legacy Order, OrderItem, ReturnRequest models (to be migrated to order_entities.py)`
- ❌ `logistics.py → Legacy Shipment, ShipmentEvent models (to be migrated to logistics_entities.py)`
- ❌ `finance.py → RefundLedger model`
- ❌ `mixins.py → AuditMixin, SoftDeleteMixin, VersionMixin`

### Frontend Web

**Present (14):**

- ✅ `web_app/orders/page.tsx`
- ✅ `web_app/orders/[id]/page.tsx`
- ✅ `orders/loading.tsx`
- ✅ `orders/error.tsx`
- ✅ `web_app/tracking/[id]/page.tsx`
- ✅ `web_app/admin/orders/page.tsx`
- ✅ `admin/orders/_components/ReturnsPanel.tsx`
- ✅ `admin/orders/_components/BarcodePanel.tsx`
- ✅ `web_app/returns/page.tsx`
- ✅ `web_app/returns/[id]/page.tsx`
- ✅ `returns/error.tsx`
- ✅ `returns/loading.tsx`
- ✅ `orderHelpers.ts`
- ✅ `returnsApi.ts`

**Missing (12):**

- ❌ `orders/OrderTimeline.tsx`
- ❌ `orders/OrderTable.tsx`
- ❌ `orders/TrackingView.tsx`
- ❌ `orders/ReturnRequestForm.tsx`
- ❌ `orders/RefundStatus.tsx`
- ❌ `orders/ShippingLabelPrint.tsx`
- ❌ `orders/OrderOpsCockpit.tsx`
- ❌ `lib/order/orders.ts`
- ❌ `lib/order/tracking.ts`
- ❌ `hooks/useOrders.ts`
- ❌ `hooks/useOrderTracking.ts`
- ❌ `hooks/useReturns.ts`

### Frontend Mobile

**Present (6):**

- ✅ `orders/[id].tsx`
- ✅ `logistics-partner/shipments.tsx`
- ✅ `logistics-partner/scan.tsx`
- ✅ `logistics-partner/dashboard.tsx`
- ✅ `logistics-partner/profile.tsx`
- ✅ `returns.tsx`

**Missing (4):**

- ❌ `orders/index.tsx`
- ❌ `components/orders/OrderTimeline.tsx`
- ❌ `components/orders/TrackingView.tsx`
- ❌ `components/orders/ReturnRequestForm.tsx`

### Tests

**Missing (16):**

- ❌ `tests/backend/_test_order_lifecycle.py`
- ❌ `tests/backend/_test_order_status_guards.py`
- ❌ `tests/backend/_test_order_label_print.py`
- ❌ `tests/backend/_test_shipment_lifecycle.py`
- ❌ `tests/backend/_test_pod_delivery.py`
- ❌ `tests/backend/_test_returns_refunds.py`
- ❌ `tests/backend/_test_autocancel.py`
- ❌ `tests/backend/_test_rls_country_orders.py`
- ❌ `tests/backend/_test_reconciliation.py`
- ❌ `tests/frontend/web_app/_test_orders_page.test.tsx`
- ❌ `tests/frontend/web_app/_test_tracking_page.test.tsx`
- ❌ `tests/frontend/web_app/_test_admin_ops_cockpit.test.tsx`
- ❌ `tests/frontend/web_app/_test_returns_page.test.tsx`
- ❌ `tests/frontend/mobile_app/_test_orders_mobile.test.tsx`
- ❌ `tests/frontend/mobile_app/_test_logistics_mobile.test.tsx`
- ❌ `tests/playwright/_test_order_tracker_e2e.spec.ts`

### API Routes

**Missing (37):**

- ❌ `POST /api/v1/customer/orders`
- ❌ `GET /api/v1/customer/orders`
- ❌ `GET /api/v1/customer/orders/{order_id}`
- ❌ `PATCH /api/v1/customer/orders/{order_id}`
- ❌ `POST /api/v1/customer/orders/{order_id}/cancel`
- ❌ `POST /api/v1/customer/orders/{order_id}/confirm`
- ❌ `POST /api/v1/customer/orders/{order_id}/pack`
- ❌ `POST /api/v1/customer/orders/{order_id}/ship`
- ❌ `POST /api/v1/customer/orders/{order_id}/in-transit`
- ❌ `POST /api/v1/customer/orders/{order_id}/out-for-delivery`
- ❌ `POST /api/v1/customer/orders/{order_id}/deliver`
- ❌ `GET /api/v1/customer/orders/{order_id}/tracking`
- ❌ `GET /api/v1/customer/orders/{order_id}/history`
- ❌ `POST /api/v1/customer/orders/{order_id}/labels`
- ❌ `GET /api/v1/customer/orders/{order_id}/labels`
- ❌ `POST /api/v1/customer/orders/preview`
- ❌ `POST /api/v1/customer/orders/{order_id}/scan-receipt`
- ❌ `POST /api/v1/customer/orders/{order_id}/confirmation-requests/{confirmation_id}/respond`
- ❌ `POST /api/v1/admin/orders/{country_code}`
- ❌ `GET /api/v1/admin/orders/{country_code}`
- ❌ `PUT /api/v1/admin/orders/{country_code}/{order_id}/status`
- ❌ `POST /api/v1/admin/orders/{country_code}/bulk-status`
- ❌ `POST /api/v1/admin/orders/{country_code}/archive`
- ❌ `POST /api/v1/admin/orders/{country_code}/restore`
- ❌ `GET /api/v1/logistics/shipments`
- ❌ `GET /api/v1/logistics/shipments/{shipment_id}`
- ❌ `POST /api/v1/logistics/shipments/{shipment_id}/pod`
- ❌ `POST /api/v1/logistics/shipments/{shipment_id}/events`
- ❌ `POST /api/v1/logistics/shipments/{shipment_id}/scan`
- ❌ `GET /api/v1/logistics/shipments/{shipment_id}/events`
- ❌ `GET /api/v1/returns`
- ❌ `POST /api/v1/returns`
- ❌ `PATCH /api/v1/returns/{return_id}`
- ❌ `POST /api/v1/returns/{return_id}/pickup`
- ❌ `POST /api/v1/refunds`
- ❌ `GET /api/v1/refunds/{refund_id}`
- ❌ `GET /orders/{id}/label`

### DB Model Classes

**Present (12):**

- ✅ `Order`
- ✅ `OrderItem`
- ✅ `OrderLogisticsAllocation`
- ✅ `OrderNotification`
- ✅ `ReturnRequest`
- ✅ `Shipment`
- ✅ `ShipmentEvent`
- ✅ `ShipmentConfirmation`
- ✅ `RefundLedger`
- ✅ `LogisticsPartner`
- ✅ `LogisticsPartnerProfile`
- ✅ `LogisticsPartnerServiceArea`

**Missing (6):**

- ❌ `ProofOfDelivery`
- ❌ `ShippingLabel`
- ❌ `OrderStatusHistory`
- ❌ `OrderEvent`
- ❌ `OrderStatusRule`
- ❌ `Package`

---

## SYS_003 — Customer Return Policy & Returns Management

### Backend Files

**Missing (17):**

- ❌ `returns.py → thin router for return/refund endpoints (create, list, approve, reject, complete, bulk update)`
- ❌ `supplier.py → thin router for supplier return window endpoints (get, update product return window)`
- ❌ `orders/returns_controller.py → orchestrates return routes, delegates to returns_service, no FastAPI imports`
- ❌ `products_controller.py → orchestrates product return window routes, delegates to products_service, no FastAPI imports`
- ❌ `admin/returns_admin_controller.py → orchestrates admin return resolution routes, delegates to returns_service, no FastAPI imports`
- ❌ `orders/returns_service.py → owns DB writes for return_requests (create, approve, reject, complete), business logic, validation`
- ❌ `orders/returns_write_service.py → write-model commands for return lifecycle transitions, outbox event publishing`
- ❌ `orders/returns_controller_service.py → orchestrates return controller flow, delegates to returns_service`
- ❌ `core/returns_service.py → core returns service (shared logic, policy validation)`
- ❌ `catalog/products_service.py → owns DB writes for product return window updates, validation against supplier profile max`
- ❌ `middleware/rls_middleware.py → RLS enforcement on return request queries (cross-cutting)`
- ❌ `jobs/refund_processing_worker.py → background worker for automatic refund processing (Stripe/Tap), DLQ handling`
- ❌ `jobs/return_notification_task.py → background worker for return notification fan-out (return created, updated, refund issued, replacement completed)`
- ❌ `events/event_publisher.py → Redis pub/sub event publisher (reuse existing, extend for return events)`
- ❌ `events/return_events.py → domain event schemas for return/replacement/refund events`
- ❌ `providers/payments/stripe_provider.py → Stripe payment intent refund adapter (subclass BaseProvider)`
- ❌ `providers/payments/tap_provider.py → Tap refund endpoint adapter (subclass BaseProvider)`

### Database Files

**Present (9):**

- ✅ `base.py`
- ✅ `database.py`
- ✅ `session.py`
- ✅ `transaction.py`
- ✅ `schemas.py`
- ✅ `models.py`
- ✅ `create_tables.py`
- ✅ `init_db.py`
- ✅ `database_logging.py`

**Missing (4):**

- ❌ `security/`
- ❌ `setup/`
- ❌ `seeds/`
- ❌ `alembic/`

### Model Files

**Missing (3):**

- ❌ `orders.py → Legacy ReturnRequest model (to be migrated to order_entities.py)`
- ❌ `products.py → Legacy Product model with return_window_days (to be migrated to catalog/product_entities.py)`
- ❌ `mixins.py → AuditMixin, SoftDeleteMixin, VersionMixin`

### Frontend Web

**Present (13):**

- ✅ `web_app/orders/[id]/page.tsx`
- ✅ `orders/loading.tsx`
- ✅ `orders/error.tsx`
- ✅ `admin/orders/_components/ReturnsPanel.tsx`
- ✅ `web_app/supplier/products/page.tsx`
- ✅ `web_app/supplier/returns/page.tsx`
- ✅ `web_app/returns/page.tsx`
- ✅ `web_app/returns/[id]/page.tsx`
- ✅ `returns/loading.tsx`
- ✅ `returns/error.tsx`
- ✅ `web_app/admin/returns/page.tsx`
- ✅ `returnsApi.ts`
- ✅ `i18n.ts`

**Missing (4):**

- ❌ `orders/ReturnRequestForm.tsx`
- ❌ `orders/RefundStatus.tsx`
- ❌ `lib/order/returns.ts`
- ❌ `hooks/useReturns.ts`

### Frontend Mobile

**Present (4):**

- ✅ `returns.tsx`
- ✅ `supplier/returns.tsx`
- ✅ `admin/returns.tsx`
- ✅ `lib/api.ts`

**Missing (2):**

- ❌ `components/orders/ReturnRequestForm.tsx`
- ❌ `components/orders/RefundStatus.tsx`

### Tests

**Missing (8):**

- ❌ `tests/backend/_test_return_policy.py`
- ❌ `tests/backend/_test_return_validation.py`
- ❌ `tests/backend/_test_return_refund_flow.py`
- ❌ `tests/backend/_test_supplier_return_window.py`
- ❌ `tests/frontend/web_app/_test_returns_page.test.tsx`
- ❌ `tests/frontend/web_app/_test_return_form.test.tsx`
- ❌ `tests/frontend/mobile_app/_test_returns_mobile.test.tsx`
- ❌ `tests/playwright/_test_return_policy_e2e.spec.ts`

### API Routes

**Missing (11):**

- ❌ `GET /api/v1/returns`
- ❌ `POST /api/v1/returns`
- ❌ `GET /api/v1/returns/{return_id}`
- ❌ `PUT /api/v1/returns/bulk`
- ❌ `PUT /api/v1/returns/{return_id}`
- ❌ `PUT /api/v1/returns/{return_id}/status`
- ❌ `POST /api/v1/supplier/products/{product_id}/return-window`
- ❌ `GET /api/v1/supplier/products/{product_id}/return-window`
- ❌ `GET /api/v1/admin/returns`
- ❌ `PATCH /api/v1/admin/returns/{return_id}`
- ❌ `POST /api/v1/admin/returns/bulk-update`

### DB Model Classes

**Present (4):**

- ✅ `ReturnRequest`
- ✅ `Product`
- ✅ `RefundLedger`
- ✅ `OrderNotification`

---

## SYS_004 — Finance & Treasury ERP System (GL · Treasury · Automation · Payments · Commission · Reporting)

### Backend Files

**Missing (88):**

- ❌ `finance/treasury_router.py → thin router for treasury endpoints (cash position, snapshots, forecasts, settlements, gateway settlements, COD remittance)`
- ❌ `finance/ledger_router.py → thin router for general ledger endpoints (journal entries, journal entry lines, pending entries, trial balance, financial statements)`
- ❌ `finance/automation_router.py → thin router for automation endpoints (trigger, status, runs, exception queue, control tower)`
- ❌ `finance/bank_reconciliation_router.py → thin router for bank reconciliation endpoints (import statements, match, reconcile, exception filter)`
- ❌ `finance/commission_router.py → thin router for commission endpoints (rates, ledger entries, supplier settlements, badge tiers)`
- ❌ `finance/supplier_payout_router.py → thin router for supplier payout endpoints (batches, batch items, payouts, pre-review links)`
- ❌ `finance/tax_router.py → thin router for tax endpoints (tax rules, country category rates, VAT remittances, WHT)`
- ❌ `finance/expense_router.py → thin router for expense endpoints (scanned expenses, AP bills, fixed assets, OCR dropzone)`
- ❌ `finance/ap_ar_router.py → thin router for AR/AP endpoints (invoices, bills, receipts, payments, aging, dunning)`
- ❌ `finance/reporting_router.py → thin router for reporting endpoints (report definitions, preview, execute, schedule, export)`
- ❌ `finance/control_tower_router.py → thin router for automation control tower endpoints (automation rules, runs, DLQ, toggles, thresholds)`
- ❌ `payments.py → thin router for payment endpoints (methods, create, confirm, webhook, refund)`
- ❌ `admin/payment_gateways_router.py → thin router for payment gateway admin endpoints (wizard, credentials, test connection, routing rules)`
- ❌ `promotions.py → thin router for promotion endpoints (apply, active, admin CRUD, preview)`
- ❌ `coupons.py → thin router for coupon endpoints (validate, CRUD, archive, restore, bulk)`
- ❌ `admin/commissions_router.py → thin router for commission admin endpoints (global rate, category rates, supplier overrides, badge tiers, preview calculator)`
- ❌ `admin/promotions.py → thin router for admin promotion endpoints (country-scoped coupons, campaigns)`
- ❌ `finance/treasury_controller.py → orchestrates treasury routes, delegates to treasury_service, no FastAPI imports`
- ❌ `finance/ledger_controller.py → orchestrates GL routes, delegates to general_ledger_service, no FastAPI imports`
- ❌ `finance/automation_controller.py → orchestrates automation routes, delegates to automation_service, no FastAPI imports`
- ❌ `finance/bank_reconciliation_controller.py → orchestrates bank rec routes, delegates to bank_reconciliation_service, no FastAPI imports`
- ❌ `finance/commission_controller.py → orchestrates commission routes, delegates to commission_service, no FastAPI imports`
- ❌ `finance/supplier_payout_controller.py → orchestrates payout routes, delegates to supplier_payout_service, no FastAPI imports`
- ❌ `finance/tax_controller.py → orchestrates tax routes, delegates to tax_service, no FastAPI imports`
- ❌ `finance/expense_controller.py → orchestrates expense routes, delegates to expense_service, no FastAPI imports`
- ❌ `finance/ap_ar_controller.py → orchestrates AR/AP routes, delegates to ap_service/ar_service, no FastAPI imports`
- ❌ `finance/reporting_controller.py → orchestrates reporting routes, delegates to reporting_service, no FastAPI imports`
- ❌ `finance/control_tower_controller.py → orchestrates control tower routes, delegates to control_tower_service, no FastAPI imports`
- ❌ `payments_controller.py → orchestrates payment routes, delegates to payment_engine, no FastAPI imports`
- ❌ `payments/payment_gateway_controller.py → orchestrates gateway wizard routes, delegates to payment_gateway_registry + payment_vault_service, no FastAPI imports`
- ❌ `promotion_controller.py → orchestrates promotion routes, delegates to promotion_engine, no FastAPI imports`
- ❌ `coupons_controller.py → orchestrates coupon routes, delegates to coupon_service, no FastAPI imports`
- ❌ `finance/treasury_service.py → owns DB writes for treasury (cash position, snapshots, forecasts, settlements, gateway settlement tracking, COD remittance, reserve transfers)`
- ❌ `finance/general_ledger_service.py → owns DB writes for GL (post_journal_entry with Dr==Cr abort, SELECT FOR UPDATE on account_balances, trial balance, financial statements)`
- ❌ `finance/automation_service.py → orchestrates 14 automation items, triple-verify, staging, exception routing, config-as-data thresholds`
- ❌ `finance/bank_reconciliation_service.py → owns DB writes for bank rec (import statements, auto-match, exception routing, bulk reconcile)`
- ❌ `finance/supplier_payout_service.py → owns DB writes for supplier payouts (batch generator from commission_ledger_entries + payout_rules, Maker-Checker dispatch, supplier pre-review links)`
- ❌ `finance/tax_service.py → owns DB writes for tax (VAT/WHT calculation, inclusive/exclusive, category overrides, vat_remittances aggregation)`
- ❌ `finance/expense_service.py → owns DB writes for expenses (OCR staging, AP bill drafting, fixed assets card creation, duplicate check)`
- ❌ `finance/ap_service.py → owns DB writes for AP (bills, payments, aging, 3-way match PO↔GRN↔Invoice, landed-cost allocation)`
- ❌ `finance/ar_service.py → owns DB writes for AR (invoices, receipts, aging, dunning cadence, credit limits, IFRS-15 deferred amortization)`
- ❌ `finance/exception_queue_service.py → owns DB reads/writes for exception queue (prioritization, split-screen review data, approve/edit/reject actions, audit trail)`
- ❌ `finance/control_tower_service.py → owns DB reads/writes for automation control tower (automation toggles, threshold management, automation_runs logging, DLQ monitoring)`
- ❌ `finance/reporting_service.py → owns DB reads for reports (report_definitions JSONB queries, materialized view refreshes, CSV/PDF/email export)`
- ❌ `payments/payment_engine.py → central payment router (smart routing, tier-based fallback, ZoziPaymentEvent dispatch to Treasury, health monitoring)`
- ❌ `payments/payment_gateway_registry.py → auto-discovery engine for payment gateway adapters (pkgutil scan)`
- ❌ `payments/payment_webhook_service.py → webhook handler (ZoziPaymentEvent normalizer, idempotency gate via ProcessedWebhookEvent, signature verification)`
- ❌ `payments/payment_vault_service.py → AES-256-GCM credential vault (encrypt_secret, decrypt_secret, key rotation)`
- ❌ `promotions/promotion_engine.py → rules-based promotion engine (evaluate cart/order, stacking/best-only, precedence order, fraud detection)`
- ❌ `promotions/promotion_evaluator.py → promotion evaluator (fetch active promotions, evaluate rules, calculate discount, record in ledger)`
- ❌ `promotions/promotion_ledger_service.py → immutable promotion ledger service (one row per application, supplier contribution tracking, fraud flags)`
- ❌ `promotions/referral_service.py → referral service (code generation, referee validation, points awarding, fraud checks, delay for refunds)`
- ❌ `promotions/points_service.py → points service (balance tracking, redemption, expiry, monthly cap)`
- ❌ `discounts/coupon_service.py → coupon service (validation, usage tracking, stacking, country-scoping, soft-delete/archive)`
- ❌ `catalog/commission_calculation_service.py → commission calculation service (rate resolution per order item, low-value cap enforcement, immutable ledger entries)`
- ❌ `middleware/rls_middleware.py → RLS enforcement on all finance tables keyed on `country_code`; cross-country reads return zero rows without global/admin role`
- ❌ `middleware/finance_permission_middleware.py → Finance permission enforcement (finance.ap.post, finance.ledger.approve, finance.reconciliation, etc.)`
- ❌ `middleware/pci_dss_compliance_middleware.py → PCI-DSS compliance middleware (payment data handling, credential vault integration)`
- ❌ `jobs/bank_reconciliation_worker.py → background worker for daily bank statement import + auto-match (CSV/API)`
- ❌ `jobs/payout_batch_worker.py → background worker for nightly payout batch generator (cron 02:00, commission_ledger_entries + payout_rules → payout_batches draft)`
- ❌ `jobs/supplier_payout_dispatch_worker.py → background worker for supplier payout dispatch (Maker-Checker, supplier pre-review SMS/email links)`
- ❌ `jobs/accrual_reversal_worker.py → background worker for auto-accrual & reversal (month-end 23:59 / day-1 cron)`
- ❌ `jobs/depreciation_worker.py → background worker for monthly depreciation run (straight-line/declining, disposal gain/loss)`
- ❌ `jobs/fx_revaluation_worker.py → background worker for month-end FX revaluation (timestamped exchange_rates, draft JEs)`
- ❌ `jobs/vat_remittance_worker.py → background worker for continuous VAT aggregation + month-end ZATCA/FTA CSV export wizard`
- ❌ `jobs/orphan_detector_worker.py → background worker for daily 03:00 orphan detector (delivered/paid orders without journal entries → Critical alert)`
- ❌ `jobs/ocr_expense_worker.py → background worker for OCR expense/asset capture (camera/upload/email → scanned_expenses staging, pgvector embed)`
- ❌ `jobs/email_to_ledger_worker.py → background worker for IMAP watcher on finance@zozi.com (PDFs/CSVs → scanned_expenses/gateway_settlement_schedules)`
- ❌ `jobs/import_purchase_worker.py → background worker for import & purchase automation (PO/GRN/vendor-invoice → 3-way match + landed-cost allocation)`
- ❌ `jobs/loan_investment_worker.py → background worker for loans & investments schedule cron (effective-interest amortization / valuation JEs)`
- ❌ `jobs/wholesale_b2b_worker.py → background worker for wholesale/B2B revenue (bulk-order dispatch, AR invoices, IFRS-15 deferred amortization, auto dunning cadence)`
- ❌ `jobs/dunning_worker.py → background worker for auto dunning cadence (emails day 3/7/14, late-fee per config)`
- ❌ `jobs/report_scheduler_worker.py → background worker for scheduled report delivery (daily/weekly/monthly email/CSV/PDF)`
- ❌ `jobs/supplier_pre_review_worker.py → background worker for supplier pre-review link dispatch (secure SMS/email before payout approval)`
- ❌ `jobs/data_retention_worker.py → background worker for data retention (audit logs archive to S3 after 2yr, outbox hard delete 7d after processed)`
- ❌ `events/finance_events.py → domain event schemas for finance (OrderDelivered, RefundApproved, PaymentCaptured, PayoutDispatched, JournalEntryPosted, BankReconciled, etc.)`
- ❌ `events/payment_events.py → domain event schemas for payment events (ZoziPaymentEvent, PAYMENT_CAPTURED, REFUND_SUCCEEDED, CHARGEBACK_OPENED)`
- ❌ `providers/payments/stripe_provider.py → Stripe adapter (5 mandatory methods + normalize_webhook → ZoziPaymentEvent, health_check, idempotency)`
- ❌ `providers/payments/tap_provider.py → Tap adapter (5 mandatory methods + normalize_webhook → ZoziPaymentEvent, health_check, idempotency)`
- ❌ `providers/payments/thawani_provider.py → Thawani adapter (5 mandatory methods + normalize_webhook → ZoziPaymentEvent, health_check, idempotency)`
- ❌ `providers/payments/paytabs_provider.py → PayTabs adapter (5 mandatory methods + normalize_webhook → ZoziPaymentEvent, health_check, idempotency)`
- ❌ `providers/payments/mada_provider.py → Mada adapter (5 mandatory methods + normalize_webhook → ZoziPaymentEvent, health_check, idempotency)`
- ❌ `providers/payments/stc_pay_provider.py → STC Pay adapter (5 mandatory methods + normalize_webhook → ZoziPaymentEvent, health_check, idempotency)`
- ❌ `providers/payments/generic_rest_adapter.py → Generic REST Adapter (no-code gateway setup via DB-stored templates for Charge URL, Auth Headers, JSON Payload Template)`
- ❌ `providers/ai/ocr_provider.py → OCR provider (receipt/bill/invoice parsing, per-field confidence, pgvector embed, duplicate hash)`
- ❌ `providers/ai/whisper_provider.py → Whisper STT provider (voice-to-text finance ops, EN phi3/AR qwen2.5, explicit degraded mode)`
- ❌ `providers/ai/finance_chatbot_provider.py → Finance chatbot provider (RAG over CoA+ledger+docs via pgvector, confirm-gated auto-post)`
- ❌ `providers/media/media_storage_provider.py → R2/S3 media storage adapter (scanned receipts, invoices, asset photos, presigned URLs)`

### Database Files

**Present (9):**

- ✅ `base.py`
- ✅ `database.py`
- ✅ `session.py`
- ✅ `transaction.py`
- ✅ `schemas.py`
- ✅ `models.py`
- ✅ `create_tables.py`
- ✅ `init_db.py`
- ✅ `database_logging.py`

**Missing (4):**

- ❌ `security/`
- ❌ `setup/`
- ❌ `seeds/`
- ❌ `alembic/`

### Model Files

**Missing (1):**

- ❌ `mixins.py → AuditMixin, SoftDeleteMixin, VersionMixin`

### Frontend Web

**Present (2):**

- ✅ `web_app/admin/finance/page.tsx`
- ✅ `web_app/admin/promotions/page.tsx`

**Missing (45):**

- ❌ `web_app/admin/finance/dashboard/page.tsx`
- ❌ `web_app/admin/finance/treasury/page.tsx`
- ❌ `web_app/admin/finance/ledger/page.tsx`
- ❌ `web_app/admin/finance/settlements/page.tsx`
- ❌ `web_app/admin/finance/receivables/page.tsx`
- ❌ `web_app/admin/finance/payables/page.tsx`
- ❌ `web_app/admin/finance/purchasing/page.tsx`
- ❌ `web_app/admin/finance/assets/page.tsx`
- ❌ `web_app/admin/finance/tax/page.tsx`
- ❌ `web_app/admin/finance/reports/page.tsx`
- ❌ `web_app/admin/finance/automation/page.tsx`
- ❌ `web_app/admin/finance/reconciliation/page.tsx`
- ❌ `web_app/admin/finance/payouts/page.tsx`
- ❌ `web_app/admin/payment-gateways/page.tsx`
- ❌ `web_app/admin/commissions/page.tsx`
- ❌ `admin/promotions/CouponsPanel.tsx`
- ❌ `web_app/admin/discounts/page.tsx`
- ❌ `web_app/admin/countries/:code/finance/page.tsx`
- ❌ `finance/CommandCenter.tsx`
- ❌ `finance/Dashboard.tsx`
- ❌ `finance/ExceptionQueue.tsx`
- ❌ `finance/ReconciliationView.tsx`
- ❌ `finance/PayoutControlRoom.tsx`
- ❌ `finance/AutomationControlTower.tsx`
- ❌ `finance/ReportBuilder.tsx`
- ❌ `finance/OCRDropzone.tsx`
- ❌ `finance/ChatbotDrawer.tsx`
- ❌ `finance/VoiceChip.tsx`
- ❌ `finance/CommissionPage.tsx`
- ❌ `finance/PromotionBuilder.tsx`
- ❌ `finance/CouponsPanel.tsx`
- ❌ `hooks/useFinanceDashboard.ts`
- ❌ `hooks/useExceptionQueue.ts`
- ❌ `hooks/useAutomationControlTower.ts`
- ❌ `hooks/useBankReconciliation.ts`
- ❌ `hooks/usePayouts.ts`
- ❌ `hooks/usePromotions.ts`
- ❌ `hooks/useCoupons.ts`
- ❌ `lib/finance/financeApi.ts`
- ❌ `lib/finance/reconciliationApi.ts`
- ❌ `lib/finance/payoutApi.ts`
- ❌ `lib/promotions/promotionsApi.ts`
- ❌ `lib/discounts/couponsApi.ts`
- ❌ `lib/order/orders.ts`
- ❌ `styles/finance.css`

### Frontend Mobile

**Present (3):**

- ✅ `lib/api.ts`
- ✅ `lib/paymentService.ts`
- ✅ `lib/authStore.ts`

**Missing (16):**

- ❌ `mobile_app/admin/finance/page.tsx`
- ❌ `admin/finance/dashboard.tsx`
- ❌ `admin/finance/reconciliation.tsx`
- ❌ `admin/finance/payouts.tsx`
- ❌ `admin/finance/automation.tsx`
- ❌ `mobile_app/admin/payment-gateways/page.tsx`
- ❌ `mobile_app/admin/commissions/page.tsx`
- ❌ `mobile_app/supplier/payouts/page.tsx`
- ❌ `mobile_app/supplier/invoices/page.tsx`
- ❌ `mobile_app/logistics-partner/payouts/page.tsx`
- ❌ `mobile_app/logistics-partner/remittance/page.tsx`
- ❌ `components/finance/ExceptionQueue.tsx`
- ❌ `components/finance/VoiceChip.tsx`
- ❌ `components/finance/OCRDropzone.tsx`
- ❌ `components/finance/CommissionPreview.tsx`
- ❌ `theme/`

### Tests

**Missing (50):**

- ❌ `tests/backend/_test_finance_general_ledger.py`
- ❌ `tests/backend/_test_finance_treasury.py`
- ❌ `tests/backend/_test_finance_double_entry.py`
- ❌ `tests/backend/_test_finance_penny_rounding.py`
- ❌ `tests/backend/_test_finance_time_travel_audit.py`
- ❌ `tests/backend/_test_finance_bank_reconciliation.py`
- ❌ `tests/backend/_test_finance_commission_engine.py`
- ❌ `tests/backend/_test_finance_supplier_payout.py`
- ❌ `tests/backend/_test_finance_tax_engine.py`
- ❌ `tests/backend/_test_finance_expense_ocr.py`
- ❌ `tests/backend/_test_finance_ap_3way_match.py`
- ❌ `tests/backend/_test_finance_ar_dunning.py`
- ❌ `tests/backend/_test_finance_report_builder.py`
- ❌ `tests/backend/_test_finance_control_tower.py`
- ❌ `tests/backend/_test_finance_automation_exception_queue.py`
- ❌ `tests/backend/_test_finance_automation_idempotency.py`
- ❌ `tests/backend/_test_finance_automation_kill_switch.py`
- ❌ `tests/backend/_test_finance_payment_webhook_normalizer.py`
- ❌ `tests/backend/_test_finance_payment_vault.py`
- ❌ `tests/backend/_test_finance_payment_routing_fallback.py`
- ❌ `tests/backend/_test_finance_promotion_engine.py`
- ❌ `tests/backend/_test_finance_promotion_ledger.py`
- ❌ `tests/backend/_test_finance_referral_points.py`
- ❌ `tests/backend/_test_finance_coupon_validation.py`
- ❌ `tests/backend/_test_finance_coupon_stacking.py`
- ❌ `tests/backend/_test_finance_shadow_mode_cutover.py`
- ❌ `tests/backend/_test_finance_orphan_detector.py`
- ❌ `tests/backend/_test_finance_rls_country_isolation.py`
- ❌ `tests/backend/_test_finance_chaos_monkey.py`
- ❌ `tests/backend/_test_finance_k6_load.py`
- ❌ `tests/frontend/web_app/_test_finance_command_center.test.tsx`
- ❌ `tests/frontend/web_app/_test_finance_dashboard.test.tsx`
- ❌ `tests/frontend/web_app/_test_finance_exception_queue.test.tsx`
- ❌ `tests/frontend/web_app/_test_finance_reconciliation.test.tsx`
- ❌ `tests/frontend/web_app/_test_finance_payout_control_room.test.tsx`
- ❌ `tests/frontend/web_app/_test_finance_automation_tower.test.tsx`
- ❌ `tests/frontend/web_app/_test_finance_report_builder.test.tsx`
- ❌ `tests/frontend/web_app/_test_finance_ocr_dropzone.test.tsx`
- ❌ `tests/frontend/web_app/_test_finance_chatbot_drawer.test.tsx`
- ❌ `tests/frontend/web_app/_test_finance_payment_gateways.test.tsx`
- ❌ `tests/frontend/web_app/_test_finance_commissions.test.tsx`
- ❌ `tests/frontend/web_app/_test_finance_promotions.test.tsx`
- ❌ `tests/frontend/web_app/_test_finance_coupons.test.tsx`
- ❌ `tests/frontend/mobile_app/_test_finance_mobile.test.tsx`
- ❌ `tests/frontend/mobile_app/_test_finance_supplier_payouts_mobile.test.tsx`
- ❌ `tests/frontend/mobile_app/_test_finance_logistics_remittance_mobile.test.tsx`
- ❌ `tests/playwright/_test_finance_e2e.spec.ts`
- ❌ `tests/playwright/_test_finance_command_center_e2e.spec.ts`
- ❌ `tests/playwright/_test_finance_payment_flow_e2e.spec.ts`
- ❌ `tests/playwright/_test_finance_reconciliation_e2e.spec.ts`

### API Routes

**Missing (104):**

- ❌ `GET /api/v1/finance/dashboard`
- ❌ `GET /api/v1/finance/treasury/cash-position`
- ❌ `GET /api/v1/finance/treasury/snapshots`
- ❌ `GET /api/v1/finance/treasury/forecasts`
- ❌ `GET /api/v1/finance/treasury/gateway-settlements`
- ❌ `POST /api/v1/finance/treasury/reserve-transfer`
- ❌ `GET /api/v1/finance/ledger/journal-entries`
- ❌ `GET /api/v1/finance/ledger/journal-entries/{entry_id}`
- ❌ `GET /api/v1/finance/ledger/trial-balance`
- ❌ `GET /api/v1/finance/ledger/balance-sheet`
- ❌ `GET /api/v1/finance/ledger/income-statement`
- ❌ `GET /api/v1/finance/ledger/cash-flow`
- ❌ `POST /api/v1/finance/ledger/pending-journal-entries`
- ❌ `POST /api/v1/finance/ledger/pending-journal-entries/{entry_id}/approve`
- ❌ `POST /api/v1/finance/ledger/pending-journal-entries/{entry_id}/reject`
- ❌ `GET /api/v1/finance/automation/runs`
- ❌ `GET /api/v1/finance/automation/runs/{run_id}`
- ❌ `POST /api/v1/finance/automation/exception-queue/{item_id}/approve`
- ❌ `POST /api/v1/finance/automation/exception-queue/{item_id}/reject`
- ❌ `POST /api/v1/finance/automation/control-tower/toggle`
- ❌ `PUT /api/v1/finance/automation/control-tower/thresholds`
- ❌ `GET /api/v1/finance/automation/dlq`
- ❌ `POST /api/v1/finance/bank-reconciliation/import`
- ❌ `POST /api/v1/finance/bank-reconciliation/auto-match`
- ❌ `POST /api/v1/finance/bank-reconciliation/reconcile`
- ❌ `GET /api/v1/finance/bank-reconciliation/exceptions`
- ❌ `GET /api/v1/finance/commissions/ledger`
- ❌ `GET /api/v1/finance/commissions/rules`
- ❌ `PUT /api/v1/finance/commissions/rules/{rule_id}`
- ❌ `POST /api/v1/finance/commissions/preview`
- ❌ `GET /api/v1/finance/commissions/badge-tiers`
- ❌ `PUT /api/v1/finance/commissions/badge-tiers/{tier_id}`
- ❌ `GET /api/v1/finance/payouts/batches`
- ❌ `POST /api/v1/finance/payouts/batches/{batch_id}/approve`
- ❌ `POST /api/v1/finance/payouts/batches/{batch_id}/dispatch`
- ❌ `GET /api/v1/finance/payouts/supplier/{supplier_id}`
- ❌ `GET /api/v1/finance/tax/rules`
- ❌ `PUT /api/v1/finance/tax/rules/{rule_id}`
- ❌ `GET /api/v1/finance/tax/country-category-rates`
- ❌ `POST /api/v1/finance/tax/vat-remittance/export`
- ❌ `POST /api/v1/finance/expenses/scan`
- ❌ `POST /api/v1/finance/expenses/{expense_id}/approve`
- ❌ `POST /api/v1/finance/expenses/{expense_id}/reject`
- ❌ `GET /api/v1/finance/ap/bills`
- ❌ `POST /api/v1/finance/ap/bills`
- ❌ `POST /api/v1/finance/ap/3way-match`
- ❌ `GET /api/v1/finance/ar/invoices`
- ❌ `POST /api/v1/finance/ar/invoices`
- ❌ `GET /api/v1/finance/ar/aging`
- ❌ `POST /api/v1/finance/ar/dunning`
- ❌ `GET /api/v1/finance/reports`
- ❌ `POST /api/v1/finance/reports`
- ❌ `GET /api/v1/finance/reports/{report_id}/preview`
- ❌ `POST /api/v1/finance/reports/{report_id}/execute`
- ❌ `POST /api/v1/finance/reports/{report_id}/schedule`
- ❌ `GET /api/v1/finance/reports/{report_id}/export`
- ❌ `GET /api/v1/finance/control-tower/automations`
- ❌ `POST /api/v1/finance/control-tower/automations/{automation_id}/toggle`
- ❌ `PUT /api/v1/finance/control-tower/automations/{automation_id}/thresholds`
- ❌ `GET /api/v1/finance/control-tower/runs`
- ❌ `GET /api/v1/finance/control-tower/dlq`
- ❌ `GET /api/v1/payments/methods`
- ❌ `POST /api/v1/payments/create`
- ❌ `POST /api/v1/payments/confirm`
- ❌ `POST /api/v1/payments/webhook/{provider_code}`
- ❌ `POST /api/v1/payments/refund`
- ❌ `GET /api/v1/payments/transactions`
- ❌ `POST /api/v1/admin/payment-gateways`
- ❌ `GET /api/v1/admin/payment-gateways`
- ❌ `PUT /api/v1/admin/payment-gateways/{gateway_id}`
- ❌ `POST /api/v1/admin/payment-gateways/{gateway_id}/test-connection`
- ❌ `GET /api/v1/admin/payment-gateways/health`
- ❌ `POST /api/v1/admin/payment-gateways/routing-rules`
- ❌ `POST /api/v1/promotions/apply`
- ❌ `GET /api/v1/promotions/active`
- ❌ `POST /api/v1/admin/promotions`
- ❌ `GET /api/v1/admin/promotions/config`
- ❌ `PUT /api/v1/admin/promotions/config`
- ❌ `GET /api/v1/admin/promotions/tiers`
- ❌ `POST /api/v1/admin/promotions/tiers`
- ❌ `PUT /api/v1/admin/promotions/tiers/{tier_id}`
- ❌ `DELETE /api/v1/admin/promotions/tiers/{tier_id}`
- ❌ `POST /api/v1/admin/promotions/preview`
- ❌ `POST /api/v1/promotions/points/redeem`
- ❌ `GET /api/v1/promotions/points/balance`
- ❌ `POST /api/v1/coupons/validate`
- ❌ `GET /api/v1/coupons`
- ❌ `POST /api/v1/coupons`
- ❌ `DELETE /api/v1/coupons/{coupon_id}`
- ❌ `POST /api/v1/coupons/bulk-archive`
- ❌ `POST /api/v1/coupons/bulk-restore`
- ❌ `GET /api/v1/admin/{code}/promotions/coupons`
- ❌ `POST /api/v1/admin/{code}/promotions/coupons`
- ❌ `POST /api/v1/coupons/{id}/archive`
- ❌ `POST /api/v1/coupons/{id}/restore`
- ❌ `GET /api/v1/admin/commissions`
- ❌ `PUT /api/v1/admin/commissions/global-rate`
- ❌ `GET /api/v1/admin/commissions/category-rates`
- ❌ `PUT /api/v1/admin/commissions/category-rates/{rate_id}`
- ❌ `GET /api/v1/admin/commissions/supplier-overrides`
- ❌ `POST /api/v1/admin/commissions/supplier-overrides`
- ❌ `GET /api/v1/admin/commissions/badge-tiers`
- ❌ `POST /api/v1/admin/commissions/badge-tiers`
- ❌ `POST /api/v1/admin/commissions/preview`

### DB Model Classes

**Present (39):**

- ✅ `JournalEntry`
- ✅ `JournalEntryLine`
- ✅ `PendingJournalEntry`
- ✅ `FiscalPeriod`
- ✅ `AccountGroup`
- ✅ `Account`
- ✅ `AccountBalance`
- ✅ `TreasuryAccount`
- ✅ `TreasuryTransaction`
- ✅ `CashPositionSnapshot`
- ✅ `GatewaySettlementSchedule`
- ✅ `CashFlowForecast`
- ✅ `ScannedExpense`
- ✅ `BankStatementImport`
- ✅ `BankStatementLine`
- ✅ `BankMappingRule`
- ✅ `CommissionLedgerEntry`
- ✅ `BadgeTier`
- ✅ `PayoutRule`
- ✅ `PayoutBatch`
- ✅ `PayoutBatchItem`
- ✅ `Payout`
- ✅ `TaxRule`
- ✅ `CountryCategoryTaxRate`
- ✅ `FixedAsset`
- ✅ `Accrual`
- ✅ `PurchaseOrder`
- ✅ `AutomationRule`
- ✅ `PaymentGatewayConnection`
- ✅ `ProcessedWebhookEvent`
- ✅ `PromotionEngineConfig`
- ✅ `PromotionOrderTier`
- ✅ `UserPoints`
- ✅ `PointsTransaction`
- ✅ `Coupon`
- ✅ `CouponUsage`
- ✅ `RefundLedger`
- ✅ `MediaAsset`
- ✅ `CountryConfig`

**Missing (23):**

- ❌ `ExchangeRate`
- ❌ `AutomationRun`
- ❌ `ExceptionQueue`
- ❌ `CommissionRule`
- ❌ `CategoryCommissionRate`
- ❌ `VatRemittance`
- ❌ `ApBill`
- ❌ `ApLedgerEntry`
- ❌ `ArInvoice`
- ❌ `ArLedgerEntry`
- ❌ `DunningSchedule`
- ❌ `FixedAssetDepreciation`
- ❌ `Grn`
- ❌ `LoanSchedule`
- ❌ `InvestmentSchedule`
- ❌ `ReportDefinition`
- ❌ `ReportSchedule`
- ❌ `ReportExecution`
- ❌ `EventDeadLetter`
- ❌ `PaymentIntent`
- ❌ `PaymentTransaction`
- ❌ `Promotion`
- ❌ `PromotionApplication`

---

## SYS_005 — Multi-Country Admin Onboarding & Management System

### Backend Files

**Missing (58):**

- ❌ `country_admin.py → thin router for country admin CRUD + draft/approve/publish/rollback endpoints`
- ❌ `country_staff.py → thin router for country staff assignment endpoints`
- ❌ `country_auto_populate.py → thin router for country auto-populate / heuristic engine endpoints`
- ❌ `country_research.py → thin router for country research data endpoints`
- ❌ `country_versioning.py → thin router for country version history endpoints`
- ❌ `country_payouts.py → thin router for country payouts endpoints`
- ❌ `country_communications.py → thin router for country communications endpoints`
- ❌ `country_maps.py → thin router for country map endpoints`
- ❌ `country_dropdown.py → thin router for country dropdown/selector endpoints`
- ❌ `core/country_admin_controller.py → orchestrates country workflow routes, delegates to country_config_admin_service, no FastAPI imports`
- ❌ `core/country_staff_controller.py → orchestrates country staff routes, delegates to country_staff_service, no FastAPI imports`
- ❌ `router_bridges/country_research.py → orchestrates country research routes, delegates to country_research_service, no FastAPI imports`
- ❌ `router_bridges/country_communications.py → orchestrates country communications routes, delegates to country_communication_service, no FastAPI imports`
- ❌ `geography/country_controller.py → orchestrates country CRUD routes, delegates to country_service, no FastAPI imports`
- ❌ `geography/country_versioning_controller.py → orchestrates country versioning routes, delegates to country_versioning_service, no FastAPI imports`
- ❌ `core/country_payouts_controller.py → orchestrates country payouts routes, delegates to country_payouts_service, no FastAPI imports`
- ❌ `core/country_maps_controller.py → orchestrates country maps routes, delegates to country_maps_service, no FastAPI imports`
- ❌ `core/country_dropdown_controller.py → orchestrates country dropdown routes, delegates to country_dropdown_service, no FastAPI imports`
- ❌ `geography/country_communication_controller.py → orchestrates country communication routes, delegates to country_communication_service, no FastAPI imports`
- ❌ `geography/country_service.py → owns DB reads for country configs and basic data`
- ❌ `geography/country_write_service.py → owns DB writes for country configs`
- ❌ `geography/country_config_admin_service.py → owns DB writes for country config lifecycle (draft/approve/publish/rollback), version history, audit logging`
- ❌ `geography/country_config_write_service.py → owns DB writes for country config writes`
- ❌ `geography/country_heuristic_engine.py → algorithmic heuristic engine (payment gateway ranking, commission tiers, KYC rules, COD reliance, payout settings, logistics model, fraud risk scoring)`
- ❌ `geography/country_auto_populate.py → orchestrates auto-populate from research JSON`
- ❌ `geography/country_auto_populate_write_service.py → owns DB writes for auto-populated country configs`
- ❌ `geography/country_staff_service.py → owns DB reads for country staff assignments and permissions`
- ❌ `geography/country_staff_write_service.py → owns DB writes for country staff assignments, role sync, JWT claim updates`
- ❌ `geography/country_rls_service.py → owns RLS enforcement and country access validation`
- ❌ `geography/country_versioning_service.py → owns DB writes for CountryConfigVersion records`
- ❌ `geography/country_audit_admin_service.py → owns DB writes for country audit logs`
- ❌ `geography/country_admin_write_service.py → owns DB writes for admin country operations`
- ❌ `geography/country_tax_service.py → owns DB writes for country tax config (VAT/WHT, category overrides)`
- ❌ `geography/country_communication_service.py → owns DB writes for country communications`
- ❌ `geography/country_research.py → country research data ingestion from companion doc`
- ❌ `geography/country_curated.py → curated country data service`
- ❌ `geography/country_detection.py → country detection service (IP → country)`
- ❌ `geography/country_data_orchestrator.py → orchestrates country data pipeline`
- ❌ `geography/country_restriction_service.py → country restriction/access control service`
- ❌ `geography/country_payout_write_service.py → owns DB writes for country payouts config`
- ❌ `geography/country_maps_service.py → owns DB writes for country map data`
- ❌ `geography/country_dropdown_service.py → owns DB reads for country dropdown data`
- ❌ `security/country_context_service.py → resolves country context from request (JWT → staff → IP → header)`
- ❌ `core/country_admin_service.py → core country admin service (shared logic)`
- ❌ `core/country_staff_service.py → core country staff service (shared logic)`
- ❌ `core/country_payouts_service.py → core country payouts service`
- ❌ `core/country_maps_service.py → core country maps service`
- ❌ `core/country_dropdown_service.py → core country dropdown service`
- ❌ `ai/country_ai_research.py → AI research service for country intelligence`
- ❌ `country/country_communications_service.py → country communications service`
- ❌ `country/country_communications_read_service.py → country communications read service`
- ❌ `middleware/country_context.py → country context middleware (JWT → staff → IP → header fallback)`
- ❌ `middleware/rls_middleware.py → RLS enforcement middleware (sets app.current_country_code, enforces country access)`
- ❌ `jobs/country_auto_populate_worker.py → background worker for country auto-populate from research JSON (Celery/Redis)`
- ❌ `jobs/data_retention_worker.py → background worker for data retention (audit logs archive, version history cleanup)`
- ❌ `events/event_publisher.py → Redis pub/sub event publisher (reuse existing, extend for country events)`
- ❌ `providers/geography/country.py → geography provider (country data, maps, IP detection)`
- ❌ `providers/geography/country_http.py → HTTP provider for external country data APIs`

### Database Files

**Present (9):**

- ✅ `base.py`
- ✅ `database.py`
- ✅ `session.py`
- ✅ `transaction.py`
- ✅ `schemas.py`
- ✅ `models.py`
- ✅ `create_tables.py`
- ✅ `init_db.py`
- ✅ `database_logging.py`

**Missing (4):**

- ❌ `security/`
- ❌ `setup/`
- ❌ `seeds/`
- ❌ `alembic/`

### Model Files

**Missing (1):**

- ❌ `mixins.py → AuditMixin, SoftDeleteMixin, VersionMixin`

### Frontend Web

**Present (25):**

- ✅ `web_app/admin/countries/page.tsx`
- ✅ `web_app/admin/countries/[code]/staff/page.tsx`
- ✅ `admin/countries/CountryLedgerTable.tsx`
- ✅ `admin/countries/constants.ts`
- ✅ `admin/countries/types.ts`
- ✅ `admin/countries/components/OverviewTab.tsx`
- ✅ `admin/countries/components/TaxTab.tsx`
- ✅ `admin/countries/components/LogisticsProvidersTab.tsx`
- ✅ `admin/countries/components/LogisticsModelTab.tsx`
- ✅ `admin/countries/components/PaymentGatewaysTab.tsx`
- ✅ `admin/countries/components/KycTab.tsx`
- ✅ `admin/countries/components/PayoutSettingsTab.tsx`
- ✅ `admin/countries/components/CommissionTiersTab.tsx`
- ✅ `admin/countries/components/CategoryCommissionsTab.tsx`
- ✅ `admin/countries/components/FeatureFlagsTab.tsx`
- ✅ `admin/countries/components/LocalizationTab.tsx`
- ✅ `admin/countries/components/AnalyticsTab.tsx`
- ✅ `admin/countries/components/StaffTab.tsx`
- ✅ `admin/countries/components/RegionsTab.tsx`
- ✅ `admin/countries/components/MapTab.tsx`
- ✅ `admin/countries/components/CommunicationsTab.tsx`
- ✅ `admin/countries/components/PromotionsTab.tsx`
- ✅ `admin/countries/components/VersionsTab.tsx`
- ✅ `admin/countries/components/LegalRulesTab.tsx`
- ✅ `admin/countries/components/CountriesTabProps.ts`

**Missing (1):**

- ❌ `web_app/admin/countries/[code]/page.tsx`

### Frontend Mobile

**Present (1):**

- ✅ `lib/api.ts`

**Missing (4):**

- ❌ `mobile_app/admin/countries/[code]/page.tsx`
- ❌ `components/admin/CountryOverview.tsx`
- ❌ `components/admin/CountryTaxConfig.tsx`
- ❌ `components/admin/CountryLogistics.tsx`

### Tests

**Missing (19):**

- ❌ `tests/backend/_test_country_onboarding.py`
- ❌ `tests/backend/_test_country_rls_isolation.py`
- ❌ `tests/backend/_test_country_heuristic_engine.py`
- ❌ `tests/backend/_test_country_admin_lifecycle.py`
- ❌ `tests/backend/_test_country_staff_rbac.py`
- ❌ `tests/backend/_test_country_auto_populate.py`
- ❌ `tests/backend/_test_country_tax_resolution.py`
- ❌ `tests/backend/_test_country_logistics_isolation.py`
- ❌ `tests/backend/_test_country_payment_gateway_country_scoping.py`
- ❌ `tests/backend/_test_country_commission_overrides.py`
- ❌ `tests/backend/_test_country_feature_flags.py`
- ❌ `tests/backend/_test_country_cross_customer_session.py`
- ❌ `tests/backend/_test_country_config_versioning.py`
- ❌ `tests/frontend/web_app/_test_country_admin.test.tsx`
- ❌ `tests/frontend/web_app/_test_country_staff.test.tsx`
- ❌ `tests/frontend/web_app/_test_country_onboarding_wizard.test.tsx`
- ❌ `tests/frontend/mobile_app/_test_country_mobile.test.tsx`
- ❌ `tests/playwright/_test_country_admin_e2e.spec.ts`
- ❌ `tests/playwright/_test_country_rls_e2e.spec.ts`

### API Routes

**Missing (51):**

- ❌ `GET /api/v1/countries`
- ❌ `GET /api/v1/countries/{code}`
- ❌ `POST /api/v1/countries`
- ❌ `PUT /api/v1/countries/{code}`
- ❌ `DELETE /api/v1/countries/{code}`
- ❌ `POST /api/v1/countries/{code}/draft`
- ❌ `POST /api/v1/countries/{code}/approve`
- ❌ `POST /api/v1/countries/{code}/publish`
- ❌ `POST /api/v1/countries/{code}/rollback`
- ❌ `GET /api/v1/countries/{code}/versions`
- ❌ `GET /api/v1/countries/{code}/versions/{version_id}`
- ❌ `POST /api/v1/countries/{code}/preview/tax`
- ❌ `POST /api/v1/countries/{code}/preview/logistics`
- ❌ `POST /api/v1/countries/{code}/preview/commission`
- ❌ `GET /api/v1/countries/{code}/staff`
- ❌ `POST /api/v1/countries/{code}/staff`
- ❌ `PUT /api/v1/countries/{code}/staff/{staff_id}`
- ❌ `DELETE /api/v1/countries/{code}/staff/{staff_id}`
- ❌ `GET /api/v1/countries/{code}/suppliers`
- ❌ `POST /api/v1/countries/{code}/suppliers`
- ❌ `GET /api/v1/countries/{code}/products`
- ❌ `POST /api/v1/countries/{code}/products`
- ❌ `GET /api/v1/countries/{code}/orders`
- ❌ `GET /api/v1/countries/{code}/banners`
- ❌ `POST /api/v1/countries/{code}/banners`
- ❌ `GET /api/v1/countries/{code}/promotions`
- ❌ `POST /api/v1/countries/{code}/promotions`
- ❌ `GET /api/v1/countries/{code}/logistics-partners`
- ❌ `POST /api/v1/countries/{code}/logistics-partners`
- ❌ `GET /api/v1/countries/{code}/payment-gateways`
- ❌ `POST /api/v1/countries/{code}/payment-gateways`
- ❌ `GET /api/v1/countries/{code}/tax`
- ❌ `PUT /api/v1/countries/{code}/tax`
- ❌ `GET /api/v1/countries/{code}/commissions`
- ❌ `PUT /api/v1/countries/{code}/commissions`
- ❌ `GET /api/v1/countries/{code}/feature-flags`
- ❌ `PUT /api/v1/countries/{code}/feature-flags`
- ❌ `GET /api/v1/countries/{code}/analytics`
- ❌ `GET /api/v1/countries/{code}/localization`
- ❌ `PUT /api/v1/countries/{code}/localization`
- ❌ `GET /api/v1/countries/auto-populate`
- ❌ `POST /api/v1/countries/auto-populate`
- ❌ `GET /api/v1/countries/{code}/payouts`
- ❌ `POST /api/v1/countries/{code}/payouts/settings`
- ❌ `GET /api/v1/countries/{code}/cod-reconciliation`
- ❌ `POST /api/v1/countries/{code}/cod-reconciliation/settle`
- ❌ `GET /api/v1/countries/global`
- ❌ `GET /api/v1/countries/{code}/gateway-credentials`
- ❌ `POST /api/v1/countries/{code}/gateway-credentials`
- ❌ `GET /api/v1/countries/{code}/kyc`
- ❌ `PUT /api/v1/countries/{code}/kyc`

### DB Model Classes

**Present (16):**

- ✅ `CountryConfig`
- ✅ `CountryConfigVersion`
- ✅ `CountryFeatureFlag`
- ✅ `CountryStaffAssignment`
- ✅ `CountryCity`
- ✅ `CountryCategoryTaxRate`
- ✅ `CountryCommunicationThread`
- ✅ `CrossCountryCustomerSession`
- ✅ `TaxRule`
- ✅ `ShippingRule`
- ✅ `PayoutRule`
- ✅ `CountryGatewayCredentials`
- ✅ `CountryLocalization`
- ✅ `CountryLogisticsZone`
- ✅ `LogisticsPartnerKYCRequirement`
- ✅ `SupplierKYCRequirement`

---

## SYS_006 — Country Intelligence & Auto-Research Feature

### Backend Files

**Missing (11):**

- ❌ `country_research.py → thin router for country research endpoints (POST /research/run, GET /research/{code}, GET /research/{code}/dashboard, GET /research/{code}/history, GET /research/{code}/json)`
- ❌ `geography/country_research_controller.py → orchestrates country research routes, delegates to country_research_service, no FastAPI imports`
- ❌ `geography/country_research_service.py → orchestrates research engine pipeline, persists results, manages history, delegates dashboard aggregation to country_research_dashboard_service`
- ❌ `geography/country_research_dashboard_service.py → aggregates 20 research modules into dashboard payload (stat cards, chart data, alerts, map overlays)`
- ❌ `geography/country_confidence_service.py → confidence decision tree enforcement (high→auto-use, medium→flag, low→manual verification required)`
- ❌ `geography/country_ai_research.py → Ollama LLM orchestration (prompt building, JSON parsing, model auto-selection, confidence tagging)`
- ❌ `middleware/research_progress_middleware.py → WebSocket middleware for real-time research progress updates during long-running jobs`
- ❌ `jobs/country_research_worker.py → background worker for country research pipeline (Celery/Redis), publishes progress events via Redis pub/sub`
- ❌ `events/country_research_events.py → domain event schemas for country research lifecycle (started, progress, completed, failed)`
- ❌ `providers/geography/country_research_provider.py → free data source adapters subclass BaseProvider (REST Countries, World Bank, Frankfurter, GeoNames, Wikipedia, Google News RSS, DuckDuckGo)`
- ❌ `providers/geography/country_llm_provider.py → Ollama LLM adapter subclass BaseAIProvider (deep qualitative research, health_check, async processing, confidence tagging)`

### Database Files

**Present (9):**

- ✅ `base.py`
- ✅ `database.py`
- ✅ `session.py`
- ✅ `transaction.py`
- ✅ `schemas.py`
- ✅ `models.py`
- ✅ `create_tables.py`
- ✅ `init_db.py`
- ✅ `database_logging.py`

**Missing (4):**

- ❌ `security/`
- ❌ `setup/`
- ❌ `seeds/`
- ❌ `alembic/`

### Model Files

**Missing (1):**

- ❌ `mixins.py → AuditMixin, SoftDeleteMixin, VersionMixin`

### Frontend Web

**Missing (11):**

- ❌ `web_app/admin/research/[country]/page.tsx`
- ❌ `research/StatCardsGrid.tsx`
- ❌ `research/ChartsSection.tsx`
- ❌ `research/RankedLists.tsx`
- ❌ `research/AlertPanel.tsx`
- ❌ `research/TimelineSection.tsx`
- ❌ `research/ConfidencePanel.tsx`
- ❌ `research/MapOverlay.tsx`
- ❌ `research/JsonExport.tsx`
- ❌ `hooks/useCountryResearch.ts`
- ❌ `lib/research/researchApi.ts`

### Frontend Mobile

**Missing (4):**

- ❌ `admin/research/[country].tsx`
- ❌ `components/research/ResearchStatCards.tsx`
- ❌ `components/research/ResearchModules.tsx`
- ❌ `lib/researchApi.ts`

### Tests

**Missing (10):**

- ❌ `tests/backend/_test_country_research_engine.py`
- ❌ `tests/backend/_test_country_research_api.py`
- ❌ `tests/backend/_test_country_research_confidence.py`
- ❌ `tests/backend/_test_country_research_dashboard.py`
- ❌ `tests/backend/_test_country_research_onboarding_integration.py`
- ❌ `tests/backend/_test_country_research_web_evidence.py`
- ❌ `tests/backend/_test_country_research_ollama_fallback.py`
- ❌ `tests/frontend/web_app/_test_country_research_dashboard.test.tsx`
- ❌ `tests/frontend/mobile_app/_test_country_research_mobile.test.tsx`
- ❌ `tests/playwright/_test_country_research_e2e.spec.ts`

### API Routes

**Missing (8):**

- ❌ `POST /api/v1/research/run`
- ❌ `GET /api/v1/research/{country_code}`
- ❌ `GET /api/v1/research/{country_code}/json`
- ❌ `GET /api/v1/research/{country_code}/dashboard`
- ❌ `GET /api/v1/research/{country_code}/history`
- ❌ `GET /api/v1/research/{country_code}/modules/{module_id}`
- ❌ `POST /api/v1/research/{country_code}/onboard`
- ❌ `GET /api/v1/research/sources/status`

### DB Model Classes

**Missing (4):**

- ❌ `CountryResearch`
- ❌ `ResearchModule`
- ❌ `ResearchWebEvidence`
- ❌ `CountryResearchHistory`

---

## SYS_007 — Payment System & Cash Management Cycle

### Backend Files

**Missing (61):**

- ❌ `payments.py -> thin router for payment endpoints (create, confirm, webhook, refund, methods, transactions)`
- ❌ `admin/payment_gateways_router.py -> thin router for payment gateway admin endpoints (wizard, credentials, test connection, routing rules)`
- ❌ `finance/treasury_router.py -> thin router for treasury endpoints (cash position, snapshots, forecasts, settlements, gateway settlements, COD remittance)`
- ❌ `finance/ledger_router.py -> thin router for general ledger endpoints (journal entries, pending entries, trial balance, financial statements)`
- ❌ `finance/commission_router.py -> thin router for commission endpoints (rates, ledger entries, supplier settlements, badge tiers)`
- ❌ `finance/supplier_payout_router.py -> thin router for supplier payout endpoints (batches, batch items, payouts, pre-review links)`
- ❌ `finance/bank_reconciliation_router.py -> thin router for bank reconciliation endpoints (import statements, match, reconcile, exception filter)`
- ❌ `finance/ap_ar_router.py -> thin router for AR/AP endpoints (invoices, bills, receipts, payments, aging, dunning)`
- ❌ `orders/customer_orders_router.py -> thin router for customer order endpoints (create, preview, list, get, tracking, cancel)`
- ❌ `logistics/shipments_router.py -> thin router for shipment endpoints (create, list, status transitions, events, GPS update, POD)`
- ❌ `payments_controller.py -> orchestrates payment routes, delegates to payment_engine, no FastAPI imports`
- ❌ `payments/payment_gateway_controller.py -> orchestrates gateway wizard routes, delegates to payment_gateway_registry + payment_vault_service, no FastAPI imports`
- ❌ `finance/treasury_controller.py -> orchestrates treasury routes, delegates to treasury_service, no FastAPI imports`
- ❌ `finance/ledger_controller.py -> orchestrates GL routes, delegates to general_ledger_service, no FastAPI imports`
- ❌ `finance/commission_controller.py -> orchestrates commission routes, delegates to commission_service, no FastAPI imports`
- ❌ `finance/supplier_payout_controller.py -> orchestrates payout routes, delegates to supplier_payout_service, no FastAPI imports`
- ❌ `finance/bank_reconciliation_controller.py -> orchestrates bank rec routes, delegates to bank_reconciliation_service, no FastAPI imports`
- ❌ `finance/ap_ar_controller.py -> orchestrates AR/AP routes, delegates to ap_service/ar_service, no FastAPI imports`
- ❌ `orders/orders_controller.py -> orchestrates customer order routes, delegates to orders_service, no FastAPI imports`
- ❌ `orders/logistics_controller.py -> orchestrates logistics/shipment routes, delegates to logistics_service, no FastAPI imports`
- ❌ `payments/payment_engine.py -> central payment router (smart routing, tier-based fallback, ZoziPaymentEvent dispatch to Treasury, health monitoring)`
- ❌ `payments/payment_gateway_registry.py -> auto-discovery engine for payment gateway adapters (pkgutil scan)`
- ❌ `payments/payment_webhook_service.py -> webhook handler (ZoziPaymentEvent normalizer, idempotency gate via ProcessedWebhookEvent, signature verification)`
- ❌ `payments/payment_vault_service.py -> AES-256-GCM credential vault (encrypt_secret, decrypt_secret, key rotation)`
- ❌ `finance/treasury_service.py -> owns DB writes for treasury (cash position, snapshots, forecasts, settlements, COD remittance, reserve transfers)`
- ❌ `finance/general_ledger_service.py -> owns DB writes for GL (post_journal_entry with Dr==Cr abort, SELECT FOR UPDATE on account_balances, trial balance, financial statements)`
- ❌ `finance/supplier_payout_service.py -> owns DB writes for supplier payouts (batch generator from commission_ledger_entries + payout_rules, Maker-Checker dispatch, supplier pre-review links)`
- ❌ `finance/bank_reconciliation_service.py -> owns DB writes for bank rec (import statements, auto-match, exception routing, bulk reconcile)`
- ❌ `finance/exception_queue_service.py -> owns DB reads/writes for exception queue (prioritization, split-screen review data, approve/edit/reject actions, audit trail)`
- ❌ `finance/ap_service.py -> owns DB writes for AP (bills, payments, aging, 3-way match PO↔GRN↔Invoice, landed-cost allocation)`
- ❌ `finance/ar_service.py -> owns DB writes for AR (invoices, receipts, aging, dunning cadence, credit limits, IFRS-15 deferred amortization)`
- ❌ `orders/orders_service.py -> owns DB writes for orders (create, preview, get, cancel), fee-aware payment method totals, delivery charge lookup`
- ❌ `logistics/logistics_service.py -> owns DB writes for logistics (delivery settings management, COD remittance, settlement calculation)`
- ❌ `middleware/rls_middleware.py -> RLS enforcement on all payment/finance tables keyed on `country_code`; cross-country reads return zero rows without global/admin role`
- ❌ `middleware/pci_dss_compliance_middleware.py -> PCI-DSS compliance middleware (payment data handling, credential vault integration)`
- ❌ `middleware/finance_permission_middleware.py -> Finance permission enforcement (finance.ap.post, finance.ledger.approve, finance.reconciliation, etc.)`
- ❌ `jobs/payout_batch_worker.py -> background worker for nightly payout batch generator (cron 02:00, commission_ledger_entries + payout_rules -> payout_batches draft)`
- ❌ `jobs/supplier_payout_dispatch_worker.py -> background worker for supplier payout dispatch (Maker-Checker, supplier pre-review SMS/email links)`
- ❌ `jobs/bank_reconciliation_worker.py -> background worker for daily bank statement import + auto-match (CSV/API)`
- ❌ `jobs/accrual_reversal_worker.py -> background worker for auto-accrual & reversal (month-end 23:59 / day-1 cron)`
- ❌ `jobs/depreciation_worker.py -> background worker for monthly depreciation run (straight-line/declining, disposal gain/loss)`
- ❌ `jobs/fx_revaluation_worker.py -> background worker for month-end FX revaluation (timestamped exchange_rates, draft JEs)`
- ❌ `jobs/vat_remittance_worker.py -> background worker for continuous VAT aggregation + month-end ZATCA/FTA CSV export wizard`
- ❌ `jobs/orphan_detector_worker.py -> background worker for daily 03:00 orphan detector (delivered/paid orders without journal entries -> Critical alert)`
- ❌ `jobs/ocr_expense_worker.py -> background worker for OCR expense/asset capture (camera/upload/email -> scanned_expenses staging, pgvector embed)`
- ❌ `jobs/email_to_ledger_worker.py -> background worker for IMAP watcher on finance@zozi.com (PDFs/CSVs -> scanned_expenses/gateway_settlement_schedules)`
- ❌ `jobs/dunning_worker.py -> background worker for auto dunning cadence (emails day 3/7/14, late-fee per config)`
- ❌ `jobs/report_scheduler_worker.py -> background worker for scheduled report delivery (daily/weekly/monthly email/CSV/PDF)`
- ❌ `jobs/data_retention_worker.py -> background worker for data retention (audit logs archive to S3 after 2yr, outbox hard delete 7d after processed)`
- ❌ `events/event_publisher.py -> Redis pub/sub event publisher (reuse existing, extend for finance events: OrderDelivered, RefundApproved, PaymentCaptured, PayoutDispatched)`
- ❌ `events/finance_events.py -> domain event schemas for finance (OrderDelivered, RefundApproved, PaymentCaptured, PayoutDispatched, JournalEntryPosted, BankReconciled, etc.)`
- ❌ `events/payment_events.py -> domain event schemas for payment events (ZoziPaymentEvent, PAYMENT_CAPTURED, REFUND_SUCCEEDED, CHARGEBACK_OPENED)`
- ❌ `providers/payments/stripe_provider.py -> Stripe adapter (5 mandatory methods + normalize_webpack -> ZoziPaymentEvent, health_check, idempotency)`
- ❌ `providers/payments/tap_provider.py -> Tap adapter (5 mandatory methods + normalize_webhook -> ZoziPaymentEvent, health_check, idempotency)`
- ❌ `providers/payments/thawani_provider.py -> Thawani adapter (5 mandatory methods + normalize_webhook -> ZoziPaymentEvent, health_check, idempotency)`
- ❌ `providers/payments/paytabs_provider.py -> PayTabs adapter (5 mandatory methods + normalize_webhook -> ZoziPaymentEvent, health_check, idempotency)`
- ❌ `providers/payments/mada_provider.py -> Mada adapter (5 mandatory methods + normalize_webhook -> ZoziPaymentEvent, health_check, idempotency)`
- ❌ `providers/payments/stc_pay_provider.py -> STC Pay adapter (5 mandatory methods + normalize_webhook -> ZoziPaymentEvent, health_check, idempotency)`
- ❌ `providers/payments/generic_rest_adapter.py -> Generic REST Adapter (no-code gateway setup via DB-stored templates for Charge URL, Auth Headers, JSON Payload Template)`
- ❌ `providers/ai/ocr_provider.py -> OCR provider (receipt/bill/invoice parsing, per-field confidence, pgvector embed, duplicate hash)`
- ❌ `providers/media/media_storage_provider.py -> R2/S3 media storage adapter (scanned receipts, invoices, asset photos, presigned URLs)`

### Database Files

**Present (9):**

- ✅ `base.py`
- ✅ `database.py`
- ✅ `session.py`
- ✅ `transaction.py`
- ✅ `schemas.py`
- ✅ `models.py`
- ✅ `create_tables.py`
- ✅ `init_db.py`
- ✅ `database_logging.py`

**Missing (4):**

- ❌ `security/`
- ❌ `setup/`
- ❌ `seeds/`
- ❌ `alembic/`

### Model Files

**Missing (14):**

- ❌ `finance/treasury_models.py -> SQLAlchemy ORM models: TreasuryAccount, TreasuryTransaction, CashPositionSnapshot, GatewaySettlementSchedule, CashFlowForecast, ExchangeRate`
- ❌ `finance/ledger_models.py -> SQLAlchemy ORM models: JournalEntry, JournalEntryLine, PendingJournalEntry, FiscalPeriod, AccountGroup, Account, AccountBalance`
- ❌ `finance/commission_models.py -> SQLAlchemy ORM models: CommissionLedgerEntry, CommissionRule, BadgeTier, CategoryCommissionRate`
- ❌ `finance/payout_models.py -> SQLAlchemy ORM models: PayoutRule, PayoutBatch, PayoutBatchItem, Payout`
- ❌ `finance/bank_models.py -> SQLAlchemy ORM models: BankStatementImport, BankStatementLine, BankMappingRule`
- ❌ `finance/ar_ap_models.py -> SQLAlchemy ORM models: ArInvoice, ArLedgerEntry, ApBill, ApLedgerEntry, DunningSchedule`
- ❌ `payments.py -> SQLAlchemy ORM models: PaymentGatewayConnection, ProcessedWebhookEvent, PaymentIntent, PaymentTransaction, Coupon, CouponUsage`
- ❌ `logistics/logistics_entities.py -> SQLAlchemy ORM models: Shipment, ShipmentEvent, LogisticsPartner, LogisticsPartnerProfile, LogisticsPartnerServiceArea, LogisticsPricingProfile, LogisticsVehicleRule, LogisticsCategoryPricingRule`
- ❌ `orders/order_entities.py -> SQLAlchemy ORM models: Order, OrderItem, OrderLogisticsAllocation, ReturnRequest, OrderNotification`
- ❌ `finance.py -> SQLAlchemy ORM models: RefundLedger`
- ❌ `promotions.py -> SQLAlchemy ORM models: Promotion, PromotionApplication, PromotionEngineConfig, PromotionOrderTier, UserPoints, PointsTransaction`
- ❌ `configuration/ -> SQLAlchemy ORM models: AutomationRule, OrderStatusRule, ReturnPolicy, CountryConfig, TaxRule, CommissionRule, PayoutRule`
- ❌ `mixins.py -> AuditMixin, SoftDeleteMixin, VersionMixin`
- ❌ `media/ -> SQLAlchemy ORM models: MediaAsset (metadata only, bytes in R2/S3)`

### Frontend Web

**Present (7):**

- ✅ `web_app/admin/finance/page.tsx`
- ✅ `web_app/supplier/payouts/page.tsx`
- ✅ `web_app/logistics-partner/payouts/page.tsx`
- ✅ `money.ts`
- ✅ `orderHelpers.ts`
- ✅ `returnsApi.ts`
- ✅ `i18n.ts`

**Missing (41):**

- ❌ `web_app/admin/finance/dashboard/page.tsx`
- ❌ `web_app/admin/finance/treasury/page.tsx`
- ❌ `web_app/admin/finance/ledger/page.tsx`
- ❌ `web_app/admin/finance/settlements/page.tsx`
- ❌ `web_app/admin/finance/receivables/page.tsx`
- ❌ `web_app/admin/finance/payables/page.tsx`
- ❌ `web_app/admin/finance/reconciliation/page.tsx`
- ❌ `web_app/admin/finance/payouts/page.tsx`
- ❌ `web_app/admin/finance/automation/page.tsx`
- ❌ `web_app/admin/payment-gateways/page.tsx`
- ❌ `web_app/admin/commissions/page.tsx`
- ❌ `web_app/admin/countries/:code/finance/page.tsx`
- ❌ `web_app/logistics-partner/remittance/page.tsx`
- ❌ `finance/CommandCenter.tsx`
- ❌ `finance/Dashboard.tsx`
- ❌ `finance/ExceptionQueue.tsx`
- ❌ `finance/ReconciliationView.tsx`
- ❌ `finance/PayoutControlRoom.tsx`
- ❌ `finance/AutomationControlTower.tsx`
- ❌ `finance/ReportBuilder.tsx`
- ❌ `finance/OCRDropzone.tsx`
- ❌ `finance/ChatbotDrawer.tsx`
- ❌ `finance/VoiceChip.tsx`
- ❌ `finance/CommissionPage.tsx`
- ❌ `finance/PromotionBuilder.tsx`
- ❌ `finance/CouponsPanel.tsx`
- ❌ `hooks/useFinanceDashboard.ts`
- ❌ `hooks/useExceptionQueue.ts`
- ❌ `hooks/useAutomationControlTower.ts`
- ❌ `hooks/useBankReconciliation.ts`
- ❌ `hooks/usePayouts.ts`
- ❌ `hooks/usePromotions.ts`
- ❌ `hooks/useCoupons.ts`
- ❌ `lib/finance/financeApi.ts`
- ❌ `lib/finance/reconciliationApi.ts`
- ❌ `lib/finance/payoutApi.ts`
- ❌ `lib/promotions/promotionsApi.ts`
- ❌ `lib/discounts/couponsApi.ts`
- ❌ `lib/order/orders.ts`
- ❌ `styles/finance.css`
- ❌ `promotionsApi.ts`

### Frontend Mobile

**Present (3):**

- ✅ `lib/api.ts`
- ✅ `lib/paymentService.ts`
- ✅ `lib/authStore.ts`

**Missing (16):**

- ❌ `mobile_app/admin/finance/page.tsx`
- ❌ `admin/finance/dashboard.tsx`
- ❌ `admin/finance/reconciliation.tsx`
- ❌ `admin/finance/payouts.tsx`
- ❌ `admin/finance/automation.tsx`
- ❌ `mobile_app/admin/payment-gateways/page.tsx`
- ❌ `mobile_app/admin/commissions/page.tsx`
- ❌ `mobile_app/supplier/payouts/page.tsx`
- ❌ `mobile_app/supplier/invoices/page.tsx`
- ❌ `mobile_app/logistics-partner/payouts/page.tsx`
- ❌ `mobile_app/logistics-partner/remittance/page.tsx`
- ❌ `components/finance/ExceptionQueue.tsx`
- ❌ `components/finance/VoiceChip.tsx`
- ❌ `components/finance/OCRDropzone.tsx`
- ❌ `components/finance/CommissionPreview.tsx`
- ❌ `theme/`

### Tests

**Missing (32):**

- ❌ `tests/backend/_test_payment_collection_cod.py`
- ❌ `tests/backend/_test_payment_collection_card.py`
- ❌ `tests/backend/_test_logistics_delivery_settings.py`
- ❌ `tests/backend/_test_supplier_payout_automation.py`
- ❌ `tests/backend/_test_logistics_payout_settlement.py`
- ❌ `tests/backend/_test_commission_engine.py`
- ❌ `tests/backend/_test_payment_gateway_wizard.py`
- ❌ `tests/backend/_test_bank_reconciliation.py`
- ❌ `tests/backend/_test_cod_reconciliation.py`
- ❌ `tests/backend/_test_refund_reconciliation.py`
- ❌ `tests/backend/_test_payout_reconciliation.py`
- ❌ `tests/backend/_test_payment_webhook_normalizer.py`
- ❌ `tests/backend/_test_payment_vault.py`
- ❌ `tests/backend/_test_payment_routing_fallback.py`
- ❌ `tests/backend/_test_finance_double_entry.py`
- ❌ `tests/backend/_test_finance_penny_rounding.py`
- ❌ `tests/backend/_test_finance_supplier_payout.py`
- ❌ `tests/backend/_test_finance_rls_country_isolation.py`
- ❌ `tests/frontend/web_app/_test_payment_system.test.tsx`
- ❌ `tests/frontend/web_app/_test_finance_command_center.test.tsx`
- ❌ `tests/frontend/web_app/_test_finance_dashboard.test.tsx`
- ❌ `tests/frontend/web_app/_test_finance_reconciliation.test.tsx`
- ❌ `tests/frontend/web_app/_test_finance_payout_control_room.test.tsx`
- ❌ `tests/frontend/web_app/_test_finance_payment_gateways.test.tsx`
- ❌ `tests/frontend/web_app/_test_finance_commissions.test.tsx`
- ❌ `tests/frontend/mobile_app/_test_finance_mobile.test.tsx`
- ❌ `tests/frontend/mobile_app/_test_finance_supplier_payouts_mobile.test.tsx`
- ❌ `tests/frontend/mobile_app/_test_finance_logistics_remittance_mobile.test.tsx`
- ❌ `tests/playwright/_test_payment_flow_e2e.spec.ts`
- ❌ `tests/playwright/_test_finance_e2e.spec.ts`
- ❌ `tests/playwright/_test_finance_command_center_e2e.spec.ts`
- ❌ `tests/playwright/_test_finance_reconciliation_e2e.spec.ts`

### API Routes

**Missing (69):**

- ❌ `POST /api/v1/payments/create`
- ❌ `POST /api/v1/payments/confirm`
- ❌ `POST /api/v1/payments/webhook/{provider_code}`
- ❌ `POST /api/v1/payments/refund`
- ❌ `GET /api/v1/payments/methods`
- ❌ `GET /api/v1/payments/transactions`
- ❌ `POST /api/v1/admin/payment-gateways`
- ❌ `GET /api/v1/admin/payment-gateways`
- ❌ `PUT /api/v1/admin/payment-gateways/{gateway_id}`
- ❌ `POST /api/v1/admin/payment-gateways/{gateway_id}/test-connection`
- ❌ `GET /api/v1/admin/payment-gateways/health`
- ❌ `POST /api/v1/admin/payment-gateways/routing-rules`
- ❌ `GET /api/v1/finance/dashboard`
- ❌ `GET /api/v1/finance/treasury/cash-position`
- ❌ `GET /api/v1/finance/treasury/snapshots`
- ❌ `GET /api/v1/finance/treasury/forecasts`
- ❌ `GET /api/v1/finance/treasury/gateway-settlements`
- ❌ `POST /api/v1/finance/treasury/reserve-transfer`
- ❌ `POST /api/v1/finance/treasury/cod-reconciliation/settle`
- ❌ `GET /api/v1/finance/ledger/journal-entries`
- ❌ `GET /api/v1/finance/ledger/journal-entries/{entry_id}`
- ❌ `GET /api/v1/finance/ledger/trial-balance`
- ❌ `GET /api/v1/finance/ledger/balance-sheet`
- ❌ `GET /api/v1/finance/ledger/income-statement`
- ❌ `GET /api/v1/finance/ledger/cash-flow`
- ❌ `POST /api/v1/finance/ledger/pending-journal-entries`
- ❌ `POST /api/v1/finance/ledger/pending-journal-entries/{entry_id}/approve`
- ❌ `POST /api/v1/finance/ledger/pending-journal-entries/{entry_id}/reject`
- ❌ `GET /api/v1/finance/commissions/ledger`
- ❌ `GET /api/v1/finance/commissions/rules`
- ❌ `PUT /api/v1/finance/commissions/rules/{rule_id}`
- ❌ `POST /api/v1/finance/commissions/preview`
- ❌ `GET /api/v1/finance/commissions/badge-tiers`
- ❌ `PUT /api/v1/finance/commissions/badge-tiers/{tier_id}`
- ❌ `GET /api/v1/finance/payouts/batches`
- ❌ `POST /api/v1/finance/payouts/batches/{batch_id}/approve`
- ❌ `POST /api/v1/finance/payouts/batches/{batch_id}/dispatch`
- ❌ `GET /api/v1/finance/payouts/supplier/{supplier_id}`
- ❌ `GET /api/v1/finance/payouts/logistics/{partner_id}`
- ❌ `POST /api/v1/finance/bank-reconciliation/import`
- ❌ `POST /api/v1/finance/bank-reconciliation/auto-match`
- ❌ `POST /api/v1/finance/bank-reconciliation/reconcile`
- ❌ `GET /api/v1/finance/bank-reconciliation/exceptions`
- ❌ `GET /api/v1/finance/ar/invoices`
- ❌ `POST /api/v1/finance/ar/invoices`
- ❌ `GET /api/v1/finance/ar/aging`
- ❌ `POST /api/v1/finance/ar/dunning`
- ❌ `GET /api/v1/finance/ap/bills`
- ❌ `POST /api/v1/finance/ap/bills`
- ❌ `POST /api/v1/finance/ap/3way-match`
- ❌ `GET /api/v1/logistics/delivery-settings`
- ❌ `POST /api/v1/logistics/delivery-settings`
- ❌ `PUT /api/v1/logistics/delivery-settings/{setting_id}`
- ❌ `GET /api/v1/logistics/delivery-settings/approval`
- ❌ `POST /api/v1/logistics/delivery-settings/{setting_id}/approve`
- ❌ `POST /api/v1/logistics/cod-remittance`
- ❌ `GET /api/v1/logistics/cod-reconciliation`
- ❌ `POST /api/v1/logistics/cod-reconciliation/settle`
- ❌ `GET /api/v1/supplier/bank-accounts`
- ❌ `POST /api/v1/supplier/bank-accounts`
- ❌ `PUT /api/v1/supplier/bank-accounts/{account_id}`
- ❌ `GET /api/v1/logistics/bank-accounts`
- ❌ `POST /api/v1/logistics/bank-accounts`
- ❌ `PUT /api/v1/logistics/bank-accounts/{account_id}`
- ❌ `GET /api/v1/admin/bank-accounts`
- ❌ `POST /api/v1/admin/bank-accounts`
- ❌ `PUT /api/v1/admin/bank-accounts/{account_id}`
- ❌ `GET /api/v1/admin/bank-verification`
- ❌ `POST /api/v1/admin/bank-verification/{entity_id}`

### DB Model Classes

**Present (40):**

- ✅ `PaymentGatewayConnection`
- ✅ `ProcessedWebhookEvent`
- ✅ `TreasuryAccount`
- ✅ `TreasuryTransaction`
- ✅ `CashPositionSnapshot`
- ✅ `GatewaySettlementSchedule`
- ✅ `CashFlowForecast`
- ✅ `JournalEntry`
- ✅ `JournalEntryLine`
- ✅ `PendingJournalEntry`
- ✅ `FiscalPeriod`
- ✅ `AccountGroup`
- ✅ `Account`
- ✅ `AccountBalance`
- ✅ `CommissionLedgerEntry`
- ✅ `BadgeTier`
- ✅ `PayoutRule`
- ✅ `PayoutBatch`
- ✅ `PayoutBatchItem`
- ✅ `Payout`
- ✅ `BankStatementImport`
- ✅ `BankStatementLine`
- ✅ `BankMappingRule`
- ✅ `LogisticsPartner`
- ✅ `LogisticsPartnerProfile`
- ✅ `LogisticsPartnerServiceArea`
- ✅ `LogisticsPricingProfile`
- ✅ `LogisticsVehicleRule`
- ✅ `LogisticsCategoryPricingRule`
- ✅ `Order`
- ✅ `OrderItem`
- ✅ `OrderLogisticsAllocation`
- ✅ `OrderNotification`
- ✅ `ReturnRequest`
- ✅ `RefundLedger`
- ✅ `Coupon`
- ✅ `CouponUsage`
- ✅ `CountryConfig`
- ✅ `AutomationRule`
- ✅ `MediaAsset`

**Missing (11):**

- ❌ `PaymentIntent`
- ❌ `PaymentTransaction`
- ❌ `ExchangeRate`
- ❌ `CommissionRule`
- ❌ `CategoryCommissionRate`
- ❌ `ArInvoice`
- ❌ `ArLedgerEntry`
- ❌ `ApBill`
- ❌ `ApLedgerEntry`
- ❌ `DunningSchedule`
- ❌ `EventDeadLetter`

---

## SYS_008 — Promotion Engine & Loyalty System

### Backend Files

**Missing (15):**

- ❌ `promotions.py → thin router for promotion endpoints (apply, active list, admin CRUD, preview)`
- ❌ `coupons.py → thin router for coupon endpoints (validate, CRUD, archive, restore, bulk-archive, bulk-restore)`
- ❌ `admin/promotions.py → thin router for admin promotion endpoints (country-scoped coupons, campaigns, tier editor, preview calculator)`
- ❌ `promotion_controller.py → orchestrates promotion routes, delegates to promotion_engine, no FastAPI imports`
- ❌ `coupons_controller.py → orchestrates coupon routes, delegates to coupon_service, no FastAPI imports`
- ❌ `promotions/promotion_engine.py → rules-based promotion engine (evaluate cart/order, stacking/best-only, precedence order, fraud detection)`
- ❌ `promotions/promotion_evaluator.py → promotion evaluator (fetch active promotions, evaluate rules, calculate discount, record in ledger)`
- ❌ `promotions/promotion_ledger_service.py → immutable promotion ledger service (one row per application, supplier contribution tracking, fraud flags)`
- ❌ `promotions/referral_service.py → referral service (code generation, referee validation, points awarding, fraud checks, delay for refunds)`
- ❌ `promotions/points_service.py → points service (balance tracking, redemption, expiry, monthly cap)`
- ❌ `discounts/coupon_service.py → coupon service (validation, usage tracking, stacking, country-scoping, soft-delete/archive)`
- ❌ `middleware/rls_middleware.py → RLS enforcement on all promotion tables keyed on `country_code`; cross-country reads return zero rows without global/admin role`
- ❌ `jobs/promotion_ledger_worker.py → background worker for async promotion ledger writes and fraud checks (Celery/Redis queue)`
- ❌ `events/promotion_events.py → domain event schemas for promotion lifecycle (PROMOTION_APPLIED, REFERRAL_AWARDED, POINTS_REDEEMED, FRAUD_FLAGGED)`
- ❌ `providers/ai/fraud_detection_provider.py → ML-based fraud detection adapter (subclass BaseAIProvider, anomaly detection for referral networks, velocity monitoring)`

### Database Files

**Present (9):**

- ✅ `base.py`
- ✅ `database.py`
- ✅ `session.py`
- ✅ `transaction.py`
- ✅ `schemas.py`
- ✅ `models.py`
- ✅ `create_tables.py`
- ✅ `init_db.py`
- ✅ `database_logging.py`

**Missing (4):**

- ❌ `security/`
- ❌ `setup/`
- ❌ `seeds/`
- ❌ `alembic/`

### Model Files

**Missing (1):**

- ❌ `mixins.py → AuditMixin, SoftDeleteMixin, VersionMixin`

### Frontend Web

**Present (2):**

- ✅ `web_app/admin/promotions/page.tsx`
- ✅ `money.ts`

**Missing (12):**

- ❌ `admin/promotions/CouponsPanel.tsx`
- ❌ `finance/PromotionBuilder.tsx`
- ❌ `finance/CouponsPanel.tsx`
- ❌ `web_app/customer/referral/page.tsx`
- ❌ `web_app/customer/loyalty/page.tsx`
- ❌ `web_app/supplier/promotions/page.tsx`
- ❌ `hooks/usePromotions.ts`
- ❌ `hooks/useCoupons.ts`
- ❌ `lib/promotions/promotionsApi.ts`
- ❌ `lib/discounts/couponsApi.ts`
- ❌ `promotionsApi.ts`
- ❌ `styles/finance.css`

### Frontend Mobile

**Present (1):**

- ✅ `lib/api.ts`

**Missing (6):**

- ❌ `mobile_app/admin/promotions/page.tsx`
- ❌ `admin/promotions/CouponsPanel.tsx`
- ❌ `mobile_app/customer/referral/page.tsx`
- ❌ `mobile_app/customer/loyalty/page.tsx`
- ❌ `mobile_app/supplier/promotions/page.tsx`
- ❌ `theme/`

### Tests

**Missing (18):**

- ❌ `tests/backend/_test_promotion_engine.py`
- ❌ `tests/backend/_test_promotion_evaluator.py`
- ❌ `tests/backend/_test_promotion_ledger.py`
- ❌ `tests/backend/_test_referral_points.py`
- ❌ `tests/backend/_test_loyalty_program.py`
- ❌ `tests/backend/_test_coupon_validation.py`
- ❌ `tests/backend/_test_coupon_stacking.py`
- ❌ `tests/backend/_test_bogo_engine.py`
- ❌ `tests/backend/_test_flash_sale_engine.py`
- ❌ `tests/backend/_test_promotion_fraud_detection.py`
- ❌ `tests/backend/_test_promotion_rls_country_isolation.py`
- ❌ `tests/frontend/web_app/_test_promotion_builder.test.tsx`
- ❌ `tests/frontend/web_app/_test_coupons_panel.test.tsx`
- ❌ `tests/frontend/web_app/_test_customer_referral.test.tsx`
- ❌ `tests/frontend/web_app/_test_customer_loyalty.test.tsx`
- ❌ `tests/frontend/mobile_app/_test_promotions_mobile.test.tsx`
- ❌ `tests/frontend/mobile_app/_test_referral_mobile.test.tsx`
- ❌ `tests/playwright/_test_promotion_e2e.spec.ts`

### API Routes

**Missing (27):**

- ❌ `POST /api/v1/promotions/apply`
- ❌ `GET /api/v1/promotions/active`
- ❌ `POST /api/v1/admin/promotions`
- ❌ `GET /api/v1/admin/promotions/config`
- ❌ `PUT /api/v1/admin/promotions/config`
- ❌ `GET /api/v1/admin/promotions/tiers`
- ❌ `POST /api/v1/admin/promotions/tiers`
- ❌ `PUT /api/v1/admin/promotions/tiers/{tier_id}`
- ❌ `DELETE /api/v1/admin/promotions/tiers/{tier_id}`
- ❌ `POST /api/v1/admin/promotions/preview`
- ❌ `POST /api/v1/promotions/points/redeem`
- ❌ `GET /api/v1/promotions/points/balance`
- ❌ `GET /api/v1/promotions/referral/code`
- ❌ `POST /api/v1/promotions/referral/validate`
- ❌ `POST /api/v1/promotions/scratch-card/reveal`
- ❌ `POST /api/v1/coupons/validate`
- ❌ `GET /api/v1/coupons`
- ❌ `POST /api/v1/coupons`
- ❌ `DELETE /api/v1/coupons/{coupon_id}`
- ❌ `POST /api/v1/coupons/bulk-archive`
- ❌ `POST /api/v1/coupons/bulk-restore`
- ❌ `GET /api/v1/admin/{code}/promotions/coupons`
- ❌ `POST /api/v1/admin/{code}/promotions/coupons`
- ❌ `POST /api/v1/coupons/{id}/archive`
- ❌ `POST /api/v1/coupons/{id}/restore`
- ❌ `GET /api/v1/admin/promotions/fraud-alerts`
- ❌ `GET /api/v1/admin/promotions/analytics`

### DB Model Classes

**Present (6):**

- ✅ `PromotionEngineConfig`
- ✅ `PromotionOrderTier`
- ✅ `UserPoints`
- ✅ `PointsTransaction`
- ✅ `Coupon`
- ✅ `CouponUsage`

**Missing (2):**

- ❌ `Promotion`
- ❌ `PromotionApplication`

---

## SYS_009 — Discount Management System (Coupons · Country-Scoped Discounts · Validation & Stacking · Soft-Delete/Archive)

### Backend Files

**Missing (9):**

- ❌ `coupons.py → thin router for coupon endpoints (public validate + admin global CRUD, archive, restore, bulk-archive, bulk-restore)`
- ❌ `admin/promotions.py → thin router for country-scoped promotion endpoints (/admin/{code}/promotions/coupons)`
- ❌ `coupons_controller.py → orchestrates coupon routes, delegates to coupon_service, no FastAPI imports`
- ❌ `promotion_controller.py → orchestrates promotion routes, delegates to promotion_engine + coupon_service, no FastAPI imports`
- ❌ `discounts/coupon_service.py → coupon service (validation, usage tracking, stacking, country-scoping, soft-delete/archive)`
- ❌ `promotions/promotion_engine.py → promotion engine (stacking/best-only logic, precedence order, fraud detection)`
- ❌ `promotions/promotion_evaluator.py → promotion evaluator (fetch active promotions, evaluate rules, calculate discount, record in ledger)`
- ❌ `middleware/rls_middleware.py → RLS enforcement on coupons and coupons_usage tables keyed on country_code; cross-country reads return zero rows without global/admin role`
- ❌ `events/promotion_events.py → domain event schemas for coupon lifecycle (COUPON_VALIDATED, COUPON_APPLIED, COUPON_ARCHIVED, COUPON_RESTORED)`

### Database Files

**Present (9):**

- ✅ `base.py`
- ✅ `database.py`
- ✅ `session.py`
- ✅ `transaction.py`
- ✅ `schemas.py`
- ✅ `models.py`
- ✅ `create_tables.py`
- ✅ `init_db.py`
- ✅ `database_logging.py`

**Missing (4):**

- ❌ `security/`
- ❌ `setup/`
- ❌ `seeds/`
- ❌ `alembic/`

### Model Files

**Missing (1):**

- ❌ `mixins.py → AuditMixin, SoftDeleteMixin, VersionMixin`

### Frontend Web

**Present (1):**

- ✅ `money.ts`

**Missing (4):**

- ❌ `admin/promotions/CouponsPanel.tsx`
- ❌ `finance/CouponsPanel.tsx`
- ❌ `hooks/useCoupons.ts`
- ❌ `lib/discounts/couponsApi.ts`

### Frontend Mobile

**Present (1):**

- ✅ `lib/api.ts`

**Missing (2):**

- ❌ `admin/promotions/CouponsPanel.tsx`
- ❌ `components/finance/CouponsPanel.tsx`

### Tests

**Missing (7):**

- ❌ `tests/backend/_test_coupon_validation.py`
- ❌ `tests/backend/_test_coupon_stacking.py`
- ❌ `tests/backend/_test_coupon_soft_delete.py`
- ❌ `tests/backend/_test_coupon_country_scoping.py`
- ❌ `tests/frontend/web_app/_test_coupons_panel.test.tsx`
- ❌ `tests/frontend/mobile_app/_test_coupons_mobile.test.tsx`
- ❌ `tests/playwright/_test_coupons_e2e.spec.ts`

### API Routes

**Missing (10):**

- ❌ `POST /api/v1/coupons/validate`
- ❌ `GET /api/v1/coupons`
- ❌ `POST /api/v1/coupons`
- ❌ `DELETE /api/v1/coupons/{coupon_id}`
- ❌ `POST /api/v1/coupons/bulk-archive`
- ❌ `POST /api/v1/coupons/bulk-restore`
- ❌ `POST /api/v1/coupons/{id}/archive`
- ❌ `POST /api/v1/coupons/{id}/restore`
- ❌ `GET /api/v1/admin/{code}/promotions/coupons`
- ❌ `POST /api/v1/admin/{code}/promotions/coupons`

### DB Model Classes

**Present (2):**

- ✅ `Coupon`
- ✅ `CouponUsage`

---

## SYS_010 — Banner Management System (Canvas · Country-Scoped · Background Effects · Promotion Integration)

### Backend Files

**Missing (6):**

- ❌ `banners.py -> thin router for banner endpoints (public list + admin global CRUD, image upload, delete)`
- ❌ `admin_promotions.py -> thin router for country-scoped promotion endpoints (/admin/{code}/promotions/banners)`
- ❌ `banner_controller.py -> orchestrates banner routes, delegates to banner_service, no FastAPI imports`
- ❌ `promotion_controller.py -> orchestrates promotion routes, delegates to banner_service + promotion_engine, no FastAPI imports`
- ❌ `promotions/banner_service.py -> banner service (CRUD, soft-delete, country-scoping, canvas validation, effect selection)`
- ❌ `events/promotion_events.py -> domain event schemas for banner lifecycle (BANNER_CREATED, BANNER_UPDATED, BANNER_DELETED)`

### Database Files

**Present (9):**

- ✅ `base.py`
- ✅ `database.py`
- ✅ `session.py`
- ✅ `transaction.py`
- ✅ `schemas.py`
- ✅ `models.py`
- ✅ `create_tables.py`
- ✅ `init_db.py`
- ✅ `database_logging.py`

**Missing (4):**

- ❌ `security/`
- ❌ `setup/`
- ❌ `seeds/`
- ❌ `alembic/`

### Model Files

**Missing (3):**

- ❌ `payments.py -> SQLAlchemy ORM model: Banner`
- ❌ `mixins.py -> AuditMixin, SoftDeleteMixin, VersionMixin`
- ❌ `configuration/ -> SQLAlchemy ORM models: CountryConfig`

### Frontend Web

**Present (7):**

- ✅ `BannerCanvasEditor.tsx`
- ✅ `BannerCarousel.tsx`
- ✅ `BackgroundEffect.tsx`
- ✅ `lib/effectStore.ts`
- ✅ `web_app/products/page.tsx`
- ✅ `HomeClient.tsx`
- ✅ `layout.tsx`

**Missing (2):**

- ❌ `BannerCanvasView.tsx`
- ❌ `admin/dashboard/tabs/BannerTab.tsx`

### Frontend Mobile

**Present (1):**

- ✅ `lib/api.ts`

**Missing (2):**

- ❌ `admin/promotions/BannersPanel.tsx`
- ❌ `components/promotion/BannersPanel.tsx`

### Tests

**Missing (8):**

- ❌ `tests/backend/_test_banner_service.py`
- ❌ `tests/backend/_test_banner_country_scoping.py`
- ❌ `tests/backend/_test_banner_canvas_persistence.py`
- ❌ `tests/backend/_test_banner_effects.py`
- ❌ `tests/frontend/web_app/_test_banner_canvas_editor.test.tsx`
- ❌ `tests/frontend/web_app/_test_banner_carousel.test.tsx`
- ❌ `tests/frontend/mobile_app/_test_banners_mobile.test.tsx`
- ❌ `tests/playwright/_test_banner_e2e.spec.ts`

### API Routes

**Missing (8):**

- ❌ `GET /api/v1/banners`
- ❌ `POST /api/v1/admin/banners`
- ❌ `PUT /api/v1/admin/banners/{id}`
- ❌ `DELETE /api/v1/admin/banners/{id}`
- ❌ `POST /api/v1/banners/{id}/image`
- ❌ `GET /api/v1/admin/banners`
- ❌ `GET /api/v1/admin/{code}/promotions/banners`
- ❌ `POST /api/v1/admin/{code}/promotions/banners`

### DB Model Classes

**Present (1):**

- ✅ `Banner`

---

## SYS_011 — Email System (Transactional · Newsletter · Campaigns · Runtime Provider)

### Backend Files

**Missing (9):**

- ❌ `email.py -> thin router for email endpoints (config/runtime, webhooks/resend, newsletter, template CRUD, campaign CRUD, analytics, open/click tracking)`
- ❌ `auth.py -> thin router for auth email trigger endpoints (verify-email, resend-verification, forgot-password, reset-password)`
- ❌ `email_controller.py -> orchestrates email routes, delegates to email_event_service and transactional_email_service, no FastAPI imports`
- ❌ `auth_controller.py -> orchestrates auth email flows (verification, password reset), delegates to email_service, no FastAPI imports`
- ❌ `comms/email_event_service.py -> owns DB writes for email delivery events, suppressions, webhook processing, runtime config cache management`
- ❌ `comms/transactional_email_service.py -> owns DB writes for milestone transactional emails (order/payment/refund/return/shipment), sender resolution, DLP scanning`
- ❌ `utils/email_service.py -> delivery helpers (send_email, verification, password reset, newsletter welcome, campaign send, runtime config cache refresh/invalidation, sender purpose mapping)`
- ❌ `utils/background_jobs.py -> background job registry used by campaign send queue`
- ❌ `middleware/websocket_manager.py -> WebSocket manager for real-time email notifications (reuse existing, extend for comms)`

### Database Files

**Present (9):**

- ✅ `base.py`
- ✅ `database.py`
- ✅ `session.py`
- ✅ `transaction.py`
- ✅ `schemas.py`
- ✅ `models.py`
- ✅ `create_tables.py`
- ✅ `init_db.py`
- ✅ `database_logging.py`

**Missing (4):**

- ❌ `security/`
- ❌ `setup/`
- ❌ `seeds/`
- ❌ `alembic/`

### Model Files

**Missing (2):**

- ❌ `comms/communication.py -> SQLAlchemy ORM models: EmailVerificationToken, PasswordResetToken, NewsletterSubscriber, EmailTemplate, EmailCampaign, CampaignRecipient, EmailProviderConfig, EmailSuppression, EmailDeliveryEvent`
- ❌ `mixins.py -> AuditMixin, SoftDeleteMixin, VersionMixin`

### Frontend Web

**Present (11):**

- ✅ `web_app/admin/email/page.tsx`
- ✅ `admin/EmailProviderConfigManager.tsx`
- ✅ `admin/EmailCampaignManager.tsx`
- ✅ `admin/EmailTemplateManager.tsx`
- ✅ `admin/CreateCampaignForm.tsx`
- ✅ `web_app/verify-email/page.tsx`
- ✅ `web_app/reset-password/page.tsx`
- ✅ `web_app/newsletter/preferences/page.tsx`
- ✅ `web_app/newsletter/unsubscribe/page.tsx`
- ✅ `NewsletterSignup.tsx`
- ✅ `layout.tsx`

**Missing (2):**

- ❌ `web_app/forgot-password/page.tsx`
- ❌ `web_app/newsletter/page.tsx`

### Frontend Mobile

**Present (7):**

- ✅ `admin/email.tsx`
- ✅ `(auth)/verify-email.tsx`
- ✅ `(auth)/forgot-password.tsx`
- ✅ `(auth)/reset-password.tsx`
- ✅ `edit-profile.tsx`
- ✅ `change-password.tsx`
- ✅ `components/NewsletterSignup.tsx`

### Tests

**Missing (9):**

- ❌ `tests/backend/_test_email_runtime_config.py`
- ❌ `tests/backend/_test_email_webhooks_and_transactional_flows.py`
- ❌ `tests/backend/_test_email_campaigns.py`
- ❌ `tests/backend/_test_email_ab.py`
- ❌ `tests/backend/_test_auth_email_flows.py`
- ❌ `tests/frontend/web_app/_test_admin_email_dashboard.test.tsx`
- ❌ `tests/frontend/web_app/_test_newsletter_flows.test.tsx`
- ❌ `tests/frontend/mobile_app/_test_email_mobile.test.tsx`
- ❌ `tests/playwright/_test_email_e2e.spec.ts`

### API Routes

**Missing (27):**

- ❌ `GET /email/config/runtime`
- ❌ `PUT /email/config/runtime`
- ❌ `POST /email/config/test-send`
- ❌ `POST /email/webhooks/resend`
- ❌ `POST /email/newsletter/subscribe`
- ❌ `POST /email/newsletter/unsubscribe`
- ❌ `GET /email/newsletter/preferences`
- ❌ `PUT /email/newsletter/preferences`
- ❌ `GET /email/templates`
- ❌ `POST /email/templates`
- ❌ `PUT /email/templates/{id}`
- ❌ `DELETE /email/templates/{id}`
- ❌ `GET /email/campaigns`
- ❌ `POST /email/campaigns`
- ❌ `PUT /email/campaigns/{id}`
- ❌ `DELETE /email/campaigns/{id}`
- ❌ `POST /email/campaigns/{id}/send`
- ❌ `GET /email/campaigns/{id}/analytics`
- ❌ `POST /email/track-open`
- ❌ `POST /email/track-click`
- ❌ `GET /email/history/{user_id}`
- ❌ `POST /email/bulk`
- ❌ `POST /email/from-alias`
- ❌ `POST /auth/verify-email`
- ❌ `POST /auth/resend-verification`
- ❌ `POST /auth/forgot-password`
- ❌ `POST /auth/reset-password`

### DB Model Classes

**Present (9):**

- ✅ `EmailVerificationToken`
- ✅ `PasswordResetToken`
- ✅ `NewsletterSubscriber`
- ✅ `EmailTemplate`
- ✅ `EmailCampaign`
- ✅ `CampaignRecipient`
- ✅ `EmailProviderConfig`
- ✅ `EmailSuppression`
- ✅ `EmailDeliveryEvent`

---

## SYS_012 — Advanced Smart Search · Filter · Sort Bar — Implementation

### Backend Files

**Missing (9):**

- ❌ `search.py -> thin router for search endpoints (`/search/filtered`, `/search/by-image`, `/search/voice`, `/search/advanced`, `/search/fuzzy`, `/search/predict`, `/search/trending`)`
- ❌ `search_controller.py -> orchestrates search routes, delegates to advanced_filter_service + ai_search_service + providers, no FastAPI imports`
- ❌ `advanced_filter_service.py -> owns DB writes for filter application, facet counts, cursor pagination, sort logic, JSONB filter_attributes WHERE clauses`
- ❌ `ai_search_service.py -> owns DB reads for hybrid retrieval, RRF fusion, NLP parsing, autocomplete, trending, did-you-mean, mode reporting`
- ❌ `providers/embedding_provider.py -> text-to-vector adapter (subclass BaseAIProvider, CPU-friendly quantized, lazy-load, cache in memory)`
- ❌ `providers/clip_provider.py -> image+text-to-vector adapter (subclass BaseAIProvider, CPU-friendly quantized, lazy-load, cache in memory)`
- ❌ `providers/whisper_provider.py -> audio-to-text adapter (subclass BaseAIProvider, CPU-friendly quantized, lazy-load, cache in memory)`
- ❌ `jobs/search_enrichment_worker.py -> background worker for batch embeddings, search analytics flush, facet MV refresh`
- ❌ `events/search_events.py -> domain event schemas for search lifecycle (SEARCH_QUERY, SEARCH_CLICK, ZERO_RESULT, IMAGE_SEARCH, VOICE_SEARCH)`

### Database Files

**Present (9):**

- ✅ `base.py`
- ✅ `database.py`
- ✅ `session.py`
- ✅ `transaction.py`
- ✅ `schemas.py`
- ✅ `models.py`
- ✅ `create_tables.py`
- ✅ `init_db.py`
- ✅ `database_logging.py`

**Missing (4):**

- ❌ `security/`
- ❌ `setup/`
- ❌ `seeds/`
- ❌ `alembic/`

### Model Files

**Missing (7):**

- ❌ `catalog/product.py -> SQLAlchemy ORM model: Product with `search_vector tsvector`, `embedding vector(N)`, `filter_attributes JSONB`, generated columns, composite indexes`
- ❌ `catalog/category.py -> SQLAlchemy ORM model: Category with materialized-path hierarchy`
- ❌ `catalog/brand.py -> SQLAlchemy ORM model: Brand`
- ❌ `supplier/supplier.py -> SQLAlchemy ORM model: Supplier`
- ❌ `analytics/search_event.py -> SQLAlchemy ORM model: SearchEvent (outbox-backed)`
- ❌ `mixins.py -> AuditMixin, SoftDeleteMixin, VersionMixin`
- ❌ `configuration/ -> SQLAlchemy ORM models: SearchSynonym, SearchBoost, SearchFacetDefinition`

### Frontend Web

**Present (4):**

- ✅ `layout.tsx`
- ✅ `FilterSearchBar.tsx`
- ✅ `web_app/products/page.tsx`
- ✅ `HomeClient.tsx`

**Missing (6):**

- ❌ `search/SearchDropdown.tsx`
- ❌ `search/UnderstandingChips.tsx`
- ❌ `search/FacetPanel.tsx`
- ❌ `search/ImageSearchUpload.tsx`
- ❌ `search/VoiceSearchButton.tsx`
- ❌ `web_app/search/page.tsx`

### Frontend Mobile

**Missing (5):**

- ❌ `(tabs)/index.tsx`
- ❌ `components/ProductSearchFilterBar.tsx`
- ❌ `components/search/SearchBar.tsx`
- ❌ `components/search/VoiceSearchButton.tsx`
- ❌ `components/search/ImageSearchUpload.tsx`

### Tests

**Missing (15):**

- ❌ `tests/backend/_test_search_hybrid_retrieval.py`
- ❌ `tests/backend/_test_search_faceted_filtering.py`
- ❌ `tests/backend/_test_search_cursor_pagination.py`
- ❌ `tests/backend/_test_search_providers_embedding.py`
- ❌ `tests/backend/_test_search_providers_clip.py`
- ❌ `tests/backend/_test_search_providers_whisper.py`
- ❌ `tests/backend/_test_search_voice_parser.py`
- ❌ `tests/backend/_test_search_image_endpoint.py`
- ❌ `tests/backend/_test_search_facet_counts.py`
- ❌ `tests/backend/_test_search_rate_limit.py`
- ❌ `tests/frontend/web_app/_test_search_bar_header.test.tsx`
- ❌ `tests/frontend/web_app/_test_search_combined_filters.test.tsx`
- ❌ `tests/frontend/web_app/_test_search_image_voice.test.tsx`
- ❌ `tests/frontend/mobile_app/_test_search_mobile.test.tsx`
- ❌ `tests/playwright/_test_search_e2e.spec.ts`

### API Routes

**Missing (10):**

- ❌ `GET /search/filtered`
- ❌ `POST /search/by-image`
- ❌ `POST /search/voice`
- ❌ `GET /search/advanced`
- ❌ `GET /search/fuzzy`
- ❌ `GET /search/predict`
- ❌ `GET /search/trending`
- ❌ `GET /search/filters`
- ❌ `POST /search/admin/synonyms`
- ❌ `POST /search/admin/boosts`

### DB Model Classes

**Present (2):**

- ✅ `Product`
- ✅ `Category`

**Missing (6):**

- ❌ `Brand`
- ❌ `Supplier`
- ❌ `SearchEvent`
- ❌ `SearchSynonym`
- ❌ `SearchBoost`
- ❌ `SearchFacetDefinition`

---

## SYS_013 — Admin Command Center — Unified Operations Single Window

### Backend Files

**Missing (18):**

- ❌ `command_center.py -> thin router for Command Center endpoints (zones, Action Drawer, Ctrl+K, broadcasts, escalations, war-room, safe-box, news, country plane, simulations)`
- ❌ `admin.py -> thin router for existing admin endpoints to merge into Single Window`
- ❌ `analytics.py -> thin router for existing analytics endpoints to merge into Single Window`
- ❌ `command_center_controller.py -> orchestrates Command Center flows, delegates to tier services, anomaly engine, country orchestrator; no FastAPI imports`
- ❌ `command_center_service.py -> owns DB reads for dashboard aggregation, tier coordination, freshness metadata, zone shaping by role + RLS`
- ❌ `telemetry_service.py -> T1 WS telemetry channel (Redis PubSub → `/ws/admin/telemetry` heartbeat increments)`
- ❌ `treasury_reader_service.py -> T3 ledger reader (instant SQL on `account_balances` only)`
- ❌ `news_pipeline_service.py -> news ingestion, dedupe, AI enrichment, routing, moderation, Regulatory Shield`
- ❌ `escalation_service.py -> escalation lifecycle (tier timers, ack audit, SMS/email fallback)`
- ❌ `broadcast_service.py -> broadcast CRUD, global/local routing, read-confirm tracking`
- ❌ `country_orchestrator_service.py -> heuristic fetchers, 48h Redis cache, degraded flags, gateway ranking, commission-tier, KYC-tier, logistics recommender`
- ❌ `anomaly_detection_service.py -> config-driven anomaly rules, deep-link action cards`
- ❌ `simulation_service.py -> What-If snapshot-only projections, labeled outputs`
- ❌ `jobs/metric_aggregation_job.py -> T2 Redis JSON + T4 MV refresh cron (5min + nightly)`
- ❌ `jobs/news_enrichment_job.py -> 15-min news fetch/dedupe/enrich/route cron`
- ❌ `jobs/kpi_watchdog_job.py -> hourly KPI targets vs actuals, auto-tickets`
- ❌ `events/event_publisher.py -> Redis pub/sub for telemetry, search/video events`
- ❌ `providers/ai/enrichment_provider.py -> optional LLM re-rank / enrichment adapter (subclass BaseAIProvider, staged→commit)`

### Database Files

**Present (9):**

- ✅ `base.py`
- ✅ `database.py`
- ✅ `session.py`
- ✅ `transaction.py`
- ✅ `schemas.py`
- ✅ `models.py`
- ✅ `create_tables.py`
- ✅ `init_db.py`
- ✅ `database_logging.py`

**Missing (4):**

- ❌ `security/`
- ❌ `setup/`
- ❌ `seeds/`
- ❌ `alembic/`

### Model Files

**Missing (12):**

- ❌ `analytics/system_health_event.py -> SQLAlchemy ORM model: SystemHealthEvent`
- ❌ `analytics/search_log.py -> SQLAlchemy ORM model: SearchLog`
- ❌ `analytics/user_session.py -> SQLAlchemy ORM model: UserSession`
- ❌ `admin/escalation.py -> SQLAlchemy ORM model: Escalation`
- ❌ `admin/broadcast.py -> SQLAlchemy ORM models: Broadcast, BroadcastReadConfirm`
- ❌ `admin/shift_handover_log.py -> SQLAlchemy ORM model: ShiftHandoverLog`
- ❌ `admin/grievance.py -> SQLAlchemy ORM model: Grievance`
- ❌ `news/news_source.py -> SQLAlchemy ORM model: NewsSource`
- ❌ `news/news_article.py -> SQLAlchemy ORM model: NewsArticle (ai_sentiment, ai_tags JSONB, SHA256 content_hash dedupe)`
- ❌ `country/country_config.py -> SQLAlchemy ORM models: CountryConfig + CountryConfigVersion, CountryCity, CountryCategoryTaxRate, CountryFeatureFlag, CountryStaffAssignment`
- ❌ `configuration/search_config.py -> SQLAlchemy ORM models: SearchSynonym, SearchBoost, SearchFacetDefinition`
- ❌ `mixins.py -> AuditMixin, SoftDeleteMixin, VersionMixin`

### Frontend Web

**Present (1):**

- ✅ `web_app/admin/command-center/page.tsx`

**Missing (12):**

- ❌ `admin/CommandCenterLayout.tsx`
- ❌ `admin/ActionDrawer.tsx`
- ❌ `admin/CtrlKPalette.tsx`
- ❌ `admin/EscalationMatrix.tsx`
- ❌ `admin/WarRoomChat.tsx`
- ❌ `admin/SafeBox.tsx`
- ❌ `admin/BroadcastBanner.tsx`
- ❌ `admin/RegulatoryShield.tsx`
- ❌ `admin/MarketRadar.tsx`
- ❌ `admin/CountryControlPlane.tsx`
- ❌ `admin/WhatIfSimulator.tsx`
- ❌ `admin/KPIWatchdog.tsx`

### Frontend Mobile

**Missing (2):**

- ❌ `admin/command-center.tsx`
- ❌ `components/admin/ActionDrawer.tsx`

### Tests

**Missing (16):**

- ❌ `tests/backend/_test_command_center_roles_rls.py`
- ❌ `tests/backend/_test_command_center_4_tier_data.py`
- ❌ `tests/backend/_test_command_center_treasury_ledger.py`
- ❌ `tests/backend/_test_command_center_escalation_audit.py`
- ❌ `tests/backend/_test_command_center_broadcasts.py`
- ❌ `tests/backend/_test_command_center_news_pipeline.py`
- ❌ `tests/backend/_test_command_center_country_orchestrator.py`
- ❌ `tests/backend/_test_command_center_anomaly_rules.py`
- ❌ `tests/backend/_test_command_center_simulation_engine.py`
- ❌ `tests/backend/_test_command_center_kpi_watchdog.py`
- ❌ `tests/backend/_test_command_center_alert_fatigue.py`
- ❌ `tests/frontend/web_app/_test_command_center_single_window.test.tsx`
- ❌ `tests/frontend/web_app/_test_command_center_roles.test.tsx`
- ❌ `tests/frontend/web_app/_test_command_center_e2e.test.tsx`
- ❌ `tests/frontend/mobile_app/_test_command_center_mobile.test.tsx`
- ❌ `tests/playwright/_test_command_center_e2e.spec.ts`

### API Routes

**Missing (26):**

- ❌ `GET /api/v1/admin/command-center`
- ❌ `GET /api/v1/admin/command-center/zones`
- ❌ `GET /api/v1/admin/command-center/zone/{zone_id}`
- ❌ `GET /api/v1/admin/command-center/action-drawer`
- ❌ `POST /api/v1/admin/command-center/broadcasts`
- ❌ `PUT /api/v1/admin/command-center/broadcasts/{id}/read-confirm`
- ❌ `POST /api/v1/admin/command-center/escalations`
- ❌ `POST /api/v1/admin/command-center/escalations/{id}/ack`
- ❌ `POST /api/v1/admin/command-center/escalations/{id}/approve`
- ❌ `POST /api/v1/admin/command-center/escalations/{id}/block`
- ❌ `POST /api/v1/admin/command-center/shift-handover`
- ❌ `GET /api/v1/admin/command-center/shift-handover/pending`
- ❌ `POST /api/v1/admin/command-center/war-room/threads`
- ❌ `POST /api/v1/admin/command-center/war-room/threads/{id}/messages`
- ❌ `GET /api/v1/admin/command-center/safe-box`
- ❌ `POST /api/v1/admin/command-center/safe-box`
- ❌ `GET /api/v1/admin/command-center/news`
- ❌ `POST /api/v1/admin/command-center/news/{id}/publish`
- ❌ `POST /api/v1/admin/command-center/news/{id}/moderate`
- ❌ `GET /api/v1/admin/command-center/regulatory-shield`
- ❌ `GET /api/v1/admin/command-center/country/{code}/orchestrator`
- ❌ `POST /api/v1/admin/command-center/country/{code}/publish`
- ❌ `POST /api/v1/admin/command-center/simulate`
- ❌ `GET /api/v1/admin/command-center/kpi-watchdog`
- ❌ `GET /api/v1/admin/command-center/kpi-watchdog/tickets`
- ❌ `GET /api/v1/admin/command-center/telemetry`

### DB Model Classes

**Present (11):**

- ✅ `SystemHealthEvent`
- ✅ `UserSession`
- ✅ `ShiftHandoverLog`
- ✅ `NewsSource`
- ✅ `NewsArticle`
- ✅ `CountryConfig`
- ✅ `CountryConfigVersion`
- ✅ `CountryCity`
- ✅ `CountryCategoryTaxRate`
- ✅ `CountryFeatureFlag`
- ✅ `CountryStaffAssignment`

**Missing (8):**

- ❌ `SearchLog`
- ❌ `Escalation`
- ❌ `Broadcast`
- ❌ `BroadcastReadConfirm`
- ❌ `Grievance`
- ❌ `SearchSynonym`
- ❌ `SearchBoost`
- ❌ `SearchFacetDefinition`

---

## SYS_014 — Supplier Product Upload � Speed-First Automation-First Modal Flow

### Backend Files

**Missing (13):**

- ❌ `suppliers/supplier.py -> thin router for supplier upload endpoints (remove-background, ai-analyze, voice-transcribe, analyze-parallel, variant-axes)`
- ❌ `suppliers/supplier_upload_controller.py -> orchestrates upload flow, delegates to services; no FastAPI imports`
- ❌ `suppliers/supplier_upload_service.py -> owns DB writes for product creation, variant inventory, media_assets linking`
- ❌ `suppliers/variant_config_service.py -> loads zozi_variant_config.json, exposes axes + material options`
- ❌ `media/background_removal_service.py -> BG removal via provider adapter`
- ❌ `ai/product_analysis_service.py -> AI product name/description/tags/color detection`
- ❌ `ai/voice_transcription_service.py -> voice note -> text -> NLP parse`
- ❌ `jobs/background_removal_job.py -> BG removal background worker`
- ❌ `jobs/ai_analysis_job.py -> AI analysis background worker`
- ❌ `events/event_publisher.py -> Redis pub/sub for product-change events`
- ❌ `providers/ai/background_removal_provider.py -> BG removal adapter (subclass BaseAIProvider)`
- ❌ `providers/ai/product_analysis_provider.py -> AI analysis adapter (subclass BaseAIProvider)`
- ❌ `providers/ai/voice_transcription_provider.py -> voice->text adapter (subclass BaseAIProvider)`

### Database Files

**Present (9):**

- ✅ `base.py`
- ✅ `database.py`
- ✅ `session.py`
- ✅ `transaction.py`
- ✅ `schemas.py`
- ✅ `models.py`
- ✅ `create_tables.py`
- ✅ `init_db.py`
- ✅ `database_logging.py`

**Missing (4):**

- ❌ `security/`
- ❌ `setup/`
- ❌ `seeds/`
- ❌ `alembic/`

### Model Files

**Missing (4):**

- ❌ `supplier/supplier_product.py -> SQLAlchemy ORM model: SupplierProduct`
- ❌ `supplier/product_variant.py -> SQLAlchemy ORM model: ProductVariant`
- ❌ `media/media_asset.py -> SQLAlchemy ORM model: MediaAsset (url, mime, hash; no bytes)`
- ❌ `mixins.py -> AuditMixin, SoftDeleteMixin, VersionMixin`

### Frontend Web

**Present (4):**

- ✅ `web_app/supplier/products/add/page.tsx`
- ✅ `supplier/upload/UploadModal.tsx`
- ✅ `lib/uploadOrchestrator.ts`
- ✅ `lib/variantConfig.ts`

**Missing (7):**

- ❌ `supplier/upload/ProcessingModal.tsx`
- ❌ `supplier/upload/PhotoEditModal.tsx`
- ❌ `supplier/upload/AIResultsModal.tsx`
- ❌ `supplier/upload/QuantityModal.tsx`
- ❌ `supplier/upload/VerifyPublishModal.tsx`
- ❌ `supplier/upload/VoiceModal.tsx`
- ❌ `lib/variantEngine.ts`

### Frontend Mobile

**Missing (8):**

- ❌ `supplier/products/add.tsx`
- ❌ `components/supplier/upload/UploadModal.tsx`
- ❌ `components/supplier/upload/ProcessingModal.tsx`
- ❌ `components/supplier/upload/PhotoEditModal.tsx`
- ❌ `components/supplier/upload/AIResultsModal.tsx`
- ❌ `components/supplier/upload/QuantityModal.tsx`
- ❌ `components/supplier/upload/VerifyPublishModal.tsx`
- ❌ `components/supplier/upload/VoiceModal.tsx`

### Tests

**Missing (8):**

- ❌ `tests/backend/_test_supplier_upload_parallel_endpoint.py`
- ❌ `tests/backend/_test_supplier_upload_variant_config.py`
- ❌ `tests/backend/_test_supplier_upload_rls.py`
- ❌ `tests/backend/_test_supplier_upload_voice_flow.py`
- ❌ `tests/frontend/web_app/_test_supplier_upload_flow.test.tsx`
- ❌ `tests/frontend/web_app/_test_supplier_upload_voice.test.tsx`
- ❌ `tests/frontend/mobile_app/_test_supplier_upload_flow.test.tsx`
- ❌ `tests/playwright/_test_supplier_upload_e2e.spec.ts`

### API Routes

**Missing (10):**

- ❌ `POST /api/v1/supplier/upload/analyze-parallel`
- ❌ `GET /api/v1/supplier/upload/variant-axes`
- ❌ `POST /api/v1/supplier/upload/remove-background`
- ❌ `POST /api/v1/supplier/upload/ai-analyze`
- ❌ `POST /api/v1/supplier/upload/voice-transcribe`
- ❌ `POST /api/v1/supplier/products`
- ❌ `GET /api/v1/supplier/products`
- ❌ `GET /api/v1/supplier/products/{id}`
- ❌ `PUT /api/v1/supplier/products/{id}`
- ❌ `DELETE /api/v1/supplier/products/{id}`

### DB Model Classes

**Present (2):**

- ✅ `ProductVariant`
- ✅ `MediaAsset`

**Missing (1):**

- ❌ `SupplierProduct`

---

## SYS_015 — Supplier Commission Structure - Countries wise vary and Product wise vary

### Backend Files

**Missing (14):**

- ❌ `admin_commission.py -> thin router for commission category rates and badge tiers CRUD`
- ❌ `admin_geography_configuration.py -> thin router for country-scoped commission rates and tiers`
- ❌ `core_commission.py -> thin router for supplier/product overrides and commission preview`
- ❌ `core/admin_commission_controller.py -> orchestrates admin commission routes, delegates to admin_commission_service`
- ❌ `admin/admin_geography_configuration_controller.py -> orchestrates country commission routes, delegates to admin_geography_configuration_service`
- ❌ `core/commission_controller.py -> orchestrates core commission routes, delegates to commission_service`
- ❌ `finance/commission_controller.py -> orchestrates finance commission routes, delegates to commission_service`
- ❌ `core/admin_commission_service.py -> owns DB writes for global config, category rates, badge tiers`
- ❌ `finance/commission_geography_service.py -> country-scoped commission category rate + badge tier CRUD`
- ❌ `finance/commission_service.py -> supplier/product override CRUD, preview logic, ledger entry persistence`
- ❌ `finance/commission_engine.py -> deterministic rate resolution, low-value cap, seed defaults, Decimal-only arithmetic`
- ❌ `events/event_publisher.py -> Redis pub/sub for commission-calculated events`
- ❌ `jobs/supplier_payout_worker.py -> payout execution background worker`
- ❌ `providers/finance/ledger_audit_provider.py -> commission ledger audit adapter (subclass BaseProvider)`

### Database Files

**Present (9):**

- ✅ `base.py`
- ✅ `database.py`
- ✅ `session.py`
- ✅ `transaction.py`
- ✅ `schemas.py`
- ✅ `models.py`
- ✅ `create_tables.py`
- ✅ `init_db.py`
- ✅ `database_logging.py`

**Missing (4):**

- ❌ `security/`
- ❌ `setup/`
- ❌ `seeds/`
- ❌ `alembic/`

### Model Files

**Missing (5):**

- ❌ `commission.py -> SQLAlchemy ORM: CommissionAgreement, ProductCommissionOverride, CommissionLedgerEntry, CommissionCategoryRate`
- ❌ `admin.py -> SQLAlchemy ORM: CommissionBadgeTier, CommissionGlobalConfig`
- ❌ `geography/country_enhancements.py -> SQLAlchemy ORM: CountryCommissionRate, CountryCommissionRateHistory`
- ❌ `finance/__init__.py -> forward re-exports for commission models`
- ❌ `mixins.py -> AuditMixin, SoftDeleteMixin, VersionMixin`

### Frontend Web

**Present (4):**

- ✅ `web_app/admin/commission/page.tsx`
- ✅ `supplier/CommissionPolicySummary.tsx`
- ✅ `web_app/admin/countries/page.tsx`
- ✅ `web_app/supplier/profile/page.tsx`

**Missing (5):**

- ❌ `admin/CommissionGlobalRate.tsx`
- ❌ `admin/CommissionCategoryRates.tsx`
- ❌ `admin/CommissionSupplierOverrides.tsx`
- ❌ `admin/CommissionBadgeTiers.tsx`
- ❌ `admin/CommissionPreviewCalculator.tsx`

### Frontend Mobile

**Missing (7):**

- ❌ `mobile_app/admin/commission/page.tsx`
- ❌ `components/admin/CommissionGlobalRate.tsx`
- ❌ `components/admin/CommissionCategoryRates.tsx`
- ❌ `components/admin/CommissionSupplierOverrides.tsx`
- ❌ `components/admin/CommissionBadgeTiers.tsx`
- ❌ `components/admin/CommissionPreviewCalculator.tsx`
- ❌ `components/supplier/CommissionPolicySummary.tsx`

### Tests

**Missing (11):**

- ❌ `tests/backend/_test_commission_engine_rate_resolution.py`
- ❌ `tests/backend/_test_commission_engine_low_value_cap.py`
- ❌ `tests/backend/_test_commission_ledger_immutability.py`
- ❌ `tests/backend/_test_commission_country_rates.py`
- ❌ `tests/backend/_test_commission_supplier_product_overrides.py`
- ❌ `tests/backend/_test_commission_geography_service.py`
- ❌ `tests/backend/_test_commission_seed_defaults.py`
- ❌ `tests/frontend/web_app/_test_admin_commission_page.test.tsx`
- ❌ `tests/frontend/web_app/_test_supplier_commission_policy.test.tsx`
- ❌ `tests/frontend/mobile_app/_test_admin_commission_page.test.tsx`
- ❌ `tests/playwright/_test_commission_admin_flow.spec.ts`

### API Routes

**Missing (23):**

- ❌ `GET /api/v1/admin/commission/global`
- ❌ `PUT /api/v1/admin/commission/global`
- ❌ `GET /api/v1/admin/commission/categories`
- ❌ `POST /api/v1/admin/commission/categories`
- ❌ `PUT /api/v1/admin/commission/categories/{id}`
- ❌ `DELETE /api/v1/admin/commission/categories/{id}`
- ❌ `GET /api/v1/admin/commission/suppliers`
- ❌ `POST /api/v1/admin/commission/suppliers/{id}/override`
- ❌ `DELETE /api/v1/admin/commission/suppliers/{id}/override`
- ❌ `GET /api/v1/admin/commission/badge-tiers`
- ❌ `POST /api/v1/admin/commission/badge-tiers`
- ❌ `PUT /api/v1/admin/commission/badge-tiers/{id}`
- ❌ `DELETE /api/v1/admin/commission/badge-tiers/{id}`
- ❌ `POST /api/v1/admin/commission/preview`
- ❌ `GET /api/v1/admin/countries/{code}/commission-rates`
- ❌ `POST /api/v1/admin/countries/{code}/commission-rates`
- ❌ `DELETE /api/v1/admin/countries/{code}/commission-rates/{tier}/{name}`
- ❌ `GET /api/v1/admin/countries/{code}/commissions`
- ❌ `PUT /api/v1/admin/countries/{code}/commissions`
- ❌ `GET /api/v1/admin/countries/{code}/commission-tiers`
- ❌ `PUT /api/v1/admin/countries/{code}/commission-tiers`
- ❌ `GET /api/v1/supplier/commission/policy`
- ❌ `GET /api/v1/commission/effective-rate`

### DB Model Classes

**Present (9):**

- ✅ `CommissionAgreement`
- ✅ `ProductCommissionOverride`
- ✅ `CommissionLedgerEntry`
- ✅ `CommissionCategoryRate`
- ✅ `CommissionBadgeTier`
- ✅ `CommissionGlobalConfig`
- ✅ `CountryCommissionRate`
- ✅ `CountryCommissionRateHistory`
- ✅ `SupplierCountryCommission`

---

## SYS_016 — Logistic Panel - Countries wise vary and Product wise vary

### Backend Files

**Missing (20):**

- ❌ `logistics_partner.py -> thin router for logistics partner endpoints (public list, profile CRUD, service-areas CRUD, pricing-profiles CRUD, category-rules CRUD, vehicle-rules CRUD, review actions)`
- ❌ `logistics_locations_create.py -> thin router for logistics city-pair location management endpoints`
- ❌ `logistics_logistics_status.py -> thin router for shipment status update endpoints`
- ❌ `core/logistics_partner_controller.py -> orchestrates logistics partner routes, delegates to logistics_partner_service, no FastAPI imports`
- ❌ `core/logistics_locations_controller.py -> orchestrates logistics location routes, delegates to logistics_locations_service, no FastAPI imports`
- ❌ `logistics/logistics_logistics_status_controller.py -> orchestrates shipment status routes, delegates to logistics_logistics_status_service, no FastAPI imports`
- ❌ `orders/logistics_partner_controller.py -> orchestrates order-logistics partner assignment routes, delegates to logistics_partner_service, no FastAPI imports`
- ❌ `router_bridges/logistics_partner_geography_service.py -> router bridge for partner geography and charge resolution`
- ❌ `core/logistics_partner_service.py -> owns DB writes for partner profile, service areas, pricing profiles, category rules, vehicle rules; review orchestration (approve/reject)`
- ❌ `core/logistics_locations_service.py -> owns DB writes for city-pair location management`
- ❌ `logistics/logistics_partner_pricing.py -> charge resolution by city pair + country_code, approval status filtering, city distance matrix lookup, Decimal-only arithmetic`
- ❌ `logistics/logistics_engine.py -> partner matching, claim board queries, approved-partner filtering`
- ❌ `logistics/logistics_partner_write_service.py -> logistics partner write service (profile and area updates)`
- ❌ `logistics/logistics_write_service.py -> logistics write service (shipment and event updates)`
- ❌ `logistics/logistics_logistics_status_service.py -> shipment status transitions, GPS updates, event publishing`
- ❌ `middleware/rls_dependency.py -> RLS enforcement on logistics queries (cross-cutting)`
- ❌ `jobs/logistics_charge_sync_job.py -> background worker for cart cache invalidation on charge approval/rejection`
- ❌ `jobs/logistics_partner_visibility_job.py -> background worker for updating public partner directory visibility on approval/rejection`
- ❌ `events/event_publisher.py -> Redis pub/sub event publisher (reuse existing, extend for logistics approval events)`
- ❌ `events/logistics_events.py -> domain event schemas for charge_approved, charge_rejected, partner_approved, partner_rejected`

### Database Files

**Present (9):**

- ✅ `base.py`
- ✅ `database.py`
- ✅ `session.py`
- ✅ `transaction.py`
- ✅ `schemas.py`
- ✅ `models.py`
- ✅ `create_tables.py`
- ✅ `init_db.py`
- ✅ `database_logging.py`

**Missing (4):**

- ❌ `security/`
- ❌ `setup/`
- ❌ `seeds/`
- ❌ `alembic/`

### Model Files

**Missing (3):**

- ❌ `logistics/logistics_entities.py -> SQLAlchemy ORM: LogisticsPartner, LogisticsPartnerProfile, LogisticsPartnerServiceArea, LogisticsPricingProfile, LogisticsVehicleRule, LogisticsCategoryPricingRule, Shipment, ShipmentEvent`
- ❌ `logistics.py -> Legacy logistics models (to be migrated to logistics_entities.py)`
- ❌ `mixins.py -> AuditMixin, SoftDeleteMixin, VersionMixin`

### Frontend Web

**Present (8):**

- ✅ `web_app/logistics-partner/profile/page.tsx`
- ✅ `web_app/logistics-partner/dashboard/page.tsx`
- ✅ `web_app/logistics-partner/shipments/page.tsx`
- ✅ `web_app/logistics-partner/routes/page.tsx`
- ✅ `web_app/logistics-partner/payouts/page.tsx`
- ✅ `web_app/logistics-partners/page.tsx`
- ✅ `web_app/logistics-partners/[id]/page.tsx`
- ✅ `admin/logistics/_components/LogisticsPartnersPanel.tsx`

**Missing (4):**

- ❌ `logistics/ServiceAreaForm.tsx`
- ❌ `logistics/PricingProfileForm.tsx`
- ❌ `logistics/CategoryRuleForm.tsx`
- ❌ `logistics/VehicleRuleForm.tsx`

### Frontend Mobile

**Present (3):**

- ✅ `logistics-partner/dashboard.tsx`
- ✅ `logistics-partner/shipments.tsx`
- ✅ `logistics-partner/payouts.tsx`

**Missing (6):**

- ❌ `logistics-partner/profile/ (Expo Router screens)`
- ❌ `logistics-partner/routes.tsx`
- ❌ `components/logistics/ServiceAreaForm.tsx`
- ❌ `components/logistics/PricingProfileForm.tsx`
- ❌ `components/logistics/CategoryRuleForm.tsx`
- ❌ `components/logistics/VehicleRuleForm.tsx`

### Tests

**Missing (13):**

- ❌ `tests/backend/_test_logistics_partner_profile_approval.py`
- ❌ `tests/backend/_test_logistics_service_area_charge_approval.py`
- ❌ `tests/backend/_test_logistics_pricing_profile_approval.py`
- ❌ `tests/backend/_test_logistics_charge_resolution_cart.py`
- ❌ `tests/backend/_test_logistics_partner_visibility.py`
- ❌ `tests/backend/_test_logistics_shipment_board_gating.py`
- ❌ `tests/backend/_test_logistics_rls_country.py`
- ❌ `tests/backend/_test_logistics_city_distance_lookup.py`
- ❌ `tests/frontend/web_app/_test_logistics_partner_profile.test.tsx`
- ❌ `tests/frontend/web_app/_test_admin_logistics_panel.test.tsx`
- ❌ `tests/frontend/web_app/_test_cart_logistics_charge_resolution.test.tsx`
- ❌ `tests/frontend/mobile_app/_test_logistics_partner_profile.test.tsx`
- ❌ `tests/playwright/_test_logistics_panel_e2e.spec.ts`

### API Routes

**Missing (34):**

- ❌ `GET /api/v1/logistics/public`
- ❌ `GET /api/v1/logistics/public/{partner_id}`
- ❌ `GET /api/v1/logistics/profile`
- ❌ `PUT /api/v1/logistics/profile`
- ❌ `POST /api/v1/logistics/profile/terms/accept`
- ❌ `POST /api/v1/logistics/profile/submit-review`
- ❌ `GET /api/v1/logistics/service-areas`
- ❌ `POST /api/v1/logistics/service-areas`
- ❌ `PUT /api/v1/logistics/service-areas/{area_id}`
- ❌ `DELETE /api/v1/logistics/service-areas/{area_id}`
- ❌ `GET /api/v1/logistics/pricing-profiles`
- ❌ `POST /api/v1/logistics/pricing-profiles`
- ❌ `PUT /api/v1/logistics/pricing-profiles/{profile_id}`
- ❌ `DELETE /api/v1/logistics/pricing-profiles/{profile_id}`
- ❌ `GET /api/v1/logistics/category-rules`
- ❌ `POST /api/v1/logistics/category-rules`
- ❌ `PUT /api/v1/logistics/category-rules/{rule_id}`
- ❌ `DELETE /api/v1/logistics/category-rules/{rule_id}`
- ❌ `GET /api/v1/logistics/vehicle-rules`
- ❌ `POST /api/v1/logistics/vehicle-rules`
- ❌ `PUT /api/v1/logistics/vehicle-rules/{rule_id}`
- ❌ `DELETE /api/v1/logistics/vehicle-rules/{rule_id}`
- ❌ `GET /api/v1/logistics/city-distances`
- ❌ `POST /api/v1/logistics/city-distances`
- ❌ `PUT /api/v1/logistics/city-distances/{matrix_id}`
- ❌ `DELETE /api/v1/logistics/city-distances/{matrix_id}`
- ❌ `POST /api/v1/logistics/review/profile/{partner_id}`
- ❌ `POST /api/v1/logistics/review/service-areas/{area_id}`
- ❌ `POST /api/v1/logistics/review/pricing-profiles/{profile_id}`
- ❌ `POST /api/v1/logistics/review/category-rules/{rule_id}`
- ❌ `POST /api/v1/logistics/review/vehicle-rules/{rule_id}`
- ❌ `GET /api/v1/logistics/shipping-quote`
- ❌ `GET /api/v1/logistics-partner/me/bank-account`
- ❌ `PUT /api/v1/logistics-partner/me/bank-account`

### DB Model Classes

**Present (10):**

- ✅ `LogisticsPartner`
- ✅ `LogisticsPartnerProfile`
- ✅ `LogisticsPartnerServiceArea`
- ✅ `LogisticsPricingProfile`
- ✅ `LogisticsVehicleRule`
- ✅ `LogisticsCategoryPricingRule`
- ✅ `Shipment`
- ✅ `ShipmentEvent`
- ✅ `CityDistanceMatrix`
- ✅ `ShippingCarrier`

---

## SYS_017 — AI Provider System and Automation List

### Backend Files

**Missing (134):**

- ❌ `providers/ai/chatbot_provider.py -> AI chatbot provider (RAG over product catalog + order history, subclass BaseAIProvider)`
- ❌ `providers/ai/ocr_provider.py -> OCR provider for bill/receipt scanning (subclass BaseAIProvider)`
- ❌ `providers/ai/search_vectorization_provider.py -> Hybrid search vectorization (CLIP + FTS + pgvector, subclass BaseAIProvider)`
- ❌ `providers/ai/country_intelligence_provider.py -> Country intelligence AI for admin analytics (subclass BaseAIProvider)`
- ❌ `providers/ai/admin_analytics_provider.py -> Admin analytics AI (anomaly detection, forecasting, risk scoring, subclass BaseAIProvider)`
- ❌ `providers/image/background_removal_provider.py -> Image background removal provider (subclass BaseProvider)`
- ❌ `providers/image/product_analysis_provider.py -> Image-to-text product analysis provider (description, tags, variants, subclass BaseAIProvider)`
- ❌ `providers/voice/voice_to_text_provider.py -> Voice-to-text provider (Whisper/CTC optimized for short commands, subclass BaseAIProvider)`
- ❌ `providers/geography/ip_detection_provider.py -> IP address detection and geolocation provider (subclass BaseProvider)`
- ❌ `providers/geography/map_location_provider.py -> Map and location provider (geocoding, reverse geocoding, distance matrix, subclass BaseProvider)`
- ❌ `providers/automation/workflow_engine_provider.py -> Workflow automation engine provider (trigger->condition->action, approvals, parallel/scheduled, versioning)`
- ❌ `providers/automation/event_engine_provider.py -> Event engine provider (pub/sub, queue, retry, DLQ, monitoring)`
- ❌ `providers/automation/notification_engine_provider.py -> Notification engine provider (email/SMS/WhatsApp/push/in-app, templates, retry)`
- ❌ `providers/automation/scheduled_jobs_engine_provider.py -> Scheduled jobs engine provider (cron, recurring, delayed, one-time, history, monitoring)`
- ❌ `providers/automation/approval_engine_provider.py -> Approval engine provider (single/multi-level, auto-approval, escalation, history)`
- ❌ `providers/automation/rule_engine_provider.py -> Rule engine provider (business/country/supplier/customer/promotion/logistics rules)`
- ❌ `providers/automation/assignment_engine_provider.py -> Assignment engine provider (delivery/support/complaint/task assignment, load balancing)`
- ❌ `providers/automation/reminder_engine_provider.py -> Reminder engine provider (payment/KYC/expiry/follow-up/renewal reminders)`
- ❌ `providers/automation/escalation_engine_provider.py -> Escalation engine provider (SLA monitoring, auto-escalation, levels, manager notification)`
- ❌ `providers/automation/finance_automation_provider.py -> Finance automation provider (auto journal, commission, settlement, payout, reconciliation, refund)`
- ❌ `providers/automation/inventory_automation_provider.py -> Inventory automation provider (stock updates, low-stock alerts, out-of-stock, auto reservation, sync)`
- ❌ `providers/automation/order_automation_provider.py -> Order automation provider (validation, supplier routing, split-order, status updates, return workflow)`
- ❌ `providers/automation/logistics_automation_provider.py -> Logistics automation provider (delivery assignment, route optimization, pickup scheduling, tracking, POD verification, COD reconciliation)`
- ❌ `providers/automation/ai_automation_provider.py -> AI automation provider (product description, categorization, image optimization, duplicate detection, content moderation)`
- ❌ `providers/automation/data_automation_provider.py -> Data automation provider (import/export, cleanup, archive, backup verification)`
- ❌ `providers/automation/security_automation_provider.py -> Security automation provider (login monitoring, suspicious activity, account lock, session cleanup, API monitoring)`
- ❌ `providers/automation/customer_automation_provider.py -> Customer automation provider (welcome journey, cart abandonment, review requests, loyalty rewards, re-engagement)`
- ❌ `providers/automation/supplier_automation_provider.py -> Supplier automation provider (KYC workflow, store approval, product approval, performance alerts, payout notifications)`
- ❌ `providers/automation/admin_automation_provider.py -> Admin automation provider (dashboard alerts, health monitoring, error reporting, daily/weekly summary)`
- ❌ `providers/automation/monitoring_recovery_provider.py -> Monitoring & recovery provider (automation logs, failure alerts, retry queue, execution history, performance metrics)`
- ❌ `providers/automation/automation_registry_provider.py -> Central automation registry provider (enable/disable, priority, dependencies, dry-run, audit trail, version control, RBAC)`
- ❌ `providers/_base.py -> BaseProvider/BaseAIProvider base classes (health_check, retry, circuit breaker)`
- ❌ `ai/chatbot_router.py -> thin router for AI chatbot endpoints`
- ❌ `ai/ocr_router.py -> thin router for OCR endpoints`
- ❌ `ai/image_analysis_router.py -> thin router for image analysis endpoints (bg removal, product analysis)`
- ❌ `ai/voice_router.py -> thin router for voice-to-text endpoints`
- ❌ `ai/search_vector_router.py -> thin router for search vectorization endpoints`
- ❌ `ai/ip_detection_router.py -> thin router for IP detection endpoints`
- ❌ `ai/map_location_router.py -> thin router for map/location endpoints`
- ❌ `ai/country_intelligence_router.py -> thin router for country intelligence endpoints`
- ❌ `ai/admin_analytics_router.py -> thin router for admin analytics AI endpoints`
- ❌ `automation/workflow_router.py -> thin router for workflow automation endpoints`
- ❌ `automation/event_router.py -> thin router for event engine endpoints`
- ❌ `automation/notification_router.py -> thin router for notification engine endpoints`
- ❌ `automation/scheduled_jobs_router.py -> thin router for scheduled jobs endpoints`
- ❌ `automation/approval_router.py -> thin router for approval engine endpoints`
- ❌ `automation/rule_router.py -> thin router for rule engine endpoints`
- ❌ `automation/assignment_router.py -> thin router for assignment engine endpoints`
- ❌ `automation/reminder_router.py -> thin router for reminder engine endpoints`
- ❌ `automation/escalation_router.py -> thin router for escalation engine endpoints`
- ❌ `automation/finance_automation_router.py -> thin router for finance automation endpoints`
- ❌ `automation/inventory_automation_router.py -> thin router for inventory automation endpoints`
- ❌ `automation/order_automation_router.py -> thin router for order automation endpoints`
- ❌ `automation/logistics_automation_router.py -> thin router for logistics automation endpoints`
- ❌ `automation/ai_automation_router.py -> thin router for AI automation endpoints`
- ❌ `automation/data_automation_router.py -> thin router for data automation endpoints`
- ❌ `automation/security_automation_router.py -> thin router for security automation endpoints`
- ❌ `automation/customer_automation_router.py -> thin router for customer automation endpoints`
- ❌ `automation/supplier_automation_router.py -> thin router for supplier automation endpoints`
- ❌ `automation/admin_automation_router.py -> thin router for admin automation endpoints`
- ❌ `automation/monitoring_recovery_router.py -> thin router for monitoring & recovery endpoints`
- ❌ `automation/automation_registry_router.py -> thin router for automation registry endpoints`
- ❌ `ai/chatbot_controller.py -> orchestrates chatbot routes, delegates to chatbot_service, no FastAPI imports`
- ❌ `ai/ocr_controller.py -> orchestrates OCR routes, delegates to ocr_service, no FastAPI imports`
- ❌ `ai/image_analysis_controller.py -> orchestrates image analysis routes, delegates to image_analysis_service, no FastAPI imports`
- ❌ `ai/voice_controller.py -> orchestrates voice-to-text routes, delegates to voice_service, no FastAPI imports`
- ❌ `ai/search_vector_controller.py -> orchestrates search vectorization routes, delegates to search_vector_service, no FastAPI imports`
- ❌ `ai/ip_detection_controller.py -> orchestrates IP detection routes, delegates to ip_detection_service, no FastAPI imports`
- ❌ `ai/map_location_controller.py -> orchestrates map/location routes, delegates to map_location_service, no FastAPI imports`
- ❌ `ai/country_intelligence_controller.py -> orchestrates country intelligence routes, delegates to country_intelligence_service, no FastAPI imports`
- ❌ `ai/admin_analytics_controller.py -> orchestrates admin analytics AI routes, delegates to admin_analytics_service, no FastAPI imports`
- ❌ `automation/workflow_controller.py -> orchestrates workflow automation routes, delegates to workflow_engine_service, no FastAPI imports`
- ❌ `automation/event_controller.py -> orchestrates event engine routes, delegates to event_engine_service, no FastAPI imports`
- ❌ `automation/notification_controller.py -> orchestrates notification engine routes, delegates to notification_engine_service, no FastAPI imports`
- ❌ `automation/scheduled_jobs_controller.py -> orchestrates scheduled jobs routes, delegates to scheduled_jobs_service, no FastAPI imports`
- ❌ `automation/approval_controller.py -> orchestrates approval engine routes, delegates to approval_engine_service, no FastAPI imports`
- ❌ `automation/rule_controller.py -> orchestrates rule engine routes, delegates to rule_engine_service, no FastAPI imports`
- ❌ `automation/assignment_controller.py -> orchestrates assignment engine routes, delegates to assignment_engine_service, no FastAPI imports`
- ❌ `automation/reminder_controller.py -> orchestrates reminder engine routes, delegates to reminder_engine_service, no FastAPI imports`
- ❌ `automation/escalation_controller.py -> orchestrates escalation engine routes, delegates to escalation_engine_service, no FastAPI imports`
- ❌ `automation/finance_automation_controller.py -> orchestrates finance automation routes, delegates to finance_automation_service, no FastAPI imports`
- ❌ `automation/inventory_automation_controller.py -> orchestrates inventory automation routes, delegates to inventory_automation_service, no FastAPI imports`
- ❌ `automation/order_automation_controller.py -> orchestrates order automation routes, delegates to order_automation_service, no FastAPI imports`
- ❌ `automation/logistics_automation_controller.py -> orchestrates logistics automation routes, delegates to logistics_automation_service, no FastAPI imports`
- ❌ `automation/ai_automation_controller.py -> orchestrates AI automation routes, delegates to ai_automation_service, no FastAPI imports`
- ❌ `automation/data_automation_controller.py -> orchestrates data automation routes, delegates to data_automation_service, no FastAPI imports`
- ❌ `automation/security_automation_controller.py -> orchestrates security automation routes, delegates to security_automation_service, no FastAPI imports`
- ❌ `automation/customer_automation_controller.py -> orchestrates customer automation routes, delegates to customer_automation_service, no FastAPI imports`
- ❌ `automation/supplier_automation_controller.py -> orchestrates supplier automation routes, delegates to supplier_automation_service, no FastAPI imports`
- ❌ `automation/admin_automation_controller.py -> orchestrates admin automation routes, delegates to admin_automation_service, no FastAPI imports`
- ❌ `automation/monitoring_recovery_controller.py -> orchestrates monitoring & recovery routes, delegates to monitoring_recovery_service, no FastAPI imports`
- ❌ `automation/automation_registry_controller.py -> orchestrates automation registry routes, delegates to automation_registry_service, no FastAPI imports`
- ❌ `ai/chatbot_service.py -> owns DB writes for chatbot sessions, messages, citations, RAG queries`
- ❌ `ai/ocr_service.py -> owns DB writes for OCR scans, structured extraction results, expense/asset linking`
- ❌ `ai/image_analysis_service.py -> owns DB writes for image analysis, bg removal results, product tags, variant suggestions`
- ❌ `ai/voice_service.py -> owns DB writes for voice transcriptions, command parsing, finance task creation`
- ❌ `ai/search_vector_service.py -> owns DB writes for vector embeddings, search analytics, hybrid ranking`
- ❌ `ai/ip_detection_service.py -> owns DB writes for IP lookups, geo-resolution cache, manual-pin fallback`
- ❌ `ai/map_location_service.py -> owns DB writes for geocoding, reverse geocoding, distance matrix`
- ❌ `ai/country_intelligence_service.py -> owns DB writes for country research, regulatory summaries, holiday calendars`
- ❌ `ai/admin_analytics_service.py -> owns DB writes for admin analytics, anomaly detection, forecasting, risk scoring`
- ❌ `ai/ai_provider_registry_service.py -> central provider registry, health checks, circuit breaker, model routing, concurrent pool management`
- ❌ `automation/workflow_engine_service.py -> workflow engine (trigger->condition->action, approvals, parallel/scheduled, versioning)`
- ❌ `automation/event_engine_service.py -> event engine (pub/sub, queue, retry, DLQ, monitoring)`
- ❌ `automation/notification_engine_service.py -> notification engine (email/SMS/WhatsApp/push/in-app, templates, retry)`
- ❌ `automation/scheduled_jobs_engine_service.py -> scheduled jobs engine (cron, recurring, delayed, one-time, history, monitoring)`
- ❌ `automation/approval_engine_service.py -> approval engine (single/multi-level, auto-approval, escalation, history)`
- ❌ `automation/rule_engine_service.py -> rule engine (business/country/supplier/customer/promotion/logistics rules)`
- ❌ `automation/assignment_engine_service.py -> assignment engine (delivery/support/complaint/task assignment, load balancing)`
- ❌ `automation/reminder_engine_service.py -> reminder engine (payment/KYC/expiry/follow-up/renewal reminders)`
- ❌ `automation/escalation_engine_service.py -> escalation engine (SLA monitoring, auto-escalation, levels, manager notification)`
- ❌ `automation/finance_automation_service.py -> finance automation (auto journal, commission, settlement, payout, reconciliation, refund)`
- ❌ `automation/inventory_automation_service.py -> inventory automation (stock updates, low-stock alerts, out-of-stock, auto reservation, sync)`
- ❌ `automation/order_automation_service.py -> order automation (validation, supplier routing, split-order, status updates, return workflow)`
- ❌ `automation/logistics_automation_service.py -> logistics automation (delivery assignment, route optimization, pickup scheduling, tracking, POD verification, COD reconciliation)`
- ❌ `automation/ai_automation_service.py -> AI automation (product description, categorization, image optimization, duplicate detection, content moderation)`
- ❌ `automation/data_automation_service.py -> data automation (import/export, cleanup, archive, backup verification)`
- ❌ `automation/security_automation_service.py -> security automation (login monitoring, suspicious activity, account lock, session cleanup, API monitoring)`
- ❌ `automation/customer_automation_service.py -> customer automation (welcome journey, cart abandonment, review requests, loyalty rewards, re-engagement)`
- ❌ `automation/supplier_automation_service.py -> supplier automation (KYC workflow, store approval, product approval, performance alerts, payout notifications)`
- ❌ `automation/admin_automation_service.py -> admin automation (dashboard alerts, health monitoring, error reporting, daily/weekly summary)`
- ❌ `automation/monitoring_recovery_service.py -> monitoring & recovery (automation logs, failure alerts, retry queue, execution history, performance metrics)`
- ❌ `automation/automation_registry_service.py -> central automation registry (enable/disable, priority, dependencies, dry-run, audit trail, version control, RBAC)`
- ❌ `middleware/ai_rate_limit_middleware.py -> AI rate-limit and circuit-breaker middleware (cross-cutting)`
- ❌ `middleware/automation_guard_middleware.py -> Automation execution guard middleware (cross-cutting)`
- ❌ `jobs/ai_batch_inference_worker.py -> background worker for batch AI inference (Celery/Redis)`
- ❌ `jobs/ai_ocr_batch_worker.py -> background worker for batch OCR processing`
- ❌ `jobs/ai_transcription_worker.py -> background worker for voice transcription batch`
- ❌ `jobs/automation_execution_worker.py -> background worker for async automation execution`
- ❌ `jobs/automation_retry_worker.py -> background worker for automation retry queue and DLQ`
- ❌ `jobs/automation_scheduler_worker.py -> background worker for scheduled/cron/delayed automation jobs`
- ❌ `events/ai_events.py -> domain event schemas for AI inference events`
- ❌ `events/automation_events.py -> domain event schemas for automation events (triggered, completed, failed, retried)`
- ❌ `providers/media/media_storage_provider.py -> R2/S3 media storage adapter for product images, scanned receipts`

### Database Files

**Present (9):**

- ✅ `base.py`
- ✅ `database.py`
- ✅ `session.py`
- ✅ `transaction.py`
- ✅ `schemas.py`
- ✅ `models.py`
- ✅ `create_tables.py`
- ✅ `init_db.py`
- ✅ `database_logging.py`

**Missing (4):**

- ❌ `security/`
- ❌ `setup/`
- ❌ `seeds/`
- ❌ `alembic/`

### Model Files

**Missing (7):**

- ❌ `ai/ai_model.py -> SQLAlchemy ORM model: AiModel (registry entry: name, version, provider_type, health_status, config_json)`
- ❌ `ai/ai_inference_log.py -> SQLAlchemy ORM model: AiInferenceLog (append-only: actor, model_name, input_hash, output_hash, latency_ms, tokens, status, error_json, country_code)`
- ❌ `ai/ai_provider_health.py -> SQLAlchemy ORM model: AiProviderHealth (circuit-breaker state, consecutive_failures, last_success_at, last_error_at)`
- ❌ `automation/automation_run.py -> SQLAlchemy ORM model: AutomationRun (append-only: engine_name, trigger_type, input_json, output_json, status, actor, latency_ms, retry_count, error_json, country_code)`
- ❌ `automation/automation_trigger.py -> SQLAlchemy ORM model: AutomationTrigger (trigger definition: engine_name, event_type, cron, condition_json, enabled, priority)`
- ❌ `automation/automation_action.py -> SQLAlchemy ORM model: AutomationAction (action definition: engine_name, action_type, target_service, payload_json, retry_policy_json, timeout_ms)`
- ❌ `media/ -> SQLAlchemy ORM models: MediaAsset (metadata only, bytes in R2/S3)`

### Frontend Web

**Present (1):**

- ✅ `web_app/chatbot/page.tsx`

**Missing (11):**

- ❌ `web_app/admin/ai-providers/page.tsx`
- ❌ `web_app/admin/automation/page.tsx`
- ❌ `web_app/supplier/products/upload/page.tsx`
- ❌ `admin/AiProviderRegistry.tsx`
- ❌ `admin/AiProviderStaging.tsx`
- ❌ `admin/AiProviderTest.tsx`
- ❌ `automation/AutomationEngineCard.tsx`
- ❌ `automation/AutomationDryRun.tsx`
- ❌ `automation/AutomationAuditTrail.tsx`
- ❌ `supplier/AiProductUpload.tsx`
- ❌ `chat/AiChatBot.tsx`

### Frontend Mobile

**Present (1):**

- ✅ `chatbot.tsx`

**Missing (4):**

- ❌ `supplier/products/upload.tsx`
- ❌ `admin/ai-providers.tsx`
- ❌ `components/supplier/AiProductUpload.tsx`
- ❌ `components/chat/AiChatBot.tsx`

### Tests

**Missing (41):**

- ❌ `tests/backend/_test_ai_provider_registry.py`
- ❌ `tests/backend/_test_ai_chatbot_provider.py`
- ❌ `tests/backend/_test_ai_ocr_provider.py`
- ❌ `tests/backend/_test_ai_background_removal_provider.py`
- ❌ `tests/backend/_test_ai_product_analysis_provider.py`
- ❌ `tests/backend/_test_ai_voice_to_text_provider.py`
- ❌ `tests/backend/_test_ai_search_vectorization_provider.py`
- ❌ `tests/backend/_test_ai_ip_detection_provider.py`
- ❌ `tests/backend/_test_ai_map_location_provider.py`
- ❌ `tests/backend/_test_ai_country_intelligence_provider.py`
- ❌ `tests/backend/_test_ai_admin_analytics_provider.py`
- ❌ `tests/backend/_test_automation_workflow_engine.py`
- ❌ `tests/backend/_test_automation_event_engine.py`
- ❌ `tests/backend/_test_automation_notification_engine.py`
- ❌ `tests/backend/_test_automation_scheduled_jobs_engine.py`
- ❌ `tests/backend/_test_automation_approval_engine.py`
- ❌ `tests/backend/_test_automation_rule_engine.py`
- ❌ `tests/backend/_test_automation_assignment_engine.py`
- ❌ `tests/backend/_test_automation_reminder_engine.py`
- ❌ `tests/backend/_test_automation_escalation_engine.py`
- ❌ `tests/backend/_test_automation_finance_automation.py`
- ❌ `tests/backend/_test_automation_inventory_automation.py`
- ❌ `tests/backend/_test_automation_order_automation.py`
- ❌ `tests/backend/_test_automation_logistics_automation.py`
- ❌ `tests/backend/_test_automation_ai_automation.py`
- ❌ `tests/backend/_test_automation_data_automation.py`
- ❌ `tests/backend/_test_automation_security_automation.py`
- ❌ `tests/backend/_test_automation_customer_automation.py`
- ❌ `tests/backend/_test_automation_supplier_automation.py`
- ❌ `tests/backend/_test_automation_admin_automation.py`
- ❌ `tests/backend/_test_automation_monitoring_recovery.py`
- ❌ `tests/backend/_test_automation_registry.py`
- ❌ `tests/backend/_test_ai_provider_validation_cycle.py`
- ❌ `tests/frontend/web_app/_test_ai_providers_page.test.tsx`
- ❌ `tests/frontend/web_app/_test_automation_dashboard.test.tsx`
- ❌ `tests/frontend/web_app/_test_supplier_ai_upload.test.tsx`
- ❌ `tests/frontend/web_app/_test_chatbot_page.test.tsx`
- ❌ `tests/frontend/mobile_app/_test_supplier_ai_upload_mobile.test.tsx`
- ❌ `tests/frontend/mobile_app/_test_chatbot_mobile.test.tsx`
- ❌ `tests/playwright/_test_ai_provider_e2e.spec.ts`
- ❌ `tests/playwright/_test_automation_dashboard_e2e.spec.ts`

### API Routes

**Missing (23):**

- ❌ `GET /health/ai-providers`
- ❌ `POST /api/v1/ai/chatbot/message`
- ❌ `POST /api/v1/ai/ocr/scan`
- ❌ `POST /api/v1/ai/image/background-removal`
- ❌ `POST /api/v1/ai/image/analyze`
- ❌ `POST /api/v1/ai/voice/transcribe`
- ❌ `POST /api/v1/ai/search/vectorize`
- ❌ `GET /api/v1/ai/search/hybrid`
- ❌ `GET /api/v1/ai/ip/detect`
- ❌ `POST /api/v1/ai/map/geocode`
- ❌ `POST /api/v1/ai/map/reverse-geocode`
- ❌ `GET /api/v1/ai/map/distance-matrix`
- ❌ `GET /api/v1/ai/country/intelligence`
- ❌ `GET /api/v1/ai/admin/analytics`
- ❌ `GET /api/v1/automation/engines`
- ❌ `POST /api/v1/automation/{engine}/execute`
- ❌ `POST /api/v1/automation/{engine}/dry-run`
- ❌ `GET /api/v1/automation/{engine}/runs`
- ❌ `POST /api/v1/automation/{engine}/enable`
- ❌ `POST /api/v1/automation/{engine}/disable`
- ❌ `POST /api/v1/automation/{engine}/trigger`
- ❌ `GET /api/v1/automation/registry`
- ❌ `GET /api/v1/automation/audit-trail`

### DB Model Classes

**Present (1):**

- ✅ `MediaAsset`

**Missing (6):**

- ❌ `AiModel`
- ❌ `AiInferenceLog`
- ❌ `AiProviderHealth`
- ❌ `AutomationRun`
- ❌ `AutomationTrigger`
- ❌ `AutomationAction`

---
